"""Independent sign contrasts and measurement-boundary regressions.

Reference self checks test the harness, not learning. Native inventory equality
is tested through the actual JSONL process when its existing target is built.
"""
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt.alphabet import parse_word
from nabt.codec import OccurrenceIdentity, decode_number, unpack_cells
from nabt.errors import NabtError
from nabt.machine import Machine, compose_effects
from nabt.phonological_modes import realize
from tools.arabic_training import sign_curriculum as s
from tools.entropy_framework.reuse_run import describe_entries, entry_command


class SignMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = s.matrix()

    def test_all_cells_preserved_with_three_distinct_populations(self):
        rows = self.matrix['cells']
        self.assertEqual([r['cell'] for r in rows], list(range(116)))
        self.assertEqual(Counter(r['classification'] for r in rows),
                         {'CV_CANDIDATE':84, 'SUKUN_CELL':29, 'MOVING_ALIF_REJECTED':3})
        self.assertEqual({r['carrier_name'] for r in rows if r['carrier'] == 'ء'}, {'همزة'})
        self.assertEqual({r['carrier_name'] for r in rows if r['carrier'] == 'ا'}, {'ألف'})

    def test_ba_kasra_name_and_existing_numeric_domains(self):
        row = self.matrix['cells'][6]
        self.assertEqual((row['a116_rendering'],row['cell_name'],row['content_number']),
                         ('بِ','باء / كسرة',7))
        self.assertEqual(unpack_cells(bytes.fromhex(row['framed_a116_hex'])), (6,))
        self.assertEqual(decode_number(7), (6,))
        self.assertNotEqual(row['utf8_hex'], row['framed_a116_hex'])
        self.assertEqual(OccurrenceIdentity('s','v1',2,8).local_number,240)
        self.assertNotEqual(OccurrenceIdentity('s','v1',2,8),OccurrenceIdentity('other','v1',2,8))

    def test_shape_gate_does_not_grant_independent_preposition(self):
        row = self.matrix['cells'][6]
        self.assertTrue(row['shape_from_zero']['waqf']['licensed'])
        self.assertEqual(row['role'], 'UNASSIGNED_WITHOUT_HOST')
        self.assertEqual(row['independent_word_license'],'NOT_ESTABLISHED')
        for n in (0,1,2,3,7):
            self.assertFalse(self.matrix['cells'][n]['shape_from_zero']['wasl']['licensed'])

    def test_cvv_is_84_long_templates_not_116_and_not_words(self):
        rows = self.matrix['cvv_templates']
        self.assertEqual(len(rows),84)
        self.assertEqual(len({tuple(r['cells']) for r in rows}),84)
        na = next(r for r in rows if r['a116_rendering'] == 'نَاْ')
        self.assertEqual(na['cells'],[96,3])
        self.assertEqual(na['content_number'],11256)
        self.assertEqual(na['lexical_role'],'UNASSIGNED_WITHOUT_HOST')
        self.assertIn('CVVC',self.matrix['syllable_targets'])

    def test_total_effect_and_source_lacuna_are_visible(self):
        self.assertTrue(all(len(r['entry_effect']['destinations']) == 97 for r in self.matrix['cells']))
        self.assertEqual({r['carrier'] for r in self.matrix['cells']
                          if r['articulation']['source_collation'] != 'ANCHORED'}, {'ل','ن'})
        self.assertTrue(all(r['articulation']['acoustic_validation'] is False for r in self.matrix['cells']))

    def test_join_uses_actual_entry_and_preserves_both_cells(self):
        machine = Machine('waqf')
        left = machine.effect(parse_word('كَتْتْ')); right = machine.effect(parse_word('كَ'))
        self.assertTrue(machine.analyse(left.cells).licensed)
        self.assertTrue(machine.analyse(right.cells).licensed)
        self.assertFalse(machine.analyse(left.cells + right.cells).licensed)
        joined = compose_effects(left,right)
        self.assertEqual(joined.cells,left.cells+right.cells)
        self.assertEqual(joined.destinations[0],96)

    def test_declared_roles_preserve_correlated_prerequisites(self):
        roles = self.matrix['declared_roles']
        self.assertEqual(len(roles['declarations']),34)
        self.assertFalse(roles['classifier'])
        row = next(r for r in roles['declarations'] if r['key'] == 'imperfect_prefix')
        self.assertEqual(row['examples'],['أ','ن','ي','ت'])
        self.assertIn('correlated_person_profile',row['requirements'])
        self.assertIn('independent_interpreted_source',row['requirements'])

    def test_ta_pause_does_not_erase_source_identity(self):
        feminine = realize('talha',end='waqf')
        spelled_t = realize('bint',end='waqf')
        self.assertEqual(feminine['alternatives'][0]['segments'][-1],'h')
        self.assertEqual(spelled_t['alternatives'][0]['segments'][-1],'t')
        self.assertEqual(spelled_t['written_form'],'بِنْتٌ')

    def test_boundaries_and_options_are_independent(self):
        result = realize('ism',start='wasl',end='waqf')
        self.assertEqual(result['alternatives'][0]['segments'],['s','m'])
        self.assertEqual(result['written_form'],'اِسْمٌ')
        result = realize('irmi',end='waqf',profile='sibawayhi_attested_options')
        self.assertEqual(len(result['alternatives']),2)

    def test_source_change_cannot_be_hidden_by_saved_matrix(self):
        with patch.dict(s.SOURCE_PINS, {'qatr':'0'*64}):
            with self.assertRaises(ValueError):
                s.matrix()

    def test_no_stage_unlock_or_training_from_matrix(self):
        for key in ('meaning_stage_unlocked','arabic_complete','model_training_performed'):
            self.assertIs(self.matrix[key],False)


class SignEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.identity,cls.inputs = s.suite()
        cls.real_suite = staticmethod(s.suite)

    def setUp(self):
        # The contract-parser tests share one freshly rebuilt reference suite.
        # The source-mutation test below deliberately restores real replay.
        replacement = patch.object(s, 'suite', return_value=(self.rows,self.identity,self.inputs))
        replacement.start()
        self.addCleanup(replacement.stop)

    def response(self):
        return {'schema':s.VERSION+'.predictions','suite_sha256':self.identity,
                'predictor':'test-reference', 'answers':[{'id':r['id'],'value':deepcopy(r['answer'])} for r in self.rows]}

    def test_exact_public_denominators_without_gold_in_questions(self):
        questions = s.questions()
        self.assertEqual(len(questions['tasks']),368)
        self.assertEqual(Counter(t['stage'] for t in questions['tasks']), {'D0':8,'D1':116,'D3':84,'D4':160})
        self.assertTrue(all('answer' not in t for t in questions['tasks']))
        self.assertEqual(questions['evaluation_kind'],'EXPOSED_SYMBOLIC_DEVELOPMENT')

    def test_perfect_reference_does_not_establish_learning(self):
        result = s.evaluate(self.response())
        self.assertEqual(result['correct'],368)
        self.assertTrue(result['symbolic_suite_pass'])
        self.assertFalse(result['learning_established'])
        self.assertFalse(result['meaning_stage_unlocked'])
        self.assertIn('unseen_role_acquisition',result['unmeasured'])

    def test_missing_answers_count_against_original_population(self):
        data = self.response(); data['answers'] = data['answers'][:1]
        result = s.evaluate(data)
        self.assertEqual(result['total'],368)
        self.assertEqual(result['correct'],1)
        self.assertEqual(sum(v['missing'] for v in result['by_stage'].values()),367)
        self.assertFalse(result['symbolic_suite_pass'])

    def test_empty_response_is_not_vacuous_success(self):
        data = self.response(); data['answers'] = []
        result = s.evaluate(data)
        self.assertEqual(result['correct'],0)
        self.assertFalse(result['symbolic_suite_pass'])

    def test_boolean_does_not_equal_cell_zero(self):
        data = self.response(); data['answers'][0]['value']['cell'] = False
        result = s.evaluate(data)
        self.assertEqual(result['correct'],367)

    def test_float_is_not_an_integer_code(self):
        data = self.response(); data['answers'][0]['value']['cell'] = 0.0
        self.assertEqual(s.evaluate(data)['correct'],367)

    def test_dropping_one_valid_pause_alternative_is_wrong(self):
        data = self.response()
        row = next(r for r in data['answers'] if len(r['value'].get('segments_alternatives',[])) == 2)
        row['value']['segments_alternatives'].pop()
        self.assertEqual(s.evaluate(data)['correct'],367)

    def test_duplicate_and_unknown_task_ids_rejected(self):
        data = self.response(); data['answers'][1]['id'] = data['answers'][0]['id']
        with self.assertRaises(ValueError): s.evaluate(data)
        data = self.response(); data['answers'][0]['id'] = 'not-a-task'
        with self.assertRaises(ValueError): s.evaluate(data)

    def test_wrong_snapshot_and_extra_authority_fields_rejected(self):
        data = self.response(); data['suite_sha256'] = '0'*64
        with self.assertRaises(ValueError): s.evaluate(data)
        data = self.response(); data['meaning_stage_unlocked'] = True
        with self.assertRaises(ValueError): s.evaluate(data)

    def test_caller_cannot_supply_smaller_gold_population(self):
        data = self.response(); data['total'] = 1
        with self.assertRaises(ValueError): s.evaluate(data)

    def test_changed_source_stops_evaluation_before_score(self):
        with patch.object(s, 'suite', self.real_suite), patch.dict(s.SOURCE_PINS, {'sibawayhi':'0'*64}):
            with self.assertRaises(ValueError): s.evaluate(self.response())

    def test_input_bound_and_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'answers.json'
            for value in ('{"a":0,"a":1}', '{"a":NaN}'):
                path.write_text(value)
                with self.assertRaises(ValueError): s._read_predictions(path)
            path.write_bytes(b' '*(s.MAX_INPUT_BYTES+1))
            with self.assertRaises(NabtError): s._read_predictions(path)

    def test_output_is_exclusive_and_cli_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            path=Path(tmp)/'saved.json'; path.write_text('keep')
            self.assertEqual(s.main(['questions','--output',str(path)]),2)
            self.assertEqual(path.read_text(),'keep')
            response=Path(tmp)/'response.json'
            data=self.response(); data['answers']=[]; response.write_text(json.dumps(data))
            self.assertEqual(s.main(['evaluate','--predictions',str(response)]),1)


