"""Reuse actual article licenses; preserve source and all lower-stage failures."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import aligned_acquisition as v1, connected_acquisition_v3 as v3
from tools.arabic_training import unit_composition as u
from tools.grammar_catalog import gateway, operations, orchestration

ROOT = Path(__file__).resolve().parents[1]
READY = all((ROOT / 'formal/.lake/build/bin' / name).is_file() for name in (
    'alignedAcquisition', 'connectedAcquisitionV3', 'progressiveUnitProbe',
    'verifiedReading', 'lexicalDenotation'))
if os.environ.get('NABT_REQUIRE_UNIT_NATIVE') == '1' and not READY:
    raise RuntimeError('Build the installed unit, article and interpretation owners')


class DispatchBoundary(unittest.TestCase):
    def test_failure_of_first_owner_is_not_a_fallback_license(self):
        for status in ('INVALID_INPUT', 'RESOURCE_EXHAUSTED', 'VERIFICATION_FAILED',
                       'VERIFICATION_UNAVAILABLE', 'SOURCE_EVIDENCE_UNAVAILABLE'):
            first = {'status': status, 'verified': False}
            with self.subTest(status=status), patch.object(v1, 'read_acquired', return_value=first), \
                    patch.object(v3, 'read_acquired', side_effect=AssertionError('owner bypass')):
                self.assertEqual(u._acquire_host('الْوَلَدُ', 'test', 'wasl'), (first, None))

    def test_snapshot_binds_extra_sources_including_absence_and_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'evidence/cognitive_curriculum_v1').mkdir(parents=True)
            (root / 'evidence/cognitive_curriculum_v1/source_review.json').write_text('{}')
            with patch.object(operations, 'current_catalog', return_value=({'authority':'TEST'}, 'catalog', None, {})):
                before, _ = operations.source_snapshot(root)
                path = root / operations.ACQUISITION_INPUTS[0]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{}')
                after, _ = operations.source_snapshot(root)
                self.assertEqual(after['proof_catalog'], 'catalog')
                self.assertEqual(before['files'][operations.ACQUISITION_INPUTS[0]], 'UNAVAILABLE')
                self.assertNotEqual(operations.digest(before), operations.digest(after))
                path.unlink(); path.symlink_to(root / 'evidence/cognitive_curriculum_v1/source_review.json')
                with self.assertRaisesRegex(ValueError, 'snapshot'):
                    operations.source_snapshot(root)


@unittest.skipUnless(READY, 'requires native article and interpretation owners')
class NativeArticleBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = json.loads((ROOT / 'examples/io_gateway/article_orchestration.json').read_text())

    def compose(self, parts, mode='wasl'):
        return u.execute({'op':'compose', 'parts':parts, 'separators':[''] * (len(parts)-1),
                          'mode':mode, 'source_id':'article_bridge'})['result']

    def test_moon_and_sun_cells_have_independent_explicit_oracles(self):
        # A116: hamza/fatha=112, lam/sukun=91, waw/fatha=104,
        # lam/fatha=88, dal/damma=29; sun ra doubles, written lam is silent.
        for surface, cells in [('الْوَلَدُ', [112,91,104,88,29]),
                               ('الرَّجُلُ', [112,39,36,17,89])]:
            for mode in ('wasl', 'waqf'):
                with self.subTest(surface=surface, mode=mode):
                    expected = cells if mode == 'wasl' else cells[:-1] + [cells[-1] + 2]
                    row = self.compose([surface], mode)['words'][0]
                    self.assertEqual(row['status'], 'CELL_EFFECT_REPLAYED')
                    self.assertEqual(row['acquisition_owner']['acquisition']['words'][0]['cells'], expected)
                    self.assertTrue(row['native_receipt']['sound_shape_accepted'])
                    self.assertEqual(row['prior_acquisition_owner']['status'], 'DEFER')
                    self.assertEqual(row['acquisition_dispatch']['onset'], 'word_initial')
                    self.assertFalse(row['acquisition_dispatch']['connected_speech_established'])

    def test_every_installed_article_surface_reaches_its_existing_native_owner(self):
        packet = json.loads(v3._SOURCES_PATH.read_text())
        surfaces = [s for r in packet['finite_registry']['readings']
                    if r['article_kind'] != 'none' for s in r['input_surfaces']]
        self.assertGreater(len(surfaces), 100)
        for surface in surfaces:
            with self.subTest(surface=surface):
                actual, prior = u._acquire_host(surface, 'article_bridge', 'wasl')
                self.assertIsNotNone(prior)
                self.assertEqual(actual['status'], 'ACQUIRED')
                self.assertTrue(actual['verified'] and actual['shape_verified'])
                self.assertTrue(actual['source_evidence'])
                self.assertEqual(actual['acquisition']['text'], surface)
                self.assertEqual(''.join(p['raw'] for p in actual['acquisition']['pieces']), surface)

    def test_composition_keeps_silent_lam_and_original_piece_boundaries(self):
        r = self.compose(['ا', 'ل', 'رَّجُلُ'])
        row = r['words'][0]
        self.assertTrue(r['source_restored'])
        self.assertEqual([p['text'] for p in r['pieces']], ['ا', 'ل', 'رَّجُلُ'])
        self.assertEqual(row['piece_effects'][1]['cells'], [])
        self.assertTrue(row['native_receipt']['sound_shape_accepted'])
        with self.assertRaisesRegex(ValueError, 'boundary splits'):
            self.compose(['ال', 'ْوَلَدُ'])

    def test_article_appearance_cannot_license_unknown_or_conflicting_words(self):
        for surface in ('الْعَبْ', 'الْكِتَابُ', 'الْوَلَدٌ', 'الولد',
                        'بِالْقَوْمِ', 'بِالْأَسَدِ', 'الْحَيَوَانَ', 'الْمُفْتَرِسَ'):
            with self.subTest(surface=surface):
                row = self.compose([surface])['words'][0]
                self.assertNotIn('native_receipt', row)
                self.assertEqual(row['status'], 'DEFER_EXACT_A116_READING')
        invalid = self.compose(['الْوَلَدََ'])
        self.assertEqual(invalid['status'], 'OWNER_REJECT')
        self.assertEqual(invalid['owner_error']['code'], 'CONFLICTING_MARKS')

    def test_base_words_keep_their_owner_and_unknown_vowels_do_not_trigger_article(self):
        with patch.object(v3, 'read_acquired', side_effect=AssertionError('unrelated owner')):
            self.assertEqual(self.compose(['كَتَبَ'])['words'][0]['status'], 'CELL_EFFECT_REPLAYED')
            self.assertEqual(self.compose(['كتب'])['words'][0]['status'], 'DEFER_EXACT_A116_READING')
            # v1 may represent waw+long-alif; that is not an article/clitic license.
            row = self.compose(['وَالْقَوْمُ'])['words'][0]
            self.assertNotIn('acquisition_dispatch', row)

    def test_missing_native_or_changed_source_has_no_partial_article_license(self):
        with tempfile.TemporaryDirectory() as d, patch.object(v3, '_NATIVE_PATH', Path(d)/'missing'):
            row = self.compose(['الْوَلَدُ'])['words'][0]
            self.assertEqual(row['acquisition_owner']['status'], 'VERIFICATION_UNAVAILABLE')
            self.assertNotIn('native_receipt', row)
        original = v3._read_bounded
        def changed(path, limit):
            data = original(path, limit)
            return data + b' ' if path == v3._SOURCES_PATH else data
        with patch.object(v3, '_read_bounded', side_effect=changed):
            row = self.compose(['الْوَلَدُ'])['words'][0]
            self.assertEqual(row['acquisition_owner']['status'], 'SOURCE_EVIDENCE_UNAVAILABLE')
            self.assertNotIn('native_receipt', row)

    def test_article_resource_exhaustion_stays_a_resource_failure(self):
        with patch.object(v3, '_native', side_effect=OverflowError('native budget')):
            with self.assertRaises(u.ResourceLimit):
                self.compose(['الْوَلَدُ'])

    def test_real_gateway_reaches_concept_and_rejects_edited_trace(self):
        receipt = gateway.run(self.request)
        accepted = gateway.accept_output(receipt, expected_request=self.request)
        self.assertTrue(accepted['valid'], accepted)
        result = receipt['execution']['owner_result']
        self.assertEqual(result['stopped_at'], 'concept')
        self.assertEqual([r['name'] for r in result['dispatch_ledger']], orchestration.table()['layers'])
        self.assertTrue(all(r['closed'] for r in result['dispatch_ledger'][:-1]))
        self.assertFalse(result['world_truth_established'])
        changed = deepcopy(receipt)
        changed['execution']['owner_result']['dispatch_ledger'][0]['closed'] = False
        self.assertFalse(gateway.accept_output(changed, expected_request=self.request)['valid'])

    def test_withdrawal_stops_at_the_actual_next_missing_gate(self):
        p = deepcopy(self.request['payload']); p.pop('lexical_text')
        with patch.object(orchestration, '_syntax', side_effect=AssertionError('morphology bypass')):
            self.assertEqual(orchestration.run(p)['stopped_at'], 'morphology')
        p = deepcopy(self.request['payload']); p.pop('context')
        self.assertEqual(orchestration.run(p)['stopped_at'], 'syntax')

