"""Frozen authored cases plus separately labelled post-open integrity review.

The additional attacks below do not increase the independent 184-case count.
They target source identity, witness scope and representation authority.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from nabt.counting import (count_source_units, read_count_phrase,
                           verify_count_phrase, verify_source_count)
from nabt.errors import NabtError
from nabt.nominal import (decode_nominal, nominal_number, number_rule,
                          read_nominal, read_nominal_facts, verify_nominal,
                          verify_nominal_facts, weak_root_profile)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nabt_independent_nominal_evaluator",
                                             ROOT / "tools/nominal_evaluation.py")
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def fixture(identifier):
    return next(c for c in EVALUATOR.load_material()["cases"] if c["id"] == identifier)


def block(identifier, surface, *clauses):
    return "قراءة «" + identifier + "» للفظ «" + surface + "»:\n" + "\n".join(clauses)


class NominalIndependentReviewTests(unittest.TestCase):
    def test_frozen_pre_open_cases(self):
        for case in EVALUATOR.load_material()["cases"]:
            with self.subTest(case=case["id"]):
                result = EVALUATOR.run_case(case)
                self.assertTrue(result["passed"], result)

    def test_blanket_deferral_fails_required_positive_profile(self):
        case = fixture("NOM-F01")
        report = read_nominal_facts(**EVALUATOR.inputs_for(case))
        for axis in report["readings"][0]["axes"].values():
            axis["status"], axis["activated"] = "DEFER", False
        with self.assertRaises(ValueError):
            EVALUATOR.check_nominal_expectations(case["expect"], report)

    def test_accepting_every_class_fails_raw_cue_exclusion(self):
        case = fixture("NOM-R01")
        report = read_nominal(**EVALUATOR.inputs_for(case))
        report["occurrences"][0]["readings"][0]["kind"].update(status="LICENSED", candidates=["noun"])
        with self.assertRaises(ValueError):
            EVALUATOR.check_nominal_expectations(case["expect"], report)

    def test_written_occurrence_shift_detected_without_reader_replay(self):
        inputs = {"text": "رجل رجل", "source_id": "review", "scope": "a", "lexical_source_id": "review_lexicon"}
        report = read_nominal(**inputs)
        self.assertTrue(EVALUATOR.independent_nominal_checks(report, inputs))
        changed = deepcopy(report)
        changed["occurrences"][0]["span"] = deepcopy(changed["occurrences"][1]["span"])
        with self.assertRaises(ValueError):
            EVALUATOR.independent_nominal_checks(changed, inputs)
        self.assertFalse(verify_nominal(changed)["valid"])

    def test_source_assertion_cannot_transfer_between_readings(self):
        inputs = {"text": block("first", "رجل", "هو اسم.", "هو مذكر.") + "\n" +
                  block("second", "امرأة", "هو اسم.", "هو مؤنث."), "source_id": "review", "scope": "a"}
        report = read_nominal_facts(**inputs)
        self.assertTrue(EVALUATOR.independent_fact_checks(report, inputs))
        changed = deepcopy(report)
        changed["readings"][0]["properties"][1] = deepcopy(changed["readings"][1]["properties"][1])
        with self.assertRaises(ValueError):
            EVALUATOR.independent_fact_checks(changed, inputs)
        self.assertFalse(verify_nominal_facts(changed)["valid"])

    def test_source_qualification_and_missing_traits_are_not_discarded(self):
        base = block("first", "رجل", "هو اسم.", "هو مذكر.")
        partial = read_nominal_facts(base)["readings"][0]
        self.assertEqual(set(partial["axes"]["number"]["candidates"]), {"singular", "dual", "plural"})
        for text in (base + "\nبشرط شاهد مجهول.", "قيد سابق لم يحلل.\n" + base):
            with self.subTest(text=text):
                report = read_nominal_facts(text)
                self.assertFalse(any(axis["activated"] for axis in report["readings"][0]["axes"].values()))
                self.assertEqual(report["status"], "DEFER")

    def test_lexical_identity_cannot_be_swapped_when_labels_agree(self):
        lexical = block("first", "رجل", "هو اسم.", "هو مذكر.", "يدل على واحد.")
        inputs = {"text": "رجل", "lexical_text": lexical, "source_id": "review", "lexical_source_id": "review_lexicon", "scope": "a"}
        report = read_nominal(**inputs)
        changed = deepcopy(report)
        changed["occurrences"][0]["readings"][0]["lexical_source_link"]["source_id"] = "other_lexicon"
        with self.assertRaises(ValueError):
            EVALUATOR.independent_nominal_checks(changed, inputs)
        self.assertFalse(verify_nominal(changed)["valid"])
        self.assertFalse(verify_nominal(report, lexical_source_id="other_lexicon")["valid"])
        self.assertFalse(verify_nominal(report, lexical_text=lexical + "\n")["valid"])
        self.assertFalse(verify_nominal(report, lexical_text=None)["valid"])
        self.assertTrue(verify_nominal(report)["valid"])

    def test_plural_base_gender_cannot_be_borrowed_from_another_reading(self):
        case = fixture("NOM-L01")
        inputs = EVALUATOR.inputs_for(case)
        report = read_nominal_facts(**inputs)
        changed = deepcopy(report)
        changed["readings"][0]["singular_links"][0]["singular_gender"] = "feminine"
        with self.assertRaises(ValueError):
            EVALUATOR.independent_fact_checks(changed, inputs)
        self.assertFalse(verify_nominal_facts(changed)["valid"])

    def test_unknown_unshaddad_flag_cannot_be_filled_by_mask_edit(self):
        case = fixture("NOM-M02")
        inputs = EVALUATOR.inputs_for(case)
        report = read_nominal(**inputs)
        changed = deepcopy(report)
        axis = changed["occurrences"][0]["readings"][0]["manqus"]
        axis.update(status="LICENSED", candidates=[True], positive_mask=31)
        with self.assertRaises(ValueError):
            EVALUATOR.independent_nominal_checks(changed, inputs)
        self.assertFalse(verify_nominal(changed)["valid"])

    def test_quoted_mentions_cannot_become_unquoted_uses(self):
        inputs = {"text": "«رجل» رجل", "source_id": "review", "scope": "a"}
        report = count_source_units(**inputs)
        self.assertTrue(EVALUATOR.independent_count_checks(report, inputs))
        changed = deepcopy(report)
        changed["units"][0]["reading_context"] = "UNQUOTED"
        with self.assertRaises(ValueError):
            EVALUATOR.independent_count_checks(changed, inputs)
        self.assertFalse(verify_source_count(changed)["valid"])

    def test_duplicate_unit_reference_cannot_increase_count(self):
        inputs = {"text": "رجل", "source_id": "review", "scope": "a"}
        report = count_source_units(**inputs)
        changed = deepcopy(report)
        changed["units"].append(deepcopy(changed["units"][0]))
        changed["count"] = 2
        with self.assertRaises(ValueError):
            EVALUATOR.independent_count_checks(changed, inputs)
        self.assertFalse(verify_source_count(changed)["valid"])

    def test_digits_cannot_supply_observed_gender(self):
        case = fixture("NOM-Q01")
        inputs = EVALUATOR.inputs_for(case)
        report = read_count_phrase(**inputs)
        self.assertTrue(EVALUATOR.independent_phrase_checks(report, inputs))
        changed = deepcopy(report)
        changed["numeral"]["unit_gender"] = "feminine"
        changed["alternatives"][0]["checks"]["unit_gender"].update(status="MATCH", observed="feminine")
        with self.assertRaises(ValueError):
            EVALUATOR.independent_phrase_checks(changed, inputs)
        self.assertFalse(verify_count_phrase(changed)["valid"])

    def test_counted_gender_cannot_use_unrelated_origin(self):
        case = fixture("NOM-Q01")
        inputs = EVALUATOR.inputs_for(case)
        report = read_count_phrase(**inputs)
        changed = deepcopy(report)
        changed["alternatives"][0]["singular_origin"]["target_reading_id"] = "other"
        with self.assertRaises(ValueError):
            EVALUATOR.independent_phrase_checks(changed, inputs)
        self.assertFalse(verify_count_phrase(changed)["valid"])

    def test_counted_case_requirement_cannot_become_actual_case(self):
        case = fixture("NOM-Q01")
        report = read_count_phrase(**EVALUATOR.inputs_for(case))
        changed = deepcopy(report)
        changed["alternatives"][0]["actual_case"] = "genitive"
        with self.assertRaises(ValueError):
            EVALUATOR.semantic_restraint(changed)
        self.assertFalse(verify_count_phrase(changed)["valid"])

    def test_boolean_numeric_operands_and_root_normalization_are_rejected(self):
        for value in (True, False, 3.0, "3"):
            with self.subTest(value=value), self.assertRaises(NabtError):
                number_rule(value, "masculine")
        for root in (True, "قال", "رمى", "أكل", "أكل", "كُتب"):
            with self.subTest(root=root), self.assertRaises(NabtError):
                weak_root_profile(root)

    def test_raw_reader_has_no_answer_operands(self):
        for supplied in ({"gender": "masculine"}, {"definiteness": "definite"}, {"root": "كتب"}, {"word_class": "noun"}):
            with self.subTest(supplied=supplied), self.assertRaises(TypeError):
                read_nominal("رجل", **supplied)

    def test_pronoun_candidate_does_not_conflict_with_independent_verb_reading(self):
        report = read_nominal("هم", lexical_text=block("verb", "هم", "هو فعل."))
        readings = report["occurrences"][0]["readings"]
        verb = next(r for r in readings if r["lexical_reading_id"] == "verb")
        pronoun = next(r for r in readings if r["pronoun_candidates"])
        self.assertEqual(verb["kind"]["candidates"], ["verb"])
        self.assertNotEqual(verb["status"], "CONFLICT")
        self.assertEqual(pronoun["reading_basis"], "CANDIDATE_PRONOUN_READING")
        self.assertFalse(pronoun["exhaustive_over_arabic_homographs"])
        self.assertNotEqual(verb["reading_id"], pronoun["reading_id"])

    def test_nominal_number_replays_source_and_all_alternatives(self):
        report = read_nominal("أنت")
        self.assertEqual(decode_nominal(nominal_number(report)), report)
        changed = deepcopy(report)
        changed["occurrences"][0]["readings"][0]["axes"]["gender"]["candidates"] = ["masculine"]
        forged = int.from_bytes(b"\x01" + EVALUATOR.wire(changed), "big")
        with self.assertRaises(NabtError):
            decode_nominal(forged)
        for value in (True, False, 0, -1):
            with self.subTest(value=value), self.assertRaises(NabtError):
                decode_nominal(value)


if __name__ == "__main__":
    unittest.main()
