"""Current native-admission registration cannot waive historical language failures."""
from hashlib import sha256
import json
from pathlib import Path
import tarfile
import unittest

from tools.text_evaluation.integrity import verify_code_freeze

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "evidence/attested_mark_recovery_v1"
NEW = ROOT / "evidence/certified_natural_use_v1"


class CertifiedNaturalUseFreezeTests(unittest.TestCase):
    def test_previous_runtime_policy_and_oracle_remain_immutable(self):
        for name, expected in (
            ("code_freeze_v1.json", "1c47bfee3fa0baa190ec0e0455dfcb2528aec65a6280694956c1e00186948d30"),
            ("code_freeze_v1.tar.gz", "d04ff4bf22171441e5731bfdb67dd4b4d6e6470db0e75b58977656d42e5172c2"),
            ("regression_policy_v1.json", "784ba72cb7738d3639a267e82da0b510fbf1f7f284271b26eac3ffe66c26dad9"),
            ("independent_oracle/runner_freeze_v4.json", "f5ada86aaedd33b823750e36fcae0610f4925621652f34c422d2cc67f54f102e"),
        ):
            with self.subTest(name=name):
                self.assertEqual(sha256((OLD / name).read_bytes()).hexdigest(), expected)

    def test_discovery_is_the_only_packaged_change(self):
        current = json.loads((NEW / "code_freeze_v1.json").read_bytes())
        self.assertEqual(sha256((NEW / "code_freeze_v1.json").read_bytes()).hexdigest(),
                         "1b49907b0b0ec2475113daa93366a6ec127b7b303c12d8e3313681c30bbdab0f")
        archive_path = NEW / "code_freeze_v1.tar.gz"
        self.assertEqual(sha256(archive_path.read_bytes()).hexdigest(),
                         "16a6e83e0d8cffe5898789751a221053da1530119ec12871be52fc26e6968d01")
        by_path = {row["path"]: row for row in current["files"]}
        with tarfile.open(archive_path, "r:gz") as archive:
            self.assertEqual({member.name for member in archive.getmembers()}, set(by_path))
            self.assertEqual(len(archive.getmembers()), len(by_path))
            for member in archive.getmembers():
                raw = archive.extractfile(member).read()
                self.assertEqual((len(raw), sha256(raw).hexdigest()),
                                 (by_path[member.name]["bytes"], by_path[member.name]["sha256"]))
        with self.assertRaises(ValueError):
            verify_code_freeze(NEW / "code_freeze_v1.json", ROOT)
        old = json.loads((OLD / "code_freeze_v1.json").read_bytes())
        previous, actual = ({row["path"]: row for row in item["files"]} for item in (old, current))
        self.assertEqual(set(previous), set(actual))
        self.assertEqual(len(actual), 101)
        self.assertEqual([name for name in previous if previous[name] != actual[name]],
                         ["src/nabt/data/framework_foundation.json"])
        with self.assertRaises(ValueError):
            verify_code_freeze(OLD / "code_freeze_v1.json", ROOT)

    def test_all_existing_denominators_and_failure_signatures_are_preserved(self):
        old = json.loads((OLD / "regression_policy_v1.json").read_bytes())
        new = json.loads((NEW / "regression_policy_v1.json").read_bytes())
        self.assertEqual(new["suites"], old["suites"])
        self.assertEqual(new["runtime_file_count"], old["runtime_file_count"])
        self.assertEqual(new["previous_policy_sha256"], sha256((OLD / "regression_policy_v1.json").read_bytes()).hexdigest())

    def test_current_holdout_does_not_relabel_the_historical_identity(self):
        from tools import framework_foundation_postreview as review
        manifest = NEW / "code_freeze_v1.json"
        current = json.loads(manifest.read_bytes())
        self.assertNotEqual(review.RUNTIME_SHA256, sha256(manifest.read_bytes()).hexdigest())
        self.assertNotEqual(review.RUNTIME_SNAPSHOT_SHA256, current["snapshot_sha256"])
        self.assertNotEqual(review.RUNTIME_ARCHIVE_SHA256, current["archive_sha256"])

    def test_previous_oracle_identity_is_preserved_without_repinning(self):
        frozen_path = NEW / "independent_oracle/runner_freeze_v5.json"
        raw = frozen_path.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(),
                         "7965b7ac4d69fd0ed0cdf73811bad94d25559852a70f249d642eec5a59793eb7")
        frozen = json.loads(raw)
        self.assertTrue(frozen["files"])
        self.assertIs(frozen["runtime_calls_performed_by_freezer"], False)
        self.assertIs(frozen["historical_files_repinned"], False)


if __name__ == "__main__":
    unittest.main()
