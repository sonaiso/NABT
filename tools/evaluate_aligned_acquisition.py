#!/usr/bin/env python3
"""Replay the independently frozen acquisition matrix without changing its text.

No gold row is an implementation rule.  The gold digest below was received at
the independent matrix freeze; its contents remained hidden while this harness
was written.  First runs require a committed implementation and a code-freeze
manifest with this shape::

    {"schema": "nabt.aligned-acquisition-code-freeze.v1", "commit": "<git id>",
     "spec_sha256": "<sha256>", "gold": {"path": "...", "sha256": "..."},
     "files": {"repository/relative/path": "<sha256>"},
     "native": {"formal/.lake/build/bin/name": "<sha256>"}}

Tracked file bytes must equal both the manifest and the named git commit.
Native binary hashes bind this local run, not every reproducible Lean build.
The output is exclusively created and never overwritten, including on failure.

The first phase also verifies the local matrix-to-implementation git chronology.
Exposed replays retain the original matrix ID as historical evidence but do not
claim that chronology: publication or squash merges may replace commit IDs.
Both phases still require the fixed gold/spec content pins, exact committed
runtime files, native build identity, and the same representation checks.
The initial execution snapshot must itself match the validated freeze before
runtime imports; equality between two snapshots is not evidence of that match.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.resources.abc import TraversableResources
from importlib.util import spec_from_file_location
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "evidence/aligned_acquisition_v1/gold.json"
GOLD_SHA256 = "d94bc45073f21e082c345bef0eb3ac4636451a6695cc247ce447241ee6ffedf7"
MATRIX_COMMIT = "e29d11caf2a4fad5ac74a8474cde97103886cc3a"
SPEC_PATH = "docs/ACQUISITION_READER_SPEC.md"
SPEC_SHA256 = "5f8dda47209169b9e3995fc44e3da0bcf1bfc3580fa74a6dbe2afe4cf7687b7f"
INFERENCE_SOURCE_PATH = "evidence/licensed_inference_v1/source_links.json"
SEPARATORS = frozenset(' \t\r\n.،؛,:!?؟()[]{}«»"“”')
ACQUISITION_STATUSES = {"ACQUIRED", "DEFER", "INVALID_INPUT"}
GOAL_KINDS = {"acquisition", "person", "nominal_syntax", "conditional_inference"}
HEX = re.compile(r"[0-9a-f]{64}\Z")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def case_source_id(case_id: str) -> str:
    """Preserve independent identity while satisfying the existing reader's ID grammar."""
    return "independent_" + digest(case_id.encode("utf-8", "strict"))


def unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load_json(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("input JSON exceeds evaluator budget")
    result = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=unique_object,
                        parse_constant=lambda value: (_ for _ in ()).throw(
                            ValueError("nonfinite JSON number: " + value)))
    if type(result) is not dict:
        raise ValueError("JSON document must be an object")
    return result, digest(raw)


def git(*args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                            capture_output=True, timeout=60)
    return result.stdout if binary else result.stdout.decode("utf-8", "strict").strip()


def local_path(name: str) -> Path:
    if type(name) is not str or not name or Path(name).is_absolute():
        raise ValueError("freeze paths must be repository-relative strings")
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or path.relative_to(ROOT).as_posix() != name:
        raise ValueError("noncanonical or escaping freeze path: " + name)
    return path


def cells_valid(value: Any) -> bool:
    return type(value) is list and all(type(cell) is int and 0 <= cell < 116 for cell in value)


