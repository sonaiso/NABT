"""The additive proof paths cannot rewrite historical coverage obligations."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from tools.text_evaluation.integrity import verify_code_freeze

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "evidence/progressive_rule_audit_v1"
NEW = ROOT / "evidence/source_acquisition_v1"
PREVIOUS = {
    "code_freeze_v1.json": "b184a00c3c19b3204b889f14567b042c987046e7698f657bf9586ff307f01cf5",
    "code_freeze_v1.tar.gz": "8646f73fef57bd97428cc3686843a0f3c9e12f2cf850342c6462e507c232c8e9",
    "regression_policy_v1.json": "4f1660cbba2b513f134f0677e5b48a04d57139b32b9a475b280bd4417a35664f",
    "independent_oracle/runner_freeze_v1.json": "e3ddc002acc6b9ac951b9c7c36e1c7d42e936b5854aeed97b6b5848abbb411b5",
}


class SourceAcquisitionRuntimeFreezeTests(unittest.TestCase):
    def test_previous_published_identities_are_immutable(self):
        for name, expected in PREVIOUS.items():
            with self.subTest(name=name):
                self.assertEqual(sha256((OLD / name).read_bytes()).hexdigest(), expected)

    def test_current_runtime_changes_only_native_acquisition_registration(self):
        current = verify_code_freeze(NEW / "code_freeze_v1.json", ROOT)
        old = json.loads((OLD / "code_freeze_v1.json").read_bytes())
        before, after = ({row["path"]: row for row in freeze["files"]}
                         for freeze in (old, current))
        self.assertFalse(set(after) - set(before))
        self.assertFalse(set(before) - set(after))
        self.assertEqual([name for name in before if before[name] != after[name]],
                         ["src/nabt/data/framework_foundation.json"])
        self.assertEqual(len(after), 102)
        self.assertEqual(current["previous_runtime_manifest_sha256"], PREVIOUS["code_freeze_v1.json"])
        with self.assertRaises(ValueError):
            verify_code_freeze(OLD / "code_freeze_v1.json", ROOT)
        archive_path = NEW / current["archive_filename"]
        self.assertEqual(sha256(archive_path.read_bytes()).hexdigest(), current["archive_sha256"])
        with tarfile.open(archive_path, "r:gz") as archive:
            self.assertEqual(len(archive.getmembers()), len(after))
            self.assertEqual({member.name for member in archive.getmembers()}, set(after))
            for member in archive.getmembers():
                raw = archive.extractfile(member).read()
                self.assertEqual((len(raw), sha256(raw).hexdigest()),
                                 (after[member.name]["bytes"], after[member.name]["sha256"]))

    def test_policy_keeps_every_failure_and_denominator(self):
        before = json.loads((OLD / "regression_policy_v1.json").read_bytes())
        after = json.loads((NEW / "regression_policy_v1.json").read_bytes())
        self.assertEqual(after["suites"], before["suites"])
        self.assertEqual(after["previous_policy_sha256"], PREVIOUS["regression_policy_v1.json"])
        self.assertEqual(after["runtime_file_count"], 102)
        from tools import framework_foundation_gate as gate
        self.assertEqual(gate.load_policy(), after)
        self.assertEqual(gate.RUNTIME_SHA256,
                         sha256((NEW / "code_freeze_v1.json").read_bytes()).hexdigest())

    def test_omitting_an_authoritative_module_is_rejected(self):
        current = json.loads((NEW / "code_freeze_v1.json").read_bytes())
        current["files"] = [row for row in current["files"]
                            if row["path"] != "src/nabt/classical_certified.py"]
        current["snapshot_sha256"] = sha256(json.dumps(
            current["files"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incomplete.json"
            path.write_text(json.dumps(current))
            with self.assertRaisesRegex(ValueError, "exactly the authoritative"):
                verify_code_freeze(path, ROOT)

    def test_continuation_wrappers_change_only_versioned_execution_identity(self):
        for name in ("run_oracle_v1.py", "run_regression_v1.py",
                     "review_continuation_v1.py", "run_source_counterexamples_v1.py"):
            before = (OLD / "independent_oracle" / name).read_text()
            expected = (before.replace("evidence/progressive_rule_audit_v1/",
                                       "evidence/source_acquisition_v1/")
                        .replace("nabt.progressive-rule-audit.", "nabt.source-acquisition.")
                        .replace("runner_freeze_v1.json", "runner_freeze_v5.json"))
            if name == "run_oracle_v1.py":
                marker = "    dependency=importlib.util.module_from_spec(dependency_spec);dependency_spec.loader.exec_module(dependency)\n"
                expected = expected.replace(marker, marker + "    dependency.check_execution_lifecycle(freeze)\n", 1)
            with self.subTest(name=name):
                self.assertEqual((NEW / "independent_oracle" / name).read_text(), expected)

    def test_refreeze_records_the_observed_execution_without_reclaiming_priority(self):
        path = NEW / "independent_oracle/freeze_runner_v1.py"
        spec = importlib.util.spec_from_file_location("source_acquisition_freezer", path)
        freezer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(freezer)
        record = json.loads(path.with_name("runner_freeze_v5.json").read_bytes())
        freezer.check_execution_lifecycle(record)
        self.assertIs(record["before_first_new_runtime_oracle_prediction"], False)
        self.assertEqual(record["freeze_phase"], "dependency_refreeze_after_observed_execution")
        self.assertNotIn("previous_runner_freeze_sha256", record)
        first = record["prior_observed_runtime_execution"]
        self.assertEqual(first["runner_sha256"], record["initial_pre_oracle_dependency_freeze"]["sha256"])
        self.assertEqual(first["runtime_freeze_sha256"], record["runtime_freeze_sha256"])
        for value in (True, 0, None, "false"):
            forged = dict(record, before_first_new_runtime_oracle_prediction=value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "execution lifecycle"):
                freezer.check_execution_lifecycle(forged)
        for field in ("freeze_phase", "prior_observed_runtime_execution", "initial_pre_oracle_dependency_freeze"):
            forged = dict(record)
            forged.pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "execution lifecycle"):
                freezer.check_execution_lifecycle(forged)
        from datetime import datetime
        first_time = datetime.fromisoformat(first["started_utc"])
        superseded_time = datetime.fromisoformat(record["superseded_dependency_freeze"]["created_utc"])
        between = first_time + (superseded_time - first_time) / 2
        forged = dict(record, created_utc=between.isoformat())
        with self.assertRaisesRegex(ValueError, "superseded dependency freeze"):
            freezer.check_execution_lifecycle(forged)
        forged = dict(record, created_utc="2000-01-01T00:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "does not follow"):
            freezer.check_execution_lifecycle(forged)

    def test_current_oracle_and_holdout_have_the_complete_registered_identity(self):
        path = NEW / "independent_oracle/run_oracle_v1.py"
        spec = importlib.util.spec_from_file_location("source_acquisition_oracle", path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        receipt = runner.check_runner_freeze(path.with_name("runner_freeze_v5.json"))
        self.assertTrue(receipt["files"])
        from tools import framework_foundation_postreview as review
        manifest = NEW / "code_freeze_v1.json"
        current = json.loads(manifest.read_bytes())
        self.assertEqual(review.RUNTIME_SHA256, sha256(manifest.read_bytes()).hexdigest())
        self.assertEqual(review.RUNTIME_SNAPSHOT_SHA256, current["snapshot_sha256"])
        self.assertEqual(review.RUNTIME_ARCHIVE_SHA256, current["archive_sha256"])

    def test_current_catalog_includes_the_actual_new_kernel_declarations(self):
        folder = NEW / "catalog_references"
        migration = json.loads((folder / "catalog_migration.json").read_bytes())
        current = json.loads((folder / "proof_catalog.json").read_bytes())
        prior = json.loads((OLD / "catalog_references/proof_catalog.json").read_bytes())
        names = {row["name"] for row in current["theorems"]}
        old_names = {row["name"] for row in prior["theorems"]}
        self.assertTrue(old_names <= names)
        self.assertEqual(len(names), 1611)
        added = names - old_names
        self.assertEqual(len(added), 32)
        self.assertEqual(sum(name.startswith("Nabt.LexicalSourceAcquisition.") for name in added), 21)
        self.assertEqual(sum(name.startswith("Nabt.QualifiedCueLicensing.") for name in added), 11)
        self.assertEqual(migration["added_declarations"], sorted(added))
        audit_path = ROOT / migration["kernel_audit"]["path"]
        self.assertEqual(sha256(audit_path.read_bytes()).hexdigest(),
                         migration["kernel_audit"]["sha256"])
        audit = json.loads(audit_path.read_bytes())
        self.assertIs(audit["ok"], True)
        self.assertEqual(set(audit["theorem_axioms"]), names)


if __name__ == "__main__":
    unittest.main()
