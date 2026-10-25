"""Reuse the catalogue ranker for locally replayed usuli policy proposals.

Search never supplies a premise, chooses an interpretation, or establishes a
world fact. Typed IDs are restored from pinned bytes after database retrieval.
"""
from collections import Counter
from hashlib import sha256
import json

from tools.grammar_catalog.retrieval import SearchIndex, RetrievalError, tokens
from .inventory import ROOT, build_inventory

INPUT_RECIPE = "nabt.inference.search-projection.v1"


def inventory_sha256(inventory):
    return sha256(json.dumps(inventory, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def iter_documents(inventory):
    """Shared raw projection for local ranker and optional PostgreSQL storage."""
    passages = {p["passage_id"]: p for p in inventory["passages"]}
    for rule in inventory["rules"]:
        pids = list(dict.fromkeys(rule["source_passage_ids"] + rule.get("reviewed_context_passage_ids", [])))
        body = " ".join(passages[p]["raw_text"] for p in pids)
        text = " ".join([rule["title"], rule["claim"],
                         " ".join(rule["required_evidence"]), body])
        yield "rule", rule["rule_id"], text, rule
    for passage in passages.values():
        yield "passage", passage["passage_id"], passage["raw_text"], passage


class InferenceSearchIndex(SearchIndex):
    """Source replay precedes indexing; no caller catalogue is accepted."""

    def __init__(self, *, root=ROOT):
        self._catalog = build_inventory(root)
        self.catalog_sha256 = inventory_sha256(self._catalog)
        self._docs = {}
        for kind, identifier, text, row in iter_documents(self._catalog):
            self._add(kind, identifier, text, row)
        self._tf = {key: Counter(tokens(doc["search_text"]))
                    for key, doc in self._docs.items()}

    def search(self, query, limit=10, hints=None, vector_scores=None, kind=None):
        if vector_scores is not None and (type(vector_scores) is not dict or
                vector_scores.get("input_recipe") != INPUT_RECIPE):
            raise RetrievalError("Inference embedding input recipe mismatch")
        result = super().search(query, limit, hints, vector_scores, kind)
        return {**result, "schema": "nabt.inference-retrieval.v1",
                "inventory_sha": self.catalog_sha256,
                "occurrence_classification_proved": False,
                "world_truth_established": False}

    def rehydrate_database(self, proposals):
        if (type(proposals) is not dict or
                proposals.get("schema") != "nabt.inference-database-proposals.v1" or
                proposals.get("inventory_sha") != self.catalog_sha256):
            raise RetrievalError("Inference database schema/snapshot mismatch")
        result = super().rehydrate_database({
            "schema": "nabt.database-proposals.v1",
            "snapshot_sha": self.catalog_sha256,
            "candidates": proposals.get("candidates"),
        })
        return {**result, "schema": "nabt.rehydrated-inference-proposals.v1",
                "inventory_sha": self.catalog_sha256,
                "occurrence_classification_proved": False,
                "world_truth_established": False}


def search(query, *, limit=10, hints=None, vector_scores=None, kind=None, root=ROOT):
    return InferenceSearchIndex(root=root).search(query, limit, hints, vector_scores, kind)
