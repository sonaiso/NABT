"""Spec-authored cases and complete finite-table native conformance; no held-out rows."""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import connected_acquisition_v3 as v3


class ConnectedV3SpecTests(unittest.TestCase):
    def test_literal_connected_moon_cells_and_source(self):
        text = 'قَامَ الْقَوْمُ'
        r = v3.propose_acquisition(text, onset='connected')
        self.assertEqual(r['status'], 'ACQUIRED')
        self.assertEqual([w['cells'] for w in r['acquisition']['words']],
                         [[80, 3, 92], [112, 91, 80, 107, 93]])
        self.assertEqual(r['realization']['phrase_cells'], [80, 3, 92, 91, 80, 107, 93])
        self.assertEqual(r['realization']['words'][1]['cells'][0], 91)
        pieces = r['realization']['pieces']
        self.assertEqual(''.join(p['raw'] for p in pieces), text)
        raw = text.encode()
        for p in pieces:
            self.assertEqual(raw[p['byte_start']:p['byte_end']], p['raw'].encode())
            self.assertEqual(text[p['start']:p['end']], p['raw'])
        elided = [p for p in pieces if p['rule'] == 'ARTICLE_WASL_ELISION']
        self.assertEqual(len(elided), 1)
        self.assertEqual(elided[0]['raw'], 'ا')
        self.assertEqual(elided[0]['cells'], [])
        self.assertEqual(elided[0]['cell_start'], elided[0]['cell_end'])

    def test_sun_is_two_ra_cells_and_original_lam_survives(self):
        r = v3.propose_acquisition('قَامَ الرَّجُلُ', onset='connected')
        self.assertEqual(r['realization']['phrase_cells'], [80, 3, 92, 39, 36, 17, 89])
        lam = [p for p in r['realization']['pieces'] if p['rule'].endswith('ARTICLE_SUN_LAM')]
        self.assertEqual([(p['raw'], p['cells']) for p in lam], [('ل', [])])
        self.assertEqual(v3.propose_acquisition('قَامَ الشَّمْسُ', onset='connected')['status'], 'DEFER')

    def test_initial_connected_and_internal_qat(self):
        one = v3.propose_acquisition('الْقَوْمُ', onset='connected')
        self.assertEqual(one['realization']['phrase_cells'], [112, 91, 80, 107, 93])
        r = v3.propose_acquisition('قَامَ الْأَوْلَادُ', onset='connected')
        self.assertEqual(r['realization']['words'][1]['cells'], [91, 112, 107, 88, 3, 29])
        self.assertEqual(sum(p['rule'] == 'ARTICLE_WASL_ELISION' for p in r['realization']['pieces']), 1)

    def test_literal_aliases_supply_only_installed_reading(self):
        expected = {'قمتُ': [81, 95, 9], 'قمتَ': [81, 95, 8], 'قمتِ': [81, 95, 10],
                    'الولدُ': [112, 91, 104, 88, 29], 'ذاهبٌ': [32, 3, 102, 5, 99],
                    'الولدانِ': [112, 91, 104, 88, 28, 3, 98],
                    'الأولادُ': [112, 91, 112, 107, 88, 3, 29]}
        for text, cells in expected.items():
            with self.subTest(text=text):
                r = v3.propose_acquisition(text)
                self.assertEqual(r['acquisition']['words'][0]['cells'], cells)
                self.assertEqual(r['acquisition']['text'], text)
        for text in ['قمت', 'الولد', 'ذاهب', 'الولدان', 'الأولاد', 'ذاهبون']:
            self.assertEqual(v3.propose_acquisition(text)['status'], 'DEFER')

    def test_contact_and_boundaries_are_debt_not_linguistic_rejection(self):
        for text in ['ذَاهِبٌ الْوَلَدُ', 'قُلْ الْقَوْمُ', 'فِي الْقَوْمُ',
                     ' قَامَ الْقَوْمُ', 'قَامَ  الْقَوْمُ', 'قَامَ\nالْقَوْمُ',
                     'قَامَ الْقَوْمُ.', 'قَامَ\tالْقَوْمُ']:
            with self.subTest(text=text):
                r = v3.propose_acquisition(text, onset='connected')
                self.assertEqual(r['status'], 'DEFER')
                self.assertEqual(r['realization']['phrase_cells'], [])
                self.assertEqual(''.join(p['raw'] for p in r['realization']['pieces']), text)
        self.assertEqual(v3.propose_acquisition('قَامَ الْقَوْمُ.', onset='word_initial')['status'], 'ACQUIRED')

    def test_invalid_marks_precede_finite_or_prefix_rules(self):
        for text in ['الْقَوْمُُ', 'الرََّّجُلُ', 'قُُمْتُ']:
            self.assertEqual(v3.propose_acquisition(text, onset='connected')['status'], 'INVALID_INPUT')
        self.assertEqual(v3.propose_acquisition('قَامَ', onset=True)['status'], 'INVALID_INPUT')
        self.assertEqual(v3.propose_acquisition(' '.join(['قَامَ'] * 33))['status'], 'RESOURCE_EXHAUSTED')

    def test_source_packet_and_original_bytes_are_replayed(self):
        self.assertEqual(v3.source_inventory()['surfaces'], 151)
        original = v3._read_bounded
        def altered(path, limit):
            data = original(path, limit)
            return data + b'x' if path.name == 'qatr.txt' else data
        with patch.object(v3, '_read_bounded', altered):
            self.assertRaises(ValueError, v3.source_inventory)
        with patch.object(v3, 'SOURCE_MANIFEST_SHA256', '0' * 64):
            r = v3.acquire('قَامَ')
            self.assertFalse(r['verified'])
            self.assertEqual(r['status'], 'SOURCE_EVIDENCE_UNAVAILABLE')


