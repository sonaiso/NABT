#!/usr/bin/env python3
"""Bounded verification of external certificate proposals; no model execution.

Candidates are JSON bytes, never code, commands, paths or proof authority.
The budget covers verification after proposals have been supplied, not LLM time.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from nabt.errors import NabtError
from tools.source_codec import encode_source, verify_source, word_view
from tools import explainable_pilot as pilot

SCHEMA = "nabt.bounded-decoding.v1"
MAX_K = 16
MAX_CANDIDATE_BYTES = 1048576


def read_report(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate field")
            result[key] = value
        return result

    def unsigned(token):
        if not token.isascii() or not token.isdigit():
            raise ValueError("noncanonical integer")
        return int(token)

    def finite(token):
        value = float(token)
        if not math.isfinite(value):
            raise ValueError("nonfinite number")
        return value

    raw = pilot.read_bounded(path, 8 * 1048576)
    try:
        report = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                            parse_int=unsigned, parse_float=finite, parse_constant=finite)
        pilot.wire(report).encode("utf-8")
        return report
    except (ValueError, RecursionError) as exc:
        raise pilot.PilotError("INVALID_INPUT", "Invalid report JSON") from exc


def _budget(k, seconds):
    if type(k) is not int or not 1 <= k <= MAX_K:
        raise pilot.PilotError("INVALID_INPUT", "k must be an integer in [1, 16]")
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 60:
        raise pilot.PilotError("INVALID_INPUT", "verification budget must be in (0, 60] seconds")


def run_candidates(raw, query, candidates, *, k=1, seconds=20, checker=None,
                   identity="text", revision="1", scope="default"):
    _budget(k, seconds)
    pilot.validate_inputs(raw, query, identity, revision, scope, seconds)
    if type(candidates) is not list or len(candidates) > k or any(type(c) is not bytes for c in candidates):
        raise pilot.PilotError("INVALID_INPUT", "Supply at most k byte-valued candidate documents")
    # Bound work before hashing or parsing any untrusted proposal.
    if any(len(c) > MAX_CANDIDATE_BYTES for c in candidates):
        raise pilot.PilotError("RESOURCE_LIMIT", "A certificate proposal exceeds 1 MiB")
    started = time.monotonic()
    binding = dict(identity=identity, revision=revision, scope=scope)
    sources = {"source": encode_source(raw, **binding), "query": encode_source(query, **binding)}
    attempts, selected, accepted_statuses = [], None, set()
    selected_index = None
    for index in range(k):
        row = {"index": index, "candidate_sha256": None, "accepted": False,
               "executed": False, "answer_status": None, "answer_sha256": None}
        attempts.append(row)
        if index >= len(candidates):
            row["error"] = "MISSING_CANDIDATE"
            continue
        candidate = candidates[index]
        row["candidate_sha256"] = pilot.sha(candidate)
        remaining = seconds - (time.monotonic() - started)
        if remaining <= 0:
            row["error"] = "RESOURCE_LIMIT"
            continue
        attempt_start = time.monotonic()
        row["executed"] = True
        try:
            certificate = pilot.strict_json(candidate)
            # None must never trigger the implicit local proposer in pilot.answer.
            if type(certificate) is not dict:
                raise pilot.PilotError("INVALID_INPUT", "A proposal must be a certificate object")
            remaining = seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise pilot.PilotError("RESOURCE_LIMIT", "Verification budget exhausted during parsing")
            answer = pilot.answer(raw, query, certificate=certificate, checker=checker,
                                  timeout=min(20, remaining), **binding)
            if time.monotonic() - started > seconds:
                raise pilot.PilotError("RESOURCE_LIMIT", "Verification budget exhausted")
            status = answer["answer"]["status"]
            row.update(accepted=True, answer_status=status,
                       answer_sha256=pilot.sha(pilot.wire(answer).encode("utf-8")))
            accepted_statuses.add(status)
            if selected is None:
                selected, selected_index = answer, index
        except pilot.PilotError as exc:
            row["error"] = exc.code
        row["elapsed_seconds"] = time.monotonic() - attempt_start
    if len(accepted_statuses) > 1:
        selected, selected_index = None, None
        decision = "INCONSISTENT_VERIFIED_RESULTS"
    else:
        decision = "ANSWER_AVAILABLE" if selected is not None else "NO_VERIFIED_CANDIDATE"
    return {"schema": SCHEMA, **sources, "law_id": pilot.ground.LAW_ID,
            "budget": {"k": k, "verification_seconds": seconds},
            "supplied_candidates": len(candidates), "attempts": attempts,
            "decision": decision, "selected_index": selected_index, "answer": selected,
            "elapsed_seconds": time.monotonic() - started,
            "limits": {"candidate_set_exhaustive": False, "all_arabic_complete": False,
                       "neural_generation_measured": False, "a116_chain_established": False,
                       "audit_log_authenticated": False, "grammar_constrained_generation": False,
                       "language": "canonical_ground_source_entailment"}}


def verify_selected(raw, query, candidates, report, *, checker=None,
                    identity="text", revision="1", scope="default"):
    """Recheck the selected answer, not authenticity of timings or rejected logs."""
    if type(report) is not dict or report.get("schema") != SCHEMA:
        raise pilot.PilotError("INVALID_INPUT", "Unsupported decoding report")
    binding = dict(identity=identity, revision=revision, scope=scope)
    try:
        verify_source(raw, report.get("source"), **binding)
        verify_source(query, report.get("query"), **binding)
        index = report.get("selected_index")
        if (type(candidates) is not list or type(index) is not int or index < 0
                or index >= len(candidates) or len(candidates) > MAX_K):
            raise pilot.PilotError("ANSWER_REJECTED", "No independently supplied selected proposal")
        proposal = candidates[index]
        if type(proposal) is not bytes or len(proposal) > MAX_CANDIDATE_BYTES:
            raise pilot.PilotError("INVALID_INPUT", "Selected proposal is not bounded bytes")
        certificate = pilot.strict_json(proposal)
        answer = report["answer"]
        replay = pilot.verify(raw, query, answer, checker=checker, **binding)
        if pilot.wire(certificate) != pilot.wire(answer["analysis_certificate"]["kernel_certificate"]):
            raise pilot.PilotError("ANSWER_REJECTED", "Selected answer differs from original proposal")
    except NabtError as exc:
        raise pilot.PilotError(exc.code, exc.message) from exc
    except (KeyError, TypeError, IndexError) as exc:
        raise pilot.PilotError("ANSWER_REJECTED", "Malformed selected answer") from exc
    return {"verified": True, "answer_replay": replay, "scope": "selected_answer_only",
            "audit_log_authenticated": False, "selection_order_authenticated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    encode = commands.add_parser("encode")
    encode.add_argument("source", type=Path)
    encode.add_argument("--word", action="store_true", help="Probe exactly one word in current A116")
    for name in ("run", "verify"):
        sub = commands.add_parser(name)
        sub.add_argument("source", type=Path)
        sub.add_argument("query", type=Path)
        sub.add_argument("--candidate", type=Path, action="append", default=[])
        sub.add_argument("--checker", type=Path)
        if name == "run":
            sub.add_argument("--k", type=int, default=1)
            sub.add_argument("--seconds", type=float, default=20)
        else:
            sub.add_argument("report", type=Path)
    for sub in (encode, *[commands.choices[n] for n in ("run", "verify")]):
        sub.add_argument("--source-id", default="text")
        sub.add_argument("--revision", default="1")
        sub.add_argument("--scope", default="default")
        sub.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        binding = dict(identity=args.source_id, revision=args.revision, scope=args.scope)
        raw = pilot.read_bounded(args.source, 65536)
        if args.command == "encode":
            result = (word_view if args.word else encode_source)(raw, **binding)
        else:
            query = pilot.read_bounded(args.query, 8192)
            if len(args.candidate) > MAX_K:
                raise pilot.PilotError("RESOURCE_LIMIT", "At most 16 candidate files are permitted")
            candidates = [pilot.read_bounded(p, MAX_CANDIDATE_BYTES) for p in args.candidate]
            if args.command == "run":
                result = run_candidates(raw, query, candidates, k=args.k, seconds=args.seconds,
                                        checker=args.checker, **binding)
            else:
                # Run reports contain measured decimal times, unlike certificates.
                report = read_report(args.report)
                result = verify_selected(raw, query, candidates, report, checker=args.checker, **binding)
        serialized = pilot.wire(result) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        else:
            print(serialized, end="")
        return 1 if (result.get("decision") in {"NO_VERIFIED_CANDIDATE", "INCONSISTENT_VERIFIED_RESULTS"}
                     or result.get("outcome") in {"DEFER", "REJECT"}) else 0
    except (pilot.PilotError, NabtError, OSError) as exc:
        print(pilot.wire({"schema": "nabt.pilot-error.v1", "error": getattr(exc, "code", "IO_ERROR"),
                          "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
