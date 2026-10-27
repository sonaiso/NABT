"""Measure occurrence reference separately from whole-clause analysis.

The unchanged historical 25 and the separately authored 20 have distinct
denominators. Only text/context cross into the runtime. Lean checks a scoped
reference certificate; Python compares that receipt to editorial gold.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tools import benchmark_semantic_axes as historical
from tools.semantic_axes import identity as digest_value

REFERENCE = ROOT / "evidence/contextual_semantics_v1/reference.json"
REFERENCE_SHA256 = "6f2e1c1127196d2b5fbbc2f357dbbf1a003881061727e96ad29d153c6628707d"
STATUSES = ("PASS", "FAIL", "UNMEASURED", "NOT_APPLICABLE")
SCOPE = {
    "reference": "INITIAL_OCCURRENCE_ONLY",
    "comparison": "PYTHON_REFERENCE_COMPARISON",
    "native": "CONDITIONAL_REFERENCE_CERTIFICATE_NOT_GOLD_OR_FULL_SENTENCE_PROOF",
    "original_syntax_and_readings": "UNCHANGED_ATTESTED_QAC_PYTHON_REPLAY",
    "sources": "PINNED_SOURCE_ANNOTATIONS_AND_DECLARED_CONTEXT_PREMISES",
    "independent_reference": "AUTHORED_DIAGNOSTIC_NOT_EXTERNAL_BLIND_HOLDOUT",
}


def file_sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load_independent_reference():
    value = historical._strict_json(REFERENCE)
    freeze = historical._strict_json(REFERENCE.with_name("reference.freeze.json"))
    if (file_sha(REFERENCE) != REFERENCE_SHA256 or
            freeze.get("reference_sha256") != REFERENCE_SHA256 or
            freeze.get("frozen_before_new_runtime_execution") is not True or
            type(freeze.get("case_count")) is not int or freeze["case_count"] != 20 or
            len(value.get("cases", [])) != 20):
        raise ValueError("Independent reference identity or scope mismatch")
    ids = set()
    for case in value["cases"]:
        if case["id"] in ids or set(case["input"]) != {"text", "context"}:
            raise ValueError("Independent reference IDs/input boundary mismatch")
        ids.add(case["id"])
        if (digest_value(case["input"]) != freeze["case_input_sha256"].get(case["id"]) or
                digest_value(case["expected"]) != freeze["case_expected_sha256"].get(case["id"])):
            raise ValueError("Independent reference case binding mismatch")
    for filename, key in (("reference_sources.json", "sources_sha256"),
                          ("reference_input_review.json", "input_review_sha256")):
        if file_sha(REFERENCE.with_name(filename)) != freeze.get(key):
            raise ValueError("Independent reference source review mismatch")
    return value


def identity():
    from tools import contextual_reference as runtime
    result = runtime.identity()
    baseline_paths = sorted((ROOT / "src/nabt").rglob("*.py")) + [
        ROOT / "tools/semantic_axes.py", ROOT / "tools/benchmark_semantic_axes.py",
        ROOT / "tools/attested_lexical_loader.py", ROOT / "evidence/lexical_loading_v1/matrix.json",
        ROOT / "evidence/lexical_completion_v1/catalog.json"]
    baseline_manifest = {str(path.relative_to(ROOT)): file_sha(path) for path in baseline_paths}
    return {**result, "original_reference_sha256": historical.REFERENCE_SHA256,
            "independent_reference_sha256": REFERENCE_SHA256,
            "scorer_sha256": file_sha(__file__),
            "baseline_source_sha256": digest_value(baseline_manifest)}


def metric(statuses):
    if any(status not in STATUSES for status in statuses):
        raise ValueError("Unknown comparison status")
    passed, failed, unmeasured = (statuses.count(s) for s in STATUSES[:3])
    return {"eligible": passed + failed + unmeasured,
            "measured": passed + failed, "passed": passed,
            "failed": failed, "unmeasured": unmeasured}


def compare_reference(expected, execution):
    """No receipt truth flag may substitute for an exact gold comparison."""
    observed = execution.get("reference")
    state = expected.get("status")
    status, reason = "FAIL", "REFERENCE_NOT_ACQUIRED_AS_EXPECTED"
    if state == "not_applicable":
        status, reason = "NOT_APPLICABLE", "EXCLUDED_BY_ORIGINAL_REFERENCE_SCOPE"
    elif (execution.get("native_checked") is not True or
          execution.get("certificate_checked") is not True):
        status, reason = "UNMEASURED", "NATIVE_REFERENCE_CHECK_UNAVAILABLE"
    elif type(observed) is not dict:
        # A checked refusal to interpret a different occurrence is not a
        # successful 'unresolved' answer about the requested occurrence.
        reason = "TARGET_OCCURRENCE_OUTSIDE_EXECUTED_REFERENCE_SCOPE"
    else:
        wanted = expected.get("target_ids", [])
        candidates = observed.get("candidate_entity_ids")
        bound = observed.get("bound_entity_id")
        if type(candidates) is list and len(candidates) == len(set(candidates)):
            same = observed.get("surface") == expected.get("surface")
            if "span" in expected:
                same = same and observed.get("span") == expected["span"]
            # This version licenses the initial, outer occurrence only.
            if "scope" in expected:
                same = same and expected["scope"] == "outer"
            if "occurrence" in expected:
                same = same and expected["occurrence"] == 0
            if state == "resolved":
                same = (same and len(wanted) == 1 and set(candidates) == set(wanted)
                        and bound == wanted[0] and observed.get("status") == "RESOLVED")
            elif state == "ambiguous":
                same = (same and len(wanted) > 1 and set(candidates) == set(wanted)
                        and bound is None and observed.get("status") == "AMBIGUOUS")
            elif state == "unresolved":
                same = (same and not candidates and not wanted and bound is None
                        and observed.get("status") == "NO_CANDIDATE")
            else:
                same = False
            if same:
                status, reason = "PASS", "REFERENCE_MATCH"
    return {"status": status, "expected": deepcopy(expected),
            "observed": deepcopy(observed), "reason": reason}


def summarize(cases):
    groups = {}
    for name in ("original_25", "independent_20"):
        rows = [c for c in cases if c["group"] == name]
        group = {"case_count": len(rows),
                 "reference_after": metric([c["reference_comparison"]["status"] for c in rows])}
        if name == "original_25":
            group["baseline_axes"] = {
                axis: metric([c["baseline_axes"][axis] for c in rows])
                for axis in ("syntax", "readings", "reference")}
        else:
            group["metric_categories"] = {
                category: metric([c["reference_comparison"]["status"] for c in rows
                                  if c["metric_category"] == category])
                for category in ("positive_binding", "alternative_retention", "safe_nonresolution")}
        groups[name] = group
    return groups


def run(*, require_native=False):
    from tools import contextual_reference as runtime
    original, original_sha, _ = historical.load_reference()
    independent = load_independent_reference()
    baseline = historical.run(lexical_profile="attested_qac_v1")
    baseline_by_id = {row["id"]: row for row in baseline["cases"]}
    initial_identity = identity()
    rows = []
    for group, cases in (("original_25", original["cases"]),
                         ("independent_20", independent["cases"])):
        for case in cases:
            request = {"text": case["input"]["text"],
                       "context": deepcopy(case["input"].get("context", {}))}
            # Neither case IDs, expected reference nor a supplied answer is
            # provided to the runtime. Optional historical query is unused.
            execution = runtime.execute_request(deepcopy(request))
            expected = case["expected"]["reference"]
            if execution.get("input_sha256") != digest_value(request):
                raise ValueError("Runtime returned a receipt for a different input")
            base = baseline_by_id[case["id"]] if group == "original_25" else None
            category = case.get("metric_category", {
                "resolved": "positive_binding", "ambiguous": "alternative_retention",
                "unresolved": "safe_nonresolution", "not_applicable": "not_applicable",
            }[expected["status"]])
            rows.append({"id": case["id"], "group": group, "input": request,
                         "input_sha256": digest_value(request),
                         "metric_category": category, "expected_reference": deepcopy(expected),
                         "baseline_axes": ({axis: base["axis_results"][axis]["status"]
                                            for axis in ("syntax", "readings", "reference")}
                                           if base else None),
                         "reference_comparison": compare_reference(expected, execution),
                         "execution": execution})
    final_identity = identity()
    if final_identity != initial_identity or original_sha != historical.REFERENCE_SHA256:
        raise ValueError("Source or executable identity changed during measurement")
    checked = all(row["execution"].get("native_checked") is True and
                  row["execution"].get("certificate_checked") is True for row in rows)
    if require_native and not checked:
        raise RuntimeError("Native contextual-reference verification unavailable")
    return {"schema": "nabt.contextual-reference-benchmark.v1", **final_identity,
            "groups": summarize(rows), "cases": rows,
            "all_cases_native_checked": checked, "scope": deepcopy(SCOPE),
            "whole_arabic_complete": False, "tawatur_evaluated": False,
            "world_truth_established": False, "motive_measured": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--require-native", action="store_true")
    args = parser.parse_args()
    report = run(require_native=args.require_native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"groups": report["groups"],
                      "all_cases_native_checked": report["all_cases_native_checked"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
