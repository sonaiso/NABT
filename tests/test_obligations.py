"""Independent truth-assignment enumeration, identity boundaries, and budgets."""

from dataclasses import FrozenInstanceError, replace
from itertools import product
import json
import random
import unittest

from nabt.errors import NabtError
from nabt.obligations import (
    And, Atom, Constant, FALSE, Limits, Or, Proposition, PropositionRegistry, TRUE,
    all_of, any_of, compile_obligations, evaluate_obligations,
)


def proposition(name, **changes):
    fields = dict(name=name, source="sha256:source-v1", occurrence="word:3",
                  reading="reading:v1", context="context:one",
                  definition="definition:" + name, policy="policy:one")
    fields.update(changes)
    return Proposition(**fields)


def truth(formula, present):
    """Ordinary truth on a set of full identities; no residual recurrence."""
    if type(formula) is Constant:
        return formula.value
    if type(formula) is Atom:
        return formula.proposition in present
    if type(formula) is And:
        return truth(formula.left, present) and truth(formula.right, present)
    if type(formula) is Or:
        return truth(formula.left, present) or truth(formula.right, present)
    raise AssertionError("Oracle received an invalid formula")


def referenced(formula):
    if type(formula) is Constant:
        return set()
    if type(formula) is Atom:
        return {formula.proposition}
    return referenced(formula.left) | referenced(formula.right)


def enumerate_reference(formula, registry, positive, negative):
    """Enumerate subsets of unknown identities, then compare set inclusion.

    This oracle never invokes the compiler, its minimizer, or its bitwise
    conjunction. It is deliberately limited to small independently chosen domains.
    """
    identities = registry.propositions
    positive_names = {p for i, p in enumerate(identities) if positive & (1 << i)}
    negative_names = {p for i, p in enumerate(identities) if negative & (1 << i)}
    relevant = referenced(formula)
    if positive_names & negative_names & relevant:
        return "CONFLICT", set()
    unknown = tuple(relevant - positive_names - negative_names)
    if len(unknown) > 10:
        raise AssertionError("Reference enumeration is limited to ten unknowns")
    sufficient = set()
    for selected in product((False, True), repeat=len(unknown)):
        additional = frozenset(p for p, keep in zip(unknown, selected) if keep)
        if truth(formula, positive_names | additional):
            sufficient.add(additional)
    minimal = {p for p in sufficient if not any(q < p for q in sufficient)}
    status = "LICENSED" if frozenset() in minimal else ("PENDING" if minimal else "REJECTED")
    masks = {sum(1 << i for i, p in enumerate(identities) if p in plan) for plan in minimal}
    return status, masks


def all_depth_two_formulas(a, b):
    """The exact finite grammar, as syntax, not deduplicated by semantics."""
    leaves = (TRUE, FALSE, Atom(a), Atom(b))
    one = leaves + tuple(op(l, r) for op in (And, Or) for l in leaves for r in leaves)
    return leaves + tuple(op(l, r) for op in (And, Or) for l in one for r in one)


class ObligationTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c = (proposition(name) for name in "ABC")
        self.registry = PropositionRegistry((self.a, self.b, self.c))

    def assert_error(self, code, action, *, status="REJECT"):
        with self.assertRaises(NabtError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(caught.exception.status, status)
        return caught.exception

    def test_named_alternative_obligations_and_projection(self):
        formula = And(Atom(self.c), Or(Atom(self.a), Atom(self.b)))
        program = compile_obligations(formula, self.registry)
        pending = program.evaluate(self.registry.bit(self.c))
        self.assertEqual(pending.status, "PENDING")
        self.assertEqual(pending.projection, "U")
        self.assertEqual({plan.names for plan in pending.minimal_plans}, {("A",), ("B",)})
        self.assertEqual(set(pending.minimal_plan_masks), {self.registry.bit(self.a), self.registry.bit(self.b)})
        self.assertEqual(program.evaluate(self.registry.mask((self.a, self.c))).status, "LICENSED")
        self.assertEqual(program.evaluate(negative_mask=self.registry.bit(self.c)).status, "REJECTED")

    def test_equality_deduplication_absorption_and_correlations(self):
        duplicated = evaluate_obligations(Or(Atom(self.a), Atom(self.a)), self.registry)
        self.assertEqual(duplicated.minimal_plan_masks, (self.registry.bit(self.a),))
        absorbed = evaluate_obligations(Or(Atom(self.a), And(Atom(self.a), Atom(self.b))), self.registry)
        self.assertEqual(absorbed.minimal_plan_masks, duplicated.minimal_plan_masks)
        shared = And(Or(Atom(self.a), Atom(self.b)), Or(Atom(self.a), Atom(self.c)))
        result = evaluate_obligations(shared, self.registry)
        self.assertEqual(set(result.minimal_plan_masks), {self.registry.bit(self.a),
                                                        self.registry.mask((self.b, self.c))})
        self.assertNotIn(self.registry.bit(self.b), result.minimal_plan_masks)
        self.assertNotIn(self.registry.bit(self.c), result.minimal_plan_masks)

    def test_unknown_is_not_false_and_constants_are_exact(self):
        program = compile_obligations(Atom(self.a), self.registry)
        self.assertEqual(program.evaluate().status, "PENDING")
        self.assertEqual(program.evaluate(negative_mask=self.registry.bit(self.a)).status, "REJECTED")
        self.assertEqual(evaluate_obligations(TRUE, PropositionRegistry(())).minimal_plan_masks, (0,))
        self.assertEqual(evaluate_obligations(FALSE, PropositionRegistry(())).minimal_plan_masks, ())
        self.assertEqual(evaluate_obligations(all_of(), self.registry).status, "LICENSED")
        self.assertEqual(evaluate_obligations(any_of(), self.registry).status, "REJECTED")

    def test_conflict_precedes_even_absorbing_constants(self):
        bit = self.registry.bit(self.a)
        for formula in (Atom(self.a), Or(TRUE, Atom(self.a)), And(FALSE, Atom(self.a))):
            result = evaluate_obligations(formula, self.registry, bit, bit)
            self.assertEqual(result.status, "CONFLICT")
            self.assertIsNone(result.projection)
            self.assertFalse(result.plans_complete)
            self.assertEqual(result.conflicts, (self.a,))
            self.assertEqual(result.minimal_plan_masks, ())
            self.assertEqual(result.as_dict()["residuals"][0]["kind"], "CONFLICTING_SUPPORT")

    def test_unrelated_conflicts_are_reported_without_changing_this_claim(self):
        conflict = self.registry.bit(self.b)
        result = evaluate_obligations(Atom(self.a), self.registry, conflict, conflict)
        self.assertEqual(result.status, "PENDING")
        self.assertEqual(result.conflict_mask, 0)
        self.assertEqual(result.out_of_scope_conflict_mask, conflict)
        self.assertEqual(result.out_of_scope_conflicts, (self.b,))
        self.assertTrue(result.plans_complete)

    def test_full_identity_binding_covers_every_field(self):
        for field in ("name", "source", "occurrence", "reading", "context", "definition", "policy"):
            changed = replace(self.a, **{field: "other:" + field})
            registry = PropositionRegistry((self.a, changed))
            self.assertNotEqual(registry.bit(self.a), registry.bit(changed))
            self.assertNotEqual(self.a.proposition_id, changed.proposition_id)
            unknown = evaluate_obligations(Atom(changed), registry, registry.bit(self.a))
            self.assertEqual(unknown.status, "PENDING")
            self.assertEqual(unknown.minimal_plans[0].propositions, (changed,))
            self.assert_error("UNREGISTERED_PROPOSITION", lambda: compile_obligations(Atom(changed), self.registry))

    def test_context_combination_requires_explicit_permission(self):
        other = replace(self.b, context="context:two")
        registry = PropositionRegistry((self.a, other))
        formula = And(Atom(self.a), Atom(other))
        self.assert_error("CONTEXT_MISMATCH", lambda: compile_obligations(formula, registry))
        self.assert_error("CONTEXT_MISMATCH", lambda: compile_obligations(formula, registry,
                                                                         allowed_contexts=("context:one",)))
        program = compile_obligations(formula, registry, allowed_contexts=("context:one", "context:two"))
        self.assertEqual(program.evaluate().minimal_plan_masks, (registry.universe_mask,))
        # Unreferenced registry entries from other contexts do not mix this claim.
        self.assertEqual(compile_obligations(Atom(self.a), registry).contexts, ("context:one",))

    def test_registry_order_does_not_change_numbers_or_replay(self):
        reversed_registry = PropositionRegistry((self.c, self.a, self.b))
        formula = Or(Atom(self.a), Atom(self.b))
        p = compile_obligations(formula, self.registry)
        q = compile_obligations(formula, reversed_registry)
        self.assertEqual(p.as_dict(), q.as_dict())
        self.assertEqual(p.evaluate().as_dict(), q.evaluate().as_dict())
        self.assertNotEqual(p.evaluate().replay_id, p.evaluate(self.registry.bit(self.c)).replay_id)
        permitted = compile_obligations(formula, self.registry, allowed_contexts=(self.a.context,))
        self.assertNotEqual(p.program_id, permitted.program_id)
        self.assertEqual(len(p.program_id), 64)

    def test_compilation_snapshots_caller_objects(self):
        original = proposition("local")
        registry = PropositionRegistry((original,))
        atom = Atom(original)
        program = compile_obligations(atom, registry)
        expected = program.evaluate().as_dict()
        # Forced mutation of untrusted construction inputs cannot mutate the program.
        object.__setattr__(original, "name", "changed")
        object.__setattr__(atom, "proposition", self.b)
        object.__setattr__(registry.propositions[0], "context", "changed")
        self.assertEqual(program.evaluate().as_dict(), expected)
        with self.assertRaises(FrozenInstanceError):
            program.program_id = "caller-label"

    def test_forced_mutation_of_compiled_values_is_rejected_at_consumption(self):
        mutations = (
            lambda p: object.__setattr__(p, "instructions", (("true", 0),)),
            lambda p: object.__setattr__(p, "instructions", (("atom", False),)),
            lambda p: object.__setattr__(p, "relevant_mask", 0),
            lambda p: object.__setattr__(p, "relevant_mask", True),
            lambda p: object.__setattr__(p, "contexts", ("other-context",)),
            lambda p: object.__setattr__(p, "allowed_contexts", ("context:one",)),
            lambda p: object.__setattr__(p, "program_id", "self-certified"),
            lambda p: object.__setattr__(p, "registry", None),
            lambda p: object.__setattr__(p.registry, "registry_id", "self-certified"),
            lambda p: object.__setattr__(p.registry.propositions[0], "source", "changed-source"),
            lambda p: object.__setattr__(p.limits, "max_candidates", 2_000_000),
            lambda p: object.__setattr__(p, "_source_snapshot", ()),
        )
        for mutate in mutations:
            program = compile_obligations(Atom(self.a), self.registry)
            mutate(program)
            self.assert_error("INVALID_COMPILED_OBLIGATIONS", program.evaluate)
            self.assert_error("INVALID_COMPILED_OBLIGATIONS", program.as_dict)
        program = compile_obligations(Atom(self.a), self.registry)
        object.__setattr__(program, "relevant_mask", 0)
        self.assert_error("INVALID_COMPILED_OBLIGATIONS", lambda: program.evaluate(1, 1))
        # A matching replacement digest cannot replace replay of the bound syntax.
        replacement = compile_obligations(TRUE, self.registry)
        program = compile_obligations(Atom(self.a), self.registry)
        for field in ("instructions", "relevant_mask", "contexts", "program_id"):
            object.__setattr__(program, field, getattr(replacement, field))
        self.assert_error("INVALID_COMPILED_OBLIGATIONS", program.evaluate)

    def test_masks_and_budget_numbers_reject_booleans_and_other_domains(self):
        program = compile_obligations(Atom(self.a), self.registry)
        for bad in (True, False, -1, 1.0, "1", None):
            self.assert_error("INVALID_NATURAL", lambda: program.evaluate(bad))
            self.assert_error("INVALID_NATURAL", lambda: program.evaluate(negative_mask=bad))
            self.assert_error("INVALID_NATURAL", lambda: Limits(max_plans=bad))
        self.assert_error("OUTSIDE_DOMAIN", lambda: program.evaluate(1 << len(self.registry.propositions)))
        self.assert_error("INVALID_OBLIGATION_LIMIT", lambda: Limits(max_nodes=0))
        self.assert_error("OUTSIDE_DOMAIN", lambda: Limits(max_depth=1000))

    def test_invalid_syntax_registry_and_identities_have_named_errors(self):
        for bad in (True, 1, "A", ("atom", 0), Constant(1), And(Atom(self.a), None)):
            self.assert_error("INVALID_FORMULA", lambda: compile_obligations(bad, self.registry))
        self.assert_error("INVALID_PROPOSITION_IDENTITY", lambda: compile_obligations(Atom(0), self.registry))
        self.assert_error("INVALID_PROPOSITION_REGISTRY", lambda: compile_obligations(Atom(self.a), (self.a,)))
        self.assert_error("DUPLICATE_PROPOSITION", lambda: PropositionRegistry((self.a, self.a)))
        self.assert_error("INVALID_PROPOSITION_IDENTITY", lambda: PropositionRegistry(("A",)))
        self.assert_error("INVALID_PROPOSITION_IDENTITY", lambda: replace(self.a, source=""))
        self.assert_error("INVALID_PROPOSITION_IDENTITY", lambda: replace(self.a, policy="  "))
        self.assert_error("INVALID_UNICODE", lambda: replace(self.a, name="\ud800"))
        self.assert_error("INVALID_CONTEXT_PERMISSION", lambda: compile_obligations(Atom(self.a), self.registry,
                                                                                   allowed_contexts="context:one"))
        cycle = And(TRUE, FALSE)
        object.__setattr__(cycle, "left", cycle)
        self.assert_error("CYCLIC_FORMULA", lambda: compile_obligations(cycle, self.registry))

    def test_all_declared_depth_two_formulas_match_independent_enumeration(self):
        registry = PropositionRegistry((self.a, self.b))
        formulas = all_depth_two_formulas(self.a, self.b)
        self.assertEqual(len(formulas), 2596)
        self.assertEqual(len(set(formulas)), 2596)
        checked = 0
        # Four support states, including both: 2,596 syntax trees × 16 environments.
        for formula in formulas:
            program = compile_obligations(formula, registry)
            for positive in range(4):
                for negative in range(4):
                    expected_status, expected_masks = enumerate_reference(formula, registry, positive, negative)
                    result = program.evaluate(positive, negative)
                    self.assertEqual(result.status, expected_status, (formula, positive, negative))
                    self.assertEqual(set(result.minimal_plan_masks), expected_masks, (formula, positive, negative))
                    self.assertEqual(len(result.minimal_plan_masks), len(set(result.minimal_plan_masks)))
                    checked += 1
        self.assertEqual(checked, 41536)

    def test_random_larger_formulas_against_subset_oracle(self):
        rng = random.Random(20261023)
        identities = tuple(proposition("atom:" + str(i)) for i in range(6))
        registry = PropositionRegistry(identities)

        def build(depth):
            if depth == 0 or rng.randrange(4) == 0:
                return rng.choice((TRUE, FALSE, *(Atom(p) for p in identities)))
            return rng.choice((And, Or))(build(depth - 1), build(depth - 1))

        for _ in range(250):
            formula = build(5)
            positive, negative = rng.randrange(64), rng.randrange(64)
            expected_status, expected_masks = enumerate_reference(formula, registry, positive, negative)
            result = evaluate_obligations(formula, registry, positive, negative)
            self.assertEqual((result.status, set(result.minimal_plan_masks)), (expected_status, expected_masks))

    def test_expansion_is_preflighted_and_exhaustion_is_defer(self):
        pairs = tuple((proposition("a" + str(i)), proposition("b" + str(i))) for i in range(6))
        registry = PropositionRegistry(p for pair in pairs for p in pair)
        formula = all_of(*(Or(Atom(a), Atom(b)) for a, b in pairs))
        program = compile_obligations(formula, registry, limits=Limits(max_candidates=40))
        error = self.assert_error("RESOURCE_LIMIT", program.evaluate, status="DEFER")
        self.assertGreater(error.details["already_used"] + error.details["next_expansion"], 40)
        self.assert_error("RESOURCE_LIMIT", lambda: compile_obligations(formula, registry,
                                                                        limits=Limits(max_nodes=5)), status="DEFER")
        self.assert_error("RESOURCE_LIMIT", lambda: compile_obligations(formula, registry,
                                                                        limits=Limits(max_atoms=2)), status="DEFER")
        self.assert_error("RESOURCE_LIMIT", lambda: compile_obligations(formula, registry,
                                                                        limits=Limits(max_depth=2)), status="DEFER")
        self.assert_error("RESOURCE_LIMIT", lambda: compile_obligations(formula, registry,
                                                                        limits=Limits(max_plans=3)).evaluate(), status="DEFER")
        self.assert_error("RESOURCE_LIMIT", lambda: compile_obligations(formula, registry,
                                                                        limits=Limits(max_comparisons=1)).evaluate(), status="DEFER")
        self.assertEqual(len(compile_obligations(formula, registry).evaluate().minimal_plans), 2 ** 6)

    def test_negatives_block_only_their_named_alternatives(self):
        result = evaluate_obligations(Or(Atom(self.a), Atom(self.b)), self.registry,
                                      negative_mask=self.registry.bit(self.a))
        self.assertEqual(result.status, "PENDING")
        self.assertEqual(result.minimal_plan_masks, (self.registry.bit(self.b),))
        # A closed finite universal formula is exactly its named conjunction.
        universal = all_of(*(Atom(p) for p in self.registry.propositions))
        result = evaluate_obligations(universal, self.registry, self.registry.mask((self.a, self.b)))
        self.assertEqual(result.minimal_plan_masks, (self.registry.bit(self.c),))
        result = evaluate_obligations(universal, self.registry, negative_mask=self.registry.bit(self.a))
        self.assertEqual(result.status, "REJECTED")

    def test_exact_output_byte_preflight_includes_escaping_and_all_statuses(self):
        escaped = proposition('name:"\\\u0000', source="\u0000" * 128, definition="تعريف")
        registry = PropositionRegistry((escaped, self.a))
        formula = Or(Atom(escaped), Atom(self.a))
        program = compile_obligations(formula, registry)
        for positive in range(4):
            for negative in range(4):
                result = program.evaluate(positive, negative)
                encoded = json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")
                self.assertEqual(result._check_output_budget(), len(encoded))
        result = program.evaluate()
        needed = result._check_output_budget()
        exact = compile_obligations(formula, registry, limits=Limits(max_output_bytes=needed)).evaluate()
        self.assertEqual(exact.as_dict(), result.as_dict())
        self.assert_error("RESOURCE_LIMIT", lambda: compile_obligations(
            formula, registry, limits=Limits(max_output_bytes=needed - 1)).evaluate(), status="DEFER")

    def test_repeated_long_plan_identities_defer_before_large_serialization(self):
        identities = tuple(proposition(str(i), **{field: "x" * 8192
                                                for field in ("source", "occurrence", "reading",
                                                              "context", "definition", "policy")})
                           for i in range(20))
        registry = PropositionRegistry(identities)
        formula = all_of(*(Or(Atom(identities[i]), Atom(identities[i + 1])) for i in range(0, 20, 2)))
        # Search has only 1,024 plans, but a naive JSON payload would exceed 500 MB.
        error = self.assert_error("RESOURCE_LIMIT", lambda: compile_obligations(formula, registry).evaluate(),
                                  status="DEFER")
        self.assertIn("serialized byte budget", error.message)
        self.assertEqual(error.details["maximum"], 8_000_000)


if __name__ == "__main__":
    unittest.main()