class ConnectedV3InstalledPathTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / 'data' / 'original.txt'
        self.dependency = self.root / 'data' / 'dependency.json'
        self.packet = self.root / 'evidence' / 'sourced_acquisition_v3' / 'source_evidence.json'
        self.source.parent.mkdir()
        self.packet.parent.mkdir(parents=True)
        self.source.write_bytes(b'abc')
        self.dependency.write_bytes(b'{}')
        digest = v3.sha256(b'abc').hexdigest()
        document = {
            'schema': 'nabt.sourced-acquisition-source.v3', 'law_id': v3.LAW_ID,
            'alphabet_id': v3.ALPHABET_ID,
            'sources': [{'source_id': 'fixture', 'repository_path': 'data/original.txt',
                         'bytes': 3, 'source_sha256': digest}],
            'passages': [{'source_id': 'fixture', 'source_sha256': digest,
                          'byte_start_0based': 0, 'byte_end_0based_exclusive': 3,
                          'raw_text': 'abc', 'span_sha256': digest}],
            'upstream_dependencies': [{'path': 'data/dependency.json',
                                       'sha256': v3.sha256(b'{}').hexdigest()}],
            'finite_registry': {'readings': v3._READINGS},
        }
        self.packet.write_text(v3._wire(document), encoding='utf-8')
        self.patches = patch.multiple(v3, ROOT=self.root, _SOURCES_PATH=self.packet,
                                      SOURCE_MANIFEST_SHA256=v3.sha256(self.packet.read_bytes()).hexdigest())
        self.patches.start()
        self.addCleanup(self.patches.stop)

    def test_regular_installed_files_pass(self):
        self.assertEqual(v3.source_inventory()['sources'], 1)

    def test_same_bytes_packet_symlink_rejected(self):
        self._same_bytes_symlink_rejected(self.packet)

    def test_same_bytes_original_source_symlink_rejected(self):
        self._same_bytes_symlink_rejected(self.source)

    def test_same_bytes_dependency_symlink_rejected(self):
        self._same_bytes_symlink_rejected(self.dependency)

    def _same_bytes_symlink_rejected(self, path):
        copy = path.with_name(path.name + '.same-bytes')
        copy.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(copy)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            v3.source_inventory()

    def test_symlinked_source_parent_rejected(self):
        actual = self.root / 'actual-data'
        self.source.parent.rename(actual)
        (self.root / 'data').symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            v3.source_inventory()

    def test_noncanonical_and_alternate_packet_paths_rejected(self):
        for relative in ['data/../data/original.txt', 'data//original.txt',
                         './data/original.txt', str(self.source)]:
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, 'noncanonical'):
                v3._installed_path(relative)
        alternate = self.root / 'alternate.json'
        alternate.write_bytes(self.packet.read_bytes())
        with patch.object(v3, '_SOURCES_PATH', alternate), self.assertRaisesRegex(ValueError, 'packet path differs'):
            v3.source_inventory()

    def test_original_source_read_is_bounded_to_declared_bytes(self):
        self.source.write_bytes(b'abc' + b'x' * 4096)
        with patch.object(v3, '_read_bounded', wraps=v3._read_bounded) as reader:
            with self.assertRaisesRegex(ValueError, 'retained source bytes changed'):
                v3.source_inventory()
            self.assertIn(((self.source, 3), {}), reader.call_args_list)
        self.assertEqual(v3._read_bounded(self.source, 3), b'abcx')


