"""Source-relative sound imperative subject suffixes, law v1.

The lexical premise comes from the conservative complete imperfect bridge.
The output is a morphological possibility, never an acquired target attestation,
object capacity, resolved addressee, or sound measurement. Dual genders remain
separate readings even though they have exactly the same written shape.
"""
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json

from .corpus_evidence import lookup_clusters, _render
from .errors import NabtError
from .productive_forms import sound_imperative

LAW_ID = "nabt.sound-imperative-paradigm.v1"
POLICY_SHA256 = "1f0a8baec82a0a7cd37217278e3258d12cec4e18b1408b332d32b7eecb95310d"


def paradigm_rows():
    """Complete finite interpretation compared to the Lean export by the gate."""
    return [
        {"profile": "2FS", "gender": 1, "number": 0, "final": "ِ", "suffix": "ي", "kind": "subject_pronoun"},
        {"profile": "2MD", "gender": 0, "number": 1, "final": "َ", "suffix": "ا", "kind": "subject_pronoun"},
        {"profile": "2FD", "gender": 1, "number": 1, "final": "َ", "suffix": "ا", "kind": "subject_pronoun"},
        {"profile": "2MP", "gender": 0, "number": 2, "final": "ُ", "suffix": "وا", "kind": "subject_pronoun"},
        {"profile": "2FP", "gender": 1, "number": 2, "final": "ْ", "suffix": "نَ", "kind": "feminine_subject"},
    ]


def replay_policy():
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("imperative_paradigm_v1.json").read_bytes()
        if sha256(raw).hexdigest() != POLICY_SHA256:
            raise ValueError("Imperative paradigm policy changed")
        policy = json.loads(raw)
        if policy["law_id"] != LAW_ID:
            raise ValueError("Imperative paradigm law changed")
        for p in policy["passages"]:
            source = directory.joinpath(p["source_id"] + ".txt").read_bytes()
            span = source[p["start"]:p["end"]]
            if (sha256(source).hexdigest() != p["source_sha256"] or
                    sha256(span).hexdigest() != p["span_sha256"] or
                    span.decode() != p["raw_text"]):
                raise ValueError("Imperative paradigm source changed")
        return policy
    except (OSError, ValueError, UnicodeError, KeyError, TypeError) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Imperative paradigm source replay failed", status="DEFER") from exc


def sound_imperative_paradigm(candidate):
    """Additional subject profiles only; the old 2MS law keeps its identity."""
    base = sound_imperative(candidate)
    if base is None:
        return []
    result = []
    for row in paradigm_rows():
        # Radical nun plus feminine-subject nun needs a separately licensed
        # idgham surface and two roles on one shadda cluster. Do not invent it.
        if row["profile"] == "2FP" and base["root"].endswith("ن"):
            continue
        derived = deepcopy(base)
        shape = lookup_clusters(base["form"])
        shape[-1][1] = {row["final"]}
        form = _render(shape) + row["suffix"]
        witness = deepcopy(base["productive_derivation"])
        witness.update(law_id=LAW_ID, policy_sha256=POLICY_SHA256,
                       base_law_id=base["productive_derivation"]["law_id"],
                       base_policy_sha256=base["productive_derivation"]["policy_sha256"],
                       singular_imperative=base["form"], generated_form=form,
                       target_profile=row["profile"], target_attested=False,
                       target_role_labels_used=False)
        count = len(lookup_clusters(form))
        derived.update(form=form, host_form=form, host_end_cluster=count,
                       profile_id=row["profile"],
                       person_profile={"person": 2, "gender": row["gender"], "number": row["number"]},
                       variant="sound_imperative_paradigm_from_imperfect",
                       host_variant="sound_imperative_paradigm_from_imperfect",
                       productive_derivation=witness,
                       parts=[{"kind": "verbal_stem", "start_cluster": 0, "end_cluster": 4},
                              {"kind": row["kind"], "start_cluster": 4, "end_cluster": 5}])
        if row["profile"] == "2MP":
            derived["parts"].append({"kind": "separator_alif", "start_cluster": 5, "end_cluster": 6})
        if row["profile"] == "2FP":
            derived["nun_readings"].append({"kind": "feminine_subject", "cluster_index": 4,
                                            "realization": "present", "status": "SOURCE_BOUND_PRODUCTIVE_PARADIGM"})
        else:
            derived["nun_readings"].append({"kind": "five_verb_raf", "cluster_index": None,
                                            "realization": "deleted", "status": "IMPERATIVE_WITHOUT_INFLECTION_NUN"})
        derived["rule_ids"].append(LAW_ID)
        result.append(derived)
    return result
