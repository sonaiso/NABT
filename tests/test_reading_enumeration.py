"""Finite independent oracles and adversarial native enumeration contracts.

These are authored engineering cases, not held-out Arabic acquisition scores.
The Lean theorems quantify over arbitrary finite pools; Python tests exercise
their native/JSON adapter and integration with fresh free-reader reports.
"""
from copy import deepcopy
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import mantuq_mafhum as mm
from tools import source_semantics as bridge

ROOT = mm.ROOT
TRAINING = (ROOT / "examples/discourse_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/discourse_context.json").read_text())
BINDING = {"source": "أنا عالم. أنا كاتب.", "source_id": "source", "scope": "scope",
           "context": "{}", "lexicon": "independently specified test premises"}


def atom(name):
    return {"kind": "atom", "concept": name, "args": []}


def premise(index):
    return {"kind": "premise", "index": index}


def alternative(ps, identity="same-label", binding=None):
    # Reusing a label must NOT merge alternatives or source evidence.
    return {"reading_id": identity, "binding": binding or BINDING, "premises": ps}


def request(pools, proofs, target=None):
    return {"op": "meaning_enumeration", "expected": BINDING, "pools": pools,
            "conclusion": target or atom("A"), "proofs": proofs}


class EnumerationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.probe = bridge.executable()
        except RuntimeError:
            if "NABT_CLASSICAL_SEMANTIC_PROBE" in os.environ:
                raise
            raise unittest.SkipTest("build classicalSemanticProbe for native enumeration checks")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source_path = Path(self.temp.name) / "source.txt"
        self.source_path.write_bytes(BINDING["source"].encode())
        self.source = {"local_path": str(self.source_path), "source_id": BINDING["source_id"],
                       "edition": "test", "revision": "1", "work": "target"}

    def native(self, requests):
        return bridge.native(requests, source=self.source, probe=self.probe)

    def test_two_by_three_choices_are_six_even_with_duplicate_labels(self):
        a = atom("A")
        pools = [[alternative([a])] * 2, [alternative([a])] * 3]
        row = self.native([request(pools, [premise(0)] * 6)])[0]
        self.assertTrue(row["checked"])
        self.assertEqual(row["combinations"], 6)
        self.assertEqual(row["pool_sizes"], [2, 3])
        self.assertTrue(row["supplied_pool_composition_proved"])
        for key in ["reader_enumeration_proved", "pool_completeness_proved", "python_projection_proved",
                    "world_truth_established", "premise_truth_established", "all_arabic_complete"]:
            self.assertFalse(row[key])

    def test_missing_extra_and_invalid_last_certificate_reject(self):
        a = atom("A")
        pools = [[alternative([a])] * 2, [alternative([a])] * 3]
        cases = [[premise(0)] * 5, [premise(0)] * 7, [premise(0)] * 5 + [premise(99)]]
        self.assertTrue(all(not r["checked"] for r in self.native([request(pools, ps) for ps in cases])))

    def test_empty_document_pool_and_premises_never_vacuously_pass(self):
        cases = [([], []), ([], [premise(0)]), ([[]], []),
                 ([[alternative([atom("A")])], []], []), ([[alternative([])]], [premise(0)])]
        self.assertTrue(all(not r["checked"] for r in self.native([request(p, ps) for p, ps in cases])))

    def test_incomplete_rival_is_retained_and_blocks(self):
        pools = [[alternative([atom("A")]), alternative(None)], [alternative([atom("A")])]]
        row = self.native([request(pools, [premise(0), premise(0)])])[0]
        self.assertEqual(row["combinations"], 2)
        self.assertFalse(row["checked"])

    def test_source_context_lexicon_and_scope_are_exact(self):
        cases = []
        for key in BINDING:
            changed = {**BINDING, key: BINDING[key] + "changed"}
            cases.append(request([[alternative([atom("A")]), alternative([atom("A")], binding=changed)]],
                                 [premise(0), premise(0)]))
        self.assertTrue(all(not r["checked"] for r in self.native(cases)))

    def test_native_reopens_source_and_does_not_normalize_it(self):
        r = request([[alternative([atom("A")])]], [premise(0)])
        for raw in [BINDING["source"].encode() + b" ", BINDING["source"].encode() + b"\xff"]:
            self.source_path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "INVALID_INPUT"):
                self.native([r])
        self.source_path.write_bytes(BINDING["source"].encode())
        self.source["source_id"] = "changed"
        with self.assertRaisesRegex(ValueError, "INVALID_INPUT"):
            self.native([r])
        with self.assertRaisesRegex(ValueError, "independently opened"):
            bridge.native([r], probe=self.probe)

    def test_derivation_across_pools_preserves_all_combinations(self):
        a, b, c = map(atom, "ABC")
        rule = {"kind": "implies", "left": {"kind": "both", "left": a, "right": b}, "right": c}
        proof = {"kind": "apply", "rule": premise(2),
                 "argument": {"kind": "pair", "left": premise(0), "right": premise(1)}}
        pools = [[alternative([a]), alternative([a])], [alternative([b])], [alternative([rule])]]
        row = self.native([request(pools, [proof, proof], c)])[0]
        self.assertTrue(row["checked"])
        self.assertEqual(row["conclusion"], c)
        # An implication's consequent does not provide its antecedent.
        inverse = request([[alternative([c])], [alternative([rule])]],
                          [{"kind": "apply", "rule": premise(1), "argument": premise(0)}], a)
        self.assertFalse(self.native([inverse])[0]["checked"])

    def test_independent_closed_form_universal_or_oracle(self):
        # For independent pools of atomic alternatives: A occurs in every
        # selection iff at least one entire pool contains A. This oracle does
        # not enumerate, concatenate, or invoke the production proof checker.
        cases, expected = [], []
        for mask in range(64):
            flags = [bool(mask & (1 << n)) for n in range(6)]
            pools = [[alternative([atom("A" if flags[2*i+j] else "B")]) for j in range(2)] for i in range(3)]
            proofs = []
            for indices in product(range(2), repeat=3):
                present = [flags[2*i+j] for i, j in enumerate(indices)]
                proofs.append(premise(present.index(True) if any(present) else 3))
            cases.append(request(pools, proofs))
            expected.append(any(flags[i] and flags[i+1] for i in (0, 2, 4)))
        self.assertEqual([r["checked"] for r in self.native(cases)], expected)

    def test_permuting_pools_requires_reindexing_proofs(self):
        pools = [[alternative([atom("A")])], [alternative([atom("B")])]]
        rows = self.native([request(pools, [premise(0)]), request(pools[::-1], [premise(0)]),
                            request(pools[::-1], [premise(1)])])
        self.assertEqual([r["checked"] for r in rows], [True, False, True])

    def test_full_qualified_claim_and_force_are_not_erased(self):
        base = {"force": "ASSERT", "question_kind": None, "assertion_allowed": True}
        claim = {"predicate": "عالم", "args": ["zayd"], "time": "اليوم", "positive": True,
                 "place": "هنا", "restriction": ["only"], "tense": "past"}
        original = mm.claim_formula(base, claim)
        variants = [mm.claim_formula({**base, "force": "QUESTION"}, claim)]
        variants += [mm.claim_formula(base, {**claim, key: None}) for key in claim]
        rows = self.native([request([[alternative([original]), alternative([f])]], [premise(0)] * 2, original)
                            for f in variants])
        self.assertTrue(all(not r["checked"] for r in rows))

    def test_resource_boundary_checks_all_4096_or_returns_no_verdict(self):
        pool = [alternative([atom("A")])] * 2
        row = self.native([request([pool] * 12, [premise(0)] * 4096)])[0]
        self.assertTrue(row["checked"])
        self.assertEqual(row["combinations"], 4096)
        with self.assertRaisesRegex(ValueError, "RESOURCE_LIMIT"):
            self.native([request([pool] * 13, [])])

    def test_late_empty_pool_short_circuits_a_huge_empty_product(self):
        pool = [alternative([atom("A")])] * 128
        for pools in [[[]] + [pool] * 4, [pool] * 2 + [[]] + [pool] * 2, [pool] * 4 + [[]]]:
            row = self.native([request(pools, [])])[0]
            self.assertEqual(row["combinations"], 0)
            self.assertFalse(row["checked"])

    def test_strict_boolean_index_extra_flag_and_duplicate_key_reject(self):
        r = request([[alternative([atom("A")])]], [premise(0)])
        for change in [{**r, "proofs": [premise(True)]}, {**r, "coverage_complete": True}]:
            with self.assertRaisesRegex(ValueError, "INVALID_INPUT"):
                self.native([change])
        for replacement in ['"index":0,"index":0', r'"index":0,"\u0069ndex":0']:
            payload = bridge.wire(r).replace('"index":0', replacement)
            run = subprocess.run([str(self.probe), str(self.source_path), "source", "test", "1", "target"],
                                 input=payload.encode() + b"\n" + bridge.wire(r).encode() + b"\n",
                                 capture_output=True, check=True)
            first, second = map(json.loads, run.stdout.splitlines())
            self.assertEqual(first["error"], "INVALID_INPUT")
            self.assertTrue(second["checked"])

    def test_raw_key_guard_preserves_repeated_strings_and_distinct_nested_keys(self):
        # Identical field names in separate objects are valid; JSON-looking
        # string values, escaped quotes and Arabic text are never parsed as keys.
        a = atom('"x":1,"x":2 \\ عربي')
        r = request([[alternative([a]), alternative([a])]], [premise(0)] * 2, a)
        self.assertTrue(self.native([r])[0]["checked"])

    def test_free_reader_document_pipeline_uses_fresh_reports(self):
        row = mm.audit_discourse("أنا عالم. أنا كاتب.", TRAINING, CONTEXT, probe=self.probe)
        doc = row["document"]
        self.assertEqual(row["schema"], "nabt.mantuq-mafhum-free-audit.v2")
        self.assertTrue(doc["supplied_pool_composition_proved"])
        self.assertEqual(doc["status"], "CHECKED_COMMON_CONSEQUENCE")
        self.assertEqual(len(doc["common_consequences"]), 2)
        self.assertFalse(row["reader_enumeration_proved"])
        report = bridge.read_discourse("أنا عالم. أنا كاتب.", lexical_model=bridge.learn_qac_lexicon(TRAINING),
                                       context=CONTEXT, source_id="input", scope="default")
        report["clauses"][0]["analyses"] = []
        with self.assertRaisesRegex(ValueError, "REPORT_CHANGED"):
            mm.audit_discourse("أنا عالم. أنا كاتب.", TRAINING, CONTEXT, report=report, probe=self.probe)

    def test_actual_incomplete_antecedent_does_not_become_complete(self):
        context = deepcopy(CONTEXT)
        for entity in context["entities"]:
            if entity["id"] == "zayd":
                entity["gender"] = "unknown"
        row = mm.audit_discourse("أنا عالم. هو كاتب.", TRAINING, context, probe=self.probe)
        self.assertGreater(row["document"]["incomplete_alternatives"], 0)
        self.assertEqual(row["document"]["common_consequences"], [])
        self.assertEqual(row["document"]["status"], "UNMEASURED")

    def test_adapter_does_not_expand_over_budget_or_call_it_a_failure(self):
        a = {"analysis_id": "a", "rejected_candidate": False, "licensed_syntax": True,
             "references_complete": True, "force": "ASSERT", "assertion_allowed": True,
             "claims": [{"predicate": "عالم", "args": ["zayd"]}]}
        clauses = [{"analyses": [a, a]}] * 13
        with patch.object(bridge, "native", side_effect=AssertionError("must defer before enumeration")):
            row = mm._document_consequences(clauses, BINDING, probe=self.probe)
        self.assertEqual(row["status"], "UNMEASURED")
        self.assertEqual(row["reason"], "RESOURCE_LIMIT")
        self.assertFalse(row["supplied_pool_composition_proved"])
        self.assertEqual(row["common_consequences"], [])


if __name__ == "__main__":
    unittest.main()