def load_gold(path: Path) -> dict:
    gold, actual_hash = load_json(path)
    if actual_hash != GOLD_SHA256:
        raise ValueError("gold differs from the independently frozen SHA-256")
    if gold.get("schema") != "nabt.aligned-acquisition-gold.v1":
        raise ValueError("unsupported acquisition gold schema")
    cases = gold.get("cases")
    if type(cases) is not list or len(cases) != 72:
        raise ValueError("the frozen matrix requires exactly 72 cases")
    ids, families = set(), Counter()
    for case in cases:
        if type(case) is not dict:
            raise ValueError("each gold case must be an object")
        for field in ("id", "family", "text"):
            if type(case.get(field)) is not str:
                raise ValueError("gold " + field + " must be text")
            case[field].encode("utf-8", "strict")
        if not case["id"] or case["id"] in ids or not case["family"]:
            raise ValueError("gold case IDs must be nonempty and unique")
        ids.add(case["id"])
        families[case["family"]] += 1
        if case.get("ending") not in {"wasl", "waqf"}:
            raise ValueError("gold ending must be wasl or waqf")
        expected = case.get("expected")
        if (type(expected) is not dict or not set(expected) <=
                {"acquisition_status", "word_cells", "reason"} or
                expected.get("acquisition_status") not in ACQUISITION_STATUSES):
            raise ValueError("unsupported representation expectation")
        if "word_cells" in expected and (type(expected["word_cells"]) is not list or
                not all(cells_valid(cells) for cells in expected["word_cells"])):
            raise ValueError("gold cells must be A116 integers, never Booleans")
        if "reason" in expected and type(expected["reason"]) is not str:
            raise ValueError("gold reason must be text")
        goal = case.get("goal")
        if (type(goal) is not dict or set(goal) != {"kind", "positive", "description"}
                or goal["kind"] not in GOAL_KINDS or type(goal["positive"]) is not bool
                or type(goal["description"]) is not str):
            raise ValueError("unsupported downstream goal contract")
        if "query" in case:
            if type(case["query"]) is not str:
                raise ValueError("gold query must be exact text")
            case["query"].encode("utf-8", "strict")
    if len(families) != 4 or min(families.values()) < 12:
        raise ValueError("gold must retain four families with at least 12 rows each")
    return gold


def verify_freeze(path: Path, phase: str, gold_path: Path) -> tuple[dict, dict]:
    freeze, freeze_hash = load_json(path)
    if freeze.get("schema") != "nabt.aligned-acquisition-code-freeze.v1":
        raise ValueError("unsupported code-freeze schema")
    commit = freeze.get("commit")
    if type(commit) is not str or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("code freeze requires a complete git commit ID")
    if git("rev-parse", commit + "^{commit}") != commit:
        raise ValueError("code-freeze commit does not exist")
    if phase == "first" and git("rev-parse", "HEAD") != commit:
        raise ValueError("first run requires HEAD at the implementation freeze")
    # This chronology claim belongs only to the original local first execution.
    # Published snapshots and squash merges can preserve exact contents while
    # assigning new commit identities; their runs are explicitly exposed.
    if phase == "first":
        git("merge-base", "--is-ancestor", MATRIX_COMMIT, commit)
    pinned_gold = freeze.get("gold")
    if (type(pinned_gold) is not dict or pinned_gold.get("sha256") != GOLD_SHA256
            or local_path(pinned_gold.get("path")).resolve() != gold_path.resolve()):
        raise ValueError("code-freeze gold path/hash differs from the independent pin")
    if digest(git("show", commit + ":" + pinned_gold["path"], binary=True)) != GOLD_SHA256:
        raise ValueError("committed gold differs from the independent content pin")
    files, native = freeze.get("files"), freeze.get("native")
    if type(files) is not dict or not files or type(native) is not dict or not native:
        raise ValueError("code freeze requires tracked files and local native hashes")
    if set(files) & set(native):
        raise ValueError("source and native freeze paths must not overlap")
    required = {"tools/aligned_acquisition.py", "tools/evaluate_aligned_acquisition.py",
                "evidence/aligned_acquisition_v1/source_evidence.json",
                SPEC_PATH, INFERENCE_SOURCE_PATH}
    if not required <= set(files):
        raise ValueError("code freeze omits evaluator, implementation or specification")
    tracked = set(git("ls-files", "-z").split("\0"))
    data_files = {name for name in tracked if name.startswith("src/nabt/data/")}
    if not data_files <= set(files):
        raise ValueError("code freeze omits installed runtime data: " +
                         ", ".join(sorted(data_files - set(files))))
    for name, expected_hash in files.items():
        file_path = local_path(name)
        if name not in tracked or type(expected_hash) is not str or not HEX.fullmatch(expected_hash):
            raise ValueError("invalid or untracked code-freeze entry: " + name)
        if digest(file_path.read_bytes()) != expected_hash:
            raise ValueError("working file differs from implementation freeze: " + name)
        if digest(git("show", commit + ":" + name, binary=True)) != expected_hash:
            raise ValueError("file is not committed at implementation freeze: " + name)
    inference_sources, _ = load_json(local_path(INFERENCE_SOURCE_PATH))
    linked_sources = {item["local_path"] for item in inference_sources["sources"]}
    linked_sources.update(item["path"] for item in inference_sources["source_registries"])
    if not linked_sources <= set(files):
        raise ValueError("code freeze omits inference source evidence: " +
                         ", ".join(sorted(linked_sources - set(files))))
    if files[SPEC_PATH] != SPEC_SHA256 or freeze.get("spec_sha256") != SPEC_SHA256:
        raise ValueError("specification differs from the independent content pin")
    if phase == "first" and digest(git("show", MATRIX_COMMIT + ":" + SPEC_PATH, binary=True)) != SPEC_SHA256:
        raise ValueError("specification differs from the independent matrix freeze")
    # Check the exact first-run native build locally. Later build changes are
    # retained as evidence, never silently interpreted as the original build.
    required_native = {"formal/.lake/build/bin/alignedAcquisition", "formal/.lake/build/bin/licensedInference"}
    if not required_native <= set(native):
        raise ValueError("code freeze omits a native acquisition or inference binary")
    native_current = {}
    for name, expected_hash in native.items():
        file_path = local_path(name)
        if type(expected_hash) is not str or not HEX.fullmatch(expected_hash):
            raise ValueError("invalid native hash in code freeze")
        native_current[name] = digest(file_path.read_bytes()) if file_path.is_file() else None
        if phase == "first" and native_current[name] != expected_hash:
            raise ValueError("local native binary differs from first-run freeze: " + name)
    return freeze, {"manifest_sha256": freeze_hash, "commit": commit,
                    "original_local_matrix_commit": MATRIX_COMMIT,
                    "original_matrix_ancestry_verified": phase == "first",
                    "held_out_first_execution": phase == "first",
                    "content_pins": {"spec_sha256": SPEC_SHA256, "gold_sha256": GOLD_SHA256},
                    "committed_content_pins_verified": True, "native": native_current,
                    "native_matches_freeze": native_current == native}


