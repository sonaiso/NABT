"""A bounded, source-replayed bridge from written runs to word analyses.

Three levels remain distinct: exact written occurrences; licensed alternative
segmentations/lexical readings; and a small set of contextual case checks.
No Atom, individual identity, or factual premise is produced here. The policy
is an authored application of the pinned grammatical passages, not a theorem
that a dictionary or the Python parser covers Arabic.
"""

from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
from itertools import product
import json
import re
import unicodedata

from . import words
from .alphabet import ALPHABET_ID, parse_word
from .codec import encode_cells
from .errors import NabtError, natural, resource_limit
from .learning.source_evidence import SourceBlob, SourceSpan
from .text_ir import span_dict

LANGUAGE_ID = "nabt.arabic-words.v1"
READER_VERSION = "nabt.word-reader.v1"
NUMBER_DOMAIN = "nabt.word-reading.canonical-json-utf8.sentinel256.v1"
EXPECTED_POLICY_SHA256 = "c03134674fb8702af2d0ff4ce91c06d6b6b2f1422373da52e6449f24d1efd5f1"
MAX_SOURCE_BYTES = 8192
MAX_RUNS = 128
MAX_ALTERNATIVES = 32
MAX_COMPOSITIONS = 64
MAX_REPORT_BYTES = 2 * 1024 * 1024
_VOWELS = frozenset("ًٌٍَُِْ")
_MARKS = _VOWELS | frozenset("ّٰ")
_PUNCTUATION = frozenset(".،؛,:!?؟()[]{}")
_CLOSERS = {"«": "»", '"': '"', "“": "”"}


def _wire(value) -> bytes:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise NabtError("INVALID_WORD_REPORT", "A report must be bounded strict JSON") from error
    if len(raw) > MAX_REPORT_BYTES:
        raise resource_limit("Word report exceeds its byte budget")
    return raw


def _identity(value) -> str:
    return sha256(_wire(value)).hexdigest()


def _span(source: SourceBlob, start: int, end: int) -> SourceSpan:
    natural(start, "byte_start"); natural(end, "byte_end")
    if not start < end <= len(source.raw_bytes):
        raise NabtError("INVALID_WORD_SPAN", "A word span must be a nonempty source interval")
    raw = source.raw_bytes[start:end]
    try:
        raw.decode("utf-8", "strict")
    except UnicodeError as error:
        raise NabtError("INVALID_WORD_SPAN", "A word span splits a UTF-8 scalar") from error
    return SourceSpan(source.source_id, source.sha256, start, end, sha256(raw).hexdigest())


