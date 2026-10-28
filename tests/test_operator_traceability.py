"""Actual operator identities/types and adversarial metadata regressions.

These checks validate explicit references, not source fidelity or refinement.
The full compiled join remains a separate gate.
"""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from tools.grammar_catalog import catalog
from tools.grammar_catalog.operator_traceability import TraceabilityError, validate_registry

PREFIX = "nabt.classical-rule-inventory.v1::"
EXPECTED = {
    "HAMZA-INTERROGATIVE-AL": "ClassicalHamza.enumeration_exact",
    "HAMZA-FINAL-LONG": "ClassicalHamza.enumeration_exact",
    "HAMZA-ACTIVE-PARTICIPLE": "ClassicalHamza.enumeration_exact",
    "HAMZA-BROKEN-PLURAL": "ClassicalHamza.enumeration_exact",
    "HAMZA-TWO-GLIDES": "ClassicalHamza.enumeration_exact",
    "HAMZA-LEXICAL-COMMAND": "ClassicalHamza.enumeration_exact",
    "WEAK-INITIAL-WAW": "ClassicalWeak.enumeration_exact",
    "WEAK-INITIAL-OPEN-EXCEPTION": "ClassicalWeak.enumeration_exact",
    "WEAK-WAW-TO-YA": "ClassicalWeak.enumeration_exact",
    "WEAK-YA-TO-WAW": "ClassicalWeak.enumeration_exact",
    "WEAK-MOVE-TO-ALIF": "ClassicalWeak.enumeration_exact",
    "WEAK-AFWAL-BLOCK": "ClassicalWeak.enumeration_exact",
    "WEAK-IFTIAL-RECIPROCAL": "ClassicalWeak.enumeration_exact",
    "WEAK-TWO-ELIGIBLE": "ClassicalWeak.enumeration_exact",
    "WEAK-NOMINAL-SUFFIX-BLOCK": "ClassicalWeak.enumeration_exact",
    "WEAK-VOWEL-TRANSFER": "ClassicalWeak.enumeration_exact",
    "GEM-VOWELED-FINAL": "ClassicalGemination.enumeration_exact",
    "GEM-JUSSIVE-VARIANTS": "ClassicalGemination.enumeration_exact",
    "GEM-FEMININE-SUFFIX": "ClassicalGemination.enumeration_exact",
    "GEM-EXCLAMATION": "ClassicalGemination.enumeration_exact",
    "ASSIM-NUN-B-BLOCKED-TEXT": "ClassicalGemination.nun_exact",
    "CMD-WEAK-DELETE": "ClassicalBoundaryAffixes.weak_exact",
    "AFFIX-LIGHT-NUN-PAUSE": "ClassicalBoundaryAffixes.light_exact",
    "MUGHNI-ANA-BOUNDARY": "ClassicalBoundaryAffixes.ana_exact",
}


class OperatorTraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((catalog.ROOT / catalog.OPERATOR_TRACEABILITY).read_text())
        cls.crosswalk = json.loads((catalog.ROOT / catalog.CROSSWALK).read_text())
        cls.names = set(json.loads((catalog.ROOT / "formal/theorems.json").read_text())["theorems"])
        cls.current = catalog.build_catalog()

    def validate(self, registry):
        return validate_registry(registry, self.crosswalk, catalog.CROSSWALK, self.names,
                                 lambda path: catalog._read(catalog.ROOT, path))

    def test_all_24_current_operators_have_actual_scoped_declarations(self):
        rows, _ = self.validate(self.registry)
        self.assertEqual(set(rows), set(EXPECTED))
        current = {r["local_id"]: r for r in self.current["rules"] if r["runtime_rule_id"]}
        self.assertEqual(set(current), set(EXPECTED))
        self.assertEqual(self.current["schema"], "nabt.grammar-retrieval-catalog.v2")
        self.assertEqual(self.current["coverage"]["operators_with_explicit_scoped_theorem"], 24)
        for rid, short in EXPECTED.items():
            row = current[rid]
            self.assertEqual(row["theorem_names"], ["Nabt." + short])
            self.assertTrue(row["implemented_scope"].strip())
            evidence = row["operator_traceability"]
            ref = evidence["formal_references"][0]
            self.assertEqual(ref["declaration"], "Nabt." + short)
            self.assertIn("↔", ref["statement_source_text"])
            self.assertTrue(all(v is False for v in evidence["claims"].values()))
            self.assertFalse(row["full_source_rule_complete"])
        self.assertIsNone(self.current["coverage"]["whole_arabic_coverage"])

    def test_specific_types_cannot_be_confused_with_general_enumeration(self):
        rows, _ = self.validate(self.registry)
        nun = rows["ASSIM-NUN-B-BLOCKED-TEXT"]["formal_references"][0]
        self.assertIn('some (⟨"م", .s⟩, right) ↔ NunAdmissible', nun["statement_source_text"])
        self.assertIn("textual discrepancy", nun["proof_scope"])
        weak = rows["WEAK-INITIAL-WAW"]["formal_references"][0]
        self.assertIn("a ∈ candidates f ↔ Admissible f a", weak["statement_source_text"])
        self.assertIn("does not bind a Frame to a cell Window", weak["proof_scope"])
        self.assertIn("Minority pause has no licensed output",
                      rows["MUGHNI-ANA-BOUNDARY"]["formal_references"][0]["proof_scope"])
        self.assertIn("Bakr unvocalized action does not imply a completed surface",
                      rows["GEM-FEMININE-SUFFIX"]["formal_references"][0]["proof_scope"])

    def test_historical_crosswalk_is_preserved_and_overlay_is_additive(self):
        raw = (catalog.ROOT / catalog.CROSSWALK).read_bytes()
        self.assertEqual(sha256(raw).hexdigest(),
                         "52f27b7e00e730525c4278d7600f3668495ef75cf327f19a6fe7a81759b4c8a6")
        old = [r for r in self.crosswalk["rows"] if r["status"] == "new_scoped_conditional_operator"]
        self.assertEqual(sum(r["implemented_scope"] is None for r in old), 10)
        self.assertEqual(sum("formal_exactness_theorem" in r for r in old), 6)
        current = {r["local_id"]: r for r in self.current["rules"]}
        for row in self.crosswalk["rows"]:
            if row["rule_id"] not in EXPECTED:
                self.assertEqual(current[row["rule_id"]]["implemented_scope"], row["implemented_scope"])
                self.assertNotIn("operator_traceability", current[row["rule_id"]])

    def test_missing_extra_duplicate_and_blank_records_fail(self):
        for kind in ("missing", "extra", "duplicate", "scope", "proof_scope"):
            value = deepcopy(self.registry)
            if kind == "missing":
                value["rows"].pop()
            elif kind == "extra":
                value["rows"][0]["rule_id"] = "INVENTED"
            elif kind == "duplicate":
                value["rows"][0] = deepcopy(value["rows"][1])
            elif kind == "scope":
                value["rows"][0]["implemented_scope"] = None
            else:
                value["rows"][0]["formal_references"][0]["proof_scope"] = ""
            with self.subTest(kind=kind), self.assertRaises(TraceabilityError):
                self.validate(value)

    def test_forged_type_names_path_offsets_hashes_and_claims_fail(self):
        mutations = {
            "declaration": "Nabt.ClassicalBoundaryAffixes",
            "source_path": "formal/Nabt/ClassicalHamza.lean",
            "statement_source_text": "theorem light_exact : True",
            "statement_source_sha256": "0" * 64,
            "source_sha256": "0" * 64,
            "statement_start_byte": True,
            "statement_end_line": False,
        }
        for key, replacement in mutations.items():
            value = deepcopy(self.registry)
            value["rows"][0]["formal_references"][0][key] = replacement
            with self.subTest(key=key), self.assertRaises(TraceabilityError):
                self.validate(value)
        value = deepcopy(self.registry)
        value["claims"]["whole_arabic_complete"] = True
        with self.assertRaisesRegex(TraceabilityError, "overclaimed"):
            self.validate(value)

    def test_public_builder_rejects_changed_registry_before_using_its_claims(self):
        original_read = catalog._read
        forged = deepcopy(self.registry)
        forged["rows"][0]["implemented_scope"] = "forged but nonempty"
        def read(root, path):
            return (json.dumps(forged).encode() if path == catalog.OPERATOR_TRACEABILITY
                    else original_read(root, path))
        with patch.object(catalog, "_read", side_effect=read):
            with self.assertRaisesRegex(catalog.CatalogError, "installed input hash mismatch"):
                catalog.build_catalog()


if __name__ == "__main__":
    unittest.main()
