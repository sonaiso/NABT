"""Versioned command migration retains old evidence and all old scoring duties."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from tools import framework_foundation_gate as gate
from tools.text_evaluation.integrity import verify_code_freeze

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "evidence/interface_migration_v1"
NEW = ROOT / "evidence/legacy_migration_v2"
PINS = {
    "code_freeze_v1.json": "b3a6ddeaf65f0f3c1397a0c265ba3b21fe4dafc0b088498345789b257e4c8271",
    "code_freeze_v1.tar.gz": "d65857512be35a17389dc69b5da5e4ba6b2b5d64f647f4bd49ab9ce2e862c4a5",
    "regression_policy_v1.json": "da9c90ed0b5d8fbf8be6cf5ebca490c16773af0931e82512a880feb60fd8472e",
    "independent_oracle/runner_freeze_v5.json": "0f7ae3bf2cab565b2976aa9b0cca39dc87a452f965dba7987ab95525ce890613",
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class LegacyMigrationRuntimeFreezeTests(unittest.TestCase):
    def test_published_predecessor_identities_are_immutable(self):
        for name, expected in PINS.items():
            with self.subTest(name=name):
                self.assertEqual(sha256((OLD / name).read_bytes()).hexdigest(), expected)

    def test_current_delta_and_archive_are_exact(self):
        current = verify_code_freeze(NEW / "code_freeze_v1.json", ROOT)
        previous = json.loads((OLD / "code_freeze_v1.json").read_bytes())
        before, after = ({row["path"]: row for row in freeze["files"]}
                         for freeze in (previous, current))
        changed = sorted(name for name in before if before[name] != after[name])
        added = sorted(set(after) - set(before))
        self.assertEqual(changed, ["src/nabt/cli.py", "src/nabt/data/framework_foundation.json"])
        self.assertEqual(added, ["src/nabt/data/transport_command_contracts.json",
                                 "src/nabt/transport_contract.py"])
        self.assertFalse(set(before) - set(after))
        self.assertEqual((current["changed_runtime_paths"], current["added_runtime_paths"]),
                         (changed, added))
        self.assertEqual(current["previous_runtime_manifest_sha256"], PINS["code_freeze_v1.json"])
        self.assertEqual(len(after), 104)
        with self.assertRaises(ValueError):
            verify_code_freeze(OLD / "code_freeze_v1.json", ROOT)
        archive_path = NEW / current["archive_filename"]
        self.assertEqual(sha256(archive_path.read_bytes()).hexdigest(), current["archive_sha256"])
        with tarfile.open(archive_path, "r:gz") as archive:
            self.assertEqual(len(archive.getmembers()), len(after))
            self.assertEqual({member.name for member in archive.getmembers()}, set(after))
            for member in archive.getmembers():
                self.assertTrue(member.isfile())
                raw = archive.extractfile(member).read()
                self.assertEqual((len(raw), sha256(raw).hexdigest()),
                                 (after[member.name]["bytes"], after[member.name]["sha256"]))

    def test_policy_preserves_all_material_denominators_and_failures(self):
        previous = json.loads((OLD / "regression_policy_v1.json").read_bytes())
        current = gate.load_policy()
        self.assertEqual(current["suites"], previous["suites"])
        self.assertEqual(current["previous_policy_sha256"], PINS["regression_policy_v1.json"])
        self.assertEqual(current["runtime_file_count"], 104)
        self.assertEqual(current["runtime_freeze_sha256"],
                         sha256((NEW / "code_freeze_v1.json").read_bytes()).hexdigest())

    def test_transport_module_cannot_be_omitted_from_rehashed_inventory(self):
        changed = json.loads((NEW / "code_freeze_v1.json").read_bytes())
        changed["files"] = [row for row in changed["files"]
                            if row["path"] != "src/nabt/transport_contract.py"]
        changed["snapshot_sha256"] = sha256(json.dumps(
            changed["files"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "omitted.json"
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "exactly the authoritative"):
                verify_code_freeze(path, ROOT)

    def test_continuation_changes_identity_only_not_material_or_scoring(self):
        for stem in ("run_oracle", "run_regression", "review_continuation",
                     "run_source_counterexamples", "test_continuation"):
            expected = ((OLD / "independent_oracle" / (stem + "_v5.py")).read_text()
                        .replace("evidence/interface_migration_v1/", "evidence/legacy_migration_v2/")
                        .replace("nabt.interface-migration.", "nabt.legacy-migration."))
            for name in ("run_oracle", "run_regression", "review_continuation",
                         "run_source_counterexamples", "test_continuation", "freeze_runner", "runner_freeze"):
                expected = expected.replace(name + "_v5", name + "_v1")
            for schema in ("directed-runner-freeze", "directed-oracle-execution",
                           "directed-regression", "directed-independent-review",
                           "directed-source-counterexamples", "continuation-review",
                           "regression-execution"):
                expected = expected.replace("nabt.legacy-migration." + schema + ".v5",
                                            "nabt.legacy-migration." + schema + ".v1")
            if stem == "test_continuation":
                expected = (expected.replace(
                    "evidence/legacy_migration_v2/independent_oracle/runner_freeze_v4.json",
                    "evidence/interface_migration_v1/independent_oracle/runner_freeze_v5.json")
                    .replace("1da2599f895c9e8b58bd1963176a09bae0dbebe5516b225d943b88fca1b3b00d",
                             PINS["independent_oracle/runner_freeze_v5.json"])
                    .replace("'/interface_migration_v1/independent_oracle/review_'",
                             "'/legacy_migration_v2/independent_oracle/review_'"))
            with self.subTest(stem=stem):
                self.assertEqual((NEW / "independent_oracle" / (stem + "_v1.py")).read_text(), expected)

    def test_predecessor_ci_is_not_presented_as_this_release_execution(self):
        record = json.loads((NEW / "predecessor_ci/final-six-workflows.json").read_bytes())
        self.assertEqual(sha256((NEW / "predecessor_ci/snapshot-13.json").read_bytes()).hexdigest(),
                         "8360859cc3a202baafeedfadaaf4581c67bbbdcb8a5bc4b6733c79eb94897a4e")
        self.assertEqual(sha256((NEW / "predecessor_ci/final-six-workflows.json").read_bytes()).hexdigest(),
                         "80dd493a5169bb88877f35c4aa0546bb4a964cd9582326f269d6390104194a3f")
        self.assertTrue(record)
        freezer = load_module("legacy_freezer_lifecycle", NEW / "independent_oracle/freeze_runner_v1.py")
        lifecycle = freezer._execution_lifecycle()
        self.assertEqual(lifecycle["previous_release_validation"]["commit"],
                         "8203c8ce1c2072c7659191b2a7194ce9f29555ad")
        self.assertIs(lifecycle["previous_release_validation"]["previous_counts_reused_as_current_results"], False)

    def test_dependency_freeze_has_honest_lifecycle_and_exact_inventory(self):
        folder = NEW / "independent_oracle"
        freezer = load_module("legacy_freezer_identity", folder / "freeze_runner_v1.py")
        runner = load_module("legacy_runner_identity", folder / "run_oracle_v1.py")
        path = folder / "runner_freeze_v1.json"
        checked = runner.check_runner_freeze(path)
        record = json.loads(path.read_bytes())
        freezer.check_execution_lifecycle(record)
        self.assertTrue(checked["files"])
        for field in ("before_first_new_runtime_oracle_prediction", "blind_evaluation_claimed",
                      "runtime_calls_performed_by_freezer"):
            self.assertIs(record[field], False)
            for forged in (True, 0, None, "false"):
                changed = deepcopy(record)
                changed[field] = forged
                with self.subTest(field=field, forged=forged), self.assertRaises(ValueError):
                    freezer.check_execution_lifecycle(changed)
        paths = {row["path"] for row in checked["files"]}
        for name in ("src/nabt/transport_contract.py", "tests/_transport_native.py",
                     "tools/linguistic_truth/discourse_boundary.py",
                     "evidence/legacy_migration_v2/independent_review/run_reference.py"):
            self.assertIn(name, paths)


if __name__ == "__main__":
    unittest.main()
