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
OLD = ROOT / "evidence/certified_natural_use_v1"
NEW = ROOT / "evidence/progressive_rule_audit_v1"
PREVIOUS = {
    "code_freeze_v1.json": "1b49907b0b0ec2475113daa93366a6ec127b7b303c12d8e3313681c30bbdab0f",
    "code_freeze_v1.tar.gz": "16a6e83e0d8cffe5898789751a221053da1530119ec12871be52fc26e6968d01",
    "regression_policy_v1.json": "452d9aa53b92883cf416809d099a663f253306adaace9d2762e605faf56b6e81",
    "independent_oracle/runner_freeze_v5.json": "7965b7ac4d69fd0ed0cdf73811bad94d25559852a70f249d642eec5a59793eb7",
}


class ProgressiveRuleRuntimeFreezeTests(unittest.TestCase):
    def test_previous_published_identities_are_immutable(self):
        for name, expected in PREVIOUS.items():
            with self.subTest(name=name):
                self.assertEqual(sha256((OLD / name).read_bytes()).hexdigest(), expected)

    def test_current_runtime_adds_only_the_named_surface_and_registration(self):
        current = verify_code_freeze(NEW / "code_freeze_v1.json", ROOT)
        old = json.loads((OLD / "code_freeze_v1.json").read_bytes())
        before, after = ({row["path"]: row for row in freeze["files"]}
                         for freeze in (old, current))
        self.assertEqual(set(after) - set(before), {"src/nabt/classical_certified.py"})
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

    def test_omitting_the_added_module_cannot_reuse_the_previous_inventory(self):
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
            expected = (before.replace("evidence/certified_natural_use_v1/",
                                       "evidence/progressive_rule_audit_v1/")
                        .replace("nabt.certified-natural-use.", "nabt.progressive-rule-audit.")
                        .replace("runner_freeze_v5.json", "runner_freeze_v1.json"))
            with self.subTest(name=name):
                self.assertEqual((NEW / "independent_oracle" / name).read_text(), expected)

    def test_current_oracle_and_holdout_have_the_complete_registered_identity(self):
        path = NEW / "independent_oracle/run_oracle_v1.py"
        spec = importlib.util.spec_from_file_location("progressive_rule_oracle", path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        receipt = runner.check_runner_freeze(path.with_name("runner_freeze_v1.json"))
        self.assertTrue(receipt["files"])
        from tools import framework_foundation_postreview as review
        manifest = NEW / "code_freeze_v1.json"
        current = json.loads(manifest.read_bytes())
        self.assertEqual(review.RUNTIME_SHA256, sha256(manifest.read_bytes()).hexdigest())
        self.assertEqual(review.RUNTIME_SNAPSHOT_SHA256, current["snapshot_sha256"])
        self.assertEqual(review.RUNTIME_ARCHIVE_SHA256, current["archive_sha256"])


if __name__ == "__main__":
    unittest.main()
