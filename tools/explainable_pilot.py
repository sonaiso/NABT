#!/usr/bin/env python3
"""Versioned, replayable answers from NABT's existing ground-reading proposer.

An answer file is untrusted data. Verification reopens independent source/query
bytes and runs the configured native Lean checker before rebuilding the display.
This adapter is not an LLM, a general Arabic reader, or a proof of its renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import verified_reading as ground
from tools.explainable_contracts import explanation
from nabt.errors import NabtError

ANSWER_SCHEMAS = {"v1": "nabt.explainable-answer.v1", "v2": "nabt.explainable-answer.v2"}
ANSWER_SCHEMA = ANSWER_SCHEMAS["v2"]
ANALYSIS_SCHEMA = "nabt.analysis-certificate.v1"
MAX_BUNDLE_BYTES = 4 * 1048576
STATUSES = {"SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "DEFER"}
MESSAGES = {
    "SUPPORTED": "السؤال مؤيد بدليل خال من التعارض وفق قواعد المصدر.",
    "REFUTED": "نقيض السؤال مؤيد بدليل خال من التعارض وفق قواعد المصدر.",
    "CONFLICT": "يمكن اشتقاق السؤال ونقيضه من المصدر؛ النتيجة متعارضة.",
    "UNKNOWN": "لا يشتق السؤال ولا نقيضه بعد فحص الإغلاق الكامل لقواعد المصدر.",
    "DEFER": "يوجد اشتقاق يتأثر بالتعارض، ولا يوجد دليل خال منه؛ الحكم معلق.",
}


class PilotError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def strict_json(raw):
    """Decode answer/certificate wire data; numeric fields are unsigned integers."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    def constant(_value):
        raise ValueError("only unsigned decimal integer tokens are allowed")

    def unsigned(token):
        if not token.isascii() or not token.isdigit():
            raise ValueError("signed integer token is not canonical")
        return int(token)

    if len(raw) > MAX_BUNDLE_BYTES:
        raise PilotError("RESOURCE_LIMIT", "answer exceeds 4 MiB")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_int=unsigned, parse_float=constant, parse_constant=constant)
        # These wire schemas have unsigned integer fields only. Reject numeric
        # spelling before decoding erases -0; then reject escaped surrogates.
        wire(value).encode("utf-8")
        return value
    except (ValueError, RecursionError) as exc:
        raise PilotError("INVALID_INPUT", "invalid, noncanonical or duplicate-key JSON") from exc


def read_bounded(path, limit):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise PilotError("RESOURCE_LIMIT", f"input exceeds {limit} bytes")
    return raw


def checker_path(checker=None):
    path = Path(checker or os.environ.get("NABT_VERIFIED_READING",
                ROOT / "formal/.lake/build/bin/verifiedReading")).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise PilotError("CHECKER_UNAVAILABLE", "build the native Lean verifiedReading executable")
    return path


def validate_inputs(raw, query, identity, revision, scope, timeout):
    for value, limit in ((raw, 65536), (query, 8192)):
        if type(value) is not bytes:
            raise PilotError("INVALID_INPUT", "source and question must be bytes")
        if len(value) > limit:
            raise PilotError("RESOURCE_LIMIT", "source or question exceeds its byte budget")
        try:
            value.decode("utf-8")
        except UnicodeError as exc:
            raise PilotError("INVALID_INPUT", "source and question must be UTF-8") from exc
    for value in (identity, revision, scope):
        if type(value) is not str or not value or "\x00" in value:
            raise PilotError("INVALID_INPUT", "binding fields must be nonempty strings without NUL")
        try:
            size = len(value.encode("utf-8"))
        except UnicodeError as exc:
            raise PilotError("INVALID_INPUT", "binding fields must encode as UTF-8") from exc
        if size > 256:
            raise PilotError("RESOURCE_LIMIT", "binding field exceeds 256 UTF-8 bytes")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0 or timeout > 60:
        raise PilotError("INVALID_INPUT", "timeout must be a number in (0, 60] seconds")


