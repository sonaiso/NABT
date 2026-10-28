"""Contract-authored unit and boundary examples, independent of held-out gold."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.certificates import issue_certificate
from nabt.errors import NabtError
from nabt.word_reader import read_words
from tools import aligned_acquisition as v1
from tools import aligned_acquisition_v2 as aa

ROOT = Path(__file__).resolve().parents[1]
BINDING = dict(source_id="unit", revision="2", scope="citation", ending="wasl", onset="word_initial")


class ArticleProposalTests(unittest.TestCase):
    def test_three_finite_signatures_have_independent_a116_arrays(self):
        # A116 carrier indices: hamza 28, lam 22, ha 5, qaf 20, waw 26,
        # ghayn 18, alif 0, mim 23; states fatha/damma/kasra/sukun 0/1/2/3.
        examples = (("الْحَقَّ", "ARTICLE_HAQQ", [112, 91, 20, 83, 80]),
                    ("ٱَلْقَوْمُ", "ARTICLE_QAWM", [112, 91, 80, 107, 93]),
                    ("اَلْغُلَامِ", "ARTICLE_GHULAM", [112, 91, 73, 88, 3, 94]))
        for text, reading, cells in examples:
            with self.subTest(text=text):
                result = aa.propose_acquisition(text)
                self.assertEqual(result["status"], "ACQUIRED")
                self.assertEqual(result["words"][0]["cells"], cells)
                self.assertEqual(result["pieces"][0]["rule"], reading + "_INITIAL")
                self.assertEqual(result["pieces"][0]["raw"], text[:result["pieces"][0]["end"]])
                self.assertEqual(result["law_id"], aa.LAW_ID)
                self.assertEqual(result["onset"], "word_initial")
                self.assertNotIn("verified", result)

    def test_exact_finite_variants_and_pause_are_separate_policies(self):
        for initial in ("ا", "اَ", "ٱ", "ٱَ"):
            for vowel, final_cell in (("َ", 80), ("ُ", 81), ("ِ", 82)):
                for marks in ("ّ" + vowel, vowel + "ّ"):
                    text = initial + "لْحَق" + marks
                    wasl = aa.propose_acquisition(text)
                    waqf = aa.propose_acquisition(text, ending="waqf")
                    self.assertEqual(wasl["words"][0]["cells"], [112, 91, 20, 83, final_cell])
                    self.assertEqual(waqf["words"][0]["cells"], [112, 91, 20, 83, 83])
                    self.assertEqual(wasl["pieces"][-1]["raw"], "ق" + marks)
        pair = aa.propose_acquisition("الْحَقُّ ٱلْقَوْمِ؟", ending="waqf")
        self.assertEqual([word["cells"] for word in pair["words"]],
                         [[112, 91, 20, 83, 81], [112, 91, 80, 107, 95]])

    def test_finite_word_witness_not_prefix_or_lexical_guess(self):
        unsupported = ("الْعَبْ", "ٱلْبَسْ", "الْقَ", "الْحَقَ", "الْحِقَّ",
                       "الْحَقْ", "الْحَقٌّ", "الْقَوَمُ", "الْقَومُ", "الْغَلَامُ",
                       "الْغُلَام", "الْغُلَاْمُ", "اُلْقَوْمُ", "الَحَقَّ",
                       "الْحَقَّنَ", "الْشَمْسُ", "الْبَابُ", "الحق")
        for text in unsupported:
            with self.subTest(text=text):
                result = aa.propose_acquisition(text)
                self.assertEqual(result["status"], "DEFER")
                self.assertTrue(all(piece["rule"] == "ARTICLE_READING_NOT_LICENSED"
                                    and piece["cells"] == [] for piece in result["pieces"]))

    def test_malformed_precedence_and_whole_word_debts(self):
        for text in ("اَُلْحَقَّ", "الْحَقَّّ", "الْحَقّْ", "الْقَوْمُٰ", "َالْحَقَّ"):
            for onset in ("word_initial", "connected"):
                self.assertEqual(aa.propose_acquisition(text, onset=onset)["status"], "INVALID_INPUT")
        result = aa.propose_acquisition("اللَّهُ")
        self.assertEqual(result["status"], "DEFER")
        self.assertTrue(all(piece["rule"] == "ORTHOGRAPHIC_LEXICON_REQUIRED" for piece in result["pieces"]))
        result = aa.propose_acquisition("اَللََّّهُ")
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertEqual(result["pieces"][0]["rule"], "ORTHOGRAPHIC_LEXICON_REQUIRED")

    def test_connected_defers_every_nonmalformed_piece(self):
        for text in ("الْحَقَّ", "بَابٌ", "«الْغُلَامُ»\r\nبَ", "اَلْحَقَّ بّْ"):
            for ending in ("wasl", "waqf"):
                result = aa.propose_acquisition(text, onset="connected", ending=ending)
                for piece in result["pieces"]:
                    self.assertEqual(piece["cells"], [])
                    if piece["status"] not in ("INVALID_INPUT", "BOUNDARY"):
                        self.assertEqual((piece["status"], piece["rule"]),
                                         ("DEFER", "CONNECTED_ONSET_NOT_IMPLEMENTED"))
                self.assertNotEqual(result["status"], "ACQUIRED")
        for text in ("", " \t،\r\n"):
            result = aa.propose_acquisition(text, onset="connected")
            self.assertEqual((result["status"], result["reason"], result["words"]), ("DEFER", "NO_WORD", []))

    def test_source_restoration_and_scalar_byte_offsets(self):
        for text in ("«ٱَلْحَقَّ»\r\nالْقَوْمُ", "😀الْغُلَامِ\tبَ", "\u0301الْحَقَّ", "الْحَقَّ\u00a0بَ"):
            report = aa.propose_acquisition(text)
            self.assertEqual("".join(piece["raw"] for piece in report["pieces"]), text)
            scalar = byte = 0
            for piece in report["pieces"]:
                self.assertEqual((piece["start"], piece["byte_start"]), (scalar, byte))
                self.assertEqual(text[piece["start"]:piece["end"]], piece["raw"])
                self.assertEqual(text.encode()[piece["byte_start"]:piece["byte_end"]], piece["raw"].encode())
                scalar, byte = piece["end"], piece["byte_end"]
            self.assertEqual((scalar, byte), (len(text), len(text.encode())))

    def test_other_words_remain_v1_and_verified_v1_is_never_relabelled(self):
        for text in ("بَابٌ", "وَالْحَقَّ", "إِنْ", "هَٰذَا", "مَاءً", "بّْ"):
            original = v1.propose_acquisition(text, ending="waqf")
            with patch.object(v1, "acquire", side_effect=AssertionError("v1 authority reused")), \
                    patch.object(v1, "read_acquired", side_effect=AssertionError("v1 receipt reused")):
                result = aa.propose_acquisition(text, ending="waqf")
            self.assertEqual(result, {**original, "law_id": aa.LAW_ID, "onset": "word_initial"})

    def test_input_types_metadata_and_budgets_fail_closed(self):
        for text in (None, True, 1, [], {}, b"\xff", "\ud800"):
            self.assertEqual(aa.acquire(text)["status"], "INVALID_INPUT")
        for onset in (None, True, 1, "wasl", "WORD_INITIAL", []):
            self.assertEqual(aa.acquire("الْحَقَّ", onset=onset)["status"], "INVALID_INPUT")
        for key in ("source_id", "revision", "scope", "ending"):
            self.assertEqual(aa.acquire("الْحَقَّ", **{key: True})["status"], "INVALID_INPUT")
        for text in ("a" * 4097, b"a" * 8193, "😀" * 2049):
            self.assertEqual(aa.acquire(text)["status"], "RESOURCE_EXHAUSTED")

    def test_native_absence_and_transport_mutations(self):
        with patch.object(aa, "_NATIVE_PATH", Path("/nonexistent/alignedAcquisitionV2")):
            report = aa.read_acquired("الْحَقَّ")
        self.assertEqual(report["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(report["verified"])
        self.assertEqual(report["shape_handoffs"], [])
        for mutation in ("onset", "law", "span", "bool", "reading", "raw", "extra"):
            forged = aa.propose_acquisition("الْحَقَّ")
            if mutation == "onset": forged["onset"] = "connected"
            if mutation == "law": forged["law_id"] = v1.LAW_ID
            if mutation == "span": forged["pieces"][0]["byte_end"] += 1
            if mutation == "bool": forged["pieces"][0]["start"] = False
            if mutation == "reading": forged["pieces"][0]["rule"] = "ARTICLE_QAWM_INITIAL"
            if mutation == "raw": forged["pieces"][0]["raw"] = "أَ"
            if mutation == "extra": forged["grammar_certified"] = True
            with patch.object(aa, "_native", return_value=forged):
                report = aa.acquire("الْحَقَّ")
            self.assertEqual(report["status"], "VERIFICATION_FAILED", mutation)
            self.assertFalse(report["verified"])

    def test_pins_cover_base_and_additive_evidence(self):
        inventory = aa.source_inventory()
        self.assertEqual(inventory["passages"], 16)
        self.assertEqual(inventory["finite_readings"], ["ARTICLE_HAQQ", "ARTICLE_QAWM", "ARTICLE_GHULAM"])
        self.assertEqual(inventory["base_acquisition"], v1.source_inventory())
        for module in (v1, aa):
            with patch.object(module, "SOURCE_MANIFEST_SHA256", "0" * 64):
                with self.assertRaises(ValueError):
                    aa.source_inventory()

    def test_receipts_reject_non_json_containers_and_nonfinite_values(self):
        for value in ({"pieces": ()}, {0: "wrong key"}, {"x": float("nan")}, {"x": {1}}):
            self.assertEqual(aa.verify_acquired(value, text="الْحَقَّ", **BINDING)["status"], "INVALID_RECEIPT")
        cyclic = {}
        cyclic["self"] = cyclic
        self.assertEqual(aa.verify_acquired(cyclic, text="الْحَقَّ", **BINDING)["status"], "INVALID_RECEIPT")

    def test_ordinary_shape_machine_rejects_deleted_silent_onset(self):
        with self.assertRaises(NabtError) as error:
            issue_certificate([91, 20, 83, 80], "wasl", source_text=None)
        self.assertEqual(error.exception.code, "UNLICENSED_SHAPE")
        self.assertEqual(issue_certificate([112, 91, 20, 83, 80], "wasl", source_text=None)["cells"],
                         [112, 91, 20, 83, 80])


@unittest.skipUnless(aa._NATIVE_PATH.is_file(), "build alignedAcquisitionV2 for native integration")
class ArticleNativeTests(unittest.TestCase):
    def test_native_replays_contract_examples_and_boundaries(self):
        for text in ("الْحَقَّ", "ٱَلْقَوْمُ", "اَلْغُلَامِ", "الْحَقَّ", "الْعَبْ",
                     "الْحَقَ", "اَُلْحَقَّ", "اللَّهُ", "بَابٌ", "«الْحَقَّ»\r\nبَ", "", "😀"):
            for onset in ("word_initial", "connected"):
                for ending in ("wasl", "waqf"):
                    report = aa.acquire(text, onset=onset, ending=ending)
                    self.assertTrue(report["verified"], (text, onset, ending, report))

    def test_native_transport_is_exact_and_bounded(self):
        request = dict(text="الْحَقَّ", **BINDING)
        valid = json.dumps(request).encode()
        malformed = [b"\xff", b"[]", valid[:-1] + b',"onset":"connected"}',
                     valid[:-1] + b',"on\\u0073et":"connected"}',
                     valid.replace(b'"word_initial"', b'true'),
                     valid.replace(b'"word_initial"', b'"wasl"'),
                     valid.replace(b'"unit"', b'"\\ud800"'),
                     valid[:-1] + b',"extra":0}',
                     json.dumps({key: value for key, value in request.items() if key != "onset"}).encode()]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "request.json"
            for raw in malformed:
                path.write_bytes(raw)
                result = subprocess.run([str(aa._NATIVE_PATH), str(path)], capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 2, raw)
                self.assertEqual(json.loads(result.stdout)["status"], "INVALID_INPUT")
            for raw in (b" " * (1024 * 1024 + 1), json.dumps({**request, "text": "a" * 4097}).encode()):
                path.write_bytes(raw)
                result = subprocess.run([str(aa._NATIVE_PATH), str(path)], capture_output=True, timeout=30)
                self.assertEqual(json.loads(result.stdout)["status"], "RESOURCE_EXHAUSTED")

    def test_original_bytes_shape_and_all_receipt_bindings(self):
        text = " \r\nٱَلْقَوْمُ «الْحَقَّ» "
        report = aa.read_acquired(text, **BINDING)
        self.assertTrue(report["verified"], report)
        self.assertEqual(report["word_reader"], read_words(text.encode(), source_id="unit", scope="citation"))
        self.assertTrue(all(row["status"] == "SHAPE_LICENSED" for row in report["shape_handoffs"]))
        self.assertTrue(aa.verify_acquired(report, text=text, **BINDING)["valid"])
        for key, value in (("source_id", "other"), ("revision", "3"), ("scope", "other"),
                           ("ending", "waqf"), ("onset", "connected")):
            self.assertFalse(aa.verify_acquired(report, text=text, **{**BINDING, key: value})["valid"])
        self.assertFalse(aa.verify_acquired(report, text=text + " ", **BINDING)["valid"])
        for key, value in (("verified", 1), ("onset", "connected"), ("authority", "GRAMMAR_CERTIFIED")):
            forged = copy.deepcopy(report)
            forged[key] = value
            self.assertFalse(aa.verify_acquired(forged, text=text, **BINDING)["valid"])

    def test_source_failure_and_resource_statuses_are_distinct(self):
        for error, status in ((ValueError("pin"), "SOURCE_EVIDENCE_UNAVAILABLE"),
                              (OverflowError("limit"), "RESOURCE_EXHAUSTED")):
            with patch.object(aa, "source_inventory", side_effect=error):
                report = aa.read_acquired("الْحَقَّ")
            self.assertEqual(report["status"], status)
            self.assertFalse(report["verified"])
            self.assertIsNone(report["word_reader"])

    def test_cli_read_verify_and_duplicate_key_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, receipt = Path(temporary) / "source", Path(temporary) / "receipt"
            source.write_bytes("الْحَقَّ".encode())
            command = [sys.executable, "-m", "tools.article_acquisition_cli"]
            run = subprocess.run([*command, "read", str(source)], cwd=ROOT, capture_output=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            receipt.write_bytes(run.stdout)
            verify = [*command, "verify", str(receipt), str(source)]
            replay = subprocess.run(verify, cwd=ROOT, capture_output=True, timeout=30)
            self.assertEqual(replay.returncode, 0, replay.stdout)
            receipt.write_bytes(b'{"verified":true,' + run.stdout.lstrip()[1:])
            replay = subprocess.run(verify, cwd=ROOT, capture_output=True, timeout=30)
            self.assertEqual(replay.returncode, 2)
            self.assertEqual(json.loads(replay.stdout)["error"], "DUPLICATE_JSON_KEY")


if __name__ == "__main__":
    if os.environ.get("NABT_REQUIRE_ARTICLE_ACQUISITION_NATIVE") == "1" and not aa._NATIVE_PATH.is_file():
        raise SystemExit("native article acquisition checker is required")
    unittest.main()
