"""Conditional morphology algebra over source-qualified, four-state evidence.

These operations are not a spelling classifier. The reader binds the supplied
traits to source clauses. The native Lean export fixes the finite functions;
the existing named-obligation engine computes the missing positive witnesses.
"""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError, natural
from .obligations import (Atom, Proposition, PropositionRegistry, all_of, any_of,
                          evaluate_obligations)

LAW_ID = "nabt.morphology.v1"
EVIDENCE_DOMAIN = "nabt.morphology.evidence-base4.v1"
EXPECTED_TABLE_SHA256 = "643abb2ec66ca0c153e840b2f59a0a75b7af4344a476db7e77d29171487f162f"
CAUSE_TRAITS = ("alam", "wasf", "tanithAlif", "muntaha", "falan", "afal",
                "adl", "tarkib", "tanith", "ajamiOver3", "waznFil")
CONSTRUCTIONS = ("built", "inflected")
TENSES = ("past", "imperfect", "imperative")
NUNS = ("none", "direct_emphatic", "separated_emphatic", "feminine_plural")
EVIDENCE = ("unknown", "affirmed", "denied", "conflict")


@lru_cache(maxsize=1)
def _table(raw):
    if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Morphology table differs from its pin", status="DEFER")
    return json.loads(raw)


def installed_table():
    # Do not return a mutable authority object from the cache.
    try:
        return json.loads(json.dumps(_table(files("nabt").joinpath("data/morphology.json").read_bytes())))
    except OSError as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Morphology table is unavailable", status="DEFER") from error


def evidence_number(states: tuple[int, ...]) -> int:
    """Only a fixed, caller-declared schema gives the digits their meanings."""
    if type(states) is not tuple or len(states) > 32:
        raise NabtError("INVALID_MORPHOLOGY_EVIDENCE", "Use at most 32 four-state evidence digits")
    for state in states:
        natural(state, "evidence_state", maximum=3)
    return sum(state << (2 * i) for i, state in enumerate(states))


def decode_evidence(number: int, width: int) -> tuple[int, ...]:
    natural(width, "evidence_width", maximum=32)
    natural(number, "evidence_number", maximum=(1 << (2 * width)) - 1)
    return tuple((number >> (2 * i)) & 3 for i in range(width))


def possible_bools(state: int) -> tuple[bool, ...]:
    natural(state, "evidence_state", maximum=3)
    return ((False, True), (True,), (False,), ())[state]


def cause_candidates(states: tuple[int, ...]) -> tuple[bool, ...]:
    if type(states) is not tuple or len(states) != len(CAUSE_TRAITS):
        raise NabtError("INVALID_CAUSE_EVIDENCE", "Cause evidence uses the complete fixed 11-trait schema")
    evidence_number(states)
    if 3 in states:
        return ()
    positive = sum(1 << i for i, state in enumerate(states) if state == 1)
    negative = sum(1 << i for i, state in enumerate(states) if state == 2)
    rows = installed_table()["cause_rows"]
    return tuple(sorted({row["diptote"] for row in rows
                         if row["mask"] & positive == positive and not row["mask"] & negative}))


def named_residual(names: tuple[str, ...], states: tuple[int, ...], *, identity: dict,
                   formula_kind: str) -> dict:
    """Use NABT's already-proved positive-formula engine, with full identities.

    The source reader, not a caller-supplied numeric field, owns this binding.
    The result licenses a conditional formula only; source truth is separate.
    """
    if type(names) is not tuple or type(states) is not tuple or len(names) != len(states):
        raise NabtError("INVALID_MORPHOLOGY_RESIDUAL", "Names and evidence must have the same finite width")
    evidence_number(states)
    propositions = {name: Proposition(name, identity["source"], identity["occurrence"],
                                      identity["reading"], identity["context"],
                                      LAW_ID + ":" + name, identity["policy"]) for name in names}
    registry = PropositionRegistry(propositions.values())
    atom = lambda name: Atom(propositions[name])
    if formula_kind == "cause" and names == CAUSE_TRAITS:
        formula = any_of(atom("tanithAlif"), atom("muntaha"),
                         all_of(atom("wasf"), any_of(atom("falan"), atom("afal"), atom("adl"))),
                         all_of(atom("alam"), any_of(*(atom(n) for n in
                             ("tarkib", "falan", "tanith", "ajamiOver3", "waznFil", "adl")))))
    elif formula_kind == "genitive" and names == ("al", "idhafa"):
        formula = any_of(atom("al"), atom("idhafa"))
    else:
        raise NabtError("INVALID_MORPHOLOGY_RESIDUAL", "Unknown installed formula schema")
    positive = registry.mask(propositions[n] for n, s in zip(names, states) if s & 1)
    negative = registry.mask(propositions[n] for n, s in zip(names, states) if s & 2)
    result = evaluate_obligations(formula, registry, positive, negative,
                                  allowed_contexts=(identity["context"],))
    return {"status": result.status,
            "registry": registry.as_dict(),
            "positive_mask": positive, "negative_mask": negative,
            "minimal_plans": [[p.name for p in plan.propositions] for plan in result.minimal_plans],
            "conflicts": [p.name for p in result.conflicts],
            "scope": "SUFFICIENT_POSITIVE_COMPLETIONS_OF_THIS_INSTALLED_FORMULA"}
