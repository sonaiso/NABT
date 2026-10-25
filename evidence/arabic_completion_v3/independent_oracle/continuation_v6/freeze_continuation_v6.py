#!/usr/bin/env python3
"""Freeze unchanged-oracle evaluator dependencies before the new run."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORACLE = HERE.parent
ROOT = ORACLE.parents[2]


def main():
    output = HERE / 'runner_freeze_v6.json'
    if output.exists():
        raise ValueError('Never overwrite an observed dependency freeze')
    spec = importlib.util.spec_from_file_location('classical_law_oracle_runner', HERE / 'run_oracle_v6.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runtime = ROOT / 'evidence/arabic_completion_v6/code_freeze_v1.json'
    snapshot = runner.E.runtime_snapshot(runtime, ROOT)
    current_paths = {r['path'] for r in json.loads(runtime.read_bytes())['files']}
    old_path = ORACLE / 'continuation_v5/runner_freeze_v5.json'
    old = json.loads(old_path.read_bytes())
    selected = set()
    for row in old['files']:
        path = row['path']
        if '/continuation_v5/' in path:
            path = path.replace('/continuation_v5/', '/continuation_v6/').replace('_v5.py', '_v6.py')
        selected.add(path)
    selected |= {r['path'] for r in snapshot['files'] if r['path'] not in current_paths}
    selected |= {str(p.relative_to(ROOT)) for p in HERE.glob('*.py')}
    selected |= {'tests/test_completion_v6_gate.py'}
    rows = [runner.file_row(ROOT / name) for name in sorted(selected)]
    freeze = {k: v for k, v in old.items() if k not in ('schema', 'created_utc', 'runtime_freeze_sha256', 'files')}
    freeze.update(schema='nabt.completion-directed-runner-freeze.v6',
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  runtime_freeze_sha256=sha256(runtime.read_bytes()).hexdigest(),
                  previous_dependency_freeze_sha256=sha256(old_path.read_bytes()).hexdigest(), files=rows,
                  scope='New conditional-law runtime; same original oracle inputs/gold and residual signatures. Historical evidence is read-only.')
    with output.open('x', encoding='utf-8') as out:
        json.dump(freeze, out, ensure_ascii=False, indent=2)
        out.write('\n')
    print(json.dumps({'runner_freeze': str(output.relative_to(ROOT)),
                      'sha256': sha256(output.read_bytes()).hexdigest(), 'files': len(rows),
                      'runtime_calls_performed': False}))


if __name__ == '__main__':
    main()
