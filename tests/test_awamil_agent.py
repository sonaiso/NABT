"""Boundary and independent authored scope tests for the awamil consumer."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog.awamil import AwamilIndex, answer
from tools.grammar_catalog.awamil_cli import check, analyze
from tools.grammar_catalog.awamil_relations import matrix, verify_matrix
from tools.lexical_training.awamil_agent import curriculum, dataset
from tools import mantuq_mafhum as mm

ROOT = Path(__file__).resolve().parents[1]


class AwamilCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = AwamilIndex()
        cls.catalog = cls.index.catalog()

    def test_two_hundreds_are_not_renumbered_into_one(self):
        cards = {c['id']: c for c in self.catalog['cards']}
        self.assertEqual(self.catalog['counts'], {'jurjani': 100, 'nabt': 100, 'relations': 12})
        self.assertEqual(cards['jurjani:001']['label'], 'الباء')
        self.assertEqual(cards['nabt:001']['label'], 'إنّ')
        self.assertEqual(self.catalog['partition'], {'samai': 91, 'qiyasi': 7, 'manawi': 2})
        self.assertFalse(any(r['equivalence_established'] for r in self.catalog['crosswalk']))

    def test_homographs_survive_display_limit_and_marks_survive_query(self):
        result = self.index.search('ما', 1, collection='jurjani')
        self.assertEqual(set(result['all_same_spelling_ids']), {'jurjani:024', 'jurjani:044'})
        self.assertEqual(len(result['candidates']), 1)
        for query in ('كَتَبَ', 'كُتِبَ', 'قمتُ', 'قمتَ', 'قمتِ'):
            result = self.index.search(query)
            self.assertEqual(result['query_occurrences'][0]['surface'], query)
            self.assertEqual(result['query_occurrences'][0]['utf8_span'], [0, len(query.encode())])

    def test_relation_sources_are_rehydrated_and_not_accepted_sentences(self):
        result = answer('الجملة الاسمية المبتدأ والخبر', collection='relations')
        self.assertEqual(result['retrieval']['candidates'][0]['id'], 'relation:nominal')
        self.assertTrue(result['retrieval']['candidates'][0]['record']['source_passages'])
        self.assertFalse(result['application_certified'])
        cards = self.index.catalog()
        cards['cards'][0]['authority'] = 'CERTIFIED'
        self.assertEqual(self.index.rehydrate('item', 'jurjani:001')['authority'], 'ENUMERATION_ONLY')

    def test_stale_index_and_coedited_manifest_cannot_pass(self):
        changed = deepcopy(self.catalog)
        changed['cards'][0]['label'] = 'forged'
        with patch('tools.grammar_catalog.awamil.build_awamil_catalog', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'STALE'):
                self.index.search('الباء')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'sources').mkdir()
            raw = (mm.INVENTORY.parent/'sources/awamil_inventory.tsv').read_bytes() + b'\n'
            (p/'sources/awamil_inventory.tsv').write_bytes(raw)
            obj = json.loads(mm.INVENTORY.read_text())
            from hashlib import sha256
            obj['inventory_sha256'] = sha256(raw).hexdigest()
            (p/'inventory.json').write_text(json.dumps(obj))
            with patch.object(mm, 'INVENTORY', p/'inventory.json'):
                with self.assertRaisesRegex(ValueError, 'INVENTORY_CHANGED'):
                    mm.load_awamil_inventory()

    def test_curriculum_covers_each_original_factor_once(self):
        c = curriculum(dev_results=[{'factor_id': 'jurjani:100', 'top1_correct': False}])
        self.assertEqual(len(c['units']), 100)
        self.assertEqual(c['units'][0]['unit_id'], 'jurjani:100')
        self.assertEqual({r['unit_id'] for r in c['units']}, {f'jurjani:{i:03d}' for i in range(1,101)})
        self.assertTrue(all(not r['application_mastered'] for r in c['units']))
        self.assertEqual(len(c['table_practice_ids']), 100)

    def test_every_identity_is_trained_without_input_ids_and_splits_do_not_overlap(self):
        rows = dataset(self.catalog)
        for split in ('train', 'dev', 'test'):
            selected = [r for r in rows if r['split'] == split]
            self.assertEqual(len({r['factor_id'] for r in selected}), 212)
            self.assertTrue(all(all(k not in r['query'] for k in r['gold']) for r in selected))
        sets = [{r['query'] for r in rows if r['split'] == split} for split in ('train','dev','test')]
        self.assertFalse(sets[0] & sets[1] or sets[1] & sets[2] or sets[0] & sets[2])

    def test_conditional_case_check_never_turns_into_source_recognition(self):
        valid = check({'factor_id': 'nabt:001', 'assignments': {'0': 0, '1': 1}})
        invalid = check({'factor_id': 'nabt:001', 'assignments': {'0': 1, '1': 0}})
        missing = check({'factor_id': 'nabt:001', 'assignments': {'0': 0}})
        self.assertTrue(valid['result']['complete'])
        self.assertFalse(invalid['result']['viable'])
        self.assertFalse(missing['result']['complete'])
        self.assertFalse(valid['application_certified'])
        for identity in ('jurjani:001', 'nabt:000', 'nabt:101'):
            with self.assertRaises(ValueError):
                check({'factor_id': identity, 'assignments': {}})
        with self.assertRaises(ValueError):
            check({'factor_id': 'nabt:001', 'assignments': {'0': True}})


class AwamilRelationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.options = {'lexical_text': (ROOT/'examples/construction_training.tsv').read_text(),
                       'context': json.loads((ROOT/'examples/construction_context.json').read_text())}

    def surfaces(self, text, predication):
        raw = text.encode()
        return [raw[predication[k]['start']:predication[k]['end']].decode()
                for k in ('musnad_ilayh','musnad','predication_head')]

    def first(self, text):
        report = matrix(text, **self.options)
        self.assertEqual(report['status'], 'LICENSED_DISCOURSE')
        return next(r for r in report['rows'] if not r['rejected_candidate'])

    def test_nominal_verbal_and_pp_heads_are_source_bound(self):
        for text, expected in [('زيدٌ حكيمٌ.', ['زيدٌ', 'حكيمٌ', 'حكيمٌ']),
                               ('كتب زيدٌ.', ['زيدٌ', 'كتب', 'كتب']),
                               ('زيدٌ فوقَ المكتبِ.', ['زيدٌ', 'فوقَ المكتبِ', 'فوقَ المكتبِ'])]:
            row = self.first(text)
            self.assertEqual(self.surfaces(text, row['predications'][0]), expected)

    def test_governor_is_not_silently_substituted_for_predication_head(self):
        text = 'كان زيدٌ حكيمًا.'
        row = self.first(text)
        self.assertEqual(self.surfaces(text, row['predications'][0]), ['زيدٌ', 'حكيمًا', 'حكيمًا'])
        self.assertTrue(any(r['owner_relation']['kind'] == 'operator' for r in row['relations']))

    def test_embedded_and_restrictive_predicates_do_not_escape_scope(self):
        row = self.first('ظن زيدٌ سالمًا حكيمًا.')
        self.assertEqual(row['predications'][0]['scope'], 'embedded')
        self.assertEqual(row['predications'][0]['binding']['claim_path'], ['restriction',0,'embedded',0])
        self.assertFalse(row['embedded_fact_projection_added'])
        text = 'زيدٌ الذي هو حكيمٌ كريمٌ.'
        row = self.first(text)
        self.assertEqual(self.surfaces(text,row['predications'][0]), ['زيدٌ','كريمٌ','كريمٌ'])
        self.assertTrue(any(r['family'] == 'embedding' for r in row['relations']))

    def test_withdrawal_replay_and_head_mutation_fail(self):
        text = 'زيدٌ حكيمٌ.'
        report = matrix(text, **self.options)
        self.assertTrue(verify_matrix(report, text=text, **self.options)['valid'])
        changed = deepcopy(report)
        changed['rows'][0]['predications'][0]['predication_head'] = changed['rows'][0]['predications'][0]['musnad_ilayh']
        self.assertFalse(verify_matrix(changed, text=text, **self.options)['valid'])
        self.assertFalse(verify_matrix(report, text='زيدٌ حكيمًا.', **self.options)['valid'])
        self.assertFalse(verify_matrix(report, text=text, context=self.options['context'])['valid'])
        self.assertNotEqual(matrix('في الدارِ.', **self.options)['status'], 'LICENSED_DISCOURSE')

    def test_retrieval_limits_do_not_prune_application_and_answer_uses_owner_spans(self):
        request = {'text': 'كان زيدٌ حكيمًا.', **self.options}
        narrow, broad = analyze(request, limit=1), analyze(request, limit=20)
        self.assertEqual(narrow['application'], broad['application'])
        self.assertIn('رأس الإسناد: حكيمًا', narrow['answer_ar'])
        self.assertFalse(narrow['retrieval_prunes_owner_candidates'])
        self.assertFalse(narrow['world_truth_established'])


if __name__ == '__main__':
    unittest.main()
