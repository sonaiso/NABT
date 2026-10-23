"""Authored context-name agreement regression frozen before its correction.

This is explicit semantic context, not independently acquired lexical gender.
The standalone runner preserves the isolated before/after source inventories.
"""
import importlib.util
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import (read_discourse, ask_discourse,
                            verify_discourse, verify_discourse_answer)

FOLDER = Path(__file__).resolve().parents[1] / 'evidence/constructions/context_name_review'
SPEC = importlib.util.spec_from_file_location('context_name_review_runner', FOLDER / 'run_review.py')
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)
API = (learn_qac_lexicon, read_discourse, ask_discourse, verify_discourse, verify_discourse_answer)


class ContextNameAgreementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, material = REVIEW.load_material()
        cls.cases = {case['id']: case for case in material['cases']}

    def check_frozen_case(self, case_id):
        raw = REVIEW.execute_case(self.cases[case_id], API)
        self.assertTrue(raw['score']['passed'], raw['score'])
        self.assertFalse(raw['score']['false_accept'], raw['score'])


def _case_test(case_id):
    def test(self):
        self.check_frozen_case(case_id)
    test.__name__ = 'test_' + case_id.lower().replace('-', '_')
    return test


for _case_id in ['CNR-P01', 'CNR-P02', 'CNR-P03', 'CNR-P04',
                 'CNR-B01', 'CNR-B02', 'CNR-B03', 'CNR-B04', 'CNR-B05',
                 'CNR-B06', 'CNR-B07', 'CNR-B08', 'CNR-B09', 'CNR-B10',
                 'CNR-R01', 'CNR-R02']:
    setattr(ContextNameAgreementTests, 'test_' + _case_id.lower().replace('-', '_'), _case_test(_case_id))


if __name__ == '__main__':
    unittest.main()
