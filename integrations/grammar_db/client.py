"""Rebuildable retrieval index. Nothing returned by this module is a certificate.

The database is an untrusted proposal store. Rehydrate IDs from a freshly
validated local catalogue before displaying quotations or applying a rule.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"[0-9a-f]{64}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")
INPUT_RECIPE = "nabt.catalog.search-projection.v1"
MAX_QUERY_CHARACTERS = 10000


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def snapshot_digest(catalog: dict) -> str:
    from tools.grammar_catalog.catalog import catalog_sha256
    return catalog_sha256(catalog)


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _positive_integer(value: Any, label: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer in 1..{maximum}")
    return value


def search_projection(text: str) -> str:
    """Search-only normalization. Never changes stored source text or evidence."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    from tools.grammar_catalog.retrieval import tokens
    return " ".join(tokens(text))


def document_id(kind: str, entity_id: str) -> str:
    return kind + ":" + entity_id


def _item_id(item: dict) -> str:
    # Catalogue adapters supply stable typed identity. No positional IDs.
    value = item.get("item_id", item.get("item_key", item.get("id")))
    if not isinstance(value, str) or not value:
        raise ValueError("catalogue item is missing a stable ID")
    return value


def documents(catalog: dict):
    from tools.grammar_catalog.retrieval import iter_documents
    for kind, identifier, raw_search_text, _ in iter_documents(catalog):
        yield (document_id(kind, identifier), kind, identifier, search_projection(raw_search_text))


def initialize(connection) -> None:
    """Install schema once. Uses the caller's transaction, never commits it."""
    with connection.cursor() as cursor:
        cursor.execute(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))


def load_catalog(connection, catalog: dict, root: Path | str) -> str:
    """Replay source validation, then atomically insert a new immutable snapshot.

    Existing snapshots fail with a uniqueness error instead of silently trusting
    or overwriting potentially corrupted database data. No caller hash is trusted.
    A connection transaction context commits only if it owns the transaction;
    callers already inside a transaction retain ownership of the outer commit.
    """
    from tools.grammar_catalog.catalog import validate_catalog
    verified = validate_catalog(catalog, root=Path(root))
    digest = snapshot_digest(verified)
    with connection.transaction():
        _insert_verified_catalog(connection, verified, digest)
    return digest


def _insert_verified_catalog(connection, catalog: dict, digest: str) -> None:
    """Internal import step. Public entry point must call validate_catalog first."""
    from psycopg.types.json import Jsonb
    _sha(digest, "snapshot")
    if catalog.get("authority") != "RETRIEVAL_ONLY":
        raise ValueError("catalogue has the wrong authority")
    with connection.cursor() as cur:
        cur.execute("INSERT INTO nabt_catalog.snapshots VALUES (%s,%s,%s,%s,DEFAULT)",
                    (digest, catalog["schema"], "RETRIEVAL_ONLY", Jsonb(catalog.get("coverage", {}))))
        cur.executemany("INSERT INTO nabt_catalog.sources VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", [
            (digest, r["source_key"], r["source_id"], r["sha256"], r["title"], r.get("local_path"),
             r.get("original_url"), r.get("bytes"), r["content_available"], Jsonb({k: v for k, v in r.items()
                 if k not in {"source_key", "source_id", "sha256", "title", "local_path", "original_url", "bytes", "content_available"}})) for r in catalog["sources"]])
        cur.executemany("INSERT INTO nabt_catalog.passages VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", [
            (digest, r["passage_id"], r["source_key"], r["start"], r["end"], r["sha256"],
             r["raw_text"], Jsonb(r.get("kinds", r.get("kind", []))), Jsonb({k: v for k, v in r.items()
                 if k not in {"passage_id", "source_key", "start", "end", "sha256", "raw_text", "kinds"}})) for r in catalog["passages"]])
        cur.executemany("INSERT INTO nabt_catalog.rules VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", [
            (digest, r["rule_key"], r["registry_id"], r["local_id"], r["title"], r.get("description", ""),
             r.get("keywords", []), r.get("runtime_rule_id"), r.get("source_status", "UNSPECIFIED"),
             Jsonb(r.get("scope", {})), Jsonb({k: v for k, v in r.items()
                 if k not in {"rule_key", "registry_id", "local_id", "title", "description", "keywords", "runtime_rule_id", "source_status", "scope", "source_passage_ids", "theorem_names"}})) for r in catalog["rules"]])
        cur.executemany("INSERT INTO nabt_catalog.attestations VALUES (%s,%s,%s)", [
            (digest, r["rule_key"], passage) for r in catalog["rules"] for passage in r["source_passage_ids"]])
        cur.executemany("INSERT INTO nabt_catalog.theorem_references VALUES (%s,%s,%s)", [
            (digest, r["rule_key"], theorem) for r in catalog["rules"] for theorem in r.get("theorem_names", [])])
        cur.executemany("INSERT INTO nabt_catalog.items VALUES (%s,%s,%s,%s)", [
            (digest, _item_id(r), r.get("kind", "unspecified"), Jsonb(r)) for r in catalog.get("items", [])])
        cur.executemany("INSERT INTO nabt_catalog.documents (snapshot_sha,document_id,kind,entity_id,search_text) VALUES (%s,%s,%s,%s,%s)", [
            (digest, *row) for row in documents(catalog)])


