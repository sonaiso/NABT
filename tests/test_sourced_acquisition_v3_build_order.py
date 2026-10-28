"""Exercise actual Make dependencies with recorded, non-native processes."""
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
RUNNER = runpy.run_path(str(ROOT / "tests/test_aligned_acquisition_build_order.py"))["RUNNER"]


# Model the real check_linguistic_truth.py --lake subprocess, which the generic
# command recorder otherwise hides. Only temporary fixture binaries are made.
LINGUISTIC_BUILD = r"""
if kind == "python" and args[:1] == ["tools/check_linguistic_truth.py"]:
    subprocess.run([sys.executable, str(Path(__file__).resolve()), "lake", "build", "linguisticTruth"],
                   cwd="formal", check=True)
"""
LINGUISTIC_DELAY = r"""
    if targets == ["linguisticTruth"]:
        if os.environ.get("NABT_ORDER_DELAY_LINGUISTIC"):
            # An unordered v3 freeze releases the competing build immediately.
            # With the dependency fixed, only the bounded timeout releases it.
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                events = Path(os.environ["NABT_ORDER_LOG"]).read_text().splitlines()
                if any('"start"' in row and '"tools/freeze_sourced_acquisition_v3.py"' in row
                       for row in events):
                    break
                time.sleep(0.01)
        if os.environ.get("NABT_ORDER_FAIL_LINGUISTIC"):
            record(["failed", *event])
            raise SystemExit(9)
"""


class SourcedBuildOrder(unittest.TestCase):
    def run_make(self, target, fail=False, *, delay_linguistic=False, fail_linguistic=False):
        with tempfile.TemporaryDirectory(prefix="sourced-v3-order-") as directory:
            root = Path(directory)
            for name in ("Makefile", "tools/aligned_acquisition.mk", "tools/article_acquisition.mk",
                         "tools/sourced_acquisition_v3.mk", "integrations/current_proof_references.mk",
                         "integrations/grammar_catalog.mk", "integrations/mantuq_inference.mk",
                         "integrations/linguistic_truth.mk", "integrations/licensed_inference.mk"):
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, path)
            (root / "formal").mkdir()
            runner = root / "runner.py"
            body = RUNNER.replace('if "alignedAcquisition" in targets and',
                                  'if "connectedAcquisitionV3" in targets and')
            body = body.replace("import sys\n", "import sys\nimport subprocess\n")
            body = body.replace('    targets = args[1:]\n',
                                '    targets = args[1:]\n' + LINGUISTIC_DELAY)
            body = body.replace('record(["end", *event])',
                                LINGUISTIC_BUILD + '\nrecord(["end", *event])')
            runner.write_text(body)
            log = root / "events.jsonl"
            env = {k: v for k, v in os.environ.items() if k not in
                   {"MAKEFLAGS", "MFLAGS", "MAKEFILES", "NABT_ORDER_FAIL_NATIVE",
                    "NABT_ORDER_DELAY_LINGUISTIC", "NABT_ORDER_FAIL_LINGUISTIC"}}
            env["NABT_ORDER_LOG"] = str(log)
            if fail:
                env["NABT_ORDER_FAIL_NATIVE"] = "1"
            if delay_linguistic:
                env["NABT_ORDER_DELAY_LINGUISTIC"] = "1"
            if fail_linguistic:
                env["NABT_ORDER_FAIL_LINGUISTIC"] = "1"
            result = subprocess.run(["make", "--no-print-directory", "-j8", "-f",
                "tools/sourced_acquisition_v3.mk", target,
                "PYTHON=" + sys.executable + " " + str(runner) + " python",
                "LAKE=" + sys.executable + " " + str(runner) + " lake",
                "EVIDENCE_DIR=artifacts/local/order"], cwd=root, env=env,
                capture_output=True, text=True, timeout=30)
            return result, [json.loads(line) for line in log.read_text().splitlines()]

    def test_v3_waits_for_historical_replays_native_checks_and_links(self):
        for target in ("sourced-acquisition-evaluation", "check"):
            with self.subTest(target=target):
                result, rows = self.run_make(target)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Circular", result.stderr)
                def event(kind, token):
                    return next(i for i, row in enumerate(rows) if row[0] == kind and token in row)
                v2 = event("end", "tools/evaluate_article_acquisition.py")
                native = rows.index(["end", "lake", "build", "connectedAcquisitionV3", "acquiredSyntaxV3", "linguisticTruth"])
                linked = event("end", "tools.check_sourced_acquisition_links")
                frozen = event("start", "tools/freeze_sourced_acquisition_v3.py")
                evaluated = event("start", "tools/evaluate_sourced_acquisition_v3.py")
                self.assertLess(v2, native); self.assertLess(native, linked)
                self.assertLess(linked, frozen); self.assertLess(frozen, evaluated)
                self.assertLess(event("end", "test_acquired_person_nominal_v3.py"), frozen)
                self.assertEqual(sum(row[0] == "start" and "tools/freeze_sourced_acquisition_v3.py" in row for row in rows), 1)

    def test_v3_native_failure_never_freezes_or_scores(self):
        result, rows = self.run_make("sourced-acquisition-evaluation", fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("tools/freeze_sourced_acquisition_v3.py" in row or
                             "tools/evaluate_sourced_acquisition_v3.py" in row for row in rows))


    def test_parallel_linguistic_native_rebuild_finishes_before_v3(self):
        result, rows = self.run_make("check", delay_linguistic=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        linguistic = rows.index(["end", "lake", "build", "linguisticTruth"])
        native = rows.index(["start", "lake", "build", "connectedAcquisitionV3", "acquiredSyntaxV3", "linguisticTruth"])
        frozen = next(i for i, row in enumerate(rows) if row[0] == "start" and
                      "tools/freeze_sourced_acquisition_v3.py" in row)
        self.assertLess(linguistic, native)
        self.assertLess(linguistic, frozen)

    def test_direct_v3_requires_successful_linguistic_native_dependency(self):
        result, rows = self.run_make("sourced-acquisition-evaluation", fail_linguistic=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(["failed", "lake", "build", "linguisticTruth"], rows)
        self.assertFalse(any("tools/freeze_sourced_acquisition_v3.py" in row or
                             "tools/evaluate_sourced_acquisition_v3.py" in row for row in rows))

    def test_parallel_linguistic_native_failure_blocks_v3_freeze(self):
        result, rows = self.run_make("check", delay_linguistic=True, fail_linguistic=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(["failed", "lake", "build", "linguisticTruth"], rows)
        self.assertFalse(any("tools/freeze_sourced_acquisition_v3.py" in row or
                             "tools/evaluate_sourced_acquisition_v3.py" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
