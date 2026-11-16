"""Regression coverage for additive lesson registration; mocks are routing evidence only."""
from copy import deepcopy
from importlib import import_module
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.lexical_training import teaching

RUNNERS = ("ntl_curriculum", "ntl_course", "ntl_core", "context_transfer",
           "corpus_concepts", "ifadah_programs", "school_apprentice", "ntl_witness_pilot",
           "opencyc_inquiry")


class LessonDispatchRegression(unittest.TestCase):
    def test_every_installed_adapter_keeps_its_dispatch(self):
        schemas = set()
        for name in RUNNERS:
            module = import_module("tools.lexical_training." + name)
            self.assertNotIn(module.SCHEMA, schemas)
            schemas.add(module.SCHEMA)
            request = {"schema": module.SCHEMA}
            marker = {"schema": module.RESULT, "status": "DEFER", "execution_measured": False}
            with self.subTest(adapter=name), patch.object(module, "run", return_value=marker) as run:
                self.assertIs(teaching.run_lesson(request), marker)
                run.assert_called_once_with(request)

    def test_witness_error_keeps_invalid_input_boundary(self):
        from tools.lexical_training import ntl_witness_pilot
        with patch.object(ntl_witness_pilot, "run", side_effect=ValueError("bad source")):
            result = teaching.run_lesson({"schema": ntl_witness_pilot.SCHEMA})
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertIs(result["execution_measured"], False)

    def test_real_witness_receipts_replay_without_promoting_unknown_readings(self):
        from tools.lexical_training import ntl_witness_pilot
        for text, withdraw, status in (
            ("لم يُفتح باب المختبر؛ مكان الرصد في المختبر.", [], "SOURCE_BOUND"),
            ("لم يُفتح باب المختبر؛ مكان الرصد في المختبر.", ["binding"], "SOURCE_BOUND"),
            ('قالت المعلمة «سَجِّلْ وثيقة الإعارة».', [], "UNBOUND_READING"),
        ):
            request = {"schema": ntl_witness_pilot.SCHEMA, "source_id": "replay-probe",
                       "text": text, "withdraw": withdraw}
            with self.subTest(status=status, withdraw=withdraw):
                report = teaching.run_lesson(request)
                self.assertEqual(report["status"], status)
                self.assertIs(report["execution_measured"], True)
                self.assertIs(report["world_occurrence_established"], False)
                self.assertTrue(teaching.verify_lesson(report, expected_lesson=request)["valid"])
                forged = deepcopy(report)
                forged["world_occurrence_established"] = True
                self.assertFalse(teaching.verify_lesson(forged, expected_lesson=request)["valid"])
                changed_request = dict(request, source_id="other-source")
                self.assertFalse(teaching.verify_lesson(report, expected_lesson=changed_request)["valid"])
                if status == "UNBOUND_READING":
                    self.assertEqual(report["questions"], [])
                    self.assertIn("SCOPED_BINDING_REQUIRED", report["residuals"])
                elif withdraw:
                    reading = next(q for q in report["questions"] if q["id"] == "reading")
                    self.assertEqual(reading["after"]["state"], "WITHDRAWN")
                    self.assertIsNone(reading["after"]["answer"])
                    self.assertEqual(report["kept"], ["context"])

    def test_new_and_existing_neural_receipts_replay_floats(self):
        for name in ("school_apprentice", "ntl_witness_pilot"):
            module = import_module("tools.lexical_training." + name)
            request = {"schema": module.SCHEMA}
            # The test double is only for serialization/replay, never native proof.
            report = {"status": "SUPPORTED", "execution_measured": True,
                      "neural": {"authority": "NONE", "score": 0.125}}
            with self.subTest(adapter=name), patch.object(teaching, "run_lesson", return_value=report) as replay:
                result = teaching.verify_lesson(deepcopy(report), expected_lesson=request)
                self.assertTrue(result["valid"])
                replay.assert_called_once_with(request)
                changed = deepcopy(report)
                changed["neural"]["score"] = 0.75
                self.assertFalse(teaching.verify_lesson(changed, expected_lesson=request)["valid"])

    def test_unmeasured_receipt_is_not_accepted(self):
        from tools.lexical_training import ntl_witness_pilot
        request = {"schema": ntl_witness_pilot.SCHEMA}
        report = {"status": "DEFER", "execution_measured": False, "neural": {"score": 0.5}}
        with patch.object(teaching, "run_lesson", return_value=report):
            result = teaching.verify_lesson(report, expected_lesson=request)
        self.assertTrue(result["replay_matches"])
        self.assertFalse(result["valid"])

    def test_missing_and_nonboolean_execution_metadata_fail_closed(self):
        from tools.lexical_training import ntl_witness_pilot
        request = {"schema": ntl_witness_pilot.SCHEMA}
        reports = [{"status": "DEFER"}] + [
            {"status": "DEFER", "execution_measured": flag}
            for flag in (None, 0, 1, "true", [], {})]
        for report in reports:
            with self.subTest(report=report), patch.object(teaching, "run_lesson", return_value=report):
                result = teaching.verify_lesson(deepcopy(report), expected_lesson=request)
                self.assertTrue(result["replay_matches"])
                self.assertIs(result["valid"], False)

    def test_malformed_expected_lesson_fails_closed(self):
        for request in (None, False, 1, "lesson", [], {}, {"schema": "unknown"}):
            with self.subTest(request=request):
                report = teaching.run_lesson(request)
                self.assertIs(teaching.verify_lesson(report, expected_lesson=request)["valid"], False)

    def test_real_context_lesson_replays_and_keeps_native_status(self):
        from tools import aligned_acquisition
        from tools.lexical_training import context_transfer
        request = {"schema": context_transfer.SCHEMA, **deepcopy(context_transfer.SEA),
                   "probes": ["أمامنا بَحْرٌ تتلاطم أمواجه.", "لم يظهر بَحْرٌ تتلاطم أمواجه."]}
        report = teaching.run_lesson(request)
        self.assertIs(report["execution_measured"], True)
        self.assertIs(report["world_truth_established"], False)
        self.assertIs(report["semantic_license"], False)
        self.assertTrue(teaching.verify_lesson(report, expected_lesson=request)["valid"])
        first, outside = report["predictions"]
        self.assertEqual(outside["decision"], "UNRESOLVED")
        self.assertEqual(outside["reason"], "OUTSIDE_CLAUSE_PROFILE")
        if aligned_acquisition._NATIVE_PATH.is_file():
            self.assertEqual(first["decision"], "literal")
            self.assertEqual(first["address"]["status"], "ACQUIRED")
        else:
            self.assertEqual(first["decision"], "UNRESOLVED")
            self.assertEqual(first["reason"], "VERIFICATION_UNAVAILABLE")
        forged = deepcopy(report)
        forged["semantic_license"] = True
        self.assertFalse(teaching.verify_lesson(forged, expected_lesson=request)["valid"])

    def test_native_suite_union_is_preserved_without_duplicate_recipe(self):
        path = Path(__file__).resolve().parents[1] / "integrations/io_gateway.mk"
        text = path.read_text(encoding="utf-8")
        for target in ("io-gateway", "ntl-course-check"):
            lines = text.splitlines()
            start = next(i for i, line in enumerate(lines) if line.startswith(target + ":"))
            recipe = []
            for line in lines[start + 1:]:
                if not line.startswith("\t"):
                    break
                recipe.append(line)
            commands = [line for line in recipe if " -m unittest " in line]
            self.assertEqual(len(commands), 1)
            for test in ("tests.test_ntl_witness_pilot", "tests.test_ifadah_programs",
                         "tests.test_pr113_regressions", "tests.test_lesson_dispatch_regression"):
                self.assertEqual(commands[0].split().count(test), 1)
            if target == "ntl-course-check":
                self.assertIn("NABT_REQUIRE_IO_GATEWAY_NATIVE=1", commands[0])


if __name__ == "__main__":
    unittest.main()
