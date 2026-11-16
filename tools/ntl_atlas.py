"""Source-bound NTL atlas staging, not a reader or semantic admission owner.

All imported annotations remain proposals. External NABT requests use the existing
text.read gateway; callers must independently retain and verify that request.
No model score, reviewer label, or root inventory entry grants semantic authority.
This module uses only the standard library and has no external experiment imports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "nabt.ntl-atlas.staging.v1"
MAX_BYTES = 8_000_000
MAX_ROWS = 100_000
RADICALS = frozenset("ءبتثجحخدذرزسشصضطظعغفقكلمنهوي")
OBLIGATIONS = (
    "MORPHOLOGICAL_ROOT_REVIEW", "ATTESTED_LEMMA", "SENSE_SPECIFIC_SOURCE",
    "MASDAR_AND_VALENCY_ATTESTATION", "ROLE_AND_CONTEXT_BINDING",
    "INDEPENDENT_MECHANISM_EVIDENCE", "SOURCE_REPORTED_PURPOSE_ONLY",
)


def _check(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("MAX_PACKET_DEPTH")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value.bit_length() > 256:
            raise ValueError("INTEGER_RESOURCE_LIMIT")
        return
    if type(value) is str:
        if len(value.encode("utf-8")) > MAX_BYTES:
            raise ValueError("STRING_RESOURCE_LIMIT")
        return
    if type(value) is list:
        if len(value) > MAX_ROWS:
            raise ValueError("LIST_RESOURCE_LIMIT")
        for item in value:
            _check(item, depth + 1)
        return
    if type(value) is dict:
        if len(value) > MAX_ROWS or any(type(k) is not str for k in value):
            raise ValueError("INVALID_OBJECT")
        for k, item in value.items():
            _check(k, depth + 1)
            _check(item, depth + 1)
        return
    raise ValueError("NONCANONICAL_VALUE")


def canonical(value: Any) -> bytes:
    _check(value)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise ValueError("PACKET_RESOURCE_LIMIT")
    return raw


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _unique(pairs: list[tuple[str, Any]]) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("DUPLICATE_JSON_KEY")
        out[key] = value
    return out


def decode_json(raw: bytes) -> Any:
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError("INVALID_OR_OVERSIZE_JSON")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))
    canonical(value)
    return value


def freeze(path: Path, value: Any) -> None:
    """Exclusive creation: an existing historical record is never replaced."""
    payload = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)


def fold(value: dict) -> int:
    if type(value) is not dict:
        raise ValueError("OBJECT_REQUIRED")
    return int.from_bytes(b"\x01" + canonical(value), "big")


def unfold(number: int) -> dict:
    if type(number) is not int or number <= 0 or number.bit_length() > 8 * (MAX_BYTES + 1):
        raise ValueError("INVALID_NUMBER_OR_LIMIT")
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    if raw[:1] != b"\x01":
        raise ValueError("WRONG_ENVELOPE")
    value = decode_json(raw[1:])
    if type(value) is not dict or fold(value) != number:
        raise ValueError("NONCANONICAL_NUMBER")
    return value


@dataclass(frozen=True)
class Source:
    source_id: str
    revision: str
    body: bytes
    sha256: str
    domain: str
    license_id: str

    def __post_init__(self) -> None:
        if any(type(x) is not str or not x for x in (
            self.source_id, self.revision, self.domain, self.license_id, self.sha256
        )):
            raise ValueError("SOURCE_METADATA_REQUIRED")
        if type(self.body) is not bytes or not 0 < len(self.body) <= MAX_BYTES:
            raise ValueError("SOURCE_BODY_REQUIRED")
        self.body.decode("utf-8")
        if hashlib.sha256(self.body).hexdigest() != self.sha256:
            raise ValueError("SOURCE_HASH_MISMATCH")

    def span(self, start: int, stop: int) -> dict:
        if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= len(self.body):
            raise ValueError("INVALID_BYTE_SPAN")
        quote = self.body[start:stop].decode("utf-8")
        # Reject slices that begin or end inside a Unicode code point.
        self.body[:start].decode("utf-8")
        self.body[:stop].decode("utf-8")
        return {"source_id": self.source_id, "revision": self.revision,
                "source_sha256": self.sha256, "start": start, "stop": stop,
                "quote": quote, "domain": self.domain}

    def verify_span(self, span: dict) -> bool:
        try:
            return type(span) is dict and span == self.span(span["start"], span["stop"])
        except (KeyError, TypeError, ValueError, UnicodeError):
            return False


def inventory(source: Source, expected_blob: str) -> tuple[list[dict], dict]:
    """Enumerate every row, preserving bytes; do not normalize root candidates."""
    blob = hashlib.sha1(b"blob " + str(len(source.body)).encode("ascii") + b"\0" + source.body).hexdigest()
    if blob != expected_blob:
        raise ValueError("INVENTORY_BLOB_MISMATCH")
    records, offset = [], 0
    for line_no, line in enumerate(source.body.splitlines(keepends=True), 1):
        data = line.rstrip(b"\r\n")
        form = data.decode("utf-8")
        if form and not form.startswith("#"):
            if form != form.strip() or any(c.isspace() for c in form):
                raise ValueError("INVENTORY_WHITESPACE_AMBIGUITY")
            span = source.span(offset, offset + len(data))
            identity = {"schema": SCHEMA, "kind": "ROOT_LIST_OCCURRENCE", "span": span}
            records.append({
                "id": digest(identity), "identity": identity, "source_line": line_no,
                "form": form, "length": len(form),
                "numeric_identity_hex": format(fold(identity), "x"),
                "outside_alphabet": sorted(set(form) - RADICALS),
                "status": "SOURCE_LISTED_ONLY", "sense_ids": [],
                "residuals": list(OBLIGATIONS), "authority": "NONE",
            })
            if len(records) > MAX_ROWS:
                raise ValueError("INVENTORY_ROW_LIMIT")
        offset += len(line)
    summary = {
        "schema": SCHEMA, "source_sha256": source.sha256, "git_blob": blob,
        "rows": len(records), "unique_forms": len({r["form"] for r in records}),
        "length_3": sum(r["length"] == 3 for r in records),
        "length_4": sum(r["length"] == 4 for r in records),
        "character_review_rows": sum(bool(r["outside_alphabet"]) for r in records),
        "senses_reviewed": 0, "coverage": "SOURCE_ENUMERATION_ONLY",
        "semantic_authority": "NONE", "source_license": source.license_id,
    }
    return records, summary


def make_proposal(record: dict, source: Source, lemma: str, sense_key: str,
                  start: int, stop: int, author: str) -> dict:
    if any(type(x) is not str or not x for x in (lemma, sense_key, author)):
        raise ValueError("PROPOSAL_IDENTITIES_REQUIRED")
    if type(record) is not dict or record.get("status") != "SOURCE_LISTED_ONLY":
        raise ValueError("SOURCE_INVENTORY_RECORD_REQUIRED")
    identity = record.get("identity")
    if record.get("id") != digest(identity):
        raise ValueError("ROOT_RECORD_IDENTITY_MISMATCH")
    span = source.span(start, stop)
    # Presence of a lemma in a quotation is only a source anchor, not a sense proof.
    if lemma not in span["quote"]:
        raise ValueError("LEMMA_NOT_PRESENT_IN_SELECTED_QUOTE")
    payload = {"schema": SCHEMA, "kind": "SENSE_ANNOTATION_PROPOSAL",
               "root_record_id": record["id"], "lemma": lemma,
               "sense_key": sense_key, "span": span, "author": author,
               "status": "PROPOSED_ONLY", "authority": "NONE",
               "open_obligations": list(OBLIGATIONS)}
    return {**payload, "proposal_digest": digest(payload)}


def check_proposal(proposal: dict, record: dict, lexical_source: Source) -> bool:
    try:
        span = proposal["span"]
        expected = make_proposal(record, lexical_source, proposal["lemma"],
                                 proposal["sense_key"], span["start"], span["stop"], proposal["author"])
        return canonical(expected) == canonical(proposal)
    except (KeyError, TypeError, ValueError):
        return False


def review_event(proposal: dict, record: dict, lexical_source: Source,
                 reviewer: str, decision: str, rationale: str,
                 trusted_reviewers: frozenset[str]) -> dict:
    """Record an explicit trusted-workflow premise, never a semantic certificate.

    A reviewer identifier is not a cryptographic identity. Production callers must
    authenticate the workflow separately; this record alone grants no permission.
    """
    if not check_proposal(proposal, record, lexical_source):
        raise ValueError("PROPOSAL_REPLAY_MISMATCH")
    if reviewer not in trusted_reviewers or reviewer == proposal["author"]:
        raise ValueError("INDEPENDENT_REVIEWER_REQUIRED")
    if decision not in {"REQUEST_OWNER_REPLAY", "REJECT", "DEFER"}:
        raise ValueError("REVIEW_CANNOT_GRANT_LICENSE")
    if type(rationale) is not str or not rationale.strip():
        raise ValueError("REVIEW_RATIONALE_REQUIRED")
    return {"schema": SCHEMA, "kind": "ANNOTATION_REVIEW_EVENT",
            "proposal_digest": proposal["proposal_digest"], "reviewer": reviewer,
            "decision": decision, "rationale": rationale, "authority": "NONE",
            "admission": "NOT_ADMITTED", "synthetic": lexical_source.domain.startswith("synthetic")}


def gateway_plan(source: Source, start: int, stop: int) -> dict:
    span = source.span(start, stop)
    request = {"schema": "nabt.io.request.v1", "route": "text.read",
               "payload": {"text": span["quote"]}}
    return {"schema": SCHEMA, "kind": "GATEWAY_REPLAY_PLAN", "span": span,
            "request": request, "request_sha256": digest(request),
            "authority": "NONE", "execution": "NOT_RUN", "verified": False,
            "required_commands": [
                "python -m tools.grammar_catalog gateway run --request REQUEST --output RECEIPT",
                "python -m tools.grammar_catalog gateway verify --request REQUEST --receipt RECEIPT"],
            "open_obligations": ["NATIVE_GATEWAY_REPLAY", "OWNER_SCOPE_RETAINED"]}


def check_plan(plan: dict, source: Source) -> bool:
    try:
        return canonical(plan) == canonical(gateway_plan(source, plan["span"]["start"], plan["span"]["stop"]))
    except (KeyError, TypeError, ValueError):
        return False


def cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("inventory")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--revision", required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--blob", required=True)
    p.add_argument("--license", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    source = Source(args.source_id, args.revision, raw, args.sha256,
                    "root-inventory", args.license)
    rows, summary = inventory(source, args.blob)
    args.out.mkdir(parents=True, exist_ok=False)
    with (args.out / "records.jsonl").open("xb") as stream:
        for row in rows:
            stream.write(canonical(row) + b"\n")
    freeze(args.out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli()
