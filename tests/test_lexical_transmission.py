"""Transmission classification preserves claims, sources and unresolved authority."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import lexical_testimony as testimony
from tools import lexical_transmission as transmission


native_available = unittest.skipUnless(
    (transmission.ROOT / "formal/.lake/build/bin/lexicalTransmission").is_file(),
    "lexicalTransmission native executable is built by the required Lean gate")


class LexicalTransmission(unittest.TestCase):
    @native_available
    def test_individual_report_is_identified_without_truth_grade(self):
        result = transmission.assess_transmission("بيت", context="مقام جديد")
        self.assertEqual(result["status"], "DOCUMENTARY_REPORTS")
        self.assertTrue(result["native_checked"])
        self.assertEqual(result["reports"][0]["documentary_status"], "IDENTIFIED_SINGLE_SOURCE_REPORT")
        self.assertTrue(result["source_replay"][0]["source_file_replayed"])
        for key in ("tawatur_established", "historical_authenticity_established",
                    "intended_sense_established", "world_truth_established", "strict_language_accepted"):
            self.assertIs(result[key], False)

    @native_available
    def test_multiple_senses_from_one_work_do_not_become_three_sources(self):
        result = transmission.assess_transmission("قلم")
        self.assertEqual(len(result["reports"]), 3)
        self.assertEqual(result["source_families"], ["lisan"])
        self.assertEqual(result["source_relationship_status"], "NOT_A_MULTISOURCE_ASSESSMENT")
        self.assertEqual(len({row["sense_id"] for row in result["reports"]}), 3)

    @native_available
    def test_two_books_are_not_independent_and_different_readings_are_not_collapsed(self):
        result = transmission.assess_transmission("فهم")
        self.assertEqual(result["source_families"], ["lisan", "maqayis"])
        self.assertEqual(result["source_relationship_status"], "INDEPENDENCE_UNASSESSED")
        self.assertFalse(result["cross_source_sense_alignment_established"])
        self.assertEqual(result["dependency_reviews"], [])
        self.assertEqual([r["sense_id"] for r in result["reports"]],
                         ["lisan:fahm-knowledge", "lisan:fahm-tribe", "maqayis:fahm-knowledge"])

    @native_available
    def test_unknown_index_is_measured_empty_not_attested_arabic(self):
        result = transmission.assess_transmission("شمس")
        self.assertEqual(result["status"], "UNMEASURED_ROOT")
        self.assertTrue(result["native_checked"])
        self.assertEqual(result["reports"], [])
        self.assertEqual(result["claims"], [])
        self.assertFalse(result["strict_language_accepted"])

    @native_available
    def test_context_is_bound_byte_for_byte_not_interpreted(self):
        contexts = ['قال: «فهم»', 'لم يقل: «فهم»', 'إن قال: «فهم»', '  فهم\n']
        for context in contexts:
            result = transmission.assess_transmission("فهم", context=context)
            self.assertEqual(result["native_request"]["context"], context)
            self.assertTrue(all(r["context"] == context for r in result["reports"]))
            self.assertFalse(result["intended_sense_established"])

    def test_invalid_inputs_never_invoke_native(self):
        with patch.object(testimony, "_native") as native:
            for entry, context in [(True, ""), ("", ""), ("بيت", True), ("بيت", "\ud800"),
                                   ("\ud800", "")]:
                self.assertEqual(transmission.assess_transmission(entry, context=context)["status"], "INVALID_INPUT")
            native.assert_not_called()

    def test_missing_catalogue_has_no_native_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(transmission, "ROOT", Path(directory)):
                result = transmission.assess_transmission("بيت")
            self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
            self.assertFalse(result["native_checked"])
            self.assertNotIn("claim", result)

    def test_corrupted_source_is_rejected_before_native(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / testimony.CATALOG
            path.parent.mkdir(parents=True)
            path.write_bytes((testimony.ROOT / testimony.CATALOG).read_bytes())
            path = root / testimony.SOURCES["maqayis"][2]
            path.parent.mkdir(parents=True)
            path.write_bytes(b"altered")
            with patch.object(testimony, "_native") as native, patch.object(transmission, "ROOT", root):
                self.assertEqual(transmission.assess_transmission("بيت")["status"], "SOURCE_UNAVAILABLE")
                native.assert_not_called()

    def test_public_reader_rejects_alternate_root_and_caller_grades(self):
        for key in ("root", "checker", "native_checked", "reports", "transmission_type"):
            with self.assertRaises(TypeError):
                transmission.assess_transmission("بيت", **{key: True})

    def test_request_limits_are_resources_not_invalid_arabic(self):
        with patch.object(testimony, "_native") as native:
            for entry, context in [("x" * 129, ""), ("بيت", "x" * 65537)]:
                result = transmission.assess_transmission(entry, context=context)
                self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
                self.assertEqual(result["claims"], [])
            native.assert_not_called()

    def test_missing_native_cannot_grant_a_documentary_claim(self):
        read_bytes = Path.read_bytes
        def absent(path):
            if path.name == "lexicalTransmission":
                raise FileNotFoundError(path)
            return read_bytes(path)
        with patch.object(Path, "read_bytes", absent):
            result = transmission.assess_transmission("بيت")
            self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(result["claims"], [])
            self.assertFalse(result["native_checked"])

    @native_available
    def test_mismatched_receipt_or_promoted_rank_never_furnishes_claim(self):
        original = testimony._native
        for mutation in ("omit", "context", "source", "tawatur", "boolean", "dependency", "sense"):
            def forged(exe, request=None):
                value = original(exe, request)
                if request is not None:
                    if mutation == "omit": value["reports"] = value["reports"][:1]
                    elif mutation == "context": value["context"] = "other"
                    elif mutation == "source": value["reports"][0]["citation"]["start_byte"] += 1
                    elif mutation == "tawatur": value["tawatur_established"] = True
                    elif mutation == "boolean": value["strict_language_accepted"] = 0
                    elif mutation == "dependency": value["source_relationship_status"] = "INDEPENDENT"
                    else: value["reports"][1]["sense_id"] = value["reports"][0]["sense_id"]
                return value
            with patch.object(testimony, "_native", side_effect=forged):
                result = transmission.assess_transmission("فهم")
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE", mutation)
                self.assertFalse(result["native_checked"])
                self.assertNotIn("claim", result)

    @native_available
    def test_export_cannot_install_extra_dependency_or_report(self):
        original = testimony._native
        def forged(exe, request=None):
            result = original(exe, request)
            if request is None:
                result["dependency_reviews"] = ["independent because another book exists"]
            return result
        with patch.object(testimony, "_native", side_effect=forged):
            self.assertEqual(transmission.assess_transmission("فهم")["status"], "VERIFICATION_UNAVAILABLE")

    @native_available
    def test_timeout_is_resource_failure_not_linguistic_rejection(self):
        with patch.object(testimony, "_native", side_effect=subprocess.TimeoutExpired("native", 20)):
            result = transmission.assess_transmission("بيت")
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertNotIn("claim", result)

    @native_available
    def test_native_protocol_rejects_caller_grade_and_report(self):
        exe = transmission.ROOT / "formal/.lake/build/bin/lexicalTransmission"
        for extra in ("tawatur_established", "reports", "dependency_reviews", "native_checked"):
            result = testimony._native(exe, {"entry": "بيت", "context": "", extra: True})
            self.assertEqual(result["status"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