class SignIntegrationTests(unittest.TestCase):
    def test_native_quota_cannot_claim_exhaustion_with_duplicates_or_omissions(self):
        request={'op':'quota','consonants':1,'vowels':1,'max_atoms':10}
        response={'status':'OK','op':'quota','law_id':'nabt.licensed-derivation.v1',
                  'scope':'conditional_on_supplied_interpretations','conditional':True,
                  'acquisition_measured':False,
                  'enumeration':'COMPLETE','search_complete':True,
                  'consonants':1,'vowels':1,'count':2,'shapes':['CV','VC'],
                  'shape_numbers':[4,5],'linguistic_license_inferred':False}
        s._check_quota(request,response)
        for shapes,numbers in ((['CV','CV'],[4,4]), (['CV'],[4]), (['CC','VC'],[3,5])):
            wrong={**response,'count':len(shapes),'shapes':shapes,'shape_numbers':numbers}
            with self.assertRaises(ValueError): s._check_quota(request,wrong)
        wrong={**response,'enumeration':'EXHAUSTED','search_complete':False,
               'required_atoms':2,'linguistic_rejection':False}
        with self.assertRaises(ValueError): s._check_quota(request,wrong)

    def test_existing_dispatcher_owns_the_entry(self):
        entry=describe_entries()['sign-curriculum']
        self.assertEqual(entry['module'],'tools.arabic_training.sign_curriculum')
        self.assertEqual(entry_command('sign-curriculum',['questions'])[-2:],
                         ['tools.arabic_training.sign_curriculum','questions'])

    @unittest.skipUnless((s.ROOT/'formal/.lake/build/bin/unitDiscoveryProbe').is_file(), 'native unit inventory not built')
    def test_real_native_role_inventory_boundary(self):
        result=s.native_check()
        self.assertTrue(result['matched'])
        self.assertEqual(result['declarations'],34)

    @unittest.skipUnless((s.ROOT/'formal/.lake/build/bin/progressiveUnitProbe').is_file(), 'native progressive probe not built')
    def test_real_native_quota_and_syllable_addresses(self):
        result=s.native_shapes()
        self.assertEqual(len(result['cases']),30)
        targets=[r['native_response'] for r in result['cases'][24:]]
        self.assertEqual([r['shape_n'] for r in targets],[4,10,9,21,19,43])
        self.assertTrue(all(r['linguistic_license_inferred'] is False for r in targets))


if __name__ == '__main__':
    unittest.main()
