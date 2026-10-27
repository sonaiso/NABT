"""Six source-pinned, conditional hamza operators over declared morphophonemes.

This is not a parser, an attestation oracle, a spelling renderer or an acoustic
model. Morphological origin/analysis is an explicit unacquired premise. Results
never grant a word or reading certificate, including when source bytes replay.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError

LAW_ID = "nabt.classical-hamza.v1"
ALPHABET_ID = "nabt.classical-hamza-morphophonemes.v1"
INVENTORY_SHA256 = "6de39f04e6981ec646a9af98ed3ebb600d1c60bcd498ddfc925d6ba44664061d"
RULE_IDS = (
    "HAMZA-INTERROGATIVE-AL", "HAMZA-FINAL-LONG",
    "HAMZA-ACTIVE-PARTICIPLE", "HAMZA-BROKEN-PLURAL",
    "HAMZA-TWO-GLIDES", "HAMZA-LEXICAL-COMMAND",
)
LETTERS = frozenset("ءابتثجحخدذرزسشصضطظعغفقكلمنهوي")
GLIDES = {"waw": "و", "ya": "ي"}
LONGS = {"alif": "ا", **GLIDES}


from nabt import foundation

def _bad(message):
    raise NabtError("INVALID_CLASSICAL_HAMZA_FRAME", message)


def _keys(frame, expected):
    if type(frame) is not dict or set(frame) != set(expected):
        _bad("Frame fields must match the declared rule schema exactly")


def _choice(value, values, name):
    if type(value) is not str or value not in values:
        _bad(f"Invalid {name}")
    return value


def _atoms(value, name, *, minimum=0, maximum=128, feminine=False):
    if type(value) is not list:
        _bad(f"{name} must be a list of atomic morphophonemes")
    if len(value) > maximum:
        raise NabtError("RESOURCE_LIMIT", f"{name} exceeds the declared bound", status="DEFER")
    allowed = LETTERS | ({"ة"} if feminine else set())
    if len(value) < minimum or any(type(x) is not str or x not in allowed for x in value):
        _bad(f"Invalid atoms in {name}; no normalization or vowel stripping is performed")
    return list(value)


def _atom(value, name):
    if type(value) is not str or value not in LETTERS:
        _bad(f"Invalid {name}")
    return value


def _source(rule_id):
    """Replay installed original bytes; no caller manifest is accepted."""
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("classical_rule_inventory_v1.json").read_bytes()
        if sha256(raw).hexdigest() != INVENTORY_SHA256:
            raise ValueError("Inventory digest mismatch")
        inventory = json.loads(raw)
        rule = next(r for r in inventory["rules"] if r["rule_id"] == rule_id)
        sources = {s["source_id"]: s for s in inventory["sources"]}
        result = []
        for span in rule["source_spans"]:
            source = sources[span["source_id"]]
            body = directory.joinpath(source["local_file"]).read_bytes()
            selected = body[span["start"]:span["end"]]
            if (sha256(body).hexdigest() != source["raw_sha256"] or
                    sha256(selected).hexdigest() != span["sha256"] or
                    selected.decode("utf-8") != span["raw_text"]):
                raise ValueError("Source replay mismatch")
            result.append({"source_id": span["source_id"], "start": span["start"],
                           "end": span["end"], "sha256": span["sha256"],
                           "source_sha256": source["raw_sha256"],
                           "original_url": source["original_url"]})
        return result
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Hamza source replay failed",
                        status="DEFER") from exc


def _compute(rule_id, frame):
    """Return (input atoms, alternatives, blocker, unresolved premises)."""
    alternatives = []
    blocker = None
    unresolved = []

    def emit(operation, atoms):
        alternatives.append({"operation": operation, "morphophonemes": atoms})

    if rule_id == RULE_IDS[0]:
        _keys(frame, ("tail", "boundary"))
        tail = _atoms(frame["tail"], "tail", minimum=1)
        boundary = _choice(frame["boundary"], ("ibtida", "wasl", "waqf"), "boundary")
        underlying = ["ء", "ا", "ل", *tail]
        if boundary in ("ibtida", "wasl"):
            emit("interrogative_ibdal", ["ء", "ا", "ل", *tail])
            emit("interrogative_tashil", ["ء", "HAMZA_TASHIL", "ل", *tail])
        else:
            unresolved.append("WAQF_IS_NOT_AN_ONSET_MODE")
    elif rule_id == RULE_IDS[1]:
        _keys(frame, ("prefix", "glide", "alif_origin", "suffix"))
        prefix = _atoms(frame["prefix"], "prefix", minimum=1)
        glide = GLIDES[_choice(frame["glide"], GLIDES, "glide")]
        origin = _choice(frame["alif_origin"], ("added", "radical", "unknown"), "alif_origin")
        suffix = _atoms(frame["suffix"], "suffix")
        underlying = [*prefix, "ا", glide, *suffix]
        if origin == "unknown":
            unresolved.append("ALIF_ORIGIN")
        elif origin != "added":
            blocker = "ALIF_IS_NOT_ADDED"
        elif suffix:
            blocker = "GLIDE_IS_NOT_FINAL"
        else:
            emit("hamzate_final", [*prefix, "ا", "ء"])
    elif rule_id == RULE_IDS[2]:
        _keys(frame, ("first", "glide", "last", "verb_medial"))
        first, last = _atom(frame["first"], "first"), _atom(frame["last"], "last")
        glide = GLIDES[_choice(frame["glide"], GLIDES, "glide")]
        state = _choice(frame["verb_medial"], ("changed_to_alif", "retained", "unknown"), "verb_medial")
        underlying = [first, "ا", glide, last]
        if state == "unknown":
            unresolved.append("VERB_MEDIAL_ILLAL")
        elif state != "changed_to_alif":
            blocker = "VERB_MEDIAL_RETAINED"
        else:
            emit("hamzate_medial", [first, "ا", "ء", last])
    elif rule_id == RULE_IDS[3]:
        _keys(frame, ("singular", "singular_long_origin", "plural_template"))
        singular = _atoms(frame["singular"], "singular", minimum=4, feminine=True)
        origin = _choice(frame["singular_long_origin"],
                         ("added_long", "radical_long", "nonlong", "unknown"), "singular_long_origin")
        template = _choice(frame["plural_template"], ("mafail", "mafail_long", "other", "unknown"), "plural_template")
        # Retain the singular-to-plural atom map. No caller target spelling is used.
        core = singular[:-1] if singular[-1] == "ة" else singular
        if len(core) != 4 or any(x == "ة" for x in core):
            _bad("This singular alignment is four atoms, optionally followed by feminine ta")
        underlying = [*core[:2], "ا", core[2], core[3]]
        if template == "unknown" or origin == "unknown":
            unresolved.append("SINGULAR_MADD_OR_TEMPLATE")
        elif template != "mafail":
            blocker = "NOT_MAFAIL_TEMPLATE"
        elif origin != "added_long" or core[2] not in LONGS.values():
            blocker = "THIRD_ATOM_IS_NOT_AN_ADDED_LONG_VOWEL"
        else:
            emit("hamzate_plural", [*core[:2], "ا", "ء", core[3]])
    elif rule_id == RULE_IDS[4]:
        _keys(frame, ("underlying_plural", "plural_template"))
        underlying = _atoms(frame["underlying_plural"], "underlying_plural", minimum=1)
        template = _choice(frame["plural_template"], ("mafail", "mafail_long", "other", "unknown"), "plural_template")
        if template == "unknown":
            unresolved.append("PLURAL_TEMPLATE")
        elif template != "mafail":
            blocker = "NOT_MAFAIL_TEMPLATE"
        elif (len(underlying) != 5 or underlying[1] not in GLIDES.values() or
              underlying[2] != "ا" or underlying[3] not in GLIDES.values()):
            blocker = "NO_TWO_GLIDES_AROUND_MAFAIL_ALIF"
        else:
            emit("hamzate_second_glide", [*underlying[:3], "ء", underlying[4]])
    else:
        _keys(frame, ("root", "profile"))
        underlying = _atoms(frame["root"], "root", minimum=3)
        if len(underlying) != 3:
            _bad("Lexical command root must contain exactly three atoms")
        profile = _choice(frame["profile"], ("named_common", "all_attested"), "profile")
        forms = {("ء", "خ", "ذ"): ["خ", "ذ"],
                 ("ء", "ك", "ل"): ["ك", "ل"],
                 ("ء", "م", "ر"): ["م", "ر"]}
        if tuple(underlying) not in forms:
            unresolved.append("ROOT_OUTSIDE_NAMED_SOURCE_LEXICON")
        else:
            emit("short_command", forms[tuple(underlying)])
            if underlying == ["ء", "ك", "ل"] and profile == "all_attested":
                emit("full_dialect_command", ["ء", "و", "ك", "ل"])
    return underlying, alternatives, blocker, unresolved


def evaluate(rule_id, frame):
    """Apply a named conditional one-step rule; never authorize free text.

    ``frame`` contains a declared morphological analysis, not an acquired one.
    ``source_replayed`` records the rule's provenance, not the input's attestation.
    Hamza is always the unseated atom ء; combining marks and seated hamzas are
    rejected, not silently normalized. Follow-on transformations remain separate.
    """
    foundation.require_foundation('nabt.classical_hamza.evaluate')
    if type(rule_id) is not str or rule_id not in RULE_IDS:
        raise NabtError("UNKNOWN_CLASSICAL_HAMZA_RULE", "Unknown hamza rule", status="DEFER")
    underlying, alternatives, blocker, unresolved = _compute(rule_id, frame)
    sources = _source(rule_id)
    status = "CONDITIONAL_TRANSFORM" if alternatives else ("DEFER" if unresolved else "BLOCKED")
    return {"law_id": LAW_ID, "rule_id": rule_id, "alphabet_id": ALPHABET_ID,
            "status": status, "input_frame": deepcopy(frame), "input_morphophonemes": underlying,
            "alternatives": alternatives, "blocker": blocker, "unresolved": unresolved,
            "premises_established": False, "language_license_granted": False,
            "source_replayed": True, "source_spans": sources,
            "output_layer": "one_step_morphophonemes_not_orthographic_or_acoustic_surface"}


def finite_export_rows():
    """Development conformance controls; not a linguistic-coverage denominator."""
    frames = []
    for boundary in ("ibtida", "wasl", "waqf"):
        frames.append((RULE_IDS[0], {"tail": ["ر", "ج", "ل"], "boundary": boundary}))
    for origin in ("added", "radical", "unknown"):
        for suffix in ([], ["ن"]):
            frames.append((RULE_IDS[1], {"prefix": ["د", "ع"], "glide": "waw",
                "alif_origin": origin, "suffix": suffix}))
    for state in ("changed_to_alif", "retained", "unknown"):
        frames.append((RULE_IDS[2], {"first": "ق", "glide": "waw", "last": "ل", "verb_medial": state}))
    for origin in ("added_long", "radical_long", "nonlong", "unknown"):
        for template in ("mafail", "mafail_long", "other", "unknown"):
            frames.append((RULE_IDS[3], {"singular": ["ص", "ح", "ي", "ف", "ة"],
                "singular_long_origin": origin, "plural_template": template}))
    for template in ("mafail", "mafail_long", "other", "unknown"):
        frames.append((RULE_IDS[4], {"underlying_plural": ["ء", "و", "ا", "و", "ل"], "plural_template": template}))
    for root in (["ء", "خ", "ذ"], ["ء", "ك", "ل"], ["ء", "م", "ر"], ["ء", "س", "ر"]):
        for profile in ("named_common", "all_attested"):
            frames.append((RULE_IDS[5], {"root": root, "profile": profile}))
    rows = []
    for rule_id, frame in frames:
        underlying, alternatives, _, _ = _compute(rule_id, frame)
        rows.append({"rule_id": rule_id, "frame": frame, "input": underlying,
                     "operations": [a["operation"] for a in alternatives],
                     "outputs": [a["morphophonemes"] for a in alternatives]})
    return rows
