"""Real PostgreSQL/pgvector constraints; synthetic geometry is not NLP quality.

Requires NABT_TEST_DATABASE_URL pointing to a disposable database. The grammar
suite may run first; this suite refuses to replace an inference schema.
"""
import copy
import os
from pathlib import Path
import unittest

from integrations.grammar_db import client as grammar
from integrations.grammar_db.tests.test_postgres import fixture as grammar_fixture
from integrations.inference_db import client
from tools.grammar_catalog.catalog import build_catalog, catalog_sha256
from tools.mantuq_inference import build_inventory
from tools.mantuq_inference.retrieval import InferenceSearchIndex

DSN = os.environ.get("NABT_TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[3]


@unittest.skipUnless(DSN, "NABT_TEST_DATABASE_URL is not set; inference PostgreSQL tests not executed")
class InferencePostgreSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        cls.psycopg = psycopg
        cls.connection = psycopg.connect(DSN, autocommit=True)
        cls.addClassCleanup(cls.connection.close)
        if not cls.connection.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='nabt_catalog')").fetchone()[0]:
            grammar.initialize(cls.connection)
        client.initialize(cls.connection)
        cls.catalog_sha, cls.inventory_sha = "5" * 64, "4" * 64
        synthetic = grammar_fixture()
        with cls.connection.transaction():
            grammar._insert_verified_catalog(cls.connection, synthetic, cls.catalog_sha)
        cls.inventory = build_inventory()
        cls.projection = client.project_inventory(cls.inventory, synthetic)
        with cls.connection.transaction():
            # Explicit synthetic DB fixture, not source-replaying public import.
            client._insert_projection(cls.connection, cls.projection, cls.inventory_sha,
                                      cls.catalog_sha, "nabt.inference-test-fixture.v1")
        cls.metadata = client.embedding_metadata(cls.inventory_sha, "test/synthetic", "a" * 40, 3)
        client.store_embeddings(cls.connection, cls.metadata, [
            ("matching", [1, 0, 0]), ("inclusion", [0, 1, 0]), ("opposition", [-1, 0, 0])])
        cls.profile = cls.projection["profiles"][0]
        cls.passage = cls.inventory["passages"][0]["passage_id"]
        with cls.connection.transaction(), cls.connection.cursor() as cur:
            cur.execute("INSERT INTO nabt_inference.contexts VALUES (%s,'test-context',%s,'synthetic context','{}')", (cls.inventory_sha, cls.profile))
            cur.execute("INSERT INTO nabt_inference.profiles VALUES (%s,'test-other','synthetic distinct profile')", (cls.inventory_sha,))
            cur.executemany("INSERT INTO nabt_inference.lexemes VALUES (%s,%s,%s,NULL)",
                            [(cls.inventory_sha, "word1", "لفظ"), (cls.inventory_sha, "word2", "لفظ ثان")])
            cur.executemany("INSERT INTO nabt_inference.concepts VALUES (%s,%s,%s)",
                            [(cls.inventory_sha, "sense1", "synthetic first"), (cls.inventory_sha, "sense2", "synthetic second")])

    def test_exact_vector_geometry_and_complete_stream_fusion(self):
        result = client.search(self.connection, self.inventory_sha, "", embedding=[1, 0, 0], embedding_run=self.metadata)
        self.assertEqual([r["id"] for r in result["candidates"]], ["matching", "inclusion", "opposition"])
        self.assertEqual([r["vector_score"] for r in result["candidates"]], [1.0, 0.0, -1.0])
        self.assertEqual(result["vector_mode"], "EXACT")
        self.assertEqual(result["stored_rule_count"], 9)
        self.assertEqual(result["stored_vector_count"], 3)
        self.assertFalse(result["vector_inventory_complete"])
        fused = client.search(self.connection, self.inventory_sha, "المخالفة", embedding=[1, 0, 0], embedding_run=self.metadata, k=1)
        self.assertEqual(fused["authority"], "RETRIEVAL_ONLY")
        self.assertGreater(fused["candidate_count_before_limit"], len(fused["candidates"]))
        self.assertTrue(all(r["kind"] == "rule" and "raw_text" not in r for r in result["candidates"]))

    def test_many_to_many_senses_preserve_profile_and_context(self):
        context_rows = self.connection.execute("""SELECT count(*), count(DISTINCT rule_id),
            bool_and(source_context_only), bool_or(linguistic_license_established),
            bool_or(executable_rule_changed) FROM nabt_inference.reviewed_contexts
            WHERE inventory_sha=%s""", (self.inventory_sha,)).fetchone()
        self.assertEqual(context_rows, (40, 5, True, False, False))
        with self.assertRaises(self.psycopg.errors.CheckViolation):
            with self.connection.transaction():
                self.connection.execute("""INSERT INTO nabt_inference.reviewed_contexts
                    VALUES (%s,'inclusion',%s,'REVIEWED_CONTEXT_CANDIDATE_BASIS',true,true,false)""",
                                        (self.inventory_sha, self.passage))
        with self.connection.transaction():
            for word, concept in (("word1", "sense1"), ("word1", "sense2"), ("word2", "sense1")):
                self.connection.execute("INSERT INTO nabt_inference.senses VALUES (%s,%s,%s,'test-context',%s,%s)",
                                        (self.inventory_sha, word, concept, self.profile, self.passage))
        count = self.connection.execute("SELECT count(*) FROM nabt_inference.senses WHERE inventory_sha=%s", (self.inventory_sha,)).fetchone()[0]
        self.assertEqual(count, 3)
        with self.assertRaises(self.psycopg.errors.ForeignKeyViolation) as caught:
            with self.connection.transaction():
                self.connection.execute("INSERT INTO nabt_inference.senses VALUES (%s,'word2','sense2','test-context','test-other',%s)", (self.inventory_sha, self.passage))
        self.assertEqual(caught.exception.diag.constraint_name, "senses_inventory_sha_context_id_profile_id_fkey")

    def test_observation_is_unreviewed_without_empirical_truth_default(self):
        self.connection.execute("""INSERT INTO nabt_inference.observations
            (inventory_sha,observation_id,context_id,concept_id)
            VALUES (%s,'observation','test-context','sense1')""", (self.inventory_sha,))
        row = self.connection.execute("SELECT protocol_uri,evidence_sha,result_text,review_state FROM nabt_inference.observations WHERE inventory_sha=%s", (self.inventory_sha,)).fetchone()
        self.assertEqual(row, (None, None, None, "UNREVIEWED"))
        for state in ("TRUE", "PROVED"):
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                with self.connection.transaction():
                    self.connection.execute("INSERT INTO nabt_inference.observations VALUES (%s,%s,'test-context','sense1',NULL,NULL,NULL,%s)", (self.inventory_sha, state, state))
        with self.assertRaises(self.psycopg.errors.CheckViolation):
            with self.connection.transaction():
                self.connection.execute("INSERT INTO nabt_inference.observations VALUES (%s,'incomplete','test-context','sense1','protocol',NULL,NULL,'REPORTED')", (self.inventory_sha,))

    def test_blocker_absence_requires_explicit_negative_polarity(self):
        with self.assertRaises(self.psycopg.errors.CheckViolation):
            with self.connection.transaction():
                self.connection.execute("INSERT INTO nabt_inference.obligations VALUES (%s,'guarded_cause',0,'blocker_absence','blocker',true)", (self.inventory_sha,))
        self.connection.execute("INSERT INTO nabt_inference.obligations VALUES (%s,'guarded_cause',0,'blocker_absence','blocker',false)", (self.inventory_sha,))

    def test_cross_catalog_binding_is_not_inferred_from_known_document(self):
        other = "6" * 64
        with self.connection.transaction():
            grammar._insert_verified_catalog(self.connection, grammar_fixture(), other)
        with self.assertRaises(self.psycopg.errors.ForeignKeyViolation) as caught:
            with self.connection.transaction():
                self.connection.execute("INSERT INTO nabt_inference.grammar_navigation VALUES (%s,'matching',%s,'passage:p1')", (self.inventory_sha, other))
        self.assertEqual(caught.exception.diag.constraint_name, "grammar_navigation_inventory_sha_catalog_sha_fkey")

    def test_vector_composite_foreign_keys_and_unit_checks(self):
        cases = [("agreement", 2, "[1,0]", self.psycopg.errors.ForeignKeyViolation,
                  "embeddings_inventory_sha_run_id_dimensions_fkey"),
                 ("unknown", 3, "[1,0,0]", self.psycopg.errors.ForeignKeyViolation,
                  "embeddings_inventory_sha_rule_id_fkey"),
                 ("agreement", 3, "[0,0,0]", self.psycopg.errors.CheckViolation, None)]
        for rule, dims, vector, error, constraint in cases:
            with self.subTest(rule=rule, dims=dims), self.assertRaises(error) as caught:
                with self.connection.transaction():
                    self.connection.execute("INSERT INTO nabt_inference.embeddings VALUES (%s,%s,%s,%s,%s::vector)",
                                            (self.inventory_sha, self.metadata["run_id"], rule, dims, vector))
            if constraint:
                self.assertEqual(caught.exception.diag.constraint_name, constraint)

    def test_bad_queries_metadata_and_numeric_limits_do_not_gain_authority(self):
        for k in (True, 0, 1.0, 1001):
            with self.assertRaises(ValueError):
                client.search(self.connection, self.inventory_sha, "", k=k)
        for metadata in (dict(self.metadata, dimensions=True), dict(self.metadata, input_recipe="unknown")):
            with self.assertRaises(ValueError):
                client.search(self.connection, self.inventory_sha, "", embedding=[1, 0, 0], embedding_run=metadata)
        result = client.search(self.connection, self.inventory_sha, "'; DROP TABLE nabt_inference.rules; --")
        self.assertFalse(result["exhaustive_language_claim"])
        self.assertEqual(result["stored_rule_count"], 9)

    def test_immutable_and_atomic_import(self):
        for query in ("UPDATE nabt_inference.rules SET source_status='PROVED' WHERE inventory_sha=%s",
                      "DELETE FROM nabt_inference.snapshots WHERE inventory_sha=%s"):
            with self.assertRaises(self.psycopg.errors.RaiseException):
                with self.connection.transaction():
                    self.connection.execute(query, (self.inventory_sha,))
        with self.assertRaises(self.psycopg.errors.RaiseException):
            with self.connection.transaction():
                self.connection.execute("TRUNCATE nabt_inference.embeddings")
        malformed = copy.deepcopy(self.projection)
        malformed["rules"][0]["payload"]["source_passage_ids"] = ["absent"]
        with self.assertRaises(self.psycopg.errors.ForeignKeyViolation) as caught:
            with self.connection.transaction():
                client._insert_projection(self.connection, malformed, "7" * 64, self.catalog_sha, "synthetic")
        self.assertEqual(caught.exception.diag.constraint_name, "rule_passages_inventory_sha_passage_id_fkey")
        self.assertIsNone(self.connection.execute("SELECT 1 FROM nabt_inference.snapshots WHERE inventory_sha=%s", ("7" * 64,)).fetchone())

    def test_public_import_replays_sources_and_local_rehydration(self):
        catalog = build_catalog()
        catalog_sha = catalog_sha256(catalog)
        if not self.connection.execute("SELECT 1 FROM nabt_catalog.snapshots WHERE snapshot_sha=%s", (catalog_sha,)).fetchone():
            grammar.load_catalog(self.connection, catalog, root=ROOT)
        receipt = client.load_inventory(self.connection, root=ROOT)
        self.assertEqual(receipt["counts"], {"sources": 4, "passages": 54, "rules": 9,
                                             "navigation": 0, "reviewed_context_edges": 40})
        result = client.search(self.connection, receipt["inventory_sha"], "المطابقة")
        self.assertTrue(result["candidates"])
        result["candidates"][0]["raw_text"] = "forged database quotation"
        restored = InferenceSearchIndex().rehydrate_database(result)
        self.assertNotIn("forged database quotation", str(restored))
        with self.assertRaises(self.psycopg.errors.UniqueViolation):
            client.load_inventory(self.connection, root=ROOT)
        print("Source-replayed inference import counts:", receipt["counts"])


if __name__ == "__main__":
    unittest.main()