def replay_policy() -> dict:
    """Verify installed policy bytes and every cited interval, on every read."""
    root = files("nabt").joinpath("data/source_evidence")
    try:
        raw = root.joinpath("word_policy.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_POLICY_SHA256:
            raise ValueError("word policy pin differs")
        policy = json.loads(raw)
        sources = {}
        for source_id, digest in policy["sources"].items():
            if re.fullmatch(r"[a-z][a-z0-9_]*", source_id) is None:
                raise ValueError("bad installed source name")
            source = root.joinpath(source_id + ".txt").read_bytes()
            if sha256(source).hexdigest() != digest:
                raise ValueError("word source pin differs")
            sources[source_id] = source
        for rule in policy["rules"]:
            excerpt = sources[rule["source_id"]][rule["start"]:rule["end"]]
            if (sha256(excerpt).hexdigest() != rule["sha256"]
                    or excerpt.decode("utf-8") != rule["text"]):
                raise ValueError("word rule excerpt differs")
        return policy
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed word-source policy cannot be replayed", status="DEFER") from error


def _clusters(text: str) -> list[tuple[str, frozenset[str], int, int]]:
    """Keep source character intervals; comparing sets never rewrites bytes."""
    result = []
    i = 0
    while i < len(text):
        start, char = i, text[i]
        if not (unicodedata.category(char).startswith("L") and "\u0600" <= char <= "\u06ff"):
            code = "MARK_WITHOUT_CARRIER" if unicodedata.category(char).startswith("M") else "UNSUPPORTED_WORD_SCRIPT"
            raise NabtError(code, "A lexical run needs supported Arabic carriers", status="REJECT" if code == "MARK_WITHOUT_CARRIER" else "DEFER")
        i += 1
        marks = []
        while i < len(text) and unicodedata.category(text[i]).startswith("M"):
            if text[i] not in _MARKS:
                raise NabtError("UNSUPPORTED_WORD_MARK", "This mark has no installed lexical-reading law", status="DEFER")
            marks.append(text[i]); i += 1
        if len(marks) != len(set(marks)) or sum(m in _VOWELS for m in marks) > 1:
            raise NabtError("CONFLICTING_MARKS", "One carrier has conflicting or repeated marks")
        result.append((char, frozenset(marks), start, i))
    return result


def _matches(observed, template) -> bool:
    return (len(observed) == len(template)
            and all(a[0] == b[0] and a[1] <= b[1] for a, b in zip(observed, template)))


def _source(raw: bytes | str, source_id: str, scope: str) -> SourceBlob:
    if type(scope) is not str or not scope or len(scope) > 256 or any(ord(c) < 32 for c in scope):
        raise NabtError("INVALID_WORD_SCOPE", "Use a bounded nonempty scope identity")
    if type(raw) is str:
        try:
            raw = raw.encode("utf-8", "strict")
        except UnicodeError as error:
            raise NabtError("INVALID_UTF8", "Input has an invalid Unicode scalar") from error
    if type(raw) is not bytes or not raw:
        raise NabtError("INVALID_WORD_SOURCE", "A source must contain nonempty UTF-8 bytes")
    if len(raw) > MAX_SOURCE_BYTES:
        raise resource_limit("Word-reading source exceeds its byte budget", maximum_bytes=MAX_SOURCE_BYTES)
    try:
        return SourceBlob(source_id, raw)
    except (ValueError, TypeError, UnicodeError) as error:
        raise NabtError("INVALID_WORD_SOURCE", "Invalid source identity or UTF-8 source") from error


def _scan(source: SourceBlob) -> list[dict]:
    """An exact byte partition; written runs are not yet grammatical words."""
    text = source.raw_bytes.decode("utf-8")
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))
    result, i, runs = [], 0, 0
    while i < len(text):
        start, char = i, text[i]
        if char.isspace():
            kind = "spacing"
            while i < len(text) and text[i].isspace():
                i += 1
        elif char in _CLOSERS:
            end = text.find(_CLOSERS[char], i + 1)
            if end < 0:
                raise NabtError("UNTERMINATED_QUOTE", "A quoted mention must have a matching end")
            kind, i = "quotation", end + 1
        elif char in _PUNCTUATION:
            kind, i = "punctuation", i + 1
        else:
            kind = "written_run"
            while (i < len(text) and not text[i].isspace()
                   and text[i] not in _PUNCTUATION and text[i] not in _CLOSERS):
                i += 1
            runs += 1
            if runs > MAX_RUNS:
                raise resource_limit("Too many written runs", maximum=MAX_RUNS)
        span = _span(source, offsets[start], offsets[i])
        result.append({"kind": kind, "span": span_dict(span), "surface": span.extract(source).decode("utf-8")})
    return result


def _cell_encoding(surface: str) -> dict:
    try:
        cells = parse_word(surface)
    except NabtError as error:
        return {"alphabet_id": ALPHABET_ID, "status": "NOT_ENCODED", "reason": error.code,
                "authority": "NO_LEXICAL_OR_SYNTACTIC_CONCLUSION"}
    return {"alphabet_id": ALPHABET_ID, "status": "ENCODED", "cells": list(cells),
            "number_hex": hex(encode_cells(cells)), "authority": "ENCODING_ONLY"}


