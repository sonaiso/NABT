"""Finite parser/unit cases; raw source native execution is independently tested."""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.licensed_inference import InferenceBudget, aggregate_evidence, evaluate
from tools.licensed_inference.parser import read_source, read_query
from tools.licensed_inference.runtime import ROOT, _native, wire


K = "عرف زيد الحق"
E = "سار زيد أمامك خلف الدار"
Q = "هل سار زيد أمامك خلف الدار؟"


class FiniteParser(unittest.TestCase):
    def test_qualified_event_and_token_byte_spans(self):
        text = " \tسَارَ زَيْدٌ أَمَامَكَ خَلْفَ الدَّارِ إِنْ عَرَفَ عَمْرٌو الْحَقَّ.\n"
        parsed = read_source(text)
        self.assertEqual(parsed["status"], "PROPOSED")
        rule = parsed["clauses"][0]
        self.assertEqual(rule["head"]["arguments"], ["زيد", "أمامك_خلف_الدار"])
        self.assertEqual(rule["body"][0]["arguments"], ["عمرو", "الحق"])
        for segment in parsed["segments"]:
            for token in segment["tokens"]:
                span = token["span"]
                self.assertEqual(text.encode()[span["start_byte"]:span["end_byte"]].decode(), span["raw_text"])

    def test_front_post_and_negative_condition_keep_signed_body(self):
        front = read_source("إن لم يعرف زيد الحق لم يسر عمرو خلف الدار")
        post = read_source("لم يسر عمرو خلف الدار إن لم يعرف زيد الحق")
        self.assertEqual(front["clauses"], post["clauses"])
        rule = front["clauses"][0]
        self.assertFalse(rule["body"][0]["positive"])
        self.assertFalse(rule["head"]["positive"])

    def test_unsupported_later_clause_blocks_every_executable_clause(self):
        for text in (K + ". " + E + " ربما", K + ".." + E,
                     "«\n" + K + ".\n»", K + ". قال زيد " + E,
                     "عُرِفَ زَيْدٌ الْحَقَّ", "عَرَّفَ زَيْدٌ الْحَقَّ",
                     "سَارَ زَيْدَ", "عرف\u00a0زيد الحق"):
            parsed = read_source(text)
            self.assertIsNone(parsed["clauses"], text)
            self.assertEqual(parsed["reason"], "OUTSIDE_FRAGMENT")

    def test_hidden_subject_is_not_bound_to_main_subject(self):
        for text in (E + " إن عرف الحق", "إن عرف الحق " + E):
            parsed = read_source(text)
            self.assertEqual(parsed["reason"], "UNRESOLVED_REFERENCE")
            self.assertIsNone(parsed["clauses"])
            self.assertIsNone(parsed["segments"][0]["proposal"]["antecedent_subject"])

    def test_query_is_full_and_locatives_are_not_projected_away(self):
        self.assertNotEqual(read_query(Q), read_query("هل سار زيد؟"))
        self.assertIsNone(read_query(Q + " ربما"))
        self.assertIsNone(read_query("هل سار زيد?"))
        self.assertFalse(read_query("هل لم يسر زيد أمامك خلف الدار؟")["positive"])


class AggregateCalculation(unittest.TestCase):
    def evidence(self, positive=False, negative=False, clean_positive=False, clean_negative=False):
        return dict(positive=positive, negative=negative,
                    clean_positive=clean_positive, clean_negative=clean_negative)

    def test_cross_reading_disagreement_is_distinct_from_same_reading_conflict(self):
        positive = self.evidence(True, False, True, False)
        negative = self.evidence(False, True, False, True)
        opposed = aggregate_evidence([positive, negative])
        self.assertEqual(opposed["status"], "DISAGREEMENT")
        self.assertFalse(opposed["aggregate"]["within_reading_conflict"])
        conflict = aggregate_evidence([positive, self.evidence(True, True)])
        self.assertEqual(conflict["status"], "CONFLICT")
        self.assertFalse(conflict["aggregate"]["skeptical_clean_positive"])

    def test_empty_missing_or_contaminated_reading_cannot_universally_support(self):
        positive = self.evidence(True, False, True, False)
        self.assertEqual(aggregate_evidence([])["status"], "UNKNOWN")
        self.assertEqual(aggregate_evidence([positive, self.evidence()])["status"], "DEFER")
        self.assertEqual(aggregate_evidence([self.evidence(True)])["status"], "DEFER")
        with self.assertRaises(ValueError):
            aggregate_evidence([{"status": "SUPPORTED"}])
        with self.assertRaises(ValueError):
            aggregate_evidence([dict(positive=1, negative=False, clean_positive=True, clean_negative=False)])


class PublicBoundaries(unittest.TestCase):
    def test_invalid_raw_utf8_metadata_and_boolean_budget(self):
        for source, query in ((True, Q), (K, []), (b"\xff", Q), (K, "\ud800"), ("", Q)):
            self.assertEqual(evaluate(source, query)["status"], "INVALID_INPUT")
        self.assertEqual(evaluate(K, Q, scope="\ud800")["status"], "INVALID_INPUT")
        for bad in (True, -1, 2.5, 513):
            with self.assertRaises(ValueError):
                InferenceBudget(max_atoms=bad)

    def test_bytes_budget_before_parsing(self):
        with patch("tools.licensed_inference.runtime.read_source", side_effect=AssertionError("must not parse")):
            result = evaluate(K, Q, budget=InferenceBudget(max_source_bytes=1))
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")


class ActualNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.licensed_inference.sources import build_inventory
        build_inventory()
        if not (ROOT / "formal/.lake/build/bin/licensedInference").exists():
            raise unittest.SkipTest("build optional licensedInference")

    def check(self, source, query=Q, status=None, **options):
        result = evaluate(source, query, **options)
        if status:
            self.assertEqual(result["status"], status, result.get("reason"))
        self.assertFalse(result["world_truth_established"])
        self.assertFalse(result["all_arabic_complete"])
        return result

    def test_actual_fact_and_rule_firing_use_original_source_and_checked_closure(self):
        text = E + " إن " + K + ". " + K + ".\n"
        result = self.check(text, status="SUPPORTED", source_id="source_a", revision="r1", scope="مجلس", time="t1")
        self.assertTrue(result["verified"])
        self.assertTrue(result["all_readings_complete"])
        self.assertEqual(result["native_result"]["source_text"], text)
        self.assertEqual(result["binding"]["time"], "t1")
        self.assertEqual(json.loads(result["native_result"]["source_scope"]), {"scope": "مجلس", "time": "t1"})
        self.assertTrue(result["closure_records"][0]["steps"])

    def test_condition_is_not_actuality_or_converse_or_denial(self):
        rule = E + " إن " + K
        self.check(rule, status="UNKNOWN")
        self.check(rule + ". " + E, "هل عرف زيد الحق؟", "UNKNOWN")
        self.check(rule + ". لم يعرف زيد الحق", "هل لم يسر زيد أمامك خلف الدار؟", "UNKNOWN")

    def test_scope_and_full_event_frame_do_not_alias(self):
        self.check(E + " إن عرف عمرو الحق. " + K, status="UNKNOWN")
        self.check(E, "هل سار زيد؟", "UNKNOWN")
        self.check(E, "هل سار زيد خلف الدار؟", "UNKNOWN")
        first = self.check(K, "هل عرف زيد الحق؟", "SUPPORTED", time="t1")
        second = self.check(K, "هل عرف زيد الحق؟", "SUPPORTED", time="t2")
        self.assertNotEqual(first["proposal"]["source"]["scope"], second["proposal"]["source"]["scope"])

    def test_conflict_and_signed_query_with_clean_support(self):
        self.check(E + ". لم يسر زيد أمامك خلف الدار", status="CONFLICT")
        self.check("لم يسر زيد أمامك خلف الدار", status="REFUTED")
        self.check("لم يسر زيد أمامك خلف الدار", "هل لم يسر زيد أمامك خلف الدار؟", "SUPPORTED")
        self.check(K + ". لم يعرف زيد الحق. " + E + " إن " + K, status="DEFER")

    def test_unresolved_and_unrecognized_source_do_not_receive_certificates(self):
        unresolved = self.check(E + " إن عرف الحق", status="UNKNOWN")
        self.assertEqual(unresolved["reason"], "UNRESOLVED_REFERENCE")
        self.assertFalse(unresolved["all_readings_complete"])
        self.assertFalse(unresolved["verified"])
        unsupported = self.check(K + ". زيد يعرف أمرا آخر", status="UNKNOWN")
        self.assertEqual(unsupported["proposal"]["readings"], [])

    def test_resource_limits_and_missing_checker_do_not_become_unknown(self):
        for budget in (InferenceBudget(max_readings=0), InferenceBudget(max_atoms=0),
                       InferenceBudget(max_closure_steps=0), InferenceBudget(max_clauses=0)):
            self.check(K, "هل عرف زيد الحق؟", "RESOURCE_EXHAUSTED", budget=budget)
        with patch("tools.licensed_inference.runtime._native", side_effect=OSError("missing native")):
            self.check(K, "هل عرف زيد الحق؟", "VERIFICATION_UNAVAILABLE")

    def test_native_response_must_match_complete_typed_postcondition(self):
        genuine = self.check(E, status="SUPPORTED")["native_result"]
        mutations = []
        for key, value in (("verified", 1), ("reading_count", 1.0), ("world_truth_established", True),
                           ("status", "UNKNOWN"), ("source_scope", "changed")):
            changed = deepcopy(genuine)
            changed[key] = value
            mutations.append(changed)
        changed = deepcopy(genuine)
        changed["rows"][0]["positive"] = 1
        mutations.append(changed)
        for changed in mutations:
            with patch("tools.licensed_inference.runtime._native", return_value=changed):
                result = self.check(E, status="VERIFICATION_UNAVAILABLE")
            self.assertFalse(result["verified"])
            self.assertFalse(result["closures_checked"])

    def test_native_reopens_original_bytes_and_checks_missing_extra_readings(self):
        cert = self.check(E, status="SUPPORTED")["proposal"]
        binding = {key: cert["source"][key] for key in ("identity", "revision", "scope")}
        for mutated in ({**cert, "readings": []}, {**cert, "readings": cert["readings"] * 2}):
            response = _native(E.encode(), Q.encode(), mutated, binding)
            self.assertFalse(response["verified"])
        response = _native((E + " ربما").encode(), Q.encode(), cert, binding)
        self.assertFalse(response["verified"])


if __name__ == "__main__":
    unittest.main()
