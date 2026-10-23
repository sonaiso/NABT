"""Counterexamples for active, scope-local Arabic query declarations.

These builder tests pin expected atoms and judgments; they are not a held-out
measure of Arabic coverage or an independent implementation of the reader.
"""
import contextlib
import copy
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest

from nabt.arabic_reader import LANGUAGE_ID, parse_query, read_arabic
from nabt.cli import main
from nabt.errors import NabtError
from nabt.program import Program, compile_request, execute_program, verify_execution
from nabt.semantics import SemanticKernel
from nabt.text_ir import Atom


class ArabicQueryContextTests(unittest.TestCase):
    def kernel(self):
        return SemanticKernel(language_id=LANGUAGE_ID)

    def assert_invalid_query(self, kernel, text="هل سالم يراجع تقرير؟", **kwargs):
        with self.assertRaises(NabtError) as caught:
            kernel.query(text, **kwargs)
        self.assertEqual(caught.exception.code, "INVALID_QUERY")

    def test_declared_relation_can_be_asked_as_text(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("علاقة يراجع. سالم يراجع تقرير.", source_id="source").accepted)
        answer = kernel.query("هل سالم يراجع تقرير؟")
        self.assertEqual(answer.query, Atom("يراجع", ("سالم", "تقرير")))
        self.assertEqual(answer.status, "SUPPORTED")
        self.assertTrue(kernel.verify_certificate(answer.proofs["query"])["accepted"])
        self.assertEqual(kernel.query("هل تقرير يراجع سالم؟").status, "UNKNOWN")
        self.assertEqual(kernel.query("هل ليس سالم يراجع تقرير؟").status, "REFUTED")

    def test_declaration_licenses_reading_without_asserting_a_fact(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("علاقة يراجع.", source_id="lexicon").accepted)
        before = kernel.snapshot()
        answer = kernel.query("هل سالم يراجع تقرير؟")
        self.assertEqual(answer.status, "UNKNOWN")
        self.assertEqual(answer.proofs, {})
        self.assertEqual(kernel.snapshot(), before)

    def test_query_context_keeps_individual_and_relation_roles_together(self):
        kernel = self.kernel()
        text = "فرد سالم. سالم باحث. علاقة يراجع. سالم يراجع تقرير."
        self.assertTrue(kernel.add_source(text, source_id="source").accepted)
        self.assertEqual(kernel.query("هل سالم باحث؟").status, "SUPPORTED")
        self.assertEqual(kernel.query("هل سالم يراجع تقرير؟").status, "SUPPORTED")

    def test_relation_context_is_scope_local(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("علاقة يراجع. سالم يراجع تقرير.", source_id="a", scope="a").accepted)
        self.assertEqual(kernel.query("هل سالم يراجع تقرير؟", scope="a").status, "SUPPORTED")
        self.assert_invalid_query(kernel, scope="b")
        self.assertTrue(kernel.add_source("علاقة يراجع.", source_id="b", scope="b").accepted)
        self.assertEqual(kernel.query("هل سالم يراجع تقرير؟", scope="b").status, "UNKNOWN")

    def test_withdrawal_removes_only_the_last_active_declaration(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("علاقة يراجع.", source_id="one").accepted)
        self.assertTrue(kernel.add_source("علاقة يراجع.", source_id="two").accepted)
        self.assertTrue(kernel.remove_source("one").accepted)
        self.assertEqual(kernel.query("هل سالم يراجع تقرير؟").status, "UNKNOWN")
        self.assertTrue(kernel.remove_source("two").accepted)
        self.assert_invalid_query(kernel)

    def test_replacement_changes_context_and_failed_replacement_is_atomic(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("علاقة يراجع. سالم يراجع تقرير.", source_id="source").accepted)
        before = kernel.snapshot()
        self.assertFalse(kernel.replace_source("علاقة يفحص. لا تكتب.", source_id="source").accepted)
        self.assertEqual(kernel.snapshot(), before)
        self.assertEqual(kernel.query("هل سالم يراجع تقرير؟").status, "SUPPORTED")
        self.assert_invalid_query(kernel, "هل سالم يفحص تقرير؟")
        self.assertTrue(kernel.replace_source("علاقة يفحص. سالم يفحص تقرير.", source_id="source").accepted)
        self.assert_invalid_query(kernel)
        self.assertEqual(kernel.query("هل سالم يفحص تقرير؟").status, "SUPPORTED")

    def test_scope_replacement_removes_the_old_scope_permission(self):
        kernel = self.kernel()
        text = "علاقة يراجع. سالم يراجع تقرير."
        self.assertTrue(kernel.add_source(text, source_id="source", scope="old").accepted)
        self.assertTrue(kernel.replace_source(text, source_id="source", scope="new").accepted)
        self.assert_invalid_query(kernel, scope="old")
        self.assertEqual(kernel.query("هل سالم يراجع تقرير؟", scope="new").status, "SUPPORTED")

    def test_future_or_rejected_declarations_do_not_enter_context(self):
        kernel = self.kernel()
        self.assertFalse(kernel.add_source("سالم يراجع تقرير. علاقة يراجع.", source_id="future").accepted)
        self.assert_invalid_query(kernel)
        self.assertFalse(kernel.add_source("علاقة يراجع. لا تكتب.", source_id="rejected").accepted)
        self.assert_invalid_query(kernel)
        self.assertEqual(kernel.snapshot()["sources"], [])

    def test_query_context_does_not_leak_into_source_admission(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("علاقة يراجع.", source_id="lexicon").accepted)
        self.assertFalse(kernel.add_source("سالم يراجع تقرير.", source_id="unlicensed").accepted)
        self.assertEqual(kernel.query("هل سالم يراجع تقرير؟").status, "UNKNOWN")
        self.assertFalse(read_arabic("سالم يراجع تقرير.").accepted)

    def test_forged_caller_declaration_is_not_an_active_source_declaration(self):
        doc = read_arabic("فرد سالم.", source_id="source").document
        foreign = read_arabic("علاقة يراجع.", source_id="forged").document.declarations
        forged = replace(doc, declarations=doc.declarations + foreign)
        kernel = self.kernel()
        self.assertTrue(kernel.add_document(forged).accepted)
        self.assert_invalid_query(kernel)
        self.assertEqual(kernel.snapshot()["sources"][0]["source_id"], "source")

    def test_declaration_inside_query_cannot_authorize_itself(self):
        kernel = self.kernel()
        self.assert_invalid_query(kernel, "علاقة يراجع. هل سالم يراجع تقرير؟")
        self.assertEqual(kernel.snapshot()["sources"], [])

    def test_relation_spelling_is_exact_including_diacritics(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("علاقة يُرَاجِعُ. سالم يُرَاجِعُ تقرير.", source_id="source").accepted)
        self.assertEqual(kernel.query("هل سالم يُرَاجِعُ تقرير؟").query,
                         Atom("يُرَاجِعُ", ("سالم", "تقرير")))
        self.assertEqual(kernel.query("هل سالم يُرَاجِعُ تقرير؟").status, "SUPPORTED")
        self.assert_invalid_query(kernel)
        self.assert_invalid_query(kernel, "هل سالم يُرَاجَعُ تقرير؟")

    def test_quoted_relation_identity_is_not_split_or_normalized(self):
        kernel = self.kernel()
        text = "علاقة «يطلع على». سالم «يطلع على» تقرير."
        self.assertTrue(kernel.add_source(text, source_id="source").accepted)
        answer = kernel.query("هل سالم «يطلع على» تقرير؟")
        self.assertEqual(answer.query, Atom("يطلع على", ("سالم", "تقرير")))
        self.assertEqual(answer.status, "SUPPORTED")
        self.assert_invalid_query(kernel, "هل سالم «يطلع  على» تقرير؟")

    def test_context_names_do_not_fabricate_local_stem_cues(self):
        kernel = self.kernel()
        self.assertTrue(kernel.add_source("مفهوم باحث. علاقة يراجع.", source_id="lexicon").accepted)
        # The source-local accusative-alif rule needs a cited stem span; a
        # relation name or a cross-source concept name is not such a span.
        self.assert_invalid_query(kernel, "هل سالم يراجع باحثًا؟")

    def test_context_requires_bounded_exact_ground_name_sets(self):
        invalid = ([], set(), frozenset((True,)), frozenset((3,)), frozenset(("",)),
                   frozenset((" ",)), frozenset(("x\x00",)), frozenset(("?س",)))
        for keyword in ("known_individuals", "known_relations"):
            for value in invalid:
                with self.subTest(keyword=keyword, value=value), self.assertRaises(NabtError) as caught:
                    parse_query("هل سالم هو باحث؟", **{keyword: value})
                self.assertEqual(caught.exception.code, "INVALID_QUERY_CONTEXT")
            with self.subTest(keyword=keyword), self.assertRaises(NabtError) as caught:
                parse_query("هل سالم هو باحث؟", **{keyword: frozenset(("س" * 513,))})
            self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")

    def test_context_budget_counts_both_roles(self):
        subjects = frozenset(f"اسم{i}" for i in range(8192))
        relations = frozenset(f"صلة{i}" for i in range(8192))
        query = parse_query("هل سالم صلة0 تقرير؟", known_individuals=subjects, known_relations=relations)
        self.assertEqual(query.atom, Atom("صلة0", ("سالم", "تقرير")))
        with self.assertRaises(NabtError) as caught:
            parse_query("هل سالم صلة0 تقرير؟", known_individuals=subjects,
                        known_relations=relations | frozenset(("أخرى",)))
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")

    def test_numeric_relation_query_and_receipt_replay(self):
        request = {"task": "arabic_inquiry", "events": [
            {"op": "add", "source_id": "source", "text": "علاقة يراجع. سالم يراجع تقرير."},
            {"op": "query", "query_id": "review", "text": "هل سالم يراجع تقرير؟"}]}
        program = compile_request(request)
        receipt = execute_program(Program.from_number(program.number))
        self.assertEqual(receipt["result"]["status"], "SUPPORTED")
        self.assertEqual(receipt["result"]["query_reading"]["atom"],
                         {"predicate": "يراجع", "args": ["سالم", "تقرير"], "positive": True})
        self.assertEqual(receipt["installed_contracts"]["text_reader"], "nabt.arabic-reader.v2")
        self.assertTrue(verify_execution(receipt)["valid"])
        tampered = copy.deepcopy(receipt)
        tampered["result"]["query_reading"]["context_program_sha256"] = "0" * 64
        self.assertFalse(verify_execution(tampered)["valid"])

    def test_cli_ask_arabic_with_declared_relation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "theory.txt"
            path.write_text("علاقة يراجع. سالم يراجع تقرير.", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["ask-arabic", str(path), "هل سالم يراجع تقرير؟"])
            self.assertEqual(status, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["result"]["status"], "SUPPORTED")
            self.assertTrue(verify_execution(receipt)["valid"])


if __name__ == "__main__":
    unittest.main()
