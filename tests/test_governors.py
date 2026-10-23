"""Development regressions; the independent new-material trial is separate."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt import governors
from nabt.arabic_reader import decode_reading_number, read_arabic as old_read
from nabt.governor_reader import LANGUAGE_ID, read_arabic, replay_source_policy
from nabt.errors import NabtError
from nabt.program import Program, compile_request, execute_program, verify_execution
from nabt.semantics import SemanticKernel

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "«خالد» هو قارئٌ. إِنَّ خالدًا متأهبٌ."
QUESTION = "هل خالد هو متأهب؟"


class GovernorAlgebraTests(unittest.TestCase):
    def test_finite_lookup_keeps_conditional_and_interrogative_rows(self):
        table = governors.installed_table()
        self.assertEqual(len(table.entries), 100)
        self.assertEqual(len({e.label for e in table.entries}), 96)
        for label in ("مَن", "ما", "متى", "أين"):
            self.assertEqual({e.class_code for e in governors.lookup(label)}, {10, 12})
            self.assertEqual(len(governors.lookup(label)), 2)
        self.assertEqual(governors.lookup("إن"), ())
        self.assertEqual(governors.lookup("الباء")[0].class_code, 7)
        self.assertEqual(governors.lookup("ب"), ())  # a label is not a tokenizer

    def test_numeric_pairing_domain_and_separate_category_permission(self):
        occupied = set()
        for role in (0, 1, 2, 6, 9, 10, 11, 12, 13):
            for mark in range(4):
                number = governors.role_mark_number(role, mark)
                self.assertNotIn(number, occupied)
                occupied.add(number)
                self.assertEqual(governors.decode_role_mark(number), (role, mark))
        self.assertEqual(len(occupied), 36)
        self.assertFalse(governors.category_allows(0, 3))
        self.assertEqual(governors.decode_role_mark(3), (0, 3))
        for invalid in (True, -1, 56, 12):
            with self.subTest(invalid=invalid), self.assertRaises(NabtError):
                governors.decode_role_mark(invalid)
        with self.assertRaises(NabtError):
            governors.role_mark_number(0, True)

    def test_unknown_case_stays_viable_but_wrong_case_closes_it(self):
        expected = [[[0, 0], [1, 1]]]
        pending = governors.check_assignment(2, {0: None, 1: 1})
        self.assertEqual(pending["complete"], [])
        self.assertEqual(pending["viable"], expected)
        self.assertEqual(pending["deficits"][0]["missing"], [{"role": 0, "mark": 0}])
        for left in range(4):
            for right in range(4):
                report = governors.check_assignment(2, {0: left, 1: right})
                self.assertEqual(bool(report["complete"]), (left, right) == (0, 1))
                self.assertEqual(report["complete"], report["viable"])
        self.assertTrue(governors.check_assignment(2, {0: 0, 1: 1, 2: 2})["complete"])
        for invalid in (0, 14, True):
            with self.subTest(invalid=invalid), self.assertRaises(NabtError):
                governors.check_assignment(invalid, {})

    def test_coordinate_link_and_alternative_governors(self):
        for mark in range(4):
            self.assertEqual(governors.check_assignment(8, {9: mark, 10: mark})["complete"], [[]])
            self.assertEqual(governors.check_assignment(8, {9: mark})["complete"], [])
            self.assertEqual(governors.check_assignment(8, {9: mark})["viable"], [[]])
        self.assertEqual(governors.check_assignment(8, {9: 0, 10: 1})["viable"], [])
        self.assertEqual(governors.check_assignment(9, {})["viable"], [[[6, 2]], [[2, 0]]])
        self.assertEqual(governors.check_assignment(13, {13: 0})["complete"], [[[13, 0]]])


class SourceBuiltGovernorTests(unittest.TestCase):
    def test_new_source_builds_evidence_before_numerical_check(self):
        reading = read_arabic(SOURCE, source_id="new_source", scope="trial")
        self.assertTrue(reading.accepted)
        self.assertFalse(reading.document.declarations)
        result = reading.steps[-1].governor
        self.assertTrue(result["syntactic_evidence_complete"])
        self.assertEqual(result["case_check"]["complete"], [[[0, 0], [1, 1]]])
        self.assertEqual([r["role_mark_number"]["value"] for r in result["roles"]], [0, 5])
        self.assertEqual(result["semantic_projection"], "SOURCE_RELATIVE_ASSERTION")
        self.assertEqual(result["referent_identity"]["name"], "خالد")
        for record in [result["operator"], *result["roles"], result["referent_identity"]]:
            span = record["span"]
            part = SOURCE.encode()[span["start"]:span["end"]]
            self.assertEqual(sha256(part).hexdigest(), span["span_sha256"])
            self.assertEqual(span["source_id"], "new_source")
        self.assertEqual(result["referent_identity"]["span"]["start"], 0)

    def test_indefinite_roles_do_not_create_global_individual_identity(self):
        reading = read_arabic("إنّ شجرةً مثمرةٌ.")
        self.assertFalse(reading.accepted)
        self.assertEqual(reading.document.facts, ())
        self.assertEqual(reading.document.residuals[0].code, "REFERENT_IDENTITY_EVIDENCE")
        self.assertTrue(reading.steps[0].governor["syntactic_evidence_complete"])
        self.assertIsNone(reading.steps[0].governor["referent_identity"])

    def test_reference_witness_is_an_actual_subject_not_latest_same_lexeme(self):
        source = "«خالد» هو قارئٌ. شعارٌ هو خالدٌ. إنّ خالدًا متأهبٌ."
        reading = read_arabic(source)
        self.assertTrue(reading.accepted)
        self.assertEqual(reading.steps[-1].governor["referent_identity"]["span"]["start"], 0)

    def test_missing_and_conflicting_case_are_not_filled_from_expected_equation(self):
        for clause, reason in (("إنّ خالد متأهبٌ", "VISIBLE_CASE_EVIDENCE"),
                               ("إنّ خالدٌ متأهبٌ", "CASE_ROLE_MISMATCH"),
                               ("إنّ خالدًا متأهبٍ", "DECLENSION_CLASS_EVIDENCE"),
                               ("إنّ خالدًا يكتبُ", "NOUN_CATEGORY_EVIDENCE")):
            with self.subTest(clause=clause):
                reading = read_arabic("«خالد» هو قارئٌ. " + clause + ".")
                self.assertFalse(reading.accepted)
                self.assertEqual(reading.document.residuals[-1].code, reason)
                kernel = SemanticKernel(language_id=LANGUAGE_ID)
                self.assertFalse(kernel.add_source(reading.document.source.raw_bytes, source_id="test").accepted)
                self.assertEqual(kernel.query("هل خالد هو قارئ؟").status, "OUT_OF_SCOPE")

    def test_original_profile_is_explicitly_preserved(self):
        text = "خالدٌ هو قارئٌ. إنّ خالد متأهب."
        self.assertTrue(old_read(text).accepted)
        self.assertFalse(read_arabic(text).accepted)
        self.assertNotEqual(old_read(SOURCE).document.language_id, read_arabic(SOURCE).document.language_id)
        self.assertNotIn("governor", old_read(SOURCE).steps[-1].as_dict())

    def test_source_identity_is_local_and_alif_is_not_guessed(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source("«خالد» هو قارئٌ.", source_id="identity").accepted)
        second = kernel.add_source("إنّ خالدًا متأهبٌ.", source_id="other")
        self.assertFalse(second.accepted)
        self.assertIn("UNSUPPORTED_ACCUSATIVE_ALIF_IDENTITY", {r["code"] for r in second.residuals})
        reading = read_arabic("فرد عص. فرد عصا. إنّ عصًا واضحٌ.")
        self.assertFalse(reading.accepted)
        self.assertIn("UNSUPPORTED_ACCUSATIVE_ALIF_IDENTITY", {r.code for r in reading.document.residuals})

    def test_equal_case_pattern_never_turns_wish_comparison_or_quotation_into_fact(self):
        for clause in ("ليت خالدًا متأهبٌ", "لعلّ خالدًا متأهبٌ", "كأنّ خالدًا متأهبٌ",
                       "أنّ خالدًا متأهبٌ", "قال إنّ خالدًا متأهبٌ", '"إنّ خالدًا متأهبٌ"',
                       "إنْ خالدًا متأهبٌ", "إن خالدًا متأهبٌ", "إنّ ما خالدًا متأهبٌ",
                       "إنما خالدٌ متأهبٌ", "إنّ خالدًا متأهبٌ و قارئٌ"):
            with self.subTest(clause=clause):
                reading = read_arabic("«خالد» هو قارئٌ. " + clause + ".")
                self.assertFalse(any(f.atom.predicate == "متأهب" for f in reading.document.facts))
        quoted = read_arabic('«إنّ» هو اسمٌ.')
        self.assertTrue(quoted.accepted)
        self.assertIsNone(quoted.steps[0].governor)

    def test_replay_rejects_forged_case_or_ref_source_even_with_recomputed_number(self):
        reading = read_arabic(SOURCE)
        self.assertEqual(decode_reading_number(int(reading.packet()["number_hex"], 16)), reading.as_dict())
        for path in ("role", "reference"):
            value = reading.as_dict()
            if path == "role":
                value["steps"][-1]["governor"]["roles"][0]["role_mark_number"]["value"] = 1
            else:
                value["steps"][-1]["governor"]["referent_identity"]["span"]["source_id"] = "other"
            raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            with self.assertRaises(NabtError):
                decode_reading_number(int.from_bytes(b"\x01" + raw, "big"))

    def test_numeric_program_revision_withdraws_cited_text(self):
        request = {"task": "governor_inquiry", "events": [
            {"op": "add", "source_id": "source", "text": SOURCE},
            {"op": "query", "query_id": "q", "text": QUESTION},
            {"op": "replace", "source_id": "source", "text": "«خالد» هو قارئٌ. إنّ خالدًا نائمٌ."},
            {"op": "query", "query_id": "q", "text": QUESTION},
            {"op": "remove", "source_id": "source"},
            {"op": "query", "query_id": "q", "text": QUESTION},
        ]}
        program = compile_request(request)
        self.assertEqual(program, Program.from_number(program.number))
        receipt = execute_program(program)
        answers = [step["result"]["status"] for step in receipt["trace"] if step["opcode"] == 33]
        self.assertEqual(answers, ["SUPPORTED", "OUT_OF_SCOPE", "OUT_OF_SCOPE"])
        self.assertTrue(verify_execution(receipt)["valid"])
        forged = deepcopy(receipt)
        forged["installed_contracts"]["text_language"] = "nabt.arabic-syntax.v1"
        self.assertFalse(verify_execution(forged)["valid"])

    def test_source_policy_replays_and_installed_tampering_is_deferred(self):
        self.assertEqual(replay_source_policy()["source_sha256"],
                         "2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "data/source_evidence"
            target.mkdir(parents=True)
            for name in ("qatr.txt", "governor_policy.json"):
                (target / name).write_bytes((ROOT / "src/nabt/data/source_evidence" / name).read_bytes())
            with (target / "qatr.txt").open("ab") as handle:
                handle.write(b"\n")
            with patch("nabt.governor_reader.files", return_value=Path(directory)):
                with self.assertRaises(NabtError) as caught:
                    read_arabic(SOURCE)
                self.assertEqual((caught.exception.code, caught.exception.status),
                                 ("INSTALLED_CONTRACT_FAILED", "DEFER"))

    def test_review_counterexamples_preserve_surface_marks_without_inventing_cases(self):
        cases = [
            ("رجلٌ هو حاضرٌ. إِنَّ رجلًا شاهدٌ.", "REFERENT_IDENTITY_EVIDENCE"),
            ("فرد زيد. إِنَّ زيدَ حاضٌرٌ.", "UNSUPPORTED_INTERNAL_TANWIN"),
            ("فرد زيد. إِنَّ زيدَ هدىٌ.", "DECLENSION_CLASS_EVIDENCE"),
            ("فرد مصطفى. إِنَّ مصطفىَ حاضرٌ.", "DECLENSION_CLASS_EVIDENCE"),
            ("فرد زيد. إِنَّ زيدَ قاضٍ.", "DECLENSION_CLASS_EVIDENCE"),
            ("فرد زيد. إِنَّ زيدً حاضرٌ.", "ORTHOGRAPHY_EVIDENCE"),
            ("فرد معلمين. إِنَّ معلمينَ حاضرونَ.", "DECLENSION_CLASS_EVIDENCE"),
        ]
        for source, reason in cases:
            with self.subTest(source=source):
                reading = read_arabic(source)
                self.assertFalse(reading.accepted)
                self.assertEqual(reading.document.residuals[-1].code, reason)
                admission = SemanticKernel(language_id=LANGUAGE_ID).add_source(source)
                self.assertFalse(admission.accepted)
                self.assertEqual(admission.status, "DEFER")
        report = read_arabic(cases[4][0]).steps[-1].governor
        self.assertEqual(report["roles"][1]["surface_mark"], 2)
        self.assertIsNone(report["roles"][1]["observed_mark"])
        self.assertEqual(report["case_check"]["complete"], [])
        self.assertEqual(report["case_check"]["viable"], [[[0, 0], [1, 1]]])

    def test_question_force_prevents_projection_even_after_case_match(self):
        reading = read_arabic("«خالد» هو قارئٌ. إِنَّ خالدًا متأهبٌ؟")
        self.assertFalse(reading.accepted)
        self.assertEqual(reading.steps[-1].governor["semantic_projection"], "DEFER")
        self.assertEqual(reading.steps[-1].fact_count, 0)


if __name__ == "__main__":
    unittest.main()
