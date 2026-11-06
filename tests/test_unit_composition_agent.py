"""Independent finite oracles, boundary attacks and actual installed-owner replay."""
from copy import deepcopy
from itertools import product
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.arabic_training import unit_composition as units
from tools.evidence_lifecycle_v1 import ResourceLimit

ROOT = Path(__file__).resolve().parents[1]
NATIVE = all((ROOT/'formal/.lake/build/bin'/p).is_file()
             for p in ('progressiveUnitProbe','alignedAcquisition'))
if os.environ.get('NABT_REQUIRE_UNIT_NATIVE') == '1' and not NATIVE:
    raise RuntimeError('Build progressiveUnitProbe and alignedAcquisition before this gate')


class CatalogueTests(unittest.TestCase):
    def test_cards_are_views_of_current_owners_and_preserve_open_scope(self):
        from tools.grammar_catalog.unit_catalog import catalog
        report = catalog()
        self.assertEqual(report['counts'],dict(ordered_shape=8,a116=116,pattern=71,
            declared_function=34,lexeme=16,phonological_example=20,curriculum_topic=80))
        cards = {r['id']:r for r in report['cards']}
        self.assertEqual(len(cards),sum(report['counts'].values()))
        self.assertEqual(cards['cell:0']['record']['classification'],'MOVING_ALIF_REJECTED')
        self.assertTrue(cards['phonology:idrib']['source']['passages'])
        self.assertIsNone(report['future_pattern'])
        self.assertFalse(report['lexical_or_grammatical_completeness_claimed'])
        self.assertEqual(report['agent_profile'],'units.compose')
        composition=next(p for p in report['proof_navigation'] if p['id']=='units.compose')
        self.assertIn('Nabt.BinaryUnitDomain.candidates_complete',composition['declaration_ids'])
        self.assertTrue(composition['open_obligations'])

    def test_curriculum_holds_out_radicals_not_templates_and_claims_no_training(self):
        from tools.grammar_catalog.unit_catalog import curriculum
        data = curriculum()
        self.assertEqual(len(data['examples']),213)
        roots,patterns = {},{}
        for split in ('train','dev','test'):
            rows = [r for r in data['examples'] if r['split']==split]
            self.assertEqual(len(rows),71)
            roots[split] = {r['request']['root'] for r in rows}
            patterns[split] = {r['pattern_id'] for r in rows}
        self.assertFalse(roots['train'] & roots['test'])
        self.assertFalse(roots['dev'] & roots['test'])
        self.assertEqual(patterns['train'],patterns['test'])
        self.assertFalse(data['model_weights_trained'])
        self.assertFalse(data['linguistic_mastery_measured'])

    def test_search_returns_source_cards_and_never_executes(self):
        from tools.grammar_catalog.unit_catalog import search
        with patch.object(units,'execute',side_effect=AssertionError('retrieval executed')):
            report=search('اسم الفاعل',limit=5)
        self.assertIn('topic:active_participle',{r['id'] for r in report['candidates']})
        self.assertTrue(report['ranking_executes_nothing'])
        self.assertEqual(report['authority'],'RETRIEVAL_ONLY')

    def test_invalid_inputs_and_caller_mastery_do_not_unlock_anything(self):
        for req in [dict(op='enumerate',max_c=True),dict(op='enumerate',include_pairs=1),
                    dict(op='enumerate',max_c=0,max_v=0),dict(op='shape',parts=['X']),
                    dict(op='shape',parts=['CV'],mastery=True),
                    dict(op='compose',parts=['كَتَبَ هُوَ'],separators=[]),
                    dict(op='compose',parts=['وَ','كَتَبَ'],separators=['\n']),
                    dict(op='read',text='كَتَبَ',source_id=[]),
                    dict(op='cell_page',length=2,offset=13456),
                    dict(op='cell_page',length=2,offset=True),
                    dict(op='unknown')]:
            with self.subTest(req=req), self.assertRaises(ValueError): units.execute(req)
        for req in [dict(op='enumerate',max_c=5),dict(op='shape',parts=['C'*13])]:
            with self.assertRaises(ResourceLimit): units.execute(req)

    def test_absent_native_owner_is_defer_not_python_simulation(self):
        with patch('tools.entropy_framework.reuse_run.entry_command',side_effect=FileNotFoundError):
            report=units.execute({'op':'enumerate'})
        self.assertEqual(report['result']['reason'],'NATIVE_PROBE_UNAVAILABLE')
        self.assertFalse(report['native_execution_performed'])
        self.assertFalse(report['general_grammar_license'])

    def test_existing_weak_application_retains_original_hypotheses(self):
        request={'op':'weak_application','text':'قَالَ','application':{
            'schema':'nabt.derivation-surface-request.v1','profile':'medial-alif-unmarked.v1',
            'span':{'start':0,'end':10},'root':'قول','pattern_id':'past.I.a','ending':'َ',
            'hypotheses':{'context':'ordinary','origin':'original'}}}
        r=units.execute(request)['result']['owner']
        self.assertEqual(r['original_request'],request['application'])
        self.assertFalse(r['grammar_certified'])
        self.assertFalse(r['attested_root'])
        self.assertEqual(r['generation']['surface'],'قَوَلَ')
        self.assertTrue(r['surface_alternatives'])


