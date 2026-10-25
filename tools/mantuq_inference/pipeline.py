"""Search proposals plus an unfiltered scan of installed conditional policies."""
from copy import deepcopy

from tools.grammar_catalog.routing import schedule
from tools.grammar_catalog.retrieval import RetrievalError
from .inventory import ROOT, build_inventory
from .evaluator import evaluate, EvaluationBudget
from .retrieval import InferenceSearchIndex


def run(query, requests_by_policy, *, display_limit=10, preferred_order=None,
        max_policies=None, evaluation_budget=None, vector_scores=None, root=ROOT):
    """Evaluate explicit plans even when their policy is absent from top-k.

    Missing plans are preserved as unknowns. The scan does not manufacture a
    reading, bridge, interpretation, or negative conclusion from a query.
    """
    inventory = build_inventory(root)
    installed = [r["rule_id"] for r in inventory["rules"]]
    if (type(requests_by_policy) is not dict or
            any(type(k) is not str or k not in installed for k in requests_by_policy)):
        raise RetrievalError("Requests must map installed policy IDs to explicit plans")
    for key, request in requests_by_policy.items():
        if type(request) is not dict or request.get("policy_id") != key:
            raise RetrievalError("Plan identity differs from its policy key")
    if preferred_order is not None and (type(preferred_order) is not list or
            len(preferred_order) > 1000 or any(type(p) is not str or p not in installed
                                              for p in preferred_order)):
        raise RetrievalError("Preferred order must contain installed policy IDs")
    if max_policies is None:
        max_policies = len(installed)
    if type(max_policies) is not int or not 0 <= max_policies <= len(installed):
        raise RetrievalError("Policy budget must be an integer within the inventory size")
    if evaluation_budget is not None and type(evaluation_budget) is not EvaluationBudget:
        raise RetrievalError("Expected installed EvaluationBudget")
    index = InferenceSearchIndex(root=root)
    retrieved = index.search(query, limit=display_limit, vector_scores=vector_scores, kind="rule")
    ranked = preferred_order if preferred_order is not None else [r["id"] for r in retrieved["candidates"]]
    ordered = schedule(installed, ranked)
    plans = deepcopy(requests_by_policy)
    rows = []
    for policy in ordered[:max_policies]:
        if policy not in plans:
            result = {"status": "UNKNOWN", "reason": "NO_STRUCTURED_PREMISES",
                      "conditional_consequence": False, "all_arabic_complete": False,
                      "world_truth_established": False}
        else:
            result = evaluate(plans[policy], budget=evaluation_budget, root=root)
        rows.append({"policy_id": policy, "result": result})
    complete = len(rows) == len(installed)
    return {"schema": "nabt.inference-pipeline.v1", "authority": "CONDITIONAL_ASSUMPTIONS_ONLY",
            "retrieval": retrieved, "inventory_sha": index.catalog_sha256,
            "schedule": ordered, "rows": rows, "pending_policy_ids": ordered[max_policies:],
            "installed_policy_count": len(installed), "examined_policy_count": len(rows),
            "inventory_exhausted": complete,
            "status": "POLICY_SCAN_COMPLETE" if complete else "RESOURCE_EXHAUSTED",
            "display_limit_affects_inference": False,
            "premises_established_from_free_text": False,
            "occurrence_classification_proved": False, "whole_arabic_complete": False,
            "world_truth_established": False}
