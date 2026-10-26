#!/usr/bin/env python3
"""Conditional classical reading families; never a free-text licensing parser."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "src/nabt/data/classical_reference_readings.json"
INVENTORY = ROOT / "src/nabt/data/source_evidence/classical_rule_inventory_v1.json"
LAW_ID = "nabt.classical-conditional-readings.v1"
ENDINGS = ("nominative", "accusative", "genitive", "jussive")
NUMBERS = ("singular", "dual", "plural")
READINGS = (
    "topic", "omitted_verb", "description_subject", "fronted_predicate",
    "an_interpretive_indicative", "an_interpretive_jussive", "an_masdariyya_subjunctive",
)


import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

def _frame(frame: dict) -> dict:
    if type(frame) is not dict or type(frame.get("family")) is not str:
        raise ValueError("a typed conditional frame is required; text is not parsed")
    family = frame["family"]
    extra = {"free_ishtighal": set(), "matched_description": {"number"},
             "interpretive_an": {"has_la"}}.get(family)
    if extra is None or set(frame) - ({"family", "observed_ending"} | extra):
        raise ValueError("unknown family or premise field")
    observed = frame.get("observed_ending")
    if observed is not None and (type(observed) is not str or observed not in ENDINGS):
        raise ValueError("unknown observed ending")
    result = {"family": family, "observed_ending": observed}
    if family == "matched_description":
        if frame.get("number") not in NUMBERS:
            raise ValueError("a matching grammatical number is required")
        result["number"] = frame["number"]
    if family == "interpretive_an":
        if type(frame.get("has_la")) is not bool:
            raise ValueError("has_la must be Boolean")
        result["has_la"] = frame["has_la"]
    return result


def reading_ending(reading: str) -> str:
    if reading not in READINGS:
        raise ValueError("unknown reading")
    if reading in {"omitted_verb", "an_masdariyya_subjunctive"}:
        return "accusative"
    if reading == "an_interpretive_jussive":
        return "jussive"
    return "nominative"


def enumerate_readings(frame: dict) -> dict:
    """Compute consequences *if* the supplied linguistic premises are established.

    No raw text, example identity, source gold set, acquisition certificate, or
    caller authority is consumed. Supplying a frame does not establish it.
    """
    foundation.require_foundation('tools.classical_reference_readings.enumerate_readings')
    frame = _frame(frame)
    family = frame["family"]
    if family == "free_ishtighal":
        readings = ["topic", "omitted_verb"]
    elif family == "matched_description":
        readings = (["description_subject"] if frame["number"] == "singular" else [])
        readings += ["fronted_predicate"]
    else:
        readings = ["an_interpretive_indicative"]
        if frame["has_la"]:
            readings += ["an_interpretive_jussive"]
        readings += ["an_masdariyya_subjunctive"]
    if frame["observed_ending"] is not None:
        readings = [r for r in readings if reading_ending(r) == frame["observed_ending"]]
    return {"law_id": LAW_ID, "frame": frame, "readings": readings,
            "ranks": [READINGS.index(r) for r in readings],
            "endings": [reading_ending(r) for r in readings],
            "premises_verified": False, "language_certificate_granted": False,
            "scope": "Conditional enumeration only; this tool does not infer its premises from text."}


def verify_proposal(frame: dict, proposal: list[str]) -> dict:
    foundation.require_foundation('tools.classical_reference_readings.verify_proposal')
    if type(proposal) is not list or any(type(r) is not str or r not in READINGS for r in proposal):
        raise ValueError("proposal must be a list of known reading IDs")
    expected = enumerate_readings(frame)["readings"]
    return {"conditional_exact_match": proposal == expected,
            "missing": [r for r in expected if r not in proposal],
            "unexpected": [r for r in proposal if r not in expected],
            "duplicates": len(set(proposal)) != len(proposal),
            "language_certificate_granted": False}


def all_frames() -> list[dict]:
    frames = []
    for ending in (None, *ENDINGS):
        frames.append({"family": "free_ishtighal", "observed_ending": ending})
        frames += [{"family": "matched_description", "number": n, "observed_ending": ending}
                   for n in NUMBERS]
        frames += [{"family": "interpretive_an", "has_la": b, "observed_ending": ending}
                   for b in (True, False)]
    return frames


def conformance(export: dict | None = None) -> dict:
    export = export if export is not None else json.loads(EXPORT.read_text())
    if export.get("law_id") != LAW_ID:
        raise ValueError("wrong Lean law ID")
    rows = export["rows"]
    expected_frames = all_frames()
    if len(rows) != len(expected_frames):
        raise ValueError("Lean export does not enumerate the full conditional input domain")
    mismatches = []
    for expected_frame, row in zip(expected_frames, rows):
        if _frame(row["frame"]) != expected_frame:
            raise ValueError("Lean frame order/domain mismatch")
        actual = enumerate_readings(expected_frame)
        if any(actual[k] != row[k] for k in ("readings", "ranks", "endings")):
            mismatches.append(expected_frame)
    return {"valid": not mismatches, "input_count": len(rows), "mismatches": mismatches,
            "scope": "Exhaustive finite input-domain agreement with kernel-compiled Lean export."}


# Evaluation annotations, deliberately separate from the enumerator. These
# select a conditional family, never provide the answer list to the enumerator.
REFERENCE_FRAMES = {
    "REF-QATR-ISHTIGHAL": {"family": "free_ishtighal"},
    "REF-QATR-ISHTIGHAL-PP": {"family": "free_ishtighal"},
    "REF-AQIL-SINGULAR-PREDICATE": {"family": "matched_description", "number": "singular"},
    "REF-AQIL-DUAL-PREDICATE": {"family": "matched_description", "number": "dual"},
    "REF-MUGHNI-AN-LA": {"family": "interpretive_an", "has_la": True},
    "REF-MUGHNI-AN-NO-LA": {"family": "interpretive_an", "has_la": False},
}
REFERENCE_LABELS = {
    "nominative_topic": "topic", "accusative_omitted_verb": "omitted_verb",
    "accusative_omitted_jawaztu": "omitted_verb", "description_topic": "description_subject",
    "fronted_predicate": "fronted_predicate", "interpretive_negative": "an_interpretive_indicative",
    "interpretive_prohibition": "an_interpretive_jussive",
    "masdariyya_negative": "an_masdariyya_subjunctive",
    "interpretive_indicative": "an_interpretive_indicative",
    "masdariyya_subjunctive": "an_masdariyya_subjunctive",
}


def benchmark_reference_constructions() -> dict:
    spec = importlib.util.spec_from_file_location("classical_rule_inventory", ROOT / "tools/classical_rule_inventory.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    inventory = json.loads(INVENTORY.read_text())
    replay = validator.validate_inventory(inventory, INVENTORY.parent)
    cases, expected_total, observed_total, intersection_total = [], 0, 0, 0
    for reference in inventory["reference_constructions"]:
        frame = REFERENCE_FRAMES[reference["case_id"]]
        expected = [REFERENCE_LABELS[a["id"]] for a in reference["expected_alternatives"]]
        # Only the premises enter the algorithm. Gold is compared afterwards.
        actual = enumerate_readings(frame)["readings"]
        expected_total += len(expected)
        observed_total += len(actual)
        intersection_total += len(set(expected) & set(actual))
        cases.append({"case_id": reference["case_id"], "input": reference["input"],
                      "assumed_frame": frame, "exact_set_match": set(expected) == set(actual),
                      "order_match": expected == actual, "expected": expected, "actual": actual,
                      "source_spans": reference["source_spans"],
                      "vocalized_alternatives": reference["expected_alternatives"],
                      "free_text_parser_evaluated": False})
    return {"schema": "nabt.classical-reference-benchmark.v1", "law_id": LAW_ID,
            "source_replay_valid": replay["valid"], "case_count": len(cases),
            "exact_set_matches": sum(c["exact_set_match"] for c in cases),
            "order_matches": sum(c["order_match"] for c in cases),
            "expected_reading_count": expected_total, "returned_reading_count": observed_total,
            "matched_reading_count": intersection_total,
            "free_text_parser_evaluated": False, "premise_acquisition_evaluated": False,
            "scope": "Source-adjudicated conditional operation benchmark; authored, not blind NLP accuracy.",
            "cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", help="JSON conditional frame, not free text")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    try:
        result = (enumerate_readings(json.loads(args.frame)) if args.frame else
                  benchmark_reference_constructions() if args.benchmark else conformance())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("valid", True) else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
