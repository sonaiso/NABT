"""Contract examples and adversarial boundaries, independently specified here.

These are development tests, not the frozen independent evaluation matrix.
"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import acquired_person_nominal_v3 as bridge

ROOT = Path(__file__).resolve().parents[1]
BINDING = dict(source_id="syntax-test", revision="3", scope="utterance",
               ending="wasl", onset="word_initial")
NATIVE = (ROOT / "formal/.lake/build/bin/acquiredSyntaxV3").is_file()
COMPOSITE = NATIVE and (ROOT / "formal/.lake/build/bin/connectedAcquisitionV3").is_file()


class SyntaxInputTests(unittest.TestCase):
    def test_invalid_input_and_binding_fail_before_dependencies(self):
        bad = (None, True, 1, [], {}, "", "\ud800", "x\x85", "x" * 513)
        with patch.object(bridge.acquisition, "read_acquired") as call:
            for key in ("task", "source_id", "revision", "scope", "ending", "onset"):
                for value in bad:
                    args = {**BINDING, "task": "person", key: value}
                    report = bridge.evaluate("قمتُ", **args)
                    self.assertEqual(report["status"], "INVALID_INPUT", (key, repr(value)))
                    self.assertFalse(report["chain_complete"])
            for source in (True, [], {}, 4, b"\xff", "\ud800"):
                self.assertEqual(bridge.evaluate(source, task="person")["status"], "INVALID_INPUT")
            for source in ("ق" * 4097, b"a" * 8193):
                self.assertEqual(bridge.evaluate(source, task="person")["status"], "RESOURCE_EXHAUSTED")
        call.assert_not_called()

    def test_receipt_non_json_and_oversize_are_not_authority(self):
        for report in ([], True, {0: "key"}, {"x": ()}, {"x": float("nan")}):
            result = bridge.verify(report, text="قمتُ", task="person", **BINDING)
            self.assertEqual(result["status"], "INVALID_RECEIPT")
        with patch.object(bridge, "MAX_REPORT_BYTES", 8):
            result = bridge.verify({"large": "receipt"}, text="قمتُ", task="person", **BINDING)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")


@unittest.skipUnless(NATIVE, "build acquiredSyntaxV3")
class NativeSyntaxTests(unittest.TestCase):
    def check_native(self, source, task):
        proposal = bridge.propose_syntax(source, task=task, **BINDING)
        request = {key: proposal[key] for key in
                   ("text", "task", "source_id", "revision", "scope", "ending", "onset")}
        self.assertEqual(bridge._wire(bridge._native(request)), bridge._wire(proposal))
        return proposal

    def test_three_persons_both_exact_aliases_and_source_spans(self):
        examples = (("قمتُ", "قُمْتُ", 1, None, "ُ"),
                    ("قمتَ", "قُمْتَ", 2, "masculine", "َ"),
                    ("قمتِ", "قُمْتِ", 2, "feminine", "ِ"))
        for short, full, person, gender, vowel in examples:
            for raw in (short, full):
                source = " \t" + raw + ".\t "
                report = self.check_native(source, "person")
                self.assertEqual(report["status"], "LICENSED_PERSON")
                projection = report["person"]
                self.assertEqual((projection["person"], projection["gender"], projection["source_vowel"]),
                                 (person, gender, vowel))
                self.assertIsNone(projection["referent"])
                for span in (projection["source_word"], projection["source_suffix"]):
                    self.assertEqual(source[span["start"]:span["end"]], span["raw"])
                    self.assertEqual(source.encode()[span["byte_start"]:span["byte_end"]].decode(), span["raw"])
                self.assertEqual(projection["source_suffix"]["raw"], "ت" + vowel)

    def test_nominal_orders_aliases_numbers_and_collective_ambiguity(self):
        examples = (("الولدُ", "ذاهبٌ", "الْوَلَدُ", "ذَاهِبٌ", "singular"),
                    ("الولدانِ", "ذاهبانِ", "الْوَلَدَانِ", "ذَاهِبَانِ", "dual"),
                    ("الأولادُ", "ذاهبونَ", "الْأَوْلَادُ", "ذَاهِبُونَ", "plural"))
        for short_s, short_p, full_s, full_p, number in examples:
            for subject in (short_s, full_s):
                for predicate in (short_p, full_p):
                    for si, source in ((0, subject + " " + predicate), (1, predicate + "\t" + subject)):
                        report = self.check_native(source, "nominal_syntax")
                        p = report["nominal"]
                        self.assertEqual(report["status"], "LICENSED_NOMINAL")
                        self.assertEqual((p["number"], p["subject_index"], p["predicate_index"]), (number, si, 1-si))
                        self.assertEqual(p["subject_source"]["raw"], subject)
                        self.assertEqual(p["predicate_source"]["raw"], predicate)
                        self.assertEqual(p["lexical_cardinality_alternatives"],
                                         ["individual", "collective"] if number == "singular" else [])
                        self.assertIsNone(p["denotation_cardinality"])

    def test_missing_person_vowels_remain_three_diagnostics(self):
        for raw in ("قمت", "قُمْت", "قُمْتْ"):
            result = self.check_native(raw, "person")
            self.assertEqual(result["status"], "DEFER")
            self.assertIsNone(result["person"])
            self.assertEqual(result["diagnostic_person_hypotheses"], [
                {"reading_id": "QUMTU", "person": 1, "number": "singular", "gender": None},
                {"reading_id": "QUMTA", "person": 2, "number": "singular", "gender": "masculine"},
                {"reading_id": "QUMTI", "person": 2, "number": "singular", "gender": "feminine"}])

    def test_case_adjacency_is_not_predication_and_mismatches_defer(self):
        subjects = ("الولدُ", "الولدانِ", "الأولادُ")
        predicates = ("ذاهبٌ", "ذاهبانِ", "ذاهبونَ")
        for i, subject in enumerate(subjects):
            for j, predicate in enumerate(predicates):
                if i == j:
                    continue
                for raw in (subject + " " + predicate, predicate + " " + subject):
                    self.assertIsNone(self.check_native(raw, "nominal_syntax")["nominal"])
        for source in ("رَجُلٌ كِتَابٌ", "وَلَدٌ ذَاهِبٌ", "الْوَلَدُ الذَّاهِبُ",
                       "الْوَلَدَ ذَاهِبٌ", "قُمْتُ الْوَلَدُ", "الولد ذاهبٌ", "أذاهبٌ الولدُ",
                       "ما ذاهبٌ الولدُ", "الولدُ ذاهبٌ اليوم", "الولدُ ذاهبٌ،", "الولدُ\nذاهبٌ",
                       "«الولدُ ذاهبٌ»", "الولدُ ذاهبٌ..", "الولدُ؛ذاهبٌ", "ذاهبٌ"):
            result = self.check_native(source, "nominal_syntax")
            self.assertEqual(result["status"], "DEFER", source)
        for source in ("قمتُُ", "قمتَُ", "قُمتُ", "قُمْتَِ", "قمتُ\n", "«قمتُ»", "قمتُ.​"):
            result = self.check_native(source, "person")
            self.assertEqual(result["status"], "DEFER", source)
            self.assertEqual(result["diagnostic_person_hypotheses"], [])

    def test_native_duplicate_keys_invalid_utf8_and_metadata(self):
        request = dict(text="قمتُ", task="person", **BINDING)
        raw = json.dumps(request, ensure_ascii=False).encode()
        payloads = (b"\xff", raw[:-1] + b',"task":"person"}',
                    json.dumps({**request, "source_id": True}).encode(),
                    json.dumps({**request, "task": "anything"}).encode(),
                    raw[:-1] + b',"extra":1}')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            for payload in payloads:
                path.write_bytes(payload)
                result = subprocess.run([str(bridge._NATIVE_PATH), str(path)], capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)["status"], "INVALID_INPUT")


@unittest.skipUnless(COMPOSITE, "build connectedAcquisitionV3 and acquiredSyntaxV3")
class CompositeTests(unittest.TestCase):
    def test_complete_original_source_readings_endings_and_connected_gate(self):
        for source, task in (("قمتُ", "person"), ("قمتَ", "person"), ("قمتِ", "person"),
                             ("الولدُ ذاهبٌ", "nominal_syntax"), ("ذاهبانِ الولدانِ", "nominal_syntax"),
                             ("الأولادُ ذاهبونَ", "nominal_syntax")):
            for ending in ("wasl", "waqf"):
                result = bridge.evaluate(source.encode(), task=task, **{**BINDING, "ending": ending})
                self.assertTrue(result["chain_complete"], (source, ending, result["blocked_by"]))
                self.assertFalse(result["referents_established"])
                self.assertFalse(result["world_truth_established"])
                self.assertEqual(result["acquisition"]["acquisition"]["text"], source)
        result = bridge.evaluate("ذاهبٌ الولدُ", task="nominal_syntax", **{**BINDING, "onset": "connected"})
        self.assertFalse(result["chain_complete"])
        self.assertIsNone(result["nominal"])
        self.assertTrue(result["syntax"]["verified"])
        self.assertIsNotNone(result["syntax"]["native_result"]["nominal"])

    def test_every_dependency_reopens_original_input(self):
        source = b" \t" + "قمتُ".encode() + b". "
        with patch.object(bridge.acquisition, "read_acquired", wraps=bridge.acquisition.read_acquired) as acq, \
                patch.object(bridge, "_native", wraps=bridge._native) as native:
            result = bridge.evaluate(source, task="person", **BINDING)
        self.assertTrue(result["chain_complete"])
        self.assertEqual(acq.call_args.args[0], source)
        self.assertEqual(native.call_args.args[0]["text"].encode(), source)

    def test_missing_native_mismatch_and_source_failure_cannot_borrow_success(self):
        for error, expected in ((FileNotFoundError(), "VERIFICATION_UNAVAILABLE"),
                                (ValueError(), "VERIFICATION_FAILED"),
                                (OverflowError(), "RESOURCE_EXHAUSTED")):
            with patch.object(bridge, "_native", side_effect=error):
                result = bridge.evaluate("قمتُ", task="person", **BINDING)
            self.assertEqual(result["status"], expected)
            self.assertIsNone(result["person"])
            self.assertFalse(result["chain_complete"])
        with patch.object(bridge.acquisition, "source_inventory", side_effect=ValueError("changed source")):
            result = bridge.evaluate("قمتُ", task="person", **BINDING)
        self.assertEqual(result["status"], "SOURCE_EVIDENCE_UNAVAILABLE")
        self.assertIsNone(result["person"])

    def test_entire_receipt_and_independent_binding_replay(self):
        source = "قمتُ"
        report = bridge.evaluate(source, task="person", **BINDING)
        self.assertTrue(bridge.verify(report, text=source, task="person", **BINDING)["valid"])
        changes = (("person", "person", True), ("person", "gender", "masculine"),
                   ("person", "source_vowel", "َ"), ("binding", "scope", "elsewhere"))
        for parent, key, value in changes:
            forged = copy.deepcopy(report)
            forged[parent][key] = value
            self.assertFalse(bridge.verify(forged, text=source, task="person", **BINDING)["valid"])
        for field, value in (("source_id", "other"), ("revision", "4"), ("scope", "other"),
                             ("ending", "waqf"), ("onset", "connected")):
            self.assertFalse(bridge.verify(report, text=source, task="person", **{**BINDING, field: value})["valid"])
        self.assertFalse(bridge.verify(report, text="قمتَ", task="person", **BINDING)["valid"])
        self.assertFalse(bridge.verify(report, text=source, task="nominal_syntax", **BINDING)["valid"])
        deferred = bridge.evaluate("قمت", task="person", **BINDING)
        replay = bridge.verify(deferred, text="قمت", task="person", **BINDING)
        self.assertTrue(replay["replay_matches"])
        self.assertFalse(replay["valid"])


if __name__ == "__main__":
    unittest.main()
