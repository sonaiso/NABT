"""Exact source/A116 boundary tests; these do not substitute for native replay."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from nabt import alphabet, codec
from tools.grammar_catalog import opencyc_slice as oc
from tests.test_opencyc_slice import request, row, diagnostic_closure


class BoundaryTests(unittest.TestCase):
    def test_example_digest_and_slice(self):
        path = Path(__file__).resolve().parents[1] / 'examples/relations/opencyc_slice.json'
        payload = json.loads(path.read_text(encoding='utf-8'))['payload']
        compiled = oc.compile_slice(payload['opencyc_slice'])
        self.assertEqual(compiled['status'], 'COMPILED')
        bindings = oc._arabic_bindings(payload['text'], payload['opencyc_slice'])
        self.assertEqual(bindings[0]['restored'], payload['text'])
        self.assertFalse(bindings[0]['semantic_alignment_established'])

    def test_all_cells_reuse_original_codec(self):
        for number in range(116):
            with self.subTest(number=number):
                surface = alphabet.render_word([number])
                p = request(bindings=[{'constant': '#$Dog', 'byte_span': [0, len(surface.encode())]}])
                result = oc._arabic_bindings(surface, p)[0]
                self.assertEqual(result['cells'], [number])
                self.assertEqual(codec.decode_number(int(result['number_hex'], 16)), (number,))
                self.assertFalse(result['semantic_alignment_established'])

    def test_missing_mark_stays_deferred(self):
        p = request(bindings=[{'constant': '#$Dog', 'byte_span': [0, len('كلب'.encode())]}])
        result = oc._arabic_bindings('كلب', p)[0]
        self.assertEqual(result['status'], 'DEFER')
        self.assertNotIn('number_hex', result)
        self.assertEqual(result['residual']['code'], 'MISSING_VOCALIZATION')

    def test_utf8_span_cannot_split_scalar(self):
        p = request(bindings=[{'constant': '#$Dog', 'byte_span': [1, 4]}])
        with self.assertRaises(oc.SliceError): oc._arabic_bindings('كَلْبُ', p)

    def test_source_change_changes_binding_not_meaning_license(self):
        p = request(bindings=[{'constant': '#$Dog', 'byte_span': [0, 4]}])
        a = oc._arabic_bindings('بَ', p)[0]
        b = oc._arabic_bindings('بِ', p)[0]
        self.assertNotEqual(a['number_hex'], b['number_hex'])
        self.assertNotEqual(a['source_sha256'], b['source_sha256'])
        self.assertFalse(a['semantic_alignment_established'])
        self.assertFalse(b['semantic_alignment_established'])

    def test_constraint_report_is_only_obligations(self):
        p = request([row('r', '(arg1Isa #$owns #$Human)')],
                    application={'predicate': '#$owns', 'arguments': ['#$Fido']})
        c = oc.compile_slice(p)
        atoms = [{'predicate': a, 'arguments': list(b), 'positive': pos}
                 for a, b, pos in diagnostic_closure(c['clauses'])]
        result = oc._argument_report(c, {'known': atoms, 'clean_known': atoms})
        self.assertEqual(result['status'], 'DEFER_ARGUMENT_OBLIGATIONS')
        self.assertFalse(result['application_asserted'])
        self.assertFalse(result['arity_completeness_established'])

    def test_request_copy_cannot_rewrite_history(self):
        p = request(); original = deepcopy(p)
        c = oc.compile_slice(p)
        p['withdrawn'].append('g1')
        self.assertEqual(c['request'], original)
        self.assertEqual(c['request_sha256'], oc.digest(original))

    def test_native_tests_in_actual_ci_entry(self):
        root = Path(__file__).resolve().parents[1]
        makefile = (root/'integrations/opencyc_slice.mk').read_text()
        self.assertIn('check io-gateway-native: opencyc-slice-native', makefile)
        self.assertIn('NABT_REQUIRE_OPENCYC_NATIVE=1', makefile)
        self.assertIn('tests.test_opencyc_boundary', makefile)
        self.assertIn('include integrations/opencyc_slice.mk', (root/'GNUmakefile').read_text())


if __name__ == '__main__':
    unittest.main()
