"""Literal controls for skipping an identity-only tokenizer removal pass.

The pre-existing Unicode suite covers the character law and operation order.
This small supplement adds long/tail cases and the old helper's non-str input
semantics. It does not expand the separately validated UTF-8 search API.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from tools.grammar_catalog.retrieval import tokens


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "evidence/operator_context_v1/performance_followup_v2/acceptance_token_identity.json"
CONTRACT_SHA256 = "30af42625da120d40f86f86a5d8f869d0a40ad45f157f0cad9c42c1f500a159d"


class StringSubclass(str):
    pass


class IterationSubclass(str):
    def __new__(cls, text, characters):
        value = super().__new__(cls, text)
        value.characters = tuple(characters)
        return value

    def __iter__(self):
        return iter(self.characters)


class TranslateSubclass(str):
    calls = 0

    def translate(self, table):
        type(self).calls += 1
        raise AssertionError("The original join returns a built-in str")


class TokenIdentityAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = CONTRACT.read_bytes()
        if hashlib.sha256(raw).hexdigest() != CONTRACT_SHA256:
            raise AssertionError("Frozen token identity expectations changed")
        cls.contract = json.loads(raw)

    def test_01_exact_strings_keep_tail_deletion_order_and_fresh_results(self):
        for case in self.contract["exact_string_cases"]:
            with self.subTest(case=case["id"]):
                if case.get("recipe") == "repeat":
                    value = case["unit"] * case["repeat"]
                    expected = case["expected_unit"] * case["repeat"]
                elif case.get("recipe") == "tail":
                    value = case["prefix_character"] * case["prefix_count"] + case["tail"]
                    expected = ["a" * case["prefix_count"] + case["expected_suffix"]]
                else:
                    value, expected = case["input"], case["expected_tokens"]
                first = tokens(value)
                self.assertIs(type(first), list)
                self.assertEqual(first, expected)
                first.append("caller mutation")
                self.assertEqual(tokens(value), expected)

    def test_02_legacy_iterables_subclasses_and_exception_classes_are_preserved(self):
        for case in self.contract["legacy_iterable_cases"]:
            with self.subTest(case=case["id"]):
                recipe = case["recipe"]
                if recipe == "list":
                    value = list(case["characters"])
                elif recipe == "tuple":
                    value = tuple(case["characters"])
                elif recipe == "iterator":
                    value = iter(case["characters"])
                elif recipe == "generator":
                    value = (character for character in case["characters"])
                elif recipe == "mapping":
                    value = {character: offset for offset, character in enumerate(case["characters"])}
                elif recipe == "string_subclass":
                    value = StringSubclass(case["text"])
                elif recipe == "iteration_subclass":
                    value = IterationSubclass(case["text"], case["characters"])
                elif recipe == "translate_subclass":
                    value = TranslateSubclass(case["text"])
                else:
                    self.fail("Unimplemented frozen iterable case: " + recipe)
                TranslateSubclass.calls = 0
                self.assertEqual(tokens(value), case["expected_tokens"])
                self.assertEqual(TranslateSubclass.calls, 0)
                if recipe in ("iterator", "generator"):
                    self.assertEqual(list(value), [])

        def broken_iterator():
            yield "A"
            raise ValueError("preserved iterator failure")

        factories = {
            "none": lambda: None,
            "integer": lambda: 7,
            "bytes_iteration": lambda: b"AB",
            "multicharacter_element": lambda: ["AB"],
            "empty_character_element": lambda: [""],
            "nonstring_element": lambda: [7],
            "iterator_exception": broken_iterator,
        }
        exceptions = {"TypeError": TypeError, "ValueError": ValueError}
        for case in self.contract["legacy_error_cases"]:
            with self.subTest(case=case["id"]), self.assertRaises(exceptions[case["exception"]]):
                tokens(factories[case["id"]]())


if __name__ == "__main__":
    unittest.main()
