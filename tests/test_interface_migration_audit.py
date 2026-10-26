"""All registered boundaries, plus missing/conditional guard mutations."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import interface_migration_audit as migration

ROOT = Path(__file__).resolve().parents[1]


class InterfaceMigrationAuditTests(unittest.TestCase):
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
