"""Real PostgreSQL + pgvector tests on a fresh, disposable test database.

Set NABT_TEST_DATABASE_URL. Never point this suite at a production database.
The suite creates its own schema and refuses to replace an existing schema.
"""
from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import unittest

from integrations.grammar_db import client

DSN = os.environ.get("NABT_TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[3]


def fixture() -> dict:
    raw = "الأمر مبني\nالجازم يسكن\n"
    first = "الأمر مبني\n"
    data = raw.encode()
    whole = hashlib.sha256(data).hexdigest()
    sources = [{"source_key": "fixture:" + whole, "source_id": "fixture", "sha256": whole,
                "title": "Synthetic database fixture; not a linguistic source", "bytes": len(data),
                "content_available": True, "local_path": None, "original_url": None}]
    passages = []
    for name, start, end in (("p1", 0, len(first.encode())), ("p2", len(first.encode()), len(data))):
        part = data[start:end]
        passages.append({"passage_id": name, "source_key": sources[0]["source_key"],
                         "start": start, "end": end, "sha256": hashlib.sha256(part).hexdigest(),
                         "raw_text": part.decode(), "kind": ["test_fixture"]})
    rules = [{"rule_key": "fixture::" + name, "registry_id": "fixture", "local_id": name,
              "title": title, "description": "", "keywords": [title], "source_passage_ids": [passage],
              "theorem_names": [], "runtime_rule_id": None, "source_status": "SYNTHETIC", "scope": {}}
             for name, title, passage in (("r1", "الأمر", "p1"), ("r2", "الأمر", "p1"), ("r3", "الجازم", "p2"))]
    return {"schema": "nabt.database-test-fixture.v1", "authority": "RETRIEVAL_ONLY",
            "sources": sources, "passages": passages, "rules": rules, "items": [], "coverage": {}}


@unittest.skipUnless(DSN, "NABT_TEST_DATABASE_URL is not set; PostgreSQL integration not executed")
class PostgreSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        cls.psycopg = psycopg
        cls.connection = psycopg.connect(DSN, autocommit=True)
        cls.addClassCleanup(cls.connection.close)
        client.initialize(cls.connection)
        cls.synthetic = fixture()
        cls.sha = "1" * 64
        with cls.connection.transaction():
            # Deliberately synthetic SQL fixture; public loader tested separately.
            client._insert_verified_catalog(cls.connection, cls.synthetic, cls.sha)
        cls.metadata = client.embedding_metadata(cls.sha, "test/model", "a" * 40, 3)
        client.store_embeddings(cls.connection, cls.metadata, [
            ("rule:fixture::r1", [1, 0, 0]), ("rule:fixture::r2", [0, 1, 0]),
            ("rule:fixture::r3", [-1, 0, 0])])

    def test_server_versions(self):
        row = self.connection.execute("SELECT current_setting('server_version'),extversion FROM pg_extension WHERE extname='vector'").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "0.8.7")
        print("PostgreSQL / pgvector tested versions:", row)

    def test_many_to_many_attestation_and_raw_text_are_preserved(self):
        rows = self.connection.execute("SELECT rule_key FROM nabt_catalog.attestations WHERE snapshot_sha=%s AND passage_id='p1' ORDER BY rule_key", (self.sha,)).fetchall()
        self.assertEqual(rows, [("fixture::r1",), ("fixture::r2",)])
        raw = self.connection.execute("SELECT raw_text FROM nabt_catalog.passages WHERE snapshot_sha=%s AND passage_id='p1'", (self.sha,)).fetchone()[0]
        self.assertEqual(raw.encode(), "الأمر مبني\n".encode())

    def test_lexical_search_returns_multiple_typed_proposals_and_no_quotes(self):
        result = client.search(self.connection, self.sha, "الأمر", k=10)
        self.assertEqual(result["authority"], "RETRIEVAL_ONLY")
        self.assertFalse(result["exhaustive_language_claim"])
        ids = {row["id"] for row in result["candidates"]}
        self.assertTrue({"fixture::r1", "fixture::r2", "p1"} <= ids)
        self.assertTrue(all("raw_text" not in row and "confidence_score" not in row for row in result["candidates"]))

    def test_exact_cosine_and_rrf_keep_negative_scores_as_scores(self):
        result = client.search(self.connection, self.sha, "", embedding=[1, 0, 0], embedding_run=self.metadata, k=10)
        self.assertEqual(result["distance_mode"], "EXACT")
        self.assertEqual([row["id"] for row in result["candidates"]], ["fixture::r1", "fixture::r2", "fixture::r3"])
        self.assertEqual([row["vector_score"] for row in result["candidates"]], [1.0, 0.0, -1.0])
        fused = client.search(self.connection, self.sha, "الجازم", embedding=[1, 0, 0], embedding_run=self.metadata, k=10)
        self.assertEqual(fused["candidates"][0]["id"], "fixture::r3")

    def test_k_only_limits_display_and_bad_numeric_limits_rejected(self):
        limited = client.search(self.connection, self.sha, "الأمر", k=1)
        self.assertEqual(len(limited["candidates"]), 1)
        self.assertGreater(limited["candidate_count_before_limit"], 1)
        for value in (True, 0, -1, 1.0, 1001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                client.search(self.connection, self.sha, "الأمر", k=value)

    def test_malicious_query_is_data_and_empty_results_are_not_rejection(self):
        result = client.search(self.connection, self.sha, "'; DROP TABLE nabt_catalog.rules; --")
        self.assertEqual(result["status"], "NO_CANDIDATES")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM nabt_catalog.rules WHERE snapshot_sha=%s", (self.sha,)).fetchone()[0], 3)
        with self.assertRaises(ValueError):
            client.search(self.connection, "2" * 64, "الأمر")

    def test_wrong_embedding_run_or_dimension_rejected(self):
        with self.assertRaises(ValueError):
            client.search(self.connection, self.sha, "", embedding=[1, 2], embedding_run=self.metadata)
        wrong = dict(self.metadata, model_revision="b" * 40)
        with self.assertRaises(ValueError):
            client.search(self.connection, self.sha, "", embedding=[1, 0, 0], embedding_run=wrong)
        with self.assertRaises(ValueError):
            client.search(self.connection, self.sha, "", embedding=[1, 0, 0])
        wrong_snapshot = dict(self.metadata, snapshot_sha="2" * 64)
        with self.assertRaises(ValueError):
            client.search(self.connection, self.sha, "", embedding=[1, 0, 0], embedding_run=wrong_snapshot)

    def test_sql_constraints_reject_zero_nan_dimensions_and_orphans(self):
        cases = [
            (self.metadata["run_id"], "passage:p1", 3, "[0,0,0]"),
            (self.metadata["run_id"], "passage:p1", 3, "[NaN,1,0]"),
            (self.metadata["run_id"], "passage:p1", 3, "[1,2]"),
            (self.metadata["run_id"], "passage:p1", 2, "[1,2]"),
            (self.metadata["run_id"], "unknown", 3, "[1,2,3]"),
            ("f" * 64, "passage:p1", 3, "[1,2,3]"),
        ]
        for run, doc, dims, vector in cases:
            with self.subTest(doc=doc, vector=vector), self.assertRaises(self.psycopg.Error):
                with self.connection.transaction():
                    self.connection.execute("INSERT INTO nabt_catalog.embeddings VALUES (%s,%s,%s,%s,%s::vector)", (self.sha, run, doc, dims, vector))

    def test_snapshot_rows_are_immutable_under_normal_dml(self):
        for query in ("UPDATE nabt_catalog.rules SET title='invented' WHERE snapshot_sha=%s",
                      "DELETE FROM nabt_catalog.snapshots WHERE snapshot_sha=%s"):
            with self.subTest(query=query), self.assertRaises(self.psycopg.Error):
                with self.connection.transaction():
                    self.connection.execute(query, (self.sha,))
        with self.assertRaises(self.psycopg.Error):
            with self.connection.transaction():
                self.connection.execute("TRUNCATE nabt_catalog.embeddings")

    def test_atomic_import_does_not_leave_partial_snapshot(self):
        broken = copy.deepcopy(self.synthetic)
        broken["rules"][0]["source_passage_ids"] = ["nonexistent"]
        digest = "3" * 64
        with self.assertRaises(self.psycopg.Error):
            with self.connection.transaction():
                client._insert_verified_catalog(self.connection, broken, digest)
        self.assertIsNone(self.connection.execute("SELECT 1 FROM nabt_catalog.snapshots WHERE snapshot_sha=%s", (digest,)).fetchone())

    def test_public_loader_replays_installed_source_catalogue(self):
        from tools.grammar_catalog.catalog import build_catalog
        catalog = build_catalog(root=ROOT)
        digest = client.load_catalog(self.connection, catalog, root=ROOT)
        counts = self.connection.execute("""SELECT
            (SELECT count(*) FROM nabt_catalog.rules WHERE snapshot_sha=%s),
            (SELECT count(*) FROM nabt_catalog.passages WHERE snapshot_sha=%s),
            (SELECT count(*) FROM nabt_catalog.sources WHERE snapshot_sha=%s)""", (digest, digest, digest)).fetchone()
        self.assertEqual(counts, (len(catalog["rules"]), len(catalog["passages"]), len(catalog["sources"])))
        print("Source-validated catalogue import counts (rules, passages, sources):", counts)
        result = client.search(self.connection, digest, "مبتدأ زيد وعاذر خبر", k=20)
        self.assertTrue(result["candidates"])
        with self.assertRaises(self.psycopg.errors.UniqueViolation):
            client.load_catalog(self.connection, catalog, root=ROOT)
        catalog["authority"] = "PROOF"
        with self.assertRaises(ValueError):
            client.load_catalog(self.connection, catalog, root=ROOT)


if __name__ == "__main__":
    unittest.main()
