"""Replay independently authored diagnostics without feeding targets to acquisition.

A semantic diagnostic success, a native-checked conditional claim, and a strict
Arabic acceptance are three separate measurements. This runner never upgrades
an imported receipt to a locally executed proof and never combines occurrences
by a stripped word. The old 44-case benchmark and its denominator are unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
CORPUS = ROOT / "evidence/certified_natural_use_v1/independent_cases.json"
CONTROLS = ROOT / "evidence/certified_natural_use_v1/projection_controls.json"
CORPUS_SHA256 = "d2fcae08a163bf017184a42638a02901d1331704ee0dca4881b880215fb095f3"
CONTROLS_SHA256 = "73e1b414a8a24da6e4d83e6b469d6e812db656612a925f3fd9c8befe44aaa0ce"
SCHEMA = "nabt.certified-natural-use.benchmark.v1"
ALIASES = {
    "الحيوان المفترس": "lion", "حيوان مفترس": "lion", "السبع المعروف": "lion",
    "الأسد الحيوان": "lion", "الرجل الشجاع": "brave_man", "رجل شجاع": "brave_man",
    "الشجاع": "brave_man", "العين الباصرة": "eye", "الباصرة": "eye",
    "عضو الإبصار": "eye", "عين الماء": "spring", "عين الماء الجارية": "spring",
    "العين الجارية": "spring", "الماء النابع": "spring", "الذهب": "gold",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _load(path, expected):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError("INDEPENDENT_CORPUS_IDENTITY_CHANGED")
    result = json.loads(raw)
    if len({case["id"] for case in result["cases"]}) != len(result["cases"]):
        raise ValueError("DUPLICATE_CASE_ID")
    for case in result["cases"]:
        target = case.get("target")
        if target:
            raw_text = case["input"]["text"].encode("utf-8")
            start, end = target["start_byte"], target["end_byte"]
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw_text)
                    or raw_text[start:end] != target["surface"].encode("utf-8")
                    or sha(raw_text[start:end]) != target["sha256"]):
                raise ValueError("INVALID_TARGET_IDENTITY")
    return result


def load_cases():
    return _load(CORPUS, CORPUS_SHA256)["cases"], _load(CONTROLS, CONTROLS_SHA256)["cases"]


def _check(name, actual, expected, *, measured=True):
    return {"name": name, "actual": actual, "expected": expected,
            "outcome": ("PASS" if type(actual) is type(expected) and actual == expected else "FAIL")
            if measured else "UNMEASURED"}


def _outcome(checks):
    statuses = {check["outcome"] for check in checks}
    return "FAIL" if "FAIL" in statuses else "UNMEASURED" if "UNMEASURED" in statuses else "PASS"


def _ratio(n, d):
    return {"numerator": n, "denominator": d, "fraction": n / d if d else None}


def _arguments(case):
    context = case["input"]["context"]
    return {"profile_id": case["input"]["profile_id"],
            "source_id": context["utterance_id"], "subject": context["speaker_id"],
            "context": canonical(context)}


def _source_ok(case, diagnostic):
    raw = case["input"]["text"].encode("utf-8")
    source = diagnostic.get("source", {})
    return (source.get("source_id") == case["input"]["context"]["utterance_id"]
            and source.get("raw_text") == case["input"]["text"]
            and type(source.get("bytes")) is int and source["bytes"] == len(raw)
            and source.get("sha256") == sha(raw))


def _target_occurrences(case, diagnostic):
    """No lemma normalization: exact original spans must agree in both records."""
    target = case.get("target")
    if target is None:
        raw = case["input"]["text"].encode("utf-8")
        target = {"start_byte": 0, "end_byte": len(raw), "raw_text": case["input"]["text"]}
    start, end = target["start_byte"], target["end_byte"]
    text = case["input"]["text"]
    raw = text.encode("utf-8")
    matches = []
    for occurrence in diagnostic.get("occurrences", []):
        span = occurrence.get("span", {})
        frame = occurrence.get("frame", {}).get("occurrence", {})
        if (type(span.get("start_byte")) is int and type(span.get("end_byte")) is int
                and span["start_byte"] == start and span["end_byte"] == end
                and span.get("raw_text") == raw[start:end].decode("utf-8")
                and span.get("sha256") == sha(raw[start:end])
                and type(frame.get("start_byte")) is int and type(frame.get("end_byte")) is int
                and frame["start_byte"] == start and frame["end_byte"] == end
                and frame.get("raw") == text and frame.get("revision") == sha(raw)):
            matches.append(occurrence)
    return matches


def _observed_senses(matches):
    candidates, selected, excluded, unmapped = set(), set(), set(), set()
    for occurrence in matches:
        names = {}
        for candidate in occurrence.get("candidates", []):
            label = ALIASES.get(candidate.get("gloss"))
            if label is None:
                label = "UNMAPPED:" + str(candidate.get("sense_id"))
                unmapped.add(label)
            names[str(candidate.get("sense_id"))] = label
            candidates.add(label)
        for key, result in (("selected_sense_ids", selected), ("excluded_sense_ids", excluded)):
            for identifier in occurrence.get(key, []):
                result.add(names.get(str(identifier), "UNMAPPED:" + str(identifier)))
    return candidates, selected, excluded, unmapped


def _same(left, right):
    return canonical(left) == canonical(right)


def _proof_claims(report):
    """Check binding consistency only; imported evidence is never executed here."""
    projection = report.get("foundation_source", {})
    diagnostic = report.get("diagnostic", {})
    diagnostic_rows, native_rows = diagnostic.get("occurrences", []), report.get("occurrences", [])
    occurrences = {row.get("occurrence_id"): row for row in diagnostic_rows}
    combined = {row.get("occurrence_id"): row for row in native_rows}
    if len(occurrences) != len(diagnostic_rows) or len(combined) != len(native_rows):
        return False, 0
    checked = 0
    seen_claims = set()
    for claim in report.get("claims", []):
        binding = claim.get("binding", {})
        frame = binding.get("frame", {})
        identity = (claim.get("kind"), binding.get("request_sha256"))
        if identity in seen_claims:
            return False, checked
        seen_claims.add(identity)
        matches = [row for row in occurrences.values() if _same(row.get("frame"), frame)]
        if len(matches) != 1:
            return False, checked
        occurrence = matches[0]
        item = combined.get(occurrence.get("occurrence_id"), {})
        receipt = item.get("native_receipt", {})
        request = {"op": "certify_a116", "source": projection.get("source"),
                   "cells": projection.get("cells"), "request": occurrence.get("native_request")}
        if not (report.get("native_checked") is True and item.get("native_checked") is True
                and claim.get("authority") == "KERNEL_CHECKED_CONDITIONAL"
                and claim.get("proof", {}).get("kind") == "NATIVE_LEAN_RECEIPT"
                and claim.get("proof", {}).get("law_id") == "nabt.certified-lexical.v1"
                and claim.get("kind") in {"A116_EXACT_INSTALLED_CANDIDATE_SET", "A116_CONDITIONAL_SUPPORTED_USE"}
                and _same(binding.get("source"), projection.get("source"))
                and _same(projection.get("source"), receipt.get("source"))
                and projection.get("status") == receipt.get("projection_status") == "COMPLETE"
                and bool(projection.get("cells"))
                and _same(receipt.get("cells"), projection.get("cells"))
                and receipt.get("source_bound") is True and receipt.get("cells_exact") is True
                and receipt.get("candidate_set_checked") is True
                and binding.get("request_sha256") == item.get("request_sha256") == sha(canonical(request).encode())
                and binding.get("response_sha256") == item.get("response_sha256") == sha(canonical(receipt).encode())):
            return False, checked
        if claim["kind"] == "A116_CONDITIONAL_SUPPORTED_USE" and not (
                receipt.get("certified_from_a116") is True
                and bool(claim.get("accepted_candidates"))
                and _same(claim["accepted_candidates"], receipt.get("accepted_candidates"))):
            return False, checked
        if claim["kind"] == "A116_EXACT_INSTALLED_CANDIDATE_SET" and not (
                type(claim.get("candidate_count")) is int and claim["candidate_count"] > 0
                and claim["candidate_count"] == len(request["request"]["proposed"])):
            return False, checked
        checked += 1
    return True, checked


def evaluate(case, report, *, projection_control=False):
    """Score execution output; this function does not authenticate imported proof."""
    diagnostic = report.get("diagnostic", {})
    expected = case["expected"]
    matches = _target_occurrences(case, diagnostic)
    candidates, selected, excluded, unmapped = _observed_senses(matches)
    integrity = [_check("source_identity", _source_ok(case, diagnostic), True)]
    context = _arguments(case)
    context_ok = bool(matches) and all(
        o["frame"]["occurrence"].get("source") == context["source_id"]
        and o["frame"]["occurrence"].get("referent") == context["subject"]
        and o["frame"]["occurrence"].get("context") == context["context"] for o in matches)
    # A wrapper can safely defer a reading yet still return an exact source.
    authority = [_check("strict_language_not_claimed", report.get("strict_language_accepted"), False),
                 _check("world_truth_not_claimed", diagnostic.get("world_truth_established"), False),
                 _check("all_arabic_not_claimed", diagnostic.get("all_arabic_complete"), False)]
    # Absence is no positive assertion, not evidence that motives were measured.
    declarations = [obj[key] for obj in (report, diagnostic)
                    for key in ("world_truth_established", "all_arabic_complete", "motive_established")
                    if key in obj]
    authority.append(_check("no_contradictory_outer_authority", all(value is False for value in declarations), True))
    if "lexical_surface_licensed" in report:
        authority.append(_check("surface_mapping_not_claimed", report["lexical_surface_licensed"], False))
    binding_ok, bounded_claim_count = _proof_claims(report)
    authority.append(_check("named_proof_binding_consistency", binding_ok, True))
    checks = []
    if expected.get("well_formed_marks") is False:
        checks.append(_check("malformed_source_rejected", diagnostic.get("status"), "INVALID_INPUT"))
        checks.append(_check("no_selected_meaning", sorted(selected), []))
    else:
        checks.append(_check("exact_target_occurrence", bool(matches), True))
        checks.append(_check("target_context_identity", context_ok, True))
        for sense in expected["required_candidates"]:
            checks.append(_check("candidate_recall." + sense, sense in candidates, True))
        checks.append(_check("selected_senses", sorted(selected), sorted(expected["selected_senses"])))
        for sense in expected.get("excluded_senses", []):
            checks.append(_check("excluded_sense." + sense, sense in excluded, True))
        if expected.get("scope") in {"quoted_speaker", "hypothetical", "negated_embedding"}:
            # A source/context hash is not an acquired quotation/condition scope.
            observed_scopes = {o.get("acquired_scope") for o in matches if "acquired_scope" in o}
            measured = bool(observed_scopes)
            checks.append(_check("acquired_scope", sorted(observed_scopes), [expected["scope"]], measured=measured))
    if projection_control:
        checks.append(_check("source_projection", report.get("foundation_source", {}).get("status"), "COMPLETE"))
        checks.append(_check("a116_candidate_set_native_checked", binding_ok and bounded_claim_count > 0, True))
    candidate_occurrences = [row for row in diagnostic.get("occurrences", []) if row.get("candidates")]
    native_required = bool(candidate_occurrences) or projection_control
    native_rows = report.get("occurrences", [])
    native_by_id = {row.get("occurrence_id"): row for row in native_rows}
    executed_candidates = (report.get("native_checked") is True
        and len(native_by_id) == len(native_rows)
        and bool(candidate_occurrences)
        and all(native_by_id.get(row.get("occurrence_id"), {}).get("native_checked") is True
                and bool(native_by_id.get(row.get("occurrence_id"), {}).get("native_receipt"))
                for row in candidate_occurrences))
    execution = [_check("no_runtime_verification_error", report.get("status") not in {
        "VERIFICATION_UNAVAILABLE", "SOURCE_UNAVAILABLE", "RESOURCE_EXHAUSTED", "ERROR"}, True)]
    if native_required:
        execution.append(_check("all_candidate_occurrences_native_checked", executed_candidates, True))
    if projection_control:
        execution.append(_check("a116_candidate_set_checked", report.get("candidate_set_checked"), True))
        execution.append(_check("a116_candidate_proof_present", binding_ok and bounded_claim_count > 0, True))
        execution.append(_check("no_intent_asserted_by_enumeration", sorted(selected), []))
    return {"id": case["id"], "family": case.get("family", "projection_controls"),
            "semantic_diagnostic": _outcome(checks), "checks": checks,
            "integrity": {"outcome": _outcome(integrity), "checks": integrity},
            "authority": {"outcome": _outcome(authority), "checks": authority},
            "execution": {"outcome": _outcome(execution), "checks": execution, "native_required": native_required},
            "observation": {"status": diagnostic.get("status"), "wrapper_status": report.get("status"),
                            "projection_status": report.get("foundation_source", {}).get("status"),
                            "matched_occurrence_ids": [o.get("occurrence_id") for o in matches],
                            "candidates": sorted(candidates), "selected": sorted(selected),
                            "excluded": sorted(excluded), "unmapped": sorted(unmapped),
                            "native_checked": report.get("native_checked"),
                            "strict_language_accepted": report.get("strict_language_accepted"),
                            "conditional_claims": report.get("claims", []),
                            "consistent_named_claim_count": bounded_claim_count,
                            "motive_assessment": "UNMEASURED",
                            "residuals": report.get("residuals", [])},
            "executed_locally": False,
            "proof_interpretation": "Consistency measurement only; execution is established separately by run(), and no imported status grants proof authority."}


def summarize(rows):
    total = len(rows)
    positive = [r for r in rows if any(c["name"] == "selected_senses" and c["expected"] for c in r["checks"])]
    selections = [c for r in positive for c in r["checks"] if c["name"] == "selected_senses"]
    return {"cases": total, "semantic_diagnostic_outcomes": dict(Counter(r["semantic_diagnostic"] for r in rows)),
            "positive_selection": _ratio(sum(c["outcome"] == "PASS" for c in selections), len(selections)),
            "positive_case_with_scope": _ratio(sum(r["semantic_diagnostic"] == "PASS" for r in positive), len(positive)),
            "source_identity": _ratio(sum(r["integrity"]["outcome"] == "PASS" for r in rows), total),
            "authority_safety": _ratio(sum(r["authority"]["outcome"] == "PASS" for r in rows), total),
            "required_native_execution": _ratio(sum(r["execution"]["outcome"] == "PASS" for r in rows), total),
            "declared_native_checked_cases": _ratio(sum(r["observation"]["native_checked"] is True for r in rows), total),
            "native_receipt_cases": _ratio(sum(r.get("executed_locally") is True and r["observation"]["native_checked"] is True for r in rows), total),
            "strict_language_acceptances": sum(r["observation"]["strict_language_accepted"] is True for r in rows),
            "consistent_named_claims": sum(r["observation"]["consistent_named_claim_count"] for r in rows),
            "locally_executed_named_claims": sum(r["observation"]["consistent_named_claim_count"]
                                                 for r in rows if r.get("executed_locally") is True),
            "families": {family: dict(Counter(r["semantic_diagnostic"] for r in rows if r["family"] == family))
                         for family in sorted({r["family"] for r in rows})},
            "motive_assessment": "UNMEASURED",
            "interpretation": "Native receipts and safe deferrals do not count as successful positive language understanding."}


def run():
    cases, controls = load_cases()
    from tools.linguistic_truth.certified import acquire_certified
    from tools.benchmark_linguistic_truth import evidence_snapshot, integrity_check
    import importlib
    for name in ("tools.linguistic_truth.inventory", "tools.linguistic_truth.sources",
                 "tools.linguistic_truth.pipeline", "tools.linguistic_truth.correction",
                 "tools.linguistic_truth.marked_forms", "nabt.codec", "nabt.machine"):
        importlib.import_module(name)
    before_evidence = evidence_snapshot()
    before_evidence["input_files"].update({
        str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in (CORPUS, CONTROLS)})
    rows, control_rows = [], []
    for group, destination, is_control in ((cases, rows, False), (controls, control_rows, True)):
        for case in group:
            # Only original text and explicitly declared context cross this boundary.
            output = acquire_certified(case["input"]["text"], **_arguments(case))
            row = evaluate(case, output, projection_control=is_control)
            row["executed_locally"] = True
            row["receipt"] = output
            destination.append(row)
    after_evidence = evidence_snapshot()
    after_evidence["input_files"].update({
        str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in (CORPUS, CONTROLS)})
    integrity = integrity_check(before_evidence, after_evidence)
    return {"schema": SCHEMA, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
            "execution": "ACTUAL_LOCAL_ACQUIRE_CERTIFIED_CALLS", "gold_sha256": CORPUS_SHA256,
            "projection_controls_sha256": CONTROLS_SHA256,
            "evaluation_role": "AUTHORED_DIAGNOSTIC_NOT_BLIND_POPULATION_ACCURACY",
            "rows": rows, "summary": summarize(rows), "projection_control_rows": control_rows,
            "projection_control_summary": summarize(control_rows), "all_arabic_complete": False,
            "tawatur_evaluated": False, "native_acquisition_refinement_proved": False,
            "execution_evidence": {"before": before_evidence, "after": after_evidence, "integrity": integrity},
            "safety_gate_passed": integrity["valid"] and all(row[axis]["outcome"] == "PASS"
                                      for row in rows + control_rows for axis in ("integrity", "authority", "execution"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == ".gz" else raw)
    print(json.dumps({"summary": result["summary"], "projection_control_summary": result["projection_control_summary"],
                      "safety_gate_passed": result["safety_gate_passed"]}, ensure_ascii=False))
    return 0 if result["safety_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
