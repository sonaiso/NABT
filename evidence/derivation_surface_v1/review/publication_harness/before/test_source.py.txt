"""Focused publication-helper regressions, with no historical evidence writes.

Each helper is loaded under an isolated repository-shaped path.  Archive and
child-test boundaries are replaced by cheap controls; filesystem writes and
Git worktree/index changes remain real.  The tiny collector fixtures are
synthetic observations and cannot be mistaken for retained release evidence.
"""
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from types import ModuleType
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
# The before/after evidence runner may select the three archived helper files.
# Every selected helper is still copied under a fresh TemporaryDirectory.
SOURCE_ROOT = ROOT
PREFIX = Path("evidence/derivation_surface_v1/validation")
HARNESSES = tuple(PREFIX / name / "run_clean_checkout.py"
                  for name in ("clean_checkout", "clean_checkout_final"))
COLLECTOR = PREFIX / "collect_release_evidence.py"
SENTINEL = b"retained observation must stay byte-identical\n"


class ExpensiveBoundary(RuntimeError):
    """Stop before a real archive or child suite is executed."""


def isolated_module(relative, root):
    raw = (SOURCE_ROOT / relative).read_bytes()
    logical = root / relative
    logical.parent.mkdir(parents=True, exist_ok=True)
    logical.write_bytes(raw)
    module = ModuleType("isolated_derivation_evidence_" + relative.parent.name)
    module.__file__ = str(logical)
    exec(compile(raw, str(logical), "exec", dont_inherit=True), module.__dict__)
    return module


def git(root, *args):
    return subprocess.check_output(
        ["git", "-c", "user.name=NABT evidence fixture", "-c",
         "user.email=nabt-fixture@example.invalid", *args],
        cwd=root, text=True, stderr=subprocess.PIPE).strip()


def collector_fixture(root):
    module = isolated_module(COLLECTOR, root)
    runtime = root / "src" / "fixture.py"
    runtime.parent.mkdir()
    runtime.write_text("state = 'tested'\n", encoding="utf-8")
    git(root, "init", "--quiet")
    git(root, "add", "src/fixture.py")
    git(root, "commit", "--quiet", "-m", "synthetic tested runtime")
    module.HEAD = git(root, "rev-parse", "HEAD")

    def put_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    for directory, exit_code in ((module.ATTEMPT, 2), (module.RESUME, 0)):
        directory.mkdir(parents=True)
        log = b"synthetic completed local observation\n"
        (directory / "full_check.log").write_bytes(log)
        put_json(directory / "execution.json", {
            "implementation_commit": module.HEAD, "exit_code": exit_code,
            "log_sha256": sha256(log).hexdigest(), "log_bytes": len(log),
            "reused_completed_target": {"same_implementation_commit": module.HEAD},
        })
    put_json(module.HERE / "unittest_summary.json", {
        "tested_head": module.HEAD,
        "methods": {"distinct_ids": 3126, "ok": 3088, "skipped": 38,
                    "failures": 0, "errors": 0},
        "footer": {"result": "OK (skipped=38)"},
    })
    for path in (module.ATTEMPT / "code_entropy.json",
                 root / "artifacts/local/derivation-surface-full-check/code_entropy.json",
                 root / "artifacts/local/derivation-surface-full-check/code_entropy_baseline.json"):
        put_json(path, {"synthetic": True})
    return module, runtime


