"""Bounded transport from a private proof lab to the installed Lean checker.

The request contains text and budgets, never code, paths, rules or authority.
The result is an execution receipt; it does not strengthen the kernel's scope.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.licensed_inference import InferenceBudget, evaluate

REQUEST_SCHEMA = "nabt.proof-lab-request.v1"
RESULT_SCHEMA = "nabt.proof-lab-result.v1"
ENVELOPE_SCHEMA = "nabt.proof-lab-envelope.v1"
MAX_PAYLOAD_BYTES = 32768
MAX_SOURCE_BYTES = 16384
MAX_QUERY_BYTES = 4096
MAX_RESULT_BYTES = 2 * 1024 * 1024
MAX_EVENT_BYTES = 2 * 1024 * 1024
BUDGET_LIMITS = {
    "max_clauses": 64, "max_readings": 64,
    "max_atoms": 256, "max_closure_steps": 256,
}
SMOKE_ID = "00000000-0000-4000-8000-000000000001"
SMOKE_PAYLOAD = json.dumps({
    "schema": REQUEST_SCHEMA, "mode": "inference",
    "source_text": "إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ. عَرَفَ زَيْدٌ الْحَقَّ.",
    "query_text": "هَلْ سَارَ زَيْدٌ؟",
}, ensure_ascii=False, separators=(",", ":"))
SCOPE = {
    "law_id": "nabt.licensed-inference.v1",
    "accepted_language": "nabt.explicit-subject-active.v1",
    "claim": "Source-relative inference in the installed bounded grammar",
    "whole_arabic": "NOT_PROVED",
    "external_world": "NOT_VERIFIED",
    "benchmark_denominator": "38 frozen diagnostic cases, not all Arabic",
}
RESULT_STATES = {
    "SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "DEFER", "DISAGREEMENT",
    "INVALID_INPUT", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE", "RESOURCE_EXHAUSTED",
}
CHECKED_STATES = {"SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "DEFER", "DISAGREEMENT"}
BOOLEAN_FLAGS = {
    "verified", "native_checked", "all_readings_complete", "closures_checked",
    "all_arabic_complete", "world_truth_established", "premise_world_truth_established",
    "source_interpretation_historically_proved",
}


class RequestError(ValueError):
    """A stable error code; it never includes caller-supplied text."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RequestError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _constant(_):
    raise RequestError("NONFINITE_JSON_NUMBER")


