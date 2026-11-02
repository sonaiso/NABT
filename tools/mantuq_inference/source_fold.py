"""Bounded, reversible transport of the existing source-bound inference result.

The number names canonical UTF-8 data in a versioned sentinel256 domain. It is
not a Program, a new inference engine, or a proof of Arabic completeness.
Decoding restores untrusted data. Only replay with independent source, query,
plan, identity, budget and configured native checkers can verify that data.
"""
from __future__ import annotations

from hashlib import sha256
import re

from tools import meaning_preservation_v1 as json_contract
from tools.explainable_pilot import PilotError
from .source_bound import evaluate_source


FOLD_SCHEMA = "nabt.mantuq-source-fold.v1"
PAYLOAD_SCHEMA = "nabt.mantuq-source-fold-payload.v1"
FOLD_DOMAIN = "nabt.mantuq-source.canonical-json-utf8.sentinel256.v1"
RESULT_SCHEMA = "nabt.mantuq-source-result.v1"
REPLAY_SCHEMA = "nabt.mantuq-source-replay.v1"
MAX_PAYLOAD_BYTES = 8 * 1048576
MAX_ENVELOPE_BYTES = 17 * 1048576
RESULT_FIELDS = frozenset((
    "schema", "status", "reason", "conditional_consequence", "input_binding",
    "plan", "budget", "source_answer", "source_witnesses", "conditional_request",
    "conditional_result", "native_checkers", "limits",
))
SEMANTIC_STATUSES = frozenset(("SUPPORTED", "UNKNOWN", "REFUTED", "CONFLICT", "DEFER"))
ENVELOPE_FIELDS = frozenset((
    "schema", "domain", "number_hex", "payload_sha256", "authority", "requires_source_replay",
))


def _preflight(value, maximum):
    """Count each JSON occurrence before allocating its complete wire document.

    Shared Python objects are counted every time they occur. No memoization can
    hide their expansion into a JSON tree. This guard does not supply a parser:
    canonical serialization and strict decoding remain owned by the installed
    meaning-preservation JSON contract.
    """
    used = 0

    def add(size):
        nonlocal used
        used += size
        if used > maximum:
            raise PilotError("RESOURCE_LIMIT", "canonical JSON exceeds its cumulative byte budget")

    def string_size(text):
        # Every code point contributes at least one byte. Reject giant strings
        # before creating an encoded or escaped copy, then count exact UTF-8.
        if len(text) + 2 > maximum - used:
            raise PilotError("RESOURCE_LIMIT", "JSON string exceeds the remaining byte budget")
        add(2)
        for char in text:
            code = ord(char)
            if 0xD800 <= code <= 0xDFFF:
                raise PilotError("INVALID_INPUT", "unpaired Unicode surrogate")
            if char in '"\\' or char in "\b\f\n\r\t":
                add(2)
            elif code < 32:
                add(6)
            else:
                add(1 if code < 128 else 2 if code < 2048 else 3 if code < 65536 else 4)

    def visit(item, depth):
        if depth > json_contract.MAX_DEPTH:
            raise PilotError("RESOURCE_LIMIT", "JSON depth exceeds the installed limit")
        kind = type(item)
        if kind is dict:
            add(2 + max(0, len(item) - 1) + len(item))
            for key, child in item.items():
                if type(key) is not str:
                    raise PilotError("INVALID_INPUT", "JSON object keys must be strings")
                string_size(key)
                visit(child, depth + 1)
        elif kind is list:
            add(2 + max(0, len(item) - 1))
            for child in item:
                visit(child, depth + 1)
        elif kind is str:
            string_size(item)
        elif kind is bool:
            add(4 if item else 5)
        elif item is None:
            add(4)
        elif kind is int:
            if abs(item) > json_contract.MAX_INTEGER:
                raise PilotError("RESOURCE_LIMIT", "JSON integer exceeds the installed magnitude limit")
            add(len(str(item)))
        else:
            raise PilotError("INVALID_INPUT", "only strict integer-valued JSON data are accepted")

    visit(value, 0)
    return used


def bounded_wire(value, maximum=MAX_PAYLOAD_BYTES):
    """Canonical bytes with a cumulative preallocation bound, for this adapter."""
    if type(maximum) is not int or not 0 < maximum <= MAX_ENVELOPE_BYTES:
        raise PilotError("INVALID_INPUT", "invalid JSON byte budget")
    size = _preflight(value, maximum)
    try:
        raw = json_contract.wire(value).encode("utf-8")
    except json_contract.ResourceLimit as error:
        raise PilotError("RESOURCE_LIMIT", str(error)) from error
    except (json_contract.InputError, TypeError, ValueError, RecursionError) as error:
        raise PilotError("INVALID_INPUT", "value does not satisfy the installed JSON contract") from error
    if len(raw) != size or len(raw) > maximum:
        raise PilotError("RESOURCE_LIMIT", "canonical JSON size differs from bounded accounting")
    return raw


def strict_input(raw, *, maximum=MAX_PAYLOAD_BYTES):
    """Reuse the installed duplicate-key, number, depth and UTF-8 protections."""
    try:
        return json_contract.strict_loads(raw, maximum_bytes=maximum)
    except json_contract.ResourceLimit as error:
        raise PilotError("RESOURCE_LIMIT", str(error)) from error
    except (json_contract.InputError, ValueError, TypeError, RecursionError) as error:
        raise PilotError("INVALID_INPUT", "invalid strict JSON input") from error


