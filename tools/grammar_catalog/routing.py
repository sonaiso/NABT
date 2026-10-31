"""Proposal ordering with an unfiltered fallback over installed conditional laws.

This does not infer grammatical premises from a query. Each law requires its
own explicitly supplied frame, and each resulting receipt is replayed by NABT.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from nabt import classical_laws
from nabt.errors import NabtError, resource_limit

from .catalog import CatalogError, _canonical as catalog_canonical, validate_catalog
from .retrieval import ROOT, RetrievalError, SearchIndex

MAX_ROUTING_DOCUMENT_BYTES = 8_388_608
MAX_ROUTING_DOCUMENT_NODES = 1_000_000
MAX_ROUTING_DOCUMENT_DEPTH = 64
SOURCE_CONTEXT_SCHEMA = "nabt.classical-rule-source-context.v1"
SOURCE_INVENTORY_PATH = "src/nabt/data/source_evidence/classical_rule_inventory_v1.json"
ROUTING_SCHEMA = "nabt.conditional-rule-routing.v2"


def _integer_limit():
    return resource_limit("Routing JSON exceeds the interpreter's decimal integer conversion limit",
                          maximum_integer_digits=sys.get_int_max_str_digits())


def _snapshot_document(value, label="routing document"):
    """Copy exact finite JSON before hashing or use, with explicit resource bounds."""
    nodes = 0
    active = set()

    def string(text):
        if len(text) > MAX_ROUTING_DOCUMENT_BYTES:
            raise resource_limit(label + " exceeds its byte budget",
                                 maximum_bytes=MAX_ROUTING_DOCUMENT_BYTES)
        try:
            size = len(text.encode("utf-8"))
        except UnicodeError as exc:
            raise RetrievalError(label + " must contain valid UTF-8") from exc
        if size > MAX_ROUTING_DOCUMENT_BYTES:
            raise resource_limit(label + " exceeds its byte budget",
                                 maximum_bytes=MAX_ROUTING_DOCUMENT_BYTES)
        return text

    def copy(value, depth):
        nonlocal nodes
        nodes += 1
        if nodes > MAX_ROUTING_DOCUMENT_NODES:
            raise resource_limit(label + " exceeds its JSON node budget",
                                 maximum_nodes=MAX_ROUTING_DOCUMENT_NODES)
        if depth > MAX_ROUTING_DOCUMENT_DEPTH:
            raise resource_limit(label + " exceeds its nesting budget",
                                 maximum_depth=MAX_ROUTING_DOCUMENT_DEPTH)
        kind = type(value)
        if kind in (dict, list):
            identity = id(value)
            if identity in active:
                raise RetrievalError(label + " must not contain cyclic containers")
            active.add(identity)
            try:
                if kind is list:
                    return [copy(item, depth + 1) for item in value]
                if any(type(key) is not str for key in value):
                    raise RetrievalError(label + " object keys must be strings")
                return {string(key): copy(item, depth + 1) for key, item in value.items()}
            finally:
                active.remove(identity)
        if kind is str:
            return string(value)
        if kind is int:
            try:
                str(value)
            except ValueError as exc:
                raise _integer_limit() from exc
            return value
        if kind is float:
            if not math.isfinite(value):
                raise RetrievalError(label + " numbers must be finite")
            return value
        if value is None or kind is bool:
            return value
        raise RetrievalError(label + " permits only ordinary JSON containers and scalars")

    snapshot = copy(value, 0)
    try:
        encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    except ValueError as exc:
        # Integers were checked above; a changed interpreter bound still must
        # not become a linguistic or malformed-frame judgment.
        if "integer string conversion" in str(exc):
            raise _integer_limit() from exc
        raise RetrievalError(label + " is not finite JSON") from exc
    if len(encoded) > MAX_ROUTING_DOCUMENT_BYTES:
        raise resource_limit(label + " exceeds its byte budget",
                             maximum_bytes=MAX_ROUTING_DOCUMENT_BYTES)
    return snapshot, encoded


def read_routing_document(path):
    """Read a bounded CLI request/report without duplicate-key coercion."""
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_ROUTING_DOCUMENT_BYTES + 1)
    if len(raw) > MAX_ROUTING_DOCUMENT_BYTES:
        raise resource_limit("Routing input file exceeds its byte budget",
                             maximum_bytes=MAX_ROUTING_DOCUMENT_BYTES)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise RetrievalError("Routing JSON has a duplicate object key")
            result[key] = value
        return result

    def integer(text):
        try:
            return int(text)
        except ValueError as exc:
            raise _integer_limit() from exc

    def constant(_):
        raise RetrievalError("Routing JSON numbers must be finite")

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_int=integer, parse_constant=constant)
    except RecursionError as exc:
        raise resource_limit("Routing JSON exceeds the parser nesting budget",
                             maximum_depth=MAX_ROUTING_DOCUMENT_DEPTH) from exc
    return _snapshot_document(value, "routing input file")[0]


def routing_document_text(value):
    """Check the actual emitted bytes, including indentation and final newline."""
    snapshot, _ = _snapshot_document(value)
    text = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if len(text.encode("utf-8")) > MAX_ROUTING_DOCUMENT_BYTES:
        raise resource_limit("Routing output file exceeds its byte budget",
                             maximum_bytes=MAX_ROUTING_DOCUMENT_BYTES)
    return text


def _version(report_version, *, verifying=False):
    if type(report_version) is not int or report_version not in (1, 2):
        raise RetrievalError("Routing report version must be integer 1 or 2")
    if verifying and report_version != 2:
        raise RetrievalError("Whole-request routing verification supports v2 only")


def _fresh_index(index):
    """Replay the existing owner, reject mutable index changes, then use fresh data."""
    if type(index) is not SearchIndex:
        raise RetrievalError("Expected a source-replayed search index")
    try:
        root = index._root
        catalog = index._catalog
        documents = index._docs
        frequencies = index._tf
        advertised_digest = index.catalog_sha256
    except AttributeError as exc:
        raise RetrievalError("Source index is missing its owned state") from exc
    if not isinstance(root, Path):
        raise RetrievalError("Source index root must be an owned path")
    # SearchIndex delegates this catalogue check to validate_catalog and returns
    # newly replayed data. A caller's recomputed digest cannot authenticate it.
    fresh = SearchIndex(catalog, root=root)
    if type(advertised_digest) is not str or advertised_digest != fresh.catalog_sha256:
        raise RetrievalError("Source index catalogue digest differs from fresh owner replay")
    for current, expected, label in ((documents, fresh._docs, "documents"),
                                     (frequencies, fresh._tf, "term frequencies")):
        if type(current) is not dict or set(current) != set(expected):
            raise RetrievalError("Source index " + label + " differ from fresh owner replay")
        for key, expected_row in expected.items():
            row = current[key]
            if label == "term frequencies":
                if type(row) is not Counter:
                    raise RetrievalError("Source index term frequencies must be exact Counters")
                # Counter equality ignores extra zero terms and bool == int;
                # exact typed JSON of its explicit contents preserves both.
                row, expected_row = dict(row), dict(expected_row)
            try:
                same = catalog_canonical(row) == catalog_canonical(expected_row)
            except CatalogError as exc:
                raise RetrievalError("Source index " + label + " are not canonical owner data") from exc
            if not same:
                raise RetrievalError("Source index " + label + " differ from fresh owner replay")
    return fresh


def _source_contexts(index, installed):
    inventory = classical_laws.replay_inventory()
    inventory_inputs = [row for row in index._catalog["inputs"]
                        if row["path"] == SOURCE_INVENTORY_PATH]
    if (not inventory_inputs or
            any(row["sha256"] != classical_laws.INVENTORY_SHA256 for row in inventory_inputs) or
            installed["inventory_sha256"] != classical_laws.INVENTORY_SHA256):
        raise RetrievalError("Source index and installed inventory identity disagree")
    source_rules = {row["rule_id"]: row for row in inventory["rules"]}
    if len(source_rules) != len(inventory["rules"]):
        raise RetrievalError("Installed source inventory has duplicate rule identities")
    contexts = {}
    for installed_rule in installed["rules"]:
        rid = installed_rule["rule_id"]
        if rid not in source_rules:
            raise RetrievalError("Installed operator lacks an exact source rule")
        source = source_rules[rid]
        key = inventory["schema"] + "::" + rid
        record = index.rehydrate("rule", key)
        expected_join = {"rule_key": key, "registry_id": inventory["schema"],
                         "local_id": rid, "runtime_rule_id": rid,
                         "scope": source["scope"], "source_status": source["status"]}
        if any(record.get(field) != value for field, value in expected_join.items()):
            raise RetrievalError("Source catalogue and installed operator rule join disagree")
        expected_installed = {"source_scope": source["scope"],
                              "source_blockers": source["blockers"],
                              "source_text_status": source["status"]}
        if any(installed_rule.get(field) != value for field, value in expected_installed.items()):
            raise RetrievalError("Installed operator and source context disagree")
        contexts[rid] = {
            "schema": SOURCE_CONTEXT_SCHEMA, "authority": "AUTHORED_SOURCE_CONTEXT_ONLY",
            "semantic_authority": "NONE", "action_authority": "NONE",
            "rule_key": key, "rule_id": rid,
            "owner": {"path": SOURCE_INVENTORY_PATH, "schema": inventory["schema"],
                      "sha256": classical_laws.INVENTORY_SHA256},
            "source_scope": source["scope"], "source_blockers": source["blockers"],
            "boundary_mode": source["boundary_mode"], "source_text_status": source["status"],
            "interpretation_note": source["interpretation_note"],
            "positive_cases": deepcopy(source["positive_cases"]),
            "negative_cases": deepcopy(source["negative_cases"]),
            "source_spans": deepcopy(source["source_spans"]),
            "premises_established_from_free_text": False, "grants_language_license": False,
        }
    return contexts, inventory


def _recheck_sources(index, inventory):
    # Compare captured identities; never replace an earlier observation with a
    # newly read digest. These are repeated checks, not an atomic filesystem read.
    current = classical_laws.replay_inventory()
    if catalog_canonical(current) != catalog_canonical(inventory):
        raise RetrievalError("Installed inventory changed during routing")
    validate_catalog(index._catalog, index._root)


def schedule(inventory, ranked):
    """Canonical identity deduplication; every installed ID occurs exactly once."""
    if type(inventory) is not list or type(ranked) is not list:
        raise RetrievalError("Schedule requires lists")
    if any(type(r) is not str for r in inventory + ranked):
        raise RetrievalError("Schedule identifiers must be strings")
    installed = set(inventory)
    if len(installed) != len(inventory):
        raise RetrievalError("Installed rule identities must be unique")
    return list(dict.fromkeys([r for r in ranked if r in installed] + inventory))


def _evaluate_candidates(index, ranked_rule_keys, frames_by_rule, *, budget, report_version):
    """The existing conditional scan, shared by both report versions."""
    if type(index) is not SearchIndex:
        raise RetrievalError("Expected a source-replayed search index")
    if type(ranked_rule_keys) is not list or len(ranked_rule_keys) > 1000:
        raise RetrievalError("Expected at most 1000 ranked catalogue rule keys")
    proposed = []
    for key in ranked_rule_keys:
        rule = index.rehydrate("rule", key)
        if rule["runtime_rule_id"] is not None:
            proposed.append(rule["runtime_rule_id"])
    installed_catalog = classical_laws.catalog()
    installed = [r["rule_id"] for r in installed_catalog["rules"]]
    if type(frames_by_rule) is not dict or any(type(k) is not str for k in frames_by_rule):
        raise RetrievalError("Frames must map installed rule IDs to explicit premises")
    if set(frames_by_rule) - set(installed):
        raise RetrievalError("Frame refers to a rule outside the installed conditional inventory")
    requested_budget = budget
    if budget is None:
        budget = len(installed)
    if type(budget) is not int or not 0 <= budget <= len(installed):
        raise RetrievalError("Budget must be an integer within the installed inventory size")
    ordered = schedule(installed, proposed)
    if report_version == 2:
        contexts, inventory = _source_contexts(index, installed_catalog)
    rows = []
    for rid in ordered[:budget]:
        if rid not in frames_by_rule:
            rows.append({"rule_id": rid, "status": "MISSING_PREMISES"})
            continue
        try:
            receipt = classical_laws.evaluate(rid, deepcopy(frames_by_rule[rid]))
            if report_version == 1:
                verification = classical_laws.verify(receipt)
        except NabtError as exc:
            if report_version == 2 and exc.code == "INSTALLED_CONTRACT_FAILED":
                raise
            # Invalid premises and resource exhaustion remain different failures.
            rows.append({"rule_id": rid, "status": "FRAME_ERROR", "error": exc.as_dict()})
            continue
        if report_version == 2:
            # Failure to replay a generated receipt is an owner failure, not a
            # bad caller frame. Keep it outside the frame-error handler.
            verification = classical_laws.verify(receipt)
        result = receipt["result"]
        partial = (result.get("status") == "DEFER" or bool(result.get("unresolved_profiles")) or
                   result.get("alternatives_complete_within_requested_profile") is False or
                   any(a.get("surface_complete") is False for a in result["alternatives"]))
        rows.append({"rule_id": rid, "status": "PARTIAL" if partial else "CHECKED_CONDITIONAL",
                     "receipt": receipt, "verification": verification})
    inventory_exhausted = len(rows) == len(installed)
    complete = inventory_exhausted and all(r["status"] == "CHECKED_CONDITIONAL" for r in rows)
    report = {"schema": "nabt.conditional-rule-routing.v1", "catalog_sha256": index.catalog_sha256,
            "authority": "CONDITIONAL_TRANSFORMATION_ONLY", "schedule": ordered, "rows": rows,
            "installed_rule_count": len(installed), "examined_rule_count": len(rows),
            "inventory_exhausted": inventory_exhausted, "pending_rule_ids": ordered[budget:],
            "status": ("RESOURCE_EXHAUSTED" if not inventory_exhausted else
                       "CONDITIONAL_SCAN_COMPLETE" if complete else "INCOMPLETE_PREMISES_OR_RESULTS"),
            "conditional_evaluation_complete": complete,
            "premises_established_from_free_text": False, "grants_language_license": False,
            "exhaustive_language_claim": False, "whole_book_completeness": False}
    if report_version == 2:
        report["schema"] = ROUTING_SCHEMA
        for row in rows:
            row["source_context"] = deepcopy(contexts[row["rule_id"]])
        report["request"] = {"ranked_rule_keys": deepcopy(ranked_rule_keys),
                             "frames_sha256": sha256(_snapshot_document(frames_by_rule)[1]).hexdigest(),
                             "budget": requested_budget}
        _recheck_sources(index, inventory)
        report = _snapshot_document(report)[0]
    return report


def evaluate_candidates(index, ranked_rule_keys, frames_by_rule, *, budget=None, report_version=2):
    """Scan installed rules; v2 adds replayed source context beside their receipts."""
    _version(report_version)
    if report_version == 1:
        return _evaluate_candidates(index, ranked_rule_keys, frames_by_rule,
                                    budget=budget, report_version=1)
    request = _snapshot_document({"ranked_rule_keys": ranked_rule_keys,
                                  "frames_by_rule": frames_by_rule, "budget": budget},
                                 "routing request")[0]
    fresh = _fresh_index(index)
    return _evaluate_candidates(fresh, request["ranked_rule_keys"], request["frames_by_rule"],
                                budget=request["budget"], report_version=2)


def _build_routing_report(index, request, report_version):
    found = index.search(request["query"], kind="rule", limit=10)
    report = _evaluate_candidates(index, [row["id"] for row in found["candidates"]],
                                  request["frames_by_rule"], budget=request["budget"],
                                  report_version=report_version)
    report["retrieval"] = found
    if report_version == 2:
        report["request"]["query"] = request["query"]
        report = _snapshot_document(report)[0]
    return report


def build_routing_report(index, query, frames_by_rule, *, budget=None, report_version=2):
    """The existing query/search/scan composition, with raw request binding in v2."""
    _version(report_version)
    if type(index) is not SearchIndex:
        raise RetrievalError("Expected a source-replayed search index")
    request = {"query": query, "frames_by_rule": frames_by_rule, "budget": budget}
    if report_version == 2:
        request = _snapshot_document(request, "routing request")[0]
        index = _fresh_index(index)
    return _build_routing_report(index, request, report_version)


def verify_routing_report(report, *, query, frames_by_rule, budget=None, report_version=2, root=ROOT):
    """Replay v2 from independent inputs and current owners, not report claims."""
    _version(report_version, verifying=True)
    submitted, encoded = _snapshot_document(report, "submitted routing report")
    if type(submitted) is not dict or submitted.get("schema") != ROUTING_SCHEMA:
        raise RetrievalError("Whole-request routing verification requires the v2 report schema")
    request = _snapshot_document({"query": query, "frames_by_rule": frames_by_rule,
                                  "budget": budget}, "routing request")[0]
    # This index is newly created by the verifier, never supplied by the report.
    index = SearchIndex(root=root)
    expected = _build_routing_report(index, request, 2)
    expected_bytes = _snapshot_document(expected)[1]
    if encoded != expected_bytes:
        raise RetrievalError("Routing report differs from complete source and request replay")
    return {"schema": "nabt.conditional-rule-routing-verification.v1", "valid": True,
            "report_schema": ROUTING_SCHEMA, "report_sha256": sha256(expected_bytes).hexdigest(),
            "catalog_sha256": expected["catalog_sha256"], "authority": "ROUTING_REPLAY_ONLY",
            "semantic_authority": "NONE", "action_authority": "NONE",
            "premises_established_from_free_text": False, "grants_language_license": False,
            "exhaustive_language_claim": False, "whole_book_completeness": False}
