"""Counterexamples from Qatr's text, source identity and native ambiguity checks."""
import json
import os
from pathlib import Path
import unittest

from tools.arabic_training.data import ROOT, sha
from tools.qatr_training.data import QATR_SHA256, premises, native_checks, export_teacher


class QatrPremiseTests(unittest.TestCase):
    def row(self,**changes):
        row=dict(Invariable_Declinable='معرب',Morph_tag='NOUN_CONCRETE',
                 Case_Mood_Marker='الكسرة',Case_Mood='مجرور',Syntactic_Role='مضاف إليه')
        row.update(changes);return row

    def test_gold_case_and_role_never_select_reading_set(self):
        a=premises(self.row())[0]
        b=premises(self.row(Case_Mood='منصوب',Syntactic_Role='مفعول به'))[0]
        self.assertEqual(a,b);self.assertIsNone(a['classes'])

    def test_estimated_case_labels_are_erased(self):
        values=[premises(self.row(Case_Mood_Marker=x))[0] for x in ['ضمة مقدرة','فتحة مقدرة','الكسرة المقدرة']]
        self.assertEqual(values[0],values[1]);self.assertEqual(values[1],values[2])
        self.assertEqual(values[0]['mark'],'hidden')

    def test_diptote_annotation_does_not_invent_class_premise(self):
        a=premises(self.row(Case_Mood_Marker='الفتحة (ممنوع من الصرف)'))[0]
        self.assertEqual(a,premises(self.row(Case_Mood_Marker='الفتحة'))[0])

    def test_built_case_position_is_outside_inflection_teacher(self):
        self.assertEqual(premises(self.row(Invariable_Declinable='مبني')),
                         (None,'DECLINABILITY_NOT_ESTABLISHED'))

    def test_unresolved_sign_and_kind_are_obligations(self):
        self.assertEqual(premises(self.row(Case_Mood_Marker=''))[1],'SIGN_UNRESOLVED')
        self.assertEqual(premises(self.row(Morph_tag='UNINFLECTED_VERB'))[1],'KIND_OUTSIDE_SCOPED_MAPPING')

    def test_qatr_source_and_passages_are_exact(self):
        raw=(ROOT/'src/nabt/data/source_evidence/qatr.txt').read_bytes()
        self.assertEqual(sha(raw),QATR_SHA256)
        registry=json.loads((ROOT/'evidence/qatr_lean_training/source_coverage.json').read_text())
        lines=raw.splitlines(keepends=True)
        for row in registry['sections']:
            quote=b''.join(lines[row['first_line']-1:row['last_line']])
            self.assertEqual(sha(quote),row['span_sha256'])
            self.assertEqual(raw[row['start_byte']:row['end_byte']],quote)


@unittest.skipUnless(os.environ.get('NABT_QATR_READING'),'native Lean qatrReading required')
class QatrNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe=Path(os.environ['NABT_QATR_READING'])

    def query(self,kind,mark,classes=None,proposed=None):
        return native_checks(self.exe,[dict(kind=kind,mark=mark,classes=classes,proposed=proposed)])[0]

    def test_source_examples_keep_multiple_cases(self):
        # Qatr L82–90: dual/masculine-plural ya, feminine-plural kasra, five-verb deletion.
        for kind,mark,classes,want in [
            ('noun','ya',['iMuthanna'],['nasb','jarr']),
            ('noun','ya',['iJamM'],['nasb','jarr']),
            ('noun','kasra',['iJamF'],['nasb','jarr']),
            ('verb','nun_deleted',None,['nasb','jazm']),
            ('noun','hidden',['iMaqsur'],['nasb','raf','jarr']),
            ('verb','weak_deleted',None,['jazm'])]:
            self.assertEqual(self.query(kind,mark,classes)['cases'],want)

    def test_no_weak_deletion_from_remaining_vowel(self):
        self.assertEqual(self.query('verb','damma')['cases'],['raf'])
        self.assertEqual(self.query('verb','weak_deleted')['cases'],['jazm'])

    def test_drop_alternative_and_add_foreign_row_rejected(self):
        result=self.query('verb','nun_deleted')
        ids=[r['id'] for r in result['rows']]
        self.assertTrue(self.query('verb','nun_deleted',proposed=ids)['complete_proposal'])
        for i in range(len(ids)):
            self.assertFalse(self.query('verb','nun_deleted',proposed=ids[:i]+ids[i+1:])['complete_proposal'])
        noun=self.query('noun','damma')['rows'][0]['id']
        self.assertFalse(self.query('verb','nun_deleted',proposed=ids+[noun])['complete_proposal'])

    def test_unknown_is_not_closed_empty_or_particle(self):
        self.assertGreater(len(self.query('noun','hidden')['rows']),0)
        self.assertEqual(self.query('noun','hidden',[])['rows'],[])
        self.assertEqual(self.query('particle','hidden')['rows'],[])

    def test_each_legal_row_survives_its_observation(self):
        table=export_teacher(self.exe)
        self.assertEqual(len({r['id'] for r in table['rows']}),45)
        for row in table['rows']:
            result=self.query(row['kind'],row['mark'],[row['class']])
            self.assertIn(row,result['rows'])

    def test_boolean_identity_unknown_fields_and_limits_rejected(self):
        self.assertEqual(self.query('verb','nun_deleted',proposed=[True])['status'],'INVALID_INPUT')
        self.assertEqual(self.query('verb','nun_deleted',proposed=[999])['status'],'INVALID_INPUT')
        self.assertEqual(self.query('verb','nun_deleted',classes=['iSahih']*16)['status'],'RESOURCE_LIMIT')
        response=native_checks(self.exe,[dict(kind='verb',mark='damma',classes=None,proposed=None,world_truth=True)])[0]
        self.assertEqual(response['status'],'INVALID_INPUT')

    def test_stream_recovers_after_invalid_request(self):
        responses=native_checks(self.exe,[{},dict(kind='noun',mark='kasra',classes=['iJamF'],proposed=None)])
        self.assertEqual(responses[0]['status'],'INVALID_INPUT')
        self.assertEqual(responses[1]['cases'],['nasb','jarr'])
