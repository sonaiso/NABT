"""Adversarial scope of the reviewed vocalization and inflection bridge.

These are authored development cases, not a blind accuracy denominator. The
historical 44-case benchmark and its expected labels remain unchanged.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.linguistic_truth import AcquisitionBudget, acquire
from tools.linguistic_truth.marked_forms import (
    LAW_ID, REVIEW_PATH, _load_review, _reviewed_forms,
)
from tools.linguistic_truth.runtime import ROOT


class ReviewReplay(unittest.TestCase):
    def test_every_lexeme_and_rule_is_bound_to_source_passages(self):
        review = _load_review(ROOT)
        passage_ids = {row["id"] for row in review["passages"]}
        for row in review["lexemes"] + review["rules"]:
            self.assertTrue(row["passage_ids"])
            self.assertLessEqual(set(row["passage_ids"]), passage_ids)

    def test_source_withdrawal_and_changed_bytes_cannot_grant_forms(self):
        review = _load_review(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [REVIEW_PATH, *(Path(row["path"]) for row in review["sources"])]
            for path in paths:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, root / path)
            self.assertEqual(_load_review(root), review)
            source = root / review["sources"][0]["path"]
            original = source.read_bytes()
            source.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "MARK_SOURCE_CHANGED"):
                _load_review(root)
            source.unlink()
            with self.assertRaises(OSError):
                _load_review(root)

    def test_missing_role_rule_does_not_fall_back_to_a_lexical_ending(self):
        review = deepcopy(_load_review(ROOT))
        review["rules"] = [row for row in review["rules"] if row["id"] != "regular_genitive"]
        self.assertEqual(_reviewed_forms(review, "الأسد", "expression"), [])
        self.assertEqual(_reviewed_forms(review, "القرء", "expression"), [])
        self.assertEqual(_reviewed_forms(review, "أسد", "expression"), [])
        self.assertEqual(_reviewed_forms(review, "الحيوان المجهول", "sense"), [])


class ReviewedCueAcquisition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "formal/.lake/build/bin/linguisticTruth").is_file():
            raise unittest.SkipTest("native linguisticTruth not built")

    def acquire(self, text, **kwargs):
        return acquire(text, profile_id="linguistic", **kwargs)

    def test_two_attested_verbs_and_partial_vocalization_retain_exact_source(self):
        for cue in ("أَعْنِي", "أُرِيدُ"):
            for head in ("بِالأَسَدِ", "بِالْأَسَدِ", "بالأسد"):
                text = cue + " " + head + " الْحَيَوَانَ الْمُفْتَرِسَ."
                with self.subTest(text=text):
                    report = self.acquire(text)
                    self.assertEqual(report["status"], "COMPLETE")
                    self.assertEqual(report["source"]["raw_text"], text)
                    self.assertEqual(report["source"]["sha256"], sha256(text.encode()).hexdigest())
                    self.assertEqual(report["occurrences"][0]["selected_sense_ids"], ["asad_animal"])
                    self.assertTrue(report["native_checked"])
                    self.assertFalse(report["world_truth_established"])
                    self.assertFalse(report["all_arabic_complete"])
                    evidence = report["orthography_evidence"][0]
                    self.assertIs(evidence["native_acquisition_proof"], False)
                    for license_ in evidence["licenses"]:
                        self.assertEqual(license_["law_id"], LAW_ID)
                        self.assertTrue(license_["passage_ids"])
                        span = license_["span"]
                        self.assertEqual(text.encode()[span["start_byte"]:span["end_byte"]].decode(), span["raw_text"])

    def test_solar_article_and_three_attested_shujaa_vowels_are_not_collapsed(self):
        for adjective in ("الشَّجَاعَ", "الشِّجَاعَ", "الشُّجَاعَ"):
            with self.subTest(adjective=adjective):
                text = "أُرِيدُ بِالْأَسَدِ الرَّجُلَ " + adjective + " لا الْحَيَوَانَ الْمُفْتَرِسَ"
                report = self.acquire(text)
                self.assertEqual(report["status"], "COMPLETE")
                self.assertEqual(report["occurrences"][0]["supported_use_kinds"], ["figurative"])
                forms = {license_["form"] for item in report["orthography_evidence"] for license_ in item["licenses"]}
                self.assertIn("الرَّجُلَ " + adjective, forms)
                self.assertEqual(sum(form.startswith("الرَّجُلَ ") for form in forms), 1)

    def test_missing_shin_vowel_retains_all_three_reviewed_forms(self):
        report = self.acquire("أَعْنِي بالأسد الرَّجُلَ الشّجَاعَ")
        self.assertEqual(report["status"], "COMPLETE")
        forms = {license_["form"] for item in report["orthography_evidence"]
                 for license_ in item["licenses"] if license_["role"] == "sense"}
        self.assertEqual(forms, {"الرَّجُلَ الشَّجَاعَ", "الرَّجُلَ الشِّجَاعَ", "الرَّجُلَ الشُّجَاعَ"})
        # Known figurative intention alone still does not discharge the native
        # calculus's exclusion premise for a figurative classification.
        self.assertEqual(report["occurrences"][0]["certified_sense_ids"], [])

    def test_contrary_role_vowels_and_active_passive_cannot_be_erased(self):
        template = "أَعْنِي بِالْأَسَدِ الْحَيَوَانَ الْمُفْتَرِسَ"
        changes = (("بِالْأَسَدِ", "بَالْأَسَدِ"), ("بِالْأَسَدِ", "بِالْأَسَدُ"),
                   ("الْحَيَوَانَ", "الْحَيَوَانُ"), ("الْمُفْتَرِسَ", "الْمُفْتَرِسِ"),
                   ("الْمُفْتَرِسَ", "الْمُفْتَرَسَ"), ("الْمُفْتَرِسَ", "الْمُفْتَرِّسَ"),
                   ("أَعْنِي", "أُعْنِي"), ("أَعْنِي", "أَعْنِّي"))
        for old, new in changes:
            with self.subTest(change=(old, new)):
                report = self.acquire(template.replace(old, new))
                self.assertEqual(report["status"], "UNKNOWN")
                self.assertEqual(report["reason"], "UNSUPPORTED_OBSERVED_MARKS")
                self.assertEqual(report["acquired_premises"], [])
                self.assertFalse(report["intended_sense_acquired"])

    def test_quoted_conditional_and_wrong_preposition_cues_are_not_promoted(self):
        clause = "أَعْنِي بِالْأَسَدِ الْحَيَوَانَ الْمُفْتَرِسَ"
        for text in ("قال: «" + clause + "»", "إن " + clause,
                     clause.replace("بِالْأَسَدِ", "لِلْأَسَدِ"), clause + " ربما"):
            with self.subTest(text=text):
                report = self.acquire(text)
                self.assertEqual(report["status"], "UNKNOWN")
                self.assertEqual(report["acquired_premises"], [])

    def test_negation_and_signed_conflict_remain_distinct(self):
        clause = "أَعْنِي بِالْأَسَدِ الْحَيَوَانَ الْمُفْتَرِسَ"
        negative = self.acquire("لا " + clause)
        self.assertEqual(negative["occurrences"][0]["selected_sense_ids"], [])
        self.assertEqual(negative["occurrences"][0]["excluded_sense_ids"], ["asad_animal"])
        conflict = self.acquire(clause + " لا الْحَيَوَانَ الْمُفْتَرِسَ")
        self.assertEqual(conflict["status"], "CONFLICT")
        self.assertEqual(conflict["occurrences"][0]["certified_sense_ids"], [])

    def test_unknown_convention_retains_hypotheses(self):
        report = acquire("أَعْنِي بِالْأَسَدِ الْحَيَوَانَ الْمُفْتَرِسَ")
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertEqual(report["reason"], "CONVENTION_PROFILE_UNESTABLISHED")
        self.assertEqual(report["occurrences"][0]["certified_sense_ids"], [])

    def test_review_failure_never_degrades_to_mark_stripping(self):
        with patch("tools.linguistic_truth.marked_forms._load_review", side_effect=ValueError("MARK_SOURCE_CHANGED")):
            report = self.acquire("أَعْنِي بِالْأَسَدِ الْحَيَوَانَ الْمُفْتَرِسَ")
        self.assertEqual(report["status"], "SOURCE_UNAVAILABLE")
        self.assertEqual(report["acquired_premises"], [])
        self.assertFalse(report["native_checked"])

    def test_budget_and_uncovered_forms_remain_explicit(self):
        text = "أَعْنِي بِالْأَسَدِ الْحَيَوَانَ الْمُفْتَرِسَ"
        result = self.acquire(text, budget=AcquisitionBudget(max_occurrences=0))
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(result["acquisition_scan_complete"])
        result = self.acquire("أعني بالقرء الطُهْرَ")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["intended_sense_acquired"])


if __name__ == "__main__":
    unittest.main()
