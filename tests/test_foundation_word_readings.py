"""Source-to-foundation integration, independently of lexical acceptance."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from nabt import foundation
from nabt.errors import NabtError
from nabt.word_reader import read_words, verify_word_reading


class FoundationWordIntegration(unittest.TestCase):
    def test_partial_projection_does_not_invent_an_encoding(self):
        report = read_words("إِنْ", source_id="same_occurrence")
        projection = report["foundation_source"]
        self.assertEqual(projection["status"], "PARTIAL")
        self.assertEqual(projection["source"]["text"], "إِنْ")
        self.assertEqual(projection["source"]["id"], report["source_id"])
        self.assertEqual(projection["source"]["revision"], report["source_sha256"])
        self.assertEqual("".join(p["text"] for p in projection["pieces"]), "إِنْ")
        self.assertTrue(verify_word_reading(report)["valid"])

    def test_complete_cells_do_not_create_a_morphological_reading(self):
        report = read_words("قُمْتُ")
        projection = report["foundation_source"]
        self.assertEqual(projection["status"], "COMPLETE")
        self.assertEqual(projection["cells"], [81, 95, 9])
        self.assertEqual(report["semantic_projection"], "NONE")
        self.assertEqual(report["facts"], [])

    def test_receipt_cannot_be_removed_changed_or_reused(self):
        report = read_words("هَلْ", source_id="first")
        for field in ("cells", "number", "source", "status", "pieces"):
            changed = deepcopy(report)
            del changed["foundation_source"][field]
            self.assertFalse(verify_word_reading(changed)["valid"], field)
        changed = deepcopy(report)
        del changed["foundation_source"]
        self.assertFalse(verify_word_reading(changed)["valid"])
        self.assertFalse(verify_word_reading(report, source_id="second")["valid"])

    def test_direct_api_and_verification_cannot_bypass_foundation(self):
        report = read_words("هَلْ")
        self.assertTrue(verify_word_reading(report)["valid"])
        with patch.object(foundation, "require_foundation", side_effect=NabtError(
                "FOUNDATION_SENTINEL", "independent admission denial", status="DEFER")):
            for operation in (lambda: read_words("هَلْ"),
                              lambda: verify_word_reading(report)):
                with self.assertRaises(NabtError) as error:
                    operation()
                self.assertEqual(error.exception.code, "FOUNDATION_SENTINEL")

    def test_cli_publishes_projection_scope_and_keeps_residuals(self):
        root = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PYTHONPATH": str(root / "src")}
        for text, code, status in (("قُمْتُ", 0, "COMPLETE"),
                                   ("جَاءَ", 3, "PARTIAL"),
                                   ("قُمْتَُ", 2, "INVALID")):
            result = subprocess.run([sys.executable, "-m", "nabt", "foundation", text],
                                    cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, code, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value["projection"]["status"], status)
            self.assertFalse(value["linguistic_license"])
            self.assertFalse(value["world_truth_established"])
            self.assertEqual(value["scope"], "SOURCE_REPRESENTATION_ONLY")


if __name__ == "__main__":
    unittest.main()
