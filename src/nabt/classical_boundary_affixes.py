"""Conditional, source-bound boundary/affix transformations.

This module does not acquire morphology or a speaker's intention from free text.
A well-formed frame states premises; it cannot certify those premises. Returned
segments belong to a declared symbolic alphabet, not an acoustic measurement.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
from itertools import product
import json

from .errors import NabtError

LAW_ID = "nabt.classical-boundary-affixes.v1"
RULE_IDS = ("CMD-WEAK-DELETE", "AFFIX-LIGHT-NUN-PAUSE", "MUGHNI-ANA-BOUNDARY")
ALPHABET_ID = "nabt.boundary-affix-segments.v1"
SEGMENTS = tuple("ءابتثجحخدذرزسشصضطظعغفقكلمنهوي") + ("a", "i", "u", "a:", "i:", "u:")
INVENTORY_SHA256 = "6de39f04e6981ec646a9af98ed3ebb600d1c60bcd498ddfc925d6ba44664061d"
PROFILES = ("khalil", "yunus", "both")
SHAPES = ("singular_open", "deleted_ya_command", "deleted_waw_command",
          "retained_ya_command", "retained_waw_command", "deleted_ya_indicative",
          "deleted_waw_indicative", "indicative_dual")
TAILS = {
    "singular_open": ["a", "ن"],
    "deleted_ya_command": ["i", "ن"],
    "deleted_waw_command": ["u", "ن"],
    "retained_ya_command": ["ي", "i", "ن"],
    "retained_waw_command": ["و", "u", "ن"],
    "deleted_ya_indicative": ["i", "ن"],
    "deleted_waw_indicative": ["u", "ن"],
    # Here light nun is intended but absent: the source retains indicative nun.
    "indicative_dual": ["a:", "ن", "i"],
}


from nabt import foundation

def _bad(message):
    raise NabtError("INVALID_CLASSICAL_BOUNDARY_FRAME", message)


def _choice(value, allowed, name):
    if type(value) is not str or value not in allowed:
        _bad(f"Invalid {name}")
    return value


def _tokens(value):
    if type(value) is not list or not value:
        _bad("segments must be a nonempty list")
    if len(value) > 256:
        raise NabtError("RESOURCE_LIMIT", "Frame exceeds 256 symbolic segments", status="DEFER")
    if any(type(s) is not str or s not in SEGMENTS for s in value):
        _bad("Invalid segment in versioned alphabet")
    return value


def _source(rule_id):
    """Recheck the installed inventory and whole source bytes on every request."""
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("classical_rule_inventory_v1.json").read_bytes()
        if sha256(raw).hexdigest() != INVENTORY_SHA256:
            raise ValueError("Inventory identity mismatch")
        inventory = json.loads(raw)
        rule = next(r for r in inventory["rules"] if r["rule_id"] == rule_id)
        sources = {s["source_id"]: s for s in inventory["sources"]}
        for span in rule["source_spans"]:
            source = sources[span["source_id"]]
            body = directory.joinpath(source["local_file"]).read_bytes()
            selected = body[span["start"]:span["end"]]
            if (sha256(body).hexdigest() != source["raw_sha256"] or
                    sha256(selected).hexdigest() != span["sha256"] or
                    selected.decode() != span["raw_text"]):
                raise ValueError("Original source replay failed")
        return [{k: span[k] for k in ("source_id", "line_start", "line_end", "start", "end", "sha256")}
                for span in rule["source_spans"]]
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Boundary-affix source replay failed",
                        status="DEFER") from exc


def _out(segments, derivation, evidence_kind="conditional_rule"):
    return {"segments": list(segments), "derivation": derivation, "evidence_kind": evidence_kind}


def _weak(frame):
    _choice(frame["person"], ("2ms", "2fs", "2dual", "2mp", "2fp"), "person")
    _choice(frame["suffix"], ("none", "subject", "object", "emphatic"), "suffix")
    radical = _choice(frame["final_radical"], ("و", "ي", "sound"), "final radical")
    if frame["person"] != "2ms" or frame["suffix"] != "none":
        return [], "person_or_suffix_outside_weak_deletion_contract"
    before = frame["segments"]
    if len(before) < 2 or before[-2] not in SEGMENTS[:29]:
        return [], "final_long_vowel_has_no_immediate_consonant"
    allowed = {"و": ("a:", "u:"), "ي": ("a:", "i:"), "sound": ()}[radical]
    if before[-1] not in allowed:
        return [], "weak_radical_and_realized_vowel_do_not_match"
    return [_out(before[:-1] + [before[-1][0]], "delete_weak_final")], None


def _light(frame):
    shape = _choice(frame["shape"], SHAPES, "light-nun shape")
    profile = _choice(frame["profile"], PROFILES, "grammatical profile")
    nun = _choice(frame["nun_kind"], ("light", "heavy", "feminine"), "nun kind")
    following = _choice(frame["following"], ("none", "consonant", "hamzat_wasl"), "following onset")
    if frame["end"] == "waqf" and following != "none":
        _bad("A pause cannot have a connected following onset")
    if nun != "light":
        return [], "heavy_and_feminine_nun_are_not_light_nun"
    tail = TAILS[shape]
    before = frame["segments"]
    if len(before) <= len(tail) or before[-len(tail):] != tail:
        return [], "segments_do_not_match_the_declared_morphological_shape"
    prefix = before[:-len(tail)]
    if shape == "indicative_dual" and profile == "yunus":
        return [], "yunus_dual_extension_requires_separate_source_contract"
    if frame["end"] == "wasl":
        if shape != "indicative_dual" and following == "hamzat_wasl":
            return [_out(before[:-1], "drop_light_nun_before_wasl")], None
        return [_out(before, "retain_in_connection")], None
    if shape == "singular_open":
        return [_out(prefix + ["a:"], "replace_light_nun_with_alif")], None
    if shape in ("deleted_ya_command", "deleted_waw_command"):
        vowel = "i:" if shape == "deleted_ya_command" else "u:"
        return [_out(prefix + [vowel], "restore_deleted_subject_glide")], None
    if shape == "indicative_dual":
        return [_out(prefix + ["a:", "ن"], "restore_indicative_nun", "reported_khalil")], None
    is_ya = shape in ("retained_ya_command", "deleted_ya_indicative")
    glide, long_vowel = ("ي", "i:") if is_ya else ("و", "u:")
    retained = shape in ("retained_ya_command", "retained_waw_command")
    result = []
    if profile in ("khalil", "both"):
        tail = [glide] if retained else [long_vowel, "ن"]
        result.append(_out(prefix + tail,
                           "drop_light_nun_after_retained_glide" if retained else "restore_indicative_nun",
                           "reported_khalil"))
    if profile in ("yunus", "both"):
        tail = [glide, long_vowel] if retained else [long_vowel]
        result.append(_out(prefix + tail, "yunus_replacement_after_nonfatha",
                           "reported_yunus" if retained else "source_analogical_yunus"))
    return result, None


def _ana(frame):
    _choice(frame["analysis"], ("speaker_pronoun", "masdariyya_particle", "other"), "analysis")
    profile = _choice(frame["profile"], ("majority", "minority_sukun", "both"), "ana profile")
    if frame["analysis"] != "speaker_pronoun":
        return [], "ana_rule_requires_speaker_pronoun_analysis"
    # Input is the citation representation, retained unchanged in the receipt.
    if frame["segments"] != ["ء", "a", "ن", "a:"]:
        return [], "input_is_not_the_canonical_ana_citation_form"
    if frame["end"] == "waqf":
        if profile == "minority_sukun":
            return [], "minority_pause_not_established_by_cited_passage"
        return [_out(["ء", "a", "ن", "a:"], "ana_pause_alif", "reported_majority")], None
    result = []
    if profile in ("majority", "both"):
        result.append(_out(["ء", "a", "ن", "a"], "ana_connected_fatha", "reported_majority"))
    if profile in ("minority_sukun", "both"):
        result.append(_out(["ء", "a", "ن"], "ana_connected_sukun", "reported_minority"))
    return result, None


def evaluate(rule_id, frame):
    """Compute a conditional relation; labels never establish their own premises."""
    foundation.require_foundation('nabt.classical_boundary_affixes.evaluate')
    _choice(rule_id, RULE_IDS, "rule ID")
    if type(frame) is not dict:
        _bad("frame must be a dictionary")
    fields = {"segments", "start", "end"}
    if rule_id == RULE_IDS[0]:
        fields |= {"final_radical", "person", "suffix"}
    elif rule_id == RULE_IDS[1]:
        fields |= {"shape", "profile", "nun_kind", "following"}
    else:
        fields |= {"analysis", "profile"}
    if set(frame) != fields:
        _bad("Frame fields do not match the selected rule")
    _tokens(frame["segments"])
    _choice(frame["start"], ("ibtida", "wasl"), "start")
    _choice(frame["end"], ("wasl", "waqf"), "end")
    source = _source(rule_id)
    alternatives, reason = (dict(zip(RULE_IDS, (_weak, _light, _ana)))[rule_id])(frame)
    unresolved = []
    if rule_id == RULE_IDS[2] and frame["end"] == "waqf" and frame["profile"] in ("both", "minority_sukun") and frame["analysis"] == "speaker_pronoun":
        unresolved.append("minority_sukun_pause")
    if rule_id == RULE_IDS[1] and frame["shape"] == "indicative_dual" and frame["profile"] in ("both", "yunus") and frame["nun_kind"] == "light":
        unresolved.append("yunus_indicative_dual")
    status = "CONDITIONAL" if alternatives else ("DEFER" if unresolved else "OUTSIDE_SCOPE")
    return {"law_id": LAW_ID, "rule_id": rule_id, "alphabet": ALPHABET_ID,
            "status": status,
            "unresolved_profiles": unresolved,
            "alternatives_complete_within_requested_profile": not unresolved,
            "premises_established": False, "language_license": False,
            "input": deepcopy(frame), "alternatives": alternatives, "reason": reason,
            "source_spans": source,
            "output_layer": "morphological_preboundary" if rule_id == RULE_IDS[0] else "symbolic_boundary",
            "start_boundary_preserved": True,
            "free_text_analysis": False, "acoustic_validation": False}


# These are editorially segmented instantiations of original spellings, not a
# learned parser or a general assertion that every generated shape is a word.
_EXAMPLES = {
    "qatr_irmi": (RULE_IDS[0], "ارم", {"segments": ["i", "ر", "م", "i:"], "start": "ibtida", "end": "wasl", "final_radical": "ي", "person": "2ms", "suffix": "none"}),
    "qatr_ughzu": (RULE_IDS[0], "اغز", {"segments": ["u", "غ", "ز", "u:"], "start": "ibtida", "end": "wasl", "final_radical": "و", "person": "2ms", "suffix": "none"}),
    "qatr_ikhsha": (RULE_IDS[0], "اخش", {"segments": ["i", "خ", "ش", "a:"], "start": "ibtida", "end": "wasl", "final_radical": "ي", "person": "2ms", "suffix": "none"}),
    "sibawayhi_idriba": (RULE_IDS[1], "اضربا", {"segments": ["i", "ض", "ر", "i", "ب", "a", "ن"], "start": "ibtida", "end": "waqf", "shape": "singular_open", "profile": "khalil", "nun_kind": "light", "following": "none"}),
    "sibawayhi_idribi": (RULE_IDS[1], "اضربي", {"segments": ["i", "ض", "ر", "i", "ب", "i", "ن"], "start": "ibtida", "end": "waqf", "shape": "deleted_ya_command", "profile": "khalil", "nun_kind": "light", "following": "none"}),
    "sibawayhi_idribu": (RULE_IDS[1], "اضربوا", {"segments": ["i", "ض", "ر", "i", "ب", "u", "ن"], "start": "ibtida", "end": "waqf", "shape": "deleted_waw_command", "profile": "khalil", "nun_kind": "light", "following": "none"}),
    "sibawayhi_ikhshay": (RULE_IDS[1], "اخشي", {"segments": ["i", "خ", "ش", "a", "ي", "i", "ن"], "start": "ibtida", "end": "waqf", "shape": "retained_ya_command", "profile": "both", "nun_kind": "light", "following": "none"}),
    "sibawayhi_ikhshaw": (RULE_IDS[1], "اخشوا", {"segments": ["i", "خ", "ش", "a", "و", "u", "ن"], "start": "ibtida", "end": "waqf", "shape": "retained_waw_command", "profile": "both", "nun_kind": "light", "following": "none"}),
    "sibawayhi_tadribin": (RULE_IDS[1], "تضربين", {"segments": ["ت", "a", "ض", "ر", "i", "ب", "i", "ن"], "start": "ibtida", "end": "waqf", "shape": "deleted_ya_indicative", "profile": "both", "nun_kind": "light", "following": "none"}),
    "sibawayhi_tadribun": (RULE_IDS[1], "تضربون", {"segments": ["ت", "a", "ض", "ر", "i", "ب", "u", "ن"], "start": "ibtida", "end": "waqf", "shape": "deleted_waw_indicative", "profile": "both", "nun_kind": "light", "following": "none"}),
    "sibawayhi_tadriban": (RULE_IDS[1], "تضربان", {"segments": ["ت", "a", "ض", "ر", "i", "ب", "a:", "ن", "i"], "start": "ibtida", "end": "waqf", "shape": "indicative_dual", "profile": "khalil", "nun_kind": "light", "following": "none"}),
    "mughni_ana": (RULE_IDS[2], "ضمير المتكلم", {"segments": ["ء", "a", "ن", "a:"], "start": "ibtida", "end": "wasl", "analysis": "speaker_pronoun", "profile": "both"}),
}


def source_examples():
    return [{"example_id": k, "rule_id": v[0], "source_anchor": v[1], "frame": deepcopy(v[2])}
            for k, v in _EXAMPLES.items()]


def evaluate_example(example_id):
    if type(example_id) is not str or example_id not in _EXAMPLES:
        raise NabtError("UNKNOWN_CLASSICAL_BOUNDARY_EXAMPLE", "Unknown installed example", status="DEFER")
    rule_id, anchor, frame = _EXAMPLES[example_id]
    result = evaluate(rule_id, deepcopy(frame))
    directory = files("nabt").joinpath("data/source_evidence")
    inventory = json.loads(directory.joinpath("classical_rule_inventory_v1.json").read_bytes())
    rule = next(r for r in inventory["rules"] if r["rule_id"] == rule_id)
    if not any(anchor in s["raw_text"] for s in rule["source_spans"]):
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Example anchor absent from source", status="DEFER")
    result.update(example_id=example_id, source_anchor=anchor,
                  source_instantiation="editorially_interpreted_pinned_passage",
                  whole_word_automatically_acquired=False)
    return result


def finite_export_rows():
    """Finite conformance controls; not a linguistic coverage denominator."""
    rows = []
    for radical, vowel, person, suffix in product(("و", "ي", "sound"), ("a:", "i:", "u:"), ("2ms", "2fs", "2dual", "2mp", "2fp"), ("none", "subject", "object", "emphatic")):
        f = dict(segments=["ك", vowel], final_radical=radical, person=person, suffix=suffix, start="ibtida", end="wasl")
        alts, _ = _weak(f)
        rows.append({"rule_id": RULE_IDS[0], "frame": f, "alternatives": alts})
    for shape, profile, nun, end, following in product(SHAPES, PROFILES, ("light", "heavy", "feminine"), ("wasl", "waqf"), ("none", "consonant", "hamzat_wasl")):
        if end == "waqf" and following != "none":
            continue
        f = dict(segments=["ك"] + TAILS[shape], shape=shape, profile=profile, nun_kind=nun, end=end, following=following, start="ibtida")
        alts, _ = _light(f)
        rows.append({"rule_id": RULE_IDS[1], "frame": f, "alternatives": alts})
    for analysis, profile, end in product(("speaker_pronoun", "masdariyya_particle", "other"), ("majority", "minority_sukun", "both"), ("wasl", "waqf")):
        f = dict(segments=["ء", "a", "ن", "a:"], analysis=analysis, profile=profile, end=end, start="ibtida")
        alts, _ = _ana(f)
        rows.append({"rule_id": RULE_IDS[2], "frame": f, "alternatives": alts})
    return rows
