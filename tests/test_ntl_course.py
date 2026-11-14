"""An independently authored key for worksheets, source witnesses and transfer."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway
from tools.lexical_training import ntl_course as course, teaching

ROOT = Path(__file__).resolve().parents[1]
NATIVE = all((ROOT / "formal/.lake/build/bin" / n).is_file() for n in
             ("temporalContextProbe", "scopedCompositionProbe", "epistemicMeasurement"))
if os.environ.get("NABT_REQUIRE_IO_GATEWAY_NATIVE") == "1" and not NATIVE:
    raise RuntimeError("NTL admission requires temporalContextProbe, scopedCompositionProbe and epistemicMeasurement")


KEY = {
    "C1": (5, "ALIGNED", 3, True, "aligned_and_matches", [2, 3]),
    "C2": (3, "ALIGNED", -5, False, "implementation_disagrees", [2, 3]),
    "C3": (6, "ALIGNED", 5, True, "aligned_and_matches", [2, 3]),
    "C4": (6, "MISMATCH", 3, True, "inputs_mismatch", [2, 3]),
    "P1": ("سائل", "ALIGNED", True, True, "aligned_and_matches", [2, 3]),
    "P2": ("صلب", "ALIGNED", False, False, "implementation_disagrees", [2, 3]),
    "P3": ("صلب", "OPEN", True, True, "missing_endpoint", [2]),
    "P4": ("غاز", "CONFLICT", True, True, "observations_conflict", [2, 3, 4]),
    "P5": ("غاز", "MISMATCH", False, False, "inputs_mismatch", [2, 3]),
}


def answers(cid):
    *cards, reason, lines = KEY[cid]
    return dict(zip(course.ntl.DOMAINS, cards), bridge={"reason": reason, "lines": lines})


def session(action, focus="integrated", **inputs):
    return dict(schema=course.SCHEMA, action=action, focus=focus, **inputs)


class Worksheets(unittest.TestCase):
    def test_scoped_worksheet_does_not_call_graders_or_include_solutions(self):
        with patch.object(course, "evidence", side_effect=AssertionError):
            for lane in course.LANES:
                report = teaching.run_lesson(session("worksheet", lane, cases=["C3", "P5"]))
                for sheet in report["cases"].values():
                    self.assertEqual(list(sheet["questions"]), [lane])
                    self.assertFalse(set(sheet) & {"solution", "evidence", "grades", "domain_trace"})
                    self.assertEqual("source_lines" in sheet, lane in ("linguistic", "physical", "bridge"))
                    self.assertEqual("program" in sheet, lane in ("programming", "bridge"))

    def test_validation(self):
        for request in (session("worksheet", cases=["P2", "P2"]), session("teach", cases=["U9"]),
                        session("assess", "formal", submissions={"P1": {"formal": 1}}),
                        session("assess", "formal", submissions={"C1": {"formal": False}}),
                        session("assess", "linguistic", submissions={"P1": {"formal": True}}),
                        session("assess", submissions={"P1": {"bridge": {"reason": "missing_endpoint", "lines": [2,2]}}}),
                        session("assess", submissions={"P1": {}}, scores=[1]),
                        session("induce", "bridge", examples=["P1"], probes=["P1"]),
                        session("induce", "bridge", examples=[], probes=[])):
            self.assertEqual(teaching.run_lesson(request)["status"], "INVALID_INPUT")


@unittest.skipUnless(NATIVE, "Build io-gateway owners")
class Teaching(unittest.TestCase):
    def test_entire_bank_and_transfer_denominators(self):
        self.assertEqual(set(KEY), set(course.catalog()))
        bank = {cid: answers(cid) for cid in KEY}
        r = teaching.run_lesson(session("assess", submissions=bank))
        self.assertEqual(sum(x["status"] == "CORRECT" for case in r["cases"].values()
                             for x in case["grades"].values()), 45)
        for row in r["progress"].values():
            self.assertTrue(row["demonstrated_on_bank"])
            self.assertEqual(row["required_transfer_cases"], 7)
            self.assertFalse({"C1","P1"} & set(row["correct_transfer_cases"]))

    def test_partial_revised_answers_and_wrong_witness(self):
        incomplete = {"C2": {"bridge": {"reason": "implementation_disagrees", "lines": [2, 4]}}}
        r = teaching.run_lesson(session("assess", submissions=incomplete))
        self.assertEqual(r["cases"]["C2"]["grades"]["bridge"]["status"], "REVISE")
        self.assertEqual(r["cases"]["C2"]["grades"]["formal"]["status"], "UNANSWERED")
        revised = deepcopy(incomplete)
        revised["C2"]["bridge"]["lines"] = [3, 2]
        result = teaching.run_lesson(session("assess", "bridge", submissions=revised))
        self.assertEqual(result["progress"]["bridge"]["correct_transfer_cases"], ["C2"])
        self.assertFalse(result["progress"]["bridge"]["demonstrated_on_bank"])

    def test_teacher_trace_contradiction_withdrawal_and_conflict(self):
        r = teaching.run_lesson(session("teach", cases=["P2", "P3", "P4"]))
        cases = r["cases"]
        self.assertEqual(cases["P2"]["report_checks"][0]["status"], "REFUTED")
        for cid in ("P2", "P3", "P4"):
            self.assertEqual(cases[cid]["solution"], answers(cid))
            self.assertTrue(cases[cid]["evidence"]["arithmetic"]["native_check"]["native_checked"])
        self.assertEqual(len(cases["P4"]["evidence"]["record"]["conflicts"]), 1)

    def test_nominal_relabelling_and_native_failure(self):
        case = course.catalog()["P1"]
        with patch.dict(course.PHASES, {"صلب": 71, "سائل": 9, "غاز": 3}):
            self.assertIs(course.phase_result(case)["cards"]["formal"]["answer"], True)
        with patch.object(course.scoped_composition, "evaluate",
                          return_value={"chain_complete": False, "status":"DEFER", "native_check":None}):
            r = teaching.run_lesson(session("assess", submissions={"P1": answers("P1")}))
        grades = r["cases"]["P1"]["grades"]
        self.assertEqual([grades[k]["status"] for k in course.LANES],
                         ["CORRECT","CORRECT","UNGRADABLE","UNGRADABLE","UNGRADABLE"])

    def test_transfer_and_unseen_pattern(self):
        request = json.loads((ROOT/"examples/io_gateway/ntl_course_induction.json").read_text())
        r = teaching.run_lesson(request["payload"]["lesson"])
        self.assertEqual(r["candidate_counts"], [10,4,2,1])
        self.assertTrue(all(p["assessment"] == "CORRECT" for p in r["probes"].values()))
        self.assertEqual(r["probes"]["P5"]["possible"], [False])
        self.assertFalse(r["probes"]["P5"]["feature_pattern_seen"])
        request["payload"]["lesson"].update(examples=[], probes=["P5"])
        r = teaching.run_lesson(request["payload"]["lesson"])
        self.assertEqual(r["candidate_counts"], [10])
        self.assertEqual(r["probes"]["P5"]["assessment"], "UNDECIDED")

    def test_gateway_replay_and_tampering(self):
        request = json.loads((ROOT/"examples/io_gateway/ntl_course_assessment.json").read_text())
        receipt = gateway.run(request)
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])
        receipt["execution"]["owner_result"]["progress"]["bridge"]["demonstrated_on_bank"] = True
        self.assertFalse(gateway.accept_output(receipt, expected_request=request)["valid"])

    def test_published_teacher_worksheet_and_induction_through_gateway(self):
        for action in ("worksheet", "teach", "induction"):
            with self.subTest(action=action):
                request = json.loads((ROOT / f"examples/io_gateway/ntl_course_{action}.json").read_text())
                receipt = gateway.run(request)
                self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])
                result = receipt["execution"]["owner_result"]
                self.assertEqual(result["status"], "COURSE_SESSION")
                self.assertTrue(result["execution_measured"])
                if action == "worksheet":
                    self.assertEqual(set(result["cases"]), {"C2", "P3"})
                    for sheet in result["cases"].values():
                        self.assertFalse({"grades", "evidence", "solution"} & set(sheet))
                elif action == "teach":
                    for cid in ("C1", "P1"):
                        self.assertEqual(result["cases"][cid]["solution"], answers(cid))
                else:
                    self.assertEqual(result["candidate_counts"], [10, 4, 2, 1])
                    self.assertEqual({p["assessment"] for p in result["probes"].values()}, {"CORRECT"})
                    self.assertFalse(result["probes"]["P5"]["feature_pattern_seen"])
