"""Pinned, independently annotated source-statement witnesses.

The annotation is a public-reference correction, made after first evaluation.
It records raw-byte statement boundaries and ordered component roles; it does
not contain NABT analysis IDs and imports no production reader or verifier.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


ANNOTATION_PATH = Path(__file__).resolve().parents[2] / "evidence/arabic_syntax/review_fixes/statement_oracle_v2.json"
ANNOTATION_SHA256 = "73c232127ce3da747b54face3f508273e3730be37a89522dceec4d5446cbd0bd"
ANNOTATION_SCHEMA = "nabt.arabic-syntax.statement-oracle.v2"


def load_statement_oracle() -> dict:
    raw = ANNOTATION_PATH.read_bytes()
    if sha256(raw).hexdigest() != ANNOTATION_SHA256:
        raise ValueError("Independent statement annotation checksum differs")
    data = json.loads(raw)
    if data["schema"] != ANNOTATION_SCHEMA:
        raise ValueError("Unknown independent statement annotation schema")
    return {row["source_text_sha256"]: row for row in data["records"]}


def annotate_statement(raw_text: str, statement: str, *, component_roles: list,
                       facts: list | None = None, rules: list | None = None,
                       rule_kinds: list | None = None,
                       occurrence: int = 0) -> dict:
    """Construct an explicit trusted fixture annotation from raw text only.

    Test authors supply interpretation and every token's roles themselves.
    This is not a runtime Arabic parser, a certificate field, or an override
    accepted by the evaluator CLI. The caller must trust the returned fixture.
    """
    if type(raw_text) is not str or type(statement) is not str or not statement:
        raise ValueError("An annotation needs raw text and a nonempty statement")
    if type(occurrence) is not int or occurrence < 0:
        raise ValueError("Invalid statement occurrence")
    matches = list(re.finditer(re.escape(statement), raw_text))
    if occurrence >= len(matches):
        raise ValueError("Annotated statement is absent from its source")
    match = matches[occurrence]
    before, after = raw_text[:match.start()], raw_text[match.end():]
    if (before.rstrip() and before.rstrip()[-1] not in ".;؛؟\n\r") or (after.lstrip() and after.lstrip()[0] not in ".;؛؟\n\r"):
        raise ValueError("Annotation must cover a complete source statement")
    tokens = list(re.finditer(r"«[^«»]*»|[^\s«»]+", statement))
    if len(tokens) != len(component_roles) or any(type(r) is not list or not r or any(type(v) is not str or not v for v in r) for r in component_roles):
        raise ValueError("Each ordered source component needs explicit roles")
    offset = match.start()
    components = [{"start": len(raw_text[:offset+t.start()].encode()),
                   "end": len(raw_text[:offset+t.end()].encode()), "roles": roles}
                  for t, roles in zip(tokens, component_roles)]
    return {"start": len(before.encode()), "end": len(raw_text[:match.end()].encode()),
            "facts": facts or [], "rules": rules or [], "components": components,
            "rule_kinds": rule_kinds if rule_kinds is not None else ["explicit_rule"] * len(rules or [])}


def fixture_source(raw_text: str, statements: list) -> dict:
    """Package explicitly authored statement fixtures for helper-only tests."""
    return {"raw_text": raw_text, "source_text_sha256": sha256(raw_text.encode()).hexdigest(),
            "statements": statements}
