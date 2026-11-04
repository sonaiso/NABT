"""Source-supervised targets, score isolation and actual owner boundaries."""
from copy import deepcopy
import json
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

HAS_NUMPY = importlib.util.find_spec('numpy') is not None
if HAS_NUMPY:
    from tools.lexical_training import acquisition as a
ROOT = Path(__file__).resolve().parents[1]
RUN = Path(os.environ.get('NABT_LEXICAL_ACQUISITION_RUN',
                          ROOT / 'evidence/lexical_acquisition_v1/run_01'))


@unittest.skipUnless(HAS_NUMPY, 'optional NumPy learner dependency not installed')
class SourceLearningTests(unittest.TestCase):
    def test_supervision_uses_quotations_not_supplied_root_or_component_inputs(self):
        cat, labels, rows, ys = a.dataset()
        self.assertEqual(len(rows),18)
        self.assertEqual(len(labels['component']),23)
        self.assertEqual({r['text'] for r in rows},{s['citation']['quotation'] for s in cat['senses']})
        for y in ys.values():
            self.assertTrue(a.np.allclose(y.sum(axis=1),1))
        self.assertNotIn('الشجاعة',labels['component'])
        self.assertNotIn('mutabaqa',labels['component'])

    def test_source_identity_and_interpretation_rank_are_preserved(self):
        _,_,rows,_=a.dataset()
        sources=[s for r in rows for s in r['sources']]
        self.assertTrue(any(s['source_check']=='RETAINED_QUOTATION_ONLY' for s in sources))
        self.assertTrue(any(s['source_file_replayed'] for s in sources))
        self.assertTrue(all(not s['historical_authenticity_established'] for s in sources))

    def test_target_atoms_are_semantic_units_not_gloss_words(self):
        _,labels,_,_=a.dataset()
        self.assertIn('حس الأذن',labels['component'])
        self.assertIn('الأذن',labels['component'])
        self.assertNotIn('حس',labels['component'])

    def test_no_root_or_target_can_be_supplied_to_the_predictor(self):
        with self.assertRaises(TypeError): a.propose('الكتابة',RUN,root='قلم')
        with self.assertRaises(TypeError): a.propose('الكتابة',RUN,target=['الذي يكتب به'])

    def test_global_candidates_and_proposal_authority_survive(self):
        r=a.propose('أداة نكتب بها',RUN)
        self.assertEqual(len(r['ranking']['sense']),18)
        self.assertEqual(len(r['ranking']['component']),23)
        self.assertEqual(r['authority'],'NONE')
        self.assertFalse(r['intended_sense_established'])
        self.assertFalse(r['calibrated_probabilities'])

    def test_prediction_does_not_claim_unknown_sense_detection(self):
        r=a.propose('لفظ غريب لا نعرف مدلوله',RUN)
        self.assertEqual(r['unknown_sense_detection'],'NOT_IMPLEMENTED')
        self.assertEqual(len(r['ranking']['sense']),18)
        self.assertFalse(r['intended_sense_established'])

    def test_invalid_text_stops_before_model_or_native_execution(self):
        with patch.object(a,'load_model') as load:
            for text in ['',True,'latin-only','ب'*9000]:
                with self.subTest(text=type(text).__name__),self.assertRaises(ValueError):a.propose(text,RUN)
            load.assert_not_called()

    def test_raw_text_and_hash_are_preserved(self):
        text='  قَلَمٌ\nللكتابة '
        r=a.propose(text,RUN)
        self.assertEqual(r['input'],text)
        self.assertEqual(r['input_sha256'],a.digest(text.encode()))

    def test_model_rejects_label_substitution_and_nonfinite_tensors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'run';shutil.copytree(RUN,path)
            meta=json.loads((path/'model.json').read_text())
            meta['labels']['component'].reverse();a.save(path/'model.json',meta)
            with self.assertRaises(ValueError):a.load_model(path)
            shutil.copy(RUN/'model.json',path/'model.json')
            with a.np.load(path/'weights.npz',allow_pickle=False) as f: weights={k:f[k] for k in f.files}
            weights['sense_w1'][0,0]=float('nan')
            a.np.savez(path/'weights.npz',**weights)
            meta=json.loads((path/'model.json').read_text())
            meta['weights_sha256']=a.digest((path/'weights.npz').read_bytes());a.save(path/'model.json',meta)
            with self.assertRaisesRegex(ValueError,'invalid tensor'):a.load_model(path)

    def test_fresh_training_replays_both_learned_heads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'run'
            report=a.train_run(path)
            self.assertTrue(all(x>0 for x in report['parameter_delta_l2'].values()))
            self.assertTrue(a.replay_training(path,RUN)['training_replayed'])
            with a.np.load(path/'weights.npz',allow_pickle=False) as f:weights={k:f[k] for k in f.files}
            weights['component_w1'][:]=0
            a.np.savez(path/'weights.npz',**weights)
            meta=json.loads((path/'model.json').read_text());meta['weights_sha256']=a.digest((path/'weights.npz').read_bytes())
            a.save(path/'model.json',meta)
            with self.assertRaisesRegex(ValueError,'tensor differs'):a.replay_training(path,RUN)

    def test_diagnostic_does_not_use_root_and_keeps_baseline(self):
        report=json.loads((RUN/'FIRST_TEST.json').read_text())
        self.assertFalse(report['root_supplied_to_predictor'])
        self.assertFalse(report['target_supplied_to_predictor'])
        self.assertEqual(report['diagnostic_status'],'EXPOSED_AUTHORED_SEEN_SENSES_GLOBAL_RANKING')
        self.assertEqual(set(report['metrics']),{'neural','lexical_baseline'})
        predictions=json.loads((RUN/'predictions.json').read_text())
        models,meta,_=a.load_model(RUN)
        x=a.encode([r['text'] for r in predictions])
        for head,labels in meta['labels'].items():
            scores=a.forward(models[head],x)
            for i,row in enumerate(predictions):
                self.assertEqual([labels[j] for j in a._rank(scores[i],labels)],row['neural'][head]['ranked_ids'])

    def test_curriculum_reuses_all_source_inventories_without_claiming_training(self):
        from tools.lexical_training.curriculum import curriculum
        r=curriculum()
        self.assertEqual(r['requested_axis_count'],30)
        self.assertEqual(r['research_inventory']['denominators'],
            {'morphology_families':51,'composition_groups':34,'interpretation_contracts':15,'nominal_templates':20})
        self.assertFalse(r['next_matrix_gate']['passed'])
        self.assertTrue(all(not x['complete_learning_certified'] for x in r['requested_axes']))
        ids={x['id'] for x in r['requested_axes']}
        self.assertTrue({'diptote','future','voice','counting','nawasikh','mental_condition'} <= ids)


