"""Release observation using the installed frozen-input owners unchanged.

This records input identity only.  It does not run the directed oracle,
claim a new experiment, or replace any native/runtime release gate.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from tools import interpretive_links_regression, inflection_evaluation


def identity(relative):
    raw = (ROOT / relative).read_bytes()
    return {"path": relative, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def main():
    report = {
        "schema": "nabt.derivation-surface.frozen-owner-observation.v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tools:. python evidence/derivation_surface_v1/validation/check_frozen_owners.py",
        "scope": "Frozen oracle dependency and authoritative runtime/archive identity only; no new oracle or linguistic evaluation",
        "owners": [identity("tools/interpretive_links_regression.py"),
                   identity("tools/inflection_evaluation.py")],
        "checks": [],
    }
    operations = [
        ("oracle_dependencies", "tools.interpretive_links_regression.check_dependencies",
         interpretive_links_regression.check_dependencies),
        ("runtime_and_archive", "tools.inflection_evaluation.runtime_snapshot",
         lambda: inflection_evaluation.runtime_snapshot(
             ROOT / "evidence/interpretive_links_v1/code_freeze_v1.json", ROOT)),
    ]
    for name, owner, operation in operations:
        try:
            result = operation()
            count = result["runtime_file_count"] if name == "runtime_and_archive" else len(result["files"])
            report["checks"].append({"name": name, "owner": owner, "passed": True,
                                      "file_count": count, "result": result})
        except Exception as error:
            report["checks"].append({"name": name, "owner": owner, "passed": False,
                                      "error_type": type(error).__name__, "error": str(error)})
    report["passed"] = all(row["passed"] for row in report["checks"])
    output = Path(__file__).with_name("frozen_owner_checks.json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": report["passed"], "checks": [
        {key: value for key, value in row.items() if key != "result"}
        for row in report["checks"]]}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
