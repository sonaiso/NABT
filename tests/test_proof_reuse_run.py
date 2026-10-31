"""The reuse front door forwards existing contracts; it does not decide them."""
from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.entropy_framework import reuse_run as runner
from tools.entropy_framework.registry import FrameworkError, FrameworkResourceError


class ReuseEntryTests(unittest.TestCase):
    def test_only_code_owned_entries_select_programs(self):
        with patch.object(runner.subprocess, "run") as execute:
            for entry in ("os", "tools.other", "core; echo injected", "../core", True, None,
                          {"module": "os", "command": ["sh"]}):
                with self.subTest(entry=entry), self.assertRaises(FrameworkError):
                    runner.run_entry(entry, [])
            execute.assert_not_called()

    def test_description_is_detached_from_dispatch(self):
        descriptions = runner.describe_entries()
        descriptions["core"]["module"] = "arbitrary_module"
        descriptions["core"]["native_target"] = "foreign"
        del descriptions["meaning-preservation"]
        command = runner.entry_command("core", ["--version"])
        self.assertEqual(command, [sys.executable, "-B", "-m", "nabt", "--version"])
        self.assertIn("meaning-preservation", runner.describe_entries())

    def test_arguments_remain_separate_literal_tokens(self):
        arguments = ["ask-discourse", "a path with spaces.txt", "هل زيدٌ حكيمٌ؟; $(false)"]
        command = runner.entry_command("core", arguments)
        self.assertEqual(command[-3:], arguments)
        self.assertEqual(len(command), 7)
        with patch.object(runner.subprocess, "run", return_value=subprocess.CompletedProcess(command, 3)) as execute:
            self.assertEqual(runner.run_entry("core", arguments), 3)
        self.assertEqual(execute.call_args.args[0], command)
        self.assertNotIn("shell", execute.call_args.kwargs)

    def test_raw_streams_stdin_and_nonzero_status_are_not_reinterpreted(self):
        for status in (0, 2, 3, 5):
            with self.subTest(status=status), patch.object(runner.subprocess, "run",
                    return_value=subprocess.CompletedProcess([], status)) as execute:
                self.assertEqual(runner.run_entry("core", ["--version"]), status)
                for intercepted in ("stdin", "stdout", "stderr", "input", "capture_output", "text"):
                    self.assertNotIn(intercepted, execute.call_args.kwargs)
                self.assertFalse(execute.call_args.kwargs["check"])

    def test_invalid_or_excessive_arguments_fail_before_execution(self):
        bad = ("--help", {}, [None], [True], ["a\x00b"], ["\ud800"])
        with patch.object(runner.subprocess, "run") as execute:
            for arguments in bad:
                with self.subTest(arguments=arguments), self.assertRaises(FrameworkError):
                    runner.run_entry("core", arguments)
            for arguments in ([""] * (runner.MAX_ARGUMENTS + 1), ["x" * (runner.MAX_ARGUMENT_BYTES + 1)]):
                with self.assertRaises(FrameworkResourceError):
                    runner.run_entry("core", arguments)
            execute.assert_not_called()

    def test_missing_native_has_no_python_fallback(self):
        with tempfile.TemporaryDirectory() as temporary, io.StringIO() as error:
            with patch.object(runner.subprocess, "run") as execute, redirect_stderr(error):
                code = runner.run_entry("progressive", [], root=Path(temporary))
            self.assertEqual(code, 69)
            execute.assert_not_called()
            report = json.loads(error.getvalue())
            self.assertEqual(report["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(report["semantic_authority"], "NONE")
            self.assertEqual(report["entrypoint_id"], "progressive")

    def test_missing_local_module_cannot_fall_back_to_a_system_package(self):
        with tempfile.TemporaryDirectory() as temporary, io.StringIO() as error:
            with patch.object(runner.subprocess, "run") as execute, redirect_stderr(error):
                self.assertEqual(runner.run_entry("core", ["--version"], root=Path(temporary)), 69)
            execute.assert_not_called()
            self.assertEqual(json.loads(error.getvalue())["reason"], "INSTALLED_MODULE_MISSING")

    def test_os_failure_stays_unavailable_and_does_not_select_another_route(self):
        with io.StringIO() as error, patch.object(runner.subprocess, "run", side_effect=PermissionError) as execute:
            with redirect_stderr(error):
                self.assertEqual(runner.run_entry("core", ["--version"]), 69)
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(json.loads(error.getvalue())["status"], "EXECUTION_UNAVAILABLE")

    def test_native_paths_are_installed_targets_not_argument_controlled(self):
        root = Path(tempfile.gettempdir()) / "nabt-reuse-test"
        command = runner.entry_command("epistemic-native", ["literal-data"], root=root)
        self.assertEqual(command, [str(root / "formal/.lake/build/bin/epistemicMeasurement"), "literal-data"])

    def test_each_python_entry_resolves_in_existing_tree(self):
        for name, entry in runner.describe_entries().items():
            with self.subTest(name=name):
                self.assertTrue(entry["description"])
                self.assertTrue(entry["scope"])
                self.assertNotEqual(entry["module"] is None, entry["native_target"] is None)
                if entry["module"]:
                    relative = Path(*entry["module"].split("."))
                    roots = (runner.ROOT, runner.ROOT / "src")
                    self.assertTrue(any((root / relative.with_suffix(".py")).is_file()
                                        or (root / relative / "__main__.py").is_file() for root in roots))


class ExistingProcessEquivalence(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "POSIX terminating-signal process contract")
    def test_native_terminating_signal_is_preserved_end_to_end(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            native = root / "formal/.lake/build/bin/progressiveUnitProbe"
            native.parent.mkdir(parents=True)
            native.write_text("#!" + sys.executable + "\nimport os, signal\nos.write(1,b'raw-before-signal\\n')\nos.kill(os.getpid(), signal.SIGTERM)\n")
            native.chmod(0o755)
            direct = subprocess.run([str(native)], capture_output=True)
            environment = os.environ | {"PYTHONPATH": os.pathsep.join((str(runner.ROOT / "src"), str(runner.ROOT)))}
            code = "import sys; from pathlib import Path; from tools.entropy_framework.reuse_run import run_entry; sys.exit(run_entry('progressive',[],root=Path(sys.argv[1])))"
            forwarded = subprocess.run([sys.executable, "-B", "-c", code, str(root)],
                                       cwd=runner.ROOT, env=environment, capture_output=True)
            self.assertEqual(direct.returncode, -signal.SIGTERM)
            self.assertEqual((forwarded.returncode, forwarded.stdout, forwarded.stderr),
                             (direct.returncode, direct.stdout, direct.stderr))

    def test_real_core_output_error_and_exit_status_are_byte_identical(self):
        environment = os.environ | {"PYTHONPATH": os.pathsep.join((str(runner.ROOT / "src"), str(runner.ROOT)))}
        for arguments in (["encode", "كَتَبَ"], ["unknown-subcommand"]):
            with self.subTest(arguments=arguments):
                direct = subprocess.run([sys.executable, "-B", "-m", "nabt", *arguments],
                                        cwd=runner.ROOT, env=environment, capture_output=True)
                code = "import sys; from tools.entropy_framework.reuse_run import run_entry; sys.exit(run_entry('core',sys.argv[1:]))"
                forwarded = subprocess.run([sys.executable, "-B", "-c", code, *arguments],
                                           cwd=runner.ROOT, env=environment, capture_output=True)
                self.assertEqual((forwarded.returncode, forwarded.stdout, forwarded.stderr),
                                 (direct.returncode, direct.stdout, direct.stderr))


if __name__ == "__main__":
    unittest.main()
