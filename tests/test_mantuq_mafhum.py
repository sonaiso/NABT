"""Authored engineering cases and independent finite models, not Arabic holdout.

Native checkers are mandatory when CI supplies their environment variables.
The manual source transcription is evidence, not an automatically proved
interpretation of the original books.
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
BINDING = {"source": "أنا عالم.", "source_id": "s", "scope": "scope", "context": "{}", "lexicon": "L"}


def atom(name):
    return {"kind": "atom", "concept": name, "args": []}


def binary(kind, left, right):
    return {"kind": kind, "left": left, "right": right}


def premise(index):
    return {"kind": "premise", "index": index}


def apply(rule, argument):
    return {"kind": "apply", "rule": rule, "argument": argument}


def evaluate(formula, valuation):
    # Truth-table oracle: no proof traversal, saturation or production parser.
    if formula["kind"] == "atom":
        return valuation[formula["concept"]]
    a, b = evaluate(formula["left"], valuation), evaluate(formula["right"], valuation)
    return a and b if formula["kind"] == "both" else not a or b


class MeaningContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.probe = bridge.executable()
        except RuntimeError:
            if "NABT_CLASSICAL_SEMANTIC_PROBE" in os.environ:
                raise
            raise unittest.SkipTest("build classicalSemanticProbe for native meaning checks")

    def native(self, requests, **kwargs):
        return bridge.native(requests, probe=self.probe, **kwargs)

    def test_all_retained_sources_and_numbered_inventory(self):
        source = mm.attest_sources(probe=self.probe)
        self.assertEqual(len(source["method_passages"]), 16)
        self.assertEqual(len(source["grammar_passages"]), 6)
        self.assertEqual(len({r["source_id"] for r in source["method_passages"] + source["grammar_passages"]}), 7)
        self.assertFalse(source["interpretation_adequacy_proved"])
        result = mm.audit_inventory(probe=self.probe)
        self.assertEqual(result["entries_checked"], 100)
        self.assertFalse(result["full_rule_semantics_complete"])
        entries = self.native([{"op": "awamil_inventory"}])[0]["entries"]
        self.assertEqual([sum(e["group"] == n for e in entries) for n in range(1, 16)],
                         [17, 6, 2, 7, 4, 5, 9, 4, 9, 13, 4, 4, 7, 7, 2])
        self.assertEqual(entries[23]["name"], entries[43]["name"])
        self.assertNotEqual(entries[23]["family"], entries[43]["family"])

    def test_method_work_quote_and_byte_pin_cannot_be_substituted(self):
        catalog = json.loads(mm.CATALOG.read_text())
        source = catalog["sources"][0]; span = source["spans"][0]
        request = {"op": "method_source", "law": source["law_id"], "offset": span["offset"], "quote": span["quote"]}
        row = self.native([{**request, "law": "nabt.shakhsiyya3-indications.v1"}], source=source)[0]
        self.assertTrue(row["attested"]); self.assertFalse(row["work_matches"])
        for change in ({"offset": 1}, {"quote": ""}, {"quote": span["quote"] + "مخترع"}):
            self.assertFalse(self.native([{**request, **change}], source=source)[0]["attested"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            raw = (ROOT / source["local_path"]).read_bytes()
            (path / "source").write_bytes(raw + b"unquoted mutation")
            source["local_path"] = str(path / "source")
            (path / "catalog").write_text(json.dumps(catalog))
            with patch.object(mm, "CATALOG", path / "catalog"), self.assertRaisesRegex(ValueError, "SOURCE_CHANGED"):
                mm.attest_sources(probe=self.probe)

    def test_inventory_extra_entry_is_not_a_hundred_factor_proof(self):
        catalog = json.loads(mm.INVENTORY.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); (path / "sources").mkdir()
            (path / "sources/awamil_inventory.tsv").write_bytes((mm.INVENTORY.parent / "sources/awamil_inventory.tsv").read_bytes())
            catalog["rows"].append({**catalog["rows"][-1], "id": 101})
            (path / "catalog").write_text(json.dumps(catalog))
            with patch.object(mm, "INVENTORY", path / "catalog"), self.assertRaisesRegex(ValueError, "INVENTORY_DIFFERS"):
                mm.audit_inventory(probe=self.probe)

    def test_contrast_policy_all_48_rows_and_no_occurrence_authority(self):
        requests, expected = [], []
        for kind in ["attribute", "condition", "endpoint", "number", "name", "innama"]:
            for q, o, u in product([False, True], repeat=3):
                requests.append({"op": "contrast_policy", "kind": kind, "qualified": q,
                                 "overridden": o, "usual_case": u})
                expected.append((kind, q, o, u) in {(k, True, False, False)
                                for k in ["attribute", "condition", "endpoint", "number"]})
        rows = self.native(requests)
        self.assertEqual([r["conditional_policy_allows"] for r in rows], expected)
        self.assertTrue(all(not r["occurrence_license_established"] for r in rows))

    def test_soundness_against_independent_models(self):
        a, b = atom("A"), atom("B")
        pool = [a, b, binary("both", a, b), binary("implies", a, b), binary("implies", b, a)]
        proof_pool = [premise(0), premise(1), premise(2), {"kind": "left", "child": premise(0)},
                      {"kind": "right", "child": premise(0)}, apply(premise(0), premise(1)),
                      apply(premise(1), premise(0)), binary("pair", premise(0), premise(1))]
        cases = [(list(ps), proof) for ps in product(pool, repeat=2) for proof in proof_pool]
        rows = self.native([{"op": "meaning_infer", "premises": ps, "proof": p} for ps, p in cases])
        checked = 0
        for (ps, _), row in zip(cases, rows, strict=True):
            if row["checked"]:
                checked += 1
                for av, bv in product([False, True], repeat=2):
                    model = {"A": av, "B": bv}
                    if all(evaluate(f, model) for f in ps):
                        self.assertTrue(evaluate(row["conclusion"], model), (ps, row, model))
            self.assertFalse(row["premise_truth_established"])
            self.assertFalse(row["usuli_subtype_established"])
        self.assertEqual(len(cases), 200)
        self.assertGreater(checked, 50)

    def test_recursive_implication_pair_and_no_inverse_or_empty_ancestor(self):
        a, b, c = map(atom, "ABC")
        rule = binary("implies", binary("both", a, b), c)
        proof = apply(premise(2), binary("pair", premise(0), premise(1)))
        row = self.native([{"op": "meaning_infer", "premises": [a, b, rule], "proof": proof}])[0]
        self.assertEqual(row["conclusion"], c)
        self.assertTrue(row["uses_implication"])
        invalid = [([], proof), ([binary("implies", a, b), b], apply(premise(0), premise(1))),
                   ([a], {"kind": "left", "child": premise(0)}), ([a], premise(99))]
        self.assertTrue(all(not r["checked"] for r in self.native([
            {"op": "meaning_infer", "premises": ps, "proof": p} for ps, p in invalid])))

    def test_common_consequence_does_not_require_identical_whole_readings(self):
        a, b, c = map(atom, "ABC")
        readings = [{"binding": BINDING, "premises": [binary("both", a, b)],
                     "proof": {"kind": "left", "child": premise(0)}},
                    {"binding": BINDING, "premises": [c, binary("implies", c, a)],
                     "proof": apply(premise(1), premise(0))}]
        request = {"op": "meaning_common", "expected": BINDING, "readings": readings}
        self.assertEqual(self.native([request])[0]["conclusion"], a)
        for bad in [{"binding": BINDING, "premises": None, "proof": premise(0)},
                    {"binding": BINDING, "premises": [b], "proof": premise(0)}]:
            self.assertFalse(self.native([{**request, "readings": readings + [bad]}])[0]["checked"])
        self.assertFalse(self.native([{**request, "readings": []}])[0]["checked"])
        for key in BINDING:
            changed = deepcopy(readings); changed[0]["binding"][key] += "changed"
            self.assertFalse(self.native([{**request, "readings": changed}])[0]["checked"])

    def test_native_transport_rejects_authority_flags_and_invalid_indices(self):
        request = {"op": "meaning_infer", "premises": [atom("A")], "proof": premise(0)}
        for changed in [{**request, "verified": True}, {**request, "proof": premise(True)},
                        {**request, "proof": {"kind": "deny_antecedent", "child": premise(0)}}]:
            with self.assertRaisesRegex(ValueError, "INVALID_INPUT"):
                self.native([changed])
        deep = premise(0)
        for _ in range(32):
            deep = {"kind": "left", "child": deep}
        with self.assertRaisesRegex(ValueError, "RESOURCE_LIMIT"):
            self.native([{**request, "proof": deep}])

    def test_free_reader_reference_time_and_nonassertive_force(self):
        for text in ["أنا عالم.", "زيد عالم. هو كاتب.", "كتب زيد أمس.", "هل زيد عالم؟"]:
            result = mm.audit_discourse(text, TRAINING, CONTEXT, probe=self.probe)
            self.assertTrue(result["source_replay_pass"])
            self.assertFalse(result["reader_enumeration_proved"])
            self.assertFalse(result["world_truth_established"])
            for clause in result["clauses"]:
                self.assertTrue(clause["common_consequences"])
                self.assertEqual(len(clause["reading_ids"]), clause["viable_readings"])
                for c in clause["common_consequences"]:
                    self.assertEqual(len(c["certificates"]), clause["viable_readings"])
                    record = json.loads(c["formula"]["args"][0]["value"])
                    if "أمس" in text:
                        self.assertEqual(record["claim"]["time"][0]["form"], "أمس")
                    if "هل" in text:
                        self.assertEqual(record["force"], "QUESTION")
                        self.assertFalse(record["assertion_allowed"])

    def test_unresolved_and_unread_source_remain_unmeasured(self):
        for text, context in [("إن هذا عالم.", CONTEXT), ("هُوَ عَالِمٌ.", {}), ("«زيد عالم».", CONTEXT)]:
            row = mm.audit_discourse(text, TRAINING, context, probe=self.probe)
            self.assertTrue(all(c["status"] == "UNMEASURED" for c in row["clauses"]))
            self.assertTrue(all(not c["common_consequences"] for c in row["clauses"]))

    def test_ambiguous_hamza_keeps_both_entity_readings(self):
        context = deepcopy(CONTEXT)
        context["entities"] += [
            {"id": "ahmad", "name": "أحمد", "kind": "person", "gender": "masculine", "number": "singular"},
            {"id": "hamad", "name": "حمد", "kind": "person", "gender": "masculine", "number": "singular"}]
        text = "أَحْمَد عَالِمٌ؟"
        fresh = bridge.read_discourse(text, lexical_model=bridge.learn_qac_lexicon(TRAINING), context=context)
        viable = [a for a in fresh["clauses"][0]["analyses"] if not a["rejected_candidate"]]
        self.assertEqual({c["args"][0] for a in viable for c in a["claims"]}, {"ahmad", "hamad"})
        audit = mm.audit_discourse(text, TRAINING, context, report=fresh, probe=self.probe)
        self.assertEqual(audit["clauses"][0]["reading_ids"], [a["analysis_id"] for a in viable])
        self.assertEqual(audit["clauses"][0]["status"], "UNMEASURED")
        self.assertFalse(audit["clauses"][0]["common_consequences"])

    def test_forged_candidate_omission_and_changed_bindings_are_replayed(self):
        fresh = bridge.read_discourse("أنا عالم.", lexical_model=bridge.learn_qac_lexicon(TRAINING), context=CONTEXT)
        changed = deepcopy(fresh); changed["clauses"][0]["analyses"].pop()
        for report, context, training in [(changed, CONTEXT, TRAINING),
                                           (fresh, {**CONTEXT, "speaker": "hind"}, TRAINING),
                                           (fresh, CONTEXT, TRAINING + b"\n")]:
            with self.assertRaisesRegex(ValueError, "REPORT_CHANGED"):
                mm.audit_discourse("أنا عالم.", training, context, report=report, probe=self.probe)

    def test_every_claim_qualifier_changes_atom_identity(self):
        analysis = {"force": "ASSERT", "question_kind": None, "assertion_allowed": True}
        claim = {"args": ["zayd"], "positive": True, "predicate": "كتب", "time": ["أمس"],
                 "place": ["البيت"], "restriction": ["فقط"], "tense": "past", "voice": "active"}
        original = mm.claim_formula(analysis, claim)
        changed_formulas = []
        for field in claim:
            changed = deepcopy(claim); changed[field] = "changed"
            changed_formulas.append(mm.claim_formula(analysis, changed))
        for field in analysis:
            changed = {**analysis, field: "changed"}
            changed_formulas.append(mm.claim_formula(changed, claim))
        requests = [{"op": "meaning_common", "expected": BINDING, "readings": [
            {"binding": BINDING, "premises": [f], "proof": premise(0)} for f in [original, altered]]}
            for altered in changed_formulas]
        self.assertTrue(all(not r["checked"] for r in self.native(requests)))


class SourceToMeaning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.probe = bridge.executable()
        except RuntimeError:
            if "NABT_CLASSICAL_SEMANTIC_PROBE" in os.environ:
                raise
            raise unittest.SkipTest("build classicalSemanticProbe")
        cls.verified = Path(os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
        if not cls.verified.is_file():
            if "NABT_VERIFIED_READING" in os.environ:
                raise RuntimeError("NABT_VERIFIED_READING is not built")
            raise unittest.SkipTest("build verifiedReading")

    def run_source(self, text, question="هل سالم هو عالم؟\n"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "source").write_text(text)
            (path / "query").write_text(question)
            return mm.derive_controlled(path / "source", path / "query", scope="local",
                                        probe=self.probe, verified_probe=self.verified)

    def test_exact_reading_recursive_multi_premise_meaning_and_execution(self):
        text = ("سالم يحب سهيل.\nسالم هو حكيم.\n"
                "إذا سالم يحب سهيل و سالم هو حكيم فإن سهيل هو عالم.\n"
                "إذا سهيل هو عالم فإن سالم هو عالم.\n")
        row = self.run_source(text)
        self.assertEqual(row["execution"]["status"], "SUPPORTED")
        self.assertEqual(len(row["signed_consequences"]), 1)
        checked = row["signed_consequences"][0]["lean"]
        self.assertTrue(checked["source_reading_checked"])
        self.assertEqual(checked["source_text"], text)
        self.assertEqual(checked["conclusion"]["concept"], "عالم")
        self.assertEqual(checked["conclusion"]["args"][0]["value"], "local")

    def test_signed_conflict_unknown_and_dependency_defer_are_preserved(self):
        cases = [("سالم هو عالم.\n", "SUPPORTED", 1),
                 ("ليس سالم هو عالم.\n", "REFUTED", 1),
                 ("سالم هو عالم.\nليس سالم هو عالم.\n", "CONFLICT", 2),
                 ("سالم هو حكيم.\n", "UNKNOWN", 0),
                 ("سالم هو حكيم.\nليس سالم هو حكيم.\nإذا سالم هو حكيم فإن سالم هو عالم.\n", "DEFER", 1),
                 ("إذا سالم هو حكيم فإن سالم هو عالم.\nإذا سالم هو عالم فإن سالم هو حكيم.\n", "UNKNOWN", 0)]
        for text, status, count in cases:
            with self.subTest(status=status):
                row = self.run_source(text)
                self.assertEqual(row["execution"]["status"], status)
                self.assertEqual(len(row["signed_consequences"]), count)
                self.assertFalse(row["world_truth_established"])

    def test_caller_premises_and_changed_rules_cannot_supply_consequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source"
            source = {"local_path": str(path), "source_id": "s", "revision": "r", "edition": "test", "work": "target"}
            request = {"op": "meaning_from_source", "scope": "s", "proof": apply(premise(1), premise(0))}
            good = "سالم هو حكيم.\nإذا سالم هو حكيم فإن سالم هو عالم.\n"
            for text, expected in [(good, True), (good.replace("إذا سالم هو حكيم", "إذا سهيل هو حكيم"), False)]:
                path.write_text(text)
                self.assertEqual(bridge.native([request], source=source, probe=self.probe)[0]["checked"], expected)
            with self.assertRaisesRegex(ValueError, "INVALID_INPUT"):
                bridge.native([{**request, "premises": [atom("invented")]}], source=source, probe=self.probe)
            for raw in [good.encode() + b"trailing", b"\xff", "سالم عالم.\n".encode()]:
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, "INVALID_INPUT"):
                    bridge.native([request], source=source, probe=self.probe)


if __name__ == "__main__":
    unittest.main()