def snapshot(freeze: dict, gold_path: Path) -> dict:
    paths = set(freeze["files"]) | set(freeze["native"])
    return {"files": {name: digest(local_path(name).read_bytes())
                       if local_path(name).is_file() else None for name in sorted(paths)},
            "gold_sha256": digest(gold_path.read_bytes()), "head": git("rev-parse", "HEAD")}


def runtime_module(name: str) -> bool:
    return name in {"tools", "nabt"} or name.startswith(("tools.", "nabt."))


class FrozenPackageResources(TraversableResources):
    """Preserve repository package-data access for the existing NABT readers."""
    def __init__(self, directory: Path):
        self.directory = directory

    def files(self):
        return self.directory


class FrozenSourceLoader(Loader):
    """Compile the checked bytes directly; never read or write a .pyc file."""
    def __init__(self, owner, relative: str | None, directory: Path | None):
        self.owner, self.relative, self.directory = owner, relative, directory

    def create_module(self, spec):
        return None

    def get_resource_reader(self, fullname):
        return FrozenPackageResources(self.directory) if self.directory is not None else None

    def exec_module(self, module):
        if self.relative is None:
            return  # A repository-owned namespace, with no executable initializer.
        path = local_path(self.relative)
        raw = path.read_bytes()
        if digest(raw) != self.owner.files[self.relative]:
            raise ImportError("runtime source differs from validated freeze: " + self.relative)
        code = compile(raw, str(path), "exec", dont_inherit=True)
        self.owner.executed[self.relative] = digest(raw)
        exec(code, module.__dict__)


