"""Reviewer counterexamples for the Arabic syntax bridge, not held-out data.

These cases check why an extracted reading is licensed, independently of the
implementation's own examples. Unsupported/ambiguous cases may defer; they
must not acquire the incorrect facts or rules identified by the reviewer.
"""
from __future__ import annotations

import copy
import json
import unittest

from nabt.arabic_reader import (
    Mood, decode_reading_number, read_arabic,
)
from nabt.errors import NabtError
from nabt.text_ir import Atom


class ArabicReaderReview(unittest.TestCase):
    def assert_restored(self, reading, text):
        doc = reading.document
        self.assertEqual(doc.source.raw_bytes, text.encode("utf-8"))
        self.assertEqual(b"".join(s.span.extract(doc.source) for s in doc.segments), doc.source.raw_bytes)
        for step in reading.steps:
            for cue in step.cues:
                self.assertEqual(cue.span.extract(doc.source).decode("utf-8"), cue.surface)

    def test_lexical_waw_is_not_a_conjunction_prefix_license(self):
        text = "الطالب ناجح واثق."
        reading = read_arabic(text)
        self.assert_restored(reading, text)
        self.assertNotIn(Atom("اثق", ("الطالب",)), [f.atom for f in reading.document.facts])
        if reading.accepted:
            # A future broader parser may prove the complete lexical reading.
            self.assertIn(Atom("واثق", ("الطالب",)), [f.atom for f in reading.document.facts])

    def test_lexical_waw_survives_before_a_complete_following_clause(self):
        text = "فرد وليد. سالم هو نقي وليدٌ هو أمين."
        reading = read_arabic(text)
        self.assert_restored(reading, text)
        self.assertNotIn(Atom("أمين", ("ليد",)), [f.atom for f in reading.document.facts])

    def test_tanwin_cannot_decide_predication_direction_alone(self):
        reading = read_arabic("ناجحٌ سالمٌ.")
        self.assertFalse(reading.accepted)
        self.assertEqual(reading.document.facts, ())

    def test_orphan_mark_cannot_create_a_licensed_operator(self):
        for text in ("ِإنّ سالم هو نقي.", "ُهل سالم هو نقي؟"):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assert_restored(reading, text)
                self.assertFalse(reading.accepted)
                self.assertEqual(reading.document.facts, ())
                self.assertEqual(reading.document.queries, ())

    def test_question_punctuation_survives_spaces_and_tabs(self):
        for text in ("الطالب ناجح ؟", "سالم هو نقي \t؟", "سالم هو نقي  ?"):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assert_restored(reading, text)
                self.assertEqual(reading.document.facts, ())
                self.assertEqual(reading.document.rules, ())
                if reading.accepted:
                    self.assertEqual(reading.steps[0].mood, Mood.QUESTION)

    def test_initial_alif_lam_may_belong_to_a_verb(self):
        for text in ("التفت سالم.", "التهب الخشب."):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assertFalse(reading.accepted)
                self.assertEqual(reading.document.facts, ())
                self.assertTrue(reading.document.residuals)

    def test_question_operator_does_not_establish_nominal_word_roles(self):
        reading = read_arabic("هل نام زيد؟")
        self.assertNotIn(Atom("زيد", ("نام",)), [q.atom for q in reading.document.queries])
        if reading.accepted:
            self.assertIn(Atom("نام", ("زيد",)), [q.atom for q in reading.document.queries])

    def test_shared_predicate_does_not_jump_over_an_explicit_new_subject(self):
        text = "سالم هو نشيط و فهد هو لطيف و مرح."
        reading = read_arabic(text)
        self.assert_restored(reading, text)
        self.assertNotIn(Atom("مرح", ("سالم",)), [f.atom for f in reading.document.facts])
        if reading.accepted:
            self.assertIn(Atom("مرح", ("فهد",)), [f.atom for f in reading.document.facts])

    def test_vocalized_imperative_kul_is_not_universal_quantification(self):
        reading = read_arabic("كُلْ طعام الطفل.")
        self.assertEqual(reading.document.facts, ())
        self.assertEqual(reading.document.rules, ())
        if reading.accepted:
            self.assertEqual(reading.steps[0].mood, Mood.COMMAND)

    def test_tanwin_does_not_license_removal_of_lexical_alif(self):
        for text in ("ليس الشيء عصًا.", "ليس الشيء عصاً."):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assert_restored(reading, text)
                self.assertNotIn(Atom("عص", ("الشيء",), False), [f.atom for f in reading.document.facts])

    def test_conditional_copula_does_not_guess_a_verb_as_an_individual(self):
        reading = read_arabic("إذا كان يراجع أحمد فإن المحضر محفوظ.")
        self.assertFalse(reading.accepted)
        self.assertEqual(reading.document.rules, ())

    def test_multiple_terminal_vowels_cannot_hide_behind_shadda(self):
        for text in ("سالمَُّ هو نقي.", "الطالبُُّ ناجحٌ.", "الطالبُْ ناجحٌ."):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assertFalse(reading.accepted)
                self.assertEqual(reading.document.facts, ())

    def test_explicit_nominal_control_still_reads_and_restores(self):
        text = "الطالبُ هو ناجحٌ و سعيدٌ.\r\nهل الطالبُ هو سعيدٌ؟"
        reading = read_arabic(text)
        self.assert_restored(reading, text)
        self.assertTrue(reading.accepted)
        self.assertEqual([f.atom for f in reading.document.facts],
                         [Atom("ناجح", ("الطالب",)), Atom("سعيد", ("الطالب",))])
        self.assertEqual([q.atom for q in reading.document.queries], [Atom("سعيد", ("الطالب",))])

    def test_unbound_pronoun_remains_unresolved(self):
        text = "هو ناجح."
        reading = read_arabic(text)
        self.assert_restored(reading, text)
        self.assertFalse(reading.accepted)
        self.assertEqual(reading.document.facts, ())

    def test_invisible_controls_do_not_become_semantic_names(self):
        for text in ("سا\u200dلم هو نقي.", "سالم هو نقي\x00."):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assert_restored(reading, text)
                self.assertFalse(reading.accepted)
                self.assertEqual(reading.document.facts, ())

    def test_unread_trailing_operand_leaves_no_prefix_assertion(self):
        reading = read_arabic("سالم هو نقي و")
        self.assertFalse(reading.accepted)
        self.assertEqual(reading.document.facts, ())

    def test_query_and_wish_content_are_not_asserted(self):
        for text in ("هل سالم هو نقي؟", "ليت سالم هو نقي.", "لعل سالم هو نقي."):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assertEqual(reading.document.facts, ())
                self.assertEqual(reading.document.rules, ())

    def test_numeric_reading_replays_instead_of_trusting_embedded_atoms(self):
        reading = read_arabic("سالم هو نقي.")
        number = int(reading.packet()["number_hex"], 16)
        self.assertEqual(decode_reading_number(number), reading.as_dict())
        forged = copy.deepcopy(reading.as_dict())
        forged["document"]["facts"][0]["atom"]["predicate"] = "مخترع"
        raw = json.dumps(forged, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        with self.assertRaises(NabtError):
            decode_reading_number(int.from_bytes(b"\x01" + raw, "big"))
        with self.assertRaises(NabtError):
            decode_reading_number(True)

    def test_source_exhaustion_is_distinct_from_a_false_linguistic_answer(self):
        with self.assertRaises(NabtError) as caught:
            read_arabic("س" * 65537)
        self.assertEqual(caught.exception.status, "DEFER")


if __name__ == "__main__":
    unittest.main()