@unittest.skipUnless(HAS_NUMPY and os.environ.get('NABT_LEXICAL_ACQUISITION_NATIVE')=='1',
                     'dedicated native learning connection gate not configured')
class NativeLearningConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ['lexicalDenotation','linguisticTruth']:
            if not (a.ROOT/'formal/.lake/build/bin'/name).is_file():
                raise AssertionError('native gate requires '+name)

    def test_condition_is_not_a_usage_witness(self):
        bare=a.connect('الأسد',RUN,profile_id='linguistic')
        self.assertTrue(bare['all_native_lexical_checks_completed'])
        mental=a.testimony.assess('أسد',['الشجاعة'])
        self.assertTrue(mental['rows'][0]['indications']['iltizam'])
        self.assertFalse(bare['usage_owner']['intended_sense_acquired'])
        self.assertEqual(bare['indication_application']['status'],'DEFER')
        self.assertFalse(bare['indication_application']['mental_necessity_is_sufficient'])

    def test_actual_cue_acquisition_keeps_alignment_and_world_obligations(self):
        text='أعني بالأسد الحيوان المفترس'
        r=a.connect(text,RUN,profile_id='linguistic')
        self.assertEqual(r['usage_owner']['status'],'COMPLETE')
        self.assertTrue(r['usage_owner']['native_checked'])
        self.assertTrue(r['usage_owner']['intended_sense_acquired'])
        self.assertTrue(4 <= len(r['conditional_lexical_receipts']) <= 14)
        self.assertFalse(r['all_installed_pairs_checked'])
        self.assertEqual(r['indication_application']['missing'],['EXACT_USAGE_SENSE_TO_DICTIONARY_SENSE_ALIGNMENT'])
        self.assertFalse(r['world_truth_established'])
        self.assertTrue(a.verify_connection(r,text=text,directory=RUN,profile_id='linguistic')['valid'])
        changed=deepcopy(r);changed['indication_application']['status']='LICENSED'
        self.assertFalse(a.verify_connection(changed,text=text,directory=RUN,profile_id='linguistic')['valid'])

    def test_scores_change_proposals_but_cannot_change_native_verdict_for_a_query(self):
        original=a.propose('الأسد',RUN)
        reversed_proposal=deepcopy(original)
        reversed_proposal['ranking']['sense'].reverse()
        reversed_proposal['ranking']['component'].reverse()
        first=a.connect('الأسد',RUN,profile_id='linguistic')
        with patch.object(a,'propose',return_value=reversed_proposal):
            second=a.connect('الأسد',RUN,profile_id='linguistic')
        self.assertNotEqual(first['proposed_queries'],second['proposed_queries'])
        for key in ['before_composition','after_composition','usage_owner','indication_application']:
            self.assertEqual(a.wire(first[key]),a.wire(second[key]))
        for receipt in second['conditional_lexical_receipts']:
            self.assertEqual(a.wire(receipt),a.wire(a.testimony.assess(receipt['entry'],receipt['target'])))

    def test_learned_query_is_checked_without_an_oracle_root_or_target(self):
        r=a.connect('أداة نكتب بها',RUN,profile_id='linguistic')
        roots={x['root_proposal'] for x in r['proposal']['ranking']['sense'][:3]}
        parts=[x['id'] for x in r['proposal']['ranking']['component'][:3]]
        learned=[q for q in r['proposed_queries'] if q['origin']=='LEARNED_COMPONENT_PROPOSAL']
        self.assertTrue(all(q['entry'] in roots and set(q['target']) <= set(parts) for q in learned))
        for q in r['proposed_queries']:
            if q['origin']=='RETRIEVED_NECESSITY_PREMISE':
                self.assertTrue(any(q['target']==[rule['target']] and rule['sense_id'] in
                    {x['id'] for x in r['proposal']['ranking']['sense'][:3]} for rule in a.catalogue()['necessities']))
        self.assertTrue(all(x['native_checked'] for x in r['conditional_lexical_receipts']))
        self.assertFalse(r['proposal']['intended_sense_established'])

    def test_quoted_use_does_not_activate_use(self):
        r=a.connect('«أعني بالأسد الحيوان المفترس»',RUN,profile_id='linguistic')
        self.assertFalse(r['usage_owner']['intended_sense_acquired'])
        self.assertFalse(r['world_truth_established'])

    def test_gloss_token_is_not_automatically_a_semantic_part(self):
        r=a.testimony.assess('سمع',['الأذن'])
        hearing=next(x for x in r['rows'] if x['sense_id']=='lisan:sama-hearing')
        ear=next(x for x in r['rows'] if x['sense_id']=='lisan:sama-ear')
        self.assertFalse(hearing['indications']['tadammun'])
        self.assertTrue(ear['indications']['mutabaqa'])


if __name__=='__main__':
    unittest.main()
