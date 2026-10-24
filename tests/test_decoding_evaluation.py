"""Denominators and prefix metrics must not be selected by outcome."""
import unittest
from unittest.mock import patch

from tools import evaluate_licensed_decoding as evaluation
from tools import explainable_pilot as pilot
from tests.test_licensed_decoding import BINARY


class PrefixMetrics(unittest.TestCase):
    def test_missing_checker_retains_cases_and_all_fault_slots(self):
        report = evaluation.evaluate(checker="/missing")
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["cases"]), 14)
        self.assertIsNone(report["environment"]["checker_sha256"])
        self.assertTrue(all(len(row["fault_attempts"]) == 2 for row in report["cases"]))
        self.assertTrue(all(row["error"] == "CHECKER_UNAVAILABLE" for row in report["cases"]))

    def test_missing_and_failed_first_candidates_are_not_pass_at_one(self):
        rows = [{"accepted": False, "answer_status": None},
                {"accepted": True, "answer_status": "SUPPORTED"}]
        self.assertFalse(evaluation.prefix_success(rows, "SUPPORTED", 1))
        self.assertTrue(evaluation.prefix_success(rows, "SUPPORTED", 2))
        self.assertFalse(evaluation.prefix_success(rows, "REFUTED", 2))
        self.assertFalse(evaluation.prefix_success([], "SUPPORTED", 2))


@unittest.skipUnless(BINARY.is_file(), "formal CI requires native verifiedReading")
class NativeEvaluation(unittest.TestCase):
    def test_report_retains_every_case_on_proposer_failure(self):
        with patch.object(pilot, "propose_certificate", side_effect=pilot.PilotError("RESOURCE_LIMIT", "exhausted")):
            report = evaluation.evaluate(checker=BINARY)
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["cases"]), 14)
        self.assertTrue(all(row["error"] == "RESOURCE_LIMIT" for row in report["cases"]))
        self.assertTrue(all(len(row["fault_attempts"]) == 2 and
                            all(not attempt["executed"] for attempt in row["fault_attempts"])
                            for row in report["cases"]))
        self.assertTrue(all(m["total"] == 14 and m["passed"] == 0 for m in report["metrics"].values()))
        self.assertTrue(all(v is None for v in report["unmeasured"].values()))

    def test_native_current_proposer_and_fault_injection_are_distinct(self):
        report = evaluation.evaluate(checker=BINARY)
        self.assertTrue(report["passed"])
        self.assertEqual(report["metrics"]["pass_at_1"], evaluation.metric(14, 14))
        self.assertEqual(report["metrics"]["fault_pass_at_1"], evaluation.metric(0, 14))
        self.assertEqual(report["metrics"]["fault_pass_within_2"], evaluation.metric(14, 14))
        self.assertEqual(report["timing"]["baseline"]["n"], 42)
        self.assertEqual(report["timing"]["candidate"]["n"], 42)
        self.assertFalse(report["hidden"])


if __name__ == "__main__":
    unittest.main()
