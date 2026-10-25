import unittest
from unittest.mock import patch

from tools.grammar_catalog.retrieval import RetrievalError
from tools.mantuq_inference.pipeline import run
from tools.mantuq_sources import build_inventory


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.ids = [r["rule_id"] for r in build_inventory()["rules"]]

    def test_reverse_top_one_does_not_remove_plan(self):
        # Stub the heavy proof checker only to inspect routing; benchmark C12
        # separately invokes the real native checker with a complete plan.
        plan = {"policy_id": "guarded_cause"}
        with patch("tools.mantuq_inference.pipeline.evaluate", return_value={"status": "FIXTURE"}) as evaluator:
            result = run("المطابقة", {"guarded_cause": plan}, display_limit=1,
                         preferred_order=self.ids[::-1])
        evaluator.assert_called_once()
        self.assertEqual({r["policy_id"] for r in result["rows"]}, set(self.ids))
        self.assertTrue(result["inventory_exhausted"])
        self.assertLessEqual(len(result["retrieval"]["candidates"]), 1)
        self.assertEqual(next(r["result"]["status"] for r in result["rows"]
                              if r["policy_id"] == "guarded_cause"), "FIXTURE")

    def test_budget_exhaustion_and_missing_premises_are_separate(self):
        stopped = run("المفهوم", {}, max_policies=0)
        self.assertEqual(stopped["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(stopped["pending_policy_ids"], stopped["schedule"])
        completed = run("المفهوم", {})
        self.assertEqual(completed["status"], "POLICY_SCAN_COMPLETE")
        self.assertTrue(all(r["result"]["status"] == "UNKNOWN" for r in completed["rows"]))
        self.assertFalse(completed["whole_arabic_complete"])

    def test_unknown_or_misbound_plans_and_boolean_budget_rejected(self):
        for plans in ({"unknown": {"policy_id": "unknown"}}, {"matching": {"policy_id": "analogy"}}):
            with self.assertRaises(RetrievalError):
                run("المنطوق", plans)
        with self.assertRaises(RetrievalError):
            run("المنطوق", {}, max_policies=True)
        with self.assertRaises(RetrievalError):
            run("المنطوق", {}, preferred_order=["unknown"])


if __name__ == "__main__":
    unittest.main()
