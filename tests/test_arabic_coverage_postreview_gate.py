"""Adversarial post-review gate tests; no runtime or holdout is executed."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
from pathlib import Path
import unittest


PATH = Path(__file__).resolve().parents[1] / 'tools/arabic_coverage_postreview_v2.py'
SPEC = importlib.util.spec_from_file_location('postreview_gate_under_test', PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def summary_example():
    """An explicitly authored two-case summary tests the preflight in isolation.

    Passing this function is not a gate pass: real run() pins the 36-case
    material, validates raw observations, replays every certificate, and checks
    H18 independently before it can emit gate_pass=True.
    """
    material = {'cases': [
        {'id': 'H01', 'category': 'positive', 'focus': 'first', 'questions': []},
        {'id': 'H18', 'category': 'positive', 'focus': 'second', 'questions': [{}, {}, {}]}]}
    runtime = {'files': [{'path': 'pyproject.toml', 'bytes': 5, 'sha256': 'config'},
                         {'path': 'src/nabt/example.py', 'bytes': 7, 'sha256': 'runtime'}]}
    entries = runtime['files'][1:]
    inventory = {'entries': entries, 'sha256': sha256(gate.wire(entries)).hexdigest()}
    failure = {'name': gate.TARGET[1], 'pass': False, 'unsafe_acceptance': True}
    result = {'schema': 'nabt.independent-arabic-holdout-result.v1',
              'material_freeze_sha256': gate.MATERIAL_SHA256, 'measurement_valid': True,
              'runtime_unchanged': True, 'runtime_errors': [], 'runtime_before': deepcopy(inventory),
              'runtime_after': deepcopy(inventory), 'strict_pass': False, 'coverage_complete': False,
              'case_score': {'passed': 1, 'total': 2}, 'category_scores': {'positive': {'total': 2, 'passed': 1}},
              'question_total': 3, 'cases': [
                  {'id': 'H01', 'category': 'positive', 'focus': 'first', 'passed': True,
                   'checks': [{'name': 'some_check', 'pass': True}]},
                  {'id': 'H18', 'category': 'positive', 'focus': 'second', 'passed': False, 'checks': [failure]}],
              'unsafe_acceptances': [{'case_id': 'H18', **failure}],
              'cross_case_checks': [{'name': 'cross:' + str(i), 'pass': True} for i in range(4)],
              'separate_replay_checks': [{'name': 'replay:' + str(i), 'pass': True} for i in range(4)]}
    return result, material, runtime


def journal(records):
    lines = [gate.wire(record) for record in records]
    raw = b'\n'.join(lines) + b'\n'
    result = {'raw_log': {'sha256': sha256(raw).hexdigest(), 'records': len(lines),
                         'line_sha256': [sha256(line).hexdigest() for line in lines],
                         'complete_reparse_and_line_hashes': True}}
    return raw, result


class PostreviewGateTests(unittest.TestCase):
    def test_exact_known_false_alarm_only_advances_to_further_validation(self):
        result, material, runtime = summary_example()
        self.assertEqual(gate.validate_measurement_summary(result, material, runtime), result['unsafe_acceptances'])
        self.assertNotIn('gate_pass', result)

    def test_new_failure_cannot_use_the_existing_h18_exception(self):
        for cid in ('H01', 'H18'):
            result, material, runtime = summary_example()
            case = next(case for case in result['cases'] if case['id'] == cid)
            case['checks'].append({'name': 'new_failure', 'pass': False})
            case['passed'] = False
            with self.subTest(cid=cid), self.assertRaisesRegex(ValueError, 'only the demonstrated H18'):
                gate.validate_measurement_summary(result, material, runtime)

    def test_error_flags_runtime_changes_and_material_changes_fail_closed(self):
        for field, value in [('measurement_valid', False), ('runtime_unchanged', False),
                             ('runtime_errors', [{'type': 'resource_exhaustion'}]),
                             ('material_freeze_sha256', 'unapproved')]:
            result, material, runtime = summary_example()
            result[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                gate.validate_measurement_summary(result, material, runtime)

    def test_rehashed_wrong_runtime_inventory_still_fails_the_approved_bytes(self):
        result, material, runtime = summary_example()
        result['runtime_before']['entries'][0]['sha256'] = 'changed'
        result['runtime_before']['sha256'] = sha256(gate.wire(result['runtime_before']['entries'])).hexdigest()
        result['runtime_after'] = deepcopy(result['runtime_before'])
        with self.assertRaisesRegex(ValueError, 'approved frozen runtime'):
            gate.validate_measurement_summary(result, material, runtime)

    def test_only_the_explicit_non_runtime_metadata_paths_may_extend_the_inventory(self):
        for path in sorted(gate.NON_RUNTIME_METADATA):
            result, material, runtime = summary_example()
            entries=result['runtime_before']['entries']
            entries.append({'path':path,'bytes':13,'sha256':'observed_metadata_hash'})
            entries.sort(key=lambda item:item['path'])
            result['runtime_before']['sha256']=sha256(gate.wire(entries)).hexdigest()
            result['runtime_after']=deepcopy(result['runtime_before'])
            self.assertEqual(gate.validate_measurement_summary(result,material,runtime),result['unsafe_acceptances'])
        for path in ('src/nabt/unapproved.py','src/nabt/data/source_evidence/EXTRA.md'):
            result,material,runtime=summary_example()
            entries=result['runtime_before']['entries']
            entries.append({'path':path,'bytes':13,'sha256':'unapproved'})
            entries.sort(key=lambda item:item['path'])
            result['runtime_before']['sha256']=sha256(gate.wire(entries)).hexdigest()
            result['runtime_after']=deepcopy(result['runtime_before'])
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'approved frozen runtime'):
                gate.validate_measurement_summary(result,material,runtime)

    def test_known_metadata_is_still_part_of_the_full_before_after_identity(self):
        result,material,runtime=summary_example()
        entries=result['runtime_before']['entries']
        entries.append({'path':sorted(gate.NON_RUNTIME_METADATA)[0],'bytes':13,'sha256':'before'})
        entries.sort(key=lambda item:item['path'])
        result['runtime_before']['sha256']=sha256(gate.wire(entries)).hexdigest()
        result['runtime_after']=deepcopy(result['runtime_before'])
        result['runtime_after']['entries'][0]['sha256']='after'
        result['runtime_after']['sha256']=sha256(gate.wire(result['runtime_after']['entries'])).hexdigest()
        with self.assertRaisesRegex(ValueError,'Full source inventory changed'):
            gate.validate_measurement_summary(result,material,runtime)

    def test_original_unsafe_flag_cannot_be_silently_erased_or_extended(self):
        for entries in [[], [{'case_id': 'H18', 'name': gate.TARGET[1], 'pass': False}],
                        [{'case_id': 'H01', 'name': 'other', 'pass': False, 'unsafe_acceptance': True}]]:
            result, material, runtime = summary_example(); result['unsafe_acceptances'] = entries
            with self.subTest(entries=entries), self.assertRaisesRegex(ValueError, 'unsafe inventory'):
                gate.validate_measurement_summary(result, material, runtime)

    def test_case_inventory_and_denominators_cannot_be_reduced(self):
        for change in ('missing_case', 'duplicate_case', 'score', 'questions', 'category'):
            result, material, runtime = summary_example()
            if change == 'missing_case': result['cases'].pop(0)
            elif change == 'duplicate_case': result['cases'][0] = deepcopy(result['cases'][1])
            elif change == 'score': result['case_score'] = {'passed': 1, 'total': 1}
            elif change == 'questions': result['question_total'] = 2
            else: result['category_scores']['positive']['passed'] = 2
            with self.subTest(change=change), self.assertRaises(ValueError):
                gate.validate_measurement_summary(result, material, runtime)

    def test_original_strict_failure_cannot_be_relabelled_as_success(self):
        for field in ('strict_pass', 'coverage_complete'):
            result, material, runtime = summary_example(); result[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'strict failure was concealed'):
                gate.validate_measurement_summary(result, material, runtime)

    def test_cross_context_failures_missing_checks_and_duplicate_checks_block_review(self):
        for name in ('cross_case_checks', 'separate_replay_checks'):
            for mutation in ('false', 'missing', 'duplicate'):
                result, material, runtime = summary_example()
                if mutation == 'false': result[name][0]['pass'] = False
                elif mutation == 'missing': result[name].pop()
                else: result[name][1] = deepcopy(result[name][0])
                with self.subTest(name=name, mutation=mutation), self.assertRaisesRegex(ValueError, 'context-replay check'):
                    gate.validate_measurement_summary(result, material, runtime)

    def test_raw_journal_requires_canonical_bytes_and_captured_line_inventory(self):
        record = {'call': 'lexical_summary', 'case_id': None, 'value': {'a': 1}}
        raw, result = journal([record])
        self.assertEqual(gate.read_journal(raw, result)[0], [record])
        result['raw_log']['line_sha256'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'line inventory changed'):
            gate.read_journal(raw, result)
        raw = b'{ "call":"lexical_summary","case_id":null,"value":{} }\n'
        result = {'raw_log': {'sha256': sha256(raw).hexdigest(), 'records': 1,
                             'line_sha256': [sha256(raw.rstrip(b'\n')).hexdigest()],
                             'complete_reparse_and_line_hashes': True}}
        with self.assertRaisesRegex(ValueError, 'not canonical'):
            gate.read_journal(raw, result)

    def test_duplicate_raw_calls_fail_even_with_consistent_new_hashes(self):
        record = {'call': 'lexical_summary', 'case_id': None, 'value': {}}
        raw, result = journal([record, record])
        with self.assertRaisesRegex(ValueError, 'duplicate call identities'):
            gate.read_journal(raw, result)

    def test_unknown_raw_record_fields_are_not_accepted_as_receipts(self):
        raw, result = journal([{'call': 'lexical_summary', 'case_id': None, 'value': {}, 'waiver': True}])
        with self.assertRaisesRegex(ValueError, 'Unknown raw record shape'):
            gate.read_journal(raw, result)

    def test_a_pass_flag_cannot_substitute_for_an_authored_required_claim(self):
        text = 'authored protocol source'
        case = {'id': 'H01', 'category': 'positive', 'focus': 'protocol', 'text': text,
                'questions': [], 'expected_document_status': 'LICENSED_DISCOURSE',
                'required_claims': [{'predicate': 'required'}], 'forbidden_claims': []}
        document = {'source_text': text, 'source_id': 'holdout_h01', 'scope': 'independent_holdout_v1',
                    'source_sha256': sha256(text.encode()).hexdigest(), 'world_truth': 'NOT_ESTABLISHED',
                    'status': 'LICENSED_DISCOURSE', 'claims': [], 'clauses': []}
        document['report_id'] = sha256(gate.wire(document)).hexdigest()
        by_key = {('read_discourse', 'H01', None): document}
        result = {'cases': [{'id': 'H01', 'passed': True, 'checks': []}]}
        with self.assertRaisesRegex(ValueError, 'omitted an authored required claim'):
            gate.validate_raw_observations(result, {'cases': [case]}, by_key)

    def test_h18_label_alone_never_waives_positive_support_or_other_answer_kinds(self):
        case = {'questions': [{}, {}, {'expected_status': 'UNKNOWN'}]}
        answer = {'status': 'UNKNOWN', 'kind': 'subject', 'proofs': [], 'bindings': [], 'counterproofs': [{}]}
        for key, value in [('proofs', [{}]), ('bindings', [{}]), ('counterproofs', []), ('kind', 'polar'), ('status', 'SUPPORTED')]:
            altered = {**deepcopy(answer), key: value}
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'demonstrated WH UNKNOWN'):
                gate.validate_h18({}, {}, altered, case, {})


if __name__ == '__main__':
    unittest.main()