def embedding_metadata(snapshot_sha: str, model_id: str, revision: str, dimensions: int,
                       recipe: str = INPUT_RECIPE) -> dict:
    _sha(snapshot_sha, "snapshot")
    _positive_integer(dimensions, "dimensions", 16000)
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("model_id is required")
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise ValueError("model revision must be an immutable 40-character commit SHA")
    if recipe != INPUT_RECIPE:
        raise ValueError("unsupported embedding input recipe")
    fields = {"snapshot_sha": snapshot_sha, "model_id": model_id,
              "model_revision": revision, "dimensions": dimensions, "input_recipe": recipe}
    return {**fields, "run_id": hashlib.sha256(_json(fields).encode()).hexdigest()}


def validate_vector(vector, dimensions: int):
    """Return unit float32 direction, rejecting bool/nonfinite/zero/overflow."""
    import numpy as np
    _positive_integer(dimensions, "dimensions", 16000)
    if isinstance(vector, np.ndarray):
        if vector.ndim != 1 or vector.dtype.kind not in "fiu":
            raise ValueError("embedding must be a one-dimensional numeric vector")
        values = vector.tolist()
    elif type(vector) in (list, tuple):
        values = vector
    else:
        raise ValueError("embedding must be a list, tuple or numeric ndarray")
    if len(values) != dimensions or any(type(x) not in (int, float) for x in values):
        raise ValueError("embedding dimension or component type mismatch")
    if any(abs(x) > 3.4028234663852886e38 or not math.isfinite(x) for x in values):
        raise ValueError("embedding components must be finite float32 values")
    result = np.asarray(values, dtype=np.float32)
    if not np.any(result):
        raise ValueError("zero embedding has no cosine direction")
    # pgvector cosine uses float32 accumulators. Unit directions avoid overflow
    # and underflow of norm products; raw source/corpus evidence is unaffected.
    norm = float(np.linalg.norm(result.astype(np.float64)))
    return (result.astype(np.float64) / norm).astype(np.float32)


def store_embeddings(connection, metadata: dict, rows: list[tuple[str, Any]]) -> str:
    """Atomically add a run; duplicate runs/documents fail instead of overwrite."""
    from pgvector.psycopg import register_vector
    expected = embedding_metadata(metadata["snapshot_sha"], metadata["model_id"],
                                  metadata["model_revision"], metadata["dimensions"], metadata["input_recipe"])
    if metadata != expected:
        raise ValueError("embedding metadata/run ID mismatch")
    if not rows:
        raise ValueError("an embedding run must contain at least one document")
    checked = [(doc, validate_vector(vec, metadata["dimensions"])) for doc, vec in rows]
    if any(not isinstance(doc, str) or not doc for doc, _ in checked):
        raise ValueError("invalid document ID")
    register_vector(connection)
    with connection.transaction(), connection.cursor() as cur:
        cur.execute("INSERT INTO nabt_catalog.embedding_runs VALUES (%s,%s,%s,%s,%s,%s)", (
            metadata["snapshot_sha"], metadata["run_id"], metadata["model_id"], metadata["model_revision"],
            metadata["dimensions"], metadata["input_recipe"]))
        cur.executemany("INSERT INTO nabt_catalog.embeddings VALUES (%s,%s,%s,%s,%s)", [
            (metadata["snapshot_sha"], metadata["run_id"], doc, metadata["dimensions"], vec) for doc, vec in checked])
    return metadata["run_id"]


