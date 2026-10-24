"""Native Lean checks, independently tabulated laws, and adversarial replay.

Authored examples are engineering checks, not a held-out Arabic measurement.
"""
from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import source_semantics as bridge
from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import read_discourse

TRAINING = (ROOT / "examples/discourse_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/discourse_context.json").read_text())
BINDING = {"source": "أنا عالم.", "source_id": "s", "scope": "test", "context": "{}", "lexicon": "lexicon"}


class SourceSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.probe = bridge.executable()
        except RuntimeError:
            if "NABT_CLASSICAL_SEMANTIC_PROBE" in os.environ:
                raise
            raise unittest.SkipTest("build classicalSemanticProbe for native semantic checks")

    def native(self, requests, **kwargs):
        return bridge.native(requests, probe=self.probe, **kwargs)

    def test_selected_book_laws_independent_oracle(self):
        row = self.native([{"op": "rules"}])[0]
        expected = {"noun": {"fatha": ["nasb"], "kasra": ["jarr"], "damma": ["raf"], "sukun": []},
                    "present_verb": {"fatha": ["nasb"], "kasra": [], "damma": ["raf"], "sukun": ["jazm"]}}
        self.assertEqual(row["sibawayhi_law_id"], "nabt.sibawayhi-selected.v2")
        self.assertEqual(len(row["sibawayhi"]), 16)
        for law in row["sibawayhi"]:
            if law["regime"] == "overt_primary":
                self.assertEqual(law["courses"], expected[law["class"]][law["surface"]])
            else:
                self.assertEqual(law["regime"], "unqualified")
                self.assertEqual(law["courses"], ["raf", "nasb", "jarr"] if law["class"] == "noun"
                                 else ["raf", "nasb", "jazm"])
        for mark, case in [("kasra", "nasb"), ("fatha", "jarr")]:
            # Sound feminine plural nasb and bare diptote jarr are not lost.
            self.assertIn(case, next(r["courses"] for r in row["sibawayhi"]
                                    if r["class"] == "noun" and r["regime"] == "unqualified" and r["surface"] == mark))
        self.assertEqual(row["qatr_past"], ["fath", "damm", "waqf"])
        self.assertEqual(row["qatr_present"], [None, "waqf", "fath"])
        self.assertEqual(row["qatr_five_verbs"], [True, False, False])
        self.assertEqual(row["qatr_diptote"], ["fatha", "kasra", "kasra", "kasra"])
        self.assertEqual(row["awamil_partition"], [91, 7, 2])
        self.assertEqual(row["awamil_selected_ba_senses"], ["attachment", "instrument"])
        self.assertEqual(row["maqayis_selected_senses"], ["mark", "flag", "mountain", "lip_cleft", "knowledge"])

    def test_consensus_exhaustive_finite_oracle(self):
        # Set semantics is independent of Lean's head-and-all implementation.
        cases = [values for n in range(5) for values in itertools.product([None, "A", "B"], repeat=n)]
        requests = [{"op": "consensus", "expected": BINDING,
                     "readings": [{"binding": BINDING, "meaning": v} for v in values]} for values in cases]
        for values, row in zip(cases, self.native(requests), strict=True):
            meanings = set(values)
            expected = next(iter(meanings)) if len(meanings) == 1 and None not in meanings else None
            self.assertEqual(row["consensus"], expected, values)
            self.assertEqual(row["contract_verified"], expected is not None)
        self.assertEqual(len(cases), 121)

    def test_every_binding_component_is_preserved(self):
        requests = []
        for key in BINDING:
            changed = {**BINDING, key: BINDING[key] + "changed"}
            requests.append({"op": "consensus", "expected": BINDING,
                             "readings": [{"binding": changed, "meaning": "A"}]})
        self.assertTrue(all(row["consensus"] is None for row in self.native(requests)))

    def test_closed_reference_and_rivals(self):
        cases = [(False, [], None), (False, ["zayd"], None), (True, [], None),
                 (True, ["zayd"], "zayd"), (True, ["zayd", "hind"], None),
                 (True, ["zayd", "zayd"], None)]
        rows = self.native([{"op": "reference", "closed": c, "candidates": xs} for c, xs, _ in cases])
        self.assertEqual([r["entity"] for r in rows], [out for _, _, out in cases])

    def test_time_restriction_exhaustive_intervals(self):
        intervals = list(itertools.product([-1, 0, 1], repeat=2))
        pairs = list(itertools.product(intervals, repeat=2))
        requests = [{"op": "time", "small": {"first": str(a), "last": str(b)},
                     "big": {"first": str(c), "last": str(d)}} for (a, b), (c, d) in pairs]
        for ((a, b), (c, d)), result in zip(pairs, self.native(requests), strict=True):
            small = set(range(a, b + 1)); big = set(range(c, d + 1))
            self.assertEqual(result["contained"], bool(small) and small <= big)

    def test_definition_substitution_preserves_variable_identity(self):
        var = lambda n: {"kind": "variable", "index": n}
        name = lambda s: {"kind": "name", "value": s}
        formula = {"kind": "implies", "left": {"kind": "atom", "concept": "عالم", "args": [var(0)]},
                   "right": {"kind": "atom", "concept": "يعلم", "args": [var(0), var(1), var(2)]}}
        result = self.native([{"op": "substitute", "formula": formula, "replacements": [var(1), name("زيد")]}])[0]
        expected = deepcopy(formula)
        expected["left"]["args"] = [var(1)]
        expected["right"]["args"] = [var(1), name("زيد"), var(2)]
        self.assertEqual(result["formula"], expected)
        self.assertFalse(result["world_truth_established"])

    def test_all_six_passages_match_full_pinned_sources(self):
        rows = bridge.attest_sources(probe=self.probe)
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r["attested"] for r in rows))
        self.assertEqual(len({r["source_id"] for r in rows}), 4)

    def test_recursive_passage_mutation_and_empty_quote(self):
        source = json.loads(bridge.CATALOG.read_text())["passages"][0]
        leaf = {"kind": "leaf", "offset": source["offset"], "quote": source["quote"]}
        bad = {**leaf, "quote": leaf["quote"] + "invented"}
        requests = [{"op": "evidence", "tree": {"kind": "join", "left": leaf, "right": right}}
                    for right in [leaf, bad, {**leaf, "offset": leaf["offset"] + 1}, {**leaf, "quote": ""}]]
        self.assertEqual([r["attested"] for r in self.native(requests, source=source)], [True, False, False, False])

    def test_work_identity_cannot_be_replaced_by_matching_quote(self):
        source = json.loads(bridge.CATALOG.read_text())["passages"][0]
        request = {"op": "source_rule", "law": "nabt.qatr-selected.v1",
                   "offset": source["offset"], "quote": source["quote"]}
        result = self.native([request], source=source)[0]
        self.assertTrue(result["attested"])
        self.assertFalse(result["interpretation_bound"])

    def test_source_mutation_outside_quote_is_detected_by_edition_pin(self):
        catalog = json.loads(bridge.CATALOG.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            source = catalog["passages"][0]
            raw = (ROOT / source["local_path"]).read_bytes()
            (p / "source.txt").write_bytes(raw + b"changed")
            source["local_path"] = str(p / "source.txt")
            catalog["passages"] = [source]
            (p / "catalog.json").write_text(json.dumps(catalog))
            with patch.object(bridge, "CATALOG", p / "catalog.json"), self.assertRaisesRegex(ValueError, "SOURCE_CHANGED"):
                bridge.attest_sources(probe=self.probe)

    def test_free_reader_reference_ambiguity_and_time(self):
        for text in ["أنا عالم.", "زيد عالم. هو كاتب.", "إن هذا عالم.", "كتب زيد أمس.", "«زيد عالم»."]:
            with self.subTest(text=text):
                row = bridge.audit_discourse(text, TRAINING, CONTEXT, probe=self.probe)
                self.assertTrue(row["contract_checks_pass"])
                self.assertFalse(row["reader_enumeration_proved"])
                self.assertFalse(row["all_arabic_complete"])
                self.assertFalse(row["world_truth_established"])
                if "أمس" in text:
                    self.assertTrue(any('أمس' in (c["lean"]["consensus"] or '') for c in row["clauses"]))

    def test_free_reader_open_reference_is_retained(self):
        context = deepcopy(CONTEXT); context.pop("closed_reference_scope")
        row = bridge.audit_discourse("زيد عالم. هو كاتب.", TRAINING, context, probe=self.probe)
        self.assertTrue(row["contract_checks_pass"])
        self.assertGreater(row["clauses"][-1]["incomplete_readings"], 0)
        self.assertIsNone(row["clauses"][-1]["lean"]["consensus"])
        self.assertTrue(row["unmeasured_references"])
        self.assertTrue(all(r["status"] == "UNMEASURED" for r in row["unmeasured_references"]))

    def test_closed_singleton_with_unknown_compatibility_is_unmeasured(self):
        context = deepcopy(CONTEXT)
        next(e for e in context["entities"] if e["id"] == "zayd")["gender"] = "unknown"
        text = "أنا عالم. هو كاتب."
        fresh = read_discourse(text, lexical_model=learn_qac_lexicon(TRAINING), context=context)
        refs = [r for c in fresh["clauses"] for a in c["analyses"] for r in a["references"]
                if r["origin"] == "antecedent"]
        self.assertTrue(refs)
        self.assertTrue(all(r["closed_scope"] and r["candidate_entity_ids"] == ["zayd"] for r in refs))
        self.assertTrue(all(r["bound_entity_id"] is None for r in refs))
        audit = bridge.audit_discourse(text, TRAINING, context, probe=self.probe)
        self.assertTrue(audit["contract_checks_pass"])
        unmeasured = {r["reference_id"] for r in audit["unmeasured_references"]}
        self.assertTrue({r["reference_id"] for r in refs} <= unmeasured)
        self.assertIsNone(audit["clauses"][-1]["lean"]["consensus"])

    def test_forged_report_and_changed_context_do_not_supply_authority(self):
        model = learn_qac_lexicon(TRAINING)
        report = read_discourse("أنا عالم.", lexical_model=model, context=CONTEXT)
        forged = deepcopy(report); forged["claims"] = []
        with self.assertRaisesRegex(ValueError, "REPORT_CHANGED"):
            bridge.audit_discourse("أنا عالم.", TRAINING, CONTEXT, report=forged, probe=self.probe)
        changed = {**CONTEXT, "speaker": "hind"}
        with self.assertRaisesRegex(ValueError, "REPORT_CHANGED"):
            bridge.audit_discourse("أنا عالم.", TRAINING, changed, report=report, probe=self.probe)

    def test_transport_rejects_malformed_and_resource_exhaustion_separately(self):
        inputs = [b'{"op":"reference","closed":1,"candidates":[]}\n',
                  b'{"op":"reference","closed":true,"candidates":["\\ud800"]}\n',
                  b'{"op":"rules","extra":true}\n',
                  (bridge.wire({"op": "reference", "closed": True, "candidates": ["x"] * 129}) + "\n").encode()]
        process = subprocess.run([str(self.probe)], input=b''.join(inputs), capture_output=True, check=True)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([r["error"] for r in rows], ["INVALID_INPUT"] * 3 + ["RESOURCE_LIMIT"])
        self.assertTrue(all("status" not in r for r in rows))
        for value in ["01", "+1", "-0"]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "INVALID_INPUT"):
                self.native([{"op": "time", "small": {"first": value, "last": "1"},
                              "big": {"first": "0", "last": "2"}}])

    def test_stream_recovers_after_oversized_line_and_invalid_utf8(self):
        payload = b'x' * (1048576 + 1) + b'\n\xff\n{"op":"rules"}\n'
        process = subprocess.run([str(self.probe)], input=payload, capture_output=True, check=True, timeout=20)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([rows[0]["error"], rows[1]["error"]], ["RESOURCE_LIMIT", "INVALID_INPUT"])
        self.assertEqual(len(rows[2]["sibawayhi"]), 16)


if __name__ == "__main__":
    unittest.main()
