#!/usr/bin/env python3
"""Evaluate the independently frozen v2 matrix through a pinned v1 import guard.

The v1 baseline is checked as exposed evidence; v2 first-execution chronology
is checked separately. Neither matrix is an implementation rule. Every attempt,
including failed preflight, gets an exclusively created, durable result file.
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
import sys
import tempfile
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = "tools/evaluate_aligned_acquisition.py"
BOOTSTRAP_SHA256 = "50b8e45b821818180854f6990324ea255206913ade849ee97c4fd5b5a0d056cb"
SPEC_PATH = "docs/ARTICLE_ACQUISITION_V2_SPEC.md"
SPEC_SHA256 = "48d2c5aa8887a44924e0561d7168d662d071cb940956fcdefbb3bee30173fb71"
SOURCE_PATH = "evidence/article_acquisition_v2/source_evidence.json"
SOURCE_SHA256 = "d5d348e17fd3f34eaa69e5a031956972860dd8dbf3eee25674a265ee4578543c"
GOLD_PATH = "evidence/article_acquisition_v2/gold.json"
GOLD_SHA256 = "a6e61d9dfd999452730753d290d811c483e77aece737409a34ffb776990798d1"
MATRIX_COMMIT = "5b9ad2faa958aacf971454eff500a74d2dbeb800"
FAMILY_COUNTS = {"orthography": 44, "person_category": 12,
                 "nominal_predication": 12, "conditional_inference": 21}
CELL_CASES = 87
LAW_ID = "nabt.aligned-acquisition.v2"
COMPOSITE_LAW_ID = "nabt.acquired-inference.v2"
SCOPE = "independent-article-matrix"
SCHEMA = "nabt.article-acquisition-code-freeze.v1"
RESULT_SCHEMA = "nabt.article-acquisition-evaluation.v1"
NATIVE_PATHS = frozenset("formal/.lake/build/bin/" + name for name in
                         ("alignedAcquisition", "alignedAcquisitionV2", "licensedInference"))
REFERENCE_PATHS = frozenset("evidence/article_acquisition_v2/integration/" + name + ".json"
    for name in ("proof_catalog", "grammar_link_summary", "mantuq_proof_links",
                 "linguistic_proof_links", "licensed_proof_links", "article_proof_links"))
EXTRA_PATHS = frozenset({SPEC_PATH, SOURCE_PATH, GOLD_PATH,
    "evidence/aligned_acquisition_v1/gold.json", "evidence/article_acquisition_v2/GOLD_METHOD.md",
    "formal/theorems.json", "Makefile",
    "tools/article_acquisition.mk", "tools/aligned_acquisition.mk",
    "integrations/current_proof_references.mk", "integrations/grammar_catalog.mk",
    "integrations/mantuq_inference.mk", "integrations/linguistic_truth.mk",
    "integrations/licensed_inference.mk", ".github/workflows/aligned-acquisition.yml",
    ".github/workflows/grammar-catalog-database.yml"}) | REFERENCE_PATHS


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def load_bootstrap():
    """Execute only exact code-owned source bytes, without imports or bytecode."""
    path = (ROOT / BOOTSTRAP_PATH).resolve()
    if path != ROOT / BOOTSTRAP_PATH:
        raise ValueError("bootstrap path is not canonical")
    raw = path.read_bytes()
    if digest(raw) != BOOTSTRAP_SHA256:
        raise ValueError("trusted evaluator bootstrap differs from code-owned pin")
    module = ModuleType("_nabt_article_trusted_bootstrap")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def content_pins():
    return {SPEC_PATH: SPEC_SHA256, SOURCE_PATH: SOURCE_SHA256, GOLD_PATH: GOLD_SHA256}


def extension_paths(guard, source_registry):
    paths = set(EXTRA_PATHS)
    sources = source_registry.get("sources")
    if type(sources) is not list:
        raise ValueError("v2 source registry requires sources")
    for source in sources:
        name = source.get("repository_path") if type(source) is dict else None
        guard.local_path(name)
        paths.add(name)
    return paths


def required_freeze_paths(guard, inventory, inference_registry, source_registry):
    """One union inventory policy shared by the producer and verifier."""
    return guard.required_freeze_paths(inventory, inference_registry) | extension_paths(guard, source_registry)


def verify_freeze(path, phase):
    guard = load_bootstrap()
    envelope, envelope_hash = guard.load_json(path)
    if (envelope.get("schema") != SCHEMA or envelope.get("bootstrap") !=
            {"path": BOOTSTRAP_PATH, "sha256": BOOTSTRAP_SHA256} or
            envelope.get("content_pins") != content_pins() or
            envelope.get("matrix_commit") != MATRIX_COMMIT):
        raise ValueError("v2 freeze differs from installed schema or independent pins")
    inner = envelope.get("baseline")
    if type(inner) is not dict or set(inner.get("native", {})) != NATIVE_PATHS:
        raise ValueError("v2 freeze requires the exact three native executables")
    # The old verifier retains its ORIGINAL schema/spec/gold. It validates every
    # supplied union entry; its exposed flag never stands in for v2 chronology.
    with tempfile.TemporaryDirectory(prefix="nabt-article-baseline-") as directory:
        manifest = Path(directory) / "baseline.json"
        manifest.write_text(wire(inner), encoding="utf-8")
        _, baseline_evidence = guard.verify_freeze(manifest, "exposed", guard.GOLD_PATH)
    commit = inner["commit"]
    registry = guard.parse_json(guard.git("show", commit + ":" + SOURCE_PATH, binary=True))
    required = extension_paths(guard, registry)
    if not required <= set(inner["files"]):
        raise ValueError("v2 freeze omits required extension inputs: " +
                         ", ".join(sorted(required - set(inner["files"]))))
    for name, expected in content_pins().items():
        if inner["files"].get(name) != expected:
            raise ValueError("v2 frozen content pin differs: " + name)
    if inner["files"].get(BOOTSTRAP_PATH) != BOOTSTRAP_SHA256:
        raise ValueError("frozen bootstrap differs from installed bootstrap")
    if phase not in {"first", "exposed"}:
        raise ValueError("unsupported evaluation phase")
    if phase == "first":
        if guard.git("rev-parse", "HEAD") != commit:
            raise ValueError("v2 first run requires HEAD at implementation freeze")
        guard.git("merge-base", "--is-ancestor", MATRIX_COMMIT, commit)
        for name, expected in content_pins().items():
            if digest(guard.git("show", MATRIX_COMMIT + ":" + name, binary=True)) != expected:
                raise ValueError("v2 matrix-time content pin differs: " + name)
    return envelope, {"manifest_sha256": envelope_hash, "manifest_path": str(path.resolve()),
        "canonical_manifest_sha256": digest(wire(envelope).encode("utf-8")), "baseline": baseline_evidence,
        "baseline_phase": "exposed", "v2_phase": phase,
        "v2_matrix_ancestry_verified": phase == "first",
        "held_out_first_execution": phase == "first", "matrix_commit": MATRIX_COMMIT,
        "chronology_scope": "The first phase checks git ancestry and content pins. It records the requested first-execution claim; it does not independently establish secrecy or absence of prior external execution.",
        "content_pins": content_pins(), "bootstrap_sha256": BOOTSTRAP_SHA256}


def load_gold(guard):
    gold, actual = guard.load_json(ROOT / GOLD_PATH)
    if actual != GOLD_SHA256 or gold.get("schema") != "nabt.article-acquisition-gold.v1":
        raise ValueError("v2 matrix differs from independent schema or pin")
    cases = gold.get("cases")
    if type(cases) is not list:
        raise ValueError("matrix cases must be a list")
    ids, families, cells = set(), Counter(), 0
    for case in cases:
        if type(case) is not dict or any(type(case.get(key)) is not str for key in
                ("id", "family", "text", "ending", "onset")):
            raise ValueError("invalid matrix case identity")
        if not case["id"] or case["id"] in ids:
            raise ValueError("matrix case IDs must be unique and nonempty")
        ids.add(case["id"])
        families[case["family"]] += 1
        case["text"].encode("utf-8", "strict")
        if case["ending"] not in {"wasl", "waqf"} or case["onset"] not in {"word_initial", "connected"}:
            raise ValueError("invalid matrix onset or ending")
        expected, goal = case.get("expected"), case.get("goal")
        if (type(expected) is not dict or not set(expected) <= {"acquisition_status", "word_cells"}
                or expected.get("acquisition_status") not in guard.ACQUISITION_STATUSES):
            raise ValueError("invalid representation expectation")
        if "word_cells" in expected:
            cells += 1
            if type(expected["word_cells"]) is not list or not all(
                    guard.cells_valid(value) for value in expected["word_cells"]):
                raise ValueError("expected cells must be A116 integers, never Booleans")
        if (type(goal) is not dict or goal.get("kind") not in guard.GOAL_KINDS
                or type(goal.get("positive")) is not bool):
            raise ValueError("invalid goal contract")
        if goal["kind"] == "conditional_inference":
            if (type(goal.get("query")) is not str or goal.get("query_ending") not in {"wasl", "waqf"}
                    or type(goal.get("expected_status")) is not str
                    or type(goal.get("expected_chain_complete")) is not bool):
                raise ValueError("conditional goal requires exact query and chain contract")
            goal["query"].encode("utf-8", "strict")
    if dict(families) != FAMILY_COUNTS or cells != CELL_CASES:
        raise ValueError("matrix denominators differ from independent freeze")
    return gold


def source_checks(guard, acquisition, text, source_id, scope, onset, ending):
    """Independent v2 identity, exact partition, byte-offset and cell checks."""
    checks = {key: False for key in ("identity", "restoration", "intervals", "cell_domain", "words")}
    if type(acquisition) is not dict:
        return checks
    checks["identity"] = all(acquisition.get(key) == value for key, value in {
        "law_id": LAW_ID, "alphabet_id": "nabt.a116.v1", "text": text,
        "source_id": source_id, "revision": "1", "scope": scope,
        "onset": onset, "ending": ending}.items())
    pieces, words = acquisition.get("pieces"), acquisition.get("words")
    if (type(pieces) is not list or type(words) is not list or
            any(type(item) is not dict for item in pieces + words)):
        return checks
    checks["restoration"] = (all(type(p.get("raw")) is str for p in pieces)
                             and "".join(p["raw"] for p in pieces) == text)
    checks["cell_domain"] = all(guard.cells_valid(item.get("cells")) for item in pieces + words)
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))
    cursor, valid = 0, True
    for piece in pieces:
        start, end = piece.get("start"), piece.get("end")
        if (type(start) is not int or type(end) is not int or start != cursor or
                not start < end <= len(text) or piece.get("raw") != text[start:end] or
                any(type(piece.get(k)) is not int or piece[k] != v for k, v in
                    (("byte_start", offsets[start]), ("byte_end", offsets[end])))):
            valid = False
            break
        cursor = end
    checks["intervals"] = valid and cursor == len(text)
    spans, cursor = [], 0
    while cursor < len(text):
        if text[cursor] in guard.SEPARATORS:
            cursor += 1
        else:
            start = cursor
            while cursor < len(text) and text[cursor] not in guard.SEPARATORS:
                cursor += 1
            spans.append((start, cursor))
    valid = checks["intervals"] and checks["cell_domain"] and len(words) == len(spans)
    for word, (start, end) in zip(words, spans):
        members = [p for p in pieces if type(p.get("start")) is int and start <= p["start"] < end]
        valid = valid and all(type(word.get(k)) is int and word[k] == v for k, v in
            (("start", start), ("end", end), ("byte_start", offsets[start]), ("byte_end", offsets[end])))
        valid = (valid and bool(members) and members[0]["start"] == start and members[-1]["end"] == end
                 and word.get("cells") == [c for p in members for c in p.get("cells", [])])
    checks["words"] = bool(valid)
    return checks


def checked_acquisition(guard, receipt, text, identity, scope, onset, ending):
    if type(receipt) is not dict:
        raise ValueError("acquisition receipt must be an object")
    acquisition = receipt.get("acquisition")
    checks = source_checks(guard, acquisition, text, identity, scope, onset, ending)
    checks["status_consistent"] = (type(acquisition) is dict and
        acquisition.get("status") in guard.ACQUISITION_STATUSES and receipt.get("status") == acquisition["status"])
    verified = (receipt.get("schema") == "nabt.acquired-reading.v2" and receipt.get("verified") is True
                and receipt.get("authority") == "NATIVE_REPLAYED_LOCAL_REPRESENTATION")
    return {"verified": verified, "source_checks": checks,
            "status": acquisition.get("status") if verified and type(acquisition) is dict else receipt.get("status"),
            "word_cells": [w.get("cells") for w in acquisition.get("words", [])]
                          if type(acquisition) is dict else None,
            "acquired": verified and all(checks.values()) and receipt.get("status") == "ACQUIRED"}


def complete_shapes(receipt, ending):
    words = receipt.get("acquisition", {}).get("words", [])
    handoffs = receipt.get("shape_handoffs", [])
    return (bool(words) and len(words) == len(handoffs) and all(
        type(handoff.get("word_index")) is int and handoff["word_index"] == index and
        handoff.get("mode") == (ending if index == len(words) - 1 else "wasl") and
        (handoff.get("certificate") or {}).get("mode") == handoff.get("mode") and
        handoff.get("status") == "SHAPE_LICENSED" and wire(handoff.get("span")) ==
        wire({key: word[key] for key in ("start", "end", "byte_start", "byte_end")})
        for index, (word, handoff) in enumerate(zip(words, handoffs))))


def evaluate_case(guard, case, acquisition, composite):
    identity = "independent_" + digest(case["id"].encode("utf-8"))
    binding = {"source_id": identity, "revision": "1", "scope": SCOPE, "onset": case["onset"]}
    row = {"id": case["id"], "family": case["family"], "expected": case["expected"],
           "executed": False, "false_license": False, "false_chain": False, "false_support": False}
    goal = case["goal"]
    measured = {"kind": goal["kind"], "positive": goal["positive"],
                "measurement_status": "UNMEASURED", "outcome": "MISS" if goal["positive"] else "UNMEASURED"}
    try:
        raw = acquisition.read_acquired(case["text"], **binding, ending=case["ending"])
        observed = checked_acquisition(guard, raw, case["text"], identity, SCOPE, case["onset"], case["ending"])
        expected = case["expected"]
        representation = observed["status"] == expected["acquisition_status"]
        cells_match = (wire(observed["word_cells"]) == wire(expected["word_cells"])) if "word_cells" in expected else None
        row.update(executed=True, acquisition_result=raw, observed=observed,
            representation_match=representation and cells_match is not False, cells_match=cells_match,
            false_license=observed["status"] == "ACQUIRED" and expected["acquisition_status"] != "ACQUIRED")
        if goal["kind"] == "acquisition" and observed["verified"] and all(observed["source_checks"].values()):
            measured.update(measurement_status="MEASURED", outcome="SUCCESS" if observed["acquired"] == goal["positive"] else "MISS")
        elif goal["kind"] == "conditional_inference":
            cb = {**binding, "time": "unspecified", "source_ending": case["ending"], "query_ending": goal["query_ending"]}
            result = composite.evaluate(case["text"], goal["query"], **cb)
            replay = composite.verify(result, source=case["text"], query=goal["query"], **cb)
            canonical_scope = wire({"scope": SCOPE, "time": "unspecified"})
            source = checked_acquisition(guard, result.get("source_acquisition"), case["text"],
                identity, canonical_scope, case["onset"], case["ending"])
            query = checked_acquisition(guard, result.get("query_acquisition"), goal["query"],
                identity, canonical_scope, case["onset"], goal["query_ending"])
            complete = result.get("chain_complete") is True
            trusted = (result.get("schema") == "nabt.acquired-inference-result.v2" and
                       result.get("law_id") == COMPOSITE_LAW_ID and replay.get("replay_matches") is True and
                       type(result.get("chain_complete")) is bool and type(result.get("verified")) is bool and
                       result.get("world_truth_established") is False and result.get("all_arabic_complete") is False and
                       source["verified"] and query["verified"] and all(source["source_checks"].values())
                       and all(query["source_checks"].values()) and
                       result.get("binding") == {**cb, "native_scope": canonical_scope})
            licensed = result.get("licensed_inference") or {}
            native = licensed.get("native_result") or {}
            reading = (licensed.get("law_id") == "nabt.licensed-inference.v1" and
                all(licensed.get(key) is True for key in ("verified", "native_checked", "closures_checked")) and
                all(native.get(key) == value for key, value in {"source_text": case["text"],
                    "query_text": goal["query"], "source_id": identity, "revision": "1",
                    "source_scope": canonical_scope}.items()))
            complete_checked = (trusted and complete and replay.get("valid") is True and
                result.get("verified") is True and source["acquired"] and query["acquired"] and
                reading and complete_shapes(result["source_acquisition"], case["ending"]) and
                complete_shapes(result["query_acquisition"], goal["query_ending"]) and
                result.get("world_truth_established") is False and result.get("all_arabic_complete") is False)
            status = result.get("status")
            complete_checked = complete_checked and (result.get("answer") or {}).get("status") == status
            row.update(composite_result=result, composite_replay=replay,
                composite_source_checks=source, composite_query_checks=query,
                chain_complete=complete_checked, composite_verified=trusted, nested_inference_status=licensed.get("status"),
                composite_match=trusted and status == goal["expected_status"] and complete == goal["expected_chain_complete"]
                    and complete_checked == goal["expected_chain_complete"],
                false_chain=complete and (not complete_checked or not goal["expected_chain_complete"]),
                false_support=complete and status == "SUPPORTED" and goal["expected_status"] != "SUPPORTED")
            if complete_checked and status in {"SUPPORTED", "REFUTED", "UNKNOWN", "CONFLICT"}:
                measured.update(measurement_status="MEASURED", outcome="SUCCESS" if
                    ((status == "SUPPORTED") == goal["positive"] and
                     (goal["positive"] or status in {"REFUTED", "UNKNOWN"})) else "MISS")
        row["goal"] = measured
    except Exception as exc:
        row.update(error={"type": type(exc).__name__, "message": str(exc)}, goal=measured)
    return row


def counts(rows):
    positives = [row for row in rows if row["goal"]["positive"]]
    acquisitions = [row for row in positives if row["goal"]["kind"] == "acquisition"]
    conditional = [row for row in rows if row["goal"]["kind"] == "conditional_inference"]
    positive_conditional = [row for row in conditional if row["goal"]["positive"]]
    return {"denominator": len(rows), "executed": sum(row["executed"] for row in rows),
        "native_verified": sum(row.get("observed", {}).get("verified") is True for row in rows),
        "status_matches": sum(row.get("observed", {}).get("status") == row["expected"]["acquisition_status"] for row in rows),
        "representation_matches": sum(row.get("representation_match") is True for row in rows),
        "cells": {"denominator": sum("word_cells" in row["expected"] for row in rows),
                  "matches": sum(row.get("cells_match") is True for row in rows)},
        "false_licenses": sum(row["false_license"] for row in rows),
        "false_chains": sum(row["false_chain"] for row in rows),
        "false_supports": sum(row["false_support"] for row in rows),
        "positive_goal_source_acquisition": {"denominator": len(positives),
            "complete": sum(row.get("observed", {}).get("acquired") is True for row in positives)},
        "positive_acquisition_goals": {"denominator": len(acquisitions),
            "complete": sum(row.get("observed", {}).get("acquired") is True for row in acquisitions)},
        "conditional": {"denominator": len(conditional), "contract_matches": sum(row.get("composite_match") is True for row in conditional),
            "complete_chains": sum(row.get("chain_complete") is True for row in conditional),
            "positive_denominator": len(positive_conditional),
            "positive_supported_complete": sum(row.get("chain_complete") is True and
                row.get("composite_result", {}).get("status") == "SUPPORTED" for row in positive_conditional)},
        "goals": {kind: {"denominator": sum(row["goal"]["kind"] == kind for row in rows),
            "outcomes": dict(Counter(row["goal"]["outcome"] for row in rows if row["goal"]["kind"] == kind)),
            "measurement": dict(Counter(row["goal"]["measurement_status"] for row in rows if row["goal"]["kind"] == kind))}
            for kind in ("acquisition", "person", "nominal_syntax", "conditional_inference")},
        "runtime_statuses": dict(Counter(row.get("observed", {}).get("status", "EVALUATOR_FAILURE") for row in rows)),
        "shape_statuses": dict(Counter(h.get("status") for row in rows
            for h in row.get("acquisition_result", {}).get("shape_handoffs", []))),
        "resource_outcomes": {"acquisition": sum(row.get("observed", {}).get("status") == "RESOURCE_EXHAUSTED" for row in rows),
            "composite": sum(row.get("composite_result", {}).get("status") == "RESOURCE_EXHAUSTED" for row in rows)}}


def run(envelope, evidence, phase):
    guard = load_bootstrap()
    inner = envelope["baseline"]
    def snapshot():
        state = guard.snapshot(inner, ROOT / GOLD_PATH)
        manifest = Path(evidence["manifest_path"])
        state["manifest_sha256"] = digest(manifest.read_bytes()) if manifest.is_file() else None
        return state

    before = snapshot()
    mismatches = [name for hashes in (inner["files"], inner["native"]) for name, value in hashes.items()
                  if before["files"].get(name) != value]
    if before["gold_sha256"] != GOLD_SHA256:
        mismatches.append("v2 gold")
    if phase == "first" and before["head"] != inner["commit"]:
        mismatches.append("v2 first-run HEAD")
    if (before["manifest_sha256"] != evidence["manifest_sha256"] or
            digest(wire(envelope).encode("utf-8")) != evidence["canonical_manifest_sha256"]):
        mismatches.append("v2 freeze envelope")
    if mismatches:
        raise ValueError("initial snapshot differs from validated freeze: " + ", ".join(sorted(set(mismatches))))
    gold = load_gold(guard)
    with guard.frozen_runtime(inner) as imports:
        acquisition = importlib.import_module("tools.aligned_acquisition_v2")
        composite = importlib.import_module("tools.acquired_inference_v2")
        rows = [evaluate_case(guard, case, acquisition, composite) for case in gold["cases"]]
        after = snapshot()
        loaded = {}
        for module in tuple(sys.modules.values()):
            name = getattr(module, "__file__", None)
            if name:
                path = Path(name).resolve()
                if path.suffix == ".py" and path.is_relative_to(ROOT):
                    loaded[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    uncovered = sorted(set(loaded) - set(inner["files"]))
    wrong = sorted(name for name, value in loaded.items() if inner["files"].get(name) != value)
    integrity = before == after and not uncovered and not wrong and evidence["baseline"]["native_matches_freeze"]
    unsafe = [row["id"] for row in rows if row["false_license"] or row["false_chain"] or row["false_support"] or "error" in row
        or row.get("observed", {}).get("verified") is not True
        or (row["goal"]["kind"] == "conditional_inference" and row.get("composite_verified") is not True)
        or not all(row.get("observed", {}).get("source_checks", {"missing": False}).values())]
    safety = bool(rows) and integrity and not unsafe
    representation = safety and all(row.get("representation_match") is True for row in rows)
    composite_match = safety and all(row.get("composite_match") is True for row in rows
                                    if row["goal"]["kind"] == "conditional_inference")
    return {"schema": RESULT_SCHEMA, "phase": phase, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Finite independent matrix; local word-initial representation and existing PR34 consequence, not general Arabic or connected pronunciation.",
        "summary": counts(rows), "families": {family: counts([r for r in rows if r["family"] == family]) for family in sorted(FAMILY_COUNTS)},
        "execution_evidence": {**evidence, "before": before, "after": after, "integrity_valid": integrity,
            "initial_snapshot_matches_freeze": True, "runtime_import_policy": "fresh-frozen-source-only.v1",
            "executed_repository_python": imports.executed, "loaded_repository_python": loaded,
            "uncovered_modules": uncovered, "loaded_hash_mismatches": wrong},
        "contract_gate": {"passed": safety, "failures": unsafe},
        "representation_gate": {"passed": representation}, "composite_gate": {"passed": composite_match}, "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-freeze", type=Path, required=True)
    parser.add_argument("--phase", choices=("first", "exposed"), required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve and fsync an attempt BEFORE bootstrap/provenance validation.
    with args.output.open("x", encoding="utf-8") as output:
        report = {"schema": RESULT_SCHEMA, "phase": args.phase, "status": "ATTEMPT_STARTED",
                  "started_at_utc": datetime.now(timezone.utc).isoformat(), "gold_sha256": GOLD_SHA256}
        output.write(wire(report) + "\n")
        output.flush()
        os.fsync(output.fileno())
        stage = "preflight"
        try:
            envelope, evidence = verify_freeze(args.code_freeze, args.phase)
            stage = "execution"
            report = run(envelope, evidence, args.phase)
        except Exception as exc:
            report = {**report, "status": "EVALUATOR_FAILURE", "failure_stage": stage,
                      "error": {"type": type(exc).__name__, "message": str(exc)}}
        output.seek(0)
        json.dump(report, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        output.truncate()
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps({key: value for key, value in report.items() if key in
        {"summary", "contract_gate", "representation_gate", "composite_gate", "status", "error", "failure_stage"}}, ensure_ascii=False))
    return 0 if all(report.get(key, {}).get("passed") for key in
                    ("contract_gate", "representation_gate", "composite_gate")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
