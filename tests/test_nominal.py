"""Public-boundary counterexamples, source withdrawal, and CLI composition."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nabt.counting import (count_source_units, read_count_phrase,
                           verify_count_phrase, verify_source_count)
from nabt.errors import NabtError
from nabt.nominal import (read_nominal, read_nominal_facts, verify_nominal,
                          verify_nominal_facts, nominal_number, decode_nominal)

ROOT = Path(__file__).resolve().parents[1]
ORIGINS = '''قراءة «plural» للفظ «رجال»:
هو اسم.
هو مذكر.
هو جمع بتغيير بناء مفرده.
مفرده القراءة «single».
قراءة «single» للفظ «رجل»:
هو اسم.
هو مذكر.
يدل على واحد.
'''


class NominalSourceBoundaries(unittest.TestCase):
    def test_raw_endings_do_not_answer_nominal_axes(self):
        report = read_nominal("عرفات زيتون شمس هند وجدان أبيات قضاة")
        for occurrence in report["occurrences"]:
            row = occurrence["readings"][0]
            self.assertFalse(row["receipt"]["activated"])
            self.assertEqual(row["qualified_profile_codes"], [])
            self.assertTrue(all(axis["status"] == "DEFER" for axis in row["axes"].values()))
            self.assertIsNone(row["grammatical_nun_type"])
            self.assertIsNone(row["actual_case"])

    def test_tanwin_does_not_enter_this_nominal_law_without_a_witness(self):
        row = read_nominal("محمدٌ") ["occurrences"][0]["readings"][0]
        self.assertEqual(row["kind"]["status"], "DEFER")
        self.assertEqual(row["axes"]["definiteness"]["status"], "DEFER")
        self.assertIn("terminal_tanwin", [o["type"] for o in row["observations"]])

    def test_homographic_pronoun_does_not_override_independent_verb_reading(self):
        text = 'قراءة «verb» للفظ «هم»:\nهو فعل.'
        readings = read_nominal("هم", lexical_text=text)["occurrences"][0]["readings"]
        self.assertEqual(len(readings), 2)
        lexical = next(r for r in readings if r["lexical_reading_id"] == "verb")
        pronoun = next(r for r in readings if r["pronoun_candidates"])
        self.assertEqual(lexical["kind"]["candidates"], ["verb"])
        self.assertNotEqual(lexical["status"], "CONFLICT")
        self.assertEqual(pronoun["reading_basis"], "CANDIDATE_PRONOUN_READING")
        self.assertFalse(pronoun["exhaustive_over_arabic_homographs"])

    def test_masculine_noun_with_alif_taa_plural_remains_possible(self):
        source = 'قراءة «names» للفظ «طلحات»:\nهو اسم.\nهو مذكر.\nهو جمع بألف وتاء زائدتين.'
        row = read_nominal_facts(source)["readings"][0]
        self.assertEqual(row["axes"]["gender"]["candidates"], ["masculine"])
        self.assertEqual(row["axes"]["form"]["candidates"], ["sound_feminine_plural"])
        self.assertEqual(row["axes"]["definiteness"]["status"], "DEFER")

    def test_unknown_clause_blocks_the_reading(self):
        source = ORIGINS + "هذه عبارة خارج اللغة المحددة."
        result = read_nominal_facts(source)
        self.assertTrue(result["readings"][1]["blocked"])
        self.assertEqual(result["readings"][0]["singular_links"][0]["status"], "DEFER")

    def test_origin_cycle_never_licenses_a_link(self):
        source = ('قراءة «a» للفظ «أول»:\nهو اسم.\nهو مذكر.\nيدل على واحد.\nمفرده القراءة «b».\n'
                  'قراءة «b» للفظ «ثان»:\nهو اسم.\nهو مذكر.\nيدل على واحد.\nمفرده القراءة «a».')
        for row in read_nominal_facts(source)["readings"]:
            self.assertIn("CYCLIC_ORIGIN_LINK", row["singular_links"][0]["missing"])

    def test_manqus_requires_all_five_premises(self):
        first = 'قراءة «n» للفظ «قاضي»:\nهو اسم.\nهو معرب.\nآخره ياء لازمة.\nما قبل الياء مكسور.'
        self.assertEqual(read_nominal_facts(first)["readings"][0]["manqus"]["candidates"], [False, True])
        complete = first + '\nياؤه الأخيرة غير مشددة.'
        self.assertEqual(read_nominal_facts(complete)["readings"][0]["manqus"]["candidates"], [True])
        contradictory = complete.replace("قاضي", "كرسيّ")
        self.assertEqual(read_nominal_facts(contradictory)["status"], "CONFLICT")

    def test_supplied_root_and_formal_root_candidate_stay_separate(self):
        report = read_nominal("وَقَيَ قَالَ")
        first, second = report["occurrences"]
        self.assertTrue(any(c["root"] == "وقي" and c["class"] == "lafif_mafruq"
                            for c in first["weak_root_candidates"]))
        self.assertTrue(all(c["status"] == "CANDIDATE" and not c["attested_root"]
                            for c in first["weak_root_candidates"]))
        self.assertFalse(any(c["root"] == "قول" for c in second["weak_root_candidates"]))
        self.assertEqual(first["readings"][0]["manqus"]["candidates"], [False, True])

    def test_source_withdrawal_and_rebinding_fail_replay(self):
        report = read_nominal("رجال", lexical_text=ORIGINS)
        self.assertTrue(verify_nominal(report)["valid"])
        for options in ({"lexical_text": None}, {"scope": "elsewhere"},
                        {"source_id": "other"}, {"lexical_source_id": "other"}, {"text": "رجال رجال"}):
            self.assertFalse(verify_nominal(report, **options)["valid"])
        for path in ("receipt", "identity"):
            forged = deepcopy(report)
            forged["occurrences"][0]["readings"][0][path]["forged"] = True
            self.assertFalse(verify_nominal(forged)["valid"])

    def test_canonical_numeric_encoding_is_replay_bound(self):
        report = read_nominal("هُنَّ")
        self.assertEqual(decode_nominal(nominal_number(report)), report)
        with self.assertRaises(NabtError):
            decode_nominal(True)
        self.assertFalse(verify_nominal_facts({"status": "READ"})["valid"])


class CountingBoundaries(unittest.TestCase):
    def test_source_count_retains_occurrences_mentions_and_byte_spans(self):
        source = "كتب كتب «كتب» 3 Latin"
        result = count_source_units(source)
        self.assertEqual(result["count"], 3)
        self.assertEqual(len({u["occurrence_id"] for u in result["units"]}), 3)
        self.assertEqual([u["reading_context"] for u in result["units"]], ["UNQUOTED", "UNQUOTED", "MENTION"])
        self.assertIsNone(result["world_cardinality"])
        for row in result["units"]:
            span = row["span"]
            part = source.encode()[span["start"]:span["end"]]
            self.assertEqual(part.decode(), row["surface"])
            self.assertEqual(sha256(part).hexdigest(), span["span_sha256"])
        self.assertTrue(verify_source_count(result)["valid"])
        forged = deepcopy(result)
        forged["count"] = 2
        self.assertFalse(verify_source_count(forged)["valid"])

    def test_digits_do_not_supply_numeral_gender(self):
        for text in ("3 رجال", "٣ رجال", "\n3 رجال\n"):
            report = read_count_phrase(text, lexical_text=ORIGINS)
            row = report["alternatives"][0]
            self.assertEqual(report["numeral"]["value"], 3)
            self.assertEqual(row["checks"]["unit_gender"]["status"], "NOT_OBSERVED")
            self.assertEqual(row["rule"]["unit_gender"], "feminine")
            self.assertEqual(row["checks"]["counted_case"]["status"], "NOT_OBSERVED")
            self.assertIsNone(report["actual_case"])

    def test_closed_word_sequence_checks_gender_without_case_authority(self):
        good = read_count_phrase("ثلاثة رجال", lexical_text=ORIGINS)
        bad = read_count_phrase("ثلاث رجال", lexical_text=ORIGINS)
        self.assertEqual(good["alternatives"][0]["checks"]["unit_gender"]["status"], "MATCH")
        self.assertEqual(bad["alternatives"][0]["checks"]["unit_gender"]["status"], "CONFLICT")
        self.assertEqual(good["status"], "DEFER")
        self.assertTrue(verify_count_phrase(good)["valid"])
        self.assertFalse(verify_count_phrase(good, lexical_text=None)["valid"])

    def test_compound_rules_use_singular_gender_and_preserve_mismatch(self):
        source = 'قراءة «s» للفظ «رجل»:\nهو اسم.\nهو مذكر.\nيدل على واحد.'
        for text, value in (("ثلاثة عشر رجل", 13), ("ثلاثة وعشرون رجل", 23),
                            ("ثلاثة و عشرون رجل", 23), ("أحد عشر رجل", 11)):
            report = read_count_phrase(text, lexical_text=source)
            self.assertEqual(report["numeral"]["value"], value)
            self.assertEqual(report["alternatives"][0]["conditional_status"], "COMPATIBLE_OBSERVED_FEATURES")
        mismatch = read_count_phrase("ثلاثة عشرة رجل", lexical_text=source)
        self.assertEqual(mismatch["alternatives"][0]["checks"]["ten_gender"]["status"], "CONFLICT")

    def test_plural_gender_cannot_substitute_for_missing_singular_origin(self):
        source = ORIGINS.replace('مفرده القراءة «single».\n', '')
        report = read_count_phrase("3 رجال", lexical_text=source)
        self.assertEqual({a["rule"]["singular_gender"] for a in report["alternatives"]}, {"masculine", "feminine"})
        self.assertTrue(all("SINGULAR_GENDER_WITNESS" in a["missing"] for a in report["alternatives"]))

    def test_no_unbounded_number_or_cross_clause_attachment(self):
        for text in ("101 رجال", "200 رجال", "1001 رجال"):
            report = read_count_phrase(text, lexical_text=ORIGINS)
            self.assertEqual(report["alternatives"], [])
            self.assertIn("NUMBER_RULE_OUTSIDE_DOMAIN", report["missing"])
        for text in ("3، رجال", "3\nرجال", "3\u2028رجال", "«3 رجال»", "ثَلاثة رجال"):
            self.assertEqual(read_count_phrase(text, lexical_text=ORIGINS)["alternatives"], [])
        with self.assertRaises(NabtError):
            read_count_phrase("03 رجال")

    def test_one_and_two_never_license_word_order_or_world_cardinality(self):
        report = read_count_phrase("1 رجل", lexical_text=ORIGINS)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["construction_truth"], "NOT_ESTABLISHED")
        self.assertIsNone(report["world_cardinality"])
        self.assertIsNone(report["ordinal"])

    def test_cli_requires_expected_sources_and_detects_withdrawal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, lexical, report = root / "input.txt", root / "lexical.txt", root / "reading.json"
            source.write_text("رجال", encoding="utf-8")
            lexical.write_text(ORIGINS, encoding="utf-8")
            args = [sys.executable, "-m", "nabt"]
            run = subprocess.run(args + ["read-nominal", str(source), "--lexical-source", str(lexical)],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 3, run.stderr)
            report.write_text(run.stdout, encoding="utf-8")
            replay = subprocess.run(args + ["verify-nominal", str(report), "--source", str(source),
                                           "--lexical-source", str(lexical)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            withdrawn = subprocess.run(args + ["verify-nominal", str(report), "--source", str(source)],
                                       cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(withdrawn.returncode, 2)
            self.assertFalse(json.loads(withdrawn.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
