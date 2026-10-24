#!/usr/bin/env python3
"""Preserve a successful full gate and independently finalize its raw streams.

This records existing observations, not a proof of linguistic completeness.
It fails on an incomplete gzip/JSONL stream even when a saved hash matches it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent


def record(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data),
            'sha256': sha256(data).hexdigest()}


def load(path):
    return json.loads(path.read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def output_inventory(folder):
    paths = sorted(path for path in folder.rglob('*') if path.is_file())
    require(not any(path.is_symlink() for path in paths), 'Unexpected symlink in evidence outputs')
    return {str(path.relative_to(folder)): record(path) for path in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    require(run.is_relative_to(ROOT / 'artifacts/local'), 'Expected a repository-local gate run')
    initial_outputs = output_inventory(run)
    finalizer_before = record(Path(__file__).resolve())
    execution = load(run / 'execution.json')
    require(execution['all_required_gates_passed'] is True and execution['exit_code'] == 0,
            'The full release gate did not pass')
    before, after = load(run / 'inputs_before.json'), load(run / 'inputs_after.json')
    require(before == after and execution['executable_inputs_unchanged'] is True,
            'Executable input bytes changed during the full gate')
    for item in after['files']:
        require(record(ROOT / item['path']) == item, 'Verified input changed after the gate: ' + item['path'])
    log = (run / 'make_check.log').read_bytes()
    require(sha256(log).hexdigest() == execution['log']['sha256'], 'Gate log changed')
    summaries = re.findall(r'Ran (\d+) tests? in ([0-9.]+)s\n\n([^\n]+)', log.decode())
    require(summaries and all(status == 'OK' for _, _, status in summaries),
            'Missing, failed, or skipped unittest summary')
    builds = re.findall(r'Build completed successfully \((\d+) jobs\)', log.decode())
    require(builds and int(builds[0]) == 100, 'Full Lean build receipt differs')
    raw_streams = []
    raw_paths = sorted(run.rglob('*.raw.jsonl.gz'))
    require(run / 'inflection-regression.raw.jsonl.gz' in raw_paths, 'Required inflection raw stream is missing')
    for path in raw_paths:
        compressed = path.read_bytes()
        raw_identity = {'path': str(path.relative_to(ROOT)), 'bytes': len(compressed),
                        'sha256': sha256(compressed).hexdigest()}
        require(raw_identity == initial_outputs[str(path.relative_to(run))], 'Raw bytes changed before validation')
        payload = gzip.decompress(compressed)
        require(payload.endswith(b'\n'), 'Raw stream lacks its final newline: ' + str(path))
        lines = payload.splitlines()
        require(lines and all(line for line in lines), 'Empty raw journal record')
        decoded = [json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
                   for line in lines]
        complete_inflection_inventory = None
        if path.name == 'inflection-regression.raw.jsonl.gz':
            inflection = load(path.with_name('inflection-regression.json'))
            same = lambda first, second: json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
            shapes = ({'law'}, {'model_profile', 'summary'}, {'case_id', 'report', 'verification'},
                      {'case_id', 'score'})
            require(all(type(row) is dict and set(row) in shapes for row in decoded),
                    'Unknown or overlapping inflection record shape')
            expected_ids = [case['id'] for case in inflection['cases']]
            require(len(expected_ids) == len(set(expected_ids)) == 74, 'Incomplete inflection case inventory')
            require([row['case_id'] for row in decoded if 'report' in row] == expected_ids,
                    'Raw inflection report inventory differs')
            require([row['case_id'] for row in decoded if 'score' in row] == expected_ids
                    and same([row['score'] for row in decoded if 'score' in row], inflection['cases']),
                    'Raw inflection scores differ')
            require(same([row['law'] for row in decoded if 'law' in row], inflection['conditional_sign_law'])
                    and len(inflection['conditional_sign_law']) == 60, 'Raw inflection law inventory differs')
            profiles = [row['model_profile'] for row in decoded if 'model_profile' in row]
            require(len(profiles) == len(set(profiles)) == len(inflection['model_profiles']) == 5
                    and set(profiles) == set(inflection['model_profiles']), 'Raw inflection model inventory differs')
            require(all(same(row['summary'], inflection['model_profiles'][row['model_profile']])
                        for row in decoded if 'model_profile' in row), 'Raw inflection model summary differs')
            require(len(decoded) == 213 and raw_identity['sha256'] == inflection['raw_log']['sha256'],
                    'Raw inflection count or digest differs')
            complete_inflection_inventory = {'laws': 60, 'profiles': 5, 'reports': 74, 'scores': 74}
        raw_streams.append({**raw_identity, 'decoded_bytes': len(payload),
                            'decoded_sha256': sha256(payload).hexdigest(),
                            'json_record_count': len(lines), 'complete_gzip_and_json_verified': True,
                            'exact_inflection_inventory': complete_inflection_inventory})
    scores = {}
    for suite, expected_passed in (('construction', 80), ('discourse', 63)):
        path = run / (suite + '-regression.json')
        result = load(path)
        require(result['measurement_valid'] is True and result['gate_pass'] is True
                and result['strict_pass'] is False and result['passed'] == expected_passed
                and result['total'] == 86 and result['false_accept_count'] == 0
                and result.get('gate_integrity_errors') == []
                and not result['execution_errors'] and not result['question_execution_errors'],
                'Unexpected final coverage measurement: ' + suite)
        raw_path = path.parent / result['raw_log']['filename']
        require(record(raw_path)['sha256'] == result['raw_log']['sha256'], 'Raw report hash mismatch')
        scores[suite] = {key: result[key] for key in ('passed', 'total', 'strict_pass', 'gate_pass',
                                                     'false_accept_count', 'measurement_valid')}
        scores[suite]['report'] = record(path)
        scores[suite]['failed_cases'] = [case['id'] for case in result['cases'] if not case['passed']]
    holdout = load(run / 'arabic-holdout.json')
    postreview = load(run / 'arabic-holdout-postreview/review.json')
    require(holdout['case_score'] == {'passed': 35, 'total': 36}
            and holdout['strict_pass'] is False and postreview['gate_pass'] is True
            and postreview['postreview_case_score'] == {'passed': 36, 'total': 36}
            and postreview['remaining_unsafe_acceptances'] == [], 'Holdout review differs')
    matches = sum(counts.get(expected, 0) for expected, counts in holdout['question_status_by_expectation'].items())
    require(matches == holdout['question_total'] == 63 and postreview['replayed_certificate_count'] == 103,
            'Holdout question or verification counts differ')
    axioms = load(run / 'axioms.json')
    require(axioms['ok'] is True and axioms['theorem_count'] == 990
            and axioms['project_axioms_allowed'] is False, 'Formal audit differs')
    archive = FOLDER / 'full_validation_reports_v2.zip'
    files = sorted(path for path in run.rglob('*') if path.is_file())
    require(not any(path.is_symlink() for path in files), 'Unexpected symlink in evidence outputs')
    require(output_inventory(run) == initial_outputs, 'Output inventory changed during finalization')
    members = []
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as saved:
        for path in files:
            name = str(path.relative_to(run))
            data = path.read_bytes()
            require(len(data) == initial_outputs[name]['bytes']
                    and sha256(data).hexdigest() == initial_outputs[name]['sha256'],
                    'Output bytes changed before archiving: ' + name)
            saved.writestr(name, data)
            members.append({'name': name, 'bytes': len(data), 'sha256': sha256(data).hexdigest()})
    with zipfile.ZipFile(archive) as saved:
        require(saved.namelist() == [item['name'] for item in members], 'Archive inventory differs')
        for item in members:
            data = saved.read(item['name'])
            require(len(data) == item['bytes'] and sha256(data).hexdigest() == item['sha256'],
                    'Archive member bytes differ: ' + item['name'])
    require(output_inventory(run) == initial_outputs, 'Output inventory changed while archiving')
    require(record(Path(__file__).resolve()) == finalizer_before, 'Finalizer source changed during execution')
    report = {
        'schema': 'nabt.arabic-coverage.full-validation.v2',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'validation_scope': 'Local make formal check plus complete raw-stream and archive finalization. Remote CI and publication are established separately.',
        'finalizer': finalizer_before, 'output_inventory_stable_during_finalization': True,
        'full_release_gate_pass': True, 'execution': execution,
        'primary_unittest_count': int(summaries[0][0]),
        'unittest_groups': [{'tests': int(count), 'seconds': float(seconds), 'status': status}
                            for count, seconds, status in summaries],
        'formal_build_jobs': int(builds[0]), 'formal_audited_declarations': axioms['theorem_count'],
        'observed_axioms': axioms['observed_axioms'], 'project_axioms_allowed': False,
        'runtime_freeze': record(FOLDER / 'code_freeze_v2.json'),
        'executable_inputs': {'count': before['file_count'], 'sha256': before['sha256'],
                              'unchanged_during_gate': True, 'rechecked_after_gate': True},
        'coverage': scores,
        'holdout': {'original_case_score': holdout['case_score'], 'original_strict_pass': False,
                    'postreview_case_score': postreview['postreview_case_score'],
                    'question_status_matches': matches, 'question_total': holdout['question_total'],
                    'verification_operations': postreview['replayed_certificate_count'],
                    'verification_operation_breakdown': {'documents': 36, 'answers': 63,
                                                        'changed_context_rejections': 4},
                    'same_frozen_material_after_development': True,
                    'corrected_false_alarm': 'H18/question:2:no_grounded_evidence',
                    'review': record(run / 'arabic-holdout-postreview/review.json')},
        'raw_stream_finalization': raw_streams,
        'archive': record(archive), 'archive_members': members,
        'historical_failed_full_gate': 'evidence/arabic_coverage/full_validation_attempt_v1.json',
        'all_Arabic_completeness': 'NOT_ESTABLISHED',
        'not_claimed': ['General Python/Lean refinement', 'Adequate formal reference for all Arabic',
                        'Complete conversion of the four classical books', 'General source-acquisition authentication',
                        'Independent observation of all external facts', 'A new blind test after development'],
    }
    output = FOLDER / 'full_validation_v2.json'
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'report': record(output), 'archive': record(archive),
                      'archive_entries': len(members), 'verified_raw_streams': len(raw_streams),
                      'primary_unittests': report['primary_unittest_count']}))


if __name__ == '__main__':
    main()
