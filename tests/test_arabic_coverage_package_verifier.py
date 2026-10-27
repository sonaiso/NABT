"""Release-profile and answer-contract checks; no wheel is built here."""

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest
from zipfile import ZipFile

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse_answer


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("coverage_package_verifier", ROOT / "tools/verify_construction_package.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class ArabicCoveragePackageVerifierTests(unittest.TestCase):
    def test_historical_coverage_profiles_match_their_own_archived_bytes(self):
        for version in (1, 2):
            with self.subTest(freeze_version=version):
                profile = self._assert_archive_profile(
                    ROOT / f"evidence/arabic_coverage/code_freeze_v{version}.json",
                    "0.16.0a1", 77, "v5", 23)
                # Markdown is outside the runtime freeze. Inspect the captured
                # 0.16 package documents, not the changed live 0.17 checkout.
                package_path = ROOT / "evidence/arabic_coverage/package_validation_v2.zip"
                self.assertEqual(sha256(package_path.read_bytes()).hexdigest(),
                    "28ef35c07b5c015aab58433178a6a126b901df5bba5ec23feb0041dce4aac8e1")
                with ZipFile(package_path) as package:
                    for name, record in profile["package_documents"].items():
                        data = package.read("inputs/" + name)
                        self.assertEqual((len(data), sha256(data).hexdigest()),
                                         (record["bytes"], record["sha256"]))

    def _assert_archive_profile(self, path, package_version, source_count, language_version, rule_count):
        raw = path.read_bytes()
        freeze = json.loads(raw)
        pin = VERIFIER.CODE_FREEZE_PINS[sha256(raw).hexdigest()]
        profile = VERIFIER.RELEASE_PROFILES[pin["profile"]]
        self.assertEqual((pin["version"], pin["source_file_count"]), (package_version, source_count))
        self.assertEqual(profile["language_id"], "nabt.arabic-discourse-frames." + language_version)
        self.assertEqual(profile["reader_version"], "nabt.discourse-reader." + language_version)
        self.assertEqual(freeze["snapshot_sha256"], pin["snapshot_sha256"])
        self.assertEqual(sha256(json.dumps(freeze["files"], sort_keys=True,
                                          separators=(",", ":")).encode()).hexdigest(), pin["snapshot_sha256"])
        rows = {row["path"]: row for row in freeze["files"]}
        self.assertEqual(len(rows), source_count)
        archive_path = path.with_name(freeze["archive_filename"])
        self.assertEqual(sha256(archive_path.read_bytes()).hexdigest(), pin["archive_sha256"])
        with tarfile.open(archive_path, "r:gz") as archive:
            self.assertEqual(len(archive.getmembers()), source_count)
            self.assertEqual({member.name for member in archive.getmembers()}, set(rows))
            for member in archive.getmembers():
                self.assertTrue(member.isfile())
                data = archive.extractfile(member).read()
                self.assertEqual((len(data), sha256(data).hexdigest()),
                                 (rows[member.name]["bytes"], rows[member.name]["sha256"]))
            for name, key in (
                    ("src/nabt/data/construction_evidence.json", "table_sha256"),
                    ("src/nabt/data/source_evidence/construction_policy.json", "policy_sha256"),
                    ("src/nabt/data/source_evidence/discourse_policy.json", "discourse_policy_sha256")):
                with self.subTest(path=name):
                    self.assertEqual(sha256(archive.extractfile(name).read()).hexdigest(), profile[key])
            for name, expected in VERIFIER.supplementary_file_hashes(profile).items():
                with self.subTest(path=name):
                    self.assertEqual(sha256(archive.extractfile("src/" + name).read()).hexdigest(), expected)
            policy = json.loads(archive.extractfile("src/nabt/data/source_evidence/construction_policy.json").read())
            self.assertEqual(policy["policy_id"], profile["policy_id"])
            self.assertEqual(len(policy["passages"]), rule_count)
            self.assertEqual({row["rule"] for row in policy["passages"]}, profile["rules"])
            package_rows = {name.removeprefix("src/"): row for name, row in rows.items()
                            if name.startswith("src/")}
            self.assertLessEqual(VERIFIER.REQUIRED_PACKAGE_FILES | profile["extra_package_files"], set(package_rows))
            VERIFIER.inspect_supplementary_files(profile, package_rows)
        return profile

    def test_completion_profile_matches_80_file_freeze_and_new_source_inventory(self):
        freeze_path = ROOT / "evidence/arabic_completion_v3/code_freeze_v2.json"
        profile = self._assert_archive_profile(freeze_path, "0.17.0a1", 80, "v6", 25)
        pin = VERIFIER.CODE_FREEZE_PINS[sha256(freeze_path.read_bytes()).hexdigest()]
        self.assertEqual((pin["selection"], pin["profile"]), ("arabic_completion_v3_review2", "arabic_completion_v3"))
        self.assertEqual(VERIFIER.DEFAULT_FREEZE, "evidence/legacy_migration_v2/code_freeze_v1.json")
        self.assertEqual(profile["supplementary_source_ids"], ["mukhtar_sihah", "sabban"])
        self.assertEqual(set(VERIFIER.supplementary_file_hashes(profile)), {
            "nabt/data/source_evidence/construction_supplementary_sources_v2.json",
            "nabt/data/source_evidence/sabban.txt", "nabt/data/source_evidence/mukhtar_sihah.txt"})
        for path, record in profile["package_documents"].items():
            data = (ROOT / "src" / path).read_bytes()
            self.assertEqual((len(data), sha256(data).hexdigest()), (record["bytes"], record["sha256"]))
        # The historical document pin remains separate from this new profile.
        self.assertEqual(VERIFIER.PACKAGE_DOCUMENTS["nabt/data/source_evidence/LICENSE-DATA.md"]["sha256"],
                         "ac2d62edd753190b9c0f8bd254beb245f3a199c5774a917c814c69e238360aae")

    def test_pre_correction_completion_profile_still_matches_its_own_archive(self):
        path = ROOT / "evidence/arabic_completion_v3/code_freeze_v1.json"
        self._assert_archive_profile(path, "0.17.0a1", 80, "v6", 25)
        pin = VERIFIER.CODE_FREEZE_PINS[sha256(path.read_bytes()).hexdigest()]
        self.assertEqual(pin["selection"], "arabic_completion_v3")

    def test_missing_or_changed_current_supplementary_source_cannot_pass(self):
        profile = VERIFIER.RELEASE_PROFILES["arabic_completion_v3"]
        freeze = json.loads((ROOT / VERIFIER.DEFAULT_FREEZE).read_text())
        rows = {row["path"].removeprefix("src/"): row for row in freeze["files"]
                if row["path"].startswith("src/")}
        VERIFIER.inspect_supplementary_files(profile, rows)
        for name in ("nabt/data/source_evidence/construction_supplementary_sources_v2.json",
                     "nabt/data/source_evidence/sabban.txt", "nabt/data/source_evidence/mukhtar_sihah.txt"):
            for change in ("remove", "different_bytes"):
                with self.subTest(path=name, change=change):
                    altered = deepcopy(rows)
                    if change == "remove":
                        altered.pop(name)
                    else:
                        altered[name]["sha256"] = "0" * 64
                    with self.assertRaisesRegex(ValueError, "supplementary"):
                        VERIFIER.inspect_supplementary_files(profile, altered)
        replay = {"supplementary_registry_sha256": profile["supplementary_registry_sha256"],
                  "supplementary_source_ids": ["mukhtar_sihah", "sabban"]}
        VERIFIER.inspect_supplementary_replay(profile, replay)
        for altered in ({**replay, "supplementary_source_ids": ["sabban"]},
                        {**replay, "supplementary_source_ids": ["mukhtar_sihah", "sabban", "unregistered"]},
                        {**replay, "supplementary_registry_sha256":
                            VERIFIER.RELEASE_PROFILES["arabic_coverage_v1"]["supplementary_registry_sha256"]}):
            with self.assertRaisesRegex(ValueError, "registry did not replay"):
                VERIFIER.inspect_supplementary_replay(profile, altered)

    def test_consensus_smoke_does_not_rewrite_historical_rejection(self):
        historical = VERIFIER.RELEASE_PROFILES["construction_v3"]
        self.assertEqual(VERIFIER.query_smoke_names(historical), VERIFIER.QUERY_AGREEMENT_NAMES)
        for key in ("arabic_coverage_v1", "arabic_completion_v3"):
            names = VERIFIER.query_smoke_names(VERIFIER.RELEASE_PROFILES[key])
            self.assertNotIn("reject-ambiguous-person-query", names)
            self.assertIn("agree-ambiguous-person-query", names)
            self.assertIn("verify-consensus-answer", names)
            self.assertEqual(len(names), len(set(names)))

    def test_consensus_inspection_replays_and_rejects_erased_or_disagreeing_readings(self):
        raw = VERIFIER.query_source()
        model = learn_qac_lexicon(raw)
        context = VERIFIER.QUERY_CONTEXT
        text, question = "زيدٌ حكيمٌ. هندٌ حكيمةٌ.", "من صبورٌ؟"
        report = read_discourse(text, lexical_model=model, context=context)
        answer = ask_discourse(text, question, lexical_model=model, context=context)
        args = ("fixture", text, question, answer, VERIFIER.RELEASE_PROFILES["arabic_completion_v4"],
                sha256(raw).hexdigest(), report["context"]["sha256"])
        VERIFIER.inspect_consensus_unknown_answer(*args)
        self.assertTrue(verify_discourse_answer(answer, text=text, question=question,
                                                lexical_model=model, context=context)["valid"])
        changes = []
        changed = deepcopy(answer)
        changed["question_interpretations"] = [i for i in changed["question_interpretations"]
            if i["query"]["args"][0]["gender"] == "masculine"]
        changes.append(changed)
        changed = deepcopy(answer)
        changed["question_interpretations"][0]["status"] = "SUPPORTED"
        changes.append(changed)
        changed = deepcopy(answer)
        changed["proofs"] = [{"unsupported": True}]
        changes.append(changed)
        for changed in changes:
            with self.subTest(changed=changed["status"]):
                with self.assertRaises(ValueError):
                    VERIFIER.inspect_consensus_unknown_answer(*args[:3], changed, *args[4:])
                self.assertFalse(verify_discourse_answer(changed, text=text, question=question,
                                                         lexical_model=model, context=context)["valid"])


if __name__ == "__main__":
    unittest.main()
