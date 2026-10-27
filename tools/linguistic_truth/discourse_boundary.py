"""Native bounded discourse boundaries with separately scoped cue diagnostics.

The first negation marker never becomes a premise denying the later cue.
Opaque text is preserved, not interpreted as an event. The later reader retains
its existing diagnostic authority; no alias or intended meaning is installed by
this envelope adapter.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from nabt import foundation
from nabt.errors import NabtError

_ROOT = Path(__file__).resolve().parents[2]
_EXECUTABLE = _ROOT / "formal/.lake/build/bin/discourseBoundaryCue"
_REVIEW = _ROOT / "evidence/discourse_boundary_v1/source_review.json"
_REVIEW_SHA = "8e32b13df1713c19b110874d40589b32391f108c69731989bf471b41c6d0cbd8"
_LAW = "nabt.discourse-boundary-cue.v1"
_SCHEMA = "nabt.discourse-boundary-receipt.v1"
_PATTERN = re.compile(
    r"\A(?P<negation_prefix>لم |لَمْ )(?P<denied_body>.+?)"
    r"(?P<boundary>؛ )(?P<conjunction>وَ|و)(?P<cue_prefix>أَقْصِدُ |أقصد )"
    r"(?P<cue_body>.+?)(?P<dot>\.)?\Z")
_FORBIDDEN = frozenset("«»\"“”‘’'`()[]{}:؛;.!?؟،,")


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _parse_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("DUPLICATE_DISCOURSE_RECEIPT_FIELD")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_DISCOURSE_RECEIPT")))


def _review():
    raw = _REVIEW.read_bytes()
    if sha256(raw).hexdigest() != _REVIEW_SHA:
        raise ValueError("DISCOURSE_REVIEW_CHANGED")
    value = _parse_json(raw)
    source_bytes = {}
    for row in value["sources"]:
        path = (_ROOT / row["path"]).resolve()
        if not path.is_relative_to(_ROOT.resolve()):
            raise ValueError("DISCOURSE_SOURCE_OUTSIDE_ROOT")
        data = path.read_bytes()
        if sha256(data).hexdigest() != row["sha256"] or len(data) != row["bytes"]:
            raise ValueError("DISCOURSE_SOURCE_CHANGED")
        source_bytes[row["id"]] = data
    for row in value["passages"]:
        data = source_bytes[row["source_id"]]
        start, end = row["start_byte"], row["end_byte"]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(data):
            raise ValueError("DISCOURSE_PASSAGE_BOUNDS")
        part = data[start:end]
        if part != row["quote"].encode("utf-8") or sha256(part).hexdigest() != row["sha256"]:
            raise ValueError("DISCOURSE_PASSAGE_CHANGED")
    return value


def _projection(text):
    value = foundation.inspect_source(text)
    return {"status": "INCOMPLETE" if value["status"] == "PARTIAL" else value["status"],
            **{key: value[key] for key in ("alphabet_id", "number_domain", "cells", "number")}}


def _plain(text):
    return (bool(text) and text == text.strip(" \t\r\n\v\f")
            and all(ord(char) >= 32 and char not in _FORBIDDEN for char in text))


def _expected(request):
    text = request["source"]["text"]
    projection = _projection(text)
    envelope = None
    match = _PATTERN.fullmatch(text)
    if match is not None and projection["status"] != "INVALID":
        row = match.groupdict()
        paired_cue = ((row["conjunction"] == "وَ") == (row["cue_prefix"] == "أَقْصِدُ "))
        if paired_cue and _plain(row["denied_body"]) and _plain(row["cue_body"]):
            denied_start = len(row["negation_prefix"].encode("utf-8"))
            denied_end = denied_start + len(row["denied_body"].encode("utf-8"))
            cue_start = denied_end + len((row["boundary"] + row["conjunction"]).encode("utf-8"))
            cue_text = row["cue_prefix"] + row["cue_body"]
            envelope = {key: row[key] for key in ("negation_prefix", "denied_body", "boundary",
                                                  "conjunction", "cue_prefix", "cue_body")}
            envelope.update(denied_start_byte=denied_start, denied_end_byte=denied_end,
                cue_text=cue_text, cue_start_byte=cue_start,
                cue_end_byte=cue_start + len(cue_text.encode("utf-8")),
                full_stop=bool(row["dot"]), projects_denied_to_positive=False)
    return {"schema": _LAW, "source": request["source"], "context": request["context"],
        "source_projection": projection,
        "status": "CHECKED_DISCOURSE_BOUNDARY" if envelope else "OUTSIDE_EXECUTED_DISCOURSE",
        "envelope": envelope, "licensed_envelope_count": 1 if envelope else 0,
        "denied_body_syntax_established": False,
        "cue_body_syntax_established": False, "intended_sense_established": False,
        "external_truth_established": False, "strict_language_accepted": False,
        "whole_arabic_complete": False}


def _native(request):
    identity = sha256(_EXECUTABLE.read_bytes()).hexdigest()
    result = subprocess.run([str(_EXECUTABLE)], input=_wire(request) + b"\n",
                            capture_output=True, timeout=30, check=False)
    if result.returncode or sha256(_EXECUTABLE.read_bytes()).hexdigest() != identity:
        raise ValueError("DISCOURSE_NATIVE_EXECUTION_FAILED")
    if len(result.stdout) > 1048576:
        raise OverflowError("DISCOURSE_NATIVE_RESPONSE_LIMIT")
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        raise ValueError("DISCOURSE_NATIVE_RESPONSE_COUNT")
    value = _parse_json(lines[0])
    if type(value) is dict and value.get("status") == "RESOURCE_LIMIT":
        raise OverflowError("DISCOURSE_NATIVE_RESOURCE_LIMIT")
    if _wire(value) != _wire(_expected(request)):
        raise ValueError("DISCOURSE_NATIVE_RECEIPT_MISMATCH")
    return value, identity


def _cue_diagnostic_summary(child):
    """Retain every choice and obligation without repeated native/source bodies.

    This is a diagnostic projection, not a verifier or a proof-authority grant.
    The entire original child remains reproducible from the recorded call; its
    exact canonical digest is retained even when its verbose bodies are omitted.
    """
    raw = _wire(child)
    occurrence_fields = ("occurrence_id", "expression", "span", "clause_span",
        "surface_segmentations", "available_senses", "selected_sense_ids", "excluded_sense_ids",
        "cue_readings", "cue_span", "signed_conflict", "reason", "classification_status",
        "profile_authority", "residuals", "unresolved_premises", "missing_premises")
    candidate_fields = ("sense_id", "gloss", "designation_id", "use_kind", "support_status",
        "native_use_kind", "convention", "conditional_support_status", "reason",
        "residuals", "unresolved_premises", "missing_premises")
    reported_fields = ("native_checked", "intended_sense_acquired", "formal_guard_decided",
                       "certified_sense_ids", "supported_use_kinds")

    def occurrence_summary(occurrence):
        out = {key: deepcopy(occurrence[key]) for key in occurrence_fields if key in occurrence}
        out["authority"] = "DIAGNOSTIC_CUE_ACQUISITION_ONLY"
        out["reported_child_flags"] = {key: deepcopy(occurrence[key]) for key in reported_fields
                                       if key in occurrence}
        out["candidates"] = [{key: deepcopy(candidate[key]) for key in candidate_fields
                               if key in candidate} for candidate in occurrence.get("candidates", [])]
        out["profile_readings"] = [{"profile_id": profile["profile_id"],
            "authority": "UNESTABLISHED_PROFILE_HYPOTHESIS",
            "conditional_result": occurrence_summary(profile["conditional_result"])}
            for profile in occurrence.get("profile_readings", [])]
        return out

    summary_fields = ("status", "reason", "source", "context", "pending_profiles",
        "unclassified_spans", "acquired_premises", "acquisition_scan_complete",
        "all_installed_readings_retained", "acquisition_extension_sha256", "inventory_sha256",
        "accepted_language", "residuals", "unresolved_premises", "missing_premises")
    summary = {key: deepcopy(child[key]) for key in summary_fields if key in child}
    summary.update(schema="nabt.cue-diagnostic-summary.v1", authority="DIAGNOSTIC_CUE_ACQUISITION_ONLY",
        raw_child_schema=child.get("schema"), raw_child_sha256=sha256(raw).hexdigest(),
        raw_child_bytes=len(raw), full_child_receipt_included=False,
        summary_kernel_proved=False, claims=[], native_checked=False,
        strict_language_accepted=False, intended_sense_established=False,
        world_truth_established=False, whole_arabic_complete=False,
        reported_child_flags={key: deepcopy(child[key]) for key in reported_fields if key in child},
        occurrences=[occurrence_summary(item) for item in child.get("occurrences", [])],
        omitted_detail_classes=["DUPLICATED_SOURCE_QUOTATIONS", "NATIVE_REQUESTS_AND_RECEIPTS",
                                "VERBOSE_CANDIDATE_DERIVATIONS", "ORTHOGRAPHY_AND_SYNTAX_EVIDENCE"])
    return summary


def acquire_discourse_boundary(text, *, source_id="user_text", context="unspecified",
                              profile_id="linguistic"):
    """Run the installed boundary law and isolate the later diagnostic reader.

    Caller arguments are raw input and explicit context only. A native boundary
    claim survives a separately recorded child diagnostic failure, but neither
    result licenses intended meaning, event truth or a free synonym expansion.
    """
    foundation.require_foundation("tools.linguistic_truth.discourse_boundary.acquire_discourse_boundary")
    report = {"schema": _SCHEMA, "law_id": _LAW, "status": "OUTSIDE_EXECUTED_DISCOURSE",
        "native_checked": False, "claims": [], "envelope": None,
        "later_cue_diagnostic": None, "selected_senses_scoped": [],
        "strict_language_accepted": False, "intended_sense_established": False,
        "world_truth_established": False, "whole_arabic_complete": False,
        "source_projection_complete": False,
        "residuals": ["OPAQUE_DENIED_AND_CUE_BODIES_NOT_PARSED_BY_BOUNDARY_LAW",
                      "CUE_INTERPRETATION_NOT_KERNEL_ACQUIRED", "EXTERNAL_REFERENCE_AND_TRUTH_NOT_ESTABLISHED"]}
    if type(text) not in {str, bytes}:
        return {**report, "status": "INVALID_INPUT", "reason": "RAW_TEXT_REQUIRED"}
    try:
        raw = text.encode("utf-8", "strict") if type(text) is str else text
        text = raw.decode("utf-8", "strict")
        if not text:
            raise ValueError("EMPTY_TEXT")
        for label in (source_id, context, *(() if profile_id is None else (profile_id,))):
            if type(label) is not str or not label.strip():
                raise ValueError("INVALID_DISCOURSE_CONTEXT_LABEL")
            label.encode("utf-8", "strict")
    except (UnicodeError, ValueError) as exc:
        return {**report, "status": "INVALID_INPUT", "reason": str(exc)}
    if (len(raw) > 16384 or len(source_id.encode("utf-8")) > 1024
            or len(context.encode("utf-8")) > 4096
            or (profile_id is not None and len(profile_id.encode("utf-8")) > 256)):
        return {**report, "status": "RESOURCE_EXHAUSTED", "reason": "DISCOURSE_INPUT_LIMIT"}
    source = {"id": source_id, "revision": sha256(raw).hexdigest(), "text": text}
    report.update(source=source, context=context, profile_id=profile_id)
    try:
        foundation.validate_source(text)
        review = _review()
        report["source_review"] = {"sha256": _REVIEW_SHA, "authority": review["authority"],
            "passage_ids": [row["id"] for row in review["passages"]],
            "replay_scope": "RETAINED_FILES_AND_PASSAGE_BYTES_ONLY",
            "historical_authenticity_established": False,
            "source_interpretation_kernel_proved": False}
    except NabtError as exc:
        return {**report, "status": "RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT"
                else "INVALID_INPUT", "reason": exc.code}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {**report, "status": "SOURCE_UNAVAILABLE", "reason": str(exc)}
    request = {"source": source, "context": context}
    try:
        receipt, binary_hash = _native(request)
    except (OverflowError, subprocess.TimeoutExpired) as exc:
        return {**report, "status": "RESOURCE_EXHAUSTED", "reason": str(exc)}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {**report, "status": "VERIFICATION_UNAVAILABLE", "reason": str(exc)}
    envelope = receipt["envelope"]
    report.update(status=receipt["status"], native_checked=True, envelope=envelope,
                  native_receipt=receipt, executable_sha256=binary_hash,
                  source_projection_complete=receipt["source_projection"]["status"] == "COMPLETE")
    if envelope is None:
        report["reason"] = "OUTSIDE_EXPLICIT_BOUNDARY_GRAMMAR_NOT_ARABIC_REJECTION"
        return report
    marked = [envelope["negation_prefix"] == "لَمْ ", envelope["conjunction"] == "وَ",
              envelope["cue_prefix"] == "أَقْصِدُ "]
    report["operator_marking_profile"] = ("EXACT_MARKED_OPERATORS" if all(marked)
        else "EXACT_UNMARKED_OPERATORS" if not any(marked) else "MIXED_OPERATOR_MARKING")
    report["claims"] = [{"kind": "EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE",
        "scope": "Exact installed negation/boundary/cue markers and disjoint preserved source slices; opaque bodies and cue interpretation excluded.",
        "source_sha256": source["revision"], "request_sha256": sha256(_wire(request)).hexdigest(),
        "receipt_sha256": sha256(_wire(receipt)).hexdigest(), "source_review_sha256": _REVIEW_SHA,
        "proof": {"law_id": _LAW, "theorems": [
            "Nabt.DiscourseBoundaryCueBridge.readings_sound",
            "Nabt.DiscourseBoundaryCueBridge.readings_complete",
            "Nabt.DiscourseBoundaryCueBridge.acquired_restores_source",
            "Nabt.DiscourseBoundaryCueBridge.acquired_disjoint_spans",
            "Nabt.DiscourseBoundaryCueBridge.acquired_retains_conjunction",
            "Nabt.DiscourseBoundaryCueBridge.acquired_exact_denied_bytes",
            "Nabt.DiscourseBoundaryCueBridge.acquired_exact_cue_bytes",
            "Nabt.DiscourseBoundaryCueBridge.acquired_valid_marks"]},
        "premises": ["PINNED_EXECUTABLE_AND_TRANSPORT", "EDITORIALLY_SELECTED_BOUNDARY_GRAMMAR",
                     "SOURCE_INTERPRETATION_NOT_KERNEL_PROVED"],
        "does_not_establish": ["DENIED_EVENT_TRUTH", "BODY_SYNTAX", "CUE_INTENDED_MEANING",
                               "CROSS_CLAUSE_REFERENCE", "ALL_ARABIC"]}]
    from .runtime import acquire
    child_id = source_id + ":later-cue:" + str(envelope["cue_start_byte"])
    child_context = ("later-cue:" + source["revision"] + ":" + str(envelope["cue_start_byte"])
                     + ":" + sha256(context.encode("utf-8")).hexdigest())
    try:
        child = acquire(envelope["cue_text"], source_id=child_id, profile_id=profile_id,
                        context=child_context, subject="unspecified")
        if type(child) is not dict or type(child.get("occurrences", [])) is not list:
            raise ValueError("CHILD_DIAGNOSTIC_SHAPE_MISMATCH")
        if child.get("occurrences"):
            cue_raw = envelope["cue_text"].encode("utf-8")
            expected_source = {"source_id": child_id, "raw_text": envelope["cue_text"],
                               "sha256": sha256(cue_raw).hexdigest(), "bytes": len(cue_raw)}
            if (_wire(child.get("source")) != _wire(expected_source)
                    or type(child.get("context")) is not dict
                    or child.get("context", {}).get("context") != child_context
                    or child.get("context", {}).get("profile_id") != profile_id):
                raise ValueError("CHILD_DIAGNOSTIC_BINDING_MISMATCH")
            for occurrence in child["occurrences"]:
                start, end = occurrence["span"]["start_byte"], occurrence["span"]["end_byte"]
                if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(cue_raw)
                        or occurrence["span"]["raw_text"].encode("utf-8") != cue_raw[start:end]
                        or occurrence["span"]["sha256"] != sha256(cue_raw[start:end]).hexdigest()
                        or type(occurrence["selected_sense_ids"]) is not list
                        or type(occurrence["excluded_sense_ids"]) is not list
                        or any(type(sense) is not str or not sense for sense in
                               occurrence["selected_sense_ids"] + occurrence["excluded_sense_ids"])
                        or type(occurrence["occurrence_id"]) is not str):
                    raise ValueError("CHILD_DIAGNOSTIC_SPAN_MISMATCH")
        child_summary = _cue_diagnostic_summary(child)
    except (OSError, ValueError, KeyError, TypeError, RecursionError, NabtError) as exc:
        child = {"status": "VERIFICATION_UNAVAILABLE", "reason": str(exc), "occurrences": []}
        child_summary = _cue_diagnostic_summary(child)
    report["later_cue_diagnostic"] = {"authority": "DIAGNOSTIC_CUE_ACQUISITION_ONLY",
        "parent_source_sha256": source["revision"], "parent_start_byte": envelope["cue_start_byte"],
        "parent_end_byte": envelope["cue_end_byte"], "source_text": envelope["cue_text"],
        "context_transfer": "LATER_EXPLICIT_CUE_ONLY", "parent_context": context,
        "profile_id": profile_id,
        "inherited_denial": False,
        "replay": {"surface": "tools.linguistic_truth.runtime.acquire",
            "input": {"text": envelope["cue_text"], "source_id": child_id,
                      "profile_id": profile_id, "context": child_context, "subject": "unspecified"}},
        "result": child_summary}
    for occurrence in child.get("occurrences", []):
        report["selected_senses_scoped"].append({"authority": "DIAGNOSTIC_CUE_ACQUISITION_ONLY",
            "scope": "later_explicit_cue", "sense_ids": occurrence["selected_sense_ids"],
            "excluded_sense_ids": occurrence["excluded_sense_ids"],
            "child_occurrence_id": occurrence["occurrence_id"],
            "parent_start_byte": envelope["cue_start_byte"] + occurrence["span"]["start_byte"],
            "parent_end_byte": envelope["cue_start_byte"] + occurrence["span"]["end_byte"],
            "projects_to_denied_clause": False, "intended_sense_kernel_proved": False})
    return report
