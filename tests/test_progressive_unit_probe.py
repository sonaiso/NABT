"""Adversarial integration checks for the new Lean construction/shape adapter.

These authored contract regressions are not a held-out Arabic acquisition
evaluation. Build ``progressiveUnitProbe`` first. An explicitly configured
NABT_PROGRESSIVE_UNIT_PROBE must exist; Python-only discovery may skip when
the optional Lean executable has not been built.
"""

from __future__ import annotations

from copy import deepcopy
from itertools import combinations
import json
import math
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def source(atoms, *, source_id=1, revision=1):
    return {"source_id": source_id, "revision": revision, "scope_id": 7,
            "atomization_id": 3, "atoms": list(atoms)}


def atomic(origin, index):
    return {"op": "atom", "source": deepcopy(origin),
            "before": origin["atoms"][:index], "value": origin["atoms"][index],
            "after": origin["atoms"][index + 1:]}


def tag(class_id=10, *, rule_id=8, reading_id=4, requirements=()):
    return {"rule_id": rule_id, "reading_id": reading_id, "class_id": class_id,
            "requirements": list(requirements)}


def join(left, right, **metadata):
    return {"op": "join", "tag": tag(**metadata), "left": left, "right": right}


def unary(operation, child, *, replacement=None, **metadata):
    result = {"op": operation, "tag": tag(**metadata), "child": child}
    if operation == "substitute":
        result["replacement"] = list(replacement)
    return result


WITNESS_SOURCE = source(["independent premise"], source_id=90)


def receipt(target, *, witness_id=100, positive=True, requirement=0):
    premise = deepcopy(WITNESS_SOURCE)
    extent = {name: premise[name] for name in
              ("source_id", "revision", "scope_id", "atomization_id")}
    extent.update(start=0, stop=1)
    return {"target": deepcopy(target), "requirement": requirement,
            "positive": positive, "witness_id": witness_id,
            "supports": [{"source": premise, "span": extent}]}


def request(target, origin, interpreted=(), *, offered=None, seen=None):
    result = {"op": "derive", "tree": deepcopy(target),
              "inventory": [deepcopy(origin), deepcopy(WITNESS_SOURCE)],
              "interpreted": deepcopy(list(interpreted)),
              "offered": deepcopy(list(interpreted if offered is None else offered))}
    if seen is not None:
        result["seen"] = list(seen)
    return result


class ProgressiveUnitProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declared = os.environ.get("NABT_PROGRESSIVE_UNIT_PROBE")
        cls.probe = Path(declared) if declared else ROOT / "formal/.lake/build/bin/progressiveUnitProbe"
        if not cls.probe.is_file():
            if declared:
                raise RuntimeError("Declared Lean probe executable is missing: " + str(cls.probe))
            raise unittest.SkipTest("Build progressiveUnitProbe before Lean integration tests")

    def raw_queries(self, payload):
        run = subprocess.run([str(self.probe)], input=payload, capture_output=True,
                             check=True, timeout=20)
        self.assertEqual(run.stderr, b"")
        replies = [json.loads(line) for line in run.stdout.splitlines()]
        for reply in replies:
            self.assertEqual(reply["law_id"], "nabt.licensed-derivation.v1")
            self.assertEqual(reply["scope"], "conditional_on_supplied_interpretations")
            self.assertIs(reply["conditional"], True)
            self.assertIs(reply["acquisition_measured"], False)
        return replies

    def queries(self, *requests):
        payload = "".join(json.dumps(value, ensure_ascii=False) + "\n" for value in requests)
        replies = self.raw_queries(payload.encode("utf-8"))
        self.assertEqual(len(replies), len(requests))
        return replies

    def query(self, value):
        reply, = self.queries(value)
        return reply

    def fixture(self):
        origin = source(["C", "V"])
        target = join(atomic(origin, 0), atomic(origin, 1))
        return origin, target

    def test_atomic_base_requires_the_complete_registered_source(self):
        origin = source(["a", "b", "c"])
        target = atomic(origin, 1)
        valid = request(target, origin)
        absent = deepcopy(valid)
        absent["inventory"] = []
        good, missing = self.queries(valid, absent)
        self.assertEqual(good["verdict"], "LICENSED")
        self.assertEqual(good["extent"], [1, 2])
        self.assertEqual(good["raw"], ["b"])
        self.assertEqual(good["before"], ["a"])
        self.assertEqual(good["after"], ["c"])
        self.assertEqual(good["reconstruction"], origin["atoms"])
        self.assertEqual(good["rank"], 0)
        self.assertEqual(missing["verdict"], "INVALID_DERIVATION")

    def test_exact_flattening_does_not_license_a_join_without_premises(self):
        origin, target = self.fixture()
        result = self.query(request(target, origin))
        self.assertIs(result["structural"], True)
        self.assertIs(result["reconstruction_matches"], True)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIs(result["licensed"], False)
        self.assertEqual(result["necessity"], "NOT_ESTABLISHED_BY_A_SINGLE_DERIVATION")

    def test_complete_exact_target_witness_licenses_the_join(self):
        origin, target = self.fixture()
        result = self.query(request(target, origin, [receipt(target)]))
        self.assertEqual(result["verdict"], "LICENSED")
        self.assertEqual(result["rank"], 1)
        self.assertEqual(result["extent"], [0, 2])
        self.assertEqual(result["output"], ["C", "V"])
        self.assertEqual(result["undo_source"], origin["atoms"])
        self.assertEqual(result["premise_steps"][0]["offered_admitted_ids"], [100])

    def test_supported_parent_does_not_bypass_an_unsupported_child(self):
        origin, child = self.fixture()
        parent = unary("wrap", child, class_id=20)
        result = self.query(request(parent, origin, [receipt(parent)]))
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIs(result["premise_steps"][0]["positive_complete"], True)
        self.assertIs(result["premise_steps"][1]["positive_complete"], False)

    def test_negative_child_blocks_parent_even_when_parent_has_support(self):
        origin, child = self.fixture()
        parent = unary("wrap", child, class_id=20)
        child_yes = receipt(child, witness_id=101)
        parent_yes = receipt(parent, witness_id=102)
        child_no = receipt(child, witness_id=103, positive=False)
        result = self.query(request(parent, origin, [child_yes, parent_yes, child_no],
                                    offered=[child_yes, parent_yes]))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertIs(result["conflict"], True)
        self.assertEqual(result["premise_steps"][1]["known_negative_ids"], [103])

    def test_known_negative_cannot_be_hidden_by_omitting_it_from_offered(self):
        origin, target = self.fixture()
        yes = receipt(target, witness_id=201)
        no = receipt(target, witness_id=202, positive=False)
        complete, omitted = self.queries(request(target, origin, [yes, no]),
                                         request(target, origin, [yes, no], offered=[yes]))
        for result in (complete, omitted):
            self.assertEqual(result["verdict"], "REJECTED")
            self.assertIs(result["conflict"], True)
            self.assertEqual(result["premise_steps"][0]["known_negative_ids"], [202])
        self.assertEqual(omitted["premise_steps"][0]["offered_admitted_ids"], [201])

    def test_receipt_binding_includes_each_target_component(self):
        origin, target = self.fixture()
        mutations = []
        for field in ("rule_id", "reading_id", "class_id"):
            altered = deepcopy(target)
            altered["tag"][field] += 1
            mutations.append(altered)
        altered = deepcopy(target)
        altered["tag"]["requirements"] = [5]
        mutations.append(altered)
        altered = deepcopy(target)
        altered["left"]["source"]["revision"] += 1
        mutations.append(altered)
        altered = deepcopy(target)
        altered["left"], altered["right"] = altered["right"], altered["left"]
        mutations.append(altered)
        for result in self.queries(*(request(target, origin, [receipt(value)]) for value in mutations)):
            self.assertEqual(result["verdict"], "UNKNOWN")
            self.assertEqual(result["premise_steps"][0]["offered_admitted_ids"], [])

    def test_each_declared_requirement_is_needed(self):
        origin, target = self.fixture()
        target["tag"]["requirements"] = [7]
        mandatory = receipt(target, witness_id=301)
        extra = receipt(target, witness_id=302, requirement=7)
        missing, complete = self.queries(request(target, origin, [mandatory]),
                                         request(target, origin, [mandatory, extra]))
        self.assertEqual(missing["verdict"], "UNKNOWN")
        self.assertEqual(complete["verdict"], "LICENSED")

    def test_offered_receipt_without_interpretation_has_no_authority(self):
        origin, target = self.fixture()
        result = self.query(request(target, origin, [], offered=[receipt(target)]))
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(result["premise_steps"][0]["offered_admitted_ids"], [])

    def test_support_needs_nonempty_registered_in_bounds_provenance(self):
        origin, target = self.fixture()
        invalid = []
        empty = receipt(target)
        empty["supports"] = []
        invalid.append(empty)
        wrong_revision = receipt(target)
        wrong_revision["supports"][0]["span"]["revision"] += 1
        invalid.append(wrong_revision)
        outside = receipt(target)
        outside["supports"][0]["span"]["stop"] = 2
        invalid.append(outside)
        forged_source = receipt(target)
        forged_source["supports"][0]["source"]["atoms"] = ["different premise"]
        invalid.append(forged_source)
        for result in self.queries(*(request(target, origin, [value]) for value in invalid)):
            self.assertEqual(result["verdict"], "UNKNOWN")

    def test_join_requires_original_adjacency_without_gaps_or_overlap(self):
        origin = source(["a", "gap", "b"])
        gap = join(atomic(origin, 0), atomic(origin, 2))
        overlap = join(atomic(origin, 0), atomic(origin, 0))
        for result in self.queries(request(gap, origin, [receipt(gap)]),
                                   request(overlap, origin, [receipt(overlap)])):
            self.assertEqual(result["verdict"], "INVALID_DERIVATION")
            self.assertIs(result["licensed"], False)

    def test_equal_bytes_from_different_revisions_do_not_join(self):
        origin, target = self.fixture()
        target["right"]["source"]["revision"] = 2
        payload = request(target, origin, [receipt(target)])
        payload["inventory"].append(deepcopy(target["right"]["source"]))
        result = self.query(payload)
        self.assertEqual(result["verdict"], "INVALID_DERIVATION")

    def test_substitution_deletion_retains_raw_and_rejects_forged_current_output(self):
        origin = source(["before", "removed", "after"])
        target = unary("substitute", atomic(origin, 1), replacement=[], class_id=30)
        valid, forged = self.queries(request(target, origin, [receipt(target)]),
                                     request(target, origin, [receipt(target)], seen=["invented"]))
        self.assertEqual(valid["verdict"], "LICENSED")
        self.assertEqual(valid["output"], [])
        self.assertEqual(valid["raw"], ["removed"])
        self.assertEqual(valid["extent"], [1, 2])
        self.assertEqual(valid["undo_source"], origin["atoms"])
        self.assertIsNone(forged["undo_raw"])
        self.assertIsNone(forged["undo_source"])

    def test_no_op_substitution_and_same_class_lift_are_invalid(self):
        origin, child = self.fixture()
        noop_sub = unary("substitute", atomic(origin, 0), replacement=["C"])
        noop_lift = unary("lift", child, class_id=10)
        results = self.queries(request(noop_sub, origin, [receipt(noop_sub)]),
                               request(noop_lift, origin, [receipt(child), receipt(noop_lift)]))
        self.assertEqual([value["verdict"] for value in results],
                         ["INVALID_DERIVATION", "INVALID_DERIVATION"])

    def test_each_constructor_increases_rank_and_keeps_original_source(self):
        origin, joined = self.fixture()
        wrapped = unary("wrap", joined, class_id=20)
        changed = unary("substitute", wrapped, replacement=["CV"], class_id=30)
        lifted = unary("lift", changed, class_id=40)
        witnesses = [receipt(value, witness_id=400 + index)
                     for index, value in enumerate((joined, wrapped, changed, lifted))]
        result = self.query(request(lifted, origin, witnesses))
        self.assertEqual(result["verdict"], "LICENSED")
        self.assertEqual(result["rank"], 4)
        self.assertEqual([step["rank"] for step in result["premise_steps"]], [4, 3, 2, 1])
        self.assertEqual(result["raw"], ["C", "V"])
        self.assertEqual(result["output"], ["CV"])
        self.assertEqual(result["undo_source"], origin["atoms"])

    def test_unit_key_preserves_occurrence_without_erasing_alternative_trees(self):
        origin = source(["same", "same"])
        atom = atomic(origin, 0)
        wrapped = unary("wrap", atom, class_id=12)
        lifted = unary("lift", atom, class_id=12)
        alternate, repeated = self.queries({"op": "compare", "left": wrapped, "right": lifted},
                                           {"op": "compare", "left": atom, "right": atomic(origin, 1)})
        self.assertIs(alternate["same_unit_key"], True)
        self.assertIs(alternate["same_derivation"], False)
        self.assertIs(repeated["same_output"], True)
        self.assertIs(repeated["same_occurrence"], False)
        self.assertIs(repeated["same_unit_key"], False)

    def test_caller_acceptance_flags_do_not_substitute_for_evidence(self):
        origin, target = self.fixture()
        payload = request(target, origin)
        payload.update(licensed=True, verified=True, necessity=True, search_complete=True)
        result = self.query(payload)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIs(result["licensed"], False)

    def test_bool_and_noncanonical_numbers_are_not_natural_identifiers(self):
        origin, target = self.fixture()
        payload = request(target, origin)
        payload["tree"]["tag"]["class_id"] = True
        bad = [json.dumps(payload).encode() + b"\n"]
        for value in (b"true", b"-1", b"1.0", b"1e1", b"01"):
            bad.append(b'{"op":"quota","consonants":' + value + b',"vowels":1}\n')
        results = self.raw_queries(b"".join(bad))
        self.assertEqual(len(results), len(bad))
        for result in results:
            self.assertEqual(result["error"], "INVALID_INPUT")

    def test_unicode_surrogate_errors_do_not_alias_valid_source_atoms(self):
        origin = source(["TOKEN"])
        payload = json.dumps(request(atomic(origin, 0), origin)).encode()
        bad = payload.replace(b"TOKEN", br"\ud800") + b"\n"
        pair = payload.replace(b"TOKEN", br"\ud83d\ude00") + b"\n"
        invalid, valid = self.raw_queries(bad + pair)
        self.assertEqual(invalid["error"], "INVALID_INPUT")
        self.assertEqual(valid["verdict"], "LICENSED")
        self.assertEqual(valid["raw"], ["😀"])

    def test_bad_input_line_isolated_from_the_next_valid_request(self):
        replies = self.raw_queries(b'{"op":"alphabet","bad":"\xff"}\n' +
                                   b'{"op":\n' + b'{"op":"alphabet"}\n')
        self.assertEqual(len(replies), 3)
        self.assertEqual(replies[0]["error"], "INVALID_INPUT")
        self.assertEqual(replies[1]["error"], "INVALID_INPUT")
        self.assertEqual(replies[2]["status"], "OK")

    def test_ordered_quota_enumeration_matches_independent_position_subsets(self):
        for consonants, vowels in ((0, 0), (2, 1), (2, 2), (3, 2), (3, 3)):
            with self.subTest(consonants=consonants, vowels=vowels):
                total = consonants + vowels
                expected = set()
                for positions in combinations(range(total), consonants):
                    c_positions = set(positions)
                    expected.add("".join("C" if index in c_positions else "V" for index in range(total)))
                result = self.query({"op": "quota", "consonants": consonants, "vowels": vowels})
                self.assertEqual(set(result["shapes"]), expected)
                self.assertEqual(result["count"], math.comb(total, consonants))
                self.assertEqual(len(set(result["shape_numbers"])), result["count"])
                self.assertIs(result["linguistic_license_inferred"], False)

    def test_equal_cv_counts_preserve_order_and_each_contiguous_partition(self):
        cvvc, cvcv, cvc = self.queries({"op": "shape", "shape": "CVVC"},
                                      {"op": "shape", "shape": "CVCV"},
                                      {"op": "shape", "shape": "CVC"})
        self.assertEqual((cvvc["consonants"], cvvc["vowels"]), (2, 2))
        self.assertEqual((cvcv["consonants"], cvcv["vowels"]), (2, 2))
        self.assertNotEqual(cvvc["shape_n"], cvcv["shape_n"])
        self.assertEqual(cvvc["decoded"], "CVVC")
        self.assertEqual(cvvc["partition_count"], 8)
        self.assertEqual({tuple(parts) for parts in cvc["partitions"]},
                         {("CVC",), ("C", "VC"), ("CV", "C"), ("C", "V", "C")})

    def test_budget_exhaustion_is_not_rejection_or_completion(self):
        exhausted, hard_limit = self.queries({"op": "quota", "consonants": 3, "vowels": 3,
                                              "max_atoms": 5},
                                             {"op": "quota", "consonants": 1, "vowels": 1,
                                              "max_atoms": 13})
        self.assertEqual(exhausted["enumeration"], "EXHAUSTED")
        self.assertIs(exhausted["search_complete"], False)
        self.assertIs(exhausted["linguistic_rejection"], False)
        self.assertNotIn("shapes", exhausted)
        self.assertEqual(hard_limit["error"], "RESOURCE_LIMIT")

    def test_quantity_is_declared_and_vv_does_not_acquire_length(self):
        c = {"kind": "consonant", "id": 1}
        long = {"kind": "vowel", "quality": 0, "quantity": "long"}
        short = {"kind": "vowel", "quality": 0, "quantity": "short"}
        long_result, two_short = self.queries({"op": "quantity", "segments": [c, long, c]},
                                              {"op": "quantity", "segments": [c, short, short, c]})
        for result in (long_result, two_short):
            self.assertEqual(result["shape"], "CVVC")
            self.assertIs(result["source_aligned_license"], False)
            self.assertIs(result["long_vowel_inferred_from_vv"], False)
        self.assertEqual(long_result["segments"], 3)
        self.assertEqual(two_short["segments"], 4)

    def test_a116_cells_and_compound_effect_keep_their_own_domains(self):
        alphabet, initial, dead, compound_as_cell = self.queries(
            {"op": "alphabet"},
            {"op": "cell_effect", "cells": [84], "mode": "waqf", "entry": 0},
            {"op": "cell_effect", "cells": [84], "mode": "waqf", "entry": 96},
            {"op": "cell_effect", "cells": [9864], "mode": "waqf", "entry": 0})
        self.assertEqual(alphabet["cells"], 116)
        self.assertEqual(alphabet["non_sukun_cells"], 87)
        self.assertEqual(alphabet["sukun_cells"], 29)
        self.assertIs(alphabet["all_cells_are_phonetic_cv"], False)
        self.assertEqual(initial["unit_n"], 85)
        self.assertEqual(initial["exit"], 1)
        self.assertEqual(dead["exit"], 96)
        self.assertEqual(len(initial["effect"]), 97)
        self.assertIs(initial["lexical_attestation_inferred"], False)
        self.assertEqual(compound_as_cell["error"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