@unittest.skipUnless(NATIVE,'Installed Lean owners are required; CI explicitly requires both')
class NativeCompositionTests(unittest.TestCase):
    def test_a116_products_use_the_existing_numbering_without_false_exhaustion(self):
        r=units.execute(dict(op='cell_page',length=2,offset=13454,limit=16))['result']
        self.assertEqual(r['domain_count'],13456)
        self.assertEqual(r['cells'],[[115,114],[115,115]])
        self.assertEqual(r['numeric_first'],13571)
        self.assertTrue(r['reached_domain_end'])
        self.assertFalse(r['whole_domain_measured'])
        self.assertIsNone(r['next_offset'])
        r=units.execute(dict(op='cell_page',length=4,limit=1))['result']
        self.assertEqual(r['domain_count'],181063936)
        self.assertEqual(r['cells'],[[0,0,0,0]])
        self.assertEqual(r['next_offset'],1)
        self.assertFalse(r['source_acquired'])

    def test_quotas_equal_independent_bruteforce_and_pairs_are_ordered(self):
        report=units.execute({'op':'enumerate'})
        result=report['result']
        self.assertEqual((result['ordered_shape_count'],result['ordered_pairs'],result['syllable_pairs']),
                         (250,64,36))
        self.assertEqual(len(report['native_calls']),88)
        for row in result['quota_results']:
            c,v=row['consonants'],row['vowels']
            oracle={''.join(p) for p in product('CV',repeat=c+v) if p.count('C')==c}
            self.assertEqual(set(row['shapes']),oracle)
            self.assertEqual(len(row['shapes']),len(oracle))
            self.assertTrue(row['search_complete'])
            self.assertFalse(row['linguistic_license_inferred'])
        pairs=[r for r in report['native_calls'] if r['request']['op']=='compose_shapes']
        self.assertEqual({tuple(r['request']['parts']) for r in pairs},set(product(units.PAIR_BASIS,repeat=2)))
        self.assertFalse(result['arabic_license_inferred'])

    def test_noncommutative_order_and_same_surface_different_assemblies(self):
        def run(parts): return units.execute(dict(op='shape',parts=parts))['result']
        a,b=run(['C','V']),run(['V','C'])
        self.assertNotEqual(a['composition']['shape_n'],b['composition']['shape_n'])
        a,b=run(['CV','CVV']),run(['CVC','VV'])
        self.assertEqual(a['composition']['shape_n'],b['composition']['shape_n'])
        self.assertNotEqual(a['assembly_id'],b['assembly_id'])
        self.assertEqual(run(['CV','CV'])['forest']['count'],5)

    def test_exhausted_forest_retains_valid_shape_and_explicit_incompleteness(self):
        result=units.execute(dict(op='shape',parts=['CVVCC','CVVC']))['result']
        self.assertEqual(result['status'],'COMPOSED')
        self.assertEqual(result['forest']['enumeration'],'EXHAUSTED')
        self.assertFalse(result['forest_complete'])
        self.assertFalse(result['arabic_license_inferred'])

    def test_acquired_long_alif_and_full_97_state_effect(self):
        request=dict(op='compose',parts=['كَ','ا','تِبُ'],separators=['',''])
        report=units.execute(request)
        row=report['result']['words'][0]
        self.assertEqual(row['status'],'CELL_EFFECT_REPLAYED')
        self.assertEqual(row['effect']['cells'],[84,3,10,5])
        self.assertEqual(row['unit_n'],132731266)
        self.assertEqual(len(row['native_receipt']['effect']),97)
        self.assertTrue(row['acquisition_owner']['verified'])
        self.assertEqual(''.join(p['text'] for p in report['result']['pieces']),'كَاتِبُ')
        for r in row['native_receipt']['effect']:
            self.assertEqual(r['exit'],row['effect']['destinations'][r['entry']])
            self.assertEqual(r['weight'],row['effect']['weights'][r['entry']])
        self.assertFalse(report['result']['arabic_role_license_granted'])

    def test_word_and_combining_cluster_boundaries_are_enforced(self):
        attached=units.execute(dict(op='compose',parts=['وَ','كَتَبَ'],separators=['']))['result']
        detached=units.execute(dict(op='compose',parts=['مِنْ','هُوَ'],separators=[' '],mode='waqf'))['result']
        self.assertEqual(len(attached['words']),1)
        self.assertEqual(len(detached['words']),2)
        self.assertEqual(detached['text'],'مِنْ هُوَ')
        self.assertEqual([w['mode'] for w in detached['words']],['wasl','waqf'])
        self.assertFalse(detached['cross_word_effect_composed'])
        with self.assertRaises(ValueError):
            units.execute(dict(op='compose',parts=['ك','َتَبَ'],separators=['']))

    def test_local_rejection_does_not_discard_reusable_effect(self):
        # A final silent b cannot start a word; its effect remains usable after ka.
        a=units.execute(dict(op='compose',parts=['بْ'],separators=[]))['result']['words'][0]
        b=units.execute(dict(op='compose',parts=['كَ','بْ'],separators=[''],mode='waqf'))['result']['words'][0]
        self.assertFalse(a['native_receipt']['sound_shape_accepted'])
        self.assertTrue(b['native_receipt']['sound_shape_accepted'])
        self.assertEqual(a['status'],b['status'])

    def test_source_readings_keep_unknown_separate_from_sound_rejection(self):
        report=units.execute(dict(op='compose',parts=['كتب'],separators=[]))
        self.assertEqual(report['result']['words'][0]['status'],'DEFER_EXACT_A116_READING')
        self.assertFalse(report['general_grammar_license'])

    def test_phonology_is_conditional_on_source_boundary_and_quantity(self):
        initial=units.execute(dict(op='phonology',example_id='idrib',start='ibtida',end='waqf'))['result']
        linked=units.execute(dict(op='phonology',example_id='idrib',start='wasl',end='wasl'))['result']
        self.assertNotEqual(initial['alternatives'][0]['quantity']['shape'],linked['alternatives'][0]['quantity']['shape'])
        self.assertFalse(initial['syllable_license_granted'])
        self.assertFalse(initial['acoustic_validation'])
        self.assertTrue(initial['phonological_owner']['source_passages'])
        self.assertEqual(units.execute(dict(op='phonology',example_id='absent'))['result']['status'],'DEFER')

    def test_derived_participle_reuses_source_acquisition(self):
        report=units.execute(dict(op='generate',root='كتب',pattern_id='nominal.faail',ending='ُ'))
        r=report['result']
        self.assertEqual(r['generator_owner']['surface'],'كَاتِبُ')
        self.assertEqual(r['lower_trace']['words'][0]['status'],'CELL_EFFECT_REPLAYED')
        self.assertFalse(r['attested_word'])
        self.assertFalse(r['lexical_meaning_assigned'])

    def test_verification_requires_independent_request_and_fresh_complete_receipt(self):
        request=dict(op='compose',parts=['وَ','كَتَبَ'],separators=[''],source_id='lesson')
        report=units.execute(request)
        self.assertTrue(units.verify(report,expected_request=request)['valid'])
        for field,value in [('general_grammar_license',True),('execution_snapshot_sha256','0'*64)]:
            forged=deepcopy(report);forged[field]=value
            self.assertFalse(units.verify(forged,expected_request=request)['valid'])
        for change in [dict(source_id='another'),dict(separators=[' ']),dict(parts=['كَتَبَ','وَ'])]:
            self.assertFalse(units.verify(report,expected_request={**request,**change})['valid'])


if __name__=='__main__': unittest.main()
