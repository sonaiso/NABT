"""Independent authority/binding attacks, not evidence of Arabic completeness.

The temporary executable and mocked subprocess in transport tests are explicit
fixtures. They exercise rejection of corrupted wire replies; they never count
as native execution or as a linguistic oracle. Native linguistic controls live
in a separate class and use the independently frozen reference material.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from nabt import foundation
from nabt.errors import NabtError
from tests._transport_native import require_native
from tools.linguistic_truth import six_noun as adapter
from tools import benchmark_six_noun_acquisition as benchmark


TEXT = "جَاءَ أَبُو زَيْدٍ"
CONTEXT = "نص تعليمي؛ لا تعيين لشخص أو إثبات لواقعة"


def request(text=TEXT, *, source_id="independent-adversarial", context=CONTEXT):
    return {"source": {"id": source_id, "revision": sha256(text.encode()).hexdigest(),
                       "text": text}, "context": context}


class SixNounIndependentInputAttacks(unittest.TestCase):
    def test_direct_api_foundation_denial_precedes_all_other_work(self):
        error = NabtError("DENIED_FOR_TEST", "foundation unavailable", status="DEFER")
        with patch.object(foundation, "require_foundation", side_effect=error), \
                patch.object(adapter, "_review") as review, patch.object(adapter, "_native") as native:
            with self.assertRaises(NabtError):
                adapter.acquire_six_noun(TEXT)
            review.assert_not_called()
            native.assert_not_called()

    def test_caller_cannot_supply_acquired_features_or_certificate(self):
        for key in ("reading", "grammar_certified", "proof", "checker", "receipt", "source_review",
                    "prerequisites", "companion_meaning", "rule_id", "orthographic_bridge"):
            with self.subTest(key=key), patch.object(adapter, "_native") as native:
                with self.assertRaises(TypeError):
                    adapter.acquire_six_noun(TEXT, **{key: True})
                native.assert_not_called()

    def test_invalid_raw_types_encoding_and_marks_do_not_load_sources(self):
        inputs = (True, 116, {}, b"\xff", "\ud800", "", "َجَاءَ أَبُو زَيْدٍ",
                  "جَاءَ أَبَُو زَيْدٍ", "جَاءَ أَبُُو زَيْدٍ", "جَاءَ أَبُو زَيْدٍّّ")
        with patch.object(adapter, "_review") as review, patch.object(adapter, "_native") as native:
            for value in inputs:
                with self.subTest(value=repr(value)):
                    result = adapter.acquire_six_noun(value)
                    self.assertEqual(result["status"], "INVALID_INPUT")
                    self.assertEqual(result["claims"], [])
                    self.assertFalse(result["native_checked"])
            review.assert_not_called()
            native.assert_not_called()

    def test_request_budget_exhaustion_is_not_language_rejection(self):
        with patch.object(adapter, "_review") as review, patch.object(adapter, "_native") as native:
            result = adapter.acquire_six_noun("س" * adapter._MAX_INPUT_BYTES)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["linguistic_rejection"])
            self.assertEqual(result["claims"], [])
            review.assert_not_called()
            native.assert_not_called()

    def test_source_failure_does_not_become_linguistic_invalidity(self):
        with patch.object(adapter, "_review", side_effect=ValueError("SOURCE_CHANGED")), \
                patch.object(adapter, "_native") as native:
            result = adapter.acquire_six_noun(TEXT)
            self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
            self.assertEqual(result["claims"], [])
            self.assertFalse(result["linguistic_rejection"])
            native.assert_not_called()

    def test_timeout_is_not_absence_of_licensed_readings(self):
        with patch.object(adapter, "_native", side_effect=subprocess.TimeoutExpired("fixture", 30)):
            result = adapter.acquire_six_noun(TEXT)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["linguistic_rejection"])
            self.assertEqual(result["claims"], [])

    def test_receipt_depth_exhaustion_has_no_proof_authority(self):
        with patch.object(adapter, "_native", side_effect=RecursionError("transport depth fixture")):
            result = adapter.acquire_six_noun(TEXT)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["native_checked"])
            self.assertFalse(result["linguistic_rejection"])
            self.assertEqual(result["claims"], [])


class SixNounIndependentTransportAttacks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nabt-six-noun-wire-test-")
        self.addCleanup(self.temp.cleanup)
        self.executable = Path(self.temp.name) / "fixture-not-an-executable"
        self.executable.write_bytes(b"explicit transport fixture; not Lean")
        self.req = request()

    def invoke_wire(self, raw, *, returncode=0):
        result = subprocess.CompletedProcess([str(self.executable)], returncode, raw, b"")
        with patch.object(adapter, "_EXECUTABLE", self.executable), \
                patch.object(adapter.subprocess, "run", return_value=result):
            return adapter._native(self.req)

    def test_exact_postcondition_mutations_are_rejected(self):
        # Production replay is used only to manufacture an otherwise consistent
        # wire fixture, not to generate any linguistic expected answer.
        baseline = adapter._expected(self.req)
        mutations = []
        for key, value in (("id", "another-source"), ("revision", "0" * 64),
                           ("text", TEXT + " ")):
            changed = deepcopy(baseline)
            changed["source"][key] = value
            mutations.append(("source." + key, changed))
        for key, value in (("context", "مقام مختلف"), ("grammar_certified", 1),
                           ("foundation_complete", 0), ("strict_language_accepted", True),
                           ("whole_arabic_complete", True), ("external_truth_established", True),
                           ("intended_sense_established", True), ("caller_proof_authority", True)):
            changed = deepcopy(baseline)
            changed[key] = value
            mutations.append((key, changed))
        for key, value in (("start_byte", True), ("end_byte", 0.0),
                           ("word", "أَخُو"), ("grammatical_case", "jarr")):
            changed = deepcopy(baseline)
            self.assertIsNotNone(changed["reading"])
            changed["reading"][key] = value
            mutations.append(("reading." + key, changed))
        changed = deepcopy(baseline)
        changed["source_projection"]["cells"][0] = float(changed["source_projection"]["cells"][0])
        mutations.append(("source_projection.cells.integer_type", changed))
        changed = deepcopy(baseline)
        changed["orthographic_bridge"]["raw"] += " "
        mutations.append(("orthographic_bridge.raw", changed))
        for name, changed in mutations:
            with self.subTest(field=name), self.assertRaises(ValueError):
                self.invoke_wire(adapter._wire(changed) + b"\n")

    def test_duplicate_fields_and_nonfinite_json_are_rejected(self):
        payloads = (b'{"source":{"id":"first","id":"second"}}\n',
                    b'{"grammar_certified":false,"grammar_certified":true}\n',
                    b'{"reading":{"start_byte":NaN}}\n', b'{"number":Infinity}\n')
        for raw in payloads:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.invoke_wire(raw)

    def test_extra_reply_and_nonzero_exit_are_rejected(self):
        wire = adapter._wire(adapter._expected(self.req)) + b"\n"
        with self.assertRaises(ValueError):
            self.invoke_wire(wire + wire)
        with self.assertRaises(ValueError):
            self.invoke_wire(wire, returncode=1)

    def test_native_resource_receipt_is_not_negative_linguistic_result(self):
        with self.assertRaises(OverflowError):
            self.invoke_wire(b'{"status":"RESOURCE_LIMIT"}\n')

    def test_executable_change_during_execution_is_rejected(self):
        raw = adapter._wire(adapter._expected(self.req)) + b"\n"
        def changed_binary(*args, **kwargs):
            self.executable.write_bytes(b"different fixture")
            return subprocess.CompletedProcess(args[0], 0, raw, b"")
        with patch.object(adapter, "_EXECUTABLE", self.executable), \
                patch.object(adapter.subprocess, "run", side_effect=changed_binary), \
                self.assertRaises(ValueError):
            adapter._native(self.req)


class SixNounIndependentScoreAttacks(unittest.TestCase):
    """Synthetic score fixtures test the comparator, not language or native Lean."""

    @staticmethod
    def fixture(case_id):
        case = next(c for c in benchmark._load_reference()["cases"] if c["id"] == case_id)
        inp = case["input"]
        receipt = {"source": request(inp["text"], source_id=inp["source_id"])["source"],
            "context": inp["context"], "status": "DEFER", "native_checked": True,
            "grammar_certified": False, "claims": [], "linguistic_rejection": False,
            "strict_language_accepted": False, "intended_sense_established": False,
            "speaker_reference_established": False, "world_truth_established": False,
            "external_truth_established": False, "tawatur_established": False,
            "whole_arabic_complete": False,
            "reading": {"grammatical_case": case["expected"]["grammatical_case"],
                        "lexeme": case["expected"]["lexeme"]},
            "residuals": ["COMMON_LETTER_CASE_MISMATCH", "DHU_COMPANIONSHIP_NOT_ACQUIRED"]}
        return case, receipt

    def test_negative_answer_for_another_source_is_not_success(self):
        case, receipt = self.fixture("N01")
        self.assertTrue(benchmark._score(case, receipt)["full_form_analysis"])
        receipt["source"]["id"] = "different-occurrence"
        self.assertFalse(benchmark._score(case, receipt)["full_form_analysis"])

    def test_specific_missing_condition_in_another_context_is_not_success(self):
        case, receipt = self.fixture("D01")
        self.assertTrue(benchmark._score(case, receipt)["alternative_specificity"])
        receipt["context"] += " مقام آخر"
        self.assertFalse(benchmark._score(case, receipt)["alternative_specificity"])

    def test_unlicensed_authority_is_never_safe_abstention(self):
        for flag in ("grammar_certified", "strict_language_accepted", "intended_sense_established",
                     "speaker_reference_established", "world_truth_established", "external_truth_established",
                     "tawatur_established", "whole_arabic_complete"):
            case, receipt = self.fixture("N01")
            receipt[flag] = True
            with self.subTest(flag=flag):
                self.assertFalse(benchmark._score(case, receipt)["full_form_analysis"])


class SixNounIndependentNativeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_native("sixNounAcquisition")

    def test_uncertain_and_wrapped_cases_cannot_acquire_positive_authority(self):
        for text in ("جَاءَ ذُو مَالٍ", "جَاءَ أَبَا زَيْدٍ", "جَاءَ أَبِي زَيْدٍ",
                     "قَالَ عَمْرٌو: «جَاءَ أَبُو زَيْدٍ»", "لَمْ يَجِئْ أَبُو زَيْدٍ",
                     "إِنْ جَاءَ أَبُو زَيْدٍ قُمْتُ"):
            with self.subTest(text=text):
                result = adapter.acquire_six_noun(text, context=CONTEXT)
                self.assertTrue(result["native_checked"], result)
                self.assertNotEqual(result["status"], "CHECKED_SIX_NOUN")
                self.assertFalse(result["grammar_certified"])
                self.assertFalse(result["linguistic_rejection"])
                self.assertEqual(result["claims"], [])

    def test_same_grammar_new_context_never_supplies_reference_or_world_truth(self):
        reports = [adapter.acquire_six_noun(TEXT, context=context)
                   for context in ("تعليم النحو بلا أشخاص", "رواية غير مصادق عليها عن واقعة")]
        for result in reports:
            self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
            for flag in ("strict_language_accepted", "intended_sense_established",
                         "speaker_reference_established", "world_truth_established",
                         "external_truth_established", "tawatur_established", "whole_arabic_complete"):
                self.assertIs(result[flag], False)
        self.assertNotEqual(reports[0]["request_sha256"], reports[1]["request_sha256"])
        self.assertNotEqual(reports[0]["receipt_sha256"], reports[1]["receipt_sha256"])

    def test_original_partial_projection_is_not_silently_promoted(self):
        result = adapter.acquire_six_noun(TEXT, source_id="raw-projection-control", context=CONTEXT)
        self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
        self.assertEqual(foundation.inspect_source(TEXT)["status"], "PARTIAL")
        self.assertFalse(result["source_projection_complete"])
        self.assertFalse(result["foundation_complete"])
        receipt = result["native_receipt"]
        self.assertEqual(receipt["source_projection"]["status"], "INCOMPLETE")
        bridge = result["orthographic_bridge"]
        self.assertEqual(bridge["raw"], TEXT)
        self.assertNotEqual(bridge["canonical"], TEXT)
        self.assertTrue(bridge["canonical_projection_complete"])
        self.assertNotEqual(bridge["profile"], receipt["source_projection"]["alphabet_id"])
        raw = TEXT.encode("utf-8")
        reading = result["reading"]
        self.assertEqual(raw[reading["start_byte"]:reading["end_byte"]], "أَبُو".encode("utf-8"))
        self.assertEqual(result["claims"][0]["source"], result["source"])
        self.assertEqual(result["claims"][0]["context"], CONTEXT)

    def test_unobserved_semantic_prerequisite_is_distinct_from_observed_case_mismatch(self):
        unknown = adapter.acquire_six_noun("جَاءَ ذُو زَيْدٍ", context=CONTEXT)
        wrong_case = adapter.acquire_six_noun("جَاءَ أَبِي زَيْدٍ", context=CONTEXT)
        for result in (unknown, wrong_case):
            self.assertTrue(result["native_checked"], result)
            self.assertEqual(result["status"], "DEFER")
            self.assertFalse(result["grammar_certified"])
            self.assertEqual(result["claims"], [])
        unknown_states = {item["name"]: item["state"] for item in unknown["reading"]["prerequisites"]}
        wrong_states = {item["name"]: item["state"] for item in wrong_case["reading"]["prerequisites"]}
        self.assertEqual(unknown_states["dhu_companionship"], "unknown")
        self.assertEqual(unknown_states["required_case_matches_observed_ending"], "affirmed")
        self.assertEqual(wrong_states["required_case_matches_observed_ending"], "denied")


if __name__ == "__main__":
    unittest.main()
