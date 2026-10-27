"""New admission identities cannot replace old observations or widen their gold."""
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
OLD = ROOT / "evidence/source_acquisition_v1"
NEW = ROOT / "evidence/interface_migration_v1"
PREVIOUS = {
    "code_freeze_v1.json": "ba748dfab327531e79bd0f35814c43e37501315faad9cfdce5835f3939fbec7b",
    "code_freeze_v1.tar.gz": "19471ac4523c0e829579e71df563ab6703f814101ee20c94c3c7331e14ca3a94",
    "regression_policy_v1.json": "855af093fb8534aeb87c60450a36365d4d05b636864454e397d5a9943cc19e63",
    "independent_oracle/runner_freeze_v5.json": "ecf96d1d8eabaa42d53522d179142ace305587eec3a3b49bd52a799a12ac323a",
}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class InterfaceMigrationRuntimeFreezeTests(unittest.TestCase):
    def test_published_predecessor_bytes_remain_exact(self):
        for name, expected in PREVIOUS.items():
            with self.subTest(name=name):
                self.assertEqual(sha256((OLD / name).read_bytes()).hexdigest(), expected)

    def test_current_runtime_is_exact_registration_only_and_archived(self):
        current = verify_code_freeze(NEW / "code_freeze_v1.json", ROOT)
        old = json.loads((OLD / "code_freeze_v1.json").read_bytes())
        before, after = ({row["path"]: row for row in item["files"]} for item in (old, current))
        self.assertEqual(set(before), set(after))
        self.assertEqual([name for name in before if before[name] != after[name]],
                         ["src/nabt/data/framework_foundation.json"])
        self.assertEqual(current["previous_runtime_manifest_sha256"], PREVIOUS["code_freeze_v1.json"])
        self.assertEqual(len(after), 102)
        with self.assertRaises(ValueError):
            verify_code_freeze(OLD / "code_freeze_v1.json", ROOT)
        path = NEW / current["archive_filename"]
        self.assertEqual(sha256(path.read_bytes()).hexdigest(), current["archive_sha256"])
        with tarfile.open(path, "r:gz") as saved:
            members = saved.getmembers()
            self.assertEqual(len(members), len(after))
            self.assertEqual({m.name for m in members}, set(after))
            for member in members:
                self.assertTrue(member.isfile())
                raw = saved.extractfile(member).read()
                self.assertEqual((len(raw), sha256(raw).hexdigest()),
                                 (after[member.name]["bytes"], after[member.name]["sha256"]))

    def test_policy_keeps_every_case_threshold_and_failure_signature(self):
        old = json.loads((OLD / "regression_policy_v1.json").read_bytes())
        current = json.loads((NEW / "regression_policy_v1.json").read_bytes())
        self.assertEqual(current["suites"], old["suites"])
        self.assertEqual(current["previous_policy_sha256"], PREVIOUS["regression_policy_v1.json"])
        self.assertEqual(current["runtime_file_count"], 102)
        self.assertEqual(gate.load_policy(), current)
        self.assertEqual(gate.RUNTIME_SHA256, sha256((NEW / "code_freeze_v1.json").read_bytes()).hexdigest())

    def test_inventory_omission_is_not_covered_by_rehashed_manifest(self):
        current = json.loads((NEW / "code_freeze_v1.json").read_bytes())
        current["files"] = [r for r in current["files"] if r["path"] != "src/nabt/classical_certified.py"]
        current["snapshot_sha256"] = sha256(json.dumps(
            current["files"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "omitted.json"
            path.write_text(json.dumps(current))
            with self.assertRaisesRegex(ValueError, "exactly the authoritative"):
                verify_code_freeze(path, ROOT)

    def test_continuation_changes_identity_only_not_scoring(self):
        for name in ("run_oracle_v1.py", "run_regression_v1.py", "review_continuation_v1.py",
                     "run_source_counterexamples_v1.py", "test_continuation_v1.py"):
            expected = ((OLD / "independent_oracle" / name).read_text()
                        .replace("evidence/source_acquisition_v1/", "evidence/interface_migration_v1/")
                        .replace("nabt.source-acquisition.", "nabt.interface-migration.")
                        .replace("runner_freeze_v5.json", "runner_freeze_v1.json"))
            if name == "test_continuation_v1.py":
                # This test's predecessor identity advances with the wrapper;
                # none of its semantic tamper controls or expected scores change.
                expected = (expected.replace(
                    "evidence/progressive_rule_audit_v1/independent_oracle/runner_freeze_v1.json",
                    "evidence/source_acquisition_v1/independent_oracle/runner_freeze_v5.json")
                    .replace("e3ddc002acc6b9ac951b9c7c36e1c7d42e936b5854aeed97b6b5848abbb411b5",
                             PREVIOUS["independent_oracle/runner_freeze_v5.json"])
                    .replace("'/source_acquisition_v1/independent_oracle/review_'",
                             "'/interface_migration_v1/independent_oracle/review_'"))
            with self.subTest(name=name):
                self.assertEqual((NEW / "independent_oracle" / name).read_text(), expected)

    def test_dependency_freeze_is_post_development_not_an_unseen_test_claim(self):
        path = NEW / "independent_oracle/freeze_runner_v1.py"
        freezer = module("interface_dependency_freezer", path)
        record = json.loads(path.with_name("runner_freeze_v1.json").read_bytes())
        freezer.check_execution_lifecycle(record)
        self.assertIs(record["before_first_new_runtime_oracle_prediction"], False)
        self.assertIs(record["blind_evaluation_claimed"], False)
        self.assertIs(record["runtime_calls_performed_by_freezer"], False)
        for field in ("before_first_new_runtime_oracle_prediction", "blind_evaluation_claimed",
                      "runtime_calls_performed_by_freezer"):
            for fake in (True, 0, None, "false"):
                changed = deepcopy(record)
                changed[field] = fake
                with self.subTest(field=field, fake=fake), self.assertRaises(ValueError):
                    freezer.check_execution_lifecycle(changed)

    def test_runner_checks_complete_dependency_inventory_and_runtime_identity(self):
        runner = module("interface_migration_oracle_test", NEW / "independent_oracle/run_oracle_v1.py")
        receipt = runner.check_runner_freeze(NEW / "independent_oracle/runner_freeze_v1.json")
        self.assertTrue(receipt["files"])
        from tools import framework_foundation_postreview as review
        current = json.loads((NEW / "code_freeze_v1.json").read_bytes())
        self.assertEqual(review.RUNTIME_SHA256, gate.RUNTIME_SHA256)
        self.assertEqual(review.RUNTIME_SNAPSHOT_SHA256, current["snapshot_sha256"])
        self.assertEqual(review.RUNTIME_ARCHIVE_SHA256, current["archive_sha256"])


if __name__ == "__main__":
    unittest.main()
