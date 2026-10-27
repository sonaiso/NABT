"""Adversarial checks authored separately from the semantic-axes scorer.

The fixtures below are protocol specimens, not linguistic reference cases.
They never execute the frozen gold suite and cannot serve as Arabic evidence.
"""
from copy import deepcopy
import unittest

from tools import semantic_axes as adapter
from tools import benchmark_semantic_axes as benchmark


def specimen():
    request = {"text": "سَامِرٌ كَاتِبٌ", "context": {
        "entities": [{"id": "samir", "name": "سَامِرٌ"}],
        "speaker": "samir"}}
    case = {"id": "adversarial-protocol", "family": "protocol_test", "input": request,
            "expected": {
                "syntax": {"clause_form": "nominal", "required_roles": [
                    {"surface": "سَامِرٌ", "role": "nominal_subject"}]},
                "readings": {"required": [{"force": "ASSERT", "predicate": "كاتب"}],
                             "forbidden": [{"positive": False}], "selection": "unique"},
                "reference": {"surface": "سَامِرٌ", "status": "resolved", "target_ids": ["samir"]},
                "motive": {"status": "unestablished"},
                "world": {"status": "unestablished"}}}
    claim = {"positive": True, "predicate_kind": "property", "predicate": "كاتب",
             "tense": None, "time": None, "place": None, "restriction": None}
    analysis = {"rejected_candidate": False, "licensed_syntax": True,
                "force": "ASSERT", "claims": [claim], "frame": "nominal_predication",
                "assignments": [{"surface": "سَامِرٌ", "actual_role": "nominal_subject", "activated": True}],
                "analysis_id": "protocol-analysis", "span": {"start": 0, "end": 1},
                "references": [{"surface": "سَامِرٌ", "status": "RESOLVED",
                                "candidate_entity_ids": ["samir"], "bound_entity_id": "samir",
                                "reference_id": "protocol-reference"}]}
    raw = {"clauses": [{"status": "LICENSED", "force": "ASSERT", "span": {"start": 0, "end": 1},
                        "analyses": [analysis], "obligations": []}],
           "claims": [claim], "world_truth": "NOT_ESTABLISHED", "status": "LICENSED"}
    execution = adapter.execute_request(request, reader=lambda *a, **k: deepcopy(raw),
        verifier=lambda *a, **k: {"valid": True, "status": "VERIFIED",
                                 "authority": "TEXT_CONTEXT_AND_LEXICAL_SOURCE_REPLAY_ONLY"},
        lexical_model={})
    return case, execution, raw


class AdversarialSemanticAxes(unittest.TestCase):
    def test_protocol_control_has_positive_measurements(self):
        case, execution, _ = specimen()
        row = benchmark.score_case(case, execution)
        for axis in ("syntax", "readings", "reference"):
            self.assertEqual(row["axis_results"][axis]["status"], "PASS")

    def assert_no_measured_promotion(self, case, execution):
        try:
            result = benchmark.score_case(case, execution)
        except (ValueError, TypeError):
            return
        for axis in ("syntax", "readings", "reference"):
            self.assertEqual(result["axis_results"][axis]["status"], "UNMEASURED", axis)
        self.assertTrue(all(c["verification"]["checked"] is False for c in result["claims"]))

    def test_reusing_execution_for_different_text_is_not_authority(self):
        case, execution, _ = specimen()
        case["input"]["text"] = "سَامِرٌ لَيْسَ كَاتِبًا"
        self.assert_no_measured_promotion(case, execution)

    def test_same_text_with_changed_or_absent_context_cannot_reuse_receipt(self):
        case, execution, _ = specimen()
        for new_context in ({}, {"entities": [{"id": "other", "name": "سَامِرٌ"}], "speaker": "other"}):
            changed = deepcopy(case)
            changed["input"]["context"] = new_context
            self.assert_no_measured_promotion(changed, execution)

    def test_input_and_context_identity_conflicts_fail_closed(self):
        case, execution, _ = specimen()
        for key in ("input_sha256", "context_sha256", "replay_receipt_sha256"):
            altered = deepcopy(execution)
            altered[key] = "0" * 64
            self.assert_no_measured_promotion(case, altered)

    def test_receipt_with_contradictory_false_verification_is_not_checked(self):
        case, execution, _ = specimen()
        altered = deepcopy(execution)
        altered["replay_receipt"]["replay"]["valid"] = False
        altered["replay_receipt_sha256"] = adapter.identity(altered["replay_receipt"])
        self.assert_no_measured_promotion(case, altered)

    def test_observation_hash_cannot_be_repurposed_as_lean_proof(self):
        case, execution, _ = specimen()
        result = benchmark.score_case(case, execution)
        self.assertTrue(all(c["verification"]["kind"] != "LEAN_NATIVE" for c in result["claims"]))
        self.assertTrue(all(c["verification"]["theorem_references"] == [] for c in result["claims"]))

    def test_always_abstain_is_not_syntax_reading_or_reference_success(self):
        case, execution, _ = specimen()
        execution["observed"].update(syntax=[], readings=[], references=[], reading_selection=None,
                                     semantic_alternative_counts=[])
        result = benchmark.score_case(case, execution)
        for axis in ("syntax", "readings", "reference"):
            self.assertNotEqual(result["axis_results"][axis]["status"], "PASS", axis)

    def test_unimplemented_motive_and_world_remain_unmeasured(self):
        case, execution, _ = specimen()
        row = benchmark.score_case(case, execution)
        summary = benchmark.summarize([row])
        for axis in ("motive", "world"):
            self.assertEqual(summary[axis]["eligible"], 1)
            self.assertEqual(summary[axis]["measured"], 0)
            self.assertEqual(summary[axis]["unmeasured"], 1)
            self.assertIsNone(summary[axis]["rate"])

    def test_unlicensed_and_rejected_analyses_do_not_enter_projection(self):
        _, _, raw = specimen()
        for field, value in (("rejected_candidate", True), ("licensed_syntax", False)):
            altered = deepcopy(raw)
            altered["clauses"][0]["analyses"][0][field] = value
            observed = adapter.observe(altered)
            self.assertEqual(observed["syntax"], [])
            self.assertEqual(observed["readings"], [])
            self.assertEqual(observed["references"], [])

    def test_expected_labels_never_cross_adapter_boundary(self):
        case, _, _ = specimen()
        one = adapter.build_request(case)
        case["expected"] = {"fabricated": "answer"}
        case["id"] = "leaking-answer"
        self.assertEqual(adapter.build_request(case), one)
        self.assertEqual(set(one), {"text", "context"})

    def test_reference_scope_gap_cannot_be_union_hidden(self):
        case, execution, _ = specimen()
        good = execution["observed"]["references"][0]
        unresolved = deepcopy(good)
        unresolved.update(status="OPEN_SCOPE", bound_entity_id=None, candidate_entity_ids=[])
        got = benchmark._reference(case["expected"]["reference"], [good, unresolved])
        self.assertNotEqual(got["status"], "PASS")

    def test_open_reference_scope_is_not_exhaustive_ambiguity(self):
        expected = {"surface": "هُوَ", "status": "ambiguous", "target_ids": ["a", "b"]}
        actual = [{"surface": "هُوَ", "status": "OPEN_SCOPE", "bound_entity_id": None,
                   "candidate_entity_ids": ["a", "b"]}]
        self.assertNotEqual(benchmark._reference(expected, actual)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
