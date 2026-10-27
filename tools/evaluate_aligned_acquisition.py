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
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib
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
    # An implementation snapshot must descend from the independently frozen matrix.
    git("merge-base", "--is-ancestor", MATRIX_COMMIT, commit)
    pinned_gold = freeze.get("gold")
    if (type(pinned_gold) is not dict or pinned_gold.get("sha256") != GOLD_SHA256
            or local_path(pinned_gold.get("path")).resolve() != gold_path.resolve()):
        raise ValueError("code-freeze gold path/hash differs from the independent pin")
    files, native = freeze.get("files"), freeze.get("native")
    if type(files) is not dict or not files or type(native) is not dict or not native:
        raise ValueError("code freeze requires tracked files and local native hashes")
    required = {"src/nabt/aligned_acquisition.py", "tools/evaluate_aligned_acquisition.py",
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
    if files[SPEC_PATH] != freeze.get("spec_sha256"):
        raise ValueError("specification hash is not pinned consistently")
    if digest(git("show", MATRIX_COMMIT + ":" + SPEC_PATH, binary=True)) != freeze["spec_sha256"]:
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
                    "matrix_commit": MATRIX_COMMIT, "native": native_current,
                    "native_matches_freeze": native_current == native}


def snapshot(freeze: dict, gold_path: Path) -> dict:
    paths = set(freeze["files"]) | set(freeze["native"])
    return {"files": {name: digest(local_path(name).read_bytes())
                       if local_path(name).is_file() else None for name in sorted(paths)},
            "gold_sha256": digest(gold_path.read_bytes()), "head": git("rev-parse", "HEAD")}


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
    gold = load_gold(gold_path)
    before = snapshot(freeze, gold_path)
    sys.path[:0] = [str(ROOT), str(ROOT / "src")]
    acquisition = importlib.import_module("nabt.aligned_acquisition")
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
    changed = sorted(name for name in set(before["files"]) | set(after["files"])
                     if before["files"].get(name) != after["files"].get(name))
    integrity = (before == after and not uncovered and freeze_evidence["native_matches_freeze"])
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
                "loaded_repository_python": loaded, "uncovered_modules": uncovered,
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
