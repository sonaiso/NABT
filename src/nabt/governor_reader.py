"""Source-built noun/case evidence for the first governor activation profile.

The full finite case algebra is installed, but activation is deliberately
limited to explicit emphatic inna with two overtly marked nominal terms.
Unknown indefinites are not turned into globally named individuals. The
reader can establish their roles while deferring referential interpretation.
"""

from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
import json

from . import arabic_reader as base
from .errors import NabtError
from .governors import (LAW_ID, ROLE_MARK_DOMAIN, EXPECTED_TABLE_SHA256,
                        check_assignment, lookup, role_mark_number)
from .text_ir import Atom, ParsedDocument, Query, span_dict

LANGUAGE_ID = "nabt.arabic-governors.v1"
READER_VERSION = "nabt.arabic-governor-reader.v1"
POLICY_ID = "nabt.governor-source-cues.v1"
DEFERRED_OBLIGATIONS = frozenset({
    "REFERENT_IDENTITY_EVIDENCE", "NOUN_CATEGORY_EVIDENCE", "VISIBLE_CASE_EVIDENCE",
    "GOVERNOR_BLOCKER_MA", "GOVERNOR_COMPLETE_TWO_TERM_CLAUSE", "GOVERNOR_SENSE_EVIDENCE",
    "DECLENSION_CLASS_EVIDENCE", "ORTHOGRAPHY_EVIDENCE",
})
EXPECTED_POLICY_SHA256 = "26fdd34913ccca180bb1bf19bd58d725881117c0d01027f51374fd29d578dfa6"
QATR_SHA256 = "2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d"


def replay_source_policy() -> dict:
    root = files("nabt").joinpath("data/source_evidence")
    raw = root.joinpath("governor_policy.json").read_bytes()
    source = root.joinpath("qatr.txt").read_bytes()
    if sha256(raw).hexdigest() != EXPECTED_POLICY_SHA256 or sha256(source).hexdigest() != QATR_SHA256:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Governor source policy or its pinned book differs", status="DEFER")
    policy = json.loads(raw)
    for p in policy["passages"]:
        part = source[p["start"]:p["end"]]
        if (p["source_sha256"] != QATR_SHA256 or sha256(part).hexdigest() != p["span_sha256"]
                or part.decode("utf-8") != p["raw_text"]):
            raise NabtError("INSTALLED_CONTRACT_FAILED", "Governor policy passage does not replay", status="DEFER")
    return {"policy_id": POLICY_ID, "policy_sha256": EXPECTED_POLICY_SHA256,
            "source_id": "qatr", "source_sha256": QATR_SHA256,
            "passages": [{k: v for k, v in p.items() if k != "raw_text"} for p in policy["passages"]],
            "authority": "AUTHORED_READING_POLICY_WITH_PINNED_TEXT_SUPPORT"}


def _observed_ending(token):
    if token.quoted:
        return None
    if token.value.endswith(("ًا", "اً")):
        return "ً"
    return token.value[-1] if token.value[-1:] in base._CASE else None


def _check_tanwin_position(token):
    """An internal tanwin cannot certify a noun in this spelling profile."""
    if token.quoted:
        return
    for index, char in enumerate(token.value):
        if char not in {"ً", "ٌ", "ٍ"}:
            continue
        remaining = base._bare(token.value[index + 1:])
        if remaining and not (char == "ً" and remaining == "ا" and token.value.endswith("ًا")):
            raise base._Unresolved("UNSUPPORTED_INTERNAL_TANWIN", "Only a final tanwin with its licensed support alif can be noun evidence")