class DerivationSurfaceEvidenceHarnessTests(unittest.TestCase):
    def retain_staging_cleanup(self, command):
        staging = Path(command[command.index("--output") + 1]).parent
        self.assertTrue(staging.name.startswith("nabt-derivation-clean-"))
        self.addCleanup(shutil.rmtree, staging, ignore_errors=True)

    def test_harnesses_allocate_fresh_output_before_archive(self):
        for relative in HARNESSES:
            for mode in ("explicit", "default"):
                with self.subTest(harness=str(relative), mode=mode), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    module = isolated_module(relative, root)
                    retained = module.EVIDENCE / "acceptance.log"
                    retained.write_bytes(SENTINEL)
                    destination = root / "new-output"
                    argv = [str(root / relative)]
                    if mode == "explicit":
                        argv += ["--output-dir", str(destination)]

                    def archive_boundary(command, **options):
                        self.assertEqual(command[:2], ["git", "archive"])
                        self.retain_staging_cleanup(command)
                        if mode == "explicit":
                            outputs = [destination] if destination.is_dir() else []
                        else:
                            parent = root / "artifacts/local"
                            outputs = list(parent.iterdir()) if parent.exists() else []
                        self.assertEqual(len(outputs), 1, "Fresh output must exist before archive execution")
                        self.assertTrue(outputs[0].is_dir())
                        self.assertNotEqual(outputs[0], module.EVIDENCE)
                        self.assertEqual(list(outputs[0].iterdir()), [])
                        self.assertEqual(retained.read_bytes(), SENTINEL)
                        raise ExpensiveBoundary("archive intentionally not executed")

                    with mock.patch.object(sys, "argv", argv), \
                            mock.patch.object(module.subprocess, "run", side_effect=archive_boundary) as run, \
                            redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                        with self.assertRaises(ExpensiveBoundary):
                            module.main()
                    self.assertEqual(run.call_count, 1)
                    self.assertEqual(retained.read_bytes(), SENTINEL)

    def test_harnesses_reject_existing_output_without_touching_history(self):
        for relative in HARNESSES:
            for kind in ("retained_directory", "other_directory", "file"):
                with self.subTest(harness=str(relative), kind=kind), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    module = isolated_module(relative, root)
                    retained = module.EVIDENCE / "acceptance.log"
                    retained.write_bytes(SENTINEL)
                    destination = module.EVIDENCE if kind == "retained_directory" else root / "existing"
                    if kind == "other_directory":
                        destination.mkdir()
                        (destination / "acceptance.log").write_bytes(SENTINEL)
                    elif kind == "file":
                        destination.write_bytes(SENTINEL)
                    with mock.patch.object(sys, "argv", [str(root / relative), "--output-dir", str(destination)]), \
                            mock.patch.object(module.subprocess, "run", side_effect=ExpensiveBoundary("unexpected execution")) as run, \
                            redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as failure:
                            module.main()
                    self.assertEqual(failure.exception.code, 2)
                    run.assert_not_called()
                    self.assertEqual(retained.read_bytes(), SENTINEL)
                    if kind == "file":
                        self.assertEqual(destination.read_bytes(), SENTINEL)
                    else:
                        self.assertEqual((destination / "acceptance.log").read_bytes(), SENTINEL)

    def test_harnesses_do_not_replace_a_log_collision_after_allocation(self):
        for relative in HARNESSES:
            with self.subTest(harness=str(relative)), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                module = isolated_module(relative, root)
                retained = module.EVIDENCE / "acceptance.log"
                retained.write_bytes(SENTINEL)
                destination = root / "new-output"
                child_calls = []

                def cheap_archive_and_child(command, **options):
                    if command[:2] == ["git", "archive"]:
                        self.retain_staging_cleanup(command)
                        archive = Path(command[command.index("--output") + 1])
                        # Empty local tar only: no repository export or large archive.
                        with tarfile.open(archive, "w"):
                            pass
                        destination.mkdir(exist_ok=True)
                        (destination / "acceptance.log").write_bytes(SENTINEL)
                        return subprocess.CompletedProcess(command, 0, b"", b"")
                    child_calls.append(command)
                    if len(child_calls) > 1:
                        raise ExpensiveBoundary("stop after the first synthetic child result")
                    return subprocess.CompletedProcess(command, 0, b"synthetic child output\n", b"")

                observed = None
                with mock.patch.object(sys, "argv", [str(root / relative), "--output-dir", str(destination)]), \
                        mock.patch.object(module.subprocess, "run", side_effect=cheap_archive_and_child), \
                        redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    try:
                        module.main()
                    except (FileExistsError, ExpensiveBoundary) as error:
                        observed = error
                self.assertEqual(retained.read_bytes(), SENTINEL,
                                 "The historical output was overwritten")
                self.assertEqual((destination / "acceptance.log").read_bytes(), SENTINEL)
                self.assertIsInstance(observed, FileExistsError)
                self.assertEqual(len(child_calls), 1)

    def test_collector_allows_clean_snapshot_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            module, runtime = collector_fixture(Path(temp))
            with mock.patch.object(module.zipfile, "ZipFile", side_effect=ExpensiveBoundary("ZIP intentionally not written")) as archive:
                with self.assertRaises(ExpensiveBoundary):
                    module.main()
            self.assertEqual(archive.call_count, 1)
            self.assertFalse((module.HERE / "release_gate_outputs.zip").exists())
            self.assertEqual(runtime.read_text(encoding="utf-8"), "state = 'tested'\n")

    def test_collector_rejects_actual_staged_and_unstaged_runtime_changes(self):
        for mode in ("unstaged", "staged", "staged_with_restored_worktree"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                module, runtime = collector_fixture(root)
                original = runtime.read_bytes()
                runtime.write_bytes(b"state = 'changed'\n")
                if mode != "unstaged":
                    git(root, "add", "src/fixture.py")
                if mode == "staged_with_restored_worktree":
                    runtime.write_bytes(original)
                self.assertEqual(git(root, "rev-parse", "HEAD"), module.HEAD)
                with mock.patch.object(module.zipfile, "ZipFile", side_effect=ExpensiveBoundary("unexpected archive")) as archive:
                    with self.assertRaises(AssertionError):
                        module.main()
                archive.assert_not_called()
                self.assertFalse((module.HERE / "release_gate_outputs.zip").exists())


if __name__ == "__main__":
    unittest.main()
