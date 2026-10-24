"""Static independent continuation checks; no new runtime prediction here."""
from copy import deepcopy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


P = module('tested_continuation_review', 'review_continuation_v3.py')
C = module('tested_continuation_source', 'run_source_counterexamples_v1.py')


class ContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline, cls.reviewed, cls.expected, cls.mutations = P.historical_reference()

    def test_no_production_runtime_is_imported_by_static_review(self):
        self.assertFalse(any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules))

    def test_every_historical_public_call_and_case_record_is_exact(self):
        old = P.canonical_records(gzip.decompress((P.ORACLE / 'first_run_v1/raw.jsonl.gz').read_bytes()))
        before = [x for x in old if x['kind'] == 'public_api_call']
        after = [x for x in self.expected if x['kind'] == 'public_api_call']
        self.assertEqual(len(before), 171)
        self.assertEqual(P.E.wire(before), P.E.wire(after))
        self.assertEqual(P.E.wire([x['record'] for x in old if x['kind'] == 'case_observation']),
                         P.E.wire([x['record'] for x in self.expected if x['kind'] == 'case_observation']))
        self.assertEqual(len(self.expected), 214)
        P.require_exact_trace(self.expected, self.expected)

    def test_fresh_independent_scores_preserve_all_24_observations(self):
        _, material, _, profiles = P.R.load_material()
        observations = [x for x in self.expected if x['kind'] == 'case_observation']
        audits = {key: P.E.SourceAudit((P.ORACLE / profile['file']).read_bytes(),
                                      source_id='independent_oracle_lexical_' + key)
                  for key, profile in profiles.items()}
        records = {}
        for case, observation in zip(material['cases'], observations):
            record = observation['record']
            records[case['id']] = record
            scored = P.S.score_case(case, record, audits[record['profile']])
            with self.subTest(case=case['id']):
                self.assertEqual(P.E.wire(scored), P.E.wire(observation['score']))
        logs = []
        outcomes = P.M.run(records, audits, logs.append)
        self.assertEqual(P.E.wire(logs), P.E.wire(self.mutations))
        self.assertEqual(sum(x['outcome'] == 'PASS' for x in outcomes), 13)
        self.assertEqual(sum(x['outcome'] == 'UNEXERCISED' for x in outcomes), 5)
        self.assertEqual(self.reviewed['fixed_cases'], {'total': 22, 'passed': 14, 'failed': 8})
        self.assertEqual(self.reviewed['questions']['status_matches'], 19)

    def test_trace_rejects_added_authority_changed_input_and_boolean_call_id(self):
        index = next(i for i, x in enumerate(self.expected) if x.get('name') == 'read_discourse')
        for kind in ('authority', 'input', 'call_type', 'omitted', 'reordered', 'score'):
            changed = deepcopy(self.expected)
            if kind == 'authority':
                changed[index]['returned']['world_truth'] = 'ESTABLISHED'
            elif kind == 'input':
                changed[index]['inputs']['text'] = 'different'
            elif kind == 'call_type':
                changed[0]['call_id'] = True
                self.assertEqual(changed[0]['call_id'], self.expected[0]['call_id'])
            elif kind == 'omitted':
                changed.pop(index)
            elif kind == 'reordered':
                changed[index], changed[index + 1] = changed[index + 1], changed[index]
            else:
                row = next(x for x in changed if x['kind'] == 'case_observation' and x['case_id'] == 'N04')
                row['score']['passed'] = True
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'Continuation'):
                P.require_exact_trace(changed, self.expected)

    def test_raw_canonical_form_cannot_be_replaced_by_equal_json(self):
        good = P.R.dump({'call_id': 1, 'kind': 'public_api_call'}) + b'\n'
        self.assertEqual(P.canonical_records(good)[0]['call_id'], 1)
        for bad in (good[:-1], b'{"kind":"public_api_call", "call_id":1}\n', b'{"x":NaN}\n'):
            with self.subTest(raw=bad), self.assertRaises(ValueError):
                P.canonical_records(bad)

    def test_snapshot_allows_only_absolute_checkout_relocation(self):
        original = {'runtime_root': '/old/repo', 'runtime_file_count': 80,
                    'files': [{'path': 'src/nabt/reader.py', 'bytes': 1, 'sha256': 'a' * 64}]}
        current = deepcopy(original)
        current['runtime_root'] = '/runner/work/repo'
        self.assertTrue(P.snapshot_equal(current, original))
        for kind in ('root', 'count', 'hash', 'bytes', 'authority'):
            changed = deepcopy(current)
            if kind == 'root': changed['runtime_root'] = 'relative'
            if kind == 'count': changed['runtime_file_count'] = 80.0
            if kind == 'hash': changed['files'][0]['sha256'] = 'b' * 64
            if kind == 'bytes': changed['files'][0]['bytes'] = True
            if kind == 'authority': changed['extra_authority'] = True
            with self.subTest(kind=kind): self.assertFalse(P.snapshot_equal(changed, original))

    def test_source_counterexample_material_has_two_controls_and_four_refusals(self):
        material, _ = C.load_cases()
        predicates = [C.raw_can_license((C.MATERIAL / c['raw_file']).read_bytes()) for c in material['cases']]
        self.assertEqual(predicates, [True, True, False, False, False, False])
        self.assertEqual(material['old_denominators_unchanged'], {'fixed_cases': 22, 'provenance_probes': 2, 'questions': 29})

    def test_raw_source_predicate_rejects_missing_and_competing_profiles(self):
        raw = (C.MATERIAL / 'h01.tsv').read_bytes()
        self.assertTrue(C.raw_can_license(raw))
        for before, after in [(b'|3MS|PERF', b'|3MS|2MS|PERF'), (b'|3MS|PERF', b'|3MS|PERF|IMPF'),
                              (b'|3MS|PERF', b'|3MS|PERF|(I)|(II)'), (b'\tHasiba\t', b'\tHsb\t'),
                              (b'LEM:Hasiba', b'LEM:Hasiba|LEM:Hasaba')]:
            with self.subTest(after=after):
                self.assertFalse(C.raw_can_license(raw.replace(before, after)))

    def test_missing_report_is_an_integrity_failure_not_a_negative_pass(self):
        material, context = C.load_cases()
        case = material['cases'][2]
        score = C.score_case(case, {'inputs': {**case['input'], 'context': context}, 'report': None,
                                   'verification': {'valid': True}, 'questions': []}, context)
        self.assertFalse(score['passed'])
        self.assertEqual(score['checks'][0]['kind'], 'integrity')
        self.assertFalse(score['checks'][0]['passed'])

    def test_source_saved_review_rejects_forged_call_binding_before_scoring(self):
        material, _ = C.load_cases()
        case = material['cases'][0]
        raw = (C.MATERIAL / case['raw_file']).read_bytes()
        good = {'kind': 'public_api_call', 'call_id': 1, 'name': 'learn_qac_lexicon', 'case_id': case['id'],
                'question_index': None, 'inputs': {'source_id': case['source_id'], 'raw_hex': raw.hex(),
                'raw_sha256': case['raw_sha256'], 'excluded_verses': []}, 'returned': {}}
        for kind in ('source', 'bytes', 'call_type', 'extra'):
            row = deepcopy(good)
            if kind == 'source': row['inputs']['source_id'] = 'unrelated_source'
            if kind == 'bytes': row['inputs']['raw_hex'] = '00'
            if kind == 'call_type': row['call_id'] = True
            if kind == 'extra': row['authority'] = 'TRUST_ME'
            result = {key: None for key in ('schema', 'started_utc', 'material_freeze_sha256', 'source_material_freeze_sha256',
                'runtime_freeze_sha256', 'runner', 'snapshot', 'code_archive', 'cases', 'execution_errors', 'scoring_errors',
                'not_a_blind_sample', 'historical_denominators_unchanged', 'raw_journal', 'public_api_calls', 'snapshot_after',
                'runtime_unchanged', 'runner_and_helpers_unchanged', 'summary', 'finished_utc', 'measurement_valid', 'gate_pass')}
            result.update(schema=C.VERSION, source_material_freeze_sha256=P.SOURCE_MATERIAL,
                          not_a_blind_sample=True, historical_denominators_unchanged=True)
            with self.subTest(kind=kind), patch.object(C.P, 'checked_artifacts',
                    return_value=(result, [row], {}, {}, {})), self.assertRaisesRegex(ValueError, 'call/inputs'):
                C.review_saved(Path('unused.json'), Path('unused.gz'))


if __name__ == '__main__':
    unittest.main()
