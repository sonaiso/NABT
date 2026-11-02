"""Delegate one supplied derivation to the existing weak law and exact source.

This adapter neither discovers a lexical root nor licenses an Arabic reading.
The template owner fills the supplied pattern; the classical owner alone
decides and performs the conditional weak-letter operation.  The one new
presentation convention omits the sukun of the medial alif produced by
``to_alif``.  Its edit and inverse are recorded independently of source spans.

Every report retains the complete original request and both unchanged owner
results.  Independent source/request replay, rather than an embedded authority
flag or digest, is the verification boundary.  No existing source inventory,
template, weak-law rule, or recursive grammar is extended by this module.
"""
from __future__ import annotations

from copy import deepcopy

from nabt import alphabet, classical_laws, derivation
from nabt.errors import NabtError, natural, resource_limit
from nabt.text_ir import span_dict
from nabt.word_reader import _scan, _source, _span
from tools.explainable_pilot import PilotError
from tools.mantuq_inference.source_fold import bounded_wire


REQUEST_SCHEMA = "nabt.derivation-surface-request.v1"
REPORT_SCHEMA = "nabt.derivation-surface-report.v1"
REALIZATION_PROFILE = "medial-alif-unmarked.v1"
AUTHORITY = "SOURCE_BOUND_CONDITIONAL_SURFACE_APPLICATION"
REPLAY_AUTHORITY = "DERIVATION_SURFACE_REPLAY_ONLY"
RULE_ID = "WEAK-MOVE-TO-ALIF"

MAX_SOURCE_BYTES = 8192
MAX_REQUEST_BYTES = 4096
MAX_REPORT_BYTES = 262144
MAX_LABEL_BYTES = 96
MAX_JSON_DEPTH = 24
MAX_JSON_NODES = 8192

_REQUEST_FIELDS = frozenset((
    "schema", "profile", "span", "root", "pattern_id", "ending", "hypotheses",
))
_PATTERNS = frozenset(("past.I.a", "past.I.i", "past.I.u"))
_CONTEXTS = frozenset(("ordinary", "afal_quality"))
_ORIGINS = frozenset(("original", "transferred"))
# Conversion of the existing A116 state order, not another phonological law.
_WEAK_VOWELS_BY_A116_STATE = ("a", "u", "i", "0")
_UNRESOLVED = (
    "SUPPLIED_ROOT_AND_PATTERN_NOT_INDEPENDENT_LEXICAL_WITNESSES",
    "SUPPLIED_LEXICAL_AND_SEMANTIC_CLASS_NOT_ESTABLISHED",
    "SUPPLIED_VOWEL_ORIGIN_NOT_ESTABLISHED",
    "REALIZATION_PROFILE_IS_A_DECLARED_PRESENTATION_CONVENTION",
    "RecursiveSourceBridge.CertifiedBridge_NOT_DISCHARGED",
)


def _invalid(message):
    raise NabtError("INVALID_DERIVATION_SURFACE_INPUT", message)


def _json_structure_budget(value):
    """Bound visits/depth before the shared cumulative JSON byte guard."""
    visited = 0

    def visit(item, depth):
        nonlocal visited
        visited += 1
        if depth > MAX_JSON_DEPTH or visited > MAX_JSON_NODES:
            raise resource_limit("Derivation surface JSON exceeds its structural budget")
        kind = type(item)
        if kind is dict:
            for key, child in item.items():
                if type(key) is not str:
                    _invalid("JSON object keys must be strings")
                visit(child, depth + 1)
        elif kind is list:
            for child in item:
                visit(child, depth + 1)
        elif kind not in (str, int, bool, type(None)):
            _invalid("Use strict integer-valued JSON, without object or numeric coercion")

    visit(value, 0)


def _wire(value, maximum):
    _json_structure_budget(value)
    try:
        # Existing occurrence-by-occurrence byte accounting rejects expansion
        # before allocating a complete serialized document, including aliases.
        return bounded_wire(value, maximum=maximum)
    except PilotError as error:
        if error.code == "RESOURCE_LIMIT":
            raise resource_limit("Derivation surface JSON exceeds its byte or integer budget") from error
        raise NabtError("INVALID_DERIVATION_SURFACE_INPUT", "Use bounded strict UTF-8 JSON") from error


def validate_derivation_surface_request(request):
    """Validate only request shape/size; perform no source or owner operation.

    The recursive consumer uses this on its entire bounded request list before
    any source replay.  Well-typed values outside the profile are deliberately
    retained; they are not malformed input and may not silently become defaults.
    """
    _wire(request, MAX_REQUEST_BYTES)
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        _invalid("Expected exactly the versioned derivation surface request fields")
    if request["schema"] != REQUEST_SCHEMA or type(request["schema"]) is not str:
        _invalid("Unknown derivation surface request schema")
    for name in ("profile", "root", "pattern_id", "ending"):
        if type(request[name]) is not str:
            _invalid(name + " must be an exact string")
    selected = request["span"]
    if type(selected) is not dict or set(selected) != {"start", "end"}:
        _invalid("The occurrence span must have exactly start and end")
    natural(selected["start"], "span.start")
    natural(selected["end"], "span.end")
    if selected["start"] >= selected["end"]:
        _invalid("The occurrence span must be nonempty and ordered")
    hypotheses = request["hypotheses"]
    if type(hypotheses) is not dict or set(hypotheses) != {"context", "origin"}:
        _invalid("Hypotheses must have exactly context and origin")
    if any(value is not None and type(value) is not str for value in hypotheses.values()):
        _invalid("Each supplied hypothesis is an exact string or null")


