"""Independent Arabic contrasts and source/ontology boundary regressions."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, gateway_links, relational
from tests.test_io_gateway import NATIVE, ROOT


def read(path):
    return json.loads((ROOT / path).read_text())


class RelationalRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = relational.catalog()

    def test_past_vowels_are_exact_and_not_collapsed_by_search(self):
        patterns = self.catalog['past_patterns']
        self.assertEqual([p['label']+'َ' for p in patterns], ['فَعَلَ', 'فَعِلَ', 'فَعُلَ'])
        for text, name in [('فَعَلَ','past.I.a'), ('فَعِلَ','past.I.i'), ('فَعُلَ','past.I.u')]:
            found = relational.search(text)
            self.assertEqual(found['vocalized_shape_focus'], [name])
            self.assertEqual(found['exact_shape_records'][0]['pattern']['id'], name)
            self.assertEqual(found['raw_query'], text)
        self.assertEqual(relational.search('فعل')['vocalized_shape_focus'], [])

    def test_accompaniment_and_purpose_have_independent_exact_sources(self):
        cards = {r['id']:r for r in self.catalog['cards']}
        accompaniment = cards['relation:accompaniment']['sources'][0]
        purpose = cards['relation:purpose']['sources'][0]
        self.assertIn('التنصيص على المعية', accompaniment['raw_text'])
        self.assertIn('شاركه وقتا وفاعلا', purpose['raw_text'])
        self.assertNotEqual(accompaniment['sha256'], purpose['sha256'])
        for card in cards.values():
            for source in card.get('sources', []):
                raw = (ROOT/source['source']['local_path']).read_bytes()
                self.assertEqual(raw[source['start']:source['end']].decode(), source['raw_text'])
                self.assertEqual(sha256(raw[source['start']:source['end']]).hexdigest(), source['sha256'])

    def test_source_hash_corruption_is_rejected(self):
        from tools.grammar_catalog.catalog import build_catalog
        bad = build_catalog()
        next(s for s in bad['sources'] if s['source_id']=='qatr')['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Qatr source changed'):
            relational._anchors(bad)

    def test_ontology_uses_current_foundation_and_does_not_inherit_by_shape(self):
        cards = {r['id']:r for r in self.catalog['cards']}
        for key in ('kind_nature','property','spatial_relation','temporal_relation','causal_relation'):
            row = cards['foundation:'+key]
            self.assertFalse(row['ontology_certified'])
            self.assertTrue(row['existing_curriculum_row']['owner_modules'])
        self.assertFalse(self.catalog['past_to_nominal_link']['shared_root_is_sufficient'])
        self.assertFalse(cards['relation:effect']['inverse_inference_licensed'])

    def test_proof_links_include_existing_owners_and_this_test_file(self):
        graph = gateway_links.build('relations.analyze')
        self.assertIn('tests/test_relational_rag.py', {r['path'] for r in graph['tests']})
        self.assertTrue({'Nabt.Derivation','Nabt.EpistemicMeasurement','Nabt.TemporalContext'} <= {r['module'] for r in graph['declarations']})
        self.assertFalse(graph['formal_application_established'])


class RelationalAnalysis(unittest.TestCase):
    def test_three_past_patterns_passive_and_nominal_ambiguity(self):
        report = relational.analyze({'text':'كَتَبَ فَرِحَ كَرُمَ كُتِبَ كَاتِبٌ'})
        rows = report['shape_occurrences']
        self.assertEqual([r['past_pattern_candidates'] for r in rows], [['past.I.a'],['past.I.i'],['past.I.u'],[],[]])
        self.assertEqual(set(rows[0]['all_pattern_candidates']), {'past.I.a','grammar.masdar.bare.fa3al','grammar.sifa.fa3al'})
        self.assertIn('passive.I', rows[3]['all_pattern_candidates'])
        self.assertIn('nominal.faail', rows[4]['all_pattern_candidates'])
        self.assertIn('grammar.sifa.faa3il', rows[4]['all_pattern_candidates'])
        self.assertFalse(any(r['lexical_meaning_certified'] for r in rows))
        self.assertEqual(report['ontology_bridge']['ontology_assertions'], [])

    def test_repeated_and_quoted_occurrences_keep_separate_identities(self):
        report = relational.analyze({'text':'كَتَبَ كَتَبَ «كَتَبَ»'})
        rows = report['shape_occurrences']
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({r['occurrence_id'] for r in rows}), 3)
        self.assertEqual([r['reading_context'] for r in rows], ['UNQUOTED','UNQUOTED','MENTION'])
        self.assertEqual(len({r['span']['start'] for r in rows}), 3)

    def test_retrieval_top_k_cannot_prune_owners(self):
        a = relational.analyze({'text':'كَتَبَ', 'query':'المصاحبة', 'limit':1})
        b = relational.analyze({'text':'كَتَبَ', 'query':'الزمان', 'limit':5})
        self.assertEqual(a['owner_reports'], b['owner_reports'])
        self.assertEqual(a['shape_occurrences'], b['shape_occurrences'])
        self.assertEqual(a['owner_reports']['temporal']['status'], 'UNKNOWN')
        self.assertFalse(a['empirical_causality_established'])

    def test_caller_authority_or_independent_inference_source_rejected(self):
        for name in ('ontology_certified','checker','proof_catalogue','causal_license'):
            with self.assertRaises(ValueError):
                relational.validate({'text':'كَتَبَ',name:True})
        for name in ('source','source_id','checker','approved'):
            with self.assertRaises(ValueError):
                relational.validate({'text':'كَتَبَ','inference':{'query':'هل؟','plan':{},name:'other'}})
        with self.assertRaises(ValueError):
            relational.validate({'text':'كَتَبَ','limit':True})

    def test_gateway_replay_rejects_forged_ontology_assertion(self):
        request = {'schema':gateway.REQUEST_SCHEMA,'route':'relations.analyze','payload':{'text':'كَتَبَ'}}
        receipt = gateway.run(request)
        self.assertEqual(receipt['status'], 'EXECUTED', receipt['execution'])
        check = gateway.accept_output(receipt, expected_request=request)
        self.assertTrue(check['valid'], check)
        changed = deepcopy(receipt)
        changed['execution']['owner_result']['ontology_bridge']['ontology_assertions'] = [{'kind':'invented'}]
        self.assertFalse(gateway.accept_output(changed, expected_request=request)['valid'])


@unittest.skipUnless(NATIVE, 'Build existing native source and temporal owners')
class NativeRelationalOwners(unittest.TestCase):
    def test_source_inference_keeps_conditioned_status_and_bridge_withdrawal(self):
        lesson = read('examples/cognitive_teaching/world_prior.json')['payload']
        request = {'text':lesson['source_text'], 'source_id':lesson['source_id'],
            'inference':{'query':lesson['query_text'],'plan':lesson['plan'],
                         **{k:lesson[k] for k in ('revision','scope','context','time')}}}
        full = relational.analyze(request)
        owner = full['owner_reports']['source_inference']
        self.assertEqual(owner['status'], 'SUPPORTED')
        self.assertTrue(owner['conditional_consequence'])
        removed = deepcopy(request)
        removed['text'] = '\n'.join(removed['text'].splitlines()[:-1])+'\n'
        removed['inference']['plan']['bridge_clause'] = None
        deferred = relational.analyze(removed)
        self.assertEqual(deferred['owner_reports']['source_inference']['status'], 'UNKNOWN')
        self.assertFalse(deferred['owner_reports']['source_inference']['conditional_consequence'])
        for report in (full, deferred):
            self.assertFalse(report['world_truth_established'])
            self.assertFalse(report['empirical_causality_established'])
            self.assertEqual(report['ontology_bridge']['status'], 'DEFER')
        self.assertNotEqual(full['source_sha256'], deferred['source_sha256'])

    def test_temporal_source_is_bound_to_original_input(self):
        req = read('examples/context_application/yesterday.json')
        report = relational.analyze(req)
        from tools.grammar_catalog.temporal import evaluate
        self.assertEqual(report['owner_reports']['temporal'], evaluate(req))
        broken = deepcopy(req); broken['text']='كَتَبَ'
        with self.assertRaises(ValueError):
            relational.analyze(broken)


if __name__ == '__main__':
    unittest.main()
