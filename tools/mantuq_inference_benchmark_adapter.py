"""Transport for frozen semantic cases; no expected answer enters execution.

Every nonempty law below is an explicit fixture assumption. It is not claimed
to have been extracted from the fixture's Arabic title or an usul book. The
runtime must check the implication rather than infer it from filled slots.
"""
from copy import deepcopy
from hashlib import sha256
import json


def request_for(case):
    # Case facts specify independently authored assumptions, not observations of
    # the world. IDs deliberately retain branch, time and scope in atom identity.
    arguments = ["origin_A", "branch_B", "time_T", "scope_S"]

    def atom(predicate, positive=True):
        return {"predicate": predicate, "arguments": list(arguments), "positive": positive}

    family = case["family"]
    if family == "guarded_cause":
        slots = [("cause", atom("cause")), ("condition", atom("condition")),
                 ("blockerAbsence", atom("blocker", False))]
        mapping = {"cause": atom("cause"), "not_cause": atom("cause", False),
                   "condition": atom("condition"), "blocker": atom("blocker"),
                   "not_blocker": atom("blocker", False)}
        conclusion = atom("ruling")
        policy = "guarded_cause"
    elif family == "analogy":
        slots = [("originRuling", atom("origin_ruling")), ("sharedCause", atom("shared_cause")),
                 ("transferBridge", atom("transfer_bridge")), ("condition", atom("branch_condition")),
                 ("blockerAbsence", atom("blocker", False))]
        mapping = {name: atom(name) for name in ("origin_ruling", "shared_cause", "transfer_bridge", "branch_condition", "blocker")}
        mapping["not_blocker"] = atom("blocker", False)
        conclusion = atom("branch_ruling")
        policy = "analogy"
    elif family == "opposition":
        slots = [("premise", atom("antecedent", False)), ("necessaryBridge", atom("necessary_bridge")),
                 ("qualified", atom("qualified")), ("countertextAbsence", atom("countertext", False)),
                 ("usualCaseAbsence", atom("usual", False))]
        mapping = {"negative_antecedent": atom("antecedent", False), "qualified": atom("qualified"),
                   "not_countertext": atom("countertext", False), "countertext": atom("countertext"),
                   "not_usual": atom("usual", False), "usual": atom("usual")}
        conclusion = atom("ruling", False)
        policy = "opposition"
    elif family == "direct":
        slots = [("premise", atom("asserted"))]
        mapping = {"asserted": atom("asserted"), "not_asserted": atom("asserted", False)}
        conclusion = atom("asserted")
        policy = "matching"
    else:
        raise ValueError("Unknown frozen fixture family")
    hypotheses = [deepcopy(mapping[name]) for name in case["facts"]]
    if family == "opposition" and case.get("necessary_bridge"):
        hypotheses.append(atom("necessary_bridge"))
    if case.get("changed_evidence_scope"):
        for hypothesis in hypotheses:
            hypothesis["arguments"][3] = "scope_elsewhere"
    if case.get("changed_branch"):
        for hypothesis in hypotheses:
            hypothesis["arguments"][1] = "branch_C"
    if case.get("changed_time"):
        for hypothesis in hypotheses:
            hypothesis["arguments"][2] = "time_U"
    requirements = [{"slot": slot, "atom": a} for slot, a in slots]
    reading = {
        "reading_id": "fixture_reading",
        "requirements": requirements, "hypotheses": hypotheses,
        # The frozen profile declares this full implication. The missing bridge
        # cases still lack their separate necessary/transfer bridge obligation.
        "bridge": {"body": [deepcopy(r["atom"]) for r in requirements],
                   "head": deepcopy(conclusion), "basis": "caller_assumption"},
    }
    if family == "opposition":
        reading["necessary_relation"] = (
            {"kind": "necessary", "antecedent": atom("ruling"), "consequent": atom("antecedent"),
             "basis": "caller_assumption"} if case.get("necessary_bridge") else None)
    request = {
        "schema": "nabt.mantuq-inference-request.v1", "policy_id": policy,
        "binding": {"source_id": "independent_benchmark_fixture", "scope": "scope_S", "time": "time_T",
                    "context": "Explicit symbolic premises; no empirical or original-book truth asserted.",
                    "source_text": "فَرْضِيَّةٌ شَرْطِيَّةٌ لِلْقِيَاسِ الْبَرْمَجِيِّ."},
        "conclusion": conclusion, "readings": [reading],
    }
    if family == "opposition":
        request["contrast_kind"] = case.get("contrast_kind", "condition")
    request.update(deepcopy(case.get("caller_fields", {})))
    return request


