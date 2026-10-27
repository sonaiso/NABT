"""Strict public A116/Lean receipt path for installed lexical acquisition.

The caller supplies raw text and explicit context, never a ledger, premise set,
checker path, proof flag, or imported receipt.  Python's acquisition remains a
separate obligation: even a native conditional theorem cannot certify that its
premises were correctly acquired from arbitrary Arabic.  The report therefore
has no blanket language-acceptance or completeness promotion.
"""
from __future__ import annotations

from hashlib import sha256
import json
import subprocess

from nabt import foundation
from nabt.errors import NabtError

from . import runtime
from .calculus import canonical_json, evaluate_request

SCHEMA = "nabt.certified-linguistic-acquisition.v1"
LAW_ID = "nabt.certified-lexical.v1"
_MAX_NATIVE_BYTES = 1048576
_MAX_NATIVE_RESPONSE_BYTES = 4 * _MAX_NATIVE_BYTES


def _digest(value):
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_NATIVE_FIELD")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_NATIVE_VALUE")))


def _native(request):
    """Execute only the repository-owned checker; no external path argument."""
    payload = canonical_json(request).encode("utf-8") + b"\n"
    if len(payload) > _MAX_NATIVE_BYTES:
        raise OverflowError("NATIVE_CERTIFICATION_REQUEST_LIMIT")
    executable = runtime.ROOT / "formal/.lake/build/bin/linguisticTruth"
    completed = subprocess.run([str(executable)], input=payload,
        capture_output=True, timeout=60, check=False)
    if completed.returncode:
        raise ValueError("NATIVE_CERTIFICATION_FAILED")
    if len(completed.stdout) > _MAX_NATIVE_RESPONSE_BYTES:
        raise OverflowError("NATIVE_CERTIFICATION_RESPONSE_LIMIT")
    result = _strict_json(completed.stdout.decode("utf-8", "strict"))
    if (type(result) is dict and set(result) == {"status", "message"}
            and result["status"] == "RESOURCE_LIMIT" and type(result["message"]) is str):
        raise OverflowError("NATIVE_CERTIFICATION_RESOURCE_LIMIT")
    return result


def _blocked(status, reason, diagnostic=None, projection=None):
    report = {"schema": SCHEMA, "law_id": LAW_ID, "status": status,
        "reason": reason, "strict_language_accepted": False, "lexical_surface_licensed": False,
        "native_checked": False, "candidate_set_checked": False,
        "conditional_use_checked": False, "claims": [], "occurrences": [],
        "residuals": [reason], "all_arabic_complete": False,
        "world_truth_established": False, "tawatur_evaluated": False,
        "native_acquisition_proof": False}
    if diagnostic is not None:
        report["diagnostic"] = diagnostic
    if projection is not None:
        report["foundation_source"] = projection
        report["source"] = projection["source"]
    return report


def _source_request(projection, request):
    return {"op": "certify_a116", "source": projection["source"],
            "cells": projection["cells"], "request": request}


