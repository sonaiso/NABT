"""Scoped acquisition for the native one-axis passage lesson (v1)."""
from __future__ import annotations

from datetime import date
import hashlib
import json
import re
import subprocess

from tools import connected_acquisition_v3 as acquisition
from tools import evidence_lifecycle_v1 as wire
from .reasoning_curriculum import ROOT

LAW = "nabt.grounded-passage.v1"
NATIVE = ROOT / "formal/.lake/build/bin/groundedPassage"
ANSWERS = ("position", "direction", "distance", "crossing", "permission_endpoint",
           "crossing_before_deadline")
BASE = {"id", "revision", "kind", "site", "day"}
FIELDS = {"map": {"gate", "unit", "x"}, "fix": {"subject", "unit", "samples"},
          "track": {"subject", "unit", "samples"}, "message": {"addressee", "text"}}
TARGET = {"map": "maps", "fix": "fixes", "track": "tracks", "message": "permits"}
LIMIT = {"map": 1, "fix": 1, "track": 4, "message": 1}
WORD = r"[ء-غف-يً-ْ]+"
NOTICE = re.compile(rf"(قَبْلَ|حَتَّى) ([0-2][0-9]:[0-5][0-9])، (لَكَ عُبُورُ بَابِ ({WORD}))\.")


def _digest(value):
    return hashlib.sha256(wire.wire(value).encode("utf-8")).hexdigest()


def _day(value):
    wire._text(value, "day", 10)
    if date.fromisoformat(value).isoformat() != value:
        raise ValueError("Use a canonical ISO local date")


def _coordinate(x):
    if type(x) is not int or abs(x) > 10_000_000:
        raise ValueError("Coordinate must be a bounded signed integer")


def _read_message(row, query, digest):
    match = NOTICE.fullmatch(row["text"])
    if not match:
        return None, {"status": "DEFER", "reason": "OUTSIDE_NOTICE_GRAMMAR"}
    cue, clock, _, gate = match.groups()
    if gate != query["gate"]:
        return None, {"status": "OUT_OF_SCOPE", "reason": "OTHER_GATE"}
    hour, minute = map(int, clock.split(":"))
    if hour >= 24:
        return None, {"status": "DEFER", "reason": "INVALID_CLOCK"}
    inspected = []
    for index, onset, ending in ((1, "word_initial", "wasl"), (3, "connected", "waqf")):
        span = match.span(index)
        byte_span = [len(row["text"][:offset].encode()) for offset in span]
        reading = acquisition.read_acquired(match[index], source_id=digest, revision=row["revision"],
                                            scope=_digest(query), onset=onset, ending=ending)
        inspected.append({"message_bytes": byte_span, "reading": reading})
        if reading["status"] in {"RESOURCE_EXHAUSTED", "RESOURCE_LIMIT"}:
            return None, {"status": "RESOURCE_LIMIT", "reason": "OWNER_CHECK_FAILED", "parts": inspected}
        if not reading["verified"]:
            return None, {"status": reading["status"], "reason": "OWNER_CHECK_FAILED", "parts": inspected}
        if not reading["shape_verified"]:
            return None, {"status": "DEFER", "reason": "UNLICENSED_NOTICE_SHAPE", "parts": inspected}
    endpoint = "exclusive" if cue == "قَبْلَ" else "unspecified"
    return ({"id": digest, "minute": hour * 60 + minute, "endpoint": endpoint},
            {"status": "ACQUIRED", "clock_text": clock, "clock_chars": list(match.span(2)),
             "parts": inspected, "gate": gate, "addressee": row["addressee"]})


def _project_row(row, query, digest, active):
    kind = row["kind"]
    for key in FIELDS[kind] & {"subject", "gate", "addressee"}:
        wire._text(row[key], key, 96)
    matching = row["site"] == query["site"] and row["day"] == query["day"]
    if kind == "message":
        wire._text(row["text"], "notice", 1024, content=True)
        if not active:
            return None, {"status": "INACTIVE"}
        if matching and row["addressee"] == query["subject"]:
            return _read_message(row, query, digest)
    else:
        if row["unit"] not in ("m", "cm"):
            raise ValueError("Use m or cm in the exact one-axis profile")
        data = {"id": digest, "cmPerUnit": 100 if row["unit"] == "m" else 1}
        if kind == "map":
            _coordinate(row["x"])
            data["gateX"] = row["x"]
            matching = matching and row["gate"] == query["gate"]
        else:
            samples = row["samples"]
            wire._array(samples, "samples", 48)
            if kind == "fix" and len(samples) != 1:
                raise ValueError("A position fix has exactly one sample")
            previous = -1
            for sample in samples:
                wire._fields(sample, ("minute", "x"), "sample")
                if type(sample["minute"]) is not int or not 0 <= sample["minute"] < 1440:
                    raise ValueError("Minute outside the local day")
                if sample["minute"] <= previous:
                    raise ValueError("Samples require strictly increasing local minutes")
                previous = sample["minute"]
                _coordinate(sample["x"])
            data["samples"] = samples
            matching = matching and row["subject"] == query["subject"]
        if matching:
            return data, {"status": "PROJECTED"}
    return None, {"status": "OUT_OF_SCOPE"}


