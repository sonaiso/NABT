"""Checked conditional reference and qualified discourse projection law.

No function discovers a referent, force, grammatical relation or external
truth. Callers acquire and retain the witnesses consumed by these finite
tables. An unspecified feature is a nonconstraint only when the reader omits
that axis; an explicit constraint compared with an unknown feature stays
possible. It cannot silently eliminate an otherwise surviving competitor.
"""

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError, natural

LAW_ID = "nabt.discourse-evidence.v1"
EXPECTED_TABLE_SHA256 = "30d990bf93aa436d9452e5a0a4172349727c9e5bb2c6fd1491e53d518b546325"
EXPECTED_POLICY_SHA256 = "584dce90517121ba5e1fad8015f50e14b1adad437c6af879753038703222b3b7"
COMPATIBILITIES = ("possible", "confirmed", "conflict")
REFERENCE_ORIGINS = ("named", "antecedent", "speaker", "addressee", "deictic", "relative_return")
FORCES = ("ASSERT", "QUESTION", "COMMAND", "PROHIBITION", "WISH", "HOPE", "VOCATIVE", "AMBIGUOUS", "QUOTED")
POLARITIES = ("positive", "negative")
CONNECTORS = ("AND", "OR", "XOR", "IMPLIES")
REFERENCE_BITS = ("origin_licensed", "identity_bound", "source_supported", "scope_allowed",
                  "quote_allowed", "order_licensed", "return_licensed")
ASSERTION_BITS = ("licensed_syntax", "scope_complete", "references_complete", "qualifiers_preserved",
                  "nonquoted", "source_supported")
CLAIM_FIELDS = ("predicate", "arguments", "polarity", "tense", "time", "place", "restriction")
CAUSAL_BITS = ("relation_licensed", "source_supported", "scope_complete", "endpoints_resolved")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Repeated object key")
        result[key] = value
    return result


@lru_cache(maxsize=1)
def _table():
    try:
        raw = files("nabt").joinpath("data/discourse_evidence.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
            raise ValueError("Discourse table digest differs")
        table = json.loads(raw, object_pairs_hook=_unique_object)
        if table["law_id"] != LAW_ID or type(table["schema_version"]) is not int or table["schema_version"] != 1:
            raise ValueError("Discourse law identity differs")
        for key, expected in (("compatibilities", COMPATIBILITIES), ("reference_origins", REFERENCE_ORIGINS),
                              ("forces", FORCES), ("polarities", POLARITIES), ("connectors", CONNECTORS),
                              ("reference_bits", REFERENCE_BITS), ("assertion_bits", ASSERTION_BITS),
                              ("claim_fields", CLAIM_FIELDS), ("causal_bits", CAUSAL_BITS)):
            if table[key] != list(expected):
                raise ValueError("Discourse named domain differs: " + key)
        for key, size in (("role_rows", 5), ("feature_rows", 25), ("combine_rows", 9), ("reference_rows", 2304),
                          ("selection_rows", 12), ("assertion_rows", 576), ("negation_rows", 2),
                          ("truth_rows", 16), ("coordination_rows", 8),
                          ("claim_projection_rows", 128), ("causal_rows", 16)):
            if type(table[key]) is not list or len(table[key]) != size:
                raise ValueError("Discourse finite inventory differs: " + key)
        return table
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed discourse law cannot be replayed",
                        status="DEFER") from error


def installed_registry():
    """A copy of the digest-checked installed law; never the mutable cache."""
    return deepcopy(_table())


@lru_cache(maxsize=1)
def _indexes():
    table = _table()
    return {
        "roles": {r["label"]: r["case"] for r in table["role_rows"]},
        "features": {(r["left"], r["right"]): r["status"] for r in table["feature_rows"]},
        "combine": {(r["left"], r["right"]): r["status"] for r in table["combine_rows"]},
        "reference": {(r["origin"], r["compatibility"], r["mask"]): r["allowed"] for r in table["reference_rows"]},
        "selection": {(r["count_class"], r["closed_scope"], r["all_confirmed"]): r["status"] for r in table["selection_rows"]},
        "assertion": {(r["force"], r["mask"]): r["allowed"] for r in table["assertion_rows"]},
        "negation": {r["input"]: r["output"] for r in table["negation_rows"]},
        "truth": {(r["operator"], r["left"], r["right"]): r["value"] for r in table["truth_rows"]},
        "coordination": {(r["operator"], r["polarity"]): r["project_branches"] for r in table["coordination_rows"]},
        "projection": {r["mask"]: r["allowed"] for r in table["claim_projection_rows"]},
        "causal": {r["mask"]: r["allowed"] for r in table["causal_rows"]},
    }


def _label(value, allowed, name):
    if type(value) is not str or value not in allowed:
        raise NabtError("INVALID_DISCOURSE_DOMAIN", name + " must be an installed label")
    return value


def _boolean(value, name):
    if type(value) is not bool:
        raise NabtError("INVALID_DISCOURSE_BOOLEAN", name + " must be an actual Boolean")
    return value


def _mask(names, values):
    return sum(int(_boolean(value, name)) << i for i, (name, value) in enumerate(zip(names, values)))


def feature_compatibility(left, right):
    for name, value in (("left_feature", left), ("right_feature", right)):
        if value is not None:
            natural(value, name, maximum=3)
    return _indexes()["features"][(left, right)]


def role_case(label):
    """Required case of a supplied role; this cannot acquire an actual role."""
    _label(label, ("nominal_subject", "nominal_predicate", "time_adverb", "place_adverb", "imperfect_indicative"), "conditional_role")
    return _indexes()["roles"][label]


