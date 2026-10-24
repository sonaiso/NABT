#!/usr/bin/env python3
"""Run the release gates and record the exact executable inputs before/after.

Reports are never overwritten. Documentation may subsequently record the
results; it is not included in the executable-input stability assertion.
"""
from __future__ import annotations

import argparse
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


def inventory():
    paths = {ROOT / name for name in ('Makefile', 'pyproject.toml', 'README.md', 'AGENTS.md',
                                     '.github/workflows/ci.yml')}
    for directory in ('src', 'tools', 'tests', 'formal'):
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
    output.mkdir(parents=True, exist_ok=False)
    before = inventory()
    save(output / 'inputs_before.json', before)
    command = ['make', 'formal', 'check', 'LAKE=' + str(args.lake.resolve()),
               'PYTHON=' + sys.executable, 'EVIDENCE_DIR=' + str(output),
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
        'schema': 'nabt.arabic-coverage.full-gate-execution.v1', 'command': command,
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
        'seconds': round(time.monotonic() - clock, 3), 'python': sys.version,
        'platform': platform.platform(), 'exit_code': result.returncode,
        'before_sha256': before['sha256'], 'after_sha256': after['sha256'],
        'input_file_count': before['file_count'], 'executable_inputs_unchanged': before == after,
        'all_required_gates_passed': result.returncode == 0 and before == after,
        'log': {'path': log.name, 'bytes': log.stat().st_size,
                'sha256': sha256(log.read_bytes()).hexdigest()},
        'scope': 'Repository release gates on pinned runtime and explicitly captured executable inputs; no claim of all-Arabic completeness.',
    }
    save(output / 'execution.json', report)
    print(json.dumps({key: report[key] for key in ('exit_code', 'seconds', 'input_file_count',
                                                 'executable_inputs_unchanged', 'all_required_gates_passed')}))
    return 0 if report['all_required_gates_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
