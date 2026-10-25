"""Counterexamples to misleading progress metrics on the inherited diagnostic."""
from copy import deepcopy
import unittest

from tools import benchmark_linguistic_truth as benchmark
from tools.measure_natural_use import natural_metrics, ratio, validate_report


class NaturalUseMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = __import__('json').loads((benchmark.ROOT / 'evidence/linguistic_truth_v1/benchmark_final.json').read_text())

    def test_known_baseline_stage_denominators(self):
        result = natural_metrics(validate_report(self.report))
        for name, pair in {
            'full_case_success': (0, 6), 'any_lexical_occurrence': (2, 6),
            'required_candidate_obligations': (4, 12), 'positive_intended_selection': (0, 5),
            'required_ambiguity_preserved': (0, 1), 'source_identity_preserved': (6, 6),
            'native_checked_candidate_cases': (2, 6),
        }.items():
            self.assertEqual((result[name]['numerator'], result[name]['denominator']), pair)
        self.assertIsNone(result['selection_precision']['fraction'])

    def test_no_predictions_is_not_perfect_precision(self):
        self.assertIsNone(ratio(0, 0)['fraction'])

    def test_no_candidates_is_not_successful_ambiguity(self):
        result = natural_metrics(validate_report(self.report))
        self.assertEqual(result['required_ambiguity_preserved']['numerator'], 0)
        self.assertEqual(result['required_ambiguity_preserved']['denominator'], 1)

    def test_no_skipped_or_duplicate_cases_in_a_report(self):
        for operation in ('omit', 'duplicate'):
            changed = deepcopy(self.report)
            if operation == 'omit':
                changed['rows'].pop()
            else:
                changed['rows'][-1] = changed['rows'][0]
            with self.assertRaises(ValueError):
                validate_report(changed)

    def test_changed_gold_and_boolean_counts_are_not_accepted(self):
        changed = deepcopy(self.report)
        changed['gold_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            validate_report(changed)
        changed = deepcopy(self.report)
        changed['summary']['authority']['excess_claims'] = False
        with self.assertRaises(ValueError):
            validate_report(changed)

    def test_relabelled_result_without_changed_observation_is_rejected(self):
        changed = deepcopy(self.report)
        row = next(r for r in changed['rows'] if r['id'] == 'N05')
        for check in row['checks']:
            check['outcome'] = 'PASS'
        row['outcome'] = 'PASS'
        changed['summary'] = benchmark.summarize(changed['rows'])
        with self.assertRaisesRegex(ValueError, 'CHECKS_DIFFER_FROM_OBSERVATION'):
            validate_report(changed)

    def test_false_native_flag_is_not_counted(self):
        rows = validate_report(deepcopy(self.report))
        for occurrence in rows['N02']['raw_result']['occurrences']:
            occurrence['native_checked'] = False
        self.assertEqual(natural_metrics(rows)['native_checked_candidate_cases']['numerator'], 1)

    def test_false_native_flag_cannot_keep_a_passing_contract_gate(self):
        changed = deepcopy(self.report)
        row = next(r for r in changed['rows'] if r['id'] == 'N02')
        for occurrence in row['raw_result']['occurrences']:
            occurrence['native_checked'] = False
        with self.assertRaisesRegex(ValueError, 'CONTRADICTORY_CONTRACT_GATE'):
            validate_report(changed)

    def test_changed_execution_snapshot_cannot_keep_valid_integrity(self):
        changed = deepcopy(self.report)
        changed['execution_evidence']['after']['native_checker']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'CONTRADICTORY_EXECUTION_INTEGRITY'):
            validate_report(changed)

    def test_unmeasured_selection_is_not_a_correct_abstention(self):
        rows = validate_report(deepcopy(self.report))
        c = next(x for x in rows['N02']['checks'] if x['name'] == 'selected_senses')
        c.update(outcome='UNMEASURED', actual=None)
        result = natural_metrics(rows)
        self.assertEqual(result['positive_intended_selection']['numerator'], 0)
        self.assertEqual(result['positive_intended_selection']['denominator'], 5)


if __name__ == '__main__':
    unittest.main()