class FrozenSourceFinder(MetaPathFinder):
    """Own tools/nabt imports, including packages, without ambient fallback."""
    def __init__(self, files: dict):
        self.files = files
        self.executed = {}
        self.loaders = {}

    def find_spec(self, fullname, path=None, target=None):
        if not runtime_module(fullname):
            return None
        base = ("src/" if fullname.split(".")[0] == "nabt" else "") + fullname.replace(".", "/")
        package, source = base + "/__init__.py", base + ".py"
        if package in self.files:
            relative, directory = package, local_path(base)
        elif source in self.files:
            relative, directory = source, None
        elif any(name.startswith(base + "/") and name.endswith(".py") for name in self.files):
            relative, directory = None, local_path(base)
            # Never silently turn an unlisted initializer into a namespace.
            if (directory / "__init__.py").exists():
                raise ImportError("unfrozen package initializer: " + package)
        else:
            raise ModuleNotFoundError("runtime module absent from validated freeze: " + fullname)
        loader = FrozenSourceLoader(self, relative, directory)
        self.loaders[fullname] = loader
        if relative is None:
            spec = ModuleSpec(fullname, loader, is_package=True)
            spec.submodule_search_locations = [str(directory)]
            return spec
        return spec_from_file_location(fullname, local_path(relative), loader=loader,
            submodule_search_locations=[str(directory)] if directory is not None else None)

    def audit_origins(self):
        for name, module in tuple(sys.modules.items()):
            if not runtime_module(name):
                continue
            loader = self.loaders.get(name)
            spec = getattr(module, "__spec__", None)
            if loader is None or spec is None or spec.loader is not loader:
                raise ImportError("runtime module was not loaded from frozen source: " + name)
            expected_file = str(local_path(loader.relative)) if loader.relative else None
            if getattr(module, "__file__", None) != expected_file or spec.origin != expected_file:
                raise ImportError("runtime module origin changed: " + name)
            expected_path = [str(loader.directory)] if loader.directory is not None else None
            actual_path = getattr(module, "__path__", None)
            if (list(actual_path) if actual_path is not None else None) != expected_path:
                raise ImportError("runtime package path changed: " + name)


@contextmanager
def frozen_runtime(freeze: dict):
    """Fresh, source-only repository imports for this single-threaded evaluator.

Quarantine all preloaded tools/nabt modules: a matching __file__ cannot prove
what code an existing module object executed. Restore the caller's cache only
after evaluation, including on error. The interpreter/stdlib remain trusted.
"""
    previous = {name: module for name, module in tuple(sys.modules.items()) if runtime_module(name)}
    previous_path = sys.path[:]
    for name in previous:
        del sys.modules[name]
    finder = FrozenSourceFinder(freeze["files"])
    sys.meta_path.insert(0, finder)
    try:
        yield finder
        finder.audit_origins()
    finally:
        sys.meta_path.remove(finder)
        for name in tuple(sys.modules):
            if runtime_module(name):
                del sys.modules[name]
        sys.modules.update(previous)
        sys.path[:] = previous_path


