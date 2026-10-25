#!/usr/bin/env python3
"""Validate a new frozen implementation against unchanged, explicit evidence.

No production parser is imported here. Public calls and case records must be
identical to the first trace. The only expected trace changes are the already
preserved v2 scores and mutations; they are independently recomputed again.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib.util
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ORACLE = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


R = module('continuation_execution_v3', HERE / 'run_oracle_v6.py')
E, S = R.E, R.S
M = module('continuation_mutations_v2', ORACLE / 'oracle_mutations_v2.py')
FIRST_RESULT = '3a8fe4d22da4ab2c0ab3e26060d5b1a9c3ba5c488b049363473f920f8a8a0159'
FIRST_RAW = 'd401000ab9334c094064d3845abd6df659cdd2db8268a249ea9b67e5699d5ac0'
FIRST_CODE = '7789b7b6ba15c50b2d2e91a9ad08fdda43e4d40392d60e666727cae3b84d27c6'
REVIEW_RESULT = '1ca1469c18749b3ba7160c54029bfd449621ffdb97782a832325bdbf6a885080'
REVIEW_MUTATIONS = '7990001814d006e8af4bb00249ec932544c81b167d004c4459d5631f78ea36bf'
REVIEW_FREEZE = '069d998a8983210024ce5c9a37e6cd5de4604cd542616d9af9696bfb01ff986e'
SOURCE_MATERIAL = '4364eda40400336c3734b190183b9730dc437e0855df5fdd5a004586d3d1a844'


def pinned(path, checksum):
    data = path.read_bytes()
    E.require(sha256(data).hexdigest() == checksum, 'Pinned historical evidence changed: ' + str(path))
    return data


def canonical_records(data):
    E.require(data.endswith(b'\n'), 'Journal is truncated')
    values = []
    for line in data.splitlines(keepends=True):
        value = json.loads(line)
        E.require(line == R.dump(value) + b'\n', 'Journal record is not canonical')
        values.append(value)
    return values


def snapshot_equal(current, saved):
    if (type(current) is not dict or type(saved) is not dict or
            type(current.get('runtime_root')) is not str or type(saved.get('runtime_root')) is not str or
            not Path(current['runtime_root']).is_absolute() or not Path(saved['runtime_root']).is_absolute()):
        return False
    return E.wire(current) == E.wire({**saved, 'runtime_root': current['runtime_root']})


def historical_reference():
    """Use old evidence as a comparison, never repin it to the new runtime."""
    R.load_material()
    baseline = json.loads(pinned(ORACLE / 'first_run_v1/result.json', FIRST_RESULT))
    old = canonical_records(gzip.decompress(pinned(ORACLE / 'first_run_v1/raw.jsonl.gz', FIRST_RAW)))
    pinned(ORACLE / 'first_run_v1/result.code.tar.gz', FIRST_CODE)
    reviewed = json.loads(pinned(ORACLE / 'postreview_run_v2/review.json', REVIEW_RESULT))
    mutations = canonical_records(gzip.decompress(pinned(
        ORACLE / 'postreview_run_v2/mutations.jsonl.gz', REVIEW_MUTATIONS)))
    freeze = json.loads(pinned(ORACLE / 'postreview_freeze_v2.json', REVIEW_FREEZE))
    for row in freeze['files']:
        E.require(E.wire(R.file_row(R.ROOT / row['path'])) == E.wire(row),
                  'Historical v2 review/scorer file changed: ' + row['path'])
    E.require(reviewed['review_valid'] is True and reviewed['measurement_valid'] is True and
              reviewed['strict_pass'] is False and reviewed['new_runtime_calls'] == 0,
              'Preserved review does not have its declared limited authority')
    E.require(len(old) == 214 and len(mutations) == 18, 'Historical observation inventory changed')
    scores = {x['id']: x for x in reviewed['cases']}
    E.require(len(scores) == 24, 'Historical reviewed case inventory changed')
    expected, mutation_index = [], 0
    for row in old:
        if row['kind'] == 'case_observation':
            expected.append({**row, 'score': scores[row['case_id']]})
        elif row['kind'] == 'mutation_observation':
            replacement = mutations[mutation_index]
            E.require(replacement['kind'] == row['kind'] and
                      replacement['recipe']['id'] == row['recipe']['id'],
                      'Historical mutation order changed')
            expected.append(replacement)
            mutation_index += 1
        else:
            E.require(row['kind'] in ('public_api_call', 'cross_case_observations'),
                      'Unknown historical record kind')
            expected.append(row)
    E.require(mutation_index == 18, 'Historical mutation inventory incomplete')
    return baseline, reviewed, expected, mutations


def require_exact_trace(actual, expected):
    """No public field, authority, input, record order or result may be ignored."""
    E.require(len(actual) == len(expected), 'Continuation observation count changed')
    for index, (got, wanted) in enumerate(zip(actual, expected)):
        E.require(E.wire(got) == E.wire(wanted),
                  'Continuation trace differs at record %d (%s, case %s, call %s)' %
                  (index, wanted.get('kind'), wanted.get('case_id'), wanted.get('call_id')))


def checked_artifacts(result_path, raw_path):
    result = json.loads(result_path.read_text())
    runner = R.check_runner_freeze(HERE / 'runner_freeze_v6.json')
    current = E.runtime_snapshot(R.ROOT / 'evidence/arabic_completion_v6/code_freeze_v1.json', R.ROOT)
    E.require(result['runtime_freeze_sha256'] == R.RUNTIME_SHA and
              result['material_freeze_sha256'] == R.MATERIAL_SHA and
              E.wire(result['runner']) == E.wire(runner), 'Continuation runtime/material/dependency pin mismatch')
    E.require(snapshot_equal(current, result['snapshot_after']), 'Measured runtime or checker bytes changed')
    material, _, _, _ = R.load_material()
    by_path = {row['path']: row for row in current['files']}
    for row in runner['files']:
        by_path.setdefault(row['path'], row)
    for path in (HERE / 'runner_freeze_v6.json', R.ROOT / current['runtime_freeze']):
        row = R.file_row(path)
        by_path.setdefault(row['path'], row)
    for name in ['freeze.json', *[row['path'] for row in material['files']]]:
        row = R.file_row(ORACLE / name)
        by_path.setdefault(row['path'], row)
    expected_snapshot = {**current, 'files': list(by_path.values())}
    expected_snapshot['measured_snapshot_sha256'] = E.digest(expected_snapshot['files'])
    E.require(snapshot_equal(expected_snapshot, result['snapshot']), 'Measured archive inventory changed')
    archive_name = result['code_archive']['filename']
    E.require(type(archive_name) is str and Path(archive_name).name == archive_name,
              'Unsafe measured archive filename')
    archive = result_path.parent / archive_name
    E.require(sha256(archive.read_bytes()).hexdigest() == result['code_archive']['sha256'], 'Measured archive changed')
    with tarfile.open(archive, 'r:gz') as saved:
        members = saved.getmembers()
        E.require(len(members) == len(by_path) and {m.name for m in members} == set(by_path)
                  and all(m.isfile() for m in members), 'Measured archive members changed')
        for member in members:
            data, row = saved.extractfile(member).read(), by_path[member.name]
            E.require(len(data) == row['bytes'] and sha256(data).hexdigest() == row['sha256'],
                      'Measured archive member changed: ' + member.name)
    data = gzip.decompress(raw_path.read_bytes())
    values = canonical_records(data)
    inventory = [{'index': i, 'bytes': len(R.dump(row) + b'\n'),
                  'sha256': sha256(R.dump(row) + b'\n').hexdigest(), 'kind': row['kind'],
                  'case_id': row.get('case_id'), 'call_id': row.get('call_id')}
                 for i, row in enumerate(values)]
    E.require(E.wire(inventory) == E.wire(result['raw_journal']['inventory']), 'Typed raw record inventory changed')
    checked = R.finish_journal(raw_path, inventory)
    E.require(E.wire(checked) == E.wire(result['raw_journal']), 'Raw journal bytes or location changed')
    E.require(result['runtime_unchanged'] is True and result['runner_and_helpers_unchanged'] is True,
              'Measured code changed during execution')
    return result, values, current, runner, checked


def review(result_path, raw_path, output_dir):
    E.require(not output_dir.exists(), 'Refusing to replace a continuation review')
    baseline, reference, expected, expected_mutations = historical_reference()
    result, values, current, runner, inventory = checked_artifacts(result_path, raw_path)
    E.require([(x['kind'], x.get('case_id'), x.get('name')) for x in values] ==
              [(x['kind'], x.get('case_id'), x.get('name')) for x in expected],
              'Public operation and case inventory changed')
    E.require(set(result) == set(baseline), 'Continuation result adds or omits fields')
    E.require(result['schema'] == R.VERSION and result['scorer'] == S.VERSION and
              result['statistical_blind_sample_claimed'] is False and result['strict_only'] is True and
              result['regression_waiver_used'] is False, 'Continuation changed its evaluation contract')
    for key in ('scope', 'public_api_calls'):
        E.require(E.wire(result[key]) == E.wire(baseline[key]), 'Continuation metadata changed: ' + key)
    calls = [row for row in values if row['kind'] == 'public_api_call']
    E.require([row['call_id'] for row in calls] == list(range(1, 172)) and
              all(type(row['call_id']) is int and 'error' not in row for row in calls),
              'Public call inventory incomplete or errored')
    E.require(Counter(row['name'] for row in calls) == {
        'learn_qac_lexicon': 3, 'read_discourse': 53, 'verify_discourse': 53, 'ask_discourse': 29,
        'verify_discourse_answer': 29, 'verify_discourse_changed_speaker': 2,
        'verify_answer_changed_speaker': 2}, 'Public call types changed')
    for call in calls:
        if call['name'].startswith('verify_'):
            E.require(call['returned'].get('valid') is ('changed_speaker' not in call['name']),
                      'Production replay does not have its declared outcome')
    _, material, contexts, profiles = R.load_material()
    observations = [row for row in values if row['kind'] == 'case_observation']
    records = {row['case_id']: row['record'] for row in observations}
    E.require([row['case_id'] for row in observations] == [c['id'] for c in material['cases']] and len(records) == 24,
              'Case inventory changed')
    learning_calls = [call for call in calls if call['name'] == 'learn_qac_lexicon']
    E.require(len(learning_calls) == len(profiles), 'Learning call inventory changed')
    for actual, key in zip(learning_calls, profiles):
        raw = (ORACLE / profiles[key]['file']).read_bytes()
        source_id = 'independent_oracle_lexical_' + key
        inputs = {'source_id': source_id, 'raw_hex': raw.hex(),
                  'raw_sha256': sha256(raw).hexdigest(), 'excluded_verses': []}
        E.require(set(actual) == {'kind', 'call_id', 'name', 'case_id', 'question_index', 'inputs', 'returned'} and
                  actual['case_id'] is None and actual['question_index'] is None and
                  E.wire(actual['inputs']) == E.wire(inputs) and
                  E.wire(actual['returned']['source']) == E.wire({
                      'id': source_id, 'byte_length': len(raw), 'sha256': sha256(raw).hexdigest()}),
                  'Learning call inputs or returned source differ from frozen material')
    model_summaries = {call['inputs']['source_id'].removeprefix('independent_oracle_lexical_'): call['returned']
                       for call in calls if call['name'] == 'learn_qac_lexicon'}
    observation_calls = []
    for case, observation in zip(material['cases'], observations):
        record = observation['record']
        inputs = {k: case['input'][k] for k in ('text', 'source_id', 'scope')}
        inputs['context'] = contexts[case['input']['context_id']]
        public = {**inputs, 'lexical_profile': case['input']['lexical_profile'],
                  'model_summary': model_summaries[case['input']['lexical_profile']]}
        report = record['report']
        expected_calls = [
            ('read_discourse', None, public, report),
            ('verify_discourse', None, {**public, 'certificate_report_id': report['report_id']},
             record['verification']),
        ]
        E.require(len(record['questions']) == len(case['expected']['questions']),
                  'Question observation count changed')
        for qi, (wanted, entry) in enumerate(zip(case['expected']['questions'], record['questions'])):
            question = wanted['text']
            answer, inquiry = entry['answer'], entry['inquiry']
            expected_calls.extend([
                ('ask_discourse', qi, {**public, 'question': question}, answer),
                ('read_discourse', qi, {**public, 'text': question, 'source_id': 'question'}, inquiry),
                ('verify_discourse', qi,
                 {**public, 'text': question, 'source_id': 'question',
                  'certificate_report_id': inquiry['report_id']}, entry['inquiry_verification']),
                ('verify_discourse_answer', qi,
                 {**public, 'question': question, 'certificate_answer_id': answer['answer_id']},
                 entry['verification']),
            ])
        observation_calls.extend((case['id'], call) for call in expected_calls)
    actual_observation_calls = [call for call in calls if call['name'] in (
        'read_discourse', 'verify_discourse', 'ask_discourse', 'verify_discourse_answer')]
    E.require(len(actual_observation_calls) == len(observation_calls),
              'Public observation calls do not match scored records')
    for actual, (case_id, (name, question_index, inputs, returned)) in zip(
            actual_observation_calls, observation_calls):
        E.require(set(actual) == {'kind', 'call_id', 'name', 'case_id', 'question_index', 'inputs', 'returned'} and
                  actual['kind'] == 'public_api_call' and type(actual['call_id']) is int and
                  actual['name'] == name and actual['case_id'] == case_id and
                  E.wire(actual['question_index']) == E.wire(question_index) and
                  E.wire(actual['inputs']) == E.wire(inputs) and
                  E.wire(actual['returned']) == E.wire(returned),
                  'Public call input/output differs from its scored observation')
    audits = {key: E.SourceAudit((ORACLE / p['file']).read_bytes(), source_id='independent_oracle_lexical_' + key)
              for key, p in profiles.items()}
    scores = []
    for case, observation in zip(material['cases'], observations):
        record = observation['record']
        wanted_input = {k: case['input'][k] for k in ('text', 'source_id', 'scope')}
        wanted_input['context'] = contexts[case['input']['context_id']]
        E.require(E.wire(record['inputs']) == E.wire(wanted_input) and
                  record['profile'] == case['input']['lexical_profile'], 'Frozen case input changed')
        score = S.score_case(case, record, audits[record['profile']])
        E.require(E.wire(score) == E.wire(observation['score']), 'Fresh independent case validation changed')
        scores.append(score)
    mutation_records = []
    mutation_outcomes = M.run(records, audits, mutation_records.append)
    E.require(E.wire(mutation_outcomes) == E.wire(reference['mutation_checks']), 'Mutation outcome regressed or an unexercised control was relabelled')
    E.require(E.wire(mutation_outcomes) == E.wire(result['mutation_checks']), 'Fresh mutation outcomes changed')
    E.require(E.wire(scores) == E.wire(result['cases']), 'Result scores differ from freshly validated records')
    cross_rows = [row for row in values if row['kind'] == 'cross_case_observations']
    E.require(len(cross_rows) == 1, 'Cross-case observation inventory changed')
    cross = cross_rows[0]
    E.require(set(cross) == {'kind', 'case_id', 'checks', 'changed_speaker'} and
              cross['case_id'] is None and set(cross['changed_speaker']) == {'P04', 'P05'},
              'Cross-case observation fields changed')
    changed_calls = [call for call in calls if call['name'] in (
        'verify_discourse_changed_speaker', 'verify_answer_changed_speaker')]
    E.require(len(changed_calls) == 4, 'Changed-speaker call inventory changed')
    by_case = {case['id']: case for case in material['cases']}
    for index, (case_id, other_id) in enumerate((('P04', 'P05'), ('P05', 'P04'))):
        record = records[case_id]
        public = {**record['inputs'], 'context': records[other_id]['inputs']['context']}
        replay = cross['changed_speaker'][case_id]
        E.require(set(replay) == {'report', 'answer'}, 'Changed-speaker replay fields changed')
        wanted = [
            ('verify_discourse_changed_speaker',
             {**public, 'certificate_report_id': record['report']['report_id']}, replay['report']),
            ('verify_answer_changed_speaker',
             {**public, 'question': by_case[case_id]['expected']['questions'][0]['text'],
              'certificate_answer_id': record['questions'][0]['answer']['answer_id']}, replay['answer']),
        ]
        for actual, (name, inputs, returned) in zip(changed_calls[index * 2:index * 2 + 2], wanted):
            E.require(set(actual) == {'kind', 'call_id', 'name', 'case_id', 'question_index', 'inputs', 'returned'} and
                      actual['case_id'] == case_id and actual['question_index'] is None and actual['name'] == name and
                      E.wire(actual['inputs']) == E.wire(inputs) and E.wire(actual['returned']) == E.wire(returned),
                      'Changed-speaker public call differs from its observation')
    by_score = {score['id']: score for score in scores}
    actor = records['P04']['inputs']['text'] == records['P05']['inputs']['text']
    for case_id, wanted_actor in (('P04', 'malik'), ('P05', 'hind')):
        actor = actor and any(claim['predicate_kind'] == 'event' and claim['predicate'] == 'أَكْرَمَ' and
                              claim['args'] == [wanted_actor, 'khalid'] for claim in records[case_id]['report']['claims'])
        actor = actor and all(cross['changed_speaker'][case_id][name]['valid'] is False
                              for name in ('report', 'answer'))
    cross_checks = [
        {'id': 'X01', 'passed': all(by_score[key]['passed'] is True for key in ('G01', 'G05', 'G06'))},
        {'id': 'X02', 'passed': bool(by_score['N01']['passed'] is True and
          by_score['N03']['provenance_outcome'] in ('correct_abstention', 'checked_derivation'))},
        {'id': 'X03', 'passed': bool(actor)},
    ]
    E.require(E.wire(cross_checks) == E.wire(cross['checks']) and
              E.wire(cross_checks) == E.wire(result['cross_case_checks']),
              'Cross-case summary differs from validated observations')
    E.require(result['questions']['independently_validated'] >= reference['questions']['independently_validated'], 'Question evidence regressed')
    E.require(len(result['cross_case_checks']) == len(reference['cross_case_checks']) and all(
        new['id'] == old['id'] and (not old['passed'] or new['passed'])
        for new, old in zip(result['cross_case_checks'], reference['cross_case_checks'])), 'Cross-case authority regressed')
    for key in ('unsafe_check_failures', 'independent_integrity_failures', 'execution_errors', 'scoring_errors'):
        E.require(result[key] == [], 'New integrity/error/extra-authority failure: ' + key)
    fixed = [case for case in scores if case['fixed_status_case']]
    probes = [case for case in scores if not case['fixed_status_case']]
    fixed_summary = {'total': len(fixed), 'passed': sum(case['passed'] is True for case in fixed),
                     'failed': sum(case['passed'] is False for case in fixed)}
    provenance_summary = {'total': len(probes),
                          'outcomes': {case['id']: case['provenance_outcome'] for case in probes},
                          'not_counted_as_language_coverage': True}
    question_results = [question for case in scores for question in case['questions']]
    E.require(all(type(question['status_match']) is bool and
                  type(question['independently_validated']) is bool for question in question_results),
              'Question outcomes are not typed booleans')
    question_summary = {'total': sum(len(case['expected']['questions']) for case in material['cases']),
                        'observed': len(question_results),
                        'status_matches': sum(question['status_match'] is True for question in question_results),
                        'independently_validated': sum(
                            question['independently_validated'] is True for question in question_results)}
    E.require(E.wire(result['fixed_cases']) == E.wire(fixed_summary) and
              E.wire(result['questions']) == E.wire(question_summary) and
              E.wire(result['conditional_provenance']) == E.wire(provenance_summary),
              'Fixed-case, question, or provenance summary differs from validated records')
    measurement_valid = not (result['execution_errors'] or result['scoring_errors'] or
                             result['independent_integrity_failures'] or
                             any(mutation['outcome'] == 'ERROR' for mutation in mutation_outcomes))
    E.require(type(result['measurement_valid']) is bool and result['measurement_valid'] is measurement_valid,
              'Measurement validity differs from validated records')
    strict_pass = bool(measurement_valid and result['runtime_unchanged'] is True and
                       result['runner_and_helpers_unchanged'] is True and
                       all(case['passed'] is True for case in scores) and
                       all(check['passed'] is True for check in result['cross_case_checks']) and
                       all(mutation['outcome'] == 'PASS' for mutation in mutation_outcomes))
    E.require(type(result['strict_pass']) is bool and result['strict_pass'] is strict_pass,
              'Partial result was converted to full success or invalid measurement')
    categories = {category: {'total': sum(c['category'] == category for c in scores),
                             'passed': sum(c['category'] == category and c['passed'] for c in scores)}
                  for category in sorted({c['category'] for c in scores})}
    E.require(E.wire(result['categories']) == E.wire(categories), 'Case categories changed')
    residuals = {c['id']: sorted(x['check'] for x in c['checks'] if not x['passed']) for c in scores}
    E.require(set(residuals) == set(reference['regression_gate']['actual_failure_inventory']) and all(
        set(checks) <= set(reference['regression_gate']['actual_failure_inventory'][cid]) for cid, checks in residuals.items()),
        'New case failures were introduced')
    E.require(E.wire(R.check_runner_freeze(HERE / 'runner_freeze_v6.json')) == E.wire(runner) and
              E.wire(E.runtime_snapshot(R.ROOT / 'evidence/arabic_completion_v6/code_freeze_v1.json', R.ROOT)) == E.wire(current),
              'Runtime/checker changed during independent review')
    review = {'schema': 'nabt.completion-continuation-review.v6.review2',
              'reviewed_utc': datetime.now(timezone.utc).isoformat(),
              'runtime_freeze_sha256': R.RUNTIME_SHA, 'material_freeze_sha256': R.MATERIAL_SHA,
              'dependency_freeze_sha256': runner['sha256'], 'historical_material_unchanged': True,
              'historical_first_result_sha256': FIRST_RESULT, 'historical_review_result_sha256': REVIEW_RESULT,
              'public_api_calls': 171, 'new_runtime_calls_in_review': 0,
              'exact_historical_public_calls_and_case_records': False,
              'only_record_changes_are_previously_preserved_v2_scores_and_mutations': False,
              'expected_canonical_trace_sha256': sha256(b''.join(R.dump(x) + b'\n' for x in expected)).hexdigest(),
              'raw_journal': inventory, 'fixed_cases': result['fixed_cases'], 'questions': result['questions'],
              'conditional_provenance': result['conditional_provenance'], 'mutation_checks': mutation_outcomes,
              'residuals': residuals, 'measurement_valid': measurement_valid, 'review_valid': True,
              'unsafe_check_failures': [], 'independent_integrity_failures': [], 'execution_errors': [],
              'scoring_errors': [], 'runtime_unchanged': True, 'dependencies_unchanged': True,
              'strict_pass': strict_pass, 'regression_gate_pass': True,
              'scope': 'Same 24 authored inputs and retained partial result under a separately frozen classical-source runtime. No new blind experiment or universal completeness claim.'}
    output_dir.mkdir(parents=True)
    (output_dir / 'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
    return review