def combine_compatibility(states):
    """Combine explicit constraints; an empty collection is vacuously confirmed.

    A missing constraint, such as the unspecified gender of a speaker pronoun,
    is omitted by its reader. A missing entity feature for an explicit
    constraint must instead contribute ``possible``.
    """
    if type(states) not in (list, tuple) or len(states) > 32:
        raise NabtError("INVALID_DISCOURSE_FEATURES", "Use at most 32 explicit feature constraints")
    result = "confirmed"
    for state in states:
        _label(state, COMPATIBILITIES, "compatibility")
        result = _indexes()["combine"][(result, state)]
    return result


def reference_allowed(origin, compatibility, *, origin_licensed=False, identity_bound=False,
                      source_supported=False, scope_allowed=False, quote_allowed=False,
                      order_licensed=False, return_licensed=False):
    """Admission of a possible reference, not unique antecedent selection.

    A named/speaker/addressee/deictic identity can have an independent explicit
    context witness despite unknown nonconflicting traits. Textual antecedent
    selection separately needs the closed-universe/singleton gate below.
    Order means an independently licensed textual or syntactic-order relation;
    this law does not impose universal left-to-right antecedence.
    """
    _label(origin, REFERENCE_ORIGINS, "reference_origin")
    _label(compatibility, COMPATIBILITIES, "compatibility")
    mask = _mask(REFERENCE_BITS, (origin_licensed, identity_bound, source_supported, scope_allowed,
                                  quote_allowed, order_licensed, return_licensed))
    return _indexes()["reference"][(origin, compatibility, mask)]


def selection_status(candidate_count, *, closed_scope, all_confirmed):
    natural(candidate_count, "distinct_candidate_count", maximum=4096)
    _boolean(closed_scope, "closed_scope")
    _boolean(all_confirmed, "all_confirmed")
    return _indexes()["selection"][(min(candidate_count, 2), closed_scope, all_confirmed)]


def assertion_allowed(force, *, licensed_syntax=False, scope_complete=False, references_complete=False,
                      qualifiers_preserved=False, nonquoted=False, source_supported=False):
    _label(force, FORCES, "force")
    mask = _mask(ASSERTION_BITS, (licensed_syntax, scope_complete, references_complete,
                                  qualifiers_preserved, nonquoted, source_supported))
    return _indexes()["assertion"][(force, mask)]


def negate_polarity(polarity):
    return _indexes()["negation"][_label(polarity, POLARITIES, "polarity")]


def connective_value(operator, left, right):
    """Truth-functional computation on supplied valuations, never a causal test."""
    _label(operator, CONNECTORS, "connector")
    return _indexes()["truth"][(operator, _boolean(left, "left"), _boolean(right, "right"))]


def coordination_projection(operator, polarity):
    _label(operator, CONNECTORS, "connector")
    _label(polarity, POLARITIES, "polarity")
    return _indexes()["coordination"][(operator, polarity)]


def claim_projection_allowed(*, predicate_equal=False, arguments_equal=False, polarity_equal=False,
                             tense_equal=False, time_equal=False, place_equal=False, restriction_equal=False):
    """All qualified claim fields must match; omitted qualifiers are not erased."""
    mask = _mask(CLAIM_FIELDS, (predicate_equal, arguments_equal, polarity_equal, tense_equal,
                                time_equal, place_equal, restriction_equal))
    return _indexes()["projection"][mask]


def causal_allowed(*, relation_licensed=False, source_supported=False, scope_complete=False,
                   endpoints_resolved=False):
    mask = _mask(CAUSAL_BITS, (relation_licensed, source_supported, scope_complete, endpoints_resolved))
    return _indexes()["causal"][mask]


def replay_discourse_policy():
    """Replay exact primary grammar windows; they do not certify a new parse."""
    from .word_reader import replay_policy
    base = replay_policy()
    try:
        directory = files("nabt").joinpath("data/source_evidence")
        raw = directory.joinpath("discourse_policy.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_POLICY_SHA256:
            raise ValueError("Discourse policy digest differs")
        policy = json.loads(raw, object_pairs_hook=_unique_object)
        if policy["policy_id"] != "nabt.discourse-grammar-sources.v2" or policy["schema_version"] != 1:
            raise ValueError("Discourse grammar identity differs")
        sources, rules = {}, {}
        for passage in policy["passages"]:
            source_id = passage["source_id"]
            if source_id not in base["sources"] or passage["rule"] in rules:
                raise ValueError("Unknown source or repeated rule identity")
            if source_id not in sources:
                sources[source_id] = directory.joinpath(source_id + ".txt").read_bytes()
            original = sources[source_id]
            start, end = passage["start"], passage["end"]
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(original):
                raise ValueError("Invalid source byte span")
            excerpt = original[start:end]
            if (sha256(original).hexdigest() != passage["source_sha256"] or
                    sha256(excerpt).hexdigest() != passage["span_sha256"] or
                    excerpt.decode("utf-8") != passage["raw_text"]):
                raise ValueError("Discourse source passage differs")
            rules[passage["rule"]] = {key: passage[key] for key in
                                      ("source_id", "start", "end", "span_sha256", "line_start", "line_end")}
        return {"policy_id": policy["policy_id"], "policy_sha256": EXPECTED_POLICY_SHA256,
                "rules": rules, "scope": policy["scope"]}
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Discourse grammar sources cannot be replayed",
                        status="DEFER") from error
