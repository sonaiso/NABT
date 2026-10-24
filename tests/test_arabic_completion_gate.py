"""Adversarial mutations of the actual complete strict measurement receipts."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('arabic_completion_gate_tested', ROOT / 'tools/arabic_completion_gate.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class ReviewedArabicCompletionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = gate.load_policy()
        cls.results = {}
        for suite, policy in cls.policy['suites'].items():
            payload = (ROOT / policy['strict_measurement']).read_bytes()
            if sha256(payload).hexdigest() != policy['strict_measurement_sha256']:
                raise AssertionError('Preserved strict measurement changed: ' + suite)
            cls.results[suite] = json.loads(payload)

    def each(self):
        return ((suite, deepcopy(result)) for suite, result in self.results.items())

    def reject(self, suite, result):
        decision = gate.gate_decision(suite, result, True)
        self.assertFalse(decision['gate_pass'], (suite, decision))
        self.assertFalse(decision['coverage_complete'])
        self.assertTrue(decision['unexpected_failures'] or decision['gate_integrity_errors'])

    @staticmethod
    def fail(result, suite, case_id, check_id):
        case = next(c for c in result['cases'] if c['id'] == case_id)
        check = next(c for c in case['checks'] if c['check'] == check_id)
        check['passed'] = False
        failure = deepcopy(check) if suite == 'construction' else {'check': check_id}
        existing = {f['check']: f for f in case['failures']}
        existing[check_id] = failure
        case['failures'] = [existing[c['check']] for c in case['checks'] if c['passed'] is False]
        case['passed'] = False
        result['passed'] = sum(c['passed'] for c in result['cases'])

    def test_narrow_debt_acceptance_preserves_all_scores_and_failed_flags(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                before = deepcopy(result)
                decision = gate.gate_decision(suite, result, True)
                self.assertTrue(decision['gate_pass'])
                self.assertFalse(decision['coverage_complete'])
                self.assertFalse(decision['all_arabic_completeness_established'])
                self.assertFalse(result['strict_pass'])
                self.assertEqual(result, before)
                self.assertEqual(len(decision['documented_boundary_failures']),
                                 30 if suite == 'construction' else 38)
                self.assertEqual(sum(not c['passed'] for c in result['cases']),
                                 4 if suite == 'construction' else 18)
                self.assertFalse(gate.gate_decision(suite, result, False)['gate_pass'])

    def test_a_previously_fixed_case_cannot_reenter_the_old_debt_list(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                self.fail(result, suite, 'CON-Z02' if suite == 'construction' else 'DSC-P02',
                          'complete_construction' if suite == 'construction' else 'required_claim:0')
                self.reject(suite, result)

    def test_a_previously_fixed_check_in_a_residual_case_is_not_waived(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                self.fail(result, suite, 'CON-Z10' if suite == 'construction' else 'DSC-T04',
                          'complete_construction' if suite == 'construction' else 'reading:0')
                self.reject(suite, result)

    def test_changed_failure_status_requires_new_review(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                case = next(c for c in result['cases'] if c['failures'])
                failure = next(f for f in case['failures'] if f['check'].startswith('question:'))
                failure['details']['status' if suite == 'construction' else 'actual'] = 'UNKNOWN'
                if suite == 'construction':
                    check = next(c for c in case['checks'] if c['check'] == failure['check'])
                    check['details'] = deepcopy(failure['details'])
                self.reject(suite, result)

    def test_inventories_reject_missing_duplicate_reordered_cases(self):
        for suite, base in self.each():
            for mode in ('missing', 'duplicate', 'reordered'):
                with self.subTest(suite=suite, mode=mode):
                    result = deepcopy(base)
                    if mode == 'missing':
                        result['cases'].pop()
                    elif mode == 'duplicate':
                        result['cases'][-1] = deepcopy(result['cases'][0])
                    else:
                        result['cases'][0], result['cases'][1] = result['cases'][1], result['cases'][0]
                    self.reject(suite, result)

    def test_removing_a_check_does_not_improve_coverage(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                result['cases'][0]['checks'].pop()
                self.reject(suite, result)

    def test_failed_checks_cannot_be_removed_or_relabeled_as_passed(self):
        for suite, base in self.each():
            for mode in ('failure_deleted', 'pass_forged', 'check_forged'):
                with self.subTest(suite=suite, mode=mode):
                    result = deepcopy(base)
                    case = next(c for c in result['cases'] if c['failures'])
                    if mode == 'failure_deleted':
                        case['failures'].pop()
                    elif mode == 'pass_forged':
                        case['passed'] = True
                        result['passed'] += 1
                    else:
                        next(c for c in case['checks'] if c['passed'] is False)['passed'] = True
                    self.reject(suite, result)

    def test_booleans_and_numbers_are_not_interchangeable(self):
        for suite, base in self.each():
            for field, value in (('false_accept_count', False), ('false_accept_case_count', False),
                                 ('total', True), ('passed', True), ('strict_pass', 0)):
                with self.subTest(suite=suite, field=field):
                    result = deepcopy(base)
                    result[field] = value
                    self.reject(suite, result)
            result = deepcopy(base)
            result['cases'][0]['checks'][0]['passed'] = 1
            self.reject(suite, result)

    def test_false_acceptance_is_never_waived_even_with_zero_summary(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                result['cases'][0]['false_accepts'] = [{'check': 'independent_counterexample'}]
                self.reject(suite, result)

    def test_errors_and_invalid_measurements_cannot_pass(self):
        for suite, base in self.each():
            for field in ('execution_errors', 'question_execution_errors', 'measurement_valid'):
                with self.subTest(suite=suite, field=field):
                    result = deepcopy(base)
                    result[field] = False if field == 'measurement_valid' else [{'error': 'counterexample'}]
                    self.reject(suite, result)

    def test_invalid_or_truncated_raw_journal_cannot_pass(self):
        for suite, base in self.each():
            for mode in ('validity', 'record', 'count'):
                with self.subTest(suite=suite, mode=mode):
                    result = deepcopy(base)
                    raw = result['raw_log']
                    if mode == 'validity':
                        raw['complete_gzip_verified' if suite == 'construction' else 'valid'] = False
                    elif mode == 'record':
                        raw['record_inventory' if suite == 'construction' else 'records'].pop()
                    else:
                        raw['case_count'] = True
                    self.reject(suite, result)

    def test_material_and_runtime_pins_cannot_be_substituted(self):
        for suite, base in self.each():
            for field in ('gold_freeze_sha256', 'source_sha256', 'runtime_freeze_sha256',
                          'runtime_snapshot_sha256', 'runtime_file_count'):
                with self.subTest(suite=suite, field=field):
                    result = deepcopy(base)
                    target = result['snapshot'] if field.startswith('runtime_') else result
                    target[field] = 76 if field == 'runtime_file_count' else '0' * 64
                    self.reject(suite, result)

    def test_replay_failure_cannot_be_added_to_coverage_debt(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                self.fail(result, suite, result['cases'][0]['id'],
                          'report_replay' if suite == 'construction' else 'original_report_replay')
                self.reject(suite, result)

    def test_construction_question_certificates_remain_unconditional(self):
        result = deepcopy(self.results['construction'])
        question = next(c for c in result['cases'][0]['checks'] if c['check'].startswith('question:'))
        question['details']['certificate'] = False
        self.reject('construction', result)

    def test_forged_strict_pass_does_not_bypass_the_gate(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                result['strict_pass'] = True
                self.reject(suite, result)

    def test_debt_can_shrink_without_relabeling_other_failures(self):
        for suite, result in self.each():
            with self.subTest(suite=suite):
                case = next(c for c in result['cases'] if len(c['failures']) > 1)
                failure = case['failures'].pop(0)
                next(c for c in case['checks'] if c['check'] == failure['check'])['passed'] = True
                decision = gate.gate_decision(suite, result, True)
                self.assertTrue(decision['gate_pass'])
                self.assertFalse(decision['coverage_complete'])
                self.assertFalse(decision['all_arabic_completeness_established'])

    def test_policy_byte_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'policy.json'
            path.write_bytes(gate.POLICY_PATH.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'policy bytes changed'):
                gate.load_policy(path)

    def test_malformed_receipt_fails_closed(self):
        self.reject('construction', {})
        self.reject('discourse', {'snapshot': None})


if __name__ == '__main__':
    unittest.main()
