"""Continuation-boundary checks; no runtime predictions or old gold edits."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G = load('reviewed_holdout_continuation_v4', ROOT / 'tools/arabic_coverage_postreview_v4.py')
H = load('legacy_holdout_summary_fixture', ROOT / 'tests/test_arabic_coverage_postreview_gate.py')


class HoldoutContinuationV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(G.PREVIOUS_ARCHIVE) as archive:
            cls.raw = archive.read(G.PREVIOUS_RAW_MEMBER)

    def test_previous_complete_public_trace_is_accepted_without_claiming_improvement(self):
        result = G.previous_trace(self.raw)
        self.assertTrue(result['all_raw_bytes_equal'])
        self.assertEqual(result['raw_record_count'], 203)
        self.assertEqual(result['unique_call_count'], 203)
        self.assertEqual(result['ignored_public_fields'], [])
        self.assertFalse(result['prediction_success_or_accuracy_increase_claimed'])

    def test_changed_public_field_missing_call_or_extra_bytes_cannot_keep_the_old_success(self):
        records = [json.loads(line) for line in self.raw.splitlines()]
        changed = deepcopy(records)
        changed[1]['value']['source_id'] = 'another_source'
        extra_field = deepcopy(records)
        extra_field[0]['value']['ignored_runtime_note'] = 'must_not_be_ignored'
        variants = [b''.join(G.wire(x) + b'\n' for x in changed),
                    b''.join(G.wire(x) + b'\n' for x in extra_field),
                    b''.join(G.wire(x) + b'\n' for x in records[:-1]), self.raw + b'\n']
        for index, raw in enumerate(variants):
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'public payloads differ'):
                G.previous_trace(raw)

    def test_runtime_v2_pin_does_not_replace_or_relabel_the_historical_freeze(self):
        old = ROOT / 'evidence/arabic_completion_v3/code_freeze_v1.json'
        new = ROOT / 'evidence/arabic_completion_v3/code_freeze_v2.json'
        self.assertEqual(sha256(old.read_bytes()).hexdigest(), G.PREVIOUS_RUNTIME_SHA256)
        self.assertEqual(sha256(new.read_bytes()).hexdigest(), G.RUNTIME_SHA256)
        self.assertNotEqual(G.PREVIOUS_RUNTIME_SHA256, G.RUNTIME_SHA256)
        manifest = json.loads(new.read_bytes())
        self.assertEqual(len(manifest['files']), 80)
        self.assertEqual(manifest['snapshot_sha256'], G.RUNTIME_SNAPSHOT_SHA256)
        self.assertEqual(manifest['archive_sha256'], G.RUNTIME_ARCHIVE_SHA256)

    def test_historical_gate_and_frozen_producer_stay_byte_exact(self):
        pins = {
            'tools/arabic_coverage_postreview_v3.py': '8b92416cea17cb8f4831c7053ceec838559cd06f6525258819c9fda092ba5ba1',
            'tools/arabic_coverage_holdout_v1.py': 'c30a4dda7e0f61362a7fdf774d77fc343486cb58ce9c8017c2c1355bec8efae5',
            'tools/arabic_coverage_holdout_v2.py': '0c04cf6806f9f0210a84084eed1e47bafb3e4bca9fb613e8860a120c9f0dfbb4',
            'evidence/arabic_coverage/holdout_v2/freeze.json': G.MATERIAL_SHA256,
        }
        for path, expected in pins.items():
            with self.subTest(path=path):
                self.assertEqual(sha256((ROOT / path).read_bytes()).hexdigest(), expected)

    def test_h18_exception_cannot_absorb_a_new_failure_in_the_continuation(self):
        result, material, runtime = H.summary_example()
        self.assertEqual(G.validate_measurement_summary(result, material, runtime), result['unsafe_acceptances'])
        result['cases'][0]['checks'].append({'name': 'new_source_premise_failure', 'pass': False})
        result['cases'][0]['passed'] = False
        with self.assertRaisesRegex(ValueError, 'only the demonstrated H18'):
            G.validate_measurement_summary(result, material, runtime)


if __name__ == '__main__':
    unittest.main()
