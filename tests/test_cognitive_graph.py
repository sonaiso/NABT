from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.lexical_training import cognitive_graph as c, cognitive_training as t, teaching
from tools.grammar_catalog import gateway

READY = c.alignment.concepts.NATIVE.is_file()
if os.environ.get('NABT_REQUIRE_SHARED_NATIVE') == '1' and not READY:
    raise RuntimeError('Cognitive graph requires the native definition owner')


class CognitiveContracts(unittest.TestCase):
    def test_sign_trace_keeps_repetition_marks_and_a116_scope(self):
        text = 'كَتَبَ كُتِبَ كَتَبَ قلم'
        nodes = c.sign_nodes(text, 'source:a')
        self.assertEqual(len({r['id'] for r in nodes}), 4)
        self.assertEqual(nodes[0]['a116']['status'], 'REPRESENTED')
        self.assertNotEqual(nodes[0]['a116']['cells'], nodes[1]['a116']['cells'])
        self.assertEqual(nodes[0]['a116']['cells'], nodes[2]['a116']['cells'])
        self.assertEqual(nodes[3]['a116']['status'], 'DEFER')
        for node in nodes:
            a, b = node['utf8_span']
            self.assertEqual(text.encode()[a:b].decode(), node['surface'])
        self.assertFalse(nodes[0]['a116']['lexical_attestation_established'])

    def test_missing_ledger_entries_are_not_invented(self):
        rows = c.coverage()
        self.assertEqual([r['number'] for r in rows if 'status' in r], [3, 14])
        self.assertTrue(all(not r.get('whole_decomposition_learned', False) for r in rows))

    def test_archived_measurements_recount_reviewed_and_unknown_separately(self):
        for directory in (c.DIRECTORY, c.DIRECTORY/'sum_ablation'):
            report = json.loads((directory/'FIRST_TEST.json').read_text())
            self.assertEqual(report['weights_sha256'], sha256((directory/'model.json').read_bytes()).hexdigest())
            for name, metrics in report['evaluation'].items():
                predictions = json.loads((directory/(name+'_predictions.json')).read_text())
                reviewed = [r for r in predictions if r['review_status'] != 'UNREVIEWED']
                positives = [r for r in reviewed if c.alignment.NULL not in r['gold']]
                tp = sum(r['proposed_id'] in r['gold'] for r in positives)
                fp = sum(r['proposed_id'] is not None and r['proposed_id'] not in r['gold'] for r in reviewed)
                self.assertEqual(metrics['neural']['true_positive'], tp)
                self.assertEqual(metrics['neural']['false_positive'], fp)
                self.assertEqual(metrics['neural']['false_negative'], len(positives)-tp)
                self.assertTrue(all(r['correct'] is None for r in predictions if r['review_status'] == 'UNREVIEWED'))
                self.assertLess(metrics['portable_max_abs_error'], 1e-4)
            self.assertFalse(report['independent_semantic_adjudication'])
            self.assertFalse(report['world_truth_established'])


