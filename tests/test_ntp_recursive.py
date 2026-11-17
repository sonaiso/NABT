"""Real gradient, law independence and gateway replay acceptance boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import importlib.util
import unittest
from unittest.mock import patch
from nabt.errors import NabtError
from tests.test_io_gateway import NATIVE

from tools.grammar_catalog import gateway, gateway_routes, ntp
from tools.lexical_training import ntp_recursive as net, train_ntp_recursive as fit


class RecursiveLearning(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('numpy'), 'training-only NumPy required')
    def test_finite_difference_and_gradient_to_bits_cells_and_shared_join(self):
        protocol, rows = fit.inputs()
        report = fit.gradient_check(protocol, rows['train'][0])
        self.assertTrue(report['passed'], report)
        _, grad = fit.loss_grad(fit.initialize(protocol['seed']), rows['train'][0])
        for key in ('bits', 'carrier', 'mark', 'compose'):
            self.assertGreater(float((grad[key] ** 2).sum()), 0, key)

    @unittest.skipUnless(importlib.util.find_spec('numpy'), 'training-only NumPy required')
    def test_replay_and_root_partition(self):
        protocol, rows = fit.inputs()
        roots = [{r['root'] for r in rows[s]} for s in ('train', 'development', 'test')]
        self.assertFalse(roots[0] & (roots[1] | roots[2]))
        self.assertFalse(roots[1] & roots[2])
        learned, _ = fit.fit(protocol, rows['train'])
        from tools.lexical_training.train_apprentice import _difference
        self.assertLessEqual(_difference(net.load(), fit.model(learned, protocol)), 2e-9)

    def test_forward_restores_source_and_model_cannot_change_law(self):
        req = {'text': 'كُتِبَ'}
        original = net.forward(req)
        changed = deepcopy(net.load())
        for matrix in changed['parameters'].values():
            if matrix and isinstance(matrix[0], list):
                for row in matrix:
                    for i in range(len(row)): row[i] = 0.
        with patch.object(net, 'load', return_value=changed):
            other = net.forward(req)
        self.assertEqual(original['cells'], original['restored'])
        self.assertEqual(original['law'], other['law'])
        self.assertEqual(original['algebra'], other['algebra'])
        self.assertNotEqual(original['proposals'], other['proposals'])
        self.assertFalse(original['grammar_certified'])
        self.assertFalse(original['world_truth_established'])

    def test_pinned_model_failure_preserves_law_and_source(self):
        with patch.object(net, 'MODEL', Path('/missing/model')):
            result = net.forward({'text': 'كَتَبَ'})
        self.assertEqual(result['status'], 'MODEL_UNAVAILABLE')
        self.assertEqual(result['cells'], result['restored'])
        self.assertIn('law', result)
        with self.assertRaises(ValueError): net.forward({'text': 'كتب', 'approved': True})
        model = deepcopy(net.load()); model['parameters']['bits'][0][0] = True
        with self.assertRaises(ValueError): net.validate_model(model)

    def test_illegal_initial_sukun_is_never_licensed_by_weights(self):
        result = net.forward({'text': 'كْتَبَ'})
        self.assertFalse(result['law']['licensed'])
        self.assertFalse(result['grammar_certified'])
        self.assertEqual(result['authority'], 'NONE')

    def test_long_exact_number_fits_existing_json_integer_boundary(self):
        from tools.evidence_lifecycle_v1 import _encoded
        result = net.forward({'text': 'كَ' * 64})
        self.assertEqual(net.decode_number(int(result['number_hex'], 16)), tuple(result['cells']))
        self.assertGreater(int(result['number_hex'], 16), 2 ** 53)
        _encoded(result, 1048576, floats=True)

    def test_join_effect_matches_direct_machine_for_every_entry_state(self):
        result = net.forward({'text': 'كَتَبْتُ'})
        effect = result['algebra']['effect']
        machine = net.Machine('wasl')
        for state in range(97):
            direct = machine.analyse(result['cells'], start_state=state)
            self.assertEqual(effect['destinations'][state], direct.final_state)
            self.assertEqual(effect['weights'][state], sum(s.weight_delta for s in direct.trace))
        self.assertTrue(result['algebra']['source_restored'])

    def test_installed_binary_frame_reaches_same_model_and_law(self):
        text = net.forward({'text': 'كُتِبَ'})
        frame = net.forward({'packed_hex': text['packed_hex']})
        for key in ('text', 'cells', 'law', 'algebra', 'proposals', 'restored'):
            self.assertEqual(frame[key], text[key])
        self.assertEqual(frame['input_kind'], 'A116_BIT_FRAME')
        for raw in ('00', text['packed_hex'].upper(), text['packed_hex'] + '00'):
            with self.assertRaises((ValueError, NabtError)):
                net.forward({'packed_hex': raw})


class NTPBoundary(unittest.TestCase):
    @unittest.skipUnless(NATIVE, 'native text/grammar owners required')
    def test_native_think_from_original_text_and_installed_bit_frame(self):
        for req in (ntp.request('think', {'text': 'زيد حكيم'}),
                    ntp.request('think', {'packed_hex': net.pack_cells(net.parse_word('كَتَبَ')).hex()})):
            result = gateway.run(req)
            self.assertEqual(result['status'], 'EXECUTED', result)
            self.assertEqual(result['execution']['owner_result']['owner_operation'], 'text.read')
            self.assertTrue(gateway.accept_output(result, expected_request=req)['valid'])

    def test_dispatch_all_legacy_adapters_through_ntp(self):
        with patch.object(ntp, 'execute', return_value={'observed': True}) as dispatch:
            self.assertEqual(gateway_routes.execute('grammar.search', {'query': 'اسم'}), {'observed': True})
        dispatch.assert_called_once_with('grammar.search', {'query': 'اسم'}, inside_worker=False)

    def test_nested_routes_paths_and_authority_injection_rejected(self):
        for p in ({'operation': 'ntp', 'input': {}}, {'operation': '__import__', 'input': {}},
                  {'operation': 'forward', 'input': {'text': 'كَتَبَ', 'model_path': '/tmp/m'}},
                  {'operation': 'forward', 'input': {'text': 'كَتَبَ'}, 'approved': True}):
            with self.assertRaises(ValueError): gateway_routes.validate('ntp', p)

    def test_owner_output_preserved_and_neural_withdrawal_cannot_certify(self):
        owner = {'status': 'DEFER', 'missing': ['source_witness'], 'alternatives': [1, 2]}
        with patch.object(gateway_routes, '_execute_owner', return_value=owner), \
             patch.object(net, 'load', side_effect=OSError('withdrawn')):
            result = ntp.execute('ntp', {'operation': 'text.read', 'input': {'text': 'كَتَبَ'}})
        self.assertEqual(result['owner_result'], owner)
        self.assertEqual(result['recursive_observations'][0]['observation']['status'], 'MODEL_UNAVAILABLE')
        self.assertFalse(result['neural_selection_permitted'])

    def test_thinking_from_bits_uses_original_text_owner_without_licensing_from_score(self):
        packed = net.pack_cells(net.parse_word('كُتِبَ')).hex()
        p = ntp.validate({'operation': 'think', 'input': {'packed_hex': packed}})
        owner_result = {'status': 'DEFER', 'open_obligations': ['lexical_witness']}
        with patch.object(gateway_routes, '_execute_owner', return_value=owner_result) as owner:
            result = ntp.execute('ntp', p, inside_worker=True)
        owner.assert_called_once_with('text.read', {'text': 'كُتِبَ'}, inside_worker=True)
        self.assertEqual(result['owner_result'], owner_result)
        self.assertEqual(result['representation_source'], 'EXACT_DECODED_A116_BIT_FRAME')
        self.assertFalse(result['world_truth_established'])

    def test_actual_gateway_replay_and_forgery_rejection(self):
        req = ntp.request('forward', {'text': 'كَتَبَ'})
        result = gateway.run(req)
        self.assertEqual(result['status'], 'EXECUTED', result)
        self.assertTrue(gateway.accept_output(result, expected_request=req)['valid'])
        bad = deepcopy(result)
        bad['execution']['owner_result']['grammar_certified'] = True
        self.assertFalse(gateway.accept_output(bad, expected_request=req)['valid'])
        self.assertFalse(gateway.accept_output(result['execution']['owner_result'], expected_request=req)['valid'])
        other = ntp.request('forward', {'text': 'كُتِبَ'})
        self.assertFalse(gateway.accept_output(result, expected_request=other)['valid'])


if __name__ == '__main__':
    unittest.main()
