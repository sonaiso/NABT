"""Independent, frozen scoped metrics for the bounded epistemic evidence law.

Authored conditional controls and correspondence to an agency snapshot have
separate denominators. Missing native execution is UNMEASURED, never success.
The runtime receives input/profile only; expected labels stay in this scorer.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import epistemic_measurement as adapter

EVIDENCE = ROOT / "evidence/epistemic_measurement_v1"
REFERENCE = EVIDENCE / "reference.json"
REFERENCE_SHA256 = "d3754d7d04ba83c69e25ea0c4d661da4bde4795633429cd64979f21f87a9fe70"
AUTHORED_REGISTRY = EVIDENCE / "authored_registry.json"
AUTHORED_REGISTRY_SHA256 = "9c972a7a76ae90711b20208d57bb648d0560bee9d5c13c52eaaf920e5043c6c6"
AUTHORED_FREEZE = EVIDENCE / "reference.freeze.json"
AUTHORED_FREEZE_SHA256 = "c03a2746ed2cce0e83e755d51da94bb581d4ad068c776eec8da15b21a579b1d6"
AGENCY_REFERENCE = EVIDENCE / "agency_reference.json"
AGENCY_REFERENCE_SHA256 = "ccbf599e3d1536e8f3b5ab29ca40508e82e192770c14b23d7cc880f2b7725a6d"
CATEGORIES = {"SUPPORTED": "positive_capability", "REFUTED": "refutation", "CONFLICT": "conflict",
              "UNKNOWN": "safe_abstention", "RESOURCE_LIMIT": "resource_boundary"}


def _file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _pinned_json(path: Path, expected: str) -> dict:
    if _file_sha(path) != expected:
        raise ValueError("Frozen epistemic evidence digest mismatch: " + path.name)
    value = adapter.strict_loads(path.read_bytes())
    if type(value) is not dict:
        raise ValueError("Frozen epistemic evidence must be an object")
    return value


def load_reference() -> list[dict]:
    authored = _pinned_json(REFERENCE, REFERENCE_SHA256)
    registry = _pinned_json(AUTHORED_REGISTRY, AUTHORED_REGISTRY_SHA256)
    freeze = _pinned_json(AUTHORED_FREEZE, AUTHORED_FREEZE_SHA256)
    agency = _pinned_json(AGENCY_REFERENCE, AGENCY_REFERENCE_SHA256)
    if (authored.get("schema") != "nabt.epistemic-measurement-reference.v1"
            or freeze.get("reference_sha256") != REFERENCE_SHA256
            or freeze.get("authored_registry_sha256") != AUTHORED_REGISTRY_SHA256
            or freeze.get("case_count") != 32
            or registry.get("authority") != "AUTHORED_SCENARIO_NOT_EMPIRICAL_OR_HUMAN_TESTIMONY"):
        raise ValueError("Reference freeze identity differs from installed benchmark")
    cases = []
    identifiers = set()
    for group, document, profile, evidence_class in (
            ("authored_controls", authored, adapter.AUTHORED_PROFILE, "AUTHORED_SCENARIO"),
            ("agency_record", agency, adapter.USGS_PROFILE, "AGENCY_RECORD")):
        if type(document.get("cases")) is not list or not document["cases"]:
            raise ValueError("Every benchmark group needs declared cases")
        for original in document["cases"]:
            if type(original) is not dict or type(original.get("id")) is not str or original["id"] in identifiers:
                raise ValueError("Reference case identities must be unique")
            case = deepcopy(original)
            if case.get("source_profile") != profile:
                raise ValueError("Reference source profile differs from group")
            adapter.validate_certificate(case.get("expected"))
            if case.get("metric_category") != CATEGORIES[case["expected"]["status"]]:
                raise ValueError("Reference metric category disagrees with expected decision")
            if type(case.get("input")) is not dict or "query" not in case["input"]:
                raise ValueError("Reference requires input-only query payload")
            if group == "authored_controls":
                if (adapter.digest(case["input"]) != freeze["case_input_sha256"].get(case["id"])
                        or adapter.digest(case["expected"]) != freeze["case_expected_sha256"].get(case["id"])):
                    raise ValueError("Reference case differs from independently frozen input/expectation")
            case["group"] = group
            case["evidence_class"] = evidence_class
            identifiers.add(case["id"])
            cases.append(case)
    if sum(case["group"] == "authored_controls" for case in cases) != 32:
        raise ValueError("Authored denominator differs from frozen 32 cases")
    return cases


def identity() -> dict:
    """Installed identities include BOTH independent references and the raw agency pin."""
    # No caller manifest can replace these installed pins. Reading also verifies bytes.
    load_reference()
    if _file_sha(adapter.USGS_RAW_PATH) != adapter.USGS_RAW_SHA256:
        raise ValueError("Installed USGS raw source digest mismatch")
    reference_sha = adapter.digest({"authored_controls": REFERENCE_SHA256, "agency_record": AGENCY_REFERENCE_SHA256})
    source_sha = adapter.digest({"authored_registry_sha256": AUTHORED_REGISTRY_SHA256,
                                "agency_raw_sha256": adapter.USGS_RAW_SHA256,
                                "agency_profile": adapter.USGS_PROFILE})
    return {"reference_sha256": reference_sha, "source_registry_sha256": source_sha,
            "runtime_sha256": _file_sha(Path(adapter.__file__)),
            "native_sha256": _file_sha(adapter.NATIVE) if adapter.NATIVE.is_file() else None}


def _metrics() -> dict:
    return {category: {"eligible": 0, "measured": 0, "passed": 0, "failed": 0, "unmeasured": 0}
            for category in CATEGORIES.values()}


def run(*, require_native: bool = True) -> dict:
    """Run the fixed suite. `require_native` never upgrades a Python-only comparison.

    The flag is accepted for callers/CLI policy; missing native always appears as
    UNMEASURED in the returned audit, so a valid failure receipt remains viewable.
    """
    if type(require_native) is not bool:
        raise ValueError("require_native must be a Boolean")
    references = load_reference()
    installed = identity()
    report = {"schema": "nabt.epistemic-measurement-benchmark.v1", "law_id": adapter.LAW_ID,
              **installed, "groups": {group: {"case_count": 0, "metrics": _metrics()}
                                       for group in ("authored_controls", "agency_record")},
              "cases": [], "all_cases_native_checked": False, "hidden_motive_measured": False,
              "free_arabic_acquisition_measured": False, "whole_arabic_complete": False,
              "world_truth_established": False}
    for reference in references:
        # Deliberately do not pass reference ID, expected labels, category or gold text.
        execution = adapter.execute_request(reference["input"], source_profile=reference["source_profile"])
        native_checked = execution["native_checked"] is True and execution["certificate_checked"] is True
        if native_checked and execution["execution"]["native_sha256"] != installed["native_sha256"]:
            native_checked = False
            execution["execution"]["error"] = "NATIVE_CHANGED_DURING_SUITE"
        observed = execution["observed"] if native_checked else None
        comparison = "UNMEASURED" if not native_checked else "PASS" if observed == reference["expected"] else "FAIL"
        case = {"id": reference["id"], "group": reference["group"],
                "query": deepcopy(reference["input"]["query"]), "expected": deepcopy(reference["expected"]),
                "observed": observed, "comparison": comparison, "native_checked": native_checked,
                "certificate_checked": native_checked, "proof_scope": execution["proof_scope"],
                "source_bindings": execution["source_bindings"], "evidence_class": execution["evidence_class"],
                "execution": execution["execution"]}
        case["receipt_sha256"] = adapter.digest(case)
        report["cases"].append(case)
        group = report["groups"][reference["group"]]
        group["case_count"] += 1
        metric = group["metrics"][reference["metric_category"]]
        metric["eligible"] += 1
        if comparison == "UNMEASURED":
            metric["unmeasured"] += 1
        else:
            metric["measured"] += 1
            metric["passed" if comparison == "PASS" else "failed"] += 1
    if identity() != installed:
        raise RuntimeError("Epistemic execution identity changed during suite")
    if any(case["execution"]["native_sha256"] not in (None, installed["native_sha256"]) for case in report["cases"]):
        raise RuntimeError("Mixed native executable identities in suite")
    report["all_cases_native_checked"] = all(case["native_checked"] for case in report["cases"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-native", action="store_true")
    args = parser.parse_args()
    report = run(require_native=args.require_native)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    failed = any(case["comparison"] == "FAIL" for case in report["cases"])
    missing = args.require_native and not report["all_cases_native_checked"]
    return 1 if failed or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