def _ending_observed(observed, template, ending: int | None) -> bool:
    if ending is None:
        return False  # Built words have no inflection-ending observation here.
    # The installed pilot only reads the four short marks and tanwin variants.
    # Long/substitute endings require a later orthographic realization bridge.
    if ending > 3:
        return False
    wanted = ({"ُ", "ٌ"}, {"َ", "ً"}, {"ِ", "ٍ"}, {"ْ"})[ending]
    for index in range(len(template) - 1, -1, -1):
        if template[index][1] & wanted:
            return bool(observed[index][1] & wanted)
    return False


def _part(source, scope, run, entry, form, observed, template, spec, index, segmentation_id):
    lo, hi = spec["carrier_start"], spec["carrier_end"]
    if type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= len(observed):
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed segmentation has invalid carrier bounds", status="DEFER")
    before = run["surface"][:observed[lo][2]].encode("utf-8")
    middle = run["surface"][observed[lo][2]:observed[hi-1][3]]
    start = run["span"]["start"] + len(before)
    span = _span(source, start, start + len(middle.encode("utf-8")))
    kind, cls = spec["kind"], spec.get("declension_class")
    natural(kind, "kind", maximum=2)
    if cls is not None and words.class_kind(cls) != kind:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed class disagrees with the independent lexical kind", status="DEFER")
    ending = form.get("ending") if len(entry.get("segments", [])) <= 1 else spec.get("ending")
    observed_ending = ending if _ending_observed(observed[lo:hi], template[lo:hi], ending) else None
    pairs = words.case_candidates((cls,), observed_ending) if cls is not None else ()
    features = dict(entry.get("features", {})); features.update(spec.get("features", {}))
    key = {"source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
           "span": span_dict(span), "segmentation_id": segmentation_id, "part": index,
           "entry_id": entry["id"], "canonical_form": form["text"], "policy": EXPECTED_POLICY_SHA256}
    obligations = []
    if features.get("pronoun") or features.get("reference_required"):
        obligations.append("REFERENT_INTERPRETATION_EVIDENCE")
    if kind == 2:
        obligations.append("ATTACHMENT_AND_ACTIVATION_EVIDENCE")
    if features.get("requires_construction"):
        obligations.append("CONSTRUCTION_READING_EVIDENCE")
    if features.get("requires_attachment"):
        obligations.append("ATTACHED_HOST_EVIDENCE")
    if kind == 0 and cls == 0 and not any(marks & frozenset("ًٌٍ") for _, marks, _, _ in observed[lo:hi]):
        # This lexical pilot also stores plain short-vowel templates. They
        # witness a candidate noun and ending, not omission of tanwin in a
        # complete simple frame. Idafa, pause and other omission licences
        # need their own construction witness; absence is not rejection.
        obligations.append("CONSTRUCT_STATE_OR_TANWIN_EVIDENCE")
    return {"reading_id": _identity(key), "occurrence_id": run["occurrence_id"],
            "segmentation_id": segmentation_id, "span": span_dict(span), "surface": middle,
            "entry_id": entry["id"], "kind": kind, "kind_name": words.KINDS[kind],
            "capacities": words.capacities(kind), "declension_class": cls,
            "construction": spec.get("construction", entry["construction"]),
            "observed_ending": observed_ending, "case_candidates": [list(p) for p in pairs],
            "actual_role": None, "actual_case": None, "referent": None,
            "features": features, "rule_ids": entry["rule_ids"],
            "evidence_basis": entry.get("analysis_basis", "AUTHORED_APPLICATION_OF_PINNED_SOURCE"),
            "class_and_template_basis": entry.get("class_and_template_basis"),
            "lexical_attestations": entry.get("lexical_attestations", []),
            "obligations": obligations, "cell_encoding": _cell_encoding(middle),
            "authority": "PRECOMPOSITION_ANALYSIS_ONLY"}


