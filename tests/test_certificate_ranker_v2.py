"""Independent structural and native authority boundaries for ranker v2."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import train_certificate_ranker_v2 as v2


class StructuralProposalTests(unittest.TestCase):
    def setUp(self):
        self.source='سالم هو حكيم.\n'.encode()
        self.query='هل سالم هو عالم؟\n'.encode()
        self.cert=v2.ground.propose(self.source,self.query)

    def test_hard_negatives_evade_old_length_features_but_new_features_expose_them(self):
        original=v2.features(self.source,self.query,self.cert)
        for kind in ('bad_step_index','bad_clean_step_index','wrong_law'):
            with self.subTest(kind=kind):
                altered=v2.features(self.source,self.query,v2.mutate(self.cert,kind))
                self.assertEqual(original[:-2],altered[:-2])
                self.assertNotEqual(original[-2:],altered[-2:])

    def test_empty_trace_mutation_preserves_old_feature_lengths(self):
        cert=v2.ground.propose('إذا سالم هو حكيم فإن سالم هو عالم.\n'.encode(),self.query)
        self.assertEqual(cert['steps'],[])
        for kind in ('bad_step_index','bad_clean_step_index'):
            mutated=v2.mutate(cert,kind)
            self.assertFalse(v2.indices_in_bounds(mutated))
            self.assertEqual(len(mutated['known']),len(mutated['steps']))
            self.assertEqual(len(mutated['clean_known']),len(mutated['clean_steps']))

    def test_index_type_and_bound_edges(self):
        self.assertTrue(v2.indices_in_bounds(self.cert))
        for value in (-1,True,0.0,'0',1,1048576):
            c=deepcopy(self.cert);c['steps'][0]['index']=value
            self.assertFalse(v2.indices_in_bounds(c))
        self.assertFalse(v2.indices_in_bounds(None))

    def test_holdout_mutation_not_in_training_protocol(self):
        self.assertNotIn('bad_clean_step_index',v2.TRAIN_KINDS)
        self.assertIn('bad_clean_step_index',v2.VALIDATION_KINDS)
        protocol=json.loads((v2.ROOT/'evidence/certificate_ranker_v2/protocol.json').read_text())
        self.assertEqual(protocol['train_candidate_kinds'],v2.TRAIN_KINDS)
        self.assertEqual(protocol['validation_candidate_kinds'],v2.VALIDATION_KINDS)

    def test_no_mutation_changes_the_original_certificate(self):
        before=deepcopy(self.cert)
        for kind in v2.VALIDATION_KINDS:v2.mutate(self.cert,kind)
        self.assertEqual(before,self.cert)

    def test_unmeasured_or_boolean_labels_never_train(self):
        for measurement,label in [('UNMEASURED',None),('MEASURED',True),('MEASURED',False),('MEASURED',2)]:
            row={'measurement':measurement,'label':label,'features':[1.0]*len(v2.FEATURES)}
            with self.assertRaises(ValueError):v2.fit([row],epochs=1,learning_rate=.1,seed=1)

    def test_optimizer_changes_weights_reproducibly_from_independent_vectors(self):
        rows=[{'measurement':'MEASURED','label':y,'features':[1.0,float(y),*([0.0]*(len(v2.FEATURES)-2))]} for y in (0,1)]
        params={'epochs':30,'learning_rate':.1,'seed':2}
        w,curve=v2.fit(rows,**params)
        self.assertGreater(v2.prior.score(w,rows[1]['features']),v2.prior.score(w,rows[0]['features']))
        self.assertLess(curve[-1]['log_loss'],curve[0]['log_loss'])
        self.assertEqual((w,curve),v2.fit(rows,**params))

    def test_model_cannot_drop_candidates_or_promote_an_unmeasured_run(self):
        model={'schema':v2.SCHEMA,'features':v2.FEATURES,'weights':[0.0]*len(v2.FEATURES),'authority':'proposal-order-only'}
        with patch.object(v2.prior,'check',side_effect=[{'measurement':'MEASURED','label':1,'semantic_status':'UNKNOWN'}, {'measurement':'UNMEASURED','label':None,'semantic_status':None}]):
            result=v2.rank_and_check(self.source,self.query,[self.cert,self.cert],model,None)
        self.assertEqual(len(result['attempts']),2)
        self.assertIsNone(result['selected_original_index'])
        self.assertFalse(result['all_attempts_measured'])
        self.assertFalse(result['world_truth_established'])

    def test_existing_run_directory_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'keep').write_text('receipt')
            with self.assertRaises(FileExistsError):
                v2.execute(v2.ROOT/'evidence/certificate_ranker_v2/protocol.json',path,None)
            self.assertEqual((path/'keep').read_text(),'receipt')


class NativeRankingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker=v2.ROOT/'formal/.lake/build/bin/verifiedReading'
        if not cls.checker.is_file():raise unittest.SkipTest('native verifiedReading unavailable')

    def test_fresh_lean_rejects_every_new_hard_mutation(self):
        source='سالم هو حكيم.\n'.encode();query='هل سالم هو عالم؟\n'.encode()
        cert=v2.ground.propose(source,query)
        for kind in ('wrong_law','bad_step_index','bad_clean_step_index','original'):
            with self.subTest(kind=kind):
                row=v2.prior.check(source,query,v2.mutate(cert,kind),self.checker)
                self.assertEqual(row['measurement'],'MEASURED')
                self.assertEqual(row['label'],int(kind=='original'))
                if kind=='original':self.assertEqual(row['semantic_status'],'UNKNOWN')


if __name__=='__main__':unittest.main()
