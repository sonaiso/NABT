"""Conditional, source-replayed gemination operators; never a free-text parser.

The input is an explicitly segmented morphophonemic frame. The caller's choice
of dialect or construction is a premise, not evidence that a word has that role.
The original frame is retained. Output doubles consonants rather than erasing
their identity, and source spelling is never rewritten by a sound projection.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
from itertools import product
import json

from .errors import NabtError

LAW_ID = "nabt.classical-gemination.v1"
RULE_IDS = (
    "GEM-VOWELED-FINAL", "GEM-JUSSIVE-VARIANTS", "GEM-FEMININE-SUFFIX",
    "GEM-EXCLAMATION", "ASSIM-NUN-B-BLOCKED-TEXT",
)
INVENTORY_SHA256 = "6de39f04e6981ec646a9af98ed3ebb600d1c60bcd498ddfc925d6ba44664061d"
VOWELS = ("s", "a", "i", "u")
DIALECTS = ("hijaz", "tamim", "kab_ghani", "bakr", "attested_union")
CONTEXTS = ("ordinary", "command", "jussive", "feminine", "exclamation", "hallumma")
LETTERS = frozenset("ءابتثجحخدذرزسشصضطظعغفقكلمنهويىأإآؤئٱ")
CONNECTIONS = ("within_word", "word_boundary_wasl", "word_boundary_waqf")
_SIBAWAYHI_VOWELS = (1711414, 1714952,
    "2ac335f32b2b4e31ea861cdba3dbf8dedd6cb6fc29ef546efa33cc8fd8f4e397")
_SIBAWAYHI_NUN = (2586239, 2587666,
    "e420f759a65a5ca92e1cd7e2c591498da34f26572898a1c7819a8c612228b623")


from nabt import foundation

def replay_sources(rule_id):
    """Recheck installed original bytes and contradictory readings on every call."""
    if type(rule_id) is not str:
        raise NabtError("INVALID_GEMINATION_RULE", "Rule ID must be a string")
    if rule_id not in RULE_IDS:
        raise NabtError("UNKNOWN_CLASSICAL_GEMINATION_RULE", "Unknown scoped rule", status="DEFER")
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("classical_rule_inventory_v1.json").read_bytes()
        if sha256(raw).hexdigest() != INVENTORY_SHA256:
            raise ValueError("inventory changed")
        inventory = json.loads(raw)
        rule = next(r for r in inventory["rules"] if r["rule_id"] == rule_id)
        source_map = {s["source_id"]: s for s in inventory["sources"]}
        spans = deepcopy(rule["source_spans"])
        if rule_id == RULE_IDS[1]:
            start, end, digest = _SIBAWAYHI_VOWELS
            spans.append({"source_id": "sibawayhi", "start": start, "end": end,
                          "sha256": digest, "line_start": 14412, "line_end": 14440})
        if rule_id == RULE_IDS[-1]:
            start, end, digest = _SIBAWAYHI_NUN
            spans.append({"source_id": "sibawayhi", "start": start, "end": end,
                          "sha256": digest, "line_start": 21472, "line_end": 21482})
        loaded = {}
        for span in spans:
            sid = span["source_id"]
            if sid not in loaded:
                source = source_map[sid]
                loaded[sid] = directory.joinpath(source["local_file"]).read_bytes()
                if sha256(loaded[sid]).hexdigest() != source["raw_sha256"]:
                    raise ValueError("source changed")
            chunk = loaded[sid][span["start"]:span["end"]]
            if sha256(chunk).hexdigest() != span["sha256"]:
                raise ValueError("source span changed")
            if "raw_text" in span and chunk.decode() != span["raw_text"]:
                raise ValueError("source reading changed")
        return [{k: v for k, v in s.items() if k != "raw_text"} for s in spans]
    except (OSError, ValueError, KeyError, TypeError, StopIteration, UnicodeError) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Gemination source replay failed",
                        status="DEFER") from exc


def _enum(value, allowed, name):
    if type(value) is not str or value not in allowed:
        raise NabtError("INVALID_GEMINATION_FRAME", "Invalid " + name)
    return value


def _cell(value):
    if type(value) not in (list, tuple) or len(value) != 2:
        raise NabtError("INVALID_GEMINATION_FRAME", "A cell is [letter, vowel]")
    letter, vowel = value
    _enum(letter, LETTERS, "cell letter")
    _enum(vowel, VOWELS, "cell vowel")
    return (letter, vowel)


def _cells(value):
    if type(value) not in (list, tuple):
        raise NabtError("INVALID_GEMINATION_FRAME", "A cell list is required")
    if len(value) > 128:
        raise NabtError("RESOURCE_LIMIT", "Cell list exceeds the execution bound", status="DEFER")
    return tuple(_cell(x) for x in value)


def _frame(value, nun):
    keys = ({"left", "right", "connection"} if nun else
            {"prefix", "first", "second", "suffix", "context", "dialect"})
    if type(value) is not dict or set(value) != keys:
        raise NabtError("INVALID_GEMINATION_FRAME", "Frame fields must match the declared schema")
    if nun:
        return {"left": _cell(value["left"]), "right": _cell(value["right"]),
                "connection": _enum(value["connection"], CONNECTIONS, "connection")}
    return {"prefix": _cells(value["prefix"]), "first": _cell(value["first"]),
            "second": _cell(value["second"]), "suffix": _cells(value["suffix"]),
            "context": _enum(value["context"], CONTEXTS, "context"),
            "dialect": _enum(value["dialect"], DIALECTS, "dialect")}


def _actions(rule, context, dialect, preceding, last):
    """Finite control layer exported independently by Lean; no source authority."""
    if rule == "GEM-EXCLAMATION" and context == "hallumma":
        return ["retain_hallumma"] if preceding == "u" and last == "a" else []
    if preceding == "s":
        return []
    if rule == "GEM-VOWELED-FINAL":
        return ["contract_keep"] if context == "ordinary" and last != "s" else []
    if rule == "GEM-JUSSIVE-VARIANTS" and context in ("command", "jussive") and last == "s":
        if dialect == "hijaz":
            return ["split"]
        if dialect == "tamim":
            return ["contract_a"] + (["contract_" + preceding] if preceding != "a" else [])
        if dialect == "kab_ghani":
            return ["contract_i"]
        if dialect == "attested_union":
            return ["split", "contract_a", "contract_i"] + (["contract_u"] if preceding == "u" else [])
        return []  # The named Bakr passage concerns subject suffixes, not this frame.
    if rule == "GEM-FEMININE-SUFFIX" and context == "feminine" and last == "s":
        if dialect == "bakr":
            return ["bakr_contraction_unvocalized"]
        if dialect == "attested_union":
            return ["split", "bakr_contraction_unvocalized"]
        return ["split"]
    if rule == "GEM-EXCLAMATION" and context == "exclamation" and last == "s":
        return ["split"]
    return []


def _shape_reason(frame):
    prefix, first, second, suffix = (frame[k] for k in ("prefix", "first", "second", "suffix"))
    if first[0] != second[0] or first[0] in "ايوىٱآ":
        return "requires_identical_consonantal_radicals_outside_glide_exceptions"
    if first[1] == "s" and frame["context"] != "hallumma":
        return "moving_first_twin_required_by_this_scope"
    if not prefix:
        return "word_initial_twin_exception_not_covered"
    if any(c[0] == "ٱ" for c in prefix[1:] + (first, second) + suffix):
        return "wasl_hamza_must_be_initial"
    if prefix[0][0] == "ٱ" and (len(prefix) < 2 or prefix[1][1] != "s"):
        return "wasl_support_requires_following_sukun"
    if frame["context"] in ("command", "jussive", "exclamation") and suffix:
        return "suffix_sensitive_final_vowels_need_separate_scope"
    if frame["context"] == "feminine" and suffix != (("ن", "a"),):
        return "feminine_frame_requires_actual_nun_suffix"
    if frame["context"] == "exclamation" and not (
            len(prefix) == 2 and prefix[0] == ("أ", "a") and prefix[1][1] == "s" and first[1] == "i"):
        return "requires_af_il_exclamation_shape_and_independent_construction_premise"
    if frame["context"] == "hallumma" and not (
            prefix == (("ه", "a"), ("ل", "u")) and first == ("م", "s") and
            second == ("م", "a") and not suffix):
        return "hallumma_is_a_fixed_lexical_exception"
    return None


def _segments(cells):
    result = []
    for letter, vowel in cells:
        result.append("ʔ" if letter == "ٱ" else letter)
        if vowel != "s":
            result.append(vowel)
    return result


def _project(frame, action):
    prefix = list(frame["prefix"])
    first, second, suffix = frame["first"], frame["second"], frame["suffix"]
    if action == "bakr_contraction_unvocalized":
        return {"operation": action, "cells": None, "segments": None,
                "surface_complete": False,
                "defer_reason": "source_attests_contraction_but_this_span_does_not_fix_final_vowel"}
    moved, dropped = False, False
    if action not in ("split", "retain_hallumma"):
        if prefix[-1][1] == "s" and prefix[-1][0] not in "اىآ":
            prefix[-1] = (prefix[-1][0], first[1])
            moved = True
            if len(prefix) == 2 and prefix[0][0] == "ٱ":
                prefix = prefix[1:]
                dropped = True
        last = second[1] if action == "contract_keep" else action[-1]
        cells = prefix + [(first[0], "s"), (second[0], last)] + list(suffix)
    else:
        cells = prefix + [first, second] + list(suffix)
    return {"operation": action, "cells": [list(c) for c in cells],
            "segments": _segments(cells), "surface_complete": True,
            "vowel_transferred": moved, "initial_wasl_removed": dropped}


def _preceding(frame):
    previous = frame["prefix"][-1]
    if previous[0] in "اىآ":
        return "a"
    return frame["first"][1] if previous[1] == "s" else previous[1]


def evaluate(rule_id, frame):
    """Enumerate conditional operations, with outside-scope distinct from rejection.

    No result establishes the input's morphological classification, dialect,
    lexical attestation, or an exclamation's syntactic context. ``CONDITIONAL``
    explicitly describes this limitation, even when the symbolic form is total.
    """
    foundation.require_foundation('nabt.classical_gemination.evaluate')
    sources = replay_sources(rule_id)
    original = deepcopy(frame)
    f = _frame(frame, rule_id == RULE_IDS[-1])
    alternatives, reason = [], None
    if rule_id == RULE_IDS[-1]:
        if f["left"] == ("ن", "s") and f["right"][0] == "ب" and f["connection"] != "word_boundary_waqf":
            cells = [("م", "s"), f["right"]]
            alternatives = [{"operation": "nun_to_mim_before_ba", "cells": [list(c) for c in cells],
                             "segments": _segments(cells), "surface_complete": True}]
        else:
            reason = "requires_sukun_nun_adjacent_to_ba_without_interword_pause"
    else:
        reason = _shape_reason(f)
        if reason is None:
            alternatives = [_project(f, a) for a in _actions(rule_id, f["context"], f["dialect"],
                                                            _preceding(f), f["second"][1])]
            if not alternatives:
                reason = "construction_dialect_or_vowel_outside_rule"
    return {"law_id": LAW_ID, "rule_id": rule_id,
            "status": "CONDITIONAL" if alternatives else "OUTSIDE_SCOPE",
            "original_frame": original, "alternatives": alternatives,
            "reason": reason, "source_spans": sources,
            "premises_established": False, "word_attestation_established": False,
            "free_text_acquisition_proved": False, "acoustic_validation": False,
            "complete_for_arabic": False,
            "textual_discrepancy_retained": rule_id == RULE_IDS[-1]}


def finite_export_rows():
    """All 1,920 finite morphology controls and 72 assimilation controls.

    These rows compare a control relation, not the unbounded cell projections or
    acquisition of linguistic premises. An additional 504 abstract projection
    controls compare actual cells; they are not licensed words or analyses.
    """
    morph = [{"rule_id": rule, "context": context, "dialect": dialect,
              "preceding": preceding, "last": last,
              "actions": _actions(rule, context, dialect, preceding, last)}
             for rule, context, dialect, preceding, last in
             product(RULE_IDS[:4], CONTEXTS, DIALECTS, VOWELS, VOWELS)]
    nun = [{"left": left, "vowel": vowel, "right": right, "connection": connection,
            "actions": (["nun_to_mim_before_ba"] if left == "ن" and vowel == "s" and
                        right == "ب" and connection != "word_boundary_waqf" else [])}
           for left, vowel, right, connection in
           product(("ن", "م"), VOWELS, ("ب", "ي", "د"), CONNECTIONS)]
    prefixes = (
        (("ر", "s"),), (("ٱ", "u"), ("ر", "s")), (("ر", "a"),),
        (("ٱ", "i"), ("ط", "s"), ("م", "a"), ("ء", "s")),
        (("م", "a"), ("ا", "s")), (("أ", "a"), ("م", "s")),
    )
    actions = ("split", "contract_keep", "contract_a", "contract_i", "contract_u",
               "bakr_contraction_unvocalized", "retain_hallumma")
    projections = []
    for prefix, first, last, action in product(prefixes, ("a", "i", "u"), VOWELS, actions):
        frame = {"prefix": prefix, "first": ("د", first), "second": ("د", last),
                 "suffix": (("ن", "a"),)}
        projections.append({"prefix": [list(c) for c in prefix], "first": first,
                            "last": last, "action": action, "cells": _project(frame, action)["cells"]})
    return {"law_id": LAW_ID, "morphology": morph, "assimilation": nun, "projections": projections}
