from copy import deepcopy
from hashlib import sha256
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import contextual_alignment as a, contextual_data as d
from tools.lexical_training import shared_encoder as old, teaching
from tools.grammar_catalog import gateway

ROOT = a.ROOT
READY = a.concepts.NATIVE.is_file()
if os.environ.get('NABT_REQUIRE_SHARED_NATIVE') == '1' and not READY:
    raise RuntimeError('Context alignment needs the native definition owner')


class AlignmentContracts(unittest.TestCase):
    def test_occurrences_keep_marks_and_multiple_word_boundaries(self):
        text='قَلَمٌ، قلم؛ قَلَمٌ'
        from tools.grammar_catalog.operations import exact_terms
        terms=exact_terms(text)
        self.assertEqual(len(terms),3)
        for term in terms:
            start,end=term['utf8_span']
            self.assertEqual(text.encode()[start:end].decode(),term['surface'])
        self.assertNotEqual(terms[0]['utf8_span'],terms[2]['utf8_span'])
        self.assertEqual(terms[0]['surface'],terms[2]['surface'])

    def test_request_rejects_labels_paths_and_unbounded_input(self):
        for payload in ({'text':'قلم','model':'/tmp/m'}, {'text':'قلم','concept_id':'lisan:qalam-writing'},
                        {'text':True},{'text':'ا'*129},{'text':'قلم','source_id':True}):
            with self.assertRaises(ValueError):a.validate_request(payload)

    def test_occurrence_capacity_is_a_resource_limit_through_the_cli(self):
        payload={'text':'ا '*33}
        self.assertLess(len(payload['text'].encode()),old.MAX_BYTES)
        with self.assertRaises(a.ResourceLimit):a.validate_request(payload)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'request.json'
            path.write_text(json.dumps({'schema':gateway.REQUEST_SCHEMA,'route':'neural.align','payload':payload}))
            result=subprocess.run([sys.executable,'-m','tools.grammar_catalog','gateway','run',
                                   '--request',str(path)],capture_output=True,text=True,check=False)
        self.assertEqual(result.returncode,3,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'RESOURCE_LIMIT')

    def test_supervision_spans_reject_boolean_and_decimal_coordinates(self):
        corpus=json.loads(d.CORPUS.read_text())
        index=next(i for i,r in enumerate(corpus['rows'])
                   if r['annotations'] and r['annotations'][0]['codepoint_span'][0]==0)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'corpus.json'
            for field in ('codepoint_span','utf8_span'):
                for convert in (lambda span:[False,span[1]],lambda span:[float(x) for x in span]):
                    changed=deepcopy(corpus)
                    annotation=changed['rows'][index]['annotations'][0]
                    annotation[field]=convert(annotation[field])
                    path.write_text(json.dumps(changed,ensure_ascii=False))
                    with self.assertRaises(ValueError):d.dataset(path)

    def test_model_rejects_tensor_threshold_and_label_corruption(self):
        model,_=a.load_model()
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'model.json'
            mutations=[]
            for key,value in [('alignment_bias',[0]),('alignment_labels',[a.NULL]),('authority','ACCEPT')]:
                changed=deepcopy(model);changed[key]=value;mutations.append(changed)
            for value in (True,-1,float('nan'),1.1):
                changed=deepcopy(model);changed['calibration']['min_probability']=value;mutations.append(changed)
            for changed in mutations:
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):a.load_model(path)

    def test_partition_groups_hashes_and_native_identity_vocabulary(self):
        splits=d.dataset();seen=set();groups=set()
        for rows in splits.values():
            self.assertFalse(seen & {r['text'] for r in rows});seen.update(r['text'] for r in rows)
            self.assertFalse(groups & {r['group'] for r in rows});groups.update(r['group'] for r in rows)
        report=json.loads((a.DIRECTORY/'FIRST_TEST.json').read_text())
        self.assertEqual(report['partition_hashes'],{k:d.digest(v) for k,v in splits.items()})
        model,_=a.load_model()
        ids={label for row in splits['train'] for annotation in row['annotations'] for label in annotation['concept_ids']}
        self.assertEqual(set(model['alignment_labels']),ids|{a.NULL})
        self.assertFalse(report['independent_semantic_adjudication'])
        self.assertGreater(report['shared_encoder_delta_l2'],0)

    def test_retained_metrics_are_recounted_including_false_alignments(self):
        report=json.loads((a.DIRECTORY/'FIRST_TEST.json').read_text())
        rows=json.loads((a.DIRECTORY/'predictions.json').read_text())
        positives=[r for r in rows if a.NULL not in r['gold']]
        tp=sum(r['proposed_id'] in r['gold'] for r in positives)
        fp=sum(r['proposed_id'] is not None and r['proposed_id'] not in r['gold'] for r in rows)
        metric=report['metrics']
        self.assertEqual(metric['gold_mentions'],len(positives))
        self.assertEqual(metric['true_positive'],tp)
        self.assertEqual(metric['false_positive'],fp)
        self.assertEqual(metric['false_negative'],len(positives)-tp)
        self.assertEqual(metric['tokens'],len(rows))
        self.assertEqual(report['weights_sha256'],sha256(a.MODEL.read_bytes()).hexdigest())
        self.assertLess(report['portable_max_abs_error'],1e-4)
        self.assertFalse(report['predictions_grant_authority'])

    def test_existing_shared_model_logits_survive_trajectory_refactor(self):
        model,_=old.load_model()
        retained=json.loads((ROOT/'evidence/shared_cognition_v1/predictions.json').read_text())
        for row in retained:
            scores=old.logits(model,row['text'])
            for head,result in row['heads'].items():
                labels=model['labels'][head]
                predicted=labels[max(range(len(labels)),key=lambda i:scores[head][i])]
                self.assertEqual(predicted,result['predictions']['neural'])

    def test_null_and_ambiguous_predictions_never_become_definitions(self):
        model,_=a.load_model();count=len(model['alignment_labels'])
        scores=[-20.0]*(count-1)+[20.0]
        self.assertEqual(a.decide(model,scores)['status'],'UNALIGNED')
        model['calibration'].update(min_probability=0.9,min_margin=0.2)
        scores=[0.0]*count;scores[0]=2;scores[1]=2
        self.assertEqual(a.decide(model,scores)['status'],'AMBIGUOUS')
        self.assertIsNone(a.decide(model,scores)['proposed_id'])


