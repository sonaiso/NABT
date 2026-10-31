"""Independent boundary checks for the permanent existing-capability map.

The small synthetic catalogue tests source accounting, never Lean proof
validity. The real-repository check uses the selected compiled catalogue and
requires every current formal module to have an explicit retained route.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.entropy_framework import reuse
from tools.entropy_framework.__main__ import main
from tools.entropy_framework.registry import FrameworkError


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def make_root(root):
    """Author a two-module fixture independently of the production enumerator."""
    contents = {
        "formal/Nabt/Origin.lean": "import Std\nnamespace Nabt.Origin\ntheorem same (x : Nat) : x = x := rfl\nend Nabt.Origin\n",
        "formal/Nabt/Data.lean": "import Nabt.Origin\nnamespace Nabt.Data\ndef units := [1,2]\nend Nabt.Data\n",
        "formal/lakefile.lean": "lean_exe oldConsumer where\n  root := `OldConsumer\n",
        "formal/OldConsumer.lean": "import Nabt.Origin\ndef main : IO Unit := pure ()\n",
        "formal/lean-toolchain": "leanprover/lean4:v4.34.1\n",
        "formal/theorems.json": json.dumps({"theorems": ["Nabt.Origin.same"]}),
        "tools/proof_catalog.py": "# Existing catalogue producer identity.\n",
        "tools/old_consumer.py": "from tools import old_checker\n",
        "tools/old_checker.py": "def check():\n    return True\n",
        "tests/test_old_consumer.py": "# Independent historical check.\n",
        "docs/OLD_CONTRACT.md": "Conditional original contract.\n",
        "tools/entropy_framework/reuse.py": "# Current use-map implementation identity.\n",
        "tools/entropy_framework/reuse_run.py": "# Existing CLI delegation identity.\n",
        "tools/entropy_framework/__main__.py": "# Existing organizational CLI.\n",
        "tools/code_entropy.py": "# Existing static import audit.\n",
        "tools/check_sourced_acquisition_links.py": "# Existing compiled/source-header validation.\n",
        reuse.SELECTOR: "NABT_PROOF_REFERENCE_DIR ?= evidence/current\n",
    }
    for path, text in contents.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    inputs = {name: digest(text.encode()) for name, text in contents.items()
              if name.startswith("formal/") or name == "tools/proof_catalog.py"}
    declaration = {
        "name": "Nabt.Origin.same", "module": "Nabt.Origin",
        "canonical_name": "Nabt.Origin.same", "statement_sha256": "a" * 64,
        "universe_parameters": 0,
        "range": {"line": 3, "end_line": 3},
        "source_path": "formal/Nabt/Origin.lean",
        "source_sha256": inputs["formal/Nabt/Origin.lean"],
        "proof_dependencies": ["Eq.refl"],
        "type_dependencies": ["Eq", "Nat"], "axioms": [],
    }
    catalog = {
        "schema": "nabt.compiled-proof-catalog.v1",
        "authority": "COMPILED_DECLARATION_INDEX_ONLY",
        "lean_toolchain": "leanprover/lean4:v4.34.1",
        "inputs": inputs,
        "counts": {"advertised_declarations": 1, "normalized_statement_groups": 1},
        "theorems": [declaration],
    }
    directory = root / "evidence/current"
    directory.mkdir(parents=True)
    (directory / "proof_catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    family = {
        "id": "origin-and-data", "title_ar": "الأصل وبياناته",
        "formal_modules": ["Nabt.Origin", "Nabt.Data"],
        "runtime_paths": ["tools/old_consumer.py"],
        "checker_paths": ["tools/old_checker.py"],
        "test_paths": ["tests/test_old_consumer.py"],
        "doc_paths": ["docs/OLD_CONTRACT.md"],
        "native_targets": ["oldConsumer"], "entrypoint_ids": ["old-consumer"],
        "scope": "Equality preservation with its supplied premise.",
        "open_debts": ["General text acquisition is not established by this route."],
    }
    registry = {"reuse": {"schema": "nabt.proof-reuse.v1", "families": [family]}}
    (root / reuse.REGISTRY).write_text(json.dumps(registry), encoding="utf-8")
    entries = {"old-consumer": {"module": "tools.old_consumer", "native_target": None,
                                "description": "The original consumer.", "args_help": "--help"}}
    return registry, catalog, entries


class ProofReuseBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.registry, self.catalog, self.entries = make_root(self.root)
        self.entries_patch = patch("tools.entropy_framework.reuse_run.describe_entries", return_value=self.entries)
        self.entries_patch.start()
        self.addCleanup(self.entries_patch.stop)

    def build(self, **kwargs):
        return reuse.build_reuse_report(self.root, **kwargs)

    def write_catalog(self, value):
        (self.root / "evidence/current/proof_catalog.json").write_text(json.dumps(value), encoding="utf-8")

    def test_derived_population_distinguishes_proof_and_data(self):
        before = deepcopy(self.registry)
        report = self.build(registry=self.registry)
        self.assertEqual(report["population"], {
            "formal_modules": 2, "theorem_bearing_modules": 1,
            "data_or_definition_modules": 1, "advertised_declarations": 1,
            "normalized_statement_groups": 1, "families": 1,
        })
        rows = {row["module"]: row for row in report["modules"]}
        self.assertEqual(rows["Nabt.Data"]["declaration_count"], 0)
        self.assertEqual(rows["Nabt.Origin"]["declarations"][0]["name"], "Nabt.Origin.same")
        statement = rows["Nabt.Origin"]["declarations"][0]["source_statement"]
        self.assertEqual(statement["status"], "EXACT_SOURCE_HEADER")
        self.assertIn("(x : Nat)", statement["declaration_header"])
        self.assertEqual(self.registry, before)
        self.assertEqual(report, self.build(registry=self.registry))

    def test_relations_keep_compiled_static_and_authored_evidence_separate(self):
        report = self.build()
        relation = report["relations"]
        self.assertEqual(relation["compiled_proof_dependencies"][0]["to"], ["Eq.refl"])
        self.assertEqual(relation["compiled_type_dependencies"][0]["to"], ["Eq", "Nat"])
        self.assertIn({"from": "Nabt.Data", "to": "Nabt.Origin", "kind": "LEAN_MODULE_IMPORT",
                       "target_in_nabt_module_population": True}, relation["lean_module_imports"])
        self.assertEqual(relation["static_python_imports"]["edges"], [{
            "from": "tools.old_consumer", "to": "tools.old_checker", "kind": "STATIC_PYTHON_IMPORT"}])
        self.assertTrue(all(row["kind"].startswith("AUTHORED_") for row in relation["authored_routes"]))
        for row in relation["authored_routes"]:
            if row["from"].startswith("Nabt."):
                self.assertEqual(row["kind"], "AUTHORED_FAMILY_MEMBERSHIP")
                self.assertTrue(row["to"].startswith("family:"))

    def test_binary_presence_and_full_mapping_do_not_claim_execution(self):
        binary = self.root / "formal/.lake/build/bin/oldConsumer"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"unexecuted binary")
        report = self.build()
        self.assertTrue(report["families"][0]["native_availability"][0]["binary_present"])
        self.assertFalse(report["runtime_execution_performed"])
        self.assertFalse(report["all_capabilities_executed"])
        self.assertFalse(report["catalogue"]["compiled_this_run"])
        self.assertEqual(report["execution_receipts"], [])
        self.assertEqual(report["semantic_authority"], "NONE")
        self.assertEqual(len(report["open_bridge_debts"]), 1)

    def test_stale_source_does_not_disappear_under_selection(self):
        (self.root / "formal/Nabt/Data.lean").write_text("-- changed", encoding="utf-8")
        with self.assertRaisesRegex(FrameworkError, "stale compiled catalogue input"):
            self.build(module="Nabt.Origin")

    def test_new_lean_source_or_deleted_input_invalidates_catalogue(self):
        path = self.root / "formal/Nabt/New.lean"
        path.write_text("import Nabt.Origin\n", encoding="utf-8")
        with self.assertRaisesRegex(FrameworkError, "every current Lean source"):
            self.build()
        path.unlink()
        (self.root / "formal/Nabt/Origin.lean").unlink()
        with self.assertRaisesRegex(FrameworkError, "missing or escaped file"):
            self.build()

    def test_manifest_change_fails_even_if_its_hash_is_replaced(self):
        manifest = self.root / "formal/theorems.json"
        manifest.write_text(json.dumps({"theorems": ["Nabt.Origin.same", "Nabt.Origin.extra"]}))
        altered = deepcopy(self.catalog)
        altered["inputs"]["formal/theorems.json"] = digest(manifest.read_bytes())
        self.write_catalog(altered)
        with self.assertRaisesRegex(FrameworkError, "exact current manifest"):
            self.build()

    def test_later_make_assignment_cannot_silently_override_selected_snapshot(self):
        original = (self.root / reuse.SELECTOR).read_text()
        for assignment in ("NABT_PROOF_REFERENCE_DIR := evidence/other",
                           "override NABT_PROOF_REFERENCE_DIR = evidence/other",
                           "undefine NABT_PROOF_REFERENCE_DIR"):
            (self.root / reuse.SELECTOR).write_text(original + assignment + "\n")
            with self.subTest(assignment=assignment), self.assertRaisesRegex(FrameworkError, "unoverridden literal default"):
                self.build()

    def test_duplicate_and_missing_module_routes_rejected(self):
        for mutation, error in (("missing", "unmapped formal modules"), ("duplicate", "more than once")):
            registry = deepcopy(self.registry)
            family = registry["reuse"]["families"][0]
            if mutation == "missing":
                family["formal_modules"].remove("Nabt.Data")
            else:
                registry["reuse"]["families"].append(dict(family, id="another-family"))
            with self.subTest(mutation=mutation), self.assertRaisesRegex(FrameworkError, error):
                self.build(registry=registry)

    def test_unknown_native_entrypoint_module_and_missing_path_rejected(self):
        for field, replacement in (("native_targets", ["invented"]),
                                   ("entrypoint_ids", ["invented"]),
                                   ("formal_modules", ["Nabt.Invented"]),
                                   ("runtime_paths", ["tools/does_not_exist.py"])):
            registry = deepcopy(self.registry)
            registry["reuse"]["families"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                self.build(registry=registry)

    def test_code_owned_entrypoint_must_resolve_to_local_source_or_declared_native(self):
        self.entries["old-consumer"]["module"] = "tools.missing_consumer"
        with self.assertRaisesRegex(FrameworkError, "missing or ambiguous local entrypoint module"):
            self.build()
        self.entries["old-consumer"].update(module=None, native_target="missingNative")
        with self.assertRaisesRegex(FrameworkError, "undeclared native target"):
            self.build()
        self.entries["old-consumer"].update(module="tools.old_consumer", native_target="oldConsumer")
        with self.assertRaisesRegex(FrameworkError, "exactly one"):
            self.build()

    def test_authority_and_execution_fields_are_not_route_inputs(self):
        for field, value in (("status", "PROVED"), ("executed", True),
                             ("semantic_authority", "CERTAIN"), ("theorems", ["invented"])):
            registry = deepcopy(self.registry)
            registry["reuse"]["families"][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(FrameworkError, "invalid family fields"):
                self.build(registry=registry)

    def test_catalogue_count_bool_cannot_impersonate_integer(self):
        altered = deepcopy(self.catalog)
        altered["counts"]["advertised_declarations"] = True
        self.write_catalog(altered)
        with self.assertRaisesRegex(FrameworkError, "catalogue count differs"):
            self.build()

    def test_escaped_and_symlinked_reference_paths_fail(self):
        for path in ("../outside.py", "/tmp/outside.py", "tools/../tools/old_consumer.py"):
            registry = deepcopy(self.registry)
            registry["reuse"]["families"][0]["runtime_paths"] = [path]
            with self.subTest(path=path), self.assertRaisesRegex(FrameworkError, "noncanonical repository path"):
                self.build(registry=registry)
        linked = self.root / "tools/linked.py"
        linked.symlink_to(self.root / "tools/old_consumer.py")
        registry = deepcopy(self.registry)
        registry["reuse"]["families"][0]["runtime_paths"] = ["tools/linked.py"]
        with self.assertRaisesRegex(FrameworkError, "symlink is not a source identity"):
            self.build(registry=registry)

    def test_proof_only_family_keeps_its_debt(self):
        registry = deepcopy(self.registry)
        family = registry["reuse"]["families"][0]
        family["runtime_paths"] = []
        family["native_targets"] = []
        family["entrypoint_ids"] = []
        report = self.build(registry=registry)
        self.assertEqual(len(report["open_bridge_debts"]), 1)
        family["open_debts"] = []
        with self.assertRaisesRegex(FrameworkError, "unconsumed family needs an explicit open debt"):
            self.build(registry=registry)

    def test_module_query_retains_full_validation_and_references(self):
        report = self.build(module="Nabt.Origin")
        self.assertEqual([row["module"] for row in report["modules"]], ["Nabt.Origin"])
        self.assertEqual(report["population"]["formal_modules"], 2)
        self.assertEqual(report["selection"]["formal_modules"], 1)
        self.assertEqual(report["families"][0]["entrypoint_ids"], ["old-consumer"])
        for kwargs in ({"module": "Nabt.Missing"}, {"family": "missing"},
                       {"module": "Nabt.Origin", "family": "origin-and-data"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(FrameworkError):
                self.build(**kwargs)


class ProofReuseCliTests(unittest.TestCase):
    def test_delegation_preserves_child_status_and_does_not_emit_report(self):
        with patch("tools.entropy_framework.reuse.build_reuse_report", return_value={}), \
             patch("tools.entropy_framework.reuse_run.run_entry", return_value=7) as runner, \
             redirect_stdout(io.StringIO()) as output:
            status = main(["reuse", "--run", "old-consumer", "--", "--output", "original.json"])
        self.assertEqual(status, 7)
        runner.assert_called_once_with("old-consumer", ["--output", "original.json"])
        self.assertEqual(output.getvalue(), "")

    def test_failed_catalogue_validation_never_dispatches(self):
        with patch("tools.entropy_framework.reuse.build_reuse_report", side_effect=FrameworkError("stale")), \
             patch("tools.entropy_framework.reuse_run.run_entry") as runner, \
             redirect_stdout(io.StringIO()) as output:
            status = main(["reuse", "--run", "old-consumer"])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output.getvalue())["semantic_authority"], "NONE")
        runner.assert_not_called()


class InstalledProofReuseTests(unittest.TestCase):
    def test_every_current_module_and_theorem_resolves_without_claiming_execution(self):
        report = reuse.build_reuse_report()
        root = Path(__file__).resolve().parents[1]
        expected_modules = {"Nabt." + path.relative_to(root / "formal/Nabt").with_suffix("").as_posix().replace("/", ".")
                            for path in (root / "formal/Nabt").rglob("*.lean")}
        manifest = json.loads((root / "formal/theorems.json").read_text())["theorems"]
        self.assertEqual({row["module"] for row in report["modules"]}, expected_modules)
        self.assertEqual({declaration["name"] for row in report["modules"] for declaration in row["declarations"]},
                         set(manifest))
        assigned = [module for family in report["families"] for module in family["formal_modules"]]
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertEqual(set(assigned), expected_modules)
        self.assertEqual(report["population"]["advertised_declarations"], len(manifest))
        self.assertFalse(report["runtime_execution_performed"])
        self.assertFalse(report["all_capabilities_executed"])
        self.assertTrue(report["open_bridge_debts"])


if __name__ == "__main__":
    unittest.main()