def _read_run(source, scope, segment, policy):
    run = dict(segment)
    run["occurrence_id"] = _identity({"source_id": source.source_id, "source_sha256": source.sha256,
                                      "scope": scope, "span": run["span"]})
    run.update({"alternatives": [], "obligations": [], "candidate_kinds": [0, 1, 2]})
    if run["kind"] == "quotation":
        run.update({"status": "MENTION", "boundary_status": "QUOTED_BYTES_ONLY",
                    "obligations": ["MENTION_USE_EVIDENCE"]})
        return run
    try:
        observed = _clusters(run["surface"])
    except NabtError as error:
        run.update({"status": error.status, "boundary_status": "UNRESOLVED",
                    "obligations": [error.code]})
        return run
    for entry in policy["entries"]:
        for form in entry["forms"]:
            template = _clusters(form["text"])
            if not _matches(observed, template):
                continue
            required = entry.get("required_marks", []) + form.get("required_marks", [])
            if any(not set(r["marks"]) <= observed[r["carrier"]][1] for r in required):
                continue
            specs = entry.get("segments") or [{"carrier_start": 0, "carrier_end": len(observed),
                        "kind": entry["kind"], "declension_class": entry.get("declension_class"),
                        "construction": entry["construction"]}]
            intervals = [(s["carrier_start"], s["carrier_end"]) for s in specs]
            if intervals[0][0] != 0 or intervals[-1][1] != len(observed) or any(a[1] != b[0] for a, b in zip(intervals, intervals[1:])):
                raise NabtError("INSTALLED_CONTRACT_FAILED", "Segmentation does not cover its written run exactly", status="DEFER")
            sid = _identity({"occurrence_id": run["occurrence_id"], "entry": entry["id"],
                             "form": form["text"], "intervals": intervals, "policy": EXPECTED_POLICY_SHA256})
            parts = [_part(source, scope, run, entry, form, observed, template, spec, i, sid)
                     for i, spec in enumerate(specs)]
            if "".join(p["surface"] for p in parts) != run["surface"]:
                raise NabtError("INSTALLED_CONTRACT_FAILED", "Segmentation lost source bytes", status="DEFER")
            run["alternatives"].append({"segmentation_id": sid, "entry_id": entry["id"],
                    "canonical_template": form["text"], "observed_template_complete": all(a[1] == b[1] for a, b in zip(observed, template)),
                    "parts": parts, "coverage": "EXACT_SOURCE_PARTITION"})
            if len(run["alternatives"]) > MAX_ALTERNATIVES:
                raise resource_limit("Too many word reading alternatives", maximum=MAX_ALTERNATIVES)
    if run["alternatives"]:
        run["status"] = "READ" if len(run["alternatives"]) == 1 else "AMBIGUOUS"
        run["boundary_status"] = "LICENSED_ALTERNATIVES"
        run["candidate_kinds"] = sorted({a["parts"][0]["kind"] for a in run["alternatives"] if len(a["parts"]) == 1})
        run["component_kinds"] = [list(p["kind"] for p in a["parts"]) for a in run["alternatives"]]
        if not any(a["observed_template_complete"] for a in run["alternatives"]):
            # One matching *known* partially vocalized template is not a proof
            # that unknown homographs are absent from Arabic.
            run["status"] = "AMBIGUOUS"
            run["obligations"].append("VOCALIZATION_OR_LEXICAL_SELECTION_EVIDENCE")
        run["exhaustiveness"] = "INSTALLED_TEMPLATES_ONLY"
    else:
        run.update({"status": "DEFER", "boundary_status": "UNRESOLVED",
                    "obligations": ["LEXICAL_READING_EVIDENCE", "SEGMENTATION_EVIDENCE"]})
    return run


def _single_parts(run):
    return [alt["parts"][0] for alt in run["alternatives"] if len(alt["parts"]) == 1]