def source_checks(acquisition: Any, text: str, source_id: str, ending: str) -> dict:
    """Independent alignment/domain checks, including incomplete acquisitions."""
    checks = {"source_identity": False, "source_restoration": False,
              "piece_intervals": False, "cell_domain": False, "word_alignment": False}
    if type(acquisition) is not dict:
        return checks
    checks["source_identity"] = all(acquisition.get(key) == wanted for key, wanted in {
        "law_id": "nabt.aligned-acquisition.v1", "alphabet_id": "nabt.a116.v1",
        "source_id": source_id, "revision": "1", "scope": "independent-matrix",
        "ending": ending, "text": text}.items())
    pieces, words = acquisition.get("pieces"), acquisition.get("words")
    if type(pieces) is not list or type(words) is not list:
        return checks
    if any(type(piece) is not dict for piece in pieces) or any(type(word) is not dict for word in words):
        return checks
    checks["source_restoration"] = (all(type(piece.get("raw")) is str for piece in pieces)
                                    and "".join(piece["raw"] for piece in pieces) == text)
    checks["cell_domain"] = all(cells_valid(item.get("cells")) for item in [*pieces, *words])
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))
    cursor = 0
    intervals_valid = True
    for piece in pieces:
        start, end = piece.get("start"), piece.get("end")
        if (type(start) is not int or type(end) is not int or start != cursor
                or not start < end <= len(text) or piece.get("raw") != text[start:end]
                or type(piece.get("byte_start")) is not int or type(piece.get("byte_end")) is not int
                or piece["byte_start"] != offsets[start] or piece["byte_end"] != offsets[end]):
            intervals_valid = False
            break
        cursor = end
    checks["piece_intervals"] = intervals_valid and cursor == len(text)
    spans = []
    cursor = 0
    while cursor < len(text):
        if text[cursor] in SEPARATORS:
            cursor += 1
            continue
        start = cursor
        while cursor < len(text) and text[cursor] not in SEPARATORS:
            cursor += 1
        spans.append((start, cursor))
    aligned = len(words) == len(spans) and checks["piece_intervals"] and checks["cell_domain"]
    for word, (start, end) in zip(words, spans):
        if any(type(word.get(key)) is not int or word[key] != value for key, value in {
            "start": start, "end": end, "byte_start": offsets[start], "byte_end": offsets[end]}.items()):
            aligned = False
            continue
        members = [piece for piece in pieces if start <= piece["start"] < end]
        if (not members or members[0]["start"] != start or members[-1]["end"] != end
                or word["cells"] != [cell for piece in members for cell in piece["cells"]]):
            aligned = False
    checks["word_alignment"] = aligned
    return checks


def goal_result(case: dict, acquired: bool, verified_representation: bool,
                inference: Any = None) -> dict:
    goal = case["goal"]
    base = {"kind": goal["kind"], "positive": goal["positive"],
            "description": goal["description"], "measurement_status": "UNMEASURED"}
    if goal["kind"] == "acquisition":
        if not verified_representation:
            return {**base, "outcome": "MISS" if goal["positive"] else "UNMEASURED",
                    "reason": "NO_NATIVE_VERIFIED_REPRESENTATION_RESULT"}
        success = acquired if goal["positive"] else not acquired
        return {**base, "measurement_status": "MEASURED", "outcome": "SUCCESS" if success else "MISS",
                "reason": "VERIFIED_ACQUISITION" if acquired else "NO_VERIFIED_ACQUISITION"}
    if goal["kind"] in {"person", "nominal_syntax"}:
        return {**base, "outcome": "MISS" if goal["positive"] else "UNMEASURED",
                "reason": "NO_EXACT_PERSON_OR_SYNTAX_GOAL_CONTRACT"}
    if type(inference) is not dict:
        return {**base, "outcome": "MISS" if goal["positive"] else "UNMEASURED",
                "reason": "NO_QUERY_OR_INFERENCE_RESULT"}
    exact = (inference.get("source", {}).get("raw_text") == case["text"]
             and inference.get("source", {}).get("sha256") == digest(case["text"].encode("utf-8"))
             and inference.get("source", {}).get("source_id") == case_source_id(case["id"])
             and inference.get("source", {}).get("revision") == "1"
             and inference.get("binding", {}).get("scope") == "independent-matrix"
             and inference.get("query", {}).get("raw_text") == case.get("query")
             and inference.get("query", {}).get("sha256") == digest(case.get("query", "").encode("utf-8")))
    supported_contract = (exact and inference.get("verified") is True
                          and inference.get("law_id") == "nabt.licensed-inference.v1"
                          and inference.get("native_checked") is True
                          and inference.get("all_readings_complete") is True
                          and inference.get("closures_checked") is True
                          and inference.get("world_truth_established") is False
                          and inference.get("authority") == "SOURCE_RELATIVE_CONSEQUENCE")
    if not supported_contract:
        return {**base, "outcome": "MISS" if goal["positive"] else "UNMEASURED",
                "reason": "INFERENCE_NOT_NATIVE_VERIFIED_ON_EXACT_SOURCE_AND_QUERY",
                "inference_status": inference.get("status"), "exact_source_and_query": exact}
    status = inference.get("status")
    # The Boolean goal asks whether the exact query is licensed, not whether
    # its contrary is true. UNKNOWN therefore satisfies a measured negative
    # licensing goal, while conflicts/deferred readings remain unmeasured.
    if status not in {"SUPPORTED", "REFUTED", "UNKNOWN"}:
        return {**base, "outcome": "MISS" if goal["positive"] else "UNMEASURED",
                "reason": "NO_UNAMBIGUOUS_QUERY_LICENSING_OUTCOME", "inference_status": status}
    success = (status == "SUPPORTED") == goal["positive"]
    return {**base, "measurement_status": "MEASURED", "outcome": "SUCCESS" if success else "MISS",
            "reason": "EXACT_SOURCE_RELATIVE_QUERY_LICENSING", "inference_status": status,
            "exact_source_and_query": exact}


