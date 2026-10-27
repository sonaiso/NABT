"""Exact witnessed spelling, with a native A116 bridge and no sense transfer.

Only the installed, byte-replayed QAC rows are admitted. A source annotation
is testimony about that row; the theorem checks its FORM encoding and the new
occurrence's exact spelling. It does not establish the intended sense, the
grammatical role in the new context, the truth of the corpus, or all Arabic.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess

from nabt import foundation
from nabt.errors import NabtError
from tools import attested_lexical_loader as source_loader

_ROOT = Path(__file__).resolve().parents[2]
_LEDGER = _ROOT / "evidence/lexical_surface_binding_v1/source_ledger.json"
_LEDGER_SHA = "01c585ae3b4b27d957ca703faf0370ad7bf28d9d5f4f0d564bdb13d63381e9f1"
_LAW = "nabt.lexical-surface-binding.v1"
_SCHEMA = "nabt.witnessed-surface-receipt.v1"
_BW_CARRIERS = "AbtvjHxd*rzs$SDTZEgfqklmnhwy'"
_BW_MARKS = "auio"
_AR_CARRIERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهويء"
_AR_MARKS = "َُِْ"


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value):
    return sha256(_wire(value)).hexdigest()


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_NATIVE_FIELD")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_NATIVE_VALUE")))


def _decode(form):
    if len(form) % 2:
        return None
    cells = []
    for carrier, mark in zip(form[::2], form[1::2]):
        if carrier not in _BW_CARRIERS or mark not in _BW_MARKS:
            return None
        cells.append(4 * _BW_CARRIERS.index(carrier) + _BW_MARKS.index(mark))
    return cells


def _arabic(cells):
    return "".join(_AR_CARRIERS[cell // 4] + _AR_MARKS[cell % 4] for cell in cells)


def _installed():
    ledger_raw = _LEDGER.read_bytes()
    if sha256(ledger_raw).hexdigest() != _LEDGER_SHA:
        raise ValueError("INSTALLED_SURFACE_LEDGER_CHANGED")
    ledger = _json(ledger_raw)
    with source_loader.DEFAULT_SOURCE.open("rb") as stream:
        payload = stream.read(source_loader.MAX_PAYLOAD_BYTES + 1)
    raw = source_loader._decode_source(payload)
    if (sha256(raw).hexdigest() != ledger["source"]["sha256"]
            or len(raw) != ledger["source"]["bytes"]):
        raise ValueError("SOURCE_IDENTITY_CHANGED")
    witnesses = []
    for row in ledger["rows"]:
        fragment = raw[row["source_start_byte"]:row["source_end_byte"]]
        if (fragment.decode("utf-8") != row["raw_line"]
                or sha256(fragment).hexdigest() != row["row_sha256"]):
            raise ValueError("SOURCE_ROW_CHANGED")
        fields = row["raw_line"].rstrip("\r\n").split("\t")
        lemma = [field[4:] for field in fields[3].split("|") if field.startswith("LEM:")]
        if (fields[0] != row["id"] or fields[1] != row["form"] or fields[2] != row["tag"]
                or lemma != [row["annotation_lemma"]]
                or fragment[row["form_start_byte"]:row["form_end_byte"]] != row["form"].encode("ascii")
                or not _decode(row["form"])):
            raise ValueError("SOURCE_ANNOTATION_OR_FORM_CHANGED")
        witnesses.append({"id": row["id"], "expression": row["annotation_lemma"],
            "convention": ledger["convention"], "binding": {
                "source": {"id": "qac:" + row["id"], "revision": row["row_sha256"],
                           "text": row["raw_line"]},
                "scope_id": ledger["source"]["sha256"], "occurrence_id": row["id"],
                "reading_id": row["annotation_lemma"], "start_byte": row["form_start_byte"],
                "end_byte": row["form_end_byte"], "surface": row["form"]}})
    return ledger, witnesses


def _native(requests):
    payload = b"".join(_wire(request) + b"\n" for request in requests)
    if len(payload) > 4 * 1048576:
        raise OverflowError("SURFACE_REQUEST_LIMIT")
    executable = _ROOT / "formal/.lake/build/bin/lexicalSurface"
    binary_hash = sha256(executable.read_bytes()).hexdigest()
    completed = subprocess.run([str(executable)], input=payload, capture_output=True,
                               timeout=60, check=False)
    if completed.returncode or sha256(executable.read_bytes()).hexdigest() != binary_hash:
        raise ValueError("NATIVE_SURFACE_EXECUTION_FAILED")
    if len(completed.stdout) > 4 * 1048576:
        raise OverflowError("SURFACE_RESPONSE_LIMIT")
    responses = [_json(line) for line in completed.stdout.splitlines()]
    if len(responses) != len(requests):
        raise ValueError("NATIVE_SURFACE_RESPONSE_COUNT")
    if any(type(row) is dict and row.get("status") == "RESOURCE_LIMIT" for row in responses):
        raise OverflowError("NATIVE_SURFACE_RESOURCE_LIMIT")
    return responses, binary_hash


def _expected(request, projection, exact):
    frame = request["frame"]
    matched = [witness["id"] for witness in request["witnesses"]
        if exact and projection["status"] == "COMPLETE"
        and witness["expression"] == frame["expression"]
        and witness["convention"] == frame["convention"]
        and request["surface"] == _arabic(_decode(witness["binding"]["surface"]))
        and projection["cells"] == _decode(witness["binding"]["surface"])]
    return {"schema": _LAW, "source": request["source"], "frame": frame,
        "surface": request["surface"], "projection_status": projection["status"],
        "cells": projection["cells"], "number": projection["number"],
        "occurrence_exact": exact, "witness_count": len(request["witnesses"]),
        "matched_ids": matched, "status": "CHECKED_EXACT_SURFACE" if matched else "NO_EXACT_WITNESS",
        "intended_sense_established": False, "whole_arabic_complete": False}


def certify_surface(text, *, start_byte=0, end_byte=None, source_id="user_text",
                    context="unspecified", referent="unspecified", time="unspecified"):
    """Recheck all installed form witnesses for one exact source occurrence.

    No caller-supplied witness, checker, sense, proof flag or receipt is accepted.
    The claim is exact documentary spelling/annotation alignment only. Unicode
    bytes, source position and context are retained even when matching fails.
    """
    foundation.require_foundation("tools.linguistic_truth.surface.certify_surface")
    report = {"schema": _SCHEMA, "law_id": _LAW, "status": "DEFER", "reason": None,
        "native_checked": False, "exact_surface_checked": False, "claims": [], "matches": [],
        "strict_language_accepted": False, "intended_sense_established": False,
        "source_interpretation_proved": False, "annotation_acquisition_kernel_proved": False,
        "tawatur_evaluated": False,
        "whole_arabic_complete": False, "residuals": ["SOURCE_ANNOTATION_TESTIMONY",
            "SOURCE_ROW_ACQUISITION_NOT_KERNEL_PROVED",
            "SOURCE_ANNOTATION_ACQUISITION_NOT_KERNEL_PROVED",
            "NEW_CONTEXT_SENSE_NOT_ESTABLISHED", "GRAMMATICAL_APPLICATION_NOT_ESTABLISHED"]}
    try:
        whole = foundation.inspect_source(text, source_id=source_id, revision="observed")
        original = whole["source"]["text"]
        raw = original.encode("utf-8")
        end_byte = len(raw) if end_byte is None else end_byte
        if (type(start_byte) is not int or type(end_byte) is not int
                or not 0 <= start_byte < end_byte <= len(raw)):
            raise ValueError("INVALID_SOURCE_SPAN")
        for value in (context, referent, time):
            if type(value) is not str or not value or len(value.encode("utf-8")) > 1024:
                raise ValueError("INVALID_CONTEXT_LABEL")
        surface = raw[start_byte:end_byte].decode("utf-8", "strict")
        source = {"id": source_id, "revision": sha256(raw).hexdigest(), "text": original}
        projection = foundation.inspect_source(surface, source_id=source_id, revision=source["revision"])
        boundaries = {0, *(piece["start_byte"] for piece in whole["pieces"]),
                      *(piece["end_byte"] for piece in whole["pieces"])}
        exact = start_byte in boundaries and end_byte in boundaries
        report["source"] = source
        report["occurrence"] = {"source": source_id, "revision": source["revision"], "raw": original,
            "start_byte": start_byte, "end_byte": end_byte, "referent": referent, "time": time, "context": context}
        report["surface"] = surface
        report["foundation_source"] = projection
    except (NabtError, ValueError, UnicodeError) as error:
        report.update(status="RESOURCE_EXHAUSTED" if isinstance(error, NabtError)
                      and error.code == "RESOURCE_LIMIT" else "INVALID_INPUT",
                      reason=error.code if isinstance(error, NabtError) else str(error))
        return report
    try:
        ledger, witnesses = _installed()
    except (OSError, NabtError, ValueError, KeyError, TypeError, UnicodeError):
        report.update(status="SOURCE_UNAVAILABLE", reason="INSTALLED_WITNESS_REPLAY_FAILED")
        return report
    report["source_ledger_sha256"] = _LEDGER_SHA
    report["source_corpus_sha256"] = ledger["source"]["sha256"]
    expressions = sorted({(w["expression"], w["convention"]) for w in witnesses})
    requests = [{"source": source, "frame": {"occurrence": report["occurrence"],
        "expression": expression, "convention": convention}, "surface": surface,
        "witnesses": witnesses} for expression, convention in expressions]
    try:
        responses, binary_hash = _native(requests)
        for request, response in zip(requests, responses, strict=True):
            if _wire(response) != _wire(_expected(request, projection, exact)):
                raise ValueError("NATIVE_SURFACE_POSTCONDITION_MISMATCH")
    except (subprocess.TimeoutExpired, OverflowError):
        report.update(status="RESOURCE_EXHAUSTED", reason="NATIVE_SURFACE_RESOURCE_LIMIT")
        return report
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        report.update(status="VERIFICATION_UNAVAILABLE", reason="NATIVE_SURFACE_UNAVAILABLE_OR_REJECTED")
        return report
    report["native_checked"] = True
    report["native_binary_sha256"] = binary_hash
    report["native_receipts"] = responses
    matched = [identity for response in responses for identity in response["matched_ids"]]
    report["matches"] = [row for row in ledger["rows"] if row["id"] in matched]
    report["exact_surface_checked"] = bool(matched)
    report["status"] = "CHECKED_EXACT_SURFACE" if matched else "DEFER"
    report["reason"] = "DOCUMENTARY_FORM_ONLY" if matched else "NO_EXACT_INSTALLED_WITNESS"
    for request, response in zip(requests, responses, strict=True):
        if not response["matched_ids"]:
            continue
        report["claims"].append({"kind": "EXACT_WITNESSED_FORM_WITH_DECLARED_ANNOTATION",
            "source": source, "frame": request["frame"], "witness_ids": response["matched_ids"],
            "request_sha256": _digest(request), "response_sha256": _digest(response),
            "source_ledger_sha256": _LEDGER_SHA,
            "proof": {"kind": "NATIVE_LEAN_RECEIPT", "law_id": _LAW, "theorems": [
                "Nabt.LexicalSurfaceBinding.witnesses_exact",
                "Nabt.LexicalSurfaceBinding.checked_cells_exact",
                "Nabt.LexicalSurfaceBinding.decodeForm_encode",
                "Nabt.LexicalSurfaceBinding.changed_surface_rejected"]},
            "scope": "Conditional on the retained source row, Lean checks its exact FORM encoding and equality with the observed Arabic spelling under the declared expression label. Python replays the row's byte interval in the full pinned corpus and its LEM extraction; neither acquisition step is kernel-proved. No transfer of corpus sense or grammatical role into the new context.",
            "unresolved_premises": list(report["residuals"])})
    return report
