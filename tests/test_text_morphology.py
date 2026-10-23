"""Behavioral tests for new-source evidence, independent of spelling answers."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nabt.errors import NabtError
from nabt.text_evidence import kind_candidates, receipt_activated
from nabt.text_morphology import (decode_text_morphology, read_text_morphology,
                                  text_morphology_number, verify_text_morphology)


def description(word, body, reading="r1"):
    return f"قراءة «{reading}» للفظ «{word}»:\n{body}"


NOUN = "يدل على معنى مستقل غير مقترن بزمن\nيسلم من شبه الحرف"
GENUS = NOUN + "\nلا يمنع تصوره الشركة\nيدل على ذات دون اعتبار صفة"
QUALITY = NOUN + "\nلا يمنع تصوره الشركة\nيدل على ذات باعتبار صفة"
NO_CAUSES = "\nليس علما\nليس وصفا\nليس آخره ألف التأنيث\nليس على صيغة منتهى الجموع"


class TextMorphologyTests(unittest.TestCase):
    def test_open_noun_sign_without_authored_content_lexicon(self):
        source = "غَيْمٌ رَذَاذٌ صَقِيعٌ دُلْفَةٌ"
        report = read_text_morphology(source)
        self.assertEqual(report["recognition_basis"]["content_word_answer_entries_used"], 0)
        for occurrence in report["occurrences"]:
            with self.subTest(word=occurrence["surface"]):
                self.assertEqual(occurrence["axes"]["kind"]["candidates"], ["noun"])
                self.assertEqual(occurrence["axes"]["kind"]["status"], "LICENSED")
                self.assertEqual(occurrence["axes"]["construction"]["status"], "DEFER")
                self.assertIsNone(occurrence["actual_role"])
                self.assertIsNone(occurrence["actual_case"])
                self.assertIsNone(occurrence["readings"][0]["lexical_link"])

    def test_evidence_retraction_keeps_occurrence_and_reopens_kind(self):
        a = read_text_morphology("غَيْمٌ")["occurrences"][0]
        b = read_text_morphology("غَيْم")["occurrences"][0]
        self.assertEqual(a["axes"]["kind"]["candidates"], ["noun"])
        self.assertEqual(b["axes"]["kind"]["candidates"], ["noun", "particle", "verb"])
        self.assertNotEqual(a["occurrence_id"], b["occurrence_id"])

    def test_all_observation_spans_address_original_bytes(self):
        text = "\tرَجُلاً، صَهٍ\nالْتَقَى «لَمْ يَعْمَلْ»"
        report = read_text_morphology(text)
        raw = text.encode()
        self.assertEqual("".join(s["surface"] for s in report["partition"]), text)
        for occurrence in report["occurrences"]:
            for item in [occurrence, *occurrence["observations"]]:
                span = item["span"]
                selected = raw[span["start"]:span["end"]]
                self.assertEqual(selected.decode(), item["surface"])
                self.assertEqual(sha256(selected).hexdigest(), span["span_sha256"])
        self.assertEqual(len(report["occurrences"]), 3)
        self.assertFalse(report["attachments"])

    def test_imperfect_context_never_supplies_kind_or_role(self):
        report = read_text_morphology("لَمْ يَزْدَهِرْ")
        target = report["occurrences"][1]
        self.assertEqual(target["axes"]["kind"]["status"], "DEFER")
        self.assertEqual(target["readings"][0]["receipts"], [])
        self.assertFalse(report["attachments"][0]["kind_constraint_activated"])
        self.assertFalse(report["attachments"][0]["independent_kind_compatible"])
        self.assertIsNone(target["actual_case"])

    def test_independent_verb_source_makes_candidate_compatible_without_creating_government(self):
        body = "يدل على حدث مقترن بزمن بهيئته\nفعله مضارع\nلا تتصل به نون إناث ولا نون توكيد"
        report = read_text_morphology("لَمْ يَزْدَهِرْ", lexical_text=description("يَزْدَهِرْ", body))
        target = report["occurrences"][1]
        self.assertEqual(target["axes"]["kind"]["candidates"], ["verb"])
        self.assertEqual(target["axes"]["construction"]["candidates"], ["inflected"])
        self.assertTrue(report["attachments"][0]["independent_kind_compatible"])
        self.assertFalse(report["attachments"][0]["kind_constraint_activated"])
        self.assertIsNone(target["actual_case"])

    def test_no_crossing_boundaries_for_attachment(self):
        for separator in ("، ", "\n", "\r", "\u2028", " «قول» ", ". "):
            with self.subTest(separator=separator):
                self.assertFalse(read_text_morphology("لَمْ" + separator + "يَعْمَلْ")["attachments"])

    def test_semantic_axis_requires_separate_lexical_premise(self):
        word = "سَارِمٌ"
        plain = read_text_morphology(word)
        sourced = read_text_morphology(word, lexical_text=description(word, QUALITY))
        self.assertEqual(plain["occurrences"][0]["axes"]["nominal_semantics"]["status"], "DEFER")
        self.assertEqual(sourced["occurrences"][0]["axes"]["nominal_semantics"]["candidates"], ["mushtaq"])
        self.assertFalse(verify_text_morphology(sourced, text=word, lexical_text=None)["valid"])
        self.assertTrue(verify_text_morphology(sourced, text=word)["valid"])
        self.assertFalse(verify_text_morphology(sourced, text=word,
                                              lexical_text=description(word, GENUS))["valid"])

    def test_source_relations_do_not_match_unobserved_vowels(self):
        report = read_text_morphology("سارم", lexical_text=description("سَارِمٌ", QUALITY))
        self.assertEqual(report["unused_lexical_readings"], ["r1"])
        self.assertIsNone(report["occurrences"][0]["readings"][0]["lexical_link"])
        self.assertEqual(report["occurrences"][0]["axes"]["kind"]["status"], "DEFER")

    def test_no_cross_reading_conjunction_of_cause_traits(self):
        word = "سَرَمَانَ"
        lexical = description(word, NOUN + "\nهو علم", "one") + "\n" + description(
            word, NOUN + "\nآخره ألف التأنيث", "two")
        # The unsupported clause remains blocked; a different reading's valid
        # evidence does not silently repair its source.
        report = read_text_morphology(word, lexical_text=lexical)
        branches = report["occurrences"][0]["readings"]
        self.assertEqual(len(branches), 2)
        self.assertNotEqual(branches[0]["reading_id"], branches[1]["reading_id"])
        self.assertTrue(branches[0]["blockers"])
        self.assertFalse(branches[1]["blockers"])

    def test_mixed_applicability_never_becomes_licensed_diptote_class(self):
        word = "مَا"
        lexical = description(word, NOUN + NO_CAUSES, "noun") + "\n" + description(
            word, "يدل على حدث مقترن بزمن بهيئته\nفعله ماض" + NO_CAUSES, "verb")
        report = read_text_morphology(word, lexical_text=lexical)
        axes = report["occurrences"][0]["axes"]
        self.assertEqual(axes["kind"]["status"], "DEFER")
        self.assertEqual(axes["diptote"]["status"], "DEFER")
        self.assertIn("UNRESOLVED_READING_DOMAIN", axes["diptote"]["missing"])

    def test_text_refinement_rechecks_lexical_property_domains(self):
        lexical = description("كِتَابٌ", "يدل على حدث مقترن بزمن\nفعله ماض\nيسلم من شبه الحرف")
        report = read_text_morphology("كِتَابٌ", lexical_text=lexical)
        reading = report["occurrences"][0]["readings"][0]
        self.assertEqual(reading["status"], "CONFLICT")
        self.assertIn("PROPERTY_DOMAIN_MISMATCH", [b["code"] for b in reading["blockers"]])
        self.assertNotEqual(reading["axes"]["construction"]["status"], "LICENSED")

    def test_lexical_context_is_not_transferred_to_new_occurrence(self):
        word = "مَسَاجِدَ"
        source = description(word, NOUN + "\nعلى صيغة منتهى الجموع\nدخلت عليه أل\nهو مضاف")
        report = read_text_morphology(word, lexical_text=source)
        reading = report["occurrences"][0]["readings"][0]
        self.assertFalse({"al", "idhafa"} & {p["property"] for p in reading["linked_properties"]})
        genitive = reading["axes"]["diptote"]["genitive"]
        self.assertFalse(genitive["context_properties_transferred"])
        self.assertFalse(genitive["applied_to_occurrence"])

    def test_invalid_marks_are_input_rejections_not_linguistic_conflicts(self):
        for word in ("كَُتُبٌ", "كٌتُب", "ٌ", "رَجُلٌٌ", "اٌ", "رَجُلاٌ", "اٍ", "اًا"):
            with self.subTest(word=word), self.assertRaises(NabtError) as caught:
                read_text_morphology(word)
            self.assertEqual(caught.exception.status, "REJECT")
        self.assertEqual(read_text_morphology("word")["status"], "DEFER")

    def test_fath_tanwin_retains_both_alif_placements_and_maqsura(self):
        for word in ("رَجُلًا", "رَجُلاً", "فَتًى", "هُدًى", "شَيْئًا"):
            with self.subTest(word=word):
                axis = read_text_morphology(word)["occurrences"][0]["axes"]["kind"]
                self.assertEqual(axis["candidates"], ["noun"])
                self.assertEqual(axis["status"], "LICENSED")

    def test_receipt_and_number_do_not_authorize_modified_analysis(self):
        report = read_text_morphology("غَيْمٌ")
        number = text_morphology_number(report)
        self.assertEqual(decode_text_morphology(number), report)
        changed = deepcopy(report)
        changed["occurrences"][0]["axes"]["construction"].update(status="LICENSED", candidates=["inflected"])
        self.assertFalse(verify_text_morphology(changed)["valid"])
        raw = json.dumps(changed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        with self.assertRaises(NabtError):
            decode_text_morphology(int.from_bytes(b"\x01" + raw, "big"))
        for number in (True, 0, -1):
            with self.subTest(number=number), self.assertRaises(NabtError):
                decode_text_morphology(number)

    def test_receipt_binding_is_distinct_for_repeated_word_and_scope(self):
        report = read_text_morphology("غَيْمٌ غَيْمٌ", scope="one")
        a, b = report["occurrences"]
        self.assertNotEqual(a["readings"][0]["receipts"][0]["receipt_id"],
                            b["readings"][0]["receipts"][0]["receipt_id"])
        self.assertFalse(verify_text_morphology(report, scope="two")["valid"])
        self.assertFalse(verify_text_morphology(report, source_id="other")["valid"])

    def test_cli_verifier_requires_both_external_sources_when_applicable(self):
        report = read_text_morphology("سَارِمٌ", lexical_text=description("سَارِمٌ", QUALITY))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "text.txt").write_text("سَارِمٌ")
            (root / "lexical.txt").write_text(description("سَارِمٌ", QUALITY))
            (root / "report.json").write_text(json.dumps(report, ensure_ascii=False))
            cmd = [sys.executable, "-m", "nabt", "verify-text-morphology", str(root / "report.json"),
                   "--source", str(root / "text.txt")]
            absent = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(absent.returncode, 2, absent.stderr)
            supplied = subprocess.run(cmd + ["--lexical-source", str(root / "lexical.txt")],
                                      capture_output=True, text=True)
            self.assertEqual(supplied.returncode, 0, supplied.stderr)

    def test_code_domains_reject_booleans_and_incomplete_flags(self):
        with self.assertRaises(NabtError):
            kind_candidates((True,))
        with self.assertRaises(NabtError):
            receipt_activated((1, True, True, False, True, True))
        with self.assertRaises(NabtError):
            receipt_activated((True,))


if __name__ == "__main__":
    unittest.main()
