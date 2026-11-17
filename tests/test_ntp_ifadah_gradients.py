"""Differentiate the portable program scorer independently of the training tape.

The numerical objective is -log(public portable candidate probability), not
the trainer's loss implementation. No fitting or artifact writes occur here.
"""
from copy import deepcopy
import importlib.util
import math
import unittest

from tools.lexical_training import ntp_ifadah as net
from tools.lexical_training import ntp_recursive as cells
from tools.lexical_training import train_ntp_ifadah as training


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'training-only NumPy required')
class PortableProgramGradients(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol, _, _ = training.inputs()

    def setUp(self):
        self.parameters = training.initialize(self.protocol['seed'])

    def portable_scores(self, groups):
        return net.scores(training.model(self.parameters, self.protocol), groups)

    def portable_loss(self, groups, target):
        probability = next(row['score'] for row in self.portable_scores(groups)
                           if row['name'] == target)
        return -math.log(probability)

    def test_single_word_cross_word_and_repeated_cell_gradients(self):
        import numpy as np

        cases = (
            ([cells.parse_word('هَلْ')], 'ask'),
            ([cells.parse_word('هَلْ'), cells.parse_word('لَيْسَ')], 'ask_negation'),
            # Repeated carrier/state visits require summing their contributions;
            # these are numerical A116 inputs, not new linguistic attestations.
            ([[100, 91, 100], [88, 111, 44]], 'wish'),
        )
        expected_groups = {'bits', 'carrier', 'mark', 'compose', 'bias',
                           'program_force', 'program_frame'}
        epsilon = 1e-5
        for groups, target in cases:
            with self.subTest(groups=groups, target=target):
                original = deepcopy(groups)
                analytic_loss, gradients = training.loss_grad(self.parameters, groups, target)
                self.assertEqual(set(gradients), expected_groups)
                self.assertAlmostEqual(analytic_loss, self.portable_loss(groups, target), places=12)
                for name, gradient in gradients.items():
                    self.assertTrue(np.isfinite(gradient).all(), name)
                    self.assertGreater(float(np.linalg.norm(gradient)), 0., name)
                    largest = int(np.abs(gradient).argmax())
                    rng = np.random.default_rng(22)
                    indices = {largest, *map(int, rng.choice(
                        gradient.size, min(3, gradient.size), replace=False))}
                    for flat_index in sorted(indices):
                        index = np.unravel_index(flat_index, gradient.shape)
                        old = self.parameters[name][index]
                        try:
                            self.parameters[name][index] = old + epsilon
                            plus = self.portable_loss(groups, target)
                            self.parameters[name][index] = old - epsilon
                            minus = self.portable_loss(groups, target)
                        finally:
                            self.parameters[name][index] = old
                        numerical = (plus - minus) / (2 * epsilon)
                        self.assertLess(abs(float(gradient[index]) - numerical),
                                        self.protocol['gradient_check_tolerance'],
                                        (name, index, groups))
                self.assertEqual(groups, original)

    def test_target_changes_loss_not_features_parameters_or_candidate_domain(self):
        import numpy as np

        groups = [cells.parse_word('هَلْ'), cells.parse_word('لَيْسَ')]
        original_groups = deepcopy(groups)
        original_parameters = {key: value.copy() for key, value in self.parameters.items()}
        before = self.portable_scores(groups)
        first_loss, first = training.loss_grad(self.parameters, groups, 'ask_negation')
        second_loss, second = training.loss_grad(self.parameters, groups, 'wish')
        self.assertNotAlmostEqual(first_loss, second_loss, places=9)
        for name in first:
            self.assertGreater(float(np.linalg.norm(first[name] - second[name])), 0., name)
            np.testing.assert_array_equal(self.parameters[name], original_parameters[name])
        self.assertEqual(groups, original_groups)
        self.assertEqual(self.portable_scores(groups), before)
        self.assertEqual([row['name'] for row in before], list(net.CANDIDATES))
        self.assertAlmostEqual(sum(row['score'] for row in before), 1., places=14)

    def test_portable_input_preserves_cell_order_word_order_and_grouping(self):
        groups = [[100, 91], [88, 111, 44]]
        baseline = [row['score'] for row in self.portable_scores(groups)]
        variants = (
            [list(reversed(groups[0])), groups[1]],
            list(reversed(groups)),
            [groups[0] + groups[1]],
        )
        for changed in variants:
            with self.subTest(groups=changed):
                probabilities = [row['score'] for row in self.portable_scores(changed)]
                self.assertGreater(max(abs(a - b) for a, b in zip(
                    baseline, probabilities, strict=True)), 1e-8)


if __name__ == '__main__':
    unittest.main()