def evaluate_case(case: dict, read_acquired: Any, infer: Any) -> dict:
    source_id = case_source_id(case["id"])
    row = {"id": case["id"], "family": case["family"], "text": case["text"],
           "ending": case["ending"], "expected": case["expected"], "executed": False}
    try:
        receipt = read_acquired(case["text"], source_id=source_id, revision="1",
                                scope="independent-matrix", ending=case["ending"])
        if type(receipt) is not dict:
            raise TypeError("read_acquired must return an object")
        row.update(executed=True, raw_result=receipt)
        acquisition = receipt.get("acquisition")
        checks = source_checks(acquisition, case["text"], source_id, case["ending"])
        verified = (receipt.get("verified") is True
                    and receipt.get("authority") == "NATIVE_REPLAYED_LOCAL_REPRESENTATION")
        canonical_status = acquisition.get("status") if type(acquisition) is dict else None
        status = canonical_status if verified else receipt.get("status")
        words = acquisition.get("words") if type(acquisition) is dict else None
        cells = [word.get("cells") for word in words] if type(words) is list else None
        expected = case["expected"]
        reason = acquisition.get("reason") if type(acquisition) is dict else receipt.get("reason")
        rules = [piece.get("rule") for piece in acquisition.get("pieces", [])] if type(acquisition) is dict else []
        observed = {"status": status, "proposal_status": canonical_status, "verified": verified,
                    "word_cells": cells, "reason": reason, "piece_rules": rules,
                    "source_checks": checks}
        compared = {"status_match": status == expected["acquisition_status"],
                    "cells_expected": "word_cells" in expected,
                    "cells_match": cells == expected["word_cells"] if "word_cells" in expected else None,
                    "reason_expected": "reason" in expected,
                    "reason_match": (expected["reason"] == reason or expected["reason"] in rules)
                    if "reason" in expected else None}
        compared["representation_match"] = all(value for name, value in compared.items()
                                                if name.endswith("_match") and value is not None)
        acquired = verified and status == "ACQUIRED" and all(checks.values())
        row.update(observed=observed, checks=compared, verified_acquired=acquired,
                   false_license=status == "ACQUIRED" and expected["acquisition_status"] != "ACQUIRED")
    except Exception as exc:
        row.update(executed=False, error={"type": type(exc).__name__, "message": str(exc)},
                   verified_acquired=False, false_license=False,
                   checks={"status_match": False, "cells_expected": "word_cells" in case["expected"],
                           "cells_match": None, "reason_expected": "reason" in case["expected"],
                           "reason_match": None, "representation_match": False})
    inference = None
    if case["goal"]["kind"] == "conditional_inference" and "query" in case:
        try:
            inference = infer(case["text"], case["query"], source_id=source_id,
                              revision="1", scope="independent-matrix")
            row["inference_result"] = inference
        except Exception as exc:
            row["inference_error"] = {"type": type(exc).__name__, "message": str(exc)}
    verified_representation = (row.get("observed", {}).get("verified") is True
                               and all(row["observed"]["source_checks"].values()))
    row["goal"] = goal_result(case, row["verified_acquired"], verified_representation, inference)
    return row


def goal_counts(rows: list[dict]) -> dict:
    outcomes = Counter(row["goal"]["outcome"] for row in rows)
    return {key: outcomes[key] for key in ("SUCCESS", "MISS", "UNMEASURED")}


def measurement_counts(rows: list[dict]) -> dict:
    measured = Counter(row["goal"]["measurement_status"] for row in rows)
    return {key: measured[key] for key in ("MEASURED", "UNMEASURED")}


