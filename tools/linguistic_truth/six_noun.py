"""Native, source-bound acquisition for a declared six-noun construction family.

Raw text is the only linguistic input. The installed Lean executable acquires
the governor, word form, and complement; Python replays its full transport
contract and independently rechecks the pinned rule passages. A certificate
for this authored grammar is not lexical intent, source authenticity, historical
transmission, an external event, or completeness of Arabic.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from nabt import foundation
from nabt.errors import NabtError

_ROOT = Path(__file__).resolve().parents[2]
_EXECUTABLE = _ROOT / "formal/.lake/build/bin/sixNounAcquisition"
_REVIEW = _ROOT / "evidence/six_noun_acquisition_v1/source_review.json"
_REVIEW_SHA = "315e6c067d9bacded9661bef043594be90437b73f1f695842d1d087d0dac0b8e"
_LAW = "nabt.six-noun-acquisition.v1"
_SCHEMA = "nabt.six-noun-acquisition-receipt.v1"
_MAX_INPUT_BYTES = 4096
_MAX_RESPONSE_BYTES = 1048576
_THEOREMS = tuple("Nabt.SixNounAcquisition." + name for name in (
    "acquired_exact", "acquired_source_restored", "acquired_exact_word_bytes",
    "acquired_byte_bounds", "canonical_number_restores_cells", "supported_case_sign",
    "dhu_has_no_supported_reading", "grammar_certified",
    "grammar_certificate_requires_support", "certificate_preserves_source",
    "certificate_all_nodes_licensed", "certificate_case_sign",
    "certificate_realization_matches_projection", "certificate_numeric_realization",
    "trace_node_raw_exact", "trace_node_realization", "trace_node_number_restores",
    "trace_children_match_derivation",
    "certificate_trace_nodes_licensed", "certificate_trace_source_exact"))

# A transport replay of the installed finite Lean profile. It cannot authorize
# a claim without an actual exact native receipt; it is not an Arabic parser.
_GOVERNORS = (
    ("arrival", "جَاءَ ", "جَاْءَ ", "waw"),
    ("seeing", "رَأَيْتُ ", "رَءَيْتُ ", "alif"),
    ("passing", "مَرَرْتُ بِ", "مَرَرْتُ بِ", "ya"),
)
_WORDS = {
    "ab": (("أَبُو", "ءَبُوْ"), ("أَبَا", "ءَبَاْ"), ("أَبِي", "ءَبِيْ")),
    "akh": (("أَخُو", "ءَخُوْ"), ("أَخَا", "ءَخَاْ"), ("أَخِي", "ءَخِيْ")),
    "ham": (("حَمُو", "حَمُوْ"), ("حَمَا", "حَمَاْ"), ("حَمِي", "حَمِيْ")),
    "fu": (("فُو", "فُوْ"), ("فَا", "فَاْ"), ("فِي", "فِيْ")),
    "dhu": (("ذُو", "ذُوْ"), ("ذَا", "ذَاْ"), ("ذِي", "ذِيْ")),
    "han": (("هَنُو", "هَنُوْ"), ("هَنَا", "هَنَاْ"), ("هَنِي", "هَنِيْ")),
}
_ENDINGS = (("waw", "raf"), ("alif", "nasb"), ("ya", "jarr"))
_COMPLEMENTS = (("zayd", "زَيْدٍ", "زَيْدِنْ"), ("amr", "عَمْرٍو", "عَمْرِنْ"))
_UNRESOLVED = ["SOURCE_AUTHENTICITY_NOT_PROVED", "RULE_INTERPRETATION_NOT_PROVED",
    "LEXICAL_PROFILE_NOT_GENERAL_CLASSIFICATION", "READING_EXHAUSTIVENESS_OUTSIDE_PROFILE_NOT_PROVED",
    "INTENDED_REFERENCE_NOT_ESTABLISHED", "EXTERNAL_TRUTH_NOT_ESTABLISHED"]


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _parse_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("DUPLICATE_SIX_NOUN_RECEIPT_FIELD")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_SIX_NOUN_RECEIPT")))


def _review():
    raw = _REVIEW.read_bytes()
    if sha256(raw).hexdigest() != _REVIEW_SHA:
        raise ValueError("SIX_NOUN_REVIEW_CHANGED")
    review = _parse_json(raw)
    if review["law_id"] != _LAW:
        raise ValueError("SIX_NOUN_REVIEW_LAW_MISMATCH")
    sources = {}
    for source in review["sources"]:
        if source["id"] in sources:
            raise ValueError("SIX_NOUN_DUPLICATE_SOURCE_ID")
        path = (_ROOT / source["path"]).resolve()
        if not path.is_relative_to(_ROOT.resolve()):
            raise ValueError("SIX_NOUN_SOURCE_OUTSIDE_ROOT")
        data = path.read_bytes()
        if (type(source["bytes"]) is not int or len(data) != source["bytes"]
                or sha256(data).hexdigest() != source["sha256"]):
            raise ValueError("SIX_NOUN_SOURCE_CHANGED")
        sources[source["id"]] = data
    for passage in review["passages"]:
        start, end = passage["start_byte"], passage["end_byte"]
        data = sources[passage["source_id"]]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(data):
            raise ValueError("SIX_NOUN_PASSAGE_BOUNDS")
        part = data[start:end]
        if part != passage["quote"].encode("utf-8") or sha256(part).hexdigest() != passage["sha256"]:
            raise ValueError("SIX_NOUN_PASSAGE_CHANGED")
    return review


def _projection(text):
    value = foundation.inspect_source(text)
    return {"status": "INCOMPLETE" if value["status"] == "PARTIAL" else value["status"],
            **{key: value[key] for key in ("alphabet_id", "number_domain", "cells", "number")}}


def _expected_node_trace(request, receipt, canonical_parts):
    """Replay the native five-node derivation, never accept caller-supplied nodes."""
    if not receipt["grammar_certified"]:
        return []
    reading, source = receipt["reading"], request["source"]
    raw = source["text"].encode("utf-8")
    start, end = reading["start_byte"], reading["end_byte"]
    prefix, word, complement = canonical_parts
    case_code = {"waw": 1, "alif": 0, "ya": 2}[reading["ending"]]
    expected_case_code = {"raf": 1, "nasb": 0, "jarr": 2}[reading["grammatical_case"]]
    governor_passage = {"arrival": "qatr_subject", "seeing": "qatr_object",
                        "passing": "qatr_genitive"}[reading["governor"]]
    noun_passages = ["qatr_six_inventory_case", "alfiyya_idafa_non_speaker"] + (
        ["alfiyya_variants"] if reading["lexeme"] in {"ab", "akh", "ham"} else
        ["alfiyya_dhu_fum"] if reading["lexeme"] in {"fu", "dhu"} else
        ["alfiyya_han", "sibawayhi_han_report"])
    specs = (
        ("prefix", "PREFIX_EXACT_V1", [], 0, start, prefix,
         "verbPhrase", 0, 0, [governor_passage]),
        ("noun", "NOUN_FULL_FORM_V1", [], start, end, word,
         "noun", case_code, 1, noun_passages),
        ("complement", "COMPLEMENT_EXACT_V1", [], end + 1, len(raw), complement,
         "noun", 2, 2, ["qatr_genitive"]),
        ("idafa", "IDAFA_EXACT_V1", ["noun", "complement"], start, len(raw), word + " " + complement,
         "nounPhrase", case_code, 1, ["qatr_genitive", "alfiyya_idafa_non_speaker"]),
        ("sentence", "SIX_NOUN_COMMON_LETTER_V1", ["prefix", "idafa"], 0, len(raw),
         prefix + word + " " + complement, "verbalClause", expected_case_code, 0,
         [governor_passage] + noun_passages),
    )
    nodes = {}
    for node_id, rule_id, children, first, last, canonical, category, state, position, passages in specs:
        projection = _projection(canonical)
        prerequisites = [
            {"name": "exact_source_interval", "state": "affirmed", "origin": "native_source_slice"},
            {"name": "declared_finite_profile", "state": "affirmed",
             "origin": "authored_profile_not_general_classification"},
        ]
        if not children:
            prerequisites.append({"name": "declared_lexical_slot_allowed", "state": "affirmed",
                                  "origin": "native_grammar"})
        else:
            prerequisites.append({"name": "child_interfaces_match", "state": "affirmed",
                                  "origin": "native_grammar"})
            if node_id == "idafa":
                prerequisites.append({"name": "ordered_noun_complement_children", "state": "affirmed",
                                      "origin": "native_grammar"})
            else:
                prerequisites.extend(deepcopy(reading["prerequisites"]))
        nodes[node_id] = {"node_id": node_id, "law_id": _LAW,
            "scope": "INSTALLED_EXACT_SPELLING_COMMON_LETTER_PROFILE",
            "source": deepcopy(source), "context": request["context"],
            "orthographic_profile": "nabt.six-noun-exact-spelling.v1",
            "alphabet_id": projection["alphabet_id"], "number_domain": projection["number_domain"],
            "rule_id": rule_id, "children": children, "rule_source_review_sha256": _REVIEW_SHA,
            "passage_ids": list(passages), "start_byte": first, "end_byte": last,
            "raw": raw[first:last].decode("utf-8"),
            "input_cells": [deepcopy(nodes[child]["output_cells"]) for child in children],
            "output_cells": projection["cells"], "output_number": projection["number"],
            "input_faces": [deepcopy(nodes[child]["output_face"]) for child in children],
            "output_face": {"category": category, "state": state, "position": position, "residual": []},
            "prerequisites": prerequisites, "alternatives": list(reading["alternatives"]),
            "unresolved": list(receipt["unresolved"]), "licensed": True}
    return list(nodes.values())


def _expected(request):
    """Replay every ABI field, preserving the difference between raw and canonical.

    This independent transport comparison is not used to make a proof claim by
    itself. The native response must equal it, including all negative authority
    declarations, residuals, exact spans, and the request's opaque context.
    """
    source, context = request["source"], request["context"]
    original = _projection(source["text"])
    result = {"schema": _LAW, "law_id": _LAW, "source": deepcopy(source), "context": context,
        "source_projection": original, "status": "INVALID_SOURCE" if original["status"] == "INVALID"
            else "OUTSIDE_EXECUTED_FRAGMENT", "reading": None, "grammar_certified": False, "node_trace": [],
        "foundation_complete": original["status"] == "COMPLETE", "orthographic_bridge": None,
        "unresolved": ["INVALID_SOURCE_MARKS_OR_EMPTY" if original["status"] == "INVALID"
                       else "OUTSIDE_EXACT_TEMPLATE_OR_VARIANT_NOT_ACQUIRED"],
        "source_restored": True, "intended_sense_established": False,
        "external_truth_established": False, "strict_language_accepted": False,
        "whole_arabic_complete": False}
    if original["status"] == "INVALID":
        return result
    for governor, prefix, canonical_prefix, expected_ending in _GOVERNORS:
        for lexeme, words in _WORDS.items():
            for (ending, observed_case), (word, canonical_word) in zip(_ENDINGS, words):
                for complement, complement_text, canonical_complement in _COMPLEMENTS:
                    raw = prefix + word + " " + complement_text
                    if raw != source["text"]:
                        continue
                    canonical = canonical_prefix + canonical_word + " " + canonical_complement
                    projection = _projection(canonical)
                    complete = projection["status"] == "COMPLETE"
                    same_case = ending == expected_ending
                    supported = lexeme != "dhu" and same_case and complete
                    alternatives = (["QASR_AND_NAQS_NOT_ENUMERATED_BY_THIS_PROFILE"]
                        if lexeme in {"ab", "akh", "ham"} else
                        ["NAQS_PREFERRED_FULL_FORM_READING_ONLY"] if lexeme == "han" else
                        ["COMPANIONSHIP_OR_RELATIVE_READING_UNRESOLVED"] if lexeme == "dhu" else [])
                    prerequisite_rows = [
                        ("exact_full_form_profile", "affirmed", "exact_source_spelling"),
                        ("singular_non_diminutive", "affirmed", "declared_finite_lexical_profile"),
                        ("idafa_to_non_speaker_ya", "affirmed", "exact_complement_template"),
                        ("fu_meem_removed", "affirmed" if lexeme == "fu" else "not_applicable",
                         "exact_source_spelling"),
                        ("dhu_companionship", "unknown" if lexeme == "dhu" else "not_applicable",
                         "not_acquired_from_surface"),
                        ("required_case_matches_observed_ending", "affirmed" if same_case else "denied",
                         "declared_governor_template"),
                    ]
                    start = len(prefix.encode("utf-8"))
                    result.update(status="CHECKED_SIX_NOUN" if supported else "DEFER",
                        grammar_certified=supported,
                        reading={"governor": governor, "lexeme": lexeme, "ending": ending,
                            "complement": complement, "prefix": prefix, "word": word,
                            "complement_text": complement_text, "start_byte": start,
                            "end_byte": start + len(word.encode("utf-8")),
                            "grammatical_case": dict(_ENDINGS)[expected_ending],
                            "observed_case": observed_case, "convention": "common_letter_substitution",
                            "prerequisites": [{"name": name, "state": state, "origin": origin}
                                              for name, state, origin in prerequisite_rows],
                            "alternatives": alternatives},
                        orthographic_bridge={"profile": "nabt.six-noun-exact-spelling.v1",
                            "raw": raw, "canonical": canonical, "cells": projection["cells"],
                            "number": projection["number"], "raw_reconstruction_checked": True,
                            "canonical_projection_complete": complete},
                        unresolved=list(_UNRESOLVED)
                            + (["DHU_COMPANIONSHIP_NOT_ACQUIRED"] if lexeme == "dhu" else [])
                            + (["COMMON_LETTER_CASE_MISMATCH"] if not same_case else [])
                            + (["DECLARED_ORTHOGRAPHIC_PROFILE_INCOMPLETE"] if not complete else []))
                    result["node_trace"] = _expected_node_trace(request, result,
                        (canonical_prefix, canonical_word, canonical_complement))
                    return result
    return result


def _native(request):
    identity = sha256(_EXECUTABLE.read_bytes()).hexdigest()
    result = subprocess.run([str(_EXECUTABLE)], input=_wire(request) + b"\n",
                            capture_output=True, timeout=30, check=False)
    if result.returncode or sha256(_EXECUTABLE.read_bytes()).hexdigest() != identity:
        raise ValueError("SIX_NOUN_NATIVE_EXECUTION_FAILED")
    if len(result.stdout) > _MAX_RESPONSE_BYTES:
        raise OverflowError("SIX_NOUN_NATIVE_RESPONSE_LIMIT")
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        raise ValueError("SIX_NOUN_NATIVE_RESPONSE_COUNT")
    value = _parse_json(lines[0])
    if type(value) is dict and value.get("status") == "RESOURCE_LIMIT":
        raise OverflowError("SIX_NOUN_NATIVE_RESOURCE_LIMIT")
    # Compare serialized types as well as values: False, 0, 0.0 and "0" differ.
    if _wire(value) != _wire(_expected(request)):
        raise ValueError("SIX_NOUN_NATIVE_RECEIPT_MISMATCH")
    return value, identity


def _documentary_links_match(receipt, review):
    """Keep matching authored IDs from silently pointing outside the pinned review."""
    known = {passage["id"] for passage in review["passages"]}
    trace = receipt.get("node_trace")
    if type(trace) is not list:
        return False
    for node in trace:
        if type(node) is not dict:
            return False
        passages = node.get("passage_ids")
        if (type(passages) is not list or not passages
                or any(type(passage) is not str or passage not in known for passage in passages)):
            return False
    return True


def acquire_six_noun(text, *, source_id="user_text", context="unspecified"):
    """Acquire a bounded construction; no caller-supplied features or proof flags.

