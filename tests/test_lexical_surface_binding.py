"""Independent source examples and mutations of the exact witnessed-form gate."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from nabt import foundation
from nabt.errors import NabtError
from tools.linguistic_truth import surface

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "formal/.lake/build/bin/lexicalSurface"
SOURCE = surface.source_loader.DEFAULT_SOURCE


class SurfaceAdmissionTests(unittest.TestCase):
    def test_foundation_denial_precedes_source_and_native(self):
        with patch.object(foundation, "require_foundation", side_effect=NabtError("DENIED", "test")), \
                patch.object(surface, "_installed") as installed:
            with self.assertRaises(NabtError):
                surface.certify_surface("عَيْنَ")
            installed.assert_not_called()

    def test_caller_cannot_supply_witness_checker_or_verification_flags(self):
        for name in ("witnesses", "checker", "native_checked", "proof", "ledger", "expression"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                surface.certify_surface("عَيْنَ", **{name: True})

    def test_noninteger_and_out_of_range_spans_rejected(self):
        for start, end in ((True, 12), (0, 12.0), (0, False), (-1, 12), (0, 100), (5, 5)):
            with self.subTest(start=start, end=end):
                report = surface.certify_surface("عَيْنَ", start_byte=start, end_byte=end)
                self.assertEqual(report["status"], "INVALID_INPUT")
                self.assertFalse(report["native_checked"])
                self.assertEqual(report["claims"], [])

    def test_corrupted_installed_source_cannot_supply_an_attestation(self):
        with patch.object(surface, "_installed", side_effect=ValueError("changed")), \
                patch.object(surface, "_native") as native:
            result = surface.certify_surface("عَيْنَ")
            self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
            self.assertEqual(result["claims"], [])
            native.assert_not_called()

    def test_oversize_source_is_resource_exhaustion_before_acquisition(self):
        with patch.object(surface, "_installed") as installed:
            result = surface.certify_surface("ع" * 40000)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["native_checked"])
            self.assertEqual(result["claims"], [])
            installed.assert_not_called()


@unittest.skipUnless(NATIVE.is_file() and SOURCE.is_file(), "built lexicalSurface and pinned QAC source required")
class SurfaceNativeTests(unittest.TestCase):
    def test_all_selected_nouns_and_verbs_replay_actual_source_rows(self):
        examples = {"عَيْنَ": {"(5:45:7:3)", "(34:12:9:1)", "(102:7:3:1)"},
            "كَتَبَ": {"(2:187:28:1)"}, "ضَرَبَ": {"(14:24:4:1)"},
            "خَرَجَ": {"(19:11:1:2)"}, "دَخَلَ": {"(3:37:11:1)"},
            "وَلَدَ": {"(37:152:1:1)"}, "عَلِمَ": {"(2:60:15:1)"},
            "سَمِعَ": {"(2:181:4:1)"}, "قَتَلَ": {"(2:251:4:2)"}}
        for text, ids in examples.items():
            with self.subTest(text=text):
                result = surface.certify_surface(text)
                self.assertEqual(result["status"], "CHECKED_EXACT_SURFACE")
                self.assertEqual({row["id"] for row in result["matches"]}, ids)
                self.assertTrue(result["native_checked"])
                self.assertTrue(result["claims"])
                self.assertFalse(result["strict_language_accepted"])
                self.assertFalse(result["intended_sense_established"])

    def test_vowel_change_missing_mark_and_unlicensed_inflection_do_not_match(self):
        for text in ("عِيْنَ", "عَيْنُ", "عَيْنِ", "عين", "عَيْن", "كَتِبَ", "كَتَبْ", "خَرِجَ", "دَخَلُ"):
            with self.subTest(text=text):
                result = surface.certify_surface(text)
                self.assertTrue(result["native_checked"])
                self.assertEqual(result["status"], "DEFER")
                self.assertEqual(result["claims"], [])
                self.assertEqual(result["matches"], [])

    def test_equal_cells_do_not_erase_spaces_or_license_a_different_span(self):
        plain = surface.certify_surface("عَيْنَ")
        for text in (" عَيْنَ", "عَيْنَ ", "عَيْ نَ"):
            result = surface.certify_surface(text)
            self.assertEqual(result["foundation_source"]["cells"], plain["foundation_source"]["cells"])
            self.assertTrue(result["native_checked"])
            self.assertEqual(result["claims"], [])

    def test_exact_local_occurrence_preserves_negation_quotation_and_context(self):
        reports = []
        for text, context in (("قَالَ: عَيْنَ.", "quoted"), ("لَمْ يَقُلْ عَيْنَ.", "negated")):
            start = text.encode().index("عَيْنَ".encode())
            result = surface.certify_surface(text, start_byte=start, end_byte=start+12,
                context=context, referent="speaker-A", time="t1")
            self.assertEqual(result["status"], "CHECKED_EXACT_SURFACE")
            self.assertEqual(result["source"]["text"], text)
            self.assertEqual(result["claims"][0]["frame"]["occurrence"]["context"], context)
            self.assertFalse(result["intended_sense_established"])
            self.assertFalse(result["strict_language_accepted"])
            reports.append(result)
        self.assertNotEqual(reports[0]["claims"][0]["request_sha256"], reports[1]["claims"][0]["request_sha256"])

    def test_cutting_last_mark_cannot_create_an_exact_occurrence(self):
        result = surface.certify_surface("عَيْنَ", end_byte=10)
        self.assertTrue(result["native_checked"])
        self.assertEqual(result["claims"], [])
        self.assertTrue(all(row["occurrence_exact"] is False for row in result["native_receipts"]))

    def test_native_unavailable_and_forged_positive_postcondition_fail_closed(self):
        with patch.object(surface, "_native", side_effect=FileNotFoundError):
            result = surface.certify_surface("عَيْنَ")
            self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(result["claims"], [])
        original = surface._native
        def mutate(requests):
            rows, digest = original(requests)
            rows[0]["matched_ids"] = ["invented"]
            return rows, digest
        with patch.object(surface, "_native", side_effect=mutate):
            result = surface.certify_surface("عَيْنَ")
            self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
            self.assertFalse(result["native_checked"])
            self.assertEqual(result["claims"], [])

    def test_changed_source_bytes_are_detected_after_a_successful_call(self):
        self.assertTrue(surface.certify_surface("عَيْنَ")["exact_surface_checked"])
        with patch.object(surface.source_loader, "_decode_source", side_effect=ValueError("changed")):
            result = surface.certify_surface("عَيْنَ")
            self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
            self.assertEqual(result["claims"], [])

    def test_resource_exhaustion_is_not_a_linguistic_rejection(self):
        with patch.object(surface, "_native", side_effect=OverflowError("bounded")):
            result = surface.certify_surface("عَيْنَ")
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["native_checked"])
            self.assertEqual(result["claims"], [])

    def test_native_protocol_rejects_duplicate_keys_and_recovers(self):
        raw = b'{"source":{},"source":{}}\n{}\n'
        completed = subprocess.run([str(NATIVE)], input=raw, capture_output=True, check=True)
        rows = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["status"] == "INVALID_INPUT" for row in rows))


if __name__ == "__main__":
    unittest.main()
