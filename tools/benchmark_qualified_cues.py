"""Measure frozen, independently authored cue cases without granting proof authority.

The runtime receives only text and declared context. Positive acquisition, safe
abstention, scope comprehension, numeric projection and native execution have
separate denominators. In particular, rejecting a quotation safely does not
pass the quoted speaker's positive meaning target.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.benchmark_certified_natural_use import (  # noqa: E402
    _arguments, _observed_senses, _proof_claims, _source_ok, _target_occurrences,
)

CORPUS = ROOT / "evidence/qualified_cue_licensing_v1/independent_cases.json"
CORPUS_SHA256 = "ae10bce75024763f9e751dcc8af1ea090124d1fbac93d09e002e1ea2cd78fb68"
SCHEMA = "nabt.qualified-cue-licensing.benchmark.v1"
_UNAVAILABLE = {"VERIFICATION_UNAVAILABLE", "SOURCE_UNAVAILABLE", "RESOURCE_EXHAUSTED", "ERROR"}
_PROMOTION_KEYS = {"world_truth_established", "motive_established", "all_arabic_complete",
                   "whole_arabic_complete", "universal_arabic_completeness", "strict_language_accepted"}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY:" + key)
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError("NONFINITE_JSON_NUMBER:" + value)


def load_cases():
    raw = CORPUS.read_bytes()
    if _sha(raw) != CORPUS_SHA256:
        raise ValueError("INDEPENDENT_CORPUS_IDENTITY_CHANGED")
    corpus = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_nonfinite)
    cases = corpus["cases"]
    if len(cases) != 24 or len({case["id"] for case in cases}) != 24:
        raise ValueError("INDEPENDENT_CORPUS_POPULATION_CHANGED")
    for path, expected in corpus["historical_gold_sha256"].items():
        if _sha((ROOT / path).read_bytes()) != expected:
            raise ValueError("HISTORICAL_GOLD_CHANGED:" + path)
    for case in cases:
        source = case["input"]["text"].encode("utf-8", "strict")
        target = case["target"]
        start, end = target["start_byte"], target["end_byte"]
        if (type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(source)
                or source[start:end] != target["surface"].encode("utf-8", "strict")
                or _sha(source[start:end]) != target["sha256"]):
            raise ValueError("INVALID_TARGET_IDENTITY:" + case["id"])
    return cases


def _check(name, actual, expected, *, measured=True):
    equal = type(actual) is type(expected) and actual == expected
    return {"name": name, "actual": actual, "expected": expected,
            "outcome": ("PASS" if equal else "FAIL") if measured else "UNMEASURED"}


def _axis(checks, *, eligible=True):
    statuses = {check["outcome"] for check in checks}
    outcome = ("NOT_ELIGIBLE" if not eligible else "FAIL" if "FAIL" in statuses
               else "UNMEASURED" if "UNMEASURED" in statuses or not checks else "PASS")
    return {"eligible": eligible, "outcome": outcome, "checks": checks if eligible else []}


def _declarations(value):
    """Inspect explicit declarations; absence means no promotion, not world truth."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _PROMOTION_KEYS:
                yield key, child
            yield from _declarations(child)
    elif isinstance(value, list):
        for child in value:
            yield from _declarations(child)


def _context_ok(case, matches):
    context = _arguments(case)
    return bool(matches) and all(
        row["frame"]["occurrence"].get("source") == context["source_id"]
        and row["frame"]["occurrence"].get("referent") == context["subject"]
        and row["frame"]["occurrence"].get("context") == context["context"]
        for row in matches)


def _scope_checks(expected, matches):
    # These fields must be acquired by a scope adapter, never invented from gold
    # or from a source/context hash by this evaluator.
    checks = []
    for actual_key, expected_key in (
            ("acquired_scope", "scope"), ("scope_stack", "scope_stack"),
            ("semantic_owner", "semantic_owner"),
            ("local_declared_senses", "local_declared_senses")):
        present = bool(matches) and all(actual_key in row for row in matches)
        values = [row.get(actual_key) for row in matches]
        if actual_key == "local_declared_senses":
            correct = present and all(isinstance(v, list) and all(isinstance(x, str) for x in v)
                and len(v) == len(set(v)) and sorted(v) == sorted(expected[expected_key]) for v in values)
        else:
            correct = present and all(type(v) is type(expected[expected_key])
                                     and v == expected[expected_key] for v in values)
        checks.append(_check(actual_key, correct, True, measured=present))
    return checks


