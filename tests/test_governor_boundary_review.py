"""Independent review counterexamples; not the held-out evaluation corpus."""

import unittest

from nabt.governor_reader import LANGUAGE_ID, read_arabic
from nabt.program import compile_request, execute_program, verify_execution
from nabt.semantics import SemanticKernel


class GovernorBoundaryReviewTests(unittest.TestCase):
    def assert_deferred(self, source, obligation):
        reading = read_arabic(source)
        self.assertFalse(reading.accepted)
        self.assertEqual(reading.steps[-1].fact_count, 0)
        self.assertIn(obligation, reading.steps[-1].obligations)
        admission = SemanticKernel(language_id=LANGUAGE_ID).add_source(source)
        self.assertEqual((admission.accepted, admission.status), (False, "DEFER"))
        return reading

    def test_repeated_indefinite_builds_roles_but_not_a_recurring_individual(self):
        source = "طالبةٌ هي حاضرةٌ. إِنَّ طالبةً نشيطةٌ."
        reading = self.assert_deferred(source, "REFERENT_IDENTITY_EVIDENCE")
        report = reading.steps[-1].governor
        self.assertTrue(report["syntactic_evidence_complete"])
        self.assertIsNone(report["referent_identity"])
        self.assertEqual(report["semantic_projection"], "DEFER")
        self.assertEqual([r["observed_mark"] for r in report["roles"]], [0, 1])
        # A concept declaration is still different from an individual binding.
        self.assert_deferred("مفهوم طالبة. إِنَّ طالبةً نشيطةٌ.", "REFERENT_IDENTITY_EVIDENCE")
        for prefix in ("فرد طالبة.", "«طالبة» هي حاضرةٌ."):
            with self.subTest(prefix=prefix):
                self.assertTrue(read_arabic(prefix + " إِنَّ طالبةً نشيطةٌ.").accepted)

    def test_internal_tanwin_and_estimated_cases_never_become_observed_assignments(self):
        self.assert_deferred("فرد سهيل. إِنَّ سهيلَ صابٌرٌ.", "UNSUPPORTED_INTERNAL_TANWIN")
        for source, surface in (("فرد فتى. إِنَّ فتىً مسافرٌ.", "ً"),
                                ("فرد بشر. إِنَّ بشرَ قاضٍ.", "ٍ")):
            with self.subTest(source=source):
                report = self.assert_deferred(source, "DECLENSION_CLASS_EVIDENCE").steps[-1].governor
                role = report["roles"][0 if surface == "ً" else 1]
                self.assertEqual(role["surface_ending"], surface)
                self.assertIsNone(role["observed_mark"])
                self.assertIsNone(role["role_mark_number"])
                self.assertEqual(report["case_check"]["complete"], [])
                self.assertTrue(report["case_check"]["viable"])

    def test_an_attested_stem_does_not_license_an_extra_support_alif(self):
        for name, predicate in (("غرفة", "واسعة"), ("ملجأ", "واسع"), ("سماء", "صافية")):
            with self.subTest(name=name):
                prefix = f"فرد {name}. إِنَّ "
                self.assertTrue(read_arabic(prefix + name + "ً " + predicate + "ٌ.").accepted)
                self.assert_deferred(prefix + name + "ًا " + predicate + "ٌ.", "ORTHOGRAPHY_EVIDENCE")
                self.assert_deferred(prefix + name + "اً " + predicate + "ٌ.", "ORTHOGRAPHY_EVIDENCE")

    def test_possible_article_and_tanwin_require_a_spelling_interpretation(self):
        self.assertTrue(read_arabic("فرد الرجل. إِنَّ الرجلَ حاضرٌ.").accepted)
        self.assert_deferred("فرد الرجل. إِنَّ الرجلًا حاضرٌ.", "ORTHOGRAPHY_EVIDENCE")
        self.assert_deferred("فرد زيد. إِنَّ زيدَ الحاضرٌ.", "ORTHOGRAPHY_EVIDENCE")

    def test_missing_identity_is_defer_through_the_program_and_replay_boundary(self):
        program = compile_request({"task": "governor_inquiry", "events": [
            {"op": "add", "source_id": "unresolved", "text": "إِنَّ شجرةً مثمرةٌ."},
        ]})
        receipt = execute_program(program)
        self.assertEqual(receipt["run_status"], "STOPPED")
        self.assertEqual(receipt["result"]["status"], "DEFER")
        self.assertFalse(receipt["result"]["accepted"])
        self.assertEqual(receipt["result"]["residuals"][0]["code"], "REFERENT_IDENTITY_EVIDENCE")
        self.assertTrue(verify_execution(receipt)["valid"])


if __name__ == "__main__":
    unittest.main()
