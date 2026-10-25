#!/usr/bin/env python3
"""Freeze the new oracle runner/dependencies before its first runtime execution.

Original inputs, gold, previous freezes and previous observations are read-only.
This performs byte/archive checks, not a prediction or a new blind experiment.
"""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORACLE=HERE.parent
ROOT=ORACLE.parents[2]


def main():
    output=HERE/'runner_freeze_v5.json'
    if output.exists(): raise ValueError('Never overwrite an observed dependency freeze')
    spec=importlib.util.spec_from_file_location('classical_source_oracle_runner',HERE/'run_oracle_v5.py')
    R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
    runtime=ROOT/'evidence/arabic_completion_v5/code_freeze_v1.json'
    snapshot=R.E.runtime_snapshot(runtime,ROOT)
    current_paths={r['path'] for r in json.loads(runtime.read_bytes())['files']}
    old=json.loads((ORACLE/'continuation_v4/runner_freeze_v4_review3.json').read_bytes())
    selected=set()
    for row in old['files']:
        path=row['path'].replace('/continuation_v4/','/continuation_v5/')
        path=path.replace('review_continuation_v4.py','review_continuation_v5.py').replace('run_oracle_v4.py','run_oracle_v5.py').replace('run_regression_v4.py','run_regression_v5.py')
        selected.add(path)
    selected |= {r['path'] for r in snapshot['files'] if r['path'] not in current_paths}
    selected |= {str(p.relative_to(ROOT)) for p in HERE.glob('*.py')}
    selected |= {'tests/test_completion_v5_gate.py','tests/test_imperative_paradigm.py',
                 'tools/imperative_paradigm_validation.py'}
    rows=[R.file_row(ROOT/name) for name in sorted(selected)]
    freeze={k:v for k,v in old.items() if k not in ('schema','created_utc','runtime_freeze_sha256','files')}
    freeze.update(schema='nabt.completion-directed-runner-freeze.v5',created_utc=datetime.now(timezone.utc).isoformat(),
        runtime_freeze_sha256=sha256(runtime.read_bytes()).hexdigest(),
        previous_dependency_freeze_sha256=sha256((ORACLE/'continuation_v4/runner_freeze_v4_review3.json').read_bytes()).hexdigest(),
        files=rows,scope='New runtime and checker dependency continuation of identical original oracle material. No historical input, gold, result or freeze is rewritten.')
    with output.open('x',encoding='utf-8') as out: json.dump(freeze,out,ensure_ascii=False,indent=2);out.write('\n')
    print(json.dumps({'runner_freeze':str(output.relative_to(ROOT)),'sha256':sha256(output.read_bytes()).hexdigest(),
                      'files':len(rows),'runtime_calls_performed':False}))

if __name__=='__main__':main()
