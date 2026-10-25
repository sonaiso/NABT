"""Tamper and identity tests for the compiled declaration index."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import proof_catalog as catalog


def row(name="Nabt.Example.one", ast=None, dependencies=None):
    return {"name": name, "module": "Nabt.Example", "range": None,
            "universe_parameters": 0, "statement_ast": ast or ["const", "True"],
            "proof_dependencies": dependencies or [], "type_dependencies": ["True"],
            "axioms": []}


def log(rows, count=None):
    return "\n".join("NABT_PROOF " + json.dumps(item) for item in rows) + \
        f"\nNABT_PROOF_COUNT {len(rows) if count is None else count}\n"


class ProofCatalogTests(unittest.TestCase):
    def test_exact_export_order_and_count(self):
        rows = [row(), row("Nabt.Example.two", ["const", "False"])]
        names = [item["name"] for item in rows]
        self.assertEqual(catalog.parse_export(log(rows), names), rows)
        for malformed in (log(rows[::-1]), log(rows[:-1]), log(rows, 3),
                          log(rows) + "NABT_PROOF_COUNT 2\n"):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                catalog.parse_export(malformed, names)

    def test_missing_or_repeated_manifest_cannot_authorize(self):
        with self.assertRaises(ValueError):
            catalog.parse_export(log([]), [])
        with self.assertRaises(ValueError):
            catalog.parse_export(log([row(), row()]), [row()["name"]] * 2)

    def test_unapproved_axiom_and_boolean_count_rejected(self):
        for change in ({"axioms": ["sorryAx"]}, {"axioms": ["Nabt.customAxiom"]},
                       {"universe_parameters": True}, {"universe_parameters": -1},
                       {"statement_ast": []}, {"proof_dependencies": [False]}):
            altered = row() | change
            with self.subTest(change=change), self.assertRaises(ValueError):
                catalog.parse_export(log([altered]), [altered["name"]])

    def test_same_statement_canonicalizes_dependency_sink(self):
        base = row("Nabt.Example.z_base")
        alias = row("Nabt.Example.a_alias", dependencies=[base["name"]])
        distinct = row("Nabt.Example.other", ["const", "False"])
        before = deepcopy([alias, base, distinct])
        entries, groups = catalog.summarize_rows(before)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["canonical_name"], base["name"])
        self.assertEqual(groups[0]["representative_policy"], "unique_dependency_sink")
        self.assertEqual(entries[0]["same_statement_dependencies"], [base["name"]])
        self.assertNotEqual(entries[0]["statement_sha256"], entries[2]["statement_sha256"])
        self.assertEqual(before, [alias, base, distinct])

    def test_dependency_alone_does_not_imply_statement_equivalence(self):
        base = row()
        dependent = row("Nabt.Example.dependent", ["app", "Not", ["const", "True"]],
                        [base["name"]])
        entries, groups = catalog.summarize_rows([base, dependent])
        self.assertEqual(groups, [])
        self.assertEqual(entries[1]["canonical_name"], dependent["name"])

    def test_universe_arity_is_part_of_statement_identity(self):
        first = row()
        second = row("Nabt.Example.polymorphic") | {"universe_parameters": 1}
        _, groups = catalog.summarize_rows([first, second])
        self.assertEqual(groups, [])

    def test_stored_catalog_scalar_type_forgery_is_rejected(self):
        expected = {"theorems": [{"universe_parameters": 0}], "counts": {"total": 1}}
        self.assertTrue(catalog.catalog_matches(deepcopy(expected), expected))
        for value in (False, 0.0):
            altered = deepcopy(expected)
            altered["theorems"][0]["universe_parameters"] = value
            self.assertEqual(altered, expected)  # The former Python comparison conflated them.
            self.assertFalse(catalog.catalog_matches(altered, expected))
        for value in (True, 1.0):
            altered = deepcopy(expected)
            altered["counts"]["total"] = value
            self.assertEqual(altered, expected)
            self.assertFalse(catalog.catalog_matches(altered, expected))
        with self.assertRaises(ValueError):
            catalog.catalog_matches({"count": float("nan")}, expected)

    def test_recorded_proof_catalog_preserves_aliases_and_source_links(self):
        report = json.loads((ROOT / "evidence/grammar_catalog_v1/proof_catalog.json").read_text())
        entries = {item["name"]: item for item in report["theorems"]}
        self.assertEqual(len(entries), report["counts"]["advertised_declarations"])
        self.assertEqual(report["counts"]["redundant_statement_names"], 3)
        pairs = {
            "Nabt.TextEvidence.noun_sign_does_not_determine_construction":
                "Nabt.Morphology.noun_unknown_keeps_both",
            "Nabt.SourceSemantics.execution_in_world":
                "Nabt.VerifiedReading.source_to_execution_entails",
            "Nabt.MaqayisDenotation.ilm_ambiguity_retained":
                "Nabt.MaqayisRules.root_does_not_determine_sense",
        }
        for alias, canonical in pairs.items():
            self.assertEqual(entries[alias]["canonical_name"], canonical)
            self.assertIn(canonical, entries[alias]["proof_dependencies"])
            self.assertEqual(entries[alias]["statement_sha256"], entries[canonical]["statement_sha256"])
        for item in entries.values():
            self.assertEqual(item["source_sha256"], report["inputs"][item["source_path"]])
        self.assertFalse(report["logical_equivalence_decided"])
        self.assertFalse(report["source_completeness_claim"])


if __name__ == "__main__":
    unittest.main()
