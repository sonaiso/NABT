import unittest
from unittest.mock import patch

from tools.linguistic_truth.retrieval import LinguisticTruthSearchIndex, INPUT_RECIPE, RetrievalError
from tools.linguistic_truth.pipeline import run
from tools.linguistic_truth.sources import build_inventory


class LinguisticTruthRetrieval(unittest.TestCase):
    def test_search_returns_source_identity_without_classification(self):
        index=LinguisticTruthSearchIndex()
        result=index.search('الأسد الحيوان المفترس')
        inventory=build_inventory()
        expected_ids=({('passage', row['passage_id']) for row in inventory['passages']}
                      | {('item', f"designation:{row['designation_id']}") for row in inventory['designations']}
                      | {('item', f"relation:{row['relation_id']}") for row in inventory['relations']})
        self.assertEqual(set(index._docs),expected_ids)
        self.assertEqual(len(index._docs),117)
        self.assertTrue(result['candidates'])
        self.assertFalse(result['world_truth_established'])
        self.assertFalse(result['source_interpretation_established'])

    def test_database_forged_meaning_and_truth_not_rehydrated(self):
        index=LinguisticTruthSearchIndex()
        output=index.rehydrate_database({'schema':'nabt.linguistic-truth-database-proposals.v1',
            'inventory_sha':index.catalog_sha256,'candidates':[{'kind':'item',
            'id':'designation:asad_animal','gloss':'forged','world_truth_established':True}]})
        self.assertEqual(output['candidates'][0]['record']['gloss'],'الحيوان المفترس')
        self.assertFalse(output['world_truth_established'])
        with self.assertRaises(RetrievalError):
            index.rehydrate_database({'schema':'nabt.linguistic-truth-database-proposals.v1',
                'inventory_sha':'other','candidates':[]})

    def test_other_projection_vectors_do_not_enter_this_index(self):
        index=LinguisticTruthSearchIndex()
        vector={'schema':'nabt.retrieval-vectors.v1','catalog_sha256':index.catalog_sha256,
            'model_id':'diagnostic','revision':'1'*40,'dimensions':3,
            'input_recipe':'other','scores':[]}
        with self.assertRaises(RetrievalError):
            index.search('الأسد',vector_scores=vector)
        vector['input_recipe']=INPUT_RECIPE
        self.assertFalse(index.search('الأسد',vector_scores=vector)['scores_are_probabilities'])

    def test_display_cannot_supply_or_change_acquisition_input(self):
        result={'status':'UNKNOWN','unknown':'all premises missing'}
        with patch('tools.linguistic_truth.pipeline.acquire',return_value=result) as acquire:
            first=run('القرء',display_limit=10)
            second=run('القرء',display_limit=1,reverse_candidates=True)
            self.assertIs(first['acquisition'],result)
            self.assertIs(second['acquisition'],result)
            self.assertEqual(acquire.call_args_list[0],acquire.call_args_list[1])
            self.assertNotEqual(first['retrieval']['candidates'],second['retrieval']['candidates'])


if __name__=='__main__':
    unittest.main()