def _label(value, name):
    if type(value) is not str or not value:
        _invalid(name + " must be a nonempty string")
    if len(value) > MAX_LABEL_BYTES:
        raise resource_limit("Derivation surface identity exceeds its byte budget", field=name)
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeError as error:
        raise NabtError("INVALID_DERIVATION_SURFACE_INPUT", "Identity must be valid UTF-8") from error
    if len(raw) > MAX_LABEL_BYTES:
        raise resource_limit("Derivation surface identity exceeds its byte budget", field=name)


def _source_occurrence(text, request, source_id, scope):
    _label(source_id, "source_id")
    _label(scope, "scope")
    if type(text) not in (str, bytes):
        _invalid("Source must be exact UTF-8 text or bytes")
    # In particular, do not allocate an encoded copy of a giant Python string.
    if len(text) > MAX_SOURCE_BYTES:
        raise resource_limit("Derivation surface source exceeds its byte budget")
    source = _source(text, source_id, scope)
    selected = request["span"]
    selected_span = _span(source, selected["start"], selected["end"])
    matching = next((run for run in _scan(source)
                     if run["kind"] == "written_run"
                     and run["span"]["start"] == selected_span.start
                     and run["span"]["end"] == selected_span.end), None)
    if matching is None:
        _invalid("The span must select one complete original written_run")
    return source, {"span": span_dict(selected_span), "surface": matching["surface"]}


def validate_derivation_surface_occurrence(text, request, *, source_id="input", scope="default"):
    """Preflight a source occurrence without template, operator or grammar work."""
    validate_derivation_surface_request(request)
    _source_occurrence(text, request, source_id, scope)


def _inside_profile(request):
    root = request["root"]
    hypotheses = request["hypotheses"]
    return (request["profile"] == REALIZATION_PROFILE
            and request["pattern_id"] in _PATTERNS
            and request["ending"] == "َ"
            and len(root) == 3
            and all(letter in derivation.RADICALS for letter in root)
            and root[1] in "وي"
            and root[0] not in "ويء" and root[2] not in "ويء"
            and (hypotheses["context"] is None or hypotheses["context"] in _CONTEXTS)
            and (hypotheses["origin"] is None or hypotheses["origin"] in _ORIGINS))


def _input_cells(generated):
    ids = alphabet.parse_word(generated["surface"])
    if len(ids) != 3:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Selected template no longer has three complete cells",
                        status="DEFER")
    pairs = [alphabet.cell_parts(cell) for cell in ids]
    return {"alphabet_id": alphabet.ALPHABET_ID, "ids": list(ids),
            "morphophonemic": [[carrier, _WEAK_VOWELS_BY_A116_STATE[state]]
                               for carrier, state in pairs]}


def _local_spans(pieces):
    result, scalar_start, byte_start = [], 0, 0
    for piece in pieces:
        scalar_end = scalar_start + len(piece)
        byte_end = byte_start + len(piece.encode("utf-8"))
        result.append({"scalar_start": scalar_start, "scalar_end": scalar_end,
                       "byte_start": byte_start, "byte_end": byte_end})
        scalar_start, byte_start = scalar_end, byte_end
    return result


