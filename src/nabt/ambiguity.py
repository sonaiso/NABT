"""Exact finite alternatives for one observed word under the installed shape law.

This is a separately named query reader. A missing mark opens four hypotheses;
it never becomes an observed sukun. The ordinary ``parse_word`` stays strict.
Paths retain their correlations: projected per-position marks cannot be freely
recombined. Counts concern licensed cell sequences, not meanings or attestations.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any
import unicodedata

from .alphabet import ALPHABET_ID, LAW_ID, CARRIERS, HARAKAT, MAX_SOURCE_BYTES, cell_id, validate_cells
from .errors import NabtError, natural, resource_limit
from .machine import DEAD_STATE, STATE_COUNT, Machine

PATTERN_VERSION = "nabt.independent-missing-marks.v1"
MAX_PATTERN_CELLS = 128
MAX_COUNT_UPDATES = 2_000_000


def _read(source: str) -> tuple[tuple[tuple[int, ...], ...], tuple[int, ...]]:
    if type(source) is not str:
        raise NabtError("INVALID_TEXT", "An observed source must be a string")
    if len(source) > MAX_SOURCE_BYTES:
        raise resource_limit("Observed source exceeds the byte budget")
    try:
        raw = source.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise NabtError("INVALID_UNICODE", "Source contains an invalid Unicode scalar") from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise resource_limit("Observed source exceeds the byte budget")
    if not source:
        raise NabtError("EMPTY_WORD", "A source must contain a carrier")
    carriers: list[str] = []
    states: list[int | None] = []
    for offset, char in enumerate(source):
        if char in CARRIERS:
            carriers.append(char)
            states.append(None)
            if len(carriers) > MAX_PATTERN_CELLS:
                raise resource_limit("Symbolic word exceeds the position budget", maximum=MAX_PATTERN_CELLS)
        elif char in HARAKAT:
            if not states:
                raise NabtError("MARK_WITHOUT_CARRIER", "A mark has no carrier", details={"offset": offset})
            if states[-1] is not None:
                raise NabtError("CONFLICTING_MARKS", "A carrier has multiple marks", details={"offset": offset})
            states[-1] = HARAKAT.index(char)
        elif char.isspace():
            raise NabtError("WORD_BOUNDARY_NOT_ALLOWED", "This reader accepts one word")
        elif unicodedata.category(char).startswith("M") or char in "أإؤئآٱىة":
            raise NabtError("UNSUPPORTED_ORTHOGRAPHY", "A separate orthographic bridge is required", status="DEFER")
        else:
            raise NabtError("UNKNOWN_CARRIER", "Symbol is outside the declared alphabet", status="DEFER")
    domains = tuple(tuple(cell_id(c, h) for h in (range(4) if s is None else (s,)))
                    for c, s in zip(carriers, states))
    return domains, tuple(i for i, s in enumerate(states) if s is None)


@dataclass(frozen=True, slots=True)
class Arc:
    cell: int
    target: int
    weight: int


@dataclass(frozen=True, slots=True, init=False)
class AmbiguityForest:
    """A finite layered DAG of exact source completions, with no preferred path.

    Construction replays the source reader and installed law. Callers cannot
    supply counts, domains, a completion flag, or a proof-status field.
    """

    source: str
    mode: str
    domains: tuple[tuple[int, ...], ...]
    missing_positions: tuple[int, ...]
    source_sha256: str
    table_sha256: str
    layers: tuple[tuple[tuple[Arc, ...], ...], ...]
    suffix_counts: tuple[tuple[int, ...], ...]
    counts_by_weight: tuple[tuple[int, int], ...]

    def __init__(self, source: str, mode: str = "waqf") -> None:
        domains, missing = _read(source)
        machine = Machine(mode)
        reachable = {0}
        layers = []
        for domain in domains:
            rows: list[tuple[Arc, ...]] = [()] * STATE_COUNT
            next_reachable = set()
            for q in sorted(reachable):
                arcs = []
                for a in domain:
                    nq, dw = machine.transition(q, a)
                    if nq != DEAD_STATE:
                        arcs.append(Arc(a, nq, dw))
                        next_reachable.add(nq)
                rows[q] = tuple(arcs)
            layers.append(tuple(rows))
            reachable = next_reachable
        # Trim only paths that cannot reach an accepted exact-length endpoint.
        suffix = [tuple(int(q in reachable and machine.final(q)) for q in range(STATE_COUNT))]
        trimmed = []
        for rows in reversed(layers):
            good = tuple(tuple(arc for arc in row if suffix[-1][arc.target]) for row in rows)
            trimmed.append(good)
            suffix.append(tuple(sum(suffix[-1][arc.target] for arc in row) for row in good))
        trimmed.reverse()
        suffix.reverse()
        # Forward polynomial coefficients, independent of suffix path counts.
        frontier = {(0, 0): 1}
        updates = 0
        for rows in trimmed:
            following: dict[tuple[int, int], int] = {}
            for (q, w), count in frontier.items():
                for arc in rows[q]:
                    updates += 1
                    if updates > MAX_COUNT_UPDATES:
                        raise resource_limit("Graded count exceeds the update budget", maximum=MAX_COUNT_UPDATES)
                    key = (arc.target, w + arc.weight)
                    following[key] = following.get(key, 0) + count
            frontier = following
        grades: dict[int, int] = {}
        for (q, w), count in frontier.items():
            if machine.final(q):
                grades[w] = grades.get(w, 0) + count
        if sum(grades.values()) != suffix[0][0]:
            raise NabtError("INTERNAL_COUNT_MISMATCH", "Independent count projections disagree")
        values = {
            "source": source, "mode": machine.mode, "domains": domains,
            "missing_positions": missing, "source_sha256": sha256(source.encode("utf-8")).hexdigest(),
            "table_sha256": machine.table_sha256, "layers": tuple(trimmed),
            "suffix_counts": tuple(suffix), "counts_by_weight": tuple(sorted(grades.items())),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def total(self) -> int:
        return self.suffix_counts[0][0]

    def witness(self, rank: int) -> tuple[int, ...]:
        """Select an exact licensed path by lexicographic rank, without enumeration."""
        remainder = natural(rank, "forest_rank")
        if remainder >= self.total:
            raise NabtError("OUTSIDE_DOMAIN", "No licensed completion at that rank")
        q, result = 0, []
        for i, rows in enumerate(self.layers):
            for arc in rows[q]:
                count = self.suffix_counts[i + 1][arc.target]
                if remainder < count:
                    result.append(arc.cell)
                    q = arc.target
                    break
                remainder -= count
            else:
                raise NabtError("INTERNAL_PATH_MISMATCH", "Rank could not be resolved")
        return tuple(result)

    def contains(self, cells: tuple[int, ...]) -> bool:
        values = validate_cells(cells)
        if len(values) != len(self.layers):
            return False
        q = 0
        for a, rows in zip(values, self.layers):
            match = next((arc for arc in rows[q] if arc.cell == a), None)
            if match is None:
                return False
            q = match.target
        return bool(self.suffix_counts[-1][q])

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope": "WORD_SHAPE_COMPLETIONS", "pattern_version": PATTERN_VERSION,
            "alphabet_id": ALPHABET_ID, "law_id": LAW_ID, "table_sha256": self.table_sha256,
            "source": self.source, "source_sha256": self.source_sha256,
            "mode": self.mode, "cell_length": len(self.domains), "complete_within_query": True,
            "raw_completion_count": 4 ** len(self.missing_positions),
            "licensed_completion_count": self.total, "counts_by_weight": dict(self.counts_by_weight),
            "residuals": [{"kind": "MISSING_OBSERVED_MARK", "position": i,
                           "admissible_hypotheses": sorted({a.cell % 4 for row in self.layers[i] for a in row})}
                          for i in self.missing_positions],
            "projected_hypotheses_are_not_independent": True,
            "lexical_attestation": "NOT_ESTABLISHED", "semantic_judgment": "NOT_ESTABLISHED",
        }
