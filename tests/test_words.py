"""Boundary tests for the conditional algebra, independent of surface parsing."""

import unittest

from nabt import NabtError
from nabt import words


class WordAlgebraTests(unittest.TestCase):
    def test_absence_is_not_particle_evidence_and_conflict_is_not_unknown(self):
        self.assertEqual(words.kind_candidates(()), (0, 1, 2))
        self.assertEqual(words.kind_candidates(((0, 1), (1, 2))), (1,))
        self.assertEqual(words.kind_candidates(((0,), (2,))), ())

    def test_capacities_do_not_assign_an_actual_role(self):
        self.assertEqual(words.capacities(0), {"subject": True, "predicate": True})
        self.assertEqual(words.capacities(1), {"subject": False, "predicate": True})
        self.assertEqual(words.capacities(2), {"subject": False, "predicate": False})

    def test_kasra_of_sound_feminine_plural_is_not_a_unique_case(self):
        self.assertEqual(words.case_candidates((4,), 2), ((4, 0), (4, 2)))
        self.assertEqual(words.refine_cases(((4, 0), (4, 2)), role=0, required_case=0), ((4, 0),))
        self.assertEqual(words.refine_cases(((4, 0), (4, 2)), role=6, required_case=2), ((4, 2),))

    def test_same_surface_damma_can_have_different_grammatical_cases(self):
        # Regular noun vs. a weak-waw imperfect whose final radical was deleted.
        self.assertEqual(words.case_candidates((0, 13), 0), ((0, 1), (13, 3)))
        self.assertEqual(words.refine_cases(((0, 1), (13, 3)), role=2, required_case=3), ((13, 3),))
        self.assertEqual(words.refine_cases(((0, 1), (13, 3)), role=0, required_case=0), ())

    def test_declared_maqsur_retains_all_nominal_cases(self):
        self.assertEqual(words.case_candidates((6,), 5), ((6, 0), (6, 1), (6, 2)))
        self.assertEqual(words.case_candidates((0,), None), ((0, 0), (0, 1), (0, 2)))
        self.assertEqual(words.case_candidates((0,), 3), ())

    def test_pair_codec_is_typed_and_separate_from_permission(self):
        for c in range(15):
            for case in range(4):
                self.assertEqual(words.decode_class_case(words.class_case_number(c, case)), (c, case))
        # 3 encodes noun-class0/jazm, but the realization table rejects it.
        self.assertEqual(words.decode_class_case(3), (0, 3))
        with self.assertRaises(NabtError):
            words.refine_cases(((0, 3),), role=2, required_case=3)

    def test_booleans_negative_unknown_and_repeated_classes_are_rejected(self):
        calls = [lambda: words.capacities(True), lambda: words.capacities(3),
                 lambda: words.case_candidates((True,), 0), lambda: words.case_candidates((15,), 0),
                 lambda: words.case_candidates((0, 0), 0), lambda: words.case_candidates((0,), -1),
                 lambda: words.case_candidates((0,), True), lambda: words.class_case_number(0, True),
                 lambda: words.decode_class_case(60), lambda: words.kind_candidates(((False,),)),
                 lambda: words.refine_cases(((0, 0),), role=True, required_case=0)]
        for call in calls:
            with self.subTest(call=call), self.assertRaises(NabtError):
                call()


if __name__ == "__main__":
    unittest.main()
