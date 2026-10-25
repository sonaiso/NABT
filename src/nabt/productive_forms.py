"""Source-bound productive forms, separate from attestation and world claims.

Only a fully observed sound Form-I imperfect licenses this imperative bridge.
Weak/hamzated/geminate roots, passive voice, affixes and missing vowels remain
outside its domain. No caller-provided label or generated training row is used.
"""
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json

from .corpus_evidence import lookup_clusters, _render
from .errors import NabtError

LAW_ID = "nabt.productive-sound-imperative.v1"
TABLE_SHA256 = '9bb8ba5742b7e9521d3d7a9ee54c6ef1305cd54e1c8fdae0d1d245dd088b3e23'
POLICY_SHA256 = "faf134dabd4ce9d3718274c04660c1c7a9532d6c6f6a1072f2c1af67978e2003"


def installed_shapes():
    raw = files("nabt").joinpath("data/productive_forms.json").read_bytes()
    if sha256(raw).hexdigest() != TABLE_SHA256:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Productive Lean export changed", status="DEFER")
    return json.loads(raw)


def replay_policy():
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("productive_forms_v1.json").read_bytes()
        if sha256(raw).hexdigest() != POLICY_SHA256:
            raise ValueError("Productive policy changed")
        installed_shapes()
        policy = json.loads(raw)
        for passage in policy["passages"]:
            source = directory.joinpath(passage["source_id"] + ".txt").read_bytes()
            if (sha256(source).hexdigest() != passage["source_sha256"] or
                    source[passage["start"]:passage["end"]].decode() != passage["raw_text"]):
                raise ValueError("Productive source changed")
        return policy
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Productive source replay failed", status="DEFER") from exc


def sound_imperative(candidate):
    """Project only 2MS, retaining the source profile as a distinct premise."""
    c = candidate
    shape = lookup_clusters(c["form"])
    root = c.get("root") or ""
    if (c.get("kind") != "verb" or c.get("aspect") != "IMPF" or
            c.get("voice") != "active" or c.get("family") != "plain" or
            c.get("variant") != "attested" or c.get("attached_pronouns") or
            c.get("profile_id") != "2MS" or not c.get("supports") or
            not c.get("lemma_bw") or len(root) != 3 or len(set(root)) != 3 or
            any(ch in "اويءأإآؤئىة" for ch in root) or not shape or len(shape) != 4 or
            shape[0][0] != "ت" or shape[0][1] != {"َ"} or
            "".join(x[0] for x in shape[1:]) != root or shape[1][1] != {"ْ"} or
            shape[2][1] not in ({"َ"}, {"ِ"}, {"ُ"}) or shape[3][1] != {"ُ"}):
        return None
    result = deepcopy(c)
    rule = next(r for r in installed_shapes()["imperative"] if {r["medial"]} == shape[2][1])
    shape[0][0], shape[0][1] = "ا", {rule["initial"]}
    shape[3][1] = {rule["final"]}
    form = _render(shape)
    witness = {"law_id": LAW_ID, "policy_sha256": POLICY_SHA256,
               "source_form": c["base_form"] or c["form"],
               "second_person_imperfect": c["form"], "generated_form": form,
               "root": root, "source_profile": c["source_person_code"],
               "source_lexical_id": c.get("source_lexical_id"),
               "source_support_ids": sorted({s["record_id"] for s in c["supports"]}),
               "target_attested": False, "target_role_labels_used": False}
    result.update(form=form, host_form=form, aspect="IMPV", form_kind="imperative",
                  construction="built", class_candidates=[], possible_cases=[],
                  family=None, variant="sound_imperative_from_imperfect",
                  host_variant="sound_imperative_from_imperfect", mutable_clusters=[],
                  parts=[{"kind": "verbal_stem", "start_cluster": 0, "end_cluster": 4}],
                  nun_readings=[deepcopy(n) for n in c.get("nun_readings", []) if n["kind"] == "radical"],
                  valency_witnesses=[], productive_derivation=witness)
    result["rule_ids"] += [LAW_ID]
    return result
