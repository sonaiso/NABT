"""A replayable lesson coordinator over installed NABT learning/checking owners.

It selects the next teaching obligation from observed receipts. Versioned neural
observations preserve the owner's decision; no caller scoring label grants authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from tools import evidence_lifecycle_v1 as wire_owner
from tools import source_learning_connection, epistemic_measurement
from tools.mantuq_inference import source_bound
from . import grounded_passage
from . import reasoning_curriculum as curriculum
from tools.grammar_catalog import temporal

SCHEMA = "nabt.cognitive-lesson.v1"
SCHEMA_V2 = "nabt.cognitive-lesson.v2"
SCHEMA_V3 = "nabt.cognitive-lesson.v3"
SCHEMA_V4 = "nabt.cognitive-lesson.v4"
RESULT_SCHEMA = "nabt.cognitive-lesson-result.v1"
ADAPTERS = set(curriculum.SHARED_ADAPTERS)
MAX_RESULT_BYTES = 16 * 1024 * 1024


def _fields(value, names, label):
    wire_owner._fields(value, names, label)


def _identity(adapter=None, shared=False, contextual=False, graph=False):
    paths = ("tools/lexical_training/teaching.py", "tools/lexical_training/reasoning_curriculum.py",
             curriculum.REVIEW)
    if shared:
        paths += ("tools/lexical_training/concepts.py", "tools/lexical_training/shared_encoder.py",
                  "evidence/shared_cognition_v1/model.json", "evidence/lexical_denotation/catalog.json",
                  "formal/.lake/build/bin/lexicalDenotation")
    if adapter == "grounded_passage":
        paths += ("tools/lexical_training/grounded_passage.py", "formal/GroundedPassageMain.lean",
                  "formal/Nabt/GroundedPassage.lean",
                  "tools/connected_acquisition_v3.py")
    if adapter == "temporal_context":
        paths += ("tools/grammar_catalog/temporal.py", "formal/TemporalContextProbe.lean",
                  "formal/Nabt/TemporalContext.lean")
    optional_resources = {"evidence/shared_cognition_v1/model.json", "formal/.lake/build/bin/lexicalDenotation"}
    if contextual:
        paths += ("tools/lexical_training/contextual_alignment.py",
                  "evidence/contextual_alignment_v1/model.json", "evidence/contextual_alignment_v1/train.json")
        optional_resources.update(("evidence/contextual_alignment_v1/model.json", "evidence/contextual_alignment_v1/train.json"))
    identity = {p: ("UNAVAILABLE" if p in optional_resources and not (curriculum.ROOT / p).is_file()
                else hashlib.sha256((curriculum.ROOT / p).read_bytes()).hexdigest()) for p in paths}
    if graph:
        from tools.grammar_catalog.gateway import snapshot, digest
        identity["cognitive_graph_snapshot"] = digest(snapshot())
    return identity


def _validate(lesson):
    wire_owner._encoded(lesson, wire_owner.MAX_REQUEST_BYTES)
    _fields(lesson, ("schema", "lesson_id", "domain_id", "matrix_id", "adapter", "payload"), "lesson")
    if lesson["schema"] not in (SCHEMA, SCHEMA_V2, SCHEMA_V3, SCHEMA_V4):
        raise ValueError("Unknown lesson schema")
    wire_owner._text(lesson["lesson_id"], "lesson_id", 128)
    for key in ("domain_id", "matrix_id", "adapter"):
        wire_owner._text(lesson[key], key, 128)
    domains = {r[0]: r for r in curriculum.DOMAINS}
    matrices = {r[0]: r for r in curriculum.MATRICES}
    if lesson["domain_id"] not in domains or lesson["matrix_id"] not in matrices:
        raise ValueError("Unknown domain or matrix")
    if lesson["adapter"] not in ADAPTERS or type(lesson["payload"]) is not dict:
        raise ValueError("Unknown adapter or malformed payload")
    # A domain selects the teaching context, not the authority of a premise.
    # Matrix/policy compatibility and the existing owner still check the proof.
    return matrices[lesson["matrix_id"]]


def _learning_measurements(owner):
    history = owner.get("history", [])
    return {"mode": "FINITE_SOURCE_SUPERVISED_GUARD_LEARNING",
            "steps": [{"step": h["step"], "status": h["status"],
                       "surviving_candidates": h["learning"].get("survivor_count"),
                       "ready_observations": sum(r["ready"] for r in h["learning"].get("observations", [])),
                       "pending_observations": len(h["learning"].get("pending", [])),
                       "application_established": h["learning"]["application_established"],
                       "support_count": len(h["support_ids"]),
                       "refutation_count": len(h["refutation_ids"]),
                       "trace_pointer": "/owner_result/history/" + str(i)}
                      for i, h in enumerate(history)],
            "held_out_generalization_measured": False,
            "sample_generalization_authorized": False}


def _next(owner, adapter, measured):
    if adapter == "temporal_context":
        if owner["status"] == "DEFER":
            return {"action": "RESTORE_NATIVE_CHECKER", "basis": "/owner_result/native_receipt"}
        if owner["status"] == "CONFLICT":
            return {"action": "REVIEW_TEMPORAL_PREMISES", "basis": "/owner_result/relations"}
        if owner["status"] in ("UNKNOWN", "PARTIAL"):
            return {"action": "ACQUIRE_TEMPORAL_ANCHOR_OR_DISAMBIGUATION", "basis": "/owner_result/nodes"}
    if not measured:
        return {"action": "RESOLVE_OWNER_OBLIGATION", "basis": "/owner_result/status"}
    if adapter == "grounded_passage":
        missing = [key for key, answer in owner["answers"].items() if answer["status"] == "UNKNOWN"]
        if missing:
            return {"action": "ACQUIRE_PASSAGE_EVIDENCE", "questions": missing, "basis": "/owner_result/answers"}
    if adapter == "source_learning":
        last = owner["history"][-1]["learning"]
        pointer = "/owner_result/history/" + str(len(owner["history"]) - 1) + "/learning"
        if last.get("pending"):
            return {"action": "ACQUIRE_MISSING_OR_CONFLICTING_OBSERVATION", "basis": pointer + "/pending"}
        if last.get("survivor_count") == 0:
            return {"action": "REVIEW_DECLARED_HYPOTHESIS_LANGUAGE", "basis": pointer + "/survivor_count"}
        if last.get("survivor_count", 0) > 1:
            return {"action": "SEEK_DISCRIMINATING_COUNTEREXAMPLE", "basis": pointer + "/survivor_count"}
        if not last["application_established"]:
            return {"action": "ACQUIRE_ADOPTION_AND_CASE_WITNESSES", "basis": pointer + "/application_established"}
        return {"action": "ASSESS_INDEPENDENT_NEW_OCCURRENCE", "basis": pointer + "/application_established"}
    if adapter == "qualified_inference" and owner["status"] == "UNKNOWN":
        readings = (owner["conditional_result"] or {}).get("readings", [])
        if (len(readings) == 1 and readings[0].get("reason") == "BRIDGE_MISSING"
                and not readings[0].get("conclusion_counterevidence")):
            return {"action": "ACQUIRE_SOURCE_BOUND_RELATION",
                    "basis": "/owner_result/conditional_result/readings/0/reason"}
    return {"action": "ASSESS_CONTRAST_AND_WITHDRAWAL", "basis": "/owner_result/status"}


def run_lesson(lesson):
    # Choose from installed identity sets before validation; freeze once.
    adapter = lesson.get("adapter") if type(lesson) is dict else None
    shared = type(lesson) is dict and lesson.get("schema") in (SCHEMA_V2, SCHEMA_V3, SCHEMA_V4)
    contextual = type(lesson) is dict and lesson.get("schema") in (SCHEMA_V3, SCHEMA_V4)
    graph = type(lesson) is dict and lesson.get("schema") == SCHEMA_V4
    result = {"schema": RESULT_SCHEMA, "status": "INVALID_INPUT", "request": None,
              "routing_policy_id": curriculum.ROUTING_POLICY,
              "execution_measured": False, "owner_result": None, "measurements": None,
              "next_step": None, "curriculum_identity": _identity(adapter, shared, contextual, graph),
              "limits": {"matrix_complete": False, "domain_expertise_certified": False,
                         "world_truth_established": False, "action_authority": "NONE",
                         "empirical_causality_established": False,
                         "domain_label_grants_authority": False,
                         "general_python_lean_refinement": False,
                         "teacher_kind": "DETERMINISTIC_RECEIPT_DRIVEN_COORDINATOR",
                         "neural_training_performed": False}}
    try:
        matrix = _validate(lesson)
        result["request"] = deepcopy(lesson)
        v2 = lesson["schema"] in (SCHEMA_V2, SCHEMA_V3, SCHEMA_V4)
        if v2:
            result["schema"] = "nabt.cognitive-lesson-result.v3" if contextual else "nabt.cognitive-lesson-result.v2"
            if graph:
                result["schema"] = "nabt.cognitive-lesson-result.v4"
            result["routing_policy_id"] = "nabt.operation-evidence-routing.v3"
            result["view_role"] = "CURRICULUM_VIEW_NOT_OPERATION_OR_CONCEPT_IDENTITY"
        if not v2 and lesson["adapter"] not in matrix[3]:
            result.update(status="DEFER", next_step={"action": "IMPLEMENT_ACQUISITION_CONTRACT",
                          "obligation_ar": matrix[4]})
            return result
        payload, adapter = lesson["payload"], lesson["adapter"]
        if adapter == "temporal_context":
            owner = temporal.evaluate(payload)
            measured = owner["native_checked"]
            measurements = {"mode": "SUPPLIED_TEMPORAL_PREMISES_NATIVE_REPLAY", "learner_trained": False,
                            "unknown_nodes": sum(not n["candidates"] for n in owner["nodes"]),
                            "trace_pointer": "/owner_result/relations"}
        elif adapter == "grounded_passage":
            owner = grounded_passage.evaluate(payload)
            measured = owner["native_checked"] and owner["acquisition_checks_available"]
            measurements = {"mode": "SOURCE_BOUND_SAMPLED_PASSAGE", "trace_pointer": "/owner_result/answers",
                            "learner_trained": False}
        elif adapter == "source_learning":
            owner = source_learning_connection.evaluate(payload)
            measured = owner.get("chain_complete") is True
            measurements = _learning_measurements(owner)
        elif adapter == "qualified_inference":
            _fields(payload, ("source_text", "query_text", "source_id", "revision", "scope",
                              "context", "time", "plan"), "qualified lesson payload")
            for key in ("source_text", "query_text", "source_id", "revision", "scope", "context", "time"):
                wire_owner._text(payload[key], key, 65536, content=True)
            if type(payload["plan"]) is not dict:
                raise ValueError("Source plan required")
            policy = payload["plan"].get("policy_id")
            if (type(policy) is not str or policy not in curriculum.POLICY_MATRICES
                    or (not v2 and lesson["matrix_id"] not in curriculum.POLICY_MATRICES[policy])):
                raise ValueError("Installed policy does not serve the requested matrix")
            owner = source_bound.evaluate_source(payload["source_text"].encode(), payload["query_text"].encode(),
                payload["plan"], **{k: payload[k] for k in ("source_id", "revision", "scope", "context", "time")})
            answer = owner.get("source_answer") or {}
            measured = bool(answer.get("verification", {}).get("native_receipt")) and owner["status"] in {
                "SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "DEFER"}
            measurements = {"mode": "SOURCE_RELATIVE_QUALIFIED_INFERENCE",
                            "role_assignment": "CALLER_PLAN_ONLY", "learner_trained": False,
                            "conditional_consequence": owner["conditional_consequence"],
                            "trace_pointer": "/owner_result/source_witnesses"}
        else:
            _fields(payload, ("source_profile", "input"), "epistemic payload")
            owner = epistemic_measurement.execute_request(payload["input"], source_profile=payload["source_profile"])
            measured = (owner["native_checked"] is True and owner["certificate_checked"] is True
                        and owner["status"] in {"SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN"})
            measurements = {"mode": "EPISTEMIC_LEDGER_REPLAY", "learner_trained": False,
                            "evidence_class": owner["evidence_class"],
                            "trace_pointer": "/owner_result/execution"}
        result.update(status=owner["status"], execution_measured=measured, owner_result=owner,
                      measurements=measurements, next_step=_next(owner, adapter, measured))
        if v2:
            # Retain the actual owner history and evidence, not a copied concept
            # per curriculum label. This key identifies an operation, not truth.
            operation = {"adapter": adapter, "payload": payload}
            result["episode"] = {
                "operation_sha256": hashlib.sha256(wire_owner.wire(operation).encode()).hexdigest(),
                "operation": operation, "owner_result_pointer": "/owner_result",
                "history_pointer": "/owner_result/history" if adapter == "source_learning" else None,
                "semantic_alignment": "OWNER_IDENTITIES_RETAINED_NO_NEW_LEXICAL_ALIGNMENT",
                "view": lesson["matrix_id"], "domain": lesson["domain_id"],
                "policy_id": payload.get("plan", {}).get("policy_id")}
            from .shared_encoder import observe_lesson
            if contextual:
                from .contextual_alignment import observe_lesson
                result["episode"]["semantic_alignment"] = "LEARNED_OCCURRENCE_PROPOSALS_WITH_SOURCE_AND_NATIVE_DEFINITION"
            if graph:
                from .cognitive_graph import observe_lesson
                result["episode"]["semantic_alignment"] = "SHARED_ENCODER_SIGN_AND_CONCEPT_GRAPH_VIEWS"
            result["episode"]["neural_observation"] = observe_lesson(adapter, payload)
        if result["curriculum_identity"] != _identity(adapter, shared, contextual, graph):
            raise ValueError("Curriculum changed during execution")
        wire_owner._encoded(result, MAX_RESULT_BYTES, floats=shared)
    except wire_owner.ResourceLimit as error:
        result.update(status="RESOURCE_LIMIT", execution_measured=False, error=str(error),
                      owner_result=None, measurements=None, next_step=None)
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as error:
        result.update(status="INVALID_INPUT", execution_measured=False, error=str(error))
    # Normalize tuples from owner reports before replay comparisons or storage.
    return json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))


def verify_lesson(report, *, expected_lesson):
    """No receipt may supply its own inputs or suppress the fresh owner run."""
    try:
        actual = run_lesson(expected_lesson)
        shared = expected_lesson.get("schema") in (SCHEMA_V2, SCHEMA_V3, SCHEMA_V4)
        matches = (wire_owner._encoded(report, MAX_RESULT_BYTES, floats=shared) ==
                   wire_owner._encoded(actual, MAX_RESULT_BYTES, floats=shared))
        return {"valid": matches and actual["execution_measured"], "replay_matches": matches,
                "status": actual["status"] if matches else "INVALID_RECEIPT"}
    except (ValueError, TypeError, RecursionError):
        return {"valid": False, "replay_matches": False, "status": "INVALID_RECEIPT"}


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request", type=Path, required=True)
    p.add_argument("--verify", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    def read(path, maximum, *, report=False):
        with path.open("rb") as stream:
            return wire_owner.strict_loads(stream.read(maximum + 1), maximum_bytes=maximum, report=report)
    try:
        lesson = read(args.request, wire_owner.MAX_REQUEST_BYTES)
        report = (verify_lesson(read(args.verify, MAX_RESULT_BYTES, report=True), expected_lesson=lesson)
                  if args.verify else run_lesson(lesson))
    except wire_owner.ResourceLimit as error:
        report = {"status": "RESOURCE_LIMIT", "execution_measured": False, "error": str(error)}
    except (OSError, ValueError) as error:
        report = {"status": "INVALID_INPUT", "execution_measured": False, "error": str(error)}
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(json.dumps({"status": report["status"], "execution_measured": report.get("execution_measured"),
                          "valid": report.get("valid"), "report": str(args.output)}, ensure_ascii=False))
    else:
        print(text, end="")
    return 0 if report.get("execution_measured", report.get("valid", False)) else 3


if __name__ == "__main__":
    raise SystemExit(main())
