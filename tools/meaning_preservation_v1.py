"""Source-bound finite observation preservation through an actual JSON channel.

The source/spec and independent authored matrix were frozen before this code.
Python proposes; the installed Lean executable independently decodes each
transported payload and computes the whole joint-reading observation. A checked
finite contract is not linguistic adequacy, source authenticity or world truth.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
LAW_ID = "nabt.meaning-preservation.v1"
QUERY_ID = "joint-readings.v1"
CODEC_ID = "strict-json-packet.v1"
NATIVE_SCHEMA = "nabt.meaning-preservation.native-response.v1"
RESULT_SCHEMA = "nabt.meaning-preservation.result.v1"
NATIVE = ROOT / "formal/.lake/build/bin/meaningPreservationV1"
MAX_REQUEST_BYTES = 1024 * 1024
MAX_PAYLOAD_BYTES = MAX_REQUEST_BYTES
MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_SOURCE_BYTES = 65536
MAX_METADATA_BYTES = 512
MAX_ITEMS = 64
MAX_DEPTH = 32
MAX_INTEGER = 2**53 - 1
FLAGS = {name: False for name in (
    "world_truth_established", "source_authenticity_established",
    "referents_established", "all_arabic_complete",
    "human_interpretation_agreement_established")}
PRODUCTIVE_FIELDS = frozenset((
    "text", "source_id", "revision", "scope", "ending", "onset",
    "source_context", "recipient_context", "transported_payload"))
CODE_PATHS = ("tools/meaning_preservation_v1.py", "tools/meaning_preservation_cli.py")


class InputError(ValueError):
    """Malformed input under this versioned contract, not a language judgment."""


class ResourceLimit(InputError):
    """A declared computational bound was exceeded."""


def _shape(value, *, report=False, depth=0):
    # Root value has depth zero; object keys are names, not child JSON values.
    if depth > MAX_DEPTH:
        raise ResourceLimit("JSON value depth exceeds 32")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise InputError("JSON object keys must be strings")
            try:
                key.encode("utf-8", "strict")
            except UnicodeError as error:
                raise InputError("Invalid Unicode object key") from error
            _shape(item, report=report, depth=depth + 1)
    elif type(value) is list:
        for item in value:
            _shape(item, report=report, depth=depth + 1)
    elif type(value) is str:
        try:
            value.encode("utf-8", "strict")
        except UnicodeError as error:
            raise InputError("Unpaired surrogate") from error
    elif type(value) is int:
        if abs(value) > MAX_INTEGER:
            raise ResourceLimit("Integer exceeds the exact JSON magnitude limit")
    elif type(value) is float:
        if not report or not math.isfinite(value):
            raise InputError("Noncanonical JSON number")
    elif type(value) not in (bool, type(None)):
        raise InputError("Non-JSON value")


def wire(value, *, report=False):
    """Typed canonical JSON; report floats are only existing producer evidence."""
    _shape(value, report=report)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _encoded(value, maximum, *, report=False):
    raw = wire(value, report=report).encode("utf-8")
    if len(raw) > maximum:
        raise ResourceLimit("JSON byte limit")
    return raw


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("Duplicate decoded JSON key")
        result[key] = value
    return result


def _integer(value):
    if re.fullmatch(r"0|-?[1-9][0-9]*", value) is None:
        raise InputError("Noncanonical JSON integer")
    if len(value.lstrip("-")) > 16:
        raise ResourceLimit("JSON integer digit limit")
    number = int(value)
    if abs(number) > MAX_INTEGER:
        raise ResourceLimit("JSON integer magnitude limit")
    return number


def _bad_number(_):
    raise InputError("Noncanonical JSON number")


def strict_loads(raw, *, maximum_bytes=MAX_REQUEST_BYTES, report=False):
    if type(raw) not in (str, bytes):
        raise InputError("Strict JSON text required")
    try:
        raw = raw.encode("utf-8", "strict") if type(raw) is str else raw
        if len(raw) > maximum_bytes:
            raise ResourceLimit("JSON byte limit")
        text = raw.decode("utf-8", "strict")
        # At most 33 containers: an empty root-relative depth-32 container is
        # permitted. The parsed-value check separately counts scalar children.
        depth, quoted, escaped = 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > MAX_DEPTH + 1:
                    raise ResourceLimit("JSON container depth limit")
            elif char in "]}":
                depth -= 1
        result = json.loads(text, object_pairs_hook=_pairs, parse_int=_integer,
                            parse_float=float if report else _bad_number,
                            parse_constant=_bad_number)
        _shape(result, report=report)
        return result
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InputError("Malformed strict UTF-8 JSON") from error
    except RecursionError as error:
        raise ResourceLimit("JSON recursion limit") from error


def _fields(value, expected, label):
    if type(value) is not dict or set(value) != set(expected):
        raise InputError(label + " has missing or unexpected fields")


def _text(value, label, maximum=MAX_METADATA_BYTES, *, content=False):
    if type(value) is not str or not value:
        raise InputError(label + " must be nonempty text")
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeError as error:
        raise InputError(label + " must be strict Unicode") from error
    if len(raw) > maximum:
        raise ResourceLimit(label + " byte limit")
    if not content and any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        raise InputError(label + " contains a forbidden metadata control")


def _array(value, label):
    if type(value) is not list or not value:
        raise InputError(label + " must be a nonempty array")
    if len(value) > MAX_ITEMS:
        raise ResourceLimit(label + " item limit")


def _context(value):
    _fields(value, ("speaker", "addressee", "time", "place"), "context")
    for key, item in value.items():
        _text(item, "context." + key)


def _term(value):
    _fields(value, ("kind", "value"), "term")
    kind = value["kind"]
    if type(kind) is not str or kind not in ("entity", "speaker", "addressee", "time", "place"):
        raise InputError("Unknown term kind")
    if kind == "entity":
        _text(value["value"], "entity value")
    elif type(value["value"]) is not str or value["value"] != "":
        raise InputError("Contextual term value must be the empty string")


def validate_packet(packet):
    _fields(packet, ("binding", "source_context", "alternatives"), "packet")
    binding = packet["binding"]
    _fields(binding, ("source_id", "revision", "scope", "source_text", "convention"), "binding")
    for key, value in binding.items():
        _text(value, "binding." + key,
              MAX_SOURCE_BYTES if key == "source_text" else MAX_METADATA_BYTES,
              content=key == "source_text")
    _context(packet["source_context"])
    _array(packet["alternatives"], "alternatives")
    seen = set()
    for reading in packet["alternatives"]:
        _fields(reading, ("predicate", "subject", "object", "positive", "tense", "voice", "force"), "reading")
        _text(reading["predicate"], "predicate")
        _term(reading["subject"])
        if reading["object"] is not None:
            _term(reading["object"])
        if type(reading["positive"]) is not bool:
            raise InputError("Reading polarity requires a Boolean")
        for field, choices in (("tense", ("past", "present", "future", "unspecified")),
                               ("voice", ("active", "passive", "unspecified")),
                               ("force", ("asserted", "quoted", "hypothetical", "question"))):
            if type(reading[field]) is not str or reading[field] not in choices:
                raise InputError("Invalid reading " + field)
        encoded = wire(reading)
        if encoded in seen:
            raise InputError("Duplicate exact reading object")
        seen.add(encoded)
    return deepcopy(packet)


def encode_packet(packet):
    """Installed canonical encoder; no claim is derived from its byte identity."""
    return _encoded(validate_packet(packet), MAX_PAYLOAD_BYTES).decode("utf-8")


def decode_packet(payload):
    _text(payload, "transported payload", MAX_PAYLOAD_BYTES, content=True)
    return validate_packet(strict_loads(payload, maximum_bytes=MAX_PAYLOAD_BYTES))


def validate_request(request):
    _encoded(request, MAX_REQUEST_BYTES)
    _fields(request, ("law_id", "query_id", "codec_id", "cases", "recipient_context"), "request")
    for key, required in (("law_id", LAW_ID), ("query_id", QUERY_ID), ("codec_id", CODEC_ID)):
        if type(request[key]) is not str or request[key] != required:
            raise InputError("Unknown installed " + key)
    _context(request["recipient_context"])
    _array(request["cases"], "cases")
    seen = set()
    for row in request["cases"]:
        _fields(row, ("case_id", "original", "transported_payload"), "case")
        _text(row["case_id"], "case ID")
        seen.add(row["case_id"])
        validate_packet(row["original"])
        decode_packet(row["transported_payload"])
    # Match native dispatch: parse every case before checking distinct IDs.
    if len(seen) != len(request["cases"]):
        raise InputError("Duplicate case ID")
    return deepcopy(request)


def _resolve(term, context):
    if term is None:
        return None
    return {"kind": term["kind"],
            "value": term["value"] if term["kind"] == "entity" else context[term["kind"]]}


def observe_packet(packet):
    """Installed query: a set of whole tuples, never field marginals."""
    packet = validate_packet(packet)
    context, binding = packet["source_context"], packet["binding"]
    observations = {}
    for row in packet["alternatives"]:
        observed = {"predicate": row["predicate"],
                    "subject": _resolve(row["subject"], context),
                    "object": _resolve(row["object"], context),
                    **{key: row[key] for key in ("positive", "tense", "voice", "force")},
                    "scope": binding["scope"], "convention": binding["convention"],
                    "time": context["time"], "place": context["place"]}
        observations[wire(observed)] = observed
    return [observations[key] for key in sorted(observations)]


def _decision(status, reason, count=0, case_id=None, other_case_id=None):
    return {"schema": NATIVE_SCHEMA, "law_id": LAW_ID, "query_id": QUERY_ID,
            "codec_id": CODEC_ID, "status": status, "reason": reason,
            "case_id": case_id, "other_case_id": other_case_id, "case_count": count,
            "world_truth_established": False,
            "whole_arabic_completeness_established": False}


def propose(request):
    """Pure untrusted decision proposal. Only evaluate_* invokes native checks."""
    try:
        request = validate_request(request)
        cases = request["cases"]
        observed = [wire(observe_packet(row["original"])) for row in cases]
        for i, left in enumerate(cases):
            for j in range(i + 1, len(cases)):
                right = cases[j]
                if left["transported_payload"] == right["transported_payload"] and observed[i] != observed[j]:
                    return _decision("CONTRACT_VIOLATION", "FIBER_COLLISION", len(cases),
                                     left["case_id"], right["case_id"])
        for index, row in enumerate(cases):
            original, decoded = row["original"], decode_packet(row["transported_payload"])
            for field, reason in (("binding", "SOURCE_BINDING_CHANGED"),
                                  ("source_context", "SOURCE_CONTEXT_CHANGED")):
                if wire(original[field]) != wire(decoded[field]):
                    return _decision("CONTRACT_VIOLATION", reason, len(cases), row["case_id"])
            if observed[index] != wire(observe_packet(decoded)):
                return _decision("CONTRACT_VIOLATION", "OBSERVATION_CHANGED", len(cases), row["case_id"])
        return _decision("FINITE_CONTRACT_VERIFIED", "ALL_FINITE_CONTRACTS_PRESERVED", len(cases))
    except ResourceLimit:
        return _decision("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT")
    except (InputError, TypeError, UnicodeError, RecursionError):
        return _decision("INVALID_INPUT", "INVALID_REQUEST")


def _native(request):
    """Only the installed executable is callable; no request supplies a path."""
    if not NATIVE.is_file():
        raise FileNotFoundError("Build the pinned meaningPreservationV1 target")
    encoded = _encoded(request, MAX_REQUEST_BYTES)
    with tempfile.TemporaryDirectory(prefix="nabt-meaning-preservation-") as directory:
        output_path = Path(directory) / "native-response.json"
        with output_path.open("wb") as output:
            run = subprocess.run([str(NATIVE)], input=encoded + b"\n", stdout=output,
                                 stderr=subprocess.DEVNULL, timeout=30, check=False)
        if output_path.stat().st_size > MAX_REPORT_BYTES:
            raise ResourceLimit("Native response byte limit")
        result = strict_loads(output_path.read_bytes(), maximum_bytes=MAX_REPORT_BYTES)
    if run.returncode == 2 and wire(result) == wire(_decision("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT")):
        raise ResourceLimit("Native resource limit")
    if run.returncode != 0:
        raise ValueError("Unexpected native process failure")
    return result


def run_identity():
    """Observed installed artifacts; hashes identify execution, never semantics."""
    return {"code": {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in CODE_PATHS},
            "native_path": str(NATIVE.relative_to(ROOT)),
            "native_sha256": sha256(NATIVE.read_bytes()).hexdigest() if NATIVE.is_file() else None}


def _base(mode):
    return {"schema": RESULT_SCHEMA, "law_id": LAW_ID, "query_id": QUERY_ID,
            "codec_id": CODEC_ID, "mode": mode, "status": "DEFER", "reason": None,
            "verified": False, "native_checked": False, "chain_complete": False,
            "finite_contract_verified": False, "authority": "NO_FINITE_CONTRACT_AUTHORITY",
            "input_request": None, "producer": None, "producer_chain_complete": False,
            "contract_request": None, "contract_request_sha256": None,
            "proposal": None, "native_result": None, "observations": [],
            "trace_evidence_kind": "PYTHON_PROJECTION_WITH_SEPARATE_NATIVE_DECISION",
            "execution": None, **FLAGS}


def _finish(result):
    try:
        _encoded(result, MAX_REPORT_BYTES, report=True)
        return result
    except ResourceLimit:
        return {**_base(result["mode"]), "status": "RESOURCE_EXHAUSTED", "reason": "WHOLE_REPORT_LIMIT"}


def _evaluate_contract(request, result):
    proposal = propose(request)
    result["proposal"] = proposal
    if proposal["status"] in ("INVALID_INPUT", "RESOURCE_EXHAUSTED"):
        return {**result, "status": proposal["status"], "reason": proposal["reason"]}
    request = validate_request(request)
    result["contract_request"] = request
    result["contract_request_sha256"] = sha256(wire(request).encode("utf-8")).hexdigest()
    result["observations"] = [{"case_id": row["case_id"],
        "original": observe_packet(row["original"]),
        "decoded": observe_packet(decode_packet(row["transported_payload"])),
        "payload_bytes": len(row["transported_payload"].encode("utf-8")),
        "payload_sha256": sha256(row["transported_payload"].encode("utf-8")).hexdigest()}
        for row in request["cases"]]
    try:
        result["execution"] = run_identity()
        native = _native(request)
        if wire(native) != wire(proposal):
            raise ValueError("Whole typed native decision differs from proposal")
        result.update(status=native["status"], reason=native["reason"], native_checked=True,
                      native_result=native)
        if native["status"] == "FINITE_CONTRACT_VERIFIED":
            result.update(verified=True, chain_complete=True, finite_contract_verified=True,
                          authority="AUTHORED_PREMISES_FINITE_CONTRACT" if result["mode"] == "authored"
                          else "PRODUCTIVE_CLAUSE_SOURCE_BOUND_FINITE_CONTRACT")
    except (FileNotFoundError, PermissionError):
        result.update(status="VERIFICATION_UNAVAILABLE", reason="INSTALLED_NATIVE_UNAVAILABLE")
    except (ResourceLimit, subprocess.TimeoutExpired):
        result.update(status="RESOURCE_EXHAUSTED", reason="NATIVE_RESOURCE_LIMIT")
    except (OSError, ValueError, TypeError, RecursionError):
        result.update(status="VERIFICATION_FAILED", reason="NATIVE_DECISION_OR_TRANSPORT_FAILED")
    return _finish(result)


def evaluate_authored(request):
    result = _base("authored")
    proposal = propose(request)
    if proposal["status"] in ("INVALID_INPUT", "RESOURCE_EXHAUSTED"):
        return {**result, "proposal": proposal, "status": proposal["status"], "reason": proposal["reason"]}
    result["input_request"] = deepcopy(request)
    return _evaluate_contract(request, result)


def _productive_request(request):
    _encoded(request, MAX_REQUEST_BYTES)
    _fields(request, PRODUCTIVE_FIELDS, "productive request")
    _text(request["text"], "source text", MAX_SOURCE_BYTES, content=True)
    for key in ("source_id", "revision", "scope", "ending", "onset"):
        _text(request[key], key)
    _context(request["source_context"])
    _context(request["recipient_context"])
    if request["transported_payload"] is not None:
        decode_packet(request["transported_payload"])
    return deepcopy(request)


def evaluate_productive_request(request):
    result = _base("productive")
    try:
        request = _productive_request(request)
    except ResourceLimit:
        return {**result, "status": "RESOURCE_EXHAUSTED", "reason": "PRODUCTIVE_REQUEST_LIMIT"}
    except (InputError, TypeError, UnicodeError, RecursionError):
        return {**result, "status": "INVALID_INPUT", "reason": "INVALID_PRODUCTIVE_REQUEST"}
    result["input_request"] = request
    # No caller original packet, receipt or hash can bypass this fresh producer.
    from tools import productive_clause_v1 as producer
    binding = {key: request[key] for key in ("source_id", "revision", "scope", "ending", "onset")}
    produced = producer.evaluate(request["text"], **binding)
    result["producer"] = produced
    complete = produced.get("chain_complete") is True and produced.get("verified") is True
    result["producer_chain_complete"] = complete
    if not complete:
        result.update(status=produced["status"], reason="PRODUCTIVE_SOURCE_CHAIN_INCOMPLETE")
        return _finish(result)
    reading = produced["reading"]
    packet = {"binding": {"source_id": request["source_id"], "revision": request["revision"],
        "scope": request["scope"], "source_text": request["text"], "convention": producer.SYNTAX_LAW_ID},
        "source_context": deepcopy(request["source_context"]),
        "alternatives": [{"predicate": reading["verb_lexeme"],
            "subject": {"kind": "entity", "value": reading["subject_lexeme"]},
            "object": {"kind": "entity", "value": reading["object_lexeme"]},
            "positive": True, "tense": reading["tense"], "voice": reading["voice"],
            "force": "asserted"}]}
    contract = {"law_id": LAW_ID, "query_id": QUERY_ID, "codec_id": CODEC_ID,
                "cases": [{"case_id": "productive-input", "original": packet,
                           "transported_payload": encode_packet(packet) if request["transported_payload"] is None
                           else request["transported_payload"]}],
                "recipient_context": deepcopy(request["recipient_context"])}
    return _evaluate_contract(contract, result)


def evaluate_productive(text, *, source_id="input", revision="1", scope="default",
                        ending="wasl", onset="word_initial", source_context,
                        recipient_context, transported_payload=None):
    return evaluate_productive_request({"text": text, "source_id": source_id,
        "revision": revision, "scope": scope, "ending": ending, "onset": onset,
        "source_context": source_context, "recipient_context": recipient_context,
        "transported_payload": transported_payload})


def verify(report, *, expected_request, mode="authored"):
    """Reexecute against independently supplied input; a receipt is no authority."""
    base = {"schema": "nabt.meaning-preservation.verification.v1", "law_id": LAW_ID,
            "valid": False, "replay_matches": False, "status": "INVALID_RECEIPT", **FLAGS}
    try:
        if type(report) is not dict:
            raise InputError("Receipt must be an object")
        encoded = _encoded(report, MAX_REPORT_BYTES, report=True)
        if type(mode) is not str or mode not in ("authored", "productive"):
            raise InputError("Unknown verification mode")
        expected = (evaluate_authored(expected_request) if mode == "authored"
                    else evaluate_productive_request(expected_request))
        if encoded != wire(expected, report=True).encode("utf-8"):
            return {**base, "replay_status": expected["status"]}
        return {**base, "valid": expected["verified"], "replay_matches": True,
                "status": "VERIFIED_RECEIPT" if expected["verified"] else expected["status"]}
    except ResourceLimit:
        return {**base, "status": "RESOURCE_EXHAUSTED"}
    except (InputError, TypeError, UnicodeError, RecursionError, OSError):
        return base
