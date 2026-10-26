"""Source-relative consequence for a finite, independently parsed Arabic law.

Python proposes complete readings and closure traces. Native Lean reopens the
original source and query, independently parses both, and checks every trace.
The scholarly-source replay and conditional logical validity are distinct.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from tools import verified_reading
from .parser import read_source, read_query

ROOT = Path(__file__).resolve().parents[2]
LAW_ID = "nabt.licensed-inference.v1"
AUTHORITY = "SOURCE_RELATIVE_CONSEQUENCE"


import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

@dataclass(frozen=True)
class InferenceBudget:
    max_source_bytes: int = 65536
    max_query_bytes: int = 8192
    max_clauses: int = 256
    max_readings: int = 64
    max_atoms: int = 512
    max_closure_steps: int = 512

    def __post_init__(self):
        limits = {"max_source_bytes": 65536, "max_query_bytes": 8192,
                  "max_clauses": 256, "max_readings": 64, "max_atoms": 512,
                  "max_closure_steps": 512}
        for key, maximum in limits.items():
            value = getattr(self, key)
            if type(value) is not int or not 0 <= value <= maximum:
                raise ValueError(f"{key} requires a natural at most {maximum}, not a Boolean")


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _base():
    return {"schema": "nabt.licensed-inference-result.v1", "law_id": LAW_ID,
            "authority": "UNVERIFIED_PROPOSAL", "verified": False, "native_checked": False,
            "accepted_language": "nabt.explicit-subject-active.v1",
            "reading_scope": "all readings of the installed finite active-voice grammar",
            "assumptions": ["fixed active-voice lexical interpretation", "one abstract discourse episode",
                            "symbolic addressee and spatial frame", "lexical objects remain symbolic tokens",
                            "source assertions are premises, not world observations"],
            "all_readings_complete": False, "closures_checked": False,
            "all_arabic_complete": False, "world_truth_established": False,
            "premise_world_truth_established": False, "source_interpretation_historically_proved": False,
            "readings": [], "closure_records": [], "unclassified_spans": []}


def _bytes(value, name, maximum):
    if type(value) not in {str, bytes}:
        raise ValueError(name + " must be raw str or bytes")
    if len(value) > maximum:
        raise OverflowError(name + " exceeds byte budget")
    try:
        raw = value.encode("utf-8", "strict") if type(value) is str else value
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise ValueError(name + " must be strict UTF-8") from exc
    if len(raw) > maximum:
        raise OverflowError(name + " exceeds byte budget")
    if not text.strip(" \t\r\n"):
        raise ValueError(name + " is empty")
    return raw, text


def _metadata(value, name):
    if (type(value) is not str or not value or len(value) > 512
            or any(ord(c) < 32 for c in value)):
        raise ValueError(name + " must be bounded nonempty text without controls")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise ValueError(name + " must be strict Unicode") from exc


def _row_status(row):
    if row["positive"] and row["negative"]:
        return "CONFLICT"
    if row["clean_positive"]:
        return "SUPPORTED"
    if row["clean_negative"]:
        return "REFUTED"
    return "DEFER" if row["positive"] or row["negative"] else "UNKNOWN"


def aggregate_evidence(rows):
    """Pure finite calculation, not an admission of caller-provided evidence.

    Only evaluate() applies this after independently checked closures. This
    helper exists for conformance and independent aggregation fixtures.
    """
    fields = ("positive", "negative", "clean_positive", "clean_negative")
    if (type(rows) is not list or len(rows) > 64 or any(type(r) is not dict
            or set(r) != set(fields) or any(type(r[f]) is not bool for f in fields) for r in rows)):
        raise ValueError("expected at most 64 exact four-Boolean evidence records")
    summary = {}
    for name in fields:
        summary["credulous_" + name] = any(r[name] for r in rows)
        summary["skeptical_" + name] = bool(rows) and all(r[name] for r in rows)
    summary["within_reading_conflict"] = any(r["positive"] and r["negative"] for r in rows)
    summary["cross_reading_opposition"] = any(
        i != j and left["positive"] and right["negative"]
        for i, left in enumerate(rows) for j, right in enumerate(rows))
    if summary["within_reading_conflict"]:
        status = "CONFLICT"
    elif summary["cross_reading_opposition"]:
        status = "DISAGREEMENT"
    elif summary["skeptical_clean_positive"] and not summary["credulous_negative"]:
        status = "SUPPORTED"
    elif summary["skeptical_clean_negative"] and not summary["credulous_positive"]:
        status = "REFUTED"
    elif not summary["credulous_positive"] and not summary["credulous_negative"]:
        status = "UNKNOWN"
    else:
        status = "DEFER"
    return {"status": status, "aggregate": summary}


def _closure(clauses, query, budget):
    facts = [c["atom"] for c in clauses if c["kind"] == "fact"]
    rules = [c for c in clauses if c["kind"] == "rule"]
    known, steps = verified_reading.closure(facts, rules)
    signed = {verified_reading.key(a) for a in known}
    blocked = {a for a in signed if verified_reading.opposite(a) in signed}
    clean_facts = [a for a in facts if verified_reading.key(a) not in blocked]
    clean_rules = [r for r in rules if all(verified_reading.key(a) not in blocked
                                         for a in [*r["body"], r["head"]])]
    clean_known, clean_steps = verified_reading.closure(clean_facts, clean_rules)
    if max(len(known), len(clean_known)) > budget.max_atoms:
        raise OverflowError("MAX_ATOMS")
    if max(len(steps), len(clean_steps)) > budget.max_closure_steps:
        raise OverflowError("MAX_CLOSURE_STEPS")
    return {"clauses": clauses, "query": query, "steps": steps, "known": known,
            "clean_steps": clean_steps, "clean_known": clean_known}


def _evidence(reading):
    query = verified_reading.key(reading["query"])
    opposite = verified_reading.opposite(query)
    known = {verified_reading.key(a) for a in reading["known"]}
    clean = {verified_reading.key(a) for a in reading["clean_known"]}
    return {"positive": query in known, "negative": opposite in known,
            "clean_positive": query in clean, "clean_negative": opposite in clean}


def _expected_success(certificate):
    evidences = [_evidence(r) for r in certificate["readings"]]
    aggregate = aggregate_evidence(evidences)
    source = certificate["source"]
    return {"law_id": LAW_ID, "verified": True, "status": aggregate["status"],
            "authority": AUTHORITY, "all_arabic_complete": False, "world_truth_established": False,
            "source_id": source["identity"], "revision": source["revision"], "source_scope": source["scope"],
            "source_text": source["text"], "query_text": certificate["query_text"],
            "reading_count": len(certificate["readings"]),
            "rows": [{"clauses": reading["clauses"], "query": reading["query"],
                      **evidence, "status": _row_status(evidence)}
                     for reading, evidence in zip(certificate["readings"], evidences)],
            "aggregate": aggregate["aggregate"]}


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate native JSON key: " + key)
        result[key] = value
    return result


def _native(source_raw, query_raw, certificate, binding):
    if (type(binding) is not dict or set(binding) != {"identity", "revision", "scope"}
            or any(type(value) is not str or not value for value in binding.values())):
        raise ValueError("expected binding requires independent identity, revision and scope")
    encoded = wire(certificate).encode()
    if len(encoded) > 1048576:
        raise OverflowError("MAX_CERTIFICATE_BYTES")
    executable = ROOT / "formal/.lake/build/bin/licensedInference"
    with tempfile.TemporaryDirectory(prefix="nabt-licensed-") as directory:
        directory = Path(directory)
        source_path, query_path, cert_path = [directory / name for name in ("source.txt", "query.txt", "certificate.json")]
        source_path.write_bytes(source_raw)
        query_path.write_bytes(query_raw)
        cert_path.write_bytes(encoded)
        run = subprocess.run([str(executable), str(source_path), str(query_path), str(cert_path),
                              binding["identity"], binding["revision"], binding["scope"]],
                             capture_output=True, text=True, timeout=60, check=False)
    result = json.loads(run.stdout, object_pairs_hook=_unique,
                        parse_constant=lambda s: (_ for _ in ()).throw(ValueError("nonfinite native number")))
    if type(result) is not dict or (result.get("verified") is True and run.returncode != 0):
        raise ValueError("native process and response disagree")
    return result


def _failure(result, expected_reason):
    keys = {"law_id", "verified", "status", "error", "message", "authority",
            "all_arabic_complete", "world_truth_established"}
    if (set(result) != keys or result["law_id"] != LAW_ID or result["verified"] is not False
            or result["authority"] != AUTHORITY or result["all_arabic_complete"] is not False
            or result["world_truth_established"] is not False or type(result["message"]) is not str
            or type(result["status"]) is not str or type(result["error"]) is not str):
        raise ValueError("native failure response identity differs")
    if result["status"] in {"RESOURCE_LIMIT", "RESOURCE_EXHAUSTED"} or result["error"] == "RESOURCE_LIMIT":
        return "RESOURCE_EXHAUSTED"
    if expected_reason is not None and result["status"] == "UNKNOWN" and result["error"] == expected_reason:
        return "UNKNOWN"
    raise ValueError("native parser or certificate rejected the full proposal: " + str(result["error"]))


def evaluate(source_text, query_text, *, source_id="user_text", revision="1", scope="default",
             time="unspecified", budget=None, root=ROOT):
    foundation.require_foundation('tools.licensed_inference.runtime.evaluate')
    output = _base()
    if budget is None:
        budget = InferenceBudget()
    try:
        if type(budget) is not InferenceBudget:
            raise ValueError("budget must be InferenceBudget")
        source_raw, source_text = _bytes(source_text, "source", budget.max_source_bytes)
        query_raw, query_text = _bytes(query_text, "query", budget.max_query_bytes)
        foundation.validate_source(source_raw)
        foundation.validate_source(query_raw)
        for key, value in {"source_id": source_id, "revision": revision, "scope": scope, "time": time}.items():
            _metadata(value, key)
    except OverflowError as exc:
        return {**output, "status": "RESOURCE_EXHAUSTED", "reason": str(exc)}
    except ValueError as exc:
        return {**output, "status": "INVALID_INPUT", "reason": str(exc)}
    native_scope = wire({"scope": scope, "time": time})
    output["source"] = {"source_id": source_id, "revision": revision, "raw_text": source_text,
                        "bytes": len(source_raw), "sha256": digest(source_raw)}
    output["query"] = {"raw_text": query_text, "bytes": len(query_raw), "sha256": digest(query_raw)}
    output["binding"] = {"source_id": source_id, "revision": revision, "scope": scope,
                         "time": time, "native_scope": native_scope, "authority": "EXPLICIT_DISCOURSE_BINDING"}
    try:
        from .sources import build_inventory
        inventory = build_inventory(root)
    except (OSError, ValueError, ImportError) as exc:
        return {**output, "status": "SOURCE_UNAVAILABLE", "reason": str(exc)}
    output["source_review_sha256"] = inventory["review_sha256"]
    parts = source_text.split(".")
    statement_count = len(parts) - (1 if not parts[-1].strip(" \t\r\n") else 0)
    if statement_count > budget.max_clauses:
        return {**output, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_CLAUSES"}
    parsed, query = read_source(source_text), read_query(query_text)
    output["source_segments"] = parsed["segments"]
    output["unclassified_spans"] = [{**s["span"], "reason": s["reason"]}
                                     for s in parsed["segments"] if s["status"] != "PROPOSED"]
    reason = "OUTSIDE_FRAGMENT" if query is None else parsed["reason"]
    output["parse_status"] = "PROPOSED_COMPLETE_READING" if reason is None else "UNKNOWN"
    output["parse_reason"] = reason
    certificate = {"law_id": LAW_ID,
        "source": {"identity": source_id, "revision": revision, "scope": native_scope, "text": source_text},
        "query_text": query_text, "readings": []}
    try:
        if len(parsed["segments"]) > budget.max_clauses:
            raise OverflowError("MAX_CLAUSES")
        if reason is None:
            if budget.max_readings < 1:
                raise OverflowError("MAX_READINGS")
            certificate["readings"] = [_closure(parsed["clauses"], query, budget)]
        output["proposal"] = certificate
        native = _native(source_raw, query_raw, certificate,
                         {"identity": source_id, "revision": revision, "scope": native_scope})
        if native.get("verified") is True:
            if reason is not None or wire(native) != wire(_expected_success(certificate)):
                raise ValueError("native complete response differs from exact source/query/readings/closures")
            output.update(status=native["status"], authority=AUTHORITY, verified=True, native_checked=True,
                          all_readings_complete=True, closures_checked=True, parse_status="CHECKED_COMPLETE_READING",
                          readings=native["rows"], closure_records=certificate["readings"],
                          aggregate=native["aggregate"], native_result=native,
                          reason="CHECKED_INSTALLED_GRAMMAR_AND_SOURCE_THEORY")
        else:
            output.update(status=_failure(native, reason), reason=native["error"], native_result=native)
    except (OverflowError, subprocess.TimeoutExpired) as exc:
        output.update(status="RESOURCE_EXHAUSTED", reason=str(exc))
    except (OSError, ValueError, KeyError) as exc:
        output.update(status="VERIFICATION_UNAVAILABLE", reason=str(exc))
    return output
