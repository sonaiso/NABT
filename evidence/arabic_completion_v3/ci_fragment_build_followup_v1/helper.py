#!/usr/bin/env python3
"""Apply one reviewed CI argument after its original full gate is finalized.

This is a local CI-only follow-up, not a replacement for the original full
validation or proof that remote final-head/merge CI has passed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / 'artifacts/local/arabic-completion-publication-audit'
FOLDER = ROOT / 'evidence/arabic_completion_v3'
OUTPUT = FOLDER / 'ci_fragment_build_followup_v1'
BACKUP_FOLDER = LOCAL / 'binary-backups/ci_fragment_build_followup_v1'
CI = ROOT / '.github/workflows/ci.yml'
PROGRAM = ROOT / 'formal/.lake/build/bin/arabicInnaFragmentProbe'
CHECKER = ROOT / 'tools/check_arabic_inna_fragment.py'
RUNNER = FOLDER / 'run_full_validation_v1.py'
FULL = FOLDER / 'full_validation_v1.json'
FULL_SHA = 'aaa46a8b772744b43df00413e247c64b420815fe5f15098ab3b56f45f191ec44'
ZIP_SHA = '23062c5cab865a4acfd29aa66928dc3301816fb7816bd712a4d1b5c53ba22d58'
INPUT_SHA = 'dee22b84c6e9fa7abd205659841c1058700d3001f429353470669bcf0f03b3c1'
OLD_CI_SHA = '62f10e3a802ebf6383d19a3c500177d4df54d0cf4ae8b40756b8f2115ec5ac88'
NEW_CI_SHA = '2e63f750292df7e6db317fc6620ca84694df40cb3513bbec43333e7675347b24'
PLAN_SHA = '5b8c27d143a87a22abe36fa68958613136d2ffd3b7ade69298bc29d39c3185db'
OLD_LINE = b'        run: python -I tools/check_arabic_inna_fragment.py --output-dir "${{ runner.temp }}/nabt-arabic-inna-fragment"\n'
NEW_LINE = b'        run: python -I tools/check_arabic_inna_fragment.py --lake "${{ runner.temp }}/nabt-tools/lean-4.34.1-linux/bin/lake" --output-dir "${{ runner.temp }}/nabt-arabic-inna-fragment"\n'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('Non-JSON constant')

    return json.loads(path.read_bytes(), object_pairs_hook=unique, parse_constant=constant)


def identity(path):
    require(path.is_file() and not path.is_symlink(), 'Expected a regular, nonsymlink file')
    data = path.read_bytes()
    name = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    return {'path': name, 'bytes': len(data), 'sha256': sha256(data).hexdigest()}


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')


def save_bytes(path, data):
    with path.open('xb') as handle:
        handle.write(data)


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def inventory_rows(value):
    require(type(value) is dict and set(value) == {'files', 'file_count', 'sha256'}, 'Unexpected inventory schema')
    rows = value['files']
    require(type(value['file_count']) is int and value['file_count'] == len(rows) == 526
            and value['sha256'] == sha256(wire(rows)).hexdigest(), 'Inventory count/digest differs')
    names = [row['path'] for row in rows]
    require(names == sorted(names, key=Path) and len(names) == len(set(names)), 'Incomplete, duplicated or reordered inventory')
    require(all(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
                and type(row['bytes']) is int and row['bytes'] >= 0 for row in rows), 'Malformed input identity')
    return {row['path']: row for row in rows}


def exact_delta(original, current, allow_ci):
    first, second = inventory_rows(original), inventory_rows(current)
    require(set(first) == set(second), 'Captured input paths were added or removed')
    changes = [name for name in first if first[name] != second[name]]
    expected = [CI.relative_to(ROOT).as_posix()] if allow_ci else []
    require(changes == expected, 'Captured inputs differ beyond the reviewed CI change')
    if allow_ci:
        require(first[expected[0]]['sha256'] == OLD_CI_SHA and second[expected[0]]['sha256'] == NEW_CI_SHA,
                'CI change is not the exact reviewed byte delta')
    return [{'path': name, 'before': first[name], 'after': second[name]} for name in changes]


def preflight(run):
    require(FULL.exists() and identity(FULL)['sha256'] == FULL_SHA, 'The pinned successful finalization is not complete')
    full = load(FULL)
    require(full['schema'] == 'nabt.arabic-completion.full-validation.v1'
            and full['full_release_gate_pass'] is True
            and full['executable_inputs']['sha256'] == INPUT_SHA
            and full['executable_inputs']['count'] == 526
            and all(full['executable_inputs'][key] is True for key in (
                'unchanged_during_gate', 'rechecked_after_gate', 'unchanged_during_finalization')),
            'The original complete gate/input receipt differs')
    require(run.resolve() == run and run.is_relative_to(ROOT / 'artifacts/local') and run.is_dir(), 'Invalid full-gate run directory')
    execution = load(run / 'execution.json')
    require(wire(execution) == wire(full['execution'])
            and execution['all_required_gates_passed'] is True
            and type(execution['exit_code']) is int and execution['exit_code'] == 0
            and ('EVIDENCE_DIR=' + str(run)) in execution['command'], 'Final report does not describe this completed run')
    before, after = load(run / 'inputs_before.json'), load(run / 'inputs_after.json')
    require(wire(before) == wire(after) and before['sha256'] == INPUT_SHA, 'Original before/after input inventory differs')
    rows = inventory_rows(before)
    require(rows[RUNNER.relative_to(ROOT).as_posix()] == identity(RUNNER), 'Original inventory runner source changed')
    archive = ROOT / full['archive']['path']
    require(archive == FOLDER / 'full_validation_reports_v1.zip'
            and identity(archive) == full['archive'] and full['archive']['sha256'] == ZIP_SHA,
            'Original finalized archive differs')
    members = full['archive_members']
    with zipfile.ZipFile(archive) as saved:
        require(saved.namelist() == [row['name'] for row in members]
                and len(members) == len({row['name'] for row in members}) == 99, 'Original archive inventory differs')
        for row in members:
            path = run / row['name']
            require(path.resolve().is_relative_to(run), 'Unsafe original archive member path')
            raw = saved.read(row['name'])
            require(len(raw) == row['bytes'] and sha256(raw).hexdigest() == row['sha256']
                    and raw == path.read_bytes(), 'Original run/archive member bytes changed')
    actual_outputs = sorted(path.relative_to(run).as_posix() for path in run.rglob('*') if path.is_file())
    require(actual_outputs == sorted(row['name'] for row in members), 'Original run gained or lost outputs after finalization')
    runner = import_file('nabt_ci_followup_inventory', RUNNER)
    current = runner.inventory()
    exact_delta(before, current, False)
    require(identity(CI)['sha256'] == OLD_CI_SHA, 'CI is not the reviewed original version')
    old = CI.read_bytes()
    require(old.count(OLD_LINE) == 1, 'The reviewed CI step is not unique')
    new = old.replace(OLD_LINE, NEW_LINE, 1)
    require(sha256(new).hexdigest() == NEW_CI_SHA, 'Proposed CI byte hash differs')
    plan = LOCAL / 'ci_fragment_build_review_v1/review.json'
    require(identity(plan)['sha256'] == PLAN_SHA, 'Scoped CI review changed')
    require(identity(PROGRAM) == full['inna_fragment_transport']['actual_program'], 'Current executable differs from the complete gate')
    require(not OUTPUT.exists() and not BACKUP_FOLDER.exists(), 'Follow-up outputs or binary backup already exist; never overwrite them')
    ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--', str(BACKUP_FOLDER / 'original-probe')],
                             cwd=ROOT, capture_output=True, check=False)
    require(ignored.returncode == 0, 'The binary backup must remain outside ordinary Git candidates')
    lake_args = [arg.removeprefix('LAKE=') for arg in execution['command'] if arg.startswith('LAKE=')]
    require(len(lake_args) == 1, 'Original pinned lake command is ambiguous')
    lake = Path(lake_args[0]).resolve(strict=True)
    require(lake.name == 'lake' and lake.parent.parent.name == 'lean-4.34.1-linux', 'Unexpected pinned Lean toolchain path')
    return full, before, runner, old, new, plan, lake


def replace_ci(payload, temp_name, mode):
    temporary = LOCAL / temp_name
    require(not temporary.exists(), 'CI staging path already exists')
    save_bytes(temporary, payload)
    temporary.chmod(mode)
    os.replace(temporary, CI)


def invoke(command, output):
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=420)
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        save_bytes(output / 'checker.stdout.bin', stdout)
        save_bytes(output / 'checker.stderr.bin', stderr)
        raise
    save_bytes(output / 'checker.stdout.bin', stdout)
    save_bytes(output / 'checker.stderr.bin', stderr)
    return process.returncode


def check_focused(directory, lake):
    result = load(directory / 'report.json')
    require(result['ok'] is True and type(result['case_count']) is int and result['case_count'] == 32
            and len(result['checks']) == 32 and all(row['pass'] is True for row in result['checks'])
            and result['returncode'] == 0 and result['error'] is None
            and result['build_performed_by_this_tool'] is True
            and result['build']['ok'] is True
            and result['build']['command'] == [str(lake), 'build', 'arabicInnaFragmentProbe']
            and result['build']['inputs_unchanged'] is True
            and result['program_and_inputs_unchanged'] is True,
            'Actual target build or32-case transport verification failed')
    require(wire(result['files_before']) == wire(result['files_after'])
            and wire(result['build']['files_before']) == wire(result['build']['files_after']),
            'Focused checker recorded changed inputs')
    for row in result['files_after'] + result['build']['files_after']:
        path = Path(row['path']) if Path(row['path']).is_absolute() else ROOT / row['path']
        require(identity(path) == row, 'Focused build/check input identity changed')
    checker = import_file('nabt_ci_followup_transport', CHECKER)
    material, frozen = checker.frozen_material()
    cases = checker.make_cases(material)
    for name in ('lexical_material.json', 'requests.jsonl', 'expectations.json'):
        require((directory / name).read_bytes() == frozen[name], 'Focused frozen transport material differs')
    checked = checker.check_wire(cases, (directory / 'responses.jsonl').read_bytes(),
                                 (directory / 'stderr.bin').read_bytes(), result['returncode'])
    require(len(checked) == 32 and wire(checked) == wire(result['checks']), 'Focused raw transport does not support its report')
    require(result['world_truth'] == 'NOT_ESTABLISHED' and all(result[key] is False for key in (
        'compiler_correctness_proved', 'lexical_acquisition_established', 'lexicon_exhaustiveness_established',
        'independent_linguistic_holdout', 'all_arabic_completeness_established')),
        'Focused transport escalated its scoped authority')
    return result


def run(run_dir):
    full, original_inputs, runner, old_ci, new_ci, plan, lake = preflight(run_dir)
    OUTPUT.mkdir()
    BACKUP_FOLDER.mkdir(parents=True)
    backup = BACKUP_FOLDER / 'original-probe'
    started = datetime.now(timezone.utc).isoformat()
    old_binary = identity(PROGRAM)
    helper_before = identity(Path(__file__).resolve())
    mode = CI.stat().st_mode & 0o777
    save_bytes(OUTPUT / 'ci.before.yml', old_ci)
    save_bytes(OUTPUT / 'ci.after.yml', new_ci)
    save_bytes(OUTPUT / 'scoped_review.json', plan.read_bytes())
    save_bytes(OUTPUT / 'helper.py', Path(__file__).read_bytes())
    save_bytes(OUTPUT / 'original_full_validation.json', FULL.read_bytes())
    save(OUTPUT / 'inputs.before.json', original_inputs)
    base = {'schema': 'nabt.ci-fragment-build-followup.v1', 'started_utc': started,
            'original_full_validation': identity(FULL), 'original_full_archive': full['archive'],
            'original_input_sha256': INPUT_SHA, 'original_ci_sha256': OLD_CI_SHA,
            'corrected_ci_sha256': NEW_CI_SHA, 'helper': helper_before,
            'original_binary': old_binary, 'binary_backup_path': backup.relative_to(ROOT).as_posix(),
            'original_full_gate_rewritten_or_replaced': False, 'remote_ci_pass_claimed': False,
            'required_remote_ci': ['final_branch_head', 'merge_commit'],
            'unchanged_runtime_test_suites_repeated': False,
            'scope': 'One reviewed workflow argument and an actual missing-binary target build followed by32 frozen wire checks.'}
    save(OUTPUT / 'preflight.json', base)
    ci_changed = binary_moved = False
    try:
        require(identity(CI)['sha256'] == OLD_CI_SHA, 'CI changed after preflight')
        replace_ci(new_ci, 'ci-followup-apply.pending', mode)
        ci_changed = True
        after_ci = runner.inventory()
        changes = exact_delta(original_inputs, after_ci, True)
        save(OUTPUT / 'inputs.after-ci.json', after_ci)
        require(identity(PROGRAM) == old_binary, 'Executable changed before backup')
        os.rename(PROGRAM, backup)
        binary_moved = True
        require(not PROGRAM.exists() and not PROGRAM.is_symlink(), 'Executable is not absent before target build')
        backup_identity = identity(backup)
        require(backup_identity['bytes'] == old_binary['bytes'] and backup_identity['sha256'] == old_binary['sha256'],
                'Original binary backup differs')
        save(OUTPUT / 'binary.before-build.json', {'binary_absent': True, 'original': old_binary, 'backup': backup_identity})
        command = [sys.executable, '-I', str(CHECKER), '--lake', str(lake), '--output-dir', str(OUTPUT / 'focused')]
        save(OUTPUT / 'command.json', {'command': command, 'binary_absent_before_invocation': not PROGRAM.exists()})
        returncode = invoke(command, OUTPUT)
        require(returncode == 0, 'Focused checker exited unsuccessfully')
        focused = check_focused(OUTPUT / 'focused', lake)
        rebuilt = identity(PROGRAM)
        require(any(row == rebuilt for row in focused['files_after']), 'Focused receipt does not identify the rebuilt executable')
        after = runner.inventory()
        require(exact_delta(original_inputs, after, True) == changes, 'Additional captured input changed during focused verification')
        require(identity(FULL)['sha256'] == FULL_SHA
                and identity(ROOT / full['archive']['path'])['sha256'] == ZIP_SHA,
                'Original complete validation artifacts changed')
        require(identity(Path(__file__).resolve()) == helper_before, 'Follow-up helper changed during execution')
        require(identity(backup) == backup_identity, 'Original binary backup changed')
        save(OUTPUT / 'inputs.after.json', after)
        report = dict(base, ok=True, completed_utc=datetime.now(timezone.utc).isoformat(),
                      captured_input_count=526, complete_inventory_delta=changes,
                      all_other_captured_inputs_exact=True, binary_absent_before_build=True,
                      actual_target_rebuilt=True, focused_cases_passed=32,
                      focused_report=identity(OUTPUT / 'focused/report.json'),
                      rebuilt_binary=rebuilt, original_binary_backup=backup_identity,
                      original_binary_recoverable=True, finalization_unchanged=True)
        save(OUTPUT / 'review.json', report)
        print(json.dumps({'ok': True, 'review': identity(OUTPUT / 'review.json'),
                          'cases': 32, 'only_ci_changed': True, 'binary_rebuilt_from_absence': True}))
        return 0
    except BaseException as failure:
        recovery = {'attempted': True, 'ci_restored': False, 'binary_restored': False}
        try:
            if binary_moved and backup.is_file():
                if PROGRAM.exists() or PROGRAM.is_symlink():
                    os.rename(PROGRAM, BACKUP_FOLDER / 'failed-or-unverified-rebuild')
                shutil.copy2(backup, PROGRAM)
                recovery['binary_restored'] = identity(PROGRAM) == old_binary
                recovery['backup'] = identity(backup)
            if ci_changed and identity(CI)['sha256'] == NEW_CI_SHA:
                replace_ci(old_ci, 'ci-followup-restore.pending', mode)
                recovery['ci_restored'] = identity(CI)['sha256'] == OLD_CI_SHA
            recovery['all_original_captured_inputs_restored'] = wire(runner.inventory()) == wire(original_inputs)
        except BaseException as restore_error:
            recovery['restore_error_type'] = type(restore_error).__name__
        report = dict(base, ok=False, completed_utc=datetime.now(timezone.utc).isoformat(),
                      error_type=type(failure).__name__, error=str(failure), recovery=recovery,
                      original_binary_recoverable=backup.is_file())
        save(OUTPUT / 'review.json', report)
        print(json.dumps({'ok': False, 'review': identity(OUTPUT / 'review.json'), 'recovery': recovery}))
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        return run(args.run_dir.resolve())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as failure:
        print(json.dumps({'ok': False, 'stage': 'preflight', 'error_type': type(failure).__name__, 'error': str(failure)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
