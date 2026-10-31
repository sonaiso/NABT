"""Independent answer-attachment checks for the existing nominal evidence path.

Expected categories below are authored oracles. Mutations recompute public
identities so that hashes alone cannot make altered explanations admissible.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse
from tools.question_answer_validation import CLAIM_FIELDS, validate_interpretations, wire


ROOT = Path(__file__).resolve().parents[1]
TRAINING = b"""LOCATION\tFORM\tTAG\tFEATURES
(1:1:1:1)\tzayodN\tPN\tSTEM|POS:PN|LEM:zayod|ROOT:zyd|MS
(1:2:1:1)\tzayodK\tPN\tSTEM|POS:PN|LEM:zayod|ROOT:zyd|MS
(1:3:1:1)\trajulN\tN\tSTEM|POS:N|LEM:rajul|ROOT:rjl|MS
(1:4:1:1)\trajulK\tN\tSTEM|POS:N|LEM:rajul|ROOT:rjl|MS
(1:5:1:1)\tkaAtibN\tN\tSTEM|POS:N|LEM:kaAtib|ROOT:ktb|MS|ACT|PCPL
(1:6:1:1)\tkaAtibK\tN\tSTEM|POS:N|LEM:kaAtib|ROOT:ktb|MS|ACT|PCPL
"""
CONTEXT = {'entities': [{'id': 'zayd', 'name': 'زيد', 'gender': 'masculine',
                         'number': 'singular', 'kind': 'person'}]}
LEXICAL = '''قراءة «writer» للفظ «كَاتِبٌ»:
يدل على معنى مستقل غير مقترن بزمن
لا يمنع تصوره الشركة
يدل على ذات باعتبار صفة
قراءة «person» للفظ «رَجُلٌ»:
يدل على معنى مستقل غير مقترن بزمن
لا يمنع تصوره الشركة
يدل على ذات دون اعتبار صفة
'''


def claim_view(claim):
    return {field: deepcopy(claim[field]) for field in CLAIM_FIELDS}


def replace_explanation_identity(answer, row):
    """Rehash tampered public content and all its repeated proof references."""
    old = row['interpretation_id']
    new = sha256(wire({k: v for k, v in row.items() if k != 'interpretation_id'})).hexdigest()
    row['interpretation_id'] = new

    def visit(value):
        if type(value) is dict:
            if 'predicate_interpretation_ids' in value:
                value['predicate_interpretation_ids'] = [new if item == old else item
                                                        for item in value['predicate_interpretation_ids']]
            for item in value.values():
                visit(item)
        elif type(value) is list:
            for item in value:
                visit(item)
    visit(answer)
    answer['predicate_interpretations'].sort(key=lambda item: item['interpretation_id'])
    answer['answer_id'] = sha256(wire({k: v for k, v in answer.items() if k != 'answer_id'})).hexdigest()


class NominalInterpretationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING, source_id='authored_nominal_oracle')
        cls.options = {'lexical_model': cls.model, 'context': CONTEXT, 'lexical_text': LEXICAL}
        cls.writer = cls.fixture('زَيْدٌ كَاتِبٌ.', 'هل زَيْدٌ كَاتِبٌ؟')

    @classmethod
    def fixture(cls, text, question, **options):
        kwargs = {**cls.options, **options}
        return (ask_discourse(text, question, **kwargs), read_discourse(text, **kwargs),
                read_discourse(question, source_id='question', **kwargs), kwargs['context'])

    def validate(self, fixture):
        answer, document, inquiry, context = fixture
        validate_interpretations(answer, document, inquiry, {'context': context}, claim_view=claim_view)

    def test_source_categories_and_derivation_are_separate_checked_axes(self):
        for word, category, tags in (('رَجُلٌ', 'jins_jamid', []), ('كَاتِبٌ', 'mushtaq', ['ACT', 'PCPL'])):
            with self.subTest(word=word):
                fixture = self.fixture(f'زَيْدٌ {word}.', f'هل زَيْدٌ {word}؟')
                self.validate(fixture)
                self.assertEqual(fixture[0]['status'], 'SUPPORTED')
                for row in fixture[0]['predicate_interpretations']:
                    self.assertEqual(row['derivation']['features'], tags)
                    denotation = row['nominal_denotation']
                    self.assertFalse(denotation['sense_equivalence_established'])
                    self.assertEqual([r['nominal_semantics']['candidates'] for r in denotation['alternatives']],
                                     [[category]])

    def test_missing_descriptions_remain_explicit_without_an_invented_class(self):
        fixture = self.fixture('زَيْدٌ كَاتِبٌ.', 'هل زَيْدٌ كَاتِبٌ؟', lexical_text=None)
        self.validate(fixture)
        for row in fixture[0]['predicate_interpretations']:
            self.assertEqual(row['nominal_denotation']['status'], 'DEFER')
            self.assertEqual(row['nominal_denotation']['alternatives'], [])
            self.assertEqual(row['derivation']['features'], ['ACT', 'PCPL'])

    def test_rehashed_explanation_cannot_change_source_or_meaning(self):
        for mutation in ('features', 'category', 'source', 'reading', 'owner', 'owner_type', 'scope', 'world', 'sense'):
            fixture = deepcopy(self.writer)
            answer = fixture[0]
            row = answer['predicate_interpretations'][0]
            if mutation == 'features':
                row['derivation']['features'] = ['VN']
            elif mutation == 'category':
                row['nominal_denotation']['alternatives'][0]['nominal_semantics']['candidates'] = ['jins_jamid']
            elif mutation == 'source':
                row['nominal_denotation']['alternatives'][0]['lexical_link']['source_id'] = 'foreign'
            elif mutation == 'reading':
                row['predicate_reading_id'] = 'foreign'
            elif mutation == 'owner':
                row['owner_claim_id'] = 'foreign'
            elif mutation == 'owner_type':
                row['owner_claim_id'] = []
            elif mutation == 'scope':
                row['predicate_claim']['tense'] = 'past'
            elif mutation == 'world':
                row['world_truth'] = 'ESTABLISHED'
            else:
                row['nominal_denotation']['sense_equivalence_established'] = True
            replace_explanation_identity(answer, row)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.validate(fixture)

    def test_complete_explanation_inventory_and_proof_references_are_required(self):
        for mutation in ('missing_row', 'duplicate_row', 'missing_reference', 'foreign_reference', 'source_omitted'):
            fixture = deepcopy(self.writer)
            answer = fixture[0]
            if mutation == 'missing_row':
                answer['predicate_interpretations'].pop()
            elif mutation == 'duplicate_row':
                answer['predicate_interpretations'].append(deepcopy(answer['predicate_interpretations'][0]))
            elif mutation == 'source_omitted':
                del answer['nominal_description_source']
            else:
                proof = answer['question_interpretations'][0]['proofs'][0]
                if mutation == 'missing_reference':
                    del proof['predicate_interpretation_ids']
                else:
                    proof['predicate_interpretation_ids'] = ['foreign']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.validate(fixture)

    def test_rival_descriptions_remain_whole_correlated_readings(self):
        rival = LEXICAL + '''قراءة «writer_as_genus» للفظ «كَاتِبٌ»:
يدل على معنى مستقل غير مقترن بزمن
لا يمنع تصوره الشركة
يدل على ذات دون اعتبار صفة
'''
        fixture = self.fixture('زَيْدٌ كَاتِبٌ.', 'هل زَيْدٌ كَاتِبٌ؟', lexical_text=rival)
        self.validate(fixture)
        row = fixture[0]['predicate_interpretations'][0]
        self.assertEqual({tuple(r['nominal_semantics']['candidates'])
                          for r in row['nominal_denotation']['alternatives']}, {('mushtaq',), ('jins_jamid',)})
        row['nominal_denotation']['alternatives'].pop()
        replace_explanation_identity(fixture[0], row)
        with self.assertRaises(ValueError):
            self.validate(fixture)

    def test_embedded_nominal_explanation_preserves_its_operator_scope(self):
        model = learn_qac_lexicon((ROOT / 'examples/construction_training.tsv').read_bytes())
        context = json.loads((ROOT / 'examples/construction_context.json').read_text())
        fixture = self.fixture('ظن زيدٌ سالمًا حكيمًا.', 'هل ظن زيدٌ سالمًا حكيمًا؟',
                               lexical_model=model, context=context, lexical_text=None)
        self.validate(fixture)
        self.assertEqual(fixture[0]['status'], 'SUPPORTED')
        for row in fixture[0]['predicate_interpretations']:
            self.assertEqual(row['claim_path'], ['restriction', 0, 'embedded', 0])
            self.assertEqual(row['assertion_scope'], 'EMBEDDED_IN_OWNER_CLAIM_NOT_ASSERTED_SEPARATELY')
        changed = deepcopy(fixture)
        row = changed[0]['predicate_interpretations'][0]
        row['assertion_scope'] = 'ASSERTED_SOURCE_CLAIM'
        replace_explanation_identity(changed[0], row)
        with self.assertRaises(ValueError):
            self.validate(changed)


if __name__ == '__main__':
    unittest.main()
