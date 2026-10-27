"""Compose installed acquisition with PR 34's original-source inference law.

This adapter adds no grammar and trusts no caller-provided receipts. Each
native checker reopens the original bytes under the same discourse binding.
An incomplete representation never inherits the inference layer's authority.
"""
from __future__ import annotations

from dataclasses import asdict
import json

from tools import aligned_acquisition as acquisition
from tools.licensed_inference import runtime as inference

LAW_ID = "nabt.acquired-inference.v1"
MAX_REPORT_BYTES = 20 * 1024 * 1024


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _base():
    return {"schema": "nabt.acquired-inference-result.v1", "law_id": LAW_ID,
            "status": "DEFER", "verified": False, "chain_complete": False,
            "authority": "NO_COMPOSITE_AUTHORITY", "answer": None,
            "source_acquisition": None, "query_acquisition": None,
            "licensed_inference": None, "gates": {}, "blocked_by": [],
            "world_truth_established": False, "all_arabic_complete": False,
            "python_lean_composition_theorem": False}


def _metadata(value):
    if (type(value) is not str or not value or len(value) > 512 or
            any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value)):
        raise ValueError("invalid independent metadata")
    value.encode("utf-8", "strict")


def _shapes(report):
    rows = report["shape_handoffs"]
    return bool(rows) and all(row["status"] == "SHAPE_LICENSED" for row in rows)


def evaluate(source, query, *, source_id="input", revision="1", scope="default",
             time="unspecified", source_ending="wasl", query_ending="wasl", budget=None):
    result = _base()
    try:
        for value in (source_id, revision, scope, time):
            _metadata(value)
        if budget is None:
            budget = inference.InferenceBudget()
        if type(budget) is not inference.InferenceBudget:
            raise ValueError("budget must be the existing InferenceBudget")
        native_scope = wire({"scope": scope, "time": time})
        _metadata(native_scope)
    except (ValueError, UnicodeError):
        return {**result, "status": "INVALID_INPUT", "blocked_by": ["INVALID_BINDING_OR_BUDGET"]}
    result["binding"] = {"source_id": source_id, "revision": revision, "scope": scope,
                         "time": time, "native_scope": native_scope,
                         "source_ending": source_ending, "query_ending": query_ending}
    result["budget"] = asdict(budget)
    binding = {"source_id": source_id, "revision": revision, "scope": native_scope}
    source_report = acquisition.read_acquired(source, **binding, ending=source_ending)
    query_report = acquisition.read_acquired(query, **binding, ending=query_ending)
    result.update(source_acquisition=source_report, query_acquisition=query_report)
    for role, report in (("SOURCE", source_report), ("QUERY", query_report)):
        if report["verified"] is not True or report["status"] == "INVALID_INPUT":
            result.update(status=report["status"], blocked_by=[role + "_ACQUISITION:" + report["status"]])
            return result
    # Use original inputs, never expanded cells, reconstructed spelling or the
    # old word reader's proposed semantics. PR 34 owns its reading/closure law.
    licensed = inference.evaluate(source, query, source_id=source_id, revision=revision,
                                   scope=scope, time=time, budget=budget)
    result["licensed_inference"] = licensed
    gates = {"source_acquired": source_report["status"] == "ACQUIRED",
             "query_acquired": query_report["status"] == "ACQUIRED",
             "source_shapes": _shapes(source_report), "query_shapes": _shapes(query_report),
             "reading_and_closures": licensed["verified"] is True and
                 licensed["native_checked"] is True and licensed["closures_checked"] is True}
    # Check every common identity, including the exact source/query and the
    # canonical scope/time, before joining evidence from the two native laws.
    native = licensed.get("native_result", {})
    gates["same_binding"] = (gates["reading_and_closures"] and
        native.get("source_text") == source_report["acquisition"]["text"] and
        native.get("query_text") == query_report["acquisition"]["text"] and
        native.get("source_id") == source_id and native.get("revision") == revision and
        native.get("source_scope") == native_scope)
    result["gates"] = gates
    result["blocked_by"] = [key for key, passed in gates.items() if not passed]
    if all(gates.values()):
        result.update(status=licensed["status"], verified=True, chain_complete=True,
                      authority="SOURCE_BOUND_ACQUISITION_AND_SOURCE_RELATIVE_CONSEQUENCE",
                      answer={"status": licensed["status"], "aggregate": licensed["aggregate"]})
    elif licensed["status"] in {"INVALID_INPUT", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE",
                                 "RESOURCE_EXHAUSTED"}:
        result["status"] = licensed["status"]
    elif any(row["status"] == "RESOURCE_EXHAUSTED" for report in (source_report, query_report)
             for row in report["shape_handoffs"]):
        result["status"] = "RESOURCE_EXHAUSTED"
    elif any(row["status"] == "SHAPE_CHECK_FAILED" for report in (source_report, query_report)
             for row in report["shape_handoffs"]):
        result["status"] = "VERIFICATION_UNAVAILABLE"
    return result


def verify(report, *, source, query, source_id, revision, scope, time,
           source_ending, query_ending, budget=None):
    """Only a complete exact replay is an accepted composed certificate."""
    try:
        if type(report) is not dict:
            raise ValueError("receipt must be an object")
        encoded = wire(report).encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            return {"valid": False, "status": "RESOURCE_EXHAUSTED"}
        expected = evaluate(source, query, source_id=source_id, revision=revision,
                            scope=scope, time=time, source_ending=source_ending,
                            query_ending=query_ending, budget=budget)
        if encoded != wire(expected).encode("utf-8"):
            raise ValueError("whole receipt differs from independent replay")
        return {"valid": expected["chain_complete"], "replay_matches": True,
                "status": "VERIFIED_COMPOSITE_RECEIPT" if expected["chain_complete"] else expected["status"],
                "blocked_by": expected["blocked_by"]}
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"valid": False, "replay_matches": False, "status": "INVALID_RECEIPT"}
