"""Independent trace, ambiguity and withdrawal checks for source recovery."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt.alphabet import parse_word, ALPHABET_ID
from nabt.codec import decode_number
from nabt.errors import NabtError
from tools.arabic_training import source_reading as r
from tools.lexical_training import shared_encoder as s, contextual_alignment as a
from tools.grammar_catalog import orchestration as o, gateway
from tools.evidence_lifecycle_v1 import ResourceLimit

ROOT=s.ROOT
READY=all((ROOT/'formal/.lake/build/bin'/n).is_file() for n in
          ('alignedAcquisition','progressiveUnitProbe','lexicalDenotation'))
if os.environ.get('NABT_REQUIRE_ORCHESTRATION_NATIVE')=='1' and not READY:
    raise RuntimeError('Source reading requires its native owners')


class SourceWindows(unittest.TestCase):
    def test_partition_restores_every_byte_and_never_splits_terms(self):
        from tools.grammar_catalog.operations import exact_terms
        for text in ('قَلَمٌ، '*40, 'قلم'+' '*600+'قلم', '😀، قُمْتُ\n'*30):
            windows=s.source_windows(text)
            self.assertEqual(''.join(w['text'] for w in windows),text)
            self.assertGreater(len(windows),1)
            for w in windows:
                start,end=w['utf8_span']
                self.assertLessEqual(end-start,256)
                self.assertEqual(text.encode()[start:end].decode(),w['text'])
                self.assertEqual(sha256(w['text'].encode()).hexdigest(),w['sha256'])
            for t in exact_terms(text):
                self.assertEqual(sum(w['utf8_span'][0]<=t['utf8_span'][0] and
                    t['utf8_span'][1]<=w['utf8_span'][1] for w in windows),1)

    def test_window_limits_are_not_truncation(self):
        for text in ('قلم '*129, 'قلم'+' '*8192):
            with self.assertRaises(ResourceLimit):s.source_windows(text)
        with self.assertRaises(ValueError):s.source_windows('ا'*129)

    def test_long_occurrences_keep_original_positions_and_no_global_head(self):
        text='قَلَمٌ، '*24
        model,_=s.load_model()
        rows,heads=a.occurrence_vectors(model,text)
        self.assertEqual(len(rows),24);self.assertIsNone(heads)
        for row in rows:
            start,end=row['utf8_span']
            self.assertEqual(text.encode()[start:end].decode(),row['surface'])
            self.assertIn('context_window',row)

    def test_short_trajectory_is_unchanged(self):
        text='كَتَبَ قُمْتُ';model,_=s.load_model()
        rows,heads=a.occurrence_vectors(model,text)
        f=s.states_for_ids(model,s.byte_ids(text))
        b=s.states_for_ids(model,list(reversed(s.byte_ids(text))))
        for row in rows:
            start,end=row['utf8_span'];n=len(text.encode())
            self.assertEqual(row['vector'],f[start]+f[end]+b[n-end]+b[n-start])
        self.assertEqual(heads,s.logits(model,text))


class CellIdentity(unittest.TestCase):
    def test_kernel_cells_are_exact_network_input(self):
        for word in ('كَتَبَ','كُتِبَ','قُمْتُ','قُمْتَ','قُمْتِ'):
            cells=parse_word(word)
            self.assertEqual([i-1 for i in s.cell_ids(cells)],list(cells))
        for cells in ([True],[116],[-1],[]):
            with self.assertRaises((ValueError,NabtError)):s.cell_ids(cells)

    def test_heldout_predictions_recompute_from_shipped_weights(self):
        model,identity=s.load_cell_model()
        report=json.loads((s.CELL_MODEL.parent/'FIRST_TEST.json').read_text())
        train=json.loads((s.CELL_MODEL.parent/'train.json').read_text())
        test=json.loads((s.CELL_MODEL.parent/'test_predictions.json').read_text())
        self.assertFalse({r['root'] for r in train}&{r['root'] for r in test})
        self.assertEqual(identity,report['weights_sha256'])
        self.assertEqual(len(test),13)
        for row in test:
            self.assertEqual(row['cells'],list(parse_word(row['text'])))
            scores=s.cell_logits(model,row['cells'])
            predicted={h:model['labels'][h][max(range(len(v)),key=v.__getitem__)] for h,v in scores.items()}
            self.assertEqual(predicted,row['predicted'])
        for h in s.CELL_HEADS:
            self.assertEqual(report['metrics'][h]['correct'],sum(x['predicted'][h]==x['labels'][h] for x in test))
        self.assertLess(report['portable_max_abs_error'],1e-4)
        self.assertFalse(report['world_truth_established'])

    def test_alphabet_tensor_and_training_mutations_are_rejected(self):
        model,_=s.load_cell_model()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.json'
            train=Path(directory)/'train.json'
            train.write_bytes(s.CELL_MODEL.with_name('train.json').read_bytes())
            for key,value in (('alphabet_id','foreign'),('authority','ACCEPT'),('parameters',{})):
                changed=deepcopy(model);changed[key]=value;path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):s.load_cell_model(path)
            path.write_text(json.dumps(model));train.write_text('[]')
            with self.assertRaisesRegex(ValueError,'provenance'):s.load_cell_model(path)

    def test_existing_marks_and_carriers_cannot_be_silently_changed(self):
        self.assertTrue(r.compatible('كتب','كَتَبَ'))
        self.assertFalse(r.compatible('كُتب','كَتَبَ'))
        self.assertFalse(r.compatible('أكل','اَكَلَ'))
        self.assertIsNone(r.substitution('كَتب','كُتِبَ'))
        self.assertEqual(r.substitution('حكيط','حَكِيمٌ')['observed'],'ط')
        self.assertIsNone(r.substitution('حكم','حَكِيمٌ'))


@unittest.skipUnless(READY,'build native source owners')
class SourceReading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'examples/awamil_agent/nominal.json').read_text())
        cls.p.update(text='زيد حكيم',source_id='source_reading_test')
        cls.reading=r.analyze(cls.p['text'],source_id=cls.p['source_id'],lexical_text=cls.p['lexical_text'])

    def test_shared_proposal_processes_every_window_without_a_global_score(self):
        text='قَلَمٌ، '*24
        result=s.propose({'text':text})
        self.assertEqual(result['status'],'PROPOSED',result)
        self.assertEqual(result['heads'],{})
        self.assertEqual(''.join(w['text'] for w in result['window_proposals']),text)
        self.assertFalse(result['cross_window_context_established'])

    def test_all_diacritizations_keep_two_occurrences_and_spacing(self):
        sources=self.reading['derived_sources']
        self.assertEqual({c['text'] for c in sources},
            {'زَيْدٌ حَكِيمٌ','زَيْدٌ حَكِيمٍ','زَيْدٍ حَكِيمٌ','زَيْدٍ حَكِيمٍ'})
        self.assertEqual([x['utf8_span'] for x in self.reading['occurrences']],[[0,6],[7,15]])
        for row in self.reading['occurrences']:
            for alt in row['alternatives']:
                self.assertEqual(list(decode_number(int(alt['unit_n_decimal']))),alt['cells'])
                self.assertEqual(alt['neural_input_ids'],s.cell_ids(alt['cells']))
                self.assertEqual(alt['alphabet_id'],ALPHABET_ID)
                self.assertFalse(alt['intended_reading_established'])

    def test_lexical_withdrawal_and_unresolved_words_remain_visible(self):
        result=r.analyze(self.p['text'])
        self.assertEqual(result['derived_sources'],[])
        self.assertEqual(result['branch_status'],'UNRESOLVED_WORDS')
        self.assertTrue(result['source_restored'])

    def test_spelling_suggestion_is_explicit_and_lexically_supported(self):
        result=r.analyze('حكيط',lexical_text=self.p['lexical_text'])
        alts=result['occurrences'][0]['alternatives']
        self.assertIn('حَكِيمٌ',{a['surface'] for a in alts})
        self.assertEqual(result['source_text'],'حكيط')
        for alt in alts:
            self.assertTrue(alt['lexical_supports'])
            self.assertEqual(alt['interpretation_scope'],'CONDITIONAL_SPELLING')
            self.assertFalse(alt['spelling_edit']['original_is_error_established'])

    def test_model_withdrawal_does_not_suppress_native_alternatives(self):
        with patch.object(s,'load_cell_model',side_effect=FileNotFoundError):
            result=r.analyze(self.p['text'],lexical_text=self.p['lexical_text'])
        self.assertEqual(result['derived_sources'],self.reading['derived_sources'])
        self.assertEqual(result['model_error'],'FileNotFoundError')

    def test_branch_budget_retains_word_alternatives(self):
        with patch.object(r,'MAX_BRANCHES',2):
            result=r.analyze(self.p['text'],lexical_text=self.p['lexical_text'])
        self.assertEqual(result['derived_sources'],[])
        self.assertEqual(result['candidate_product'],4)
        self.assertTrue(all(len(x['alternatives'])==2 for x in result['occurrences']))

    def test_gateway_replays_conditional_sources_without_parent_promotion(self):
        request={'schema':gateway.REQUEST_SCHEMA,'route':'cognitive.orchestrate','payload':self.p}
        receipt=gateway.run(request)
        self.assertEqual(receipt['status'],'EXECUTED',receipt['execution'])
        result=receipt['execution']['owner_result']
        self.assertEqual(result['stopped_at'],'orthography')
        self.assertEqual(len(result['conditional_readings']),4)
        self.assertIn('concept',{x['result']['stopped_at'] for x in result['conditional_readings']})
        for branch in result['conditional_readings']:
            self.assertEqual(branch['result']['dispatch_ledger'][0]['name'],'orthography')
            self.assertFalse(branch['parent_claim_promoted'])
            self.assertFalse(branch['result']['world_truth_established'])
        self.assertTrue(gateway.accept_output(receipt,expected_request=request)['valid'])
        altered=deepcopy(request);altered['payload']['text']='زيد حليم'
        self.assertFalse(gateway.accept_output(receipt,expected_request=altered)['valid'])


if __name__=='__main__':unittest.main()