def _check_receipt(receipt, certificate, raw, query, identity, revision, scope):
    """Check native protocol coherence, after the native success boundary.

    Membership is projected from the certificate already accepted by Lean.
    This does not replay inference or grant authority to an unchecked proposal.
    The verdict ordering is the installed SemanticInference.classify contract.
    """
    expected = {"law_id": ground.LAW_ID, "source_id": identity, "revision": revision,
                "source_scope": scope, "source_text": raw.decode(), "query_text": query.decode(),
                "scope": "canonical_ground_source_entailment", "verified": True,
                "all_arabic_complete": False, "world_truth_established": False}
    try:
        target = ground.key(certificate["query"])
        opposite = ground.opposite(target)
        full = {ground.key(atom) for atom in certificate["known"]}
        clean = {ground.key(atom) for atom in certificate["clean_known"]}
    except (KeyError, TypeError, ValueError) as exc:
        raise PilotError("CHECKER_PROTOCOL_ERROR", "accepted certificate has no readable closure") from exc
    positive, negative = target in full, opposite in full
    clean_positive, clean_negative = target in clean, opposite in clean
    expected.update(positive=positive, negative=negative,
                    clean_positive=clean_positive, clean_negative=clean_negative)
    expected["status"] = ("CONFLICT" if positive and negative else
                          "SUPPORTED" if clean_positive else
                          "REFUTED" if clean_negative else
                          "DEFER" if positive or negative else "UNKNOWN")
    # Exact canonical comparison also rejects 0/1 in Boolean protocol fields,
    # extra claims, missing polarities and an inconsistent advertised verdict.
    if (not clean <= full or wire(receipt) != wire(expected)):
        raise PilotError("CHECKER_PROTOCOL_ERROR", "native receipt differs from accepted evidence or independent inputs")