def evaluate(case, report):
    """Score a receipt's declarations; this never authenticates imported execution."""
    diagnostic = report.get("diagnostic", {})
    expected = case["expected"]
    matches = _target_occurrences(case, diagnostic)
    candidates, selected, excluded, unmapped = _observed_senses(matches)
    source_ok = _source_ok(case, diagnostic)
    context_ok = _context_ok(case, matches)
    identity_ok = source_ok and context_ok
    semantic = expected["semantic_acquisition_eligible"]
    required = expected["required_candidates"]
    positive = bool(expected["selected_senses"]) and semantic
    direct = expected["qualified_frame"] == "direct_licensed"
    mismatch = expected["qualified_frame"] == "marked_frame_mismatch"
    named_proof_ok, named_count = _proof_claims(report)
    axes = {
        "source_identity": _axis([_check("exact_source_identity", source_ok, True)]),
        "target_occurrence": _axis([
            _check("exact_target_and_declared_context", identity_ok, True)], eligible=bool(required)),
        "candidate_recall": _axis([
            _check("source_and_occurrence_bound", identity_ok, True),
            _check("required_candidates_retained", set(required).issubset(candidates), True)
        ], eligible=bool(required)),
        "diagnostic_positive_selection": _axis([
            _check("source_and_occurrence_bound", identity_ok, True),
            _check("selected_senses", sorted(selected), sorted(expected["selected_senses"]))
        ], eligible=positive),
        "explicit_negative_exclusion": _axis([
            _check("source_and_occurrence_bound", identity_ok, True),
            _check("excluded_senses", sorted(excluded), sorted(expected["excluded_senses"])),
            _check("no_unstated_positive_complement", sorted(selected), sorted(expected["selected_senses"]))
        ], eligible=bool(expected["excluded_senses"])),
        "safe_nonselection": _axis([
            _check("source_identity", source_ok, True),
            _check("no_positive_selection", sorted(selected), [])
        ], eligible=semantic and not positive),
        "scope_comprehension": _axis(_scope_checks(expected, matches), eligible=semantic),
        "direct_frame_licensing": _axis([
            _check("source_and_occurrence_bound", identity_ok, True),
            _check("complete_cue_acquired", bool(matches) and all(
                bool(row.get("cue_readings")) and row.get("intended_sense_acquired") is True
                for row in matches), True)
        ], eligible=direct),
        "marked_frame_guard": _axis([
            _check("source_identity", source_ok, True),
            _check("no_selected_meaning", sorted(selected), []),
            _check("no_excluded_meaning", sorted(excluded), []),
            _check("no_intended_use_acquired", any(
                row.get("intended_sense_acquired") is True or bool(row.get("cue_readings"))
                for row in matches), False)
        ], eligible=mismatch),
        "no_unsupported_promotion": _axis([
            _check("explicit_promotion_declarations", all(
                value is False for _, value in _declarations(report)), True)
        ]),
        "named_proof_binding_consistency": _axis([
            _check("named_claims_bound_to_native_request", named_proof_ok, True)
        ]),
        "execution_available": _axis([
            _check("no_resource_or_verification_failure", isinstance(report.get("status"), str)
                   and bool(report["status"]) and report["status"] not in _UNAVAILABLE, True)
        ]),
    }
    # This safety axis intentionally does not count absence as scope understanding.
    # A positive selection without an acquired non-current scope remains attributed
    # to the input frame's speaker; metadata in the *request* cannot fix that.
    noncurrent = semantic and expected["scope"] != "current_speaker_asserted"
    current = set()
    for row in matches:
        _, row_selected, _, _ = _observed_senses([row])
        if "current_speaker_selected_senses" in row:
            supplied = row["current_speaker_selected_senses"]
            if isinstance(supplied, list) and all(isinstance(x, str) for x in supplied):
                current.update(supplied)
            else:
                current.add("INVALID_CURRENT_SPEAKER_DECLARATION")
        elif (row.get("acquired_scope") != "quoted_speaker"
              or not isinstance(row.get("semantic_owner"), str)
              or row["semantic_owner"] == case["input"]["context"]["speaker_id"]):
            current.update(row_selected)
    axes["no_current_speaker_leakage"] = _axis([
        _check("current_speaker_selected_senses", sorted(current),
               sorted(expected["current_speaker_selected_senses"]))], eligible=noncurrent)
    candidate_rows = [row for row in diagnostic.get("occurrences", []) if row.get("candidates")]
    native_rows = report.get("occurrences", [])
    native_by_id = {row.get("occurrence_id"): row for row in native_rows}
    all_native = (report.get("native_checked") is True
        and len(native_by_id) == len(native_rows) and bool(candidate_rows)
        and all(native_by_id.get(row.get("occurrence_id"), {}).get("native_checked") is True
                and bool(native_by_id.get(row.get("occurrence_id"), {}).get("native_receipt"))
                for row in candidate_rows))
    axes["declared_native_execution"] = _axis([
        _check("all_candidate_occurrences_checked", all_native, True)], eligible=bool(candidate_rows))
    projection = report.get("foundation_source", {}).get("status")
    axes["complete_a116_projection"] = _axis([
        _check("projection_status", projection, "COMPLETE", measured=projection is not None)])
    return {"id": case["id"], "family": case["family"], "axes": axes,
            "observation": {"status": diagnostic.get("status"), "wrapper_status": report.get("status"),
                "matched_occurrence_ids": [row.get("occurrence_id") for row in matches],
                "candidates": sorted(candidates), "selected": sorted(selected), "excluded": sorted(excluded),
                "unmapped": sorted(unmapped), "projection_status": projection,
                "native_checked": report.get("native_checked"),
                "strict_language_accepted": report.get("strict_language_accepted"),
                "consistent_named_claim_count": named_count,
                "residuals": report.get("residuals", [])},
            "executed_locally": False,
            "interpretation": "DIAGNOSTIC_AND_BINDING_CHECKS_ONLY_NOT_IMPORTED_PROOF_AUTHORITY"}


