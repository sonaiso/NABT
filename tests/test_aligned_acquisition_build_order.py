"""Execute the real additive Make graph with cheap, recorded build commands.

This checks declared ordering, not native compilation or global isolation.
The historical recipes remain intact; their Python/Lake processes are replaced
only inside a temporary checkout so parallel check can be exercised cheaply.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = r'''
import json
import os
from pathlib import Path
import sys
import time

kind, *args = sys.argv[1:]
if kind == "python" and args[:1] == ["-c"]:
    print("fixture-run")
    raise SystemExit(0)

def record(event):
    with open(os.environ["NABT_ORDER_LOG"], "a") as output:
        output.write(json.dumps(event) + "\n")

event = [kind, *args]
record(["start", *event])
if kind == "lake" and args[:1] == ["build"]:
    # Give an incorrectly independent freezer a chance to overtake the build.
    time.sleep(0.05)
    targets = args[1:]
    if "alignedAcquisition" in targets and os.environ.get("NABT_ORDER_FAIL_NATIVE"):
        raise SystemExit(7)
    for target in targets:
        path = Path(".lake/build/bin") / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(0o755)
record(["end", *event])
'''


class AlignedAcquisitionBuildOrderTests(unittest.TestCase):
    def run_make(self, goal, *, fail_native=False):
        with tempfile.TemporaryDirectory(prefix="nabt-build-order-") as directory:
            root = Path(directory)
            for name in ("Makefile", "tools/aligned_acquisition.mk",
                         "integrations/current_proof_references.mk", "integrations/grammar_catalog.mk",
                         "integrations/mantuq_inference.mk", "integrations/linguistic_truth.mk",
                         "integrations/licensed_inference.mk"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            (root / "formal").mkdir()
            runner = root / "runner.py"
            runner.write_text(RUNNER)
            log = root / "commands.jsonl"
            env = {key: value for key, value in os.environ.items()
                   if key not in {"MAKEFLAGS", "MFLAGS", "MAKEFILES", "NABT_ORDER_FAIL_NATIVE"}}
            env["NABT_ORDER_LOG"] = str(log)
            if fail_native:
                env["NABT_ORDER_FAIL_NATIVE"] = "1"
            result = subprocess.run(["make", "--no-print-directory", "-j8", "-f",
                "tools/aligned_acquisition.mk", goal,
                "PYTHON=" + sys.executable + " " + str(runner) + " python",
                "LAKE=" + sys.executable + " " + str(runner) + " lake",
                "EVIDENCE_DIR=artifacts/local/order"], cwd=root, env=env,
                capture_output=True, text=True, timeout=30)
            events = [json.loads(line) for line in log.read_text().splitlines()]
            return result, events

    def test_evaluation_waits_for_native_conformance_and_integration(self):
        for goal in ("aligned-acquisition-evaluation", "check"):
            with self.subTest(goal=goal):
                result, events = self.run_make(goal)
                self.assertEqual(result.returncode, 0, result.stderr)
                formal = events.index(["end", "lake", "build"])
                ready = events.index(["end", "lake", "build", "alignedAcquisition", "licensedInference"])
                conform = next(i for i, event in enumerate(events)
                               if event[:2] == ["end", "python"] and
                               "test_current_proof_references.py" in event)
                inference = events.index(["end", "lake", "build", "licensedInference"])
                integrated = next(i for i, event in enumerate(events)
                                  if event[:3] == ["end", "python", "tools/check_acquired_inference.py"])
                frozen = next(i for i, event in enumerate(events)
                              if event[:3] == ["start", "python", "tools/freeze_aligned_acquisition.py"])
                evaluated = next(i for i, event in enumerate(events)
                                 if event[:3] == ["start", "python", "tools/evaluate_aligned_acquisition.py"])
                self.assertLess(formal, ready)
                self.assertLess(ready, conform)
                self.assertLess(conform, inference)
                self.assertLess(inference, integrated)
                self.assertLess(integrated, frozen)
                self.assertLess(frozen, evaluated)
                self.assertEqual(sum("tools/freeze_aligned_acquisition.py" in event
                                     for event in events if event[0] == "start"), 1)

    def test_failed_native_readiness_does_not_start_freezer(self):
        result, events = self.run_make("aligned-acquisition-evaluation", fail_native=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("tools/freeze_aligned_acquisition.py" in event or
                             "tools/evaluate_aligned_acquisition.py" in event for event in events))

    def test_direct_inference_gate_remains_acyclic_and_waits_for_conformance(self):
        result, events = self.run_make("licensed-inference")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Circular", result.stderr)
        conform = next(i for i, event in enumerate(events)
                       if event[:2] == ["end", "python"] and
                       "test_current_proof_references.py" in event)
        inference = events.index(["start", "lake", "build", "licensedInference"])
        self.assertLess(conform, inference)
        self.assertFalse(any("tools/freeze_aligned_acquisition.py" in event for event in events))


if __name__ == "__main__":
    unittest.main()
