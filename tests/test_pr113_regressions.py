"""Independent counterexamples for PR #113; no native result is mocked."""
from copy import deepcopy
from hashlib import sha256
import json
from unittest import TestCase, skipUnless

from tests.test_io_gateway import NATIVE
from tools.grammar_catalog import derived_event_roles as d, event_scene as scene
from tools.grammar_catalog import gateway, relational

RAIN = 'أَنْبَتَ المَطَرُ العُشْبَ لِيَنْفَعَ'
PUNCTUATION = ('شرب الولد، الشاي', 'شرب الشايَ الولدُ؟')
ALTERNATIVES = ['لام العاقبة', 'قصد مسبب آخر']


def only_candidate(text):
    report = d.analyze(text, 'regression-source')
    (candidate,) = report['candidates']
    return report, candidate


def with_lesson(lesson, text, root='نبت', form='IV'):
    verb, *tail = d.exact_terms(text)
    return d.analyze_form(lesson, text, verb, root, form, tail)


class PurposeRegression(TestCase):
    def test_rain_blocks_only_mentioned_intender_and_retains_untested(self):
        report, candidate = only_candidate(RAIN)
        (row,) = candidate['readings']
        self.assertEqual(candidate['status'], 'BLOCKED')
        self.assertEqual(row['bindings']['causer']['status'], 'LICENSED')
        self.assertEqual(row['purpose']['intent']['status'], 'BLOCKED')
        self.assertIn({'kind': 'ظاهرة طبيعية', 'value': False}, row['purpose']['intent']['witnesses'])
        self.assertEqual(row['purpose']['other_readings_open'], ALTERNATIVES)
        self.assertFalse(row['purpose']['realized'])
        self.assertFalse(report['world_occurrence_established'])
        self.assertFalse(report['empirical_causality_established'])
        self.assertEqual(report['source_id'], 'regression-source')
        self.assertEqual(report['source_sha256'], sha256(RAIN.encode()).hexdigest())
        cue = row['purpose']['cue']
        a, b = cue['utf8_span']
        self.assertEqual(RAIN.encode()[a:b].decode(), 'لِيَنْفَعَ')
        self.assertEqual(candidate['decision_chain'][-1]['status'], 'BLOCKED')

    def test_licensed_intention_and_plain_causer_remain_accepted(self):
        _, candidate = only_candidate('أَنْبَتَ الرَّجُلُ العُشْبَ لِيَنْفَعَ')
        (row,) = candidate['readings']
        self.assertEqual(candidate['status'], 'LICENSED')
        self.assertEqual(row['purpose']['intent']['status'], 'LICENSED')
        self.assertEqual(row['purpose']['other_readings_open'], [])
        self.assertFalse(row['purpose']['realized'])
        _, plain = only_candidate('أَنْبَتَ المَطَرُ العُشْبَ')
        self.assertEqual(plain['status'], 'LICENSED')
        self.assertIsNone(plain['readings'][0]['purpose'])

    def test_unknown_intention_is_unresolved_and_alternatives_untested(self):
        _, candidate = only_candidate('أَنْبَتَ الغَرِيبُ العُشْبَ لِيَنْفَعَ')
        purpose = candidate['readings'][0]['purpose']
        self.assertEqual(purpose['intent']['status'], 'UNRESOLVED')
        self.assertEqual(purpose['intent']['witnesses'], [])
        self.assertEqual(purpose['other_readings_open'], ALTERNATIVES)
        self.assertEqual(candidate['status'], 'UNRESOLVED')

    def test_conflicting_intention_does_not_close_alternatives(self):
        spec = json.loads(d.DATA.read_bytes())
        spec['properties']['رجل'] = {'ذو إرادة': False}
        lesson = d.Lesson(json.dumps(spec).encode(), d.lesson().previous, d.sources())
        candidate = with_lesson(lesson, 'أَنْبَتَ الرَّجُلُ العُشْبَ لِيَنْفَعَ')
        purpose = candidate['readings'][0]['purpose']
        self.assertEqual(purpose['intent']['status'], 'CONFLICT')
        self.assertEqual({w['value'] for w in purpose['intent']['witnesses']}, {True, False})
        self.assertEqual(purpose['other_readings_open'], ALTERNATIVES)
        self.assertEqual(candidate['status'], 'CONFLICT')

    def test_no_mentioned_intender_and_missing_sense_keep_distinct_statuses(self):
        _, candidate = only_candidate('اِنْكَسَرَ الزُّجَاجُ لِيَنْفَعَ')
        purpose = candidate['readings'][0]['purpose']
        self.assertEqual(purpose['intent']['status'], 'BLOCKED')
        self.assertEqual(purpose['other_readings_open'], ALTERNATIVES)
        books = deepcopy(d.sources())
        books['mukhtar_sihah'] = ('withdrawn', ())
        lesson = d.Lesson(d.DATA.read_bytes(), d.lesson().previous, books)
        candidate = with_lesson(lesson, RAIN)
        self.assertEqual(candidate['status'], 'DEFERRED_SENSE')
        (row,) = candidate['readings']
        self.assertEqual(row['status'], 'DEFERRED_SENSE')
        self.assertEqual(row['hypothetical_slot_status'], 'BLOCKED')
        self.assertEqual(row['purpose']['other_readings_open'], ALTERNATIVES)


