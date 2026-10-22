from collections import Counter
from itertools import product
import unittest
from unittest.mock import patch

from nabt.ambiguity import AmbiguityForest, MAX_PATTERN_CELLS
from nabt.alphabet import parse_word
from nabt.errors import NabtError
from tests import oracle


class AmbiguityTests(unittest.TestCase):
    def test_missing_marks_are_hypotheses_and_strict_reader_stays_strict(self):
        with self.assertRaises(NabtError) as caught:
            parse_word("كتب")
        self.assertEqual(caught.exception.code, "MISSING_VOCALIZATION")
        forest = AmbiguityForest("كتب")
        self.assertEqual(forest.domains, ((84, 85, 86, 87), (8, 9, 10, 11), (4, 5, 6, 7)))
        self.assertEqual(forest.missing_positions, (0, 1, 2))
        observed = AmbiguityForest("كَتبْ")
        self.assertEqual(observed.domains, ((84,), (8, 9, 10, 11), (7,)))
        self.assertEqual(observed.missing_positions, (1,))

    def test_all_paths_against_independent_enumeration(self):
        for source in ("كتب", "كَتَبَ", "كا", "كَا", "ب", "ا", "كُاْ", "كَاْ", "كْ", "مدرس", "كَو", "كو", "كي"):
            for mode in ("wasl", "waqf"):
                with self.subTest(source=source, mode=mode):
                    forest = AmbiguityForest(source, mode)
                    expected, grades = [], Counter()
                    for cells in product(*forest.domains):
                        accepted, _, weight = oracle.run(cells, mode)
                        self.assertEqual(forest.contains(cells), accepted)
                        if accepted:
                            expected.append(cells)
                            grades[weight] += 1
                    self.assertEqual(forest.total, len(expected))
                    self.assertEqual(dict(forest.counts_by_weight), dict(grades))
                    self.assertEqual([forest.witness(i) for i in range(forest.total)], sorted(expected))

    def test_projected_alternatives_cannot_be_recombined_freely(self):
        forest = AmbiguityForest("كتب", "wasl")
        report = forest.as_dict()
        self.assertEqual(forest.total, 45)
        self.assertEqual(AmbiguityForest("كتب", "waqf").total, 48)
        # Both silent marks occur in supported projections; their joint path fails.
        self.assertIn(3, report["residuals"][1]["admissible_hypotheses"])
        self.assertIn(3, report["residuals"][2]["admissible_hypotheses"])
        self.assertFalse(forest.contains((84, 11, 7)))
        self.assertFalse(forest.contains((84,)))
        self.assertFalse(forest.contains((84, 8, 4, 4)))

    def test_exact_source_identity_and_domain_cannot_be_supplied_as_authority(self):
        a, b = AmbiguityForest("كتب"), AmbiguityForest("كَتب")
        self.assertNotEqual(a.source_sha256, b.source_sha256)
        self.assertEqual(a.source, "كتب")
        with self.assertRaises(TypeError):
            AmbiguityForest("كتب", domains=((84,),))
        with self.assertRaises(AttributeError):
            a.domains = b.domains
        self.assertFalse(hasattr(a, "__dict__"))

    def test_zero_weight_madd_is_counted_at_exact_length(self):
        forest = AmbiguityForest("كَاْ")
        self.assertEqual(forest.counts_by_weight, ((1, 1),))
        self.assertEqual(forest.witness(0), (84, 3))
        self.assertFalse(forest.contains((84,)))

    def test_long_symbolic_input_and_named_budgets(self):
        forest = AmbiguityForest("ب" * 32)
        self.assertGreater(forest.total, 1_000_000)
        self.assertEqual(len(forest.witness(forest.total - 1)), 32)
        for call in (lambda: AmbiguityForest("ب" * (MAX_PATTERN_CELLS + 1)),):
            with self.assertRaises(NabtError) as caught:
                call()
            self.assertEqual((caught.exception.code, caught.exception.status), ("RESOURCE_LIMIT", "DEFER"))
        with patch("nabt.ambiguity.MAX_COUNT_UPDATES", 0):
            with self.assertRaises(NabtError) as caught:
                AmbiguityForest("كتب")
            self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")

    def test_malformed_unsupported_and_invalid_rank(self):
        for source in ("", "َب", "بَُ", "ب ب", "\ud800"):
            with self.assertRaises(NabtError):
                AmbiguityForest(source)
        for source in ("أَب", "بَّ", "بٌ", "🙂"):
            with self.assertRaises(NabtError) as caught:
                AmbiguityForest(source)
            self.assertEqual(caught.exception.status, "DEFER")
        for rank in (True, -1, 48, "0"):
            with self.assertRaises(NabtError):
                AmbiguityForest("كتب").witness(rank)


if __name__ == "__main__":
    unittest.main()
