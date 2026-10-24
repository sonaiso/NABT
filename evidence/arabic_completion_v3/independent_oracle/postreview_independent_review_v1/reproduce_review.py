#!/usr/bin/env python3
"""Independent, saved-observation-only review of the occurrence adapter erratum.

This script deliberately blocks production imports. It never calls a predictor
or replays runtime certificates. All certificates are the preserved first calls;
only independent validators and the explicitly versioned scorers are executed.
"""
import ast
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ORACLE = HERE.parent
ROOT = HERE.parents[3]
FIRST_RESULT = '3a8fe4d22da4ab2c0ab3e26060d5b1a9c3ba5c488b049363473f920f8a8a0159'
FIRST_RAW = 'd401000ab9334c094064d3845abd6df659cdd2db8268a249ea9b67e5699d5ac0'
POSTREVIEW_FREEZE = '069d998a8983210024ce5c9a37e6cd5de4604cd542616d9af9696bfb01ff986e'
AFFECTED = ['P01', 'P02', 'P03', 'P04', 'P05', 'P06']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def file_row(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data), 'sha256': sha256(data).hexdigest()}


class NoRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'nabt' or fullname.startswith('nabt.'):
            raise RuntimeError('Production import forbidden during saved-observation review: ' + fullname)
        return None


def load(file, name):
    spec = importlib.util.spec_from_file_location(name, ORACLE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def span_value(inputs, start, end):
    raw = inputs['text'].encode()
    return {'start': start, 'end': end, 'source_id': inputs['source_id'],
            'source_sha256': sha256(raw).hexdigest(), 'span_sha256': sha256(raw[start:end]).hexdigest()}


def independent_span(span, surface, inputs):
    raw = inputs['text'].encode()
    a, b = span['start'], span['end']
    require(type(a) is int and type(b) is int and 0 <= a < b <= len(raw), 'Independent span bounds')
    require(span['source_id'] == inputs['source_id'] and span['source_sha256'] == sha256(raw).hexdigest(),
            'Independent span source identity')
    require(raw[a:b].decode() == surface, 'Independent span surface')
    if 'span_sha256' in span:
        require(span['span_sha256'] == sha256(raw[a:b]).hexdigest(), 'Independent piece digest')
    return a, b


def connected(record):
    hits = [(o, r) for o in record['report']['occurrences'] for r in o['readings']
            if r.get('kind') == 'verb' and r.get('person_evidence', {}).get('attached_pronouns')]
    require(len(hits) == 1, 'Expected one saved connected candidate')
    return hits[0]


def independent_binding(record):
    report, inputs = record['report'], record['inputs']
    raw = inputs['text'].encode()
    require(report['source_text'] == inputs['text'] and report['source_id'] == inputs['source_id']
            and report['source_sha256'] == sha256(raw).hexdigest() and report['scope'] == inputs['scope'],
            'Document input binding')
    cursor = 0
    expected_occurrences = []
    for part in report['partition']:
        a, b = independent_span(part['span'], part['surface'], inputs)
        require(a == cursor, 'Full document partition gap or overlap')
        cursor = b
        if part['kind'] in ('written_run', 'quotation'):
            expected_occurrences.append((a, b))
    require(cursor == len(raw), 'Full document partition omits bytes')
    require([(o['span']['start'], o['span']['end']) for o in report['occurrences']] == expected_occurrences,
            'Complete occurrence inventory')
    occurrence, row = connected(record)
    same_id = [(o, r) for o in report['occurrences'] for r in o['readings'] if r['reading_id'] == row['reading_id']]
    require(len(same_id) == 1 and wire(same_id[0][1]) == wire(row), 'Unique exact reading binding')
    a, b = independent_span(occurrence['span'], occurrence['surface'], inputs)
    x, y = independent_span(row['stem_span'], row['stem_surface'], inputs)
    require(a <= x < y <= b, 'Stem containment')
    require(row['person_evidence']['surface'] == occurrence['surface'], 'Complete person surface')
    cursor = a
    for part in row['segmentation']['parts']:
        x, y = independent_span(part['span'], part['surface'], inputs)
        require(cursor == x, 'Complete token partition gap or overlap')
        cursor = y
    require(cursor == b and ''.join(p['surface'] for p in row['segmentation']['parts']) == occurrence['surface'],
            'Complete token partition omits bytes')
    require('identity' not in row, 'The documented schema difference no longer applies')
    require(not any(p.get('licensed') is True for p in row['person_evidence']['attached_pronouns']),
            'Saved candidate unexpectedly acquired host authority')
    return {'case_id': record['case_id'], 'reading_id': row['reading_id'], 'occurrence_span': [a, b],
            'exact_row_sha256': sha256(wire(row)).hexdigest(), 'identity_present': False,
            'unique_occurrence_row': True, 'complete_document_partition': True,
            'complete_token_partition': True, 'licensed': False}


def main():
    require(not (HERE / 'review.json').exists(), 'Refusing to overwrite an independent review')
    require(not any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules), 'Runtime already imported')
    sys.meta_path.insert(0, NoRuntime())
    P = load('postreview_v2.py', 'independent_postreview_review')
    E, S = P.E, P.S
    first_path = ORACLE / 'first_run_v1/result.json'
    raw_path = ORACLE / 'first_run_v1/raw.jsonl.gz'
    require(sha256(first_path.read_bytes()).hexdigest() == FIRST_RESULT and
            sha256(raw_path.read_bytes()).hexdigest() == FIRST_RAW, 'First evidence bytes changed')
    original = json.loads(first_path.read_bytes())
    freeze_path = ORACLE / 'postreview_freeze_v2.json'
    require(sha256(freeze_path.read_bytes()).hexdigest() == POSTREVIEW_FREEZE, 'Unreviewed postreview freeze')
    freeze = json.loads(freeze_path.read_bytes())
    require(P.current_new_inventory() == freeze['files'], 'Postreview code differs from its freeze')
    protected_paths = sorted({ROOT / item['path'] for item in freeze['files']} |
        {ROOT / item['path'] for item in original['runner']['files']} |
        {ROOT / item['path'] for item in original['snapshot_after']['files']} |
        {ORACLE / 'freeze.json', ORACLE / 'runner_freeze_v1.json', freeze_path, first_path, raw_path,
         first_path.parent / original['code_archive']['filename'],
         ORACLE / 'cases.json', ORACLE / 'contexts.json', ORACLE / 'lexical_profiles.json', Path(__file__)})
    before = [file_row(p) for p in protected_paths]
    original_checked, records, material, audits, current, runner, inventory = P.checked_inputs(first_path, raw_path)
    require(wire(original_checked) == wire(original), 'Original output changed during review')

    # Exercise only checkout metadata normalization; actual source bytes were
    # verified above. This is a controlled boundary test, not a CI invocation.
    portability_checks = []
    actual_snapshot = P.E.runtime_snapshot
    try:
        relocated = {**deepcopy(current), 'runtime_root': '/tmp/nabt-relocated-review-checkout'}
        P.E.runtime_snapshot = lambda *args, **kwargs: deepcopy(relocated)
        checked = P.checked_inputs(first_path, raw_path)
        require(checked[4] == relocated, 'A checkout-root-only relocation was rejected')
        portability_checks.append({'field': 'runtime_root', 'only_difference_accepted': True})
        for field in current:
            if field == 'runtime_root':
                continue
            changed = deepcopy(relocated)
            if type(changed[field]) is str:
                changed[field] += '__changed__'
            elif type(changed[field]) is int:
                changed[field] += 1
            elif type(changed[field]) is list:
                changed[field].append('unregistered-entry')
            else:
                raise ValueError('Unreviewed snapshot field type: ' + field)
            P.E.runtime_snapshot = lambda *args, **kwargs: deepcopy(changed)
            try:
                P.checked_inputs(first_path, raw_path)
            except ValueError as error:
                require('Current runtime/checkers differ' in str(error), 'Relocation control rejected for an unrelated reason')
                portability_checks.append({'field': field, 'non_root_change_rejected': True, 'reason': str(error)})
            else:
                raise ValueError('Relocation waiver ignored another field: ' + field)
        changed = {**deepcopy(relocated), 'runtime_file_count': float(current['runtime_file_count'])}
        require(changed == relocated and wire(changed) != wire(relocated), 'Snapshot type counterexample is not diagnostic')
        P.E.runtime_snapshot = lambda *args, **kwargs: deepcopy(changed)
        try:
            P.checked_inputs(first_path, raw_path)
        except ValueError as error:
            require('Current runtime/checkers differ' in str(error), 'Snapshot type check rejected for another reason')
            portability_checks.append({'field': 'runtime_file_count_type', 'integer_float_substitution_rejected': True})
        else:
            raise ValueError('Snapshot equality accepted an integer/float substitution')
    finally:
        P.E.runtime_snapshot = actual_snapshot

    def functions(path):
        return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    old_functions = functions(ORACLE / 'oracle_checks_v1.py')
    new_functions = functions(ORACLE / 'oracle_checks_v2.py')
    require(set(new_functions) - set(old_functions) == {'occurrence_for_row'} and
            set(old_functions) <= set(new_functions), 'Unexpected added or removed scorer functions')
    require([k for k in old_functions if old_functions[k] != new_functions[k]] == ['attached_host_evidence'],
            'Unrelated scorer function changed')
    raw_lines = [json.loads(line) for line in gzip.decompress(raw_path.read_bytes()).splitlines()]
    calls = [x for x in raw_lines if x['kind'] == 'public_api_call']
    case_by_id = {c['id']: c for c in material['cases']}
    def check_call_inputs(call, record, question=None, inquiry=False):
        expected = deepcopy(record['inputs'])
        if inquiry:
            expected.update(text=question, source_id='question')
        elif question is not None:
            expected['question'] = question
        expected['lexical_profile'] = record['profile']
        require(all(k in call['inputs'] and wire(call['inputs'][k]) == wire(v) for k, v in expected.items()),
                'Saved API call changed its declared input')
    bound_calls = 0
    for cid, record in records.items():
        for name, key, qi in [('read_discourse', 'report', None), ('verify_discourse', 'verification', None)]:
            found = [c for c in calls if c['case_id'] == cid and c['question_index'] is qi and c['name'] == name]
            require(len(found) == 1 and wire(found[0]['returned']) == wire(record[key]), 'Saved document call binding')
            check_call_inputs(found[0], record)
            bound_calls += 1
        for qi, question in enumerate(record['questions']):
            for name, key in [('ask_discourse', 'answer'), ('read_discourse', 'inquiry'),
                              ('verify_discourse', 'inquiry_verification'), ('verify_discourse_answer', 'verification')]:
                found = [c for c in calls if c['case_id'] == cid and c['question_index'] == qi and c['name'] == name]
                require(len(found) == 1 and wire(found[0]['returned']) == wire(question[key]), 'Saved question call binding')
                check_call_inputs(found[0], record, case_by_id[cid]['expected']['questions'][qi]['text'],
                                  inquiry=name in ('read_discourse', 'verify_discourse'))
                bound_calls += 1

    binding_checks = [independent_binding(records[cid]) for cid in AFFECTED]
    scores, changes = [], []
    for case, old in zip(material['cases'], original['cases']):
        require(case['id'] == old['id'], 'Original case order changed')
        record = records[case['id']]
        new = S.score_case(case, record, audits[record['profile']])
        require([c['check'] for c in new['checks']] == [c['check'] for c in old['checks']], 'Ordered check inventory changed')
        changed = [(a, b) for a, b in zip(old['checks'], new['checks']) if wire(a) != wire(b)]
        require([a['check'] for a, b in changed] == (['connected_partition_and_profiles'] if case['id'] in AFFECTED else []),
                'Unrelated exact check payload changed')
        for a, b in changed:
            require(not a['passed'] and b['passed'] and b['detail'] == {'examined': 1, 'licensed': 0, 'errors': []},
                    'Adapter correction invented licensed evidence')
            changes.append({'id': case['id'], 'before': a, 'after': b,
                            'case_pass_before': old['passed'], 'case_pass_after': new['passed']})
        keep = lambda value: {k: v for k, v in value.items() if k not in ('checks', 'passed', 'unsafe')}
        require(wire(keep(old)) == wire(keep(new)), 'Questions, provenance or other score fields changed')
        expected_unsafe = [x for x in old['unsafe'] if x != 'connected_partition_and_profiles'] if case['id'] in AFFECTED else old['unsafe']
        require(wire(new['unsafe']) == wire(expected_unsafe), 'Unrelated safety alarm changed')
        scores.append(new)
    require([n['id'] for o, n in zip(original['cases'], scores) if n['passed'] and not o['passed']] == ['P03'],
            'Unexpected whole-case success')
    require(not any(o['passed'] and not n['passed'] for o, n in zip(original['cases'], scores)), 'Case regression')

    mutation_checks = []
    def reject(name, operation, required_message=None):
        try:
            operation()
        except (ValueError, KeyError, TypeError, IndexError) as error:
            require(required_message is None or required_message in str(error), 'Rejected for an unrelated reason: ' + name)
            mutation_checks.append({'name': name, 'rejected': True, 'error_type': type(error).__name__, 'reason': str(error)})
        else:
            raise ValueError('Forged binding accepted: ' + name)
    def fresh(cid='P01'):
        record = deepcopy(records[cid]); occurrence, row = connected(record)
        return record, occurrence, row
    def bind(record, row):
        return S.occurrence_for_row(record['report'], row, record['inputs'])
    def check_parts(record):
        result = S.attached_host_evidence(record['report'], record['inputs'], audits[record['profile']])
        require(not result['errors'], '; '.join(e['message'] for e in result['errors']))

    for duplicate_occurrence in (True, False):
        record, occurrence, row = fresh()
        (record['report']['occurrences'] if duplicate_occurrence else occurrence['readings']).append(deepcopy(occurrence if duplicate_occurrence else row))
        reject('duplicate_occurrence' if duplicate_occurrence else 'duplicate_reading_entry', lambda: bind(record, row), 'exactly one')
    record, occurrence, row = fresh(); occurrence['readings'].remove(row)
    reject('missing_occurrence_no_span_fallback', lambda: bind(record, row), 'exactly one')
    record, occurrence, row = fresh('P04'); forged = deepcopy(row)
    forged['person_evidence']['person_profile']['person'] = True
    require(row == forged and wire(row) != wire(forged), 'The bool/int counterexample is not diagnostic')
    reject('same_id_row_bool_integer_substitution', lambda: bind(record, forged), 'exact reading')
    for field, value in [('source_id', 'foreign-source'), ('source_sha256', '0' * 64), ('span_sha256', '0' * 64), ('start', True)]:
        record, occurrence, row = fresh(); occurrence['span'][field] = value
        reject('occurrence_' + field, lambda: bind(record, row))
    record, occurrence, row = fresh(); foreign = record['report']['occurrences'][0]
    row['stem_span'], row['stem_surface'] = deepcopy(foreign['span']), foreign['surface']
    reject('valid_source_stem_outside_own_occurrence', lambda: bind(record, row), 'escapes')
    record, occurrence, row = fresh(); row['person_evidence']['surface'] = row['person_evidence']['host_form']
    reject('person_surface_omits_suffix', lambda: bind(record, row), 'complete observed token')
    for mode in ('gap', 'overlap', 'omitted'):
        record, occurrence, row = fresh(); parts = row['segmentation']['parts']
        if mode == 'omitted':
            parts.pop()
        else:
            a, b = parts[-1]['span']['start'] + (2 if mode == 'gap' else -2), parts[-1]['span']['end']
            parts[-1]['span'] = span_value(record['inputs'], a, b)
            parts[-1]['surface'] = record['inputs']['text'].encode()[a:b].decode()
        reject('token_partition_' + mode, lambda: check_parts(record), 'gap/overlap' if mode != 'omitted' else 'suffix bytes')
    for mode in ('document_partition_gap', 'occurrence_inventory_omission'):
        record, occurrence, row = fresh()
        record['report']['partition' if mode == 'document_partition_gap' else 'occurrences'].pop(0)
        record['report']['report_id'] = E.digest({k: v for k, v in record['report'].items() if k != 'report_id'})
        reject(mode, lambda: E.validate_report(record['report'], record['inputs'], audits[record['profile']]),
               'Partition has a gap/overlap' if mode == 'document_partition_gap' else 'Source occurrence inventory changed')

    mutation_log = []
    outcomes = P.M.run(records, audits, mutation_log.append)
    old_mutations = {x['id']: x for x in original['mutation_checks']}
    mutation_changes = [{'id': x['id'], 'before': old_mutations[x['id']]['outcome'], 'after': x['outcome']}
                        for x in outcomes if old_mutations[x['id']]['outcome'] != x['outcome']]
    require(mutation_changes == [{'id': 'V-P02', 'before': 'UNEXERCISED', 'after': 'PASS'}], 'Unrelated mutation outcome changed')
    require(E.runtime_snapshot(ROOT / 'evidence/arabic_completion_v3/code_freeze_v1.json', ROOT) == current,
            'Runtime/checkers changed during review')
    require(P.R.check_runner_freeze(ORACLE / 'runner_freeze_v1.json') == runner, 'Frozen runner changed')
    after = [file_row(p) for p in protected_paths]
    require(before == after, 'Protected evidence or code changed during review')
    require(not any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules), 'Production module imported')
    fixed = [x for x in scores if x['fixed_status_case']]
    summary = {'schema': 'nabt.oracle-occurrence-adapter-independent-review.v1',
        'reviewed_utc': datetime.now(timezone.utc).isoformat(), 'verdict': 'PASS_WITH_COVERAGE_LIMITATIONS',
        'basis': 'SAVED_FIRST_CALLS_ONLY_POSTREVIEW_NOT_BLIND', 'new_runtime_calls': 0,
        'production_imports_blocked': True, 'protected_inputs_before': before, 'protected_inputs_after': after,
        'protected_inputs_unchanged': True, 'first_result_sha256': FIRST_RESULT, 'first_raw_sha256': FIRST_RAW,
        'postreview_freeze_sha256': sha256(freeze_path.read_bytes()).hexdigest(),
        'checkout_portability_checks': portability_checks,
        'checkout_portability_scope': 'Simulated snapshot-metadata relocation only; not an actual fresh CI checkout.',
        'raw_inventory': inventory, 'saved_call_bindings_checked': bound_calls,
        'independent_occurrence_bindings': binding_checks, 'exact_check_changes': changes,
        'ordered_case_check_inventory_unchanged': True, 'all_other_check_payloads_unchanged': True,
        'fixed_cases_before': original['fixed_cases'],
        'fixed_cases_after': {'total': len(fixed), 'passed': sum(x['passed'] for x in fixed), 'failed': sum(not x['passed'] for x in fixed)},
        'newly_passed_case_ids': ['P03'], 'conditional_provenance_unchanged': original['conditional_provenance'],
        'questions_unchanged': original['questions'], 'cross_case_checks_unchanged': original['cross_case_checks'],
        'adversarial_adapter_checks': mutation_checks, 'predeclared_mutation_changes': mutation_changes,
        'predeclared_mutation_counts': dict(Counter(x['outcome'] for x in outcomes)),
        'predeclared_mutation_outcomes': outcomes,
        'remaining_case_failures': [{'id': s['id'], 'fixed_status_case': s['fixed_status_case'],
             'failed_checks': [c for c in s['checks'] if not c['passed']]} for s in scores if not s['passed']],
        'measurement_valid_after_adapter_review': not any(c['kind'] in ('integrity', 'execution') and not c['passed'] for s in scores for c in s['checks']),
        'strict_coverage_pass': False,
        'limitations': [
            'P03 is a correct abstention case; no positive attached-verb comprehension case becomes successful.',
            'All six attached candidates remain unlicensed; complete host/suffix profiles are not established.',
            'The legacy licensed-suffix check expects a standalone person token although raw QAC suffix features use PRON:3MS. This branch was not exercised or corrected.',
            'N06 remains unresolved independent review; neither conditional provenance probe is a fixed language-success denominator.',
            'Five predeclared mutations remain UNEXERCISED; absence of a licensed baseline is not a passing counterexample.',
            'Existing certificate replay results are preserved observations, not newly executed runtime checks.',
            'This authored finite directed set does not establish complete Arabic coverage or external-world truth.']}
    (HERE / 'review.json').write_bytes(json.dumps(summary, ensure_ascii=False, indent=2).encode() + b'\n')
    print(json.dumps({'review': str(HERE / 'review.json'), 'fixed_cases_after': summary['fixed_cases_after'],
        'adapter_rejections': len(mutation_checks), 'mutation_counts': summary['predeclared_mutation_counts'],
        'questions': summary['questions_unchanged'], 'new_runtime_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
