"""Retain completed local release evidence without rerunning any gate.

This is an evidence collector, not a checker or a source of linguistic authority.
The archive retains the failed full command and the successful continuation as
separate observations.  Inputs and output members are hashed incrementally.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
HEAD = "e1e4a950a1f6df4268d18c3211c5e66bccc0f78b"
ATTEMPT = ROOT / "artifacts/local/derivation-surface-full-check-attempt2"
RESUME = ROOT / "artifacts/local/derivation-surface-full-check-native-resume"
BLOCK = 1024 * 1024


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK), b""):
            value.update(block)
    return value.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main() -> None:
    before = load(ATTEMPT / "execution.json")
    after = load(RESUME / "execution.json")
    unit = load(HERE / "unittest_summary.json")
    assert before["implementation_commit"] == after["implementation_commit"] == HEAD
    assert unit["tested_head"] == HEAD
    assert unit["methods"]["distinct_ids"] == 3126
    assert unit["methods"]["ok"] == 3088
    assert unit["methods"]["skipped"] == 38
    assert unit["methods"]["failures"] == unit["methods"]["errors"] == 0
    assert unit["footer"]["result"] == "OK (skipped=38)"
    assert before["exit_code"] == 2, "Retain the observed Lake startup failure"
    assert after["exit_code"] == 0, "Remaining native/source gates must finish"
    assert after["reused_completed_target"]["same_implementation_commit"] == HEAD
    assert subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip() == HEAD
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", "src", "formal", "tools", "tests",
         "Makefile", ".github/workflows"], cwd=ROOT, text=True
    ).strip(), "Do not collect changed runtime inputs as the tested revision"
    for directory, observation in ((ATTEMPT, before), (RESUME, after)):
        log = directory / "full_check.log"
        assert digest(log) == observation["log_sha256"]
        assert log.stat().st_size == observation["log_bytes"]

    files = sorted(
        [p for p in RESUME.rglob("*") if p.is_file()]
        + [ATTEMPT / "execution.json", ATTEMPT / "full_check.log",
           ATTEMPT / "code_entropy.json",
           ROOT / "artifacts/local/derivation-surface-full-check/code_entropy.json",
           ROOT / "artifacts/local/derivation-surface-full-check/code_entropy_baseline.json"],
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    assert all(not p.is_symlink() for p in files)
    assert len(files) == len(set(files))
    members = [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
         "sha256": digest(p)}
        for p in files
    ]
    archive = HERE / "release_gate_outputs.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as bundle:
        for path, member in zip(files, members):
            entry = zipfile.ZipInfo(member["path"], (2026, 11, 2, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            with path.open("rb") as source, bundle.open(entry, "w") as target:
                shutil.copyfileobj(source, target, BLOCK)
            assert path.stat().st_size == member["bytes"]
            assert digest(path) == member["sha256"]
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.namelist() == [member["path"] for member in members]
        for member in members:
            value = hashlib.sha256()
            count = 0
            with bundle.open(member["path"]) as stream:
                for block in iter(lambda: stream.read(BLOCK), b""):
                    value.update(block)
                    count += len(block)
            assert count == member["bytes"]
            assert value.hexdigest() == member["sha256"]

    write_new(HERE / "attempt2_execution.json", before)
    write_new(HERE / "native_resume_execution.json", after)
    write_new(HERE / "release_gate_outputs.json", {
        "schema": "nabt.derivation-surface-release-evidence-archive.v1",
        "implementation_commit": HEAD,
        "archive": archive.relative_to(ROOT).as_posix(),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": digest(archive),
        "member_count": len(members),
        "member_bytes": sum(member["bytes"] for member in members),
        "members_verified_after_write": True,
        "hashing_and_copying": "Incremental 1 MiB chunks; no full archive allocation",
        "members": members,
    })
    write_new(HERE / "local_release_gate.json", {
        "schema": "nabt.derivation-surface-local-release-gate.v1",
        "implementation_commit": HEAD,
        "status": "PASSED_BY_COMPLETED_TARGET_AND_NATIVE_CONTINUATION",
        "single_uninterrupted_make_check_succeeded": False,
        "completed_test_target": {
            "record": "unittest_summary.json",
            "record_sha256": digest(HERE / "unittest_summary.json"),
            "methods": 3126, "passed": 3088, "skipped": 38,
            "failures": 0, "errors": 0,
            "scope": "Successful test target inside the retained exit-2 command",
        },
        "full_command_observation": {
            "record": "attempt2_execution.json", "exit_code": before["exit_code"],
            "meaning": "test completed successfully; following Lake startup failed in restricted environment",
        },
        "remaining_make_check_targets": {
            "record": "native_resume_execution.json", "exit_code": after["exit_code"],
            "command": after["command"],
            "meaning": "Unchanged remaining Makefile targets, with the same pinned Lean in the authorized build environment",
        },
        "retained_interruption": "interrupted_attempt1.json",
        "outputs": "release_gate_outputs.json",
        "limits": [
            "The existing documented coverage misses and optional skips are retained.",
            "Passing existing regression policies does not establish Arabic completeness.",
            "This record is local; every triggered remote gate must still pass on the publication head.",
        ],
    })
    print(json.dumps({"status": "RETAINED_AND_REHASHED", "members": len(members),
                      "archive_bytes": archive.stat().st_size,
                      "archive_sha256": digest(archive)}))


if __name__ == "__main__":
    main()
