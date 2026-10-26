"""A deterministic weighted word machine driven by its pinned Lean export.

The table is package-owned authority. Input material cannot choose or replace it.
Counting is bounded dynamic programming; no set of all words is materialized.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
from typing import Any

from .alphabet import ALPHABET_ID, LAW_ID, CARRIERS, STATE_NAMES, MAX_CELLS, validate_cell, validate_cells
from .codec import encode_cells
from .errors import NabtError, natural, resource_limit

STATE_COUNT = 97
DEAD_STATE = 96
MAX_WEIGHT = 16
# Updated only when the checked Lean exporter produces the release table.
EXPECTED_TABLE_SHA256 = "14e32ae208ac5ed2f754e83506e72133d0962756ef0c944d12370746febddcdd"


from nabt import foundation

@dataclass(frozen=True)
class _Table:
    transitions: tuple[tuple[tuple[int, int], ...], ...]
    potentials: tuple[int, ...]
    wasl: tuple[bool, ...]
    waqf: tuple[bool, ...]
    digest: str


def _state(value: object) -> int:
    return natural(value, "machine_state", maximum=STATE_COUNT - 1)


def _weight(value: object) -> int:
    n = natural(value, "consonant_weight")
    if n > MAX_WEIGHT:
        raise resource_limit("Requested consonant weight exceeds the runtime budget", maximum_weight=MAX_WEIGHT)
    return n


@lru_cache(maxsize=1)
def _load_table() -> _Table:
    try:
        raw = files("nabt").joinpath("data/law.json").read_bytes()
    except OSError as exc:
        raise NabtError("LAW_TABLE_UNAVAILABLE", "The installed law table is unavailable", status="DEFER") from exc
    digest = sha256(raw).hexdigest()
    if digest != EXPECTED_TABLE_SHA256:
        raise NabtError("LAW_TABLE_INTEGRITY", "The installed table differs from the pinned Lean export")
    try:
        table = json.loads(raw)
        expected = {"schema_version": 1, "alphabet_id": ALPHABET_ID, "law_id": LAW_ID,
                    "state_count": STATE_COUNT, "alphabet_size": 116, "start_state": 0,
                    "dead_state": DEAD_STATE, "carriers": list(CARRIERS), "states": list(STATE_NAMES)}
        for key, value in expected.items():
            if table.get(key) != value or type(table.get(key)) is not type(value):
                raise ValueError(f"Invalid table field {key}")
        rows = table["transitions"]
        if type(rows) is not list or len(rows) != STATE_COUNT:
            raise ValueError("Invalid transition rows")
        transitions = []
        for row in rows:
            if type(row) is not list or len(row) != 116:
                raise ValueError("Invalid transition columns")
            checked = []
            for edge in row:
                if type(edge) is not list or len(edge) != 2:
                    raise ValueError("Invalid transition edge")
                checked.append((_state(edge[0]), natural(edge[1], "edge_weight", maximum=1)))
            transitions.append(tuple(checked))
        pot = table["pot"]
        if type(pot) is not list or len(pot) != STATE_COUNT:
            raise ValueError("Invalid potentials")
        potentials = tuple(natural(p, "potential", maximum=2) for p in pot)
        finals = []
        for name in ("final_wasl", "final_waqf"):
            values = table[name]
            if type(values) is not list or len(values) != STATE_COUNT or any(type(b) is not bool for b in values):
                raise ValueError("Invalid final-state map")
            finals.append(tuple(values))
        return _Table(tuple(transitions), potentials, finals[0], finals[1], digest)
    except (KeyError, TypeError, ValueError) as exc:
        raise NabtError("LAW_TABLE_SCHEMA", "The installed law table has an invalid schema") from exc


@dataclass(frozen=True)
class TraceStep:
    position: int
    state_before: int
    cell: int
    state_after: int
    weight_delta: int

    def as_dict(self) -> dict[str, int]:
        return {"position": self.position, "state_before": self.state_before,
                "cell": self.cell, "state_after": self.state_after, "weight_delta": self.weight_delta}


@dataclass(frozen=True)
class Analysis:
    cells: tuple[int, ...]
    mode: str
    start_state: int
    final_state: int
    licensed: bool
    consonant_weight: int | None
    trace: tuple[TraceStep, ...]
    failure_code: str | None
    blocking_step: int | None

    @property
    def cell_length(self) -> int:
        return len(self.cells)

    def as_dict(self) -> dict[str, Any]:
        return {"alphabet_id": ALPHABET_ID, "law_id": LAW_ID,
                "scope": "WORD_SHAPE" if self.start_state == 0 else "STATE_RELATIVE_SHAPE",
                "cells": list(self.cells), "mode": self.mode, "start_state": self.start_state,
                "final_state": self.final_state, "licensed": self.licensed,
                "cell_length": self.cell_length, "consonant_weight": self.consonant_weight,
                "trace": [step.as_dict() for step in self.trace],
                "failure_code": self.failure_code, "blocking_step": self.blocking_step}


def _effect_values(cells: tuple[int, ...], table: _Table) -> tuple[tuple[int, ...], tuple[int, ...]]:
    destinations, weights = [], []
    for initial in range(STATE_COUNT):
        q, weight = initial, 0
        for a in cells:
            q, increment = table.transitions[q][a]
            weight += increment
        destinations.append(q)
        weights.append(weight)
    return tuple(destinations), tuple(weights)


@dataclass(frozen=True)
class Effect:
    """A total numerical effect, including dead states, bound to exact payload."""
    cells: tuple[int, ...]
    destinations: tuple[int, ...]
    weights: tuple[int, ...]

    def __post_init__(self) -> None:
        foundation.require_foundation('nabt.machine.effect.__post_init__')
        cells = validate_cells(self.cells)
        if type(self.cells) is not tuple or type(self.destinations) is not tuple or type(self.weights) is not tuple:
            raise NabtError("INVALID_EFFECT", "Effect fields must be immutable tuples")
        if len(self.destinations) != STATE_COUNT or len(self.weights) != STATE_COUNT:
            raise NabtError("INVALID_EFFECT", "An effect must cover every machine state")
        for q in self.destinations:
            _state(q)
        for w in self.weights:
            natural(w, "effect_weight")
        if (self.destinations, self.weights) != _effect_values(cells, _load_table()):
            raise NabtError("INVALID_EFFECT", "Declared effect does not match its payload")

    def as_dict(self) -> dict[str, Any]:
        code = encode_cells(self.cells)
        return {"alphabet_id": ALPHABET_ID, "law_id": LAW_ID,
                "cells": list(self.cells), "numeric_code": str(code) if code.bit_length() <= 12000 else None,
                "numeric_code_hex": hex(code),
                "cell_length": len(self.cells), "destinations": list(self.destinations),
                "weights": list(self.weights), "scope": "TRANSITION_EFFECT"}


def compose_effects(left: Effect, right: Effect) -> Effect:
    foundation.require_foundation('nabt.machine.compose_effects')
    if type(left) is not Effect or type(right) is not Effect:
        raise NabtError("INVALID_EFFECT", "Composition requires two verified effects")
    # Payload preservation prevents equal transition effects from erasing identity.
    cells = validate_cells(left.cells + right.cells)
    destinations = tuple(right.destinations[q] for q in left.destinations)
    weights = tuple(left.weights[q] + right.weights[left.destinations[q]] for q in range(STATE_COUNT))
    return Effect(cells, destinations, weights)


class Machine:
    """Word-level finite law. The sentence boundary 116 is outside this alphabet."""

    def __init__(self, mode: str = "waqf") -> None:
        foundation.require_foundation('nabt.machine.machine.__init__')
        if type(mode) is not str or mode not in {"waqf", "wasl"}:
            raise NabtError("INVALID_MODE", "Mode must be waqf or wasl")
        self._mode = mode
        self._table = _load_table()
        self._finals = self._table.waqf if mode == "waqf" else self._table.wasl

        @lru_cache(maxsize=None)
        def count_suffix(fuel: int, weight: int, q: int) -> int:
            if q == DEAD_STATE:
                return 0
            total = int(weight == 0 and self._finals[q])
            if fuel == 0:
                return total
            for next_state, increment in self._table.transitions[q]:
                if increment <= weight and next_state != DEAD_STATE:
                    total += count_suffix(fuel - 1, weight - increment, next_state)
            return total
        self._count_suffix = count_suffix

    @property
    def mode(self) -> str:
        """The immutable mode used by both evaluation and result labels."""
        return self._mode

    @property
    def table_sha256(self) -> str:
        return self._table.digest

    def transition(self, state: int, cell: int) -> tuple[int, int]:
        return self._table.transitions[_state(state)][validate_cell(cell)]

    def final(self, state: int) -> bool:
        return self._finals[_state(state)]

    def pot(self, state: int) -> int:
        return self._table.potentials[_state(state)]

    def cache_info(self) -> dict[str, int | None]:
        return dict(self._count_suffix.cache_info()._asdict())

    def analyse(self, cells: Iterable[int], start_state: int = 0) -> Analysis:
        foundation.require_foundation('nabt.machine.machine.analyse')
        values, initial = validate_cells(cells), _state(start_state)
        q, weight, blocker = initial, 0, None
        steps = []
        for i, a in enumerate(values):
            nq, increment = self._table.transitions[q][a]
            steps.append(TraceStep(i, q, a, nq, increment))
            if nq == DEAD_STATE and blocker is None:
                blocker = i
            q, weight = nq, weight + increment
        licensed = self._finals[q]
        reason = None if licensed else ("LAW_TRANSITION_REJECTED" if q == DEAD_STATE else "INCOMPLETE_FINAL_STATE")
        return Analysis(values, self.mode, initial, q, licensed,
                        None if q == DEAD_STATE else weight, tuple(steps), reason, blocker)

    def count(self, weight: int, start_state: int = 0) -> int:
        foundation.require_foundation('nabt.machine.machine.count')
        w, q = _weight(weight), _state(start_state)
        return self._count_suffix(3 * w + self.pot(q), w, q)

    def rank(self, cells: Iterable[int], start_state: int = 0) -> int:
        foundation.require_foundation('nabt.machine.machine.rank')
        analysis = self.analyse(cells, start_state)
        if not analysis.licensed or analysis.consonant_weight is None:
            raise NabtError("UNLICENSED_SHAPE", "Only a licensed sequence has a rank", details=analysis.as_dict())
        w = _weight(analysis.consonant_weight)
        q = analysis.start_state
        fuel = 3 * w + self.pot(q)
        if len(analysis.cells) > fuel:
            raise NabtError("LAW_BOUND_VIOLATION", "A licensed sequence exceeds the proved fuel bound")
        rank = 0
        for a in analysis.cells:
            rank += int(w == 0 and self._finals[q])
            for nq, increment in self._table.transitions[q][:a]:
                if increment <= w:
                    rank += self._count_suffix(fuel - 1, w - increment, nq)
            q, increment = self._table.transitions[q][a]
            w -= increment
            fuel -= 1
        return rank

    def unrank(self, weight: int, rank: int, start_state: int = 0) -> tuple[int, ...]:
        foundation.require_foundation('nabt.machine.machine.unrank')
        w, i, q = _weight(weight), natural(rank, "rank"), _state(start_state)
        fuel = 3 * w + self.pot(q)
        size = self._count_suffix(fuel, w, q)
        if i >= size:
            raise NabtError("RANK_OUT_OF_RANGE", "Rank is outside the declared grade", details={"count": str(size)})
        cells = []
        while True:
            base = int(w == 0 and self._finals[q])
            if i < base:
                return tuple(cells)
            i -= base
            if fuel == 0:
                raise NabtError("INTERNAL_COUNT_MISMATCH", "No transition block remains for an in-range rank")
            for a, (nq, increment) in enumerate(self._table.transitions[q]):
                block = self._count_suffix(fuel - 1, w - increment, nq) if increment <= w else 0
                if i < block:
                    cells.append(a)
                    q, w, fuel = nq, w - increment, fuel - 1
                    break
                i -= block
            else:
                raise NabtError("INTERNAL_COUNT_MISMATCH", "An in-range rank has no transition block")

    def effect(self, cells: Iterable[int]) -> Effect:
        foundation.require_foundation('nabt.machine.machine.effect')
        values = validate_cells(cells)
        destinations, weights = _effect_values(values, self._table)
        return Effect(values, destinations, weights)
