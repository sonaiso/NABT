"""Independent small graph fixtures test joins, aliases and failed references.

Synthetic dictionaries exercise only the private pure join. Public production
build_links always invokes the actual source and compiled Lean exporters.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog import links


def fixtures():
    source = {
        "inputs": [{"path": "formal/theorems.json", "sha256": "manifest"}],
        "sources": [{"source_key": "edition", "source_id": "qatr"}],
        "passages": [{"passage_id": "p1", "source_key": "edition", "source_id": "qatr",
                      "start": 0, "end": 4, "sha256": "span"}],
        "rules": [{"rule_key": "registry::r1", "title": "Rule one", "scope": "conditional",
                   "theorem_names": ["Nabt.Alias.lemma"], "source_passage_ids": ["p1"]}],
        "items": [{"item_id": "section", "title": "Source section", "description": "open",
                   "theorem_names": ["Nabt.Base.lemma"], "source_passage_ids": ["p1"]}],
    }
    def declaration(name, source):
        return {"name": name, "canonical_name": "Nabt.Base.lemma", "statement_sha256": "same-statement",
                "source_path": source, "source_sha256": name + "-source"}
    rows = [declaration("Nabt.Base.lemma", "formal/Nabt/Base.lean"),
            declaration("Nabt.Alias.lemma", "formal/Nabt/Alias.lean")]
    compiled = {
        "inputs": {"formal/theorems.json": "manifest", **{r["source_path"]: r["source_sha256"] for r in rows}},
        "theorems": rows, "fingerprint_scope": "fixture AST identity only",
        "lean_toolchain": "fixture-does-not-grant-authority",
    }
    return source, compiled


class GrammarCatalogLinkTests(unittest.TestCase):
    def test_alias_is_one_proof_node_with_two_explicit_edges(self):
        source, compiled = fixtures()
        report = links._compose(source, compiled)
        self.assertEqual(report["counts"]["explicit_reference_edges"], 2)
        self.assertEqual(report["counts"]["source_reference_nodes"], 2)
        self.assertEqual(report["counts"]["linked_passage_nodes"], 1)
        self.assertEqual(report["counts"]["canonical_theorem_nodes"], 1)
        self.assertEqual(report["proof_nodes"][0]["canonical_name"], "Nabt.Base.lemma")
        self.assertEqual(report["proof_nodes"][0]["aliases"], ["Nabt.Alias.lemma"])
        alias_edge = next(e for e in report["edges"] if e["referenced_declaration"] == "Nabt.Alias.lemma")
        self.assertEqual(alias_edge["source_path"], "formal/Nabt/Alias.lean")
        self.assertEqual(alias_edge["canonical_source_path"], "formal/Nabt/Base.lean")
        self.assertFalse(report["claims"]["source_translation_fidelity_established"])
        self.assertFalse(report["claims"]["whole_arabic_complete"])

    def test_namespace_is_not_a_declaration(self):
        source, compiled = fixtures()
        source["rules"][0]["theorem_names"] = ["Nabt.Base"]
        with self.assertRaisesRegex(links.LinkError, "missing from compiled export"):
            links._compose(source, compiled)

    def test_reference_removed_from_compiled_snapshot_fails(self):
        source, compiled = fixtures()
        compiled["theorems"] = compiled["theorems"][:1]
        with self.assertRaisesRegex(links.LinkError, "missing from compiled export"):
            links._compose(source, compiled)

    def test_manifest_snapshots_must_match(self):
        source, compiled = fixtures()
        compiled["inputs"]["formal/theorems.json"] = "different"
        with self.assertRaisesRegex(links.LinkError, "different theorem manifests"):
            links._compose(source, compiled)

    def test_canonicalization_cannot_join_different_statements(self):
        source, compiled = fixtures()
        compiled["theorems"][1]["statement_sha256"] = "another-proposition"
        with self.assertRaisesRegex(links.LinkError, "canonical identity"):
            links._compose(source, compiled)

    def test_missing_canonical_and_unbound_formal_source_fail(self):
        for mutation in ("canonical", "source"):
            source, compiled = fixtures()
            if mutation == "canonical":
                compiled["theorems"][1]["canonical_name"] = "Nabt.Missing.lemma"
            else:
                compiled["theorems"][1]["source_sha256"] = "invented"
            with self.subTest(mutation=mutation), self.assertRaises(links.LinkError):
                links._compose(source, compiled)

    def test_missing_passage_or_edition_and_duplicate_reference_fail(self):
        for mutation in ("passage", "edition", "reference"):
            source, compiled = fixtures()
            if mutation == "passage":
                source["passages"] = []
            elif mutation == "edition":
                source["sources"] = []
            else:
                source["rules"][0]["theorem_names"] *= 2
            with self.subTest(mutation=mutation), self.assertRaises(links.LinkError):
                links._compose(source, compiled)

    def test_duplicate_node_identity_fails_instead_of_overwriting(self):
        source, compiled = fixtures()
        source["rules"].append(deepcopy(source["rules"][0]))
        with self.assertRaisesRegex(links.LinkError, "repeated rule_key"):
            links._compose(source, compiled)

    def test_public_api_calls_compiler_and_source_replay_without_json_input(self):
        source, compiled = fixtures()
        # Stub file hashes to isolate the orchestration contract. This fixture
        # is not a kernel-check result and is never installed as evidence.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in compiled["inputs"]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture")
                compiled["inputs"][path] = links.sha256(b"fixture").hexdigest()
            source["inputs"][0]["sha256"] = compiled["inputs"]["formal/theorems.json"]
            for row in compiled["theorems"]:
                row["source_sha256"] = compiled["inputs"][row["source_path"]]
            with patch.object(links.proof_catalog, "build_catalog", return_value=compiled) as build_proof, \
                    patch.object(links.source_catalog, "build_catalog", return_value=source) as build_source:
                report = links.build_links(root=root, lake="specified-lake")
                build_proof.assert_called_once_with(root=root.resolve(), lake="specified-lake")
                build_source.assert_called_once_with(root=root.resolve())
                self.assertEqual(report["counts"]["unresolved_references"], 0)
        with self.assertRaises(TypeError):
            links.build_links(proof_catalog=compiled)

    def test_public_compilation_failure_is_not_partial_success(self):
        with patch.object(links.proof_catalog, "build_catalog", side_effect=ValueError("export failed")), \
                patch.object(links.source_catalog, "build_catalog") as build_source:
            with self.assertRaisesRegex(ValueError, "export failed"):
                links.build_links()
            build_source.assert_not_called()


if __name__ == "__main__":
    unittest.main()
