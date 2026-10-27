#!/usr/bin/env python3
"""Freeze additive continuation dependencies; never rewrite the old oracle.

The old material, scorer, first-run journal and corrected postreview are still
read by their original pinned paths. New wrappers only select the new runtime
identity and preserve the existing comparison obligations.
"""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT / 'evidence/certified_natural_use_v1/independent_oracle/runner_freeze_v5.json'
PREVIOUS_SHA256 = '7965b7ac4d69fd0ed0cdf73811bad94d25559852a70f249d642eec5a59793eb7'


def dependency_paths(snapshot):
    raw = PREVIOUS.read_bytes()
    if sha256(raw).hexdigest() != PREVIOUS_SHA256:
        raise ValueError('Historical dependency freeze changed')
    previous = json.loads(raw)
    prefix = 'evidence/certified_natural_use_v1/independent_oracle/'
    destination = 'evidence/progressive_rule_audit_v1/independent_oracle/'
    selected = {destination + row['path'].removeprefix(prefix)
                if row['path'].startswith(prefix) else row['path']
                for row in previous['files']}
    selected.remove('evidence/certified_natural_use_v1/regression_policy_v1.json')
    selected.update({
        'evidence/progressive_rule_audit_v1/regression_policy_v1.json',
        'evidence/progressive_rule_audit_v1/build_runtime_freeze.py',
        'tests/test_progressive_rule_runtime_freeze.py',
        'tools/text_evaluation/integrity.py',
        'evidence/certified_natural_use_v1/code_freeze_v1.json',
        'evidence/certified_natural_use_v1/code_freeze_v1.tar.gz',
        'evidence/certified_natural_use_v1/regression_policy_v1.json',
        'evidence/certified_natural_use_v1/independent_oracle/runner_freeze_v5.json',
    })
    return selected


def main():
    output = HERE / 'runner_freeze_v1.json'
    if output.exists():
        raise ValueError('Never overwrite an observed dependency freeze')
    spec = importlib.util.spec_from_file_location('progressive_oracle_runner', HERE / 'run_oracle_v1.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runtime = ROOT / 'evidence/progressive_rule_audit_v1/code_freeze_v1.json'
    snapshot = runner.E.runtime_snapshot(runtime, ROOT)
    old = json.loads(PREVIOUS.read_bytes())
    rows = [runner.file_row(ROOT / name) for name in sorted(dependency_paths(snapshot))]
    frozen = {key: value for key, value in old.items()
              if key not in ('schema', 'created_utc', 'runtime_freeze_sha256', 'files',
                             'upstream_hardening_commit', 'supersedes_pre_execution_dependency_freeze_sha256')}
    frozen.update(schema='nabt.progressive-rule-audit.directed-runner-freeze.v1',
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  runtime_freeze_sha256=sha256(runtime.read_bytes()).hexdigest(),
                  previous_dependency_freeze_sha256=PREVIOUS_SHA256, files=rows,
                  review_correction='Versioned additive runtime and exact dependency identities; all historical material, scorers, denominators and residual signatures remain unchanged. The new lexical/native classical surfaces are evaluated separately.',
                  runtime_calls_performed_by_freezer=False,
                  historical_files_repinned=False,
                  scope='Same 24 authored cases, 29 questions and separate six source counterexamples; historical evidence is read-only.')
    with output.open('x', encoding='utf-8') as stream:
        json.dump(frozen, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'runner_freeze': str(output.relative_to(ROOT)),
                      'sha256': sha256(output.read_bytes()).hexdigest(),
                      'files': len(rows), 'runtime_calls_performed': False}))


if __name__ == '__main__':
    main()
