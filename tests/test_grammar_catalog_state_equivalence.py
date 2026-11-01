"""Independent controls for reusing the existing typed state comparator.

Literal expectations are frozen before the routing optimization. Small owner
fixtures isolate structural comparison; the installed-source control and the
unchanged operator-context suite carry the separate source-replay obligation.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from nabt.corpus_sources import _same_json
from tools.grammar_catalog import catalog, routing
from tools.grammar_catalog.retrieval import RetrievalError, SearchIndex


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/operator_context_v1/performance_followup_v2"
CONTRACT_SHA256 = "e1d025291c6960c596240ea5827b8335212f8ea0787f1501e64a43d59414bd4b"


class DictSubclass(dict):
    pass


class ListSubclass(list):
    pass


class StringSubclass(str):
    pass


class IntegerSubclass(int):
    pass


class CounterSubclass(Counter):
    pass


class EqualityTrap:
    calls = 0
    __hash__ = object.__hash__

    def __eq__(self, other):
        type(self).calls += 1
        return True

    def __ne__(self, other):
        type(self).calls += 1
        return False


@contextmanager
def decimal_limit(limit):
    original = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(limit)
    try:
        yield
    finally:
        sys.set_int_max_str_digits(original)


class StateEquivalenceAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (EVIDENCE / "acceptance_contract.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != CONTRACT_SHA256:
            raise AssertionError("Frozen source-index state expectations changed")
        cls.contract = json.loads(raw)
        cls.fixture = cls.contract["fixture"]
        cls.key = tuple(cls.fixture["document_key"])
        # Check the authored reference domain; outcomes below are literal gold.
        catalog._canonical(cls.fixture["row"])
        catalog._canonical(cls.fixture["frequencies"])

    @contextmanager
    def owner_fixture(self):
        fixture, key = self.fixture, self.key
        calls = []
        source = {"failure": None}

        class FixtureIndex:
            def __init__(self, supplied=None, *, root=Path(fixture["root"])):
                calls.append((supplied, root))
                if source["failure"] is not None:
                    raise source["failure"]
                if supplied is not None and supplied != fixture["catalogue"]:
                    raise catalog.CatalogError("authored source fixture differs")
                if root != Path(fixture["root"]):
                    raise catalog.CatalogError("authored source fixture root differs")
                self._root = root
                self._catalog = deepcopy(fixture["catalogue"])
                self.catalog_sha256 = fixture["advertised_digest"]
                self._docs = {key: deepcopy(fixture["row"])}
                self._tf = {key: Counter(fixture["frequencies"])}

        index = FixtureIndex()
        calls.clear()
        with patch.object(routing, "SearchIndex", FixtureIndex):
            yield index, calls, source

    def mutate_document(self, index, name):
        row = index._docs[self.key]
        record = row["record"]
        if name == "equal_original":
            return
        if name == "reordered_row_keys":
            index._docs[self.key] = dict(reversed(list(row.items())))
        elif name == "reordered_record_keys":
            row["record"] = dict(reversed(list(record.items())))
        elif name == "shared_equal_values":
            record["pair"][1] = record["pair"][0]
        elif name == "changed_search_text":
            row["search_text"] += " forged"
        elif name == "normalized_search_text":
            row["search_text"] = "الف باء باء"
        elif name == "changed_record":
            record["authority"] = "caller claim"
        elif name == "extra_record_key":
            record["approved"] = True
        elif name == "missing_record_key":
            del record["optional"]
        elif name == "reversed_list":
            record["parts"].reverse()
        elif name == "integer_for_boolean":
            record["enabled"] = 1
        elif name == "boolean_for_integer":
            record["count"] = True
        elif name == "integer_for_nested_false":
            record["nested"]["y"] = 0
        elif name in ("float_for_integer", "nan", "infinity"):
            record["count"] = {"float_for_integer": 1.0, "nan": float("nan"),
                               "infinity": float("inf")}[name]
        elif name == "tuple_for_list":
            record["parts"] = tuple(record["parts"])
        elif name == "dict_subclass":
            row["record"] = DictSubclass(record)
        elif name == "list_subclass":
            record["parts"] = ListSubclass(record["parts"])
        elif name == "string_subclass":
            row["search_text"] = StringSubclass(row["search_text"])
        elif name == "integer_subclass":
            record["count"] = IntegerSubclass(1)
        elif name == "custom_equality_value":
            record["count"] = EqualityTrap()
        elif name == "custom_equality_key":
            del record["count"]
            record[EqualityTrap()] = 1
        elif name == "nonstring_record_key":
            record[7] = "not a JSON object key"
        elif name == "surrogate_text":
            row["search_text"] = "\ud800"
        elif name == "surrogate_key":
            record["\ud800"] = None
        elif name == "bytes_text":
            row["search_text"] = b"not an ordinary JSON string"
        elif name == "cycle":
            record["nested"]["y"] = record["nested"]
        elif name == "deep_forged_value":
            value = 1
            for _ in range(self.contract["bounded_probe_parameters"]["forged_depth"]):
                value = [value]
            record["count"] = value
        elif name == "decimal_integer_limit":
            record["count"] = 10 ** self.contract["bounded_probe_parameters"]["oversized_integer_power"]
        else:
            self.fail("Unimplemented frozen document case: " + name)

    def mutate_frequency(self, index, name):
        counter = index._tf[self.key]
        if name == "equal_original":
            return
        if name == "reordered_terms":
            index._tf[self.key] = Counter(dict(reversed(list(counter.items()))))
        elif name == "extra_zero_term":
            counter["extra"] = 0
        elif name == "extra_negative_term":
            counter["extra"] = -1
        elif name == "missing_term":
            del counter["الف"]
        elif name == "changed_positive_count":
            counter["الف"] = 2
        elif name == "negative_count":
            counter["الف"] = -1
        elif name == "zero_count":
            counter["الف"] = 0
        elif name == "boolean_count":
            counter["الف"] = True
        elif name == "float_count":
            counter["الف"] = 1.0
        elif name == "nan_count":
            counter["الف"] = float("nan")
        elif name == "integer_subclass_count":
            counter["الف"] = IntegerSubclass(1)
        elif name == "nonstring_term":
            counter[7] = 1
        elif name == "string_subclass_term":
            index._tf[self.key] = Counter({StringSubclass("الف"): 1, "باء": 2})
        elif name == "surrogate_term":
            counter["\ud800"] = 1
        elif name == "custom_equality_count":
            counter["الف"] = EqualityTrap()
        elif name == "plain_dict":
            index._tf[self.key] = dict(counter)
        elif name == "counter_subclass":
            index._tf[self.key] = CounterSubclass(counter)
        else:
            self.fail("Unimplemented frozen frequency case: " + name)

    def check_guard(self, index, calls, case):
        before_docs, before_frequencies = index._docs, index._tf
        if case["expected"] == "ACCEPT":
            fresh = routing._fresh_index(index)
            self.assertIsNot(fresh, index)
            self.assertIsNot(fresh._docs, index._docs)
            self.assertIsNot(fresh._tf, index._tf)
            self.assertEqual(fresh.catalog_sha256, self.fixture["advertised_digest"])
        else:
            with self.assertRaises(RetrievalError) as caught:
                routing._fresh_index(index)
            self.assertEqual(str(caught.exception), self.contract["errors"][case["error"]])
        self.assertEqual(len(calls), 1, "Fresh owner must be reconstructed for each comparison")
        self.assertIs(calls[0][0], index._catalog)
        self.assertEqual(calls[0][1], index._root)
        self.assertIs(index._docs, before_docs)
        self.assertIs(index._tf, before_frequencies)
        self.assertEqual(EqualityTrap.calls, 0, "Custom equality must not authorize a row")

    def test_01_document_relation_and_existing_guard_match_literal_expectations(self):
        for case in self.contract["document_cases"]:
            with self.subTest(case=case["id"]), self.owner_fixture() as (index, calls, _):
                self.mutate_document(index, case["id"])
                EqualityTrap.calls = 0
                with decimal_limit(self.contract["bounded_probe_parameters"]["decimal_conversion_limit"]):
                    self.assertIs(_same_json(index._docs[self.key], self.fixture["row"]),
                                  case["expected"] == "ACCEPT")
                    self.check_guard(index, calls, case)

    def test_02_counter_contents_and_container_type_remain_distinct(self):
        for case in self.contract["frequency_cases"]:
            with self.subTest(case=case["id"]), self.owner_fixture() as (index, calls, _):
                self.mutate_frequency(index, case["id"])
                EqualityTrap.calls = 0
                if type(index._tf[self.key]) is Counter:
                    self.assertIs(_same_json(dict(index._tf[self.key]), self.fixture["frequencies"]),
                                  case["expected"] == "ACCEPT")
                self.check_guard(index, calls, case)

    def test_03_complete_collections_and_repeated_source_failure_are_checked(self):
        for case in self.contract["collection_cases"]:
            with self.subTest(case=case["id"]), self.owner_fixture() as (index, calls, _):
                name = case["id"]
                if name == "missing_document":
                    del index._docs[self.key]
                elif name == "extra_document":
                    index._docs[("rule", "fixture::extra")] = deepcopy(self.fixture["row"])
                elif name == "document_map_subclass":
                    index._docs = DictSubclass(index._docs)
                elif name == "missing_frequency_row":
                    del index._tf[self.key]
                elif name == "frequency_map_subclass":
                    index._tf = DictSubclass(index._tf)
                else:
                    self.fail("Unimplemented frozen collection case: " + name)
                EqualityTrap.calls = 0
                self.check_guard(index, calls, dict(case, expected="REJECT"))
        with self.owner_fixture() as (index, calls, source):
            routing._fresh_index(index)
            failure = catalog.CatalogError("authored source withdrawn after first read")
            source["failure"] = failure
            with self.assertRaises(catalog.CatalogError) as caught:
                routing._fresh_index(index)
            self.assertIs(caught.exception, failure)
            self.assertEqual(len(calls), 2)

    def test_04_installed_state_reconstruction_preserves_archived_retrieval(self):
        control = self.contract["installed_control"]
        raw = (ROOT / control["archive_path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), control["archive_raw_sha256"])
        expected = json.loads(raw)["retrieval"]
        index = SearchIndex(root=ROOT)
        fresh = routing._fresh_index(index)
        self.assertIsNot(fresh, index)
        self.assertIsNot(fresh._docs, index._docs)
        self.assertIsNot(fresh._tf, index._tf)
        self.assertEqual(fresh.catalog_sha256, control["catalogue_sha256"])
        actual = fresh.search(control["query"], kind=control["kind"], limit=control["limit"])
        encode = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.assertEqual(encode(actual), encode(expected))


if __name__ == "__main__":
    unittest.main()