@unittest.skipUnless(READY, 'build lexicalDenotation')
class NativeCognitiveGraph(unittest.TestCase):
    def test_shared_identity_all_alternatives_and_original_owner_are_preserved(self):
        request = {'text': 'القلم أداة للكتابة', 'source_id': 'trace:1'}
        result = c.analyze(request)
        refs = {r['identity']['id']: r['reference'] for r in c.alignment.concepts.catalogue()['concepts']}
        self.assertEqual({r['id']:r['reference'] for r in result['concept_graph']['nodes']}, refs)
        self.assertEqual(result['relational_owner'], c.relational.analyze(request))
        self.assertEqual(len(result['alignment_edges']), len(refs)*len(result['sign_graph']['nodes']))
        for edge in result['alignment_edges']:
            self.assertIn(edge['target'], refs); self.assertFalse(edge['accepted'])
            index = int(edge['evidence_pointer'].rsplit('/', 1)[1])
            self.assertEqual(result['neural_observation']['occurrences'][index]['occurrence_id'], edge['source'])
        self.assertEqual(result['concept_graph']['grounded_world_claims'], [])
        self.assertEqual(result['concept_graph']['admitted_concept_applications'], [])
        self.assertTrue(all(r['admission'] == 'DEFINITION_CANDIDATE_NOT_GROUNDED_APPLICATION'
                            for r in result['concept_graph']['nodes']))
        self.assertEqual(result['acceptance']['status'], 'DEFER')
        self.assertFalse(result['acceptance']['unknown_is_meaningless'])

    def test_missing_model_preserves_source_without_claiming_empty_meaning(self):
        with patch.object(c, 'MODEL', Path('/nonexistent/cognitive-model.json')):
            result = c.analyze({'text': 'زعبولا'})
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['sign_graph']['nodes'][0]['surface'], 'زعبولا')
        self.assertEqual(result['alignment_edges'], [])
        self.assertEqual(result['acceptance']['status'], 'DEFER')

    def test_gateway_replays_and_rejects_changed_graph_and_request(self):
        request = {'schema':gateway.REQUEST_SCHEMA, 'route':'neural.graph',
                   'payload':{'text':'القلم أداة للكتابة', 'source_id':'independent:graph'}}
        receipt = gateway.run(request)
        self.assertEqual(receipt['status'], 'EXECUTED', receipt['execution'])
        self.assertIn('transition-law', [r['family'] for r in receipt['proof_test_links']['family_test_links']])
        view_families = {family for row in c.coverage() for view in row.get('views', [])
                         for family in view['owner_families']}
        self.assertTrue(view_families <= {r['family'] for r in receipt['proof_test_links']['family_test_links']})
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)['valid'])
        for mutation in ('acceptance', 'span', 'concept'):
            changed = deepcopy(receipt); owner = changed['execution']['owner_result']
            if mutation == 'acceptance': owner['alignment_edges'][0]['accepted'] = True
            if mutation == 'span': owner['sign_graph']['nodes'][0]['utf8_span'] = [0, 1]
            if mutation == 'concept': owner['alignment_edges'][0]['target'] = 'invented'
            self.assertFalse(gateway.accept_output(changed, expected_request=request)['valid'])
        altered = deepcopy(request); altered['payload']['source_id'] = 'different'
        self.assertFalse(gateway.accept_output(receipt, expected_request=altered)['valid'])

    @unittest.skipUnless((c.shared.ROOT/'formal/.lake/build/bin/evidenceLifecycleV1').is_file(), 'build lifecycle')
    def test_v4_lesson_withdrawal_does_not_become_neural_certification(self):
        lesson = json.loads((c.shared.ROOT/'examples/cognitive_teaching/learning.json').read_text())
        baseline = teaching.run_lesson(lesson)
        lesson['schema'] = teaching.SCHEMA_V4
        result = teaching.run_lesson(lesson)
        self.assertTrue(result['execution_measured'], result)
        self.assertEqual(result['owner_result'], baseline['owner_result'])
        self.assertEqual([r['status'] for r in result['measurements']['steps']],
                         ['SUPPORTED','SUPPORTED','SUPPORTED','UNKNOWN','SUPPORTED'])
        self.assertTrue(teaching.verify_lesson(result, expected_lesson=lesson)['valid'])
        for observation in result['episode']['neural_observation']['observations']:
            self.assertEqual(observation['proposal']['source']['text'], observation['source_text'])
            self.assertEqual(observation['proposal']['acceptance']['status'], 'DEFER')
        request = {'schema':gateway.REQUEST_SCHEMA, 'route':'cognitive.lesson', 'payload':{'lesson':lesson}}
        receipt = gateway.run(request)
        self.assertEqual(receipt['status'], 'EXECUTED', receipt['execution'])
        self.assertIsNotNone(receipt['proof_test_links']['curriculum_links'])
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)['valid'])


if __name__ == '__main__': unittest.main()
