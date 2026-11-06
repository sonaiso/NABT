"""Source-derived operation cards over the one installed proof catalogue."""
from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import unicodedata

from tools.entropy_framework.reuse import current_catalog
from tools.evidence_lifecycle_v1 import wire
from .operation_runtime import specifications
from .retrieval import ROOT, SearchIndex, RetrievalError, tokens, _limit

RECIPE = "nabt.operation-retrieval.exact-and-lexical.v1"


def digest(value):
    return sha256(wire(value).encode("utf-8")).hexdigest()


def source_snapshot(root=ROOT):
    """Conservative source/data identity, including native availability.

    Hashes establish reproducibility, not authenticity or Python/Lean refinement.
    No result cache is used; mutable source histories are executed on every call.
    """
    root = Path(root).resolve()
    catalog, relative, _, inputs = current_catalog(root)
    inputs = dict(inputs)
    paths = set()
    for directory in ("src/nabt", "tools", "docs", "formal/.lake/build/bin"):
        for path in (root / directory).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                paths.add(path.relative_to(root).as_posix())
    # This reviewed curriculum is a runtime input, not an authority inferred
    # from the historical lesson results next to it.
    paths.add("evidence/cognitive_curriculum_v1/source_review.json")
    for path in sorted(paths):
        target = root / path
        if not target.resolve().is_relative_to(root) or target.is_symlink():
            raise RetrievalError("Source snapshot cannot escape the installed repository")
        inputs[path] = sha256(target.read_bytes()).hexdigest()
    return {"schema": "nabt.operation-snapshot.v1", "files": inputs,
            "proof_catalog": relative, "proof_authority": catalog["authority"],
            "native_readiness_is_not_verification": True}, catalog


def _source_unit(root, path, symbol):
    raw = (root / path).read_bytes()
    text = raw.decode("utf-8")
    nodes = ast.parse(text).body
    node = None
    for name in symbol.split("."):
        matches = [n for n in nodes if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name]
        if len(matches) != 1:
            raise RetrievalError("Installed owner symbol missing or ambiguous: " + symbol)
        node = matches[0]
        nodes = node.body
    lines = text.splitlines(keepends=True)
    return {"path": path, "symbol": symbol, "start_line": node.lineno, "end_line": node.end_lineno,
            "file_sha256": sha256(raw).hexdigest(), "raw_text": "".join(lines[node.lineno-1:node.end_lineno])}


def exact_terms(text):
    """Literal tokens and positions; combining marks and order are retained."""
    result, start = [], None
    for i, char in enumerate(text + " "):
        keep = char.isalnum() or char == "_" or unicodedata.category(char).startswith("M")
        if keep and start is None:
            start = i
        elif not keep and start is not None:
            result.append({"surface": text[start:i], "codepoint_span": [start, i],
                "utf8_span": [len(text[:start].encode()), len(text[:i].encode())]})
            start = None
    return result


class OperationSearchIndex(SearchIndex):
    """BM25 + exact-token RRF; vectors, when supplied, remain proposals only."""

    def __init__(self, *, root=ROOT):
        self.root = Path(root).resolve()
        self.snapshot, compiled = source_snapshot(self.root)
        self.snapshot_sha256 = digest(self.snapshot)
        self._docs = {}
        cards = []
        for identifier, spec in specifications().items():
            path, symbol, module = spec.pop("owner")
            source = _source_unit(self.root, path, symbol)
            references = [{k: row[k] for k in ("name", "statement_sha256", "source_path", "source_sha256", "range")}
                          for row in compiled["theorems"] if row["module"] == module]
            if module is not None and not references:
                raise RetrievalError("Operation has no declared related proof module")
            card = {"operation_id": identifier, **spec, "source": source,
                    "related_proof_module": module, "related_declarations": references,
                    "proof_catalog": self.snapshot["proof_catalog"],
                    "relation_to_proofs": "RELATED_OWNER_MODULE_NOT_ADAPTER_REFINEMENT",
                    "prerequisites": ["VALID_TYPED_INPUTS", "CURRENT_INSTALLED_SNAPSHOT", "OWNER_GATES"],
                    "blockers": ["MISSING_INPUT", "STALE_SOURCE", "OWNER_DEFER_OR_REJECT", "RESOURCE_LIMIT"],
                    "authority": "RETRIEVAL_ONLY"}
            cards.append(card)
            self._add("item", identifier, identifier + " " + card["title"] + " " + source["raw_text"], card)
        self._catalog = {"schema": "nabt.operation-catalog.v1", "snapshot_sha256": self.snapshot_sha256,
                         "items": cards, "input_recipe": RECIPE, "authority": "RETRIEVAL_ONLY"}
        self.catalog_sha256 = digest(self._catalog)
        self._tf = {key: Counter(tokens(doc["search_text"])) for key, doc in self._docs.items()}
        self._exact = {key: {r["surface"] for r in exact_terms(doc["search_text"])} for key, doc in self._docs.items()}

    def catalog(self):
        return deepcopy(self._catalog)

    def assert_current(self):
        fresh, _ = source_snapshot(self.root)
        if digest(fresh) != self.snapshot_sha256:
            raise RetrievalError("STALE_OPERATION_SNAPSHOT")

    def search(self, query, limit=5, hints=None, vector_scores=None, kind=None):
        _limit(limit)
        if vector_scores is not None and (type(vector_scores) is not dict or vector_scores.get("input_recipe") != RECIPE):
            raise RetrievalError("Operation vector input recipe mismatch")
        self.assert_current()
        # Obtain the complete lexical/vector stream before the display limit.
        base = super().search(query, len(self._docs), hints, vector_scores, kind)
        occurrences = exact_terms(query)
        terms = {r["surface"] for r in occurrences}
        literal = {key: len(terms & values) for key, values in self._exact.items()
                   if terms & values and (kind is None or kind == key[0])}
        scores = Counter()
        lexical = {(r["kind"], r["id"]): r for r in base["candidates"]}
        for stream in (list(lexical), sorted(literal, key=lambda key: (-literal[key], key))):
            for rank, key in enumerate(stream, 1):
                scores[key] += 1 / (60 + rank)
        ordered = sorted(scores, key=lambda key: (-scores[key], key))
        rows = []
        for rank, key in enumerate(ordered[:limit], 1):
            row = lexical.get(key, {"kind": key[0], "id": key[1], "lexical_score": 0.0,
                                    "record": self.rehydrate(*key)})
            rows.append({**row, "rank": rank, "ranking_score": scores[key], "exact_token_overlap": literal.get(key, 0)})
        return {**base, "schema": "nabt.operation-retrieval.v1", "candidates": rows,
                "limit": limit, "matched_documents": len(ordered), "ranking": "lexical-and-exact-rrf-60",
                "status": "PROPOSALS" if rows else "NO_CANDIDATES", "exact_query_occurrences": occurrences,
                "raw_query": query, "query_sha256": sha256(query.encode()).hexdigest(),
                "input_recipe": RECIPE, "snapshot_sha256": self.snapshot_sha256,
                "normalization_of_execution_inputs": "NONE"}