The context is retained as an opaque identity, not interpreted to prove a
speaker's purpose or an exception's absence. Outside-scope strings and missing
semantic prerequisites are deferred, never declared invalid Arabic.
"""
    foundation.require_foundation("tools.linguistic_truth.six_noun.acquire_six_noun")
    report = {"schema": _SCHEMA, "law_id": _LAW, "status": "DEFER",
        "native_checked": False, "grammar_certified": False, "claims": [], "node_trace": [],
        "reading": None, "orthographic_bridge": None,
        "source_projection_complete": False, "foundation_complete": False,
        "strict_language_accepted": False, "intended_sense_established": False,
        "speaker_reference_established": False, "world_truth_established": False,
        "external_truth_established": False, "tawatur_established": False,
        "whole_arabic_complete": False, "linguistic_rejection": False,
        "residuals": ["SOURCE_AUTHENTICITY_NOT_ESTABLISHED",
                      "RULE_INTERPRETATION_IS_AUTHORED",
                      "REFERENCE_INTENT_AND_WORLD_TRUTH_NOT_ESTABLISHED"]}
    if type(text) not in {str, bytes}:
        return {**report, "status": "INVALID_INPUT", "reason": "RAW_TEXT_REQUIRED"}
    try:
        raw = text.encode("utf-8", "strict") if type(text) is str else text
        text = raw.decode("utf-8", "strict")
        for label, maximum in ((source_id, 1024), (context, 4096)):
            if type(label) is not str or not label.strip() or len(label.encode("utf-8")) > maximum:
                raise ValueError("INVALID_SIX_NOUN_CONTEXT_LABEL")
        if not text:
            raise ValueError("EMPTY_TEXT")
    except (UnicodeError, ValueError) as error:
        return {**report, "status": "INVALID_INPUT", "reason": str(error)}
    if len(raw) > _MAX_INPUT_BYTES:
        return {**report, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_SIX_NOUN_INPUT_BYTES"}
    source = {"id": source_id, "revision": sha256(raw).hexdigest(), "text": text}
    report.update(source=source, context=context)
    try:
        foundation.validate_source(text)
        review = _review()
        report["source_review"] = {"sha256": _REVIEW_SHA,
            "authority": review["authority"], "passage_ids": [p["id"] for p in review["passages"]]}
    except NabtError as error:
        return {**report, "status": "RESOURCE_EXHAUSTED" if error.code == "RESOURCE_LIMIT"
                else "INVALID_INPUT", "reason": error.code}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {**report, "status": "SOURCE_UNAVAILABLE", "reason": str(error)}
    request = {"source": source, "context": context}
    try:
        receipt, binary_hash = _native(request)
    except (OverflowError, RecursionError, subprocess.TimeoutExpired) as error:
        return {**report, "status": "RESOURCE_EXHAUSTED", "reason": str(error)}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        return {**report, "status": "VERIFICATION_UNAVAILABLE", "reason": str(error)}
    if not _documentary_links_match(receipt, review):
        return {**report, "status": "VERIFICATION_UNAVAILABLE",
                "reason": "SIX_NOUN_DOCUMENTARY_LINK_NOT_IN_REVIEW"}
    report.update(status=receipt["status"], native_checked=True,
        grammar_certified=receipt["grammar_certified"], reading=deepcopy(receipt["reading"]),
        node_trace=deepcopy(receipt["node_trace"]),
        orthographic_bridge=deepcopy(receipt["orthographic_bridge"]),
        source_projection_complete=receipt["source_projection"]["status"] == "COMPLETE",
        foundation_complete=receipt["foundation_complete"], native_receipt=receipt,
        executable_sha256=binary_hash, request_sha256=sha256(_wire(request)).hexdigest(),
        receipt_sha256=sha256(_wire(receipt)).hexdigest())
    report["residuals"] += list(receipt["unresolved"])
    if receipt["status"] != "CHECKED_SIX_NOUN":
        blocking = [value for value in receipt["unresolved"] if value in {
            "DHU_COMPANIONSHIP_NOT_ACQUIRED", "COMMON_LETTER_CASE_MISMATCH",
            "DECLARED_ORTHOGRAPHIC_PROFILE_INCOMPLETE", "INVALID_SOURCE_MARKS_OR_EMPTY",
            "OUTSIDE_EXACT_TEMPLATE_OR_VARIANT_NOT_ACQUIRED"}]
        report["reason"] = (blocking[0] if blocking else
                            "OUTSIDE_EXPLICIT_CONSTRUCTION_NOT_ARABIC_REJECTION")
        return report
    report["claims"] = [{"id": "SOURCE_BOUND_SIX_NOUN_CONSTRUCTION",
        "kind": "SOURCE_BOUND_SIX_NOUN_CONSTRUCTION", "authority": "NATIVE_CHECKED",
        "scope": "The installed exact-spelling construction grammar and common letter-substitution convention; lexical intent, external reference, source authenticity and all Arabic excluded",
        "source": source, "context": context, "reading": deepcopy(receipt["reading"]),
        "node_trace": deepcopy(receipt["node_trace"]),
        "source_review_sha256": _REVIEW_SHA, "request_sha256": report["request_sha256"],
        "receipt_sha256": report["receipt_sha256"], "unresolved_premises": list(report["residuals"]),
        "proof": {"law_id": _LAW, "theorems": list(_THEOREMS)}}]
    return report