def _member(ctx, token, role):
    """Extract a candidate name, noun evidence, and *observed* (not expected) case."""
    ending = _observed_ending(token)
    surface_mark = {"nom": 1, "acc": 0, "gen": 2}.get(base._CASE.get(ending))
    mark = surface_mark
    cues, errors, noun_evidence = [], [], []
    name = None
    try:
        name, cs = base._name(ctx, token, noun=True)
        cues.extend(base.Cue(c.law, "surface_case_mark", c.span, c.surface, ending)
                    if c.role.startswith("noun_case_") else c for c in cs)
    except (base.v1._SyntaxResidual, base._Unresolved) as exc:
        errors.append(exc.code)
        if isinstance(exc, base._Unresolved):
            cues.extend(exc.cues)
    stem = base._bare(name) if name is not None else ""
    if (ending is not None and (stem.endswith(("ا", "ى", "ي", "و"))
            or ending in {"ِ", "ٍ"}
            or stem.endswith("ات")
            or (ending not in {"ً", "ٌ", "ٍ"} and stem.endswith(("ان", "ون", "ين"))))):
        # A surface kasra can be accusative on a sound feminine plural; the
        # tanwin in قاضٍ does not itself establish a genitive role. A weak
        # ending may bear estimated inflection. Preserve the mark, withhold
        # the case assignment until a declension class has been established.
        errors.append("DECLENSION_CLASS_EVIDENCE")
        mark = None
    has_support_alif = token.value.endswith(("ًا", "اً"))
    if (ending == "ً" and not has_support_alif
            and not stem.endswith(("ة", "أ", "اء", "ى"))):
        errors.append("ORTHOGRAPHY_EVIDENCE")
        mark = None
    if (ending == "ً" and has_support_alif and stem.endswith(("ة", "أ", "اء", "ى"))):
        errors.append("ORTHOGRAPHY_EVIDENCE")
        mark = None
    if ending in {"ً", "ٌ", "ٍ"} and stem.startswith("ال"):
        # This bounded law cannot license tanwin while an al-article reading
        # remains possible. It does not silently choose a lexical initial al-.
        errors.append("ORTHOGRAPHY_EVIDENCE")
        mark = None
    if ending in {"ً", "ٌ", "ٍ"}:
        noun_evidence.append({"kind": "visible_tanwin", "span": span_dict(token.span),
                              "policy_rule": "noun_marks"})
        cues.append(ctx.cue(token, 15, "noun_evidence_tanwin", ending))
    if name is not None and name in ctx.nominals:
        prior = ctx.nominals[name]
        # This context is built only from earlier successfully read statements
        # in these exact source bytes, never from caller-supplied flags.
        prior_surface = prior.extract(ctx.source).decode("utf-8")
        noun_evidence.append({"kind": "prior_nominal_identity", "span": span_dict(prior),
                              "policy_rule": "noun_marks"})
        cues.append(base.Cue(15, "prior_nominal_identity", prior, prior_surface, name))
    if not noun_evidence:
        errors.append("NOUN_CATEGORY_EVIDENCE")
    if ending is None:
        errors.append("VISIBLE_CASE_EVIDENCE")
    record = {"role_code": role, "role": "inna_subject" if role == 0 else "inna_predicate",
              "span": span_dict(token.span), "surface": token.span.extract(ctx.source).decode("utf-8"),
              "lexeme": name, "category": "noun" if noun_evidence else None,
              "category_evidence": noun_evidence, "observed_mark": mark,
              "surface_ending": ending, "surface_mark": surface_mark,
              "role_mark_number": None if mark is None else {
                  "domain": ROLE_MARK_DOMAIN, "value": role_mark_number(role, mark),
                  "authority": "TYPED_ENCODING_ONLY"},
              "obligations": list(dict.fromkeys(errors))}
    if mark is not None:
        cues.append(ctx.cue(token, 16, record["role"], str(role_mark_number(role, mark))))
    return record, tuple(cues)