def _contexts(source, scope, segments, runs):
    """Only these complete frames activate: inna N N, min N, lam imperfect.

    No rule acts on the next token in an arbitrary sentence. A failure to fit
    the whole declared frame leaves an obligation, not a negative Arabic claim.
    """
    from .governors import lookup, check_assignment, role_mark_number, ROLE_MARK_DOMAIN
    grouped = [s for s in segments if s["kind"] == "punctuation" and s["surface"] in "()[]{}"]
    if grouped:
        # No parentheses/scope grammar has been installed. Dropping a group
        # delimiter could turn the inside of a question or quotation-like
        # construction into an apparently complete independent frame.
        return [{"context_id": _identity({"source": source.sha256, "source_id": source.source_id,
                    "scope": scope, "grouped_spans": [s["span"] for s in grouped]}),
                 "status": "DEFER", "bindings": [], "obligations": ["GROUPED_CONSTRUCTION_EVIDENCE"],
                 "grouped_spans": [s["span"] for s in grouped],
                 "authority": "SYNTAX_ONLY", "semantic_projection": "NONE"}]
    by_span = {(r["span"]["start"], r["span"]["end"]): r for r in runs}
    clauses, current = [], []
    for segment in segments:
        if segment["kind"] in {"written_run", "quotation"}:
            current.append(by_span[segment["span"]["start"], segment["span"]["end"]])
        elif segment["kind"] == "punctuation":
            if current:
                clauses.append(current); current = []
    if current:
        clauses.append(current)
    reports = []
    registry = {"inna": ("إنّ", 2, ((0, 0), (1, 1))),
                "min": ("من", 7, ((6, 2),)), "lam": ("لم", 5, ((2, 3),))}
    for clause in clauses:
        first = _single_parts(clause[0])
        operators = [p for p in first if p["features"].get("operator") in registry and p["kind"] == 2]
        if not operators:
            if len(clause) > 1:
                reports.append({"context_id": _identity({"source": source.sha256, "source_id": source.source_id,
                    "scope": scope, "start": clause[0]["span"]["start"], "end": clause[-1]["span"]["end"]}),
                    "status": "DEFER", "bindings": [], "obligations": ["CONSTRUCTION_READING_EVIDENCE"],
                    "authority": "SYNTAX_ONLY", "semantic_projection": "NONE"})
            continue
        for operator in operators:
            label, class_code, requirements = registry[operator["features"]["operator"]]
            rows = [row for row in lookup(label) if row.class_code == class_code and not row.implicit]
            if len(rows) != 1:
                raise NabtError("INSTALLED_CONTRACT_FAILED", "Word activation and installed governor table disagree", status="DEFER")
            context_id = _identity({"source": source.sha256, "source_id": source.source_id, "scope": scope,
                                    "span": [clause[0]["span"]["start"], clause[-1]["span"]["end"]],
                                    "operator_reading_id": operator["reading_id"], "profile": LANGUAGE_ID})
            report = {"context_id": context_id, "operator_reading_id": operator["reading_id"],
                      "governor_row_id": rows[0].row_id, "class_code": class_code,
                      "status": "DEFER", "bindings": [], "obligations": [],
                      "authority": "SYNTAX_ONLY", "semantic_projection": "NONE"}
            if len(first) != 1:
                report["obligations"].append("OPERATOR_READING_EVIDENCE")
            report["obligations"].extend(clause[0]["obligations"])
            # Visible ma/attached inna-ma is never stripped to activate inna.
            if len(clause) != len(requirements) + 1:
                report["obligations"].append("COMPLETE_CONSTITUENT_BOUNDARIES")
                reports.append(report); continue
            choices = [_single_parts(r) for r in clause[1:]]
            if any(not c for c in choices):
                report["obligations"].append("LEXICAL_READING_EVIDENCE")
                reports.append(report); continue
            combinations = 1
            for choice in choices:
                combinations *= len(choice)
            if combinations > MAX_COMPOSITIONS:
                raise resource_limit("Contextual reading product exceeds its budget", maximum=MAX_COMPOSITIONS)
            missing, conflicts = [], []
            for selected in product(*choices):
                binding, failed = [], False
                for part, (role, required) in zip(selected, requirements):
                    expected_kind = 1 if role == 2 else 0
                    if part["kind"] != expected_kind:
                        conflicts.append("LEXICAL_KIND_ROLE_CONFLICT"); failed = True; break
                    if role == 2 and part["features"].get("tense") != "imperfect":
                        conflicts.append("IMPERFECT_READING_REQUIRED"); failed = True; break
                    if "CONSTRUCT_STATE_OR_TANWIN_EVIDENCE" in part["obligations"]:
                        missing.append("CONSTRUCT_STATE_OR_TANWIN_EVIDENCE"); failed = True; break
                    if part["declension_class"] is None:
                        missing.append("DECLENSION_OR_CASE_LOCATION_EVIDENCE"); failed = True; break
                    if part["observed_ending"] is None:
                        missing.append("SURFACE_REALIZATION_EVIDENCE"); failed = True; break
                    pairs = tuple(tuple(p) for p in part["case_candidates"])
                    surviving = words.refine_cases(pairs, role=role, required_case=required)
                    if not surviving:
                        conflicts.append("CASE_ROLE_CONFLICT"); failed = True; break
                    binding.append({"analysis": part, "context_id": context_id, "role": role,
                                    "case": required, "class_case_pairs": [list(p) for p in surviving],
                                    "role_case_number": {"domain": ROLE_MARK_DOMAIN, "value": role_mark_number(role, required)},
                                    "referent": None})
                if not failed:
                    algebra = check_assignment(class_code, {b["role"]: b["case"] for b in binding})
                    if not algebra["complete"]:
                        raise NabtError("INSTALLED_CONTRACT_FAILED", "Word bridge produced an incomplete governor assignment", status="DEFER")
                    report["bindings"].append({"words": binding, "case_check": algebra})
            report["unresolved_alternative_obligations"] = sorted(set(missing))
            report["conflicts"] = sorted(set(conflicts))
            if report["bindings"] and not report["obligations"] and not missing:
                report["status"] = "CHECKED"  # Alternatives remain explicit; no arbitrary first choice.
            elif not report["bindings"] and conflicts and not missing and not report["obligations"]:
                report["status"] = "CONFLICT"
            report["obligations"] = sorted(set(report["obligations"] + missing))
            report["obligations"] = sorted(set(report["obligations"] +
                                              [o for run in clause[1:] for o in run["obligations"]]))
            if report["obligations"] and report["status"] == "CHECKED":
                report["status"] = "DEFER"
            reports.append(report)
    return reports


