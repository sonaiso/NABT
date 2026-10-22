import contextlib
import copy
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from nabt.cli import main
from nabt.errors import NabtError
from nabt.program import (
    MAX_INSTRUCTIONS,
    MAX_PROGRAM_BYTES,
    Instruction,
    Program,
    compile_request,
    execute_program,
    verify_execution,
)

EXAMPLE_IDS = (
    "sibawayhi_han_hadha",
    "sibawayhi_han_raaytu",
    "sibawayhi_han_marartu_ba",
)


def learning_request():
    return {
        "task": "source_learning",
        "events": [
            *[{"op": "observe", "record_id": name} for name in EXAMPLE_IDS],
            {"op": "query", "cue": ["مررت", "ب"], "query_id": "same-question"},
            {"op": "withdraw", "record_id": EXAMPLE_IDS[2]},
            {"op": "query", "cue": ["مررت", "ب"], "query_id": "same-question"},
            {"op": "observe", "record_id": EXAMPLE_IDS[2]},
            {"op": "query", "cue": ["مررت", "ب"], "query_id": "same-question"},
            {"op": "query", "cue": ["غير معروف"], "query_id": "missing-reading"},
        ],
    }


class ProgramTests(unittest.TestCase):
    def test_pilot_preliminary_source_failure_has_structured_exit(self):
        for error in (ValueError("digest mismatch"), KeyError("missing context")):
            with self.subTest(error=type(error).__name__):
                output = io.StringIO()
                with patch("nabt.learning.default_pilot", side_effect=error), contextlib.redirect_stderr(output):
                    code = main(["pilot"])
                report = json.loads(output.getvalue())
                self.assertEqual(code, 3)
                self.assertEqual(report["status"], "DEFER")
                self.assertEqual(report["code"], "INSTALLED_CONTRACT_FAILED")

    def test_pilot_preserves_existing_nabt_failure_classification(self):
        output = io.StringIO()
        with patch("nabt.learning.default_pilot", side_effect=NabtError("TEST_REJECT", "rejected")), contextlib.redirect_stderr(output):
            code = main(["pilot"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["code"], "TEST_REJECT")

    def test_exact_compiler_wire_and_integer_roundtrip(self):
        program = compile_request({"task": "word_shape", "text": "كَتَبَ"})
        # A literal reference packet, not a call to the production serializer.
        expected = b'{"abi":1,"code":[[1,"d983d98ed8aad98ed8a8d98e"],[2,"waqf"]]}'
        self.assertEqual(program.to_bytes(), expected)
        expected_number = 1
        for byte in expected:
            expected_number = 256 * expected_number + byte
        self.assertEqual(program.number, expected_number)
        self.assertEqual(Program.from_number(expected_number), program)
        self.assertEqual(Program.from_bytes(expected), program)
        self.assertEqual(program.packet()["authority"], "EXECUTABLE_REQUEST_ONLY")

    def test_numeric_instruction_identity_and_transport_not_linguistic_license(self):
        for mode in ("waqf", "wasl"):
            a = compile_request({"task": "word_shape", "text": "كَتَبَ", "mode": mode})
            b = compile_request({"task": "word_shape", "text": "كُتِبَ", "mode": mode})
            self.assertNotEqual(a.number, b.number)
            self.assertNotEqual(a.instructions[0].number, b.instructions[0].number)
        self.assertNotEqual(
            a.number, compile_request({"task": "word_shape", "text": "كُتِبَ"}).number
        )

    def test_exact_word_receipt_replays_and_preserves_source(self):
        receipt = execute_program(
            compile_request({"task": "word_shape", "text": "كَتَبَ"})
        )
        self.assertEqual(receipt["run_status"], "COMPLETED")
        self.assertEqual(receipt["result"]["status"], "LICENSED_SHAPE")
        self.assertEqual(receipt["result"]["certificate"]["numeric_code"], "1144809")
        self.assertEqual(
            receipt["trace"][0]["result"]["raw_utf8_hex"], "d983d98ed8aad98ed8a8d98e"
        )
        self.assertTrue(verify_execution(receipt)["valid"])
        self.assertEqual(receipt["semantic_or_real_world_judgment"], "NOT_ESTABLISHED")

    def test_unknown_marks_preserve_alternatives_and_missing_names(self):
        receipt = execute_program(
            compile_request({"task": "word_shape", "text": "كتب"})
        )
        result = receipt["result"]
        self.assertEqual(result["status"], "PENDING")
        self.assertGreater(result["licensed_completion_count"], 1)
        self.assertEqual([r["position"] for r in result["residuals"]], [0, 1, 2])
        self.assertNotIn("certificate", result)
        self.assertTrue(verify_execution(receipt)["valid"])

    def test_revision_restores_hypotheses_and_recomputes_dependent_answer(self):
        receipt = execute_program(compile_request(learning_request()))
        self.assertEqual(receipt["run_status"], "COMPLETED")
        traces = receipt["trace"]
        self.assertEqual(
            [
                len(t["result"]["learning_state"]["surviving_rule_codes"])
                for t in traces[:4]
            ],
            [8, 4, 2, 1],
        )
        queries = [t["result"] for t in traces if t["opcode"] == 13]
        self.assertEqual(
            [q["possible_marker_is_waw"] for q in queries],
            [[False], [False, True], [False], [False, True]],
        )
        self.assertEqual(queries[0]["learning_state"], queries[2]["learning_state"])
        self.assertEqual(queries[3]["known"], 0)
        self.assertEqual(len(queries[3]["missing_predicates"]), 3)
        self.assertEqual(traces[2]["result"]["cue"], "رأيت")
        self.assertEqual(traces[2]["result"]["target"], "هناك")
        self.assertFalse(traces[2]["result"]["label_marker_is_waw"])
        self.assertTrue(verify_execution(receipt)["valid"])

    def test_repeated_evidence_does_not_increase_observation_count(self):
        req = {
            "task": "source_learning",
            "events": [
                {"op": "observe", "record_id": EXAMPLE_IDS[0]},
                {"op": "observe", "record_id": EXAMPLE_IDS[0]},
            ],
        }
        result = execute_program(compile_request(req))
        self.assertEqual(len(result["final_state"]["active_source_records"]), 1)
        self.assertEqual(len(result["final_state"]["surviving_rule_codes"]), 4)

    def test_source_and_prescription_records_cannot_be_interchanged(self):
        from nabt.learning import default_pilot

        prescription = default_pilot().prescription_records()[0].record_id
        req = {
            "task": "source_learning",
            "events": [{"op": "observe", "record_id": prescription}],
        }
        receipt = execute_program(compile_request(req))
        self.assertEqual(receipt["run_status"], "STOPPED")
        self.assertEqual(receipt["result"]["code"], "RECORD_OUTSIDE_OBSERVATION_POLICY")

    def test_no_caller_authority_fields_and_no_instruction_reordering(self):
        invalid = [
            {"task": "word_shape", "text": "كتب", "trusted": True},
            {"task": "noun_obligations", "text": "ذو", "positive": 7},
            {
                "task": "source_learning",
                "events": [
                    {"op": "observe", "record_id": EXAMPLE_IDS[0], "label": True}
                ],
            },
            {"task": "source_learning", "events": [{"op": {}}]},
            {"task": "source_learning", "degree": True, "events": []},
            {
                "task": "source_learning",
                "events": [{"op": "withdraw", "record_id": EXAMPLE_IDS[0]}],
            },
        ]
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(NabtError):
                compile_request(request)
        with self.assertRaises(NabtError):
            Program((Instruction(2, ("waqf",)), Instruction(1, ("",))))
        with self.assertRaises(NabtError):
            Program((Instruction(10, (1,)), Instruction(2, ("waqf",))))

    def test_no_stale_query_identity_and_unknown_is_not_false(self):
        req = {
            "task": "source_learning",
            "events": [
                {"op": "query", "cue": ["هذا"], "query_id": "q"},
                {"op": "query", "cue": ["رأيت"], "query_id": "q"},
            ],
        }
        with self.assertRaises(NabtError) as caught:
            compile_request(req)
        self.assertEqual(caught.exception.code, "QUERY_ID_REUSED")

    def test_wire_boundary_rejects_noncanonical_unicode_bool_and_padding(self):
        good = compile_request({"task": "word_shape", "text": "كَتَبَ"})
        malformed = [
            good.to_bytes() + b" ",
            b'{"abi":true,"code":[[10,1]]}',
            b'{"abi":1,"abi":1,"code":[[10,1]]}',
            b'{"abi":1,"code":[[true,1]]}',
            b'{"abi":1,"code":[[10,NaN]]}',
            b"\xed\xa0\x80",
            b"\xf4\x90\x80\x80",
        ]
        for raw in malformed:
            with self.subTest(raw=raw), self.assertRaises(NabtError):
                Program.from_bytes(raw)
        for number in (0, True, -1, int.from_bytes(b"\x02" + good.to_bytes(), "big")):
            with (
                self.subTest(number_type=type(number).__name__),
                self.assertRaises(NabtError),
            ):
                Program.from_number(number)
        for bad in ("eda080", "f4908080"):
            invalid_text = Program((Instruction(1, (bad,)), Instruction(2, ("waqf",))))
            self.assertEqual(
                execute_program(invalid_text)["result"]["code"], "INVALID_UTF8"
            )

    def test_resource_limit_is_defer_not_negative_evidence(self):
        with self.assertRaises(NabtError) as caught:
            Program.from_number(1 << (8 * (MAX_PROGRAM_BYTES + 2)))
        self.assertEqual(
            (caught.exception.code, caught.exception.status),
            ("RESOURCE_LIMIT", "DEFER"),
        )
        with self.assertRaises(NabtError):
            compile_request(
                {"task": "source_learning", "events": [{}] * MAX_INSTRUCTIONS}
            )

    def test_full_receipt_replay_rejects_forged_hash_trace_result_and_source(self):
        good = execute_program(compile_request({"task": "word_shape", "text": "كَتَبَ"}))
        mutations = []
        bad = copy.deepcopy(good)
        bad["result"]["status"] = "MEANING_PROVED"
        mutations.append(bad)
        bad = copy.deepcopy(good)
        bad["program"]["program_number_hex"] = "0x1"
        mutations.append(bad)
        bad = copy.deepcopy(good)
        bad["trace"][0]["after_sha256"] = "0" * 64
        mutations.append(bad)
        bad = copy.deepcopy(good)
        bad["installed_contracts"]["source_policy"] = "self-approved"
        mutations.append(bad)
        bad = copy.deepcopy(good)
        bad["trace"].reverse()
        mutations.append(bad)
        bad = copy.deepcopy(good)
        bad["trusted"] = True
        mutations.append(bad)
        for index, receipt in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertFalse(verify_execution(receipt)["valid"])
        self.assertTrue(verify_execution(good)["valid"])

    def test_noun_residuals_are_named_and_do_not_accept_caller_truth_bits(self):
        receipt = execute_program(
            compile_request({"task": "noun_obligations", "text": "ذو"})
        )
        self.assertEqual(receipt["run_status"], "COMPLETED")
        result = receipt["result"]
        self.assertEqual(result["status"], "PENDING")
        self.assertEqual(
            result["missing_predicates"],
            ["idafa", "not_first_person_ya", "companionship"],
        )
        self.assertEqual(result["computed_obligations"]["status"], "PENDING")
        self.assertIn("relative_pronoun", result["alternatives"])
        self.assertTrue(verify_execution(receipt)["valid"])

    def test_cli_compiles_runs_numeric_code_and_checks_receipt(self):
        def invoke(*args):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = main(list(args))
            self.assertEqual(err.getvalue(), "")
            return status, json.loads(out.getvalue())

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "request.json"
            path.write_text(
                json.dumps({"task": "word_shape", "text": "كَتَبَ"}), encoding="utf-8"
            )
            code, packet = invoke("compile", str(path))
            self.assertEqual(code, 0)
            code, receipt = invoke("execute", packet["program_number_hex"])
            self.assertEqual(code, 0)
            path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
            code, report = invoke("verify-run", str(path))
            self.assertEqual((code, report["valid"]), (0, True))

    def test_maximum_event_receipt_fits_cli_and_empty_code_is_invalid(self):
        request = {
            "task": "source_learning",
            "events": [{"op": "observe", "record_id": EXAMPLE_IDS[0]}]
            * (MAX_INSTRUCTIONS - 1),
        }
        receipt = execute_program(compile_request(request))
        content = json.dumps(receipt, ensure_ascii=False, indent=2)
        self.assertGreater(len(content.encode("utf-8")), 262144)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "large-valid-receipt.json"
            path.write_text(content, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["verify-run", str(path)])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(out.getvalue())["valid"])
        with self.assertRaises(NabtError) as caught:
            Program.from_bytes(b'{"abi":1,"code":[]}')
        self.assertEqual(
            (caught.exception.code, caught.exception.status),
            ("INVALID_PROGRAM", "REJECT"),
        )

    def test_receipt_preflight_prevents_replay_of_oversized_or_active_objects(self):
        from unittest.mock import patch

        from nabt.program import MAX_RECEIPT_BYTES

        receipt = execute_program(
            compile_request({"task": "word_shape", "text": "كَتَبَ"})
        )
        with patch(
            "nabt.program.execute_program",
            side_effect=AssertionError("must not replay"),
        ):
            bad = copy.deepcopy(receipt)
            bad["unrecognized"] = "x" * 1024
            self.assertFalse(verify_execution(bad)["valid"])
            bad = copy.deepcopy(receipt)
            bad["result"] = "x" * (MAX_RECEIPT_BYTES + 1)
            self.assertEqual(verify_execution(bad)["code"], "RESOURCE_LIMIT")
            bad = copy.deepcopy(receipt)
            bad["result"] = object()
            self.assertFalse(verify_execution(bad)["valid"])
            bad = copy.deepcopy(receipt)
            bad["result"] = "\x00" * 400000
            self.assertEqual(verify_execution(bad)["code"], "RESOURCE_LIMIT")
            bad = copy.deepcopy(receipt)
            bad["result"] = [[0] * 60000] * 2
            self.assertEqual(verify_execution(bad)["code"], "RESOURCE_LIMIT")


if __name__ == "__main__":
    unittest.main()
