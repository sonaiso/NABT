"""Bounded evidence decisions with exact, independent Lean certificate replay.

This adapter acquires no Arabic interpretation or hidden intention. Authored
premises remain authored; the installed agency profile replays one frozen
agency field. Neither profile establishes truth of an external physical event.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "formal/.lake/build/bin/epistemicMeasurement"
LAW_ID = "nabt.epistemic-measurement.v1"
MAX_INTEGER = 2**53 - 1
MAX_REQUEST_BYTES = 1024 * 1024
USGS_RAW_PATH = ROOT / "evidence/epistemic_measurement_v1/observations/usgs_tohoku_raw.json"
USGS_RAW_SHA256 = "d9cf0301f748786d5ff881edba71e1b19c5b5008b3abeb893e8e88240433ba4a"
USGS_EVENT = "official20110311054624120_30"
USGS_REVISION = "1792147089160"
USGS_POINTER = "/properties/mag"
USGS_PROFILE = "usgs_snapshot_v1"
AUTHORED_PROFILE = "authored_controls_v1"
STATUSES = frozenset({"SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "RESOURCE_LIMIT"})
KEY_FIELDS = {"axis", "entity", "predicate", "value", "unit", "context", "time", "place"}
CERTIFICATE_FIELDS = {"status", "support_ids", "refutation_ids", "selected_ids"}
PROOF_SCOPE = {
    AUTHORED_PROFILE: "Conditional classification of the complete supplied AUTHORED_SCENARIO ledger under the installed law; no real self-report authentication, Arabic acquisition, hidden motive, or external-world truth is proved.",
    USGS_PROFILE: "Correspondence to /properties/mag in a retained preferred USGS agency record, with exact revision, type, time and place. Raw acquisition is replayed by the adapter; Lean checks the projected premises. Magnitude uncertainty is unspecified, sensor calibration is unverified, and physical world truth is not established.",
}


import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

class InputError(ValueError):
    """The supplied value does not satisfy this versioned wire contract."""


class ResourceLimit(InputError):
    """The declared bounded contract cannot evaluate this request."""


def wire(value: Any) -> str:
    """Canonical UTF-8 JSON used for input/receipt binding, never lossy numbers."""
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        text.encode("utf-8")
        return text
    except (TypeError, ValueError, UnicodeError) as exc:
        raise InputError("Value is not canonical UTF-8 JSON") from exc


def digest(value: Any) -> str:
    return sha256(wire(value).encode("utf-8")).hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in items:
        if key in result:
            raise InputError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def _bad_number(value: str) -> None:
    raise InputError("Noncanonical JSON number: " + value)


def _integer(value: str) -> int:
    if re.fullmatch(r"0|-?[1-9][0-9]*", value) is None:
        raise InputError("Noncanonical JSON integer")
    if len(value) > 17:
        raise InputError("Integer exceeds exact bound")
    number = int(value)
    if abs(number) > MAX_INTEGER:
        raise InputError("Integer exceeds exact bound")
    return number


def strict_loads(raw: str | bytes) -> Any:
    """Domain JSON contains no floats; selected agency decimals use a separate reader."""
    if type(raw) not in (str, bytes):
        raise InputError("JSON text required")
    try:
        encoded = raw.encode("utf-8") if type(raw) is str else raw
        if len(encoded) > MAX_REQUEST_BYTES:
            raise ResourceLimit("JSON byte limit")
        return json.loads(encoded.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_float=_bad_number, parse_int=_integer, parse_constant=_bad_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InputError("Malformed JSON") from exc


def _fields(value: Any, fields: set[str], label: str) -> None:
    if type(value) is not dict or set(value) != fields:
        raise InputError(label + " has missing or unexpected fields")


def _text(value: Any, label: str, *, content: bool = False, limit: int | None = None) -> None:
    if type(value) is not str or not value.strip():
        raise InputError(label + " must be a nonempty string")
    if not content and any(ord(char) < 32 for char in value):
        raise InputError(label + " contains a control character")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise InputError(label + " is not UTF-8") from exc
    if size > (limit or (65536 if content else 4096)):
        raise ResourceLimit(label + " exceeds byte limit")


def _array(value: Any, label: str, limit: int) -> None:
    if type(value) is not list:
        raise InputError(label + " must be an array")
    if len(value) > limit:
        raise ResourceLimit(label + " exceeds item limit")


def _names(value: Any, label: str, *, unique: bool = True, limit: int = 256) -> None:
    _array(value, label, limit)
    for item in value:
        _text(item, label)
    if unique and len(set(value)) != len(value):
        raise InputError(label + " contains duplicate identities")


def _key(key: Any) -> None:
    _fields(key, KEY_FIELDS, "key")
    if key["axis"] not in ("reported_motive", "recorded_observation", "hidden_motive"):
        raise InputError("Unknown epistemic axis")
    for name in KEY_FIELDS:
        _text(key[name], "key." + name, limit=32 if name == "time" else None)
    if re.fullmatch(r"0|-?[1-9][0-9]*", key["time"]) is None:
        raise InputError("Time is not a canonical signed decimal string")
    if abs(int(key["time"])) > MAX_INTEGER:
        raise InputError("Time exceeds exact integer bound")


def _source(source: Any) -> None:
    _fields(source, {"identity", "revision", "content"}, "source")
    _text(source["identity"], "source.identity")
    _text(source["revision"], "source.revision")
    _text(source["content"], "source.content", content=True)


def _query(query: Any) -> None:
    _fields(query, {"key", "positive", "origin"}, "query")
    _key(query["key"])
    _text(query["origin"], "query.origin")
    if type(query["positive"]) is not bool:
        raise InputError("query.positive must be a Boolean")


def _budget(budget: Any) -> None:
    if type(budget) is not int or budget < 0:
        raise InputError("budget must be a nonnegative integer, not a Boolean or float")
    if budget > 128:
        raise ResourceLimit("budget exceeds 128")


def validate_certificate(certificate: Any) -> None:
    _fields(certificate, CERTIFICATE_FIELDS, "certificate")
    if type(certificate["status"]) is not str or certificate["status"] not in STATUSES:
        raise InputError("Unknown certificate status")
    for field in ("support_ids", "refutation_ids", "selected_ids"):
        # A malformed proposal remains checkable; preserve duplicates and order.
        _names(certificate[field], "certificate." + field, unique=False, limit=128)


def validate_request(request: Any) -> dict:
    """Validate shape only. Inactive sources and nonclosed ancestry are evidence failures."""
    _fields(request, {"query", "active_sources", "origins", "interpretations", "budget", "certificate"}, "request")
    _query(request["query"])
    _budget(request["budget"])
    for field, limit in (("active_sources", 128), ("origins", 256), ("interpretations", 128)):
        _array(request[field], field, limit)
    for source in request["active_sources"]:
        _source(source)
    source_ids = [source["identity"] for source in request["active_sources"]]
    if len(set(source_ids)) != len(source_ids):
        raise InputError("Duplicate active source identity")
    for origin in request["origins"]:
        _fields(origin, {"id", "parents"}, "origin")
        _text(origin["id"], "origin.id")
        _names(origin["parents"], "origin.parents")
    origin_ids = [origin["id"] for origin in request["origins"]]
    if len(set(origin_ids)) != len(origin_ids):
        raise InputError("Duplicate origin identity")
    known = set(origin_ids)
    if request["query"]["origin"] not in known:
        raise InputError("Unknown query origin")
    if any(parent not in known for origin in request["origins"] for parent in origin["parents"]):
        raise InputError("Unknown parent origin")
    evidence_ids = []
    for evidence in request["interpretations"]:
        _fields(evidence, {"id", "source", "key", "positive", "kind", "origin", "ancestry"}, "interpretation")
        _text(evidence["id"], "interpretation.id")
        evidence_ids.append(evidence["id"])
        _source(evidence["source"])
        _key(evidence["key"])
        if type(evidence["positive"]) is not bool:
            raise InputError("interpretation.positive must be a Boolean")
        if evidence["kind"] not in ("self_report", "observation", "lexical", "grammar", "hypothetical", "quotation"):
            raise InputError("Unknown evidence kind")
        _text(evidence["origin"], "interpretation.origin")
        _names(evidence["ancestry"], "interpretation.ancestry")
        if evidence["origin"] not in known or any(item not in known for item in evidence["ancestry"]):
            raise InputError("Unknown evidence ancestry origin")
    if len(set(evidence_ids)) != len(evidence_ids):
        raise InputError("Duplicate interpretation identity")
    if request["certificate"] is not None:
        validate_certificate(request["certificate"])
    if len(wire(request).encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ResourceLimit("Request byte limit")
    return request


def propose(request: dict) -> dict:
    """Python proposal independently enumerates every admissible ledger item."""
    validate_request(request)
    empty = {"status": "RESOURCE_LIMIT", "support_ids": [], "refutation_ids": [], "selected_ids": []}
    if len(request["interpretations"]) > request["budget"]:
        return empty
    query = request["query"]
    permitted = {"reported_motive": "self_report", "recorded_observation": "observation"}.get(query["key"]["axis"])
    selected = []
    parents = {origin["id"]: set(origin["parents"]) for origin in request["origins"]}
    for evidence in request["interpretations"]:
        ancestry = set(evidence["ancestry"])
        if (evidence["key"] != query["key"] or evidence["source"] not in request["active_sources"]
                or evidence["kind"] != permitted or evidence["origin"] not in ancestry
                or query["origin"] in ancestry):
            continue
        if any(not parents[node].issubset(ancestry) for node in ancestry):
            continue
        selected.append(evidence)
    supports = [item["id"] for item in selected if item["positive"] == query["positive"]]
    refutes = [item["id"] for item in selected if item["positive"] != query["positive"]]
    status = "CONFLICT" if supports and refutes else "SUPPORTED" if supports else "REFUTED" if refutes else "UNKNOWN"
    return {"status": status, "support_ids": supports, "refutation_ids": refutes,
            "selected_ids": [item["id"] for item in selected]}


def _source_binding(source: dict, *, agency: bool = False) -> dict:
    return {"identity": source["identity"], "revision": source["revision"],
            "content_sha256": sha256(source["content"].encode("utf-8")).hexdigest(),
            "raw_sha256": USGS_RAW_SHA256 if agency else None,
            "raw_path": "evidence/epistemic_measurement_v1/observations/usgs_tohoku_raw.json" if agency else None,
            "field_pointer": USGS_POINTER if agency else None}


def _agency_request(input_value: dict) -> tuple[dict, list[dict]]:
    _fields(input_value, {"query", "budget"}, "agency input")
    _query(input_value["query"])
    _budget(input_value["budget"])
    raw = USGS_RAW_PATH.read_bytes()
    if sha256(raw).hexdigest() != USGS_RAW_SHA256:
        raise InputError("Installed USGS raw source digest mismatch")
    try:
        source_data = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                                 parse_float=Decimal, parse_constant=_bad_number)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("Malformed installed USGS source") from exc
    properties = source_data["properties"]
    # Check the selected preferred field, never borrow another origin's magnitude.
    if (source_data["id"] != USGS_EVENT or type(properties["updated"]) is not int
            or str(properties["updated"]) != USGS_REVISION
            or type(properties["time"]) is not int or properties["time"] != 1299822384120
            or properties["mag"] != Decimal("9.1") or properties["magType"] != "mww"
            or source_data["geometry"]["coordinates"] != [Decimal("142.373"), Decimal("38.297"), 29]):
        raise InputError("Installed USGS selected fields differ from profile")
    value = str(properties["mag"])
    key = {"axis": "recorded_observation", "entity": source_data["id"],
           "predicate": "magnitude:" + properties["magType"], "value": value,
           "unit": "dimensionless", "context": "usgs.preferred-event.v1",
           "time": str(properties["time"]),
           "place": ",".join(str(part) for part in source_data["geometry"]["coordinates"])}
    projection = {"source_sha256": USGS_RAW_SHA256, "pointer": USGS_POINTER,
                  "value": value, "revision": str(properties["updated"])}
    source = {"identity": "USGS:" + USGS_EVENT, "revision": USGS_REVISION, "content": wire(projection)}
    request = {"query": deepcopy(input_value["query"]), "budget": input_value["budget"],
               "certificate": None, "active_sources": [source],
               "origins": [{"id": "query", "parents": []}, {"id": "agency-source", "parents": []}],
               "interpretations": [{"id": "usgs.preferred.magnitude", "source": deepcopy(source),
                                    "key": key, "positive": True, "kind": "observation",
                                    "origin": "agency-source", "ancestry": ["agency-source"]}]}
    return validate_request(request), [_source_binding(source, agency=True)]


def build_request(input_value: Any, *, source_profile: str = AUTHORED_PROFILE) -> tuple[dict, list[dict]]:
    """Only normalized input and installed profile reach the runtime; no gold labels."""
    if type(source_profile) is not str:
        raise InputError("source_profile must be a string")
    if source_profile == USGS_PROFILE:
        return _agency_request(input_value)
    if source_profile != AUTHORED_PROFILE:
        raise InputError("Unknown installed source profile")
    request = deepcopy(validate_request(input_value))
    if request["certificate"] is not None:
        raise InputError("Runtime inputs must not supply a certificate")
    bindings = []
    seen = set()
    for source in request["active_sources"] + [item["source"] for item in request["interpretations"]]:
        identity = wire(source)
        if identity not in seen:
            bindings.append(_source_binding(source))
            seen.add(identity)
    return request, bindings


def _native(request: dict) -> dict:
    """Fixed installed Lean executable; no caller-supplied checker or command."""
    validate_request(request)
    completed = subprocess.run([str(NATIVE)], input=wire(request) + "\n", text=True,
                               capture_output=True, timeout=30, cwd=ROOT, check=False)
    if completed.returncode != 0 or completed.stderr.strip():
        raise InputError("Native checker exited unsuccessfully")
    if len(completed.stdout.encode("utf-8")) > 256 * 1024:
        raise ResourceLimit("Native result byte limit")
    result = strict_loads(completed.stdout)
    if type(result) is not dict:
        raise InputError("Native result must be an object")
    return result


def _checked_native(result: dict, proposed: dict) -> bool:
    expected_fields = {"law_id", "status", "observed_status", "support_ids", "refutation_ids", "selected_ids",
                       "certificate_checked", "world_truth_established", "hidden_motive_established", "all_arabic_complete"}
    if set(result) != expected_fields or result["law_id"] != LAW_ID:
        return False
    if result["certificate_checked"] is not True:
        return False
    if any(result[field] is not False for field in ("world_truth_established", "hidden_motive_established", "all_arabic_complete")):
        return False
    try:
        validate_certificate({field: result[field] for field in CERTIFICATE_FIELDS})
    except InputError:
        return False
    return result["observed_status"] == proposed["status"] and all(result[field] == proposed[field] for field in CERTIFICATE_FIELDS)


def execute_request(input_value: Any, *, source_profile: str = AUTHORED_PROFILE) -> dict:
    """Propose, replay, and bind one decision. Missing native is never a proof."""
    foundation.require_foundation('tools.epistemic_measurement.execute_request')
    profile_label = source_profile if type(source_profile) is str else "INVALID_PROFILE"
    execution = {"input": None, "input_sha256": None, "proposal_sha256": None,
                 "native_result_sha256": None, "native_sha256": None, "proposal": None,
                 "native_result": None, "error": None, "source_profile": profile_label}
    result = {"status": "UNMEASURED", "observed": None, "native_checked": False,
              "certificate_checked": False, "source_bindings": [],
              "proof_scope": PROOF_SCOPE.get(profile_label, "Unknown profile; no proof."),
              "evidence_class": "AGENCY_RECORD" if source_profile == USGS_PROFILE else "AUTHORED_SCENARIO",
              "execution": execution, "world_truth_established": False, "hidden_motive_established": False,
              "free_arabic_acquisition_measured": False, "whole_arabic_complete": False}
    try:
        request, bindings = build_request(input_value, source_profile=source_profile)
        try:
            for source in request["active_sources"]:
                foundation.validate_source(source["content"])
        except ValueError as error:
            raise InputError("Malformed source content representation") from error
        result["source_bindings"] = bindings
        proposed = propose(request)
        request["certificate"] = proposed
        validate_request(request)  # The final native line includes the certificate.
        execution.update(input=request, input_sha256=digest(request), proposal_sha256=digest(proposed), proposal=proposed)
        if not NATIVE.is_file():
            execution["error"] = "NATIVE_UNAVAILABLE"
        else:
            native_hash = sha256(NATIVE.read_bytes()).hexdigest()
            execution["native_sha256"] = native_hash
            native_result = _native(request)
            execution["native_result"] = native_result
            execution["native_result_sha256"] = digest(native_result)
            if sha256(NATIVE.read_bytes()).hexdigest() != native_hash:
                execution["error"] = "NATIVE_CHANGED_DURING_CHECK"
            elif _checked_native(native_result, proposed):
                result.update(status=proposed["status"], observed=deepcopy(proposed),
                              native_checked=True, certificate_checked=True)
            elif (set(native_result) == {"law_id", "status", "reason", "world_truth_established", "hidden_motive_established", "all_arabic_complete"}
                  and native_result["law_id"] == LAW_ID
                  and native_result["status"] in ("INVALID_INPUT", "RESOURCE_LIMIT")
                  and type(native_result["reason"]) is str
                  and all(native_result[key] is False for key in ("world_truth_established", "hidden_motive_established", "all_arabic_complete"))):
                result["status"] = native_result["status"]
                execution["error"] = "NATIVE_" + native_result["status"] + ": " + native_result["reason"]
            else:
                execution["error"] = "NATIVE_CERTIFICATE_REJECTED_OR_MALFORMED"
    except ResourceLimit as exc:
        result["status"] = "RESOURCE_LIMIT"
        execution["error"] = str(exc)
    except (InputError, OSError, KeyError, TypeError, RecursionError) as exc:
        result["status"] = "INVALID_INPUT" if isinstance(exc, (InputError, KeyError, TypeError, RecursionError)) else "UNMEASURED"
        execution["error"] = str(exc)
    except subprocess.TimeoutExpired:
        execution["error"] = "NATIVE_TIMEOUT"
    result["receipt_sha256"] = digest(result)
    return result
