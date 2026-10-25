"""Independently written authored diagnostics; not a blind corpus score."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.errors import NabtError
from nabt.imperative_paradigm import LAW_ID, replay_policy
from nabt.person_evidence import person_candidates
from test_person_evidence import corpus, verb, pronoun


class ImperativeParadigmTests(unittest.TestCase):
    def read(self, target, form='yakotubu', root='ktb', lemma='kataba', extra='', excluded=()):
        model = learn_qac_lexicon(corpus([verb(form, root=root, lemma=lemma, extra=extra)]), excluded_verses=excluded)
        return person_candidates(target, lexical_model=model)

    def test_independent_three_vowel_paradigms(self):
        cases = [
            ('yakotubu', 'ktb', 'kataba', [('اُكْتُبِي', {'2FS'}), ('اُكْتُبَا', {'2MD','2FD'}),
                                         ('اُكْتُبُوا', {'2MP'}), ('اُكْتُبْنَ', {'2FP'})]),
            ('yaDoribu', 'Drb', 'Daraba', [('اِضْرِبِي', {'2FS'}), ('اِضْرِبَا', {'2MD','2FD'}),
                                        ('اِضْرِبُوا', {'2MP'}), ('اِضْرِبْنَ', {'2FP'})]),
            ('yafo taHu'.replace(' ',''), 'ftH', 'fataHa', [('اِفْتَحِي', {'2FS'}), ('اِفْتَحَا', {'2MD','2FD'}),
                                                        ('اِفْتَحُوا', {'2MP'}), ('اِفْتَحْنَ', {'2FP'})]),
        ]
        for form, root, lemma, targets in cases:
            for target, expected in targets:
                with self.subTest(target=target):
                    rows=self.read(target, form, root, lemma)
                    self.assertEqual({r['profile_id'] for r in rows}, expected)
                    self.assertTrue(all(r['aspect']=='IMPV' and r['construction']=='built' for r in rows))

    def test_target_person_and_number_do_not_resolve_addressee(self):
        rows=self.read('اُكْتُبَا')
        self.assertEqual({(r['person_name'],r['gender_name'],r['number_name']) for r in rows},
                         {('addressee','masculine','dual'),('addressee','feminine','dual')})
        self.assertTrue(all(r['valency_witnesses']==[] for r in rows))

    def test_subject_nun_is_never_deleted_inflection_nun(self):
        row=self.read('اُكْتُبْنَ')[0]
        nun,=row['nun_readings']
        self.assertEqual((nun['kind'],nun['surface'],nun['realization']),('feminine_subject','نَ','present'))
        for surface in ('اُكْتُبِي','اُكْتُبَا','اُكْتُبُوا'):
            for other in self.read(surface):
                n,=other['nun_readings']
                self.assertEqual(n['kind'],'five_verb_raf')
                self.assertEqual(n['realization'],'deleted')
                self.assertIsNone(n['span'])

    def test_nun_final_feminine_plural_defers_until_assimilation_is_licensed(self):
        for surface in ('اُسْكُنْنَ','اُسْكُنَّ'):
            self.assertEqual(self.read(surface,'yasokunu','skn','sakana'),[])
        for surface in ('اُسْكُنِي','اُسْكُنَا','اُسْكُنُوا'):
            rows=self.read(surface,'yasokunu','skn','sakana')
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual([n['kind'] for n in row['nun_readings']],['radical','five_verb_raf'])
                self.assertEqual(row['nun_readings'][0]['realization'],'present')
                self.assertEqual(row['nun_readings'][1]['realization'],'deleted')

    def test_source_withdrawal_all_profiles(self):
        for target in ('اُكْتُبِي','اُكْتُبَا','اُكْتُبُوا','اُكْتُبْنَ'):
            self.assertEqual(self.read(target, excluded=('1:1',)),[])

    def test_wrong_marks_carriers_and_inflection_nun(self):
        for target in ('اِكْتُبِي','اُكْتِبِي','اُكْتُبْي','اُكْتُبَيْ','اُكْتُبُا',
                       'اُكْتُبِيْ','اُكْتُبُو','اُكْتُبُوَا','اُكْتُبُونَ','اُكْتُبِينَ',
                       'اُكْتُبَانِ','اُكْتُبَنَ','اُكْتُبْنْ','اكتبوا','اكْتُبَا'):
            self.assertEqual(self.read(target),[],target)

    def test_original_medial_vowel_controls_ibtida(self):
        self.assertEqual(self.read('اُضْرِبُوا','yaDoribu','Drb','Daraba'),[])
        self.assertTrue(self.read('اِضْرِبُوا','yaDoribu','Drb','Daraba'))

    def test_no_productive_objects_without_attested_suffix_word(self):
        for target in ('اُكْتُبُوهُ','اُكْتُبَاهُ','اُكْتُبِيهِ','اُكْتُبْنَهُ'):
            self.assertEqual(self.read(target),[])

    def test_attested_object_needs_independent_imperfect_host(self):
        original=[verb('yakotubu')]
        attached=[verb('Aukotubu','2MP','IMPV'),pronoun('w','2MP'),pronoun('hu','3MS')]
        model=learn_qac_lexicon(corpus(original,attached))
        rows=person_candidates('اُكْتُبُوهُ',lexical_model=model)
        self.assertTrue(rows)
        self.assertTrue(all(r['segmentation_licensed'] for r in rows))
        self.assertTrue(all('SEPARATOR_ALIF_OMITTED_BEFORE_ATTACHED_PRONOUN' in r['rule_ids'] for r in rows))
        self.assertTrue(all(r['attached_pronouns'][0]['licensed'] for r in rows))
        for row in rows:
            self.assertEqual(row['host_form'],'اُكْتُبُو')
            self.assertEqual(row['productive_derivation']['generated_form'],'اُكْتُبُوا')
        withdrawn=learn_qac_lexicon(corpus(original,attached),excluded_verses=('1:1',))
        self.assertFalse(any(r['segmentation_licensed'] for r in person_candidates('اُكْتُبُوهُ',lexical_model=withdrawn)))

    def test_attachment_never_inserts_separator_before_object(self):
        original=[verb('yakotubu')]
        attached=[verb('Aukotubu','2MP','IMPV'),pronoun('w','2MP'),pronoun('hu','3MS')]
        self.assertEqual(person_candidates('اُكْتُبُواهُ',lexical_model=learn_qac_lexicon(corpus(original,attached))),[])

    def test_source_restrictions_survive_new_paradigm(self):
        for target,form,root,lemma,extra in (
                ('اُكْتُبُوا','yktb','ktb','kataba',''),
                ('اُكْتُبُوا','yakotubu','ktb','kataba','|PASS'),
                ('اُكْتُبُوا','yakotubu','ktm','kataba',''),
                ('اُمْدُدُوا','yamodudu','mdd','mad~a',''),
                ('اُدْعُوُوا','yadoEuwu','dEw','daEaA',''),
                ('اُأْكُلُوا','ya>okulu','Akl','>akala','')):
            self.assertEqual(self.read(target,form,root,lemma,extra),[])

    def test_source_identity_and_authority_remain_distinct(self):
        row=self.read('اُكْتُبُوا')[0]
        w=row['productive_derivation']
        self.assertEqual(w['law_id'],LAW_ID)
        self.assertEqual(w['source_form'],'يَكْتُبُ')
        self.assertEqual(w['singular_imperative'],'اُكْتُبْ')
        self.assertFalse(w['target_attested'])
        self.assertFalse(w['target_role_labels_used'])
        self.assertEqual(row['valency_witnesses'],[])
        self.assertEqual(''.join(p['surface'] for p in row['parts']),'اُكْتُبُوا')

    def test_policy_is_rechecked_with_warm_compiler(self):
        self.assertTrue(self.read('اُكْتُبُوا'))
        with patch('nabt.imperative_paradigm.POLICY_SHA256','0'*64):
            with self.assertRaises(NabtError): self.read('اُكْتُبُوا')

    def test_classical_passages_replay(self):
        self.assertEqual(len(replay_policy()['passages']),5)

    def test_independent_checker_rejects_mutated_receipts_and_profile(self):
        from tools.discourse_evaluation import SourceAudit
        from tools.imperative_paradigm_evaluation import SOURCE, POSITIVES, validate
        source_id='checker_mutation_test'
        model=learn_qac_lexicon(SOURCE,source_id=source_id)
        row=person_candidates('اُكْتُبُوا',lexical_model=model)[0]
        audit=SourceAudit(SOURCE,[],source_id)
        validate(row,audit,POSITIVES[2])
        for field,value in [('source_form','يَضْرِبُ'),('source_support_ids',[]),
                            ('target_profile','2FP'),('target_attested',True)]:
            altered=deepcopy(row)
            altered['productive_derivation'][field]=value
            with self.assertRaises(ValueError): validate(altered,audit,POSITIVES[2])
        altered=deepcopy(row)
        altered['supports'][0]['record_id']='0'*64
        with self.assertRaises(ValueError): validate(altered,audit,POSITIVES[2])

    def test_generic_independent_dispatcher_replays_original_source(self):
        from tools.discourse_evaluation import SourceAudit
        from tools.productive_form_validation import validate_imperative
        for code,form in [('3MS','yakotubu'),('2MS','takotubu'),('3FS','takotubu'),
                          ('1S','>akotubu'),('1P','nakotubu')]:
            raw=corpus([verb(form,code)])
            model=learn_qac_lexicon(raw,source_id='generic_checker')
            audit=SourceAudit(raw,[],'generic_checker')
            for text in ('اُكْتُبْ','اُكْتُبِي','اُكْتُبَا','اُكْتُبُوا','اُكْتُبْنَ'):
                rows=person_candidates(text,lexical_model=model)
                self.assertTrue(rows)
                for row in rows:
                    validate_imperative(row,audit)
                    forged=deepcopy(row)
                    forged['productive_derivation']['source_form']='يَضْرِبُ'
                    with self.assertRaises(ValueError): validate_imperative(forged,audit)
                    withdrawn=SourceAudit(raw,['1:1'],'generic_checker')
                    with self.assertRaises(ValueError): validate_imperative(row,withdrawn)

    def test_independent_checker_rejects_forged_nun_collision(self):
        from tools.discourse_evaluation import SourceAudit
        from tools.productive_form_validation import validate_imperative
        raw=corpus([verb('yasokunu',root='skn',lemma='sakana')])
        source_id='nun_collision_checker'
        model=learn_qac_lexicon(raw,source_id=source_id)
        audit=SourceAudit(raw,[],source_id)
        row=person_candidates('اُسْكُنُوا',lexical_model=model)[0]
        validate_imperative(row,audit)
        row['profile_id']='2FP'
        row['person_profile']={'person':2,'gender':1,'number':2}
        row['form']='اُسْكُنْنَ'
        row['productive_derivation'].update(target_profile='2FP',generated_form='اُسْكُنْنَ')
        with self.assertRaises(ValueError): validate_imperative(row,audit)

    def test_old_singular_law_is_unchanged(self):
        row=self.read('اُكْتُبْ')[0]
        self.assertEqual(row['productive_derivation']['law_id'],'nabt.productive-sound-imperative.v1')

if __name__=='__main__':
    unittest.main()
