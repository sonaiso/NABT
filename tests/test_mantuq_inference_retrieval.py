"""Trust-boundary tests, independent of the inherited ranking arithmetic."""
import copy
import unittest

from tools.grammar_catalog.retrieval import RetrievalError
from tools.mantuq_inference.retrieval import InferenceSearchIndex, INPUT_RECIPE, iter_documents
from tools.mantuq_inference.inventory import build_inventory
from tools.mantuq_inference.links import _compose, ADAPTER_DECLARATIONS


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.index = InferenceSearchIndex()

    def vector(self, **overrides):
        value = {"schema": "nabt.retrieval-vectors.v1", "catalog_sha256": self.index.catalog_sha256,
                 "model_id": "synthetic-test-only", "revision": "a" * 40, "dimensions": 3,
                 "input_recipe": INPUT_RECIPE,
                 "scores": [{"kind": "rule", "id": "analogy", "cosine_similarity": .9}]}
        return {**value, **overrides}

    def test_same_shared_projection_and_exact_source_restoration(self):
        inventory = build_inventory()
        expected = {(k, i): t for k, i, t, _ in iter_documents(inventory)}
        self.assertEqual(len(expected), 63)
        for key, text in expected.items():
            self.assertEqual(self.index._docs[key]["search_text"], text)
        quotation = inventory["passages"][6]
        restored = self.index.rehydrate("passage", quotation["passage_id"])
        self.assertEqual(restored["raw_text"], quotation["raw_text"])

    def test_hints_cannot_prune_or_reorder_and_no_authority(self):
        plain = self.index.search("مفهوم المخالفة", kind="rule")
        hinted = self.index.search("مفهوم المخالفة", kind="rule", hints={"chapter": "القياس"})
        self.assertEqual([r["id"] for r in plain["candidates"]],
                         [r["id"] for r in hinted["candidates"]])
        self.assertEqual(plain["authority"], "RETRIEVAL_ONLY")
        self.assertFalse(plain["world_truth_established"])
        self.assertFalse(plain["occurrence_classification_proved"])

    def test_vector_bound_to_inventory_and_model_projection(self):
        result = self.index.search("غيرمعجمي", vector_scores=self.vector(), kind="rule")
        self.assertEqual(result["candidates"][0]["id"], "analogy")
        self.assertFalse(result["scores_are_probabilities"])
        for updates in ({"catalog_sha256": "0" * 64}, {"input_recipe": "wrong"},
                        {"dimensions": True}, {"revision": "main"}):
            with self.assertRaises(RetrievalError):
                self.index.search("المفهوم", vector_scores=self.vector(**updates))
        for bad in (float("nan"), float("inf"), True, 10 ** 1000, 1.1):
            with self.assertRaises(RetrievalError):
                self.index.search("المفهوم", vector_scores=self.vector(scores=[
                    {"kind": "rule", "id": "analogy", "cosine_similarity": bad}]))

    def test_database_text_and_truth_flags_never_rehydrate(self):
        proposal = {"schema": "nabt.inference-database-proposals.v1",
                    "inventory_sha": self.index.catalog_sha256, "candidates": [
                        {"kind": "rule", "id": "analogy", "rrf_score": .1,
                         "record": {"title": "fabricated", "world_truth_established": True}}]}
        result = self.index.rehydrate_database(proposal)
        self.assertEqual(result["candidates"][0]["record"], self.index.rehydrate("rule", "analogy"))
        self.assertFalse(result["world_truth_established"])
        for field, value in (("inventory_sha", "0" * 64), ("schema", "nabt.database-proposals.v1")):
            with self.assertRaises(RetrievalError):
                self.index.rehydrate_database({**proposal, field: value})
        for rows in ([{"kind": "rule", "id": "invented"}], proposal["candidates"] * 2):
            with self.assertRaises(RetrievalError):
                self.index.rehydrate_database({**proposal, "candidates": rows})


class ProofLinkTests(unittest.TestCase):
    def fixture(self):
        inventory = build_inventory()
        names = sorted({n for r in inventory["rules"] for n in r["theorem_names"]} | set(ADAPTER_DECLARATIONS))
        rows = [{"name": n, "canonical_name": n, "statement_sha256": str(i),
                 "source_path": "formal/synthetic.lean", "source_sha256": "a" * 64}
                for i, n in enumerate(names)]
        return inventory, {"theorems": rows, "inputs": {"formal/synthetic.lean": "a" * 64}}

    def test_references_resolve_without_inventing_source_for_analogy(self):
        inventory, compiled = self.fixture()
        result = _compose(inventory, compiled)
        self.assertEqual(result["counts"]["policies"], 9)
        self.assertEqual(result["counts"]["unresolved_references"], 0)
        for row in result["edges"]:
            if row["policy_id"] == "analogy":
                self.assertEqual(row["source_passage_ids"], [])
                self.assertTrue(row["source_context_only"])
        self.assertFalse(result["source_translation_fidelity_established"])

    def test_unresolved_alias_and_unbound_source_fail(self):
        inventory, compiled = self.fixture()
        for mutation in ("missing", "alias", "source"):
            changed = copy.deepcopy(compiled)
            if mutation == "missing":
                changed["theorems"].pop()
            elif mutation == "alias":
                changed["theorems"][0]["canonical_name"] = "unknown"
            else:
                changed["inputs"]["formal/synthetic.lean"] = "b" * 64
            with self.assertRaises(ValueError):
                _compose(inventory, changed)


if __name__ == "__main__":
    unittest.main()