@unittest.skipUnless(v3._NATIVE_PATH.is_file(), 'build connectedAcquisitionV3 for native tests')
class ConnectedV3NativeTests(unittest.TestCase):
    def test_all_frozen_surfaces_native_conformance(self):
        # This is an exhaustive implementation comparison over the declared
        # registry, not an independent linguistic accuracy denominator.
        for reading in v3._READINGS:
            for surface in reading['input_surfaces']:
                for ending in ['wasl', 'waqf']:
                    for onset in ['word_initial', 'connected']:
                        for prefix in (['', 'قَامَ '] if onset == 'connected' else ['']):
                            request = dict(text=prefix+surface, source_id='spec-conformance',
                                           revision='1', scope='spec', ending=ending, onset=onset)
                            with self.subTest(surface=surface, ending=ending, onset=onset, prefix=prefix):
                                self.assertEqual(v3._wire(v3._native(request)),
                                                 v3._wire(v3.propose_acquisition(**request)))

    def test_native_boundary_and_malformed_conformance(self):
        for text in ['', ' ', 'قُلْ الْقَوْمُ', 'قَامَ  الْقَوْمُ', 'قَامَ\nالْقَوْمُ',
                     'قَامَ الْقَوْمُ.', 'قَامَ الشَّمْسُ', 'الْقَوْمُُ', 'قمت', 'ذَاهِبٌ الْوَلَدُ']:
            request = dict(text=text, source_id='spec-boundary', revision='1', scope='spec',
                           ending='wasl', onset='connected')
            self.assertEqual(v3._wire(v3._native(request)), v3._wire(v3.propose_acquisition(**request)))

    def test_phrase_shape_and_receipt_binding(self):
        request = dict(text='قَامَ الْقَوْمُ', source_id='original', revision='7', scope='spec',
                       ending='wasl', onset='connected')
        r = v3.read_acquired(**request)
        self.assertTrue(r['verified'])
        self.assertEqual(r['status'], 'ACQUIRED')
        self.assertTrue(r['shape_verified'])
        self.assertEqual(r['shape_handoffs'], [])
        self.assertEqual(r['phrase_shape']['status'], 'SHAPE_LICENSED')
        self.assertTrue(v3.verify_acquired_reading(r, **request))
        for changed in [dict(request, source_id='other'), dict(request, onset='word_initial'),
                        dict(request, ending='waqf'), dict(request, text='قَامَ الْغُلَامُ')]:
            self.assertFalse(v3.verify_acquired_reading(r, **changed))
        forged = deepcopy(r)
        forged['realization']['phrase_cells'][0] = True
        self.assertFalse(v3.verify_acquired_reading(forged, **request))
        forged = deepcopy(r)
        forged['realization']['pieces'][0]['raw'] = 'قَ'
        forged['realization']['pieces'][0]['byte_start'] = True
        self.assertFalse(v3.verify_acquired_reading(forged, **request))

    def test_native_duplicate_keys_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.json'
            path.write_text('{"text":"قَامَ","text":"الْقَوْمُ","source_id":"x","revision":"1",'
                            '"scope":"x","ending":"wasl","onset":"connected"}')
            run = subprocess.run([str(v3._NATIVE_PATH), str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)['status'], 'INVALID_INPUT')


if __name__ == '__main__':
    unittest.main()
