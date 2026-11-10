"""Checked controlled reformulation and a view of existing quantified evidence.

Neither an Arabic equivalence engine nor a second inference/lifecycle owner.
The native quantifier reader checks the proposed wording; its existing source
owners supply every judgment, signed premise, dependency and revision step.
"""
from copy import deepcopy

from tools.source_learning_connection import ConnectionMismatch
from . import composition_quantifier as quantifier
from .source_evidence_view import ledger, premises


def canonical_text(frame):
    genus, prop = frame["genus"], frame["property"]
    text = {"all": f"كل {genus} هو {prop}",
            "not_all": f"ليس كل {genus} هو {prop}",
            "all_not": f"كل {genus} ليس هو {prop}"}[frame["kind"]]
    return "هل " + text + "؟" if frame["force"] == "question" else text + "."


def _meaning(projection):
    return {"frame": {key: deepcopy(projection["frame"][key])
                      for key in ("kind", "genus", "property", "force", "scope_tree")},
            **{key: deepcopy(projection[key]) for key in
               ("domain", "clauses", "policy_text", "query_text")}}


def checked_reading(native_request, projection, native_check):
    """Both projections are checked by the installed reader, not by truth values."""
    text = canonical_text(projection["frame"])
    reformulated = quantifier.project(text, native_request["domain"])
    checked = native_check({**native_request, "text": text}, reformulated)
    if _meaning(projection) != _meaning(reformulated):
        raise ConnectionMismatch("Reformulation changed scope, force, concepts or compiled obligations")
    return {"schema": "nabt.scoped-reading-view.v1", "canonical_text": text,
            "preservation": "SAME_CONTROLLED_READING_AND_COMPILED_OBLIGATIONS",
            "semantic_projection": _meaning(projection), "native_check": checked,
            "source_replaced": False, "reformulation_added_as_evidence": False,
            "general_arabic_equivalence_proved": False, "world_truth_established": False}


def evidence_view(projection, owner):
    """Expose each source-backed route to support or oppose the target.

Presence of premises is displayed independently of policy availability and of
the owner's judgment. No conclusion is recomputed from these display rows.
"""
    if not owner["chain_complete"] or not owner["lifecycle"]["native_checked"]:
        raise ConnectionMismatch("An incomplete owner cannot supply a checked evidence view")
    source_ledger = ledger(owner)
    history = []
    for step in owner["history"]:
        native = step["ground_inference"]
        if not native["native_checked"]:
            raise ConnectionMismatch("Unchecked grounding in composition evidence view")
        certificate = native["answer"]["analysis_certificate"]["kernel_certificate"]
        ready = set(step["ready_sources"])
        branches = []
        for index, clause in enumerate(projection["clauses"]):
            indices = [i for i, native_clause in enumerate(certificate["clauses"])
                       if native_clause == clause]
            rows = premises(clause["body"], source_ledger, ready, certificate)
            branches.append({"branch_index": index,
                "conclusion_polarity": "support" if clause["head"]["positive"] else "refutation",
                "clause": deepcopy(clause), "native_clause_indices": indices,
                "rule_present_in_native_program": bool(indices),
                "rule_source_bindings": [deepcopy(g) for g in native["grounding"]
                                         if g["ground_index"] in indices],
                "premises": rows,
                "missing_premise_indices": [i for i, r in enumerate(rows)
                                            if not r["present_in_native_closure"]],
                "opposed_premise_indices": [i for i, r in enumerate(rows)
                                            if r["opposite_in_native_closure"]],
                "nonclean_premise_indices": [i for i, r in enumerate(rows)
                                             if not r["present_in_clean_closure"]]})
        history.append({"step": step["step"], "event_id": step["event_id"],
            "status": step["status"], "policy_ready": quantifier.POLICY_SOURCE in ready,
            "active_sources": deepcopy(step["active_sources"]),
            "ready_sources": deepcopy(step["ready_sources"]),
            "support_ids": deepcopy(step["support_ids"]),
            "refutation_ids": deepcopy(step["refutation_ids"]), "branches": branches})
    return {"schema": "nabt.scoped-evidence-view.v1",
            "authority": "DISPLAY_OF_CHECKED_OWNER_EVIDENCE", "decision_recomputed": False,
            "source_ledger": source_ledger, "history": history,
            "status": owner["status"], "missing_evidence_is_negation": False,
            "world_truth_established": False, "action_authority": "NONE"}