def counts(rows: list[dict]) -> dict:
    positive_representation = [row for row in rows if row["expected"]["acquisition_status"] == "ACQUIRED"]
    positive_goals = [row for row in rows if row["goal"]["positive"]]
    downstream = [row for row in rows if row["goal"]["kind"] != "acquisition"]
    positive_downstream = [row for row in downstream if row["goal"]["positive"]]
    cells = [row for row in rows if row["checks"]["cells_expected"]]
    reasons = [row for row in rows if row["checks"]["reason_expected"]]
    return {"denominator": len(rows), "executed": sum(row["executed"] for row in rows),
            "native_verified": sum(row.get("observed", {}).get("verified") is True for row in rows),
            "status_matches": sum(row["checks"]["status_match"] for row in rows),
            "cell_comparisons": {"denominator": len(cells),
                                 "matches": sum(row["checks"]["cells_match"] is True for row in cells)},
            "reason_comparisons": {"denominator": len(reasons),
                                   "matches": sum(row["checks"]["reason_match"] is True for row in reasons)},
            "representation_matches": sum(row["checks"]["representation_match"] for row in rows),
            "false_licenses": sum(row["false_license"] for row in rows),
            "positive_acquisition_coverage": {"denominator": len(positive_representation),
                "verified_acquired": sum(row["verified_acquired"] for row in positive_representation),
                "verified_exact": sum(row["verified_acquired"] and row["checks"]["representation_match"]
                                      for row in positive_representation)},
            "positive_goal_acquisition_coverage": {"denominator": len(positive_goals),
                "verified_acquired": sum(row["verified_acquired"] for row in positive_goals)},
            "goals_by_kind": {kind: {"denominator": sum(row["goal"]["kind"] == kind for row in rows),
                "outcomes": goal_counts([row for row in rows if row["goal"]["kind"] == kind]),
                "measurement": measurement_counts([row for row in rows if row["goal"]["kind"] == kind])}
                for kind in sorted(GOAL_KINDS)},
            "downstream_goals": {"denominator": len(downstream),
                "all": goal_counts(downstream),
                "positive_denominator": len(positive_downstream),
                "positive": goal_counts(positive_downstream),
                "measurement": measurement_counts(downstream)},
            "shape_handoff_statuses": dict(Counter(handoff.get("status", "UNKNOWN")
                for row in rows for handoff in row.get("raw_result", {}).get("shape_handoffs", []))),
            "word_reader_statuses": dict(Counter((row.get("raw_result", {}).get("word_reader") or {}).get("status", "UNMEASURED")
                                                 for row in rows)),
            "runtime_statuses": dict(Counter(row.get("observed", {}).get("status", "EVALUATOR_ERROR") for row in rows)),
            "resource_outcomes": {"acquisition": sum(row.get("observed", {}).get("status") == "RESOURCE_EXHAUSTED" for row in rows),
                "inference": sum(row.get("inference_result", {}).get("status") == "RESOURCE_EXHAUSTED" for row in rows),
                "word_reader": sum((row.get("raw_result", {}).get("word_reader") or {}).get("status") == "RESOURCE_EXHAUSTED" for row in rows),
                "shape_handoffs": sum(handoff.get("status") == "RESOURCE_EXHAUSTED"
                    for row in rows for handoff in row.get("raw_result", {}).get("shape_handoffs", []))}}


def representation_gate(rows: list[dict], contract_passed: bool) -> dict:
    failures = [row["id"] for row in rows if row["checks"]["representation_match"] is not True]
    return {"passed": contract_passed and bool(rows) and not failures,
            "denominator": len(rows), "failures": failures,
            "scope": "All frozen representation status, cell, and reason expectations; downstream goals remain separate."}


