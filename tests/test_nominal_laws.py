"""Authored law-boundary counterexamples, separate from independent gold.

These tests exercise public input domains and nonpromotion boundaries. The
complete finite truth tables are checked by check_nominal_conformance.py.
"""

from copy import deepcopy
import unittest

from nabt.errors import NabtError
from nabt.nominal import (nominal_candidates, number_rule, read_nominal,
                          read_nominal_facts, verify_nominal, weak_root_profile)


def facts(word, *clauses, reading="r1"):
    return f"قراءة «{reading}» للفظ «{word}»:\n" + "\n".join(clauses) + "\n"


def only_reading(report):
    return report["occurrences"][0]["readings"][0]


MANQUS_FOUR = ("هو اسم.", "هو معرب.", "آخره ياء لازمة.", "ما قبل الياء مكسور.")


class NominalLawBoundaries(unittest.TestCase):
    def test_gender_and_plural_morphology_are_independent_axes(self):
        masculine_sound_feminine = nominal_candidates((0, 6))
        self.assertEqual([r["code"] for r in masculine_sound_feminine], [6, 7])
        self.assertTrue(all(r["gender"] == 0 and r["form"] == 3 and r["number"] == 2
                            for r in masculine_sound_feminine))
        self.assertEqual(nominal_candidates((1, 5)), [])
        self.assertTrue(nominal_candidates((0, 7)))
        self.assertTrue(nominal_candidates((1, 7)))

    def test_empty_evidence_keeps_both_definiteness_values(self):
        rows = nominal_candidates(())
        self.assertEqual(len(rows), 22)
        self.assertEqual({r["definiteness"] for r in rows}, {0, 1})
        self.assertEqual({r["number"] for r in rows}, {0, 1, 2})

    def test_constraint_codes_reject_bool_and_foreign_domain(self):
        for code in (True, False, -1, 11, 1.0, "1", None):
            with self.subTest(code=code), self.assertRaises(NabtError):
                nominal_candidates((code,))

    def test_cardinal_domain_does_not_extend_by_modulo(self):
        for value in (0, 101, 200, 999, 1001):
            with self.subTest(value=value), self.assertRaises(NabtError) as raised:
                number_rule(value, "masculine")
            self.assertEqual(raised.exception.code, "NUMBER_RULE_OUTSIDE_DOMAIN")
            self.assertEqual(raised.exception.status, "DEFER")
        for value in (True, False, -1, 1.0, "3"):
            with self.subTest(value=value), self.assertRaises(NabtError):
                number_rule(value, "masculine")

    def test_singular_gender_is_a_required_typed_premise(self):
        for gender in (True, 0, None, "unknown", "masc", "plural"):
            with self.subTest(gender=gender), self.assertRaises(NabtError):
                number_rule(3, gender)

    def test_teen_units_and_ten_gender_are_separate(self):
        thirteen = number_rule(13, "feminine")
        self.assertEqual(thirteen["unit_gender"], "masculine")
        self.assertEqual(thirteen["ten_gender"], "feminine")
        self.assertEqual(thirteen["counted_number"], "singular")
        self.assertEqual(thirteen["counted_case"], "accusative")
        self.assertIsNone(number_rule(23, "feminine")["ten_gender"])
        self.assertIsNone(number_rule(20, "feminine")["unit_gender"])

    def test_cardinal_requirements_never_become_actual_case_or_entity_rank(self):
        for value in (1, 2, 3, 11, 100, 1000):
            rule = number_rule(value, "masculine")
            self.assertEqual(rule["numeral_kind"], "cardinal")
            for field in ("actual_case", "actual_role", "ordinal", "world_cardinality"):
                self.assertIsNone(rule[field])
        self.assertEqual(number_rule(2, "masculine")["counted_case"], "contextual")

    def test_no_weak_slot_does_not_imply_unhamzated_or_undoubled(self):
        hamzated, doubled = weak_root_profile("ءكل"), weak_root_profile("مدد")
        self.assertEqual(hamzated["class"], "sound")
        self.assertTrue(hamzated["hamzated"])
        self.assertEqual(doubled["class"], "sound")
        self.assertTrue(doubled["geminated"])
        for result in (hamzated, doubled):
            self.assertFalse(result["attested_root"])
            self.assertIsNone(result["nominal_manqus"])
            self.assertIsNone(result["surface_realization"])

    def test_weak_root_requires_canonical_radicals_not_surface_reconstruction(self):
        for root in ("قال", "أكل", "قَى", "رَمَي", "كتبب", "abx", True, ["ك", "ت", "ب"]):
            with self.subTest(root=root), self.assertRaises(NabtError):
                weak_root_profile(root)
        self.assertEqual(weak_root_profile("وقي")["class"], "lafif_mafruq")
        self.assertEqual(weak_root_profile("روي")["class"], "lafif_maqrun")
        self.assertEqual(weak_root_profile("ويك")["status"], "RESIDUAL")
        self.assertEqual(weak_root_profile("ويو")["status"], "RESIDUAL")

    def test_raw_noun_endings_have_no_lexical_feature_authority(self):
        for surface in ("بَيْتَانِ", "مُسْلِمُونَ", "طَالِبَات", "قَاضِي"):
            with self.subTest(surface=surface):
                reading = only_reading(read_nominal(surface))
                self.assertFalse(reading["receipt"]["activated"])
                for field in ("gender", "number", "form", "definiteness"):
                    self.assertNotEqual(reading["axes"][field]["status"], "LICENSED")
                self.assertIsNone(reading["actual_case"])
                self.assertIsNone(reading["declension_class"])

    def test_tanwin_and_article_observations_do_not_determine_definiteness(self):
        for surface in ("زَيْدٌ", "الْقَوْم"):
            with self.subTest(surface=surface):
                reading = only_reading(read_nominal(surface))
                self.assertEqual(set(reading["axes"]["definiteness"]["candidates"]),
                                 {"definite", "indefinite"})
                self.assertNotEqual(reading["axes"]["definiteness"]["status"], "LICENSED")

    def test_partial_pronoun_and_dual_ambiguity_survive(self):
        for surface in ("أنت", "هُمَا", "أَنْتُمَا"):
            with self.subTest(surface=surface):
                reading = only_reading(read_nominal(surface))
                self.assertEqual({p["gender"] for p in reading["pronoun_candidates"]}, {0, 1})
                self.assertIsNone(reading["declension_class"])
        feminine = only_reading(read_nominal("أَنْتِ"))
        self.assertEqual(feminine["axes"]["gender"]["candidates"], ["feminine"])

    def test_unobserved_fifth_manqus_condition_remains_unknown(self):
        reading = read_nominal_facts(facts("الْقَاضِي", *MANQUS_FOUR))["readings"][0]
        self.assertEqual(reading["manqus"]["candidates"], [False, True])
        self.assertEqual(reading["manqus"]["status"], "DEFER")
        self.assertEqual(reading["manqus"]["negative_mask"], 0)

    def test_all_five_source_qualified_manqus_conditions_are_effective(self):
        text = facts("الْقَاضِي", *MANQUS_FOUR, "ياؤه الأخيرة غير مشددة.")
        reading = read_nominal_facts(text)["readings"][0]
        self.assertEqual(reading["manqus"]["candidates"], [True])
        self.assertEqual(reading["manqus"]["positive_mask"], 31)
        self.assertFalse(reading["manqus"]["root_weakness_consumed"])
        self.assertIsNone(reading["actual_case"])

    def test_final_yaa_gemination_is_an_observed_blocker(self):
        reading = read_nominal_facts(facts("كُرْسِيّ", *MANQUS_FOUR))["readings"][0]
        self.assertEqual(reading["manqus"]["candidates"], [False])
        self.assertTrue(reading["manqus"]["negative_mask"] & 16)
        conflict = read_nominal_facts(facts("كُرْسِيّ", *MANQUS_FOUR,
                                            "ياؤه الأخيرة غير مشددة."))["readings"][0]
        self.assertTrue(conflict["conflict"])
        self.assertNotEqual(conflict["manqus"]["status"], "LICENSED")

    def test_unparsed_source_cannot_grant_positive_nominal_properties(self):
        text = facts("زَيْد", "هو اسم.", "هو علم.", "وصف ذو قيد مجهول.")
        reading = only_reading(read_nominal("زَيْد", lexical_text=text))
        self.assertFalse(reading["receipt"]["activated"])
        self.assertNotEqual(reading["axes"]["definiteness"]["status"], "LICENSED")

    def test_foreign_source_scope_and_forged_receipt_fail_replay(self):
        lexical = facts("بَيْت", "هو اسم.", "هو مذكر.", "يدل على واحد.")
        report = read_nominal("بَيْت", lexical_text=lexical, source_id="input", scope="alpha")
        self.assertTrue(verify_nominal(report)["valid"])
        for kwargs in ({"scope": "beta"}, {"source_id": "other"}, {"lexical_text": None}):
            with self.subTest(kwargs=kwargs):
                self.assertFalse(verify_nominal(report, **kwargs)["valid"])
        forged = deepcopy(report)
        only_reading(forged)["receipt"]["identity"]["source_sha256"] = "0" * 64
        self.assertFalse(verify_nominal(forged)["valid"])


if __name__ == "__main__":
    unittest.main()
