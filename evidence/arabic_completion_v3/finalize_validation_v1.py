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
import importlib.util
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
RUNTIME_SHA256 = 'eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089'
RUNTIME_SNAPSHOT_SHA256 = 'fb14e51c7f7d751b13307ecf65573c1863c7f579252aa402231586aeda11412f'
RUNTIME_ARCHIVE_SHA256 = '8576765bdd5b9dbb93db76ec11b485634fa2f34691113a45d59dbf49238c0c87'
# Reviewed exact residual signatures; caller-supplied policy bytes grant no authority.
POLICY_SHA256 = '0bec1f1876a68f4a97e457e5b63b234597eb146510bd32fbf14bf3f270011e29'
THEOREM_COUNT = 1011
HOLDOUT_MATERIAL_SHA256 = '127a5870fcbc8f8823b95f2a9f452cf4cd87de22fcfc62b271efd32bc684c106'


def record(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data),
            'sha256': sha256(data).hexdigest()}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def parse(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'Duplicate JSON key: ' + key)
            value[key] = item
        return value

    def constant(value):
        raise ValueError('Non-JSON constant: ' + value)

    return json.loads(raw, object_pairs_hook=unique, parse_constant=constant)


def load(path):
    return parse(path.read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(left, right):
    return wire(left) == wire(right)


def repository_file(name):
    require(type(name) is str and name and not Path(name).is_absolute(), 'Expected repository-relative file')
    path = ROOT / name
    require(path.resolve().is_relative_to(ROOT) and not path.is_symlink(), 'Unsafe evidence file path')
    return path


def checked_identity(item):
    require(type(item) is dict and set(item) == {'path', 'bytes', 'sha256'}
            and type(item['bytes']) is int and item['bytes'] >= 0,
            'Malformed file identity')
    path = repository_file(item['path'])
    require(record(path) == item, 'Recorded file identity differs: ' + item['path'])
    return path


def checked_inventory(value):
    require(type(value) is dict and set(value) == {'files', 'file_count', 'sha256'},
            'Unexpected executable input inventory schema')
    rows = value['files']
    require(type(rows) is list and type(value['file_count']) is int
            and value['file_count'] == len(rows) and value['sha256'] == sha256(wire(rows)).hexdigest(),
            'Executable inventory count or digest differs')
    names = [row['path'] for row in rows]
    # The gate runner orders pathlib paths by components, not raw slash strings.
    require(names == sorted(names, key=Path) and len(names) == len(set(names)),
            'Executable input inventory is not unique and ordered')
    for row in rows:
        checked_identity(row)
    return {row['path']: row for row in rows}


def reviewed_policy(input_index):
    require(re.fullmatch('[0-9a-f]{64}', POLICY_SHA256) is not None,
            'Reviewed regression policy is not yet pinned in this finalizer')
    policy_path, runtime_path = FOLDER / 'regression_policy_v1.json', FOLDER / 'code_freeze_v1.json'
    require(record(policy_path)['sha256'] == POLICY_SHA256, 'Reviewed regression policy bytes changed')
    require(record(runtime_path)['sha256'] == RUNTIME_SHA256, 'Approved runtime freeze bytes changed')
    policy, runtime = load(policy_path), load(runtime_path)
    require(runtime['snapshot_sha256'] == RUNTIME_SNAPSHOT_SHA256
            and runtime['archive_sha256'] == RUNTIME_ARCHIVE_SHA256
            and len(runtime['files']) == 80
            and sha256(wire(runtime['files'])).hexdigest() == RUNTIME_SNAPSHOT_SHA256,
            'Approved runtime manifest contents differ')
    archive = FOLDER / runtime['archive_filename']
    require(archive.name == 'code_freeze_v1.tar.gz' and archive.parent == FOLDER
            and record(archive)['sha256'] == RUNTIME_ARCHIVE_SHA256, 'Approved runtime archive differs')
    for row in runtime['files']:
        checked_identity(row)
        require(input_index.get(row['path']) == row, 'Runtime file absent from complete gate inventory')
    for path in (policy_path, runtime_path, archive):
        item = record(path)
        require(input_index.get(item['path']) == item, 'Policy/runtime identity absent from complete gate inventory')
    require(policy['schema'] == 'nabt.arabic-completion.regression-policy.v1'
            and policy['runtime_freeze_sha256'] == RUNTIME_SHA256
            and policy['runtime_snapshot_sha256'] == RUNTIME_SNAPSHOT_SHA256
            and type(policy['runtime_file_count']) is int and policy['runtime_file_count'] == 80
            and set(policy['suites']) == {'construction', 'discourse'}, 'Policy is bound to another runtime or domain')
    for suite in policy['suites'].values():
        path = repository_file(suite['strict_measurement'])
        item = record(path)
        require(item['sha256'] == suite['strict_measurement_sha256']
                and input_index.get(item['path']) == item, 'Unbound strict policy measurement')
    return policy, runtime


def check_coverage(suite, result, policy, *, gate):
    """Recompute the complete reviewed score and exact remaining failures."""
    expected = policy['suites'][suite]
    require(result['measurement_valid'] is True and result['false_accept_count'] == 0
            and type(result['false_accept_count']) is int
            and type(result['false_accept_case_count']) is int and result['false_accept_case_count'] == 0
            and result['execution_errors'] == [] and result['question_execution_errors'] == [],
            'Invalid or unsafe coverage measurement: ' + suite)
    if suite == 'construction':
        require(result['finalization_errors'] == [], 'Construction finalization errors remain')
    for name in ('runtime_freeze_sha256', 'runtime_snapshot_sha256', 'runtime_file_count'):
        require(same(result['snapshot'][name], policy[name]), 'Coverage runtime identity differs: ' + name)
    for name in ('gold_freeze_sha256', 'source_sha256'):
        require(result[name] == expected[name], 'Coverage source/gold identity differs: ' + name)
    cases, references = result['cases'], expected['cases']
    ids = [case['id'] for case in cases]
    require(ids == [case['id'] for case in references] and len(ids) == len(set(ids))
            and type(result['total']) is int and result['total'] == expected['total'] == len(ids),
            'Complete ordered coverage case inventory differs')
    question_count, passed = 0, 0
    for case, reference in zip(cases, references):
        checks, failures = case['checks'], case['failures']
        require([check['check'] for check in checks] == reference['checks']
                and all(type(check['passed']) is bool for check in checks), 'Coverage check inventory differs')
        failed = [check for check in checks if check['passed'] is False]
        require([failure['check'] for failure in failures] == [check['check'] for check in failed]
                and same(failures, reference['allowed_failures']), 'Coverage failure payload is new or omitted')
        if suite == 'construction':
            require(same(failed, failures), 'Construction failures contradict their checks')
        require(type(case['passed']) is bool and case['passed'] == (not failed)
                and case['false_accepts'] == [], 'Coverage case status is inconsistent or unsafe')
        passed += case['passed'] is True
        question_count += sum(check['check'].startswith('question:') for check in checks)
    require(type(result['passed']) is int and result['passed'] == passed == expected['observed_passed']
            and question_count == expected['question_total'], 'Coverage score or question denominator differs')
    require(type(result['strict_pass']) is bool and result['strict_pass'] == (passed == len(ids)),
            'Strict coverage flag contradicts complete case inventory')
    if gate:
        require(result['gate_pass'] is True and result.get('gate_integrity_errors') == []
                and result.get('unexpected_failures') == []
                and result['documented_boundary_inventory_sha256'] == POLICY_SHA256
                and result['documented_boundary_runtime_sha256'] == RUNTIME_SHA256,
                'Coverage gate is not bound to the reviewed policy/runtime')
    return {'passed': passed, 'total': len(ids), 'strict_pass': result['strict_pass'],
            'gate_pass': result.get('gate_pass'), 'measurement_valid': True, 'false_accept_count': 0,
            'failed_cases': [case['id'] for case in cases if not case['passed']]}


def decode_journal(compressed, label):
    payload = gzip.decompress(compressed)
    require(payload.endswith(b'\n'), 'Raw stream lacks its final newline: ' + label)
    lines = payload.splitlines()
    require(lines and all(line for line in lines), 'Empty raw journal record: ' + label)
    decoded = [parse(line) for line in lines]
    return payload, lines, decoded


def check_formal_audit(axioms, audit_log, names):
    require(axioms['ok'] is True and type(axioms['theorem_count']) is int
            and axioms['theorem_count'] == len(names) == THEOREM_COUNT
            and axioms['project_axioms_allowed'] is False
            and axioms['all_nabt_declarations_scanned'] is True, 'Formal audit status or declaration count differs')
    entries = re.findall(r"NABT_THEOREM (Nabt\.[\w.']+) AXIOMS \[([^\]]*)\]", audit_log)
    require([name for name, _ in entries] == names
            and f'NABT_THEOREM_COUNT {THEOREM_COUNT}' in audit_log
            and 'NABT_AUDIT_OK' in audit_log, 'Compiled audit log omits or duplicates registered theorems')
    theorem_axioms = {name: sorted(a.strip() for a in raw.split(',') if a.strip()) for name, raw in entries}
    observed = sorted(set().union(*(set(values) for values in theorem_axioms.values())))
    require(same(theorem_axioms, axioms['theorem_axioms'])
            and same(observed, axioms['observed_axioms'])
            and set(observed) <= {'Classical.choice', 'Quot.sound', 'propext'},
            'Formal audit summary differs from its raw compiled declarations')


def check_inna_transport(run, input_index):
    directory = run / 'arabic-inna-fragment'
    report = load(directory / 'report.json')
    require(report['schema'] == 'nabt.inna-fragment-transport-check.v1'
            and report['ok'] is True and type(report['case_count']) is int and report['case_count'] == 32
            and type(report['returncode']) is int and report['returncode'] == 0 and report['error'] is None,
            'Inna transport did not pass all 32 authored wire cases')
    require(report['program_and_inputs_unchanged'] is True
            and same(report['files_before'], report['files_after']), 'Inna executable/input inventory changed')
    require(report['world_truth'] == 'NOT_ESTABLISHED' and all(report[key] is False for key in (
            'compiler_correctness_proved', 'lexical_acquisition_established', 'lexicon_exhaustiveness_established',
            'independent_linguistic_holdout', 'all_arabic_completeness_established', 'ledger_created_by_this_execution')),
            'Inna transport has escalated its evidence authority')
    tool = ROOT / 'tools/check_arabic_inna_fragment.py'
    require(input_index.get(record(tool)['path']) == record(tool), 'Inna checker was not captured by the full gate')
    spec = importlib.util.spec_from_file_location('nabt_finalization_inna_transport_checker', tool)
    checker = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = checker
    spec.loader.exec_module(checker)
    material, frozen = checker.frozen_material()
    cases = checker.make_cases(material)
    require(report['law_id'] == checker.LAW and report['source_status'] == material['source_status'],
            'Inna law/source authority differs')
    require(report['frozen_material'] == record(ROOT / checker.MATERIAL_DIRECTORY / 'freeze.json'),
            'Inna material freeze differs')
    expected_paths = {str((ROOT / p).relative_to(ROOT)) for p in checker.PROVENANCE_PATHS}
    expected_paths |= {'tests/test_arabic_inna_fragment_probe.py',
                       'formal/.lake/build/bin/arabicInnaFragmentProbe'}
    rows = report['files_before']
    require(len(rows) == len(expected_paths) and {row['path'] for row in rows} == expected_paths,
            'Inna program/source/checker inventory is incomplete or duplicated')
    program_name = 'formal/.lake/build/bin/arabicInnaFragmentProbe'
    for row in rows:
        path = checked_identity(row)
        if row['path'] != program_name:
            require(input_index.get(row['path']) == row, 'Inna input changed outside its shorter execution interval')
    require(report['command'] == [str(ROOT / program_name)], 'A different program produced the Inna receipt')
    artifacts = report['artifacts']
    expected_names = ('lexical_material.json', 'expectations.json', 'requests.jsonl', 'responses.jsonl', 'stderr.bin')
    require(artifacts == [record(directory / name) for name in expected_names], 'Inna artifact hashes differ')
    for name in ('lexical_material.json', 'expectations.json', 'requests.jsonl'):
        require((directory / name).read_bytes() == frozen[name], 'Inna material differs from the reviewed fixture')
    require((directory / 'requests.jsonl').read_bytes() == checker.request_stream(cases), 'Inna request interpretation differs')
    checked = checker.check_wire(cases, (directory / 'responses.jsonl').read_bytes(),
                                 (directory / 'stderr.bin').read_bytes(), report['returncode'])
    require(len(checked) == 32 and same(checked, report['checks']), 'Inna wire results do not support the saved receipt')
    return {'report': record(directory / 'report.json'), 'case_count': 32, 'checked_cases': len(checked),
            'actual_program': next(row for row in rows if row['path'] == program_name),
            'request': record(directory / 'requests.jsonl'), 'response': record(directory / 'responses.jsonl'),
            'full_wire_rechecked': True, 'program_and_inputs_unchanged': True,
            'authority': 'CONDITIONAL_ON_SUPPLIED_LEXICAL_PREMISES',
            'source_acquisition_established': False, 'lexicon_exhaustiveness_established': False,
            'independent_linguistic_holdout': False, 'world_truth': 'NOT_ESTABLISHED'}


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
    archive = FOLDER / 'full_validation_reports_v1.zip'
    output = FOLDER / 'full_validation_v1.json'
    require(not archive.exists() and not output.exists(), 'Finalized evidence already exists; it is never overwritten')
    initial_outputs = output_inventory(run)
    finalizer_before = record(Path(__file__).resolve())
    execution = load(run / 'execution.json')
    require(execution['schema'] == 'nabt.arabic-completion.full-gate-execution.v1'
            and execution['command'][:3] == ['make', 'formal', 'check']
            and execution['all_required_gates_passed'] is True
            and type(execution['exit_code']) is int and execution['exit_code'] == 0,
            'The full release gate did not pass')
    before, after = load(run / 'inputs_before.json'), load(run / 'inputs_after.json')
    require(same(before, after) and execution['executable_inputs_unchanged'] is True,
            'Executable input bytes changed during the full gate')
    input_index = checked_inventory(after)
    require(execution['before_sha256'] == before['sha256'] == execution['after_sha256']
            and type(execution['input_file_count']) is int and execution['input_file_count'] == before['file_count'],
            'Full-gate execution is not bound to its actual input inventory')
    require(input_index.get(finalizer_before['path']) == finalizer_before,
            'Finalizer was not fixed before the gate began')
    policy, runtime = reviewed_policy(input_index)
    log = (run / 'make_check.log').read_bytes()
    require(sha256(log).hexdigest() == execution['log']['sha256']
            and execution['log']['bytes'] == len(log) and execution['log']['path'] == 'make_check.log', 'Gate log changed')
    summaries = re.findall(r'Ran (\d+) tests? in ([0-9.]+)s\n\n([^\n]+)', log.decode())
    require(summaries and all(status == 'OK' for _, _, status in summaries),
            'Missing, failed, or skipped unittest summary')
    builds = re.findall(r'Build completed successfully \((\d+) jobs\)', log.decode())
    require(builds and int(builds[0]) > 0, 'Successful full Lean build receipt is missing')
    formal_inputs = sorted(name for name in input_index if name.startswith('formal/') and name.endswith('.lean'))
    required_formal = {'formal/Nabt.lean', 'formal/Audit.lean', 'formal/lakefile.lean',
                       'formal/Nabt/ArabicInnaFragment.lean', 'formal/ArabicInnaFragmentProbe.lean'}
    actual_formal = sorted(str(path.relative_to(ROOT)) for path in (ROOT / 'formal').rglob('*.lean')
                           if '.lake' not in path.parts and path.is_file())
    require(required_formal <= set(formal_inputs) and formal_inputs == actual_formal
            and 'formal/theorems.json' in input_index, 'Full Lean input inventory omits source or integration files')
    lakefile = (ROOT / 'formal/lakefile.lean').read_text()
    require(re.search(r'@\[default_target\]\s*lean_exe arabicInnaFragmentProbe\s+where\s+root := `ArabicInnaFragmentProbe', lakefile)
            and 'import Nabt.ArabicInnaFragment' in (ROOT / 'formal/Nabt.lean').read_text(),
            'The fragment executable is not a full-build default target')
    manifest = load(ROOT / 'formal/theorems.json')
    theorem_names = manifest['theorems']
    require(type(theorem_names) is list and len(theorem_names) == len(set(theorem_names)) == THEOREM_COUNT
            and sum(name.startswith('Nabt.ArabicInnaFragment.') for name in theorem_names) == 21,
            'Theorem declaration inventory differs from this release')
    audit_text = (ROOT / 'formal/Audit.lean').read_text()
    require(re.findall(r"``(Nabt\.[\w.']+)", audit_text) == theorem_names,
            'Audit does not cover every registered theorem in the declared order')
    inna = check_inna_transport(run, input_index)
    raw_streams = []
    raw_paths = sorted(path for path in run.rglob('*raw.jsonl.gz') if path.is_file())
    require(run / 'inflection-regression.raw.jsonl.gz' in raw_paths, 'Required inflection raw stream is missing')
    for path in raw_paths:
        compressed = path.read_bytes()
        raw_identity = {'path': str(path.relative_to(ROOT)), 'bytes': len(compressed),
                        'sha256': sha256(compressed).hexdigest()}
        require(raw_identity == initial_outputs[str(path.relative_to(run))], 'Raw bytes changed before validation')
        payload, lines, decoded = decode_journal(compressed, str(path))
        complete_inflection_inventory = None
        if path.name == 'inflection-regression.raw.jsonl.gz':
            inflection = load(path.with_name('inflection-regression.json'))
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
    for suite in ('construction', 'discourse'):
        path = run / (suite + '-regression.json')
        result = load(path)
        strict_reference = load(repository_file(policy['suites'][suite]['strict_measurement']))
        check_coverage(suite, strict_reference, policy, gate=False)
        scores[suite] = check_coverage(suite, result, policy, gate=True)
        raw_path = path.parent / result['raw_log']['filename']
        require(raw_path.parent == run and raw_path in raw_paths, 'Coverage raw stream is not finalized inside this run')
        require(record(raw_path)['sha256'] == result['raw_log']['sha256'], 'Raw report hash mismatch')
        scores[suite]['report'] = record(path)
        scores[suite]['reviewed_strict_measurement'] = record(repository_file(policy['suites'][suite]['strict_measurement']))
    holdout = load(run / 'arabic-holdout.json')
    postreview = load(run / 'arabic-holdout-postreview/review.json')
    require(holdout['case_score'] == {'passed': 35, 'total': 36}
            and holdout['strict_pass'] is False and postreview['gate_pass'] is True
            and postreview['schema'] == 'nabt.independent-arabic-postreview-gate.v3'
            and postreview['runtime_freeze_sha256'] == RUNTIME_SHA256
            and postreview['material_freeze_sha256'] == HOLDOUT_MATERIAL_SHA256
            and holdout['material_freeze_sha256'] == HOLDOUT_MATERIAL_SHA256
            and postreview['postreview_case_score'] == {'passed': 36, 'total': 36}
            and postreview['remaining_unsafe_acceptances'] == []
            and postreview['original_result_rewritten'] is False
            and postreview['frozen_harness_or_gold_changed'] is False
            and postreview['runtime_unchanged_during_replay'] is True
            and postreview['full_Arabic_understanding_proved'] is False, 'Holdout review differs')
    false_alarm = [{'case_id': 'H18', 'name': 'question:2:no_grounded_evidence',
                    'pass': False, 'unsafe_acceptance': True}]
    require(same(postreview['reclassified_checker_false_alarms'], false_alarm)
            and same(holdout['unsafe_acceptances'], false_alarm), 'Holdout review waived an additional or altered failure')
    require((run / 'arabic-holdout-postreview/original_result.json').read_bytes()
            == (run / 'arabic-holdout.json').read_bytes(), 'Original holdout result was not preserved byte-for-byte')
    source_inputs = [record(run / 'arabic-holdout.json'), record(run / 'arabic-holdout.raw.jsonl'),
                     record(FOLDER / 'code_freeze_v1.json')]
    require(same(postreview['source_inputs'], source_inputs), 'Holdout review is not bound to this run and approved runtime')
    require(postreview['code'] == record(ROOT / 'tools/arabic_coverage_postreview_v3.py')
            and input_index.get(postreview['code']['path']) == postreview['code'],
            'Holdout review code differs from the complete gate input')
    for item in postreview['independent_validators']:
        checked_identity(item)
        require(input_index.get(item['path']) == item, 'Holdout validator changed outside its replay interval')
    receipts_path = checked_identity(postreview['fresh_replay_receipts'])
    require(receipts_path == run / 'arabic-holdout-postreview/verification_replay.json',
            'Holdout fresh receipts are not local to this gate run')
    replay_receipts = load(receipts_path)
    calls = {'verify_discourse': 36, 'verify_discourse_answer': 63,
             'verify_discourse_changed_context': 2, 'verify_answer_changed_context': 2}
    require(type(replay_receipts) is list and len(replay_receipts) == 103
            and {call: sum(row['call'] == call for row in replay_receipts) for call in calls} == calls
            and all(row['call'] in calls and row['value']['valid'] is (row['call'] in ('verify_discourse', 'verify_discourse_answer'))
                    for row in replay_receipts), 'Holdout replay operation inventory or results differ')
    matches = sum(counts.get(expected, 0) for expected, counts in holdout['question_status_by_expectation'].items())
    require(matches == holdout['question_total'] == 63 and postreview['replayed_certificate_count'] == 103,
            'Holdout question or verification counts differ')
    axioms = load(run / 'axioms.json')
    check_formal_audit(axioms, (run / 'axioms.log').read_text(), theorem_names)
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
    require(checked_inventory(after) == input_index, 'Executable input bytes changed during finalization')
    checked_identity(inna['actual_program'])
    require(record(Path(__file__).resolve()) == finalizer_before, 'Finalizer source changed during execution')
    report = {
        'schema': 'nabt.arabic-completion.full-validation.v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'validation_scope': 'Local make formal check plus complete raw-stream and archive finalization. Remote CI and publication are established separately.',
        'finalizer': finalizer_before, 'output_inventory_stable_during_finalization': True,
        'full_release_gate_pass': True, 'execution': execution,
        'primary_unittest_count': int(summaries[0][0]),
        'unittest_groups': [{'tests': int(count), 'seconds': float(seconds), 'status': status}
                            for count, seconds, status in summaries],
        'formal_build_jobs': int(builds[0]), 'formal_build_jobs_observed_not_assumed': True,
        'formal_source_inventory': formal_inputs, 'formal_audited_declarations': axioms['theorem_count'],
        'observed_axioms': axioms['observed_axioms'], 'project_axioms_allowed': False,
        'runtime_freeze': record(FOLDER / 'code_freeze_v1.json'),
        'regression_policy': record(FOLDER / 'regression_policy_v1.json'),
        'executable_inputs': {'count': before['file_count'], 'sha256': before['sha256'],
                              'unchanged_during_gate': True, 'rechecked_after_gate': True,
                              'unchanged_during_finalization': True},
        'coverage': scores,
        'inna_fragment_transport': inna,
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
        'new_24_case_oracle_scores_included': False,
        'previous_release_full_validation': 'evidence/arabic_coverage/full_validation_v2.json',
        'all_Arabic_completeness': 'NOT_ESTABLISHED',
        'not_claimed': ['General Python/Lean refinement', 'Adequate formal reference for all Arabic',
                        'Complete conversion of the four classical books', 'General source-acquisition authentication',
                        'Independent observation of all external facts', 'A new blind test after development'],
    }
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'report': record(output), 'archive': record(archive),
                      'archive_entries': len(members), 'verified_raw_streams': len(raw_streams),
                      'primary_unittests': report['primary_unittest_count']}))


if __name__ == '__main__':
    main()
