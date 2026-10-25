"""Independent boundary examples for the native semantic checker."""
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
EXE=os.environ.get('NABT_LEXICAL_DENOTATION')

@unittest.skipUnless(EXE,'native lexicalDenotation executable not configured')
class NativeDenotation(unittest.TestCase):
    def query(self,root,target,proposed=None):
        request={'root':root,'target':target,'proposed_ids':proposed}
        run=subprocess.run([EXE],input=json.dumps(request,ensure_ascii=False)+'\n',text=True,capture_output=True,check=True)
        return json.loads(run.stdout)

    def test_installed_catalog_matches_every_byte_and_component(self):
        exported=json.loads(subprocess.check_output([EXE,'--export'],text=True))
        catalog=json.loads((ROOT/'evidence/lexical_denotation/catalog.json').read_text())
        for name,keys in [('senses',['id','root','citation','components']),('necessities',['sense_id','target','kind','citation'])]:
            self.assertEqual(exported[name],[{k:r[k] for k in keys} for r in catalog[name]])

    def test_whole_and_proper_part(self):
        whole=self.query('بيت',['مجمع الشمل','المآب','المأوى'])
        part=self.query('بيت',['المأوى'])
        self.assertEqual(whole['rows'][0]['indications'],['mutabaqa'])
        self.assertEqual(part['rows'][0]['indications'],['tadammun'])

    def test_duplicate_does_not_create_an_extra_part(self):
        self.assertEqual(self.query('فرس',['واحد الخيل','واحد الخيل'])['common_indications'],['mutabaqa'])

    def test_words_inside_gloss_are_not_semantic_parts(self):
        for root,target in [('فهم','القلب'),('سمع','الأذن'),('قلم','يكتب')]:
            r=self.query(root,[target])
            self.assertNotIn('tadammun',r['common_indications'])
            self.assertTrue(all('tadammun' not in x['indications'] for x in r['rows']))

    def test_two_sources_do_not_make_same_root_same_sense(self):
        r=self.query('فهم',['علم الشيء'])
        self.assertEqual(len(r['rows']),3)
        self.assertEqual(r['common_indications'],[])
        self.assertEqual(sum('mutabaqa' in x['indications'] for x in r['rows']),1)

    def test_all_installed_qalam_senses_retained(self):
        ids=['lisan:qalam-writing','lisan:qalam-lot','lisan:qalam-gambling']
        r=self.query('قلم',['الذي يكتب به'],ids)
        self.assertEqual([x['sense']['id'] for x in r['rows']],ids)
        self.assertTrue(r['complete_installed_proposal'])
        self.assertFalse(self.query('قلم',['الذي يكتب به'],ids[:1])['complete_installed_proposal'])
        self.assertFalse(r['all_arabic_senses_enumerated'])
        self.assertEqual(r['common_indications'],[])

    def test_blindness_mental_association_is_not_external_sight(self):
        r=self.query('عمي',['البصر'])
        self.assertEqual(r['common_indications'],['iltizam'])
        self.assertFalse(r['world_truth_asserted'])
        self.assertNotIn('mutabaqa',r['common_indications'])

    def test_no_inverse_or_unrelated_association(self):
        self.assertEqual(self.query('بصر',['ذهاب البصر كله'])['common_indications'],[])
        self.assertEqual(self.query('أسد',['العدالة'])['common_indications'],[])

    def test_empty_target_and_unknown_root(self):
        self.assertEqual(self.query('بيت',[])['common_indications'],[])
        r=self.query('غير مثبت',['المأوى'],[])
        self.assertEqual(r['status'],'UNMEASURED_ROOT')
        self.assertFalse(r['complete_installed_proposal'])

    def test_strict_types_limits_and_extra_authority_flag(self):
        requests=[{'root':'بيت','target':[True],'proposed_ids':None},
                  {'root':'بيت','target':['المأوى'],'proposed_ids':None,'authority':True},
                  {'root':'','target':[],'proposed_ids':None},
                  {'root':'بيت','target':['x']*65,'proposed_ids':None}]
        run=subprocess.run([EXE],input='\n'.join(json.dumps(r) for r in requests)+'\n',text=True,capture_output=True,check=True)
        rows=[json.loads(s) for s in run.stdout.splitlines()]
        self.assertEqual(len(rows),4)
        self.assertTrue(all('status' in r and 'rows' not in r for r in rows))

class ArtifactIntegrity(unittest.TestCase):
    def test_retained_source_spans_are_bytes_not_characters(self):
        from tools.lexical_training.data import digest
        catalog=json.loads((ROOT/'evidence/lexical_denotation/catalog.json').read_text())
        for s in catalog['senses']:
            c=s['citation']
            self.assertEqual(c['end_byte']-c['start_byte'],len(c['quotation'].encode()))
            self.assertIn('AUTHORED',s['interpretation_status'])
        for book,path in [('maqayis','evidence/classical_language/sources/maqayis.txt'),('shakhsiyya3','evidence/mantuq_mafhum/sources/shakhsiyya3.txt')]:
            data=(ROOT/path).read_bytes()
            citations=[s['citation'] for s in catalog['senses']+catalog['necessities'] if s['citation']['work']==book]
            for c in citations:
                self.assertEqual(digest(data),c['source_sha256'])
                self.assertEqual(data[c['start_byte']:c['end_byte']],c['quotation'].encode())

    def test_root_splits_and_first_test_are_consistent(self):
        from tools.lexical_training.data import digest
        run=ROOT/'evidence/lexical_denotation/run_01'
        manifest=json.loads((run/'split_manifest.json').read_text())
        training=json.loads((run/'training.json').read_text())
        first=json.loads((run/'FIRST_TEST.json').read_text())
        pred=json.loads((run/'predictions.json').read_text())
        self.assertEqual(len({x['key'] for x in manifest}),len(manifest))
        self.assertEqual(training['manifest_sha256'],digest(json.dumps(manifest,ensure_ascii=False,sort_keys=True).encode()))
        self.assertEqual(first['weights_sha256'],digest((run/'weights.pt').read_bytes()))
        self.assertEqual({x['root'] for x in pred},{x['key'] for x in manifest if x['split']=='test'})
        self.assertGreater(training['embedding_delta_l2_final'],0)
        self.assertGreater(training['updates'],0)
        self.assertEqual(first['source_truth'],'UNMEASURED')
        self.assertEqual(first['sense_equivalence'],'UNMEASURED')
        for label,key in [('selected','selected_rank'),('neural_only','neural_rank'),('baseline','baseline_rank')]:
            self.assertEqual(first[label]['top1'],sum(x[key]==1 for x in pred)/len(pred))

if __name__=='__main__':unittest.main()
