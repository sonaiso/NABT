#!/usr/bin/env python3
"""Independent artifact-only review of final construction residuals.

No runtime or evaluator module is imported or executed. This compares the
retained baseline, ordered checks, raw records, and exact frozen inputs. All
written files are new review evidence; no source, gold, or evaluator changes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import tarfile
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[3]
FINAL_SHA256 = "020cf93ac66414ede030474813a6b6643bf7fac79242d72c05378f0de1391acb"
FREEZE_SHA256 = "1818fc27f076535734d9d9e90a857683f27d464f0a205637e7231cd6e870c40c"
EXPECTED_FAILURES = {
    "CON-Z02": "complete_construction role:0 role:1 role:2 roles_same_analysis relation:0 relations_same_analysis scope:0 coherent_analysis question:0 question:1".split(),
    "CON-Z07": "complete_construction role:0 role:1 role:2 roles_same_analysis scope:0 coherent_analysis question:0 question:1".split(),
    "CON-Z10": ["question:0"],
    "CON-N01": "complete_construction qualification:0 coherent_analysis question:0 question:1".split(),
    "CON-M01": "complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1".split(),
    "CON-M03": "complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1".split(),
}
DIAGNOSES = {
    "CON-Z02": {"kind": "UNACQUIRED_OCCURRENCE_SENSE", "explanation": "حسب has qualified lexical candidates but its cognitive two-object sense is not independently established in this occurrence. The context names the people; it does not supply that sense.", "observed_obligation": "POLYSEMOUS_OPERATOR_SENSE_REQUIRES_INDEPENDENT_CONTEXT"},
    "CON-Z07": {"kind": "UNACQUIRED_OCCURRENCE_SENSE", "explanation": "علم has qualified lexical candidates but the cognitive two-object sense is not independently established. The grammar family and lemma do not discharge the occurrence-level sense premise.", "observed_obligation": "POLYSEMOUS_OPERATOR_SENSE_REQUIRES_INDEPENDENT_CONTEXT"},
    "CON-Z10": {"kind": "FROZEN_QUESTION_OUTSIDE_DECLARED_CLASSICAL_NORM", "explanation": "The negative matrix statement is complete and retains one scoped claim; only the frozen hal+ma question fails. Its inquiry carries NEGATIVE_POLAR_QUESTION_REQUIRES_LICENSE and the answer safely defers. The question-source audit records the selected classical norm and the inference applying it here. The original question and expected result remain unchanged.", "source_audit": "evidence/arabic_coverage/oracle_audit_v1/question_input_audit.json", "observed_question_obligation": "NEGATIVE_POLAR_QUESTION_REQUIRES_LICENSE"},
    "CON-N01": {"kind": "UNACQUIRED_EXACT_NAME_REFERENCE", "explanation": "The input الْمُعَلِّمُ contains an explicit shadda, while the frozen context name المعلم does not witness it. Syntax roles and the naat relation pass, but the conservative exact-name reference has NO_CANDIDATE. No alias or identity premise is invented.", "observed_obligation": "REFERENCE_NOT_UNIQUELY_LICENSED"},
    "CON-M01": {"kind": "UNACQUIRED_SEMANTIC_USE_FRAME", "explanation": "ازداد/نشاطا has no acquired nisba frame in the installed policy. The raw report has no viable analysis; therefore this is a code/source inspection diagnosis, not an emitted tamyiz obligation. A noun label or expected role does not supply the semantic use.", "observation_caveat": "No viable analysis; no emitted frame-specific obligation."},
    "CON-M03": {"kind": "UNACQUIRED_UNIT_GENERALIZATION", "explanation": "The replayed امتلأ example witnesses ماء. The target لبنا needs an independent frame or a justified semantic generalization, which has not been acquired. The existing candidate remains pending instead of treating any noun as tamyiz.", "observed_obligation": "TAMYIZ_VERSUS_OTHER_NOMINAL_USE_REQUIRES_SOURCE_FRAME"},
}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return sha256(raw).hexdigest()


def record(path, raw=None):
    raw = path.read_bytes() if raw is None else raw
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": digest(raw)}


def save(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
    return record(path, raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-report", type=Path,
        default=ROOT / "artifacts/local/arabic_coverage_construction_final_strict_v2.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    final_path = args.final_report.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    raw_final = final_path.read_bytes()
    assert digest(raw_final) == FINAL_SHA256
    final = json.loads(raw_final)
    baseline_path = ROOT / "evidence/arabic_coverage/baseline_v1.json"
    baseline_record = json.loads(baseline_path.read_bytes())
    original_archive = ROOT / baseline_record["source_archive"]
    assert digest(original_archive.read_bytes()) == baseline_record["source_archive_sha256"]
    with ZipFile(original_archive) as archive:
        baseline_raw = archive.read(baseline_record["suites"]["construction"]["archive_entry"])
    assert digest(baseline_raw) == baseline_record["suites"]["construction"]["report_sha256"]
    baseline = json.loads(baseline_raw)
    assert (baseline["passed"], baseline["total"], baseline["measurement_valid"]) == (71, 86, True)
    assert (final["passed"], final["total"], final["measurement_valid"]) == (80, 86, True)
    assert final["gate_mode"] == "strict" and final["strict_pass"] is False and final["gate_pass"] is False
    for key in ("execution_errors", "question_execution_errors", "finalization_errors", "gate_integrity_errors"):
        assert final[key] == [], key
    assert final["false_accept_count"] == final["false_accept_case_count"] == 0
    assert final["gold_freeze_sha256"] == baseline["gold_freeze_sha256"]

    gold_path = ROOT / "evidence/constructions/independent_freeze_v1.json"
    gold_raw = gold_path.read_bytes()
    assert digest(gold_raw) == final["gold_freeze_sha256"]
    for item in json.loads(gold_raw)["files"]:
        raw = (ROOT / item["path"]).read_bytes()
        assert len(raw) == item["bytes"] and digest(raw) == item["sha256"]
    material = json.loads((ROOT / "evidence/constructions/independent_cases_v1.json").read_bytes())
    expected_ids = [case["id"] for case in material["cases"]]
    assert len(expected_ids) == len(set(expected_ids)) == 86
    assert [c["id"] for c in baseline["cases"]] == [c["id"] for c in final["cases"]] == expected_ids
    frozen_cases = {case["id"]: case for case in material["cases"]}
    old_cases = {case["id"]: case for case in baseline["cases"]}
    new_cases = {case["id"]: case for case in final["cases"]}
    assert [{"id": c["id"], "failed_checks": [f["check"] for f in c["failures"]]}
            for c in baseline["cases"] if not c["passed"]] == baseline_record["suites"]["construction"]["failed_cases"]
    regressions, new_failed_checks, inventory, fixed = [], [], [], []
    for case_id in expected_ids:
        old, new = old_cases[case_id], new_cases[case_id]
        old_names = [check["check"] for check in old["checks"]]
        names = [check["check"] for check in new["checks"]]
        assert names == old_names and len(names) == len(set(names))
        assert new["failures"] == [check for check in new["checks"] if check["passed"] is False]
        assert all(type(check["passed"]) is bool for check in new["checks"])
        assert new["passed"] is (not new["failures"])
        assert new["false_accepts"] == []
        inventory.append({"id": case_id, "mode": new["mode"], "checks": names})
        if old["passed"] and not new["passed"]:
            regressions.append(case_id)
        added = sorted({f["check"] for f in new["failures"]} - {f["check"] for f in old["failures"]})
        if added:
            new_failed_checks.append({"id": case_id, "checks": added})
        if not old["passed"] and new["passed"]:
            fixed.append(case_id)
    assert not regressions and not new_failed_checks and len(fixed) == 9
    assert {c["id"]: [f["check"] for f in c["failures"]]
            for c in final["cases"] if not c["passed"]} == EXPECTED_FAILURES

    raw_path = final_path.with_name(final["raw_log"]["filename"])
    compressed = raw_path.read_bytes()
    assert len(compressed) == final["raw_log"]["bytes"] and digest(compressed) == final["raw_log"]["sha256"]
    decoded = gzip.decompress(compressed)
    assert len(decoded) == final["raw_log"]["decoded_bytes"] and digest(decoded) == final["raw_log"]["decoded_sha256"]
    lines = decoded.splitlines(keepends=True)
    assert len(lines) == final["raw_log"]["record_count"] == 87
    records, observed_inventory = [], []
    for index, line in enumerate(lines):
        row = json.loads(line)
        assert wire(row) + b"\n" == line
        records.append(row)
        observed_inventory.append({"index": index, "bytes": len(line), "sha256": digest(line),
            "kind": "model" if "model_summary" in row else "case", "id": row.get("id")})
    assert observed_inventory == final["raw_log"]["record_inventory"]
    assert digest(wire(observed_inventory)) == final["raw_log"]["record_inventory_sha256"]
    raw_cases = {r["id"]: r for r in records if "id" in r}
    assert len(raw_cases) == 86 and list(raw_cases) == expected_ids
    question_count = 0
    for case_id, raw in raw_cases.items():
        case = frozen_cases[case_id]
        assert raw["score"] == new_cases[case_id]
        assert raw["verification"]["valid"] is True
        report = raw["report"]
        assert report["source_text"] == case["input"]["text"]
        assert report["source_sha256"] == digest(case["input"]["text"].encode())
        assert report["source_id"] == case["input"]["source_id"] and report["scope"] == case["input"]["scope"]
        expected_questions = case["expected"].get("questions", [])
        assert len(raw["questions"]) == len(expected_questions)
        for expected, observed in zip(expected_questions, raw["questions"], strict=True):
            assert "error" not in observed and observed["verification"]["valid"] is True
            assert observed["answer"]["question_text"] == expected["text"]
            assert observed["inquiry"]["source_text"] == expected["text"]
            question_count += 1
    assert question_count == final["raw_log"]["question_count"] == 106

    runtime_path = ROOT / final["snapshot"]["runtime_freeze"]
    runtime_raw = runtime_path.read_bytes()
    assert digest(runtime_raw) == FREEZE_SHA256 == final["snapshot"]["runtime_freeze_sha256"]
    runtime = json.loads(runtime_raw)
    assert len(runtime["files"]) == 77
    assert runtime["snapshot_sha256"] == final["snapshot"]["runtime_snapshot_sha256"]
    assert runtime["archive_sha256"] == final["snapshot"]["runtime_archive_sha256"]
    code_path = final_path.with_name(final["code_archive"]["filename"])
    code_raw = code_path.read_bytes()
    assert digest(code_raw) == final["code_archive"]["sha256"]
    snapshot = final["snapshot"]["files"]
    assert digest(wire(snapshot)) == final["snapshot"]["measured_snapshot_sha256"]
    assert snapshot[:77] == runtime["files"]
    with tarfile.open(code_path, "r:gz") as archive:
        assert {m.name for m in archive.getmembers()} == {r["path"] for r in snapshot}
        assert len(archive.getmembers()) == len(snapshot)
        for item in snapshot:
            member = archive.getmember(item["path"])
            assert member.isfile()
            data = archive.extractfile(member).read()
            assert len(data) == item["bytes"] and digest(data) == item["sha256"]

    residuals = []
    for case_id in EXPECTED_FAILURES:
        raw = raw_cases[case_id]
        report = raw["report"]
        analyses = [a for clause in report["clauses"] for a in clause["analyses"]]
        obligations = sorted({o for a in analyses for o in a["obligations"]})
        diagnosis = DIAGNOSES[case_id]
        if "observed_obligation" in diagnosis:
            assert diagnosis["observed_obligation"] in obligations
        questions = []
        for expected, q in zip(frozen_cases[case_id]["expected"].get("questions", []), raw["questions"], strict=True):
            qobligations = sorted({o for c in q["inquiry"]["clauses"] for a in c["analyses"] for o in a["obligations"]})
            questions.append({"text": expected["text"], "expected": expected["outcome"],
                "status": q["answer"]["status"], "proof_count": len(q["answer"]["proofs"]),
                "counterproof_count": len(q["answer"]["counterproofs"]),
                "missing_premises": q["answer"]["missing_premises"], "inquiry_obligations": qobligations})
        if case_id == "CON-Z10":
            assert report["status"] == "LICENSED_DISCOURSE" and len(report["claims"]) == 1
            assert questions[0]["inquiry_obligations"] == ["NEGATIVE_POLAR_QUESTION_REQUIRES_LICENSE"]
            assert questions[1]["status"] == "UNKNOWN"
        if case_id == "CON-M01":
            assert not analyses
        residuals.append({"id": case_id, "input": frozen_cases[case_id]["input"],
            "observed": new_cases[case_id]["observed"], "failures": new_cases[case_id]["failures"],
            "obligations": obligations, "questions": questions, "diagnosis": diagnosis})

    preserved = [save(output / final_path.name, raw_final), save(output / raw_path.name, compressed),
                 save(output / code_path.name, code_raw)]
    failure_signatures = [{"id": r["id"], "failures": r["failures"]} for r in residuals]
    receipt = {"schema": "nabt.construction-residual-review.v2", "utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "empirical_audit collaborating agent; implementation participant, independent artifact comparison, shared workspace",
        "method": "Read-only comparison of retained baseline and final artifacts; no runtime/evaluator imports, reruns, or source/gold edits.",
        "verified": True, "baseline_archive": record(original_archive), "baseline_receipt": record(baseline_path),
        "baseline_report_sha256": digest(baseline_raw), "final_report_sha256": digest(raw_final),
        "runtime_freeze_sha256": FREEZE_SHA256, "runtime_file_count": 77, "measured_archive_files": len(snapshot),
        "gold_freeze_sha256": digest(gold_raw), "gold_unchanged": True,
        "case_order_equal": True, "ordered_check_inventory_equal": True,
        "ordered_case_check_inventory": inventory, "ordered_case_check_inventory_sha256": digest(wire(inventory)),
        "raw_record_count": len(records), "raw_case_count": len(raw_cases), "raw_question_count": question_count,
        "all_raw_scores_equal_final_report": True, "all_recorded_report_and_answer_replays_valid": True,
        "baseline_score": {"passed": 71, "total": 86}, "final_score": {"passed": 80, "total": 86},
        "baseline_by_mode": baseline["by_mode"], "final_by_mode": final["by_mode"],
        "nine_improved_cases": fixed, "new_failed_cases": regressions, "new_failed_checks": new_failed_checks,
        "remaining_failed_cases": list(EXPECTED_FAILURES), "remaining_failed_check_count": sum(map(len, EXPECTED_FAILURES.values())),
        "remaining_failures": residuals, "exact_failure_payload_signatures": failure_signatures,
        "exact_failure_payload_signatures_sha256": digest(wire(failure_signatures)),
        "strict_pass": False, "gate_pass_at_measurement": False,
        "false_accept_count_in_declared_checks": 0, "execution_errors": [],
        "scope": ["The frozen suite has 43 positive, 6 ambiguity, 31 boundary and 6 replay cases; 80/86 is not 80 positive comprehension examples.",
            "Seven positive cases and two ambiguity cases improve. B01/B02 pass by retaining pending alternatives and prohibiting unsupported judgments.",
            "Five positive residuals need independent semantic/reference premises. Z10's remaining failure concerns its unchanged question under the declared classical norm.",
            "Zero recorded false accepts applies to this suite's declared forbidden claims/checks, not every possible wrong interpretation.",
            "The evaluator changed through independently retained adapter reviews; the frozen input bytes, ordered cases and check names did not change.",
            "A narrow later regression gate must remain distinct from strict_pass and from completeness or world truth."],
        "preserved_artifacts": preserved,
        "reproducer": record(Path(__file__).resolve())}
    save(output / "review.json", (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"verified": True, "failed_cases": list(EXPECTED_FAILURES),
        "failed_checks": receipt["remaining_failed_check_count"], "new_failures": 0,
        "raw_records": len(records), "questions": question_count, "review": str(output / "review.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
