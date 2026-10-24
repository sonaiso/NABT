"""CLI path regression; the stand-in deliberately fails, never proves Lean."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class SemanticAuditDriverPathTests(unittest.TestCase):
    def test_driver_paths_resolve_from_invocation_directory(self):
        script = Path(__file__).resolve().parents[1] / "tools/build_semantic_audit.py"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, invocation = root / "project", root / "invocation"
            (project / "tools").mkdir(parents=True)
            (project / "formal").mkdir()
            (invocation / "bin").mkdir(parents=True)
            shutil.copyfile(script, project / "tools/build_semantic_audit.py")
            (project / "formal/Nabt.lean").write_text("-- orchestration-only fixture\n")
            marker = root / "invoked.json"
            driver = invocation / "bin/lean-driver"
            driver.write_text(
                f"#!{sys.executable}\nimport json, os, sys\n"
                f"open({str(marker)!r}, 'w').write(json.dumps({{'cwd': os.getcwd(), 'argv': sys.argv}}))\n"
                "sys.exit(17)  # deliberate compiler failure, not a successful kernel build\n")
            driver.chmod(0o755)
            for argument in ("bin/lean-driver", str(driver)):
                with self.subTest(driver=argument):
                    marker.unlink(missing_ok=True)
                    result = subprocess.run(
                        [sys.executable, str(project / "tools/build_semantic_audit.py"),
                         "--driver", argument, "--toolchain", str(root / "unused-toolchain"),
                         "--output", str(root / "output")], cwd=invocation,
                        capture_output=True, text=True, timeout=15)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertTrue(marker.exists(), result.stderr)
                    receipt = json.loads(marker.read_text())
                    self.assertEqual(Path(receipt["cwd"]), project / "formal")
                    self.assertEqual(Path(receipt["argv"][0]), driver)
                    self.assertEqual(Path(receipt["argv"][-1]), project / "formal/Nabt.lean")
                    record = json.loads((root / "output/kernel.json").read_text())
                    self.assertEqual(record[0]["exit_code"], 17)


if __name__ == "__main__":
    unittest.main()
