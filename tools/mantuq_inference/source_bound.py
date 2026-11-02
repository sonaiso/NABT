"""Bind one installed ground reading to the existing conditional evaluator.

The caller assigns evidence roles; the source is independently read by the
existing native pilot. Complete signed support is retained, and an atom that
has no clean source proof cannot be reintroduced as a clean assumption. This
adapter neither classifies an Arabic occurrence nor establishes world truth.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import re

from tools import explainable_pilot as pilot
from tools import verified_reading as ground
from . import evaluator


ROOT = Path(__file__).resolve().parents[2]
PLAN_SCHEMA = "nabt.mantuq-source-plan.v1"
RESULT_SCHEMA = "nabt.mantuq-source-result.v1"
READING_ID = "canonical-ground-reading"
_LIMITS = {
    "language": "canonical_ground_source_entailment",
    "reading_count": 1,
    "source_support": "SOURCE_RELATIVE_ONLY",
    "role_assignment": "CALLER_PLAN_ONLY",
    "source_to_requirements_proved": False,
    "occurrence_classification_proved": False,
    "semantic_bridge_proved": False,
    "reading_enumeration_proved": False,
    "source_authenticity_established": False,
    "world_truth_established": False,
    "all_arabic_complete": False,
    "rule_adoption_established": False,
    "action_authority": "NONE",
    "learner_trained": False,
    "timeout_scope": "PER_NATIVE_INVOCATION_NOT_TOTAL_WALL_TIME",
    "inner_bridge_basis": "LEGACY_CONDITIONAL_REQUEST_NOT_A_SOURCE_AUTHORITY_FLAG",
}


def _base():
    # All outcomes retain one fixed envelope. Incomplete checks never produce a
    # positive conditional claim or an invented successful native receipt.
    return {
        "schema": RESULT_SCHEMA,
        "status": "INVALID",
        "reason": "INPUT_NOT_CHECKED",
        "conditional_consequence": False,
        "input_binding": None,
        "plan": None,
        "budget": None,
        "source_answer": None,
        "source_witnesses": {"requirements": [], "bridge": None, "necessary_relation": None},
        "conditional_request": None,
        "conditional_result": None,
        "native_checkers": {"verified_reading_sha256": None, "classical_semantic_probe_sha256": None},
        "limits": deepcopy(_LIMITS),
    }


def _stop(result, status, reason):
    result.update(status=status, reason=reason, conditional_consequence=False)
    return result


def _reference(value, label):
    if value is not None and (type(value) is not str or len(value) > 16
            or re.fullmatch(r"c(?:0|[1-9][0-9]*)", value) is None):
        raise evaluator.InvalidRequest(label + " must be a canonical source clause ID or null")
    return value


def _plan(value):
    evaluator._object(value, ("schema", "policy_id", "requirements", "bridge_clause"),
                      "source plan", ("contrast_kind", "necessary_clause"))
    if type(value["schema"]) is not str or value["schema"] != PLAN_SCHEMA:
        raise evaluator.InvalidRequest("unknown source plan schema")
    policy = value["policy_id"]
    if type(policy) is not str or policy not in evaluator.SLOTS:
        raise evaluator.InvalidRequest("unknown installed policy")
    if policy == "opposition":
        if not {"contrast_kind", "necessary_clause"} <= set(value):
            raise evaluator.InvalidRequest("opposition requires contrast_kind and necessary_clause")
        if type(value["contrast_kind"]) is not str or value["contrast_kind"] not in {
                "attribute", "condition", "endpoint", "number", "name", "innama"}:
            raise evaluator.InvalidRequest("unknown opposition contrast_kind")
        _reference(value["necessary_clause"], "necessary_clause")
    elif "contrast_kind" in value or "necessary_clause" in value:
        raise evaluator.InvalidRequest("contrast_kind and necessary_clause belong only to opposition")
    _reference(value["bridge_clause"], "bridge_clause")
    requirements = value["requirements"]
    if type(requirements) is not list or not 1 <= len(requirements) <= 16:
        raise evaluator.InvalidRequest("one to sixteen requirements are required")
    for requirement in requirements:
        evaluator._object(requirement, ("slot", "atom"), "source requirement")
        evaluator._text(requirement["slot"], "slot", 128)
        evaluator._atom(requirement["atom"])
    # Slot profiles, duplicate/aliased obligations, and signed guards remain
    # owned by evaluator._validate after the independently checked query exists.
    return deepcopy(value)


def _clause(answer, clause_id):
    if clause_id is None:
        return None
    evidence = answer["analysis_certificate"]
    index = int(clause_id[1:])
    clauses = evidence["kernel_certificate"]["clauses"]
    if index >= len(clauses):
        raise evaluator.InvalidRequest("source clause reference is outside the checked reading")
    clause = clauses[index]
    if clause["kind"] != "rule":
        raise evaluator.InvalidRequest("source bridge reference must select a rule")
    span = evidence["source_clauses"][index]
    if span["id"] != clause_id:
        raise evaluator.InvalidRequest("source clause identity differs from the checked span")
    return {**deepcopy(span), "clause": deepcopy(clause)}


def _witnesses(answer, requirements):
    traces = answer["analysis_certificate"]["traces"]
    indices = {}
    for name in ("full", "clean"):
        indices[name] = {}
        for node in traces[name]:
            indices[name].setdefault(ground.key(node["atom"]), node["id"])
    return [{
        "slot": requirement["slot"],
        "atom": deepcopy(requirement["atom"]),
        "full_witness": indices["full"].get(ground.key(requirement["atom"])),
        "clean_witness": indices["clean"].get(ground.key(requirement["atom"])),
        "opposite_full_witness": indices["full"].get(ground.opposite(ground.key(requirement["atom"]))),
    } for requirement in requirements]


def _probe_path(probe):
    return Path(probe if probe is not None else os.environ.get(
        "NABT_CLASSICAL_SEMANTIC_PROBE", ROOT / "formal/.lake/build/bin/classicalSemanticProbe")).resolve()


def _fingerprint(path):
    try:
        return pilot.file_sha(path)
    except OSError:
        return None


def _request(plan, binding, conclusion, hypotheses):
    row = {"reading_id": READING_ID, "requirements": deepcopy(plan["requirements"]),
           "hypotheses": deepcopy(hypotheses), "bridge": None}
    request = {"schema": evaluator.REQUEST_SCHEMA, "policy_id": plan["policy_id"],
               "binding": {key: binding[key] for key in (
                   "source_id", "source_text", "scope", "context", "time")},
               "conclusion": deepcopy(conclusion), "readings": [row]}
    if plan["policy_id"] == "opposition":
        request["contrast_kind"] = plan["contrast_kind"]
        row["necessary_relation"] = None
    return request


def evaluate_source(raw, query, plan, *, source_id="text", revision="1", scope="default",
                    context="unspecified", time="unspecified", budget=None, checker=None,
                    semantic_probe=None, timeout=20, root=ROOT):
    """Replay source support, bind explicit rule references, then use evaluate.

    Native paths are trusted caller configuration, never fields in the plan.
    ``timeout`` limits each native invocation, not the complete operation.
    One canonical ground reading is checked; no free-Arabic enumeration or
    automatic assignment of usuli roles is claimed.
    """
    result = _base()
    try:
        if type(timeout) is not int or not 1 <= timeout <= 60:
            raise evaluator.InvalidRequest("source native timeout must be an integer in [1, 60] seconds")
        pilot.validate_inputs(raw, query, source_id, revision, scope, timeout)
        evaluator._text(context, "context", 4096)
        evaluator._text(time, "time", 512)
        if budget is None:
            budget = evaluator.EvaluationBudget()
        if type(budget) is not evaluator.EvaluationBudget:
            raise evaluator.InvalidRequest("budget must use installed EvaluationBudget")
        # Recheck its values at consumption, even if a caller bypassed frozen
        # dataclass assignment. Preserve all requested budgets in the result.
        budget = evaluator.EvaluationBudget(**vars(budget))
        result["budget"] = {**vars(budget), "native_timeout_seconds": timeout}
        result["input_binding"] = {
            "source_id": source_id, "revision": revision, "scope": scope,
            "source_text": raw.decode("utf-8"), "query_text": query.decode("utf-8"),
            "context": context, "time": time,
        }
        plan = _plan(plan)
        result["plan"] = plan
        # Validate only the plan's structural profile before native work. With
        # no hypotheses or bridge, this provisional target supplies an inert
        # atom type to the existing validator; it is never evaluated or emitted.
        preflight = _request(plan, result["input_binding"], plan["requirements"][0]["atom"], None)
        _, exhausted = evaluator._validate(preflight, budget)
        if exhausted:
            return _stop(result, "RESOURCE_EXHAUSTED", exhausted)
        answer = pilot.answer(raw, query, identity=source_id, revision=revision,
                              scope=scope, checker=checker, timeout=timeout, answer_version="v2")
        result["source_answer"] = answer
        checked_path = pilot.checker_path(checker)
        semantic_path = _probe_path(semantic_probe)
        checker_hash = answer["verification"]["checker_sha256"]
        probe_hash = _fingerprint(semantic_path)
        result["native_checkers"] = {
            "verified_reading_sha256": checker_hash,
            "classical_semantic_probe_sha256": probe_hash,
        }
        if _fingerprint(checked_path) != checker_hash:
            return _stop(result, "VERIFICATION_UNAVAILABLE", "CHECKER_CHANGED")

        certificate = answer["analysis_certificate"]["kernel_certificate"]
        conclusion = deepcopy(certificate["query"])
        requirements = deepcopy(plan["requirements"])
        request = _request(plan, result["input_binding"], conclusion, certificate["known"])
        row = request["readings"][0]
        result["conditional_request"] = request
        result["source_witnesses"]["requirements"] = _witnesses(answer, requirements)

        # Reuse the existing owner's structural checks before looking up source
        # references. A complete source never excuses a malformed policy plan.
        _, exhausted = evaluator._validate(request, budget)
        if exhausted:
            return _stop(result, "RESOURCE_EXHAUSTED", exhausted)
        bridge = _clause(answer, plan["bridge_clause"])
        if bridge is not None:
            clause = bridge["clause"]
            if (clause["body"] != [r["atom"] for r in requirements]
                    or clause["head"] != conclusion):
                raise evaluator.InvalidRequest("source bridge body/head differs from exact requirements/query")
            result["source_witnesses"]["bridge"] = bridge
            # The legacy owner accepts this explicit transcript basis only.
            # The outer envelope separately retains the checked source rule;
            # this inner label is not evidence of Arabic role classification.
            row["bridge"] = {"body": deepcopy(clause["body"]), "head": deepcopy(clause["head"]),
                             "basis": "caller_assumption"}
        if plan["policy_id"] == "opposition":
            necessary = _clause(answer, plan["necessary_clause"])
            if necessary is not None:
                clause = necessary["clause"]
                premise = next(r["atom"] for r in requirements if r["slot"] == "premise")
                if len(clause["body"]) != 1 or not evaluator.opposition_shape(
                        clause["body"][0], clause["head"], premise, conclusion):
                    raise evaluator.InvalidRequest("necessary source rule must be Q -> P with not P and target not Q")
                result["source_witnesses"]["necessary_relation"] = necessary
                row["necessary_relation"] = {"kind": "necessary", "antecedent": deepcopy(clause["body"][0]),
                    "consequent": deepcopy(clause["head"]), "basis": "caller_assumption"}
        validated, exhausted = evaluator._validate(request, budget)
        if exhausted:
            return _stop(result, "RESOURCE_EXHAUSTED", exhausted)

        normalized = validated["readings"][0]
        known = {ground.key(a) for a in certificate["known"]}
        clean = {ground.key(a) for a in certificate["clean_known"]}
        guard = evaluator.guard_verdict(evaluator.KINDS.get(plan["policy_id"], "direct"),
                                        normalized["requirements"], normalized["hypotheses"])
        could_derive = (guard == "SUPPORTED_PREMISES" and row["bridge"] is not None
                        and (plan["policy_id"] != "opposition" or row["necessary_relation"] is not None)
                        and not (plan["policy_id"] == "opposition"
                                 and plan["contrast_kind"] in {"name", "innama"})
                        and ground.opposite(ground.key(conclusion)) not in known)
        if could_derive:
            if any(ground.key(r["atom"]) in known and ground.key(r["atom"]) not in clean
                   for r in requirements):
                return _stop(result, "DEFER", "CONTESTED_SOURCE_PREMISE")
            if ground.key(conclusion) in known and ground.key(conclusion) not in clean:
                return _stop(result, "DEFER", "CONTESTED_SOURCE_CONCLUSION")

        conditional = evaluator.evaluate(request, budget=budget, root=root,
            checker=checked_path, semantic_probe=semantic_path, timeout=timeout)
        result["conditional_result"] = conditional
        if (_fingerprint(checked_path) != checker_hash
                or _fingerprint(semantic_path) != probe_hash):
            return _stop(result, "VERIFICATION_UNAVAILABLE", "CHECKER_CHANGED")
        result.update(status=conditional["status"], reason=conditional.get("reason"),
                      conditional_consequence=conditional["conditional_consequence"])
        return result
    except pilot.PilotError as error:
        if error.code == "RESOURCE_LIMIT":
            status = "RESOURCE_EXHAUSTED"
        elif error.code in {"CHECKER_UNAVAILABLE", "CHECKER_CHANGED", "CHECKER_PROTOCOL_ERROR"}:
            status = "VERIFICATION_UNAVAILABLE"
        elif error.code == "OUTSIDE_VERIFIED_LANGUAGE":
            status = "OUTSIDE_VERIFIED_LANGUAGE"
        else:
            status = "INVALID"
        return _stop(result, status, error.code)
    except evaluator.InvalidRequest as error:
        return _stop(result, "INVALID", str(error))
    except (ValueError, TypeError, KeyError, RecursionError, UnicodeError):
        return _stop(result, "INVALID", "INVALID_SOURCE_BOUND_INPUT")
    except OSError:
        return _stop(result, "SOURCE_ERROR", "SOURCE_OR_CHECKER_UNAVAILABLE")
