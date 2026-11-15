"""Independent semantic boundaries, source replay and train/test separation."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from tools.lexical_training import ifadah_programs as n, teaching
from tools.grammar_catalog import gateway, gateway_links


def lesson(text='هَلْ كَانَ الْكَاتِبُ حَاضِرًا؟'):
    return {'schema': n.SCHEMA, 'mode': 'understand', 'source_id': 'test-source', 'text': text}


class IfadahPrograms(TestCase):
    def test_distinct_operators_and_same_governance(self):
        expected = {'إِنَّ الْكَاتِبَ حَاضِرٌ': ('assert', 'emphasis'),
                    'لَيْتَ الْكَاتِبَ حَاضِرٌ': ('wish', 'plain'),
                    'لَعَلَّ الْكَاتِبَ حَاضِرٌ': ('hope', 'plain'),
                    'لَيْسَ الْكَاتِبُ حَاضِرًا': ('assert', 'negation')}
        for text, (force, frame) in expected.items():
            with self.subTest(text=text):
                row, = n.understand(text, 'test')['readings']
                self.assertEqual((row['force'], row['frame']), (force, frame))
                self.assertEqual(row['source_commitment'], force == 'assert')
                self.assertFalse(row['world_truth_established'])
                self.assertTrue(row['owner']['witnesses'])

    def test_scope_preserves_asked_negative_and_never_answers_question(self):
        result = n.run(lesson('هَلْ لَيْسَ الْكَاتِبُ حَاضِرًا؟'))
        expected = {'op': 'ask', 'body': {'op': 'negation', 'body': {
            'op': 'predication', 'subject': 0, 'predicate': 0}}}
        self.assertEqual(result['accepted_program'], expected)
        self.assertFalse(result['owner']['readings'][0]['source_commitment'])
        self.assertNotIn('answer', result)
        self.assertFalse(result['world_truth_established'])
        self.assertFalse(result['grammar_certified'])
        self.assertFalse(result['native_checked'])
        inverse = n.run(lesson('لَيْسَ هَلْ الْكَاتِبُ حَاضِرًا'))
        self.assertIsNone(inverse['neural_proposal']['name'])
        self.assertIsNone(inverse['accepted_program'])
        with self.assertRaises(ValueError):
            n.realize({'op': 'negation', 'body': {'op': 'ask', 'body': expected['body']['body']}})

    def test_source_spans_with_outer_wrapper_are_parent_bound(self):
        r = lesson()
        report = n.run(r)
        row, = report['owner']['readings']
        self.assertTrue(row['outer_question_cue']['witnesses'])
        for token in row['bindings'].values():
            a, b = token['utf8_span']
            c, d = token['codepoint_span']
            self.assertEqual(r['text'].encode()[a:b].decode(), token['surface'])
            self.assertEqual(r['text'][c:d], token['surface'])
            self.assertEqual(token['source_sha256'], sha256(r['text'].encode()).hexdigest())
        self.assertEqual(row['bindings']['subject']['surface'], 'الْكَاتِبُ')

    def test_counterexamples_abstain_locally_without_semantic_rejection(self):
        for text in ('الْكَاتِبُ، حَاضِرٌ', 'لَيْتَ الْكَاتِبُ حَاضِرٌ',
                     'هَلْ إِنَّ الْكَاتِبَ حَاضِرٌ؟', 'هَلْ الْغَرِيبُ حَاضِرٌ؟'):
            with self.subTest(text=text):
                r = n.run(lesson(text))
                self.assertEqual(r['status'], 'DEFER')
                self.assertIsNone(r['accepted_program'])
                self.assertEqual(r['owner']['readings'], [])
                self.assertFalse(r['world_truth_established'])
                self.assertIn('GENERAL_IFADAH_ACQUISITION_OPEN', r['open_obligations'])

    def test_withdraw_outer_operator_preserves_predication(self):
        question = n.run(lesson('هَلْ الْكَاتِبُ حَاضِرٌ؟'))
        assertion = n.run(lesson('الْكَاتِبُ حَاضِرٌ'))
        self.assertEqual(question['accepted_program']['body'], assertion['accepted_program'])
        self.assertFalse(question['owner']['readings'][0]['source_commitment'])
        self.assertTrue(assertion['owner']['readings'][0]['source_commitment'])
        self.assertFalse(assertion['world_truth_established'])

    def test_generation_is_only_proposed_intent_even_when_roundtrip_matches(self):
        request = {'schema': n.SCHEMA, 'mode': 'produce', 'source_id': 'goal',
                   'instruction': 'اسأل عن ثبوت الصفة الآن', 'subject': 5, 'predicate': 5}
        result = n.run(request)
        self.assertTrue(result['roundtrip_matches'])
        self.assertEqual(result['generated_text'], 'هَلْ الطَّالِبُ مُنْتَبِهٌ؟')
        self.assertEqual(result['realized_program']['op'], 'ask')
        self.assertIsNone(result['accepted_program'])
        self.assertIn('INSTRUCTION_TO_INTENT_ALIGNMENT_UNVERIFIED', result['open_obligations'])
        self.assertFalse(result['world_truth_established'])

    def test_model_failure_keeps_all_exact_readings(self):
        with patch.object(n, 'MODEL', Path('/nonexistent/ifadah-model')):
            result = n.run(lesson())
        self.assertEqual(result['neural_proposal']['status'], 'MODEL_UNAVAILABLE')
        self.assertEqual(result['status'], 'DEFER')
        self.assertEqual(len(result['owner']['readings']), 1)
        self.assertIsNone(result['accepted_program'])

    def test_lexical_source_withdrawal_cannot_be_replaced_by_weights(self):
        with patch.object(n.awamil, 'read', side_effect=ValueError('Pinned grammar source excerpt changed')):
            result = teaching.run_lesson(lesson())
        self.assertEqual(result['status'], 'EVIDENCE_UNAVAILABLE')
        self.assertFalse(result['execution_measured'])

    def test_client_cannot_supply_model_paths_or_licenses(self):
        for field, value in (('model_path', '/tmp/model'), ('licensed', True), ('program', {})):
            r = lesson(); r[field] = value
            self.assertEqual(teaching.run_lesson(r)['status'], 'INVALID_INPUT')
        goal = {'schema': n.SCHEMA, 'mode': 'produce', 'source_id': 'goal',
                'instruction': 'اسأل', 'subject': True, 'predicate': 0}
        self.assertEqual(teaching.run_lesson(goal)['status'], 'INVALID_INPUT')

    def test_replay_rejects_changed_source_and_forged_program(self):
        r = lesson(); report = teaching.run_lesson(r)
        self.assertTrue(teaching.verify_lesson(report, expected_lesson=r)['valid'])
        other = deepcopy(r); other['source_id'] = 'different'
        self.assertFalse(teaching.verify_lesson(report, expected_lesson=other)['valid'])
        forged = deepcopy(report); forged['accepted_program'] = {'op': 'assert'}
        self.assertFalse(teaching.verify_lesson(forged, expected_lesson=r)['valid'])

    def test_frozen_split_and_training_membership(self):
        data = n.dataset(); model, _ = n.load_model()
        ids = set(model['train_ids']['understand'])
        self.assertEqual(ids, {r['id'] for r in data['rows'] if r['split'] == 'train'})
        self.assertEqual(len(ids), 84)
        self.assertFalse(any(r['program'] in ('ask_past', 'ask_negation') for r in data['rows'] if r['id'] in ids))
        self.assertFalse(any('ask_past' in key or 'ask_negation' in key for key in model['train_ids']['produce']))
        self.assertEqual(len({r['text'] for r in data['rows']}), len(data['rows']))

    def test_all_programs_realize_and_recover_exact_tree(self):
        for name in n.PROGRAMS:
            for subject, predicate in ((0, 0), (5, 4)):
                tree = n.program(name, subject, predicate)
                readings = n.understand(n.realize(tree), 'roundtrip')['readings']
                self.assertIn(tree, [r['program'] for r in readings])
        with self.assertRaises(ValueError):
            n.program('plain', True, 0)
        with self.assertRaises(ValueError):
            n.realize({'op': 'predication', 'subject': True, 'predicate': 0})

    def test_local_conflict_is_not_single_program(self):
        r = n.run(lesson('لَيْتَ لَعَلَّ الْكَاتِبَ حَاضِرٌ'))
        self.assertEqual(r['neural_proposal']['force'], 'CONFLICT')
        self.assertIsNone(r['neural_proposal']['name'])
        self.assertIsNone(r['accepted_program'])

    def test_gateway_real_lesson_and_independent_request_replay(self):
        request = {'schema': gateway.REQUEST_SCHEMA, 'route': 'cognitive.lesson', 'payload': {'lesson': lesson()}}
        receipt = gateway.run(request)
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)['valid'])
        result = receipt['execution']['owner_result']
        self.assertEqual(result['accepted_program']['op'], 'ask')
        self.assertEqual(result['accepted_program']['body']['op'], 'past')
        self.assertFalse(result['native_checked'])
        changed = deepcopy(request); changed['payload']['lesson']['text'] = 'الْكَاتِبُ حَاضِرٌ'
        self.assertFalse(gateway.accept_output(receipt, expected_request=changed)['valid'])

    def test_catalog_exposes_existing_family_and_tests_without_proof_claim(self):
        graph = gateway_links.build('cognitive.lesson')
        self.assertIn(n.SCHEMA, json.dumps(graph))
        self.assertIn('tests/test_ifadah_programs.py', json.dumps(graph))
