#!/usr/bin/env python3
"""Evaluate independently authored source cases through the installed wrapper.

This does not report whole-Arabic accuracy, source-book completeness, or free-text
premise acquisition. A partial answer is required to retain its unknown branch.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEFAULT_GOLD = HERE / "benchmark_v1.json"
GOLD_SHA256 = "27b569b4807d1a7baae7e331fbf4ca98eeec06e44881a168477f754e836a3cd4"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run(gold_path=DEFAULT_GOLD):
    from nabt.classical_laws import evaluate, verify

    if digest(gold_path) != GOLD_SHA256:
        raise ValueError("Independent benchmark identity changed")
    gold = json.loads(gold_path.read_text())
    cases = gold["cases"]
    if len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate benchmark case")
    if digest(HERE / "source_obligations_v1.json") != gold["source_obligations_sha256"]:
        raise ValueError("Source obligations changed")
    source_dir = ROOT / "src/nabt/data/source_evidence"
    if digest(source_dir / "classical_rule_inventory_v1.json") != gold["inventory_sha256"]:
        raise ValueError("Installed original inventory changed")
    baseline = json.loads((ROOT / "evidence/arabic_completion_v5/rule_implementation_crosswalk.json").read_text())
    missing = {r["rule_id"] for r in baseline["rows"] if r["status"] == "not_implemented_by_this_extension"}
    if {c["rule_id"] for c in cases} != missing:
        raise ValueError("Benchmark does not cover the exact original 24-rule set")
    for rule_id in missing:
        kinds = {c["kind"] for c in cases if c["rule_id"] == rule_id}
        if not {"positive", "negative"} <= kinds:
            raise ValueError("Rule has no positive and negative diagnostics: " + rule_id)

    results = []
    for case in cases:
        rid = case["rule_id"]
        key = ("morphophonemes" if rid.startswith("HAMZA-") else
               "cells" if rid.startswith(("WEAK-", "GEM-", "ASSIM-")) else "segments")
        row = {"case_id": case["case_id"], "rule_id": rid, "kind": case["kind"], "tag": case["tag"]}
        try:
            receipt = evaluate(rid, case["frame"])
            result = receipt["result"]
            alternatives = result["alternatives"]
            outputs = [a[key] for a in alternatives]
            checks = {
                "exact_ordered_outputs": outputs == case["expected_outputs"],
                "retained_input": receipt["input_frame"] == case["frame"],
                "no_language_authority": receipt["authority"] == "CONDITIONAL_TRANSFORMATION_ONLY"
                    and receipt["grants_language_license"] is False
                    and receipt["premises_established_from_free_text"] is False,
                "original_source_attached": bool(result["source_spans"]),
                "receipt_recomputed": verify(receipt)["valid"] is True,
            }
            if "expected_status" in case:
                checks["status"] = result["status"] == case["expected_status"]
            if "expected_surface_complete" in case:
                checks["surface_partiality"] = [a["surface_complete"] for a in alternatives] == case["expected_surface_complete"]
            if "expected_evidence_kinds" in case:
                checks["source_attribution"] = [a["evidence_kind"] for a in alternatives] == case["expected_evidence_kinds"]
            if "expected_profiles_complete" in case:
                checks["profile_partiality"] = result["alternatives_complete_within_requested_profile"] is case["expected_profiles_complete"]
                checks["unknown_branch_retained"] = bool(result["unresolved_profiles"])
            row.update(passed=all(checks.values()), checks=checks, actual_outputs=outputs,
                       expected_outputs=case["expected_outputs"], actual_status=result["status"])
        except Exception as exc:
            row.update(passed=False, error_type=type(exc).__name__, error=str(exc))
        results.append(row)

    per_rule = []
    for rid in sorted(missing):
        selected = [r for r in results if r["rule_id"] == rid]
        per_rule.append({"rule_id": rid, "cases": len(selected), "passed": sum(r["passed"] for r in selected),
                         "kinds": dict(Counter(r["kind"] for r in selected))})
    kinds = {}
    for kind in ("positive", "negative", "partial"):
        selected = [r for r in results if r["kind"] == kind]
        kinds[kind] = {"total": len(selected), "passed": sum(r["passed"] for r in selected)}
    return {
        "schema": "nabt.classical-laws-independent-benchmark-result.v1",
        "scope": gold["scope"], "gold_sha256": GOLD_SHA256,
        "case_count": len(results), "passed": sum(r["passed"] for r in results),
        "failed": sum(not r["passed"] for r in results), "rule_count": len(missing),
        "kinds": kinds, "per_rule": per_rule, "cases": results,
        "negative_cases_with_any_emitted_alternative": sum(bool(r.get("actual_outputs")) for r in results if r["kind"] == "negative"),
        "whole_arabic_coverage": None, "whole_book_complete": False,
        "blind_benchmark": False, "free_text_premise_acquisition_tested": False,
        "runtime_sha256": {str(p.relative_to(ROOT)): digest(p) for p in [
            ROOT / "src/nabt" / name for name in (
                "classical_laws.py", "classical_weak.py", "classical_hamza.py",
                "classical_gemination.py", "classical_boundary_affixes.py")]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run(args.gold)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({k: result[k] for k in ("case_count", "passed", "failed", "rule_count", "kinds", "negative_cases_with_any_emitted_alternative")}, ensure_ascii=False))
        return 0 if result["failed"] == 0 else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
