"""Independent orthographic counterexamples and the installed public boundary.

Marked private fixtures test the coverage relation, never furnish authority to
the public reader. Its real inventory is replayed unchanged by public tests.
"""
from hashlib import sha256
import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from tools.linguistic_truth import acquire
from tools.linguistic_truth.runtime import (
    LAW_ID, ROOT, _covers_observed_marks, _orthography_gate, _parse_clause, _tokens,
)


def parse_fixture(text, forms, senses):
    offsets = [len(text[:i].encode("utf-8")) for i in range(len(text) + 1)]
    tokens = _tokens(text, 0, len(text), offsets)
    return tokens, _parse_clause(tokens, forms, senses)


class ObservedMarkCoverage(unittest.TestCase):
    def test_independent_carrier_aligned_examples(self):
        for observed, reviewed, expected in (
                ("ملك", "مَلِك", True),
                ("مَلِك", "مَلِك", True),
                ("ملِك", "مَلِك", True),
                ("مَلِك", "ملك", False),
                ("مُلْك", "مَلِك", False),
                ("المُفْتَرَس", "المُفْتَرِس", False),
                ("الأسدّ", "الأسد", False),
                ("دَّ", "دَّ", True),
                ("رَجُلٌ", "رَجُلُ", False),
                ("ملـك", "ملك", True),
                ("مالك", "ملك", False)):
            with self.subTest(observed=observed, reviewed=reviewed):
                self.assertEqual(_covers_observed_marks(observed, reviewed), expected)

    def test_marked_fixture_is_bound_to_its_sense_not_an_unrelated_alias(self):
        forms = {"اللفظ": {"اللفظ"}}
        senses = {"اللفظ": {"active": {"sense_id": "active", "forms": {"المُفْتَرِس"}},
                            "passive": {"sense_id": "passive", "forms": {"المُفْتَرَس"}}}}
        inventory = {"designations": [{"expression": "اللفظ", "forms": ["اللفظ"]}]}
        text = "أعني باللفظ المُفْتَرَس"
        tokens, parsed = parse_fixture(text, forms, senses)
        self.assertEqual(len(parsed["readings"]), 2)  # retrieval is not admission
        checked, issues = _orthography_gate(parsed, tokens, text.encode(), inventory, senses)
        self.assertEqual(issues, [])
        self.assertEqual([r[0]["sense_id"] for r in checked["readings"]], ["passive"])
        # An unmarked alias never licenses a new visible mark.
        senses["اللفظ"]["passive"]["forms"] = {"المفترس"}
        checked, issues = _orthography_gate(parsed, tokens, text.encode(), inventory, senses)
        self.assertIsNone(checked)
        self.assertTrue(issues)

    def test_joined_waw_keeps_sense_at_the_raw_carrier_after_its_marks(self):
        forms = {"اللفظ": {"اللفظ"}}
        senses = {"اللفظ": {"one": {"sense_id": "one", "forms": {"الأول"}},
                            "two": {"sense_id": "two", "forms": {"الثاني"}}}}
        text = "أعني باللفظ الأول وَالثاني"
        tokens, parsed = parse_fixture(text, forms, senses)
        second = parsed["readings"][0][1]
        self.assertEqual(text.encode()[second["start"]:second["end"]].decode(), "الثاني")
        self.assertEqual(tokens[-1]["text"], "وَالثاني")
        checked, issues = _orthography_gate(parsed, tokens, text.encode(),
            {"designations": [{"expression": "اللفظ", "forms": ["اللفظ"]}]}, senses)
        self.assertIsNone(checked)  # the installed cue has no marked waw reading
        self.assertEqual({issue["role"] for issue in issues}, {"grammar"})


class FoundationInputAdmission(unittest.TestCase):
    def test_law_and_foundation_are_not_caller_authority(self):
        self.assertEqual(LAW_ID, "nabt.linguistic-truth-acquisition.v5")
        with patch("nabt.foundation.require_foundation", side_effect=NabtError("DENIED", "test")):
            with self.assertRaises(NabtError):
                acquire("أعني بالأسد الحيوان المفترس", profile_id="linguistic")

    def test_conflicting_and_orphan_marks_stop_before_source_or_native_work(self):
        for text in ("أَُعني بالأسد الحيوان المفترس", "أعني بالأسدّّ الحيوان المفترس",
                     "َأعني بالأسد الحيوان المفترس", "أعني بالأسد الحيوانََ المفترس"):
            with self.subTest(text=text), patch("tools.linguistic_truth.inventory.build_inventory") as ledger, \
                    patch("tools.linguistic_truth.runtime._verify_native") as native:
                result = acquire(text.encode(), profile_id="linguistic")
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertEqual(result["reason"], "FOUNDATION_SOURCE_INVALID")
                self.assertEqual(result["source"]["raw_text"], text)
                self.assertEqual(result["source"]["sha256"], sha256(text.encode()).hexdigest())
                self.assertFalse(result["intended_sense_acquired"])
                self.assertFalse(result["native_checked"])
                ledger.assert_not_called()
                native.assert_not_called()


class InstalledOrthographicAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "formal/.lake/build/bin/linguisticTruth").exists():
            raise unittest.SkipTest("native linguisticTruth not built")

    def test_unmarked_baseline_still_acquires_from_replayed_inventory(self):
        text = "أعني بالأسد الحيوان المفترس"
        result = acquire(text, profile_id="linguistic")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["native_checked"])
        self.assertEqual(result["occurrences"][0]["supported_use_kinds"], ["literal"])
        self.assertFalse(result["world_truth_established"])

    def test_joined_conjunction_tatweel_does_not_shift_the_raw_sense(self):
        text = "أعني بالقرء الطهر ـوـالحيض"
        result = acquire(text, profile_id="linguistic")
        self.assertEqual(result["status"], "COMPLETE")
        spans = [p["sense_span"]["raw_text"] for p in result["acquired_premises"]]
        self.assertEqual(set(spans), {"الطهر", "الحيض"})
        self.assertEqual(result["source"]["raw_text"], text)

    def test_nonconflicting_but_unreviewed_marks_never_become_used_premises(self):
        for text in (
                "أعني بالأسدّ الحيوان المفترس",
                "أعني بالأسد الحيوان المُفْتَرَس",
                "أعني بالأسد الحيوان الْمُفْتَرِسُ",
                "أَعْنِي بِالْأَسَدُ الْحَيَوَانَ الْمُفْتَرِسَ",
                "أعني بالقرء الطهر وَالحيض",
                "لُا أعني بالأسد الرجل الشجاع بل الحيوان المفترس"):
            with self.subTest(text=text):
                result = acquire(text, profile_id="linguistic")
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertEqual(result["reason"], "UNSUPPORTED_OBSERVED_MARKS")
                self.assertEqual(result["acquired_premises"], [])
                self.assertFalse(result["intended_sense_acquired"])
                self.assertEqual(result["source"]["raw_text"], text)
                self.assertTrue(result["occurrences"])
                self.assertTrue(all(o["candidates"] and not o["certified_sense_ids"]
                                    for o in result["occurrences"]))
                for issue in result["unclassified_spans"][0]["orthography_issues"]:
                    span = issue["span"]
                    self.assertEqual(text.encode()[span["start_byte"]:span["end_byte"]].decode(), span["raw_text"])

    def test_newly_witnessed_la_vowel_preserves_the_existing_negative_correction(self):
        # Previously لَا was intentionally unsupported only because its fatha
        # lacked a reviewed spelling. QAC now witnesses laA; the established
        # whole-cue negative-correction parser supplies polarity independently.
        # This is a local spelling improvement, not a new rule of intention.
        text = "لَا أعني بالأسد الرجل الشجاع بل الحيوان المفترس"
        result = acquire(text, profile_id="linguistic")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["source"]["raw_text"], text)
        self.assertEqual(result["occurrences"][0]["selected_sense_ids"], ["asad_animal"])
        self.assertEqual(result["occurrences"][0]["excluded_sense_ids"], ["asad_brave"])
        self.assertTrue(result["native_checked"])
        self.assertFalse(result["world_truth_established"])
        self.assertFalse(result["all_arabic_complete"])
        derivation = result["qualified_form_derivation"]
        self.assertEqual(derivation["receipt"]["status"], "CHECKED_CONDITIONAL_FORMS")
        self.assertFalse(derivation["native_acquisition_proof"])
        self.assertFalse(derivation["receipt"]["source_interpretation_kernel_proved"])
        self.assertFalse(derivation["receipt"]["intended_sense_established"])
        self.assertFalse(derivation["receipt"]["strict_language_accepted"])
        la = [license_ for item in result["orthography_evidence"] for license_ in item["licenses"]
              if license_["role"] == "grammar" and license_["form"] == "لَا"]
        self.assertEqual(len(la), 1)
        self.assertIn("cue_la", la[0]["passage_ids"])
        self.assertTrue(la[0]["native_form_derivation_checked"])

    def test_new_la_spelling_cannot_be_used_when_its_native_checker_is_absent(self):
        text = "لَا أعني بالأسد الرجل الشجاع بل الحيوان المفترس"
        with patch("tools.linguistic_truth.marked_forms.subprocess.run",
                   side_effect=FileNotFoundError("qualifiedCueLicensing unavailable")) as native:
            result = acquire(text, profile_id="linguistic")
        native.assert_called_once()
        self.assertTrue(native.call_args.args[0][0].endswith("/qualifiedCueLicensing"))
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(result["reason"], "QUALIFIED_NATIVE_UNAVAILABLE")
        self.assertEqual(result["source"]["raw_text"], text)
        self.assertEqual(result["acquired_premises"], [])
        self.assertFalse(result["intended_sense_acquired"])
        self.assertFalse(result["native_checked"])

    def test_profile_hypotheses_cannot_restore_unreviewed_marks(self):
        result = acquire("أعني بالأسد الحيوان المُفْتَرَس")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["acquired_premises"], [])
        self.assertFalse(result["intended_sense_acquired"])
        self.assertTrue(all(not r["conditional_result"]["intended_sense_acquired"]
                            for o in result["occurrences"] for r in o["profile_readings"]))

    def test_unsupported_clause_does_not_erase_a_distinct_valid_clause(self):
        text = "أعني بالأسد الحيوان المفترس. أعني بالقرء الطُهر"
        result = acquire(text, profile_id="linguistic")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "UNSUPPORTED_OBSERVED_MARKS")
        self.assertEqual(len(result["acquired_premises"]), 1)
        self.assertEqual(result["acquired_premises"][0]["sense_id"], "asad_animal")
        self.assertEqual(result["occurrences"][1]["selected_sense_ids"], [])


if __name__ == "__main__":
    unittest.main()
