"""Deterministic proposal search over a verified, source-linked catalogue.

BM25 (k1=1.2, b=.75) and optional cosine rankings are fused by reciprocal rank
(constant 60). Scores order proposals; they are neither calibrated probabilities
nor evidence that a grammatical analysis is licensed. Normalization applies only
to the search projection. Quotations are always restored from verified bytes.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import math
from pathlib import Path
import re
import unicodedata

from .catalog import build_catalog, catalog_sha256, validate_catalog

ROOT = Path(__file__).resolve().parents[2]
KINDS = {"rule", "passage", "item"}
MAX_QUERY_BYTES = 16384


import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

class RetrievalError(ValueError):
    """Malformed proposal input; not a rejection of Arabic."""


def tokens(text):
    """Search-only projection: marks/tatweel removed, alif variants unified."""
    text = "".join(c for c in text if not unicodedata.category(c).startswith("M") and c != "ـ")
    text = text.translate(str.maketrans("أإآٱ", "اااا")).casefold()
    return re.findall(r"[^\W_]+", text, re.UNICODE)


def _text(value, label, *, maximum=MAX_QUERY_BYTES):
    if type(value) is not str:
        raise RetrievalError(f"{label} must be a string")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise RetrievalError(f"{label} must be valid UTF-8") from exc
    if size > maximum:
        raise RetrievalError(f"{label} exceeds its byte budget")
    return value


def _limit(value):
    if type(value) is not int or not 1 <= value <= 1000:
        raise RetrievalError("limit must be an integer in 1..1000")


def _finite_score(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def iter_documents(catalog):
    """Common document projection for local and optional database retrieval.

    Input must be source-validated by the caller. This function confers no trust.
    """
    passages = {p["passage_id"]: p for p in catalog["passages"]}
    for rule in catalog["rules"]:
        body = " ".join(passages[p]["raw_text"] for p in rule["source_passage_ids"])
        text = " ".join([rule["title"], rule["description"], " ".join(rule["keywords"]), body])
        yield "rule", rule["rule_key"], text, rule
    for passage in passages.values():
        yield "passage", passage["passage_id"], passage["raw_text"], passage
    for item in catalog.get("items", []):
        identifier = item.get("item_id", item.get("item_key"))
        if not identifier:
            raise RetrievalError("Catalogue item has no stable identity")
        body = " ".join(str(item.get(k, "")) for k in ("title", "description", "raw_text", "text"))
        yield "item", identifier, body, item


class SearchIndex:
    """Build once from source replay; retain no caller-owned mutable state."""

    def __init__(self, catalog=None, *, root=ROOT):
        self._catalog = (build_catalog(root) if catalog is None else
                         validate_catalog(catalog, root))
        self.catalog_sha256 = catalog_sha256(self._catalog)
        self._docs = {}
        for kind, identifier, text, row in iter_documents(self._catalog):
            self._add(kind, identifier, text, row)
        self._tf = {key: Counter(tokens(doc["search_text"])) for key, doc in self._docs.items()}

    def _add(self, kind, identifier, text, row):
        key = (kind, identifier)
        if key in self._docs:
            raise RetrievalError("Duplicate typed catalogue identity")
        self._docs[key] = {"search_text": text, "record": row}

    def rehydrate(self, kind, identifier):
        """Database/LLM text is ignored: only a known typed ID is accepted."""
        foundation.require_foundation('tools.grammar_catalog.retrieval.searchindex.rehydrate')
        if type(kind) is not str or type(identifier) is not str:
            raise RetrievalError("Expected a typed catalogue identity")
        try:
            row = self._docs[kind, identifier]["record"]
        except KeyError as exc:
            raise RetrievalError("Unknown catalogue identity") from exc
        return deepcopy(row)

    def rehydrate_database(self, proposals):
        """Discard all DB display/authority fields and restore local records."""
        foundation.require_foundation('tools.grammar_catalog.retrieval.searchindex.rehydrate_database')
        if (type(proposals) is not dict or proposals.get("schema") != "nabt.database-proposals.v1" or
                proposals.get("snapshot_sha") != self.catalog_sha256 or
                type(proposals.get("candidates")) is not list or len(proposals["candidates"]) > 1000):
            raise RetrievalError("Database proposal snapshot/schema mismatch")
        result, seen = [], set()
        for rank, row in enumerate(proposals["candidates"], 1):
            if type(row) is not dict:
                raise RetrievalError("Malformed database proposal")
            kind, identifier = row.get("kind"), row.get("id")
            record = self.rehydrate(kind, identifier)
            key = (kind, identifier)
            if key in seen:
                raise RetrievalError("Duplicate database proposal")
            seen.add(key)
            scores = {}
            for field in ("lexical_score", "vector_score", "rrf_score"):
                if field in row:
                    value = row[field]
                    if not _finite_score(value):
                        raise RetrievalError("Malformed database score")
                    scores[field] = value
            result.append({"kind": kind, "id": identifier, "rank": rank,
                           "proposal_scores": scores, "record": record})
        return {"schema": "nabt.rehydrated-database-proposals.v1", "catalog_sha256": self.catalog_sha256,
                "candidates": result, "authority": "RETRIEVAL_ONLY", "scores_are_probabilities": False,
                "exhaustive_language_claim": False, "premises_established_from_free_text": False}

    def _vectors(self, proposal):
        if proposal is None:
            return {}
        fields = {"schema", "catalog_sha256", "model_id", "revision", "dimensions", "input_recipe", "scores"}
        if type(proposal) is not dict or set(proposal) != fields:
            raise RetrievalError("Expected a versioned vector proposal envelope")
        if (proposal["schema"] != "nabt.retrieval-vectors.v1" or
                proposal["catalog_sha256"] != self.catalog_sha256):
            raise RetrievalError("Vector proposals refer to another catalogue/schema")
        if type(proposal["dimensions"]) is not int or not 1 <= proposal["dimensions"] <= 16000:
            raise RetrievalError("Invalid embedding dimension")
        for field in ("model_id", "revision", "input_recipe"):
            if not _text(proposal[field], field, maximum=1024).strip():
                raise RetrievalError("Empty embedding provenance")
        if not re.fullmatch(r"[0-9a-f]{40}", proposal["revision"]):
            raise RetrievalError("Model revision must be an immutable 40-digit commit")
        if type(proposal["scores"]) is not list or len(proposal["scores"]) > len(self._docs):
            raise RetrievalError("Invalid vector proposal list")
        scores = {}
        for row in proposal["scores"]:
            if type(row) is not dict or set(row) != {"kind", "id", "cosine_similarity"}:
                raise RetrievalError("Malformed vector proposal")
            if type(row["kind"]) is not str or type(row["id"]) is not str:
                raise RetrievalError("Malformed vector identity")
            key, score = (row["kind"], row["id"]), row["cosine_similarity"]
            if key not in self._docs or key in scores:
                raise RetrievalError("Unknown or repeated vector identity")
            if not _finite_score(score) or not -1 <= score <= 1:
                raise RetrievalError("Cosine similarity must be finite and within [-1,1]")
            scores[key] = score
        return scores

    def search(self, query, limit=10, hints=None, vector_scores=None, kind=None):
        foundation.require_foundation('tools.grammar_catalog.retrieval.searchindex.search')
        _limit(limit)
        try:
            foundation.validate_source(_text(query, "query"))
        except ValueError as error:
            raise RetrievalError("Malformed query source representation") from error
        query_terms = set(tokens(_text(query, "query")))
        if not query_terms:
            raise RetrievalError("Query must contain searchable text")
        if kind is not None and (type(kind) is not str or kind not in KINDS):
            raise RetrievalError("Unknown explicit document kind")
        hint_terms = set()
        if hints is not None:
            if type(hints) is not dict or set(hints) - {"chapter", "keywords"}:
                raise RetrievalError("Hints may contain chapter and keywords only")
            chapter, words = hints.get("chapter", ""), hints.get("keywords", [])
            _text(chapter, "chapter hint", maximum=1024)
            if type(words) is not list or len(words) > 64:
                raise RetrievalError("Expected at most 64 keyword hints")
            hint_text = " ".join(_text(w, "keyword hint", maximum=1024) for w in words)
            hint_terms = set(tokens(chapter + " " + hint_text))
        vector = self._vectors(vector_scores)
        keys = [key for key in self._docs if kind is None or key[0] == kind]
        avg_length = sum(sum(self._tf[k].values()) for k in keys) / max(1, len(keys)) or 1
        frequencies = Counter(term for key in keys for term in self._tf[key] if term in query_terms)
        lexical, hinted = {}, {}
        for key in keys:
            tf = self._tf[key]
            length = sum(tf.values())
            score = 0.0
            for term in sorted(query_terms & tf.keys()):
                df = frequencies[term]
                idf = math.log(1 + (len(keys) - df + .5) / (df + .5))
                score += idf * tf[term] * 2.2 / (tf[term] + 1.2 * (.25 + .75 * length / avg_length))
            if score > 0:
                lexical[key] = score
            if hint_terms & tf.keys():
                hinted[key] = len(hint_terms & tf.keys())
        # Untrusted LLM hints are diagnostic only. They cannot prune OR reorder.
        # Initial equal-weight hint RRF degraded the frozen adversarial benchmark;
        # that measurement is preserved separately from the post-review result.
        vector = {k: v for k, v in vector.items() if kind is None or k[0] == kind}
        candidates = lexical.keys() | vector.keys()
        hinted = {k: v for k, v in hinted.items() if k in candidates}
        fusion = Counter()
        streams = [lexical, vector] if vector else []
        for stream in streams:
            for rank, key in enumerate(sorted(stream, key=lambda k: (-stream[k], k)), 1):
                fusion[key] += 1 / (60 + rank)
        scores = fusion if streams else lexical
        ordered = sorted(candidates, key=lambda k: (-scores[k], k))
        result = []
        for rank, key in enumerate(ordered[:limit], 1):
            row = {"kind": key[0], "id": key[1], "rank": rank,
                   "lexical_score": lexical.get(key, 0.0), "ranking_score": scores[key],
                   "hint_token_overlap": hinted.get(key, 0),
                   "record": self.rehydrate(*key)}
            if key in vector:
                row["vector_score"] = vector[key]
            result.append(row)
        return {"schema": "nabt.grammar-retrieval.v1", "catalog_sha256": self.catalog_sha256,
                "candidates": result, "status": "PROPOSALS" if result else "NO_CANDIDATES",
                "matched_documents": len(ordered), "limit": limit, "kind_scope": kind,
                "ranking": "rrf-60" if streams else "bm25-k1-1.2-b-0.75",
                "hint_policy": "diagnostic_only_no_pruning_or_reordering",
                "authority": "RETRIEVAL_ONLY", "exhaustive_language_claim": False,
                "scores_are_probabilities": False, "premises_established_from_free_text": False}


def search(catalog, query, limit=10, hints=None, vector_scores=None, kind=None):
    foundation.require_foundation('tools.grammar_catalog.retrieval.search')
    return SearchIndex(catalog).search(query, limit, hints, vector_scores, kind)
