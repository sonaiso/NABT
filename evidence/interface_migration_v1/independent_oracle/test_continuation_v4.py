"""Static tamper controls over preserved observations; no runtime prediction.

Artifact byte/archive checks are stubbed only to isolate semantic review. The
production command still performs them before these same semantic checks.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tested_v6_review2', HERE / 'review_continuation_v4.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


class ContinuationReview2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = P.historical_reference()
        baseline, reference, expected, _ = cls.history
        cls.values = expected
        cls.result = deepcopy(baseline)
        for key in ('cases', 'mutation_checks', 'fixed_cases', 'questions', 'conditional_provenance',
                    'measurement_valid', 'unsafe_check_failures', 'independent_integrity_failures',
                    'execution_errors', 'scoring_errors', 'cross_case_checks', 'strict_pass',
                    'runtime_unchanged', 'runner_and_helpers_unchanged'):
            cls.result[key] = deepcopy(reference[key])
        cls.result['schema'] = P.R.VERSION
        cls.result['scorer'] = P.S.VERSION
        scores = cls.result['cases']
        cls.result['categories'] = {
            category: {'total': sum(c['category'] == category for c in scores),
                       'passed': sum(c['category'] == category and c['passed'] for c in scores)}
            for category in sorted({c['category'] for c in scores})}

    def semantic_review(self, result=None, values=None):
        result = deepcopy(self.result if result is None else result)
        values = deepcopy(self.values if values is None else values)
        runner, current = {'sha256': 'synthetic_byte_layer_fixture'}, {}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(P, 'historical_reference', return_value=self.history), \
                patch.object(P, 'checked_artifacts', return_value=(result, values, current, runner, {})), \
                patch.object(P.R, 'check_runner_freeze', return_value=runner), \
                patch.object(P.E, 'runtime_snapshot', return_value=current):
            return P.review(Path('unused.json'), Path('unused.gz'), Path(directory) / 'review')

    def test_preserved_observations_remain_partial_not_new_language_success(self):
        review = self.semantic_review()
        self.assertTrue(review['regression_gate_pass'])
        self.assertFalse(review['strict_pass'])
        self.assertEqual(review['fixed_cases'], {'total': 22, 'passed': 14, 'failed': 8})
        self.assertEqual(review['questions'], {
            'total': 29, 'observed': 29, 'status_matches': 19, 'independently_validated': 29})

    def test_aggregate_counts_and_provenance_cannot_be_forged(self):
        for group, field, value in (
                ('fixed_cases', 'passed', 22), ('fixed_cases', 'total', 23),
                ('questions', 'status_matches', 29), ('questions', 'observed', 30),
                ('questions', 'independently_validated', 30),
                ('conditional_provenance', 'total', 3),
                ('conditional_provenance', 'not_counted_as_language_coverage', False)):
            changed = deepcopy(self.result)
            changed[group][field] = value
            with self.subTest(group=group, field=field), self.assertRaisesRegex(ValueError, 'summary differs'):
                self.semantic_review(result=changed)

    def test_partial_and_measurement_flags_are_recomputed(self):
        for field, value, message in (
                ('strict_pass', True, 'Partial result'), ('strict_pass', 0, 'Partial result'),
                ('measurement_valid', False, 'Measurement validity'),
                ('measurement_valid', 1, 'Measurement validity')):
            changed = deepcopy(self.result)
            changed[field] = value
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, message):
                self.semantic_review(result=changed)

    def test_public_call_payloads_are_bound_to_scored_records(self):
        for kind in ('input', 'returned', 'question_index', 'extra_field'):
            changed = deepcopy(self.values)
            call = next(row for row in changed if row.get('name') == 'read_discourse')
            if kind == 'input':
                call['inputs']['text'] = 'different unscored input'
            elif kind == 'returned':
                call['returned']['world_truth'] = 'ESTABLISHED'
            elif kind == 'question_index':
                call['question_index'] = 0
            else:
                call['authority'] = 'TRUST_ME'
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'Public call input/output'):
                self.semantic_review(values=changed)

    def test_learning_material_and_call_identity_are_bound(self):
        for kind in ('raw_hex', 'raw_sha256', 'source_id', 'returned_source', 'boolean_id'):
            changed = deepcopy(self.values)
            call = next(row for row in changed if row.get('name') == 'learn_qac_lexicon')
            if kind == 'returned_source':
                call['returned']['source']['byte_length'] += 1
            elif kind == 'boolean_id':
                call['call_id'] = True
            else:
                call['inputs'][kind] = 'forged'
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'Learning call|Public call inventory'):
                self.semantic_review(values=changed)

    def test_cross_case_false_to_true_cannot_claim_an_unobserved_improvement(self):
        for change_raw_too in (False, True):
            changed_result, changed_values = deepcopy(self.result), deepcopy(self.values)
            changed_result['cross_case_checks'][2]['passed'] = True
            if change_raw_too:
                next(row for row in changed_values if row['kind'] == 'cross_case_observations')['checks'][2]['passed'] = True
            with self.subTest(change_raw_too=change_raw_too), self.assertRaisesRegex(ValueError, 'Cross-case summary'):
                self.semantic_review(result=changed_result, values=changed_values)

    def test_changed_speaker_calls_and_observations_are_bound(self):
        for kind in ('input_context', 'returned', 'observation'):
            changed = deepcopy(self.values)
            call = next(row for row in changed if row.get('name') == 'verify_discourse_changed_speaker')
            if kind == 'input_context':
                call['inputs']['context']['speaker'] = 'unscored'
            elif kind == 'returned':
                call['returned']['code'] = 'UNRELATED_REFUSAL'
            else:
                next(row for row in changed if row['kind'] == 'cross_case_observations')['changed_speaker']['P04']['report']['code'] = 'UNRELATED_REFUSAL'
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'Changed-speaker public call'):
                self.semantic_review(values=changed)

    def test_new_dependency_lineage_preserves_old_freeze_and_runtime(self):
        freeze = HERE / 'runner_freeze_v4.json'
        if not freeze.exists():
            self.skipTest('Dependency freeze has not been registered yet; static tests precede it')
        actual = P.R.check_runner_freeze(freeze)
        record = json.loads(freeze.read_bytes())
        old = P.R.ROOT / 'evidence/source_acquisition_v1/independent_oracle/runner_freeze_v5.json'
        self.assertEqual(record['previous_dependency_freeze_sha256'], P.sha256(old.read_bytes()).hexdigest())
        self.assertEqual(record['previous_dependency_freeze_sha256'], 'ecf96d1d8eabaa42d53522d179142ace305587eec3a3b49bd52a799a12ac323a')
        self.assertEqual(record['runtime_freeze_sha256'], P.R.RUNTIME_SHA)
        paths = {row['path'] for row in actual['files']}
        self.assertIn('tools/productive_form_validation.py', paths)
        self.assertIn('tools/productive_evaluation.py', paths)
        self.assertIn(str(Path(__file__).relative_to(P.R.ROOT)), paths)
        self.assertTrue(any('/interface_migration_v1/independent_oracle/review_' in path for path in paths))
        self.assertFalse(any('/continuation_v6_review2/review_' in path for path in paths))


if __name__ == '__main__':
    unittest.main()
