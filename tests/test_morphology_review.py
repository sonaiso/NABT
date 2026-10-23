"""Independent morphology review and explicitly declared coverage boundaries.

The source cases were authored before opening the new implementation. A
subsequent primary-source correction is recorded, not represented as an
untouched holdout. Additional adversarial tests below are post-open review.
"""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from nabt.errors import NabtError
from nabt.morphology_reader import (decode_morphology, morphology_number,
                                    read_morphology, verify_morphology)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nabt_morphology_review_evaluator", ROOT / "tools/morphology_evaluation.py")
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


class IndependentMorphologyReviewTests(unittest.TestCase):
    def test_each_frozen_case_meets_the_declared_regression_contract(self):
        material = EVALUATOR.load_material("v2")
        for case in material["cases"]:
            with self.subTest(case=case["id"]):
                result = EVALUATOR.run_case(case)
                self.assertTrue(result["passed"] or EVALUATOR.documented_boundary(result), result)

    def test_primary_source_erratum_is_uniform_and_keeps_original_gold(self):
        original = EVALUATOR.load_material("v1")
        corrected = EVALUATOR.load_material("v2")
        for old, new in zip(original["cases"], corrected["cases"]):
            with self.subTest(case=old["id"]):
                self.assertEqual(old["id"], new["id"])
                self.assertEqual(old["expected"], new["expected"])
                self.assertEqual(new["input"]["text"], old["input"]["text"].replace(
                    "يدل على حدث مقترن بزمن", "يدل على حدث مقترن بزمن بهيئته"))
        self.assertEqual(len(corrected["cases"]), len(original["cases"]) + 1)
        self.assertEqual(corrected["cases"][-1]["id"], "m43")

    def test_positive_measurement_rejects_blanket_deferral(self):
        case = next(c for c in EVALUATOR.load_material("v2")["cases"] if c["id"] == "m14")
        report = read_morphology(case["input"]["text"])
        for axis in report["readings"][0]["axes"].values():
            axis["status"] = "DEFER"
        checks = EVALUATOR.properties(case["expected"], report)
        self.assertFalse(all(c["passed"] for c in checks))
        self.assertFalse(verify_morphology(report)["valid"])

    def test_boundary_allowance_cannot_hide_an_unrelated_failure(self):
        case = next(c for c in EVALUATOR.load_material("v2")["cases"] if c["id"] == "m12")
        result = EVALUATOR.run_case(case)
        self.assertTrue(EVALUATOR.documented_boundary(result), result)
        unrelated = deepcopy(result)
        unrelated["checks"].append({"property": "source_integrity", "passed": False})
        self.assertFalse(EVALUATOR.documented_boundary(unrelated))
        wrong_candidate = deepcopy(result)
        failed = next(c for c in wrong_candidate["checks"] if not c["passed"])
        failed["observed"]["candidates"] = ["particle"]
        self.assertFalse(EVALUATOR.documented_boundary(wrong_candidate))

    def test_built_noun_does_not_acquire_an_inflected_diptote_class(self):
        text = ("قراءة «r1» للفظ «رُمْنَى»:\n"
                "يدل على معنى مستقل غير مقترن بزمن\n"
                "يشبه الحرف\nآخره ألف التأنيث\nلم تدخل عليه أل\nليس مضافا")
        report = read_morphology(text)
        axes = report["readings"][0]["axes"]
        self.assertEqual(axes["construction"]["candidates"], ["built"])
        self.assertEqual(axes["diptote"]["status"], "OUT_OF_DOMAIN")
        self.assertEqual(axes["diptote"]["cause_prediction"]["candidates"], ["diptote"])
        self.assertEqual(axes["diptote"]["cause_prediction"]["domain"], "QUALIFIED_INTRINSIC_CAUSE_FORMULA_ONLY")
        self.assertIn("LICENSED_INFLECTED_NOUN", axes["diptote"]["prerequisites"])
        self.assertFalse(axes["diptote"]["genitive"]["applied_to_occurrence"])
        self.assertIn("INDEPENDENT_GENITIVE_CASE_WITNESS", axes["diptote"]["genitive"]["prerequisites"])

    def test_known_diptote_still_does_not_invent_an_actual_case(self):
        text = ("قراءة «r1» للفظ «سَنَارِمَ»:\n"
                "يدل على معنى مستقل غير مقترن بزمن\n"
                "يسلم من شبه الحرف\nعلى صيغة منتهى الجموع\nدخلت عليه أل")
        axes = read_morphology(text)["readings"][0]["axes"]
        self.assertEqual(axes["diptote"]["status"], "LICENSED")
        self.assertEqual(axes["diptote"]["genitive"]["candidates"], ["kasra"])
        self.assertFalse(axes["diptote"]["genitive"]["applied_to_occurrence"])
        self.assertIn("INDEPENDENT_GENITIVE_CASE_WITNESS", axes["diptote"]["genitive"]["prerequisites"])

    def test_unknown_qualification_blocks_nested_sign_approval(self):
        text = ("قراءة «r1» للفظ «سَنَارِمَ»:\n"
                "يدل على معنى مستقل غير مقترن بزمن\n"
                "يسلم من شبه الحرف\nعلى صيغة منتهى الجموع\nدخلت عليه أل\n"
                "هذا الحكم مشروط بقرينة لم تبين")
        report = read_morphology(text)
        genitive = report["readings"][0]["axes"]["diptote"]["genitive"]
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(genitive["status"], "DEFER")
        self.assertTrue(genitive["blocked_by_unparsed_source"])
        self.assertIn("COMPLETE_SOURCE_INTERPRETATION", genitive["prerequisites"])

    def test_canonical_number_preserves_a_report_but_cannot_authorize_a_changed_conclusion(self):
        text = ("قراءة «r1» للفظ «سَارِمٌ»:\n"
                "يدل على معنى مستقل غير مقترن بزمن\n"
                "لا يمنع تصوره الشركة\nيدل على ذات باعتبار صفة")
        report = read_morphology(text)
        encoded = morphology_number(report)
        self.assertEqual(decode_morphology(encoded), report)
        changed = deepcopy(report)
        changed["readings"][0]["axes"]["nominal_semantics"]["candidates"] = ["jins_jamid"]
        forged = int.from_bytes(b"\x01" + EVALUATOR.wire(changed), "big")
        with self.assertRaises(NabtError):
            decode_morphology(forged)
        for invalid in (True, -1, 0):
            with self.subTest(number=invalid), self.assertRaises(NabtError):
                decode_morphology(invalid)

    def test_same_source_bytes_in_another_scope_do_not_reuse_a_certificate(self):
        text = "قراءة «r1» للفظ «لُفْ»:\nيدل على معنى غير مستقل"
        report = read_morphology(text, source_id="same_source", scope="scope_a")
        self.assertFalse(verify_morphology(report, text=text, source_id="same_source", scope="scope_b")["valid"])


if __name__ == "__main__":
    unittest.main()
