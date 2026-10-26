"""Native control authority is narrower than acquisition or Arabic acceptance."""
from copy import deepcopy
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from nabt import classical_certified as certified
from nabt import classical_hamza, classical_weak, classical_boundary_affixes
from nabt import foundation
from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[1]
BINARIES = [ROOT / 'formal/.lake/build/bin' / name for name in certified._EXPORTS.values()]
HAMZA = {'root': ['ء', 'ك', 'ل'], 'profile': 'all_attested'}


class CertifiedBoundaryTests(unittest.TestCase):
    def test_public_api_cannot_accept_authority_or_checker_arguments(self):
        for field in ('root', 'native_checked', 'proof', 'checker', 'executable', 'receipt', 'ledger'):
            with self.subTest(field=field), self.assertRaises(TypeError):
                certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', HAMZA, **{field: True})

    def test_foundation_denial_precedes_evaluation(self):
        error = NabtError('TEST_DENIED', 'No installed authority', status='DEFER')
        with patch.object(foundation, 'require_foundation', side_effect=error), \
                patch.object(certified.classical_laws, 'evaluate') as evaluator:
            with self.assertRaises(NabtError):
                certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', HAMZA)
            evaluator.assert_not_called()

    def test_source_failure_cannot_be_replaced_by_native_export(self):
        error = NabtError('INSTALLED_CONTRACT_FAILED', 'source changed', status='DEFER')
        with patch.object(certified.classical_laws, 'replay_inventory', side_effect=error), \
                patch.object(certified, '_native_export') as native:
            with self.assertRaises(NabtError):
                certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', HAMZA)
            native.assert_not_called()

    def test_missing_or_failed_native_never_leaves_a_proof(self):
        for error in (FileNotFoundError('absent'), ValueError('wrong export'),
                      OverflowError('large'), subprocess.TimeoutExpired('export', 60)):
            with self.subTest(error=type(error).__name__), \
                    patch.object(certified, '_native_export', side_effect=error):
                result = certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', HAMZA)
                self.assertFalse(result['native_checked'])
                self.assertFalse(result['bounded_rule_checked'])
                self.assertFalse(result['claims'])
                self.assertFalse(result['grants_language_license'])

    def test_duplicate_and_nonfinite_native_json_rejected(self):
        for value in ('{"x":1,"x":2}', '{"x":1,"\\u0078":2}', '{"x":NaN}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                certified._json(value)


@unittest.skipUnless(all(path.is_file() for path in BINARIES), 'four native classical exports required')
class CertifiedNativeTests(unittest.TestCase):
    def test_all_24_rule_ids_have_an_exact_native_control_path(self):
        cases = {}
        for row in classical_weak.source_examples():
            cases.setdefault(row['rule_id'], row['frame'])
        for row in classical_hamza.finite_export_rows():
            cases.setdefault(row['rule_id'], row['frame'])
        for row in classical_boundary_affixes.finite_export_rows():
            cases.setdefault(row['rule_id'], row['frame'])
        for rule, context, last, suffix in (
                ('GEM-VOWELED-FINAL', 'ordinary', 'a', []),
                ('GEM-JUSSIVE-VARIANTS', 'command', 's', []),
                ('GEM-FEMININE-SUFFIX', 'feminine', 's', [['ن', 'a']]),
                ('GEM-EXCLAMATION', 'exclamation', 's', [])):
            cases[rule] = {'prefix': [['ر', 'a']], 'first': ['د', 'a'],
                'second': ['د', last], 'suffix': suffix, 'context': context, 'dialect': 'hijaz'}
        cases['GEM-EXCLAMATION'].update(prefix=[['أ', 'a'], ['ح', 's']],
                                       first=['ب', 'i'], second=['ب', 's'])
        cases['ASSIM-NUN-B-BLOCKED-TEXT'] = {
            'left': ['ن', 's'], 'right': ['ب', 'a'], 'connection': 'word_boundary_wasl'}
        self.assertEqual(len(cases), 24)
        for rule, frame in cases.items():
            with self.subTest(rule=rule):
                result = certified.evaluate_certified(rule, frame)
                self.assertTrue(result['native_checked'])
                self.assertTrue(result['bounded_rule_checked'], result.get('residuals'))
                self.assertEqual(len(result['claims']), 1)
                self.assertFalse(result['strict_language_accepted'])
                self.assertFalse(result['source_to_control_proved'])
                self.assertFalse(result['whole_arabic_complete'])
                self.assertEqual(result['binding']['frame_sha256'], certified._digest(frame))
                self.assertEqual(result['binding']['parent_receipt_sha256'],
                                 certified._digest(result['parent_receipt']))

    def test_lexical_variant_retained_and_same_parent_bound(self):
        result = certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', HAMZA)
        row = result['claims'][0]['equation_result']
        self.assertEqual(row['operations'], ['short_command', 'full_dialect_command'])
        self.assertEqual(row['outputs'], [['ك', 'ل'], ['ء', 'و', 'ك', 'ل']])
        self.assertEqual(result['claims'][0]['binding']['source_passages_sha256'],
                         certified._digest(result['parent_receipt']['result']['source_spans']))
        self.assertFalse(result['a116_frame_projection']['native_projection_checked'])
        self.assertEqual(result['a116_frame_projection']['status'], 'BRIDGE_REQUIRED')

    def test_changed_profile_changes_binding_and_does_not_borrow_alternatives(self):
        a = certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', HAMZA)
        b = certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', {**HAMZA, 'profile': 'named_common'})
        self.assertNotEqual(a['binding']['frame_sha256'], b['binding']['frame_sha256'])
        self.assertNotEqual(a['claims'][0]['binding']['native_row_sha256'],
                            b['claims'][0]['binding']['native_row_sha256'])
        self.assertEqual(b['claims'][0]['equation_result']['operations'], ['short_command'])

    def test_finite_domain_does_not_claim_an_unexported_hamza_frame(self):
        frame = {'prefix': ['ر', 'ج'], 'glide': 'waw', 'alif_origin': 'added', 'suffix': []}
        result = certified.evaluate_certified('HAMZA-FINAL-LONG', frame)
        self.assertTrue(result['parent_receipt']['result']['alternatives'])
        self.assertTrue(result['native_checked'])
        self.assertFalse(result['bounded_rule_checked'])
        self.assertFalse(result['claims'])
        self.assertIn('FRAME_OUTSIDE_EXACT_NATIVE_EXPORT_DOMAIN', result['residuals'])

    def test_empty_native_action_set_is_not_an_arabic_rejection(self):
        result = certified.evaluate_certified('HAMZA-LEXICAL-COMMAND',
            {'root': ['ء', 'س', 'ر'], 'profile': 'all_attested'})
        self.assertTrue(result['bounded_rule_checked'])
        self.assertEqual(result['claims'][0]['equation_result']['operations'], [])
        self.assertEqual(result['status'], 'CHECKED_CONDITIONAL_CONTROL')
        self.assertFalse(result['grants_language_license'])

    def test_control_label_does_not_override_an_unmet_input_shape(self):
        frame = {'prefix': [['ر', 'a']], 'first': ['د', 'a'], 'second': ['د', 's'],
                 'suffix': [], 'context': 'exclamation', 'dialect': 'hijaz'}
        result = certified.evaluate_certified('GEM-EXCLAMATION', frame)
        self.assertTrue(result['native_checked'])
        self.assertFalse(result['claims'])
        self.assertFalse(result['bounded_rule_checked'])
        self.assertFalse(result['grants_language_license'])

    def test_supplied_cell_projection_does_not_turn_into_observed_source(self):
        example = classical_weak.source_examples()[0]
        result = certified.evaluate_certified(example['rule_id'], example['frame'])
        projection = result['a116_frame_projection']
        self.assertEqual(projection['status'], 'COMPLETE')
        self.assertEqual(projection['receipt']['source']['text'], 'يَوْعِدُ')
        self.assertFalse(projection['observed_text'])
        self.assertFalse(projection['native_projection_checked'])
        self.assertIn('CONTROL_ABSTRACTION_NOT_KERNEL_PROVED', result['claims'][0]['unresolved_premises'])

    def test_mutated_native_export_cannot_authorize_a_selected_row(self):
        actual, binary = certified._native_export('classical_hamza')
        for mutate in ('remove', 'duplicate', 'alter', 'extra'):
            changed = deepcopy(actual)
            if mutate == 'remove':
                changed['rows'] = changed['rows'][:-1]
            elif mutate == 'duplicate':
                changed['rows'].append(deepcopy(changed['rows'][0]))
            elif mutate == 'alter':
                changed['rows'][0]['operations'] = []
            else:
                changed['native_checked'] = True
            with self.subTest(mutate=mutate), \
                    patch.object(certified, '_native_export', return_value=(changed, binary)):
                result = certified.evaluate_certified('HAMZA-LEXICAL-COMMAND', HAMZA)
                self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')
                self.assertFalse(result['native_checked'])
                self.assertFalse(result['claims'])


if __name__ == '__main__':
    unittest.main()
