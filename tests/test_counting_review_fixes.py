"""Post-review regressions for PR9; separate from the frozen 184-case set.

Two tests exercise a pinned 99-case boundary matrix. The optional --record
entry point preserves each outcome and the actually imported runtime hashes,
so the identical tests can measure the old commit and the corrected package.
"""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
import unittest

from nabt import counting
from nabt.errors import NabtError

REPO = Path(__file__).resolve().parents[1]
MATERIAL = REPO / "evidence/nominal/review_fixes/cases_v1.json"
MATERIAL_SHA256 = "dc67e40341781aa8cd14466b2a606cab6f99d15c6b2ea622cc5115d87588d05b"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_cases():
    raw = MATERIAL.read_bytes()
    require(sha256(raw).hexdigest() == MATERIAL_SHA256, "Review matrix changed")
    material = json.loads(raw)
    require(material["case_count"] == len(material["cases"]) == 99, "Review case inventory changed")
    require(len({c["id"] for c in material["cases"]}) == 99, "Duplicate review case identifiers")
    return material


def check_case(case, lexical_text):
    source = case["text"]
    expected = case["expect"]
    try:
        report = counting.read_count_phrase(source, lexical_text=lexical_text,
            source_id="review_fix_" + case["id"], lexical_source_id="review_fix_lexicon", scope="counting_review_v1")
    except NabtError as error:
        observed = {"outcome": "error", "status": error.status, "code": error.code}
        require(expected == "reject_noncanonical" and error.status == "REJECT"
                and error.code == "NONCANONICAL_CARDINAL_LITERAL",
                "Unexpected error outcome: " + json.dumps(observed, ensure_ascii=True))
        return observed
    numeral = report["numeral"]
    observed = {"outcome": "report", "status": report["status"],
                "numeral_status": None if numeral is None else numeral["status"],
                "value": None if numeral is None else numeral.get("value"),
                "alternative_count": len(report["alternatives"]), "missing": report["missing"]}
    require(expected != "reject_noncanonical", "Leading-zero literal returned a report instead of REJECT: "
            + json.dumps(observed, ensure_ascii=True))
    require(report["raw_text"] == source and report["source_sha256"] == sha256(source.encode("utf-8")).hexdigest(),
            "Input controls/digits were normalized or discarded")
    require("".join(p["surface"] for p in report["nominal_report"]["partition"]) == source,
            "Source partition lost bytes")
    require(report["actual_case"] is None and report["actual_role"] is None and report["world_cardinality"] is None,
            "A bounded relation acquired actual grammar/world authority")
    require(counting.verify_count_phrase(report)["valid"] is True, "Original-source report does not replay")
    if expected == "block_internal_separator":
        require(report["alternatives"] == [] and report["counted_occurrence_id"] is None
                and "COMPLETE_SINGLE_CARDINAL_COUNTED_SEQUENCE" in report["missing"],
                "Count relation crossed an internal line/page/control boundary: " + json.dumps(observed, ensure_ascii=True))
    elif expected == "defer_long_canonical":
        require(report["alternatives"] == [] and numeral is not None and numeral["status"] == "DEFER"
                and "CARDINAL_OUTSIDE_BOUNDED_RULE" in report["missing"],
                "Canonical long numeral was coerced or misclassified as malformed")
    elif expected == "defer_zero":
        require(numeral is not None and type(numeral["value"]) is int and numeral["value"] == 0
                and report["alternatives"] == [] and "NUMBER_RULE_OUTSIDE_DOMAIN" in report["missing"],
                "Single zero was confused with noncanonical zero padding")
    else:
        require(expected == "supported_digits", "Unhandled review expectation")
        require(numeral is not None and type(numeral["value"]) is int and numeral["value"] == case["expected_value"],
                "Supported digit value disappeared")
        require(report["alternatives"] and not report["missing"]
                and all(not row["missing"] and row["conditional_status"] == "COMPATIBLE_OBSERVED_FEATURES"
                        for row in report["alternatives"]),
                "Allowed horizontal or external spacing blocked the conditional relation")
        require(numeral["unit_gender"] is None and numeral["ten_gender"] is None
                and all(row["checks"][key]["status"] in {"NOT_OBSERVED", "UNCONSTRAINED"}
                        for row in report["alternatives"] for key in ("unit_gender", "ten_gender")),
                "Digits supplied observed grammatical gender")
    return observed


class CountingReviewFixTests(unittest.TestCase):
    def test_canonicality_precedes_length_domain_deferral(self):
        material = load_cases()
        for case in material["cases"]:
            if case["group"] == "canonicality":
                with self.subTest(case=case["id"]):
                    check_case(case, material["lexical_text"])

    def test_only_horizontal_internal_spacing_connects_the_phrase(self):
        material = load_cases()
        for case in material["cases"]:
            if case["group"] == "spacing":
                with self.subTest(case=case["id"]):
                    check_case(case, material["lexical_text"])


def runtime_snapshot():
    root = Path(counting.__file__).resolve().parents[2]
    paths = sorted(p for p in (root / "src/nabt").rglob("*")
                   if p.is_file() and p.suffix in {".py", ".json", ".txt"} and "__pycache__" not in p.parts)
    paths.append(root / "pyproject.toml")
    rows = [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size,
             "sha256": sha256(p.read_bytes()).hexdigest()} for p in paths]
    return {"files": rows, "manifest_sha256": sha256(json.dumps(rows, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()}


def record(output, stage, runtime_archive=None):
    require(not output.exists(), "Refusing to overwrite a review measurement")
    material = load_cases()
    snapshot = runtime_snapshot()
    rows = []
    for case in material["cases"]:
        row = {"id": case["id"], "group": case["group"], "expect": case["expect"]}
        try:
            row.update(observed=check_case(case, material["lexical_text"]), passed=True)
        except (AssertionError, KeyError, TypeError, ValueError) as error:
            row.update(passed=False, error=type(error).__name__ + ": " + str(error))
        rows.append(row)
    unchanged = runtime_snapshot() == snapshot
    result = {"schema": "nabt.counting.review-fixes.measurement.v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "stage": stage,
        "material_sha256": MATERIAL_SHA256, "test_file_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "baseline_commit": material["baseline_commit"] if stage == "before" else None,
        "runtime_snapshot": snapshot, "runtime_unchanged_during_measurement": unchanged,
        "scope": material["scope"], "old_nominal_gold_modified": False,
        "passed": unchanged and all(r["passed"] for r in rows),
        "score": {"passed": sum(r["passed"] for r in rows), "total": len(rows)},
        "groups": {g: {"passed": sum(r["passed"] for r in rows if r["group"] == g),
                       "total": sum(r["group"] == g for r in rows)} for g in ("canonicality", "spacing")},
        "results": rows}
    if runtime_archive is not None:
        result["runtime_archive"] = {"filename": runtime_archive.name,
            "sha256": sha256(runtime_archive.read_bytes()).hexdigest()}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=True, indent=2)
        handle.write("\n")
    print(json.dumps({k: result[k] for k in ("stage", "score", "groups", "passed")}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    if "--record" in sys.argv:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--record", type=Path, required=True)
        parser.add_argument("--stage", choices=("before", "after"), required=True)
        parser.add_argument("--runtime-archive", type=Path)
        args = parser.parse_args()
        raise SystemExit(record(args.record, args.stage, args.runtime_archive))
    unittest.main()