@unittest.skipUnless(READY,'build lexicalDenotation')
class NativeAlignment(unittest.TestCase):
    def test_free_text_binds_every_occurrence_and_keeps_all_alternatives(self):
        request={'text':'كتب الطالب بالقلم ثم وضع القلم قرب الورقة','source_id':'independent:1'}
        result=a.align(request)
        self.assertIn(result['status'],('PROPOSED','UNALIGNED'),result)
        refs={r['identity']['id']:r['reference'] for r in a.concepts.catalogue()['concepts']}
        self.assertEqual({k:v['reference'] for k,v in result['definitions'].items()},refs)
        self.assertEqual(len(result['occurrences']),8)
        self.assertEqual(len({r['occurrence_id'] for r in result['occurrences']}),8)
        for row in result['occurrences']:
            self.assertEqual({r['concept_id'] for r in row['candidates']},set(refs))
            start,end=row['utf8_span']
            self.assertEqual(request['text'].encode()[start:end].decode(),row['surface'])
            self.assertTrue(all(n['training_id'].startswith('train:') for n in row['training_neighbors']))
        self.assertFalse(result['intended_sense_established'])
        self.assertFalse(result['world_truth_established'])
        self.assertFalse(result['unknown_means_meaningless'])

    def test_source_identity_changes_occurrence_but_not_concept(self):
        left=a.align({'text':'القلم أداة للكتابة','source_id':'left'})
        right=a.align({'text':'القلم أداة للكتابة','source_id':'right'})
        self.assertEqual(left['definitions'],right['definitions'])
        self.assertEqual(left['occurrences'][0]['candidates'],right['occurrences'][0]['candidates'])
        self.assertNotEqual(left['occurrences'][0]['occurrence_id'],right['occurrences'][0]['occurrence_id'])

    def test_absent_model_or_changed_native_definition_defers(self):
        with patch.object(a,'load_model',side_effect=FileNotFoundError):
            self.assertEqual(a.align({'text':'قلم'})['status'],'DEFER')
        model,identity=a.load_model()
        model['shared_model']['concept_references']['lisan:qalam-writing']['definition_sha256']='0'*64
        with patch.object(a,'load_model',return_value=(model,identity)):
            result=a.align({'text':'قلم'})
            self.assertEqual(result['status'],'DEFER');self.assertEqual(result['occurrences'],[])

    def test_changed_training_provenance_rejects_neighbors(self):
        model,_=a.load_model()
        model['training_sha256']='0'*64
        with self.assertRaises(ValueError):a._training_neighbors(model,'قلم','lisan:qalam-writing')

    def test_label_vocabulary_and_provenance_are_checked_before_any_decision(self):
        model,identity=a.load_model()
        changed=deepcopy(model)
        changed['shared_model']['labels']['concept'][0]='unknown-definition'
        changed['alignment_labels'][0]='unknown-definition'
        with patch.object(a,'load_model',return_value=(changed,identity)):
            self.assertEqual(a.align({'text':'غيرمقيس'})['status'],'DEFER')
        changed=deepcopy(model);changed['training_sha256']='0'*64
        with patch.object(a,'load_model',return_value=(changed,identity)):
            result=a.align({'text':'غيرمقيس'})
            self.assertEqual(result['status'],'DEFER');self.assertEqual(result['occurrences'],[])

    def test_gateway_rejects_forged_span_concept_or_acceptance(self):
        request={'schema':gateway.REQUEST_SCHEMA,'route':'neural.align','payload':{'text':'القلم أداة للكتابة'}}
        receipt=gateway.run(request)
        self.assertEqual(receipt['status'],'EXECUTED',receipt['execution'])
        self.assertTrue(gateway.accept_output(receipt,expected_request=request)['valid'])
        for field,value in [('proposed_id','forged'),('utf8_span',[0,1])]:
            changed=deepcopy(receipt)
            changed['execution']['owner_result']['occurrences'][0][field]=value
            self.assertFalse(gateway.accept_output(changed,expected_request=request)['valid'])
        changed=deepcopy(receipt);changed['execution']['owner_result']['intended_sense_established']=True
        self.assertFalse(gateway.accept_output(changed,expected_request=request)['valid'])

    @unittest.skipUnless((ROOT/'formal/.lake/build/bin/evidenceLifecycleV1').is_file(),'build lifecycle')
    def test_v3_lesson_keeps_source_withdrawal_and_binds_alignment(self):
        lesson=json.loads((ROOT/'examples/cognitive_teaching/learning.json').read_text())
        baseline=teaching.run_lesson(lesson)
        lesson['schema']=teaching.SCHEMA_V3;lesson['matrix_id']='mafhum'
        result=teaching.run_lesson(lesson)
        self.assertTrue(result['execution_measured'],result)
        self.assertEqual(baseline['owner_result'],result['owner_result'])
        self.assertEqual([r['status'] for r in result['measurements']['steps']],
                         ['SUPPORTED','SUPPORTED','SUPPORTED','UNKNOWN','SUPPORTED'])
        self.assertTrue(teaching.verify_lesson(result,expected_lesson=lesson)['valid'])
        observations=result['episode']['neural_observation']['observations']
        for row,source in zip(observations,lesson['payload']['sources']):
            self.assertEqual(row['proposal']['source_text'],source['text'])
            self.assertEqual(row['proposal']['source_id'],source['id'])
            self.assertFalse(row['proposal']['intended_sense_established'])

    def test_budget_preserves_long_sources_without_neural_truncation(self):
        text='قلم '*150
        result=a.observe_lesson('qualified_inference',{'source_id':'long','source_text':text})
        row=result['observations'][0]
        self.assertEqual(row['source_text'],text)
        self.assertIsNone(row['proposal']);self.assertEqual(row['status'],'NEURAL_BUDGET_DEFER')

    def test_owner_source_locator_limit_is_preserved_by_optional_observation(self):
        lesson=json.loads((ROOT/'examples/cognitive_teaching/qualified.json').read_text())
        lesson['schema']=teaching.SCHEMA_V3
        owner={'status':'SUPPORTED','source_answer':{'verification':{'native_receipt':{'checked':True}}},
               'conditional_result':None,'conditional_consequence':True}
        for source_id in ('x'*129,'م'*128,'x'*257,' '*8):
            lesson['payload']['source_id']=source_id
            with patch.object(teaching.source_bound,'evaluate_source',return_value=deepcopy(owner)):
                result=teaching.run_lesson(lesson)
            self.assertEqual(result['status'],'SUPPORTED',result)
            self.assertTrue(result['execution_measured'])
            self.assertEqual(result['owner_result'],owner)
            row=result['episode']['neural_observation']['observations'][0]
            self.assertEqual(row['source_id'],source_id)
            if not source_id.strip():
                self.assertEqual(row['status'],'NEURAL_INPUT_DEFER')
                self.assertIsNone(row['proposal'])
            elif len(source_id.encode())<=a.MAX_SOURCE_ID_BYTES:
                self.assertEqual(row['proposal']['source_id'],source_id)
            else:
                self.assertEqual(row['status'],'NEURAL_BUDGET_DEFER')
                self.assertIsNone(row['proposal'])


if __name__=='__main__':unittest.main()
