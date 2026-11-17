"""Keep both scoped-report and existing genus inputs after additive integration."""
from copy import deepcopy
from hashlib import sha256
import unittest

from tools.grammar_catalog import gateway_routes, relational


def request():
    text = 'فَتَحَ الْحَارِسُ الْبَابَ.'
    return {'text': text, 'source_id': 'independent_fixture',
        'genus_chains': {'ledger': '', 'root': 'موجود', 'parent': 'موجود', 'entity': 'الباب'},
        'report_model': {'event': 'opening_1', 'speaker': 'reporter', 'addressee': 'listener',
            'source_id': 'independent_fixture', 'source_sha256': sha256(text.encode()).hexdigest(),
            'worlds': [], 'witnesses': []}}


class RelationalInputRegression(unittest.TestCase):
    def test_both_owner_inputs_survive_validation_and_are_independently_copied(self):
        original = request()
        checked = relational.validate(original)
        routed = gateway_routes.validate('relations.analyze', original)
        self.assertEqual(checked, original)
        self.assertEqual(routed, original)
        checked['genus_chains']['entity'] = 'آخر'
        routed['report_model']['worlds'].append({})
        self.assertEqual(original, request())

    def test_old_and_new_owner_validation_both_run(self):
        for field in ('genus_chains', 'report_model'):
            invalid = request()
            invalid[field] = {}
            with self.subTest(field=field), self.assertRaises(ValueError):
                relational.validate(invalid)
            with self.subTest(route_field=field), self.assertRaises(ValueError):
                gateway_routes.validate('relations.analyze', invalid)

    def test_unknown_fields_are_not_admitted_by_the_union(self):
        for field in ('approved', 'native_checked', 'checker', 'rank', 'extra'):
            invalid = request()
            invalid[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                gateway_routes.validate('relations.analyze', invalid)

    def test_boolean_prior_mass_is_not_an_integer_weight(self):
        invalid = request()
        invalid['report_model']['worlds'] = [{'id': 'w', 'text': invalid['text'], 'mass': True}]
        with self.assertRaises(ValueError):
            gateway_routes.validate('relations.analyze', invalid)

    def test_prior_optional_inputs_remain_available(self):
        required, optional = gateway_routes.ROUTES['relations.analyze'][1:]
        self.assertIn('text', required)
        self.assertEqual(len(optional), len(set(optional)))
        self.assertTrue({'genus_chains', 'valency_context', 'licensed_speech', 'report_model',
                         'root_sense', 'inference', 'temporal', 'question_chain'} <= set(optional))


if __name__ == '__main__': unittest.main()
