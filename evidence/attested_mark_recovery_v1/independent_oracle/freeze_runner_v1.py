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
PREVIOUS = ROOT / 'evidence/framework_foundation_v1/independent_oracle/runner_freeze_v1.json'
PREVIOUS_SHA256 = 'bfceeccfe85fae87156a3be23c2e85af58db138fa0b63b34934c6db6195f9b8e'


def dependency_paths(snapshot):
    raw = PREVIOUS.read_bytes()
    if sha256(raw).hexdigest() != PREVIOUS_SHA256:
        raise ValueError('Historical dependency freeze changed')
    previous = json.loads(raw)
    prefix = 'evidence/framework_foundation_v1/independent_oracle/'
    destination = 'evidence/attested_mark_recovery_v1/independent_oracle/'
    selected = {destination + row['path'].removeprefix(prefix)
                if row['path'].startswith(prefix) else row['path']
                for row in previous['files']}
    selected.add('evidence/attested_mark_recovery_v1/regression_policy_v1.json')
    selected.add('tests/test_attested_mark_runtime_freeze.py')
    return selected


def main():
    output = HERE / 'runner_freeze_v4.json'
    if output.exists():
        raise ValueError('Never overwrite an observed dependency freeze')
    spec = importlib.util.spec_from_file_location('foundation_oracle_runner', HERE / 'run_oracle_v1.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runtime = ROOT / 'evidence/attested_mark_recovery_v1/code_freeze_v1.json'
    snapshot = runner.E.runtime_snapshot(runtime, ROOT)
    old = json.loads(PREVIOUS.read_bytes())
    selected = dependency_paths(snapshot)
    rows = [runner.file_row(ROOT / name) for name in sorted(selected)]
    frozen = {key: value for key, value in old.items()
              if key not in ('schema', 'created_utc', 'runtime_freeze_sha256', 'files', 'upstream_hardening_commit')}
    frozen.update(schema='nabt.attested-mark-recovery.directed-runner-freeze.v1',
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  runtime_freeze_sha256=sha256(runtime.read_bytes()).hexdigest(),
                  previous_dependency_freeze_sha256=sha256(PREVIOUS.read_bytes()).hexdigest(),
                  supersedes_pre_execution_dependency_freeze_sha256='c1c92ddaf90f7457c9927afbfa4c4e89c37a3a981869d818cfaa09f23b2852f3',
                  files=rows,
                  review_correction='Administrative A116 discovery registration, current-oracle wrapper selection and dependency identities only; all material, scorer, denominators and residual signatures remain unchanged.',
                  scope='Same 24 authored cases, 29 questions and separate six source counterexamples; historical evidence is read-only.')
    with output.open('x', encoding='utf-8') as stream:
        json.dump(frozen, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'runner_freeze': str(output.relative_to(ROOT)),
                      'sha256': sha256(output.read_bytes()).hexdigest(),
                      'files': len(rows), 'runtime_calls_performed': False}))


if __name__ == '__main__':
    main()
