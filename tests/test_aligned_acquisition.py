"""Boundary, mutation and native transport tests, authored without frozen gold."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import aligned_acquisition as aa
from nabt.alphabet import parse_word
from nabt.errors import NabtError
from nabt.word_reader import read_words


class AcquisitionBoundaryTests(unittest.TestCase):
    def test_invalid_inputs_and_resource_are_separate(self):
        for value in (None, True, 116, [], {}, b"\xff", "\ud800"):
            with self.subTest(value=repr(value)):
                self.assertEqual(aa.acquire(value)["status"], "INVALID_INPUT")
        for value in ("a" * 4097, b"a" * 8193, "😀" * 2049):
            self.assertEqual(aa.acquire(value)["status"], "RESOURCE_EXHAUSTED")
        for key in ("source_id", "revision", "scope"):
            for value in (True, 1, "", "x\x00", "x\x85", "\udfff", "x" * 513):
                self.assertEqual(aa.acquire("بَ", **{key: value})["status"], "INVALID_INPUT")
        for ending in (True, 1, None, "WASL"):
            self.assertEqual(aa.acquire("بَ", ending=ending)["status"], "INVALID_INPUT")

    def test_empty_and_separators_are_not_words(self):
        for text in ("", " \t\r\n،؟«»"):
            report = aa.propose_acquisition(text)
            self.assertEqual(report["status"], "DEFER")
            self.assertEqual(report["reason"], "NO_WORD")
            self.assertEqual(report["words"], [])

    def test_source_restoration_and_two_coordinate_systems(self):
        # Supplementary Unicode, unsupported marks, mixed mark order, and CRLF
        # must survive even when no whole-word acquisition is possible.
        for text in ("بَّ بَّ", "😀بَ\r\n«بَ»", "\u0301بَ", "َهذا", "بـَ\tبَ", "بَ\u00a0بَ"):
            with self.subTest(text=text):
                report = aa.propose_acquisition(text)
                self.assertEqual("".join(p["raw"] for p in report["pieces"]), text)
                cp = bp = 0
                for piece in report["pieces"]:
                    self.assertEqual((piece["start"], piece["byte_start"]), (cp, bp))
                    self.assertEqual(text[piece["start"]:piece["end"]], piece["raw"])
                    self.assertEqual(text.encode()[piece["byte_start"]:piece["byte_end"]], piece["raw"].encode())
                    self.assertTrue(all(type(c) is int and 0 <= c < 116 for c in piece["cells"]))
                    cp, bp = piece["end"], piece["byte_end"]
                self.assertEqual((cp, bp), (len(text), len(text.encode())))

    def test_exact_mark_order_is_retained_even_when_cells_coincide(self):
        left, right = (aa.propose_acquisition(s) for s in ("بَّ", "بَّ"))
        self.assertEqual(left["words"][0]["cells"], [7, 4])
        self.assertEqual(left["words"], right["words"])
        self.assertNotEqual(left["pieces"][0]["raw"], right["pieces"][0]["raw"])

    def test_pause_applies_only_to_final_word(self):
        wasl = aa.propose_acquisition("بَ بُ", ending="wasl")
        waqf = aa.propose_acquisition("بَ بُ؟ ", ending="waqf")
        self.assertEqual([w["cells"] for w in wasl["words"]], [[4], [5]])
        self.assertEqual([w["cells"] for w in waqf["words"]], [[4], [7]])

    def test_long_vowel_needs_immediate_licensed_short_cell(self):
        self.assertEqual(aa.propose_acquisition("بَا")["words"][0]["cells"], [4, 3])
        for text in ("بُا", "بَ ا", "بَاا", "بَٰا", "بَٰى", "ب?ا"):
            self.assertEqual(aa.propose_acquisition(text)["status"], "DEFER")

    def test_malformed_marks_outrank_lexical_debt(self):
        for text in ("هََذا", "بّْ", "بَُ", "بًٰ", "بَّّ", "بَٰٰ", "َبَ"):
            self.assertEqual(aa.propose_acquisition(text)["status"], "INVALID_INPUT")
        self.assertEqual(aa.propose_acquisition("بٰ")["status"], "DEFER")

    def test_strict_original_reader_has_not_become_normalizing(self):
        with self.assertRaises(NabtError):
            parse_word("بَا")
        self.assertEqual(parse_word("بَاْ"), (4, 3))

    def test_proposal_has_no_native_authority(self):
        proposal = aa.propose_acquisition("بَ")
        self.assertNotIn("verified", proposal)
        with patch.object(aa, "_NATIVE_PATH", Path("/nonexistent/nabt-native")):
            receipt = aa.read_acquired("بَ")
        self.assertFalse(receipt["verified"])
        self.assertEqual(receipt["status"], "VERIFICATION_UNAVAILABLE")
        self.assertIsNone(receipt["word_reader"])
        self.assertEqual(receipt["shape_handoffs"], [])

    def test_entire_native_result_is_compared_including_bool_int(self):
        proposal = aa.propose_acquisition("بَ")
        for mutation in ("rule", "span", "cell_bool", "extra", "source", "status"):
            forged = copy.deepcopy(proposal)
            if mutation == "rule": forged["pieces"][0]["rule"] = "MARKED_CARRIER_FAKE"
            if mutation == "span": forged["pieces"][0]["end"] += 1
            if mutation == "cell_bool": forged["pieces"][0]["start"] = False
            if mutation == "extra": forged["grammar_certified"] = True
            if mutation == "source": forged["revision"] = "2"
            if mutation == "status": forged["status"] = "DEFER"
            with patch.object(aa, "_native", return_value=forged):
                receipt = aa.acquire("بَ")
            self.assertFalse(receipt["verified"])
            self.assertEqual(receipt["status"], "VERIFICATION_FAILED")

    def test_installed_source_evidence_is_pinned(self):
        self.assertEqual(aa.source_inventory()["passages"], 23)
        with patch.object(aa, "SOURCE_MANIFEST_SHA256", "0" * 64):
            with self.assertRaises(ValueError):
                aa.source_inventory()


@unittest.skipUnless(aa._NATIVE_PATH.is_file(), "build alignedAcquisition for native integration tests")
class AcquisitionNativeTests(unittest.TestCase):
    def native_request(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            path.write_bytes(content)
            result = subprocess.run([str(aa._NATIVE_PATH), str(path)], capture_output=True, timeout=30)
        return result.returncode, json.loads(result.stdout)

    def test_native_matches_full_reports_with_debts_and_unicode(self):
        for text in ("", "بَابٌ", "بَابًا", "بَٰا", "بَال", "مَاءًا", "َهذا", "بَ\n😀", "بّْ", "«بَ»", "أُولُو"):
            for ending in ("wasl", "waqf"):
                with self.subTest(text=text, ending=ending):
                    checked = aa.acquire(text, ending=ending)
                    self.assertTrue(checked["verified"], checked)
                    self.assertEqual(checked["status"], checked["acquisition"]["status"])

    def test_native_transport_rejects_duplicates_types_and_unicode(self):
        request = {"text": "بَ", "source_id": "input", "revision": "1", "scope": "default", "ending": "wasl"}
        valid = json.dumps(request).encode()
        malformed = [b"\xff", b"[]", valid[:-1] + b',"text":"x"}',
                     valid[:-1] + b',"te\\u0078t":"x"}', valid.replace(b'"wasl"', b'true'),
                     valid.replace(b'"input"', b'"\\ud800"'), valid[:-1] + b',"extra":0}']
        for raw in malformed:
            code, report = self.native_request(raw)
            self.assertEqual(code, 2)
            self.assertEqual(report["status"], "INVALID_INPUT")

    def test_native_transport_budget(self):
        for text in ("a" * 4097, "😀" * 2049):
            request = {"text": text, "source_id": "input", "revision": "1", "scope": "default", "ending": "wasl"}
            code, report = self.native_request(json.dumps(request).encode())
            self.assertEqual((code, report["status"]), (2, "RESOURCE_EXHAUSTED"))
        code, report = self.native_request(b" " * (1024 * 1024 + 1))
        self.assertEqual((code, report["status"]), (2, "RESOURCE_EXHAUSTED"))

    def test_original_reader_and_complete_only_shape_handoff(self):
        text = "بَابٌ مجهول «بَابٌ»"
        report = aa.read_acquired(text)
        self.assertTrue(report["verified"], report)
        self.assertEqual(report["word_reader"], read_words(text.encode(), source_id="input", scope="default"))
        for word, handoff in zip(report["acquisition"]["words"], report["shape_handoffs"]):
            if word["status"] != "ACQUIRED":
                self.assertEqual(handoff["status"], "ACQUISITION_INCOMPLETE")
                self.assertNotIn("certificate", handoff)
            elif "certificate" in handoff:
                self.assertIsNone(handoff["certificate"]["source_text"])
                self.assertEqual(handoff["certificate"]["cells"], word["cells"])

    def test_exact_receipt_rejects_mutation_rehash_and_wrong_expected_binding(self):
        text = "بَابٌ"
        binding = dict(source_id="input", revision="1", scope="default", ending="wasl")
        report = aa.read_acquired(text, **binding)
        self.assertTrue(aa.verify_acquired(report, text=text, **binding)["valid"])
        for key in ("source_id", "revision", "scope", "ending"):
            wrong = {**binding, key: "waqf" if key == "ending" else "changed"}
            self.assertFalse(aa.verify_acquired(report, text=text, **wrong)["valid"])
        self.assertFalse(aa.verify_acquired(report, text="بَابٍ", **binding)["valid"])
        for field in ("reader", "cells", "raw", "offset", "status", "authority", "bool"):
            forged = copy.deepcopy(report)
            if field == "reader": forged["word_reader"]["world_truth"] = "ESTABLISHED"
            if field == "cells": forged["acquisition"]["pieces"][0]["cells"][0] += 1
            if field == "raw": forged["acquisition"]["pieces"][0]["raw"] = "تَ"
            if field == "offset": forged["acquisition"]["words"][0]["byte_end"] += 1
            if field == "status": forged["status"] = "DEFER"
            if field == "authority": forged["source_evidence"]["sha256"] = "0" * 64
            if field == "bool": forged["acquisition"]["pieces"][0]["start"] = False
            self.assertFalse(aa.verify_acquired(forged, text=text, **binding)["valid"], field)

    def test_cli_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            source, report = Path(directory) / "source.txt", Path(directory) / "report.json"
            source.write_text("بَابٌ", encoding="utf-8")
            read = subprocess.run([sys.executable, "-m", "tools.acquisition_cli", "read-acquired", str(source)],
                                  capture_output=True, timeout=30)
            self.assertEqual(read.returncode, 0, read.stderr)
            report.write_bytes(read.stdout)
            verify = subprocess.run([sys.executable, "-m", "tools.acquisition_cli", "verify-acquired", str(report), "--source", str(source)],
                                    capture_output=True, timeout=30)
            self.assertEqual(verify.returncode, 0, verify.stderr)
            self.assertTrue(json.loads(verify.stdout)["valid"])


if __name__ == "__main__":
    if os.environ.get("NABT_REQUIRE_ACQUISITION_NATIVE") == "1" and not aa._NATIVE_PATH.is_file():
        raise SystemExit("native acquisition checker is required")
    unittest.main()
