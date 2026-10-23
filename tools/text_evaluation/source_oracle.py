"""Independent finite source-clause oracle for the published v1 benchmark.

No NABT parser, semantic compiler or certificate verifier is imported. This
small interpreter implements only the declared controlled grammar. It checks
exact whole-statement boundaries, semantic payload, token spans and clause
identities; it does not establish source truth or understand general Arabic.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata


BOUNDARY = re.compile(r"«[^«»]*»|[.;؛؟\n\r]|\?(?![_\w])")
TOKEN = re.compile(r"«[^«»]*»|[^\s«»]+")
RESERVED = {"مفهوم", "علاقة", "فرد", "تعريف", "هو", "و", "إذا", "كان", "فإن", "كل", "هل", "ليس"}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _token_name(token: str, variables: bool = False) -> str:
    quoted = token.startswith("«") and token.endswith("»")
    value = token[1:-1] if quoted else token
    if not value or not value.strip() or any(unicodedata.category(c).startswith("C") for c in value):
        raise ValueError("Invalid source name")
    if quoted:
        if value.startswith("?"):
            raise ValueError("A quoted name cannot be a variable")
        return value
    if value.startswith("?"):
        if not variables or len(value) == 1:
            raise ValueError("Ungrounded source variable")
        identifier = value[1:]
    else:
        if value in RESERVED:
            raise ValueError("Reserved source name")
        identifier = value
    if not all(c == "_" or unicodedata.category(c)[0] in "LMN" for c in identifier):
        raise ValueError("Unsupported source name")
    return value


def _atom(tokens: list[str], variables: bool = False) -> dict:
    positive = not tokens or tokens[0] != "ليس"
    words = tokens if positive else tokens[1:]
    if len(words) != 3:
        raise ValueError("Source atom requires exactly three terms")
    left = _token_name(words[0], variables)
    if words[1] == "هو":
        predicate, args = _token_name(words[2]), [left]
    else:
        predicate = _token_name(words[1])
        args = [left, _token_name(words[2], variables)]
    return {"predicate": predicate, "args": args, "positive": positive}


def _regions(text: str):
    """Regexp scanning, separate from the production state-machine scanner."""
    left = 0
    for boundary in BOUNDARY.finditer(text):
        if boundary.group().startswith("«"):
            continue
        right = boundary.start()
        while left < right and text[left].isspace():
            left += 1
        while right > left and text[right - 1].isspace():
            right -= 1
        if left < right:
            yield left, right
        left = boundary.end()
    right = len(text)
    while left < right and text[left].isspace():
        left += 1
    while right > left and text[right - 1].isspace():
        right -= 1
    if left < right:
        yield left, right


def source_clauses(source: dict) -> list[dict]:
    text, source_id, scope = source["text"], source["source_id"], source["scope"]
    raw = text.encode("utf-8")
    source_hash = hashlib.sha256(raw).hexdigest()

    def span(start: int, end: int) -> dict:
        a, b = len(text[:start].encode("utf-8")), len(text[:end].encode("utf-8"))
        return {"source_id": source_id, "source_sha256": source_hash, "start": a, "end": b,
                "span_sha256": hashlib.sha256(raw[a:b]).hexdigest()}

    clauses = []
    for start, end in _regions(text):
        statement = text[start:end]
        matches = list(TOKEN.finditer(statement))
        previous = 0
        for match in matches:
            if statement[previous:match.start()].strip():
                raise ValueError("Source has unparsed bytes")
            if previous and previous == match.start():
                raise ValueError("Source token boundary is missing")
            previous = match.end()
        if not matches or statement[previous:].strip():
            raise ValueError("Source has unparsed bytes")
        tokens = [match.group() for match in matches]
        components = [span(start + match.start(), start + match.end()) for match in matches]
        source_span = span(start, end)

        def append(form: str, index: int = 0, *, atom=None, body=None, head=None):
            analysis = _hash(["nabt.controlled-arabic.v1", "nabt.text-reader.v1", source_id,
                              source_hash, scope, source_span["start"], source_span["end"], form, index])
            common = {"scope": scope, "source_id": source_id, "source_sha256": source_hash,
                      "span": source_span, "analysis_id": analysis}
            semantic = {"atom": atom} if atom is not None else {"body": body, "head": head, "kind": form}
            ident = _hash({**semantic, **common, "semantic_version": "nabt.signed-horn.v1"})
            record = {**common, "clause_id": ident, "component_spans": components}
            if atom is not None:
                record.update(kind="fact", atom=atom)
            else:
                record.update(kind="rule", body=body, head=head, rule_kind=form)
            clauses.append(record)

        def unary(name):
            return {"predicate": _token_name(name), "args": ["?x"], "positive": True}

        if tokens[0] in {"مفهوم", "علاقة", "فرد"}:
            if len(tokens) != 2:
                raise ValueError("Invalid declaration")
            _token_name(tokens[1])
        elif tokens[0] == "هل":
            _atom(tokens[1:])  # A question is never a premise.
        elif tokens[0] == "تعريف":
            if len(tokens) < 4 or len(tokens) % 2 or tokens[2] != "هو" or any(t != "و" for t in tokens[4::2]):
                raise ValueError("Invalid definition")
            defined = unary(tokens[1])
            members = [unary(t) for t in tokens[3::2]]
            for index, member in enumerate(members):
                append("definition_forward", index, body=[defined], head=member)
            append("definition_reverse", body=members, head=defined)
        elif tokens[0] == "كل":
            if len(tokens) != 4 or tokens[2] != "هو":
                raise ValueError("Invalid universal")
            append("universal", body=[unary(tokens[1])], head=unary(tokens[3]))
        elif tokens[0] == "إذا":
            if tokens.count("فإن") != 1:
                raise ValueError("Invalid conditional")
            pivot = tokens.index("فإن")
            begin = 2 if len(tokens) > 1 and tokens[1] == "كان" else 1
            cuts = [begin - 1] + [i for i in range(begin, pivot) if tokens[i] == "و"] + [pivot]
            body = [_atom(tokens[a + 1:b], True) for a, b in zip(cuts, cuts[1:])]
            head = _atom(tokens[pivot + 1:], True)
            variables = {arg for atom in body for arg in atom["args"] if arg.startswith("?")}
            if not {arg for arg in head["args"] if arg.startswith("?")} <= variables:
                raise ValueError("Unsafe source rule")
            append("explicit_rule", body=body, head=head)
        else:
            append("fact", atom=_atom(tokens))
    return clauses


def clause_matches_source(clause: object, source: dict) -> bool:
    if type(clause) is not dict:
        return False
    encoded = json.dumps(clause, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return any(encoded == json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
               for candidate in source_clauses(source))
