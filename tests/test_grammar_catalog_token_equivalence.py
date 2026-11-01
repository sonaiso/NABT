"""Independent semantic controls for the bounded mark-predicate optimization.

Versioned Unicode Mn/Mc/Me ranges come from official UnicodeData files, not
unicodedata.category or tokenizer output. Exhaustiveness applies to character
deletion in anchored contexts, not every arbitrary string or normalization.
Tests remain offline and pass on the original uncached tokenizer as well.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata
import unittest

from tools.grammar_catalog.retrieval import SearchIndex, tokens


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/operator_context_v1/performance_followup"
CONTRACT_SHA256 = "31b5b6d09c9c9db42e6953ac148b34dd28083e6a1a5c065600078aae91004c05"
ORACLE_SHA256 = "f73328c6ea539387d9e7f5b212a7c784a4447247576ff89e300dcba98e19a950"


def read_pinned(name, expected):
    raw = (EVIDENCE / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise AssertionError("Frozen tokenizer acceptance material changed: " + name)
    return json.loads(raw)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def case_input(case):
    # JSON decodes an escaped surrogate pair into a scalar. Explicit codepoints
    # preserve the separate Python surrogate characters used by this one case.
    if "input_codepoints" in case:
        return "".join(chr(cp) for cp in case["input_codepoints"])
    return case["input"]


class TokenEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = read_pinned("acceptance_contract.json", CONTRACT_SHA256)
        oracle = read_pinned("acceptance_unicode_marks.json", ORACLE_SHA256)
        # This attribute selects an external table; category() is never an oracle.
        version = unicodedata.unidata_version
        if version not in oracle["profiles"]:
            raise AssertionError("Unicode " + version + " needs a separately reviewed property table")
        profile = oracle["profiles"][version]
        ranges = oracle["range_sets"][profile["range_set"]]
        cls.marks = bytearray(cls.contract["exhaustive_classification"]["code_point_count"])
        previous = -2
        for start, end in ranges:
            if not (type(start) is int and type(end) is int and
                    previous + 1 < start <= end < len(cls.marks)):
                raise AssertionError("Unicode mark ranges must be canonical and disjoint")
            cls.marks[start:end + 1] = b"\1" * (end - start + 1)
            previous = end
        if len(ranges) != profile["range_count"] or sum(cls.marks) != profile["mark_count"]:
            raise AssertionError("External Unicode property population differs")
        if any(cls.marks[0xD800:0xE000]):
            raise AssertionError("Lone surrogates are not Unicode marks")

    def test_01_all_code_points_match_external_mark_deletion_property(self):
        rule = self.contract["exhaustive_classification"]
        first, last = rule["interval_inclusive"]
        self.assertEqual((first, last), (0, 0x10FFFF))
        marker = rule["record_marker"]
        left, right = rule["left_anchor"], rule["right_anchor"]
        checked = surrogates = 0
        # One tokenizer call per 4096 points. No million unittest subTest objects,
        # no regular-expression/category oracle, and no upstream corpus at run time.
        for beginning in range(first, last + 1, rule["batch_size"]):
            end = min(beginning + rule["batch_size"], last + 1)
            text = "".join(marker + " " + left + chr(cp) + right + " "
                           for cp in range(beginning, end))
            observed = tokens(text)
            offset = 0
            for cp in range(beginning, end):
                if offset >= len(observed) or observed[offset] != marker:
                    self.fail(f"Tokenizer lost an independent record boundary at U+{cp:04X}")
                offset += 1
                following = offset
                while following < len(observed) and observed[following] != marker:
                    following += 1
                group = observed[offset:following]
                should_delete = bool(self.marks[cp]) or cp == 0x0640
                if (group == rule["expected_deleted_tokens"]) != should_delete:
                    self.fail(f"U+{cp:04X}: external mark/tatweel deletion={should_delete}; tokens={group!r}")
                offset = following
                checked += 1
                surrogates += 0xD800 <= cp <= 0xDFFF
            self.assertEqual(offset, len(observed))
        self.assertEqual(checked, rule["code_point_count"])
        self.assertEqual(surrogates, rule["includes_lone_surrogate_count"])

    def test_02_literal_order_mixed_scripts_and_token_boundaries(self):
        for case in self.contract["literal_cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(tokens(case_input(case)), case["expected_tokens"])

    def test_03_history_and_returned_list_mutation_do_not_change_tokens(self):
        for case in reversed(self.contract["literal_cases"]):
            with self.subTest(case=case["id"]):
                first = tokens(case_input(case))
                self.assertEqual(first, case["expected_tokens"])
                first.append("caller mutation must not be cached")
                self.assertEqual(tokens(case_input(case)), case["expected_tokens"])

    def test_04_actual_catalogue_ranking_matches_existing_frozen_report(self):
        control = self.contract["catalogue_control"]
        raw = (ROOT / control["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), control["raw_sha256"])
        expected = json.loads(raw)["retrieval"]
        index = SearchIndex(root=ROOT)
        self.assertEqual(index.catalog_sha256, control["catalogue_sha256"])
        for query in (control["query"], control["equivalent_query"]):
            with self.subTest(query=query):
                actual = index.search(query, limit=control["limit"], kind=control["kind"])
                self.assertEqual(canonical(actual), canonical(expected))


if __name__ == "__main__":
    unittest.main()
