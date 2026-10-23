"""Builder checks for the Arabic bridge. These are not independent holdouts."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from nabt.arabic_reader import (LANGUAGE_ID, Mood, read_arabic, parse_query,
                               encode_cell_envelope, decode_cell_envelope)
from nabt.cli import main
from nabt.errors import NabtError
from nabt.program import Instruction, Program, compile_request, execute_program, verify_execution
from nabt.semantics import SemanticKernel
from nabt.text_ir import Atom, Fact
from nabt.text_reader import parse_document as controlled


class ArabicSyntaxTests(unittest.TestCase):
    def test_vocalized_nominal_roles_and_cases_are_read_from_source(self):
        reading = read_arabic("فرد زيد. زيدٌ قائمٌ.\r\nعمروٌ هو جالسٌ.")
        self.assertTrue(reading.accepted)
        self.assertEqual([f.atom for f in reading.document.facts],
                         [Atom("قائم", ("زيد",)), Atom("جالس", ("عمرو",))])
        self.assertEqual(b"".join(s.span.extract(reading.document.source) for s in reading.document.segments),
                         reading.document.source.raw_bytes)
        for step in reading.steps:
            for cue in step.cues:
                self.assertEqual(cue.span.extract(reading.document.source).decode(), cue.surface)

    def test_nominal_roles_can_be_licensed_by_a_text_declaration(self):
        self.assertFalse(read_arabic("راصد صبور.").accepted)
        reading = read_arabic("فرد راصد. راصد صبور.")
        self.assertTrue(reading.accepted)
        self.assertEqual(reading.document.facts[0].atom, Atom("صبور", ("راصد",)))

    def test_role_and_stem_evidence_do_not_leak_between_documents(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source("فرد راصد.", source_id="lexicon").accepted)
        self.assertFalse(kernel.add_source("راصد صبور.", source_id="unread").accepted)
        self.assertEqual([s["source_id"] for s in kernel.snapshot()["sources"]], ["lexicon"])

    def test_case_suffix_is_not_a_full_diacritic_normalizer(self):
        a = read_arabic("زَيْدٌ هو كاتِبٌ.").document.facts[0].atom
        self.assertEqual(a, Atom("كاتِب", ("زَيْد",)))
        self.assertNotEqual(a, Atom("كاتب", ("زيد",)))

    def test_accusative_alif_requires_an_attested_unique_stem(self):
        for text, predicate in (("مفهوم باحث. ليس سالمٌ هو باحثًا.", "باحث"),
                                ("مفهوم عصا. ليس سالمٌ هو عصًا.", "عصا")):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assertTrue(reading.accepted)
                self.assertEqual(reading.document.facts[0].atom, Atom(predicate, ("سالم",), False))
                self.assertTrue(any(c.role == "prior_stem_identity" for c in reading.steps[-1].cues))
        self.assertFalse(read_arabic("مفهوم عص. مفهوم عصا. ليس سالمٌ عصًا.").accepted)

    def test_conjunction_projects_only_explicitly_connected_predications(self):
        reading = read_arabic("زيدٌ هو قائمٌ و جالسٌ.")
        self.assertTrue(reading.accepted)
        self.assertEqual([f.atom for f in reading.document.facts],
                         [Atom("قائم", ("زيد",)), Atom("جالس", ("زيد",))])
        reading = read_arabic("فرد زيد. فرد عمرو. زيدٌ قائمٌ وعمروٌ جالسٌ.")
        self.assertTrue(reading.accepted)
        self.assertEqual(reading.document.facts[-1].atom, Atom("جالس", ("عمرو",)))
        self.assertFalse(read_arabic("زيدٌ قائمٌ ومجتهدٌ.").accepted)

    def test_negative_scope_is_not_distributed_over_an_unresolved_conjunction(self):
        for text in ("ليس زيدٌ قائمَ و جالسٌ.", "ليس زيد هو حاضر و سالم هو نشيط."):
            reading = read_arabic(text)
            self.assertFalse(reading.accepted)
            self.assertEqual(reading.document.facts, ())
        reading = read_arabic("ليس زيدٌ هو قائمَ و ليس عمروٌ هو جالسَ.")
        self.assertTrue(reading.accepted)
        self.assertTrue(all(not f.atom.positive for f in reading.document.facts))

    def test_quantifier_cases_and_one_way_consequence(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source("كلُّ باحثٍ مدققٌ. سالمٌ هو باحثٌ.", source_id="rule").accepted)
        answer = kernel.query("هل سالمٌ مدققٌ؟")
        self.assertEqual(answer.status, "SUPPORTED")
        self.assertTrue(kernel.verify_certificate(answer.proofs["query"])["accepted"])
        self.assertEqual(kernel.query("هل عمروٌ هو مدققٌ؟").status, "UNKNOWN")
        self.assertFalse(read_arabic("كُلْ طعام الطفل.").document.rules)
        self.assertFalse(read_arabic("كل باحث مدقق.").accepted)

    def test_conditional_never_asserts_antecedent_or_consequent(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        text = "إذا ?س هو باحث فإن ?س هو مدقق."
        self.assertTrue(kernel.add_source(text, source_id="condition").accepted)
        self.assertEqual(kernel.query("هل سالم هو مدقق؟").status, "UNKNOWN")
        self.assertTrue(kernel.add_source("فرد سالم. سالمٌ باحثٌ.", source_id="fact").accepted)
        self.assertEqual(kernel.query("هل سالمٌ مدققٌ؟").status, "SUPPORTED")

    def test_declarations_definitions_and_binary_relations_reuse_ir(self):
        text = ("تعريف باحث هو شخص و مدقق. علاقة يراجع. "
                "إذا ?س هو باحث و ?س يراجع ?ص فإن ?ص هو مفحوص. "
                "فرد سالم. سالمٌ شخصٌ و مدققٌ. سالم يراجع تقرير.")
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source(text, source_id="source").accepted)
        answer = kernel.query("هل تقرير هو مفحوص؟")
        self.assertEqual(answer.status, "SUPPORTED")
        self.assertTrue(kernel.verify_certificate(answer.proofs["query"])["accepted"])

    def test_nonassertive_moods_and_unresolved_alternatives(self):
        for text, mood in (("هل سالم هو نقي؟", Mood.QUESTION), ("ليت سالم هو نقي.", Mood.WISH),
                           ("لعل سالم هو نقي.", Mood.HOPE), ("يا سالم.", Mood.VOCATIVE)):
            r = read_arabic(text)
            self.assertTrue(r.accepted)
            self.assertEqual(r.steps[0].mood, mood)
            self.assertFalse(r.document.facts or r.document.rules)
        for text in ("لا تكتب.", "إن سالم باحث.", "سالم هو باحث أو سالم هو كاتب."):
            r = read_arabic(text)
            self.assertFalse(r.accepted)
            self.assertGreaterEqual(len(r.steps[0].alternatives), 2)

    def test_query_does_not_extract_an_embedded_question(self):
        with self.assertRaises(NabtError):
            parse_query("سالمٌ باحثٌ. هل سالمٌ مدققٌ؟")
        with self.assertRaises(NabtError):
            parse_query("هل نام زيد؟")

    def test_conflicting_operator_vowels_are_not_silently_erased(self):
        for text in ("كَلَّ باحث مدقق.", "هُلْ سالم هو نقي؟", "إذا ?س هو نقي فَإِنْ ?س هو مقبول."):
            with self.subTest(text=text):
                reading = read_arabic(text)
                self.assertFalse(reading.accepted)
                self.assertFalse(reading.document.facts or reading.document.rules)

    def test_query_role_context_is_current_and_scope_bound(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source("سالم هو نقي.", source_id="fact", scope="a").accepted)
        self.assertEqual(kernel.query("هل سالم نقي؟", scope="a").status, "SUPPORTED")
        with self.assertRaises(NabtError):
            kernel.query("هل سالم نقي؟", scope="b")
        kernel.remove_source("fact")
        with self.assertRaises(NabtError):
            kernel.query("هل سالم نقي؟", scope="a")

    def test_forged_ir_is_reparsed_under_the_kernel_profile(self):
        doc = read_arabic("سالمٌ هو باحثٌ.").document
        bad = copy.deepcopy(doc)
        f = doc.facts[0]
        object.__setattr__(bad, "facts", (Fact(Atom("مخترع", ("سالم",)), f.span, f.component_spans, f.analysis_id),))
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_document(bad).accepted)
        self.assertEqual(kernel.query("هل سالم هو باحث؟").status, "SUPPORTED")
        self.assertEqual(kernel.query("هل سالم هو مخترع؟").status, "OUT_OF_SCOPE")

    def test_profiles_do_not_silently_change_the_old_controlled_language(self):
        self.assertFalse(controlled("زيدٌ قائمٌ.").accepted)
        self.assertTrue(read_arabic("فرد زيد. زيدٌ قائمٌ.").accepted)
        a = SemanticKernel(); b = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertNotEqual(a.snapshot()["program_sha256"], b.snapshot()["program_sha256"])
        with self.assertRaises(NabtError):
            SemanticKernel(language_id="caller.parser")

    def test_revision_conflict_and_withdrawal_follow_original_sources(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source("فرد سالم. كلُّ باحثٍ مدققٌ.", source_id="law").accepted)
        self.assertTrue(kernel.add_source("فرد سالم. سالمٌ باحثٌ.", source_id="fact").accepted)
        old = kernel.query("هل سالمٌ مدققٌ؟")
        self.assertEqual(old.status, "SUPPORTED")
        self.assertTrue(kernel.remove_source("fact").accepted)
        self.assertEqual(kernel.query("هل سالمٌ مدققٌ؟").status, "UNKNOWN")
        self.assertFalse(kernel.verify_certificate(old.proofs["query"])["accepted"])
        self.assertTrue(kernel.add_source("فرد سالم. سالمٌ باحثٌ.", source_id="fact").accepted)
        self.assertTrue(kernel.add_source("مفهوم باحث. ليس سالمٌ هو باحثًا.", source_id="opposite").accepted)
        self.assertEqual(kernel.query("هل سالمٌ باحثٌ؟").status, "CONFLICT")
        self.assertEqual(kernel.query("هل سالمٌ مدققٌ؟").status, "DEFER")

    def test_unread_source_or_failed_replacement_is_atomic(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source("فرد سالم. سالمٌ باحثٌ.", source_id="fact").accepted)
        before = kernel.snapshot()
        self.assertFalse(kernel.replace_source("سالمٌ كاتبٌ. لا تكتب.", source_id="fact").accepted)
        self.assertEqual(before, kernel.snapshot())

    def test_numeric_program_and_receipt_use_installed_arabic_law(self):
        request = {"task": "arabic_inquiry", "events": [
            {"op": "add", "source_id": "law", "text": "كلُّ باحثٍ مدققٌ."},
            {"op": "add", "source_id": "fact", "text": "فرد سالم. سالمٌ باحثٌ."},
            {"op": "query", "query_id": "q", "text": "هل سالمٌ مدققٌ؟"}]}
        p = compile_request(request)
        self.assertEqual([i.opcode for i in p.instructions], [35, 31, 31, 33])
        self.assertEqual(p, Program.from_number(p.number))
        r = execute_program(p)
        self.assertEqual(r["result"]["status"], "SUPPORTED")
        self.assertEqual(r["installed_contracts"]["text_language"], LANGUAGE_ID)
        self.assertTrue(r["trace"][1]["result"]["reading_steps"])
        self.assertTrue(verify_execution(r)["valid"])
        bad = copy.deepcopy(r)
        bad["trace"][1]["result"]["reading_steps"][0]["mood_code"] = 2
        self.assertFalse(verify_execution(bad)["valid"])

    def test_numeric_program_cannot_switch_reading_laws_mid_theory(self):
        for codes in ((35, 30), (30, 35), (35, 35), (10, 35)):
            with self.subTest(codes=codes), self.assertRaises(NabtError):
                Program(tuple(Instruction(n, (1,) if n == 10 else ("scope",)) for n in codes))

    def test_cell_envelope_preserves_mood_and_already_encoded_cells(self):
        for mood in Mood:
            n = encode_cell_envelope(mood, (84, 8, 4))
            self.assertEqual(n, 132797844 + int(mood))
            self.assertEqual(decode_cell_envelope(n), (mood, (84, 8, 4)))
        for bad in (True, 8, -1):
            with self.assertRaises(NabtError):
                decode_cell_envelope(bad)

    def test_cli_runs_the_new_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "theory.txt"
            path.write_text("كلُّ باحثٍ مدققٌ. فرد سالم. سالمٌ باحثٌ.", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["read-arabic", str(path)])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output.getvalue())["language_id"], LANGUAGE_ID)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["ask-arabic", str(path), "هل سالمٌ مدققٌ؟"])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output.getvalue())["result"]["status"], "SUPPORTED")


if __name__ == "__main__":
    unittest.main()
