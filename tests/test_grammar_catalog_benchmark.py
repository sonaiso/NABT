"""Independent metric arithmetic and immutable source-judgment boundaries."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from tools.benchmark_grammar_catalog import GOLD_PATH, ROOT, load_gold, run_benchmark, score_ranking


class GrammarCatalogBenchmarkTests(unittest.TestCase):
    def test_frozen_judgments_and_source_spans_replay(self):
        gold = load_gold()
        self.assertEqual(len(gold["cases"]), 24)
        self.assertEqual(sum(bool(c["relevant_rule_ids"]) for c in gold["cases"]), 21)
        multi = next(c for c in gold["cases"] if c["id"] == "M01")
        self.assertEqual(len(multi["relevant_rule_ids"]), 3)
        self.assertEqual(len({e["spans"][0]["sha256"] for e in multi["evidence"]}), 1)

    def test_editing_a_gold_query_invalidates_the_frozen_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gold.json"
            path.write_bytes((ROOT / GOLD_PATH).read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "Frozen retrieval gold changed"):
                load_gold(path=path)

    def test_independently_calculated_metrics(self):
        result = score_ranking(["b", "a", "c", "d"], ["a", "c"])
        self.assertEqual(result["recall_at_k"], {"1": 0.0, "3": 1.0, "5": 1.0, "10": 1.0})
        self.assertEqual(result["reciprocal_rank"], 0.5)
        self.assertEqual(score_ranking(["a"], ["a", "b", "c"])["recall_at_k"]["1"], 1 / 3)
        self.assertEqual(score_ranking([], ["a"])["reciprocal_rank"], 0.0)

    def test_unjudged_queries_do_not_become_perfect_recall_or_precision(self):
        metrics = score_ranking(["possible_unjudged_match"], [])
        self.assertIsNone(metrics["reciprocal_rank"])
        self.assertTrue(all(v is None for v in metrics["recall_at_k"].values()))
        self.assertNotIn("precision", metrics)

    def test_duplicate_ids_and_malformed_domains_rejected(self):
        for ranking, relevant, cutoffs in [(["a", "a"], ["a"], (1,)), (["a"], ["a", "a"], (1,)),
                                           ([True], ["a"], (1,)), (["a"], ["a"], (True,)),
                                           (["a"], ["a"], (0,)), (["a"], ["a"], (-1,))]:
            with self.subTest(ranking=ranking, relevant=relevant, cutoffs=cutoffs), self.assertRaises(ValueError):
                score_ranking(ranking, relevant, cutoffs)

    def test_hard_hint_filter_is_observable_without_changing_gold(self):
        gold = {"judgment_scope": "minimum set", "independence": "test oracle", "cases": [
            {"id": "one", "kind": "paraphrase", "query": "query", "relevant_rule_ids": ["a", "b"],
             "adversarial_hints": {"chapter": "wrong"}}]}
        catalog = {"rules": [{"rule_key": "a"}, {"rule_key": "b"}]}
        def dropping_search(catalog, query, **kwargs):
            keys = ["b"] if kwargs.get("hints") else ["a", "b"]
            return {"authority": "RETRIEVAL_ONLY", "exhaustive_language_claim": False,
                    "candidates": [{"id": key, "kind": "rule"} for key in keys]}
        before = deepcopy(gold)
        report = run_benchmark(catalog, gold, dropping_search)
        self.assertFalse(report["soft_hint_nonfiltering_observed"])
        self.assertFalse(report["hint_ranking_invariant_observed"])
        self.assertEqual(report["cases"][0]["hints_removed_baseline_candidates"], ["a"])
        self.assertEqual(report["aggregate"]["baseline"]["micro_recall_at_k"]["3"], 1.0)
        self.assertEqual(report["aggregate"]["adversarial_hints"]["micro_recall_at_k"]["3"], 0.5)
        self.assertEqual(before, gold)
        self.assertFalse(report["whole_arabic_complete"])

    def test_hint_reordering_is_distinct_from_hard_filtering(self):
        gold = {"judgment_scope": "minimum set", "independence": "test oracle", "cases": [
            {"id": "one", "kind": "paraphrase", "query": "query", "relevant_rule_ids": ["a"],
             "adversarial_hints": {"chapter": "wrong"}}]}
        def reordering_search(catalog, query, **kwargs):
            keys = ["b", "a"] if kwargs.get("hints") else ["a", "b"]
            return {"authority": "RETRIEVAL_ONLY", "exhaustive_language_claim": False,
                    "candidates": [{"id": key, "kind": "rule"} for key in keys]}
        report = run_benchmark({"rules": [{"rule_key": "a"}, {"rule_key": "b"}]}, gold, reordering_search)
        self.assertTrue(report["soft_hint_nonfiltering_observed"])
        self.assertFalse(report["hint_ranking_invariant_observed"])
        self.assertEqual(report["aggregate"]["adversarial_hints"]["mean_reciprocal_rank"], 0.5)

    def test_forged_retrieval_authority_and_ids_are_rejected(self):
        gold = {"judgment_scope": "minimum set", "independence": "test oracle", "cases": [
            {"id": "one", "kind": "paraphrase", "query": "query", "relevant_rule_ids": ["a"], "adversarial_hints": {}}]}
        for key, authority, complete in [("fake", "RETRIEVAL_ONLY", False), ("a", "PROVED", False),
                                          ("a", "RETRIEVAL_ONLY", True)]:
            def forged(*args, **kwargs):
                return {"authority": authority, "exhaustive_language_claim": complete,
                        "candidates": [{"kind": "rule", "id": key}]}
            with self.subTest(key=key, authority=authority, complete=complete), self.assertRaises(ValueError):
                run_benchmark({"rules": [{"rule_key": "a"}]}, gold, forged)


if __name__ == "__main__":
    unittest.main()
