"""Independent authority, comparison and transport boundary regressions."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from tools import benchmark_contextual_reference as benchmark
from tools import proof_lab as lab

PAYLOAD = json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "contextual_reference"})
IDENTITY = {"code_sha": "a" * 40, "native_sha256": "b" * 64,
            "runtime_sha256": "c" * 64, "runner_sha256": "d" * 64,
            "original_reference_sha256": "e" * 64,
            "independent_reference_sha256": "f" * 64,
            "source_registry_sha256": "1" * 64, "scorer_sha256": "2" * 64,
            "baseline_source_sha256": "3" * 64}


def suite():
    return {"schema": "nabt.contextual-reference-benchmark.v1",
            "law_id": "nabt.initial-contextual-reference.v1",
            **{k: v for k, v in IDENTITY.items() if k not in ("code_sha", "runner_sha256")},
            "all_cases_native_checked": True, "whole_arabic_complete": False,
            "tawatur_evaluated": False, "world_truth_established": False,
            "motive_measured": False}


def receipt():
    return {"native_checked": True, "certificate_checked": True,
            "reference": {"surface": "أَنَا", "span": {"start": 0, "end": 5},
                          "status": "RESOLVED", "candidate_entity_ids": ["speaker_a"],
                          "bound_entity_id": "speaker_a"}}


class ContextualComparison(unittest.TestCase):
    def test_new_reference_is_frozen_without_rewriting_original(self):
        self.assertEqual(len(benchmark.load_independent_reference()["cases"]), 20)
        reference, digest, _ = benchmark.historical.load_reference()
        self.assertEqual(len(reference["cases"]), 25)
        self.assertEqual(digest, "9787e4496118a80a4f352ef19193e1e37976eb282eaf96caaad511ce77ffa431")

    def test_native_occurrence_proof_is_not_gold_agreement(self):
        expected = {"surface": "أَنَا", "status": "resolved", "target_ids": ["speaker_b"]}
        self.assertEqual(benchmark.compare_reference(expected, receipt())["status"], "FAIL")

    def test_quoted_self_reference_cannot_reuse_outer_occurrence(self):
        expected = {"surface": "أَنَا", "status": "resolved", "target_ids": ["speaker_a"],
                    "span": {"start": 0, "end": 5}, "scope": "quoted", "occurrence": 0}
        self.assertEqual(benchmark.compare_reference(expected, receipt())["status"], "FAIL")

    def test_refusal_about_no_target_is_not_successful_unresolved_answer(self):
        expected = {"surface": "أَنَا", "status": "unresolved", "target_ids": []}
        result = benchmark.compare_reference(expected, {"native_checked": True,
            "certificate_checked": True, "reference": None})
        self.assertEqual(result["status"], "FAIL")

    def test_missing_native_remains_unmeasured_not_abstention_success(self):
        expected = {"surface": "أَنَا", "status": "unresolved", "target_ids": []}
        self.assertEqual(benchmark.compare_reference(expected, {})["status"], "UNMEASURED")

    def test_duplicate_candidate_cannot_count_as_exact_resolution(self):
        expected = {"surface": "أَنَا", "status": "resolved", "target_ids": ["speaker_a"]}
        execution = receipt()
        execution["reference"]["candidate_entity_ids"] *= 2
        self.assertEqual(benchmark.compare_reference(expected, execution)["status"], "FAIL")

    def test_omitting_an_ambiguous_candidate_fails_reference_recall(self):
        expected = {"surface": "أَنَا", "status": "ambiguous", "target_ids": ["a", "b"]}
        execution = receipt()
        execution["reference"].update(status="AMBIGUOUS", candidate_entity_ids=["a"], bound_entity_id=None)
        self.assertEqual(benchmark.compare_reference(expected, execution)["status"], "FAIL")


class ContextualTransport(unittest.TestCase):
    def test_fixed_mode_cannot_inject_gold_or_attestation(self):
        self.assertEqual(lab.validate_payload(PAYLOAD)["mode"], "contextual_reference")
        for key in ("source", "context", "gold", "certificate", "author", "tawatur",
                    "native_checked", "path", "url", "executable", "lexical_profile"):
            with self.subTest(key=key), self.assertRaises(lab.RequestError):
                lab.validate_payload(json.dumps({**json.loads(PAYLOAD), key: "injected"}))

    def test_prepare_does_not_execute_reference_suite(self):
        with patch.object(lab, "_contextual_identity", return_value=IDENTITY), \
             patch.object(benchmark, "run", side_effect=AssertionError("executed")):
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD, prepare=True)
        self.assertEqual(response["status"], "PREPARED")
        self.assertEqual(response["scope"]["tawatur"], "NOT_EVALUATED")
        self.assertEqual(response["scope"]["whole_clause"], "NOT_PROVED")

    def test_missing_native_stops_before_running_comparator(self):
        with patch.object(lab, "_contextual_identity", return_value=IDENTITY | {"native_sha256": None}), \
             patch.object(benchmark, "run", side_effect=AssertionError("executed")):
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
        self.assertNotIn("contextual_reference", response)

    def test_exact_suite_is_bound_without_promoting_whole_clause(self):
        with patch.object(lab, "_contextual_identity", return_value=IDENTITY), \
             patch.object(benchmark, "run", return_value=suite()) as run:
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        run.assert_called_once_with(require_native=True)
        self.assertEqual(response["status"], "CONTEXTUAL_REFERENCE_COMPLETE")
        self.assertIs(response["all_arabic_complete"], False)

    def test_forged_source_native_or_tawatur_rejects_entire_suite(self):
        fields = ("native_sha256", "runtime_sha256", "source_registry_sha256", "scorer_sha256",
                  "original_reference_sha256", "independent_reference_sha256", "baseline_source_sha256",
                  "all_cases_native_checked", "tawatur_evaluated", "whole_arabic_complete",
                  "world_truth_established", "motive_measured")
        for key in fields:
            bad = suite()
            bad[key] = not bad[key] if type(bad[key]) is bool else "0" * 64
            with self.subTest(key=key), patch.object(lab, "_contextual_identity", return_value=IDENTITY), \
                 patch.object(benchmark, "run", return_value=bad):
                response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
            self.assertEqual(response["status"], "EXECUTION_FAILED")
            self.assertNotIn("contextual_reference", response)

    def test_identity_change_and_size_limit_return_valid_failure_receipts(self):
        with patch.object(lab, "_contextual_identity", side_effect=[IDENTITY, IDENTITY | {"code_sha": "0" * 40}]), \
             patch.object(benchmark, "run", return_value=suite()):
            changed = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        self.assertEqual(changed["status"], "EXECUTION_FAILED")
        big = deepcopy(suite())
        big["cases"] = ["x" * lab.MAX_RESULT_BYTES]
        with patch.object(lab, "_contextual_identity", return_value=IDENTITY), \
             patch.object(benchmark, "run", return_value=big):
            oversized = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        self.assertEqual(oversized["status"], "RESOURCE_EXHAUSTED")
        self.assertNotIn("contextual_reference", oversized)


if __name__ == "__main__":
    unittest.main()
