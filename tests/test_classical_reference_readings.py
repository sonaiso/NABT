"""Source-oracle benchmark, exhaustive Lean conformance and corruption tests."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("classical_reference_readings", ROOT / "tools/classical_reference_readings.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ClassicalReferenceReadingsTests(unittest.TestCase):
    def test_all_thirty_inputs_conform_to_lean(self):
        report = MODULE.conformance()
        self.assertTrue(report["valid"])
        self.assertEqual(report["input_count"], 30)

    def test_six_source_references_have_twelve_distinct_readings(self):
        report = MODULE.benchmark_reference_constructions()
        self.assertEqual(report["exact_set_matches"], 6)
        self.assertEqual(report["matched_reading_count"], 12)
        self.assertEqual(report["order_matches"], 6)
        self.assertFalse(report["free_text_parser_evaluated"])
        self.assertFalse(report["premise_acquisition_evaluated"])

    def test_each_withdrawn_reading_is_rejected(self):
        for frame in MODULE.all_frames():
            readings = MODULE.enumerate_readings(frame)["readings"]
            for i in range(len(readings)):
                with self.subTest(frame=frame, omitted=readings[i]):
                    result = MODULE.verify_proposal(frame, readings[:i] + readings[i + 1:])
                    self.assertFalse(result["conditional_exact_match"])
                    self.assertEqual(result["missing"], [readings[i]])

    def test_same_written_surface_keeps_two_descriptor_analyses(self):
        result = MODULE.enumerate_readings({"family": "matched_description", "number": "singular",
                                           "observed_ending": "nominative"})
        self.assertEqual(result["readings"], ["description_subject", "fronted_predicate"])
        self.assertNotEqual(*result["ranks"])

    def test_observed_mood_filters_an_without_inventing_a_reading(self):
        with_la = {"family": "interpretive_an", "has_la": True, "observed_ending": "jussive"}
        without_la = dict(with_la, has_la=False)
        self.assertEqual(MODULE.enumerate_readings(with_la)["readings"], ["an_interpretive_jussive"])
        self.assertEqual(MODULE.enumerate_readings(without_la)["readings"], [])

    def test_genitive_does_not_fit_any_listed_frame(self):
        for frame in MODULE.all_frames():
            if frame["observed_ending"] == "genitive":
                self.assertEqual(MODULE.enumerate_readings(frame)["readings"], [])

    def test_reordering_or_duplicates_do_not_preserve_the_contract(self):
        frame = {"family": "free_ishtighal"}
        readings = MODULE.enumerate_readings(frame)["readings"]
        self.assertFalse(MODULE.verify_proposal(frame, list(reversed(readings)))["conditional_exact_match"])
        self.assertFalse(MODULE.verify_proposal(frame, readings + readings)["conditional_exact_match"])

    def test_no_caller_label_can_grant_a_language_certificate(self):
        result = MODULE.enumerate_readings({"family": "free_ishtighal"})
        self.assertFalse(result["premises_verified"])
        self.assertFalse(result["language_certificate_granted"])
        for frame in ({"family": "free_ishtighal", "trusted": True},
                      {"family": "interpretive_an", "has_la": 1},
                      {"family": "free_ishtighal", "observed_ending": False},
                      {"family": "free_ishtighal", "gold": ["topic"]}):
            with self.assertRaises(ValueError):
                MODULE.enumerate_readings(frame)

    def test_export_mutation_is_detected(self):
        export = json.loads(MODULE.EXPORT.read_text())
        export["rows"][0]["readings"].pop()
        self.assertFalse(MODULE.conformance(export)["valid"])

    def test_incomplete_export_domain_is_rejected(self):
        export = json.loads(MODULE.EXPORT.read_text())
        export["rows"].pop()
        with self.assertRaises(ValueError):
            MODULE.conformance(export)


if __name__ == "__main__":
    unittest.main()
