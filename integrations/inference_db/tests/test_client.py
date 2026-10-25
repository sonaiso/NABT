"""Pure source/identity/projection tests; no server or model download."""
import copy
import unittest

from integrations.inference_db import client
from integrations.grammar_db.client import search_projection
from tools.grammar_catalog.catalog import build_catalog
from tools.mantuq_inference import build_inventory
from tools.mantuq_inference.retrieval import inventory_sha256, iter_documents


class InferenceClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory, cls.catalog = build_inventory(), build_catalog()

    def test_shared_projection_and_snapshot_identity(self):
        projected = client.project_inventory(self.inventory, self.catalog)
        expected = {rid: search_projection(text) for kind, rid, text, _ in iter_documents(self.inventory) if kind == "rule"}
        self.assertEqual({r["rule_id"]: r["search_text"] for r in projected["rules"]}, expected)
        self.assertEqual(client.inventory_digest(self.inventory), inventory_sha256(self.inventory))
        self.assertEqual(len(projected["rules"]), 9)
        self.assertEqual(len(projected["sources"]), 4)
        self.assertEqual(len(projected["passages"]), 54)
        self.assertEqual(sum(len(r["payload"]["reviewed_context_passage_ids"]) for r in projected["rules"]), 40)
        self.assertEqual(projected["navigation"], [])

    def test_projection_rejects_malformed_source_spans(self):
        for field, value in (("start", True), ("end", 10**100), ("sha256", "a" * 64), ("raw_text", "invented")):
            malformed = copy.deepcopy(self.inventory)
            malformed["passages"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                client.project_inventory(malformed, self.catalog)

    def test_projection_rejects_missing_typed_references(self):
        for field, value in (("source_passage_ids", ["missing"]), ("reviewed_context_passage_ids", ["missing"]),
                             ("theorem_names", [True]), ("profile", True)):
            malformed = copy.deepcopy(self.inventory)
            malformed["rules"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                client.project_inventory(malformed, self.catalog)

    def test_embedding_identity_binds_model_projection_dimensions_and_inventory(self):
        first = client.embedding_metadata("a" * 64, "fixture/model", "b" * 40, 3)
        self.assertEqual(client._check_metadata(first), first)
        for key, value in (("inventory_sha", "c" * 64), ("model_id", "fixture/other"), ("revision", "d" * 40), ("dimensions", 2)):
            args = dict(inventory_sha="a" * 64, model_id="fixture/model", revision="b" * 40, dimensions=3)
            args[key] = value
            self.assertNotEqual(first["run_id"], client.embedding_metadata(**args)["run_id"])
        for value in (True, 3.0, 0, 16001):
            with self.assertRaises(ValueError):
                client.embedding_metadata("a" * 64, "fixture/model", "b" * 40, value)
        for change in ({"dimensions": True}, {"input_recipe": "unknown"}, {"model_revision": "main"}, {"authority": "PROOF"}):
            with self.assertRaises(ValueError):
                client._check_metadata(dict(first, **change))


if __name__ == "__main__":
    unittest.main()
