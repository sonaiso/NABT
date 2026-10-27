"""Measurement-policy controls; fixture receipts are not native evidence."""
from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from tools import benchmark_six_noun_acquisition as bench


class SixNounMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.reference = bench._load_reference()
        self.case = self.reference["cases"][0]

    def receipt(self, case=None):
        case = case or self.case
        value = case["input"]
        return {"source": {"id": value["source_id"], "text": value["text"],
                "revision": sha256(value["text"].encode()).hexdigest()},
                "context": value["context"], "native_checked": True,
                "grammar_certified": True, "status": "CHECKED_SIX_NOUN",
                "reading": {"grammatical_case": "raf", "lexeme": "ab"},
                "claims": [{"context": value["context"]}], "linguistic_rejection": False,
                **{key: False for key in ("strict_language_accepted", "intended_sense_established",
                   "world_truth_established", "external_truth_established", "speaker_reference_established",
                        "tawatur_established", "whole_arabic_complete")}}

    def test_reference_is_independent_frozen_and_axes_remain_separate(self):
        self.assertEqual(len(self.reference["cases"]), 45)
        self.assertIs(self.reference["expected_answers_generated_by_production"], False)
        self.assertIs(self.reference["held_out"], False)
        for case in self.reference["cases"]:
            self.assertEqual(case["expected"]["external_truth"], "NOT_MEASURED")

    def test_safe_deferral_does_not_pass_positive_analysis(self):
        value = self.receipt()
        value.update(status="DEFER", grammar_certified=False, claims=[])
        scores = bench._score(self.case, value)
        self.assertTrue(scores["source_identity"])
        self.assertFalse(scores["positive_licensed_reading"])
        self.assertFalse(scores["full_form_analysis"])

    def test_native_flag_without_matching_case_or_claim_is_insufficient(self):
        self.assertTrue(bench._score(self.case, self.receipt())["full_form_analysis"])
        for mutate in (lambda r: r.update(claims=[]),
                       lambda r: r["reading"].update(grammatical_case="jarr"),
                       lambda r: r.update(context="different occurrence"),
                       lambda r: r.update(native_checked=1)):
            value = self.receipt(); mutate(value)
            self.assertFalse(bench._score(self.case, value)["full_form_analysis"])

    def test_scope_deferral_is_safe_boundary_not_scope_composition(self):
        case = next(c for c in self.reference["cases"] if c["id"] == "S01")
        value = self.receipt(case)
        value.update(status="OUTSIDE_EXECUTED_FRAGMENT", claims=[], grammar_certified=False, reading=None)
        scores = bench._score(case, value)
        self.assertTrue(scores["scope_authority_boundary"])
        self.assertFalse(scores["scope_composition"])
        self.assertIsNone(scores["full_form_analysis"])

    def test_generic_deferral_does_not_claim_specific_missing_premise(self):
        case = next(c for c in self.reference["cases"] if c["id"] == "D01")
        value = self.receipt(case)
        value.update(status="OUTSIDE_EXECUTED_FRAGMENT", claims=[], grammar_certified=False, reading=None)
        self.assertFalse(bench._score(case, value)["alternative_specificity"])

    def test_only_input_goes_to_runtime_and_missing_native_stays_visible(self):
        calls = []
        def unavailable(text, **kwargs):
            calls.append((text, kwargs))
            return {"status": "VERIFICATION_UNAVAILABLE", "claims": [], "native_checked": False}
        report = bench._measure(self.reference, unavailable)
        self.assertEqual(len(calls), 45)
        self.assertTrue(all(set(kw) == {"source_id", "context"} for _, kw in calls))
        self.assertEqual(report["native_required_count"], 43)
        self.assertFalse(report["native_execution_complete"])
        self.assertEqual(report["axes"]["positive_licensed_reading"]["passed"], 0)
        self.assertIsNone(report["axes"]["external_truth"]["total"])

    def test_foundation_blocks_cli_before_parser_and_acquisition(self):
        with patch.object(bench.foundation, "require_foundation", side_effect=NabtError("DENIED", "test")), \
                patch.object(bench.argparse, "ArgumentParser") as parser:
            with self.assertRaises(NabtError):
                bench.main()
            parser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
