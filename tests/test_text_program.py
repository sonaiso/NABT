"""Builder examples for the generic text path; not the separately sealed benchmark."""

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from nabt.cli import main
from nabt.errors import NabtError
from nabt.program import Instruction, Opcode, Program, compile_request, execute_program, verify_execution

ROOT = Path(__file__).resolve().parents[1]


def request():
    return {
        "task": "text_inquiry", "scope": "builder",
        "events": [
            {"op": "add", "source_id": "law", "text": "كل مهيأ هو قادر."},
            {"op": "add", "source_id": "observation", "text": "جهاز هو مهيأ."},
            {"op": "query", "query_id": "capability", "text": "هل جهاز هو قادر؟"},
        ],
    }


class TextProgramTests(unittest.TestCase):
    def test_new_text_compiles_to_typed_numbers_and_replays(self):
        program = compile_request(request())
        self.assertEqual([step.opcode for step in program.instructions], [30, 31, 31, 33])
        self.assertEqual(Program.from_number(program.number), program)
        receipt = execute_program(program)
        self.assertEqual(receipt["result"]["status"], "SUPPORTED")
        self.assertEqual(receipt["result"]["world_truth"], "NOT_ESTABLISHED")
        self.assertEqual(receipt["installed_contracts"]["text_language"], "nabt.controlled-arabic.v1")
        self.assertTrue(verify_execution(receipt)["valid"])

    def test_definition_relation_missing_conflict_and_transfer_program(self):
        scenario = json.loads((ROOT / "examples/text_inquiry_revision.json").read_text())
        receipt = execute_program(compile_request(scenario))
        results = [step["result"] for step in receipt["trace"] if step["opcode"] == 33]
        self.assertEqual([result["status"] for result in results],
                         ["SUPPORTED", "UNKNOWN", "SUPPORTED", "DEFER", "CONFLICT", "SUPPORTED"])
        self.assertTrue(results[1]["missing_premises"])
        self.assertEqual(results[3]["reason"], "CONTESTED_PREMISES")
        self.assertTrue(results[3]["contested_premises"])
        self.assertTrue(verify_execution(receipt)["valid"])

    def test_explicit_replacement_changes_derived_answer(self):
        scenario = request()
        scenario["events"].extend([
            {"op": "replace", "source_id": "observation", "text": "جهاز هو محفوظ."},
            {"op": "query", "query_id": "capability", "text": "هل جهاز هو قادر؟"},
        ])
        receipt = execute_program(compile_request(scenario))
        self.assertEqual(receipt["result"]["status"], "UNKNOWN")
        self.assertTrue(verify_execution(receipt)["valid"])

    def test_rejects_source_overwrite_inactive_removal_and_query_alias(self):
        bad_events = [
            {"op": "add", "source_id": "law", "text": "كل مهيأ هو غائب."},
            {"op": "remove", "source_id": "absent"},
            {"op": "replace", "source_id": "absent", "text": "جهاز هو موجود."},
            {"op": "query", "query_id": "capability", "text": "هل جهاز هو مهيأ؟"},
        ]
        for event in bad_events:
            with self.subTest(event=event["op"]):
                scenario = request()
                scenario["events"].append(event)
                with self.assertRaises(NabtError):
                    compile_request(scenario)

    def test_no_supplied_truth_or_ir_authority(self):
        for field, value in (("trusted", True), ("facts", []), ("proof", "accepted")):
            scenario = request()
            scenario["events"][0][field] = value
            with self.assertRaises(NabtError):
                compile_request(scenario)

    def test_domains_cannot_be_mixed(self):
        for steps in (
            (Instruction(30, ("default",)), Instruction(11, ("source",))),
            (Instruction(10, (1,)), Instruction(31, ("source", "61"))),
            (Instruction(31, ("source", "61")),),
        ):
            with self.assertRaises(NabtError):
                Program(steps)

    def test_scope_is_validated_even_before_any_text_is_added(self):
        for scope in ("\x00", "x\u200f", "\n", "\ud800"):
            with self.subTest(scope=repr(scope)), self.assertRaises(NabtError):
                Program((Instruction(30, (scope,)),))

    def test_failed_text_operations_preserve_the_active_source_in_receipt(self):
        raw = "زيد هو حي.".encode("utf-8").hex()
        for failed in (Instruction(34, ("source", "ff")),
                       Instruction(33, ("ff", "question")),
                       Instruction(33, ("هذه عبارة غير مدعومة".encode("utf-8").hex(), "question"))):
            with self.subTest(opcode=failed.opcode):
                receipt = execute_program(Program((Instruction(30, ("default",)),
                                                   Instruction(31, ("source", raw)), failed)))
                self.assertEqual(receipt["run_status"], "STOPPED")
                self.assertEqual(receipt["final_state"]["snapshot_status"], "CURRENT")
                sources = receipt["final_state"]["theory"]["sources"]
                self.assertEqual([(s["source_id"], s["raw_utf8_hex"]) for s in sources],
                                 [("source", raw)])
                self.assertTrue(verify_execution(receipt)["valid"])

    def test_unsupported_source_tail_never_admits_recognized_prefix(self):
        scenario = {"task": "text_inquiry", "events": [
            {"op": "add", "source_id": "invalid", "text": "جهاز هو مهيأ. هذه جملة خارج النحو المحدد هنا."},
            {"op": "query", "query_id": "leak", "text": "هل جهاز هو مهيأ؟"},
        ]}
        receipt = execute_program(compile_request(scenario))
        self.assertEqual(receipt["run_status"], "STOPPED")
        self.assertFalse(receipt["result"]["accepted"])
        self.assertFalse(receipt["final_state"]["theory"]["sources"])
        self.assertEqual(len(receipt["trace"]), 2)

    def test_receipt_rejects_changed_text_rule_result_or_contract(self):
        receipt = execute_program(compile_request(request()))
        for target in ("result", "trace", "contract"):
            changed = copy.deepcopy(receipt)
            if target == "result":
                changed["result"]["world_truth"] = "ESTABLISHED"
            elif target == "trace":
                changed["trace"][-1]["result"]["status"] = "REFUTED"
            else:
                changed["installed_contracts"]["text_reader"] = "invented"
            self.assertFalse(verify_execution(changed)["valid"])

    def test_direct_text_cli_interprets_and_answers_with_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_bytes((ROOT / "examples/text_theory.txt").read_bytes())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["read-text", str(source)])
            self.assertEqual(status, 0)
            parsed = json.loads(output.getvalue())
            self.assertTrue(parsed["accepted"])
            self.assertEqual(parsed["world_truth"], "NOT_ESTABLISHED")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["ask-text", str(source), "هل تقرير هو مفحوص؟"])
            self.assertEqual(status, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["result"]["status"], "SUPPORTED")
            self.assertTrue(verify_execution(receipt)["valid"])


if __name__ == "__main__":
    unittest.main()
