"""Join v2 citation acquisition to unchanged PR34 original-source inference.

Only complete, independently checked readings and shape handoffs confer joined
authority. New acquisition spellings never become aliases in PR34's language.
"""
from __future__ import annotations

from dataclasses import asdict

from tools import acquired_inference as v1
from tools import aligned_acquisition_v2 as acquisition
from tools.licensed_inference import runtime as inference

LAW_ID = "nabt.acquired-inference.v2"
MAX_REPORT_BYTES = v1.MAX_REPORT_BYTES
wire = v1.wire


def _base():
    # This is only an unverified empty envelope, never a relabelled v1 result.
    return {**v1._base(), "schema": "nabt.acquired-inference-result.v2", "law_id": LAW_ID}


def evaluate(source, query, *, source_id="input", revision="1", scope="default",
             time="unspecified", source_ending="wasl", query_ending="wasl",
             onset="word_initial", budget=None):
    result = _base()
    try:
        for value in (source_id, revision, scope, time):
            v1._metadata(value)
        for ending in (source_ending, query_ending):
            if type(ending) is not str or ending not in ("wasl", "waqf"):
                raise ValueError("invalid ending")
        if type(onset) is not str or onset not in ("word_initial", "connected"):
            raise ValueError("invalid onset")
        if budget is None:
            budget = inference.InferenceBudget()
        if type(budget) is not inference.InferenceBudget:
            raise ValueError("budget must be the existing InferenceBudget")
        # Recheck fields even if an object was forged around its frozen dataclass.
        budget = inference.InferenceBudget(**asdict(budget))
        native_scope = wire({"scope": scope, "time": time})
        v1._metadata(native_scope)
    except (ValueError, UnicodeError, TypeError):
        return {**result, "status": "INVALID_INPUT", "blocked_by": ["INVALID_BINDING_OR_BUDGET"]}
    result["binding"] = {"source_id": source_id, "revision": revision, "scope": scope,
                         "time": time, "native_scope": native_scope, "onset": onset,
                         "source_ending": source_ending, "query_ending": query_ending}
    result["budget"] = asdict(budget)
    binding = {"source_id": source_id, "revision": revision, "scope": native_scope, "onset": onset}
    source_report = acquisition.read_acquired(source, **binding, ending=source_ending)
    query_report = acquisition.read_acquired(query, **binding, ending=query_ending)
    result.update(source_acquisition=source_report, query_acquisition=query_report)
    for role, report in (("SOURCE", source_report), ("QUERY", query_report)):
        if report["verified"] is not True or report["status"] == "INVALID_INPUT":
            result.update(status=report["status"], blocked_by=[role + "_ACQUISITION:" + report["status"]])
            return result
    licensed = inference.evaluate(source, query, source_id=source_id, revision=revision,
                                   scope=scope, time=time, budget=budget)
    result["licensed_inference"] = licensed
    gates = {"source_acquired": source_report["status"] == "ACQUIRED",
             "query_acquired": query_report["status"] == "ACQUIRED",
             "source_shapes": v1._shapes(source_report), "query_shapes": v1._shapes(query_report),
             "reading_and_closures": licensed["verified"] is True and
                 licensed["native_checked"] is True and licensed["closures_checked"] is True,
             "same_onset": onset == "word_initial" and
                 all(report["onset"] == onset and report["acquisition"]["onset"] == onset
                     for report in (source_report, query_report))}
    native = licensed.get("native_result", {})
    gates["same_binding"] = (gates["reading_and_closures"] and
        native.get("source_text") == source_report["acquisition"]["text"] and
        native.get("query_text") == query_report["acquisition"]["text"] and
        native.get("source_id") == source_id and native.get("revision") == revision and
        native.get("source_scope") == native_scope and
        all(report["acquisition"]["source_id"] == source_id and
            report["acquisition"]["revision"] == revision and
            report["acquisition"]["scope"] == native_scope and
            report["acquisition"]["ending"] == ending
            for report, ending in ((source_report, source_ending), (query_report, query_ending))))
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
           source_ending, query_ending, onset, budget=None):
    """An exact incomplete receipt may replay, but is never a completed chain."""
    try:
        if type(report) is not dict:
            raise ValueError("receipt must be an object")
        encoded = acquisition._receipt_wire(report)
        if len(encoded) > MAX_REPORT_BYTES:
            return {"valid": False, "status": "RESOURCE_EXHAUSTED"}
        expected = evaluate(source, query, source_id=source_id, revision=revision,
                            scope=scope, time=time, source_ending=source_ending,
                            query_ending=query_ending, onset=onset, budget=budget)
        if encoded != wire(expected).encode("utf-8"):
            raise ValueError("whole receipt differs from independent replay")
        return {"valid": expected["chain_complete"], "replay_matches": True,
                "status": "VERIFIED_COMPOSITE_RECEIPT" if expected["chain_complete"] else expected["status"],
                "blocked_by": expected["blocked_by"]}
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"valid": False, "replay_matches": False, "status": "INVALID_RECEIPT"}
