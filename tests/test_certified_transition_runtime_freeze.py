"""A new source-acquisition registration cannot reseal old evidence or gold."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest

from tools import framework_foundation_gate as gate
from tools.text_evaluation.integrity import verify_code_freeze

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "evidence/legacy_migration_v2"
DEVELOPMENT = ROOT / "evidence/certified_transition_v1"
CURRENT = ROOT / "evidence/certified_transition_v2"
PREVIOUS_PINS = {
    "code_freeze_v1.json": "9f0eded8d010dcd349254adbc4cc4726c5c385aff53286dff37f3ba997fdca4b",
    "code_freeze_v1.tar.gz": "53a29f62b4a70382f05ccffaef5410b4f594ffd6260e51bf41e916f2df53f473",
    "regression_policy_v1.json": "8dac9b09df6c426446d4597421c15507bc80a15ab264d032e218a0caf5154cdc",
    "independent_oracle/runner_freeze_v1.json": "7a56b93650efa724a33d972d1b761c807ec884ae5a54ecfa217be2a35f656203",
}


class CertifiedTransitionFreezeTests(unittest.TestCase):
    def test_predecessor_evidence_remains_byte_identical(self):
        for name, digest in PREVIOUS_PINS.items():
            with self.subTest(name=name):
                self.assertEqual(sha256((PREVIOUS / name).read_bytes()).hexdigest(), digest)

    def test_development_identity_is_preserved_and_does_not_authorize_v2(self):
        for name, digest in {
            "code_freeze_v1.json": "7f6b8ace539ec969ecb56939929ac982eb85e064e103a2bd90983bda583104f8",
            "code_freeze_v1.tar.gz": "e488e15b491c1d5087b797810d17befcfd79c9bfc7d6493e49d19c69704340eb",
            "regression_policy_v1.json": "3ab23c2b16769123ed5d33ac01b5af46fdd82a911d7f6ca22c89b2435db07f7c",
        }.items():
            self.assertEqual(sha256((DEVELOPMENT / name).read_bytes()).hexdigest(), digest)
        with self.assertRaises(ValueError):
            verify_code_freeze(DEVELOPMENT / "code_freeze_v1.json", ROOT)
        before = json.loads((DEVELOPMENT / "code_freeze_v1.json").read_bytes())
        after = verify_code_freeze(CURRENT / "code_freeze_v1.json", ROOT)
        before_rows = {row["path"]: row for row in before["files"]}
        self.assertEqual([row["path"] for row in after["files"]
                          if row != before_rows[row["path"]]],
                         ["src/nabt/data/transport_command_contracts.json"])

    def test_registration_and_command_metadata_are_the_only_packaged_changes(self):
        current = verify_code_freeze(CURRENT / "code_freeze_v1.json", ROOT)
        previous = json.loads((PREVIOUS / "code_freeze_v1.json").read_bytes())
        old, new = ({row["path"]: row for row in item["files"]}
                    for item in (previous, current))
        self.assertEqual(set(old), set(new))
        self.assertEqual([name for name in old if old[name] != new[name]],
                         ["src/nabt/data/framework_foundation.json",
                          "src/nabt/data/transport_command_contracts.json"])
        self.assertEqual(current["changed_runtime_paths"],
                         ["src/nabt/data/transport_command_contracts.json"])
        self.assertEqual(current["added_runtime_paths"], [])
        self.assertEqual(current["removed_runtime_paths"], [])
        self.assertEqual(current["previous_runtime_manifest_sha256"],
                         sha256((DEVELOPMENT / "code_freeze_v1.json").read_bytes()).hexdigest())
        with self.assertRaises(ValueError):
            verify_code_freeze(PREVIOUS / "code_freeze_v1.json", ROOT)
        archive = CURRENT / current["archive_filename"]
        self.assertEqual(sha256(archive.read_bytes()).hexdigest(), current["archive_sha256"])
        with tarfile.open(archive, "r:gz") as saved:
            self.assertEqual({member.name for member in saved.getmembers()}, set(new))
            self.assertEqual(len(saved.getmembers()), len(new))
            for member in saved.getmembers():
                self.assertTrue(member.isfile())
                raw = saved.extractfile(member).read()
                self.assertEqual((len(raw), sha256(raw).hexdigest()),
                                 (new[member.name]["bytes"], new[member.name]["sha256"]))

    def test_existing_surfaces_and_authority_contracts_are_preserved(self):
        name = "src/nabt/data/framework_foundation.json"
        with tarfile.open(PREVIOUS / "code_freeze_v1.tar.gz", "r:gz") as saved:
            before = json.loads(saved.extractfile(name).read())
        after = json.loads((ROOT / name).read_bytes())
        by_id = {row["id"]: row for row in after["surfaces"]}
        for row in before["surfaces"]:
            self.assertEqual(by_id[row["id"]], row)
        new = by_id["tools.linguistic_truth.six_noun.acquire_six_noun"]
        self.assertEqual(new["guard_kind"], "runtime_foundation")
        self.assertIs(new["projection_completeness_established"], False)
        self.assertIn("sixNounAcquisition", after["discovery"]["lean_executables"])
        for key in ("foundation_law_id", "alphabet_id", "transport_contract"):
            self.assertEqual(after[key], before[key])
        for key, entries in before["discovery"].items():
            if isinstance(entries, list):
                self.assertTrue(set(entries).issubset(after["discovery"][key]), key)
            else:
                self.assertEqual(entries, after["discovery"][key])

    def test_policy_never_relabels_old_language_results(self):
        before = json.loads((PREVIOUS / "regression_policy_v1.json").read_bytes())
        after = gate.load_policy()
        self.assertEqual(after["suites"], before["suites"])
        self.assertEqual(after["previous_policy_sha256"],
                         sha256((DEVELOPMENT / "regression_policy_v1.json").read_bytes()).hexdigest())
        self.assertEqual(after["runtime_file_count"], before["runtime_file_count"])
        self.assertEqual(after["runtime_freeze_sha256"],
                         sha256((CURRENT / "code_freeze_v1.json").read_bytes()).hexdigest())
        migration = json.loads((CURRENT / "runtime_migration.json").read_bytes())
        for field in ("historical_material_changed", "historical_thresholds_changed",
                      "runtime_calls_performed_by_migration"):
            self.assertIs(migration[field], False)

    def test_continuation_preserves_material_and_scoring_logic(self):
        for name in ("run_oracle_v1.py", "run_regression_v1.py", "review_continuation_v1.py",
                     "run_source_counterexamples_v1.py", "test_continuation_v1.py"):
            expected = ((PREVIOUS / "independent_oracle" / name).read_text()
                        .replace("evidence/legacy_migration_v2/", "evidence/certified_transition_v2/")
                        .replace("nabt.legacy-migration.", "nabt.certified-transition-v2."))
            if name == "test_continuation_v1.py":
                expected = (expected.replace(
                    "evidence/interface_migration_v1/independent_oracle/runner_freeze_v5.json",
                    "evidence/legacy_migration_v2/independent_oracle/runner_freeze_v1.json")
                    .replace("0f7ae3bf2cab565b2976aa9b0cca39dc87a452f965dba7987ab95525ce890613",
                             PREVIOUS_PINS["independent_oracle/runner_freeze_v1.json"])
                    .replace("'/legacy_migration_v2/independent_oracle/review_'",
                             "'/certified_transition_v2/independent_oracle/review_'"))
            self.assertEqual((CURRENT / "independent_oracle" / name).read_text(), expected)

    def test_current_runner_identity_checks_all_declared_dependencies(self):
        path = CURRENT / "independent_oracle/run_oracle_v1.py"
        spec = importlib.util.spec_from_file_location("current_six_noun_freeze_runner", path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        checked = runner.check_runner_freeze(path.with_name("runner_freeze_v1.json"))
        paths = {row["path"] for row in checked["files"]}
        for name in ("tools/linguistic_truth/six_noun.py", "formal/Nabt/SixNounAcquisition.lean",
                     "formal/SixNounAcquisitionMain.lean",
                     "evidence/six_noun_acquisition_v1/source_review.json",
                     "evidence/six_noun_acquisition_v1/reference_cases.json"):
            self.assertIn(name, paths)


if __name__ == "__main__":
    unittest.main()