def _validate(result, request, projection):
    """Check the complete native postcondition, not a Boolean grant field.

    This is a defensive finite adapter. The independent Lean module proves its
    typed contract; equality here is not a general Python refinement theorem.
    """
    semantic_request = request["request"]
    semantic = evaluate_request(semantic_request)
    occurrence = semantic_request["frame"]["occurrence"]
    frame, source = semantic_request["frame"], projection["source"]
    boundaries = {0, *(row["start_byte"] for row in projection["pieces"]),
                  *(row["end_byte"] for row in projection["pieces"])}
    source_bound = (occurrence["source"] == source["id"]
        and occurrence["revision"] == source["revision"]
        and occurrence["raw"] == source["text"]
        and occurrence["start_byte"] < occurrence["end_byte"]
        and occurrence["end_byte"] <= len(source["text"].encode("utf-8"))
        and occurrence["start_byte"] in boundaries and occurrence["end_byte"] in boundaries
        and occurrence["context"] != "" and frame["expression"] != "" and frame["convention"] != "")
    cells_exact = canonical_json(request["cells"]) == canonical_json(projection["cells"])
    candidates_checked = (projection["status"] == "COMPLETE" and cells_exact
        and bool(request["cells"]) and source_bound and semantic["status"] == "CHECKED"
        and semantic["complete_proposal"] is True and bool(semantic_request["proposed"]))
    accepted = [row["candidate"] for row in semantic["rows"]
                if candidates_checked and row["verdict"] == "SUPPORTED_PREMISES"]
    status = ("RESOURCE_EXHAUSTED" if semantic["status"] == "RESOURCE_EXHAUSTED"
        else "CERTIFIED_CONDITIONAL_USE" if accepted
        else "CHECKED_CANDIDATES" if candidates_checked else "DEFERRED")
    expected = {"schema": LAW_ID, "law_id": LAW_ID,
        "authority": "A116_SOURCE_BOUND_CONDITIONAL_SUPPLIED_PREMISES", "status": status,
        "source": source, "alphabet_id": projection["alphabet_id"],
        "number_domain": projection["number_domain"], "cells": projection["cells"],
        "source_number": projection["number"], "projection_status": projection["status"],
        "source_bound": source_bound, "cells_exact": cells_exact,
        "candidate_set_checked": candidates_checked, "certified_from_a116": bool(accepted),
        "accepted_candidates": accepted, "semantic": semantic,
        "native_acquisition_proof": False, "all_arabic_complete": False,
        "world_truth_established": False}
    if type(result) is not dict or canonical_json(result) != canonical_json(expected):
        raise ValueError("NATIVE_CERTIFICATION_POSTCONDITION_MISMATCH")
    return True


def _claims(result, request):
    """Proof labels apply only to exact native-checked bounded statements."""
    if result["candidate_set_checked"] is not True:
        return []
    binding = {"source": result["source"], "frame": request["request"]["frame"],
        "request_sha256": _digest(request), "response_sha256": _digest(result)}
    candidate_claim = {"kind": "A116_EXACT_INSTALLED_CANDIDATE_SET",
        "authority": "KERNEL_CHECKED_CONDITIONAL", "binding": binding,
        "candidate_count": len(request["request"]["proposed"]),
        "scope": "Complete direct A116 projection and exact nonempty candidate enumeration for the supplied installed ledger and expression label supplied by the acquirer. Surface-to-lexeme acquisition is not kernel-proved; this does not license the lexical surface, all Arabic senses, or intended use.",
        "proof": {"kind": "NATIVE_LEAN_RECEIPT", "law_id": LAW_ID,
            "theorems": ["Nabt.CertifiedLexical.candidate_check_exact",
                "Nabt.CertifiedLexical.checked_candidates_retain_every_compatible",
                "Nabt.CertifiedLexical.checked_cells_reversible"]},
        "unresolved_premises": ["SOURCE_INTERPRETATION_REVIEW", "OCCURRENCE_TO_LEXEME_NOT_KERNEL_PROVED",
                                "LEXICAL_ACQUISITION_NOT_KERNEL_PROVED",
                                "EXPLICIT_CONTEXT_ASSUMPTION"]}
    claims = [candidate_claim]
    if result["certified_from_a116"] is True:
        claims.append({"kind": "A116_CONDITIONAL_SUPPORTED_USE",
            "authority": "KERNEL_CHECKED_CONDITIONAL", "binding": binding,
            "accepted_candidates": result["accepted_candidates"],
            "scope": "The exact candidate is supported conditional on the supplied signed premises, including intended-use evidence. This is not a proof that Python acquired those premises correctly.",
            "proof": {"kind": "NATIVE_LEAN_RECEIPT", "law_id": LAW_ID,
                "theorems": ["Nabt.CertifiedLexical.accepted_exact",
                    "Nabt.CertifiedLexical.accepted_requires_usage_premise"]},
            "unresolved_premises": ["SOURCE_INTERPRETATION_REVIEW", "OCCURRENCE_TO_LEXEME_NOT_KERNEL_PROVED",
                                    "ACQUISITION_NOT_KERNEL_PROVED",
                                    "EXPLICIT_CONTEXT_ASSUMPTION"]})
    return claims


