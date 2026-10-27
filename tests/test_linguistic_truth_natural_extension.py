"""Independent scope probes for the source-bound lexical/cue extension.

These examples are not a new blind benchmark. Retrieval of a marked form is
tested independently of admitting it as a grammatical or semantic premise.
No expected answer or caller-created certificate is passed to acquire().
"""
from hashlib import sha256
import unittest
from unittest.mock import patch

from tools.linguistic_truth import acquire
from tools.linguistic_truth.runtime import (
    ROOT, _occurrence_forms, _parse_clause, _tokens,
)


def tokenize(text):
    offsets = [len(text[:i].encode("utf-8")) for i in range(len(text) + 1)]
    return _tokens(text, 0, len(text), offsets)


class RetrievalAndAdmissionSeparation(unittest.TestCase):
    def test_accusative_retrieval_is_not_a_new_prepositional_cue_form(self):
        forms = {"اللفظ": {"اللفظ"}}
        senses = {"اللفظ": {"one": {"sense_id": "one", "forms": {"المعنى الأول"}}}}
        extension = [{"expression": "اللفظ", "form": "لَفْظًا", "normal": "لفظا",
                      "passage_ids": ["fixture-only-no-public-authority"]}]
        token = tokenize("لَفْظًا")[0]
        candidates = _occurrence_forms(token, forms, retrieval_forms=extension)
        self.assertEqual(set(candidates), {"اللفظ"})
        self.assertEqual(candidates["اللفظ"][0]["authority"], "LEXICAL_RETRIEVAL_PROPOSAL")
        self.assertIsNone(_parse_clause(tokenize("أعني بلفظا المعنى الأول"), forms, senses))

    def test_uninstalled_verb_does_not_extend_the_private_parser(self):
        forms = {"اللفظ": {"اللفظ"}}
        senses = {"اللفظ": {"one": {"sense_id": "one", "forms": {"المعنى الأول"}}}}
        self.assertIsNone(_parse_clause(tokenize("أقصد باللفظ المعنى الأول"), forms, senses))