def _result_shape(result):
    if (type(result) is not dict or set(result) != RESULT_FIELDS
            or result.get("schema") != RESULT_SCHEMA
            or type(result.get("status")) is not str
            or type(result.get("reason")) is not str
            or type(result.get("conditional_consequence")) is not bool):
        raise PilotError("FOLD_REJECTED", "payload is not a complete source-bound result")
    for name in ("input_binding", "plan", "budget", "source_witnesses", "native_checkers", "limits"):
        if type(result[name]) is not dict:
            raise PilotError("FOLD_REJECTED", "source-bound result has malformed " + name)
    for name in ("source_answer", "conditional_request", "conditional_result"):
        if result[name] is not None and type(result[name]) is not dict:
            raise PilotError("FOLD_REJECTED", "source-bound result has malformed " + name)


def _require_evaluated_source(result):
    if type(result) is not dict or result.get("schema") != RESULT_SCHEMA or type(result.get("status")) is not str:
        raise PilotError("FOLD_REJECTED", "source evaluator did not return its declared result")
    status = result["status"]
    if status not in SEMANTIC_STATUSES:
        code = ("RESOURCE_LIMIT" if status == "RESOURCE_EXHAUSTED" else
                "CHECKER_UNAVAILABLE" if status == "VERIFICATION_UNAVAILABLE" else
                "SOURCE_ERROR" if status == "SOURCE_ERROR" else "INVALID_INPUT")
        raise PilotError(code, "source evaluation did not complete: " + status + ": " + str(result.get("reason", "")))
    _result_shape(result)
    if result["source_answer"] is None:
        raise PilotError("CHECKER_UNAVAILABLE", "source evaluation has no native-checked reading")


def fold_source(raw, query, plan, **options):
    """Read and check the actual source, then transport the complete result.

    Every option is provided by the trusted caller; no executable path or budget
    is selected by a transported record. Technical failures do not issue a fold.
    """
    result = evaluate_source(raw, query, plan, **options)
    _require_evaluated_source(result)
    payload = {"schema": PAYLOAD_SCHEMA, "domain": FOLD_DOMAIN, "result": result}
    encoded = bounded_wire(payload)
    # Exactly hex(int.from_bytes(b"\x01" + encoded, "big")), without allocating
    # an additional giant integer or asking JSON to represent that integer.
    return {"schema": FOLD_SCHEMA, "domain": FOLD_DOMAIN,
            "number_hex": "0x1" + encoded.hex(),
            "payload_sha256": sha256(encoded).hexdigest(),
            "authority": "TRANSPORT_ONLY", "requires_source_replay": True}


def unfold_source(envelope):
    """Restore untrusted source-result data; this performs no inference check.

    Historical nested flags are restored byte-for-byte. They acquire no current
    authority by being decoded; consumers must use verify_fold with independent
    inputs and current configured native checkers.
    """
    if (type(envelope) is not dict or set(envelope) != ENVELOPE_FIELDS
            or envelope.get("schema") != FOLD_SCHEMA or envelope.get("domain") != FOLD_DOMAIN
            or envelope.get("authority") != "TRANSPORT_ONLY"
            or envelope.get("requires_source_replay") is not True):
        raise PilotError("FOLD_REJECTED", "unknown fold schema, domain or authority")
    number = envelope["number_hex"]
    fingerprint = envelope["payload_sha256"]
    if type(number) is not str or type(fingerprint) is not str:
        raise PilotError("FOLD_REJECTED", "fold number and digest must be strings")
    if len(number) > 3 + 2 * MAX_PAYLOAD_BYTES:
        raise PilotError("RESOURCE_LIMIT", "fold number exceeds its byte budget")
    if (not number.startswith("0x1") or len(number) <= 3 or (len(number) - 3) % 2
            or re.fullmatch(r"0x1[0-9a-f]+", number) is None
            or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None):
        raise PilotError("FOLD_REJECTED", "noncanonical sentinel256 number or digest")
    encoded = bytes.fromhex(number[3:])
    if sha256(encoded).hexdigest() != fingerprint:
        raise PilotError("FOLD_REJECTED", "fold payload digest differs")
    payload = strict_input(encoded)
    if (type(payload) is not dict or set(payload) != {"schema", "domain", "result"}
            or payload.get("schema") != PAYLOAD_SCHEMA or payload.get("domain") != FOLD_DOMAIN):
        raise PilotError("FOLD_REJECTED", "fold payload has a different schema or domain")
    if bounded_wire(payload) != encoded:
        raise PilotError("FOLD_REJECTED", "fold payload is not canonical JSON")
    _result_shape(payload["result"])
    return payload["result"]


def verify_fold(raw, query, plan, envelope, **options):
    """Rebuild from independently supplied inputs; never trust a stored receipt."""
    restored = unfold_source(envelope)
    fresh = evaluate_source(raw, query, plan, **options)
    _require_evaluated_source(fresh)
    if bounded_wire(restored) != bounded_wire(fresh):
        raise PilotError("FOLD_REJECTED", "source, query, plan, binding, budget, checker or result differs from replay")
    return {"schema": REPLAY_SCHEMA, "verified": True, "status": "VERIFIED_REPLAY",
            "source_status": fresh["status"],
            "conditional_consequence": fresh["conditional_consequence"],
            "payload_sha256": envelope["payload_sha256"],
            "world_truth_established": False, "all_arabic_complete": False,
            "action_authority": "NONE"}
