"""Administrative discovery migration cannot replace language evidence or gold."""
from hashlib import sha256
import json
from pathlib import Path
import tarfile
import unittest

from tools.text_evaluation.integrity import verify_code_freeze

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "evidence/framework_foundation_v1"
NEW = ROOT / "evidence/attested_mark_recovery_v1"


class AttestedMarkRuntimeMigration(unittest.TestCase):
    def test_previous_observed_manifest_and_archive_stay_immutable(self):
        for name, digest in (
            ("code_freeze_v2.json", "a192d915f933a8f98ddb4d166f741be4ab976d34cc2c13be71eb940f08ca06e4"),
            ("code_freeze_v2.tar.gz", "6da895ca88448dd9261f6acf0e5fe244fef311ef6dfe785acda9307a6b928598"),
            ("regression_policy_v2.json", "20b8eb82e9df6dd52905d1dd3bde2716fec819302b9a538a6f0965aa42dde275"),
        ):
            with self.subTest(name=name):
                self.assertEqual(sha256((OLD / name).read_bytes()).hexdigest(), digest)

    def test_only_discovery_registration_changes_in_complete_package_inventory(self):
        # This published migration is historical. Verify its captured bytes,
        # not the newer active checkout; the current migration has its own test.
        current = json.loads((NEW / "code_freeze_v1.json").read_bytes())
        old = json.loads((OLD / "code_freeze_v2.json").read_bytes())
        previous = {row["path"]: row for row in old["files"]}
        actual = {row["path"]: row for row in current["files"]}
        self.assertEqual(len(actual), 101)
        self.assertEqual(set(previous), set(actual))
        self.assertEqual([name for name in previous if previous[name] != actual[name]],
                         ["src/nabt/data/framework_foundation.json"])
        archive_path = NEW / current["archive_filename"]
        self.assertEqual(sha256(archive_path.read_bytes()).hexdigest(), current["archive_sha256"])
        with tarfile.open(archive_path, "r:gz") as archive:
            self.assertEqual({member.name for member in archive.getmembers()}, set(actual))
            for member in archive.getmembers():
                raw = archive.extractfile(member).read()
                self.assertEqual((len(raw), sha256(raw).hexdigest()),
                                 (actual[member.name]["bytes"], actual[member.name]["sha256"]))
        with self.assertRaises(ValueError):
            verify_code_freeze(NEW / "code_freeze_v1.json", ROOT)
        with self.assertRaises(ValueError):
            verify_code_freeze(OLD / "code_freeze_v2.json", ROOT)

    def test_policy_preserves_all_gold_checks_and_failure_signatures(self):
        old = json.loads((OLD / "regression_policy_v2.json").read_bytes())
        new = json.loads((NEW / "regression_policy_v1.json").read_bytes())
        self.assertEqual(new["suites"], old["suites"])
        self.assertEqual(new["runtime_file_count"], old["runtime_file_count"])
        self.assertEqual(new["previous_policy_sha256"], sha256((OLD / "regression_policy_v2.json").read_bytes()).hexdigest())

    def test_current_oracle_dependencies_are_frozen_without_new_prediction_claim(self):
        location = NEW / "independent_oracle/run_oracle_v1.py"
        raw = location.with_name("runner_freeze_v4.json").read_bytes()
        self.assertEqual(sha256(raw).hexdigest(),
                         "f5ada86aaedd33b823750e36fcae0610f4925621652f34c422d2cc67f54f102e")
        frozen = json.loads(raw)
        self.assertTrue(frozen["files"])
        self.assertIs(frozen["runtime_calls_performed_by_freezer"], False)
        self.assertIs(frozen["historical_files_repinned"], False)


if __name__ == "__main__":
    unittest.main()