def read_words(raw: bytes | str, *, source_id: str = "input", scope: str = "default") -> dict:
    source = _source(raw, source_id, scope)
    policy = replay_policy()
    segments = _scan(source)
    runs = [_read_run(source, scope, s, policy) for s in segments if s["kind"] in {"written_run", "quotation"}]
    contexts = _contexts(source, scope, segments, runs)
    if "".join(s["surface"] for s in segments).encode("utf-8") != source.raw_bytes:
        raise NabtError("INTERNAL_CONTRACT_FAILED", "The written partition did not restore its source")
    status = "READ"
    if any(r["status"] == "REJECT" for r in runs):
        status = "REJECT"
    elif not runs or any(r["status"] in {"DEFER", "MENTION", "AMBIGUOUS"} for r in runs) or any(c["status"] != "CHECKED" for c in contexts):
        status = "DEFER"
    result = {"schema_version": 1, "language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
              "status": status, "source_id": source.source_id, "source_sha256": source.sha256,
              "scope": scope, "raw_text": source.raw_bytes.decode("utf-8"),
              "policy_id": policy["policy_id"], "policy_sha256": EXPECTED_POLICY_SHA256,
              "segments": segments, "occurrences": runs, "contexts": contexts,
              "source_restored": True, "facts": [], "semantic_projection": "NONE",
              "world_truth": "NOT_ESTABLISHED",
              "interpretation_scope": "FINITE_ATTESTED_LEXICAL_PILOT_AND_THREE_COMPLETE_FRAMES"}
    _wire(result)  # Bound the report before presenting it or encoding it.
    return result


