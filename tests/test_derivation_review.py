"""Frozen pre-open evidence plus explicitly post-open integrity attacks.

The fixed cases are authored source-informed material, not a natural corpus.
The additional checks below review representation and authority after the
implementation was opened; they do not increase the frozen holdout count.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from nabt.derivation import (decode_derivation, derivation_number,
    generate_derivation, read_derivation, verify_derivation)
from nabt.errors import NabtError
from nabt.verb_paradigm import (availability_candidates, read_verb_paradigm,
    verify_verb_paradigm)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nabt_independent_derivation_evaluator",
                                             ROOT / "tools/derivation_evaluation.py")
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def paradigm(*lines, lexeme="كتب"):
    return "الفعل «" + lexeme + "».\n" + "\n".join(lines)


class DerivationIndependentReviewTests(unittest.TestCase):
    def test_frozen_independent_cases(self):
        for case in EVALUATOR.load_material()["cases"]:
            with self.subTest(case=case["id"]):
                result = EVALUATOR.run_case(case)
                self.assertTrue(result["passed"], result)

    def test_blanket_deferral_fails_positive_parse_measurement(self):
        case = next(c for c in EVALUATOR.load_material()["cases"] if c["id"] == "DER-GP-01")
        report = read_derivation(**case["read_request"])
        changed = deepcopy(report)
        changed["occurrences"][0]["candidates"] = []
        with self.assertRaises(ValueError):
            EVALUATOR.check_shape_expectations(case["expect"], changed)

    def test_candidate_exclusion_is_not_satisfied_by_accepting_everything(self):
        case = next(c for c in EVALUATOR.load_material()["cases"] if c["id"] == "DER-B06")
        report = read_derivation(**case["read_request"])
        changed = deepcopy(report)
        changed["occurrences"][0]["candidates"].append({"pattern_id": "nominal.mafool", "root": "كتب"})
        with self.assertRaises(ValueError):
            EVALUATOR.check_shape_expectations(case["expect"], changed)

    def test_occurrence_shift_is_rejected_even_for_identical_surfaces(self):
        inputs = {"text": "كَاتِبٌ كَاتِبٌ", "source_id": "review", "scope": "a", "profile": "surface_v1"}
        report = read_derivation(**inputs)
        self.assertTrue(EVALUATOR.independent_derivation_checks(report, inputs))
        changed = deepcopy(report)
        changed["occurrences"][0]["span"] = deepcopy(changed["occurrences"][1]["span"])
        with self.assertRaises(ValueError):
            EVALUATOR.independent_derivation_checks(changed, inputs)
        self.assertFalse(verify_derivation(changed)["valid"])

    def test_alignment_mutation_is_rejected_independently(self):
        inputs = {"text": "مَكْتُوب", "source_id": "review", "scope": "a", "profile": "stem_exact_v1"}
        report = read_derivation(**inputs)
        changed = deepcopy(report)
        candidate = next(c for c in changed["occurrences"][0]["candidates"] if c["pattern_id"] == "nominal.mafool")
        candidate["alignment"][0]["literal"] = "ب"
        with self.assertRaises(ValueError):
            EVALUATOR.independent_derivation_checks(changed, inputs)
        self.assertFalse(verify_derivation(changed)["valid"])

    def test_source_scope_and_profile_are_replayed(self):
        report = read_derivation("كَاتِبٌ", source_id="review", scope="a")
        self.assertTrue(verify_derivation(report)["valid"])
        for replacement in ({"text": "حَافِظٌ"}, {"source_id": "other"}, {"scope": "b"},
                            {"profile": "stem_exact_v1"}):
            with self.subTest(replacement=replacement):
                self.assertFalse(verify_derivation(report, **replacement)["valid"])

    def test_raw_reader_cannot_be_given_answer_operands(self):
        for operand in ({"root": "كتب"}, {"pattern_id": "nominal.faail"}, {"word_class": "noun"}):
            with self.subTest(operand=operand), self.assertRaises(TypeError):
                read_derivation("كَاتِب", **operand)
        generated = generate_derivation("كتب", "nominal.faail")
        self.assertEqual(generated["root_basis"], "SUPPLIED_FORMAL_RADICALS")
        self.assertFalse(generated["attested_root"])

    def test_boundary_and_semantic_authority_cannot_be_forged(self):
        report = read_derivation("كَاتِبٌ")
        mutations = [
            lambda r: r.update(facts=[{"asserted": "world fact"}]),
            lambda r: r["occurrences"][0].update(actual_case="raf"),
            lambda r: r["occurrences"][0]["axes"]["kind"].update(status="LICENSED", candidates=["noun"]),
            lambda r: r["occurrences"][0]["axes"]["nominal_semantics"].update(status="LICENSED", candidates=["mushtaq"]),
            lambda r: r["occurrences"][0]["candidates"][0].update(root_status="ATTESTED", actual_role="faail"),
            lambda r: r["recognition_basis"].update(given_class_used=True),
        ]
        for index, mutate in enumerate(mutations):
            changed = deepcopy(report)
            mutate(changed)
            with self.subTest(mutation=index):
                self.assertFalse(verify_derivation(changed)["valid"])

    def test_number_replay_does_not_authorize_changed_candidates(self):
        report = read_derivation("انْتَبَر", profile="stem_exact_v1")
        self.assertEqual(decode_derivation(derivation_number(report)), report)
        changed = deepcopy(report)
        changed["occurrences"][0]["candidates"] = changed["occurrences"][0]["candidates"][:1]
        forged = int.from_bytes(b"\x01" + EVALUATOR.wire(changed), "big")
        with self.assertRaises(NabtError):
            decode_derivation(forged)
        for invalid in (True, False, -1, 0):
            with self.subTest(number=invalid), self.assertRaises(NabtError):
                decode_derivation(invalid)

    def test_future_proposal_never_crosses_quote_or_newline(self):
        for text in ("سَوْفَ\nيَكْتُبُ", "سَوْفَ «يَكْتُبُ»", "سَوْفَ، يَكْتُبُ", "«سَوْفَ يَكْتُبُ»"):
            with self.subTest(text=text):
                report = read_derivation(text)
                self.assertFalse(report["future_proposals"])

    def test_quoted_shape_witnesses_cannot_become_unquoted_uses(self):
        inputs = {"text": "«كَاتِبٌ»\nمَكْتُوبٌ", "source_id": "review", "scope": "a", "profile": "surface_v1"}
        report = read_derivation(**inputs)
        self.assertEqual([o["reading_context"] for o in report["occurrences"]], ["MENTION", "UNQUOTED"])
        self.assertTrue(EVALUATOR.independent_derivation_checks(report, inputs))
        changed = deepcopy(report)
        changed["occurrences"][0]["reading_context"] = "UNQUOTED"
        with self.assertRaises(ValueError):
            EVALUATOR.independent_derivation_checks(changed, inputs)
        self.assertFalse(verify_derivation(changed)["valid"])

    def test_boolean_masks_are_not_natural_three_bit_inputs(self):
        for positive, negative in ((True, 0), (0, False), (-1, 0), (0, 8), (1.0, 0)):
            with self.subTest(masks=(positive, negative)), self.assertRaises(NabtError):
                availability_candidates(positive, negative)

    def test_unsupported_source_qualification_cannot_be_ignored(self):
        full = paradigm("الماضي مستعمل: «كَتَبَ».", "المضارع مستعمل: «يَكْتُبُ».", "الأمر مستعمل: «اكْتُبْ».")
        for text in ("قيد غير محلل.\n" + full, full + "\nهذا الحكم مشروط بشرط مجهول."):
            with self.subTest(text=text):
                report = read_verb_paradigm(text)
                self.assertFalse(EVALUATOR.classification_activated(report))
                self.assertEqual(report["status"], "DEFER")
                self.assertTrue(verify_verb_paradigm(report)["valid"])

    def test_paradigm_mask_must_follow_witnesses(self):
        inputs = {"text": paradigm("الماضي مستعمل: «كَتَبَ»."), "source_id": "review", "scope": "a"}
        report = read_verb_paradigm(**inputs)
        changed = deepcopy(report)
        changed["readings"][0]["negative_mask"] = 6
        with self.assertRaises(ValueError):
            EVALUATOR.independent_paradigm_checks(changed, inputs)
        self.assertFalse(verify_verb_paradigm(changed)["valid"])

    def test_availability_witness_cannot_transfer_between_blocks(self):
        text = paradigm("الماضي مستعمل: «كَتَبَ».") + "\n" + paradigm("المضارع مستعمل: «يَفْهَمُ».", lexeme="فهم")
        inputs = {"text": text, "source_id": "review", "scope": "a"}
        report = read_verb_paradigm(**inputs)
        changed = deepcopy(report)
        changed["readings"][0]["assertions"][0] = deepcopy(changed["readings"][1]["assertions"][0])
        with self.assertRaises(ValueError):
            EVALUATOR.independent_paradigm_checks(changed, inputs)
        self.assertFalse(verify_verb_paradigm(changed)["valid"])

    def test_paradigm_world_truth_and_nominal_semantics_are_not_authorized(self):
        report = read_verb_paradigm(paradigm("الماضي مستعمل: «لَيْسَ».", "المضارع غير مستعمل.", "الأمر غير مستعمل.", lexeme="ليس"))
        self.assertEqual(report["readings"][0]["axis"]["candidates"], ["jamid"])
        self.assertEqual(report["world_truth"], "NOT_ESTABLISHED")
        for mutate in (lambda r: r.update(world_truth="ESTABLISHED"),
                       lambda r: r.update(nominal_semantics_consumed=True),
                       lambda r: r["readings"][0].update(actual_role="predicate")):
            changed = deepcopy(report)
            mutate(changed)
            self.assertFalse(verify_verb_paradigm(changed)["valid"])


if __name__ == "__main__":
    unittest.main()
