"""Independent tests of measurement boundaries, never a linguistic proof oracle."""
from __future__ import annotations

import hashlib
import json
import unittest
from unittest.mock import patch

from tools import benchmark_qualified_cues as benchmark


def receipt(case, *, selected=(), excluded=()):
    """Synthetic untrusted receipt used to test the scorer, not acquisition."""
    text = case["input"]["text"]
    raw = text.encode("utf-8")
    context = case["input"]["context"]
    target = case["target"]
    labels = {"eye": "العين الباصرة", "spring": "عين الماء",
              "lion": "الحيوان المفترس", "brave_man": "الرجل الشجاع"}
    senses = ["lion", "brave_man"] if "سَد" in target["surface"] else ["eye", "spring"]
    frame = {"occurrence": {
        "source": context["utterance_id"], "revision": hashlib.sha256(raw).hexdigest(),
        "raw": text, "start_byte": target["start_byte"], "end_byte": target["end_byte"],
        "referent": context["speaker_id"], "context": benchmark._arguments(case)["context"]}}
    occurrence = {
        "occurrence_id": context["utterance_id"] + ":synthetic",
        "span": {"start_byte": target["start_byte"], "end_byte": target["end_byte"],
                 "raw_text": target["surface"], "sha256": target["sha256"]},
        "frame": frame,
        "candidates": [{"sense_id": sense, "gloss": labels[sense]} for sense in senses],
        "selected_sense_ids": list(selected), "excluded_sense_ids": list(excluded),
        "intended_sense_acquired": bool(selected or excluded),
        "cue_readings": [[{"synthetic": True}]] if selected or excluded else [],
    }
    return {"status": "PARTIAL", "strict_language_accepted": False, "native_checked": False,
            "claims": [], "occurrences": [], "foundation_source": {"status": "PARTIAL"},
            "diagnostic": {"status": "UNKNOWN", "world_truth_established": False,
                "all_arabic_complete": False, "occurrences": [occurrence],
                "source": {"source_id": context["utterance_id"], "raw_text": text,
                           "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}}}


class QualifiedCueBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {case["id"]: case for case in benchmark.load_cases()}

    def score(self, cid, **kwargs):
        case = self.cases[cid]
        report = receipt(case, **kwargs)
        return benchmark.evaluate(case, report), report

    def test_frozen_population_and_independent_denominators(self):
        self.assertEqual(len(self.cases), 24)
        self.assertEqual(sum(bool(case["expected"]["selected_senses"])
                             for case in self.cases.values()), 12)
        self.assertEqual(sum(case["expected"]["semantic_acquisition_eligible"]
                             for case in self.cases.values()), 20)
        self.assertEqual(sum(case["expected"]["qualified_frame"] == "marked_frame_mismatch"
                             for case in self.cases.values()), 4)

    def test_safe_quote_abstention_does_not_pass_positive_meaning(self):
        row, _ = self.score("S02")
        self.assertEqual(row["axes"]["diagnostic_positive_selection"]["outcome"], "FAIL")
        self.assertEqual(row["axes"]["no_current_speaker_leakage"]["outcome"], "PASS")
        self.assertEqual(row["axes"]["scope_comprehension"]["outcome"], "UNMEASURED")

    def test_unqualified_quote_selection_is_current_speaker_leakage(self):
        row, _ = self.score("S02", selected=["eye"])
        self.assertEqual(row["axes"]["diagnostic_positive_selection"]["outcome"], "PASS")
        self.assertEqual(row["axes"]["no_current_speaker_leakage"]["outcome"], "FAIL")
        self.assertEqual(row["axes"]["scope_comprehension"]["outcome"], "UNMEASURED")

    def test_explicit_quoted_scope_is_measured_without_granting_execution(self):
        case = self.cases["S02"]
        report = receipt(case, selected=["eye"])
        report["diagnostic"]["occurrences"][0].update({
            "acquired_scope": "quoted_speaker", "scope_stack": ["assertion", "reported_speech"],
            "semantic_owner": "entity:salma", "local_declared_senses": ["eye"],
            "current_speaker_selected_senses": [],
        })
        row = benchmark.evaluate(case, report)
        self.assertEqual(row["axes"]["scope_comprehension"]["outcome"], "PASS")
        self.assertEqual(row["axes"]["no_current_speaker_leakage"]["outcome"], "PASS")
        self.assertFalse(row["executed_locally"])
        self.assertEqual(row["axes"]["declared_native_execution"]["outcome"], "FAIL")

    def test_wrong_quoted_owner_fails_scope(self):
        case = self.cases["S02"]
        report = receipt(case, selected=["eye"])
        report["diagnostic"]["occurrences"][0]["semantic_owner"] = "entity:omar"
        row = benchmark.evaluate(case, report)
        self.assertEqual(row["axes"]["scope_comprehension"]["outcome"], "FAIL")

    def test_second_occurrence_cannot_satisfy_first_occurrence_target(self):
        first, second = self.cases["O01"], self.cases["O02"]
        report = receipt(first, selected=["eye"])
        target = second["target"]
        occurrence = report["diagnostic"]["occurrences"][0]
        occurrence["span"].update(start_byte=target["start_byte"], end_byte=target["end_byte"])
        occurrence["frame"]["occurrence"].update(start_byte=target["start_byte"], end_byte=target["end_byte"])
        row = benchmark.evaluate(first, report)
        self.assertEqual(row["axes"]["target_occurrence"]["outcome"], "FAIL")
        self.assertEqual(row["axes"]["diagnostic_positive_selection"]["outcome"], "FAIL")

    def test_same_text_other_speaker_receipt_is_not_reused(self):
        report = receipt(self.cases["D01"], selected=["eye"])
        row = benchmark.evaluate(self.cases["D02"], report)
        self.assertEqual(row["axes"]["source_identity"]["outcome"], "FAIL")
        self.assertEqual(row["axes"]["diagnostic_positive_selection"]["outcome"], "FAIL")

    def test_negative_exclusion_cannot_choose_open_world_complement(self):
        row, _ = self.score("N01", selected=["eye"], excluded=["spring"])
        self.assertEqual(row["axes"]["explicit_negative_exclusion"]["outcome"], "FAIL")
        self.assertEqual(row["axes"]["safe_nonselection"]["outcome"], "FAIL")

    def test_marked_frame_mismatch_has_no_positive_or_scope_denominator(self):
        safe, _ = self.score("M02")
        unsafe, _ = self.score("M02", selected=["spring"])
        self.assertEqual(safe["axes"]["marked_frame_guard"]["outcome"], "PASS")
        self.assertEqual(unsafe["axes"]["marked_frame_guard"]["outcome"], "FAIL")
        self.assertEqual(safe["axes"]["diagnostic_positive_selection"]["outcome"], "NOT_ELIGIBLE")
        self.assertEqual(safe["axes"]["scope_comprehension"]["outcome"], "NOT_ELIGIBLE")

    def test_contradictory_nested_promotions_are_rejected(self):
        case = self.cases["P01"]
        for key in ("motive_established", "whole_arabic_complete"):
            for value in (True, 0, "false", None):
                report = receipt(case, selected=["eye"])
                report["unexpected_layer"] = {key: value}
                row = benchmark.evaluate(case, report)
                self.assertEqual(row["axes"]["no_unsupported_promotion"]["outcome"], "FAIL")

    def test_malformed_scope_payload_does_not_crash_or_pass(self):
        case = self.cases["S02"]
        report = receipt(case)
        report["diagnostic"]["occurrences"][0].update({
            "local_declared_senses": [{"sense": "eye"}],
            "acquired_scope": "quoted_speaker", "semantic_owner": {"speaker": "salma"}})
        row = benchmark.evaluate(case, report)
        self.assertEqual(row["axes"]["scope_comprehension"]["outcome"], "FAIL")

    def test_scope_absence_does_not_expand_measured_denominator(self):
        rows = [self.score("S02")[0], self.score("M02")[0]]
        summary = benchmark.summarize(rows)
        self.assertEqual(summary["axes"]["scope_comprehension"], {
            "eligible": 1, "measured": 0, "passed": 0, "failed": 0, "unmeasured": 1, "fraction": None})
        self.assertEqual(summary["axes"]["diagnostic_positive_selection"]["failed"], 1)
        self.assertEqual(summary["locally_executed_cases"], 0)

    def test_boolean_span_cannot_match_integer_coordinate(self):
        case = self.cases["NP03"]
        report = receipt(case)
        report["diagnostic"]["occurrences"][0]["span"]["start_byte"] = False
        row = benchmark.evaluate(case, report)
        self.assertEqual(row["axes"]["target_occurrence"]["outcome"], "FAIL")

    def test_missing_execution_status_is_not_available(self):
        row = benchmark.evaluate(self.cases["P01"], {})
        self.assertEqual(row["axes"]["execution_available"]["outcome"], "FAIL")

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                json.loads(raw, object_pairs_hook=benchmark._unique_object,
                           parse_constant=benchmark._nonfinite)

    def test_diagnostic_result_does_not_invent_formal_proof(self):
        row, _ = self.score("P01", selected=["eye"])
        self.assertEqual(row["axes"]["diagnostic_positive_selection"]["outcome"], "PASS")
        self.assertEqual(row["axes"]["complete_a116_projection"]["outcome"], "FAIL")
        self.assertEqual(row["axes"]["declared_native_execution"]["outcome"], "FAIL")
        self.assertEqual(row["observation"]["consistent_named_claim_count"], 0)
        self.assertFalse(row["observation"]["strict_language_accepted"])
        self.assertNotIn("proof", row)

    def test_run_binds_changed_native_identity_and_never_passes_gold_to_acquisition(self):
        case = self.cases["P01"]
        report = receipt(case, selected=["eye"])
        before = {"input_files": {}, "native_checker": {"sha256": "native-before"}}
        after = {"input_files": {}, "native_checker": {"sha256": "native-after"}}
        with patch.object(benchmark, "load_cases", return_value=[case]), \
                patch("tools.linguistic_truth.certified.acquire_certified", return_value=report) as acquire, \
                patch("tools.benchmark_linguistic_truth.evidence_snapshot", side_effect=[before, after]):
            result = benchmark.run()
        acquire.assert_called_once_with(case["input"]["text"], **benchmark._arguments(case))
        self.assertFalse(result["execution_evidence"]["integrity"]["valid"])
        self.assertFalse(result["safety_gate_passed"])
        self.assertEqual(result["rows"][0]["receipt"], report)
        self.assertIn(str(benchmark.CORPUS.relative_to(benchmark.ROOT)),
                      result["execution_evidence"]["before"]["input_files"])

    def test_historical_runner_keeps_scores_but_binds_execution_integrity(self):
        from tools import benchmark_certified_natural_use as historical
        case = self.cases["P01"]
        report = receipt(case, selected=["eye"])
        before = {"input_files": {}, "native_checker": {"sha256": "same"}, "dependency": "old"}
        after = {"input_files": {}, "native_checker": {"sha256": "same"}, "dependency": "new"}
        with patch.object(historical, "load_cases", return_value=([case], [])), \
                patch("tools.linguistic_truth.certified.acquire_certified", return_value=report), \
                patch("tools.benchmark_linguistic_truth.evidence_snapshot", side_effect=[before, after]):
            result = historical.run()
        self.assertFalse(result["execution_evidence"]["integrity"]["valid"])
        self.assertFalse(result["safety_gate_passed"])
        self.assertEqual(result["rows"][0]["receipt"], report)
        self.assertEqual(result["summary"]["positive_selection"]["numerator"], 1)


if __name__ == "__main__":
    unittest.main()
