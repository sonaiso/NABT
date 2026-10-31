"""Contract, source attribution and adversarial replay tests; no LLM calls."""
from copy import deepcopy
from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import explainable_pilot as pilot
from tools import evaluate_explainable_pilot as evaluation
from tools.verified_reading import propose

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
if "NABT_VERIFIED_READING" in os.environ and not BINARY.is_file():
    raise RuntimeError("NABT_VERIFIED_READING must point to the built executable")
BASE = "سالم هو حكيم.\nإذا سالم هو حكيم فإن سالم هو عالم.\n".encode()
QUERY = "هل سالم هو عالم؟\n".encode()


class InputContract(unittest.TestCase):
    def assert_error(self, code, call):
        with self.assertRaises(pilot.PilotError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_duplicate_keys_and_nonfinite_json(self):
        for raw in (b'{"x":1,"\\u0078":2}', b'{"x":NaN}', b'{"x":1e400}',
                    b'{"x":-1e400}', b'{"x":"\\ud800"}', b'\xff', b'[' * 1500):
            self.assert_error("INVALID_INPUT", lambda: pilot.strict_json(raw))

    def test_unsigned_numeric_tokens_are_checked_before_normalization(self):
        for token in (b'-0', b'-1', b'0.0', b'1.5', b'0e0', b'1E2', b'+0', b'01'):
            self.assert_error("INVALID_INPUT", lambda: pilot.strict_json(b'{"index":' + token + b'}'))
        self.assertEqual(pilot.strict_json(b'{"index":0,"count":512}'), {"index": 0, "count": 512})

    def test_invalid_replay_values_fail_before_native_execution(self):
        for value in (float("inf"), float("nan"), "\ud800", object()):
            bundle = {"schema": pilot.ANSWER_SCHEMA, "extra": value}
            self.assert_error("INVALID_INPUT", lambda: pilot.verify(BASE, QUERY, bundle, checker="/missing"))
        bundle = {"schema": pilot.ANSWER_SCHEMA, "extra": "x" * pilot.MAX_BUNDLE_BYTES}
        self.assert_error("RESOURCE_LIMIT", lambda: pilot.verify(BASE, QUERY, bundle, checker="/missing"))

    def test_bad_inputs_remain_distinct_from_unknown(self):
        for raw, question, code in [(b'\xff', QUERY, "INVALID_INPUT"),
                (BASE, b'\xff', "INVALID_INPUT"), (b'x' * 65537, QUERY, "RESOURCE_LIMIT"),
                ("سالم حكيم.\n".encode(), QUERY, "OUTSIDE_VERIFIED_LANGUAGE"),
                (BASE, b'?', "OUTSIDE_VERIFIED_LANGUAGE")]:
            self.assert_error(code, lambda: pilot.answer(raw, question, checker="/missing"))
        for field in ("identity", "revision", "scope"):
            self.assert_error("INVALID_INPUT", lambda: pilot.answer(BASE, QUERY, **{field: ""}))
        for timeout in (True, 0, -1, float("nan"), float("inf"), 61):
            self.assert_error("INVALID_INPUT", lambda: pilot.answer(BASE, QUERY, timeout=timeout))

    def test_no_checker_never_grants_authority(self):
        self.assert_error("CHECKER_UNAVAILABLE", lambda: pilot.answer(BASE, QUERY, checker="/missing"))

    def test_missing_certificate_is_not_reproposed(self):
        for cert in ({}, {"kernel_certificate": None}):
            self.assert_error("ANSWER_REJECTED", lambda: pilot.verify(BASE, QUERY,
                              {"schema": pilot.ANSWER_SCHEMA, "analysis_certificate": cert}))

    def test_cli_error_has_no_semantic_status(self):
        with tempfile.TemporaryDirectory() as temp:
            source, query = Path(temp) / "source", Path(temp) / "query"
            source.write_bytes(b'\xff')
            query.write_bytes(QUERY)
            run = subprocess.run(["python", str(ROOT / "tools/explainable_pilot.py"), "answer",
                str(source), str(query), "--output", str(Path(temp) / "answer.json")],
                capture_output=True, text=True, timeout=10)
            self.assertNotEqual(run.returncode, 0)
            result = json.loads(run.stdout)
            self.assertEqual(result["error"], "INVALID_INPUT")
            self.assertNotIn("status", result)


@unittest.skipUnless(BINARY.is_file(), "build verifiedReading first; formal CI requires this suite")
class NativeAnswerContract(unittest.TestCase):
    def answer(self, raw=BASE, query=QUERY, **options):
        return pilot.answer(raw, query, checker=BINARY, **options)

    def test_repository_matrix(self):
        material = json.loads(evaluation.CASES.read_text())
        for case in material["cases"] + material["ablations"]:
            with self.subTest(case=case["id"]):
                raw, query = evaluation.inputs(case)
                bundle = self.answer(raw, query)
                self.assertEqual(bundle["answer"]["status"], case["expected"])
                self.assertTrue(pilot.verify(raw, query, bundle, checker=BINARY)["verified"])

    def test_human_authored_trace_oracle(self):
        # Expected references are authored independently; no production renderer
        # or closure is used to calculate the expected edges or byte offsets.
        bundle = self.answer()
        evidence = bundle["analysis_certificate"]
        full = evidence["traces"]["full"]
        self.assertEqual([(n["id"], n["clause_id"], n["premises"]) for n in full],
                         [("f0", "c0", []), ("f1", "c1", ["f0"])])
        self.assertEqual(evidence["roots"], {"full": {"query": "f1", "opposite_query": None},
                                           "clean": {"query": "k1", "opposite_query": None}})
        end = len("سالم هو حكيم.\n".encode())
        self.assertEqual([(s["byte_start"], s["byte_end"]) for s in evidence["source_clauses"]],
                         [(0, end), (end, len(BASE))])
        self.assertFalse(bundle["limits"]["world_truth_established"])

    def test_filtered_indices_map_back_to_original_source(self):
        raw = BASE + "ليس سالم هو حكيم.\nسالم هو عالم.\n".encode()
        e = self.answer(raw)["analysis_certificate"]
        self.assertEqual([(n["clause_id"], n["premises"]) for n in e["traces"]["clean"]], [("c3", [])])
        self.assertEqual(e["roots"]["clean"]["query"], "k0")

    def test_negative_question_roots_are_relative_to_query(self):
        b = self.answer("ليس سالم هو عالم.\n".encode(), "هل ليس سالم هو عالم؟\n".encode())
        self.assertEqual(b["answer"]["status"], "SUPPORTED")
        self.assertEqual(b["analysis_certificate"]["roots"]["full"], {"query": "f0", "opposite_query": None})

    def test_adversarial_replay(self):
        bundle = self.answer()
        for name, altered, options in evaluation.attacks(bundle):
            with self.subTest(attack=name), self.assertRaises(pilot.PilotError):
                pilot.verify(BASE, QUERY, altered, checker=BINARY, **options)
        for raw, query in ((BASE + "ليس سالم هو عالم.\n".encode(), QUERY),
                           (BASE, "هل سالم هو حكيم؟\n".encode())):
            with self.assertRaises(pilot.PilotError):
                pilot.verify(raw, query, bundle, checker=BINARY)

    def test_external_proposal_must_verify(self):
        certificate = propose(BASE, QUERY)
        self.assertEqual(self.answer(certificate=certificate)["answer"]["status"], "SUPPORTED")
        for field in ("known", "steps", "clean_known", "clean_steps"):
            altered = deepcopy(certificate)
            altered[field].pop()
            with self.assertRaises(pilot.PilotError) as caught:
                self.answer(certificate=altered)
            self.assertEqual(caught.exception.code, "CERTIFICATE_REJECTED")

    def test_cli_rejects_negative_zero_offsets_and_certificate_indices(self):
        encoded = pilot.wire(self.answer())
        with tempfile.TemporaryDirectory() as temp:
            source, query, bundle = (Path(temp) / name for name in ("source", "query", "answer.json"))
            source.write_bytes(BASE)
            query.write_bytes(QUERY)
            for field in ("byte_start", "index"):
                altered = encoded.replace('"' + field + '":0', '"' + field + '":-0', 1)
                self.assertNotEqual(altered, encoded)
                bundle.write_text(altered, encoding="utf-8")
                run = subprocess.run([sys.executable, str(ROOT / "tools/explainable_pilot.py"),
                    "verify", str(source), str(query), str(bundle), "--checker", str(BINARY)],
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(run.returncode, 2)
                result = json.loads(run.stdout)
                self.assertEqual(result["error"], "INVALID_INPUT")
                self.assertNotIn("status", result)

    def test_resource_exhaustion_is_not_unknown(self):
        with patch.object(pilot.subprocess, "run", side_effect=subprocess.TimeoutExpired("checker", 1)):
            with self.assertRaises(pilot.PilotError) as caught:
                self.answer()
            self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")

    def test_evaluation_denominators(self):
        report = evaluation.evaluate(checker=BINARY, repeats=1)
        self.assertTrue(report["passed"])
        self.assertEqual(report["input_hashes"]["tools/explainable_contracts.py"],
                         sha256((ROOT / "tools/explainable_contracts.py").read_bytes()).hexdigest())
        self.assertEqual(report["metrics"]["status_exact"], evaluation.metric(14, 14))
        self.assertEqual(report["metrics"]["tampering_rejected"], evaluation.metric(14, 14))
        self.assertEqual(report["metrics"]["source_ablation"], evaluation.metric(4, 4))
        self.assertFalse(report["hidden"])
        self.assertTrue(all(v is None for v in report["unmeasured"].values()))

    def test_proposer_failures_write_reports_with_all_denominators(self):
        for error, code in ((ValueError("unparseable input"), "OUTSIDE_VERIFIED_LANGUAGE"),
                            (ValueError("RESOURCE_LIMIT: too many atoms"), "RESOURCE_LIMIT"),
                            (pilot.NabtError("RESOURCE_LIMIT", "input budget"), "RESOURCE_LIMIT")):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "report.json"
                argv = ["evaluate_explainable_pilot", "--output", str(output),
                        "--checker", str(BINARY), "--repeats", "1"]
                with patch.object(pilot.ground, "propose", side_effect=error), \
                        patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
                    self.assertEqual(evaluation.main(), 1)
                report = json.loads(output.read_text())
                self.assertFalse(report["passed"])
                self.assertEqual(len(report["cases"]), 14)
                self.assertTrue(all(row["error"] == code for row in report["cases"]))
                for name, total in (("status_exact", 14), ("tampering_rejected", 14), ("source_ablation", 4)):
                    self.assertEqual(report["metrics"][name], evaluation.metric(0, total))
                self.assertTrue(all(row["not_executed"] for row in report["attacks"]))


if __name__ == "__main__":
    unittest.main()
