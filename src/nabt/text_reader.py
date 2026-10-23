"""Source-spanned reader for the installed controlled Arabic language, v1.

This is a whole-statement parser for a declared sublanguage, not a general
Arabic analyser. Names are supplied by the text rather than a built-in example
lexicon. Original bytes, every source segment, and exact component spans are
retained. Unsupported statements become visible residuals; the semantic
kernel admits no part of a document with a residual.

The existing native SourceBlob/SourceSpan contract is reused. No upstream
runtime, executable expression, callable, or caller-selected law is loaded.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
import unicodedata

from .errors import NabtError, resource_limit
from .learning.source_evidence import SourceBlob, SourceSpan
from .text_ir import (
    LANGUAGE_ID,
    MAX_NAME_CHARS,
    READER_VERSION,
    Atom,
    Declaration,
    Definition,
    Fact,
    ParsedDocument,
    Query,
    Residual,
    Rule,
    Segment,
    content_id,
    require_name,
)

MAX_TEXT_BYTES = 65_536
MAX_STATEMENTS = 256
MAX_SEGMENTS = 2_048
MAX_STATEMENT_BYTES = 8_192
MAX_TOKENS = 4_096
MAX_STATEMENT_TOKENS = 128
MAX_RULE_PREMISES = 16
MAX_DEFINITION_MEMBERS = 16
MAX_SOURCE_ID_CHARS = 128

_DECLARATIONS = {"مفهوم": "concept", "علاقة": "relation", "فرد": "individual"}
_RESERVED = frozenset(
    (*_DECLARATIONS, "تعريف", "هو", "و", "إذا", "كان", "فإن", "كل", "هل", "ليس")
)
_SEPARATORS = frozenset(".;؛؟\n\r")


@dataclass(frozen=True, slots=True)
class _Token:
    value: str
    span: SourceSpan
    quoted: bool = False


class _SyntaxResidual(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _syntax(code: str, message: str) -> None:
    raise _SyntaxResidual(code, message)


def _word_start(char: str) -> bool:
    return char == "_" or unicodedata.category(char).startswith("L")


def _word_continue(char: str) -> bool:
    return char == "_" or unicodedata.category(char)[0] in "LMN"


def _separator(text: str, index: int) -> bool:
    char = text[index]
    if char in _SEPARATORS:
        return True
    # A question mark followed by an identifier begins a variable. Every
    # other ASCII question mark is punctuation. Quoted content is handled
    # before this function is called.
    return char == "?" and (
        index + 1 == len(text) or not _word_start(text[index + 1])
    )


def _span(source: SourceBlob, start: int, end: int) -> SourceSpan:
    raw = source.raw_bytes[start:end]
    return SourceSpan(source.source_id, source.sha256, start, end, sha256(raw).hexdigest())


def _source(raw: bytes | str, source_id: str, scope: str) -> SourceBlob:
    if (type(source_id) is not str or len(source_id) > MAX_SOURCE_ID_CHARS
            or re.fullmatch(r"[a-z][a-z0-9_]*", source_id) is None):
        raise NabtError("INVALID_SOURCE_ID", "A source ID must match [a-z][a-z0-9_]* within 128 characters")
    if type(scope) is str and any(unicodedata.category(char).startswith("C") for char in scope):
        raise NabtError("INVALID_SCOPE", "A scope cannot contain Unicode control, format, or surrogate characters")
    require_name(scope, "scope")
    if type(raw) is str:
        if len(raw) > MAX_TEXT_BYTES:
            raise resource_limit("Text exceeds the reader byte budget", maximum_bytes=MAX_TEXT_BYTES)
        try:
            raw = raw.encode("utf-8", "strict")
        except UnicodeError as exc:
            raise NabtError("INVALID_UTF8", "Text must contain valid Unicode scalar values") from exc
    elif type(raw) is not bytes:
        raise NabtError("INVALID_TEXT_INPUT", "Text must be an exact str or bytes value")
    if len(raw) > MAX_TEXT_BYTES:
        raise resource_limit("Text exceeds the reader byte budget", maximum_bytes=MAX_TEXT_BYTES)
    if not raw:
        raise NabtError("EMPTY_TEXT", "An empty byte sequence contains no statement")
    try:
        return SourceBlob(source_id, raw)
    except UnicodeError as exc:
        raise NabtError("INVALID_UTF8", "Bytes must be strict UTF-8") from exc


def _regions(text: str) -> tuple[tuple[str, int, int], ...]:
    """Partition character offsets, retaining every original character."""
    result: list[tuple[str, int, int]] = []

    def push(kind: str, start: int, end: int) -> None:
        if start == end:
            return
        if result and result[-1][0] == kind and result[-1][2] == start:
            result[-1] = (kind, result[-1][1], end)
        else:
            if len(result) >= MAX_SEGMENTS:
                raise resource_limit("Text exceeds the source segment budget", maximum=MAX_SEGMENTS)
            result.append((kind, start, end))

    def content(start: int, end: int) -> None:
        left, right = start, end
        while left < right and text[left].isspace():
            left += 1
        while right > left and text[right - 1].isspace():
            right -= 1
        push("whitespace", start, left)
        push("statement", left, right)
        push("whitespace", right, end)

    quoted = False
    beginning = 0
    for index, char in enumerate(text):
        if char == "«":
            quoted = True
        elif char == "»":
            quoted = False
        elif not quoted and _separator(text, index):
            content(beginning, index)
            push("separator", index, index + 1)
            beginning = index + 1
    content(beginning, len(text))
    return tuple(result)


def _tokens(
    text: str,
    start: int,
    end: int,
    offsets: list[int],
    source: SourceBlob,
) -> tuple[_Token, ...]:
    result: list[_Token] = []
    cursor = start
    while cursor < end:
        if text[cursor].isspace():
            cursor += 1
            continue
        if len(result) >= MAX_STATEMENT_TOKENS:
            raise resource_limit("Statement exceeds its token budget", maximum=MAX_STATEMENT_TOKENS)
        token_start = cursor
        quoted = text[cursor] == "«"
        if quoted:
            close = text.find("»", cursor + 1, end)
            if close < 0:
                _syntax("UNCLOSED_NAME", "A quoted name requires a closing guillemet")
            value = text[cursor + 1:close]
            if "«" in value:
                _syntax("NESTED_QUOTE", "Quoted names cannot contain nested guillemets")
            cursor = close + 1
            if cursor < end and not text[cursor].isspace():
                _syntax("NAME_BOUNDARY", "A quoted name must have a whitespace token boundary")
        else:
            while cursor < end and not text[cursor].isspace():
                cursor += 1
            value = text[token_start:cursor]
            if "«" in value or "»" in value:
                _syntax("MALFORMED_QUOTE", "Guillemets must enclose one complete name")
        result.append(_Token(value, _span(source, offsets[token_start], offsets[cursor]), quoted))
    return tuple(result)


def _keyword(token: _Token, value: str) -> bool:
    return not token.quoted and token.value == value


def _name(token: _Token) -> str:
    value = token.value
    if len(value) > MAX_NAME_CHARS:
        raise resource_limit("Name exceeds its character budget", maximum_characters=MAX_NAME_CHARS)
    if not value or not value.strip():
        _syntax("EMPTY_NAME", "Names must contain at least one non-whitespace character")
    if value.startswith("?"):
        _syntax("RESERVED_VARIABLE_NAME", "A name cannot start with the reserved variable prefix '?'")
    if any(unicodedata.category(char).startswith("C") for char in value):
        _syntax("NAME_CONTROL_CHARACTER", "Names cannot contain Unicode control or format characters")
    if token.quoted:
        return value
    if value in _RESERVED:
        _syntax("RESERVED_KEYWORD", "A grammar keyword used as a name must be guillemet-quoted")
    if not (value[0] == "_" or unicodedata.category(value[0])[0] in "LN") or not all(
        _word_continue(char) for char in value
    ):
        _syntax("UNSUPPORTED_NAME", "Unquoted names contain letters, marks, numbers, and underscores")
    return value


def _term(token: _Token, *, variables: bool) -> str:
    if not token.quoted and token.value.startswith("?"):
        identifier = token.value[1:]
        if not variables:
            _syntax("VARIABLE_OUTSIDE_RULE", "Facts and questions require ground terms")
        if len(token.value) > MAX_NAME_CHARS:
            raise resource_limit("Variable exceeds its character budget", maximum_characters=MAX_NAME_CHARS)
        if not identifier or not _word_start(identifier[0]) or not all(
            _word_continue(char) for char in identifier
        ):
            _syntax("INVALID_VARIABLE", "A variable requires '?' followed by one identifier")
        return token.value
    return _name(token)


def _atom(tokens: tuple[_Token, ...], *, variables: bool) -> Atom:
    positive = True
    if tokens and _keyword(tokens[0], "ليس"):
        positive = False
        tokens = tokens[1:]
    if len(tokens) != 3:
        _syntax("UNSUPPORTED_ATOM", "An atom requires term هو concept, or term relation term")
    subject = _term(tokens[0], variables=variables)
    if _keyword(tokens[1], "هو"):
        return Atom(_name(tokens[2]), (subject,), positive)
    return Atom(_name(tokens[1]), (subject, _term(tokens[2], variables=variables)), positive)


def _split_conjunction(tokens: tuple[_Token, ...]) -> tuple[tuple[_Token, ...], ...]:
    pieces: list[tuple[_Token, ...]] = []
    start = 0
    for index, token in enumerate(tokens):
        if _keyword(token, "و"):
            if index == start:
                _syntax("EMPTY_CONJUNCT", "A conjunction requires a complete atom on both sides")
            pieces.append(tokens[start:index])
            start = index + 1
    if start == len(tokens):
        _syntax("EMPTY_CONJUNCT", "A conjunction requires a complete final atom")
    pieces.append(tokens[start:])
    return tuple(pieces)


def parse_document(
    raw: bytes | str, *, source_id: str = "text", scope: str = "default"
) -> ParsedDocument:
    """Parse exact bytes under v1 and retain unsupported whole statements.

    Invalid byte encoding/types and exhausted budgets raise ``NabtError``.
    Unsupported grammar is represented by ``document.residuals``. A document
    with any residual has ``accepted == False`` and is inadmissible as a whole.
    Parsed prefixes remain visible for inspection, never as partial authority.
    """
    source = _source(raw, source_id, scope)
    text = source.raw_bytes.decode("utf-8")
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))
    regions = _regions(text)
    statements = sum(kind == "statement" for kind, _, _ in regions)
    if statements > MAX_STATEMENTS:
        raise resource_limit("Text exceeds the statement budget", maximum=MAX_STATEMENTS)

    segments: list[Segment] = []
    declarations: list[Declaration] = []
    definitions: list[Definition] = []
    facts: list[Fact] = []
    rules: list[Rule] = []
    queries: list[Query] = []
    residuals: list[Residual] = []
    token_count = 0

    for kind, start, end in regions:
        statement_span = _span(source, offsets[start], offsets[end])
        if kind != "statement":
            segments.append(Segment(statement_span, kind))
            continue
        if statement_span.end - statement_span.start > MAX_STATEMENT_BYTES:
            raise resource_limit("Statement exceeds its byte budget", maximum_bytes=MAX_STATEMENT_BYTES)

        def analysis_id(form: str, index: int = 0) -> str:
            return content_id(
                [LANGUAGE_ID, READER_VERSION, source.source_id, source.sha256, scope,
                 statement_span.start, statement_span.end, form, index]
            )

        try:
            tokens = _tokens(text, start, end, offsets, source)
            token_count += len(tokens)
            if token_count > MAX_TOKENS:
                raise resource_limit("Text exceeds its token budget", maximum=MAX_TOKENS)
            components = tuple(token.span for token in tokens)
            first = tokens[0]
            if not first.quoted and first.value in _DECLARATIONS:
                if len(tokens) != 2:
                    _syntax("INVALID_DECLARATION", "A declaration requires exactly one name")
                name = _name(tokens[1])
                declarations.append(Declaration(_DECLARATIONS[first.value], name,
                                                statement_span, components, analysis_id("declaration")))
            elif _keyword(first, "تعريف"):
                if len(tokens) < 4 or not _keyword(tokens[2], "هو"):
                    _syntax("INVALID_DEFINITION", "A definition requires تعريف name هو name (و name)*")
                name = _name(tokens[1])
                member_tokens = tokens[3:]
                if len(member_tokens) % 2 == 0 or any(
                    not _keyword(member_tokens[index], "و")
                    for index in range(1, len(member_tokens), 2)
                ):
                    _syntax("INVALID_DEFINITION", "Definition members must be names joined by و")
                if (len(member_tokens) + 1) // 2 > MAX_DEFINITION_MEMBERS:
                    raise resource_limit("Definition exceeds its member budget", maximum=MAX_DEFINITION_MEMBERS)
                members = tuple(_name(token) for token in member_tokens[::2])
                definition = Definition(name, members, statement_span, components, analysis_id("definition"))
                defined_atom = Atom(name, ("?x",))
                member_atoms = tuple(Atom(member, ("?x",)) for member in members)
                generated = [
                    Rule((defined_atom,), member, statement_span, components,
                         analysis_id("definition_forward", index), "definition_forward")
                    for index, member in enumerate(member_atoms)
                ]
                generated.append(Rule(member_atoms, defined_atom, statement_span, components,
                                      analysis_id("definition_reverse"), "definition_reverse"))
                definitions.append(definition)
                rules.extend(generated)
            elif _keyword(first, "كل"):
                if len(tokens) != 4 or not _keyword(tokens[2], "هو"):
                    _syntax("INVALID_UNIVERSAL", "A universal requires كل concept هو concept")
                premise, conclusion = _name(tokens[1]), _name(tokens[3])
                rules.append(Rule((Atom(premise, ("?x",)),), Atom(conclusion, ("?x",)),
                                  statement_span, components, analysis_id("universal"), "universal"))
            elif _keyword(first, "إذا"):
                body_start = 2 if len(tokens) > 1 and _keyword(tokens[1], "كان") else 1
                separators = [index for index, token in enumerate(tokens) if _keyword(token, "فإن")]
                if len(separators) != 1 or separators[0] <= body_start or separators[0] == len(tokens) - 1:
                    _syntax("INVALID_RULE", "A rule requires one premise section and one فإن conclusion")
                split = separators[0]
                parts = _split_conjunction(tokens[body_start:split])
                if len(parts) > MAX_RULE_PREMISES:
                    raise resource_limit("Rule exceeds its premise budget", maximum=MAX_RULE_PREMISES)
                body = tuple(_atom(part, variables=True) for part in parts)
                head = _atom(tokens[split + 1:], variables=True)
                bound = frozenset(var for atom in body for var in atom.variables)
                if not head.variables <= bound:
                    _syntax("UNBOUND_CONCLUSION_VARIABLE", "Every conclusion variable must occur in a premise")
                rules.append(Rule(body, head, statement_span, components, analysis_id("explicit_rule")))
            elif _keyword(first, "هل"):
                atom = _atom(tokens[1:], variables=False)
                queries.append(Query(atom, statement_span, components, analysis_id("query"), scope))
            else:
                atom = _atom(tokens, variables=False)
                facts.append(Fact(atom, statement_span, components, analysis_id("fact")))
        except _SyntaxResidual as exc:
            residuals.append(Residual(exc.code, exc.message, statement_span))
            segments.append(Segment(statement_span, "residual"))
        else:
            segments.append(Segment(statement_span, "statement"))

    if statements == 0:
        residuals.append(Residual("EMPTY_DOCUMENT", "The source contains no statement",
                                  _span(source, 0, len(source.raw_bytes))))
    return ParsedDocument(
        source=source,
        scope=scope,
        segments=tuple(segments),
        declarations=tuple(declarations),
        definitions=tuple(definitions),
        facts=tuple(facts),
        rules=tuple(rules),
        queries=tuple(queries),
        residuals=tuple(residuals),
    )


def parse_query(raw: bytes | str, *, source_id: str = "query", scope: str = "default") -> Query:
    """Read exactly one ground ``هل atom`` statement, or raise ``NabtError``.

    This wrapper never extracts a question from a mixed document. Its error
    retains parser residuals, including their original source spans.
    """
    document = parse_document(raw, source_id=source_id, scope=scope)
    if (not document.accepted or len(document.queries) != 1 or document.declarations
            or document.definitions or document.facts or document.rules):
        raise NabtError("INVALID_QUERY", "A query requires exactly one ground هل statement",
                        details={"residuals": [item.as_dict() for item in document.residuals],
                                 "query_count": len(document.queries)})
    return document.queries[0]


__all__ = [
    "LANGUAGE_ID", "READER_VERSION", "MAX_TEXT_BYTES", "MAX_STATEMENTS", "MAX_SEGMENTS",
    "MAX_STATEMENT_BYTES", "MAX_TOKENS", "MAX_STATEMENT_TOKENS", "MAX_RULE_PREMISES",
    "MAX_DEFINITION_MEMBERS", "MAX_SOURCE_ID_CHARS", "parse_document", "parse_query",
]
