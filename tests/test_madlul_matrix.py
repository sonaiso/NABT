"""Denotatum/word-kind separation and source-bound crosswalk regressions."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.arabic_training import madlul_matrix as m
from tools.entropy_framework.reuse_run import entry_command


class MadlulMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = m.matrix()

    def test_five_source_kinds_are_not_word_kinds(self):
        self.assertEqual([r['label_ar'] for r in self.matrix['kinds']],
                         ['معنى ليس لفظًا','لفظ مفرد مستعمل','لفظ مفرد مهمل',
                          'لفظ مركب مستعمل','لفظ مركب مهمل'])
        self.assertNotIn('noun',m.KIND_IDS)
        self.assertNotIn('verb',m.KIND_IDS)
        self.assertNotIn('particle',m.KIND_IDS)
        self.assertFalse(self.matrix['scope']['denotatum_classifier_implemented'])

    def test_letter_name_is_explicitly_a_metalinguistic_source_example(self):
        r=m.kind_by_code(2)
        self.assertEqual(r['anchor'],'s3.p412')
        self.assertEqual(r['object_family'],'LINGUISTIC_OBJECT')
        self.assertEqual(r['classification_authority'],'SOURCE_TAXONOMY_ONLY')

    def test_kind_code_does_not_accept_a116_or_truth_flags(self):
        for value in [True,False,-1,5,115,1.0,'2',None]:
            with self.subTest(value=value), self.assertRaises(ValueError):m.kind_by_code(value)

    def test_source_bytes_cannot_be_relabelled_as_a_new_edition(self):
        d=m._catalog();d['sources'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source bytes changed'):m._sources(d)

    def test_source_window_and_line_locator_must_agree(self):
        d=m._catalog()
        a=next(a for a in d['anchors'] if a['id']=='qatr.kinds')
        a['locator']['lines_inclusive'][0]+=1
        with self.assertRaisesRegex(ValueError,'line locator'):m._sources(d)

    def test_source_window_rejects_boolean_offsets(self):
        d=m._catalog();d['anchors'][0]['start']=False
        with self.assertRaises(ValueError):m._sources(d)

    def test_primary_text_and_engineering_interpretation_keep_distinct_authority(self):
        sources={s['id']:s for s in self.matrix['sources']}
        self.assertEqual(sources['s1']['role'],'RETAINED_PRIMARY_TEXT')
        self.assertEqual(sources['interpretation_design']['role'],'ENGINEERING_DESIGN_RECORD')
        self.assertEqual(len(self.matrix['interpretation_guards']),15)
        self.assertFalse(self.matrix['interpretation_authenticity_proved'])

    def test_all_owner_declarations_resolve_in_original_catalogue(self):
        report=self.matrix['proof_catalogue']
        self.assertEqual(report['status'],'RECORDED_COMPILED_SNAPSHOT_WITH_CURRENT_SOURCE_MATCH')
        self.assertEqual(len(report['resolved_declarations']),34)
        self.assertFalse(report['compiled_this_run'])

    def test_noun_sign_is_not_denotatum_classification(self):
        r=m.inspect_text('كَاتِبٌ')
        self.assertEqual(r['owner_reports']['text_morphology']['occurrences'][0]['axes']['kind']['candidates'],['noun'])
        self.assertEqual(r['denotatum']['candidate_kinds'],list(m.KIND_IDS))
        self.assertEqual(r['denotatum']['status'],'DEFER')
        self.assertEqual(r['world_truth'],'NOT_ESTABLISHED')

    def test_unknown_word_is_not_an_unused_expression(self):
        r=m.inspect_text('لفظغيرمثبت')
        self.assertEqual(len(r['denotatum']['candidate_kinds']),5)
        self.assertFalse(r['learning_achieved'])

    def test_quotation_does_not_supply_usedness_or_naming(self):
        r=m.inspect_text('«بِ»')
        self.assertEqual(r['denotatum']['status'],'DEFER')
        self.assertIn('SOURCE_BOUND_USAGE_CLASSIFICATION',r['denotatum']['missing'])

    def test_replay_binds_fresh_source_and_all_owner_reports(self):
        r=m.inspect_text('مِنْ')
        self.assertTrue(m.verify_inspection(r,text='مِنْ')['valid'])
        self.assertFalse(m.verify_inspection(r,text='هو')['valid'])
        changed=deepcopy(r);changed['denotatum']['status']='LICENSED'
        self.assertFalse(m.verify_inspection(changed,text='مِنْ')['valid'])
        changed=deepcopy(r);changed['owner_reports'].pop('derivation')
        self.assertFalse(m.verify_inspection(changed,text='مِنْ')['valid'])

    def test_reader_limits_are_not_a_language_rejection(self):
        for s in ['',True,'ب'*m.MAX_TEXT_BYTES]:
            with self.subTest(value=type(s).__name__), self.assertRaises(ValueError):m.inspect_text(s)

    def test_owner_failure_keeps_other_reports_and_exact_failure(self):
        r=m.inspect_text('ضَرَبَ عَمْرٌو زَيْدًا')
        self.assertEqual(set(r['owner_reports']),{'word','derivation'})
        self.assertEqual(r['owner_failures']['text_morphology']['code'],
                         'NONTERMINAL_OR_MULTIPLE_TANWIN')
        self.assertEqual(r['denotatum']['status'],'DEFER')
        self.assertTrue(m.verify_inspection(r,text='ضَرَبَ عَمْرٌو زَيْدًا')['valid'])
        changed=deepcopy(r);changed['owner_failures']={}
        self.assertFalse(m.verify_inspection(changed,text='ضَرَبَ عَمْرٌو زَيْدًا')['valid'])

    def test_unexpected_programming_failure_is_not_swallowed(self):
        with patch.object(m,'read_words',side_effect=RuntimeError('unexpected')):
            with self.assertRaisesRegex(RuntimeError,'unexpected'):m.inspect_text('باء')

    def test_installed_catalogue_cannot_be_mutated_silently(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'catalog.json';path.write_text('{}')
            with patch.object(m,'_path',return_value=path):
                with self.assertRaisesRegex(ValueError,'catalogue changed'):m._catalog()

    def test_crosswalk_forbids_surface_and_truth_shortcuts(self):
        rows={r['id']:r for r in self.matrix['rows']}
        self.assertIn('FATHA_IMPLIES_NASB',rows['R12']['forbidden_inference'])
        self.assertIn('FALSE_SENTENCE_IS_UNUSED_COMPOUND',rows['R18']['forbidden_inference'])
        self.assertIn('NO_OBSERVED_NOUN_SIGN_IMPLIES_PARTICLE',rows['R04']['forbidden_inference'])

    def test_existing_router_exposes_the_same_module(self):
        command=entry_command('madlul-matrix',['matrix'])
        self.assertIn('tools.arabic_training.madlul_matrix',command)


if __name__=='__main__':unittest.main()
