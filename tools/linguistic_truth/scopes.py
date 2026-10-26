"""Acquire exact discourse envelopes in native Lean, retaining opaque bodies.

The three installed source grammars are intentionally small. The checked claim
is exact envelope acquisition and byte-bound body retention, not a complete
Arabic parse. A quoted body's existing diagnostic reader runs under a separate
source/context and never supplies a narrator assertion or proof of intent.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from nabt import foundation
from nabt.errors import NabtError

_ROOT = Path(__file__).resolve().parents[2]
_EXECUTABLE = _ROOT / "formal/.lake/build/bin/scopeAcquisition"
_REVIEW = _ROOT / "evidence/scope_acquisition_v1/source_review.json"
_REVIEW_SHA = "550f0e8b666c76ab2671e01b4395a89b3f22c205cdc3878cfefc72f7b73ece46"
_LAW = "nabt.scope-acquisition.v1"
_PATTERNS = (
    ("quoted_speaker", re.compile(r"\A(?P<prefix>قَالَ (?P<speaker>[^ ]+): «)(?P<body>.+)(?P<suffix>»(?P<dot>\.)?)\Z")),
    ("negated_embedding", re.compile(r"\A(?P<prefix>لَيْسَ صَحِيحًا أَنِّي )(?P<body>.+?)(?P<suffix>(?P<dot>\.)?)\Z")),
    ("hypothetical", re.compile(r"\A(?P<prefix>إِنْ قُلْتُ )(?P<body>.+?)(?P<suffix> فَلَا (?P<tail>.+?)(?P<dot>\.)?)\Z")),
)
_FORBIDDEN = frozenset("«»\"“”‘’'`()[]{}:؛;.!?؟،,")


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _parse_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_SCOPE_RECEIPT_FIELD")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_SCOPE_RECEIPT")))


def _review():
    raw = _REVIEW.read_bytes()
    if sha256(raw).hexdigest() != _REVIEW_SHA:
        raise ValueError("SCOPE_REVIEW_CHANGED")
    review = _parse_json(raw)
    sources = {}
    for source in review["sources"]:
        path = (_ROOT / source["path"]).resolve()
        if not path.is_relative_to(_ROOT.resolve()):
            raise ValueError("SCOPE_SOURCE_OUTSIDE_ROOT")
        data = path.read_bytes()
        if sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("SCOPE_SOURCE_CHANGED")
        sources[source["id"]] = data
    for passage in review["passages"]:
        start, end = passage["start_byte"], passage["end_byte"]
        data = sources[passage["source_id"]]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(data):
            raise ValueError("SCOPE_PASSAGE_BOUNDS")
        part = data[start:end]
        if part != passage["quote"].encode("utf-8") or sha256(part).hexdigest() != passage["sha256"]:
            raise ValueError("SCOPE_PASSAGE_CHANGED")
    return review


def _projection(text):
    value = foundation.inspect_source(text)
    return {"status": "INCOMPLETE" if value["status"] == "PARTIAL" else value["status"],
            **{key: value[key] for key in ("alphabet_id", "number_domain", "cells", "number")}}


def _plain(text):
    return (bool(text) and text == text.strip(" \t\r\n\v\f")
            and all(ord(char) >= 32 and char not in _FORBIDDEN for char in text))


def _expected(request):
    text = request["source"]["text"]
    envelope = None
    projection = _projection(text)
    for kind, pattern in _PATTERNS:
        match = pattern.fullmatch(text)
        if match is None:
            continue
        groups = match.groupdict()
        body = groups["body"]
        speaker, tail = groups.get("speaker", ""), groups.get("tail", "")
        if not _plain(body) or projection["status"] == "INVALID":
            continue
        if kind == "quoted_speaker" and (not _plain(speaker) or " " in speaker):
            continue
        if kind == "hypothetical" and (not _plain(tail) or " فَلَا " in body or " فَلَا " in tail):
            continue
        prefix, suffix = groups["prefix"], groups["suffix"]
        start = len(prefix.encode("utf-8"))
        stop = start + len(body.encode("utf-8"))
        envelope = {"kind": kind, "speaker_label": speaker, "body": body, "tail": tail,
            "full_stop": bool(groups["dot"]), "start_byte": start, "end_byte": stop,
            "prefix": prefix, "suffix": suffix, "projects_to_narrator": False,
            "body_projection": _projection(body)}
        break
    return {"schema": _LAW, "source": request["source"], "context": request["context"],
        "source_projection": projection,
        "status": "CHECKED_SCOPE_ENVELOPE" if envelope else "OUTSIDE_EXECUTED_SCOPE",
        "envelope": envelope, "body_syntax_established": False,
        "intended_sense_established": False, "speaker_reference_established": False,
        "external_truth_established": False, "strict_language_accepted": False,
        "whole_arabic_complete": False}


def _native(request):
    identity = sha256(_EXECUTABLE.read_bytes()).hexdigest()
    result = subprocess.run([str(_EXECUTABLE)], input=_wire(request) + b"\n",
                            capture_output=True, timeout=30, check=False)
    if result.returncode or sha256(_EXECUTABLE.read_bytes()).hexdigest() != identity:
        raise ValueError("SCOPE_NATIVE_EXECUTION_FAILED")
    if len(result.stdout) > 1048576:
        raise OverflowError("SCOPE_NATIVE_RESPONSE_LIMIT")
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        raise ValueError("SCOPE_NATIVE_RESPONSE_COUNT")
    value = _parse_json(lines[0])
    if type(value) is dict and value.get("status") == "RESOURCE_LIMIT":
        raise OverflowError("SCOPE_NATIVE_RESOURCE_LIMIT")
    if _wire(value) != _wire(_expected(request)):
        raise ValueError("SCOPE_NATIVE_RECEIPT_MISMATCH")
    return value, identity


def acquire_scope(text, *, source_id="user_text", context="unspecified", profile_id="linguistic"):
    """Check an envelope from raw text and optionally diagnose a quoted body.

    No source, scope, speaker-reference certificate, checker or status supplied
    by the caller can replace the installed execution. `profile_id` is an
    explicit convention premise for the child diagnostic, not a discovered
    property of the source. No claim is made about semantic completeness.
    """
    foundation.require_foundation("tools.linguistic_truth.scopes.acquire_scope")
    report = {"schema": "nabt.scope-acquisition-receipt.v1", "law_id": _LAW,
        "status": "OUTSIDE_EXECUTED_SCOPE", "native_checked": False, "claims": [],
        "envelope": None, "selected_senses_scoped": [], "quoted_reading": None,
        "strict_language_accepted": False, "intended_sense_kernel_proved": False,
        "speaker_reference_established": False, "world_truth_established": False,
        "whole_arabic_complete": False, "source_projection_complete": False,
        "residuals": ["BODY_SYNTAX_NOT_KERNEL_ACQUIRED", "SOURCE_READING_IS_DECLARED_PREMISE",
                      "EXTERNAL_REFERENCE_AND_TRUTH_NOT_ESTABLISHED"]}
    if type(text) not in {str, bytes}:
        return {**report, "status": "INVALID_INPUT", "reason": "RAW_TEXT_REQUIRED"}
    try:
        raw = text.encode("utf-8", "strict") if type(text) is str else text
        text = raw.decode("utf-8", "strict")
        for label, maximum in ((source_id, 1024), (context, 4096), (profile_id, 256)):
            if type(label) is not str or not label.strip() or len(label.encode("utf-8")) > maximum:
                raise ValueError("INVALID_SCOPE_CONTEXT_LABEL")
        if not text:
            raise ValueError("EMPTY_TEXT")
    except (UnicodeError, ValueError) as exc:
        return {**report, "status": "INVALID_INPUT", "reason": str(exc)}
    if len(raw) > 16384:
        return {**report, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_SCOPE_INPUT_BYTES"}
    source = {"id": source_id, "revision": sha256(raw).hexdigest(), "text": text}
    report["source"] = source
    report["context"] = context
    try:
        foundation.validate_source(text)
        review = _review()
        report["source_review"] = {"sha256": _REVIEW_SHA,
            "authority": review["authority"], "passage_ids": [p["id"] for p in review["passages"]]}
    except NabtError as exc:
        return {**report, "status": "RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT"
                else "INVALID_INPUT", "reason": exc.code}
    except (OSError, ValueError, KeyError) as exc:
        return {**report, "status": "SOURCE_UNAVAILABLE", "reason": str(exc)}
    request = {"source": source, "context": context}
    try:
        receipt, binary_hash = _native(request)
    except (OverflowError, subprocess.TimeoutExpired) as exc:
        return {**report, "status": "RESOURCE_EXHAUSTED", "reason": str(exc)}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {**report, "status": "VERIFICATION_UNAVAILABLE", "reason": str(exc)}
    report.update(status=receipt["status"], native_checked=True, envelope=receipt["envelope"],
        native_receipt=receipt, executable_sha256=binary_hash,
        source_projection_complete=receipt["source_projection"]["status"] == "COMPLETE")
    envelope = receipt["envelope"]
    if envelope is None:
        report["reason"] = "OUTSIDE_EXPLICIT_ENVELOPE_GRAMMAR_NOT_ARABIC_REJECTION"
        return report
    report["claims"] = [{"id": "EXACT_SCOPE_ENVELOPE", "kind": "EXACT_SCOPE_ENVELOPE",
        "authority": "NATIVE_CHECKED",
        "scope": "Installed envelope grammar and original body byte interval; opaque body syntax and intent excluded",
        "statement": "Exact source reconstruction, nonempty body bytes and installed envelope shape",
        "source_sha256": source["revision"], "request_sha256": sha256(_wire(request)).hexdigest(),
        "receipt_sha256": sha256(_wire(receipt)).hexdigest(), "source_review_sha256": _REVIEW_SHA,
        "proof": {"law_id": _LAW, "theorems": ["Nabt.ScopeAcquisition.acquired_exact",
                     "Nabt.ScopeAcquisition.acquired_exact_body_bytes"]},
        "premises": ["PINNED_EXECUTABLE_AND_TRANSPORT", "EDITORIALLY_SELECTED_SCOPE_GRAMMAR"],
        "does_not_establish": ["BODY_SYNTAX", "INTENDED_SENSE", "EXTERNAL_TRUTH", "ALL_ARABIC"]}]
    if envelope["kind"] == "quoted_speaker":
        from .runtime import acquire
        child_id = source_id + ":quoted:" + str(envelope["start_byte"])
        child_context = "quoted-source:" + source["revision"] + ":" + str(envelope["start_byte"])
        child = acquire(envelope["body"], source_id=child_id, profile_id=profile_id,
            subject="textual-speaker:" + envelope["speaker_label"], context=child_context)
        report["quoted_reading"] = {"authority": "DIAGNOSTIC_BODY_ACQUISITION",
            "parent_source_sha256": source["revision"],
            "parent_start_byte": envelope["start_byte"], "parent_end_byte": envelope["end_byte"],
            "speaker_label": envelope["speaker_label"], "context_transfer": "REPORTED_VOICE_ONLY",
            "body_result": child}
        for occurrence in child.get("occurrences", []):
            report["selected_senses_scoped"].append({
                "speaker_label": envelope["speaker_label"],
                "scope": "quoted_speaker", "authority": "DIAGNOSTIC_BODY_ACQUISITION",
                "sense_ids": occurrence["selected_sense_ids"],
                "excluded_sense_ids": occurrence["excluded_sense_ids"],
                "child_occurrence_id": occurrence["occurrence_id"],
                "parent_start_byte": envelope["start_byte"] + occurrence["span"]["start_byte"],
                "parent_end_byte": envelope["start_byte"] + occurrence["span"]["end_byte"],
                "projects_to_narrator": False, "intended_sense_kernel_proved": False})
    return report
