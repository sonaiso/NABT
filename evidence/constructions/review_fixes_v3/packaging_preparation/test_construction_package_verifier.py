"""Release-check boundaries, without building a wheel or evaluating language."""

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tarfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "construction_package_verifier", ROOT / "tools/verify_construction_package.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class ConstructionPackageVerifierTests(unittest.TestCase):
    def test_historical_and_current_profiles_match_their_archived_bytes(self):
        for version, package_version, language_version in (
                (1, "0.14.0a1", "v2"), (2, "0.14.0a1", "v2"), (3, "0.14.0a2", "v3")):
            path = ROOT / f"evidence/constructions/code_freeze_v{version}.json"
            raw = path.read_bytes()
            freeze = json.loads(raw)
            pin = VERIFIER.CODE_FREEZE_PINS[sha256(raw).hexdigest()]
            profile = VERIFIER.RELEASE_PROFILES[pin["profile"]]
            with self.subTest(version=version):
                self.assertEqual(pin["version"], package_version)
                self.assertEqual(profile["language_id"], "nabt.arabic-discourse-frames." + language_version)
                self.assertEqual(profile["reader_version"], "nabt.discourse-reader." + language_version)
                archive_path = path.with_name(freeze["archive_filename"])
                self.assertEqual(sha256(archive_path.read_bytes()).hexdigest(), pin["archive_sha256"])
                with tarfile.open(archive_path, "r:gz") as archive:
                    self.assertEqual(len(archive.getmembers()), pin["source_file_count"])
                    project = tomllib.loads(archive.extractfile("pyproject.toml").read().decode())
                    table_raw = archive.extractfile("src/nabt/data/construction_evidence.json").read()
                    policy_raw = archive.extractfile("src/nabt/data/source_evidence/construction_policy.json").read()
                self.assertEqual(project["project"]["version"], package_version)
                self.assertEqual(sha256(table_raw).hexdigest(), profile["table_sha256"])
                self.assertEqual(sha256(policy_raw).hexdigest(), profile["policy_sha256"])
                table = json.loads(table_raw)
                self.assertEqual(table["law_id"], profile["law_id"])
                self.assertEqual(table["source_policy_id"], profile["policy_id"])
                self.assertEqual({k: len(v) for k, v in table.items() if k.endswith("_rows")},
                                 profile["table_rows"])

    @staticmethod
    def deferred_report():
        profile = VERIFIER.RELEASE_PROFILES["construction_v2"]
        text = "كَانُ زيدٌ حكيمًا."
        source_hash = sha256(b"authored source").hexdigest()
        report = {
            "source_text": text, "source_sha256": sha256(text.encode()).hexdigest(),
            "lexical_model": {"source": {"sha256": source_hash}},
            "language_id": profile["language_id"], "reader_version": profile["reader_version"],
            "construction_law_id": profile["law_id"],
            "construction_law_sha256": profile["table_sha256"],
            "construction_policy_sha256": profile["policy_sha256"],
            "status": "DEFER", "claims": [],
            "clauses": [{"analyses": [{"assertion_allowed": False,
                "claims": [{"candidate": "preserved without assertion authority"}],
                "assignments": [{"activated": False, "actual_role": None,
                                  "inflected_case": None, "local_case": None}]}]}],
        }
        return text, report, profile, source_hash

    def test_deferred_candidates_are_allowed_without_actual_authority(self):
        VERIFIER.inspect_deferred_report("fixture", *self.deferred_report())

    def test_defer_label_cannot_hide_an_actual_assignment(self):
        text, report, profile, source_hash = self.deferred_report()
        for field, value in (("activated", True), ("actual_role", "kana_subject"),
                             ("inflected_case", "raf"), ("local_case", "raf")):
            with self.subTest(field=field):
                altered = deepcopy(report)
                altered["clauses"][0]["analyses"][0]["assignments"][0][field] = value
                with self.assertRaisesRegex(ValueError, "actual assignment"):
                    VERIFIER.inspect_deferred_report("fixture", text, altered, profile, source_hash)
        for field, value in (("claims", [{"unexpected": "assertion"}]),
                             ("source_sha256", "0" * 64)):
            with self.subTest(field=field):
                altered = deepcopy(report)
                altered[field] = value
                with self.assertRaises(ValueError):
                    VERIFIER.inspect_deferred_report("fixture", text, altered, profile, source_hash)
        altered = deepcopy(report)
        altered["clauses"][0]["analyses"][0]["assertion_allowed"] = True
        with self.assertRaisesRegex(ValueError, "actual assignment"):
            VERIFIER.inspect_deferred_report("fixture", text, altered, profile, source_hash)

    def test_defer_answer_cannot_hide_proofs_or_bindings(self):
        text, report, _, source_hash = self.deferred_report()
        question = "متى كَانُ زيدٌ حكيمًا؟"
        answer = {"source_text": text, "source_sha256": report["source_sha256"],
                  "question_text": question, "question_sha256": sha256(question.encode()).hexdigest(),
                  "lexical_model": report["lexical_model"], "status": "DEFER",
                  "proofs": [], "counterproofs": [], "bindings": []}
        VERIFIER.inspect_deferred_answer("fixture", text, question, answer, source_hash)
        for field in ("proofs", "counterproofs", "bindings"):
            with self.subTest(field=field):
                altered = deepcopy(answer)
                altered[field] = [{"unexpected": "authority"}]
                with self.assertRaisesRegex(ValueError, "answer authority"):
                    VERIFIER.inspect_deferred_answer("fixture", text, question, altered, source_hash)
        altered = deepcopy(answer)
        altered["question_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "identity"):
            VERIFIER.inspect_deferred_answer("fixture", text, question, altered, source_hash)


if __name__ == "__main__":
    unittest.main()
