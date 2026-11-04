"""A replayable lesson coordinator over installed NABT learning/checking owners.

It selects the next teaching obligation from observed receipts. It does not
invent examples, grant expertise, call a model, or accept caller scoring labels.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from tools import evidence_lifecycle_v1 as wire_owner
from tools import source_learning_connection, epistemic_measurement
from tools.mantuq_inference import source_bound
from . import reasoning_curriculum as curriculum

SCHEMA = "nabt.cognitive-lesson.v1"
RESULT_SCHEMA = "nabt.cognitive-lesson-result.v1"
ADAPTERS = {"source_learning", "qualified_inference", "epistemic_ledger"}
MAX_RESULT_BYTES = 16 * 1024 * 1024


def _fields(value, names, label):
    wire_owner._fields(value, names, label)


def _identity():
    paths = ("tools/lexical_training/teaching.py", "tools/lexical_training/reasoning_curriculum.py",
             curriculum.REVIEW)
    return {p: hashlib.sha256((curriculum.ROOT / p).read_bytes()).hexdigest() for p in paths}


def _validate(lesson):
    wire_owner._encoded(lesson, wire_owner.MAX_REQUEST_BYTES)
    _fields(lesson, ("schema", "lesson_id", "domain_id", "matrix_id", "adapter", "payload"), "lesson")
    if lesson["schema"] != SCHEMA:
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
    if lesson["adapter"] not in domains[lesson["domain_id"]][2]:
        raise ValueError("Adapter authority does not transfer to this domain")
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
    if not measured:
        return {"action": "RESOLVE_OWNER_OBLIGATION", "basis": "/owner_result/status"}
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
    return {"action": "ASSESS_CONTRAST_AND_WITHDRAWAL", "basis": "/owner_result/status"}


def run_lesson(lesson):
    result = {"schema": RESULT_SCHEMA, "status": "INVALID_INPUT", "request": None,
              "execution_measured": False, "owner_result": None, "measurements": None,
              "next_step": None, "curriculum_identity": _identity(),
              "limits": {"matrix_complete": False, "domain_expertise_certified": False,
                         "world_truth_established": False, "action_authority": "NONE",
                         "general_python_lean_refinement": False,
                         "teacher_kind": "DETERMINISTIC_RECEIPT_DRIVEN_COORDINATOR",
                         "neural_training_performed": False}}
    try:
        matrix = _validate(lesson)
        result["request"] = deepcopy(lesson)
        if lesson["adapter"] not in matrix[3]:
            result.update(status="DEFER", next_step={"action": "IMPLEMENT_ACQUISITION_CONTRACT",
                          "obligation_ar": matrix[4]})
            return result
        payload, adapter = lesson["payload"], lesson["adapter"]
        if adapter == "source_learning":
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
            if type(policy) is not str or lesson["matrix_id"] not in curriculum.POLICY_MATRICES.get(policy, set()):
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
            measured = owner["native_checked"] is True and owner["certificate_checked"] is True
            measurements = {"mode": "EPISTEMIC_LEDGER_REPLAY", "learner_trained": False,
                            "evidence_class": owner["evidence_class"],
                            "trace_pointer": "/owner_result/execution"}
        result.update(status=owner["status"], execution_measured=measured, owner_result=owner,
                      measurements=measurements, next_step=_next(owner, adapter, measured))
        if result["curriculum_identity"] != _identity():
            raise ValueError("Curriculum changed during execution")
        wire_owner._encoded(result, MAX_RESULT_BYTES)
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
        matches = wire_owner._encoded(report, MAX_RESULT_BYTES) == wire_owner._encoded(actual, MAX_RESULT_BYTES)
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