def evaluate(payload):
    wire._fields(payload, ("law", "query", "sources", "active"), "grounded passage")
    if payload["law"] != LAW:
        raise ValueError("Unknown grounded passage law")
    query = payload["query"]
    wire._fields(query, ("site", "day", "gate", "subject", "facing"), "query")
    for key in ("site", "gate", "subject"):
        wire._text(query[key], key, 96)
    _day(query["day"])
    if query["facing"] not in ("forward", "backward"):
        raise ValueError("Unknown observer orientation")
    wire._names(payload["active"], "active")
    wire._array(payload["sources"], "sources", sum(LIMIT.values()))
    projection = {"scope": _digest(query), "facing": query["facing"], "active": [],
                  **{name: [] for name in TARGET.values()}}
    bindings, counts = {}, dict.fromkeys(LIMIT, 0)
    checked = True
    for row in payload["sources"]:
        if type(row) is not dict or type(row.get("kind")) is not str or row["kind"] not in FIELDS:
            raise ValueError("Unknown passage source kind")
        kind = row["kind"]
        wire._fields(row, BASE | FIELDS[kind], "source")
        for key in ("id", "revision", "site"):
            wire._text(row[key], key, 96)
        _day(row["day"])
        counts[kind] += 1
        if counts[kind] > LIMIT[kind] or row["id"] in bindings:
            raise ValueError("Duplicate identity or too many records of one kind")
        digest = _digest(row)
        data, receipt = _project_row(row, query, digest, row["id"] in payload["active"])
        bindings[row["id"]] = {"digest": digest, **receipt}
        if data is not None:
            projection[TARGET[kind]].append(data)
            if row["id"] in payload["active"]:
                projection["active"].append(digest)
        elif row["id"] in payload["active"] and receipt.get("reason") == "OWNER_CHECK_FAILED":
            checked = False
    if not set(payload["active"]) <= bindings.keys():
        raise ValueError("Unregistered active source")
    result = {"law": LAW, "bindings": bindings, "native_checked": False,
              "action_authority": "NONE", "answers": {}, "status": "VERIFICATION_UNAVAILABLE"}
    if not NATIVE.is_file():
        return result
    try:
        run = subprocess.run([str(NATIVE)], input=json.dumps(wire.wire(projection)) + "\n",
                             capture_output=True, text=True, timeout=15, check=True)
    except subprocess.TimeoutExpired as error:
        raise wire.ResourceLimit("Passage replay timeout") from error
    except (OSError, subprocess.SubprocessError):
        return result
    native = wire.strict_loads(run.stdout, maximum_bytes=2**20)
    if native.get("status") == "RESOURCE_LIMIT":
        raise wire.ResourceLimit("Native passage budget exhausted")
    if native.get("status") != "CHECKED" or native.get("law") != LAW:
        return {**result, "status": "VERIFICATION_FAILED"}
    names = {binding["digest"]: name for name, binding in bindings.items()}
    for kind in ANSWERS:
        paths = [{**p, "sources": [names[s] for s in p["support"]]}
                 for p in native["paths"] if p["kind"] == kind]
        status = "SUPPORTED" if paths else "UNKNOWN"
        if not checked and kind in {"permission_endpoint", "crossing_before_deadline"}:
            status = next(b["status"] for b in bindings.values() if b.get("reason") == "OWNER_CHECK_FAILED")
        result["answers"][kind] = {"status": status, "paths": paths}
    covered = sum(bool(row["paths"]) for row in result["answers"].values())
    result.update(status="SUPPORTED" if covered == len(ANSWERS) else "PARTIAL" if covered else "UNKNOWN",
                  native_checked=True, acquisition_checks_available=checked)
    return result
