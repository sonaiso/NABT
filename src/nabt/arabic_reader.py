"""A source-preserving bridge for a declared fragment of Arabic syntax.

This is an installed reading law, not a claim to all Arabic parses. In
particular, two bare words do not acquire noun roles merely because one can
put them in a subject/predicate record. Readings retain their cues, speech
force and unmet obligations. Only an unambiguous, complete assertive reading
can contribute a premise. The kernel reparses the original bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from hashlib import sha256
import json
import re
import unicodedata

from .errors import NabtError, natural, resource_limit
from .learning.source_evidence import SourceBlob, SourceSpan
from .text_ir import (Atom, Declaration, Definition, Fact, ParsedDocument,
                      Query, Residual, Rule, Segment, MAX_NAME_CHARS,
                      content_id, require_name, span_dict)
from . import text_reader as v1

LANGUAGE_ID = "nabt.arabic-syntax.v1"
READER_VERSION = "nabt.arabic-reader.v2"
READING_NUMBER_DOMAIN = "nabt.arabic-reading.canonical-json-utf8.sentinel256.v1"
MAX_READING_BYTES = 2 * 1024 * 1024
MAX_ALTERNATIVES = 8
MAX_QUERY_CONTEXT_NAMES = 16_384


class Mood(IntEnum):
    ASSERT = 0
    QUESTION = 1
    COMMAND = 2
    PROHIBITION = 3
    WISH = 4
    HOPE = 5
    VOCATIVE = 6
    AMBIGUOUS = 7


# These are operation identifiers, not cell codes or truth values. The pinned
# source contracts and their exact formal limits are in MASHRU_SYNTAX_AUDIT.
LAWS = {
    1: "explicit_nominal_predication",
    2: "nominal_role_cues",
    3: "nominal_case_suffix",
    4: "explicit_negation",
    5: "assertive_conjunction",
    6: "complete_conditional",
    7: "one_way_universal",
    8: "polar_question",
    9: "emphasis_preserves_proposition",
    10: "nonassertive_mood",
    11: "preserve_unresolved_alternatives",
    12: "text_declared_binary_relation",
    13: "explicit_definition",
    14: "text_declaration",
}

_MARKS = frozenset("\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670")
_CASE = {"ُ": "nom", "ٌ": "nom", "َ": "acc", "ً": "acc", "ِ": "gen", "ٍ": "gen"}
_PRONOUNS = frozenset(("أنا", "نحن", "أنت", "أنتما", "أنتم", "أنتن", "هو", "هي", "هما", "هم", "هن",
                        "هذا", "هذه", "هذان", "هاتان", "هؤلاء", "ذلك", "تلك", "أولئك"))
_OPERATORS = frozenset(("هو", "هي", "ليس", "ليست", "هل", "أو", "أم", "بل", "لكن", "ثم", "و", "ف",
                       "إذا", "إن", "فإن", "فهو", "فهي", "كل", "من", "ما", "ماذا", "متى", "أين", "كيف",
                       "لا", "لم", "لن", "كان", "كانت", "يكون", "صار", "إنما", "إلا", "غير", "سوى",
                       "ليت", "لعل", "يا", "قال", "قالت", "يقول", "يقال", "زعم", "لولا", "لو", "حتى",
                       "تعريف", "مفهوم", "علاقة", "فرد", "في", "على", "عن", "إلى", "منذ", "مع"))
_NONASSERTIVE = {"ليت": Mood.WISH, "لعل": Mood.HOPE, "يا": Mood.VOCATIVE}
_WH = frozenset(("من", "ما", "ماذا", "متى", "أين", "كيف", "لماذا", "كم", "أي"))
# A written mark may be absent; it may not contradict the operator reading.
# Recognition is deliberately separate from lexical identity normalization.
_OPERATOR_FORMS = {
    "كل": ("كُلُّ",), "إن": ("إِنَّ", "إِنْ"), "فإن": ("فَإِنَّ",),
    "ليس": ("لَيْسَ",), "ليست": ("لَيْسَتْ",), "هل": ("هَلْ",),
    "هو": ("هُوَ",), "هي": ("هِيَ",), "إذا": ("إِذَا",), "كان": ("كَانَ",),
    "و": ("وَ",), "أو": ("أَوْ",), "ليت": ("لَيْتَ",), "لعل": ("لَعَلَّ",), "يا": ("يَا",),
}


def _bare(text: str) -> str:
    """Recognize operators only; never use this as lexical identity."""
    return "".join(c for c in text if c not in _MARKS)


@dataclass(frozen=True, slots=True)
class Cue:
    law: int
    role: str
    span: SourceSpan
    surface: str
    value: str

    def as_dict(self) -> dict:
        return {"law": self.law, "law_name": LAWS[self.law], "role": self.role,
                "span": span_dict(self.span), "surface": self.surface, "value": self.value}


@dataclass(frozen=True, slots=True)
class Alternative:
    form: str
    mood: Mood
    span: SourceSpan
    atoms: tuple[Atom, ...] = ()
    cues: tuple[Cue, ...] = ()
    obligations: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {"form": self.form, "mood": self.mood.name, "mood_code": int(self.mood),
                "span": span_dict(self.span), "atoms": [a.as_dict() for a in self.atoms],
                "cues": [c.as_dict() for c in self.cues], "obligations": list(self.obligations),
                "authority": "READING_CANDIDATE_ONLY"}


@dataclass(frozen=True, slots=True)
class ReadingStep:
    span: SourceSpan
    form: str
    mood: Mood
    cues: tuple[Cue, ...]
    alternatives: tuple[Alternative, ...] = ()
    obligations: tuple[str, ...] = ()
    fact_count: int = 0
    rule_count: int = 0
    query_count: int = 0

    def as_dict(self) -> dict:
        return {"span": span_dict(self.span), "form": self.form,
                "mood": self.mood.name, "mood_code": int(self.mood),
                "cues": [c.as_dict() for c in self.cues],
                "alternatives": [a.as_dict() for a in self.alternatives],
                "obligations": list(self.obligations),
                "fact_count": self.fact_count, "rule_count": self.rule_count,
                "query_count": self.query_count}


@dataclass(frozen=True, slots=True)
class ArabicReading:
    document: ParsedDocument
    steps: tuple[ReadingStep, ...]

    @property
    def accepted(self) -> bool:
        return self.document.accepted

    def as_dict(self) -> dict:
        return {"language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
                "accepted": self.accepted, "status": "INTERPRETED" if self.accepted else "DEFER",
                "world_truth": "NOT_ESTABLISHED", "document": self.document.as_dict(),
                "steps": [s.as_dict() for s in self.steps],
                "interpretation_scope": "INSTALLED_FRAGMENT_NOT_ALL_ARABIC"}

    def packet(self) -> dict:
        raw = _wire(self.as_dict())
        return {"domain": READING_NUMBER_DOMAIN, "language_id": LANGUAGE_ID,
                "number_hex": hex(int.from_bytes(b"\x01" + raw, "big")),
                "wire_sha256": sha256(raw).hexdigest(), "authority": "ENCODING_ONLY"}


def _wire(value: dict) -> bytes:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > MAX_READING_BYTES:
        raise resource_limit("Arabic reading report exceeds its byte budget")
    return raw


def decode_reading_number(number: int) -> dict:
    """Decode transport, then re-read its source; never trust a transported IR."""
    natural(number, "reading_number")
    if number.bit_length() > 8 * (MAX_READING_BYTES + 1):
        raise resource_limit("Arabic reading number exceeds its budget")
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    if not raw or raw[0] != 1:
        raise NabtError("INVALID_READING_NUMBER", "Missing reading sentinel")
    try:
        value = json.loads(raw[1:].decode("utf-8"))
        if type(value) is not dict or _wire(value) != raw[1:]:
            raise ValueError("noncanonical reading")
        doc = value["document"]
        fresh = read_arabic(doc["raw_text"], source_id=doc["source_id"], scope=doc["scope"]).as_dict()
        if _wire(fresh) != raw[1:]:
            raise ValueError("source reading mismatch")
        return fresh
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, NabtError) and exc.status == "DEFER":
            raise
        raise NabtError("INVALID_READING_NUMBER", "Reading does not replay from its source") from exc


def encode_cell_envelope(mood: Mood, cells: tuple[int, ...]) -> int:
    """The Lean envelope on already licensed A116 cells, not on arbitrary UTF-8."""
    from .codec import encode_cells
    if type(mood) is not Mood:
        raise NabtError("INVALID_READING_MOOD", "Use an installed speech-force tag")
    return 116 * encode_cells(cells) + int(mood)


def decode_cell_envelope(number: int) -> tuple[Mood, tuple[int, ...]]:
    from .codec import decode_number
    natural(number, "cell_envelope_number")
    if number % 116 >= len(Mood):
        raise NabtError("INVALID_READING_MOOD", "The numeric residue is not an installed mood")
    return Mood(number % 116), decode_number(number // 116)


class _Unresolved(Exception):
    def __init__(self, code: str, message: str, *, alternatives=(), cues=(), mood=Mood.AMBIGUOUS):
        super().__init__(message)
        self.code, self.message = code, message
        self.alternatives, self.cues, self.mood = tuple(alternatives), tuple(cues), mood


@dataclass
class _Context:
    source: SourceBlob
    individuals: set[str] = field(default_factory=set)
    relations: set[str] = field(default_factory=set)
    lexemes: dict[str, SourceSpan] = field(default_factory=dict)

    def cue(self, token: v1._Token, law: int, role: str, value: str | None = None) -> Cue:
        surface = token.span.extract(self.source).decode("utf-8")
        return Cue(law, role, token.span, surface, token.value if value is None else value)


def _kw(t: v1._Token, keyword: str) -> bool:
    return not t.quoted and _bare(t.value) == keyword


def _check_marks(token: v1._Token) -> None:
    if token.quoted:
        return
    cluster = []
    carrier = False
    for char in token.value + " ":
        if char in _MARKS:
            if not carrier:
                raise _Unresolved("UNSUPPORTED_ORPHAN_MARK", "An Arabic mark needs its own preceding carrier")
            cluster.append(char)
            continue
        if (sum(c in _CASE or c == "ْ" for c in cluster) > 1
                or cluster.count("ّ") > 1 or cluster.count("ٰ") > 1):
            raise _Unresolved("UNSUPPORTED_CONFLICTING_MARKS", "A carrier has incompatible or duplicate Arabic marks")
        cluster = []
        carrier = unicodedata.category(char).startswith("L")


def _operator_marks(token: v1._Token) -> None:
    if token.quoted or _bare(token.value) not in _OPERATOR_FORMS:
        return

    def marks(word):
        result = []
        for char in word:
            if char in _MARKS:
                result[-1].add(char)
            else:
                result.append(set())
        return result

    observed = marks(token.value)
    if not any(all(a <= b for a, b in zip(observed, marks(form)))
               for form in _OPERATOR_FORMS[_bare(token.value)]):
        raise _Unresolved("UNSUPPORTED_OPERATOR_VOCALIZATION", "Visible marks contradict the proposed operator reading")


def _name(ctx: _Context, t: v1._Token, *, noun: bool = False,
          case: str | None = None, variables: bool = False) -> tuple[str, tuple[Cue, ...]]:
    if not t.quoted and t.value.startswith("?"):
        return v1._term(t, variables=variables), ()
    if not t.quoted and _bare(t.value) in _PRONOUNS:
        raise _Unresolved("UNSUPPORTED_REFERENT", "A pronoun or deictic needs an independently bound referent")
    if not t.quoted and _bare(t.value) in _OPERATORS:
        raise _Unresolved("UNSUPPORTED_OPERATOR_SCOPE", "An operator cannot silently become a name")
    value = v1._name(t)
    cues = []
    # Only a noun role licensed by this construction permits removal of a
    # final case ending. Internal vowels, shadda, sukun and spelling stay put.
    # Both standard positions of accusative tanwin around support alif are
    # recognized; no other final alif is removed.
    if noun and not t.quoted:
        ending, stem = None, value
        if value.endswith(("ًا", "اً")):
            without_alif = value[:-2]
            with_alif = without_alif + "ا"
            options = [s for s in (without_alif, with_alif) if s in ctx.lexemes]
            if len(options) != 1:
                raise _Unresolved("UNSUPPORTED_ACCUSATIVE_ALIF_IDENTITY",
                                  "Final alif needs a text-attested stem identity; it may be part of the noun",
                                  cues=(ctx.cue(t, 11, "stem_alternatives", without_alif + " | " + with_alif),))
            ending, stem = "ً", options[0]
            attested = ctx.lexemes[stem]
            cues.append(Cue(3, "prior_stem_identity", attested,
                            attested.extract(ctx.source).decode("utf-8"), stem))
        elif value[-1:] in _CASE:
            ending, stem = value[-1], value[:-1]
        if ending is not None:
            if not stem or stem[-1:] in _CASE:
                raise _Unresolved("UNSUPPORTED_CASE_MARKS", "Multiple case marks are not a licensed lexical operation")
            if case is not None and _CASE[ending] != case:
                raise _Unresolved("CASE_ROLE_MISMATCH", "The visible case conflicts with the licensed noun role")
            value = stem
            cues.append(ctx.cue(t, 3, "noun_case_" + _CASE[ending], value))
    return value, tuple(cues)


def _role_cue(ctx: _Context, t: v1._Token) -> bool:
    if t.quoted:
        return True
    try:
        name, _ = _name(ctx, t, noun=True)
    except (v1._SyntaxResidual, _Unresolved):
        return False
    return name in ctx.individuals


def _atom(ctx: _Context, ts: tuple[v1._Token, ...], *, variables=False,
          licensed_nominal=False, subject_case="nom", predicate_case="nom") -> tuple[Atom, tuple[Cue, ...]]:
    if not ts:
        raise _Unresolved("UNSUPPORTED_EMPTY_CLAUSE", "A predicate requires an entire clause")
    if _kw(ts[0], "ليس") or _kw(ts[0], "ليست"):
        atom, cues = _atom(ctx, ts[1:], variables=variables,
                           subject_case="nom", predicate_case="acc")
        if not atom.positive:
            raise _Unresolved("UNSUPPORTED_NESTED_NEGATION", "Nested negation needs an explicit scope analysis")
        return atom.opposite(), (ctx.cue(ts[0], 4, "negative_operator"), *cues)
    if len(ts) == 3 and (_kw(ts[1], "هو") or _kw(ts[1], "هي")):
        subject, c1 = _name(ctx, ts[0], noun=True, case=subject_case, variables=variables)
        predicate, c2 = _name(ctx, ts[2], noun=True, case=predicate_case)
        return Atom(predicate, (subject,)), (*c1, ctx.cue(ts[1], 1, "predication_marker"), *c2)
    if len(ts) == 2:
        subject, c1 = _name(ctx, ts[0], noun=True, case=subject_case, variables=variables)
        predicate, c2 = _name(ctx, ts[1], noun=True, case=predicate_case)
        if _role_cue(ctx, ts[0]) and not _role_cue(ctx, ts[1]):
            return Atom(predicate, (subject,)), (*c1, ctx.cue(ts[0], 2, "subject_role", subject), *c2)
        span = v1._span(ctx.source, ts[0].span.start, ts[-1].span.end)
        raise _Unresolved("UNSUPPORTED_NOMINAL_ROLE", "Bare words need a noun-role cue or a text declaration",
                          alternatives=(
                              Alternative("nominal_candidate", Mood.ASSERT, span, (Atom(predicate, (subject,)),),
                                          obligations=("NOUN_ROLE_EVIDENCE",)),
                              Alternative("predicate_before_subject_or_unresolved_roles", Mood.AMBIGUOUS, span,
                                          (Atom(subject, (predicate,)),),
                                          obligations=("PREDICATION_DIRECTION_EVIDENCE",)),))
    if len(ts) == 3:
        relation, cr = _name(ctx, ts[1])
        if relation in ctx.relations:
            subject, c1 = _name(ctx, ts[0], noun=True, case="nom", variables=variables)
            obj, c2 = _name(ctx, ts[2], noun=True, case="acc", variables=variables)
            return Atom(relation, (subject, obj)), (*c1, ctx.cue(ts[1], 12, "declared_relation"), *cr, *c2)
    raise _Unresolved("UNSUPPORTED_CLAUSE", "This complete clause has no licensed reading in the installed fragment")


def _split_wa(ctx: _Context, ts: tuple[v1._Token, ...]) -> tuple[tuple[v1._Token, ...], tuple[Cue, ...]]:
    """Expose a written waw only in a noninitial coordination position.

    A word beginning with waw is NOT sufficient evidence. Attached waw is
    split only when a complete left clause precedes it, or in the explicitly
    enumerated property position after a copula. Other cases remain whole.
    """
    out: list[v1._Token] = []
    cues: list[Cue] = []
    for t in ts:
        if not t.quoted and len(t.value) > 1 and t.value.startswith("و") and len(out) >= 2:
            prefix = tuple(out)
            try:
                _atom(ctx, prefix)
            except (v1._SyntaxResidual, _Unresolved):
                out.append(t)
                continue
            # A complete second clause can license a syntactic split in this
            # fragment. A single right-hand word can also be a lexical waw
            # (e.g. a second adjective); never amputate it by position alone.
            start = t.span.start
            waw_end = start + len("و".encode("utf-8"))
            rest = t.value[1:]
            if rest.startswith("َ"):
                waw_end += len("َ".encode("utf-8"))
                rest = rest[1:]
            if not rest:
                out.append(t)
                continue
            waw = v1._Token("و", v1._span(ctx.source, start, waw_end))
            remainder = v1._Token(rest, v1._span(ctx.source, waw_end, t.span.end))
            try:
                whole_name, _ = _name(ctx, t, noun=True)
                rest_name, _ = _name(ctx, remainder, noun=True)
            except (v1._SyntaxResidual, _Unresolved):
                whole_name = rest_name = None
            if (t is ts[-1] or whole_name in ctx.lexemes or
                    rest_name not in ctx.individuals):
                span = v1._span(ctx.source, ts[0].span.start, ts[-1].span.end)
                raise _Unresolved("UNSUPPORTED_WAW_SEGMENTATION", "Attached waw versus lexical initial waw needs evidence",
                                  alternatives=(
                                      Alternative("waw_conjunction", Mood.ASSERT, span,
                                                  obligations=("WAW_SEGMENTATION_EVIDENCE",)),
                                      Alternative("lexical_waw", Mood.AMBIGUOUS, span,
                                                  obligations=("MULTIPLE_PREDICATES_OR_MODIFIER_SCOPE",)),),
                                  cues=(ctx.cue(t, 11, "waw_or_lexeme"),))
            out.extend((waw, remainder))
            cues.append(ctx.cue(waw, 5, "written_conjunction"))
        else:
            out.append(t)
    return tuple(out), tuple(cues)


def _conjunction(ctx: _Context, ts: tuple[v1._Token, ...], *, variables=False,
                 licensed_nominal=False, subject_case="nom", predicate_case="nom") -> tuple[tuple[Atom, ...], tuple[Cue, ...]]:
    ts, attached_cues = _split_wa(ctx, ts)
    pieces, start, connector_cues = [], 0, list(attached_cues)
    for i, t in enumerate(ts):
        if _kw(t, "و"):
            if i == start:
                raise _Unresolved("UNSUPPORTED_EMPTY_CONJUNCT", "Conjunction requires both operands")
            pieces.append(ts[start:i])
            start = i + 1
            connector_cues.append(ctx.cue(t, 5, "conjunction"))
    pieces.append(ts[start:])
    if len(pieces) > v1.MAX_RULE_PREMISES:
        raise resource_limit("Arabic conjunction exceeds its premise budget")
    atoms, cues = [], list(connector_cues)
    for part in pieces:
        if len(part) == 1 and atoms and len(atoms[0].args) == 1 and atoms[0].positive:
            # A shared subject is licensed for coordinated nominal predicates,
            # but never for a negative conjunct (¬(P∧Q) is not ¬P∧¬Q).
            if any(a.args != atoms[0].args for a in atoms):
                raise _Unresolved("UNSUPPORTED_COORDINATION_ATTACHMENT", "An omitted subject follows more than one possible antecedent")
            name, cs = _name(ctx, part[0], noun=True, case=predicate_case)
            atom = Atom(name, atoms[0].args)
            cs = (*cs, ctx.cue(part[0], 5, "shared_nominal_subject"))
        else:
            atom, cs = _atom(ctx, part, variables=variables, licensed_nominal=licensed_nominal,
                            subject_case=subject_case, predicate_case=predicate_case)
        atoms.append(atom)
        cues.extend(cs)
    if len(atoms) > 1 and any(not a.positive for a in atoms):
        # Explicitly repeated negation is clear; an outer negation's scope
        # across waw needs a richer formula algebra than this Horn bridge.
        if not all(p and (_kw(p[0], "ليس") or _kw(p[0], "ليست")) for p in pieces):
            raise _Unresolved("UNSUPPORTED_NEGATION_SCOPE", "Negation and coordination need a scope witness",
                              cues=cues)
    return tuple(atoms), tuple(cues)


def _tokens(text: str, start: int, end: int, offsets: list[int], source: SourceBlob) -> tuple[v1._Token, ...]:
    # Commas separate conditional clauses, not documents. They remain tokens
    # with their exact spans; no source byte is discarded by the reader.
    raw = v1._tokens(text, start, end, offsets, source)
    out = []
    for t in raw:
        if t.quoted:
            out.append(t)
            continue
        index, byte_start = 0, t.span.start
        for match in re.finditer("[,،]", t.value):
            a, b = match.span()
            if a > index:
                word = t.value[index:a]
                stop = byte_start + len(word.encode("utf-8"))
                out.append(v1._Token(word, v1._span(source, byte_start, stop)))
                byte_start = stop
            stop = byte_start + len(t.value[a:b].encode("utf-8"))
            out.append(v1._Token(t.value[a:b], v1._span(source, byte_start, stop)))
            byte_start, index = stop, b
        if index < len(t.value):
            out.append(v1._Token(t.value[index:], v1._span(source, byte_start, t.span.end)))
    if len(out) > v1.MAX_STATEMENT_TOKENS:
        raise resource_limit("Arabic statement exceeds its token budget")
    return tuple(out)


def _read_arabic(raw: bytes | str, *, source_id: str = "text", scope: str = "default",
                 query_subjects: frozenset[str] = frozenset(),
                 query_relations: frozenset[str] = frozenset()) -> ArabicReading:
    source = v1._source(raw, source_id, scope)
    text = source.raw_bytes.decode("utf-8")
    offsets = [0]
    for ch in text:
        offsets.append(offsets[-1] + len(ch.encode("utf-8")))
    regions = v1._regions(text)
    if sum(k == "statement" for k, _, _ in regions) > v1.MAX_STATEMENTS:
        raise resource_limit("Arabic source exceeds its statement budget")
    # Only parse_query supplies active-theory names. Source admission and
    # reading-number replay always start with an empty local lexical context.
    # Cross-source names do not become local stem-evidence spans.
    ctx = _Context(source, individuals=set(query_subjects), relations=set(query_relations))
    facts, rules, queries, declarations, definitions, residuals, segments, steps = [], [], [], [], [], [], [], []
    token_total = 0

    for kind, start, end in regions:
        span = v1._span(source, offsets[start], offsets[end])
        if kind != "statement":
            segments.append(Segment(span, kind))
            continue
        if span.end - span.start > v1.MAX_STATEMENT_BYTES:
            raise resource_limit("Arabic statement exceeds its byte budget")
        before = len(facts), len(rules), len(queries)
        cues, alternatives, obligations = (), (), ()
        mood, form = Mood.ASSERT, "unresolved"
        # Stage every record per statement; a failed trailing conjunct cannot
        # leave a prefix fact even in the visible candidate projection.
        fs, rs, qs, ds, defs = [], [], [], [], []

        def aid(label: str, i: int = 0) -> str:
            return content_id([LANGUAGE_ID, READER_VERSION, source_id, source.sha256,
                               scope, span.start, span.end, label, i])

        try:
            ts = _tokens(text, start, end, offsets, source)
            for token in ts:
                _check_marks(token)
                _operator_marks(token)
            token_total += len(ts)
            if token_total > v1.MAX_TOKENS:
                raise resource_limit("Arabic source exceeds its token budget")
            components = tuple(t.span for t in ts)
            first = _bare(ts[0].value) if not ts[0].quoted else ""
            if first in ("مفهوم", "علاقة", "فرد"):
                if len(ts) != 2:
                    raise _Unresolved("UNSUPPORTED_DECLARATION", "A declaration needs one exact name")
                name, cues = _name(ctx, ts[1])
                declaration_kind = {"مفهوم": "concept", "علاقة": "relation", "فرد": "individual"}[first]
                ds.append(Declaration(declaration_kind, name, span, components, aid("declaration")))
                cues = (*cues, ctx.cue(ts[0], 14, "declaration"))
                form = "declaration"
            elif first == "تعريف":
                if len(ts) < 4 or not _kw(ts[2], "هو"):
                    raise _Unresolved("UNSUPPORTED_DEFINITION", "Definition requires an explicit equivalence marker")
                name, cs = _name(ctx, ts[1], noun=True)
                members, member_cues = [], []
                expect_name = True
                for t in ts[3:]:
                    if expect_name:
                        member, cc = _name(ctx, t, noun=True)
                        members.append(member)
                        member_cues.extend(cc)
                    elif not _kw(t, "و"):
                        raise _Unresolved("UNSUPPORTED_DEFINITION", "Definition members need explicit separated waw")
                    expect_name = not expect_name
                if expect_name or len(members) > v1.MAX_DEFINITION_MEMBERS:
                    raise _Unresolved("UNSUPPORTED_DEFINITION", "Incomplete or oversized definition")
                defined = Atom(name, ("?x",))
                member_atoms = tuple(Atom(p, ("?x",)) for p in members)
                defs.append(Definition(name, tuple(members), span, components, aid("definition")))
                rs.extend(Rule((defined,), member, span, components, aid("definition_forward", i), "definition_forward")
                          for i, member in enumerate(member_atoms))
                rs.append(Rule(member_atoms, defined, span, components, aid("definition_reverse"), "definition_reverse"))
                cues = (*cs, *member_cues, ctx.cue(ts[0], 13, "explicit_definition"))
                form = "definition"
            elif first in _NONASSERTIVE:
                mood, form = _NONASSERTIVE[first], "speech_act"
                cues = (ctx.cue(ts[0], 10, "speech_force", mood.name),)
                if mood == Mood.VOCATIVE and len(ts) == 2:
                    _name(ctx, ts[1], noun=True)
                elif mood != Mood.VOCATIVE:
                    atoms, cs = _conjunction(ctx, ts[1:], licensed_nominal=True, subject_case="acc")
                    cues += cs
                    alternatives = (Alternative("nonasserted_content", mood, span, atoms, cues),)
                else:
                    raise _Unresolved("UNSUPPORTED_ACT_CONTENT", "Vocative plus request needs a separate act parser",
                                      mood=mood, cues=cues)
            elif first in ("لا", "إن", "أو", "أم") and not (first == "إن" and "ّ" in ts[0].value):
                labels = (("negative_assertion", Mood.ASSERT), ("prohibition", Mood.PROHIBITION)) if first == "لا" else (
                         (("emphasis", Mood.ASSERT), ("condition", Mood.ASSERT)) if first == "إن" else (
                         ("disjunctive_reading", Mood.ASSERT), ("alternative_reading", Mood.AMBIGUOUS)))
                alternatives = tuple(Alternative(label, m, span, obligations=("OPERATOR_SENSE_AND_SCOPE",)) for label, m in labels)
                raise _Unresolved("UNSUPPORTED_OPERATOR_AMBIGUITY", "Operator sense is not fixed by its unmarked spelling",
                                  alternatives=alternatives, cues=(ctx.cue(ts[0], 11, "ambiguous_operator"),))
            elif first in _WH:
                raise _Unresolved("UNSUPPORTED_OPEN_QUESTION", "An open question needs variable-answer semantics", mood=Mood.QUESTION,
                                  cues=(ctx.cue(ts[0], 8, "open_question"),))
            elif first in ("كان", "كانت", "يكون", "صار", "لم", "لن", "لو", "لولا", "إنما", "قال", "قالت", "يقول", "يقال", "زعم"):
                raise _Unresolved("UNSUPPORTED_TIME_OR_SCOPE", "Temporal, counterfactual, exclusive or reported scope must be retained",
                                  cues=(ctx.cue(ts[0], 11, "unlowered_operator"),))
            elif any(_kw(t, "أو") for t in ts):
                split = next(i for i, t in enumerate(ts) if _kw(t, "أو"))
                candidates = []
                for part in (ts[:split], ts[split + 1:]):
                    try:
                        atoms, cs = _conjunction(ctx, part)
                    except (v1._SyntaxResidual, _Unresolved):
                        atoms, cs = (), ()
                    candidates.append(Alternative("disjunct", Mood.ASSERT, span, atoms, cs,
                                                  ("DISJUNCTION_CASE_ANALYSIS",)))
                raise _Unresolved("UNSUPPORTED_DISJUNCTION", "Neither disjunct is asserted by an unresolved disjunction",
                                  alternatives=candidates, cues=(ctx.cue(ts[split], 11, "disjunction"),))
            elif any(_kw(t, "إلا") or _kw(t, "غير") or _kw(t, "سوى") for t in ts):
                raise _Unresolved("UNSUPPORTED_EXCEPTION_DOMAIN", "Exception needs domain and connectedness evidence")
            elif first == "إذا":
                split_positions = [i for i, t in enumerate(ts) if _kw(t, "فإن")]
                body_start = 2 if len(ts) > 1 and _kw(ts[1], "كان") else 1
                if len(split_positions) != 1 or split_positions[0] <= body_start or split_positions[0] >= len(ts) - 1:
                    raise _Unresolved("UNSUPPORTED_INCOMPLETE_CONDITIONAL", "A conditional needs both clauses and its explicit connector")
                cut = split_positions[0]
                body_ts = ts[body_start:cut]
                if body_ts and body_ts[-1].value in (",", "،"):
                    body_ts = body_ts[:-1]
                body, c1 = _conjunction(ctx, body_ts, variables=True, licensed_nominal=body_start == 2,
                                        predicate_case="acc" if body_start == 2 else "nom")
                heads, c2 = _conjunction(ctx, ts[cut + 1:], variables=True, licensed_nominal=True,
                                         subject_case="acc")
                bound = frozenset(v for a in body for v in a.variables)
                if any(not h.variables <= bound for h in heads):
                    raise _Unresolved("UNSUPPORTED_UNBOUND_CONCLUSION", "A head variable must be bound in the antecedent")
                rs.extend(Rule(body, head, span, components, aid("conditional", i), "explicit_rule") for i, head in enumerate(heads))
                cues = (ctx.cue(ts[0], 6, "condition"), *c1, ctx.cue(ts[cut], 6, "consequence_connector"), *c2)
                form = "conditional"
            elif first == "كل":
                if "ْ" in ts[0].value or (any(c in _MARKS for c in ts[0].value) and "ّ" not in ts[0].value):
                    raise _Unresolved("UNSUPPORTED_QUANTIFIER_READING", "The vocalized form does not license the universal quantifier",
                                      mood=Mood.COMMAND, cues=(ctx.cue(ts[0], 11, "quantifier_or_command"),))
                if len(ts) == 4 and (_kw(ts[2], "هو") or _kw(ts[2], "هي")):
                    left, right = ts[1], ts[3]
                elif len(ts) == 3:
                    left, right = ts[1], ts[2]
                    if "ّ" not in ts[0].value and not left.value.endswith("ٍ"):
                        raise _Unresolved("UNSUPPORTED_QUANTIFIER_READING", "Bare كل plus two names may be imperative or an incomplete noun phrase",
                                          alternatives=(
                                              Alternative("universal", Mood.ASSERT, span,
                                                          obligations=("QUANTIFIER_AND_PREDICATE_BOUNDARY",)),
                                              Alternative("imperative_or_noun_phrase", Mood.COMMAND, span,
                                                          obligations=("LEXICAL_ROLES",)),))
                else:
                    raise _Unresolved("UNSUPPORTED_UNIVERSAL", "The installed universal has exactly two concept terms")
                a, c1 = _name(ctx, left, noun=True, case="gen")
                b, c2 = _name(ctx, right, noun=True, case="nom")
                rs.append(Rule((Atom(a, ("?x",)),), Atom(b, ("?x",)), span, components, aid("universal"), "universal"))
                cues, form = (ctx.cue(ts[0], 7, "universal"), *c1, *c2), "universal"
            elif first == "هل":
                mood, form = Mood.QUESTION, "polar_question"
                atom, cs = _atom(ctx, ts[1:])
                qs.append(Query(atom, span, components, aid("query"), scope))
                cues = (ctx.cue(ts[0], 8, "question"), *cs)
            else:
                if first == "إن" and "ّ" in ts[0].value:
                    atom, cs = _atom(ctx, ts[1:], licensed_nominal=True, subject_case="acc")
                    atoms, cues, form = (atom,), (ctx.cue(ts[0], 9, "emphasis"), *cs), "emphatic_nominal"
                else:
                    atoms, cues = _conjunction(ctx, ts)
                    form = "conjunction" if len(atoms) > 1 else "predication"
                fs.extend(Fact(atom, span, components, aid(form, i)) for i, atom in enumerate(atoms))
            # A trailing question marker cannot turn an assertion into evidence.
            # Only the explicit هل path currently creates an answerable query.
            tail = text[end:].lstrip()
            if tail.startswith(("؟", "?")) and mood != Mood.QUESTION:
                raise _Unresolved("UNSUPPORTED_QUESTION_FORCE", "Question punctuation requires an explicit supported question reading",
                                  mood=Mood.QUESTION, cues=cues)
        except (v1._SyntaxResidual, _Unresolved) as exc:
            residuals.append(Residual(exc.code, exc.message, span))
            segments.append(Segment(span, "residual"))
            if isinstance(exc, _Unresolved):
                alternatives = exc.alternatives
                cues = tuple(dict.fromkeys((*cues, *exc.cues)))
                if mood == Mood.ASSERT:
                    mood = exc.mood
            obligations = (exc.code,)
            form = "unresolved"
        else:
            facts.extend(fs); rules.extend(rs); queries.extend(qs)
            declarations.extend(ds); definitions.extend(defs)
            for d in ds:
                ctx.lexemes[d.name] = d.component_spans[-1]
                if d.kind == "individual":
                    ctx.individuals.add(d.name)
                elif d.kind == "relation":
                    ctx.relations.add(d.name)
            # A successfully read explicit subject can be reused in this
            # source's subsequent clauses; no cross-source lexical authority.
            for f in fs:
                ctx.individuals.add(f.atom.args[0])
            # Lexical role/identity evidence is local to the original source.
            # It is rebuilt on every read and never imported from caller IR.
            names = {a.predicate for f in fs for a in (f.atom,)}
            names.update(x for f in fs for x in f.atom.args)
            names.update(a.predicate for r in rs for a in (*r.body, r.head))
            for token in ts:
                try:
                    n, _ = _name(ctx, token, noun=True)
                except (v1._SyntaxResidual, _Unresolved):
                    continue
                if n in names:
                    ctx.lexemes[n] = token.span
            segments.append(Segment(span, "statement"))
        steps.append(ReadingStep(span, form, mood, tuple(cues), tuple(alternatives), obligations,
                                 len(facts) - before[0], len(rules) - before[1], len(queries) - before[2]))

    if not steps:
        residuals.append(Residual("EMPTY_DOCUMENT", "No statement occurs in the source", v1._span(source, 0, len(source.raw_bytes))))
    doc = ParsedDocument(source=source, scope=scope, language_id=LANGUAGE_ID, reader_version=READER_VERSION,
                         segments=tuple(segments), declarations=tuple(declarations), definitions=tuple(definitions),
                         facts=tuple(facts), rules=tuple(rules), queries=tuple(queries), residuals=tuple(residuals))
    result = ArabicReading(doc, tuple(steps))
    _wire(result.as_dict())
    return result


def read_arabic(raw: bytes | str, *, source_id: str = "text", scope: str = "default") -> ArabicReading:
    return _read_arabic(raw, source_id=source_id, scope=scope)


def parse_document(raw: bytes | str, *, source_id: str = "text", scope: str = "default") -> ParsedDocument:
    return read_arabic(raw, source_id=source_id, scope=scope).document


def parse_query(raw: bytes | str, *, source_id: str = "query", scope: str = "default",
                known_individuals: frozenset[str] = frozenset(),
                known_relations: frozenset[str] = frozenset()) -> Query:
    contexts = (("subject", known_individuals), ("relation", known_relations))
    if any(type(names) is not frozenset for _, names in contexts):
        raise NabtError("INVALID_QUERY_CONTEXT", "Query contexts require exact finite sets of previously read names")
    if sum(len(names) for _, names in contexts) > MAX_QUERY_CONTEXT_NAMES:
        raise resource_limit("Query lexical context exceeds its declared name budget")
    for role, names in contexts:
        for name in names:
            if type(name) is str and len(name) > MAX_NAME_CHARS:
                raise resource_limit("Query lexical context contains a name beyond its declared length budget")
            try:
                require_name(name, role)
            except NabtError as exc:
                raise NabtError("INVALID_QUERY_CONTEXT", "Query context names must be exact nonempty ground names") from exc
            if name.startswith("?"):
                raise NabtError("INVALID_QUERY_CONTEXT", "A query context cannot declare variable names")
    reading = _read_arabic(raw, source_id=source_id, scope=scope,
                           query_subjects=known_individuals, query_relations=known_relations)
    doc = reading.document
    if (not doc.accepted or len(doc.queries) != 1 or doc.facts or doc.rules or doc.declarations or doc.definitions
            or len(reading.steps) != 1):
        raise NabtError("INVALID_QUERY", "An Arabic query requires exactly one complete supported polar question",
                        details={"residuals": [r.as_dict() for r in doc.residuals]})
    return doc.queries[0]


__all__ = ["LANGUAGE_ID", "READER_VERSION", "Mood", "LAWS", "ArabicReading", "read_arabic",
           "parse_document", "parse_query", "decode_reading_number", "encode_cell_envelope", "decode_cell_envelope"]