def word_reading_number(report: dict) -> int:
    """Replay before encoding; numeric identity alone does not grant a reading."""
    checked = verify_word_reading(report)
    if not checked["valid"]:
        raise NabtError(checked["code"], "A word report does not replay", status=checked["status"])
    return int.from_bytes(b"\x01" + _wire(report), "big")


def read_word_at(raw: bytes | str, start: int, end: int, *, source_id: str = "input", scope: str = "default") -> dict:
    """Select only a replayed written run or a licensed part of its segmentation.

    A valid UTF-8 cut is necessary, not sufficient: cutting a mark from its
    carrier or inventing a suffix boundary does not create a word witness.
    """
    source = _source(raw, source_id, scope)
    requested = _span(source, start, end)
    report = read_words(raw, source_id=source_id, scope=scope)
    found, parents = [], []
    for occurrence in report["occurrences"]:
        selected_here = []
        for alternative in occurrence["alternatives"]:
            selected_here.extend(part for part in alternative["parts"]
                                 if part["span"]["start"] == start and part["span"]["end"] == end)
        if selected_here:
            found.extend(selected_here)
            parents.append(occurrence)
    if not found:
        raise NabtError("UNLICENSED_WORD_BOUNDARY", "This cut has no source-replayed word analysis", status="DEFER")
    unresolved = any(parent["status"] != "READ" for parent in parents)
    obligations = sorted(set([o for parent in parents for o in parent["obligations"]]
                             + [o for part in found for o in part["obligations"]]))
    return {"span": span_dict(requested), "source_id": source.source_id, "source_sha256": source.sha256,
            "scope": scope, "analyses": found, "parent_occurrences": parents,
            "status": "DEFER" if unresolved else "READ", "obligations": obligations,
            "policy_sha256": EXPECTED_POLICY_SHA256,
            "authority": "SELECTED_SOURCE_ANALYSES_ONLY"}


def verify_word_reading(report: dict, *, source: bytes | str | None = None,
                        source_id: str | None = None, scope: str | None = None) -> dict:
    """Compare the whole report with independent reconstruction from its source.

    Optional expected source/id/scope bind the report to the caller's actual
    query context. A self-consistent different source is not an answer to it.
    Policy/resource failures keep their DEFER status; malformed reports fail.
    """
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        raw = report["raw_text"] if source is None else source
        sid = report["source_id"] if source_id is None else source_id
        scp = report["scope"] if scope is None else scope
        fresh = read_words(raw, source_id=sid, scope=scp)
        if _wire(report) != _wire(fresh):
            raise ValueError("source/reading mismatch")
        return {"valid": True, "status": "VERIFIED", "authority": "WORD_READING_REPLAY_ONLY",
                "source_sha256": fresh["source_sha256"]}
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_WORD_REPORT"}


def decode_word_reading(number: int) -> dict:
    natural(number, "word_reading_number")
    if number.bit_length() > 8 * (MAX_REPORT_BYTES + 1):
        raise resource_limit("Word-reading number exceeds its byte budget")
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    if not raw or raw[0] != 1:
        raise NabtError("INVALID_WORD_NUMBER", "Missing word-reading sentinel")
    try:
        value = json.loads(raw[1:].decode("utf-8"))
        if _wire(value) != raw[1:]:
            raise ValueError("noncanonical word number")
        check = verify_word_reading(value)
        if not check["valid"]:
            raise NabtError(check["code"], "Word number did not replay", status=check["status"])
        return value
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            raise
        raise NabtError("INVALID_WORD_NUMBER", "Word number is malformed or does not replay") from error
