"""Fail-closed boundaries of the independently authored Arabic evaluation."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DATA = ROOT / "evidence/arabic_syntax/independent"
ENTRYPOINT = TOOLS / "arabic_syntax_evaluation.py"
CURRENT_FREEZE = ROOT / "evidence/arabic_completion_v5/code_freeze_v1.json"


class ArabicEvaluationBoundaryTests(unittest.TestCase):
    def _invoke(self, *args: str, optimized: bool = False) -> subprocess.CompletedProcess:
        command = [sys.executable]
        if optimized:
            command.append("-O")
        command.append(str(ENTRYPOINT))
        if "--code-freeze" not in args:
            command.extend(["--code-freeze", str(CURRENT_FREEZE)])
        command.extend(map(str, args))
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        return subprocess.run(command, cwd=ROOT, env=env, text=True,
                              capture_output=True, timeout=20, check=False)

    def test_public_replay_preserves_the_visible_failure_denominators(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            result = self._invoke("--output-dir", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((output / "receipt.json").read_text())
            self.assertTrue(receipt["gate"]["passed"])
            self.assertEqual(receipt["summary"]["standalone"]["complete_episodes"], 0)
            self.assertEqual(receipt["summary"]["standalone"]["episodes"], 40)
            self.assertEqual(receipt["summary"]["declared_scope"]["complete_episodes"], 8)
            self.assertEqual(receipt["summary"]["real_excerpts"]["semantic_read"], 0)
            self.assertEqual(receipt["summary"]["real_excerpts"]["total"], 8)

    def test_data_and_manifest_cannot_be_rewritten_to_self_authorize(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "data"
            shutil.copytree(DATA, data)
            path = data / "episodes.json"
            changed = json.loads(path.read_text())
            changed["cases"][0]["events"][0]["text"] = "معلومة مزورة."
            path.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n")
            manifest_path = data / "artifact_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            record = next(x for x in manifest["files"] if x["path"] == "episodes.json")
            record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            record["bytes"] = path.stat().st_size
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            output = Path(temp) / "run"
            result = self._invoke("--data-root", data, "--output-dir", output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("manifest checksum differs", result.stderr)
            self.assertFalse(output.exists())

    def test_incomplete_runtime_freeze_is_not_an_override(self):
        with tempfile.TemporaryDirectory() as temp:
            freeze = json.loads(CURRENT_FREEZE.read_text())
            freeze["files"] = freeze["files"][:1]
            canonical = json.dumps(freeze["files"], sort_keys=True, separators=(",", ":"))
            freeze["snapshot_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
            path = Path(temp) / "freeze.json"
            path.write_text(json.dumps(freeze))
            output = Path(temp) / "run"
            result = self._invoke("--code-freeze", path, "--output-dir", output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly the authoritative", result.stderr)
            self.assertFalse(output.exists())

    def test_history_and_existing_outputs_are_not_overwritten(self):
        history = DATA / "forbidden_new_run"
        self.assertFalse(history.exists())
        result = self._invoke("--output-dir", history)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source or published history", result.stderr)
        self.assertFalse(history.exists())
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            output.mkdir()
            sentinel = output / "receipt.json"
            sentinel.write_text("existing evidence\n")
            result = self._invoke("--output-dir", output)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), "existing evidence\n")

    def test_optimized_python_cannot_disable_independent_assertions(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            result = self._invoke("--output-dir", output, optimized=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without Python -O", result.stderr)
            self.assertFalse(output.exists())

    def test_all_defer_is_not_a_successful_regression(self):
        sys.path.insert(0, str(TOOLS))
        try:
            from arabic_syntax_evaluation import FIRST_SNAPSHOT, regression_gate
            reference = json.loads((DATA / "first_results.json").read_text())
            empty = copy.deepcopy(reference)
            for case in empty["episodes"]:
                case["complete_episode"] = False
            gate = regression_gate(empty, snapshot=FIRST_SNAPSHOT, reference=reference)
            self.assertFalse(gate["passed"])
            self.assertFalse(gate["previously_complete_cases_preserved"])
        finally:
            sys.path.pop(0)

    def test_independent_certificate_oracle_rejects_changed_evidence(self):
        sys.path.insert(0, str(TOOLS))
        try:
            from arabic_syntax_evaluation_helpers.oracle_helpers import independent_certificate
            source_case = next(x for x in json.loads((DATA / "scope_episodes.json").read_text())["cases"] if x["id"] == "s07")
            active = {x["source_id"]: x["text"] for x in source_case["events"] if x["op"] == "add"}
            manual = {x["source_text_sha256"]: x["expected"] for x in json.loads((DATA / "manual_oracle.json").read_text())["records"]}
            actual_case = next(x for x in json.loads((DATA / "first_results.json").read_text())["episodes"] if x["id"] == "s07")
            answer = next(x["result"] for x in actual_case["events"] if x["op"] == "query")
            certificate = answer["proofs"]["query"]
            self.assertTrue(independent_certificate(certificate, active, "eval_s07", manual))
            forged = copy.deepcopy(certificate)
            forged["steps"][-1]["premises"] = [len(forged["steps"]) + 1]
            with self.assertRaises(AssertionError):
                independent_certificate(forged, active, "eval_s07", manual)
            forged = copy.deepcopy(certificate)
            forged["steps"][0]["clause"]["source_sha256"] = "0" * 64
            with self.assertRaises(AssertionError):
                independent_certificate(forged, active, "eval_s07", manual)
        finally:
            sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()
