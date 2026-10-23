"""Capture the paired strict legacy runs without changing either runtime.

The caller-provided prior runtime directory must reproduce the pinned v2
archive. The evaluator authenticates both complete package inventories.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def run(label, runtime_root, setup, expected_tool):
    tool = ROOT / "tools/discourse_evaluation.py"
    if sha256(tool.read_bytes()).hexdigest() != expected_tool:
        raise ValueError("The shared evaluator changed before execution")
    output = FOLDER / "runs" / (label + ".json")
    output.parent.mkdir(exist_ok=True)
    log_path = output.with_suffix(".log")
    if any(p.exists() for p in (output, log_path, output.with_suffix(".exit.json"))):
        raise ValueError("Refusing to overwrite an earlier attempt")
    command = [sys.executable, str(tool), "--qac", setup["qac"],
               "--runtime-root", runtime_root, "--runtime-freeze",
               str(ROOT / "evidence/constructions" / ("code_freeze_" + label.rsplit("_", 1)[1] + ".json")),
               "--output", str(output)]
    started = datetime.now(timezone.utc).isoformat()
    print(label + " started " + started, flush=True)
    with log_path.open("xb") as handle:
        process = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    completed = datetime.now(timezone.utc).isoformat()
    record = {"label": label, "command": command, "started_at_utc": started,
              "completed_at_utc": completed, "exit_code": process.returncode,
              "evaluator_sha256": expected_tool, "output_exists": output.exists(),
              "log": log_path.name, "log_sha256": sha256(log_path.read_bytes()).hexdigest()}
    if output.exists():
        result = json.loads(output.read_bytes())
        raw_path = output.with_suffix(".raw.jsonl.gz")
        raw = raw_path.read_bytes()
        rows = [json.loads(line) for line in gzip.decompress(raw).splitlines()]
        record.update(output_sha256=sha256(output.read_bytes()).hexdigest(),
                      raw_log_sha256=sha256(raw).hexdigest(), closed_raw_records=len(rows),
                      measurement={k: result[k] for k in
                          ("passed", "total", "strict_pass", "false_accept_count", "execution_errors",
                           "question_execution_errors", "measurement_valid", "by_question_outcome")},
                      raw_log_valid=result["raw_log"]["valid"])
        if result["measurement_valid"] is not True or result["raw_log"]["valid"] is not True:
            raise ValueError("The evaluator did not certify a complete valid measurement")
        if len(rows) != 90:
            raise ValueError("The closed raw journal has the wrong record inventory")
        expected_exit = 0 if result["strict_pass"] else 1
        if process.returncode != expected_exit:
            raise ValueError("The process status disagrees with the strict result")
    with output.with_suffix(".exit.json").open("x", encoding="utf-8") as handle:
        handle.write(wire(record))
    if not output.exists() or sha256(tool.read_bytes()).hexdigest() != expected_tool:
        raise ValueError("No final measurement or evaluator bytes changed during execution")
    print(label + " complete " + wire({k: record[k] for k in
          ("exit_code", "measurement", "raw_log_valid", "closed_raw_records")}).strip(), flush=True)
    return record


if __name__ == "__main__":
    setup = json.loads((FOLDER / "source_before_gate/manifest.json").read_bytes())
    expected_tool = next(r["sha256"] for r in setup["files"]
                         if r["original_path"] == "tools/discourse_evaluation.py")
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, label, runtime_root, setup, expected_tool)
                   for label, runtime_root in
                   (("constructions_v2", setup["old_runtime_root"]),
                    ("constructions_v4", setup["new_runtime_root"]))]
        for future in futures:
            future.result()
