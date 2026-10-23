#!/usr/bin/env python3
"""Record the explicitly requested isolated review comparisons, once."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
GROUPS = ("operator_dispatch_review", "operator_wh_review", "agreement_review",
          "prefix_review", "prefix_review/conjunction_supplement")
RUNTIMES = {
    2: "artifacts/local/operator-dispatch-review/runtime-v2",
    3: "artifacts/local/construction-review-v3/runtime-v3",
    4: "artifacts/local/construction-review-v4/runtime-v4",
}


def file_record(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw),
            "sha256": sha256(raw).hexdigest()}


def save(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)


def main():
    jobs = [(group, version) for group in GROUPS for version in (2, 4)]
    jobs += [("query_agreement_review", version) for version in (3, 4)]
    jobs += [("query_agreement_review/claim_edge_supplement", 4)]
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME"):
        environment.pop(name, None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    def run(job):
        group, version = job
        output = BASE / group / f"v{version}"
        output.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".json", ".raw.jsonl.gz", ".stdout.log", ".stderr.log", ".command.json"):
            if Path(str(output) + suffix).exists():
                raise RuntimeError("Refusing to overwrite: " + str(output) + suffix)
        argv = [sys.executable, "-I", "-B",
                f"evidence/constructions/{group}/run_review_v4.py",
                "--runtime-root", RUNTIMES[version],
                "--runtime-freeze", f"evidence/constructions/code_freeze_v{version}.json",
                "--output-prefix", str(output.relative_to(ROOT))]
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(argv, cwd=ROOT, env=environment, capture_output=True, check=False)
        stdout_path, stderr_path = Path(str(output) + ".stdout.log"), Path(str(output) + ".stderr.log")
        save(stdout_path, result.stdout)
        save(stderr_path, result.stderr)
        record = {"group": group, "runtime_version": version, "argv": argv, "cwd": str(ROOT),
                  "started_utc": started, "ended_utc": datetime.now(timezone.utc).isoformat(),
                  "exit_code": result.returncode, "stdout": file_record(stdout_path),
                  "stderr": file_record(stderr_path)}
        record_path = Path(str(output) + ".command.json")
        save(record_path, (json.dumps(record, indent=2) + "\n").encode())
        return record

    with ThreadPoolExecutor(max_workers=3) as executor:
        commands = list(executor.map(run, jobs))
    record = {"schema": "nabt.constructions.review-v4-commands.v1", "python": sys.version,
              "platform": platform.platform(), "pythonpath_removed": True, "pythonhome_removed": True,
              "isolated_python_flag": True, "commands": commands}
    save(BASE / "commands.json", (json.dumps(record, indent=2) + "\n").encode())
    print(json.dumps({"commands": len(commands), "exit_codes": [c["exit_code"] for c in commands]}))
    return 0 if all(c["exit_code"] == 0 for c in commands) else 1


if __name__ == "__main__":
    raise SystemExit(main())
