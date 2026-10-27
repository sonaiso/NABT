"""Independent form equations and adversarial scope for the additive bridge.

These development cases do not replace frozen natural-use gold. In particular
the bridge derives reviewed spellings; it does not close source acquisition,
quotation, idafa interpretation in arbitrary prose, or psychological intent.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.linguistic_truth import acquire
from tools.linguistic_truth import marked_forms as marks
from tools.linguistic_truth.runtime import ROOT


class QualifiedReview(unittest.TestCase):
    def test_review_keeps_base_and_replays_every_source_including_compressed(self):
        review = marks._replay_qualified_review(ROOT)
        self.assertEqual(sha256((ROOT / marks.REVIEW_PATH).read_bytes()).hexdigest(),
                         marks.REVIEW_SHA256)
        self.assertEqual(len(review["lexemes"]), 7)
        self.assertTrue(any(source.get("encoding") == "gzip" for source in review["sources"]))
        self.assertEqual(review["base_review"]["sha256"], marks.REVIEW_SHA256)
        self.assertIn("cue_fayd_basira", {row["id"] for row in review["passages"]})

    def test_role_gender_number_and_dependent_are_real_requirements(self):
        original = marks._replay_qualified_review(ROOT)
        changes = (("basira", "gender", "masculine", "العين الباصرة"),
                   ("basira", "number", "dual", "العين الباصرة"),
                   ("ayn_construct", "licensed_dependents", [], "عين الماء"),
                   ("ayn_construct", "inflection", "regular_definite", "عين الماء"),
                   ("maa", "number", "plural", "عين الماء"),
                   ("ayn_definite", "number", "dual", "العين"))
        for id_, field, value, absent in changes:
            with self.subTest(id=id_, field=field):
                review = deepcopy(original)
                next(row for row in review["lexemes"] if row["id"] == id_)[field] = value
                self.assertNotIn(absent, {row["normal"] for row in marks._qualified_table(review)})
        review = deepcopy(original)
        review["effective_rules"] = [r for r in review["effective_rules"] if r["id"] != "idafa_genitive"]
        self.assertNotIn("عين الماء", {row["normal"] for row in marks._qualified_table(review)})

    def test_changed_or_withdrawn_source_blocks_review(self):
        new = marks._replay_qualified_review(ROOT)
        base = marks._load_review(ROOT)
        paths = {marks.REVIEW_PATH, marks.QUALIFIED_REVIEW_PATH,
                 *(Path(row["path"]) for row in new["sources"] + base["sources"])}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in paths:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, root / path)
            marks._replay_qualified_review(root)
            source = root / next(row["path"] for row in new["sources"] if row.get("encoding") == "gzip")
            source.write_bytes(source.read_bytes() + b"x")
            with self.assertRaisesRegex(ValueError, "QUALIFIED_SOURCE_CHANGED"):
                marks._replay_qualified_review(root)
            source.unlink()
            with self.assertRaises(OSError):
                marks._replay_qualified_review(root)


class QualifiedNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = ROOT / "formal/.lake/build/bin/qualifiedCueLicensing"
        if not cls.executable.is_file():
            raise unittest.SkipTest("native qualifiedCueLicensing not built")

    def test_native_table_matches_independently_written_surface_equations(self):
        review = marks._load_qualified_review(ROOT)
        forms = {(r["normal"], r["role"], r["form"], r["next_requirement"])
                 for r in review["qualified_forms"]}
        self.assertEqual(forms, {
            ("العين", "expression", "بِالْعَيْنِ", "any"),
            ("العين الباصرة", "sense", "الْعَيْنَ الْبَاصِرَةَ", "any"),
            ("عين الماء", "sense", "عَيْنَ الْمَاءِ", "any"),
            ("لا", "grammar", "لَا", "any"),
            ("بل", "grammar", "بَلْ", "any"),
            ("بل", "grammar", "بَلِ", "definite_wasl"),
        })
        for row in review["qualified_forms"]:
            self.assertTrue(row["native_form_derivation_checked"])
            self.assertFalse(row["native_acquisition_proof"])
            self.assertFalse(row["source_interpretation_kernel_proved"])
            self.assertEqual(row["native_executable_sha256"], sha256(self.executable.read_bytes()).hexdigest())

    def test_native_api_does_not_accept_a_caller_ledger_or_status(self):
        for payload in ({"review_sha256": "0" * 64},
                        {"review_sha256": marks.QUALIFIED_REVIEW_SHA256, "forms": []},
                        {"review_sha256": marks.QUALIFIED_REVIEW_SHA256, "verified": True},
                        {"review_sha256": False}):
            with self.subTest(payload=payload):
                done = subprocess.run([str(self.executable)], input=json.dumps(payload) + "\n",
                                      text=True, capture_output=True, check=True)
                self.assertEqual(json.loads(done.stdout)["status"], "INVALID_INPUT")

    def test_entire_native_receipt_and_boolean_types_are_checked(self):
        original = marks._load_qualified_review(ROOT)["native_derivation_receipt"]
        mutations = []
        for key, value in (("strict_language_accepted", 0), ("source_interpretation_kernel_proved", True),
                           ("review_sha256", "0" * 64), ("status", "SUPPORTED"), ("forms", [])):
            bad = deepcopy(original)
            bad[key] = value
            mutations.append(json.dumps(bad, ensure_ascii=False))
        bad = deepcopy(original)
        bad["forms"][0]["form"] = "بِالْعِيْنِ"
        duplicate_status = '{"status":"FAILED",' + json.dumps(original, ensure_ascii=False)[1:]
        # Every field is otherwise valid and the last status is correct: the
        # ordinary lossy decoder would erase the contradictory first value.
        self.assertEqual(json.loads(duplicate_status), original)
        mutations.extend((json.dumps(bad, ensure_ascii=False),
                          duplicate_status,
                          '{"untrusted":NaN}'))
        for stdout in mutations:
            with self.subTest(stdout=stdout[:80]):
                with patch.object(marks.subprocess, "run", return_value=SimpleNamespace(
                        returncode=0, stdout=stdout, stderr="")):
                    with self.assertRaises(marks._QualifiedCueVerificationError):
                        marks._load_qualified_review(ROOT)

    def test_resource_receipt_is_distinct_even_on_nonzero_exit(self):
        with patch.object(marks.subprocess, "run", return_value=SimpleNamespace(
                returncode=7, stdout='{"status":"RESOURCE_LIMIT"}', stderr="budget")):
            with self.assertRaises(marks._QualifiedCueResourceError):
                marks._load_qualified_review(ROOT)

    def test_native_binary_must_not_change_during_the_call(self):
        review = marks._replay_qualified_review(ROOT)
        receipt = marks._load_qualified_review(ROOT)["native_derivation_receipt"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "formal/.lake/build/bin/qualifiedCueLicensing"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"test-only binary identity before")

            def changed(*args, **kwargs):
                executable.write_bytes(b"test-only binary identity after")
                return SimpleNamespace(returncode=0, stdout=json.dumps(receipt), stderr="")

            with patch.object(marks, "_replay_qualified_review", return_value=review), \
                    patch.object(marks.subprocess, "run", side_effect=changed):
                with self.assertRaisesRegex(marks._QualifiedCueVerificationError,
                                            "QUALIFIED_NATIVE_CHANGED_DURING_EXECUTION"):
                    marks._load_qualified_review(root)
        with patch.object(marks.subprocess, "run", side_effect=subprocess.TimeoutExpired("native", 10)):
            with self.assertRaises(marks._QualifiedCueResourceError):
                marks._load_qualified_review(ROOT)

    def test_liaison_requires_the_following_definite_wasl(self):
        review = marks._load_qualified_review(ROOT)
        for following in (None, "عين", "ألعين", "إلعين"):
            self.assertEqual([r["form"] for r in marks._reviewed_forms(
                review, "بل", "grammar", following=following)], ["بَلْ"])
        self.assertEqual({r["form"] for r in marks._reviewed_forms(
            review, "بل", "grammar", following="العين")}, {"بَلْ", "بَلِ"})


class QualifiedCueAcquisition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ("qualifiedCueLicensing", "linguisticTruth"):
            if not (ROOT / "formal/.lake/build/bin" / name).is_file():
                raise unittest.SkipTest("native checkers not built")

    def acquire(self, text, **kwargs):
        return acquire(text, profile_id="linguistic", **kwargs)

    def test_feminine_agreement_and_construct_case_are_licensed(self):
        for cue in ("أَعْنِي", "أُرِيدُ", "أَقْصِدُ"):
            for tail, expected in (("الْعَيْنَ الْبَاصِرَةَ", "ayn_eye"),
                                   ("عَيْنَ الْمَاءِ", "ayn_spring")):
                text = cue + " بِالْعَيْنِ " + tail
                with self.subTest(text=text):
                    result = self.acquire(text, source_id="study", context="utterance:local")
                    self.assertEqual(result["status"], "COMPLETE")
                    self.assertEqual(result["source"]["sha256"], sha256(text.encode()).hexdigest())
                    self.assertEqual(result["occurrences"][0]["selected_sense_ids"], [expected])
                    self.assertTrue(result["native_checked"])
                    self.assertFalse(result["world_truth_established"])
                    self.assertFalse(result["all_arabic_complete"])
                    self.assertFalse(result["qualified_form_derivation"]["native_acquisition_proof"])
                    # The noun in the explanatory tail is not the governed
                    # metalinguistic occurrence and inherits no intention.
                    for occurrence in result["occurrences"][1:]:
                        self.assertEqual(occurrence["selected_sense_ids"], [])

    def test_negative_use_does_not_choose_an_unmentioned_alternative(self):
        result = self.acquire("لَا أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["occurrences"][0]["selected_sense_ids"], [])
        self.assertEqual(result["occurrences"][0]["excluded_sense_ids"], ["ayn_spring"])

    def test_single_negative_correction_and_liaison_are_separate(self):
        result = self.acquire("لَا أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ بَلِ الْعَيْنَ الْبَاصِرَةَ")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["occurrences"][0]["selected_sense_ids"], ["ayn_eye"])
        self.assertEqual(result["occurrences"][0]["excluded_sense_ids"], ["ayn_spring"])
        wrong = self.acquire("لَا أَعْنِي بِالْعَيْنِ الْعَيْنَ الْبَاصِرَةَ بَلِ عَيْنَ الْمَاءِ")
        self.assertEqual(wrong["status"], "UNKNOWN")
        self.assertEqual(wrong["acquired_premises"], [])

    def test_contrary_vowels_article_and_adjective_gender_are_not_erased(self):
        bad = (
            "أَعْنِي بِالْعَيْنَ عَيْنَ الْمَاءِ",
            "أَعْنِي بِالْعِيْنِ عَيْنَ الْمَاءِ",
            "أَعْنِي بِالْعَيْنِ عَيْنُ الْمَاءِ",
            "أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءَ",
            "أَعْنِي بِالْعَيْنِ الْعَيْنَ الْمَاءِ",
            "أَعْنِي بِالْعَيْنِ عَيْنًا الْمَاءِ",
            "أَعْنِي بِالْعَيْنِ الْعَيْنَ الْبَاصِرِ",
            "أَعْنِي بِالْعَيْنِ الْعَيْنَ الْبَاصَرَةَ",
            "أَعْنِي بِالْعَيْنِ الْعَيْنَ الْبَاصِرَّةَ",
        )
        for text in bad:
            with self.subTest(text=text):
                result = self.acquire(text)
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertEqual(result["acquired_premises"], [])

    def test_quote_hypothesis_unfinished_tail_and_natural_use_remain_outside(self):
        clause = "أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ"
        for text in ("قال: «" + clause + "»", "إن " + clause, "ليس صحيحًا أني " + clause,
                     clause + " ربما", "رأيت عين الماء"):
            with self.subTest(text=text):
                result = self.acquire(text)
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertEqual(result["acquired_premises"], [])

    def test_occurrence_and_context_identity_do_not_leak(self):
        text = "أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ. أُرِيدُ بِالْعَيْنِ الْعَيْنَ الْبَاصِرَةَ."
        for context in ("speaker:a/utterance:1", "speaker:b/utterance:2"):
            result = self.acquire(text, context=context)
            heads = [o for o in result["occurrences"] if o["span"]["raw_text"] == "بِالْعَيْنِ"]
            self.assertEqual([o["selected_sense_ids"] for o in heads], [["ayn_spring"], ["ayn_eye"]])
            self.assertEqual(len({o["span"]["start_byte"] for o in heads}), 2)
            self.assertTrue(all(o["frame"]["occurrence"]["context"] == context for o in heads))

    def test_native_source_and_resource_failures_cannot_fall_back_to_stripping(self):
        text = "أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ"
        failures = ((marks._QualifiedCueVerificationError("lost"), "VERIFICATION_UNAVAILABLE"),
                    (marks._QualifiedCueResourceError("budget"), "RESOURCE_EXHAUSTED"),
                    (ValueError("changed source"), "SOURCE_UNAVAILABLE"))
        for failure, expected in failures:
            with self.subTest(expected=expected):
                with patch.object(marks, "_load_qualified_review", side_effect=failure):
                    result = self.acquire(text)
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["acquired_premises"], [])
                self.assertFalse(result["native_checked"])


if __name__ == "__main__":
    unittest.main()
