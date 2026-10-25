"""Metric and frozen protocol checks, independent of the inference implementation."""
from copy import deepcopy
import tempfile
from pathlib import Path
import unittest

from tools import benchmark_mantuq_inference as benchmark
from tools.mantuq_inference_benchmark_adapter import request_for


class InferenceBenchmarkTests(unittest.TestCase):
    def test_pinned_gold_and_counts(self):
        gold = benchmark.load_gold()
        self.assertEqual(len(gold["cases"]), 34)
        self.assertEqual(gold["expected_counts"],
                         {"guarded_cause": 14, "opposition": 6, "analogy": 8, "direct": 6})

    def test_edited_gold_cannot_replace_expected_results(self):
        raw = (benchmark.ROOT / benchmark.GOLD_PATH).read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "gold.json"
            path.write_bytes(raw.replace(b'"UNKNOWN"', b'"SUPPORTED"', 1))
            with self.assertRaisesRegex(ValueError, "Frozen inference gold"):
                benchmark.load_gold(path=path)

    def test_false_support_is_counted_independently(self):
        case = benchmark.load_gold()["cases"][1]
        observed = {"outcome": "SUPPORTED", "conditional_support": True,
                    "world_truth_established": False, "whole_arabic_complete": False}
        result = benchmark.score_observation(case, observed)
        self.assertTrue(result["false_support"])
        self.assertFalse(result["matched"])

    def test_missing_capability_is_unmeasured_not_pass(self):
        gold = benchmark.load_gold()
        def observer(_):
            return {"outcome": "UNMEASURED", "conditional_support": False,
                    "world_truth_established": False, "whole_arabic_complete": False}
        result = benchmark.run_benchmark(gold, observer)
        self.assertEqual(result["aggregate"]["unmeasured"], 34)
        self.assertEqual(result["aggregate"]["mismatched"], 0)
        self.assertFalse(result["complete_on_declared_diagnostic"])

    def test_boolean_and_integer_flags_are_not_interchangeable(self):
        case = benchmark.load_gold()["cases"][0]
        observed = dict(case["expected"])
        observed["conditional_support"] = 1
        with self.assertRaisesRegex(ValueError, "booleans"):
            benchmark.score_observation(case, observed)

    def test_world_or_language_claim_fails_even_when_status_matches(self):
        case = benchmark.load_gold()["cases"][0]
        for flag in ("world_truth_established", "whole_arabic_complete"):
            observed = {**case["expected"], flag: True}
            row = benchmark.score_observation(case, observed)
            self.assertTrue(row["authority_overclaim"])
            self.assertFalse(row["matched"])

    def test_inconsistent_status_is_rejected(self):
        case = benchmark.load_gold()["cases"][0]
        observed = {**case["expected"], "conditional_support": False}
        with self.assertRaisesRegex(ValueError, "disagree"):
            benchmark.score_observation(case, observed)

    def test_unexercised_pipeline_guard_is_not_a_matching_result(self):
        case = benchmark.load_gold()["cases"][0]
        observed = {**case["expected"], "contract_checks": {"all_installed_policies_examined": False}}
        row = benchmark.score_observation(case, observed)
        self.assertFalse(row["matched"])
        self.assertEqual(row["failed_contract_checks"], ["all_installed_policies_examined"])

    def test_no_metrics_imply_a_population_estimate(self):
        gold = benchmark.load_gold()
        result = benchmark.run_benchmark(gold, lambda case: deepcopy(case["expected"]))
        self.assertEqual(result["aggregate"]["matched"], 34)
        self.assertTrue(result["complete_on_declared_diagnostic"])
        self.assertFalse(result["statistical_population_accuracy_estimated"])
        self.assertFalse(result["whole_arabic_complete"])
        self.assertFalse(result["empirical_experiment_performed"])

    def test_transport_does_not_read_expected_answer(self):
        for case in benchmark.load_gold()["cases"]:
            changed = deepcopy(case)
            changed["expected"] = {"outcome": "invented", "conditional_support": "not a boolean"}
            self.assertEqual(request_for(case), request_for(changed))

    def test_transport_does_not_supply_missing_or_negated_obligations(self):
        cases = {case["id"]: case for case in benchmark.load_gold()["cases"]}
        missing = request_for(cases["C04"])["readings"][0]
        self.assertNotIn("blocker", {atom["predicate"] for atom in missing["hypotheses"]})
        no_bridge = request_for(cases["O01"])["readings"][0]
        self.assertIsNone(no_bridge["necessary_relation"])
        self.assertNotIn("necessary_bridge", {atom["predicate"] for atom in no_bridge["hypotheses"]})
        conflict = request_for(cases["C08"])["readings"][0]
        self.assertEqual({atom["positive"] for atom in conflict["hypotheses"] if atom["predicate"] == "blocker"},
                         {False, True})

    def test_context_counterexample_changes_evidence_but_not_requested_identity(self):
        cases = {case["id"]: case for case in benchmark.load_gold()["cases"]}
        baseline, changed = request_for(cases["A01"]), request_for(cases["A08"])
        self.assertEqual(baseline["conclusion"], changed["conclusion"])
        self.assertEqual(baseline["readings"][0]["requirements"], changed["readings"][0]["requirements"])
        self.assertNotEqual(baseline["readings"][0]["hypotheses"], changed["readings"][0]["hypotheses"])


if __name__ == "__main__":
    unittest.main()
