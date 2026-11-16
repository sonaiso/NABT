"""Regression coverage for additive lesson registration; mocks are routing evidence only."""
from copy import deepcopy
from importlib import import_module
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.lexical_training import teaching

RUNNERS = ("ntl_curriculum", "ntl_course", "ntl_core", "context_transfer",
           "corpus_concepts", "ifadah_programs", "school_apprentice", "ntl_witness_pilot")


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