def observe(case):
    from tools.mantuq_inference import evaluate, EvaluationBudget
    request = request_for(case)
    contract_checks, pipeline_observation = {}, None
    if "rank_order" in case or "display_limit" in case:
        from tools.mantuq_inference import build_inventory
        from tools.mantuq_inference.pipeline import run
        installed = [rule["rule_id"] for rule in build_inventory()["rules"]]
        ordered = list(reversed(installed)) if case["rank_order"] == "reverse" else installed
        baseline = run("المطابقة", {request["policy_id"]: request},
                       display_limit=len(installed), preferred_order=installed)
        routed = run("المطابقة", {request["policy_id"]: request},
                     display_limit=case["display_limit"], preferred_order=ordered)
        row_by_id = {row["policy_id"]: row["result"] for row in routed["rows"]}
        base_by_id = {row["policy_id"]: row["result"] for row in baseline["rows"]}
        result = row_by_id[request["policy_id"]]
        displayed = [candidate["id"] for candidate in routed["retrieval"]["candidates"]]
        contract_checks = {
            "all_installed_policies_examined": len(routed["rows"]) == len(installed) and set(row_by_id) == set(installed),
            "reverse_order_exercised": routed["schedule"] == ordered,
            "display_limit_exercised": len(displayed) <= case["display_limit"],
            "required_policy_outside_display": request["policy_id"] not in displayed,
            "outcome_invariant_under_display_and_rank": all(
                row_by_id[key]["status"] == base_by_id[key]["status"] and
                row_by_id[key]["conditional_consequence"] == base_by_id[key]["conditional_consequence"]
                for key in installed),
            "scan_complete": routed["inventory_exhausted"] is True,
            "no_world_or_language_claim": routed["world_truth_established"] is False and routed["whole_arabic_complete"] is False,
        }
        pipeline_observation = {"displayed_ids": displayed, "examined_ids": list(row_by_id),
                                "schedule": routed["schedule"], "installed_policy_count": len(installed)}
    else:
        kwargs = {}
        if "budget" in case:
            kwargs["budget"] = EvaluationBudget(max_readings=case["budget"])
        result = evaluate(request, **kwargs)
    status = result["status"]
    if status == "REFUTED":
        outcome = "UNKNOWN"  # Opposed obligation is not a negative target proof.
    elif status in {"SOURCE_ERROR", "VERIFICATION_UNAVAILABLE"}:
        outcome = "UNMEASURED"
    else:
        outcome = status
    return {
        "outcome": outcome, "conditional_support": result["conditional_consequence"],
        "world_truth_established": result["world_truth_established"],
        "whole_arabic_complete": result["all_arabic_complete"],
        "raw_status": status, "raw_reason": result.get("reason"),
        "contract_checks": contract_checks, "pipeline_observation": pipeline_observation,
        "reading_statuses": [{"reading_id": row["reading_id"], "status": row["status"],
                              "reason": row.get("reason"), "guard_status": row.get("guard_status")}
                             for row in result.get("readings", [])],
        "request_sha256": sha256(json.dumps(request, ensure_ascii=False, sort_keys=True,
                                              separators=(",", ":")).encode()).hexdigest(),
    }
