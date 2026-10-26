"""Optional provenance storage with an untrusted, ID-only search boundary.

The public importer obtains both inventories from local source replay. Stored
rule text, theorem names, observations and scores cannot authorize inference.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from integrations.grammar_db import client as grammar_db

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "nabt.inference-database.v1"
INPUT_RECIPE = "nabt.inference.search-projection.v1"


import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _text(value, label: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be a nonempty string")
    return value


def inventory_digest(inventory: dict) -> str:
    from tools.mantuq_inference.retrieval import inventory_sha256
    return inventory_sha256(inventory)


def initialize(connection) -> None:
    """Install once, in the caller's transaction; requires grammar_db schema."""
    with connection.cursor() as cursor:
        cursor.execute(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))


def project_inventory(inventory: dict, catalog: dict) -> dict:
    """Pure projection, not an authority boundary. Production uses load_inventory.

    Exact source bytes, authored profile names and rule payloads remain distinct.
    Unsupported structured semantics are retained as descriptive metadata only.
    """
    sources, passages, rules = inventory["sources"], inventory["passages"], inventory["rules"]
    source_map = {r["source_id"]: r for r in sources}
    passage_map = {r["passage_id"]: r for r in passages}
    if len(source_map) != len(sources) or len(passage_map) != len(passages):
        raise ValueError("repeated source or passage identity")
    if len({r["rule_id"] for r in rules}) != len(rules):
        raise ValueError("repeated rule identity")
    for row in sources:
        _text(row["source_id"], "source_id")
        grammar_db._sha(row["sha256"], "source digest")
        _text(row["local_path"], "local_path")
        if type(row["bytes"]) is not int or row["bytes"] < 0:
            raise ValueError("source bytes must be a nonnegative integer")
    for row in passages:
        _text(row["passage_id"], "passage_id")
        if row["source_id"] not in source_map:
            raise ValueError("unknown passage source")
        start, end = row["start"], row["end"]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= source_map[row["source_id"]]["bytes"]:
            raise ValueError("invalid source byte range")
        raw = _text(row["raw_text"], "raw_text").encode()
        if len(raw) != end - start or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("passage digest or byte count differs")
    from tools.mantuq_inference.retrieval import iter_documents
    try:
        shared_texts = {identifier: text for kind, identifier, text, _ in iter_documents(inventory) if kind == "rule"}
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid local search projection references") from exc
    profiles = set()
    projected_rules = []
    for rule in rules:
        rule_id = _text(rule["rule_id"], "rule_id")
        profile = _text(rule["profile"], "profile")
        profiles.add(profile)
        pids = rule["source_passage_ids"]
        context_pids = rule.get("reviewed_context_passage_ids", [])
        names = rule["theorem_names"]
        if type(pids) is not list or len(pids) != len(set(pids)) or any(p not in passage_map for p in pids):
            raise ValueError("unknown or repeated source passage")
        if (type(context_pids) is not list or len(context_pids) != len(set(context_pids)) or
                any(p not in passage_map for p in context_pids)):
            raise ValueError("unknown or repeated reviewed source context")
        if type(names) is not list or len(names) != len(set(names)) or any(type(n) is not str or not n for n in names):
            raise ValueError("invalid theorem reference")
        text = shared_texts[rule_id]
        projected_rules.append({"rule_id": rule_id, "profile": profile,
                                "status": _text(rule["implementation_status"], "status"),
                                "search_text": grammar_db.search_projection(text), "payload": rule})
    # Link only exact editions and contained byte spans. A similar word, title,
    # theorem name or translated concept never creates this provenance edge.
    catalog_sources = {s["source_key"]: s for s in catalog["sources"]}
    navigation = set()
    for rule in rules:
        for pid in rule["source_passage_ids"]:
            passage = passage_map[pid]
            source = source_map[passage["source_id"]]
            for gp in catalog["passages"]:
                gs = catalog_sources[gp["source_key"]]
                if (gs["sha256"] == source["sha256"] and gp["start"] <= passage["start"]
                        and passage["end"] <= gp["end"]):
                    navigation.add((rule["rule_id"], "passage:" + gp["passage_id"]))
    return {"sources": sources, "passages": passages, "rules": projected_rules,
            "profiles": sorted(profiles), "navigation": sorted(navigation)}


