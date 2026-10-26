"""Counterexample-guided acquisition of a finite transition procedure.

The learner proposes an inert bit-decision DAG. A separate complete-domain
comparison checks all 97 * 116 primitive transitions, including their costs.
No model score, sample count, source digest, or supplied proof flag is authority.
This learns an implementation of a fixed law; it does not discover Arabic truth.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json

from .alphabet import ALPHABET_ID, LAW_ID, validate_cell, validate_cells
from .errors import NabtError, natural, resource_limit
from .machine import Machine, STATE_COUNT

MODEL_VERSION = "nabt.transition-bit-dag.v1"
INPUT_BITS = 14
MAX_MODEL_NODES = 32767


from nabt import foundation

@dataclass(frozen=True, slots=True)
class Leaf:
    target: int
    weight: int


@dataclass(frozen=True, slots=True)
class Branch:
    bit: int
    zero: int
    one: int


@dataclass(frozen=True, slots=True)
class DecisionDAG:
    """Postorder immutable data; child indices are strictly smaller than parent."""
    nodes: tuple[Leaf | Branch, ...]

    def __post_init__(self) -> None:
        if type(self.nodes) is not tuple or not self.nodes:
            raise NabtError("INVALID_MODEL", "A model requires a nonempty immutable node tuple")
        if len(self.nodes) > MAX_MODEL_NODES:
            raise resource_limit("Candidate exceeds the node budget", maximum=MAX_MODEL_NODES)
        depths = []
        for i, node in enumerate(self.nodes):
            if type(node) is Leaf:
                natural(node.target, "target", maximum=96)
                natural(node.weight, "weight", maximum=1)
                depths.append(0)
            elif type(node) is Branch:
                natural(node.bit, "bit", maximum=INPUT_BITS - 1)
                for child in (node.zero, node.one):
                    natural(child, "child_index")
                    if child >= i:
                        raise NabtError("INVALID_MODEL", "Children must precede their parent")
                depth = 1 + max(depths[node.zero], depths[node.one])
                if depth > INPUT_BITS:
                    raise NabtError("INVALID_MODEL", "A decision path exceeds the declared bit depth")
                depths.append(depth)
            else:
                raise NabtError("INVALID_MODEL", "Only concrete inert Leaf and Branch nodes are accepted")


def _snapshot(candidate: DecisionDAG) -> DecisionDAG:
    if type(candidate) is not DecisionDAG:
        raise NabtError("INVALID_MODEL", "Only the concrete decision DAG format is accepted")
    # Revalidate even when a caller previously constructed a dataclass instance.
    DecisionDAG(candidate.nodes)
    return DecisionDAG(tuple(Leaf(n.target, n.weight) if type(n) is Leaf
                             else Branch(n.bit, n.zero, n.one) for n in candidate.nodes))


def _evaluate(nodes: tuple[Leaf | Branch, ...], code: int) -> tuple[int, int]:
    i = len(nodes) - 1
    while type(nodes[i]) is Branch:
        node = nodes[i]
        i = node.one if (code >> node.bit) & 1 else node.zero
    leaf = nodes[i]
    return leaf.target, leaf.weight


def _digest(nodes: tuple[Leaf | Branch, ...]) -> str:
    values = [["leaf", n.target, n.weight] if type(n) is Leaf else ["bit", n.bit, n.zero, n.one] for n in nodes]
    raw = json.dumps([MODEL_VERSION, ALPHABET_ID, LAW_ID, values], separators=(",", ":")).encode("ascii")
    return sha256(raw).hexdigest()


@dataclass(frozen=True)
class Counterexample:
    state: int
    cell: int
    expected: tuple[int, int]
    proposed: tuple[int, int]


@dataclass(frozen=True)
class Verification:
    model_sha256: str
    table_sha256: str
    checked_inputs: int
    mismatch_count: int
    counterexamples: tuple[Counterexample, ...]

    @property
    def accepted(self) -> bool:
        return self.checked_inputs == STATE_COUNT * 116 and self.mismatch_count == 0


def verify_candidate(candidate: DecisionDAG, *, counterexample_limit: int = 256) -> Verification:
    foundation.require_foundation('nabt.acquisition.verify_candidate')
    model = _snapshot(candidate)
    limit = natural(counterexample_limit, "counterexample_limit", maximum=STATE_COUNT * 116)
    machine = Machine()
    mismatches = 0
    examples = []
    for q in range(STATE_COUNT):
        for a in range(116):
            expected = machine.transition(q, a)
            proposed = _evaluate(model.nodes, (q << 7) | a)
            if proposed != expected:
                mismatches += 1
                if len(examples) < limit:
                    examples.append(Counterexample(q, a, expected, proposed))
    return Verification(_digest(model.nodes), machine.table_sha256, STATE_COUNT * 116, mismatches, tuple(examples))


@dataclass(frozen=True, slots=True, init=False)
class CheckedPredictor:
    """A rechecked immutable candidate. Final states always come from installed law."""
    nodes: tuple[Leaf | Branch, ...]
    verification: Verification

    def __init__(self, candidate: DecisionDAG) -> None:
        foundation.require_foundation('nabt.acquisition.checkedpredictor.__init__')
        model = _snapshot(candidate)
        report = verify_candidate(model)
        if not report.accepted:
            raise NabtError("CANDIDATE_REFUTED", "Candidate disagrees with the installed transition contract",
                            details={"mismatches": report.mismatch_count, "first": repr(report.counterexamples[0])})
        object.__setattr__(self, "nodes", model.nodes)
        object.__setattr__(self, "verification", report)

    def transition(self, state: int, cell: int) -> tuple[int, int]:
        foundation.require_foundation('nabt.acquisition.checkedpredictor.transition')
        q = natural(state, "state", maximum=96)
        a = validate_cell(cell)
        return _evaluate(self.nodes, (q << 7) | a)

    def run(self, cells: tuple[int, ...], *, mode: str = "waqf", start_state: int = 0) -> tuple[int, int, bool]:
        foundation.require_foundation('nabt.acquisition.checkedpredictor.run')
        machine = Machine(mode)
        q = natural(start_state, "state", maximum=96)
        weight = 0
        for a in validate_cells(cells):
            q, dw = _evaluate(self.nodes, (q << 7) | a)
            weight += dw
        return q, weight, machine.final(q)


def _fit(examples: dict[int, tuple[int, int]]) -> DecisionDAG:
    """Exact classification of supplied examples. Heuristic choice grants no license."""
    nodes: list[Leaf | Branch] = []
    intern: dict[Leaf | Branch, int] = {}

    def save(node: Leaf | Branch) -> int:
        if node not in intern:
            intern[node] = len(nodes)
            nodes.append(node)
        return intern[node]

    def build(rows: tuple[int, ...], bits: tuple[int, ...]) -> int:
        labels = {examples[x] for x in rows}
        if len(labels) == 1:
            target, weight = next(iter(labels))
            return save(Leaf(target, weight))
        best = None
        for bit in bits:
            zero = tuple(x for x in rows if not (x >> bit) & 1)
            one = tuple(x for x in rows if (x >> bit) & 1)
            if not zero or not one:
                continue
            c0, c1 = Counter(examples[x] for x in zero), Counter(examples[x] for x in one)
            numerator = sum(n*n for n in c0.values()) * len(one) + sum(n*n for n in c1.values()) * len(zero)
            denominator = len(zero) * len(one)
            if best is None or numerator * best[1] > best[0] * denominator:
                best = numerator, denominator, bit, zero, one
        if best is None:
            raise NabtError("INCONSISTENT_EXAMPLES", "Identical input bits have incompatible targets")
        _, _, bit, zero, one = best
        remaining = tuple(b for b in bits if b != bit)
        left, right = build(zero, remaining), build(one, remaining)
        return save(Branch(bit, left, right))

    root = build(tuple(sorted(examples)), tuple(range(INPUT_BITS)))
    # Root cannot be an earlier subtree unless the whole classifier is a leaf.
    if root != len(nodes) - 1:
        raise NabtError("INTERNAL_MODEL_ORDER", "Root is not the final postorder node")
    return DecisionDAG(tuple(nodes))


@dataclass(frozen=True)
class LearningRound:
    number: int
    training_examples: int
    model_nodes: int
    mismatches: int


@dataclass(frozen=True)
class AcquisitionResult:
    status: str
    model: CheckedPredictor | None
    rounds: tuple[LearningRound, ...]
    residual: str | None


def acquire_transition_model(*, max_rounds: int = 64, batch_size: int = 256) -> AcquisitionResult:
    foundation.require_foundation('nabt.acquisition.acquire_transition_model')
    rounds_limit = natural(max_rounds, "max_rounds", maximum=1024)
    batch = natural(batch_size, "batch_size", maximum=STATE_COUNT * 116)
    if rounds_limit == 0 or batch == 0:
        raise NabtError("INVALID_BUDGET", "Acquisition budgets must be positive")
    machine = Machine()
    examples = {0: machine.transition(0, 0)}
    history = []
    for number in range(1, rounds_limit + 1):
        candidate = _fit(examples)
        report = verify_candidate(candidate, counterexample_limit=batch)
        history.append(LearningRound(number, len(examples), len(candidate.nodes), report.mismatch_count))
        if report.accepted:
            return AcquisitionResult("VERIFIED_FINITE_CONTRACT", CheckedPredictor(candidate), tuple(history), None)
        for ce in report.counterexamples:
            examples[(ce.state << 7) | ce.cell] = ce.expected
    return AcquisitionResult("DEFER", None, tuple(history), "COUNTEREXAMPLES_REMAIN_WITHIN_BUDGET")
