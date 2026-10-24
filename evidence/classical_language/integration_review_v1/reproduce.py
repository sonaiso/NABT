#!/usr/bin/env python3
"""Re-run the focused recursive adapter tests after the integration-only fix.

Uses the existing compiled Lean probe without building Lean or running the
global gate. Historical evidence and runtime files must remain unchanged.
"""

from datetime import datetime, timezone
import argparse
import difflib
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
REVIEW = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.text_evaluation.integrity import verify_code_freeze


def record(path):
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
            "sha256": sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    paths = [output / "focused_tests_after.log", output / "test_change.patch", output / "receipt_after.json"]
    if args.output_dir.is_symlink() or any(path.exists() or path.is_symlink() for path in paths):
        raise ValueError("Choose new output paths; evidence is never overwritten")
    before = json.loads((REVIEW / "receipt_before.json").read_bytes())
    for entry in before["preserved_files"]:
        observed = record(ROOT / entry["preserved_path"])
        if (observed["bytes"], observed["sha256"]) != (entry["bytes"], entry["sha256"]):
            raise ValueError("Preserved pre-fix evidence changed")
    for entry in before["unchanged_inspected_inputs"]:
        if record(ROOT / entry["path"]) != entry:
            raise ValueError("An input outside the authorized test change differs: " + entry["path"])
    current_freeze = ROOT / "evidence/rational_inquiry/code_freeze_v2.json"
    frozen_before = verify_code_freeze(current_freeze, ROOT)
    probe = ROOT / "formal/.lake/build/bin/recursiveBridgeProbe"
    if not probe.is_file():
        raise ValueError("Build the recursive bridge probe before running this focused replay")
    inputs = [ROOT / name for name in (
        "tests/test_recursive_source_bridge.py", "tools/recursive_bridge.py",
        "tools/text_evaluation/integrity.py", "tools/word_evaluation.py",
        "tests/test_rational_inquiry_freeze.py", "evidence/constructions/code_freeze_v4.json",
        "evidence/rational_inquiry/code_freeze_v2.json",
    )] + [Path(__file__).resolve(), probe]
    input_records = [record(path) for path in inputs]
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
               "-p", "test_recursive_source_bridge.py", "-v"]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + str(ROOT)
    environment["NABT_RECURSIVE_BRIDGE_PROBE"] = str(probe)
    observed = subprocess.run(command, cwd=ROOT, env=environment,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    log = observed.stdout.decode("utf-8")
    count = re.search(r"Ran ([0-9]+) tests? in", log)
    if count is None:
        raise ValueError("The focused run did not produce a unittest method count")
    if [record(path) for path in inputs] != input_records:
        raise ValueError("A focused test input changed during execution")
    frozen_after = verify_code_freeze(current_freeze, ROOT)
    if frozen_after != frozen_before:
        raise ValueError("The registered runtime freeze changed during execution")
    original = (REVIEW / "test_recursive_source_bridge_before.py").read_text(encoding="utf-8")
    revised = (ROOT / "tests/test_recursive_source_bridge.py").read_text(encoding="utf-8")
    change = "".join(difflib.unified_diff(original.splitlines(keepends=True), revised.splitlines(keepends=True),
                    fromfile="test_recursive_source_bridge_before.py", tofile="tests/test_recursive_source_bridge.py"))
    report = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "strict_pass": observed.returncode == 0 and "skipped=" not in log,
        "command": command, "returncode": observed.returncode,
        "test_methods_run": int(count.group(1)), "full_make_check_run_by_this_replay": False,
        "compiled_probe_reused_without_build": True,
        "environment": {"PYTHONPATH": "src:.", "NABT_RECURSIVE_BRIDGE_PROBE": str(probe)},
        "input_files": input_records, "input_files_unchanged_during_execution": True,
        "runtime_inventory_verified_before_and_after": len(frozen_after["files"]),
        "runtime_snapshot_sha256": frozen_after["snapshot_sha256"],
        "historical_freeze_unchanged": True, "runtime_files_modified": False,
        "fix": ("The standalone adapter test now pins the registered inquiry v2 manifest and "
                "snapshot and verifies its complete 75-file inventory, including rational_inquiry.py. "
                "The recursive bridge remains excluded from runtime and absent from src/nabt."),
        "historical_rejection_coverage": ("Existing test_rational_inquiry_freeze.py already verifies "
                                         "that the historical freeze cannot authorize the current runtime; "
                                         "this integration fix does not duplicate or weaken those checks."),
        "log_sha256": sha256(observed.stdout).hexdigest(),
        "patch_sha256": sha256(change.encode("utf-8")).hexdigest(),
    }
    output.mkdir(parents=True, exist_ok=True)
    with paths[0].open("xb") as handle:
        handle.write(observed.stdout)
    with paths[1].open("x", encoding="utf-8") as handle:
        handle.write(change)
    with paths[2].open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("strict_pass", "returncode", "test_methods_run",
                     "runtime_inventory_verified_before_and_after", "runtime_snapshot_sha256")}, indent=2))
    return 0 if report["strict_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