def _realize_alternative(alternative, generated, input_cells, source, occurrence):
    """Realize only the existing to_alif result; never decide or redo its rule."""
    cells = alternative["cells"]
    original = input_cells["morphophonemic"]
    if (alternative["action"] != "to_alif" or type(cells) is not list or len(cells) != 3
            or cells[1] != ["ا", "0"] or original[1][0] not in "وي"
            or cells[0] != original[0] or cells[2] != original[2]):
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Weak result is outside this realization contract",
                        status="DEFER")
    states = {vowel: state for state, vowel in enumerate(_WEAK_VOWELS_BY_A116_STATE)}
    output_ids = [alphabet.cell_id(carrier, states[vowel]) for carrier, vowel in cells]
    canonical_parts = [alphabet.render_word([cell]) for cell in output_ids]
    generated_parts = [alphabet.render_word([cell]) for cell in input_cells["ids"]]
    canonical = alphabet.render_word(output_ids)
    if "".join(generated_parts) != generated["surface"] or canonical_parts[1] != "اْ":
        raise NabtError("INSTALLED_CONTRACT_FAILED", "A116 rendering differs from the declared presentation",
                        status="DEFER")

    # This is a declared presentation edit, not a second weak-letter operation.
    # It may touch only the marker of the medial alif produced above.
    realized_parts = list(canonical_parts)
    realized_parts[1] = canonical_parts[1][0]
    realized = "".join(realized_parts)
    generated_spans = _local_spans(generated_parts)
    canonical_spans = _local_spans(canonical_parts)
    realized_spans = _local_spans(realized_parts)
    scalar_start = canonical_spans[1]["scalar_start"] + 1
    byte_start = canonical_spans[1]["byte_start"] + len("ا".encode("utf-8"))
    omitted = {"mark": "ْ", "cell_index": 1,
               "coordinate_domain": "canonical_marked_surface",
               "scalar_start": scalar_start, "scalar_end": scalar_start + 1,
               "byte_start": byte_start, "byte_end": byte_start + len("ْ".encode("utf-8"))}
    if (canonical[scalar_start:scalar_start + 1] != omitted["mark"]
            or canonical[:scalar_start] + canonical[scalar_start + 1:] != realized
            or realized[:scalar_start] + omitted["mark"] + realized[scalar_start:] != canonical):
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Presentation edit does not exactly restore its input",
                        status="DEFER")

    matches = realized == occurrence["surface"]
    alignment = []
    for index, (before, marked, displayed) in enumerate(zip(
            generated_spans, canonical_spans, realized_spans, strict=True)):
        bound = None
        if matches:
            bound = span_dict(_span(source,
                occurrence["span"]["start"] + displayed["byte_start"],
                occurrence["span"]["start"] + displayed["byte_end"]))
        alignment.append({"cell_index": index, "root_index": index,
                          "generated": before, "canonical": marked,
                          "realized": displayed, "source_span": bound})
    return {"action": alternative["action"], "canonical_marked_surface": canonical,
            "realized_surface": realized, "omitted_mark": omitted,
            "cell_alignment": alignment, "exact_source_match": matches}


def evaluate_derivation_surface(text, request, *, source_id="input", scope="default"):
    """Compute one conditional application bound to an independent occurrence."""
    validate_derivation_surface_request(request)
    source, occurrence = _source_occurrence(text, request, source_id, scope)
    hypotheses = request["hypotheses"]
    missing = [name for name in ("context", "origin") if hypotheses[name] is None]
    report = {
        "schema": REPORT_SCHEMA, "authority": AUTHORITY,
        "source": {"source_id": source.source_id, "source_sha256": source.sha256,
                   "scope": scope, "raw_text": source.raw_bytes.decode("utf-8"),
                   "byte_length": len(source.raw_bytes)},
        "original_request": deepcopy(request), "occurrence": occurrence,
        "generation": None, "input_cells": None, "classical_receipt": None,
        "surface_alternatives": [], "status": "DEFER", "reason": "OUTSIDE_PROFILE",
        "missing_hypotheses": missing, "unresolved": list(_UNRESOLVED),
        "attested_root": False, "application_established": False,
        "grammar_certified": False, "grants_language_license": False,
        "world_truth": "NOT_ESTABLISHED",
    }
    if _inside_profile(request):
        generated = derivation.generate_derivation(request["root"], request["pattern_id"],
                                                   ending=request["ending"])
        inputs = _input_cells(generated)
        report["generation"], report["input_cells"] = generated, inputs
        if missing:
            report["reason"] = "MISSING_PREMISES"
        else:
            frame = {"cells": deepcopy(inputs["morphophonemic"]), "index": 1,
                     "position": "ayn", "lexeme": "", "context": hypotheses["context"],
                     "origin": hypotheses["origin"]}
            receipt = classical_laws.evaluate(RULE_ID, frame)
            report["classical_receipt"] = receipt
            alternatives = receipt["result"]["alternatives"]
            # Preserve every returned alternative.  Their conditional authority
            # and source spans remain in the unchanged facade receipt above.
            report["surface_alternatives"] = [
                _realize_alternative(row, generated, inputs, source, occurrence)
                for row in alternatives]
            report["reason"] = None
            report["status"] = ("OUTSIDE_RULE_DOMAIN" if not alternatives else
                "CONDITIONAL_MATCH" if any(row["exact_source_match"]
                                            for row in report["surface_alternatives"])
                else "SURFACE_MISMATCH")
    _wire(report, MAX_REPORT_BYTES)
    return report


def verify_derivation_surface(report, *, text, request, source_id="input", scope="default"):
    """Recompute the entire result using mandatory independent source/request."""
    try:
        observed = _wire(report, MAX_REPORT_BYTES)
        expected = evaluate_derivation_surface(text, request, source_id=source_id, scope=scope)
        if observed != _wire(expected, MAX_REPORT_BYTES):
            return {"valid": False, "status": "REJECT", "code": "DERIVATION_SURFACE_REPLAY_MISMATCH"}
        return {"valid": True, "status": "VERIFIED", "authority": REPLAY_AUTHORITY}
    except NabtError as error:
        if error.status == "DEFER":
            return {"valid": False, **error.as_dict()}
        return {"valid": False, "status": "REJECT", "code": "DERIVATION_SURFACE_REPLAY_MISMATCH"}
    except (TypeError, ValueError, KeyError, UnicodeError, RecursionError):
        return {"valid": False, "status": "REJECT", "code": "DERIVATION_SURFACE_REPLAY_MISMATCH"}
