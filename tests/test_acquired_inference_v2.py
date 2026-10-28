"""Independent v2 composition examples and exact boundary mutation checks."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from tools import acquired_inference_v2 as bridge
from tools import aligned_acquisition_v2 as acquisition
from tools.licensed_inference import runtime as inference

ROOT = Path(__file__).resolve().parents[1]
RULE = "إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ."
FACT = "عَرَفَ زَيْدٌ الْحَقَّ."
SOURCE = RULE + " " + FACT
QUERY = "هَلْ سَارَ زَيْدٌ؟"
BINDING = dict(source_id="unit", revision="2", scope="episode", time="t2",
               source_ending="wasl", query_ending="wasl", onset="word_initial")
NATIVE = all((ROOT / "formal/.lake/build/bin" / name).is_file()
             for name in ("alignedAcquisitionV2", "licensedInference"))


class ArticleCompositeInputTests(unittest.TestCase):
    def test_invalid_bindings_and_budget_never_call_inference(self):
        with patch.object(inference, "evaluate") as call:
            for key in ("source_id", "revision", "scope", "time", "onset"):
                for value in (True, 1, "", "\ud800", "x\x85", "x" * 513):
                    result = bridge.evaluate(SOURCE, QUERY, **{**BINDING, key: value})
                    self.assertEqual(result["status"], "INVALID_INPUT")
                    self.assertFalse(result["chain_complete"])
            self.assertEqual(bridge.evaluate(SOURCE, QUERY, budget={})["status"], "INVALID_INPUT")
        call.assert_not_called()

    def test_forged_dataclass_budget_is_revalidated(self):
        budget = inference.InferenceBudget()
        object.__setattr__(budget, "max_readings", True)
        self.assertEqual(bridge.evaluate(SOURCE, QUERY, budget=budget)["status"], "INVALID_INPUT")

    def test_missing_v2_native_never_inherits_pr34_authority(self):
        with patch.object(acquisition, "_native", side_effect=FileNotFoundError), \
                patch.object(inference, "evaluate") as call:
            result = bridge.evaluate(SOURCE, QUERY, **BINDING)
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertIsNone(result["answer"])
        call.assert_not_called()

    def test_receipt_type_boundaries_before_replay(self):
        for report in ([], True, {"gates": ()}, {"verified": float("nan")}, {0: "key"}):
            result = bridge.verify(report, source=SOURCE, query=QUERY, **BINDING)
            self.assertEqual(result["status"], "INVALID_RECEIPT")


@unittest.skipUnless(NATIVE, "build alignedAcquisitionV2 and licensedInference")
class ArticleCompositeNativeTests(unittest.TestCase):
    def test_article_conditional_support_and_absent_premise_unknown(self):
        for source, expected in ((SOURCE, "SUPPORTED"), (RULE, "UNKNOWN")):
            result = bridge.evaluate(source, QUERY, **BINDING)
            self.assertTrue(result["chain_complete"], result)
            self.assertTrue(result["verified"])
            self.assertEqual(result["status"], expected)
            self.assertEqual(result["answer"]["status"], expected)
            self.assertEqual(result["schema"], "nabt.acquired-inference-result.v2")
            self.assertEqual(result["law_id"], "nabt.acquired-inference.v2")
            self.assertFalse(result["world_truth_established"])
            self.assertFalse(result["all_arabic_complete"])
            self.assertFalse(result["python_lean_composition_theorem"])

    def test_conflict_is_checked_result_without_world_truth(self):
        source = FACT + " لَمْ يَعْرِفْ زَيْدٌ الْحَقَّ."
        result = bridge.evaluate(source, "هَلْ عَرَفَ زَيْدٌ الْحَقَّ؟", **BINDING)
        self.assertTrue(result["chain_complete"], result)
        self.assertEqual(result["status"], "CONFLICT")
        self.assertFalse(result["world_truth_established"])

    def test_new_spelling_does_not_extend_pr34_language(self):
        for spelling in ("ٱلْحَقَّ", "اَلْحَقَّ", "الْحَقَّ", "الْحَقُّ", "الْقَوْمُ", "الْغُلَامُ"):
            source = FACT.replace("الْحَقَّ", spelling)
            result = bridge.evaluate(source, QUERY, **BINDING)
            self.assertEqual(result["source_acquisition"]["status"], "ACQUIRED", spelling)
            self.assertEqual(result["licensed_inference"]["status"], "UNKNOWN", spelling)
            self.assertEqual(result["status"], "DEFER", spelling)
            self.assertFalse(result["chain_complete"])
            self.assertIsNone(result["answer"])
            self.assertIn("reading_and_closures", result["blocked_by"])

    def test_connected_and_missing_vowels_cannot_borrow_nested_inference(self):
        for source, query, onset in ((SOURCE, QUERY, "connected"),
                                     ("عرف زيد الحق.", "هل سار زيد؟", "word_initial")):
            result = bridge.evaluate(source, query, **{**BINDING, "onset": onset})
            self.assertEqual(result["status"], "DEFER")
            self.assertFalse(result["chain_complete"])
            self.assertIsNone(result["answer"])
            self.assertIn("source_acquired", result["blocked_by"])
            replay = bridge.verify(result, source=source, query=query, **{**BINDING, "onset": onset})
            self.assertTrue(replay["replay_matches"])
            self.assertFalse(replay["valid"])

    def test_exact_original_bytes_and_separate_ending_modes(self):
        source, query = b" \r\n" + SOURCE.encode(), QUERY.encode() + b"\r\n"
        with patch.object(inference, "evaluate", wraps=inference.evaluate) as call:
            result = bridge.evaluate(source, query, **BINDING)
        self.assertTrue(result["chain_complete"], result)
        self.assertEqual(call.call_args.args, (source, query))
        self.assertEqual(result["source_acquisition"]["acquisition"]["text"].encode(), source)
        self.assertEqual(result["binding"]["native_scope"],
                         result["licensed_inference"]["native_result"]["source_scope"])
        paused = bridge.evaluate(SOURCE, QUERY, **{**BINDING, "source_ending": "waqf"})
        self.assertTrue(paused["chain_complete"], paused)
        self.assertEqual(paused["source_acquisition"]["shape_handoffs"][-1]["mode"], "waqf")
        self.assertEqual(paused["query_acquisition"]["shape_handoffs"][-1]["mode"], "wasl")

    def test_all_independent_bindings_and_exact_bytes_are_required(self):
        result = bridge.evaluate(SOURCE, QUERY, **BINDING)
        self.assertTrue(bridge.verify(result, source=SOURCE, query=QUERY, **BINDING)["valid"])
        for key, value in (("source_id", "other"), ("revision", "3"), ("scope", "other"),
                           ("time", "t3"), ("source_ending", "waqf"), ("query_ending", "waqf"),
                           ("onset", "connected")):
            self.assertFalse(bridge.verify(result, source=SOURCE, query=QUERY,
                                           **{**BINDING, key: value})["valid"], key)
        self.assertFalse(bridge.verify(result, source=SOURCE + " ", query=QUERY, **BINDING)["valid"])
        self.assertFalse(bridge.verify(result, source=SOURCE, query=QUERY + " ", **BINDING)["valid"])

    def test_receipt_mutations_cannot_relabel_or_rehash_authority(self):
        result = bridge.evaluate(SOURCE, QUERY, **BINDING)
        mutations = []
        for key, value in (("verified", 1), ("chain_complete", 1), ("law_id", "nabt.acquired-inference.v1"),
                           ("authority", "WORLD_TRUTH"), ("world_truth_established", True)):
            forged = copy.deepcopy(result)
            forged[key] = value
            mutations.append(forged)
        forged = copy.deepcopy(result)
        forged["source_acquisition"]["acquisition"]["pieces"][0]["start"] = False
        mutations.append(forged)
        forged = copy.deepcopy(result)
        forged["source_acquisition"]["source_evidence"]["sha256"] = "0" * 64
        mutations.append(forged)
        forged = copy.deepcopy(result)
        forged["binding"]["onset"] = "connected"
        mutations.append(forged)
        forged = copy.deepcopy(result)
        forged["licensed_inference"]["aggregate"]["skeptical_clean_positive"] = False
        mutations.append(forged)
        for forged in mutations:
            self.assertFalse(bridge.verify(forged, source=SOURCE, query=QUERY, **BINDING)["valid"])

    def test_runtime_bindings_and_native_identity_are_cross_checked(self):
        licensed = inference.evaluate(SOURCE, QUERY, source_id="unit", revision="2", scope="episode", time="t2")
        for key, value in (("source_text", SOURCE + " "), ("query_text", QUERY + " "),
                           ("source_scope", "other"), ("source_id", "other"), ("revision", "3")):
            forged = copy.deepcopy(licensed)
            forged["native_result"][key] = value
            with patch.object(inference, "evaluate", return_value=forged):
                result = bridge.evaluate(SOURCE, QUERY, **BINDING)
            self.assertFalse(result["chain_complete"])
            self.assertIn("same_binding", result["blocked_by"])
        original_read = acquisition.read_acquired
        def wrong_onset(*args, **kwargs):
            report = original_read(*args, **kwargs)
            report["onset"] = "connected"
            return report
        with patch.object(acquisition, "read_acquired", side_effect=wrong_onset):
            result = bridge.evaluate(SOURCE, QUERY, **BINDING)
        self.assertFalse(result["chain_complete"])
        self.assertIn("same_onset", result["blocked_by"])

    def test_resource_and_missing_verifiers_remain_distinct(self):
        with patch.object(inference, "_native", side_effect=FileNotFoundError):
            result = bridge.evaluate(SOURCE, QUERY, **BINDING)
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(result["chain_complete"])
        limited = bridge.evaluate(SOURCE, QUERY, **BINDING,
                                  budget=inference.InferenceBudget(max_closure_steps=0))
        self.assertEqual(limited["status"], "RESOURCE_EXHAUSTED")
        for error, status in (("RESOURCE_LIMIT", "RESOURCE_EXHAUSTED"),
                              ("SHAPE_REPLAY_FAILED", "VERIFICATION_UNAVAILABLE")):
            with patch.object(acquisition, "issue_certificate", side_effect=NabtError(error, "unit")):
                result = bridge.evaluate(SOURCE, QUERY, **BINDING)
            self.assertEqual(result["status"], status)
            self.assertIsNone(result["answer"])

    def test_cli_full_chain_and_independent_onset_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, query, receipt = (Path(temporary) / name for name in ("source", "query", "receipt"))
            source.write_bytes(SOURCE.encode())
            query.write_bytes(QUERY.encode())
            command = [sys.executable, "-m", "tools.article_acquisition_cli"]
            run = subprocess.run([*command, "infer", str(source), str(query)], cwd=ROOT,
                                 capture_output=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stdout)
            receipt.write_bytes(run.stdout)
            verify = [*command, "verify-infer", str(receipt), str(source), str(query)]
            replay = subprocess.run(verify, cwd=ROOT, capture_output=True, timeout=60)
            self.assertEqual(replay.returncode, 0, replay.stdout)
            replay = subprocess.run([*verify, "--onset", "connected"], cwd=ROOT,
                                    capture_output=True, timeout=60)
            self.assertEqual(replay.returncode, 2)
            self.assertEqual(json.loads(replay.stdout)["status"], "INVALID_RECEIPT")


if __name__ == "__main__":
    unittest.main()