def acquire_certified(text, *, profile_id=None, budget=None, source_id="user_text",
                      subject="unspecified", time="unspecified", context="unspecified"):
    """Recompute installed acquisition and native-check exact named claims.

    A native receipt can certify a bounded candidate enumeration or a supplied-
    premise implication.  Neither is a proof of the Python acquisition itself,
    historical source truth, intended meaning in every context, or all Arabic.
    Incomplete source-to-A116 projection never becomes strict acceptance.
    """
    foundation.require_foundation("tools.linguistic_truth.certified.acquire_certified")
    diagnostic = runtime.acquire(text, profile_id=profile_id, budget=budget,
        source_id=source_id, subject=subject, time=time, context=context)
    if diagnostic["status"] in {"INVALID_INPUT", "RESOURCE_EXHAUSTED", "SOURCE_UNAVAILABLE"}:
        return _blocked(diagnostic["status"], diagnostic["reason"], diagnostic)
    try:
        raw = text.encode("utf-8", "strict") if type(text) is str else text
        original = raw.decode("utf-8", "strict")
        expected_source = {"source_id": source_id, "raw_text": original,
                           "sha256": sha256(raw).hexdigest(), "bytes": len(raw)}
        if canonical_json(diagnostic["source"]) != canonical_json(expected_source):
            return _blocked("VERIFICATION_UNAVAILABLE", "ACQUISITION_SOURCE_MISMATCH", diagnostic)
        projection = foundation.inspect_source(original,
            source_id=source_id, revision=expected_source["sha256"])
    except NabtError as error:
        return _blocked("RESOURCE_EXHAUSTED" if error.code == "RESOURCE_LIMIT"
                        else "INVALID_INPUT", error.code, diagnostic)
    if profile_id is None:
        return _blocked("DEFER", "CONVENTION_PROFILE_UNESTABLISHED", diagnostic, projection)
    report = _blocked("DEFER", "ACQUISITION_NOT_KERNEL_PROVED", diagnostic, projection)
    if projection["status"] != "COMPLETE":
        report["residuals"].append("SOURCE_TO_A116_INCOMPLETE")
    if diagnostic.get("unclassified_spans"):
        report["residuals"].append("UNCLASSIFIED_TEXT")
    occurrences = diagnostic.get("occurrences", [])
    if not occurrences:
        report["residuals"].append("NO_INSTALLED_LEXICAL_CANDIDATES")
        return report
    for occurrence in occurrences:
        try:
            semantic_request = occurrence["native_request"]
            frame = semantic_request["frame"]
            if (frame["convention"] != profile_id
                    or frame["occurrence"]["context"] != context
                    or frame["occurrence"]["referent"] != subject
                    or frame["occurrence"]["time"] != time):
                raise ValueError("ACQUISITION_CONTEXT_MISMATCH")
            request = _source_request(projection, semantic_request)
            result = _native(request)
            checked = _validate(result, request, projection)
        except (OverflowError, subprocess.TimeoutExpired):
            report.update(status="RESOURCE_EXHAUSTED", reason="NATIVE_CERTIFICATION_RESOURCE_LIMIT")
            report["residuals"].append(report["reason"])
            return report
        except (OSError, UnicodeError, ValueError, KeyError, TypeError, RecursionError):
            report.update(status="VERIFICATION_UNAVAILABLE", reason="NATIVE_CERTIFICATION_UNAVAILABLE_OR_REJECTED")
            report["residuals"].append(report["reason"])
            return report
        item = {"occurrence_id": occurrence["occurrence_id"],
                "request_sha256": _digest(request), "response_sha256": _digest(result),
                "native_checked": checked, "native_receipt": result,
                "claims": _claims(result, request)}
        report["occurrences"].append(item)
    report["native_checked"] = bool(report["occurrences"]) and all(
        row["native_checked"] for row in report["occurrences"])
    report["candidate_set_checked"] = bool(report["occurrences"]) and all(
        row["native_receipt"]["candidate_set_checked"] for row in report["occurrences"])
    report["conditional_use_checked"] = any(
        row["native_receipt"]["certified_from_a116"] for row in report["occurrences"])
    report["claims"] = [claim for row in report["occurrences"] for claim in row["claims"]]
    report["residuals"] = list(dict.fromkeys(report["residuals"]))
    return report