def native(raw, query, certificate, identity, revision, scope, checker, timeout):
    try:
        encoded = wire(certificate).encode("utf-8")
    except (ValueError, TypeError, RecursionError) as exc:
        raise PilotError("INVALID_INPUT", "certificate is not finite JSON") from exc
    if len(encoded) > 1048576:
        raise PilotError("RESOURCE_LIMIT", "kernel certificate exceeds 1 MiB")
    path = checker_path(checker)
    fingerprint = file_sha(path)
    # Snapshot bytes in private files: the certificate never supplies file paths.
    with tempfile.TemporaryDirectory() as temp:
        paths = [Path(temp) / name for name in ("source", "query", "certificate")]
        for target, content in zip(paths, (raw, query, encoded), strict=True):
            target.write_bytes(content)
        try:
            run = subprocess.run([str(path), *map(str, paths), identity, revision, scope],
                                 capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise PilotError("RESOURCE_LIMIT", "native checker time budget exhausted") from exc
        except OSError as exc:
            raise PilotError("CHECKER_UNAVAILABLE", "native checker could not execute") from exc
    if file_sha(path) != fingerprint:
        raise PilotError("CHECKER_CHANGED", "native executable changed during verification")
    try:
        receipt = strict_json(run.stdout)
    except PilotError as exc:
        raise PilotError("CHECKER_PROTOCOL_ERROR", "native checker did not return bounded JSON") from exc
    if not isinstance(receipt, dict):
        raise PilotError("CHECKER_PROTOCOL_ERROR", "native receipt is not an object")
    if run.returncode != 0 or receipt.get("verified") is not True:
        code = "RESOURCE_LIMIT" if receipt.get("error") == "RESOURCE_LIMIT" else "CERTIFICATE_REJECTED"
        raise PilotError(code, "native Lean checker rejected the certificate")
    _check_receipt(receipt, certificate, raw, query, identity, revision, scope)
    return receipt, fingerprint


def analysis(certificate, raw):
    """Deterministic source spans and proof DAGs, constructed only after Lean accepts.

    Clean trace indices refer to the filtered theory, so remap them to original
    source clauses. Preserve duplicates and both signs; do not claim minimality.
    """
    clauses, spans, offset = certificate["clauses"], [], 0
    indexed = {"fact": [], "rule": []}
    for i, clause in enumerate(clauses):
        text = ground.render_clause(clause)
        end = offset + len(text.encode("utf-8"))
        if raw[offset:end] != text.encode("utf-8"):
            raise PilotError("RENDERER_ERROR", "source span does not restore exact bytes")
        spans.append({"id": f"c{i}", "byte_start": offset, "byte_end": end, "text": text})
        indexed[clause["kind"]].append((i, clause))
        offset = end
    if offset != len(raw):
        raise PilotError("RENDERER_ERROR", "source spans are incomplete")
    signed = {ground.key(a) for a in certificate["known"]}
    blocked = {a for a in signed if ground.opposite(a) in signed}
    clean = {kind: [(i, c) for i, c in group if all(ground.key(a) not in blocked for a in
             ([c["atom"]] if kind == "fact" else [c["head"], *c["body"]]))]
             for kind, group in indexed.items()}
    traces, roots = {}, {}
    query = certificate["query"]
    for name, prefix, program, step_field in (("full", "f", indexed, "steps"),
                                             ("clean", "k", clean, "clean_steps")):
        trace, seen = [], {}
        for j, step in enumerate(certificate[step_field]):
            i, clause = program[step["kind"]][step["index"]]
            atom = clause["atom"] if step["kind"] == "fact" else clause["head"]
            dependencies = [] if step["kind"] == "fact" else [seen[ground.key(a)] for a in clause["body"]]
            node = {"id": f"{prefix}{j}", "clause_id": f"c{i}", "premises": dependencies,
                    "atom": atom, "text_ar": ground.render_atom(atom)}
            trace.append(node)
            seen[ground.key(atom)] = node["id"]
        traces[name] = trace
        roots[name] = {"query": seen.get(ground.key(query)),
                       "opposite_query": seen.get(ground.opposite(ground.key(query)))}
    return {"schema": ANALYSIS_SCHEMA, "source_clauses": spans, "traces": traces,
            "roots": roots, "kernel_certificate": certificate,
            "span_unit": "UTF-8 byte; zero-based; end-exclusive",
            "trace_minimality_proved": False, "renderer_formally_proved": False}


def propose_certificate(raw, query, identity="text", revision="1", scope="default"):
    """Untrusted current proposal, with the same failure contract in every caller."""
    try:
        return ground.propose(raw, query, identity, revision, scope)
    except (ValueError, NabtError) as exc:
        code = "RESOURCE_LIMIT" if (getattr(exc, "code", None) == "RESOURCE_LIMIT" or
                                   "RESOURCE_LIMIT" in str(exc)) else "OUTSIDE_VERIFIED_LANGUAGE"
        raise PilotError(code, "current proposer cannot certify this input under the ground-reading law") from exc


def answer(raw, query, *, identity="text", revision="1", scope="default",
           certificate=None, checker=None, timeout=20, answer_version="v2"):
    if type(answer_version) is not str or answer_version not in ANSWER_SCHEMAS:
        raise PilotError("INVALID_INPUT", "answer version must be v1 or v2")
    validate_inputs(raw, query, identity, revision, scope, timeout)
    if certificate is None:
        certificate = propose_certificate(raw, query, identity, revision, scope)
    receipt, fingerprint = native(raw, query, certificate, identity, revision, scope, checker, timeout)
    try:
        evidence = analysis(certificate, raw)
    except (KeyError, IndexError, TypeError) as exc:
        raise PilotError("RENDERER_ERROR", "accepted trace cannot be rendered") from exc
    result = {
        "schema": ANSWER_SCHEMAS[answer_version],
        "binding": {"source_id": identity, "revision": revision, "scope": scope,
                    "source_sha256": sha(raw), "query_sha256": sha(query),
                    "source_bytes": len(raw), "query_bytes": len(query)},
        "answer": {"status": receipt["status"], "text_ar": MESSAGES[receipt["status"]],
                   "question_ar": query.decode(),
                   "scope_ar": "الحكم تابع لمقدمات المصدر وللقواعد المضبوطة، ولا يثبت صدق المصدر في العالم."},
        "analysis_certificate": evidence,
        "verification": {"native_receipt": receipt, "checker_sha256": fingerprint},
        "limits": {"language": "canonical_ground_source_entailment", "all_arabic_complete": False,
                   "world_truth_established": False, "neural_model_measured": False,
                   "explanation_kind": "source_and_derivation_trace", "model_internal_causality_proved": False},
    }
    if answer_version == "v2":
        try:
            result["explanation"] = explanation(certificate, evidence, receipt, result["binding"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise PilotError("RENDERER_ERROR", "accepted evidence cannot be explained") from exc
    if len(wire(result).encode()) > MAX_BUNDLE_BYTES:
        raise PilotError("RESOURCE_LIMIT", "rendered answer exceeds 4 MiB")
    return result


def verify(raw, query, bundle, **options):
    """Replay with trusted caller binding/checker, never those claimed by bundle.

    Canonical JSON comparison is type-sensitive (True != 1 here), unlike Python
    container equality. Extra fields, changed display, spans or claims all fail.
    """
    if not isinstance(bundle, dict) or bundle.get("schema") not in tuple(ANSWER_SCHEMAS.values()):
        raise PilotError("ANSWER_REJECTED", "unsupported answer schema")
    version = next(version for version, schema in ANSWER_SCHEMAS.items() if schema == bundle["schema"])
    expected_version = options.pop("answer_version", version)
    if type(expected_version) is not str or expected_version != version:
        raise PilotError("ANSWER_REJECTED", "answer does not have the independently required version")
    try:
        encoded = wire(bundle).encode("utf-8")
    except (ValueError, TypeError, RecursionError) as exc:
        raise PilotError("INVALID_INPUT", "answer must be finite UTF-8 JSON") from exc
    if len(encoded) > MAX_BUNDLE_BYTES:
        raise PilotError("RESOURCE_LIMIT", "answer exceeds 4 MiB")
    try:
        certificate = bundle["analysis_certificate"]["kernel_certificate"]
    except (KeyError, TypeError) as exc:
        raise PilotError("ANSWER_REJECTED", "missing analysis certificate") from exc
    if certificate is None:
        raise PilotError("ANSWER_REJECTED", "missing kernel certificate")
    fresh = answer(raw, query, certificate=certificate, answer_version=version, **options)
    if encoded != wire(fresh).encode("utf-8"):
        raise PilotError("ANSWER_REJECTED", "answer, explanation, binding or checker differs from replay")
    replay = {"schema": "nabt.answer-replay." + version, "verified": True,
              "status": fresh["answer"]["status"]}
    if version == "v2":
        replay.update(answer_schema=fresh["schema"], explanation_schema=fresh["explanation"]["schema"])
    return replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    for operation in ("answer", "verify"):
        p = sub.add_parser(operation)
        p.add_argument("source", type=Path)
        p.add_argument("query", type=Path)
        p.add_argument("--source-id", default="text")
        p.add_argument("--revision", default="1")
        p.add_argument("--scope", default="default")
        p.add_argument("--checker", type=Path)
        p.add_argument("--timeout", type=float, default=20)
        p.add_argument("--answer-version", choices=("v1", "v2"),
                       default="v2" if operation == "answer" else None,
                       help="output version for answer; required bundle version for verify")
        if operation == "answer":
            p.add_argument("--certificate", type=Path, help="untrusted external proposal; optional")
            p.add_argument("--output", type=Path, required=True)
        else:
            p.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        raw, query = read_bounded(args.source, 65536), read_bounded(args.query, 8192)
        options = dict(identity=args.source_id, revision=args.revision, scope=args.scope,
                       checker=args.checker, timeout=args.timeout)
        if args.answer_version is not None:
            options["answer_version"] = args.answer_version
        if args.operation == "answer":
            proposal = strict_json(read_bounded(args.certificate, 1048576)) if args.certificate else None
            if args.certificate and proposal is None:
                raise PilotError("INVALID_INPUT", "external certificate cannot be null")
            result = answer(raw, query, certificate=proposal, **options)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Bound the actual file bytes, not a smaller serialization than the
            # one written. An accepted answer must remain readable by verify.
            encoded = (wire(result) + "\n").encode("utf-8")
            if len(encoded) > MAX_BUNDLE_BYTES:
                raise PilotError("RESOURCE_LIMIT", "serialized answer exceeds 4 MiB")
            args.output.write_bytes(encoded)
            print(wire({"answer_written": str(args.output), "status": result["answer"]["status"]}))
        else:
            print(wire(verify(raw, query, strict_json(read_bounded(args.bundle, MAX_BUNDLE_BYTES)), **options)))
        return 0
    except (PilotError, OSError) as exc:
        print(wire({"schema": "nabt.pilot-error.v1", "verified": False,
                    "error": exc.code if isinstance(exc, PilotError) else "IO_ERROR", "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
