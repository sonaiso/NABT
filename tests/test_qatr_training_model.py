"""Optional learner boundary tests; native kernel tests have no Torch dependency."""
import importlib.util
import unittest

TORCH=importlib.util.find_spec('torch') is not None and importlib.util.find_spec('numpy') is not None

@unittest.skipUnless(TORCH,'optional pinned torch/numpy required')
class QatrModelTests(unittest.TestCase):
    def setUp(self):
        import torch
        torch.set_num_threads(1);torch.manual_seed(7)
        from tools.qatr_training.model import QatrModel
        self.torch=torch
        self.vocab=dict(words=['<PAD>','<UNK>','رَجُلٌ'],chars=['<PAD>','<UNK>','ر','َ','ج','ُ','ل','ٌ'],readings=['noun:damma','noun:kasra'])
        self.model=QatrModel(self.vocab)

    def test_character_padding_and_batch_neighbor_do_not_change_prediction(self):
        t=self.torch;self.model.eval()
        words=t.tensor([[2]]);chars=t.tensor([[[2,3,4,5,6,7]]]);lengths=t.tensor([1])
        with t.no_grad():
            a=self.model(words,chars,lengths)
            b=self.model(words,t.nn.functional.pad(chars,(0,12)),lengths)
        for x,y in zip(a,b,strict=True):self.assertTrue(t.allclose(x,y,atol=1e-6))

    def test_gold_changes_labels_not_inputs(self):
        from tools.qatr_training.experiment import encode
        import copy
        e=dict(id='1:1',words=[dict(text='رَجُلٌ',qatr='noun:damma',case='raf')])
        f=copy.deepcopy(e);f['words'][0].update(qatr='noun:kasra',case='jarr')
        a,b=encode([e,f],self.vocab)
        self.assertEqual(a['words'],b['words']);self.assertEqual(a['chars'],b['chars'])
        self.assertNotEqual(a['readings'],b['readings']);self.assertNotEqual(a['cases'],b['cases'])

    def test_actual_gradient_update(self):
        t=self.torch;self.model.train()
        before=self.model.reading_head.weight.detach().clone()
        optimizer=t.optim.AdamW(self.model.parameters(),lr=.01)
        a,b=self.model(t.tensor([[2]]),t.tensor([[[2,3,4,5,6,7]]]),t.tensor([1]))
        loss=t.nn.functional.cross_entropy(a.reshape(1,2),t.tensor([0]))+t.nn.functional.cross_entropy(b.reshape(1,4),t.tensor([1]))
        optimizer.zero_grad();loss.backward();optimizer.step()
        self.assertFalse(t.equal(before,self.model.reading_head.weight))
