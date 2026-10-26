"""Source-bound symbolic onset/pause projections, never an acoustic recognizer.

The finite catalogue contains authored analyses of independently pinned examples.
Unknown catalogue IDs do not reject Arabic. A separate imperative adapter reruns
morphological acquisition and projects only its independently verified onset.
"""
from __future__ import annotations

from copy import deepcopy
from enum import Enum
from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError

LAW_ID = "nabt.phonological-modes.v1"
POLICY_SHA256 = "3cc6781732cdfff3bca8b396c5bea78a72e87c5d89c31ad3bf70b9876578f387"
ALPHABET = "nabt.phonological-segments.v1"
VOWELS = frozenset(("a", "i", "u", "a:", "i:", "u:"))


from nabt import foundation

class Mode(str, Enum):
    IBTIDA = "ibtida"
    WASL = "wasl"
    WAQF = "waqf"


class Profile(str, Enum):
    STANDARD_CORE = "standard_core"
    SIBAWAYHI_OPTIONS = "sibawayhi_attested_options"


def replay_policy():
    """Recheck installed policy bytes and every source span; no warm-cache trust."""
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("phonological_modes_v1.json").read_bytes()
        if sha256(raw).hexdigest() != POLICY_SHA256:
            raise ValueError("Phonological policy changed")
        policy = json.loads(raw)
        sources = {}
        for passage in policy["passages"]:
            key = passage["source_id"]
            if key not in sources:
                sources[key] = directory.joinpath(key + ".txt").read_bytes()
            source = sources[key]
            if (sha256(source).hexdigest() != passage["source_sha256"] or
                    source[passage["start"]:passage["end"]].decode() != passage["raw_text"]):
                raise ValueError("Phonological source changed")
        return policy
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Phonological source replay failed",
                        status="DEFER") from exc


def _modes(start, end, profile):
    if (type(start) not in (str, Mode) or start not in (Mode.IBTIDA, Mode.WASL) or
            type(end) not in (str, Mode) or end not in (Mode.WASL, Mode.WAQF) or
            type(profile) not in (str, Profile) or profile not in tuple(Profile)):
        raise NabtError("INVALID_PHONOLOGICAL_MODE", "Invalid onset, ending, or profile")
    return Mode(start), Mode(end), Profile(profile)


def _suffixes(example, end, profile):
    kind, vowel = example["ending"], example["vowel"]
    if kind == "stable":
        return [((), "unchanged")]
    if end == Mode.WASL:
        if kind == "tanwin":
            return [((vowel, "n"), "tanwin_in_wasl")]
        if kind == "feminine":
            return [(("t", vowel), "feminine_t_in_wasl")]
        return [((vowel,), "vowel_in_wasl")]
    if kind == "tanwin":
        return [(("a:",) if vowel == "a" else (), "tanwin_in_waqf")]
    if kind == "feminine":
        return [(("h",), "feminine_h_in_waqf")]
    if kind == "single":
        return [((vowel, "h"), "single_consonant_ha_sakt")]
    if kind == "weak" and profile == Profile.SIBAWAYHI_OPTIONS:
        return [((), "weak_pause_sukun"), ((vowel, "h"), "weak_pause_ha_sakt")]
    return [((), "final_sukun")]