def _emphatic_nominal(ctx, tokens):
    """Construct lexical and syntactic inputs; only then call the algebra.

    The boundary invokes this only for unquoted, mark-checked إن with shadda.
    We still check its shape here; the table label itself cannot activate it.
    """
    policy = replay_source_policy()
    entries = lookup("إنّ")
    if len(entries) != 1 or entries[0].class_code != 2 or entries[0].implicit:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Emphatic inna row does not match the activation law", status="DEFER")
    entry = entries[0]
    report = {"law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
              "row_ids": [entry.row_id], "class_code": entry.class_code,
              "operator": {"span": span_dict(tokens[0].span),
                           "surface": tokens[0].span.extract(ctx.source).decode("utf-8"), "label": entry.label},
              "source_policy": policy, "roles": [], "case_check": None,
              "syntactic_evidence_complete": False, "referent_identity": None,
              "semantic_projection": "DEFER", "world_truth": "NOT_ESTABLISHED"}
    cues = [ctx.cue(tokens[0], 18, "governor_class", str(entry.class_code))]

    def defer(code, message, *, alternatives=()):
        raise base._Unresolved(code, message, cues=tuple(cues), alternatives=alternatives,
                               mood=base.Mood.ASSERT, governor=report)

    if (tokens[0].quoted or base._bare(tokens[0].value) != "إن"
            or "ّ" not in tokens[0].value):
        defer("GOVERNOR_SENSE_EVIDENCE", "Explicit emphatic inna requires its own visible shadda")
    if len(tokens) > 1 and base._kw(tokens[1], "ما"):
        defer("GOVERNOR_BLOCKER_MA", "Ma after the governor needs its blocking/scope interpretation")
    if len(tokens) != 3:
        defer("GOVERNOR_COMPLETE_TWO_TERM_CLAUSE", "This activation law needs exactly a subject and a simple predicate")

    for role, token in enumerate(tokens[1:]):
        record, cs = _member(ctx, token, role)
        report["roles"].append(record)
        cues.extend(cs)
    assignment = {r["role_code"]: r["observed_mark"] for r in report["roles"]}
    report["case_check"] = check_assignment(entry.class_code, assignment)
    missing = [name for role in report["roles"] for name in role["obligations"]]
    if missing:
        defer(missing[0], "A nominal term has unmet lexical, identity, or visible-case obligations")
    if not report["case_check"]["complete"]:
        defer("CASE_ROLE_MISMATCH", "Observed marks fail the installed governor equations")
    report["syntactic_evidence_complete"] = True

    subject, predicate = (r["lexeme"] for r in report["roles"])
    if subject not in ctx.individuals or subject not in ctx.referents:
        span = base.v1._span(ctx.source, tokens[0].span.start, tokens[-1].span.end)
        defer("REFERENT_IDENTITY_EVIDENCE", "A noun role does not identify a recurring individual; an indefinite needs referential evidence",
              alternatives=(base.Alternative("governed_nominal_without_referent", base.Mood.ASSERT,
                                              span, cues=tuple(cues), obligations=("REFERENT_IDENTITY_EVIDENCE",)),))
    reference = ctx.referents[subject]
    report["referent_identity"] = {"name": subject, "span": span_dict(reference),
                                   "scope": "PREVIOUSLY_READ_IN_THIS_SOURCE"}
    cues.append(base.Cue(17, "source_local_referent", reference,
                         reference.extract(ctx.source).decode("utf-8"), subject))
    cues.append(ctx.cue(tokens[1], 17, "explicit_subject_identity", subject))
    report["semantic_projection"] = "SOURCE_RELATIVE_ASSERTION"
    return Atom(predicate, (subject,)), tuple(cues), report


def read_arabic(raw: bytes | str, *, source_id: str = "text", scope: str = "default") -> base.ArabicReading:
    return base._read_arabic(raw, source_id=source_id, scope=scope, use_governors=True)


def parse_document(raw: bytes | str, *, source_id: str = "text", scope: str = "default") -> ParsedDocument:
    return read_arabic(raw, source_id=source_id, scope=scope).document


def parse_query(raw: bytes | str, *, source_id: str = "query", scope: str = "default",
                known_individuals: frozenset[str] = frozenset(),
                known_relations: frozenset[str] = frozenset()) -> Query:
    return base._parse_query(raw, source_id=source_id, scope=scope,
                             known_individuals=known_individuals, known_relations=known_relations,
                             use_governors=True)


__all__ = ["LANGUAGE_ID", "READER_VERSION", "POLICY_ID", "read_arabic", "parse_document",
           "parse_query", "replay_source_policy"]