def run(gold_path: Path, freeze: dict, freeze_evidence: dict, phase: str) -> dict:
    before = snapshot(freeze, gold_path)
    initial_mismatches = sorted({name for hashes in (freeze["files"], freeze["native"])
                                for name, expected in hashes.items()
                                if before["files"].get(name) != expected})
    if before["gold_sha256"] != GOLD_SHA256:
        initial_mismatches.append("independent gold")
    if phase == "first" and before["head"] != freeze["commit"]:
        initial_mismatches.append("first-run HEAD")
    if initial_mismatches:
        raise ValueError("initial snapshot differs from validated freeze: " + ", ".join(initial_mismatches))
    gold = load_gold(gold_path)
    with frozen_runtime(freeze) as imports:
        acquisition = importlib.import_module("tools.aligned_acquisition")
        inference = importlib.import_module("tools.licensed_inference")
        rows = [evaluate_case(case, acquisition.read_acquired, inference.evaluate) for case in gold["cases"]]
        after = snapshot(freeze, gold_path)
        loaded = {}
        for module in tuple(sys.modules.values()):
            module_file = getattr(module, "__file__", None)
            if not module_file:
                continue
            path = Path(module_file).resolve()
            if path.suffix == ".py" and path.is_relative_to(ROOT):
                loaded[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    uncovered = sorted(name for name in loaded if name not in freeze["files"])
    loaded_mismatches = sorted(name for name, actual_hash in loaded.items()
                               if name in freeze["files"] and actual_hash != freeze["files"][name])
    changed = sorted(name for name in set(before["files"]) | set(after["files"])
                     if before["files"].get(name) != after["files"].get(name))
    integrity = (before == after and not uncovered and not loaded_mismatches
                 and freeze_evidence["native_matches_freeze"])
    families = {family: counts([row for row in rows if row["family"] == family])
                for family in sorted({row["family"] for row in rows})}
    source_failures = [row["id"] for row in rows if row.get("observed", {}).get("verified")
                       and not all(row["observed"]["source_checks"].values())]
    native_failures = [row["id"] for row in rows if row.get("observed", {}).get("verified") is not True]
    contract_passed = (integrity and not source_failures and not native_failures
                       and not any(row["false_license"] for row in rows)
                       and all(row["executed"] for row in rows))
    return {"schema": "nabt.aligned-acquisition-evaluation.v1", "phase": phase,
            "measured_at_utc": datetime.now(timezone.utc).isoformat(), "gold_sha256": GOLD_SHA256,
            "scope": "Finite independent-agent matrix; exposed after the first execution. Acquisition, shape, lexical reading, syntax, and inference are distinct claims.",
            "summary": counts(rows), "families": families,
            "execution_evidence": {**freeze_evidence, "before": before, "after": after,
                "initial_snapshot_matches_freeze": True,
                "runtime_import_policy": "fresh-frozen-source-only.v1",
                "executed_repository_python": imports.executed,
                "loaded_repository_python": loaded, "uncovered_modules": uncovered,
                "loaded_hash_mismatches": loaded_mismatches,
                "changed_files": changed, "integrity_valid": integrity,
                "python": sys.version, "platform": platform.platform()},
            "contract_gate": {"passed": contract_passed,
                              "source_check_failures": source_failures,
                              "native_verification_failures": native_failures,
                              "scope": "Execution integrity, native replay availability, source/domain checks, and absence of false acquisition licenses; not positive coverage or all-Arabic completeness."},
            "representation_gate": representation_gate(rows, contract_passed),
            "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=GOLD_PATH)
    parser.add_argument("--phase", choices=("first", "exposed"), required=True)
    parser.add_argument("--code-freeze", type=Path, required=True)
    args = parser.parse_args()
    # Validate provenance before opening matrix contents or reserving results.
    freeze, evidence = verify_freeze(args.code_freeze, args.phase, args.gold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        try:
            report = run(args.gold, freeze, evidence, args.phase)
        except Exception as exc:
            report = {"schema": "nabt.aligned-acquisition-evaluation.v1", "phase": args.phase,
                      "status": "EVALUATOR_FAILURE", "gold_sha256": GOLD_SHA256,
                      "error": {"type": type(exc).__name__, "message": str(exc)}}
        json.dump(report, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps({key: report[key] for key in ("summary", "families", "contract_gate", "representation_gate", "status", "error")
                      if key in report}, ensure_ascii=False, indent=2))
    return 0 if (report.get("contract_gate", {}).get("passed")
                 and report.get("representation_gate", {}).get("passed")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
