#!/usr/bin/env python3
"""Replay bounded classical Arabic witnesses and explicit formal interpretations.

The installed catalog selects exact editions and passages. Its pin is policy,
not a field supplied by the claim. Text attestation, an author's prescription,
an interpreted formal model and application to new Arabic remain distinct.
This repository tool does not alter the installed NABT runtime or its gold data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION = "nabt.classical-language-evidence.v1"
CATALOG_PATH = "evidence/classical_language/catalog_v2.json"
CATALOG_SHA256 = "65c83b8a76c2532604f90949352caa6c2c3f03b2f0c958066a2cb20390edff3f"
MAX_JSON_BYTES = 512 * 1024
MAX_REPORT_BYTES = 2 * 1024 * 1024
MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_TEXT_BYTES = 64 * 1024
MAX_JSON_NODES = 20000
COURSES = ("nasb", "jarr", "raf", "jazm", "fath", "damm", "kasr", "waqf")
SURFACES = ("fatha", "kasra", "damma", "sukun")
COURSE_SURFACE = {
    "nasb": "fatha", "jarr": "kasra", "raf": "damma", "jazm": "sukun",
    "fath": "fatha", "damm": "damma", "kasr": "kasra", "waqf": "sukun",
}
OPERATORS = ("inna", "anna", "kaanna", "lakinna", "layta", "laalla")
FORMS = ("full", "light")
MA_STATUSES = ("absent", "kaffa", "unknown")


import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

class EvidenceUnavailable(ValueError):
    """The installed evidence could not be reopened under its approved pins."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _plain_json(value: Any, *, report: bool = False) -> None:
    remaining = MAX_JSON_NODES * (4 if report else 1)
    def visit(item: Any, depth: int) -> None:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > (24 if report else 20):
            raise ValueError("JSON structure budget exceeded")
        if type(item) is str:
            if len(item.encode("utf-8")) > MAX_TEXT_BYTES:
                raise ValueError("text budget exceeded")
        elif item is None or type(item) is bool:
            pass
        elif type(item) is int:
            if not 0 <= item <= 100000000:
                raise ValueError("integer outside the declared JSON domain")
        elif type(item) is list:
            if len(item) > 256:
                raise ValueError("list budget exceeded")
            for child in item:
                visit(child, depth + 1)
        elif type(item) is dict:
            if len(item) > 128 or any(type(key) is not str for key in item):
                raise ValueError("invalid object keys")
            for key, child in item.items():
                visit(key, depth + 1)
                visit(child, depth + 1)
        else:
            raise ValueError("only inert JSON values are supported")
    visit(value, 0)
    if len(_canonical(value)) + (1 if report else 0) > (MAX_REPORT_BYTES if report else MAX_JSON_BYTES):
        raise ValueError("JSON byte budget exceeded")