class InstalledNaturalExtension(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "formal/.lake/build/bin/linguisticTruth").exists():
            raise unittest.SkipTest("native linguisticTruth checker not built")

    def run_reader(self, text):
        return acquire(text, profile_id="linguistic")

    def test_observed_ayn_keeps_source_attested_alternatives_without_intent(self):
        text = "ذُكرت عيناً في النص."
        result = self.run_reader(text)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["source"]["sha256"], sha256(text.encode()).hexdigest())
        self.assertTrue(result["native_checked"])
        occurrence = next(o for o in result["occurrences"] if o["expression"] == "العين")
        self.assertEqual(occurrence["span"]["raw_text"], "عيناً")
        candidates = {r["sense_id"] for r in occurrence["candidates"]}
        self.assertTrue({"ayn_eye", "ayn_spring", "ayn_gold"} <= candidates)
        self.assertEqual(occurrence["selected_sense_ids"], [])
        self.assertEqual(occurrence["certified_sense_ids"], [])
        self.assertFalse(occurrence["formal_guard_decided"])
        span = occurrence["span"]
        self.assertEqual(text.encode()[span["start_byte"]:span["end_byte"]].decode(), "عيناً")

    def test_inflected_occurrences_are_distinct_and_keep_retrieval_provenance(self):
        text = "ذُكرت أسداً. ثم ذُكرت عيناً."
        result = self.run_reader(text)
        self.assertEqual({o["expression"] for o in result["occurrences"]}, {"الأسد", "العين"})
        self.assertEqual(len({o["occurrence_id"] for o in result["occurrences"]}), 2)
        self.assertFalse(result["acquired_premises"])
        for occurrence in result["occurrences"]:
            self.assertTrue(occurrence["native_checked"])
            self.assertTrue(any(s.get("passage_ids") for s in occurrence["surface_segmentations"]))

    def test_lexical_candidates_do_not_choose_a_natural_context_sense(self):
        for text in ("لم أر عيناً.", "لو وجدت عيناً لرجعت.", "«أعني بالعين حاسة الرؤية»"):
            with self.subTest(text=text):
                result = self.run_reader(text)
                self.assertTrue(result["occurrences"])
                self.assertFalse(result["acquired_premises"])
                self.assertTrue(all(not o["selected_sense_ids"] and not o["certified_sense_ids"]
                                    for o in result["occurrences"]))
                self.assertFalse(result["world_truth_established"])

    def test_source_backed_intention_verb_uses_native_conditional_guard(self):
        text = "أَقْصِدُ بالأسد الحيوان المفترس."
        result = self.run_reader(text)
        self.assertEqual(result["status"], "COMPLETE")
        occurrence = result["occurrences"][0]
        self.assertTrue(occurrence["native_checked"])
        self.assertEqual(occurrence["selected_sense_ids"], ["asad_animal"])
        self.assertEqual(occurrence["certified_sense_ids"], ["asad_animal"])
        evidence = next(e for e in result["syntax_evidence"]
                        if e["rule"] == "SOURCE_REPLAYED_EXPLICIT_INTENTION_VERB")
        self.assertFalse(evidence["native_acquisition_proof"])
        self.assertTrue(evidence["licenses"][0]["passage_ids"])
        self.assertFalse(result["world_truth_established"])
        self.assertFalse(result["all_arabic_complete"])

    def test_negative_intention_never_becomes_positive_selection(self):
        result = self.run_reader("لا أقصد بالأسد الحيوان المفترس")
        occurrence = result["occurrences"][0]
        self.assertEqual(occurrence["selected_sense_ids"], [])
        self.assertEqual(occurrence["excluded_sense_ids"], ["asad_animal"])
        self.assertEqual(occurrence["certified_sense_ids"], [])
        self.assertTrue(occurrence["native_checked"])

    def test_new_homonym_intention_stays_bound_to_its_own_occurrence(self):
        text = "أقصد بالعين الباصرة. أقصد بالعين الجارية"
        result = self.run_reader(text)
        self.assertEqual(result["status"], "COMPLETE")
        occurrences = result["occurrences"]
        self.assertEqual(len(occurrences), 2)
        self.assertEqual([o["certified_sense_ids"] for o in occurrences],
                         [["ayn_eye"], ["ayn_spring"]])
        self.assertNotEqual(occurrences[0]["occurrence_id"], occurrences[1]["occurrence_id"])
        for occurrence in occurrences:
            self.assertTrue(occurrence["native_checked"])
            self.assertEqual({r["sense_id"] for r in occurrence["candidates"]},
                             {"ayn_eye", "ayn_spring", "ayn_gold"})
            self.assertEqual(text.encode()[occurrence["clause_span"]["start_byte"]:
                                           occurrence["clause_span"]["end_byte"]].decode(),
                             occurrence["clause_span"]["raw_text"])

    def test_same_occurrence_negative_cue_retains_contradiction(self):
        result = self.run_reader("أقصد بالأسد الحيوان المفترس ولا أقصد به الحيوان المفترس")
        self.assertEqual(result["status"], "CONFLICT")
        self.assertTrue(result["occurrences"][0]["signed_conflict"])
        self.assertFalse(result["occurrences"][0]["certified_sense_ids"])

    def test_unreviewed_spelling_and_conjunction_cannot_gain_a_premise(self):
        for text in ("أَقْصَدُ بالأسد الحيوان المفترس", "أقصُد بالأسد الحيوان المفترس",
                     "وأقصد بالأسد الحيوان المفترس", "قصدت بالأسد الحيوان المفترس",
                     "أقصد بأسداً الحيوان المفترس", "أقصد بالأسد الحيوان المعروف",
                     "أقصد بالأسد الحيوان المفترس ربما"):
            with self.subTest(text=text):
                result = self.run_reader(text)
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertFalse(result["acquired_premises"])
                self.assertFalse(any(o["certified_sense_ids"] for o in result["occurrences"]))

    def test_quotation_and_reported_speech_are_not_speaker_intention(self):
        for text in ("«أقصد بالأسد الحيوان المفترس»", "قالت هند: أقصد بالأسد الحيوان المفترس",
                     "ليس صحيحا أن أقصد بالأسد الحيوان المفترس"):
            with self.subTest(text=text):
                result = self.run_reader(text)
                self.assertFalse(result["acquired_premises"])
                self.assertEqual(result["status"], "UNKNOWN")

    def test_native_unavailability_never_promotes_new_source_licenses(self):
        with patch("tools.linguistic_truth.runtime._verify_native", side_effect=OSError("unavailable")):
            result = self.run_reader("أقصد بالأسد الحيوان المفترس")
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertTrue(result["acquired_premises"])
        self.assertFalse(result["native_checked"])
        self.assertFalse(any(o["certified_sense_ids"] for o in result["occurrences"]))


if __name__ == "__main__":
    unittest.main()