def search(connection, snapshot_sha: str, query: str, embedding=None,
           embedding_run: dict | None = None, k: int = 10) -> dict:
    """Exact lexical/cosine streams fused by RRF, returning untrusted typed IDs.

    The same embedding metadata that created document vectors must accompany a
    query vector. Scores are ranks/similarities, never calibrated probabilities.
    No predicted chapter/keyword is accepted as a candidate filter.
    """
    _sha(snapshot_sha, "snapshot")
    _positive_integer(k, "k", 1000)
    if not isinstance(query, str) or len(query) > MAX_QUERY_CHARACTERS:
        raise ValueError("query must be a string of at most 10000 characters")
    if (embedding is None) != (embedding_run is None):
        raise ValueError("query embedding and its complete metadata are required together")
    tokens = list(dict.fromkeys(search_projection(query).split()))
    if len(tokens) > 64:
        raise ValueError("query exceeds the 64-token retrieval limit")
    proposed: dict[str, dict] = {}
    with connection.cursor() as cur:
        cur.execute("SELECT 1 FROM nabt_catalog.snapshots WHERE snapshot_sha=%s", (snapshot_sha,))
        if cur.fetchone() is None:
            raise ValueError("snapshot is not installed")
        if tokens:
            # Token extraction excludes tsquery syntax; values remain parameters.
            cur.execute("""
                SELECT document_id, kind, entity_id,
                       ts_rank_cd(search_vector, to_tsquery('simple', %s)) AS score
                FROM nabt_catalog.documents
                WHERE snapshot_sha=%s AND search_vector @@ to_tsquery('simple', %s)
                ORDER BY score DESC, document_id
            """, (" | ".join(tokens), snapshot_sha, " | ".join(tokens)))
            for rank, (doc, kind, entity, score) in enumerate(cur.fetchall(), 1):
                proposed[doc] = {"kind": kind, "id": entity, "lexical_score": float(score),
                                 "lexical_rank": rank, "rrf_score": 1 / (60 + rank)}
        if embedding_run is not None:
            expected = embedding_metadata(snapshot_sha, embedding_run["model_id"],
                embedding_run["model_revision"], embedding_run["dimensions"], embedding_run["input_recipe"])
            if expected != embedding_run:
                raise ValueError("query embedding metadata does not match snapshot/run")
            cur.execute("""SELECT model_id,model_revision,dimensions,input_recipe
                FROM nabt_catalog.embedding_runs WHERE snapshot_sha=%s AND run_id=%s""",
                (snapshot_sha, embedding_run["run_id"]))
            run = cur.fetchone()
            if run is None or tuple(run) != tuple(expected[key] for key in (
                    "model_id", "model_revision", "dimensions", "input_recipe")):
                raise ValueError("embedding run is not installed or differs from metadata")
            from pgvector.psycopg import register_vector
            register_vector(connection)
            vector = validate_vector(embedding, expected["dimensions"])
            # Materialization enforces an exact distance scan even if an operator
            # adds an ANN index later. No top-k filtering occurs before fusion.
            cur.execute("""WITH corpus AS MATERIALIZED (
                    SELECT document_id,embedding FROM nabt_catalog.embeddings
                    WHERE snapshot_sha=%s AND run_id=%s
                ) SELECT c.document_id,d.kind,d.entity_id,(c.embedding <=> %s) AS distance
                FROM corpus c JOIN nabt_catalog.documents d
                    ON d.document_id=c.document_id AND d.snapshot_sha=%s
                ORDER BY distance,c.document_id""",
                (snapshot_sha, expected["run_id"], vector, snapshot_sha))
            for rank, (doc, kind, entity, distance) in enumerate(cur.fetchall(), 1):
                if not math.isfinite(distance):
                    raise ValueError("database returned a nonfinite cosine distance")
                row = proposed.setdefault(doc, {"kind": kind, "id": entity, "rrf_score": 0.0})
                row.update(vector_score=1.0-float(distance), vector_rank=rank)
                row["rrf_score"] += 1 / (60 + rank)
    ranked = sorted(proposed.items(), key=lambda pair: (-pair[1]["rrf_score"], pair[0]))
    candidates = [{**row, "rank": rank} for rank, (_, row) in enumerate(ranked[:k], 1)]
    return {"schema": "nabt.database-proposals.v1", "snapshot_sha": snapshot_sha,
            "authority": "RETRIEVAL_ONLY", "status": "PROPOSALS" if candidates else "NO_CANDIDATES",
            "candidates": candidates, "exhaustive_language_claim": False,
            "candidate_count_before_limit": len(ranked), "limit": k,
            "score_semantics": "reciprocal rank fusion; cosine similarity is not probability",
            "distance_mode": "EXACT" if embedding is not None else "LEXICAL_ONLY"}
