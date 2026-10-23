"""Exercise preliminary replay failures at the installed CLI boundary."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.cli import main, parser, run
from nabt.errors import NabtError


PACKAGE = Path(__file__).resolve().parents[1] / "src" / "nabt"
LAUNCH = (
    "import sys; from pathlib import Path; "
    "sys.path.insert(0, sys.argv[1]); import nabt.cli; "
    "assert Path(nabt.cli.__file__).resolve().parent == Path(sys.argv[1]).resolve() / 'nabt'; "
    "raise SystemExit(nabt.cli.main(['pilot']))"
)


class InstalledPilotContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.installed = self.root / "installed"
        shutil.copytree(PACKAGE, self.installed / "nabt",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def invoke_installed(self):
        # Isolated Python ignores PYTHONPATH and user-site imports. A package
        # origin assertion ensures this runs the temporary installation copy.
        return subprocess.run(
            [sys.executable, "-I", "-B", "-c", LAUNCH, str(self.installed)],
            cwd=self.root, capture_output=True, text=True, check=False,
        )

    def assert_contract_failure(self, completed):
        self.assertEqual(completed.returncode, 3, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(json.loads(completed.stderr), {
            "status": "DEFER",
            "code": "INSTALLED_CONTRACT_FAILED",
            "message": "Installed source contract could not be replayed",
        })

    def test_real_source_corruption_in_an_isolated_package_is_structured(self):
        pristine = self.invoke_installed()
        self.assertEqual((pristine.returncode, pristine.stderr), (0, ""))
        self.assertEqual(json.loads(pristine.stdout)["run_status"], "COMPLETED")
        relative = Path("data/source_evidence/qatr.txt")
        original = hashlib.sha256((PACKAGE / relative).read_bytes()).digest()
        fixture = self.installed / "nabt" / relative
        fixture.write_bytes(fixture.read_bytes() + b"\n")
        self.assert_contract_failure(self.invoke_installed())
        # The authoritative checkout fixture is untouched by the test.
        self.assertEqual(hashlib.sha256((PACKAGE / relative).read_bytes()).digest(), original)

    def test_missing_installed_replay_context_is_structured(self):
        # Sources still match their pins; this damages the copied replay table
        # so observed_records raises a real KeyError after construction.
        module = self.installed / "nabt/learning/arabic_six_nouns.py"
        module.write_bytes(module.read_bytes() + b"\n_CONTEXTS = {}\n")
        self.assert_contract_failure(self.invoke_installed())


class PilotFailureClassificationTests(unittest.TestCase):
    def test_existing_nabt_error_is_not_wrapped_during_record_replay(self):
        for status, exit_code in (("REJECT", 2), ("DEFER", 3)):
            error = NabtError("REPLAY_CLASSIFIED_FAILURE", "An already classified failure",
                              status=status, details={"phase": "observed_records"})
            with self.subTest(status=status):
                with patch("nabt.learning.SixNounPilot.observed_records", side_effect=error):
                    with self.assertRaises(NabtError) as raised:
                        run(parser().parse_args(["pilot"]))
                    self.assertIs(raised.exception, error)
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        actual_exit = main(["pilot"])
                self.assertEqual((actual_exit, stdout.getvalue()), (exit_code, ""))
                self.assertEqual(json.loads(stderr.getvalue()), error.as_dict())


if __name__ == "__main__":
    unittest.main()
