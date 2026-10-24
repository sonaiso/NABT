"""Release-profile and answer-contract checks; no wheel is built here."""

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse_answer


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("coverage_package_verifier", ROOT / "tools/verify_construction_package.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class ArabicCoveragePackageVerifierTests(unittest.TestCase):
    def test_new_profile_matches_frozen_archive_and_supplementary_sources(self):
        for version in (1, 2):
            with self.subTest(freeze_version=version):
                self._assert_archive_version(version)

    def _assert_archive_version(self, version):
        path = ROOT / f"evidence/arabic_coverage/code_freeze_v{version}.json"
        raw = path.read_bytes()
        freeze = json.loads(raw)
        pin = VERIFIER.CODE_FREEZE_PINS[sha256(raw).hexdigest()]
        profile = VERIFIER.RELEASE_PROFILES[pin["profile"]]
        self.assertEqual((pin["version"], pin["source_file_count"]), ("0.16.0a1", 77))
        self.assertEqual(profile["language_id"], "nabt.arabic-discourse-frames.v5")
        self.assertEqual(profile["reader_version"], "nabt.discourse-reader.v5")
        archive_path = path.with_name(freeze["archive_filename"])
        self.assertEqual(sha256(archive_path.read_bytes()).hexdigest(), pin["archive_sha256"])
        with tarfile.open(archive_path, "r:gz") as archive:
            self.assertEqual(len(archive.getmembers()), 77)
            for path, key in (
                    ("src/nabt/data/construction_evidence.json", "table_sha256"),
                    ("src/nabt/data/source_evidence/construction_policy.json", "policy_sha256"),
                    ("src/nabt/data/source_evidence/discourse_policy.json", "discourse_policy_sha256"),
                    ("src/nabt/data/source_evidence/construction_supplementary_sources_v1.json", "supplementary_registry_sha256"),
                    ("src/nabt/data/source_evidence/sabban.txt", "supplementary_source_sha256")):
                with self.subTest(path=path):
                    self.assertEqual(sha256(archive.extractfile(path).read()).hexdigest(), profile[key])
        for path, record in profile["package_documents"].items():
            data = (ROOT / "src" / path).read_bytes()
            self.assertEqual((len(data), sha256(data).hexdigest()), (record["bytes"], record["sha256"]))
        # The historical document pin remains separate from this new profile.
        self.assertEqual(VERIFIER.PACKAGE_DOCUMENTS["nabt/data/source_evidence/LICENSE-DATA.md"]["sha256"],
                         "ac2d62edd753190b9c0f8bd254beb245f3a199c5774a917c814c69e238360aae")

    def test_consensus_smoke_does_not_rewrite_historical_rejection(self):
        historical = VERIFIER.RELEASE_PROFILES["construction_v3"]
        current = VERIFIER.RELEASE_PROFILES["arabic_coverage_v1"]
        self.assertEqual(VERIFIER.query_smoke_names(historical), VERIFIER.QUERY_AGREEMENT_NAMES)
        names = VERIFIER.query_smoke_names(current)
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
        args = ("fixture", text, question, answer, VERIFIER.RELEASE_PROFILES["arabic_coverage_v1"],
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
