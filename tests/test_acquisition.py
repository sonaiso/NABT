from dataclasses import replace
import random
import unittest

from nabt.acquisition import Branch, CheckedPredictor, DecisionDAG, Leaf, acquire_transition_model, verify_candidate
from nabt.errors import NabtError
from tests import oracle


class AcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acquired = acquire_transition_model()
        cls.model = cls.acquired.model

    def test_learner_closes_all_transitions_against_independent_oracle(self):
        self.assertIsNotNone(self.model)
        self.assertTrue(self.model.verification.accepted)
        self.assertEqual(self.model.verification.checked_inputs, 97 * 116)
        self.assertGreater(self.acquired.rounds[0].mismatches, 0)
        self.assertEqual(self.acquired.rounds[-1].mismatches, 0)
        for q in range(97):
            for a in range(116):
                self.assertEqual(self.model.transition(q, a), oracle.transition(q, a))

    def test_whole_sequences_and_modes_not_present_as_training_examples(self):
        rng = random.Random(20261022)
        examples = [(), (84, 3), (85, 3), (84, 11, 7), (4,) * 4096]
        examples += [tuple(rng.randrange(116) for _ in range(n)) for n in (1, 2, 3, 4, 10, 50, 300)]
        for mode in ("waqf", "wasl"):
            for start in (0, 1, 4, 35, 67, 96):
                for cells in examples:
                    accepted, q, w = oracle.run(cells, mode, start)
                    self.assertEqual(self.model.run(cells, mode=mode, start_state=start), (q, w, accepted))

    def test_a_single_changed_reachable_leaf_is_refuted(self):
        # Weight corruption must fail even when the target state remains intact.
        for i, leaf in enumerate(self.model.nodes):
            if type(leaf) is Leaf:
                values = list(self.model.nodes)
                values[i] = Leaf(leaf.target, 1 - leaf.weight)
                candidate = DecisionDAG(tuple(values))
                report = verify_candidate(candidate)
                if not report.accepted:
                    self.assertGreater(report.mismatch_count, 0)
                    with self.assertRaises(NabtError) as caught:
                        CheckedPredictor(candidate)
                    self.assertEqual(caught.exception.code, "CANDIDATE_REFUTED")
                    break
        else:
            self.fail("No reachable leaf mutation was detected")

    def test_candidate_nodes_are_not_shared_with_checked_model(self):
        candidate = DecisionDAG(self.model.nodes)
        checked = CheckedPredictor(candidate)
        before = checked.run((84, 8, 4))
        self.assertTrue(all(a is not b for a, b in zip(candidate.nodes, checked.nodes)))
        root = candidate.nodes[-1]
        self.assertIs(type(root), Branch)
        self.assertFalse(hasattr(root, "__dict__"))
        # Deliberately circumvent frozen assignment on the UNTRUSTED original.
        # Its copied verifier snapshot must remain unchanged.
        old = root.one
        try:
            object.__setattr__(root, "one", root.zero)
            self.assertEqual(checked.run((84, 8, 4)), before)
            self.assertTrue(verify_candidate(DecisionDAG(checked.nodes)).accepted)
        finally:
            object.__setattr__(root, "one", old)

    def test_budget_exhaustion_has_no_approved_model(self):
        result = acquire_transition_model(max_rounds=1)
        self.assertEqual(result.status, "DEFER")
        self.assertIsNone(result.model)
        self.assertEqual(result.residual, "COUNTEREXAMPLES_REMAIN_WITHIN_BUDGET")
        for value in (0, True, -1, 1025):
            with self.assertRaises(NabtError):
                acquire_transition_model(max_rounds=value)

    def test_ast_and_input_domains_are_closed(self):
        malformed = ((Leaf(True, 1),), (Leaf(97, 1),), (Leaf(0, 2),),
                     (Branch(0, 0, 0),), (Leaf(0, 1), Branch(14, 0, 0)))
        for nodes in malformed:
            with self.assertRaises(NabtError):
                DecisionDAG(nodes)
        with self.assertRaises(NabtError):
            verify_candidate(lambda q, a: (q, 1))
        for state, cell in ((97, 0), (0, 116), (True, 0), (0, False)):
            with self.assertRaises(NabtError):
                self.model.transition(state, cell)


if __name__ == "__main__":
    unittest.main()
