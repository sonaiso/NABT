"""All registered boundaries, plus missing/conditional guard mutations."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import interface_migration_audit as migration

ROOT = Path(__file__).resolve().parents[1]


class InterfaceMigrationAuditTests(unittest.TestCase):
    def test_core_only_import_and_all_admission_denials_need_no_neural_dependencies(self):
        # -I ignores environment paths; -S disables site-packages. The finder
        # additionally fails on any attempted optional import, even a caught
        # ImportError. Thus this checks import order, not merely missing wheels.
        script = r'''
import importlib.abc
import json
from pathlib import Path
import sys
from unittest.mock import patch
root = Path(sys.argv[1])
sys.path[:0] = [str(root / "src"), str(root)]
attempts = []
optional = {"tools.arabic_training.experiment", "tools.arabic_training.model",
            "tools.arabic_training.model_v2"}
class NoNeuralImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "numpy"} or fullname in optional:
            attempts.append(fullname)
            raise AssertionError("optional dependency loaded before denial: " + fullname)
sys.meta_path.insert(0, NoNeuralImports())
from nabt import foundation
from nabt.errors import NabtError
from tools.arabic_training.proposal import propose, load_bundle
denial = NabtError("NO_NEURAL_FOUNDATION_DENIAL", "denied", status="DEFER")
with patch.object(foundation, "require_foundation", side_effect=denial) as gate:
    try:
        propose(None, None, None, None)
    except NabtError as error:
        assert error is denial
    else:
        raise AssertionError("proposal escaped its installed foundation")
    gate.assert_called_once_with("tools.arabic_training.proposal.propose")
from tools.interface_migration_audit import audit
report = audit(root)
assert report["ok"], report["failures"]
assert report["denied_before_body_count"] == report["runtime_boundary_count"]
assert attempts == [], attempts
assert "torch" not in sys.modules and "numpy" not in sys.modules
print(json.dumps({"ok": report["ok"], "optional_import_attempts": attempts,
                  "denied_before_body_count": report["denied_before_body_count"],
                  "runtime_boundary_count": report["runtime_boundary_count"]}))
'''
        completed = subprocess.run([sys.executable, "-I", "-S", "-c", script, str(ROOT)],
                                   capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["optional_import_attempts"], [])
        self.assertEqual(report["denied_before_body_count"], report["runtime_boundary_count"])

    def test_every_registered_runtime_admission_is_denied_before_body(self):
        report = migration.audit()
        self.assertTrue(report["ok"], report["failures"])
        self.assertEqual(report["denied_before_body_count"], report["runtime_boundary_count"])
        self.assertEqual(report["runtime_boundary_count"] + report["separate_primitive_count"],
                         report["surface_count"])
        self.assertFalse(report["all_results_kernel_proved"])
        self.assertFalse(report["whole_arabic_complete"])

    def test_disappearing_or_bypassed_live_guard_is_detected(self):
        registry = json.loads((ROOT / migration.architecture.REGISTRY).read_text())
        row = next(row for row in registry["surfaces"] if row["guard_kind"] == "runtime_foundation")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / migration.architecture.REGISTRY
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({"surfaces": [row]}))
            source = root / row["path"]
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes((ROOT / row["path"]).read_bytes())
            with patch.object(migration, "_callable", return_value=lambda: {"native_checked": True}):
                report = migration.audit(root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["failures"], [row["id"]])
            self.assertEqual(report["denied_before_body_count"], 0)

    def test_empty_registry_is_not_vacuous_boundary_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / migration.architecture.REGISTRY
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({"surfaces": []}))
            report = migration.audit(root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["surface_count"], 0)


if __name__ == "__main__":
    unittest.main()
