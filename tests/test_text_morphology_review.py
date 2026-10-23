"""Independent pre-open cases plus explicitly post-open adversarial review.

The case material and expected linguistic boundaries predate review of the new
reader. The attacks below inspect public behavior after that freeze; they are
not presented as another held-out corpus or a second Arabic implementation.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

from nabt.errors import NabtError
from nabt.text_morphology import (decode_text_morphology, read_text_morphology,
    text_morphology_number, verify_text_morphology)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('nabt_text_morphology_independent_evaluator',
                                            ROOT / 'tools/text_morphology_evaluation.py')
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def lexical_source(*extra, lexeme='سُنَبِلٌ', rid='r1'):
    return (f'قراءة «{rid}» للفظ «{lexeme}»:\n'
            'يدل على معنى مستقل غير مقترن بزمن\n'
            'يسلم من شبه الحرف\n'
            'لا يمنع تصوره الشركة\n' + '\n'.join(extra))


class TextMorphologyIndependentReviewTests(unittest.TestCase):
    def test_frozen_independent_cases(self):
        for case in EVALUATOR.load_material()['cases']:
            with self.subTest(case=case['id']):
                result = EVALUATOR.run_case(case)
                self.assertTrue(result['passed'], result)

    def test_blanket_deferral_fails_positive_measurement(self):
        case = next(c for c in EVALUATOR.load_material()['cases'] if c['id'] == 'tm06')
        report = read_text_morphology(**case['input'])
        changed = deepcopy(report)
        changed['occurrences'][0]['axes']['kind']['status'] = 'DEFER'
        result = EVALUATOR.property_check(case['expected'][0], changed)
        self.assertFalse(result['passed'])

    def test_independent_span_checker_rejects_shift_even_when_surface_looks_same(self):
        inputs = {'text': 'رَجُلٌ  رَجُلٌ', 'source_id': 'input', 'scope': 'review'}
        report = read_text_morphology(**inputs)
        self.assertTrue(EVALUATOR.independent_structure_checks(report, inputs))
        changed = deepcopy(report)
        changed['occurrences'][0]['span'] = deepcopy(changed['occurrences'][1]['span'])
        with self.assertRaises(ValueError):
            EVALUATOR.independent_structure_checks(changed, inputs)
        self.assertFalse(verify_text_morphology(changed)['valid'])

    def test_independent_checker_rejects_unlicensed_government(self):
        inputs = {'text': 'لَمْ يَسْتَنْبِتْ', 'source_id': 'input', 'scope': 'review'}
        report = read_text_morphology(**inputs)
        changed = deepcopy(report)
        changed['attachments'][0]['actual_case'] = 'jazm'
        with self.assertRaises(ValueError):
            EVALUATOR.independent_structure_checks(changed, inputs)
        self.assertFalse(verify_text_morphology(changed)['valid'])

    def test_source_and_scope_are_required_bindings(self):
        report = read_text_morphology('رَجُلٌ', source_id='input', scope='alpha')
        self.assertTrue(verify_text_morphology(report, text='رَجُلٌ', source_id='input', scope='alpha')['valid'])
        for kwargs in ({'text': 'رَجُلٍ'}, {'scope': 'beta'}, {'source_id': 'other'}):
            with self.subTest(expected=kwargs):
                self.assertFalse(verify_text_morphology(report, **kwargs)['valid'])

    def test_explicit_lexical_source_removal_is_not_self_replay(self):
        source = lexical_source('يدل على ذات باعتبار صفة')
        report = read_text_morphology('سُنَبِلٌ', lexical_text=source)
        self.assertTrue(verify_text_morphology(report)['valid'])
        self.assertTrue(verify_text_morphology(report, lexical_text=source)['valid'])
        self.assertFalse(verify_text_morphology(report, lexical_text=None)['valid'])
        removed = read_text_morphology('سُنَبِلٌ', lexical_text=None)
        o = removed['occurrences'][0]
        self.assertEqual(o['axes']['kind']['status'], 'LICENSED')
        self.assertEqual(o['axes']['kind']['candidates'], ['noun'])
        self.assertNotEqual(o['axes']['nominal_semantics']['status'], 'LICENSED')
        self.assertIsNone(o['readings'][0]['lexical_link'])

    def test_lexical_witness_revision_changes_only_supported_semantic_answer(self):
        old_source = lexical_source('يدل على ذات باعتبار صفة')
        new_source = lexical_source('يدل على ذات دون اعتبار صفة')
        old = read_text_morphology('سُنَبِلٌ', lexical_text=old_source)
        new = read_text_morphology('سُنَبِلٌ', lexical_text=new_source)
        self.assertEqual(old['occurrences'][0]['occurrence_id'], new['occurrences'][0]['occurrence_id'])
        self.assertNotEqual(old['occurrences'][0]['readings'][0]['reading_id'],
                            new['occurrences'][0]['readings'][0]['reading_id'])
        self.assertEqual(old['occurrences'][0]['axes']['nominal_semantics']['candidates'], ['mushtaq'])
        self.assertEqual(new['occurrences'][0]['axes']['nominal_semantics']['candidates'], ['jins_jamid'])
        self.assertEqual(old['occurrences'][0]['axes']['kind']['candidates'], ['noun'])
        self.assertEqual(new['occurrences'][0]['axes']['kind']['candidates'], ['noun'])
        self.assertFalse(verify_text_morphology(old, lexical_text=new_source)['valid'])

    def test_lexical_description_conflict_cannot_be_hidden_by_axis_status(self):
        source = lexical_source('يدل على ذات باعتبار صفة', 'يدل على ذات دون اعتبار صفة')
        report = read_text_morphology('سُنَبِلٌ', lexical_text=source)
        self.assertNotEqual(report['occurrences'][0]['axes']['nominal_semantics']['status'], 'LICENSED')
        self.assertTrue(any(b['code'] == 'LEXICAL_SOURCE_CONFLICT'
            for r in report['occurrences'][0]['readings'] for b in r['blockers']))
        changed = deepcopy(report)
        changed['occurrences'][0]['axes']['nominal_semantics'] = {
            'status':'LICENSED','candidates':['mushtaq'],'support_ids':[],'missing':[]}
        self.assertFalse(verify_text_morphology(changed)['valid'])

    def test_two_senses_do_not_share_a_single_reading_identity(self):
        source = lexical_source('يدل على ذات باعتبار صفة', rid='r1') + '\n' + \
                 lexical_source('يدل على ذات دون اعتبار صفة', rid='r2')
        report = read_text_morphology('سُنَبِلٌ', lexical_text=source)
        readings = report['occurrences'][0]['readings']
        self.assertEqual(len(readings), 2)
        self.assertEqual(len({r['reading_id'] for r in readings}), 2)
        changed = deepcopy(report)
        changed['occurrences'][0]['readings'][0]['receipts'][0]['identity']['reading_id'] = readings[1]['reading_id']
        self.assertFalse(verify_text_morphology(changed)['valid'])

    def test_lexical_link_requires_exact_surface_not_bare_letter_equality(self):
        source = lexical_source('يدل على ذات باعتبار صفة')
        for different in ('سُنَبِلٍ', 'سنبل'):
            with self.subTest(surface=different):
                report = read_text_morphology(different, lexical_text=source)
                self.assertIsNone(report['occurrences'][0]['readings'][0]['lexical_link'])
                self.assertNotEqual(report['occurrences'][0]['axes']['nominal_semantics']['status'], 'LICENSED')

    def test_unknown_or_unparseable_lexical_qualification_blocks_approval(self):
        source = lexical_source('يدل على ذات باعتبار صفة', 'هذا الحكم مقيد بشرط مجهول')
        report = read_text_morphology('سُنَبِلٌ', lexical_text=source)
        self.assertNotEqual(report['occurrences'][0]['axes']['nominal_semantics']['status'], 'LICENSED')
        self.assertTrue(any(b['code'] == 'UNPARSED_LEXICAL_SOURCE'
            for r in report['occurrences'][0]['readings'] for b in r['blockers']))

    def test_a_governor_does_not_turn_an_into_a_simple_noun(self):
        report = read_text_morphology('مِنْ أَنْ')
        target = report['occurrences'][1]
        self.assertNotEqual(target['axes']['kind']['candidates'], ['noun'])
        self.assertIsNone(target['actual_role'])
        self.assertIsNone(target['actual_case'])
        for edge in report['attachments']:
            self.assertFalse(edge['kind_constraint_activated'])
            self.assertFalse(edge['independent_kind_compatible'])

    def test_replayed_number_cannot_authorize_a_forged_kind(self):
        report = read_text_morphology('رَجُلٌ')
        number = text_morphology_number(report)
        self.assertEqual(decode_text_morphology(number), report)
        changed = deepcopy(report)
        changed['occurrences'][0]['axes']['kind']['candidates'] = ['verb']
        forged = int.from_bytes(b'\x01' + EVALUATOR.wire(changed), 'big')
        with self.assertRaises(NabtError):
            decode_text_morphology(forged)
        for invalid in (True, False, -1, 0):
            with self.subTest(number=invalid), self.assertRaises(NabtError):
                decode_text_morphology(invalid)

    def test_report_tampering_is_rejected_without_trusting_hashes_or_flags(self):
        report = read_text_morphology('رَجُلٌ')
        mutations = [
            lambda r: r.update(source_sha256='0'*64),
            lambda r: r.update(facts=[{'claimed':'world fact'}]),
            lambda r: r['occurrences'][0].update(actual_case='raf'),
            lambda r: r['occurrences'][0]['readings'][0]['receipts'][0].update(activated=False),
            lambda r: r['occurrences'][0]['readings'][0]['receipts'][0]['supports'][0]['span'].update(start=0),
            lambda r: r['occurrences'][0]['readings'][0]['receipts'][0].update(rule_id='caller_asserted_rule'),
            lambda r: r['occurrences'][0]['readings'][0]['axes']['construction'].update(status='LICENSED',candidates=['inflected']),
        ]
        for index, mutate in enumerate(mutations):
            changed = deepcopy(report)
            mutate(changed)
            with self.subTest(mutation=index):
                self.assertFalse(verify_text_morphology(changed)['valid'])

    def test_malformed_tanwin_is_rejected_not_converted_to_unknown(self):
        for text in ('رَجُلٌٌ', 'رَجُلٌَ', 'رٌجُل'):
            with self.subTest(text=text), self.assertRaises(NabtError) as raised:
                read_text_morphology(text)
            self.assertEqual(raised.exception.status, 'REJECT')
            self.assertIn(raised.exception.code, {'CONFLICTING_MARKS','NONTERMINAL_OR_MULTIPLE_TANWIN'})

    def test_incompatible_alif_tanwin_cannot_issue_a_noun_receipt(self):
        for text in ('اٌ', 'رَجُلاٌ', 'اٍ', 'رَجُلاٍ'):
            with self.subTest(text=text):
                try:
                    report = read_text_morphology(text)
                except NabtError as error:
                    self.assertIn(error.status, {'REJECT', 'DEFER'})
                    self.assertNotIn(error.code, {'RESOURCE_LIMIT', 'INSTALLED_CONTRACT_FAILED'})
                else:
                    for occurrence in report['occurrences']:
                        self.assertNotEqual(occurrence['axes']['kind']['status'], 'LICENSED')
                        self.assertFalse(any(receipt['activated']
                            for reading in occurrence['readings'] for receipt in reading['receipts']))

    def test_unsupported_script_preserves_a_named_gap_without_particle_default(self):
        report = read_text_morphology('unseen')
        self.assertNotEqual(report['status'], 'READ')
        self.assertFalse(report['facts'])
        target = report['occurrences'][0]
        self.assertNotEqual(target['axes']['kind']['status'], 'LICENSED')
        self.assertTrue(any(b['status'] == 'DEFER' for b in target['blockers']))

    def test_closed_marker_and_content_word_are_different_evidence_origins(self):
        report = read_text_morphology('لَمْ سُنَبِلٌ')
        marker, noun = report['occurrences']
        marker_receipts = marker['readings'][0]['receipts']
        noun_receipts = noun['readings'][0]['receipts']
        self.assertEqual(marker['axes']['kind']['candidates'], ['particle'])
        self.assertEqual(noun['axes']['kind']['candidates'], ['noun'])
        self.assertEqual(marker_receipts[0]['supports'][0]['basis'], 'EXACT_SOURCE_QUALIFIED_FUNCTION_MARKER')
        self.assertEqual(noun_receipts[0]['supports'][0]['type'], 'terminal_tanwin')
        self.assertEqual(report['recognition_basis']['content_word_answer_entries_used'], 0)


if __name__ == '__main__':
    unittest.main()
