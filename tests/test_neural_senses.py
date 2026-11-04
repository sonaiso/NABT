"""Proposal corruption must not acquire semantic authority or erase alternatives."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/neural_senses_v1/run_01'
HAS_NUMPY=importlib.util.find_spec('numpy') is not None


class IntegrationIdentityTests(unittest.TestCase):
    def test_shared_features_preserve_original_retriever_encoding(self):
        from tools.lexical_training.features import features
        # Golden output from the pre-change retriever at 71e74400c620.
        self.assertEqual(dict(features('علم علم',512)),
                         {365:2,481:2,188:2,489:2,1:2,449:2})

    def test_reuse_map_discovers_the_existing_owner_and_new_consumer(self):
        from tools.entropy_framework.reuse import build_reuse_report
        report=build_reuse_report(family='lexical-denotation')
        family=next(f for f in report['families'] if f['id']=='lexical-denotation')
        self.assertIn('tools/lexical_testimony.py',family['runtime_paths'])
        self.assertIn('tools/lexical_training/senses.py',family['runtime_paths'])
        self.assertIn('tests/test_neural_senses.py',family['test_paths'])


@unittest.skipUnless(HAS_NUMPY,'optional numpy training dependency not installed')
class NeuralSenseTests(unittest.TestCase):
    def setUp(self):
        from tools.lexical_training import senses
        self.s=senses

    def test_installed_weights_replay_and_no_training_query_overlap(self):
        w,meta,cat=self.s.load_model(RUN)
        self.assertEqual(len(meta['sense_ids']),18)
        train,_=self.s.training_rows(cat)
        cases=json.loads((RUN.parent/'acceptance.json').read_text())['queries']
        self.assertFalse(set(train)&{r['text'] for r in cases})
        results=json.loads((RUN/'predictions.json').read_text())
        scores=self.s.forward(w,self.s.encode([r['text'] for r in cases]))
        for i,row in enumerate(results):
            eligible=[j for j,s in enumerate(cat['senses']) if s['root']==row['root']]
            order=sorted(eligible,key=lambda j:(-float(scores[i,j]),meta['sense_ids'][j]))
            self.assertEqual(row['neural']['ranked_ids'],[meta['sense_ids'][j] for j in order])

    def test_scores_never_enter_native_owner_or_drop_senses(self):
        import numpy as np
        scores=np.zeros((1,18));scores[0,4]=1
        marker={'native_checked':False,'status':'VERIFICATION_UNAVAILABLE','rows':[]}
        with patch.object(self.s,'forward',return_value=scores),patch.object(self.s.testimony,'assess',return_value=marker) as call:
            result=self.s.propose('قلم للكتابة','قلم',RUN,['الذي يكتب به'])
        call.assert_called_once_with('قلم',['الذي يكتب به'])
        self.assertEqual(len(result['ranking']),3)
        self.assertEqual(result['ranking'][0]['sense_id'],'lisan:qalam-gambling')
        self.assertIs(result['conditional_testimony'],marker)
        self.assertEqual(result['authority'],'NONE')
        self.assertFalse(result['intended_sense_established'])

    def test_invalid_inputs_before_checker(self):
        with patch.object(self.s.testimony,'assess') as call:
            for text,entry,target in [('', 'قلم',[]),('abc','قلم',[]),('قلم',True,[]),('قلم','قلم',[True]),('قلم','قلم',['x']*65),('قلم'*3000,'قلم',[])]:
                with self.assertRaises(ValueError):self.s.propose(text,entry,RUN,target)
            call.assert_not_called()

    def test_model_rejects_identity_shape_and_nonfinite_changes(self):
        import numpy as np
        w,meta,_=self.s.load_model(RUN)
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            for mutation in ['labels','nan','shape','weights_hash']:
                m=copy.deepcopy(meta);v={k:a.copy() for k,a in w.items()}
                if mutation=='labels':m['sense_ids'].reverse()
                if mutation=='nan':v['w1'][0,0]=float('nan')
                if mutation=='shape':v['w2']=v['w2'][:1]
                np.savez(tmp/'weights.npz',**v)
                m['weights_sha256']=self.s.digest((tmp/'weights.npz').read_bytes()) if mutation!='weights_hash' else '0'*64
                (tmp/'model.json').write_text(json.dumps(m))
                with self.assertRaises(ValueError):self.s.load_model(tmp)

    def test_unknown_root_not_mapped_to_nearest_known_root(self):
        with patch.object(self.s.testimony,'assess',return_value={'native_checked':False}):
            result=self.s.propose('الكتابة','غير مثبت',RUN)
        self.assertEqual(result['ranking'],[])
        self.assertEqual(result['status'],'UNMEASURED_ROOT')

    def test_text_identity_preserved(self):
        text='  قَلَمٌ\nللكتابة '
        with patch.object(self.s.testimony,'assess',return_value={'native_checked':False}):
            result=self.s.propose(text,'قلم',RUN)
        self.assertEqual(result['text'],text)
        self.assertEqual(result['text_sha256'],self.s.digest(text.encode()))


@unittest.skipUnless(HAS_NUMPY and os.environ.get('NABT_NEURAL_SENSES_NATIVE')=='1','dedicated native gate not configured')
class NativeNeuralSenses(unittest.TestCase):
    def test_all_native_senses_and_conditional_result_unchanged(self):
        from tools.lexical_training.senses import propose
        from tools.lexical_testimony import assess
        for text,root,target in [('أداة الكتابة','قلم',['الذي يكتب به']),('قبيلة عربية','فهم',['علم الشيء']),('حيوان سبع','أسد',['الشجاعة'])]:
            before=assess(root,target)
            result=propose(text,root,RUN,target)
            self.assertTrue(before['native_checked'])
            self.assertEqual(result['conditional_testimony'],before)
            self.assertEqual({r['sense_id'] for r in result['ranking']},{r['sense_id'] for r in before['rows']})
            self.assertFalse(result['intended_sense_established'])

    def test_deliberately_wrong_neural_winner_cannot_change_native_receipt(self):
        import numpy as np
        from tools.lexical_training import senses
        before=senses.testimony.assess('قلم',['الذي يكتب به'])
        scores=np.zeros((1,18));scores[0,4]=1
        with patch.object(senses,'forward',return_value=scores):
            after=senses.propose('أداة الكتابة','قلم',RUN,['الذي يكتب به'])
        self.assertTrue(before['native_checked'])
        self.assertEqual(after['ranking'][0]['sense_id'],'lisan:qalam-gambling')
        self.assertEqual(after['conditional_testimony'],before)

    def test_native_missing_does_not_become_success(self):
        from tools.lexical_training.senses import propose
        with patch('tools.lexical_testimony._native',side_effect=OSError('missing')):
            result=propose('أداة الكتابة','قلم',RUN)
        self.assertFalse(result['conditional_testimony']['native_checked'])
        self.assertEqual(result['conditional_testimony']['status'],'VERIFICATION_UNAVAILABLE')

    def test_full_report_replay_rejects_changed_text_or_authority(self):
        import subprocess,sys
        command=[sys.executable,'tools/propose_lexical_evidence.py','--text','أداة الكتابة','--root','قلم','--sense-model',str(RUN)]
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'report.json'
            report.write_bytes(subprocess.check_output(command,cwd=ROOT))
            subprocess.run(command+['--verify',str(report)],cwd=ROOT,check=True,capture_output=True)
            original=json.loads(report.read_text())
            for field,value in [('authority','ACCEPTED'),('text','أداة القمار'),
                                ('target',['الذي يكتب به']),('entry','فهم')]:
                changed=copy.deepcopy(original);changed[field]=value
                report.write_text(json.dumps(changed))
                self.assertNotEqual(subprocess.run(command+['--verify',str(report)],cwd=ROOT,capture_output=True).returncode,0)
