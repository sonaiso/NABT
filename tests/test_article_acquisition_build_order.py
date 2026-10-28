"""Observe the additive v2 Make ordering with cheap command fixtures."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
# Reuse the existing command recorder, without running its test suite. It fakes
# tool processes only: these checks do not claim native compilation correctness.
RUNNER = runpy.run_path(str(ROOT / "tests/test_aligned_acquisition_build_order.py"))["RUNNER"]


class ArticleBuildOrderTests(unittest.TestCase):
    def run_make(self, goal, fail=False):
        with tempfile.TemporaryDirectory(prefix="article-build-order-") as directory:
            root = Path(directory)
            for name in ("Makefile", "tools/aligned_acquisition.mk", "tools/article_acquisition.mk",
                         "integrations/current_proof_references.mk", "integrations/grammar_catalog.mk",
                         "integrations/mantuq_inference.mk", "integrations/linguistic_truth.mk",
                         "integrations/licensed_inference.mk"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, path)
            (root / "formal").mkdir()
            runner = root / "runner.py"
            body = RUNNER.replace('if "alignedAcquisition" in targets and',
                                  'if "alignedAcquisitionV2" in targets and')
            runner.write_text(body)
            log = root / "commands.jsonl"
            env = {k: v for k, v in os.environ.items() if k not in
                   {"MAKEFLAGS", "MFLAGS", "MAKEFILES", "NABT_ORDER_FAIL_NATIVE"}}
            env["NABT_ORDER_LOG"] = str(log)
            if fail:
                env["NABT_ORDER_FAIL_NATIVE"] = "1"
            result = subprocess.run(["make", "--no-print-directory", "-j8", "-f",
                "tools/article_acquisition.mk", goal, "ARTICLE_PHASE=exposed",
                "PYTHON=" + sys.executable + " " + str(runner) + " python",
                "LAKE=" + sys.executable + " " + str(runner) + " lake",
                "EVIDENCE_DIR=artifacts/local/order"], cwd=root, env=env,
                capture_output=True, text=True, timeout=30)
            events = [json.loads(line) for line in log.read_text().splitlines()]
            return result, events

    def test_all_measured_builds_and_v1_replay_precede_v2_freeze(self):
        for goal in ("article-acquisition-evaluation", "check"):
            with self.subTest(goal=goal):
                result, events = self.run_make(goal)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Circular", result.stderr)
                def step(kind, fragment):
                    return next(i for i, row in enumerate(events)
                                if row[0] == kind and fragment in row)
                v1_replayed = step("end", "tools/evaluate_aligned_acquisition.py")
                v2_build = events.index(["end", "lake", "build", "alignedAcquisitionV2"])
                source_checked = step("end", "tools.check_article_source_links")
                frozen = step("start", "tools/freeze_article_acquisition.py")
                evaluated = step("start", "tools/evaluate_article_acquisition.py")
                self.assertLess(v1_replayed, v2_build)
                self.assertLess(v2_build, source_checked)
                self.assertLess(source_checked, frozen)
                self.assertLess(frozen, evaluated)
                native_ends = [i for i, row in enumerate(events)
                               if row[:3] == ["end", "lake", "build"] and
                               any(name in row for name in
                                   ("alignedAcquisition", "licensedInference", "alignedAcquisitionV2"))]
                self.assertTrue(native_ends)
                self.assertLess(max(native_ends), frozen)

    def test_failed_v2_native_build_never_starts_its_freezer(self):
        result, events = self.run_make("article-acquisition-evaluation", fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("tools/freeze_article_acquisition.py" in row or
                             "tools/evaluate_article_acquisition.py" in row for row in events))


if __name__ == "__main__":
    unittest.main()