def realize(example_id, *, start=Mode.IBTIDA, end=Mode.WASL,
            profile=Profile.STANDARD_CORE, following_id=None):
    """Project a pinned source example under explicit independent boundaries.

    A following example licenses only the recorded kasra contact cases. More
    general sandhi returns UNKNOWN, never silently returning an unverified form.
    The spelling is preserved even when its symbolic realization loses a vowel.
    """
    foundation.require_foundation('nabt.phonological_modes.realize')
    start, end, profile = _modes(start, end, profile)
    if type(example_id) is not str or (following_id is not None and type(following_id) is not str):
        raise NabtError("INVALID_PHONOLOGICAL_INPUT", "Example IDs must be strings")
    if following_id is not None and end != Mode.WASL:
        raise NabtError("INVALID_PHONOLOGICAL_BOUNDARY", "A connected follower requires wasl")
    policy = replay_policy()
    catalog = {row["example_id"]: row for row in policy["examples"]}
    if example_id not in catalog or (following_id is not None and following_id not in catalog):
        return {"status": "UNKNOWN", "reason": "outside_source_example_catalog", "law_id": LAW_ID}
    example = catalog[example_id]
    follower = catalog.get(following_id)
    # This version deliberately does not infer all sandhi from two raw strings.
    contact = follower is not None
    if contact and not (example["licenses_contact_kasra"] and
                        follower["wasl_vowel"] is not None and
                        len(follower["body"]) >= 2 and
                        all(p not in VOWELS for p in follower["body"][:2])):
        return {"status": "UNKNOWN", "reason": "outside_licensed_contact_subset", "law_id": LAW_ID}
    onset = ("ʔ", example["wasl_vowel"]) if start == Mode.IBTIDA and example["wasl_vowel"] else ()
    variants = []
    for suffix, rule in _suffixes(example, end, profile):
        phonemes = onset + tuple(example["body"]) + suffix + (("i",) if contact else ())
        variants.append({"segments": list(phonemes), "rule": rule,
                         "contact_rule": "transient_contact_kasra" if contact else None})
    return {"status": "CONDITIONAL_PROJECTION", "law_id": LAW_ID,
            "alphabet_version": ALPHABET, "policy_sha256": POLICY_SHA256,
            "example_id": example_id, "start": start.value, "end": end.value,
            "profile": profile.value, "written_form": example["written_form"],
            "source_written_form": example["source_written_form"],
            "following_id": following_id, "alternatives": variants,
            "deleted_radicals": deepcopy(example["deleted_radicals"]),
            "source_passages": deepcopy(example["passage_ids"]),
            "analysis_status": "authored_source_bound", "acoustic_validation": False,
            "complete_for_arabic": False}


def realize_imperative_onset(surface, *, lexical_model, profile_id,
                             start=Mode.IBTIDA):
    """Reusable onset-only bridge, rederived from the supplied acquired model.

    No caller candidate or label grants authority. The morphology subsystem is
    rerun. The remainder stays explicitly in its observed grapheme alphabet;
    this bridge does not claim to phonemize plural silent alif or pausal endings.
    """
    foundation.require_foundation('nabt.phonological_modes.realize_imperative_onset')
    start, _, _ = _modes(start, Mode.WASL, Profile.STANDARD_CORE)
    if type(surface) is not str or type(profile_id) is not str:
        raise NabtError("INVALID_PHONOLOGICAL_INPUT", "Surface and profile must be strings")
    replay_policy()
    from .person_evidence import person_candidates
    candidates = person_candidates(surface, lexical_model=lexical_model)
    accepted_laws = {"nabt.productive-sound-imperative.v1", "nabt.sound-imperative-paradigm.v1"}
    rows = [r for r in candidates if r.get("aspect") == "IMPV" and
            r.get("profile_id") == profile_id and
            r.get("productive_derivation", {}).get("law_id") in accepted_laws]
    if not rows:
        return {"status": "UNKNOWN", "reason": "no_rederived_imperative", "law_id": LAW_ID}
    marks = {"ِ": "i", "ُ": "u"}
    if len(surface) < 3 or surface[0] != "ا" or surface[1] not in marks:
        return {"status": "UNKNOWN", "reason": "outside_verified_wasl_encoding", "law_id": LAW_ID}
    vowel = marks[surface[1]]
    return {"status": "CONDITIONAL_PROJECTION", "law_id": LAW_ID,
            "policy_sha256": POLICY_SHA256, "written_form": surface,
            "start": start.value, "end": "unprojected", "profile_id": profile_id,
            "surface": {"onset_segments": ["ʔ", vowel] if start == Mode.IBTIDA else [],
                        "observed_vocalized_remainder": surface[2:],
                        "remainder_alphabet": "observed_arabic_graphemes"},
            "morphological_witnesses": [deepcopy(r["productive_derivation"]) for r in rows],
            "source_passages": ["hamzat_wasl"], "acoustic_validation": False,
            "complete_for_arabic": False}
