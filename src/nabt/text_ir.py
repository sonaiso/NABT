"""Versioned, inert meaning records for the NABT controlled Arabic reader.

These objects record an interpretation of exact source spans. They do not grant
source authority: the semantic kernel reparses ``source.raw_bytes`` at admission.
The source bytes and Unicode spelling are never normalized by this IR.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from hashlib import sha256
import unicodedata

from .errors import NabtError
from .learning.source_evidence import SourceBlob, SourceSpan

LANGUAGE_ID = "nabt.controlled-arabic.v1"
READER_VERSION = "nabt.text-reader.v1"
IR_VERSION = "nabt.semantic-ir.v1"
MAX_NAME_CHARS = 512


def require_name(value: object, label: str = "name") -> str:
    if type(value) is not str or not value or not value.strip() or len(value) > MAX_NAME_CHARS:
        raise NabtError("INVALID_SEMANTIC_NAME", f"{label} requires a nonempty bounded exact string")
    if any(unicodedata.category(ch).startswith("C") for ch in value):
        raise NabtError("INVALID_SEMANTIC_NAME", f"{label} contains a control character")
    return value


def is_variable(term: str) -> bool:
    return term.startswith("?")


def content_id(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def span_dict(span: SourceSpan) -> dict:
    return {"source_id": span.source_id, "source_sha256": span.source_sha256,
            "start": span.start, "end": span.end, "span_sha256": span.span_sha256}


@dataclass(frozen=True, slots=True)
class Atom:
    predicate: str
    args: tuple[str, ...]
    positive: bool = True

    def __post_init__(self) -> None:
        require_name(self.predicate, "predicate")
        if self.predicate.startswith("?"):
            raise NabtError("INVALID_PREDICATE", "Predicates cannot be variables")
        if type(self.args) is not tuple or len(self.args) not in (1, 2):
            raise NabtError("INVALID_ARITY", "The installed language admits unary concepts and binary relations")
        for arg in self.args:
            require_name(arg, "argument")
            if arg == "?" or (is_variable(arg) and any(ch.isspace() for ch in arg)):
                raise NabtError("INVALID_VARIABLE", "A variable is '?' followed by one nonempty token")
        if type(self.positive) is not bool:
            raise NabtError("INVALID_POLARITY", "Polarity must be an explicit boolean")

    @property
    def variables(self) -> frozenset[str]:
        return frozenset(arg for arg in self.args if is_variable(arg))

    @property
    def ground(self) -> bool:
        return not self.variables

    def opposite(self) -> Atom:
        return Atom(self.predicate, self.args, not self.positive)

    def as_dict(self) -> dict:
        return {"predicate": self.predicate, "args": list(self.args), "positive": self.positive}


@dataclass(frozen=True, slots=True)
class Fact:
    atom: Atom
    span: SourceSpan
    component_spans: tuple[SourceSpan, ...]
    analysis_id: str


@dataclass(frozen=True, slots=True)
class Rule:
    body: tuple[Atom, ...]
    head: Atom
    span: SourceSpan
    component_spans: tuple[SourceSpan, ...]
    analysis_id: str
    kind: str = "explicit_rule"


@dataclass(frozen=True, slots=True)
class Query:
    atom: Atom
    span: SourceSpan
    component_spans: tuple[SourceSpan, ...]
    analysis_id: str
    scope: str = "default"


@dataclass(frozen=True, slots=True)
class Declaration:
    kind: str
    name: str
    span: SourceSpan
    component_spans: tuple[SourceSpan, ...]
    analysis_id: str


@dataclass(frozen=True, slots=True)
class Definition:
    name: str
    members: tuple[str, ...]
    span: SourceSpan
    component_spans: tuple[SourceSpan, ...]
    analysis_id: str


@dataclass(frozen=True, slots=True)
class Segment:
    span: SourceSpan
    kind: str


@dataclass(frozen=True, slots=True)
class Residual:
    code: str
    message: str
    span: SourceSpan

    def as_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "span": span_dict(self.span)}


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    source: SourceBlob
    scope: str = "default"
    language_id: str = LANGUAGE_ID
    reader_version: str = READER_VERSION
    segments: tuple[Segment, ...] = ()
    declarations: tuple[Declaration, ...] = ()
    definitions: tuple[Definition, ...] = ()
    facts: tuple[Fact, ...] = ()
    rules: tuple[Rule, ...] = ()
    queries: tuple[Query, ...] = ()
    residuals: tuple[Residual, ...] = ()

    @property
    def accepted(self) -> bool:
        return not self.residuals

    @property
    def raw_text(self) -> str:
        return self.source.raw_bytes.decode("utf-8")

    def as_dict(self) -> dict:
        return {
            "ir_version": IR_VERSION, "language_id": self.language_id,
            "reader_version": self.reader_version, "source_id": self.source.source_id,
            "source_sha256": self.source.sha256, "scope": self.scope,
            "raw_text": self.raw_text, "accepted": self.accepted,
            "segments": [{"kind": s.kind, "span": span_dict(s.span)} for s in self.segments],
            "declarations": [{"kind": d.kind, "name": d.name, "span": span_dict(d.span),
                              "component_spans": [span_dict(s) for s in d.component_spans],
                              "analysis_id": d.analysis_id} for d in self.declarations],
            "definitions": [{"name": d.name, "members": list(d.members), "span": span_dict(d.span),
                             "component_spans": [span_dict(s) for s in d.component_spans],
                             "analysis_id": d.analysis_id, "direction": "equivalence"}
                            for d in self.definitions],
            "facts": [{"atom": f.atom.as_dict(), "span": span_dict(f.span),
                       "component_spans": [span_dict(s) for s in f.component_spans],
                       "analysis_id": f.analysis_id} for f in self.facts],
            "rules": [{"body": [a.as_dict() for a in r.body], "head": r.head.as_dict(),
                       "span": span_dict(r.span), "kind": r.kind,
                       "component_spans": [span_dict(s) for s in r.component_spans],
                       "analysis_id": r.analysis_id} for r in self.rules],
            "queries": [{"atom": q.atom.as_dict(), "span": span_dict(q.span),
                         "component_spans": [span_dict(s) for s in q.component_spans],
                         "scope": q.scope, "analysis_id": q.analysis_id} for q in self.queries],
            "residuals": [r.as_dict() for r in self.residuals],
        }
