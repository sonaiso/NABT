"""Current inquiry source freeze and preservation of historical runtime pins."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

from tools import (construction_evaluation, discourse_evaluation,
                   inflection_evaluation, morphology_evaluation, word_evaluation)
from tools.text_evaluation.integrity import verify_code_freeze


ROOT = Path(__file__).resolve().parents[1]
# The governor CLI imports its sibling replay helpers as a standalone tool.
sys.path.insert(0, str(ROOT / 'tools'))
try:
    from tools import governor_evaluation
finally:
    sys.path.remove(str(ROOT / 'tools'))

CURRENT = ROOT / 'evidence/rational_inquiry/code_freeze_v2.json'
PRE_FIX = ROOT / 'evidence/rational_inquiry/code_freeze_v1.json'
HISTORICAL = ROOT / 'evidence/constructions/code_freeze_v4.json'
MANIFEST_SHA256 = '49a9c891446e945b74b28489f4abda522473093ada40e503e1fcd5ce99905f4b'
PRE_FIX_SHA256 = 'cefe19d399b19e30175579e427272b790d24eab0e07b54b152e0cd3a45dc5dc4'
HISTORICAL_SHA256 = '42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5'


class InquiryRuntimeFreezeTests(unittest.TestCase):
    def test_current_inventory_includes_public_module_and_preserves_old_package(self):
        self.assertEqual(sha256(CURRENT.read_bytes()).hexdigest(), MANIFEST_SHA256)
        self.assertEqual(sha256(PRE_FIX.read_bytes()).hexdigest(), PRE_FIX_SHA256)
        self.assertEqual(sha256(HISTORICAL.read_bytes()).hexdigest(), HISTORICAL_SHA256)
        current = json.loads(CURRENT.read_text())
        historical = json.loads(HISTORICAL.read_text())
        old = {row['path']: row for row in historical['files']}
        new = {row['path']: row for row in current['files']}
        self.assertEqual(set(new) - set(old), {'src/nabt/rational_inquiry.py'})
        self.assertEqual(set(old) - set(new), set())
        self.assertEqual({path for path in old if old[path] != new[path]},
                         {'pyproject.toml', 'src/nabt/__init__.py', 'src/nabt/cli.py'})
        verify_code_freeze(CURRENT, ROOT)

    def test_all_registered_evaluators_verify_current_bytes_and_archive(self):
        word_evaluation.verify_implementation_freeze('rational_inquiry_v2')
        morphology_evaluation.verify_runtime_freeze(
            morphology_evaluation.snapshot(), 'rational_inquiry_v2')
        inflection_evaluation.runtime_snapshot(CURRENT, ROOT)
        discourse_evaluation.runtime_snapshot(CURRENT, ROOT)
        construction_evaluation.runtime_snapshot(CURRENT, ROOT)
        governor_evaluation.verify_code_freeze(ROOT, CURRENT)

    def test_old_freeze_does_not_authorize_the_new_current_inventory(self):
        checks = (
            lambda: verify_code_freeze(HISTORICAL, ROOT),
            lambda: word_evaluation.verify_implementation_freeze('constructions_v4'),
            lambda: morphology_evaluation.verify_runtime_freeze(
                morphology_evaluation.snapshot(), 'constructions_v4'),
            lambda: inflection_evaluation.runtime_snapshot(HISTORICAL, ROOT),
            lambda: discourse_evaluation.runtime_snapshot(HISTORICAL, ROOT),
            lambda: construction_evaluation.runtime_snapshot(HISTORICAL, ROOT),
            lambda: verify_code_freeze(PRE_FIX, ROOT),
            lambda: word_evaluation.verify_implementation_freeze('rational_inquiry_v1'),
            lambda: morphology_evaluation.verify_runtime_freeze(
                morphology_evaluation.snapshot(), 'rational_inquiry_v1'),
            lambda: inflection_evaluation.runtime_snapshot(PRE_FIX, ROOT),
            lambda: discourse_evaluation.runtime_snapshot(PRE_FIX, ROOT),
            lambda: construction_evaluation.runtime_snapshot(PRE_FIX, ROOT),
        )
        for check in checks:
            with self.subTest(check=check):
                with self.assertRaises(ValueError):
                    check()
        for path in (HISTORICAL, PRE_FIX):
            with self.subTest(governor_freeze=path.name):
                with self.assertRaises(governor_evaluation.oracle.ReplayValidationError):
                    governor_evaluation.verify_code_freeze(ROOT, path)


if __name__ == '__main__':
    unittest.main()
