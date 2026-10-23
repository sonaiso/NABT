"""Hand-specified AST, byte-span, scope, and boundary checks for reader v1.

The expected atoms and rule directions below are authored independently of
the production scanner. No private evaluation material is used here.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from nabt.text_ir import Atom
from nabt.text_reader import (
    MAX_DEFINITION_MEMBERS,
    MAX_RULE_PREMISES,
    MAX_STATEMENTS,
    MAX_STATEMENT_BYTES,
    MAX_TEXT_BYTES,
    parse_document,
    parse_query,
)


class TestControlledArabicAst(unittest.TestCase):
    def test_declarations_use_fresh_labels_without_asserting_instances(self) -> None:
        document = parse_document("مفهوم بلوري. علاقة يحاذي. فرد عينة_جديدة.")
        self.assertTrue(document.accepted)
        self.assertEqual(
            [(item.kind, item.name) for item in document.declarations],
            [("concept", "بلوري"), ("relation", "يحاذي"), ("individual", "عينة_جديدة")],
        )
        self.assertEqual(document.facts, ())
        self.assertEqual(document.rules, ())

    def test_facts_infer_unary_binary_and_explicit_negative_forms(self) -> None:
        document = parse_document(
            "رقاقة هو بلوري. ليس رقاقتان هو بلوري. رقاقة يحاذي مجس. ليس مجس يحاذي رقاقة."
        )
        self.assertTrue(document.accepted)
        self.assertEqual(
            tuple(item.atom for item in document.facts),
            (Atom("بلوري", ("رقاقة",)), Atom("بلوري", ("رقاقتان",), False),
             Atom("يحاذي", ("رقاقة", "مجس")), Atom("يحاذي", ("مجس", "رقاقة"), False)),
        )
        self.assertEqual(document.declarations, ())

    def test_many_unseen_labels_follow_the_same_syntax(self) -> None:
        for index in range(20):
            with self.subTest(index=index):
                subject, predicate, target = f"فرد_{index}", f"وصف_{index}", f"طرف_{index}"
                document = parse_document(f"{subject} هو {predicate}. {subject} صلة_{index} {target}.")
                self.assertTrue(document.accepted)
                self.assertEqual(document.facts[0].atom, Atom(predicate, (subject,)))
                self.assertEqual(document.facts[1].atom, Atom(f"صلة_{index}", (subject, target)))

    def test_definition_means_equivalence_in_exactly_the_declared_directions(self) -> None:
        document = parse_document("تعريف شفاف_موصل هو شفاف و موصل.")
        self.assertTrue(document.accepted)
        self.assertEqual(document.definitions[0].members, ("شفاف", "موصل"))
        self.assertEqual(
            [(rule.kind, rule.body, rule.head) for rule in document.rules],
            [
                ("definition_forward", (Atom("شفاف_موصل", ("?x",)),), Atom("شفاف", ("?x",))),
                ("definition_forward", (Atom("شفاف_موصل", ("?x",)),), Atom("موصل", ("?x",))),
                ("definition_reverse", (Atom("شفاف", ("?x",)), Atom("موصل", ("?x",))),
                 Atom("شفاف_موصل", ("?x",))),
            ],
        )
        self.assertEqual(document.facts, ())

    def test_universal_is_one_direction_and_does_not_assert_existence(self) -> None:
        document = parse_document("كل بلوري هو منتظم.")
        self.assertEqual(len(document.rules), 1)
        self.assertEqual(document.rules[0].body, (Atom("بلوري", ("?x",)),))
        self.assertEqual(document.rules[0].head, Atom("منتظم", ("?x",)))
        self.assertEqual(document.rules[0].kind, "universal")
        self.assertEqual(document.facts, ())

    def test_conditional_preserves_variables_argument_order_and_polarity(self) -> None:
        document = parse_document(
            "إذا كان ?س يجاور ?y و ليس ?y هو موصل فإن ليس ?س يتصل ?y."
        )
        self.assertTrue(document.accepted)
        rule = document.rules[0]
        self.assertEqual(rule.body, (Atom("يجاور", ("?س", "?y")), Atom("موصل", ("?y",), False)))
        self.assertEqual(rule.head, Atom("يتصل", ("?س", "?y"), False))
        self.assertEqual(rule.head.variables, frozenset(("?س", "?y")))

    def test_rule_may_use_constants_and_repeated_variables(self) -> None:
        document = parse_document("إذا ?س يساوي ?س و ?س يجاور محطة فإن محطة هو مأهول.")
        self.assertTrue(document.accepted)
        self.assertEqual(document.rules[0].body[0], Atom("يساوي", ("?س", "?س")))
        self.assertEqual(document.rules[0].head, Atom("مأهول", ("محطة",)))

    def test_definition_has_no_reverse_rule_for_an_individual_member_alone(self) -> None:
        document = parse_document("تعريف متزن هو بارد و ساكن.")
        reverse = [rule for rule in document.rules if rule.head.predicate == "متزن"]
        self.assertEqual(len(reverse), 1)
        self.assertEqual(reverse[0].body, (Atom("بارد", ("?x",)), Atom("ساكن", ("?x",))))

    def test_query_is_ground_and_has_the_requested_scope(self) -> None:
        query = parse_query("هل ليس عينة يجاور مرجع؟", scope="مختبر_أ")
        self.assertEqual(query.atom, Atom("يجاور", ("عينة", "مرجع"), False))
        self.assertEqual(query.scope, "مختبر_أ")
        self.assertTrue(query.atom.ground)

    def test_eof_and_declared_delimiters_separate_whole_statements(self) -> None:
        for separator in (".", ";", "؛", "؟", "?", "\n", "\r\n"):
            with self.subTest(separator=separator):
                document = parse_document("فرد عينة" + separator + " فرد مرجع")
                self.assertTrue(document.accepted)
                self.assertEqual([item.name for item in document.declarations], ["عينة", "مرجع"])


class TestSourceSpansAndIdentity(unittest.TestCase):
    def test_complete_source_restoration_includes_spaces_crlf_and_punctuation(self) -> None:
        raw = "  فرد «رُقَاقة أ» ;\r\n\t«رُقَاقة أ» هو بَلُّوري.  \nهل «رُقَاقة أ» هو بَلُّوري؟  ".encode()
        document = parse_document(raw, source_id="sample")
        self.assertTrue(document.accepted)
        self.assertEqual(document.source.raw_bytes, raw)
        self.assertEqual(b"".join(segment.span.extract(document.source) for segment in document.segments), raw)
        cursor = 0
        for segment in document.segments:
            self.assertEqual(segment.span.start, cursor)
            self.assertGreater(segment.span.end, segment.span.start)
            cursor = segment.span.end
        self.assertEqual(cursor, len(raw))
        self.assertEqual(document.raw_text.encode(), raw)

    def test_component_spans_are_original_utf8_byte_offsets_in_source_order(self) -> None:
        raw = "  ليس «فَرْد جديد» هو مُتّصل. ".encode()
        document = parse_document(raw, source_id="marked")
        fact = document.facts[0]
        expected = ["ليس", "«فَرْد جديد»", "هو", "مُتّصل"]
        self.assertEqual([span.extract(document.source).decode() for span in fact.component_spans], expected)
        cursor = 0
        for token, span in zip(expected, fact.component_spans):
            needle = token.encode()
            start = raw.index(needle, cursor)
            self.assertEqual((span.start, span.end), (start, start + len(needle)))
            self.assertEqual(span.source_id, "marked")
            cursor = span.end
        self.assertEqual(fact.span.extract(document.source), "ليس «فَرْد جديد» هو مُتّصل".encode())

    def test_quoted_delimiters_keywords_and_punctuation_do_not_change_scope(self) -> None:
        document = parse_document("«مقياس. و؛ هل؟» هو «و فإن».")
        self.assertTrue(document.accepted)
        self.assertEqual(len(document.facts), 1)
        self.assertEqual(document.facts[0].atom, Atom("و فإن", ("مقياس. و؛ هل؟",)))
        self.assertEqual(document.queries, ())
        reserved = parse_document("«هو» هو «ليس».")
        self.assertEqual(reserved.facts[0].atom, Atom("ليس", ("هو",)))

    def test_marks_and_unicode_composition_are_not_normalized(self) -> None:
        document = parse_document("أَب هو واصف. أب هو واصف. أب هو وَاصف.")
        self.assertTrue(document.accepted)
        self.assertEqual([item.atom.args for item in document.facts], [("أَب",), ("أب",), ("أب",)])
        self.assertEqual([item.atom.predicate for item in document.facts], ["واصف", "واصف", "وَاصف"])
        self.assertEqual(len({item.atom for item in document.facts}), 3)

    def test_quoted_interiors_remain_exact_including_edge_spaces(self) -> None:
        document = parse_document("« فرد أ » هو « وصف ب ».")
        self.assertTrue(document.accepted)
        self.assertEqual(document.facts[0].atom, Atom(" وصف ب ", (" فرد أ ",)))

    def test_occurrence_identity_is_stable_and_changes_with_scope_or_source(self) -> None:
        text = "عينة هو بلوري. عينة هو بلوري."
        document = parse_document(text, source_id="first", scope="أ")
        replay = parse_document(text, source_id="first", scope="أ")
        other_source = parse_document(text, source_id="second", scope="أ")
        other_scope = parse_document(text, source_id="first", scope="ب")
        self.assertEqual(document, replay)
        self.assertNotEqual(document.facts[0].analysis_id, document.facts[1].analysis_id)
        self.assertNotEqual(document.facts[0].analysis_id, other_source.facts[0].analysis_id)
        self.assertNotEqual(document.facts[0].analysis_id, other_scope.facts[0].analysis_id)


class TestUnsupportedScopeAndBudgets(unittest.TestCase):
    def test_unparsed_suffix_prevents_prefix_admission_for_entire_statement(self) -> None:
        text = "فرد شاهد.\nشاهد هو صادق ربما.\nفرد آخر."
        document = parse_document(text)
        self.assertFalse(document.accepted)
        self.assertEqual(document.facts, ())
        self.assertEqual([item.name for item in document.declarations], ["شاهد", "آخر"])
        self.assertEqual(len(document.residuals), 1)
        self.assertEqual(document.residuals[0].span.extract(document.source).decode(), "شاهد هو صادق ربما")
        self.assertEqual(b"".join(segment.span.extract(document.source) for segment in document.segments), text.encode())

    def test_document_with_an_unsupported_statement_is_not_accepted(self) -> None:
        document = parse_document("شاهد هو صادق. هذه جملة عربية خارج النطاق. هل شاهد هو صادق؟")
        self.assertFalse(document.accepted)
        self.assertEqual(len(document.facts), 1)  # Inspection is not partial admission.
        self.assertEqual(len(document.queries), 1)
        self.assertEqual(len(document.residuals), 1)

    def test_out_of_grammar_forms_have_no_facts_or_rules(self) -> None:
        samples = (
            "شاهد صادق", "شاهد هو صادق و آخر هو أمين", "ليس ليس شاهد هو صادق",
            "شاهد ليس صادق", "لا شاهد هو صادق", "تعريف صادق هو أمين و",
            "تعريف صادق هو أمين شيء", "كل صادق هو أمين إضافة", "مفهوم صادق إضافة",
            "إذا ?س هو صادق فإن ?ص هو أمين", "إذا ?س هو صادق فإن ?س هو أمين زيادة",
            "إذا ?س هو صادق و فإن ?س هو أمين", "إذا ?س هو صادق فإن ?س هو أمين فإن ?س هو فاضل",
            "إذا فإن ?س هو صادق", "إذا ?س هو صادق", "?س هو صادق", "هل ?س هو صادق",
            "شاهد هو ?وصف", "«?س» هو صادق", "«?س س» يجاور شاهد", "مفهوم ?س",
            "«اسم»ملتصق هو صادق", "اسم» هو صادق", "«اسم هو صادق", "«اسم «داخل»» هو صادق",
            "شاهد هو صادق $", "شاهد هو صادق\x00", "شاه\u200bد هو صادق", "\ufeffشاهد هو صادق",
        )
        for text in samples:
            with self.subTest(text=text):
                document = parse_document(text)
                self.assertFalse(document.accepted)
                self.assertTrue(document.residuals)
                self.assertEqual(document.facts, ())
                self.assertEqual(document.rules, ())
                self.assertEqual(b"".join(segment.span.extract(document.source) for segment in document.segments), text.encode())

    def test_unclosed_quote_retains_the_complete_remaining_source(self) -> None:
        text = "فرد شاهد. «اسم\nآخر هو أمين. هل شاهد هو صادق؟"
        document = parse_document(text)
        self.assertFalse(document.accepted)
        self.assertEqual(document.residuals[0].code, "UNCLOSED_NAME")
        self.assertEqual(document.residuals[0].span.extract(document.source).decode(),
                         "«اسم\nآخر هو أمين. هل شاهد هو صادق؟")
        self.assertEqual(document.facts, ())
        self.assertEqual(document.queries, ())

    def test_parse_query_cannot_extract_from_mixed_or_multiple_statement_input(self) -> None:
        for text in (
            "شاهد هو صادق", "هل شاهد هو صادق؟ هل آخر هو صادق؟",
            "فرد شاهد. هل شاهد هو صادق؟", "شاهد هو صادق. هل شاهد هو صادق؟",
            "هل شاهد هو صادق إضافة؟", "هل ?س هو صادق؟",
        ):
            with self.subTest(text=text), self.assertRaises(NabtError) as raised:
                parse_query(text)
            self.assertEqual(raised.exception.code, "INVALID_QUERY")
            self.assertEqual(raised.exception.status, "REJECT")

    def test_code_shaped_quoted_label_is_only_an_inert_name(self) -> None:
        name = "__import__('os').system('never execute')"
        document = parse_document(f"«{name}» هو «callable».")
        self.assertTrue(document.accepted)
        self.assertEqual(document.facts[0].atom, Atom("callable", (name,)))

    def test_invalid_bytes_types_ids_and_empty_input_are_distinct_from_residuals(self) -> None:
        cases = [(b"\xff", "INVALID_UTF8"), ("\ud800", "INVALID_UTF8"),
                 (bytearray(b"abc"), "INVALID_TEXT_INPUT"), (False, "INVALID_TEXT_INPUT"),
                 (b"", "EMPTY_TEXT")]
        for raw, code in cases:
            with self.subTest(code=code), self.assertRaises(NabtError) as raised:
                parse_document(raw)
            self.assertEqual(raised.exception.code, code)
        with self.assertRaises(NabtError) as raised:
            parse_document("فرد شاهد", source_id="../other")
        self.assertEqual(raised.exception.code, "INVALID_SOURCE_ID")
        with self.assertRaises(NabtError) as raised:
            parse_document("فرد شاهد", scope="\ud800")
        self.assertEqual(raised.exception.code, "INVALID_SCOPE")
        document = parse_document(" .\r\n؛  ")
        self.assertFalse(document.accepted)
        self.assertEqual(document.residuals[0].code, "EMPTY_DOCUMENT")

    def test_real_resource_boundaries_are_deferred_not_linguistic_refutations(self) -> None:
        overlarge = (
            b" " * (MAX_TEXT_BYTES + 1),
            b"x" * (MAX_STATEMENT_BYTES + 1),
            "فرد شاهد.\n" * (MAX_STATEMENTS + 1),
            "فرد " + "س" * 513,
            "إذا " + " و ".join(["?س هو صادق"] * (MAX_RULE_PREMISES + 1)) + " فإن ?س هو أمين",
            "تعريف صادق هو " + " و ".join(["أمين"] * (MAX_DEFINITION_MEMBERS + 1)),
        )
        for raw in overlarge:
            with self.subTest(length=len(raw)), self.assertRaises(NabtError) as raised:
                parse_document(raw)
            self.assertEqual(raised.exception.code, "RESOURCE_LIMIT")
            self.assertEqual(raised.exception.status, "DEFER")

    def test_cumulative_work_limit_does_not_return_a_partial_document(self) -> None:
        with patch("nabt.text_reader.MAX_TOKENS", 5), self.assertRaises(NabtError) as raised:
            parse_document("شاهد هو صادق. آخر هو صادق.")
        self.assertEqual(raised.exception.code, "RESOURCE_LIMIT")
        self.assertEqual(raised.exception.status, "DEFER")


if __name__ == "__main__":
    unittest.main()
