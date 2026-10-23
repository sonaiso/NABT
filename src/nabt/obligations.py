"""Named positive-formula obligations over a declared finite proposition registry.

Numbers address full proposition identities, never bare words or unbound labels.
Positive and negative support remain separate. This module computes consequences
of the supplied support; it does not authenticate that support or establish the
truth of a linguistic claim. The source checker is a separate boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, TypeAlias

from .errors import NabtError, natural, resource_limit


OBLIGATION_VERSION = "nabt.named-positive-obligations.v1"
MAX_REGISTRY_ATOMS = 4096
MAX_IDENTITY_BYTES = 8192
MAX_REGISTRY_BYTES = 2_000_000
_IDENTITY_FIELDS = ("name", "source", "occurrence", "reading", "context", "definition", "policy")


def _text(value: object, field: str) -> str:
    if type(value) is not str or not value or not value.strip():
        raise NabtError("INVALID_PROPOSITION_IDENTITY", f"{field} must be a nonempty string")
    if len(value) > MAX_IDENTITY_BYTES:
        raise resource_limit("Proposition identity exceeds its byte budget", field=field)
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise NabtError("INVALID_UNICODE", f"{field} contains an invalid Unicode scalar") from exc
    if len(encoded) > MAX_IDENTITY_BYTES:
        raise resource_limit("Proposition identity exceeds its byte budget", field=field)
    return value


def _digest(value: Any) -> str:
    return sha256(_json_bytes(value)).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, slots=True)
class Proposition:
    """One exact claim, bound to its source, occurrence, reading, and policy.

    The strings are opaque identities. Their presence is not a claim that their
    sources or definitions have been authenticated. Equality uses every field.
    """

    name: str
    source: str
    occurrence: str
    reading: str
    context: str
    definition: str
    policy: str

    def __post_init__(self) -> None:
        for field in _IDENTITY_FIELDS:
            _text(getattr(self, field), field)

    @property
    def key(self) -> tuple[str, ...]:
        return tuple(getattr(self, field) for field in _IDENTITY_FIELDS)

    @property
    def proposition_id(self) -> str:
        return _digest([OBLIGATION_VERSION, "proposition", self.key])

    def as_dict(self) -> dict[str, Any]:
        return {"proposition_id": self.proposition_id,
                **{field: getattr(self, field) for field in _IDENTITY_FIELDS}}


# The longer name is useful at source-checking boundaries.
PropositionIdentity = Proposition


@dataclass(frozen=True, slots=True, init=False)
class PropositionRegistry:
    """Canonical immutable finite domain; its sorted identities fix all bits."""

    propositions: tuple[Proposition, ...]
    registry_id: str

    def __init__(self, propositions: Iterable[Proposition]) -> None:
        try:
            iterator = iter(propositions)
        except TypeError as exc:
            raise NabtError("INVALID_PROPOSITION_REGISTRY", "A registry requires propositions") from exc
        copied: list[Proposition] = []
        seen: set[tuple[str, ...]] = set()
        byte_count = 0
        for original in iterator:
            if len(copied) >= MAX_REGISTRY_ATOMS:
                raise resource_limit("Proposition registry exceeds the atom budget",
                                     maximum=MAX_REGISTRY_ATOMS)
            if type(original) is not Proposition:
                raise NabtError("INVALID_PROPOSITION_IDENTITY", "Every registry entry must be a Proposition")
            proposition = Proposition(*(getattr(original, field) for field in _IDENTITY_FIELDS))
            if proposition.key in seen:
                raise NabtError("DUPLICATE_PROPOSITION", "A registry contains the same full identity twice")
            seen.add(proposition.key)
            byte_count += sum(len(s.encode("utf-8")) for s in proposition.key)
            if byte_count > MAX_REGISTRY_BYTES:
                raise resource_limit("Proposition registry exceeds the total identity budget",
                                     maximum=MAX_REGISTRY_BYTES)
            copied.append(proposition)
        entries = tuple(sorted(copied, key=lambda p: p.key))
        object.__setattr__(self, "propositions", entries)
        object.__setattr__(self, "registry_id",
                           _digest([OBLIGATION_VERSION, "registry", [p.key for p in entries]]))

    @property
    def universe_mask(self) -> int:
        return (1 << len(self.propositions)) - 1

    def index(self, proposition: Proposition) -> int:
        if type(proposition) is not Proposition:
            raise NabtError("INVALID_PROPOSITION_IDENTITY", "A formula atom needs a full Proposition identity")
        try:
            return self.propositions.index(proposition)
        except ValueError as exc:
            raise NabtError("UNREGISTERED_PROPOSITION", "The proposition is outside this exact registry",
                            details={"proposition": proposition.as_dict()}) from exc

    def bit(self, proposition: Proposition) -> int:
        return 1 << self.index(proposition)

    def mask(self, propositions: Iterable[Proposition]) -> int:
        try:
            iterator = iter(propositions)
        except TypeError as exc:
            raise NabtError("INVALID_PROPOSITION_REGISTRY", "A mask requires an iterable of propositions") from exc
        result = 0
        for count, proposition in enumerate(iterator, 1):
            if count > MAX_REGISTRY_ATOMS:
                raise resource_limit("Mask input exceeds the atom budget", maximum=MAX_REGISTRY_ATOMS)
            result |= self.bit(proposition)
        return result

    def names(self, mask: int) -> tuple[Proposition, ...]:
        checked = natural(mask, "mask", maximum=self.universe_mask)
        return tuple(p for i, p in enumerate(self.propositions) if checked & (1 << i))

    def as_dict(self) -> dict[str, Any]:
        return {"version": OBLIGATION_VERSION, "registry_id": self.registry_id,
                "propositions": [{"bit_index": i, **p.as_dict()}
                                 for i, p in enumerate(self.propositions)]}


@dataclass(frozen=True, slots=True)
class Atom:
    proposition: Proposition


@dataclass(frozen=True, slots=True)
class Constant:
    value: bool


@dataclass(frozen=True, slots=True)
class And:
    left: Formula
    right: Formula


@dataclass(frozen=True, slots=True)
class Or:
    left: Formula
    right: Formula


Formula: TypeAlias = Atom | Constant | And | Or
TRUE = Constant(True)
FALSE = Constant(False)


def all_of(*terms: Formula) -> Formula:
    """Conjunction of an explicitly declared finite family; empty means TRUE."""
    if not terms:
        return TRUE
    result = terms[0]
    for term in terms[1:]:
        result = And(result, term)
    return result


def any_of(*terms: Formula) -> Formula:
    """Disjunction of an explicitly declared finite family; empty means FALSE."""
    if not terms:
        return FALSE
    result = terms[0]
    for term in terms[1:]:
        result = Or(result, term)
    return result


@dataclass(frozen=True, slots=True)
class Limits:
    """Explicit computation budgets; exhaustion is RESOURCE_LIMIT / DEFER."""

    max_atoms: int = 256
    max_nodes: int = 8192
    max_depth: int = 128
    max_plans: int = 4096
    max_candidates: int = 100_000
    max_comparisons: int = 1_000_000
    max_output_bytes: int = 8_000_000

    def __post_init__(self) -> None:
        ceilings = {"max_atoms": MAX_REGISTRY_ATOMS, "max_nodes": 65_536,
                    "max_depth": 256, "max_plans": 65_536,
                    "max_candidates": 2_000_000, "max_comparisons": 5_000_000,
                    "max_output_bytes": 32_000_000}
        for field, ceiling in ceilings.items():
            value = natural(getattr(self, field), field, maximum=ceiling)
            if value == 0:
                raise NabtError("INVALID_OBLIGATION_LIMIT", f"{field} must be positive")


@dataclass(frozen=True, slots=True)
class CompletionPlan:
    mask: int
    propositions: tuple[Proposition, ...]

    @property
    def names(self) -> tuple[str, ...]:
        """Display labels; use full propositions/identities for binding."""
        return tuple(p.name for p in self.propositions)

    def as_dict(self) -> dict[str, Any]:
        return {"mask": self.mask, "propositions": [p.as_dict() for p in self.propositions]}


@dataclass(frozen=True, slots=True)
class ObligationResult:
    status: str
    program_id: str
    registry_id: str
    replay_id: str
    positive_mask: int
    negative_mask: int
    relevant_mask: int
    unknown_mask: int
    conflict_mask: int
    out_of_scope_conflict_mask: int
    conflicts: tuple[Proposition, ...]
    out_of_scope_conflicts: tuple[Proposition, ...]
    minimal_plans: tuple[CompletionPlan, ...]
    _max_output_bytes: int

    @property
    def minimal_plan_masks(self) -> tuple[int, ...]:
        return tuple(plan.mask for plan in self.minimal_plans)

    @property
    def projection(self) -> str | None:
        return {"LICENSED": "P", "REJECTED": "N", "PENDING": "U", "CONFLICT": None}[self.status]

    @property
    def plans_complete(self) -> bool:
        return self.status != "CONFLICT"

    def _base_dict(self) -> dict[str, Any]:
        return {
            "scope": "DECLARED_FINITE_POSITIVE_FORMULA", "version": OBLIGATION_VERSION,
            "status": self.status, "projection": self.projection,
            "program_id": self.program_id, "registry_id": self.registry_id,
            "replay_id": self.replay_id, "positive_mask": self.positive_mask,
            "negative_mask": self.negative_mask, "relevant_mask": self.relevant_mask,
            "unknown_mask": self.unknown_mask, "conflict_mask": self.conflict_mask,
            "out_of_scope_conflict_mask": self.out_of_scope_conflict_mask,
            "out_of_scope_conflicts": [],
            "plans_complete_within_declared_formula": self.plans_complete,
            "minimal_plan_masks": [], "minimal_plans": [], "residuals": [],
            "support_authentication": "CALLER_OR_SOURCE_CHECKER_RESPONSIBILITY",
        }

    def _check_output_budget(self) -> int:
        """Exact compact UTF-8 JSON size, without expanding repeated identities."""
        limit = natural(self._max_output_bytes, "max_output_bytes", maximum=32_000_000)
        size = len(_json_bytes(self._base_dict()))
        identity_sizes: dict[tuple[str, ...], int] = {}

        def add(amount: int) -> None:
            nonlocal size
            size += amount
            if size > limit:
                raise resource_limit("Named obligation output exceeds the serialized byte budget",
                                     maximum=limit, bytes_at_least=size)

        def identity_size(p: Proposition) -> int:
            # Revalidate public result identities before serializing them, too.
            if type(p) is not Proposition:
                raise NabtError("INVALID_PROPOSITION_IDENTITY", "A result requires full proposition identities")
            valid = Proposition(*(getattr(p, field) for field in _IDENTITY_FIELDS))
            key = valid.key
            if key not in identity_sizes:
                identity_sizes[key] = len(_json_bytes(valid.as_dict()))
            return identity_sizes[key]

        add(0)
        add(max(0, len(self.minimal_plans) - 1))  # Commas in the mask list.
        add(max(0, len(self.minimal_plans) - 1))  # Commas in the plan list.
        for plan in self.minimal_plans:
            add(len(str(plan.mask)))
            add(len(_json_bytes({"mask": plan.mask, "propositions": []})))
            add(max(0, len(plan.propositions) - 1))
            for p in plan.propositions:
                add(identity_size(p))
        add(max(0, len(self.out_of_scope_conflicts) - 1))
        for p in self.out_of_scope_conflicts:
            add(identity_size(p))
        add(max(0, len(self.conflicts) - 1))
        conflict_shell = len(_json_bytes({"kind": "CONFLICTING_SUPPORT", "proposition": {}})) - 2
        for p in self.conflicts:
            add(conflict_shell + identity_size(p))
        return size

    def as_dict(self) -> dict[str, Any]:
        self._check_output_budget()
        return {
            **self._base_dict(),
            "out_of_scope_conflicts": [p.as_dict() for p in self.out_of_scope_conflicts],
            "minimal_plan_masks": list(self.minimal_plan_masks),
            "minimal_plans": [plan.as_dict() for plan in self.minimal_plans],
            "residuals": [{"kind": "CONFLICTING_SUPPORT", "proposition": p.as_dict()}
                          for p in self.conflicts],
        }


class _Budget:
    def __init__(self, limits: Limits) -> None:
        self.limits = limits
        self.candidates = 0
        self.comparisons = 0

    def reserve(self, count: int) -> None:
        # This precedes constructing an AND Cartesian product or OR union.
        if count > self.limits.max_candidates - self.candidates:
            raise resource_limit("Obligation expansion exceeds the candidate budget",
                                 maximum=self.limits.max_candidates,
                                 already_used=self.candidates, next_expansion=count)
        self.candidates += count

    def minimize(self, candidates: Iterable[int]) -> tuple[int, ...]:
        # Exact equality deduplication precedes strict-containment minimization.
        distinct = sorted(set(candidates), key=lambda x: (x.bit_count(), x))
        minimal: list[int] = []
        for candidate in distinct:
            dominated = False
            for smaller in minimal:
                if self.comparisons >= self.limits.max_comparisons:
                    raise resource_limit("Obligation minimization exceeds the comparison budget",
                                         maximum=self.limits.max_comparisons)
                self.comparisons += 1
                if smaller & candidate == smaller:
                    dominated = True
                    break
            if not dominated:
                if len(minimal) >= self.limits.max_plans:
                    raise resource_limit("Obligation family exceeds the minimal-plan budget",
                                         maximum=self.limits.max_plans)
                minimal.append(candidate)
        return tuple(minimal)


@dataclass(frozen=True, slots=True, init=False)
class CompiledObligations:
    """Validated finite program, preserving names and all minimal alternatives.

    Construction snapshots the input identities and syntax. No caller-provided
    digest, status, or precomputed plan family is accepted as authority.
    """

    registry: PropositionRegistry
    instructions: tuple[tuple[str, int], ...]
    relevant_mask: int
    contexts: tuple[str, ...]
    allowed_contexts: tuple[str, ...]
    limits: Limits
    program_id: str
    _source_snapshot: tuple[Any, ...]

    def __init__(self, formula: Formula, registry: PropositionRegistry, *,
                 allowed_contexts: Iterable[str] = (), limits: Limits = Limits()) -> None:
        if type(registry) is not PropositionRegistry:
            raise NabtError("INVALID_PROPOSITION_REGISTRY", "Compilation requires a PropositionRegistry")
        if type(limits) is not Limits:
            raise NabtError("INVALID_OBLIGATION_LIMIT", "Compilation requires validated Limits")
        checked_limits = Limits(**{field: getattr(limits, field) for field in Limits.__dataclass_fields__})
        if len(registry.propositions) > checked_limits.max_atoms:
            raise resource_limit("Compilation exceeds the declared atom budget", maximum=checked_limits.max_atoms)
        snapshot = PropositionRegistry(registry.propositions)
        permitted: set[str] = set()
        try:
            context_iterator = iter(allowed_contexts)
        except TypeError as exc:
            raise NabtError("INVALID_CONTEXT_PERMISSION", "Context permissions must be an iterable") from exc
        if isinstance(allowed_contexts, (str, bytes)):
            raise NabtError("INVALID_CONTEXT_PERMISSION", "Pass explicit context identities, not a string")
        for count, context in enumerate(context_iterator, 1):
            if count > checked_limits.max_atoms:
                raise resource_limit("Context permissions exceed the declared atom budget")
            permitted.add(_text(context, "allowed_context"))
        contexts: set[str] = set()
        indices = {p.key: i for i, p in enumerate(snapshot.propositions)}
        instructions: list[tuple[str, int]] = []
        source_tokens: list[tuple[Any, ...]] = []
        relevant = 0
        active: set[int] = set()
        stack: list[tuple[object, int, bool]] = [(formula, 1, False)]
        visited = 0
        while stack:
            node, depth, leaving = stack.pop()
            if leaving:
                active.remove(id(node))
                operation = "and" if type(node) is And else "or"
                instructions.append((operation, 0))
                source_tokens.append((operation,))
                continue
            visited += 1
            if visited > checked_limits.max_nodes or depth > checked_limits.max_depth:
                raise resource_limit("Formula exceeds its node or depth budget",
                                     max_nodes=checked_limits.max_nodes, max_depth=checked_limits.max_depth)
            if id(node) in active:
                raise NabtError("CYCLIC_FORMULA", "A positive formula must be a finite tree")
            if type(node) is Constant:
                if type(node.value) is not bool:
                    raise NabtError("INVALID_FORMULA", "A formula constant must be a boolean")
                operation = "true" if node.value else "false"
                instructions.append((operation, 0))
                source_tokens.append((operation,))
            elif type(node) is Atom:
                if type(node.proposition) is not Proposition:
                    raise NabtError("INVALID_PROPOSITION_IDENTITY", "A formula atom needs a full Proposition identity")
                proposition = Proposition(*(getattr(node.proposition, field) for field in _IDENTITY_FIELDS))
                if proposition.key not in indices:
                    raise NabtError("UNREGISTERED_PROPOSITION", "The formula contains an unregistered full identity",
                                    details={"proposition": proposition.as_dict()})
                index = indices[proposition.key]
                relevant |= 1 << index
                contexts.add(proposition.context)
                instructions.append(("atom", index))
                source_tokens.append(("atom", proposition.key))
            elif type(node) in (And, Or):
                active.add(id(node))
                stack.append((node, depth, True))
                stack.append((node.right, depth + 1, False))
                stack.append((node.left, depth + 1, False))
            else:
                raise NabtError("INVALID_FORMULA", "Only Constant, Atom, And, and Or are allowed")
        if (len(contexts) > 1 and not contexts <= permitted) or (permitted and not contexts <= permitted):
            raise NabtError("CONTEXT_MISMATCH", "Combining these contexts requires explicit permission",
                            details={"formula_contexts": sorted(contexts), "allowed_contexts": sorted(permitted)})
        program = tuple(instructions)
        permissions = tuple(sorted(permitted))
        values = {"registry": snapshot, "instructions": program, "relevant_mask": relevant,
                  "contexts": tuple(sorted(contexts)), "allowed_contexts": permissions,
                  "limits": checked_limits,
                  "program_id": _digest([OBLIGATION_VERSION, snapshot.registry_id, program, permissions]),
                  "_source_snapshot": (tuple(p.key for p in snapshot.propositions),
                                       tuple(source_tokens), permissions,
                                       tuple(getattr(checked_limits, field)
                                             for field in Limits.__dataclass_fields__))}
        for field, value in values.items():
            object.__setattr__(self, field, value)

    def _replay(self) -> CompiledObligations:
        """Rebuild from tuple-only named inputs, then compare every derived field.

        Frozen dataclasses are not a security boundary: ``object.__setattr__``
        can bypass them. A hash match alone is also insufficient. Replay checks
        syntax, identity binding, contexts, limits, and the actual computation.
        Changing every input into another coherent program is another mathematical
        query; neither query authenticates linguistic evidence.
        """
        invalid = NabtError("INVALID_COMPILED_OBLIGATIONS",
                            "Compiled obligation data no longer matches replay of its bound inputs")
        try:
            if type(self) is not CompiledObligations:
                raise invalid
            snapshot = self._source_snapshot
            if type(snapshot) is not tuple or len(snapshot) != 4:
                raise invalid
            keys, tokens, permissions, limit_values = snapshot
            if (type(keys) is not tuple or len(keys) > MAX_REGISTRY_ATOMS
                    or type(tokens) is not tuple or not 0 < len(tokens) <= 65_536
                    or type(permissions) is not tuple or len(permissions) > MAX_REGISTRY_ATOMS
                    or type(limit_values) is not tuple or len(limit_values) != len(Limits.__dataclass_fields__)):
                raise invalid
            restored_limits = Limits(*limit_values)
            restored_entries = []
            for key in keys:
                if type(key) is not tuple or len(key) != len(_IDENTITY_FIELDS):
                    raise invalid
                restored_entries.append(Proposition(*key))
            restored_registry = PropositionRegistry(restored_entries)
            syntax: list[Formula] = []
            for token in tokens:
                if type(token) is not tuple or not token or type(token[0]) is not str:
                    raise invalid
                operation = token[0]
                if operation in ("true", "false") and len(token) == 1:
                    syntax.append(Constant(operation == "true"))
                elif operation == "atom" and len(token) == 2:
                    key = token[1]
                    if type(key) is not tuple or len(key) != len(_IDENTITY_FIELDS):
                        raise invalid
                    syntax.append(Atom(Proposition(*key)))
                elif operation in ("and", "or") and len(token) == 1 and len(syntax) >= 2:
                    right, left = syntax.pop(), syntax.pop()
                    syntax.append(And(left, right) if operation == "and" else Or(left, right))
                else:
                    raise invalid
            if len(syntax) != 1:
                raise invalid
            replayed = CompiledObligations(syntax[0], restored_registry,
                                          allowed_contexts=permissions, limits=restored_limits)
            if (type(self.registry) is not PropositionRegistry
                    or type(self.registry.propositions) is not tuple
                    or len(self.registry.propositions) != len(replayed.registry.propositions)
                    or type(self.registry.registry_id) is not str
                    or self.registry.registry_id != replayed.registry.registry_id):
                raise invalid
            for actual, expected in zip(self.registry.propositions, replayed.registry.propositions):
                if type(actual) is not Proposition:
                    raise invalid
                validated = Proposition(*(getattr(actual, field) for field in _IDENTITY_FIELDS))
                if validated.key != expected.key:
                    raise invalid
            if type(self.instructions) is not tuple or len(self.instructions) != len(replayed.instructions):
                raise invalid
            for actual, expected in zip(self.instructions, replayed.instructions):
                if (type(actual) is not tuple or len(actual) != 2
                        or type(actual[0]) is not str or type(actual[1]) is not int or actual != expected):
                    raise invalid
            if type(self.relevant_mask) is not int or self.relevant_mask != replayed.relevant_mask:
                raise invalid
            for field in ("contexts", "allowed_contexts"):
                actual, expected = getattr(self, field), getattr(replayed, field)
                if (type(actual) is not tuple or len(actual) != len(expected)
                        or any(type(s) is not str for s in actual) or actual != expected):
                    raise invalid
            if type(self.limits) is not Limits:
                raise invalid
            for field in Limits.__dataclass_fields__:
                actual = getattr(self.limits, field)
                if type(actual) is not int or actual != getattr(replayed.limits, field):
                    raise invalid
            if type(self.program_id) is not str or self.program_id != replayed.program_id:
                raise invalid
            if snapshot != replayed._source_snapshot:
                raise invalid
            return replayed
        except (NabtError, AttributeError, IndexError, TypeError, ValueError, OverflowError) as exc:
            if exc is invalid:
                raise
            raise invalid from exc

    def evaluate(self, positive_mask: int = 0, negative_mask: int = 0) -> ObligationResult:
        replayed = self._replay()
        return replayed._evaluate_replayed(positive_mask, negative_mask)

    def _evaluate_replayed(self, positive_mask: int, negative_mask: int) -> ObligationResult:
        positive = natural(positive_mask, "positive_mask", maximum=self.registry.universe_mask)
        negative = natural(negative_mask, "negative_mask", maximum=self.registry.universe_mask)
        conflict = positive & negative & self.relevant_mask
        outside_conflict = positive & negative & ~self.relevant_mask
        unknown = self.relevant_mask & ~(positive | negative)
        replay = _digest([OBLIGATION_VERSION, self.program_id, positive, negative])
        if conflict:
            # Do not turn inconsistent support into unknown or prioritize one side.
            masks: tuple[int, ...] = ()
            status = "CONFLICT"
        else:
            budget = _Budget(self.limits)
            families: list[tuple[int, ...]] = []
            for operation, index in self.instructions:
                if operation == "true":
                    families.append((0,))
                elif operation == "false":
                    families.append(())
                elif operation == "atom":
                    bit = 1 << index
                    families.append((0,) if positive & bit else (() if negative & bit else (bit,)))
                else:
                    right, left = families.pop(), families.pop()
                    if operation == "and":
                        if not left or not right:
                            family = ()
                        elif left == (0,):
                            family = right
                        elif right == (0,):
                            family = left
                        else:
                            budget.reserve(len(left) * len(right))
                            family = budget.minimize(x | y for x in left for y in right)
                    else:
                        if left == (0,) or right == (0,):
                            family = (0,)
                        elif not left:
                            family = right
                        elif not right:
                            family = left
                        else:
                            budget.reserve(len(left) + len(right))
                            family = budget.minimize((*left, *right))
                    families.append(family)
            masks = families[0]
            status = "LICENSED" if masks == (0,) else ("REJECTED" if not masks else "PENDING")
        result = ObligationResult(
            status, self.program_id, self.registry.registry_id, replay, positive, negative,
            self.relevant_mask, unknown, conflict, outside_conflict,
            self.registry.names(conflict), self.registry.names(outside_conflict),
            tuple(CompletionPlan(mask, self.registry.names(mask)) for mask in masks),
            self.limits.max_output_bytes,
        )
        result._check_output_budget()
        return result

    def as_dict(self) -> dict[str, Any]:
        replayed = self._replay()
        return {"version": OBLIGATION_VERSION, "program_id": replayed.program_id,
                "registry": replayed.registry.as_dict(), "instructions": [list(i) for i in replayed.instructions],
                "relevant_mask": replayed.relevant_mask, "contexts": list(replayed.contexts),
                "allowed_contexts": list(replayed.allowed_contexts),
                "limits": {field: getattr(replayed.limits, field) for field in Limits.__dataclass_fields__}}


def compile_obligations(formula: Formula, registry: PropositionRegistry, *,
                        allowed_contexts: Iterable[str] = (), limits: Limits = Limits()) -> CompiledObligations:
    return CompiledObligations(formula, registry, allowed_contexts=allowed_contexts, limits=limits)


def evaluate_obligations(formula: Formula, registry: PropositionRegistry,
                         positive_mask: int = 0, negative_mask: int = 0, *,
                         allowed_contexts: Iterable[str] = (), limits: Limits = Limits()) -> ObligationResult:
    return compile_obligations(formula, registry, allowed_contexts=allowed_contexts,
                               limits=limits).evaluate(positive_mask, negative_mask)
