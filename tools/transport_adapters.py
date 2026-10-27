"""Fresh fixed adapters for legacy transports; imported flags grant no authority."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256

from nabt import foundation
from nabt.transport_contract import _canonical
from tools.licensed_inference import runtime


def _digest(value):
    return sha256(_canonical(value)[1]).hexdigest()


def certify_inference(source, query, *, source_id="user_text", revision="1",
                      scope="default", time="unspecified", budget=None):
    """Check raw source/query through the installed finite grammar and native child.

    The claim is source-relative finite inference, never a claim about intended
    sense, historical testimony, causal truth, or unrestricted Arabic.
    """
    foundation.require_foundation("tools.transport_adapters.certify_inference")
    out = {"schema": "nabt.scoped-source-inference.v1", "claims": [],
           "native_checked": False, "strict_language_accepted": False,
           "world_truth_established": False, "all_arabic_complete": False,
           "intended_sense_established": False}
    try:
        if budget is None:
            limits = runtime.InferenceBudget()
        elif type(budget) is dict:
            if set(budget) - set(runtime.InferenceBudget.__dataclass_fields__):
                raise ValueError("UNKNOWN_INFERENCE_BUDGET_FIELD")
            limits = runtime.InferenceBudget(**budget)
        else:
            raise ValueError("budget must be an explicit JSON object")
        source_raw, source_text = runtime._bytes(source, "source", limits.max_source_bytes)
        query_raw, query_text = runtime._bytes(query, "query", limits.max_query_bytes)
        for name, value in dict(source_id=source_id, revision=revision, scope=scope, time=time).items():
            runtime._metadata(value, name)
    except OverflowError as error:
        return {**out, "status": "RESOURCE_EXHAUSTED", "reason": str(error)}
    except (TypeError, ValueError, UnicodeError) as error:
        return {**out, "status": "INVALID_INPUT", "reason": str(error)}
    request = dict(source=source_text, query=query_text, source_id=source_id,
                   revision=revision, scope=scope, time=time, budget=asdict(limits))
    out["request"] = request
    out["request_sha256"] = _digest(request)
    try:
        result = runtime.evaluate(source_raw, query_raw, source_id=source_id,
            revision=revision, scope=scope, time=time, budget=limits)
        out["legacy_result"] = result
        out["status"] = result["status"]
        if result.get("native_checked") is not True:
            return out
        expected_source = {"source_id": source_id, "revision": revision,
            "raw_text": source_text, "bytes": len(source_raw), "sha256": sha256(source_raw).hexdigest()}
        expected_query = {"raw_text": query_text, "bytes": len(query_raw),
                          "sha256": sha256(query_raw).hexdigest()}
        native_scope = runtime.wire({"scope": scope, "time": time})
        expected_binding = dict(source_id=source_id, revision=revision, scope=scope,
            time=time, native_scope=native_scope, authority="EXPLICIT_DISCOURSE_BINDING")
        proposal = result["proposal"]
        readings = proposal["readings"]
        if type(readings) is not list or not readings:
            raise ValueError("NONEMPTY_CHECKED_READINGS_REQUIRED")
        expected_proposal = {"law_id": runtime.LAW_ID,
            "source": dict(identity=source_id, revision=revision, scope=native_scope, text=source_text),
            "query_text": query_text, "readings": readings}
        native = runtime._expected_success(expected_proposal)
        required = dict(runtime._base(), schema="nabt.licensed-inference-result.v1", law_id=runtime.LAW_ID,
            authority=runtime.AUTHORITY, verified=True, native_checked=True,
            all_readings_complete=True, closures_checked=True,
            parse_status="CHECKED_COMPLETE_READING", parse_reason=None,
            all_arabic_complete=False, world_truth_established=False,
            premise_world_truth_established=False, source_interpretation_historically_proved=False,
            source=expected_source, query=expected_query, binding=expected_binding,
            proposal=expected_proposal, native_result=native, status=native["status"],
            readings=native["rows"], closure_records=readings, aggregate=native["aggregate"])
        if any(_canonical(result.get(key)) != _canonical(value) for key, value in required.items()):
            raise ValueError("EXACT_NATIVE_SOURCE_INFERENCE_POSTCONDITION_MISMATCH")
        out["native_checked"] = True
        out["claims"] = [{"kind": "SOURCE_BOUND_FINITE_INFERENCE",
            "scope": "Exact source/query and complete readings of nabt.explicit-subject-active.v1; source assertions remain premises, not world observations.",
            "proof": {"law_id": runtime.LAW_ID,
                "theorems": ["Nabt.LicensedInference.source_read_exact",
                    "Nabt.LicensedInference.query_read_exact", "Nabt.LicensedInference.verified_execution",
                    "Nabt.LicensedInference.execution_entails"],
                "request_sha256": out["request_sha256"],
                "proposal_sha256": _digest(proposal), "native_result_sha256": _digest(native)},
            "status": native["status"], "aggregate": native["aggregate"],
            "assumptions": result["assumptions"]}]
    except (OSError, TypeError, ValueError, KeyError, IndexError, UnicodeError) as error:
        out.update(status="VERIFICATION_UNAVAILABLE", reason=str(error), native_checked=False, claims=[])
    return out
