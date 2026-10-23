"""Pre-composition word algebra, with explicit and separate numeric domains.

The table is exported from ``Nabt.Words``. It describes declared inflection
classes, not a classifier of arbitrary spellings. Supplying a class or kind to
these functions grants no source evidence. ``word_reader`` owns the bounded
source-to-analysis bridge and replays its installed witnesses.
"""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
from types import MappingProxyType

from .errors import NabtError, natural

LAW_ID = "nabt.words.v1"
KIND_DOMAIN = "nabt.words.kind.v1"
CLASS_CASE_DOMAIN = "nabt.words.class-case.v1"
EXPECTED_TABLE_SHA256 = "e3e796e849386dedd6abc3a473cb15dcece2e7b35583c45d16139d3c183dbcc3"
KINDS = ("noun", "verb", "particle")
CASES = ("nasb", "raf", "jarr", "jazm")
ENDINGS = ("damma", "fatha", "kasra", "sukun", "waw", "alif", "ya", "ani", "ayni", "una", "ina")


@lru_cache(maxsize=1)
def _table(raw: bytes):
    if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Word algebra differs from its installed pin", status="DEFER")
    value = json.loads(raw)
    return (tuple(MappingProxyType(row) for row in value["classes"]),
            MappingProxyType({(row["class"], row["case"]): row["ending"] for row in value["rows"]}))


def installed_table():
    """Recheck installed bytes on every use; never accept a supplied manifest."""
    return _table(files("nabt").joinpath("data/words.json").read_bytes())


def kind_candidates(activated_constraints: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    """Intersect *already activated* constraints. Empty evidence keeps all kinds.

    This conditional algebra does not activate cues or prove that a cue is
    true of a word. The empty intersection is a conflict, not a particle.
    """
    if type(activated_constraints) is not tuple or len(activated_constraints) > 64:
        raise NabtError("INVALID_KIND_CONSTRAINTS", "Use at most 64 finite kind constraints")
    for constraint in activated_constraints:
        if type(constraint) is not tuple or len(constraint) > 3:
            raise NabtError("INVALID_KIND_CONSTRAINTS", "Kind constraints must be distinct finite codes")
        for kind in constraint:
            natural(kind, "kind", maximum=2)
        if len(set(constraint)) != len(constraint):
            raise NabtError("INVALID_KIND_CONSTRAINTS", "Do not duplicate a kind constraint")
    return tuple(k for k in range(3) if all(k in c for c in activated_constraints))


def capacities(kind: int) -> dict:
    """Predication capacities, not an actual role in a source sentence."""
    natural(kind, "kind", maximum=2)
    return {"subject": kind == 0, "predicate": kind != 2}


def class_kind(class_code: int) -> int:
    natural(class_code, "declension_class", maximum=14)
    classes, _ = installed_table()
    return classes[class_code]["kind"]


def case_candidates(class_codes: tuple[int, ...], observed_ending: int | None) -> tuple[tuple[int, int], ...]:
    """Retain (class, case) correlation; an absent ending is not a negative one.

    The finite model includes only the 15 declared *inflected* classes. Built
    words and unlicensed classes cannot be encoded here as an empty class or
    an arbitrary default. A caller must independently justify the inventory.
    """
    if type(class_codes) is not tuple or len(class_codes) > 15:
        raise NabtError("INVALID_DECLENSION_CLASSES", "Use a finite tuple of declared classes")
    for code in class_codes:
        natural(code, "declension_class", maximum=14)
    if len(class_codes) != len(set(class_codes)):
        raise NabtError("INVALID_DECLENSION_CLASSES", "Do not duplicate a class to create evidence")
    if observed_ending is not None:
        natural(observed_ending, "observed_ending", maximum=10)
    _, rows = installed_table()
    return tuple((code, case) for code in sorted(class_codes) for case in range(4)
                 if rows[code, case] is not None
                 and (observed_ending is None or rows[code, case] == observed_ending))


def refine_cases(candidates: tuple[tuple[int, int], ...], *, role: int, required_case: int) -> tuple[tuple[int, int], ...]:
    """Connect word analyses to the existing governor-role contract.

    It only filters supplied candidates. It cannot establish a governor's
    activation, complement boundary, source identity, or lexical category.
    """
    from .governors import ROLE_CATEGORIES, role_mark_number
    role_mark_number(role, required_case)  # Validate both domains, including bool.
    if type(candidates) is not tuple or len(candidates) > 60:
        raise NabtError("INVALID_CASE_CANDIDATES", "Use a bounded tuple of class/case candidates")
    for pair in candidates:
        if type(pair) is not tuple or len(pair) != 2:
            raise NabtError("INVALID_CASE_CANDIDATES", "Each candidate binds one class and one case")
        natural(pair[0], "declension_class", maximum=14)
        natural(pair[1], "case", maximum=3)
        if pair not in case_candidates((pair[0],), None):
            raise NabtError("INVALID_CASE_CANDIDATES", "This class does not realize the supplied case")
    wanted_kind = 0 if ROLE_CATEGORIES[role] == "noun" else 1
    return tuple(p for p in candidates if p[1] == required_case and class_kind(p[0]) == wanted_kind)


def class_case_number(class_code: int, case: int) -> int:
    """Typed pair, not a character cell and not an authority certificate."""
    natural(class_code, "declension_class", maximum=14)
    natural(case, "case", maximum=3)
    return 4 * class_code + case


def decode_class_case(number: int) -> tuple[int, int]:
    natural(number, "class_case_number", maximum=59)
    return divmod(number, 4)
