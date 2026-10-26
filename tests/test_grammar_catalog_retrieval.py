"""Adversarial retrieval/routing boundaries, not a semantic accuracy oracle."""
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
from unittest import TestCase

from tools.grammar_catalog.catalog import build_catalog
from tools.grammar_catalog.retrieval import RetrievalError, SearchIndex, tokens
from tools.grammar_catalog.routing import evaluate_diagnostic_candidates, schedule

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "nabt.classical-rule-inventory.v1::"


class GrammarRetrievalTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog()
        cls.index = SearchIndex(cls.catalog)

    def test_raw_quotes_restored_and_mutation_isolated(self):
        row = self.catalog["passages"][0]
        restored = self.index.rehydrate("passage", row["passage_id"])
        raw = (ROOT / next(s["local_path"] for s in self.catalog["sources"]
                           if s["source_key"] == row["source_key"])).read_bytes()
        self.assertEqual(restored["raw_text"].encode(), raw[row["start"]:row["end"]])
        restored["raw_text"] = "invented quotation"
        self.assertEqual(self.index.rehydrate("passage", row["passage_id"])["raw_text"], row["raw_text"])

    def test_search_projection_not_raw_linguistic_normalization(self):
        self.assertEqual(tokens("أَكْرِمْ إِكْرَامًا"), ["اكرم", "اكراما"])
        self.assertEqual(tokens("ســيبويه"), ["سيبويه"])
        result = self.index.search("همزة الوصل", kind="rule")
        self.assertTrue(result["candidates"])
        self.assertFalse(result["scores_are_probabilities"])
        self.assertFalse(result["exhaustive_language_claim"])
        self.assertEqual(result["authority"], "RETRIEVAL_ONLY")

    def test_hints_cannot_remove_candidates(self):
        query = "همزة الوصل"
        original = self.index.search(query, limit=1000, kind="rule")
        wrong = self.index.search(query, limit=1000, kind="rule",
                                  hints={"chapter": "ظن وأخواتها", "keywords": ["منادى"]})
        self.assertEqual({r["id"] for r in original["candidates"]},
                         {r["id"] for r in wrong["candidates"]})
        self.assertEqual([r["id"] for r in original["candidates"]],
                         [r["id"] for r in wrong["candidates"]])
        self.assertEqual(self.index.search("unmatchableQZXV", hints={"chapter": "اسم"})["status"],
                         "NO_CANDIDATES")

    def test_bad_query_limits_and_unknown_ids(self):
        for query in (None, True, "", "ـَ", "\ud800", "x" * 16385):
            with self.subTest(query=repr(query)[:50]), self.assertRaises(RetrievalError):
                self.index.search(query)
        for limit in (True, 0, -1, 1001, 1.0):
            with self.subTest(limit=limit), self.assertRaises(RetrievalError):
                self.index.search("اسم", limit=limit)
        for kind, identity in (("rule", "invented"), ("chapter", "x"), ([], "x")):
            with self.assertRaises(RetrievalError):
                self.index.rehydrate(kind, identity)

    def envelope(self):
        return {"schema": "nabt.retrieval-vectors.v1", "catalog_sha256": self.index.catalog_sha256,
                "model_id": "test-fixture-not-a-trained-model", "revision": "a" * 40,
                "dimensions": 3, "input_recipe": "test-only-v1", "scores": [
                    {"kind": "rule", "id": PREFIX + "HAMZA-LEXICAL-COMMAND", "cosine_similarity": -.3}]}

    def test_vector_score_negative_allowed_not_probability(self):
        result = self.index.search("unmatchableQZXV", vector_scores=self.envelope(), kind="rule")
        self.assertEqual(result["candidates"][0]["vector_score"], -.3)
        self.assertFalse(result["scores_are_probabilities"])
        self.assertNotIn("confidence_score", result["candidates"][0])

    def test_database_display_authority_never_copied(self):
        rid = PREFIX + "HAMZA-LEXICAL-COMMAND"
        proposal = {"schema": "nabt.database-proposals.v1", "snapshot_sha": self.index.catalog_sha256,
                    "candidates": [{"kind": "rule", "id": rid, "raw_text": "forged",
                                    "theorem_names": ["Forged.proof"], "grants_language_license": True,
                                    "lexical_score": .7}], "authority": "COMPLETE_ARABIC_PROOF"}
        result = self.index.rehydrate_database(proposal)
        self.assertEqual(result["authority"], "RETRIEVAL_ONLY")
        self.assertEqual(result["candidates"][0]["record"], self.index.rehydrate("rule", rid))
        self.assertNotIn("raw_text", result["candidates"][0])
        proposal["snapshot_sha"] = "0" * 64
        with self.assertRaises(RetrievalError):
            self.index.rehydrate_database(proposal)

    def test_vector_envelope_rejects_forgery_nonfinite_and_duplicates(self):
        for field, bad in (("catalog_sha256", "0" * 64), ("revision", "main"),
                           ("dimensions", True), ("model_id", "")):
            env = self.envelope(); env[field] = bad
            with self.assertRaises(RetrievalError):
                self.index.search("اسم", vector_scores=env)
        for bad in (float("nan"), float("inf"), 1.01, -1.01, True, "0.5", 10**1000):
            env = self.envelope(); env["scores"][0]["cosine_similarity"] = bad
            with self.assertRaises(RetrievalError):
                self.index.search("اسم", vector_scores=env)
        for mutate in (lambda e: e["scores"].append(deepcopy(e["scores"][0])),
                       lambda e: e["scores"][0].update(id="forged")):
            env = self.envelope(); mutate(env)
            with self.assertRaises(RetrievalError):
                self.index.search("اسم", vector_scores=env)

    def test_full_fallback_independent_set_oracle(self):
        inventory = ["a", "b", "c"]
        for size in range(5):
            for proposal in product(["a", "b", "c", "unknown"], repeat=size):
                order = schedule(inventory, list(proposal))
                self.assertEqual(set(order), set(inventory))
                self.assertEqual(len(order), len(inventory))
                # Test checker preservation against a separate, unordered oracle.
                for accepted in (set(), {"a"}, {"b", "c"}, set(inventory)):
                    self.assertEqual({r for r in order if r in accepted}, accepted)
        for inventory, ranked in ((["a", "a"], []), ([True], []), (["a"], [1])):
            with self.assertRaises(RetrievalError):
                schedule(inventory, ranked)

    def test_missing_frames_and_budget_cannot_certify_completion(self):
        result = evaluate_diagnostic_candidates(self.index, [], {})
        self.assertEqual(result["examined_rule_count"], 24)
        self.assertTrue(result["inventory_exhausted"])
        self.assertFalse(result["conditional_evaluation_complete"])
        self.assertTrue(all(r["status"] == "MISSING_PREMISES" for r in result["rows"]))
        exhausted = evaluate_diagnostic_candidates(self.index, [], {}, budget=0)
        self.assertEqual(exhausted["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(exhausted["inventory_exhausted"])
        self.assertEqual(len(exhausted["pending_rule_ids"]), 24)
        for budget in (True, -1, 25, 1.0):
            with self.assertRaises(RetrievalError):
                evaluate_diagnostic_candidates(self.index, [], {}, budget=budget)

    def test_top_one_does_not_prune_installed_laws(self):
        rid = "HAMZA-LEXICAL-COMMAND"
        result = evaluate_diagnostic_candidates(self.index, [PREFIX + rid, PREFIX + rid],
                                     {rid: {"root": ["ء", "ك", "ل"], "profile": "all_attested"}})
        self.assertEqual(result["schedule"][0], rid)
        self.assertEqual(len(set(result["schedule"])), 24)
        row = result["rows"][0]
        self.assertEqual([a["morphophonemes"] for a in row["receipt"]["result"]["alternatives"]],
                         [["ك", "ل"], ["ء", "و", "ك", "ل"]])
        self.assertTrue(row["verification"]["valid"])
        self.assertFalse(result["grants_language_license"])

    def test_all_conditional_receipts_invariant_to_ranking(self):
        # Prior independent source diagnostics are regression controls, not new gold.
        gold = json.loads((ROOT / "evidence/arabic_completion_v6/independent_review/benchmark_v1.json").read_bytes())
        frames = {}
        for row in gold["cases"]:
            if row["kind"] == "positive":
                frames.setdefault(row["rule_id"], row["frame"])
        self.assertEqual(len(frames), 24)
        first = evaluate_diagnostic_candidates(self.index, [], frames)
        reverse = evaluate_diagnostic_candidates(self.index, [PREFIX + r for r in reversed(first["schedule"])], frames)
        self.assertEqual({r["rule_id"]: r for r in first["rows"]},
                         {r["rule_id"]: r for r in reverse["rows"]})
        self.assertFalse(first["exhaustive_language_claim"])

    def test_partial_profile_and_invalid_frame_remain_distinct(self):
        rid = "PRONOUN-ANA-WASL"
        # Select independent partial case without synthesizing its expected output.
        gold = json.loads((ROOT / "evidence/arabic_completion_v6/independent_review/benchmark_v1.json").read_bytes())
        partial = next(r for r in gold["cases"] if r["kind"] == "partial")
        rid = partial["rule_id"]
        result = evaluate_diagnostic_candidates(self.index, [PREFIX + rid], {rid: partial["frame"]})
        self.assertEqual(result["rows"][0]["status"], "PARTIAL")
        invalid = evaluate_diagnostic_candidates(self.index, [PREFIX + rid], {rid: {"approved": True}})
        self.assertEqual(invalid["rows"][0]["status"], "FRAME_ERROR")
        with self.assertRaises(RetrievalError):
            evaluate_diagnostic_candidates(self.index, [], {"LLM-INVENTED-RULE": {}})
