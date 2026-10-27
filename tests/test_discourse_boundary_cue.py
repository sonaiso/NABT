"""Independent boundary and authority controls; no benchmark gold is imported."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from tools.linguistic_truth import discourse_boundary as boundary
from tools.linguistic_truth import runtime
from tests._transport_native import native_test


native_available = native_test("discourseBoundaryCue", "linguisticTruth", "qualifiedCueLicensing")


class DiscourseBoundaryCue(unittest.TestCase):
    @native_available
    def test_bounded_marked_and_unmarked_records_are_separate(self):
        cases = [
            ("لَمْ يَرْجِعْ عَمْرٌو؛ وَأَقْصِدُ بِالْعَيْنِ الْعَيْنَ الْبَاصِرَةَ.", "EXACT_MARKED_OPERATORS"),
            ("لم يرجع عمرو؛ وأقصد بالعين العين الباصرة.", "EXACT_UNMARKED_OPERATORS"),
            ("لَمْ يرجع عمرو؛ وأقصد بالعين العين الباصرة", "MIXED_OPERATOR_MARKING"),
        ]
        for text, profile in cases:
            result = boundary.acquire_discourse_boundary(text, context="مقام اختبار مستقل")
            self.assertEqual(result["status"], "CHECKED_DISCOURSE_BOUNDARY", result)
            self.assertEqual(result["operator_marking_profile"], profile)
            self.assertTrue(result["native_checked"])
            self.assertEqual(len(result["claims"]), 1)
            self.assertFalse(result["strict_language_accepted"])
            self.assertFalse(result["intended_sense_established"])

    @native_available
    def test_exact_raw_bytes_context_and_disjoint_intervals(self):
        text = "لم يخرج خالد؛ وأقصد بالأسد الحيوان المفترس."
        result = boundary.acquire_discourse_boundary(text.encode(), source_id="شاهد مستقل", context="مقام أ")
        envelope, raw = result["envelope"], text.encode()
        self.assertEqual(result["source"]["text"], text)
        self.assertEqual(result["native_receipt"]["context"], "مقام أ")
        self.assertEqual(raw[envelope["denied_start_byte"]:envelope["denied_end_byte"]].decode(), "يخرج خالد")
        self.assertEqual(raw[envelope["cue_start_byte"]:envelope["cue_end_byte"]].decode(), envelope["cue_text"])
        self.assertLess(envelope["denied_end_byte"], envelope["cue_start_byte"])
        self.assertEqual(envelope["negation_prefix"] + envelope["denied_body"] + envelope["boundary"]
                         + envelope["conjunction"] + envelope["cue_text"] + ".", text)

    @native_available
    def test_later_positive_diagnostic_never_asserts_denied_event(self):
        result = boundary.acquire_discourse_boundary("لم أشاهد البحر؛ وأقصد بالأسد الحيوان المفترس.")
        child = result["later_cue_diagnostic"]
        self.assertEqual(child["source_text"], "أقصد بالأسد الحيوان المفترس")
        self.assertFalse(child["inherited_denial"])
        self.assertTrue(any("asad_animal" in row["sense_ids"] for row in result["selected_senses_scoped"]))
        self.assertTrue(all(not row["projects_to_denied_clause"] for row in result["selected_senses_scoped"]))
        self.assertFalse(result["world_truth_established"])
        self.assertEqual({c["kind"] for c in result["claims"]}, {"EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE"})

    @native_available
    def test_new_context_known_animal_phrase_does_not_gain_an_alias(self):
        result = boundary.acquire_discourse_boundary("لم يسافر سالم؛ وأقصد بالأسد الحيوان المعروف.")
        self.assertEqual(result["status"], "CHECKED_DISCOURSE_BOUNDARY")
        self.assertTrue(all(not row["sense_ids"] for row in result["selected_senses_scoped"]))
        self.assertFalse(result["intended_sense_established"])
        child = result["later_cue_diagnostic"]["result"]
        self.assertFalse(child["reported_child_flags"]["intended_sense_acquired"])

    @native_available
    def test_explicit_unestablished_profile_is_not_replaced_by_default(self):
        with patch.object(runtime, "acquire", wraps=runtime.acquire) as child_reader:
            result = boundary.acquire_discourse_boundary(
                "لم أشاهد البحر؛ وأقصد بالأسد الحيوان المفترس.", profile_id=None)
        self.assertEqual(result["status"], "CHECKED_DISCOURSE_BOUNDARY")
        self.assertIsNone(result["profile_id"])
        self.assertIsNone(result["later_cue_diagnostic"]["profile_id"])
        self.assertIsNone(child_reader.call_args.kwargs["profile_id"])
        child = result["later_cue_diagnostic"]["result"]
        self.assertIsNone(child["context"]["profile_id"])
        self.assertEqual(child["context"]["authority"], "UNESTABLISHED_CONVENTION")
        self.assertFalse(result["strict_language_accepted"])
        self.assertFalse(result["intended_sense_established"])

    @native_available
    def test_compact_diagnostic_retains_every_choice_profile_and_obligation(self):
        for cue in ("أقصد بالعين عين الماء", "أقصد بالقرء الطهر أو الحيض"):
            captured = []
            original = runtime.acquire
            def capture(*args, **kwargs):
                child = original(*args, **kwargs)
                captured.append(deepcopy(child))
                return child
            with self.subTest(cue=cue), patch.object(runtime, "acquire", side_effect=capture):
                result = boundary.acquire_discourse_boundary("لم أسمع القول؛ و" + cue + ".",
                    context="مقام الاختبار محفوظ", profile_id=None)
            raw = captured[0]
            child = result["later_cue_diagnostic"]["result"]
            self.assertEqual(child["schema"], "nabt.cue-diagnostic-summary.v1")
            self.assertEqual(child["raw_child_sha256"], sha256(boundary._wire(raw)).hexdigest())
            self.assertEqual(child["raw_child_bytes"], len(boundary._wire(raw)))
            self.assertEqual(child["source"], raw["source"])
            self.assertEqual(child["context"], raw["context"])
            self.assertEqual(child["pending_profiles"], raw["pending_profiles"])
            self.assertEqual(child["acquired_premises"], raw["acquired_premises"])
            self.assertEqual(child["unclassified_spans"], raw["unclassified_spans"])
            self.assertFalse(child["full_child_receipt_included"])
            self.assertFalse(child["summary_kernel_proved"])
            self.assertFalse(child["native_checked"])
            self.assertEqual(child["claims"], [])
            self.assertNotIn("proof", child)

            def assert_all_choices(actual, expected):
                self.assertEqual(len(actual), len(expected))
                for row, original_row in zip(actual, expected):
                    for key in ("occurrence_id", "span", "clause_span", "available_senses",
                                "selected_sense_ids", "excluded_sense_ids", "cue_readings",
                                "reason", "classification_status"):
                        self.assertEqual(row.get(key), original_row.get(key), key)
                    for key in ("sense_id", "designation_id", "support_status", "reason"):
                        self.assertEqual([c.get(key) for c in row["candidates"]],
                                         [c.get(key) for c in original_row["candidates"]], key)
                    self.assertEqual([p["profile_id"] for p in row["profile_readings"]],
                        [p["profile_id"] for p in original_row.get("profile_readings", [])])
                    for profile, original_profile in zip(row["profile_readings"],
                                                        original_row.get("profile_readings", [])):
                        assert_all_choices([profile["conditional_result"]],
                                           [original_profile["conditional_result"]])
                    self.assertNotIn("native_request", row)
                    self.assertNotIn("native_result", row)
            assert_all_choices(child["occurrences"], raw["occurrences"])
            replay = result["later_cue_diagnostic"]["replay"]
            self.assertEqual(replay["surface"], "tools.linguistic_truth.runtime.acquire")
            reproduced = runtime.acquire(**replay["input"])
            self.assertEqual(child["raw_child_sha256"], sha256(boundary._wire(reproduced)).hexdigest())

    @native_available
    def test_changing_denied_clause_does_not_change_cue_slice(self):
        cues = []
        for denied in ("أسمع القول", "يشاهد صالح الحيوان", "أتكلم عن العين"):
            result = boundary.acquire_discourse_boundary("لم " + denied + "؛ وأقصد بالعين عين الماء.")
            cues.append(result["envelope"]["cue_text"])
            self.assertFalse(result["envelope"]["projects_denied_to_positive"])
        self.assertEqual(cues, ["أقصد بالعين عين الماء"] * 3)

    @native_available
    def test_missing_or_changed_operators_are_outside_bounded_domain(self):
        for text in ("لم يخرج زيد وأقصد بالأسد الحيوان المفترس.",
                     "لم يخرج زيد; وأقصد بالأسد الحيوان المفترس.",
                     "لم يخرج زيد؛  وأقصد بالأسد الحيوان المفترس.",
                     "لم يخرج زيد؛ ولا أقصد بالأسد الحيوان المفترس.",
                     "لم يخرج زيد؛ ويقصد بالأسد الحيوان المفترس.",
                     "لم يخرج زيد؛ وَأقصد بالأسد الحيوان المفترس.",
                     "لم يخرج زيد؛ وأَقْصِدُ بالأسد الحيوان المفترس."):
            result = boundary.acquire_discourse_boundary(text)
            self.assertEqual(result["status"], "OUTSIDE_EXECUTED_DISCOURSE", text)
            self.assertEqual(result["claims"], [])
            self.assertIsNone(result["later_cue_diagnostic"])

    @native_available
    def test_quoted_conditional_and_nested_material_do_not_project(self):
        for text in ("قال سالم: «لم يخرج زيد؛ وأقصد بالأسد الحيوان المفترس».",
                     "إن قلت لم يخرج زيد؛ وأقصد بالأسد الحيوان المفترس.",
                     "لم يخرج زيد؛ وأقصد بالأسد «الحيوان المفترس».",
                     "لم يخرج زيد؛ وأقصد بالأسد الحيوان المفترس؛ ثم رجعت.",
                     "لم يخرج زيد؛ وأقصد بالأسد الحيوان المفترس\n"):
            result = boundary.acquire_discourse_boundary(text)
            self.assertEqual(result["status"], "OUTSIDE_EXECUTED_DISCOURSE", text)
            self.assertEqual(result["claims"], [])

    @native_available
    def test_native_no_caller_scope_or_verifier_flags(self):
        for extra in ("checker", "envelope", "native_checked", "claims"):
            request = {"source": {"id": "case", "revision": "revision", "text": "لم أسمع؛ وأقصد بالأسد الحيوان المفترس"},
                       "context": "مقام", extra: True}
            result = subprocess.run([str(boundary._EXECUTABLE)], input=boundary._wire(request) + b"\n",
                                    capture_output=True, check=True)
            self.assertEqual(json.loads(result.stdout)["status"], "INVALID_INPUT")

    def test_public_api_cannot_select_root_checker_or_receipt(self):
        for key in ("root", "checker", "receipt", "envelope", "native_checked"):
            with self.assertRaises(TypeError):
                boundary.acquire_discourse_boundary("نص", **{key: True})

    def test_malformed_and_oversized_inputs_never_run_native(self):
        with patch.object(boundary, "_native") as native:
            for text in (False, 12, None, b"\xff", "\ud800", ""):
                self.assertEqual(boundary.acquire_discourse_boundary(text)["status"], "INVALID_INPUT")
            self.assertEqual(boundary.acquire_discourse_boundary("x" * 16385)["status"], "RESOURCE_EXHAUSTED")
            self.assertEqual(boundary.acquire_discourse_boundary("نص", context="x" * 4097)["status"], "RESOURCE_EXHAUSTED")
            native.assert_not_called()

    def test_altered_source_review_has_no_claim(self):
        original = Path.read_bytes
        def changed(path):
            return b"{}" if path == boundary._REVIEW else original(path)
        with patch.object(Path, "read_bytes", changed):
            result = boundary.acquire_discourse_boundary("لم أسمع؛ وأقصد بالأسد الحيوان المفترس")
            self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
            self.assertFalse(result["native_checked"])
            self.assertEqual(result["claims"], [])

    def test_missing_native_has_no_proof_or_child_diagnostic(self):
        original = Path.read_bytes
        def missing(path):
            if path == boundary._EXECUTABLE:
                raise FileNotFoundError(path)
            return original(path)
        with patch.object(Path, "read_bytes", missing), patch.object(runtime, "acquire") as child:
            result = boundary.acquire_discourse_boundary("لم أسمع؛ وأقصد بالأسد الحيوان المفترس")
            self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(result["claims"], [])
            child.assert_not_called()

    @native_available
    def test_mismatched_native_context_span_or_authority_is_rejected(self):
        original = subprocess.run
        for mutation in ("context", "span", "source", "count", "truth", "bool"):
            def forged(*args, **kwargs):
                completed = original(*args, **kwargs)
                value = json.loads(completed.stdout)
                if mutation == "context": value["context"] = "other"
                elif mutation == "span": value["envelope"]["cue_start_byte"] -= 1
                elif mutation == "source": value["source"]["text"] += " "
                elif mutation == "count": value["licensed_envelope_count"] = 2
                elif mutation == "truth": value["external_truth_established"] = True
                else: value["envelope"]["projects_denied_to_positive"] = 0
                return subprocess.CompletedProcess(completed.args, 0, boundary._wire(value) + b"\n", completed.stderr)
            with patch.object(subprocess, "run", side_effect=forged):
                result = boundary.acquire_discourse_boundary("لم أسمع؛ وأقصد بالأسد الحيوان المفترس")
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE", mutation)
                self.assertEqual(result["claims"], [])

    @native_available
    def test_resource_exhaustion_does_not_reject_arabic(self):
        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("native", 30)):
            result = boundary.acquire_discourse_boundary("لم أسمع؛ وأقصد بالأسد الحيوان المفترس")
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertEqual(result["claims"], [])

    @native_available
    def test_child_failure_preserves_only_independent_boundary_claim(self):
        with patch.object(runtime, "acquire", side_effect=ValueError("child unavailable")):
            result = boundary.acquire_discourse_boundary("لم أسمع؛ وأقصد بالأسد الحيوان المفترس")
            self.assertEqual(result["status"], "CHECKED_DISCOURSE_BOUNDARY")
            self.assertEqual(len(result["claims"]), 1)
            self.assertEqual(result["later_cue_diagnostic"]["result"]["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(result["selected_senses_scoped"], [])

    @native_available
    def test_mismatched_child_source_cannot_leak_scoped_selection(self):
        original = runtime.acquire
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            result["source"]["raw_text"] = "different raw source"
            return result
        with patch.object(runtime, "acquire", side_effect=changed):
            result = boundary.acquire_discourse_boundary("لم أسمع؛ وأقصد بالأسد الحيوان المفترس")
            self.assertEqual(result["status"], "CHECKED_DISCOURSE_BOUNDARY")
            self.assertEqual(result["selected_senses_scoped"], [])
            self.assertEqual(result["later_cue_diagnostic"]["result"]["status"], "VERIFICATION_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
