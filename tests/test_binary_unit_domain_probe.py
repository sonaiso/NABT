"""Executable checks of the proven finite binary grammar, not Arabic learning."""

from __future__ import annotations

from copy import deepcopy
import json
from math import comb
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = {"source_id": 91, "revision": 2, "scope_id": 3, "atomization_id": 4,
          "atoms": ["كَ", "تَ", "بَ"]}
TAG = {"rule_id": 19, "reading_id": 7, "class_id": 23, "requirements": []}


def atom(position):
    return {"op": "atom", "source": deepcopy(SOURCE),
            "before": SOURCE["atoms"][:position], "value": SOURCE["atoms"][position],
            "after": SOURCE["atoms"][position + 1:]}


def join(left, right):
    return {"op": "join", "tag": deepcopy(TAG), "left": left, "right": right}


def witness(tree, identity, positive=True):
    return {"target": deepcopy(tree), "requirement": 0, "positive": positive,
            "witness_id": identity, "supports": [{"source": deepcopy(SOURCE),
            "span": {**{k: v for k, v in SOURCE.items() if k != "atoms"},
                     "start": 0, "stop": 3}}]}


class BinaryUnitDomainProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declared = os.environ.get("NABT_PROGRESSIVE_UNIT_PROBE")
        cls.probe = Path(declared) if declared else ROOT / "formal/.lake/build/bin/progressiveUnitProbe"
        if not cls.probe.is_file():
            if declared:
                raise RuntimeError("Declared Lean probe executable is missing")
            raise unittest.SkipTest("Build progressiveUnitProbe before integration tests")

    def query(self, request):
        run = subprocess.run([str(self.probe)], input=json.dumps(request, ensure_ascii=False) + "\n",
                             text=True, capture_output=True, check=True, timeout=20)
        self.assertEqual(run.stderr, "")
        result = json.loads(run.stdout)
        self.assertEqual(result["law_id"], "nabt.licensed-derivation.v1")
        return result

    def request(self, interpreted=(), offered=None, **extra):
        return {"op": "forest_assess", "source": deepcopy(SOURCE), "tag": deepcopy(TAG),
                "start": 0, "length": 3, "inventory": [deepcopy(SOURCE)],
                "interpreted": deepcopy(list(interpreted)),
                "offered": deepcopy(list(interpreted if offered is None else offered)), **extra}

    def alternatives(self):
        return join(join(atom(0), atom(1)), atom(2)), join(atom(0), join(atom(1), atom(2)))

    def test_all_binary_shapes_match_closed_form_catalan_counts(self):
        for length in range(1, 9):
            with self.subTest(length=length):
                response = self.query({"op": "forest", "shape": "C" * length})
                expected = comb(2 * (length - 1), length - 1) // length
                self.assertEqual(response["count"], expected)
                canonical = [json.dumps(tree, separators=(",", ":")) for tree in response["trees"]]
                self.assertEqual(len(set(canonical)), expected)
                self.assertEqual(response["ranks"], [length - 1] * expected)
                self.assertEqual(response["rank_domain"], "number_of_binary_joins")

    def test_empty_partition_does_not_create_an_empty_binary_unit(self):
        self.assertEqual(self.query({"op": "shape", "shape": ""})["partitions"], [[]])
        self.assertEqual(self.query({"op": "forest", "shape": ""})["trees"], [])

    def test_generated_source_domain_keeps_both_explicit_associations(self):
        response = self.query(self.request())
        left, right = self.alternatives()
        self.assertCountEqual([r["tree"] for r in response["candidates"]], [left, right])
        self.assertEqual(response["candidate_count"], 2)
        self.assertEqual(response["pending_count"], 2)
        self.assertEqual(response["determination"], "UNRESOLVED")
        self.assertIsNone(response["chosen"])
        self.assertIs(response["necessary_within_domain"], False)

    def test_supported_path_with_pending_rival_is_not_unique(self):
        left, _ = self.alternatives()
        positive = [witness(left["left"], 1), witness(left, 2)]
        response = self.query(self.request(positive))
        self.assertEqual((response["licensed_count"], response["pending_count"]), (1, 1))
        self.assertIsNone(response["chosen"])
        self.assertIs(response["necessary_within_domain"], False)

    def test_actual_exhaustion_and_refutation_establish_only_domain_necessity(self):
        left, right = self.alternatives()
        positive = [witness(left["left"], 1), witness(left, 2)]
        negative = witness(right, 3, False)
        # The known negative is deliberately omitted from offered.
        response = self.query(self.request(positive + [negative], positive))
        self.assertEqual((response["licensed_count"], response["rejected_count"]), (1, 1))
        self.assertEqual(response["chosen"], left)
        self.assertIs(response["necessary_within_domain"], True)
        self.assertIs(response["globally_unique"], False)
        self.assertEqual(response["determination"], "UNIQUE_WITHIN_BINARY_DOMAIN")

    def test_withdrawal_recomputes_selection_through_all_children(self):
        left, right = self.alternatives()
        all_receipts = [witness(left["left"], 1), witness(left, 2), witness(right, 3, False)]
        before = self.query(self.request(all_receipts))
        after = self.query(self.request(all_receipts[1:], all_receipts))
        self.assertIs(before["necessary_within_domain"], True)
        self.assertIs(after["necessary_within_domain"], False)
        self.assertEqual(after["determination"], "UNRESOLVED")
        self.assertIsNone(after["chosen"])

    def test_two_licensed_derivations_remain_ambiguous_despite_equal_content(self):
        left, right = self.alternatives()
        receipts = [witness(left["left"], 1), witness(left, 2),
                    witness(right["right"], 3), witness(right, 4)]
        response = self.query(self.request(receipts))
        self.assertEqual(response["licensed_count"], 2)
        self.assertEqual(response["determination"], "AMBIGUOUS")
        self.assertIsNone(response["chosen"])
        self.assertIs(response["necessary_within_domain"], False)

    def test_rejected_and_conflicted_candidates_never_select_an_answer(self):
        left, right = self.alternatives()
        receipts = [witness(left["left"], 1), witness(left, 2),
                    witness(left, 3, False), witness(right, 4, False)]
        response = self.query(self.request(receipts))
        self.assertEqual(response["licensed_count"], 0)
        self.assertEqual(response["rejected_count"], 2)
        self.assertTrue(any(row["conflict"] for row in response["candidates"]))
        self.assertIsNone(response["chosen"])

    def test_caller_complete_flag_and_short_candidate_list_cannot_assert_exhaustion(self):
        left, _ = self.alternatives()
        request = self.request(search_complete=True, candidates=[left], max_atoms=2)
        response = self.query(request)
        self.assertEqual(response["enumeration"], "EXHAUSTED")
        self.assertIs(response["search_complete"], False)
        self.assertIs(response["necessary_within_domain"], False)

    def test_invalid_extent_and_missing_source_are_not_linguistic_refutations(self):
        for extra in ({"length": 0}, {"start": 2, "length": 2}):
            with self.subTest(extra=extra):
                response = self.query(self.request(**extra))
                self.assertEqual(response["error"], "INVALID_INPUT")
        response = self.query(self.request(inventory=[]))
        self.assertEqual(response["invalid_count"], 2)
        self.assertEqual(response["rejected_count"], 0)
        self.assertEqual(response["determination"], "INVALID_SOURCE_CONTEXT")
        self.assertIsNone(response["chosen"])

    def test_repeated_large_tag_cannot_exceed_the_output_budget(self):
        source = {**SOURCE, "atoms": ["C", "V"] * 4}
        large_nat = int("9" * 256)
        tag = {"rule_id": large_nat, "reading_id": large_nat,
               "class_id": large_nat, "requirements": [large_nat] * 32}
        request = self.request(source=source, inventory=[source], tag=tag,
                               length=8, max_atoms=8)
        encoded = (json.dumps(request, separators=(",", ":")) + "\n").encode()
        self.assertLess(len(encoded), 1 << 20)  # Valid input below the input cap.
        run = subprocess.run([str(self.probe)], input=encoded, capture_output=True,
                             check=True, timeout=20)
        self.assertEqual(run.stderr, b"")
        self.assertLessEqual(len(run.stdout), 16 << 20)
        response = json.loads(run.stdout)
        self.assertEqual(response["status"], "ERROR")
        self.assertEqual(response["error"], "RESOURCE_LIMIT")
        self.assertIs(response["search_complete"], False)

    def test_ordinary_eight_leaf_source_forest_remains_complete(self):
        source = {**SOURCE, "atoms": ["C", "V"] * 4}
        response = self.query(self.request(source=source, inventory=[source],
                                           length=8, max_atoms=8))
        self.assertEqual(response["status"], "OK")
        self.assertEqual(response["enumeration"], "COMPLETE")
        self.assertIs(response["search_complete"], True)
        self.assertEqual(response["candidate_count"], 429)
        self.assertEqual(response["pending_count"], 429)
        self.assertIs(response["necessary_within_domain"], False)


if __name__ == "__main__":
    unittest.main()