def load_inventory(connection, root: Path = ROOT) -> dict:
    """Rebuild installed source inventories, then import one atomic snapshot.

    No caller-supplied inventory, digest, proof flag or observation is accepted.
    The corresponding grammar catalogue must already be installed. A duplicate
    snapshot fails instead of silently trusting old database rows.
    """
    foundation.require_foundation('integrations.inference_db.client.load_inventory')
    from tools.mantuq_inference import build_inventory
    from tools.grammar_catalog.catalog import build_catalog, catalog_sha256
    root = Path(root).resolve()
    inventory, catalog = build_inventory(root=root), build_catalog(root=root)
    catalog_sha = catalog_sha256(catalog)
    digest = inventory_digest(inventory)
    projection = project_inventory(inventory, catalog)
    with connection.transaction():
        _insert_projection(connection, projection, digest, catalog_sha, inventory["schema"])
    return {"schema": SCHEMA, "inventory_sha": digest, "catalog_sha": catalog_sha,
            "authority": "PROVENANCE_ONLY",
            "counts": {**{key: len(projection[key]) for key in ("sources", "passages", "rules", "navigation")},
                       "reviewed_context_edges": sum(len(r["payload"].get("reviewed_context_passage_ids", []))
                                                     for r in projection["rules"])}}


def _insert_projection(connection, projection: dict, digest: str, catalog_sha: str,
                       inventory_schema: str) -> None:
    """Internal SQL projection. Only public source-replaying import is evidence."""
    from psycopg.types.json import Jsonb
    grammar_db._sha(digest, "inventory")
    grammar_db._sha(catalog_sha, "grammar catalogue")
    with connection.cursor() as cur:
        cur.execute("INSERT INTO nabt_inference.snapshots VALUES (%s,%s,'PROVENANCE_ONLY',%s,DEFAULT)",
                    (digest, inventory_schema, Jsonb({"schema": SCHEMA,
                     "empirical_truth_established": False, "whole_arabic_complete": False})))
        cur.execute("INSERT INTO nabt_inference.grammar_bindings VALUES (%s,%s)", (digest, catalog_sha))
        cur.executemany("INSERT INTO nabt_inference.profiles VALUES (%s,%s,%s)",
                        [(digest, p, "Authored interpretation profile; no consensus claim") for p in projection["profiles"]])
        cur.executemany("INSERT INTO nabt_inference.sources VALUES (%s,%s,%s,%s,%s,%s)",
                        [(digest, r["source_id"], r["sha256"], r["bytes"], r["local_path"], Jsonb(r)) for r in projection["sources"]])
        cur.executemany("INSERT INTO nabt_inference.passages VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        [(digest, r["passage_id"], r["source_id"], r["start"], r["end"], r["sha256"], r["raw_text"], Jsonb(r)) for r in projection["passages"]])
        cur.executemany("INSERT INTO nabt_inference.rules (inventory_sha,rule_id,profile_id,source_status,search_text,payload) VALUES (%s,%s,%s,%s,%s,%s)",
                        [(digest, r["rule_id"], r["profile"], r["status"], r["search_text"], Jsonb(r["payload"])) for r in projection["rules"]])
        cur.executemany("INSERT INTO nabt_inference.rule_passages VALUES (%s,%s,%s)",
                        [(digest, r["rule_id"], p) for r in projection["rules"] for p in r["payload"]["source_passage_ids"]])
        cur.executemany("""INSERT INTO nabt_inference.reviewed_contexts
            VALUES (%s,%s,%s,'REVIEWED_CONTEXT_CANDIDATE_BASIS',true,false,false)""",
                        [(digest, r["rule_id"], p) for r in projection["rules"]
                         for p in r["payload"].get("reviewed_context_passage_ids", [])])
        cur.executemany("INSERT INTO nabt_inference.theorem_references VALUES (%s,%s,%s,'AUTHORED_REFERENCE')",
                        [(digest, r["rule_id"], n) for r in projection["rules"] for n in r["payload"]["theorem_names"]])
        cur.executemany("INSERT INTO nabt_inference.grammar_navigation VALUES (%s,%s,%s,%s)",
                        [(digest, rule, catalog_sha, doc) for rule, doc in projection["navigation"]])


def embedding_metadata(inventory_sha: str, model_id: str, revision: str,
                       dimensions: int, recipe: str = INPUT_RECIPE) -> dict:
    grammar_db._sha(inventory_sha, "inventory")
    grammar_db._positive_integer(dimensions, "dimensions", 16000)
    if not _text(model_id, "model_id").strip():
        raise ValueError("model_id cannot be blank")
    if type(revision) is not str or not grammar_db.REVISION.fullmatch(revision):
        raise ValueError("model revision must be an immutable 40-character commit SHA")
    if recipe != INPUT_RECIPE:
        raise ValueError("unsupported inference projection recipe")
    fields = {"inventory_sha": inventory_sha, "model_id": model_id,
              "model_revision": revision, "dimensions": dimensions, "input_recipe": recipe}
    return {**fields, "run_id": hashlib.sha256(_json(fields).encode()).hexdigest()}


def _check_metadata(metadata: dict) -> dict:
    if type(metadata) is not dict:
        raise ValueError("embedding metadata must be an object")
    try:
        expected = embedding_metadata(metadata["inventory_sha"], metadata["model_id"],
            metadata["model_revision"], metadata["dimensions"], metadata["input_recipe"])
    except KeyError as exc:
        raise ValueError("incomplete embedding metadata") from exc
    if _json(expected) != _json(metadata):
        raise ValueError("embedding run metadata differs")
    return expected


def store_embeddings(connection, metadata: dict, rows: list[tuple[str, object]]) -> str:
    """Add one model-pinned run atomically; this measures no semantic quality."""
    from pgvector.psycopg import register_vector
    checked_metadata = _check_metadata(metadata)
    if type(rows) is not list or not rows:
        raise ValueError("an embedding run needs at least one rule vector")
    checked_rows = [(_text(rid, "rule_id"), grammar_db.validate_vector(vector, metadata["dimensions"]))
                    for rid, vector in rows]
    register_vector(connection)
    with connection.transaction(), connection.cursor() as cur:
        cur.execute("INSERT INTO nabt_inference.embedding_runs VALUES (%s,%s,%s,%s,%s,%s)",
                    tuple(checked_metadata[key] for key in ("inventory_sha", "run_id", "model_id",
                                                            "model_revision", "dimensions", "input_recipe")))
        cur.executemany("INSERT INTO nabt_inference.embeddings VALUES (%s,%s,%s,%s,%s)",
                        [(metadata["inventory_sha"], metadata["run_id"], rid, metadata["dimensions"], vector)
                         for rid, vector in checked_rows])
    return metadata["run_id"]


def search(connection, inventory_sha: str, query: str, *, k: int = 10,
           embedding=None, embedding_run: dict | None = None) -> dict:
    """Fuse complete lexical/vector rankings, then return untrusted rule IDs.

    Exact materialized distance scans preserve recall within the stored vector
    inventory. Neither no match nor top-k is an inference rejection. Missing
    embeddings and unmeasured semantic relevance remain explicit.
    """
    foundation.require_foundation('integrations.inference_db.client.search')
    grammar_db._sha(inventory_sha, "inventory")
    grammar_db._positive_integer(k, "k", 1000)
    if type(query) is not str or len(query) > grammar_db.MAX_QUERY_CHARACTERS:
        raise ValueError("invalid query string")
    terms = list(dict.fromkeys(grammar_db.search_projection(query).split()))
    if len(terms) > 64:
        raise ValueError("query exceeds the 64-token retrieval limit")
    if (embedding is None) != (embedding_run is None):
        raise ValueError("query embedding and pinned metadata are required together")
    if embedding_run is not None:
        _check_metadata(embedding_run)
        if embedding_run["inventory_sha"] != inventory_sha:
            raise ValueError("embedding run belongs to a different inference inventory")
    with connection.cursor() as cur:
        cur.execute("SELECT inventory_sha FROM nabt_inference.snapshots WHERE inventory_sha=%s", (inventory_sha,))
        row = cur.fetchone()
        if row is None:
            raise ValueError("inference inventory is not installed")
        candidates = {}
        if terms:
            term_query = " | ".join(terms)
            cur.execute("""SELECT rule_id,ts_rank_cd(search_vector,to_tsquery('simple',%s)) AS score
                FROM nabt_inference.rules WHERE inventory_sha=%s
                    AND search_vector @@ to_tsquery('simple',%s) ORDER BY score DESC,rule_id""",
                        (term_query, inventory_sha, term_query))
            for rank, (rid, score) in enumerate(cur.fetchall(), 1):
                candidates[rid] = {"id": rid, "kind": "rule", "lexical_rank": rank,
                                   "lexical_score": float(score), "rrf_score": 1 / (60 + rank)}
        vector_count = 0
        if embedding_run is not None:
            cur.execute("""SELECT model_id,model_revision,dimensions,input_recipe
                FROM nabt_inference.embedding_runs WHERE inventory_sha=%s AND run_id=%s""",
                        (inventory_sha, embedding_run["run_id"]))
            installed = cur.fetchone()
            if installed is None or tuple(installed) != tuple(embedding_run[key] for key in
                    ("model_id", "model_revision", "dimensions", "input_recipe")):
                raise ValueError("embedding run is not installed or metadata differs")
            from pgvector.psycopg import register_vector
            register_vector(connection)
            vector = grammar_db.validate_vector(embedding, embedding_run["dimensions"])
            cur.execute("""WITH vectors AS MATERIALIZED (
                    SELECT rule_id,embedding FROM nabt_inference.embeddings
                    WHERE inventory_sha=%s AND run_id=%s
                ) SELECT rule_id,(embedding <=> %s) AS distance FROM vectors
                ORDER BY distance,rule_id""", (inventory_sha, embedding_run["run_id"], vector))
            vector_rows = cur.fetchall()
            vector_count = len(vector_rows)
            for rank, (rid, distance) in enumerate(vector_rows, 1):
                if not math.isfinite(distance):
                    raise ValueError("nonfinite cosine distance returned by database")
                candidate = candidates.setdefault(rid, {"id": rid, "kind": "rule", "rrf_score": 0.0})
                candidate.update(vector_rank=rank, vector_score=1.0-float(distance))
                candidate["rrf_score"] += 1 / (60 + rank)
        cur.execute("SELECT count(*) FROM nabt_inference.rules WHERE inventory_sha=%s", (inventory_sha,))
        rule_count = cur.fetchone()[0]
    ranked = sorted(candidates.values(), key=lambda r: (-r["rrf_score"], r["id"]))
    if any(not math.isfinite(r["rrf_score"]) for r in ranked):
        raise ValueError("nonfinite database score")
    return {"schema": "nabt.inference-database-proposals.v1", "inventory_sha": inventory_sha,
            "authority": "RETRIEVAL_ONLY",
            "status": "PROPOSALS" if ranked else "NO_CANDIDATES",
            "candidates": [{**r, "rank": i} for i, r in enumerate(ranked[:k], 1)],
            "candidate_count_before_limit": len(ranked), "limit": k,
            "stored_rule_count": rule_count, "stored_vector_count": vector_count,
            "vector_inventory_complete": embedding_run is not None and vector_count == rule_count,
            "vector_mode": "EXACT" if embedding_run is not None else "LEXICAL_ONLY",
            "new_inference_text_embeddings_measured": False,
            "scores_are_probabilities": False, "exhaustive_language_claim": False}
