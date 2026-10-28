"""The post-exposure erratum is narrow; original evidence remains immutable."""
import copy
import gzip
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from tools import evaluate_sourced_acquisition_v3 as evaluator

ROOT = Path(__file__).resolve().parents[1]


class OracleReview(unittest.TestCase):
    def setUp(self):
        self.original = json.loads((ROOT / evaluator.GOLD_PATH).read_bytes())
        self.erratum = json.loads((ROOT / evaluator.ERRATUM_PATH).read_bytes())

    def test_original_gold_and_all_original_pins_remain_unchanged(self):
        for path, expected in {**evaluator.PINS, **evaluator.REVIEW_PINS}.items():
            with self.subTest(path=path):
                self.assertEqual(sha256((ROOT / path).read_bytes()).hexdigest(), expected)
        self.assertIn(evaluator.ERRATUM_PATH, evaluator.EXTRA_PATHS)

    def test_only_six_scalars_change_and_the_original_object_is_preserved(self):
        saved = copy.deepcopy(self.original)
        reviewed = evaluator.apply_oracle_review(self.original, self.erratum)
        by_id = {case['id']: case for case in reviewed['cases']}
        changed = 0
        for patch in self.erratum['patches']:
            values = by_id[patch['case_id']]['expected'][patch['projection']]
            self.assertEqual(values[patch['array_index']], 68)
            values[patch['array_index']] = 64
            changed += 1
        self.assertEqual(changed, 6)
        self.assertEqual(reviewed, saved)
        self.assertEqual(self.original, saved)

    def test_broader_duplicate_missing_or_boolean_patches_are_rejected(self):
        for change in ('extra', 'missing', 'duplicate', 'value', 'goal', 'boolean', 'index'):
            erratum = copy.deepcopy(self.erratum)
            rows = erratum['patches']
            if change == 'extra':
                rows.append(copy.deepcopy(rows[0]))
            elif change == 'missing':
                rows.pop()
            elif change == 'duplicate':
                rows[1] = copy.deepcopy(rows[0])
            elif change == 'value':
                rows[0]['after'] = 69
            elif change == 'goal':
                rows[0]['projection'] = '/status'
            elif change == 'boolean':
                rows[0]['before'] = True
            else:
                rows[0]['array_index'] = True
            with self.subTest(change=change), self.assertRaises(ValueError):
                evaluator.apply_oracle_review(self.original, erratum)

    def test_changed_precondition_cannot_be_silently_repatched(self):
        original = copy.deepcopy(self.original)
        case = next(case for case in original['cases'] if case['id'] == 'o_ayn_u')
        case['expected']['/realization/phrase_cells'][4] = 68
        with self.assertRaisesRegex(ValueError, 'precondition'):
            evaluator.apply_oracle_review(original, self.erratum)

    def test_pin_is_checked_before_accepting_review_metadata(self):
        guard = SimpleNamespace(load_json=lambda _: (self.erratum, 'not-the-code-owned-pin'))
        with self.assertRaisesRegex(ValueError, 'erratum pin'):
            evaluator.reviewed_gold(guard, self.original)

    def test_reviewed_oracle_cannot_claim_a_new_first_execution(self):
        with self.assertRaisesRegex(ValueError, 'exposed oracle correction'):
            evaluator.verify_freeze(Path('not-read.json'), 'first')

    def test_preserved_first_outputs_show_exactly_the_disclosed_projection_changes(self):
        item = self.erratum['preserved_first_result']
        compressed = (ROOT / item['archive_path']).read_bytes()
        self.assertEqual(sha256(compressed).hexdigest(), item['archive_sha256'])
        raw = gzip.decompress(compressed)
        self.assertEqual(sha256(raw).hexdigest(), item['decompressed_sha256'])
        first = json.loads(raw)
        reports = {row['id']: row['raw_result'] for row in first['rows']}
        reviewed = evaluator.apply_oracle_review(self.original, self.erratum)
        before = {case['id']: all(evaluator.matches(reports[case['id']], case['expected']).values())
                  for case in self.original['cases']}
        after = {case['id']: all(evaluator.matches(reports[case['id']], case['expected']).values())
                 for case in reviewed['cases']}
        self.assertEqual(sum(before.values()), 158)
        self.assertEqual(sum(after.values()), 161)
        self.assertEqual({key for key in before if before[key] != after[key]},
                         {'o_ayn_u', 'o_ayn_a', 'o_ayn_i'})
        self.assertEqual(first['summary']['positive_acquired'], 90)
        self.assertEqual(first['summary']['required_positive'], 109)


if __name__ == '__main__':
    unittest.main()
