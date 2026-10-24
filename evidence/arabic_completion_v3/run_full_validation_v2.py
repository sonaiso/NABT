#!/usr/bin/env python3
"""Run the release gates and record the exact executable inputs before/after.

Reports are never overwritten. Files under docs/ may subsequently record the
results; they are not included in the executable-input stability assertion.
The root README is captured, as are the evidence directories listed below.
"""
from __future__ import annotations

import argparse
import importlib.util
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')


def load_finalizer():
    path = ROOT / 'evidence/arabic_completion_v3/finalize_validation_v2.py'
    spec = importlib.util.spec_from_file_location('nabt_continuation_finalizer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory():
    paths = {ROOT / name for name in ('Makefile', 'pyproject.toml', 'README.md', 'AGENTS.md',
                                     '.github/workflows/ci.yml', '.gitattributes')}
    for directory in ('src', 'tools', 'tests', 'formal', 'examples'):
        for path in (ROOT / directory).rglob('*'):
            parts = path.relative_to(ROOT).parts
            if (path.is_file() and not any(part in ('__pycache__', '.lake')
                                          or part.endswith(('.egg-info', '.dist-info')) for part in parts)):
                paths.add(path)
    folder = ROOT / 'evidence/arabic_coverage'
    paths.update(folder / name for name in ('code_freeze_v1.json', 'code_freeze_v1.tar.gz',
                                           'code_freeze_v2.json', 'code_freeze_v2.tar.gz',
                                           'regression_policy_v1.json', 'run_full_validation_v1.py'))
    policy = json.loads((folder / 'regression_policy_v1.json').read_bytes())
    paths.update(ROOT / suite['strict_measurement'] for suite in policy['suites'].values())
    for name in ('holdout_v1', 'holdout_v2'):
        paths.update(path for path in (folder / name).rglob('*') if path.is_file()
                     and '__pycache__' not in path.parts)
    completion = ROOT / 'evidence/arabic_completion_v3'
    finalizer = load_finalizer()
    finalizer.require_ready()
    finalizer.preserved_history()
    # All phase evidence can be an oracle/source/checker dependency. The phase
    # README may report results later; only this run's new final outputs are
    # excluded to avoid including a report in its own before/after inventory.
    excluded = {completion / name for name in ('README.md', 'full_validation_v2.json',
                                               'full_validation_reports_v2.zip')}
    paths.update(path for path in completion.rglob('*') if path.is_file()
                 and path not in excluded and '__pycache__' not in path.parts)
    current_policy = json.loads((completion / 'regression_policy_v2.json').read_bytes())
    paths.update(ROOT / suite['strict_measurement'] for suite in current_policy['suites'].values())
    rows = []
    for path in sorted(paths):
        data = path.read_bytes()
        rows.append({'path': str(path.relative_to(ROOT)), 'bytes': len(data),
                     'sha256': sha256(data).hexdigest()})
    return {'files': rows, 'file_count': len(rows), 'sha256': sha256(wire(rows)).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lake', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    finalizer = load_finalizer()
    finalizer.require_ready()
    before = inventory()
    finalizer.reviewed_policy({row['path']: row for row in before['files']})
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'inputs_before.json', before)
    command = ['make', 'formal', 'check', 'LAKE=' + str(args.lake.resolve()),
               'PYTHON=' + sys.executable, 'EVIDENCE_DIR=' + str(output),
               'TEXT_CODE_FREEZE=' + str(ROOT / 'evidence/arabic_completion_v3/code_freeze_v2.json'),
               'RUNTIME_FREEZE_VERSION=' + finalizer.CURRENT_FREEZE_SELECTOR,
               'ARABIC_EVALUATION_DIR=' + str(output / 'arabic-regression'),
               'GOVERNOR_EVALUATION_DIR=' + str(output / 'governor-regression')]
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    with (output / 'make_check.log').open('xb') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False)
    after = inventory()
    save(output / 'inputs_after.json', after)
    log = output / 'make_check.log'
    report = {
        'schema': 'nabt.arabic-completion.full-gate-execution.v2', 'command': command,
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
        'seconds': round(time.monotonic() - clock, 3), 'python': sys.version,
        'platform': platform.platform(), 'exit_code': result.returncode,
        'before_sha256': before['sha256'], 'after_sha256': after['sha256'],
        'input_file_count': before['file_count'], 'executable_inputs_unchanged': before == after,
        'all_required_gates_passed': result.returncode == 0 and before == after,
        'log': {'path': log.name, 'bytes': log.stat().st_size,
                'sha256': sha256(log.read_bytes()).hexdigest()},
        'historical_phase_preservation': finalizer.preserved_history(),
        'current_runtime_freeze': finalizer.record(ROOT / 'evidence/arabic_completion_v3/code_freeze_v2.json'),
        'scope': 'Repository release gates on pinned runtime and explicitly captured executable inputs; no claim of all-Arabic completeness.',
    }
    save(output / 'execution.json', report)
    print(json.dumps({key: report[key] for key in ('exit_code', 'seconds', 'input_file_count',
                                                 'executable_inputs_unchanged', 'all_required_gates_passed')}))
    return 0 if report['all_required_gates_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
