"""Proposal ordering with an unfiltered fallback over installed conditional laws.

The ordinary route requires live native control checking. The explicitly named
diagnostic route preserves the older Python replay contract. Neither route
infers grammatical premises from a query or licenses the language of that query.
"""
from __future__ import annotations

from copy import deepcopy

from nabt import classical_certified, classical_laws
from nabt.errors import NabtError

from .retrieval import RetrievalError, SearchIndex


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

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


def _prepare(index, ranked_rule_keys, frames_by_rule, budget):
    if type(index) is not SearchIndex:
        raise RetrievalError("Expected a source-replayed search index")
    if type(ranked_rule_keys) is not list or len(ranked_rule_keys) > 1000:
        raise RetrievalError("Expected at most 1000 ranked catalogue rule keys")
    proposed = []
    for key in ranked_rule_keys:
        rule = index.rehydrate("rule", key)
        if rule["runtime_rule_id"] is not None:
            proposed.append(rule["runtime_rule_id"])
    installed = [r["rule_id"] for r in classical_laws.catalog()["rules"]]
    if type(frames_by_rule) is not dict or any(type(k) is not str for k in frames_by_rule):
        raise RetrievalError("Frames must map installed rule IDs to explicit premises")
    if set(frames_by_rule) - set(installed):
        raise RetrievalError("Frame refers to a rule outside the installed conditional inventory")
    if budget is None:
        budget = len(installed)
    if type(budget) is not int or not 0 <= budget <= len(installed):
        raise RetrievalError("Budget must be an integer within the installed inventory size")
    return installed, schedule(installed, proposed), budget


def _partial(result):
    return (result.get("status") == "DEFER" or bool(result.get("unresolved_profiles")) or
            result.get("alternatives_complete_within_requested_profile") is False or
            any(a.get("surface_complete") is False for a in result["alternatives"]))


def evaluate_diagnostic_candidates(index, ranked_rule_keys, frames_by_rule, *, budget=None):
    """Legacy v1 Python replay, explicitly diagnostic and without native claims."""
    foundation.require_foundation('tools.grammar_catalog.routing.evaluate_diagnostic_candidates')
    installed, ordered, budget = _prepare(index, ranked_rule_keys, frames_by_rule, budget)
    rows = []
    for rid in ordered[:budget]:
        if rid not in frames_by_rule:
            rows.append({"rule_id": rid, "status": "MISSING_PREMISES"})
            continue
        try:
            receipt = classical_laws.evaluate(rid, deepcopy(frames_by_rule[rid]))
            verification = classical_laws.verify(receipt)
            result = receipt["result"]
            rows.append({"rule_id": rid, "status": "PARTIAL" if _partial(result) else "CHECKED_CONDITIONAL",
                         "receipt": receipt, "verification": verification})
        except NabtError as exc:
            # Invalid premises and resource exhaustion remain different failures.
            rows.append({"rule_id": rid, "status": "FRAME_ERROR", "error": exc.as_dict()})
    inventory_exhausted = len(rows) == len(installed)
    complete = inventory_exhausted and all(r["status"] == "CHECKED_CONDITIONAL" for r in rows)
    return {"schema": "nabt.conditional-rule-routing.v1", "catalog_sha256": index.catalog_sha256,
            "authority": "CONDITIONAL_TRANSFORMATION_ONLY", "schedule": ordered, "rows": rows,
            "installed_rule_count": len(installed), "examined_rule_count": len(rows),
            "inventory_exhausted": inventory_exhausted, "pending_rule_ids": ordered[budget:],
            "status": ("RESOURCE_EXHAUSTED" if not inventory_exhausted else
                       "CONDITIONAL_SCAN_COMPLETE" if complete else "INCOMPLETE_PREMISES_OR_RESULTS"),
            "conditional_evaluation_complete": complete,
            "premises_established_from_free_text": False, "grants_language_license": False,
            "exhaustive_language_claim": False, "whole_book_completeness": False}


def evaluate_candidates(index, ranked_rule_keys, frames_by_rule, *, budget=None):
    """Require native authority for each supplied frame, retaining every rule.

    A v2 row separates the old diagnostic receipt from a live native receipt.
    Its claims apply only to the native finite control equation; they do not
    establish the query's premises, output spelling, or whole-book semantics.
    An exact empty action set is not rejection of a word in Arabic.
    """
    foundation.require_foundation('tools.grammar_catalog.routing.evaluate_candidates')
    installed, ordered, budget = _prepare(index, ranked_rule_keys, frames_by_rule, budget)
    rows = []
    for rid in ordered[:budget]:
        if rid not in frames_by_rule:
            rows.append({"rule_id": rid, "status": "MISSING_PREMISES", "claims": []})
            continue
        try:
            native = classical_certified.evaluate_certified(rid, deepcopy(frames_by_rule[rid]))
            parent = native["parent_receipt"]
            verification = classical_laws.verify(parent)
            checked = (native["status"] == "CHECKED_CONDITIONAL_CONTROL" and
                       native["native_checked"] is True and native["bounded_rule_checked"] is True)
            if checked:
                status = "PARTIAL" if _partial(parent["result"]) else "CHECKED_CONDITIONAL_CONTROL"
            elif native["status"] in {"RESOURCE_EXHAUSTED", "VERIFICATION_UNAVAILABLE"}:
                status = native["status"]
            else:
                status = "OUTSIDE_NATIVE_DOMAIN"
            rows.append({"rule_id": rid, "status": status,
                "diagnostic": {"authority": "PYTHON_DIAGNOSTIC_ONLY", "receipt": parent,
                               "verification": verification},
                "native_receipt": native, "claims": deepcopy(native["claims"]) if checked else []})
        except NabtError as exc:
            rows.append({"rule_id": rid,
                         "status": "RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT" else "FRAME_ERROR",
                         "error": exc.as_dict(), "claims": []})
    inventory_exhausted = len(rows) == len(installed)
    complete = bool(rows) and inventory_exhausted and all(r["status"] == "CHECKED_CONDITIONAL_CONTROL" for r in rows)
    native_checked = bool(rows) and inventory_exhausted and all(
        r.get("native_receipt", {}).get("native_checked") is True for r in rows)
    controls_complete = bool(rows) and inventory_exhausted and all(
        r.get("native_receipt", {}).get("bounded_rule_checked") is True for r in rows)
    if not inventory_exhausted or any(r["status"] == "RESOURCE_EXHAUSTED" for r in rows):
        status = "RESOURCE_EXHAUSTED"
    elif any(r["status"] == "VERIFICATION_UNAVAILABLE" for r in rows):
        status = "VERIFICATION_UNAVAILABLE"
    else:
        status = "CONDITIONAL_CONTROL_SCAN_COMPLETE" if complete else "INCOMPLETE_PREMISES_OR_RESULTS"
    return {"schema": "nabt.conditional-rule-routing.v2", "catalog_sha256": index.catalog_sha256,
            "authority": "NATIVE_FINITE_CONTROL_ONLY" if any(r["claims"] for r in rows) else "DIAGNOSTIC_ONLY",
            "native_required": True,
            "schedule": ordered, "rows": rows,
            "installed_rule_count": len(installed), "examined_rule_count": len(rows),
            "inventory_exhausted": inventory_exhausted, "pending_rule_ids": ordered[budget:],
            "status": status, "native_checked": native_checked,
            "native_control_complete": controls_complete,
            "conditional_evaluation_complete": complete,
            "strict_language_accepted": False, "source_to_control_proved": False,
            "premises_established_from_free_text": False, "grants_language_license": False,
            "exhaustive_language_claim": False, "whole_book_completeness": False}