def strict_json(raw: str | bytes, maximum: int):
    if type(raw) not in (str, bytes):
        raise RequestError("JSON_TEXT_REQUIRED")
    try:
        encoded = raw.encode("utf-8", "strict") if type(raw) is str else raw
        if len(encoded) > maximum:
            raise RequestError("INPUT_BYTE_LIMIT")
        return json.loads(encoded.decode("utf-8", "strict"),
                          object_pairs_hook=_unique, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise RequestError("INVALID_UTF8_OR_JSON") from exc


def validate_id(value):
    if type(value) is not str:
        raise RequestError("INVALID_REQUEST_ID")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise RequestError("INVALID_REQUEST_ID") from exc
    if str(parsed) != value or parsed.version != 4:
        raise RequestError("INVALID_REQUEST_ID")
    return value


def transport_key(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
        raise RequestError("TRANSPORT_KEY_UNAVAILABLE")
    return bytes.fromhex(value)


def _base64(value, maximum):
    if type(value) is not str or len(value) > 4 * ((maximum + 2) // 3):
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    try:
        result = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE") from exc
    if len(result) > maximum or base64.b64encode(result).decode("ascii") != value:
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    return result


def decrypt_envelope(request_id, serialized, key, maximum=MAX_PAYLOAD_BYTES):
    """AES-256-GCM authenticates the request ID and never accepts bare JSON."""
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate_id(request_id)
    if type(key) is not bytes or len(key) != 32:
        raise RequestError("TRANSPORT_KEY_UNAVAILABLE")
    envelope = strict_json(serialized, 512 + 4 * ((maximum + 18) // 3))
    if (type(envelope) is not dict or set(envelope) != {"schema", "nonce", "ciphertext"}
            or envelope["schema"] != ENVELOPE_SCHEMA):
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    nonce = _base64(envelope["nonce"], 12)
    ciphertext = _base64(envelope["ciphertext"], maximum + 16)
    if len(nonce) != 12 or len(ciphertext) < 16:
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, request_id.encode("utf-8"))
    except InvalidTag as exc:
        raise RequestError("ENCRYPTED_REQUEST_AUTHENTICATION_FAILED") from exc


def encrypt_envelope(request_id, plaintext, key, maximum=MAX_RESULT_BYTES):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate_id(request_id)
    if type(key) is not bytes or len(key) != 32:
        raise RequestError("TRANSPORT_KEY_UNAVAILABLE")
    if type(plaintext) is not bytes or len(plaintext) > maximum:
        raise RequestError("ENCRYPTED_PLAINTEXT_BYTE_LIMIT")
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, request_id.encode("utf-8"))
    return {"schema": ENVELOPE_SCHEMA,
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii")}


def _text(value, maximum, field):
    if type(value) is not str or not value.strip():
        raise RequestError(field + "_TEXT_REQUIRED")
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise RequestError("INVALID_UNICODE") from exc
    if len(raw) > maximum:
        raise RequestError(field + "_BYTE_LIMIT")
    return value


def validate_payload(payload):
    request = strict_json(payload, MAX_PAYLOAD_BYTES)
    if type(request) is not dict or request.get("schema") != REQUEST_SCHEMA:
        raise RequestError("INVALID_REQUEST_SCHEMA")
    mode = request.get("mode")
    if mode == "benchmark":
        if set(request) != {"schema", "mode"}:
            raise RequestError("UNEXPECTED_REQUEST_FIELD")
        return request
    if mode != "inference":
        raise RequestError("UNSUPPORTED_MODE")
    required = {"schema", "mode", "source_text", "query_text"}
    if not required <= set(request) or not set(request) <= required | {"budget"}:
        raise RequestError("UNEXPECTED_REQUEST_FIELD")
    _text(request["source_text"], MAX_SOURCE_BYTES, "SOURCE")
    _text(request["query_text"], MAX_QUERY_BYTES, "QUERY")
    supplied = request.get("budget", {})
    if type(supplied) is not dict or not set(supplied) <= set(BUDGET_LIMITS):
        raise RequestError("INVALID_BUDGET_FIELDS")
    for key, value in supplied.items():
        if type(value) is not int or not 0 <= value <= BUDGET_LIMITS[key]:
            raise RequestError("INVALID_BUDGET_VALUE")
    return request


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _code_sha():
    value = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, check=True,
                           timeout=5).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RuntimeError("CODE_IDENTITY_UNAVAILABLE")
    expected = os.environ.get("GITHUB_SHA")
    if expected and value != expected:
        raise RuntimeError("CODE_IDENTITY_MISMATCH")
    return value


def _identity():
    binary = ROOT / "formal/.lake/build/bin/licensedInference"
    return {
        "code_sha": _code_sha(),
        "native_sha256": _sha(binary.read_bytes()) if binary.is_file() else None,
        "runner_sha256": _sha(Path(__file__).read_bytes()),
        "runtime_sha256": _sha((ROOT / "tools/licensed_inference/runtime.py").read_bytes()),
        "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip(),
    }


def _authority_guard(result):
    if (type(result) is not dict or any(type(result.get(key)) is not bool for key in BOOLEAN_FLAGS)
            or result.get("schema") != "nabt.licensed-inference-result.v1"
            or result.get("law_id") != SCOPE["law_id"]
            or result.get("accepted_language") != SCOPE["accepted_language"]
            or result.get("all_arabic_complete") is not False
            or result.get("world_truth_established") is not False
            or result.get("premise_world_truth_established") is not False
            or result.get("source_interpretation_historically_proved") is not False
            or type(result.get("status")) is not str or result["status"] not in RESULT_STATES):
        raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")
    if result.get("verified") is True and not (
        result.get("native_checked") is True
        and result.get("closures_checked") is True
        and result.get("all_readings_complete") is True
        and result.get("authority") == "SOURCE_RELATIVE_CONSEQUENCE"
        and result["status"] in CHECKED_STATES
    ):
        raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")
    if result["verified"] is False and (
        result["native_checked"] or result["closures_checked"] or result["all_readings_complete"]
        or result.get("authority") != "UNVERIFIED_PROPOSAL"
        or result["status"] in {"SUPPORTED", "REFUTED", "CONFLICT", "DEFER", "DISAGREEMENT"}
    ):
        raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")


def _benchmark():
    from tools.benchmark_licensed_inference import run
    report = run()
    # Rows retain failed and unmeasured obligations. Raw results and large
    # environment snapshots are omitted only from this bounded transport.
    rows = [{key: row[key] for key in ("id", "family", "mode", "executed",
             "outcome", "checks", "observed") if key in row}
            for row in report["rows"]]
    return {
        "schema": report["schema"],
        "measured_at_utc": report["measured_at_utc"],
        "gold_sha256": report["gold_sha256"],
        "summary": report["summary"],
        "contract_gate": report["contract_gate"],
        "execution_integrity": report["execution_evidence"]["integrity"],
        "scope": report["scope"], "rows": rows,
    }


def run_payload(request_id, payload, *, prepare=False):
    started = time.monotonic()
    response = {
        "schema": RESULT_SCHEMA, "request_id": None,
        "payload_sha256": None, "code_sha": None, "native_sha256": None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0, "mode": None, "status": "INVALID_INPUT",
        "all_arabic_complete": False, "world_truth_established": False,
        "scope": dict(SCOPE),
    }
    try:
        response["request_id"] = validate_id(request_id)
        # Preserve the exact dispatch string in the digest; do not normalize.
        if type(payload) in (str, bytes):
            raw = payload.encode("utf-8", "strict") if type(payload) is str else payload
            response["payload_sha256"] = _sha(raw)
        request = validate_payload(payload)
        response["mode"] = request["mode"]
        before = _identity()
        response.update(before)
        if prepare:
            response["status"] = "PREPARED"
        elif response["native_sha256"] is None:
            response.update(status="VERIFICATION_UNAVAILABLE", error="NATIVE_CHECKER_MISSING")
        elif request["mode"] == "inference":
            budget = InferenceBudget(max_source_bytes=MAX_SOURCE_BYTES,
                max_query_bytes=MAX_QUERY_BYTES, **(BUDGET_LIMITS | request.get("budget", {})))
            result = evaluate(request["source_text"], request["query_text"],
                source_id="proof-lab:" + request_id, revision=response["code_sha"],
                scope="proof-lab-single-discourse", time="unspecified", budget=budget)
            _authority_guard(result)
            response.update(status=result["status"], result=result)
        else:
            report = _benchmark()
            response.update(status="BENCHMARK_COMPLETE" if report["contract_gate"]["passed"]
                            else "BENCHMARK_CONTRACT_FAILURE", benchmark=report)
        if not prepare and _identity() != before:
            raise RuntimeError("EXECUTION_IDENTITY_CHANGED")
    except (RequestError, UnicodeError) as exc:
        response.update(status="INVALID_INPUT", error=str(exc) if isinstance(exc, RequestError)
                        else "INVALID_UNICODE")
    except Exception:
        # Never copy exception strings: a library exception can contain text
        # from a private source, a path, or runtime credentials.
        response.update(status="EXECUTION_FAILED", error="INTERNAL_EXECUTION_FAILURE")
        response.pop("result", None)
        response.pop("benchmark", None)
    response["duration_ms"] = round((time.monotonic() - started) * 1000)
    encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(encoded) >= MAX_RESULT_BYTES:
        response.pop("result", None)
        response.pop("benchmark", None)
        response.update(status="RESOURCE_EXHAUSTED", error="RESULT_BYTE_LIMIT")
    return response


def _event_request(path, event_name):
    with path.open("rb") as stream:
        event = strict_json(stream.read(MAX_EVENT_BYTES + 1), MAX_EVENT_BYTES)
    if type(event) is not dict:
        raise RequestError("INVALID_EVENT")
    if event_name == "workflow_dispatch":
        inputs = event.get("inputs")
        if type(inputs) is not dict or set(inputs) != {"request_id", "payload"}:
            raise RequestError("INVALID_EVENT_INPUTS")
        request_id = validate_id(inputs["request_id"])
        key = transport_key(os.environ.get("NABT_LAB_TRANSPORT_KEY"))
        return request_id, decrypt_envelope(request_id, inputs["payload"], key), False
    if event_name in {"push", "pull_request"}:
        return SMOKE_ID, SMOKE_PAYLOAD, True
    raise RequestError("UNSUPPORTED_EVENT")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-file", type=Path)
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--request-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    smoke = False
    encrypted = args.event_file is not None and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    try:
        if args.event_file is not None and args.request_file is None and args.request_id is None:
            request_id, payload, smoke = _event_request(args.event_file, os.environ.get("GITHUB_EVENT_NAME"))
        elif args.request_file is not None and args.event_file is None and args.request_id is not None:
            with args.request_file.open("rb") as stream:
                payload = stream.read(MAX_PAYLOAD_BYTES + 1)
            request_id = args.request_id
        else:
            raise RequestError("ONE_INPUT_MODE_REQUIRED")
        result = run_payload(request_id, payload, prepare=args.prepare)
    except (OSError, RequestError, ImportError):
        if encrypted:
            # A failed envelope has no trusted private result to publish. No
            # plaintext fallback is written into a public repository artifact.
            print(json.dumps({"status": "ENCRYPTED_TRANSPORT_REJECTED"}))
            return 2
        result = run_payload(None, None, prepare=args.prepare)
        result["error"] = "INPUT_TRANSPORT_FAILURE"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if encrypted:
        key = transport_key(os.environ.get("NABT_LAB_TRANSPORT_KEY"))
        envelope = encrypt_envelope(request_id, serialized.encode("utf-8"), key)
        args.output.write_text(json.dumps(envelope, separators=(",", ":")) + "\n")
    else:
        args.output.write_text(serialized + "\n")
    if args.github_output is not None:
        valid = result["status"] == "PREPARED"
        artifact = "nabt-lab-smoke" if smoke else (
            "nabt-lab-" + result["request_id"] if result["request_id"] else "nabt-lab-rejected")
        # Both values are derived from validated UUIDs or fixed literals.
        with args.github_output.open("a") as stream:
            stream.write("valid=" + ("true" if valid else "false") + "\n")
            stream.write("artifact_name=" + artifact + "\n")
    print(json.dumps({"request_id": result["request_id"],
        "status": ("ENCRYPTED_RESULT_WRITTEN" if encrypted else result["status"])}, ensure_ascii=False))
    if smoke and not args.prepare and not (result.get("result", {}).get("verified") is True
                                          and result["status"] == "SUPPORTED"):
        return 2
    return 2 if result["status"] in {"EXECUTION_FAILED", "VERIFICATION_UNAVAILABLE",
                                    "BENCHMARK_CONTRACT_FAILURE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
