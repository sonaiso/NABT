"""Source and replay invariants of the deliberately bounded lexical pilot."""

import copy
import unittest

from nabt import NabtError
from nabt.word_reader import (read_words, verify_word_reading, word_reading_number,
                              decode_word_reading)


class WordReaderTests(unittest.TestCase):
    def test_partition_restores_spacing_punctuation_and_combining_mark_order(self):
        source = "  هَلْ\tضَرَبَ\nزَيْدٌ؟  "
        reading = read_words(source)
        self.assertEqual("".join(s["surface"] for s in reading["segments"]), source)
        raw = source.encode("utf-8")
        last = 0
        for segment in reading["segments"]:
            self.assertEqual(segment["span"]["start"], last)
            self.assertEqual(raw[last:segment["span"]["end"]].decode(), segment["surface"])
            last = segment["span"]["end"]
        self.assertEqual(last, len(raw))

    def test_kind_reading_does_not_manufacture_case_role_or_reference(self):
        for text in ("زَيْدٌ", "ضَرَبَ", "هُوَ", "هَلْ"):
            report = read_words(text)
            self.assertTrue(report["occurrences"][0]["alternatives"])
            for alt in report["occurrences"][0]["alternatives"]:
                for part in alt["parts"]:
                    self.assertIsNone(part["actual_role"])
                    self.assertIsNone(part["actual_case"])
                    self.assertIsNone(part["referent"])
            self.assertEqual(report["facts"], [])
            self.assertEqual(report["semantic_projection"], "NONE")

    def test_equal_spelling_at_two_occurrences_has_different_identity(self):
        report = read_words("زَيْدٌ زَيْدٌ")
        a, b = report["occurrences"]
        self.assertNotEqual(a["occurrence_id"], b["occurrence_id"])
        self.assertNotEqual(a["alternatives"][0]["parts"][0]["reading_id"],
                            b["alternatives"][0]["parts"][0]["reading_id"])

    def test_replay_binds_expected_source_id_scope_and_bytes(self):
        report = read_words("زَيْدٌ", source_id="alpha", scope="first")
        self.assertTrue(verify_word_reading(report, source="زَيْدٌ", source_id="alpha", scope="first")["valid"])
        for kwargs in ({"source": "زَيْدًا"}, {"source_id": "beta"}, {"scope": "second"}):
            self.assertFalse(verify_word_reading(report, **kwargs)["valid"])

    def test_changed_reading_kind_case_span_and_omissions_fail_full_replay(self):
        report = read_words("إِنَّ زَيْدًا قَائِمٌ")
        self.assertTrue(verify_word_reading(report)["valid"])
        mutations = []
        wrong = copy.deepcopy(report); wrong["facts"] = [{"invented": True}]; mutations.append(wrong)
        wrong = copy.deepcopy(report); wrong["occurrences"].pop(); mutations.append(wrong)
        wrong = copy.deepcopy(report); wrong["occurrences"][1]["alternatives"][0]["parts"][0]["kind"] = 2; mutations.append(wrong)
        wrong = copy.deepcopy(report); wrong["occurrences"][1]["span"]["start"] += 1; mutations.append(wrong)
        wrong = copy.deepcopy(report); wrong["contexts"] = []; mutations.append(wrong)
        wrong = copy.deepcopy(report); wrong["policy_sha256"] = "0" * 64; mutations.append(wrong)
        for value in mutations:
            with self.subTest(value=value["policy_sha256"]):
                self.assertFalse(verify_word_reading(value)["valid"])

    def test_number_replays_exact_report_and_rejects_malformed_input(self):
        report = read_words("مِنْ رَجُلٍ")
        self.assertEqual(decode_word_reading(word_reading_number(report)), report)
        for value in (0, 2, -1, True):
            with self.subTest(value=value), self.assertRaises(NabtError):
                decode_word_reading(value)
        for value in (None, [], {}, {"raw_text": "زَيْدٌ"}):
            self.assertFalse(verify_word_reading(value)["valid"])

    def test_mark_conflicts_do_not_count_as_unknown_words(self):
        for text in ("زَيْدَُ", "زَيْدَُ", "زَيْدُُ"):
            report = read_words(text)
            self.assertEqual(report["status"], "REJECT")
            self.assertEqual(report["occurrences"][0]["obligations"], ["CONFLICTING_MARKS"])

    def test_quote_is_mention_and_unknown_does_not_become_a_particle(self):
        report = read_words("«إِنَّ» زَيْدًا قَائِمٌ")
        self.assertTrue(all(c["status"] == "DEFER" and not c["bindings"] for c in report["contexts"]))
        unknown = read_words("بلبلة")["occurrences"][0]
        self.assertEqual(unknown["candidate_kinds"], [0, 1, 2])
        self.assertEqual(unknown["alternatives"], [])


if __name__ == "__main__":
    unittest.main()
