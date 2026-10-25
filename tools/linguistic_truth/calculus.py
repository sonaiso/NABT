"""Finite adapter of Nabt.LinguisticTruth over explicit supplied premises.

This module does not authenticate source bytes or acquire meanings. The public
runtime performs those steps before constructing its request. Signed evidence
uses the existing QualifiedInference adapter with an injective local symbol
table, never a hash or a caller's Boolean classification flag.
"""
from __future__ import annotations

from copy import deepcopy
import json

from tools.mantuq_inference import guard_verdict

LAW_ID = "nabt.linguistic-truth.v1"
AUTHORITY = "CONDITIONAL_SUPPLIED_LEDGER"


def _object(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise ValueError("invalid exact object fields: " + ", ".join(names))


def _text(value):
    if type(value) is not str:
        raise ValueError("text field must be a string")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ValueError("invalid Unicode scalar") from exc
    if size > 16384:
        raise ValueError("text field exceeds native 16384-byte limit")


def _nat(value):
    if type(value) is not int or value < 0 or len(str(value)) > 256:
        raise ValueError("natural field requires an unsigned integer of at most 256 digits")


def _array(value, limit, validate):
    if type(value) is not list or len(value) > limit:
        raise ValueError("array exceeds native bound or is not a list")
    for item in value:
        validate(item)


def _citation(value):
    _object(value, ("work", "revision", "source_sha256", "start_byte", "end_byte", "quotation"))
    for key in ("work", "revision", "source_sha256", "quotation"):
        _text(value[key])
    for key in ("start_byte", "end_byte"):
        _nat(value[key])


def _frame(value):
    _object(value, ("occurrence", "expression", "convention"))
    _text(value["expression"])
    _text(value["convention"])
    occurrence = value["occurrence"]
    _object(occurrence, ("source", "revision", "raw", "start_byte", "end_byte", "referent", "time", "context"))
    for key in ("source", "revision", "raw", "referent", "time", "context"):
        _text(occurrence[key])
    for key in ("start_byte", "end_byte"):
        _nat(occurrence[key])


def _designation(value):
    _object(value, ("id", "expression", "sense", "convention", "origin", "citation"))
    for key in ("id", "expression", "sense", "convention", "origin"):
        _text(value[key])
    if value["origin"] not in ("original", "transferred"):
        raise ValueError("unknown designation origin")
    _citation(value["citation"])


def _relation(value):
    _object(value, ("designation", "target_sense", "kind", "citation"))
    _designation(value["designation"])
    _text(value["target_sense"])
    _text(value["kind"])
    _citation(value["citation"])


def _candidate(value):
    _object(value, ("designation", "intended_sense", "relation"))
    _designation(value["designation"])
    _text(value["intended_sense"])
    if value["relation"] is not None:
        _relation(value["relation"])


def _judgment(value):
    if type(value) is not dict:
        raise ValueError("judgment must be an object")
    kind = value.get("kind")
    if kind == "established":
        _object(value, ("kind", "designation"))
        _designation(value["designation"])
    elif kind == "used":
        _object(value, ("kind", "frame", "sense"))
        _frame(value["frame"])
        _text(value["sense"])
    elif kind == "related":
        _object(value, ("kind", "relation"))
        _relation(value["relation"])
    elif kind == "excludes":
        _object(value, ("kind", "frame", "designation"))
        _frame(value["frame"])
        _designation(value["designation"])
    else:
        raise ValueError("unknown judgment kind")


def _atom(value):
    _object(value, ("value", "positive", "scope"))
    _judgment(value["value"])
    if type(value["positive"]) is not bool:
        raise ValueError("support polarity must be Boolean")
    _text(value["scope"])


def canonical_json(value):
    """Exact JSON identity: sorted keys and escaped strings, without hashing."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _matches(frame, designation):
    return (designation["expression"] == frame["expression"]
            and designation["convention"] == frame["convention"])


def _related(relation):
    return relation["target_sense"] != relation["designation"]["sense"] and relation["kind"] != ""


def enumerate_candidates(frame, designations, relations):
    """Preserve exact ledger order, duplicates, and every compatible alternative."""
    _frame(frame)
    _array(designations, 128, _designation)
    _array(relations, 128, _relation)
    candidates = [dict(designation=d, intended_sense=d["sense"], relation=None)
                  for d in designations if _matches(frame, d)]
    candidates.extend(dict(designation=r["designation"], intended_sense=r["target_sense"], relation=r)
                      for r in relations if r["designation"] in designations
                      and _matches(frame, r["designation"]) and _related(r))
    return deepcopy(candidates)


def candidate_kind(frame, candidate):
    """Return a structural possibility, not a supported semantic conclusion."""
    _frame(frame)
    _candidate(candidate)
    designation = candidate["designation"]
    if not _matches(frame, designation):
        return None
    relation = candidate["relation"]
    if relation is None:
        return ("literal_" + designation["origin"]
                if candidate["intended_sense"] == designation["sense"] else None)
    return ("figurative" if relation["designation"] == designation
            and relation["target_sense"] == candidate["intended_sense"] and _related(relation) else None)


def guard_requirements(frame, candidate):
    """Typed obligations lowered to the existing signed-premise checker."""
    _frame(frame)
    _candidate(candidate)
    values = [{"kind": "established", "designation": candidate["designation"]},
              {"kind": "used", "frame": frame, "sense": candidate["intended_sense"]}]
    if candidate["relation"] is not None:
        values.extend([{"kind": "related", "relation": candidate["relation"]},
                       {"kind": "excludes", "frame": frame, "designation": candidate["designation"]}])
    return deepcopy([{"role": "premise", "atom": {"value": value, "positive": True,
                     "scope": frame["occurrence"]["context"]}} for value in values])


def _encode_symbols(requirements, known):
    # Canonical values receive distinct local Nat identities. Repeated values
    # receive the same identity; no digest, delimiter joining, truncation, or
    # Python hash can merge different structured judgments.
    values = {canonical_json(a["value"]) for a in known}
    values.update(canonical_json(r["atom"]["value"]) for r in requirements)
    symbols = {value: index for index, value in enumerate(sorted(values))}

    def atom(value):
        return {"value": symbols[canonical_json(value["value"])],
                "positive": value["positive"], "scope": value["scope"]}

    return ([{"role": requirement["role"], "atom": atom(requirement["atom"])}
             for requirement in requirements], [atom(value) for value in known])


def assess_candidate(frame, candidate, known):
    _array(known, 1024, _atom)
    if candidate_kind(frame, candidate) is None:
        return "INVALID_PROFILE"
    requirements, encoded_known = _encode_symbols(guard_requirements(frame, candidate), known)
    return guard_verdict("direct", requirements, encoded_known)


def evaluate_request(request):
    """Pure full-response postcondition for a valid native JSONL request.

    This adapter neither calls Lean nor authenticates the supplied ledger. The
    conformance checker compares it against an independently executed Lean
    exporter. Invalid protocol inputs raise ValueError, never a semantic verdict.
    """
    _object(request, ("frame", "designations", "relations", "known", "proposed", "budget"))
    frame, designations, relations = request["frame"], request["designations"], request["relations"]
    _frame(frame)
    _array(designations, 128, _designation)
    _array(relations, 128, _relation)
    _array(request["known"], 1024, _atom)
    if request["proposed"] is not None:
        _array(request["proposed"], 256, _candidate)
    _nat(request["budget"])
    if request["budget"] > 4096:
        raise ValueError("ledger budget exceeds native 4096-entry bound")
    if len(canonical_json(request).encode("utf-8")) > 1048576:
        raise ValueError("request exceeds native one-MiB bound")
    enough = len(designations) + len(relations) <= request["budget"]
    candidates = enumerate_candidates(frame, designations, relations) if enough else []
    return {"status": "CHECKED" if enough else "RESOURCE_EXHAUSTED",
            "law_id": LAW_ID, "authority": AUTHORITY,
            "all_arabic_senses_enumerated": False, "world_truth_asserted": False,
            "complete_proposal": (request["proposed"] == candidates
                                  if enough and request["proposed"] is not None else None),
            "rows": [{"candidate": candidate, "kind": candidate_kind(frame, candidate),
                      "verdict": assess_candidate(frame, candidate, request["known"])}
                     for candidate in candidates]}