def summarize(rows):
    names = sorted({name for row in rows for name in row["axes"]})
    axes = {}
    for name in names:
        values = [row["axes"][name] for row in rows if row["axes"][name]["eligible"]]
        counts = Counter(value["outcome"] for value in values)
        measured = counts["PASS"] + counts["FAIL"]
        axes[name] = {"eligible": len(values), "measured": measured, "passed": counts["PASS"],
                      "failed": counts["FAIL"], "unmeasured": counts["UNMEASURED"],
                      "fraction": counts["PASS"] / measured if measured else None}
    return {"cases": len(rows), "axes": axes,
            "locally_executed_cases": sum(row["executed_locally"] is True for row in rows),
            "strict_language_acceptances": sum(row["observation"]["strict_language_accepted"] is True for row in rows),
            "motive_assessment": "UNMEASURED", "world_truth_assessment": "UNMEASURED",
            "tawatur_assessment": "UNMEASURED", "all_arabic_complete": False,
            "interpretation": "Separate diagnostic denominators; no overall Arabic accuracy or completeness score."}


def run():
    cases = load_cases()
    from tools.linguistic_truth.certified import acquire_certified
    from tools.benchmark_linguistic_truth import evidence_snapshot, integrity_check
    for name in ("tools.linguistic_truth.inventory", "tools.linguistic_truth.sources",
                 "tools.linguistic_truth.pipeline", "tools.linguistic_truth.correction",
                 "tools.linguistic_truth.marked_forms", "nabt.codec", "nabt.machine"):
        importlib.import_module(name)
    before_evidence = evidence_snapshot()
    before_evidence["input_files"][str(CORPUS.relative_to(ROOT))] = _sha(CORPUS.read_bytes())
    rows = []
    for case in cases:
        # Only the original input crosses this boundary. Utterance IDs bind
        # receipts; no gold field, target span or frame license is supplied.
        receipt = acquire_certified(case["input"]["text"], **_arguments(case))
        row = evaluate(case, receipt)
        row["executed_locally"] = True
        row["receipt"] = receipt
        rows.append(row)
    after_evidence = evidence_snapshot()
    after_evidence["input_files"][str(CORPUS.relative_to(ROOT))] = _sha(CORPUS.read_bytes())
    integrity = integrity_check(before_evidence, after_evidence)
    safety_axes = ("source_identity", "no_unsupported_promotion",
                   "named_proof_binding_consistency", "execution_available", "declared_native_execution",
                   "no_current_speaker_leakage", "marked_frame_guard", "safe_nonselection")
    return {"schema": SCHEMA, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
            "gold_sha256": CORPUS_SHA256, "execution": "ACTUAL_LOCAL_ACQUIRE_CERTIFIED_CALLS",
            "evaluation_role": "AUTHORED_DIAGNOSTIC_NOT_BLIND_EXTERNAL_OR_POPULATION_ACCURACY",
            "rows": rows, "summary": summarize(rows),
            "execution_evidence": {"before": before_evidence, "after": after_evidence, "integrity": integrity},
            "safety_gate_passed": integrity["valid"] and all(row["axes"][axis]["outcome"] in {"PASS", "NOT_ELIGIBLE"}
                                      for row in rows for axis in safety_axes),
            "native_acquisition_refinement_proved": False, "all_arabic_complete": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == ".gz" else raw)
    print(json.dumps({"summary": result["summary"], "safety_gate_passed": result["safety_gate_passed"]}, ensure_ascii=False))
    return 0 if result["safety_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
