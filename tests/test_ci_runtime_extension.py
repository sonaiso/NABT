"""The 60-minute runtime gate retains the complete v3 workflow byte for byte."""
from hashlib import sha256
import json
import unittest

from tools import interpretive_links_regression as runner


class RuntimeExtensionTests(unittest.TestCase):
    def test_v4_restores_exact_v3_workflow(self):
        path = ".github/workflows/ci.yml"
        raw = (runner.ROOT / path).read_bytes()
        frozen = json.loads(runner.pinned(runner.INSTALLER_DEPENDENCIES, runner.INSTALLER_DEPENDENCIES_SHA))
        row = next(r for r in frozen["files"] if r["path"] == path)
        restored = runner.restore_v3_workflow(raw)
        self.assertEqual(sha256(restored).hexdigest(), row["sha256"])
        self.assertEqual(len(restored), row["bytes"])
        for changed in (restored, raw.replace(b"timeout-minutes: 60", b"timeout-minutes: 90"), raw + raw):
            with self.assertRaises(ValueError):
                runner.restore_v3_workflow(changed)
        other_job = raw.replace(b"timeout-minutes: 20", b"timeout-minutes: 60")
        self.assertNotEqual(sha256(runner.restore_v3_workflow(other_job)).hexdigest(), row["sha256"])
