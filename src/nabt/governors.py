"""The finite governor equations transferred from Mashru and checked in Lean.

These functions check case assignments, not lexical recognition, referents,
speech force, or truth. A label lookup preserves homonyms. Supplying a case
or a number is never evidence that a source has that grammatical reading.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
from types import MappingProxyType
from typing import Mapping

from .errors import NabtError, natural

LAW_ID = "nabt.governors.v1"
ROLE_MARK_DOMAIN = "nabt.governors.role-mark.v1"
EXPECTED_TABLE_SHA256 = "708eebc31f9600fded7a7dd33e89d77170c451c1fe2779740178b52fe50382e0"
ROLE_CATEGORIES = MappingProxyType({0: "noun", 1: "noun", 2: "verb", 6: "noun",
                                   9: "noun", 10: "noun", 11: "verb", 12: "verb", 13: "noun"})
MARK_NAMES = ("nasb", "raf", "jarr", "jazm")


@dataclass(frozen=True, slots=True)
class GovernorEntry:
    row_id: int
    label: str
    class_code: int
    implicit: bool


@dataclass(frozen=True, slots=True)
class GovernorClass:
    code: int
    name: str
    alternatives: tuple[tuple[tuple[int, int], ...], ...]
    links: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class GovernorTable:
    entries: tuple[GovernorEntry, ...]
    classes: Mapping[int, GovernorClass]


@lru_cache(maxsize=1)
def _decode_table(raw: bytes) -> GovernorTable:
    if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Governor table differs from the installed law", status="DEFER")
    # A byte-exact installed artifact, independently compared with Lean by CI.
    value = json.loads(raw)
    return GovernorTable(
        tuple(GovernorEntry(**entry) for entry in value["entries"]),
        MappingProxyType({c["code"]: GovernorClass(
            c["code"], c["name"], tuple(tuple(tuple(pair) for pair in alt) for alt in c["alternatives"]),
            tuple(tuple(pair) for pair in c["links"])) for c in value["classes"]}),
    )


def installed_table() -> GovernorTable:
    # Recheck the actual installed bytes even when their immutable parse is cached.
    raw = files("nabt").joinpath("data/governors.json").read_bytes()
    return _decode_table(raw)


def lookup(label: str) -> tuple[GovernorEntry, ...]:
    if type(label) is not str or not label or len(label) > 128:
        raise NabtError("INVALID_GOVERNOR_LABEL", "Use an exact bounded table label")
    return tuple(e for e in installed_table().entries if e.label == label)


def _role(role: int) -> int:
    natural(role, "role")
    if role not in ROLE_CATEGORIES:
        raise NabtError("UNKNOWN_GOVERNOR_ROLE", "Role is outside the installed typed inventory")
    return role


def _mark(mark: int) -> int:
    return natural(mark, "case_mark", maximum=3)


def role_mark_number(role: int, mark: int) -> int:
    """Typed pairing only. All 36 pairs encode; category permission is separate."""
    return 4 * _role(role) + _mark(mark)


def decode_role_mark(number: int) -> tuple[int, int]:
    natural(number, "role_mark_number", maximum=55)
    role, mark = divmod(number, 4)
    return _role(role), _mark(mark)


def category_allows(role: int, mark: int) -> bool:
    category = ROLE_CATEGORIES[_role(role)]
    return _mark(mark) in ((0, 1, 2) if category == "noun" else (0, 1, 3))


def check_assignment(class_code: int, assignments: dict[int, int | None]) -> dict:
    """Return complete and still-viable alternatives, without inventing inputs.

    Like the Lean predicate, only equations and equality links of this class
    constrain the assignment. Extra known roles are irrelevant. Category
    admissibility is a separate predicate, not an undocumented extra premise.
    """
    natural(class_code, "class_code")
    cls = installed_table().classes.get(class_code)
    if cls is None:
        raise NabtError("UNKNOWN_GOVERNOR_CLASS", "No installed equation for this class")
    if type(assignments) is not dict:
        raise NabtError("INVALID_GOVERNOR_ASSIGNMENT", "Supply a finite role-to-mark dictionary")
    for role, mark in assignments.items():
        _role(role)
        if mark is not None:
            _mark(mark)
    complete, viable, deficits = [], [], []
    for alt in cls.alternatives:
        missing, conflicts = [], []
        for role, expected in alt:
            observed = assignments.get(role)
            if observed is None:
                missing.append({"role": role, "mark": expected})
            elif observed != expected:
                conflicts.append({"role": role, "expected": expected, "observed": observed})
        for left, right in cls.links:
            a, b = assignments.get(left), assignments.get(right)
            if a is None or b is None:
                missing.append({"equal_roles": [left, right]})
            elif a != b:
                conflicts.append({"equal_roles": [left, right], "observed": [a, b]})
        wire = [list(pair) for pair in alt]
        if not conflicts:
            viable.append(wire)
            if not missing:
                complete.append(wire)
        deficits.append({"alternative": wire, "missing": missing, "conflicts": conflicts})
    return {"law_id": LAW_ID, "class_code": class_code,
            "complete": complete, "viable": viable, "deficits": deficits,
            "authority": "CASE_ASSIGNMENT_ONLY"}


__all__ = ["LAW_ID", "ROLE_MARK_DOMAIN", "EXPECTED_TABLE_SHA256", "ROLE_CATEGORIES",
           "installed_table", "lookup", "check_assignment", "role_mark_number",
           "decode_role_mark", "category_allows"]
