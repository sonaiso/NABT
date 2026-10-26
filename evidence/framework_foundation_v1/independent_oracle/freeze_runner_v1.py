#!/usr/bin/env python3
"""Capture new dependency identities without rewriting historical oracle data."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORACLE = ROOT / 'evidence/arabic_completion_v3/independent_oracle'
PREVIOUS = ORACLE / 'continuation_v6_review2/runner_freeze_v6.json'
PREVIOUS_SHA256 = '6e8dde893aa919dec0dd23e37a7882b228d45d977743526ef2178483599fabb3'
NAMES = {
    'run_oracle_v6.py': 'run_oracle_v1.py',
    'review_continuation_v6.py': 'review_continuation_v1.py',
    'run_regression_v6.py': 'run_regression_v1.py',
    'run_source_counterexamples_v1.py': 'run_source_counterexamples_v1.py',
    'test_continuation_v6_review2.py': 'test_continuation_v1.py',
    'freeze_continuation_v6.py': 'freeze_runner_v1.py',
}


def dependency_paths(snapshot):
    raw = PREVIOUS.read_bytes()
    if sha256(raw).hexdigest() != PREVIOUS_SHA256:
        raise ValueError('Historical dependency freeze changed')
    previous = json.loads(raw)
    prefix = 'evidence/arabic_completion_v3/independent_oracle/continuation_v6_review2/'
    destination = 'evidence/framework_foundation_v1/independent_oracle/'
    selected = set()
    for row in previous['files']:
        name = row['path']
        if name.startswith(prefix):
            name = destination + NAMES[name.removeprefix(prefix)]
        selected.add(name)
    selected.update(row['path'] for row in snapshot['files']
                    if not row['path'].startswith('src/') and row['path'] != 'pyproject.toml')
    selected.update(destination + name for name in NAMES.values())
    selected.update({'tests/test_framework_foundation_freeze.py',
                     'tools/framework_foundation_gate.py',
                     'tools/framework_foundation_postreview.py',
                     'evidence/framework_foundation_v1/regression_policy_v2.json'})
    return selected


def main():
    output = HERE / 'runner_freeze_v1.json'
    if output.exists():
        raise ValueError('Never overwrite an observed dependency freeze')
    spec = importlib.util.spec_from_file_location('foundation_oracle_runner', HERE / 'run_oracle_v1.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runtime = ROOT / 'evidence/framework_foundation_v1/code_freeze_v2.json'
    snapshot = runner.E.runtime_snapshot(runtime, ROOT)
    old = json.loads(PREVIOUS.read_bytes())
    selected = dependency_paths(snapshot)
    rows = [runner.file_row(ROOT / name) for name in sorted(selected)]
    frozen = {key: value for key, value in old.items()
              if key not in ('schema', 'created_utc', 'runtime_freeze_sha256', 'files', 'upstream_hardening_commit')}
    frozen.update(schema='nabt.framework-foundation.directed-runner-freeze.v1',
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  runtime_freeze_sha256=sha256(runtime.read_bytes()).hexdigest(),
                  previous_dependency_freeze_sha256=sha256(PREVIOUS.read_bytes()).hexdigest(),
                  files=rows,
                  review_correction='New registered A116 foundation runtime and dependency identities only; all material, scorer, denominators and residual signatures remain unchanged.',
                  scope='Same 24 authored cases, 29 questions and separate six source counterexamples; historical evidence is read-only.')
    with output.open('x', encoding='utf-8') as stream:
        json.dump(frozen, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'runner_freeze': str(output.relative_to(ROOT)),
                      'sha256': sha256(output.read_bytes()).hexdigest(),
                      'files': len(rows), 'runtime_calls_performed': False}))


if __name__ == '__main__':
    main()
