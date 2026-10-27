"""Replay the frozen design-aware reviewer matrix without modifying its oracle.

Run from the repository root with PYTHONPATH=src:. and an unused --output.
This is an independent finite development reference, not blind validation or
proof of linguistic completeness. Native boundary and diagnostic sense results
are measured separately. No failed run or case is overwritten.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def check_case(case, result, forbidden):
    provided, expected = case["provided"], case["expected"]
    failures = []
    def check(ok, message):
        if not ok:
            failures.append(message)
    check(type(result) is dict, "result_not_object")
    if type(result) is not dict:
        return {"boundary_checks_passed": False, "failures": failures}
    raw = provided["text"].encode("utf-8")
    revision = sha256(raw).hexdigest()
    request = {"source": {"id": provided["source_id"], "revision": revision,
                          "text": provided["text"]}, "context": provided["context"]}
    for name in forbidden:
        check(result.get(name) is not True, "forbidden_top_level_promotion:" + name)
    check(result.get("strict_language_accepted") is False, "strict_acceptance_not_explicitly_false")
    claims = result.get("claims")
    if expected["boundary_acquired"]:
        check(result.get("status") == "CHECKED_DISCOURSE_BOUNDARY", "positive_boundary_not_acquired")
        check(result.get("native_checked") is True, "positive_boundary_not_native_checked")
        envelope = result.get("envelope") or {}
        native = result.get("native_receipt") or {}
        check(result.get("source") == request["source"], "parent_source_mismatch")
        check(result.get("context") == provided["context"], "parent_context_mismatch")
        check(native.get("source") == request["source"], "native_source_mismatch")
        check(native.get("context") == provided["context"], "native_context_mismatch")
        check(type(native.get("licensed_envelope_count")) is int
              and native.get("licensed_envelope_count") == 1, "native_envelope_count")
        for name in forbidden:
            check(native.get(name) is not True, "forbidden_native_promotion:" + name)
        mapping = {"denied_body": "denied_text", "cue_body": "body_text",
                   "conjunction": "conjunction_text", "cue_text": "cue_text",
                   "denied_start_byte": "denied_start_byte", "denied_end_byte": "denied_end_byte",
                   "cue_start_byte": "cue_start_byte", "cue_end_byte": "cue_end_byte"}
        for actual, oracle in mapping.items():
            check(type(envelope.get(actual)) is type(expected[oracle])
                  and envelope.get(actual) == expected[oracle], "exact_envelope:" + actual)
        check(native.get("envelope") == envelope, "native_envelope_mismatch")
        check(envelope.get("projects_denied_to_positive") is False, "denial_scope_promoted")
        for prefix, text_key in (("denied", "denied_text"), ("cue", "cue_text"),
                                 ("conjunction", "conjunction_text"), ("cue_body", "body_text")):
            start, end = expected[prefix + "_start_byte"], expected[prefix + "_end_byte"]
            check(raw[start:end] == expected[text_key].encode("utf-8"), "oracle_span_consistency:" + prefix)
        check(type(claims) is list and len(claims) == 1, "positive_claim_count")
        if type(claims) is list and len(claims) == 1:
            claim = claims[0]
            check(claim.get("kind") == "EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE", "claim_kind")
            check(claim.get("proof", {}).get("law_id") == "nabt.discourse-boundary-cue.v1", "claim_law")
            check(claim.get("source_sha256") == revision, "claim_source_binding")
            check(claim.get("request_sha256") == sha256(wire(request)).hexdigest(), "claim_request_binding")
            check(claim.get("receipt_sha256") == sha256(wire(native)).hexdigest(), "claim_receipt_binding")
            check(bool(claim.get("premises")) and bool(claim.get("does_not_establish")), "claim_limits_missing")
        child = result.get("later_cue_diagnostic") or {}
        check(child.get("authority") == "DIAGNOSTIC_CUE_ACQUISITION_ONLY", "child_authority")
        check(child.get("source_text") == expected["cue_text"], "child_text")
        check(child.get("parent_context") == provided["context"], "child_context")
        check(child.get("parent_source_sha256") == revision, "child_parent_source_binding")
        check(child.get("parent_start_byte") == expected["cue_start_byte"]
              and child.get("parent_end_byte") == expected["cue_end_byte"], "child_parent_span_binding")
        check(child.get("inherited_denial") is False, "child_inherited_denial")
        selected = set()
        for occurrence in result.get("selected_senses_scoped", []):
            check(occurrence.get("authority") == "DIAGNOSTIC_CUE_ACQUISITION_ONLY", "selection_authority")
            check(occurrence.get("intended_sense_kernel_proved") is False, "selection_intent_promoted")
            check(occurrence.get("projects_to_denied_clause") is False, "selection_denial_scope")
            selected.update(occurrence.get("sense_ids", []))
        diagnostic = child.get("result")
        diagnostic_measured = (type(diagnostic) is dict
            and type(diagnostic.get("occurrences")) is list
            and diagnostic.get("status") not in {"VERIFICATION_UNAVAILABLE", "RESOURCE_EXHAUSTED",
                                                   "RESOURCE_LIMIT", "SOURCE_UNAVAILABLE", "INVALID_INPUT"})
        return {"boundary_checks_passed": not failures, "failures": failures,
                "diagnostic_target_measured": diagnostic_measured,
                "diagnostic_target_matched": (selected == set(expected["diagnostic_selected_sense_ids"]))
                                              if diagnostic_measured else None,
                "expected_diagnostic_selection": expected["diagnostic_selected_sense_ids"],
                "observed_diagnostic_selection": sorted(selected)}
    check(not claims, "outside_domain_positive_claim")
    check(result.get("envelope") is None, "outside_domain_envelope")
    check(result.get("later_cue_diagnostic") is None, "outside_domain_child_invoked")
    if expected.get("invalid_marks"):
        check(result.get("status") == "INVALID_INPUT", "malformed_marks_not_invalid")
    else:
        check(result.get("status") == "OUTSIDE_EXECUTED_DISCOURSE", "boundary_not_outside_executed_domain")
        check(result.get("native_checked") is True, "boundary_negative_not_native_checked")
    return {"boundary_checks_passed": not failures, "failures": failures,
            "diagnostic_target_measured": False,
            "reason_not_measured": "Outside declared boundary grammar; this is not linguistic rejection."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    frozen = json.loads((HERE / "freeze.json").read_text())
    raw = (HERE / "cases.v1.json").read_bytes()
    if len(raw) != frozen["bytes"] or sha256(raw).hexdigest() != frozen["sha256"]:
        raise SystemExit("FROZEN_REFERENCE_CHANGED")
    reference = json.loads(raw)
    from tools.linguistic_truth.discourse_boundary import acquire_discourse_boundary
    run = {"schema": "nabt.legacy-wave1-independent-run.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(), "reference_sha256": frozen["sha256"],
        "runner_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "blind": False, "scope": reference["law_scope"], "results": [], "identities": {}}
    for relative in ("tools/linguistic_truth/discourse_boundary.py", "tools/linguistic_truth/runtime.py",
                     "formal/Nabt/DiscourseBoundaryCueBridge.lean", "formal/DiscourseBoundaryCueMain.lean",
                     "formal/.lake/build/bin/discourseBoundaryCue", "evidence/discourse_boundary_v1/source_review.json",
                     "src/nabt/data/framework_foundation.json"):
        path = ROOT / relative
        run["identities"][relative] = sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    # Exclusive creation precedes execution; interrupted evidence is never overwritten.
    with args.output.open("xb") as stream:
        for case in reference["cases"]:
            try:
                result = acquire_discourse_boundary(**case["provided"])
                checks = check_case(case, result, reference["forbidden_promotions"])
                run["results"].append({"id": case["id"], "family": case["family"],
                                       "provided": case["provided"], "result": result, "checks": checks})
            except Exception as error:
                run["results"].append({"id": case["id"], "family": case["family"],
                    "provided": case["provided"], "error": repr(error), "traceback": traceback.format_exc(),
                    "checks": {"boundary_checks_passed": False, "failures": ["execution_exception"],
                               "diagnostic_target_measured": False}})
        measured = [row for row in run["results"] if row["checks"].get("diagnostic_target_measured")]
        run["summary"] = {"boundary_passed": sum(row["checks"]["boundary_checks_passed"] for row in run["results"]),
            "boundary_cases": len(run["results"]), "diagnostic_target_cases": len(measured),
            "diagnostic_target_matched": sum(row["checks"]["diagnostic_target_matched"] for row in measured),
            "natural_use_historical_score_modified": False,
            "intended_meaning_or_world_truth_measured": False}
        stream.write(gzip.compress(wire(run), mtime=0))
    print(json.dumps(run["summary"]))
    for row in run["results"]:
        if not row["checks"]["boundary_checks_passed"] or row["checks"].get("diagnostic_target_matched") is False:
            print(json.dumps({"id": row["id"], "checks": row["checks"]}, ensure_ascii=False))
    return 0 if all(row["checks"]["boundary_checks_passed"] for row in run["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
