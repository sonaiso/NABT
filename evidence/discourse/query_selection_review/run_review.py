"""Run only the frozen authored query-selection regression; never write runtime."""

from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def record(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def main():
    if len(sys.argv) != 2 or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", sys.argv[1]) is None:
        raise SystemExit("Use one new lowercase result label")
    label = sys.argv[1]
    result_path = HERE / ("results_" + label + ".json")
    log_path = HERE / ("run_" + label + ".log")
    reports_path = HERE / ("reports_" + label + ".json")
    if any(p.exists() for p in (result_path, log_path, reports_path)):
        raise SystemExit("A result with this label already exists; historical files cannot be overwritten")
    freeze_path = ROOT / "evidence" / "discourse" / "code_freeze_v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    before = [record(ROOT / f["path"]) for f in freeze["files"]]
    expected = {f["path"]: f for f in freeze["files"]}
    mismatches = [f["path"] for f in before if f != expected[f["path"]]]
    spec = importlib.util.spec_from_file_location("query_selection_regression",
                                                ROOT / "tests" / "test_discourse_query_selection.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started, monotonic = utc(), time.monotonic()
    stream = io.StringIO()
    outcome = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(module))
    completed, duration = utc(), time.monotonic() - monotonic
    after = [record(ROOT / f["path"]) for f in freeze["files"]]
    log_path.write_text(stream.getvalue(), encoding="utf-8")
    reports_path.write_text(json.dumps(module.REPORTS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {
        "schema": "nabt.discourse-query-selection-review-result.v1", "label": label,
        "scope": "Six independently authored targeted regression cases; not independent gold or natural-corpus evaluation",
        "started_utc": started, "completed_utc": completed, "duration_seconds": duration,
        "material_freeze": record(HERE / "material_freeze_v1.json"),
        "reference_runtime_freeze": record(freeze_path),
        "runtime_matches_reference_v3": not mismatches,
        "runtime_differences_from_v3": mismatches,
        "runtime_unchanged_during_measurement": before == after,
        "runtime_before": before, "runtime_after": after,
        "tests_run": outcome.testsRun, "failures": len(outcome.failures), "errors": len(outcome.errors),
        "passed": outcome.testsRun - len(outcome.failures) - len(outcome.errors),
        "success": outcome.wasSuccessful() and before == after,
        "observations": module.OBSERVATIONS,
        "failure_details": [{"test": str(t), "traceback": detail} for t, detail in outcome.failures],
        "error_details": [{"test": str(t), "traceback": detail} for t, detail in outcome.errors],
        "log": record(log_path), "reports": record(reports_path),
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("label", "tests_run", "passed", "failures", "errors",
          "success", "runtime_matches_reference_v3", "runtime_differences_from_v3",
          "runtime_unchanged_during_measurement")}, ensure_ascii=False))
    raise SystemExit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
