import copy
import unittest
from tools.qatr_training.proposal import project_ranking


class QatrProposalTests(unittest.TestCase):
    def reading(self):
        return dict(cases=['nasb','jazm'],rows=[dict(id=36,case='nasb'),dict(id=39,case='jazm')])

    def test_outside_top_score_is_disclosed_and_cannot_enter_ranking(self):
        reading=self.reading();old=copy.deepcopy(reading)
        r=project_ranking(reading,[1,99,0,2])
        self.assertEqual(r['raw_case_proposal'],'raf')
        self.assertTrue(r['raw_case_outside_proposed_set'])
        self.assertEqual(r['ranked_cases'],['jazm','nasb'])
        self.assertEqual(r['reading_rows'],old['rows']);self.assertEqual(reading,old)
        self.assertEqual(r['authority'],'NONE');self.assertFalse(r['reading_licensed'])

    def test_no_score_can_delete_an_allowed_alternative(self):
        r=project_ranking(self.reading(),[100,0,0,-100])
        self.assertEqual(r['ranked_cases'],['nasb','jazm'])
        self.assertEqual(len(r['reading_rows']),2)

    def test_empty_and_invalid_cases_do_not_create_licenses(self):
        r=project_ranking(dict(cases=[],rows=[]),[1,2,3,4])
        self.assertEqual(r['status'],'NO_SUPPORTED_READING');self.assertFalse(r['reading_licensed'])
        for scores in ([True,0,0,0],[float('nan'),0,0,0],[0,0,0],['1',0,0,0]):
            with self.assertRaises(ValueError):project_ranking(self.reading(),scores)
        with self.assertRaises(ValueError):project_ranking(dict(cases=['raf'],rows=[]),[0,0,0,0])
