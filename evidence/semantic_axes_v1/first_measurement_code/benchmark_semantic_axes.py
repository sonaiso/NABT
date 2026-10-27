"""Score independent semantic axes without turning abstention into success.

This is an authored diagnostic, not population accuracy or a completeness
theorem. The runtime receives only case.input. Its Python replay and each
reference comparison remain visibly separate from any Lean-native proof.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from tools import semantic_axes as adapter

REFERENCE = ROOT / "evidence/semantic_axes_v1/reference.json"
REFERENCE_SHA256 = "18d59350e622df23d67f5f8f44864aeeee9817515a838fb05911b85b4a5a3625"
SOURCE_REVIEW_SHA256 = "ce482cf5367ec8c7af62dba10eeb1a0948e481f2c3914f4a1b665017c1e535c7"
AXES = ("syntax", "readings", "reference", "motive", "world")
STATUSES = ("PASS", "FAIL", "UNMEASURED", "NOT_APPLICABLE")
STATEMENTS = {
    "syntax": "مطابقة التحليل النحوي بالمرجع المستقل.",
    "readings": "استرجاع القراءات المطلوبة وحفظ اختلافاتها دون قراءة ممنوعة.",
    "reference": "حسم المرجع أو حفظ بدائله وفق المقام المعلن.",
    "motive": "فهم الدافع من دليل مستقل عن الصنف النحوي.",
    "world": "التحقق المستقل من صدق القضية في الواقع الخارجي.",
}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def load_reference(path=REFERENCE):
    path = Path(path)
    frozen = path.with_suffix(".sha256").read_text(encoding="utf-8").split()[0]
    if frozen != REFERENCE_SHA256 or digest(path) != frozen:
        raise ValueError("Frozen semantic-axes reference digest mismatch")
    freeze = _strict_json(path.parent / "freeze.json")
    reference = _strict_json(path)
    cases = reference.get("cases")
    if type(cases) is not list or not cases:
        raise ValueError("Reference requires a nonempty cases array")
    if (freeze.get("schema") != "nabt.semantic-axes.freeze.v1" or
            freeze.get("reference_sha256") != frozen or
            freeze.get("source_review_sha256") != SOURCE_REVIEW_SHA256 or
            digest(path.parent / "source_review.json") != SOURCE_REVIEW_SHA256 or
            type(freeze.get("case_count")) is not int or freeze["case_count"] != len(cases) or
            freeze.get("frozen_before_adapter_execution") is not True or
            freeze.get("expected_labels_derived_from_runtime") is not False):
        raise ValueError("Reference freeze does not bind this source review and case suite")
    ids = set()
    for case in cases:
        if type(case) is not dict or type(case.get("id")) is not str or case["id"] in ids:
            raise ValueError("Case IDs must be unique strings")
        ids.add(case["id"])
        adapter.build_request(case)
        if type(case.get("expected")) is not dict or set(case["expected"]) != set(AXES):
            raise ValueError("Each reference case must declare five independent axes")
        for name, expected in case["expected"].items():
            if type(expected) is not dict:
                raise ValueError("Expected axis must be an object: " + name)
    return reference, frozen, freeze


def _lemma(value):
    # Compare lexical identity only: source tokens, spans and roles remain exact.
    return "".join(c for c in unicodedata.normalize("NFC", value)
                   if c not in "ًٌٍَُِّْٰ") if type(value) is str else value


def _matches(actual, expected):
    if type(actual) is not dict or type(expected) is not dict:
        return False
    for key, value in expected.items():
        if key not in actual:
            return False
        observed = actual.get(key)
        if key == "predicate":
            observed, value = _lemma(observed), _lemma(value)
        if type(observed) is not type(value) or observed != value:
            return False
    return True


def _result(status, expected, observed, reason):
    return {"status": status, "expected": deepcopy(expected),
            "observed": deepcopy(observed), "reason": reason}


def _syntax(expected, observed):
    required = expected.get("required_roles", [])
    ok = bool(observed) and any(
        a.get("clause_form") == expected.get("clause_form") and
        all(any(_matches(role, want) for role in a.get("roles", [])) for want in required)
        for a in observed) and all(a.get("clause_form") == expected.get("clause_form") for a in observed)
    return _result("PASS" if ok else "FAIL", expected, observed,
                   "REFERENCE_MATCH" if ok else "EXPECTED_ANALYSIS_NOT_RETURNED")


def _readings(expected, observed):
    rows = observed["readings"]
    required, forbidden = expected.get("required", []), expected.get("forbidden", [])
    found = [any(_matches(row, want) for row in rows) for want in required]
    excluded = [not any(_matches(row, want) for row in rows) for want in forbidden]
    positive = bool(required) and bool(rows)
    selection = expected.get("selection") == observed["reading_selection"]
    ok = positive and all(found) and all(excluded) and selection
    actual = {"readings": rows, "selection": observed["reading_selection"],
              "required_found": found, "forbidden_absent": excluded,
              "semantic_alternative_counts": observed["semantic_alternative_counts"],
              "required_reading_recall": {"matched": sum(found), "eligible": len(required),
                  "rate": sum(found) / len(required) if required else None},
              "full_reading_precision": None,
              "precision_scope": "Only explicitly forbidden readings are checked; this reference does not enumerate every possible reading."}
    return _result("PASS" if ok else "FAIL", expected, actual,
                   "REFERENCE_MATCH" if ok else "REQUIRED_READING_OR_SELECTION_NOT_RETURNED")


def _reference(expected, observed):
    rows = [r for r in observed if r.get("surface") == expected.get("surface")]
    wanted = set(expected.get("target_ids", []))
    state = expected.get("status")
    resolved = {r["bound_entity_id"] for r in rows if r["status"] == "RESOLVED" and r["bound_entity_id"] is not None}
    candidates = {target for r in rows for target in r["candidate_entity_ids"]}
    if state == "resolved":
        ok = (bool(rows) and len(wanted) == 1 and resolved == wanted and candidates == wanted and
              all(r["status"] == "RESOLVED" and set(r["candidate_entity_ids"]) == wanted for r in rows))
    elif state == "ambiguous":
        ok = (bool(rows) and len(wanted) > 1 and not resolved and candidates == wanted and
              all(r["status"] == "AMBIGUOUS" and set(r["candidate_entity_ids"]) == wanted for r in rows))
    elif state == "unresolved":
        ok = (bool(rows) and not resolved and not candidates and not wanted and
              all(r["status"] == "NO_CANDIDATE" for r in rows))
    else:
        ok = False
    return _result("PASS" if ok else "FAIL", expected, rows,
                   "REFERENCE_MATCH" if ok else "REFERENCE_NOT_ACQUIRED_AS_EXPECTED")


def score_case(case, execution):
    request_sha = adapter.identity(adapter.build_request(case))
    receipt = execution.get("replay_receipt")
    checked = (execution.get("schema") == "nabt.semantic-axes-observation.v1" and
        execution.get("executed") is True and execution.get("replay_checked") is True and
        execution.get("input_sha256") == request_sha and
        execution.get("context_sha256") == adapter.identity(case["input"].get("context", {})) and
        execution.get("lean_native_checked") is False and
        execution.get("verification_kind") == "PYTHON_REPLAY" and
        type(receipt) is dict and receipt.get("input_sha256") == request_sha and
        receipt.get("replay", {}).get("valid") is True and
        receipt.get("replay", {}).get("status") == "VERIFIED" and
        execution.get("replay_receipt_sha256") == adapter.identity(receipt))
    observed = execution.get("observed") if checked else None
    results, claims = {}, []
    for axis in AXES:
        expected = case["expected"][axis]
        if expected.get("status") == "not_applicable":
            result = _result("NOT_APPLICABLE", expected, None, "EXCLUDED_BY_REFERENCE_SCOPE")
        elif axis in ("motive", "world"):
            result = _result("UNMEASURED", expected, None,
                "MOTIVE_CAPABILITY_NOT_IMPLEMENTED" if axis == "motive" else "WORLD_VERIFICATION_NOT_IMPLEMENTED")
        elif not checked or type(observed) is not dict:
            result = _result("UNMEASURED", expected, None, "RUNTIME_OR_REPLAY_UNAVAILABLE")
        elif axis == "syntax":
            result = _syntax(expected, observed["syntax"])
        elif axis == "readings":
            result = _readings(expected, observed)
        else:
            result = _reference(expected, observed["references"])
        results[axis] = result
        if result["status"] == "NOT_APPLICABLE":
            continue
        measured = result["status"] in ("PASS", "FAIL")
        claim_id = case["id"] + ":" + axis
        verification = {"kind": "PYTHON_REPLAY" if measured else "NOT_CHECKED",
            "checked": measured,
            "claim_id": claim_id, "input_sha256": request_sha,
            "scope": ("فُحصت مقارنة هذه الدعوى بالمرجع بعد إعادة تنفيذ Python على النص والمقام المحددين؛ لا تثبت صحة لغوية عامة أو واقعًا خارجيًا، ولم ينفذ Lean لهذه الدعوى."
                      if measured else "لا يوجد قياس منفذ لهذه الدعوى؛ لا يُدّعى لها برهان."),
            "theorem_references": []}
        if measured:
            verification["certificate_sha256"] = adapter.identity({
                "input_sha256": request_sha, "claim_id": claim_id, "axis": axis,
                "result": result, "replay_receipt_sha256": execution["replay_receipt_sha256"]})
        claims.append({"id": claim_id, "axis": axis,
                       "statement": STATEMENTS[axis], "status": result["status"],
                       "verification": verification})
    safety = {"no_world_promotion": "UNMEASURED", "no_motive_promotion": "UNMEASURED"}
    if checked and observed is not None:
        safety["no_world_promotion"] = "PASS" if observed["world_truth"] == "NOT_ESTABLISHED" else "FAIL"
        # No motive recognizer exists: an omitted field is not a semantic test.
    return {"id": case["id"], "family": case.get("family", "unspecified"),
            "input": deepcopy(case["input"]), "context_id": adapter.identity(case["input"].get("context", {})),
            "case_input_sha256": request_sha,
            "axis_results": results, "claims": claims, "safety_checks": safety,
            "safety_notes": {"no_world_promotion": "Tests the explicit output authority boundary, not external truth.",
                "no_motive_promotion": "Motive inference is not implemented; omission by design does not establish semantic detection of unsupported motives."},
            "execution": execution}


def summarize(rows):
    result = {}
    for axis in AXES:
        states = [r["axis_results"][axis]["status"] for r in rows]
        passed, failed, unmeasured = (states.count(s) for s in ("PASS", "FAIL", "UNMEASURED"))
        measured, eligible = passed + failed, passed + failed + unmeasured
        result[axis] = {"eligible": eligible, "measured": measured, "passed": passed,
            "failed": failed, "unmeasured": unmeasured,
            "rate": passed / measured if measured else None,
            "measurement_coverage": measured / eligible if eligible else None}
    return result


def historical_natural_use():
    path = ROOT / "evidence/natural_use_gap_v1/measurement.json"
    raw = _strict_json(path)
    return {"status": "HISTORICAL_NOT_RERUN", "path": str(path.relative_to(ROOT)),
            "sha256": digest(path), "full_case_success": raw["natural_after"]["full_case_success"],
            "scope": raw["scope"], "included_in_new_denominators": False}


def run(reference_path=REFERENCE, *, executor=None):
    reference, frozen, freeze = load_reference(reference_path)
    executor = adapter.execute_request if executor is None else executor
    requests = [adapter.build_request(case) for case in reference["cases"]]
    rows = []
    for case, request in zip(reference["cases"], requests, strict=True):
        try:
            execution = executor(deepcopy(request))
        except Exception as error:
            execution = {"executed": False, "replay_checked": False, "observed": None,
                         "input_sha256": adapter.identity(request),
                         "error": {"type": type(error).__name__, "code": getattr(error, "code", "RUNTIME_UNAVAILABLE")}}
        rows.append(score_case(case, execution))
    snapshot = adapter.runtime_snapshot()
    return {"schema": "nabt.semantic-axes-benchmark.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "مجموعة تشخيصية مؤلفة مستقلة ومجمّدة؛ كل مقام مستقل، ونجاح المطابقة لا يثبت صدق الواقع أو الدافع أو اكتمال العربية.",
            "case_count": len(rows), "reference_sha256": frozen,
            "adapter_sha256": digest(adapter.__file__), "input_suite_sha256": adapter.identity(requests),
            "scorer_sha256": digest(__file__), "runtime_source_sha256": adapter.identity(snapshot),
            "runtime_sources": snapshot, "reference_freeze": freeze,
            "axes": summarize(rows), "cases": rows,
            "historical_natural_use": historical_natural_use(),
            "all_arabic_complete": False, "lean_native_checked": False,
            "metric_note": "rate = passed / measured; UNMEASURED is retained in eligible, and zero measured yields null. Safety checks never raise understanding scores."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": report["case_count"], "axes": report["axes"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
