"""Replayable conditional classical transformations, with no parser authority.

The installed source inventory authenticates the text used for an interpretation.
It does not establish that a caller's morphological/semantic frame fits a word.
Consequently even a successfully replayed result cannot authorize a free reading.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module
from importlib.resources import files
import json

from .errors import NabtError, resource_limit

LAW_ID = "nabt.classical-transformations.v1"
INVENTORY_SHA256 = "6de39f04e6981ec646a9af98ed3ebb600d1c60bcd498ddfc925d6ba44664061d"
MAX_FRAME_BYTES = 65536
MODULES = (
    "classical_weak", "classical_hamza", "classical_gemination",
    "classical_boundary_affixes",
)
AUTHORITY = "CONDITIONAL_TRANSFORMATION_ONLY"


from nabt import foundation

def _canonical(value):
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise NabtError("INVALID_CLASSICAL_DOCUMENT", "Expected finite UTF-8 JSON") from exc
    return raw


def _json_frame(frame):
    if type(frame) is not dict:
        raise NabtError("INVALID_CLASSICAL_FRAME", "A frame must be a JSON object")
    # JSON coercion of tuples or integer keys would lose the original input.
    visited = 0
    def check(value, depth=0):
        nonlocal visited
        visited += 1
        if visited > 8192:
            raise resource_limit("Classical frame exceeds the structural input budget")
        if depth > 24:
            raise resource_limit("Classical frame nesting exceeds the input budget")
        if type(value) is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise NabtError("INVALID_CLASSICAL_FRAME", "Frame keys must be strings")
                check(item, depth + 1)
        elif type(value) is list:
            for item in value:
                check(item, depth + 1)
        elif type(value) is str and len(value) > MAX_FRAME_BYTES:
            raise resource_limit("Classical string exceeds the input budget")
        elif type(value) not in (str, int, bool, type(None)):
            raise NabtError("INVALID_CLASSICAL_FRAME", "Frame values must be discrete JSON values")
    check(frame)
    if len(_canonical(frame)) > MAX_FRAME_BYTES:
        raise resource_limit("Classical frame exceeds the byte budget", maximum_bytes=MAX_FRAME_BYTES)


def replay_inventory():
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("classical_rule_inventory_v1.json").read_bytes()
        if sha256(raw).hexdigest() != INVENTORY_SHA256:
            raise ValueError("Installed inventory changed")
        inventory = json.loads(raw)
        source_bytes = {}
        for row in inventory["sources"]:
            content = directory.joinpath(row["local_file"]).read_bytes()
            if sha256(content).hexdigest() != row["raw_sha256"]:
                raise ValueError("Installed source identity changed")
            source_bytes[row["source_id"]] = content
        for rule in inventory["rules"]:
            for span in rule["source_spans"]:
                fragment = source_bytes[span["source_id"]][span["start"]:span["end"]]
                if (sha256(fragment).hexdigest() != span["sha256"] or
                        fragment.decode("utf-8") != span["raw_text"]):
                    raise ValueError("Installed source span changed")
        return inventory
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Classical source replay failed",
                        status="DEFER") from exc


def _registry():
    registry = {}
    for name in MODULES:
        module = import_module("nabt." + name)
        for rule_id in module.RULE_IDS:
            if rule_id in registry:
                raise NabtError("INSTALLED_CONTRACT_FAILED", "Duplicate classical rule", status="DEFER")
            registry[rule_id] = module
    if len(registry) != 24:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Expected the fixed 24-law extension", status="DEFER")
    return registry


def catalog():
    foundation.require_foundation('nabt.classical_laws.catalog')
    inventory, registry = replay_inventory(), _registry()
    rows = []
    for rule in inventory["rules"]:
        rid = rule["rule_id"]
        if rid not in registry:
            continue
        rows.append({"rule_id": rid, "title": rule["title"], "source_scope": rule["scope"],
                     "source_blockers": rule["blockers"], "source_text_status": rule["status"],
                     "module": registry[rid].__name__,
                     "source_spans": [{k: span[k] for k in ("source_id", "start", "end", "sha256")}
                                      for span in rule["source_spans"]]})
    if {r["rule_id"] for r in rows} != set(registry):
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Rule absent from source inventory", status="DEFER")
    return {"law_id": LAW_ID, "authority": AUTHORITY, "inventory_sha256": INVENTORY_SHA256,
            "rules": rows, "rule_count": len(rows), "natural_language_completeness": None,
            "whole_book_completeness": False, "free_text_premise_acquisition": False}


def evaluate(rule_id, frame):
    foundation.require_foundation('nabt.classical_laws.evaluate')
    if type(rule_id) is not str:
        raise NabtError("INVALID_CLASSICAL_RULE", "Rule ID must be a string")
    _json_frame(frame)
    registry = _registry()
    if rule_id not in registry:
        raise NabtError("UNKNOWN_CLASSICAL_RULE", "Rule outside the installed extension", status="DEFER")
    # Replay actual sources, not a caller's checksum, approval flag or status.
    inventory = replay_inventory()
    source_rule = next(r for r in inventory["rules"] if r["rule_id"] == rule_id)
    original = deepcopy(frame)
    try:
        result = registry[rule_id].evaluate(rule_id, deepcopy(frame))
    except NabtError:
        raise
    except (TypeError, ValueError, KeyError, IndexError) as exc:
        raise NabtError("INVALID_CLASSICAL_FRAME", str(exc)) from exc
    return {"schema": "nabt.classical-transformation-receipt.v1", "law_id": LAW_ID,
            "authority": AUTHORITY, "rule_id": rule_id, "input_frame": original,
            "input_sha256": sha256(_canonical(original)).hexdigest(),
            "inventory_sha256": INVENTORY_SHA256,
            "source_text_status": source_rule["status"],
            "premises_established_from_free_text": False,
            "grants_language_license": False, "result": result}


def verify(report):
    foundation.require_foundation('nabt.classical_laws.verify')
    if type(report) is not dict or not {"rule_id", "input_frame"} <= set(report):
        raise NabtError("INVALID_CLASSICAL_RECEIPT", "Missing classical receipt input")
    expected = evaluate(report["rule_id"], report["input_frame"])
    if _canonical(report) != _canonical(expected):
        raise NabtError("CLASSICAL_RECEIPT_MISMATCH", "Receipt differs from complete recomputation")
    return {"valid": True, "authority": AUTHORITY, "law_id": LAW_ID,
            "receipt_sha256": sha256(_canonical(expected)).hexdigest(),
            "premises_established_from_free_text": False, "grants_language_license": False}
