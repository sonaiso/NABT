"""Independent post-open review; never changes the frozen acceptance oracle."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / 'evidence/derivation_surface_v1/independent/freeze.json'
# Observed immutable acceptance freeze committed at 188bfb5 before production.
FREEZE_SHA256 = 'adb95ff92dd3cb401ad4ec7a515a3e850d6344be489a9baf1b9ffa09716288ca'


def sealed_freeze():
    raw = FREEZE.read_bytes()
    if sha256(raw).hexdigest() != FREEZE_SHA256:
        raise AssertionError('The independently frozen acceptance manifest changed')
    return json.loads(raw)


class DerivationSurfaceFreezeReview(unittest.TestCase):
    def test_sealed_manifest_and_all_three_acceptance_files(self):
        freeze = sealed_freeze()
        self.assertEqual(freeze['phase'], 'EXPOSED_PREIMPLEMENTATION_ACCEPTANCE')
        self.assertEqual(len(freeze['files']), 3)
        for row in freeze['files']:
            with self.subTest(path=row['path']):
                raw = (ROOT / row['path']).read_bytes()
                self.assertEqual(len(raw), row['bytes'])
                self.assertEqual(sha256(raw).hexdigest(), row['sha256'])

    def test_existing_owner_sources_and_inventories_preserved(self):
        freeze = sealed_freeze()
        # The recursive transport is the explicitly authorized extension owner;
        # its recorded preimplementation identity is not an immutability gate.
        rows = [row for row in freeze['source_inputs_at_freeze']
                if row['path'] != 'tools/recursive_bridge.py']
        self.assertEqual(len(rows), 8)
        for row in rows:
            with self.subTest(path=row['path']):
                raw = (ROOT / row['path']).read_bytes()
                self.assertEqual(len(raw), row['bytes'])
                self.assertEqual(sha256(raw).hexdigest(), row['sha256'])


class DerivationSurfaceAllocationReview(unittest.TestCase):
    @staticmethod
    def request():
        return {'schema': 'nabt.derivation-surface-request.v1',
                'profile': 'medial-alif-unmarked.v1',
                'span': {'start': 0, 'end': 10}, 'root': 'قول',
                'pattern_id': 'past.I.a', 'ending': 'َ',
                'hypotheses': {'context': 'ordinary', 'origin': 'original'}}

    def test_giant_source_and_identity_stop_before_source_allocation(self):
        from tools import derivation_surface_bridge as bridge
        for text, options in (
            ('x' * 8193, {}), ('قَالَ', {'source_id': 'x' * 97}),
            ('قَالَ', {'scope': 'x' * 97}),
        ):
            with self.subTest(options=options), patch.object(
                    bridge, '_source', side_effect=AssertionError('source allocated before bound')):
                with self.assertRaises(NabtError) as caught:
                    bridge.evaluate_derivation_surface(text, self.request(), **options)
                self.assertEqual((caught.exception.status, caught.exception.code),
                                 ('DEFER', 'RESOURCE_LIMIT'))

    def test_aliased_json_expansion_stops_before_encoding_or_replay(self):
        from tools import derivation_surface_bridge as bridge
        from tools.mantuq_inference import source_fold
        # The same in-memory string occurs 32 times in the wire tree. Counting
        # identities once would undercount its serialized expansion by 31x.
        shared = 'x' * 8192
        report = {'repeated': [shared] * 32}
        with patch.object(source_fold.json_contract, 'wire',
                          side_effect=AssertionError('whole JSON encoded before bound')), \
             patch.object(bridge, 'evaluate_derivation_surface',
                          side_effect=AssertionError('replay started before input bound')):
            result = bridge.verify_derivation_surface(
                report, text='قَالَ', request=self.request())
        self.assertFalse(result['valid'])
        self.assertEqual((result['status'], result['code']), ('DEFER', 'RESOURCE_LIMIT'))


class RecursiveApplicationAllocationReview(unittest.TestCase):
    def test_empty_application_list_still_preflights_source_and_identity(self):
        from tools import recursive_bridge as consumer
        # [] is a valid ordered bounded list. It must not bypass source/label
        # guards just because there is no application occurrence to validate.
        for text, options in (
            ('x' * 8193, {}), ('قَالَ', {'source_id': 'x' * 97}),
            ('قَالَ', {'scope': 'x' * 97}),
        ):
            with self.subTest(options=options), patch.object(
                    consumer, 'read_recursive_source',
                    side_effect=AssertionError('source owner reached before source/identity bound')):
                with self.assertRaises(NabtError) as caught:
                    consumer.read_recursive_applications(text, [], **options)
                self.assertEqual((caught.exception.status, caught.exception.code),
                                 ('DEFER', 'RESOURCE_LIMIT'))

    def test_aggregate_alias_expansion_stops_before_encoder_or_fresh_owners(self):
        from tools import recursive_bridge as consumer
        # 17 appearances of the same 1 MiB UTF-8 value exceed the fixed 16 MiB
        # report law without allocating 17 independent values in this probe.
        shared = '\U0001f642' * 262144
        report = {'repeated': [shared] * 17}
        with patch.object(consumer.json.JSONEncoder, 'iterencode',
                          side_effect=AssertionError('encoder called before cumulative bound')), \
             patch.object(consumer, 'read_recursive_applications',
                          side_effect=AssertionError('fresh owners called before cumulative bound')):
            result = consumer.verify_recursive_applications(report, text='قَالَ', requests=[])
        self.assertFalse(result['valid'])
        self.assertEqual((result['status'], result['code']), ('DEFER', 'RESOURCE_LIMIT'))

    def test_explicit_default_and_abbreviated_cli_controls_cannot_be_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = str(Path(directory) / 'absent')
            for options in (
                ['--profile', 'surface_v1'], ['--profile=surface_v1'],
                ['--index', '0'], ['--kind', 'morphology'],
                ['--disc'], ['--profi', 'surface_v1'],
            ):
                with self.subTest(options=options):
                    run = subprocess.run(
                        [sys.executable, '-B', '-m', 'tools.recursive_bridge',
                         'read-applications', missing, '--applications', missing, *options],
                        cwd=ROOT, capture_output=True, check=False, timeout=10)
                    self.assertEqual(run.returncode, 2)
                    result = json.loads(run.stdout)
                    self.assertEqual((result['status'], result['code']),
                                     ('REJECT', 'INVALID_RECURSIVE_OPTION'))


if __name__ == '__main__':
    unittest.main()
