"""Counterexamples to misleading progress metrics on the inherited diagnostic."""
from copy import deepcopy
import unittest

from tools import benchmark_linguistic_truth as benchmark
from tools.measure_natural_use import (CURRENT_OBSERVATION, CURRENT_REPORT,
    LEGACY_OBSERVATION, _row_observation, measure, natural_metrics, ratio, validate_report)


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
        row['observation'] = _row_observation(row, LEGACY_OBSERVATION)
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

    def current_report(self, historical=None):
        report = deepcopy(self.report if historical is None else historical)
        report['schema'] = CURRENT_REPORT
        report['observation_contract'] = CURRENT_OBSERVATION
        gold = {case['id']: case for case in benchmark.load_gold()['cases']}
        for row in report['rows']:
            if row['executed']:
                row['observation'] = _row_observation(row, CURRENT_OBSERVATION)
                row['checks'] = benchmark.evaluate(gold[row['id']], row['observation'])
                row['outcome'] = benchmark.case_outcome(row['checks'])
        report['summary'] = benchmark.summarize(report['rows'])
        report['contract_gate'] = benchmark.contract_gate(report['rows'], report['summary'],
            report['execution_evidence']['integrity'])
        return report

    def test_historical_v1_without_optional_observation_stays_valid(self):
        report = deepcopy(self.report)
        for row in report['rows']:
            row.pop('observation', None)
        self.assertEqual(natural_metrics(validate_report(report)),
                         natural_metrics(validate_report(self.report)))

    def test_current_v2_can_remeasure_same_historical_raw_without_relabeling_it(self):
        current = self.current_report()
        self.assertEqual([r['raw_result'] for r in current['rows']],
                         [r['raw_result'] for r in self.report['rows']])
        validate_report(current)
        result = measure(self.report, current)
        self.assertEqual(result['schema'], 'nabt.natural-use-measurement.v2')
        self.assertEqual(result['before_observation_contract'], LEGACY_OBSERVATION)
        self.assertEqual(result['after_observation_contract'], CURRENT_OBSERVATION)
        self.assertTrue(result['observation_contract_comparison']['contract_changed'])
        self.assertFalse(result['observation_contract_comparison']['semantic_improvement_established'])
        self.assertFalse(result['observation_contract_comparison']['runtime_executed_for_counterfactual'])

    def test_schema_or_contract_relabeling_cannot_hide_an_old_observation(self):
        for contract in (None, LEGACY_OBSERVATION, 'unknown', True):
            report = deepcopy(self.report)
            report['schema'] = CURRENT_REPORT
            if contract is not None:
                report['observation_contract'] = contract
            with self.subTest(contract=contract), self.assertRaisesRegex(ValueError, 'OBSERVATION_CONTRACT'):
                validate_report(report)
        report = deepcopy(self.report)
        report['schema'] = CURRENT_REPORT
        report['observation_contract'] = CURRENT_OBSERVATION
        with self.assertRaisesRegex(ValueError, 'OBSERVATION_DIFFERS_FROM_DECLARED_CONTRACT'):
            validate_report(report)
        report = self.current_report()
        report['schema'] = self.report['schema']
        with self.assertRaisesRegex(ValueError, 'CONTRADICTORY_OBSERVATION_CONTRACT'):
            validate_report(report)
        del report['observation_contract']
        with self.assertRaisesRegex(ValueError, 'OBSERVATION_DIFFERS_FROM_DECLARED_CONTRACT'):
            validate_report(report)

    def test_v1_has_no_new_expression_focus_fallback(self):
        row = deepcopy(next(r for r in self.report['rows'] if r['id'] == 'N02'))
        legacy = _row_observation(row, LEGACY_OBSERVATION)
        current = _row_observation(row, CURRENT_OBSERVATION)
        self.assertEqual(legacy['occurrences'][0]['surface'], 'الأسد')
        self.assertNotIn('expression', legacy['occurrences'][0])
        self.assertEqual(current['occurrences'][0]['surface'], 'أسد')
        self.assertEqual(current['occurrences'][0]['expression'], 'الأسد')

    def test_observer_only_check_changes_are_not_semantic_progress(self):
        # An adversarial transport contrast on existing candidates; the gold,
        # raw runtime response and its source remain unchanged across versions.
        historical = deepcopy(self.report)
        row = next(r for r in historical['rows'] if r['id'] == 'N02')
        row['raw_result']['occurrences'][0]['expression'] = 'unrelated_lexical_label'
        row['observation'] = _row_observation(row, LEGACY_OBSERVATION)
        case = next(c for c in benchmark.load_gold()['cases'] if c['id'] == 'N02')
        row['checks'] = benchmark.evaluate(case, row['observation'])
        row['outcome'] = benchmark.case_outcome(row['checks'])
        historical['summary'] = benchmark.summarize(historical['rows'])
        historical['contract_gate'] = benchmark.contract_gate(historical['rows'], historical['summary'],
            historical['execution_evidence']['integrity'])
        current = self.current_report(historical)
        result = measure(historical, current)
        counterfactual = result['observation_contract_comparison']
        self.assertEqual(counterfactual['changed_check_count'], 2)
        self.assertEqual({check['check'] for check in counterfactual['changed_checks']},
                         {'candidate_recall.lion', 'candidate_recall.brave_man'})
        self.assertTrue(counterfactual['before_raw_results_unchanged'])
        self.assertFalse(counterfactual['semantic_improvement_established'])
        self.assertEqual(result['natural_before']['positive_intended_selection'],
                         result['natural_after']['positive_intended_selection'])


if __name__ == '__main__':
    unittest.main()
