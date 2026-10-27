"""Versioned correction reading, real native execution and adverse scopes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.linguistic_truth import acquire
from tools.linguistic_truth.correction import CITATION, replay_correction_source
from tools.linguistic_truth.runtime import ROOT, _parse_clause, _tokens


class CorrectionSyntaxTests(unittest.TestCase):
    forms = {"اللفظ": {"اللفظ"}}
    senses = {"اللفظ": {"a": {"sense_id": "a", "forms": {"الأول"}},
                         "b": {"sense_id": "b", "forms": {"الثاني"}}}}

    def parse(self, text):
        offsets = [len(text[:i].encode()) for i in range(len(text) + 1)]
        return _parse_clause(_tokens(text, 0, len(text), offsets), self.forms, self.senses)

    def test_negative_correction_preserves_signed_exact_spans(self):
        text = "لَا أُرِيدُ بِاللَّفْظِ الأَوَّلَ بَلِ الثَّانِيَ"
        result = self.parse(text)
        self.assertTrue(result["negative_correction"])
        self.assertEqual([(x["sense_id"], x["positive"]) for x in result["readings"][0]],
                         [("a", False), ("b", True)])
        self.assertEqual([text.encode()[x["start"]:x["end"]].decode() for x in result["readings"][0]],
                         ["الأَوَّلَ", "الثَّانِيَ"])

    def test_no_ellipsis_positive_correction_or_chained_scope(self):
        for text in ("أعني باللفظ الأول بل الثاني", "لا أعني باللفظ الأول بل",
                     "لا أعني باللفظ بل الثاني", "لا أعني باللفظ الأول بل الثاني بل الأول",
                     "لا أعني باللفظ الأول والثاني بل الثاني", "لا أعني باللفظ الأول بل الثاني ربما"):
            with self.subTest(text=text):
                self.assertIsNone(self.parse(text))

    def test_correction_does_not_split_the_whole_clause_budget(self):
        text = "لا أعني باللفظ " + "الأول " * 130 + "بل " + "الثاني " * 130
        with self.assertRaises(OverflowError):
            self.parse(text)

    def test_primary_source_replays_and_altered_source_fails(self):
        self.assertEqual(replay_correction_source(ROOT), CITATION)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / CITATION["path"]
            source.parent.mkdir(parents=True)
            source.write_text(CITATION["quotation"])
            with self.assertRaises(ValueError):
                replay_correction_source(directory)


class CorrectionNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / 'formal/.lake/build/bin/linguisticTruth').exists():
            raise unittest.SkipTest("native linguisticTruth not built")

    def check(self, text):
        return acquire(text, profile_id="linguistic")

    def test_native_conditional_figurative_and_reverse_readings(self):
        for denied, affirmed, kind in (("الحيوان المفترس", "الرجل الشجاع", "figurative"),
                                       ("الرجل الشجاع", "الحيوان المفترس", "literal")):
            result = self.check(f"لا أعني بالأسد {denied} بل {affirmed}")
            self.assertEqual(result["status"], "COMPLETE")
            item = result["occurrences"][0]
            self.assertTrue(item["native_checked"])
            self.assertEqual(item["supported_use_kinds"], [kind])
            self.assertEqual(len(item["certified_sense_ids"]), 1)
            self.assertEqual(result["syntax_evidence"][0]["citation"], CITATION)
            self.assertFalse(result["all_arabic_complete"])
            self.assertFalse(result["world_truth_established"])

    def test_same_sense_correction_is_conflict_not_proof(self):
        result = self.check("لا أعني بالأسد الحيوان المفترس بل الحيوان المفترس")
        self.assertEqual(result["status"], "CONFLICT")
        self.assertTrue(result["occurrences"][0]["signed_conflict"])
        self.assertEqual(result["occurrences"][0]["certified_sense_ids"], [])

    def test_quote_reporting_and_unknown_sense_never_become_certificates(self):
        for text in ('«لا أعني بالأسد الحيوان المفترس بل الرجل الشجاع»',
                     'قال زيد: لا أعني بالأسد الحيوان المفترس بل الرجل الشجاع',
                     'لا أعني بالأسد الحيوان المفترس بل المجهول'):
            result = self.check(text)
            self.assertFalse(any(o["certified_sense_ids"] for o in result["occurrences"]))
            self.assertNotIn("syntax_evidence", result)

    def test_missing_correction_source_fails_closed(self):
        with patch('tools.linguistic_truth.correction.replay_correction_source', side_effect=OSError):
            result = self.check("لا أعني بالأسد الحيوان المفترس بل الرجل الشجاع")
        self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
        self.assertFalse(result["native_checked"])
        self.assertFalse(result["occurrences"])


if __name__ == '__main__':
    unittest.main()
