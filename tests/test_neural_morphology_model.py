"""Optional learner checks; the dedicated neural CI job must run these."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HAS_TORCH=importlib.util.find_spec('torch') is not None


@unittest.skipUnless(HAS_TORCH,'optional neural training environment not installed')
class NeuralMorphologyModelTests(unittest.TestCase):
    def setUp(self):
        import torch
        from tools.arabic_training.model_v2 import MaskedMorphologyModel as MorphologyModel
        torch.set_num_threads(1)
        torch.manual_seed(47)
        self.vocab=dict(words=['<PAD>','<UNK>','كَتَبَ','زَيْدٌ'],chars=['<PAD>','<UNK>',*sorted(set('كَتَبَزَيْدٌ'))],
                        labels=dict(tag=['NOUN_PROP','PV'],declension=['معرب','مبني'],case_mood=['مرفوع','مبني']),affixes=['PRON'])
        self.model=MorphologyModel(self.vocab)
        self.example=dict(id='1:1',sura=1,split='train',words=[dict(text='كَتَبَ',labels=dict(tag='PV',declension='مبني',case_mood='مبني'),affixes=[])])
        self.receipt=dict(files={'weights.npz':'example-only'})

    def test_training_cli_defaults_to_corrected_observed_test_protocol(self):
        from unittest.mock import patch
        from tools.train_arabic_morphology import main,ROOT
        with patch('sys.argv',['train_arabic_morphology','--source','corpus.csv','--output-dir','new-run']), patch('tools.arabic_training.experiment.train') as train:
            main()
        selected=train.call_args.args[2]
        protocol=json.loads(selected.read_text())
        self.assertEqual(protocol['model_architecture'],'char-valid-mask-v2')
        self.assertTrue(protocol['test_previously_observed'])
        legacy=ROOT/'evidence/source_morphology_training/protocol.json'
        with patch('sys.argv',['train_arabic_morphology','--source','corpus.csv','--output-dir','legacy-replay','--protocol',str(legacy)]), patch('tools.arabic_training.experiment.train') as train:
            main()
        self.assertEqual(train.call_args.args[2],legacy)

    def test_weight_roundtrip_and_invalid_shape_rejected(self):
        import numpy as np
        import torch
        from tools.arabic_training.model import save_weights,load_weights
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'weights.npz'
            before={k:v.clone() for k,v in self.model.state_dict().items()}
            save_weights(self.model,path)
            with torch.no_grad():
                next(self.model.parameters()).add_(1)
            load_weights(self.model,path)
            self.assertTrue(all(torch.equal(v,self.model.state_dict()[k]) for k,v in before.items()))
            arrays={k:v.numpy() for k,v in before.items()}
            arrays['word_embedding.weight']=np.zeros((1,1),dtype=np.float32)
            np.savez_compressed(path,**arrays)
            with self.assertRaisesRegex(ValueError,'invalid weight'):
                load_weights(self.model,path)

    def test_no_gold_feature_leakage_and_no_eval_vocabulary(self):
        from copy import deepcopy
        from tools.arabic_training.experiment import encode,vocabulary
        other=deepcopy(self.example)
        other['words'][0]['labels']['tag']='UNSEEN_LABEL'
        first,second=encode([self.example,other],self.vocab)
        self.assertEqual(first['words'],second['words'])
        self.assertEqual(first['chars'],second['chars'])
        other['split']='test'
        with self.assertRaises(ValueError):
            vocabulary([other])

    def test_unseen_test_label_is_wrong_not_dropped(self):
        from copy import deepcopy
        from tools.arabic_training.experiment import evaluate
        example=deepcopy(self.example)
        example['words'][0]['labels']['tag']='UNSEEN_LABEL'
        prediction=dict(tag='PV',declension='مبني',case_mood='مبني',affixes=[])
        metric=evaluate([example],{'1:1':[prediction]},set())
        self.assertEqual(metric['tasks']['tag']['total'],1)
        self.assertEqual(metric['tasks']['tag']['accuracy'],0)
        self.assertEqual(metric['tasks']['tag']['per_class']['UNSEEN_LABEL']['recall'],0)

    def test_real_gradient_updates_parameters(self):
        import torch
        from tools.arabic_training.experiment import encode,collate
        w,c,l,y,*_=collate(encode([self.example],self.vocab),1)
        self.model.eval()
        optimizer=torch.optim.AdamW(self.model.parameters(),lr=.01)
        before=torch.nn.functional.cross_entropy(self.model(w,c,l)['tag'].flatten(0,1),y['tag'].flatten()).item()
        for _ in range(8):
            optimizer.zero_grad()
            loss=torch.nn.functional.cross_entropy(self.model(w,c,l)['tag'].flatten(0,1),y['tag'].flatten())
            loss.backward(); optimizer.step()
        self.assertLess(float(loss.detach()),before/2)

    def test_character_padding_cannot_change_logits_or_gradients(self):
        import torch
        self.model.eval()
        word=torch.tensor([[2]])
        short=torch.tensor([[[2,3,0]]])
        long=torch.tensor([[[2,3,0,0,0,0,0,0]]])
        length=torch.tensor([1])
        a=self.model(word,short,length)
        b=self.model(word,long,length)
        for task in a:
            torch.testing.assert_close(a[task],b[task],rtol=0,atol=1e-7)
        a['tag'].sum().backward()
        before={k:v.grad.clone() for k,v in self.model.named_parameters() if v.grad is not None}
        self.model.zero_grad()
        b['tag'].sum().backward()
        for k,v in self.model.named_parameters():
            if k in before:
                torch.testing.assert_close(before[k],v.grad,rtol=0,atol=1e-7)

    def test_offsets_ambiguity_and_no_proof_authority(self):
        from tools.arabic_training.proposal import propose
        self.model.eval()
        raw='  كَتَبَ\tزَيْدٌ\nكتب '.encode()
        result=propose(raw,self.model,self.vocab,self.receipt)
        self.assertFalse(result['readings_licensed'])
        self.assertFalse(result['alternatives_complete'])
        self.assertEqual(result['authority'],'NONE')
        self.assertEqual(len(result['tokens']),3)
        for token in result['tokens']:
            self.assertEqual(raw[token['start_byte']:token['end_byte']].decode(),token['text'])
        self.assertEqual(len(result['tokens'][0]['candidates']['tag']),2)
        self.assertEqual(result['tokens'][2]['status'],'UNKNOWN_INPUT_DOMAIN')

    def test_limits_invalid_input_and_checksum_are_distinct(self):
        from tools.arabic_training.proposal import propose,load_bundle
        self.assertEqual(propose(b'\xff',self.model,self.vocab,self.receipt)['status'],'INVALID_INPUT')
        self.assertEqual(propose(('بَ'*20).encode(),self.model,self.vocab,self.receipt)['status'],'RESOURCE_LIMIT')
        self.assertEqual(propose(b'',self.model,self.vocab,self.receipt)['status'],'INVALID_INPUT')
        for word in ('١َ','كَتَبَ،'):
            self.assertEqual(propose(word.encode(),self.model,self.vocab,self.receipt)['tokens'][0]['status'],'UNKNOWN_INPUT_DOMAIN')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'bundle.json').write_text(json.dumps(dict(files={'weights.npz':'wrong'})))
            (p/'weights.npz').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'checksum'):
                load_bundle(p)

    def test_malformed_marks_are_rejected_before_model_execution(self):
        from unittest.mock import patch
        from tools.arabic_training.proposal import propose
        # A source error has no per-token model proposal. This is distinct
        # from a well-formed token outside the learner's input domain.
        for text in ('َ', 'َكَتَبَ', 'كَُتَبَ', 'كََتَبَ', 'كّّتَبَ'):
            with self.subTest(text=text), patch.object(self.model, 'forward') as forward:
                result = propose(text.encode(), self.model, self.vocab, self.receipt)
                self.assertEqual(result['status'], 'INVALID_INPUT')
                self.assertEqual(result['tokens'], [])
                self.assertEqual(result['authority'], 'NONE')
                self.assertFalse(result['readings_licensed'])
                self.assertFalse(result['alternatives_complete'])
                forward.assert_not_called()


if __name__=='__main__':
    unittest.main()
