"""Source-bound integration regressions; the linguistic law belongs to PR 34."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from tools import acquired_inference as bridge
from tools import aligned_acquisition as acquisition
from tools.licensed_inference import runtime as inference

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evidence/aligned_acquisition_v1/integration/cases.json"
PIN = "985e0be8faa597ca0d1675e3ae7ee5eb7c6f1b086d95c589fadab635275030da"
SOURCE = "سَارَ زَيْدٌ."
QUERY = "هَلْ سَارَ زَيْدٌ؟"
BINDING = dict(source_id="evidence", revision="v1", scope="episode", time="t1",
               source_ending="wasl", query_ending="wasl")
NATIVE = all((ROOT / "formal/.lake/build/bin" / name).is_file()
             for name in ("alignedAcquisition", "licensedInference"))


class ComposedInputTests(unittest.TestCase):
    def test_invalid_metadata_and_budget_have_no_native_authority(self):
        for key in ("source_id", "revision", "scope", "time"):
            for value in (True, 1, "", "x\x85", "\ud800", "x" * 513):
                with self.subTest(key=key, value=repr(value)):
                    result = bridge.evaluate(SOURCE, QUERY, **{**BINDING, key: value})
                    self.assertEqual(result["status"], "INVALID_INPUT")
                    self.assertFalse(result["chain_complete"])
        self.assertEqual(bridge.evaluate(SOURCE, QUERY, budget={})["status"], "INVALID_INPUT")

    def test_frozen_integration_cases_are_not_relabelled(self):
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), PIN)


@unittest.skipUnless(NATIVE, "build alignedAcquisition and licensedInference")
class NativeComposedTests(unittest.TestCase):
    def test_frozen_cases_preserve_pr34_results_and_separate_chain_coverage(self):
        for case in json.loads(FIXTURE.read_text())["cases"]:
            with self.subTest(case=case["id"]):
                result = bridge.evaluate(case["source"], case["query"], **BINDING)
                self.assertEqual(result["licensed_inference"]["status"], case["inference_status"])
                self.assertIs(result["chain_complete"], case["chain_complete"])
                self.assertFalse(result["world_truth_established"])
                self.assertFalse(result["all_arabic_complete"])
                if case["chain_complete"]:
                    self.assertEqual(result["answer"]["status"], case["inference_status"])
                else:
                    self.assertIsNone(result["answer"])
                    self.assertEqual(result["authority"], "NO_COMPOSITE_AUTHORITY")

    def test_original_bytes_and_native_scope_are_reused_without_normalization(self):
        source, query = b" \r\n" + SOURCE.encode(), QUERY.encode() + b"\r\n"
        with patch.object(inference, "evaluate", wraps=inference.evaluate) as call:
            result = bridge.evaluate(source, query, **BINDING)
        self.assertTrue(result["chain_complete"])
        self.assertEqual(call.call_args.args, (source, query))
        self.assertEqual(result["source_acquisition"]["acquisition"]["text"].encode(), source)
        self.assertEqual(result["licensed_inference"]["source"]["raw_text"].encode(), source)
        self.assertEqual(result["binding"]["native_scope"],
                         result["licensed_inference"]["native_result"]["source_scope"])

    def test_receipt_replay_and_all_independent_bindings(self):
        report = bridge.evaluate(SOURCE, QUERY, **BINDING)
        self.assertTrue(bridge.verify(report, source=SOURCE, query=QUERY, **BINDING)["valid"])
        changes = {"source_id": "other", "revision": "v2", "scope": "other", "time": "t2",
                   "source_ending": "waqf", "query_ending": "waqf"}
        for key, value in changes.items():
            with self.subTest(key=key):
                self.assertFalse(bridge.verify(report, source=SOURCE, query=QUERY,
                    **{**BINDING, key: value})["valid"])
        for source, query in ((SOURCE + " ", QUERY), (SOURCE, QUERY + " "), (QUERY, SOURCE)):
            self.assertFalse(bridge.verify(report, source=source, query=query, **BINDING)["valid"])

    def test_forged_cells_booleans_authority_and_nested_inference_are_rejected(self):
        report = bridge.evaluate(SOURCE, QUERY, **BINDING)
        mutations = []
        for key, value in (("verified", 1), ("chain_complete", 1), ("authority", "WORLD_TRUTH"),
                           ("world_truth_established", True)):
            mutant = copy.deepcopy(report)
            mutant[key] = value
            mutations.append(mutant)
        mutant = copy.deepcopy(report)
        mutant["source_acquisition"]["acquisition"]["words"][0]["cells"][0] ^= 1
        mutations.append(mutant)
        mutant = copy.deepcopy(report)
        mutant["licensed_inference"]["aggregate"]["skeptical_clean_positive"] = False
        mutations.append(mutant)
        for mutant in mutations:
            self.assertFalse(bridge.verify(mutant, source=SOURCE, query=QUERY, **BINDING)["valid"])

    def test_missing_acquisition_verifier_never_calls_inference(self):
        with patch.object(acquisition, "_native", side_effect=FileNotFoundError), \
                patch.object(inference, "evaluate") as call:
            result = bridge.evaluate(SOURCE, QUERY, **BINDING)
        call.assert_not_called()
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertIsNone(result["answer"])

    def test_missing_inference_verifier_never_authorizes_acquisition(self):
        with patch.object(inference, "_native", side_effect=FileNotFoundError):
            result = bridge.evaluate(SOURCE, QUERY, **BINDING)
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(result["chain_complete"])
        self.assertIsNone(result["answer"])

    def test_resource_limits_remain_resource_limits(self):
        result = bridge.evaluate(SOURCE, QUERY, **BINDING,
                                 budget=inference.InferenceBudget(max_closure_steps=0))
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        for source, query in (("a" * 4097, QUERY), (SOURCE, b"a" * 8193)):
            result = bridge.evaluate(source, query, **BINDING)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")

    def test_shape_failures_are_not_ordinary_linguistic_refusals(self):
        for error, status in (("RESOURCE_LIMIT", "RESOURCE_EXHAUSTED"),
                              ("SHAPE_REPLAY_FAILED", "VERIFICATION_UNAVAILABLE")):
            with patch.object(acquisition, "issue_certificate", side_effect=NabtError(error, "test")):
                result = bridge.evaluate(SOURCE, QUERY, **BINDING)
            self.assertEqual(result["status"], status)
            self.assertIsNone(result["answer"])

    def test_source_and_query_native_bindings_cannot_be_crossed(self):
        valid = inference.evaluate(SOURCE, QUERY, source_id=BINDING["source_id"],
            revision=BINDING["revision"], scope=BINDING["scope"], time=BINDING["time"])
        for key, value in (("source_text", SOURCE + " "), ("query_text", QUERY + " "),
                           ("source_scope", "other"), ("revision", "other"), ("source_id", "other")):
            changed = copy.deepcopy(valid)
            changed["native_result"][key] = value
            with patch.object(inference, "evaluate", return_value=changed):
                result = bridge.evaluate(SOURCE, QUERY, **BINDING)
            self.assertFalse(result["chain_complete"])
            self.assertIn("same_binding", result["blocked_by"])

    def test_incomplete_exact_receipt_is_not_an_accepted_chain(self):
        report = bridge.evaluate("سار زيد.", "هل سار زيد؟", **BINDING)
        result = bridge.verify(report, source="سار زيد.", query="هل سار زيد؟", **BINDING)
        self.assertTrue(result["replay_matches"])
        self.assertFalse(result["valid"])

    def test_cli_roundtrip_and_duplicate_receipt_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, query, receipt = (root / name for name in ("source", "query", "receipt"))
            source.write_text(SOURCE)
            query.write_text(QUERY)
            command = [sys.executable, "-m", "tools.acquired_inference_cli"]
            run = subprocess.run([*command, "infer", str(source), str(query)], cwd=ROOT,
                                 capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr)
            receipt.write_text(run.stdout)
            verify = [*command, "verify", str(receipt), str(source), str(query)]
            replay = subprocess.run(verify, cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            receipt.write_text('{"verified":true,' + run.stdout.lstrip()[1:])
            replay = subprocess.run(verify, cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(replay.returncode, 2)
