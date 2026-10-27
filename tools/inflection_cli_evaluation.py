#!/usr/bin/env python3
"""Independent CLI regression evidence; no production imports in the parent.

The frozen material is separate from the original 74 and post-review 22 cases.
The child observes real source-file I/O without enforcing or faking a limit.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "evidence/inflection/review_fixes"
FREEZE_SHA256 = "0621a6e6280549d747e4df8983249fd840909f11e91047f06b6d3f589657d5a5"
VERSION = "nabt.inflection.cli-review-evaluation.v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def load_material():
    freeze_path = FOLDER / "independent_cli_freeze_v1.json"
    raw = freeze_path.read_bytes()
    require(sha256(raw).hexdigest() == FREEZE_SHA256, "CLI material freeze changed")
    freeze = json.loads(raw)
    for item in freeze["files"]:
        path = ROOT / item["path"]
        require(path.resolve().is_relative_to(FOLDER.resolve()), "Material path escaped its directory")
        content = path.read_bytes()
        require(len(content) == item["bytes"] and sha256(content).hexdigest() == item["sha256"],
                "Frozen CLI material changed: " + item["path"])
    material = json.loads((FOLDER / "independent_cli_cases_v1.json").read_bytes())
    cases = material["cases"]
    require(len(cases) == len({case["id"] for case in cases}) == freeze["case_count"] == 32,
            "CLI case inventory changed")
    keys = {"exit", "status", "code", "code_prefix", "structured_error", "no_traceback",
            "json_stdout", "valid", "io_budget"}
    require(all(set(case["expected"]) <= keys for case in cases), "Unhandled frozen predicate")
    return freeze, material


def runtime_snapshot(manifest, runtime_root, freeze):
    # This helper has an explicit content allowlist, complete file inventory and
    # archive-member checks. Its exact bytes are themselves preserved below.
    import inflection_evaluation as checker

    snapshot = checker.runtime_snapshot(manifest, runtime_root)
    extras = [Path(__file__), FOLDER / "independent_cli_freeze_v1.json"]
    extras.extend(ROOT / item["path"] for item in freeze["files"])
    existing = {item["path"] for item in snapshot["files"]}
    for path in extras:
        name = str(path.relative_to(ROOT))
        if name not in existing:
            raw = path.read_bytes()
            snapshot["files"].append({"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
            existing.add(name)
    snapshot["measured_snapshot_sha256"] = sha256(wire(snapshot["files"])).hexdigest()
    return snapshot, checker


def probe(spec_path):
    """Run one real CLI invocation in an isolated interpreter and observe I/O."""
    import builtins
    import io
    import os
    import runpy

    spec = json.loads(Path(spec_path).read_bytes())
    runtime_src = (Path(spec["runtime_root"]) / "src").resolve()
    require(not any(name == "nabt" or name.startswith("nabt.") for name in sys.modules),
            "Production modules were loaded before runtime selection")
    sys.path.insert(0, str(runtime_src))
    target = os.path.abspath(spec["source_path"])
    trace = {"schema": "nabt.cli-review.io-trace.v1", "monitor_installed": True,
             "source_path": target, "source_exists": os.path.exists(target),
             "source_size": os.stat(target).st_size if os.path.exists(target) else None,
             "reads": [], "total_returned_bytes": 0,
             "observation_scope": "Python stream read requests/returned bytes and explicit os.read; no truncation"}
    descriptors = set()
    original_builtin_open, original_io_open = builtins.open, io.open
    original_os_open, original_os_read, original_os_close = os.open, os.read, os.close

    def matches(value):
        if type(value) is int:
            return value in descriptors
        try:
            return os.path.abspath(os.fsdecode(os.fspath(value))) == target
        except (TypeError, ValueError):
            return False

    def record(method, requested, returned):
        if type(returned) is int:
            count = returned
        elif isinstance(returned, str):
            count = len(returned.encode("utf-8"))
        elif isinstance(returned, (list, tuple)):
            count = sum(len(x.encode("utf-8") if isinstance(x, str) else x) for x in returned)
        else:
            count = len(returned)
        trace["reads"].append({"method": method, "requested_bytes": requested, "returned_bytes": count})
        trace["total_returned_bytes"] += count

    class TrackedStream:
        def __init__(self, stream):
            self.stream = stream
            try:
                descriptors.add(stream.fileno())
            except (AttributeError, OSError):
                pass

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            try:
                descriptor = self.stream.fileno()
            except (AttributeError, OSError):
                descriptor = None
            try:
                return self.stream.__exit__(*args)
            finally:
                descriptors.discard(descriptor)

        def __getattr__(self, name):
            result = getattr(self.stream, name)
            return TrackedStream(result) if name in {"buffer", "raw"} and result is not None else result

        def read(self, size=-1):
            result = self.stream.read(size)
            record("read", size, result)
            return result

        def read1(self, size=-1):
            result = self.stream.read1(size)
            record("read1", size, result)
            return result

        def readinto(self, buffer):
            result = self.stream.readinto(buffer)
            record("readinto", memoryview(buffer).nbytes, result or 0)
            return result

        def readinto1(self, buffer):
            result = self.stream.readinto1(buffer)
            record("readinto1", memoryview(buffer).nbytes, result or 0)
            return result

        def readline(self, size=-1):
            result = self.stream.readline(size)
            record("readline", size, result)
            return result

        def readlines(self, hint=-1):
            result = self.stream.readlines(hint)
            record("readlines", hint, result)
            return result

        def __iter__(self):
            return self

        def __next__(self):
            result = self.stream.readline()
            record("iteration_readline", -1, result)
            if not result:
                raise StopIteration
            return result

        def close(self):
            try:
                descriptor = self.stream.fileno()
            except (AttributeError, OSError):
                descriptor = None
            try:
                return self.stream.close()
            finally:
                descriptors.discard(descriptor)

    def wrapped_open(original):
        def call(file, *args, **kwargs):
            stream = original(file, *args, **kwargs)
            return TrackedStream(stream) if matches(file) else stream
        return call

    def tracked_os_open(path, *args, **kwargs):
        descriptor = original_os_open(path, *args, **kwargs)
        if matches(path):
            descriptors.add(descriptor)
        return descriptor

    def tracked_os_read(descriptor, size):
        result = original_os_read(descriptor, size)
        if descriptor in descriptors:
            record("os.read", size, result)
        return result

    def tracked_os_close(descriptor):
        try:
            return original_os_close(descriptor)
        finally:
            descriptors.discard(descriptor)

    builtins.open = wrapped_open(original_builtin_open)
    io.open = wrapped_open(original_io_open)
    os.open, os.read, os.close = tracked_os_open, tracked_os_read, tracked_os_close
    try:
        sys.argv = ["nabt"] + spec["argv"]
        runpy.run_module("nabt", run_name="__main__")
    finally:
        builtins.open, io.open = original_builtin_open, original_io_open
        os.open, os.read, os.close = original_os_open, original_os_read, original_os_close
        modules = []
        for name, module in sorted(sys.modules.items()):
            if name == "nabt" or name.startswith("nabt."):
                filename = getattr(module, "__file__", None)
                modules.append({"module": name, "path": filename,
                                "selected_runtime": filename is not None and Path(filename).resolve().is_relative_to(runtime_src)})
        trace["loaded_modules"] = modules
        trace["origin_guard_passed"] = bool(modules) and all(row["selected_runtime"] for row in modules)
        trace["runtime_version"] = getattr(sys.modules.get("nabt"), "__version__", None)
        with original_builtin_open(spec["trace_path"], "x", encoding="utf-8") as stream:
            json.dump(trace, stream, ensure_ascii=False, indent=2)
            stream.write("\n")


def invoke(runtime_root, argv, source, work, label):
    spec_path, trace_path = work / (label + ".spec.json"), work / (label + ".trace.json")
    spec = {"runtime_root": str(runtime_root), "argv": argv, "source_path": str(source),
            "trace_path": str(trace_path)}
    spec_path.write_bytes(wire(spec))
    command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--_probe", str(spec_path)]
    completed = subprocess.run(command, cwd=work, capture_output=True, timeout=30, check=False)
    stdout, stderr = completed.stdout, completed.stderr
    return {"argv": argv, "exit_code": completed.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "stdout_base64": base64.b64encode(stdout).decode(),
            "stderr_base64": base64.b64encode(stderr).decode(),
            "stdout_sha256": sha256(stdout).hexdigest(), "stderr_sha256": sha256(stderr).hexdigest(),
            "io_trace": json.loads(trace_path.read_bytes()) if trace_path.exists() else None}


def score_case(case, raw):
    expected = case["expected"]
    checks = []

    def check(name, passed, detail=None):
        checks.append({"predicate": name, "passed": bool(passed), "detail": detail})

    check("exit_status", type(raw["exit_code"]) is int and raw["exit_code"] == expected["exit"], raw["exit_code"])
    check("no_traceback", "Traceback (most recent call last):" not in raw["stdout"] + raw["stderr"])
    trace = raw.get("io_trace") or {}
    check("fresh_selected_runtime", trace.get("monitor_installed") is True and trace.get("origin_guard_passed") is True)
    nonempty = [(name, raw[name]) for name in ("stdout", "stderr") if raw[name].strip()]
    payload = None
    if len(nonempty) == 1:
        try:
            parsed = json.loads(nonempty[0][1])
            if type(parsed) is dict:
                payload = parsed
        except (ValueError, RecursionError):
            pass
    check("single_structured_json_result", payload is not None)
    if expected.get("json_stdout"):
        check("json_on_stdout", payload is not None and nonempty[0][0] == "stdout")
    if expected.get("structured_error"):
        code = None if payload is None else payload.get("code")
        check("named_error", isinstance(code, str) and re.fullmatch(r"[A-Z][A-Z0-9_]*", code) is not None)
    for field in ("status", "code", "valid"):
        if field in expected:
            value = None if payload is None else payload.get(field)
            check(field, type(value) is type(expected[field]) and value == expected[field], value)
    if "code_prefix" in expected:
        value = None if payload is None else payload.get("code")
        check("invalid_input_code", isinstance(value, str) and value.startswith(expected["code_prefix"]), value)
    if "io_budget" in expected:
        budget = expected["io_budget"]
        reads = trace.get("reads")
        trace_ok = isinstance(reads, list) and type(trace.get("total_returned_bytes")) is int
        check("io_observation_present", trace_ok)
        if trace_ok:
            check("cumulative_source_byte_budget", trace["total_returned_bytes"] <= budget["maximum_total_returned_bytes"],
                  trace["total_returned_bytes"])
            check("bounded_source_read_requests", all(type(r.get("requested_bytes")) is int
                  and 0 <= r["requested_bytes"] <= budget["maximum_requested_bytes"] for r in reads),
                  [r.get("requested_bytes") for r in reads])
            check("read_trace_consistency", sum(r["returned_bytes"] for r in reads) == trace["total_returned_bytes"])
    return {"id": case["id"], "track": case["track"], "command": case["command"],
            "passed": all(row["passed"] for row in checks), "checks": checks,
            "failed_predicates": [row["predicate"] for row in checks if not row["passed"]],
            "exit_code": raw["exit_code"], "observed_payload": payload,
            "source_io": {k: trace.get(k) for k in ("source_size", "reads", "total_returned_bytes", "runtime_version")}}


def evaluate(args):
    freeze, material = load_material()
    output, runtime_root = args.output.resolve(), args.runtime_root.resolve()
    require(not output.exists(), "Refusing to overwrite CLI measurement")
    raw_path = output.with_suffix(".raw.jsonl.gz")
    require(not raw_path.exists(), "Refusing to overwrite CLI raw output")
    output.parent.mkdir(parents=True, exist_ok=True)
    snapshot, checker = runtime_snapshot(args.runtime_freeze, runtime_root, freeze)
    code_archive = checker.preserve_code(snapshot, output)
    report = {"schema": VERSION, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "material_freeze_sha256": FREEZE_SHA256, "claim": "POST_PUBLICATION_CLI_REGRESSION_ONLY",
              "snapshot": snapshot, "code_archive": code_archive, "setups": [], "cases": []}
    with tempfile.TemporaryDirectory(prefix="nabt-cli-review-") as temporary, gzip.open(raw_path, "xt", encoding="utf-8") as raw_log:
        work = Path(temporary)
        fixtures = {}
        for item in material["fixtures"]:
            original = ROOT / item["path"]
            destination = work / original.name
            destination.write_bytes(original.read_bytes())
            fixtures[original.name] = destination
        fixtures["missing.gz"], fixtures["missing.txt"] = work / "missing.gz", work / "missing.txt"
        reports = {}
        needed_reports = sorted({case["report_fixture"] for case in material["cases"] if case["command"] == "verify-inflection"})
        for index, name in enumerate(needed_reports):
            argv = ["read-inflection", str(fixtures[name]), "--qac", str(fixtures["qac.tsv"])]
            raw = invoke(runtime_root, argv, fixtures[name], work, "setup-" + str(index))
            raw_log.write(json.dumps({"phase": "verification_report_setup", "source_fixture": name, "raw": raw}, ensure_ascii=False) + "\n")
            raw_log.flush()
            expected = {"exit": 0, "json_stdout": True, "no_traceback": True, "status": "LICENSED_READINGS"}
            scored = score_case({"id": "setup:" + name, "track": "setup", "command": "read-inflection", "expected": expected}, raw)
            report["setups"].append(scored)
            if scored["passed"]:
                report_path = work / ("report-" + str(index) + ".json")
                report_path.write_bytes(base64.b64decode(raw["stdout_base64"]))
                reports[name] = report_path
        for case in material["cases"]:
            corpus, source = fixtures[case["corpus_fixture"]], fixtures[case["source_fixture"]]
            command = case["command"]
            if command == "audit-corpus":
                argv = [command, str(corpus), "--format", "qac"]
            elif command == "learn-qac-lexicon":
                argv = [command, str(corpus)]
            elif command == "read-inflection":
                argv = [command, str(source), "--qac", str(corpus)]
            else:
                if case["report_fixture"] not in reports:
                    row = {"id": case["id"], "track": case["track"], "command": command, "passed": False,
                           "failed_predicates": ["verification_report_setup_failed"], "checks": []}
                    report["cases"].append(row)
                    raw_log.write(json.dumps({"id": case["id"], "setup_unavailable": True}, ensure_ascii=False) + "\n")
                    raw_log.flush()
                    continue
                argv = [command, str(reports[case["report_fixture"]]), "--source", str(source), "--qac", str(corpus)]
            try:
                raw = invoke(runtime_root, argv, source, work, case["id"])
                raw_log.write(json.dumps({"id": case["id"], "raw": raw}, ensure_ascii=False) + "\n")
                raw_log.flush()
                row = score_case(case, raw)
            except Exception as error:
                row = {"id": case["id"], "track": case["track"], "command": command, "passed": False,
                       "failed_predicates": ["harness_execution_error"], "checks": [],
                       "error_type": type(error).__name__, "message": str(error)}
                raw_log.write(json.dumps({"id": case["id"], "harness_error": row}, ensure_ascii=False) + "\n")
                raw_log.flush()
            report["cases"].append(row)
    failures = Counter(predicate for case in report["cases"] for predicate in case["failed_predicates"])
    report.update(completed_at_utc=datetime.now(timezone.utc).isoformat(), total=len(report["cases"]),
                  passed=sum(case["passed"] for case in report["cases"]), failed_predicates=dict(failures),
                  setup_pass=all(case["passed"] for case in report["setups"]),
                  raw_log={"filename": raw_path.name, "sha256": sha256(raw_path.read_bytes()).hexdigest()})
    report["gate_pass"] = report["setup_pass"] and report["passed"] == report["total"] == 32
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(output), "passed": report["passed"], "total": report["total"],
                      "setup_pass": report["setup_pass"], "gate_pass": report["gate_pass"],
                      "failed_predicates": report["failed_predicates"]}, ensure_ascii=False))
    return 0 if report["gate_pass"] else 1


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--_probe":
        probe(sys.argv[2])
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-freeze", type=Path, default=ROOT / "evidence/certified_transition_v1/code_freeze_v1.json")
    parser.add_argument("--output", type=Path, required=True)
    return evaluate(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