class PunctuationRegression(TestCase):
    def test_unsupported_nouns_decline_locally(self):
        for text in PUNCTUATION + ('شرب الولد الشاي،', 'شرب الولدُ، الشايَ'):
            with self.subTest(text=text):
                self.assertIsNone(scene.analyze(text))

    def test_valid_orders_and_supported_final_period_preserve_roles(self):
        for text in ('شرب الولدُ الشايَ', 'شرب الشايَ الولدُ', 'شرب الولد الشاي', 'شرب الولدُ الشايَ.'):
            with self.subTest(text=text):
                report = scene.analyze(text, 'order-source')
                self.assertEqual(report['coverage'], 'COMPLETE_IN_FRAGMENT')
                event, = report['events']
                mentions = {b['role']: report['entities'][b['target']]['mention']['surface'] for b in event['bindings']}
                self.assertIn(mentions['actor'], ('الولدُ', 'الولد'))
                self.assertIn(mentions['patient'], ('الشايَ', 'الشاي'))
                self.assertFalse(report['world_occurrence_verified'])
                self.assertFalse(report['empirical_cause_verified'])
                self.assertEqual(report['source_sha256'], sha256(text.encode()).hexdigest())
                for entity in report['entities'].values():
                    token = entity['mention']['token']
                    a, b = token['utf8_span']
                    self.assertEqual(text.encode()[a:b].decode(), token['surface'])

    def test_case_contradiction_is_not_accepted(self):
        self.assertIsNone(scene.analyze('شرب الولدُ الشايُ'))

    def test_relational_owner_preserves_failures_and_open_bridge(self):
        for text in PUNCTUATION:
            with self.subTest(text=text):
                report = relational.analyze({'text': text, 'source_id': 'punctuation-source'})
                self.assertNotIn('event_scene', report)
                self.assertEqual(report['ontology_bridge']['status'], 'DEFER')
                self.assertEqual(report['ontology_bridge']['ontology_assertions'], [])
                self.assertFalse(report['world_truth_established'])
                self.assertFalse(report['empirical_causality_established'])
                self.assertIn('owner_failures', report)
                self.assertEqual(report['source_sha256'], sha256(text.encode()).hexdigest())

    @skipUnless(NATIVE, 'requires seven native gateway owners; run io-gateway-build first')
    def test_both_gateway_routes_real_owners_and_source_replay(self):
        for route in ('text.read', 'relations.analyze'):
            for text in PUNCTUATION + ('شرب الولدُ الشايَ', RAIN, 'أَنْبَتَ الرَّجُلُ العُشْبَ لِيَنْفَعَ'):
                with self.subTest(route=route, text=text):
                    request = {'schema': gateway.REQUEST_SCHEMA, 'route': route, 'payload': {'text': text}}
                    receipt = gateway.run(request)
                    self.assertTrue(gateway.accept_output(receipt, expected_request=request)['valid'])
                    owner = receipt['execution']['owner_result']
                    if text in PUNCTUATION:
                        self.assertNotIn('event_scene', owner)
                    elif text.startswith('شرب'):
                        self.assertEqual(owner['event_scene']['coverage'], 'COMPLETE_IN_FRAGMENT')
                    else:
                        (candidate,) = owner['derived_event_roles']['candidates']
                        expected = 'BLOCKED' if text == RAIN else 'LICENSED'
                        self.assertEqual(candidate['status'], expected)
                        if text == RAIN:
                            self.assertEqual(candidate['readings'][0]['purpose']['other_readings_open'], ALTERNATIVES)
                    changed = deepcopy(request)
                    changed['payload']['text'] += ' '
                    self.assertFalse(gateway.accept_output(receipt, expected_request=changed)['valid'])
