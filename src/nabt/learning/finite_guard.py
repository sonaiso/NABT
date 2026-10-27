"""Bounded, executable rule induction with explicitly conditional conclusions.

The hypothesis language is all signed conjunctions of at most ``degree``
declared Boolean predicates, plus false. A rule is a pair of disjoint integer
bit masks. No caller supplies its truth table, its accepted rank, or the list
of surviving rules. All consistent alternatives are retained.

This module learns a *guard*, not the interpretation of its primitive features,
an output transformation, or the truth of a source. A consensus is conditional
on the declared language containing an adequate rule and the supplied judgments
being correct. It deliberately cannot issue a ProofRank or a Certificate.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from itertools import combinations, islice, product
from math import comb
from types import MappingProxyType

from nabt.errors import resource_limit

MAX_PREDICATES = 32
MAX_HYPOTHESES = 100_000
MAX_QUERY_CASES = 4_096
MAX_OBSERVATIONS = 100_000
MAX_LEARNING_CHECKS = 2_000_000
MAX_QUERY_CHECKS = 2_000_000


from nabt import foundation

def _natural(value: int, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer (not a Boolean)")


def _nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def _digest(payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FeatureSchema:
    """Ordered predicate meanings belong to a named, versioned domain.

    A fingerprint protects identity; it does not authenticate the definitions.
    Updating a predicate's meaning requires a new ``version``.
    """

    domain: str
    version: str
    predicates: tuple[str, ...]

    def __post_init__(self) -> None:
        _nonempty(self.domain, "domain")
        _nonempty(self.version, "version")
        object.__setattr__(self, "predicates", tuple(self.predicates))
        if not 1 <= len(self.predicates) <= MAX_PREDICATES:
            raise ValueError(f"predicate count must be between 1 and {MAX_PREDICATES}")
        for name in self.predicates:
            _nonempty(name, "predicate")
        if len(set(self.predicates)) != len(self.predicates):
            raise ValueError("duplicate predicate identity")

    @property
    def width(self) -> int:
        return len(self.predicates)

    @property
    def fingerprint(self) -> str:
        return _digest((self.domain, self.version, self.predicates))

    def case(
        self, case_id: str, analysis_id: str, values: Mapping[str, bool | None]
    ) -> FeatureCase:
        """Missing keys and None are unknown, never false."""
        extras = set(values) - set(self.predicates)
        if extras:
            raise ValueError(f"undeclared predicates: {sorted(extras)}")
        known = value = 0
        for index, name in enumerate(self.predicates):
            item = values.get(name)
            if item is not None:
                if type(item) is not bool:
                    raise ValueError("predicate observations must be bool or None")
                known |= 1 << index
                if item:
                    value |= 1 << index
        return FeatureCase(case_id, analysis_id, self.fingerprint, self.width, known, value)


@dataclass(frozen=True, slots=True)
class FeatureCase:
    """One identified interpretation, with separate known and value masks."""

    case_id: str
    analysis_id: str
    schema_id: str
    width: int
    known: int
    value: int

    def __post_init__(self) -> None:
        for name in ("case_id", "analysis_id", "schema_id"):
            _nonempty(getattr(self, name), name)
        for name in ("width", "known", "value"):
            _natural(getattr(self, name), name)
        if not 1 <= self.width <= MAX_PREDICATES:
            raise ValueError("invalid feature width")
        if self.known >= 1 << self.width or self.value & ~self.known:
            raise ValueError("unknown or out-of-domain bits may not carry values")

    @property
    def complete(self) -> bool:
        return self.known == (1 << self.width) - 1


@dataclass(frozen=True, slots=True)
class Guard:
    """P must hold and N must fail. Code is base 3, scoped to the schema."""

    width: int
    positive: int = 0
    negative: int = 0
    bottom: bool = False

    def __post_init__(self) -> None:
        for name in ("width", "positive", "negative"):
            _natural(getattr(self, name), name)
        if not 1 <= self.width <= MAX_PREDICATES or type(self.bottom) is not bool:
            raise ValueError("invalid guard width or bottom flag")
        if (self.positive | self.negative) >= 1 << self.width:
            raise ValueError("guard contains an undeclared predicate")
        if self.positive & self.negative or (self.bottom and (self.positive | self.negative)):
            raise ValueError("guard is contradictory or is a noncanonical false")

    @property
    def degree(self) -> int:
        return (self.positive | self.negative).bit_count()

    @property
    def code(self) -> int:
        if self.bottom:
            return int(3**self.width)
        return sum(
            (1 if self.positive & (1 << i) else 2 if self.negative & (1 << i) else 0) * 3**i
            for i in range(self.width)
        )

    @classmethod
    def from_code(cls, width: int, code: int) -> Guard:
        _natural(width, "width")
        _natural(code, "code")
        if not 1 <= width <= MAX_PREDICATES or code > 3**width:
            raise ValueError("guard code outside declared width")
        if code == 3**width:
            return cls(width, bottom=True)
        positive = negative = 0
        for index in range(width):
            code, digit = divmod(code, 3)
            if digit == 1:
                positive |= 1 << index
            elif digit == 2:
                negative |= 1 << index
        return cls(width, positive, negative)

    def evaluate(self, value: int) -> bool:
        _natural(value, "valuation")
        if value >= 1 << self.width:
            raise ValueError("valuation outside declared width")
        return (
            not self.bottom
            and value & self.positive == self.positive
            and value & self.negative == 0
        )

    def possible(self, case: FeatureCase) -> tuple[bool, ...]:
        """Exact outcomes over all completions of the missing feature bits."""
        if case.width != self.width:
            raise ValueError("feature width mismatch")
        contradicted = (self.positive & case.known & ~case.value) | (self.negative & case.value)
        if self.bottom or contradicted:
            return (False,)
        if (self.positive | self.negative) & ~case.known:
            return (False, True)
        return (True,)

    def render(self, schema: FeatureSchema) -> str:
        if schema.width != self.width:
            raise ValueError("feature width mismatch")
        if self.bottom:
            return "false"
        literals = []
        for i, name in enumerate(schema.predicates):
            if self.positive & (1 << i):
                literals.append(name)
            elif self.negative & (1 << i):
                literals.append(f"not({name})")
        return " and ".join(literals) or "true"


@dataclass(frozen=True, slots=True)
class GuardLanguage:
    """An exhaustive finite hypothesis class, with a checked resource bound."""

    schema: FeatureSchema
    degree: int

    def __post_init__(self) -> None:
        _natural(self.degree, "degree")
        if self.degree > self.schema.width:
            raise ValueError("degree exceeds feature count")
        if self.count > MAX_HYPOTHESES:
            raise resource_limit("declared grammar exceeds the hypothesis resource budget")

    @property
    def count_by_degree(self) -> tuple[int, ...]:
        # Constants true and false both have degree zero.
        return (2,) + tuple(comb(self.schema.width, j) * 2**j for j in range(1, self.degree + 1))

    @property
    def count(self) -> int:
        return sum(self.count_by_degree)

    def enumerate(self) -> tuple[Guard, ...]:
        rules = [Guard(self.schema.width, bottom=True)]
        for size in range(self.degree + 1):
            for positions in combinations(range(self.schema.width), size):
                for signs in product((False, True), repeat=size):
                    positive = negative = 0
                    for index, sign in zip(positions, signs, strict=True):
                        if sign:
                            positive |= 1 << index
                        else:
                            negative |= 1 << index
                    rules.append(Guard(self.schema.width, positive, negative))
        return tuple(rules)


@dataclass(frozen=True, slots=True)
class Observation:
    """Externally supplied judgment; source identifiers are provenance, not proof."""

    evidence_id: str
    source_id: str
    case: FeatureCase
    label: bool | None

    def __post_init__(self) -> None:
        _nonempty(self.evidence_id, "evidence_id")
        _nonempty(self.source_id, "source_id")
        if self.label is not None and type(self.label) is not bool:
            raise ValueError("judgment must be bool or None")

    @property
    def ready(self) -> bool:
        return self.label is not None and self.case.complete


class LearningStatus(str, Enum):
    CONDITIONAL_CONSENSUS = "conditional_consensus"
    UNDERDETERMINED = "underdetermined"
    EXHAUSTED_DECLARED_GRAMMAR = "exhausted_declared_grammar"


@dataclass(frozen=True, slots=True)
class Prediction:
    status: LearningStatus
    possible: tuple[bool, ...]
    missing_predicates: tuple[str, ...]
    witness_rules: tuple[int, ...]
    case: FeatureCase
    schema_id: str
    evidence_revision: str
    reason: str


@dataclass(frozen=True, slots=True)
class QueryChoice:
    case: FeatureCase | None
    true_rule: int | None
    false_rule: int | None
    true_count: int
    false_count: int
    reason: str


@dataclass(frozen=True, slots=True)
class LearningSession:
    """Recomputable version space. Corrections restart from the full grammar.

    Only explicitly labelled, fully interpreted observations constrain this
    first implementation. Partial observations remain pending and named.
    """

    language: GuardLanguage
    observations: tuple[Observation, ...] = ()
    survivors: tuple[Guard, ...] = field(init=False)
    pending: tuple[str, ...] = field(init=False)
    _case_index: Mapping[tuple[str, str], FeatureCase] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        observations = tuple(islice(self.observations, MAX_OBSERVATIONS + 1))
        if len(observations) > MAX_OBSERVATIONS:
            raise resource_limit("observation records exceed resource budget")
        by_id: dict[str, Observation] = {}
        by_case: dict[tuple[str, str], FeatureCase] = {}
        for observation in observations:
            self._check_case(observation.case)
            old = by_id.get(observation.evidence_id)
            if old is not None and old != observation:
                raise ValueError("evidence identity reused; call revise_evidence")
            key = (observation.case.case_id, observation.case.analysis_id)
            if key in by_case and by_case[key] != observation.case:
                raise ValueError("case interpretation changed without a new analysis identity")
            by_case[key] = observation.case
            by_id[observation.evidence_id] = observation
        # Identical repeated records are idempotent; repetition grants no rank.
        observations = tuple(by_id.values())
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "_case_index", MappingProxyType(by_case))
        ready = tuple(e for e in observations if e.ready)
        if self.language.count * max(1, len(ready)) > MAX_LEARNING_CHECKS:
            raise resource_limit("learning checks exceed resource budget; no evidence was refuted")
        survivors = tuple(
            rule
            for rule in self.language.enumerate()
            if all(rule.evaluate(e.case.value) is e.label for e in ready)
        )
        object.__setattr__(self, "survivors", survivors)
        object.__setattr__(
            self, "pending", tuple(e.evidence_id for e in observations if not e.ready)
        )

    def _check_case(self, case: FeatureCase) -> None:
        if (
            case.schema_id != self.language.schema.fingerprint
            or case.width != self.language.schema.width
        ):
            raise ValueError("case belongs to a different predicate schema")

    def _check_query(self, case: FeatureCase) -> None:
        self._check_case(case)
        previous = self._case_index.get((case.case_id, case.analysis_id))
        if previous is not None and previous != case:
            raise ValueError("query changed features without a new analysis identity")

    @property
    def revision(self) -> str:
        return _digest(
            (
                self.language.schema.fingerprint,
                self.language.degree,
                sorted(
                    (
                        e.evidence_id,
                        e.source_id,
                        e.case.case_id,
                        e.case.analysis_id,
                        e.case.known,
                        e.case.value,
                        e.label,
                    )
                    for e in self.observations
                ),
            )
        )

    def observe(self, observation: Observation) -> LearningSession:
        return replace(self, observations=(*self.observations, observation))

    def revise_evidence(
        self, evidence_id: str, replacement: Observation | None
    ) -> LearningSession:
        previous = next((e for e in self.observations if e.evidence_id == evidence_id), None)
        if previous is None:
            raise KeyError(evidence_id)
        if (
            replacement is not None
            and (previous.case.case_id, previous.case.analysis_id)
            == (replacement.case.case_id, replacement.case.analysis_id)
            and previous.case != replacement.case
        ):
            raise ValueError(
                "changed features require a new analysis identity, even on correction"
            )
        remaining = tuple(e for e in self.observations if e.evidence_id != evidence_id)
        if replacement is not None:
            remaining += (replacement,)
        return replace(self, observations=remaining)

    def exhaustion_reason(self) -> str:
        if self.survivors:
            return "not_exhausted"
        by_case: dict[tuple[str, str], Observation] = {}
        by_value: dict[int, Observation] = {}
        feature_collision = False
        for observation in self.observations:
            if not observation.ready:
                continue
            key = (observation.case.case_id, observation.case.analysis_id)
            previous_case = by_case.get(key)
            if previous_case is not None and previous_case.label is not observation.label:
                return "conflicting_labels_for_same_interpretation"
            previous_value = by_value.get(observation.case.value)
            if previous_value is not None and previous_value.label is not observation.label:
                feature_collision = True
            by_case.setdefault(key, observation)
            by_value.setdefault(observation.case.value, observation)
        if feature_collision:
            return "feature_collision_or_conflicting_labels"
        return "no_consistent_rule_in_declared_grammar"

    def predict(self, case: FeatureCase) -> Prediction:
        foundation.require_foundation('nabt.learning.finite_guard.learningsession.predict')
        self._check_query(case)
        missing = tuple(
            name
            for index, name in enumerate(self.language.schema.predicates)
            if not case.known & (1 << index)
        )
        outcomes: dict[bool, int] = {}
        for rule in self.survivors:
            for outcome in rule.possible(case):
                if outcome not in outcomes:
                    outcomes[outcome] = rule.code
            if len(outcomes) == 2:
                break  # Two witnesses already establish underdetermination.
        possible = tuple(sorted(outcomes))
        if not possible:
            status = LearningStatus.EXHAUSTED_DECLARED_GRAMMAR
            reason = self.exhaustion_reason()
        elif len(possible) == 1:
            status = LearningStatus.CONDITIONAL_CONSENSUS
            reason = "all_surviving_guards_and_feature_completions_agree"
        else:
            status = LearningStatus.UNDERDETERMINED
            reason = "surviving_guards_or_missing_features_disagree"
        return Prediction(
            status,
            possible,
            missing,
            tuple(outcomes[v] for v in possible),
            case,
            self.language.schema.fingerprint,
            self.revision,
            reason,
        )

    def choose_query(self, cases: Iterable[FeatureCase]) -> QueryChoice:
        """Balanced disagreement within the supplied pool, never global equivalence."""
        foundation.require_foundation('nabt.learning.finite_guard.learningsession.choose_query')
        best = QueryChoice(None, None, None, 0, 0, "no_disagreement_in_supplied_pool")
        if not self.survivors:
            return replace(best, reason=self.exhaustion_reason())
        best_score = 0
        evaluations = 0
        for index, case in enumerate(cases):
            if index >= MAX_QUERY_CASES:
                raise resource_limit("query pool exceeds resource budget")
            self._check_query(case)
            if not case.complete:
                continue
            evaluations += len(self.survivors)
            if evaluations > MAX_QUERY_CHECKS:
                raise resource_limit(
                    "query checks exceed resource budget; no equivalence was established"
                )
            positive_count = 0
            positive_witness: Guard | None = None
            negative_witness: Guard | None = None
            for rule in self.survivors:
                if rule.evaluate(case.value):
                    positive_count += 1
                    if positive_witness is None:
                        positive_witness = rule
                else:
                    if negative_witness is None:
                        negative_witness = rule
            negative_count = len(self.survivors) - positive_count
            score = min(positive_count, negative_count)
            if score > best_score:
                best_score = score
                assert positive_witness is not None and negative_witness is not None
                best = QueryChoice(
                    case,
                    positive_witness.code,
                    negative_witness.code,
                    positive_count,
                    negative_count,
                    "two_consistent_rules_disagree_on_this_case",
                )
        return best


__all__ = [
    "FeatureCase",
    "FeatureSchema",
    "Guard",
    "GuardLanguage",
    "LearningSession",
    "LearningStatus",
    "Observation",
    "Prediction",
    "QueryChoice",
]
