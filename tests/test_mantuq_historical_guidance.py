"""Retain the original authoring contract while live agent instructions evolve."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import benchmark_mantuq_inference as benchmark


class HistoricalGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.gold_raw = (benchmark.ROOT / benchmark.GOLD_PATH).read_bytes()
        self.gold = json.loads(self.gold_raw)
        paths = [benchmark.GOLD_PATH, Path("AGENTS.md"),
                 Path(benchmark.HISTORICAL_GUIDANCE["resolved_path"])]
        paths.extend(Path(source["path"]) for source in self.gold["contract_inputs"]
                     if source["path"] != "AGENTS.md")
        for path in paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(benchmark.ROOT / path, target)

    def test_archive_has_original_gold_identity_and_gold_bytes_are_unchanged(self):
        historical = next(source for source in self.gold["contract_inputs"] if source["path"] == "AGENTS.md")
        archived = (self.root / benchmark.HISTORICAL_GUIDANCE["resolved_path"]).read_bytes()
        self.assertEqual(len(archived), 2076)
        self.assertEqual(sha256(archived).hexdigest(), historical["sha256"])
        self.assertEqual(sha256(self.gold_raw).hexdigest(), benchmark.GOLD_SHA256)
        self.assertEqual(benchmark.load_gold(self.root), self.gold)
        self.assertEqual((self.root / benchmark.GOLD_PATH).read_bytes(), self.gold_raw)

    def test_live_workflow_changes_do_not_replace_original_authoring_guidance(self):
        (self.root / "AGENTS.md").write_text("Current workflow additions evolve independently.\n")
        self.assertEqual(benchmark.load_gold(self.root), self.gold)
        records = benchmark.contract_input_bindings(self.gold, self.root)
        original = next(row for row in records if row["contract_path"] == "AGENTS.md")
        self.assertEqual(original["role"], "FROZEN_AUTHORING_GUIDANCE")
        self.assertEqual(original["origin_commit"], "f48012ec15aa30746c38c706512fc1403101df3d")
        self.assertNotEqual(original["sha256"], sha256((self.root / "AGENTS.md").read_bytes()).hexdigest())

    def test_missing_archive_has_no_fallback_even_when_live_guidance_matches_old_bytes(self):
        archived = self.root / benchmark.HISTORICAL_GUIDANCE["resolved_path"]
        (self.root / "AGENTS.md").write_bytes(archived.read_bytes())
        archived.unlink()
        with self.assertRaises(FileNotFoundError):
            benchmark.load_gold(self.root)

    def test_corrupt_archive_cannot_be_replaced_by_the_current_instruction_hash(self):
        archived = self.root / benchmark.HISTORICAL_GUIDANCE["resolved_path"]
        archived.write_bytes((self.root / "AGENTS.md").read_bytes() + b"\nchanged\n")
        with self.assertRaisesRegex(ValueError, "Frozen contract input changed: AGENTS.md"):
            benchmark.load_gold(self.root)
        altered = deepcopy(self.gold)
        next(row for row in altered["contract_inputs"] if row["path"] == "AGENTS.md")["sha256"] = sha256(archived.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "Frozen guidance identity differs"):
            benchmark.contract_input_bindings(altered, self.root)

    def test_every_semantic_and_source_contract_remains_current_byte_strict(self):
        for source in self.gold["contract_inputs"]:
            if source["path"] == "AGENTS.md":
                continue
            path = self.root / source["path"]
            original = path.read_bytes()
            path.write_bytes(original + b"\nchanged current contract\n")
            try:
                with self.subTest(source=source["path"]), self.assertRaisesRegex(ValueError, "Frozen contract input changed"):
                    benchmark.load_gold(self.root)
            finally:
                path.write_bytes(original)

    def test_edited_gold_still_fails_before_archival_resolution(self):
        path = self.root / benchmark.GOLD_PATH
        path.write_bytes(self.gold_raw.replace(b'"UNKNOWN"', b'"SUPPORTED"', 1))
        with self.assertRaisesRegex(ValueError, "Frozen inference gold changed"):
            benchmark.load_gold(self.root)

    def test_execution_metadata_separates_live_instructions_from_historical_contract(self):
        recorded = benchmark.execution_inputs()
        self.assertEqual(recorded["contract_input_policy"],
                         "ORIGINAL_FROZEN_GUIDANCE_AND_CURRENT_FROZEN_SEMANTIC_SOURCES")
        self.assertEqual(recorded["live_workflow_guidance"]["sha256"],
                         sha256((benchmark.ROOT / "AGENTS.md").read_bytes()).hexdigest())
        historical = next(row for row in recorded["contract_inputs"] if row["contract_path"] == "AGENTS.md")
        self.assertEqual(historical["resolved_path"], benchmark.HISTORICAL_GUIDANCE["resolved_path"])
        actual_files = {row["path"]: row["sha256"] for row in recorded["files"]}
        self.assertEqual(actual_files[historical["resolved_path"]], historical["sha256"])
        self.assertEqual(actual_files["AGENTS.md"], recorded["live_workflow_guidance"]["sha256"])
        self.assertFalse(recorded["hashes_grant_semantic_authority"])


if __name__ == "__main__":
    unittest.main()