def _object(value: Any, keys: set[str], name: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{name} must have exactly {sorted(keys)}")
    return value


def _text(value: Any, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _enum(value: Any, values: tuple[str, ...], name: str) -> str:
    if type(value) is not str or value not in values:
        raise ValueError(f"unsupported {name}")
    return value


def _strict_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _decode(data: bytes, *, report: bool = False) -> Any:
    if len(data) > (MAX_REPORT_BYTES if report else MAX_JSON_BYTES):
        raise ValueError("JSON byte budget exceeded")
    value = json.loads(data.decode("utf-8"), object_pairs_hook=_strict_object,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    _plain_json(value, report=report)
    return value


def _read_json(path: Path, *, report: bool = False) -> Any:
    with path.open("rb") as stream:
        return _decode(stream.read((MAX_REPORT_BYTES if report else MAX_JSON_BYTES) + 1), report=report)


def _inside(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    if type(relative) is not str or Path(relative).is_absolute():
        raise EvidenceUnavailable("invalid installed source path")
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise EvidenceUnavailable("installed source path leaves the repository")
    return result


def _catalog(root: Path) -> tuple[dict, dict[str, dict], dict[str, dict]]:
    try:
        with _inside(root, CATALOG_PATH).open("rb") as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
        if _digest(raw) != CATALOG_SHA256:
            raise EvidenceUnavailable("installed catalog digest mismatch")
        value = _decode(raw)
        if value.get("version") != VERSION:
            raise EvidenceUnavailable("unsupported installed catalog")
        sources = {row["source_id"]: row for row in value["sources"]}
        records = {row["record_id"]: row for row in value["records"]}
        if len(sources) != len(value["sources"]) or len(records) != len(value["records"]):
            raise EvidenceUnavailable("duplicate installed source or record")
        return value, sources, records
    except (OSError, UnicodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, EvidenceUnavailable):
            raise
        raise EvidenceUnavailable(f"installed catalog unavailable: {exc}") from exc


def _source(root: Path, spec: dict) -> bytes:
    try:
        with _inside(root, spec["local_path"]).open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES or len(raw) != spec["bytes"]:
            raise EvidenceUnavailable("source byte budget or recorded length mismatch")
        if _digest(raw) != spec["sha256"]:
            raise EvidenceUnavailable(f"source digest mismatch: {spec['source_id']}")
        raw.decode("utf-8", errors="strict")
        return raw
    except (OSError, UnicodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, EvidenceUnavailable):
            raise
        raise EvidenceUnavailable(f"source unavailable: {exc}") from exc


def _passage(raw: bytes, record: dict) -> dict:
    try:
        start, end = record["start"], record["end"]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw):
            raise EvidenceUnavailable("invalid installed passage boundaries")
        part = raw[start:end]
        if len(part) > MAX_TEXT_BYTES or _digest(part) != record["span_sha256"]:
            raise EvidenceUnavailable("installed passage digest or size mismatch")
        text = part.decode("utf-8", errors="strict")
        projection = record.get("lexical_projection")
        if projection is not None:
            if projection["root_token"] != f"({projection['root']})":
                raise EvidenceUnavailable("unsupported lexical heading projection")
            if projection["root_token"] not in text or projection["gloss"] not in text:
                raise EvidenceUnavailable("lexical projection absent from the raw passage")
        return {"source_id": record["source_id"], "start": start, "end": end,
                "sha256": _digest(part), "text": text}
    except (UnicodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, EvidenceUnavailable):
            raise
        raise EvidenceUnavailable(f"passage unavailable: {exc}") from exc


def grammar_result(law_id: str, inputs: dict) -> dict:
    """Conditional interpretations of selected passages, not free-text parsing."""
    if law_id == "sibawayhi-course-v1":
        _object(inputs, {"course"}, "course inputs")
        course = _enum(inputs["course"], COURSES, "course")
        return {"surface": COURSE_SURFACE[course]}
    if law_id == "sibawayhi-surface-v1":
        _object(inputs, {"surface"}, "surface inputs")
        surface = _enum(inputs["surface"], SURFACES, "surface")
        return {"courses": [c for c in COURSES if COURSE_SURFACE[c] == surface]}
    if law_id == "qatr-inna-v1":
        _object(inputs, {"operator", "form", "ma"}, "inna inputs")
        operator = _enum(inputs["operator"], OPERATORS, "inna operator")
        form = _enum(inputs["form"], FORMS, "inna form")
        ma = _enum(inputs["ma"], MA_STATUSES, "ma status")
        if form == "light" or ma == "unknown":
            return {"options": []}
        if ma == "absent":
            return {"options": ["governed"]}
        return {"options": ["governed", "blocked"] if operator == "layta" else ["blocked"]}
    if law_id == "jurjani-awamil-partition-v1":
        _object(inputs, set(), "partition inputs")
        return {"samai": 91, "qiyasi": 7, "manawi": 2, "total": 91 + 7 + 2}
    raise ValueError("unsupported formal law")


def formal_rows() -> list[dict]:
    rows = []
    for course in COURSES:
        rows.append({"law_id": "sibawayhi-functions-v1", "kind": "course",
                     "course": course, "surface": COURSE_SURFACE[course],
                     "regime": "irab" if course in COURSES[:4] else "bina"})
    for surface in SURFACES:
        rows.append({"law_id": "sibawayhi-functions-v1", "kind": "surface",
                     "surface": surface,
                     "courses": grammar_result("sibawayhi-surface-v1", {"surface": surface})["courses"]})
    for operator in OPERATORS:
        for form in FORMS:
            for ma in MA_STATUSES:
                inputs = {"operator": operator, "form": form, "ma": ma}
                rows.append({"law_id": "qatr-inna-v1", "kind": "inna", **inputs,
                             **grammar_result("qatr-inna-v1", inputs)})
    # The source partitions operators, not all lexical forms or every table called "100".
    rows.append({"law_id": "jurjani-awamil-partition-v1", "kind": "awamil_partition",
                 **grammar_result("jurjani-awamil-partition-v1", {})})
    return rows


def _request(value: Any) -> dict:
    _plain_json(value)
    _object(value, {"version", "record_id", "claim_kind", "candidate"}, "request")
    if value["version"] != VERSION:
        raise ValueError("unsupported evidence version")
    if type(value["record_id"]) is not str or re.fullmatch(r"[a-z][a-z0-9_]{0,95}", value["record_id"]) is None:
        raise ValueError("invalid record identity")
    kind = _enum(value["claim_kind"], ("PASSAGE_ATTESTATION", "LEXICAL_ATTESTATION",
                  "GRAMMAR_APPLICATION", "FORMAL_MODEL_CHECK", "UNIVERSAL_LANGUAGE", "EXTERNAL_EVENT"), "claim kind")
    candidate = value["candidate"]
    if kind == "PASSAGE_ATTESTATION":
        _object(candidate, {"text"}, "passage candidate")
        _text(candidate["text"], "candidate text")
    elif kind == "LEXICAL_ATTESTATION":
        _object(candidate, {"root", "gloss"}, "lexical candidate")
        _text(candidate["root"], "root")
        _text(candidate["gloss"], "gloss")
    elif kind in ("GRAMMAR_APPLICATION", "FORMAL_MODEL_CHECK"):
        required = {"law_id", "inputs", "expected"}
        if kind == "GRAMMAR_APPLICATION":
            required.add("target_text")
        _object(candidate, required, "formal candidate")
        if kind == "GRAMMAR_APPLICATION":
            _text(candidate["target_text"], "target text")
        _text(candidate["law_id"], "law identity")
        grammar_result(candidate["law_id"], candidate["inputs"])
        if type(candidate["expected"]) is not dict:
            raise ValueError("expected result must be an object")
    else:
        _object(candidate, {"statement"}, "out-of-scope candidate")
        _text(candidate["statement"], "statement")
    return json.loads(_canonical(value))


def _assess(request: dict, *, root: Path = ROOT) -> dict:
    request = _request(request)
    report = {
        "version": VERSION, "status": "DEFER", "request": request,
        "request_sha256": _digest(_canonical(request)), "catalog_sha256": CATALOG_SHA256,
        "record": None, "passage": None, "source_attested": False,
        "source_authentication": "PINNED_DIGITAL_EDITION_OR_REVIEWED_TRANSCRIPT",
        "source_evidence_kind": None, "actual": None, "premises_authority": "NOT_APPLICABLE",
        "target_parsed": False, "application_established": False,
        "ambiguity_retained": False, "external_event_established": False,
        "universal_language_certified": False, "law_evaluator": None, "residuals": [],
    }
    try:
        _, sources, records = _catalog(root)
        if request["record_id"] not in records:
            report["residuals"] = ["RECORD_NOT_IN_INSTALLED_CATALOG"]
            return report
        record = records[request["record_id"]]
        source = sources[record["source_id"]]
        passage = _passage(_source(root, source), record)
        report.update(record=record, passage=passage, source_attested=True,
                      source_evidence_kind=record["kind"])
        report["source"] = {k: source[k] for k in (
            "source_id", "title", "author", "edition", "sha256", "provenance_kind", "upstream_url")}
    except EvidenceUnavailable as exc:
        report["residuals"] = ["INSTALLED_EVIDENCE_UNAVAILABLE", str(exc)]
        return report
    candidate, kind = request["candidate"], request["claim_kind"]
    if kind == "PASSAGE_ATTESTATION":
        report["actual"] = {"text": passage["text"]}
        report["status"] = "ATTESTED" if candidate["text"] == passage["text"] else "MISMATCH"
        report["residuals"] = ["ATTESTATION_IS_OF_THIS_SELECTED_SOURCE_PASSAGE_ONLY"]
    elif kind == "LEXICAL_ATTESTATION":
        projection = record.get("lexical_projection")
        if record["kind"] != "LEXICAL_ENTRY" or projection is None:
            report["residuals"] = ["RECORD_HAS_NO_LICENSED_LEXICAL_PROJECTION"]
            return report
        report["actual"] = {"root": projection["root"], "gloss": projection["gloss"]}
        report["status"] = "LEXICALLY_ATTESTED" if _canonical(candidate) == _canonical(report["actual"]) else "MISMATCH"
        report["residuals"] = ["LEXICAL_RECORD_DOES_NOT_SELECT_THE_SENSE_OF_EVERY_OCCURRENCE"]
    elif kind in ("GRAMMAR_APPLICATION", "FORMAL_MODEL_CHECK"):
        if candidate["law_id"] not in record["allowed_laws"]:
            report["residuals"] = ["LAW_NOT_SUPPORTED_BY_THIS_PASSAGE"]
            return report
        report["actual"] = grammar_result(candidate["law_id"], candidate["inputs"])
        report["law_evaluator"] = "PYTHON_MIRROR_OF_LEAN"
        report["premises_authority"] = "CALLER_INTERPRETED"
        alternatives = report["actual"].get("options", report["actual"].get("courses", []))
        report["ambiguity_retained"] = len(alternatives) > 1
        if report["actual"].get("options") == []:
            report["residuals"] = ["READING_OUTSIDE_FORMALIZED_RULE_SCOPE", "EMPTY_OPTIONS_IS_NOT_LINGUISTIC_REFUTATION"]
            return report
        report["status"] = "CONDITIONALLY_CHECKED" if _canonical(candidate["expected"]) == _canonical(report["actual"]) else "MISMATCH"
        report["residuals"] = ["INTERPRETATION_IS_AUTHORED", "TARGET_READING_AND_APPLICATION_NOT_ACQUIRED"]
        if "blocked" in alternatives:
            report["residuals"].append("BLOCKED_OPERATOR_DOES_NOT_ASSIGN_DEFAULT_CASES")
        if kind == "GRAMMAR_APPLICATION":
            report["target_text_occurs_in_selected_passage"] = candidate["target_text"] in passage["text"]
    else:
        report["residuals"] = ["NO_UNIVERSAL_OR_EXTERNAL_EVENT_AUTHORITY_FROM_THIS_WITNESS"]
    return report


def assess(request: dict, *, root: Path = ROOT) -> dict:
    foundation.require_foundation('tools.classical_language_evidence.assess')
    report = _assess(request, root=root)
    # A report repeats the request and adds evidence. Its wire budget is
    # separate, includes the final newline, and is shared by API and CLI replay.
    if len(_canonical(report)) + 1 > MAX_REPORT_BYTES:
        return {"version": VERSION, "status": "DEFER", "request_sha256": report["request_sha256"],
                "catalog_sha256": CATALOG_SHA256, "source_attested": False,
                "application_established": False, "external_event_established": False,
                "universal_language_certified": False, "residuals": ["REPORT_RESOURCE_LIMIT"]}
    return report


def verify(report: dict, request: dict, *, root: Path = ROOT) -> dict:
    foundation.require_foundation('tools.classical_language_evidence.verify')
    fresh = assess(request, root=root)
    try:
        _plain_json(report, report=True)
        valid = type(report) is dict and _canonical(report) == _canonical(fresh)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        valid = False
    return {"version": VERSION, "valid": valid, "status": "VERIFIED" if valid else "REJECT",
            "claim_status": fresh["status"], "application_established": False,
            "external_event_established": False}


def audit_catalog(root: Path = ROOT) -> dict:
    try:
        catalog, sources, records = _catalog(root)
    except EvidenceUnavailable as exc:
        return {"version": VERSION, "status": "DEFER", "catalog_sha256": CATALOG_SHA256,
                "sources": [], "records": [], "residuals": [str(exc)]}
    source_rows, record_rows, buffers = [], [], {}
    for identity, source in sources.items():
        try:
            buffers[identity] = _source(root, source)
            source_rows.append({"source_id": identity, "status": "VERIFIED_BYTES", **source})
        except EvidenceUnavailable as exc:
            source_rows.append({"source_id": identity, "status": "DEFER", "reason": str(exc)})
    for identity, record in records.items():
        try:
            if record["source_id"] not in buffers:
                raise EvidenceUnavailable("source unavailable")
            passage = _passage(buffers[record["source_id"]], record)
            record_rows.append({"record_id": identity, "status": "ATTESTED", "record": record, "passage": passage})
        except EvidenceUnavailable as exc:
            record_rows.append({"record_id": identity, "status": "DEFER", "reason": str(exc)})
    complete = all(row["status"] == "ATTESTED" for row in record_rows) and all(
        row["status"] == "VERIFIED_BYTES" for row in source_rows)
    return {"version": VERSION, "status": "VERIFIED" if complete else "DEFER",
            "catalog_sha256": CATALOG_SHA256, "sources": source_rows, "records": record_rows,
            "catalog_scope": catalog["scope"], "source_authentication": "SELECTED_EDITION_OR_REVIEWED_TRANSCRIPT",
            "target_parsed": False, "application_established": False,
            "external_event_established": False, "universal_language_certified": False,
            "residuals": ["PASSAGE_SELECTION_AND_INTERPRETATION_ARE_AUTHORED", "NOT_A_BLIND_LANGUAGE_ACQUISITION_BENCHMARK"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--output", type=Path)
    query = sub.add_parser("assess")
    query.add_argument("request", type=Path)
    replay = sub.add_parser("verify")
    replay.add_argument("report", type=Path)
    replay.add_argument("--request", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "audit":
            result = audit_catalog()
        elif args.action == "assess":
            result = assess(_read_json(args.request))
        else:
            result = verify(_read_json(args.report, report=True), _read_json(args.request))
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as exc:
        print(json.dumps({"version": VERSION, "status": "INVALID_INPUT", "error": str(exc)}, ensure_ascii=False))
        return 2
    encoded = _canonical(result) + b"\n"
    if len(encoded) > MAX_REPORT_BYTES:
        print(json.dumps({"version": VERSION, "status": "DEFER", "error": "report byte budget exceeded"}))
        return 3
    if args.action == "audit" and args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(encoded)
    else:
        sys.stdout.buffer.write(encoded)
    if result["status"] in ("VERIFIED", "ATTESTED", "LEXICALLY_ATTESTED", "CONDITIONALLY_CHECKED"):
        return 0
    return 3 if result["status"] == "DEFER" else 2


if __name__ == "__main__":
    raise SystemExit(main())
