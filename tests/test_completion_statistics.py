"""Independent closed forms and NIST reference checks for completion bounds."""

import math
import unittest

from tools.lexical_training.completion_statistics import (
    binomial_lower,
    binomial_upper,
    paired_bounds,
    zero_error_required_n,
)


class CompletionStatistics(unittest.TestCase):
    def test_no_observations_have_no_bound(self):
        self.assertIsNone(binomial_upper(0, 0))
        self.assertIsNone(binomial_lower(0, 0))
        empty = paired_bounds([], [])
        self.assertEqual(empty["n"], 0)
        self.assertEqual(empty["gained"], 0)
        for field in ("delta", "delta_lower", "retention_lower"):
            self.assertIsNone(empty[field])

    def test_zero_error_closed_form_and_sample_plans(self):
        for n in (1, 10, 100, 299, 2995):
            self.assertAlmostEqual(binomial_upper(0, n), 1.0 - 0.05 ** (1.0 / n), places=14)
        self.assertEqual(zero_error_required_n(0.01), 299)
        self.assertEqual(zero_error_required_n(0.005), 598)
        self.assertEqual(zero_error_required_n(0.001), 2995)
        self.assertEqual(zero_error_required_n(0.001, alpha=0.005), 5296)
        self.assertGreater(binomial_upper(0, 2994), 0.001)
        self.assertLessEqual(binomial_upper(0, 2995), 0.001)
        self.assertGreater(binomial_upper(0, 10), 0.25)

    def test_all_successes_and_all_failures(self):
        self.assertEqual(binomial_upper(10, 10), 1.0)
        self.assertEqual(binomial_lower(0, 10), 0.0)
        self.assertAlmostEqual(binomial_lower(10, 10), 0.05 ** 0.1, places=14)
        self.assertGreaterEqual(binomial_lower(299, 299), 0.99)
        self.assertLess(binomial_lower(298, 298), 0.99)

    def test_sample_plan_integer_boundary_agrees_with_the_bound(self):
        self.assertEqual(zero_error_required_n(0.5, alpha=0.5), 1)
        self.assertEqual(binomial_upper(0, 1, alpha=0.5), 0.5)
        self.assertEqual(zero_error_required_n(0.95, alpha=0.05), 1)
        self.assertLessEqual(binomial_upper(0, 1, alpha=0.05), 0.95)

    def test_small_sample_polynomial_oracles(self):
        # n=2, k=1: CDF=1-p^2.  This is independent of the production sum.
        for alpha in (0.001, 0.05, 0.5, 0.9):
            self.assertAlmostEqual(binomial_upper(1, 2, alpha), math.sqrt(1 - alpha), places=13)
            self.assertAlmostEqual(binomial_lower(1, 2, alpha), 1 - math.sqrt(1 - alpha), places=13)
        self.assertAlmostEqual(binomial_upper(1, 3, 0.5), 0.5, places=14)

    def test_nist_twenty_trials_four_defects_ninety_percent_interval(self):
        # NIST/SEMATECH prc241: two-sided 90% interval uses .05 in each tail.
        # The source prints six decimal places, so its rounding is respected.
        self.assertAlmostEqual(binomial_lower(4, 20), 0.071354, delta=0.000001)
        self.assertAlmostEqual(binomial_upper(4, 20), 0.401029, delta=0.000001)

    def test_general_bounds_invert_an_independent_exact_polynomial(self):
        for n in (5, 10, 25, 50):
            for k in (1, n // 2, n - 1):
                for alpha in (0.01, 0.05, 0.25):
                    p = binomial_upper(k, n, alpha)
                    cdf = math.fsum(
                        math.comb(n, j) * p ** j * (1 - p) ** (n - j)
                        for j in range(k + 1)
                    )
                    self.assertAlmostEqual(cdf, alpha, delta=2e-12)

    def test_rare_error_tail_does_not_underflow(self):
        n = 100000
        p = binomial_upper(1, n)
        # P[X<=1]=(1-p)^(n-1)*(1+(n-1)*p), evaluated independently.
        log_cdf = (n - 1) * math.log1p(-p) + math.log1p((n - 1) * p)
        self.assertAlmostEqual(log_cdf, math.log(0.05), delta=1e-8)
        self.assertTrue(0 < p < 0.001)

    def test_symmetry_monotonicity_and_confidence_direction(self):
        n = 32
        uppers = [binomial_upper(k, n) for k in range(n + 1)]
        lowers = [binomial_lower(k, n) for k in range(n + 1)]
        self.assertEqual(uppers, sorted(uppers))
        self.assertEqual(lowers, sorted(lowers))
        for k in range(n + 1):
            self.assertAlmostEqual(lowers[k], 1.0 - uppers[n - k], places=14)
            self.assertLessEqual(lowers[k], k / n)
            self.assertGreaterEqual(uppers[k], k / n)
        self.assertGreater(binomial_upper(3, n, 0.01), binomial_upper(3, n, 0.05))
        self.assertLess(binomial_lower(20, n, 0.01), binomial_lower(20, n, 0.05))

    def test_binomial_type_and_range_guards(self):
        for function in (binomial_lower, binomial_upper):
            for args in ((True, 3), (1, False), (1.0, 3), (1, 3.0), ("1", 3), (None, 3)):
                with self.subTest(function=function.__name__, args=args), self.assertRaises(TypeError):
                    function(*args)
            for args in ((-1, 3), (4, 3), (0, -1), (1, 0)):
                with self.assertRaises(ValueError):
                    function(*args)
            for alpha in (float("nan"), float("inf"), -float("inf"), 0, 1, -0.1, 1.1):
                with self.assertRaises(ValueError):
                    function(0, 3, alpha)
            for alpha in (True, False, "0.05", None):
                with self.assertRaises(TypeError):
                    function(0, 3, alpha)

    def test_sample_plan_type_and_range_guards(self):
        for rate in (True, False, "0.001", None):
            with self.assertRaises(TypeError):
                zero_error_required_n(rate)
        for rate in (0, 1, -0.1, 1.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                zero_error_required_n(rate)
        with self.assertRaises(TypeError):
            zero_error_required_n(0.001, True)
        with self.assertRaises(ValueError):
            zero_error_required_n(0.001, 0)

    def test_paired_counts_follow_the_actual_pairs(self):
        result = paired_bounds([True, True, False, False], [True, False, True, False])
        self.assertEqual({k: result[k] for k in ("n", "gained", "lost", "retained", "parent_correct", "current_correct")},
                         {"n": 4, "gained": 1, "lost": 1, "retained": 1, "parent_correct": 2, "current_correct": 2})
        self.assertEqual(result["delta"], 0.0)
        self.assertLess(result["delta_lower"], 0.0)
        self.assertAlmostEqual(result["retention_lower"], 1 - math.sqrt(0.95), places=13)

    def test_paired_difference_closed_form_and_no_vacuous_retention(self):
        result = paired_bounds([False] * 100, [True] * 100)
        self.assertEqual(result["delta"], 1.0)
        # Gain lower=(alpha/2)^(1/n); loss upper=1-(alpha/2)^(1/n).
        self.assertAlmostEqual(result["delta_lower"], 2 * 0.025 ** 0.01 - 1, places=14)
        self.assertIsNone(result["retention_lower"])
        reverse = paired_bounds([True] * 100, [False] * 100)
        self.assertEqual(reverse["delta"], -1.0)
        self.assertEqual(reverse["delta_lower"], -1.0)
        self.assertEqual(reverse["retention_lower"], 0.0)
        identical = paired_bounds([True] * 299, [True] * 299)
        self.assertEqual(identical["delta"], 0.0)
        self.assertLess(identical["delta_lower"], 0.0)
        self.assertGreaterEqual(identical["retention_lower"], 0.99)

    def test_paired_outcomes_reject_non_booleans_and_mismatches(self):
        for before, after in (([0], [False]), ([True], [1]), ([None], [False]), ((True,), [True]), ([True], None)):
            with self.assertRaises(TypeError):
                paired_bounds(before, after)
        with self.assertRaises(ValueError):
            paired_bounds([True], [])
        with self.assertRaises(TypeError):
            paired_bounds([], [], True)
        with self.assertRaises(ValueError):
            paired_bounds([], [], float("nan"))

    def test_subnormal_tail_budget_does_not_become_zero_when_halved(self):
        alpha = math.nextafter(0.0, 1.0)
        result = paired_bounds([False] * 100, [True] * 100, alpha)
        expected = 2 * math.exp((math.log(alpha) - math.log(2)) / 100) - 1
        self.assertAlmostEqual(result["delta_lower"], expected, places=14)


if __name__ == "__main__":
    unittest.main()
