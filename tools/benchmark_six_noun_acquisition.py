"""Independent, frozen six-noun reference; abstention is not positive understanding."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from nabt import foundation

REFERENCE = ROOT / "evidence/six_noun_acquisition_v1/reference_cases.json"
REFERENCE_SHA256 = "8c0fc8a57def2e430ca9c2a827e3b0a1d1241742c0bd75e3d7bfd2f86c546b3c"
# Gold uses the dictionary head fum; the profile names its meem-less form fu.
# This explicit identifier correspondence does not normalize Arabic input.
LEXEME_IDS = {"fum": "fu"}


def _load_reference():
    raw = REFERENCE.read_bytes()
    if sha256(raw).hexdigest() != REFERENCE_SHA256:
        raise ValueError("FROZEN_SIX_NOUN_REFERENCE_CHANGED")
    return json.loads(raw)


def _score(case, receipt):
    expected, source = case["expected"], case["input"]
    reading = receipt.get("reading") or {}
    native = receipt.get("native_checked") is True
    positive = (native and receipt.get("grammar_certified") is True
                and receipt.get("status") == "CHECKED_SIX_NOUN"
                and bool(receipt.get("claims")))
    bound = (receipt.get("source") == {"id": source["source_id"],
        "revision": sha256(source["text"].encode()).hexdigest(), "text": source["text"]}
        and receipt.get("context") == source["context"])
    no_promotion = (not positive and receipt.get("claims") == []
                    and receipt.get("linguistic_rejection") is False
                    and receipt.get("grammar_certified") is False
                    and all(receipt.get(key) is False for key in (
                        "strict_language_accepted", "intended_sense_established",
                        "world_truth_established", "external_truth_established", "speaker_reference_established",
                        "tawatur_established", "whole_arabic_complete")))
    scores = {"source_identity": bound,
              "native_source_identity": None if expected["reading_assessment"] == "INVALID_REPRESENTATION"
                  else native and bound,
              "full_form_analysis": None, "positive_licensed_reading": None,
              "alternative_specificity": None, "scope_authority_boundary": None,
              "scope_composition": None, "context_binding": None,
              "malformed_mark_rejection": None}
    label = expected["reading_assessment"]
    if case["eligible_for"]["full_form_analysis"]:
        matches = (reading.get("grammatical_case") == expected["grammatical_case"]
                   and reading.get("lexeme") == LEXEME_IDS.get(expected["lexeme"], expected["lexeme"]))
        if label == "FULL_FORM_LICENSE_EXPECTED":
            scores["full_form_analysis"] = positive and matches and bound
            scores["positive_licensed_reading"] = scores["full_form_analysis"]
        else:
            scores["full_form_analysis"] = (native and bound and no_promotion and matches
                and "COMMON_LETTER_CASE_MISMATCH" in receipt.get("residuals", []))
    if case["eligible_for"]["alternative_reading_handling"]:
        # A generic outside-profile answer is safe but has not acquired the
        # named missing premise. Preserve that gap in this separate numerator.
        required = expected["unresolved_condition"]
        labels = receipt.get("residuals", []) + reading.get("alternatives", [])
        correspondence = {
            "QASR_OR_DEFICIENCY_READING_NOT_IMPLEMENTED": "QASR_AND_NAQS_NOT_ENUMERATED_BY_THIS_PROFILE",
            "COMPANIONSHIP_MEANING_NOT_ACQUIRED": "DHU_COMPANIONSHIP_NOT_ACQUIRED",
        }
        scores["alternative_specificity"] = (native and bound and no_promotion
            and correspondence.get(required, required) in labels)
    if case["eligible_for"]["scope_preservation"]:
        scores["scope_authority_boundary"] = native and bound and no_promotion
        # v1 deliberately has no scope-to-inflection composition witness.
        scores["scope_composition"] = False
    if case["eligible_for"]["context_binding"]:
        claim_contexts = [claim.get("context") for claim in receipt.get("claims", [])]
        scores["context_binding"] = (native and bound and positive
                                     and claim_contexts == [source["context"]])
    if case["eligible_for"]["malformed_mark_rejection"]:
        scores["malformed_mark_rejection"] = (receipt.get("status") == "INVALID_INPUT"
            and receipt.get("claims") == [] and receipt.get("native_checked") is False)
    return scores


def _measure(reference, acquire):
    records = []
    for case in reference["cases"]:
        # Only raw input crosses into production; no gold field is supplied.
        request = case["input"]
        receipt = acquire(request["text"], source_id=request["source_id"], context=request["context"])
        records.append({"id": case["id"], "expected": case["expected"],
                        "scores": _score(case, receipt), "receipt": receipt})
    axes = {}
    for name in records[0]["scores"]:
        values = [r["scores"][name] for r in records if r["scores"][name] is not None]
        axes[name] = {"passed": sum(v is True for v in values), "total": len(values),
                      "failed_ids": [r["id"] for r in records if r["scores"][name] is False]}
    for name in ("intended_reference", "external_truth", "tawatur", "whole_arabic_completeness"):
        axes[name] = {"status": "NOT_MEASURED", "passed": None, "total": None}
    native_required = [r for r in records if r["expected"]["reading_assessment"] != "INVALID_REPRESENTATION"]
    return {"schema": "nabt.six-noun-reference-measurement.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "reference_sha256": REFERENCE_SHA256,
        "reference_status": reference["reference_status"], "held_out": False,
        "case_count": len(records), "axes": axes,
        "native_required_count": len(native_required),
        "native_execution_complete": all(r["receipt"].get("native_checked") is True for r in native_required),
        "historical_metrics": reference["historical_metrics"],
        "comparison_authority": "Python comparison against independently authored frozen gold; not a Lean completeness theorem",
        "records": records}


def main():
    foundation.require_foundation("tools.benchmark_six_noun_acquisition.main")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-native", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from tools.linguistic_truth.six_noun import acquire_six_noun
    report = _measure(_load_reference(), acquire_six_noun)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, ensure_ascii=False))
    # Semantic gaps are measured, not hidden by rewriting the reference or by
    # turning a green CI gate into a positive semantic accuracy claim.
    return int(args.require_native and not report["native_execution_complete"])


if __name__ == "__main__":
    raise SystemExit(main())
