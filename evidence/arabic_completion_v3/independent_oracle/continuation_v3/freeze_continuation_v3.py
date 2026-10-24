#!/usr/bin/env python3
"""Pin only this new continuation; never replace any historical freeze."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('freeze_continuation_review', HERE / 'review_continuation_v3.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
R, E = P.R, P.E
E.require(not any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules), 'Freezer must not call the runtime')
P.historical_reference()
snapshot = E.runtime_snapshot(R.ROOT / 'evidence/arabic_completion_v3/code_freeze_v2.json', R.ROOT)
E.require(snapshot['runtime_freeze_sha256'] == R.RUNTIME_SHA, 'Wrong approved runtime')
files = {row['path']: row for row in snapshot['files'][snapshot['runtime_file_count']:]}
paths = [*HERE.glob('*.py'), HERE / 'CONTRACT.md', HERE / 'tests_before_execution.log',
         *[p for p in (HERE / 'source_counterexamples_v1').iterdir() if p.is_file()],
         P.ORACLE / 'freeze.json', P.ORACLE / 'runner_freeze_v1.json', P.ORACLE / 'postreview_freeze_v2.json',
         P.ORACLE / 'first_run_v1/result.json', P.ORACLE / 'first_run_v1/raw.jsonl.gz',
         P.ORACLE / 'first_run_v1/result.code.tar.gz', P.ORACLE / 'postreview_run_v2/review.json',
         P.ORACLE / 'postreview_run_v2/mutations.jsonl.gz', R.ROOT / 'tools/discourse_evaluation.py']
old_review = json.loads((P.ORACLE / 'postreview_freeze_v2.json').read_text())
paths.extend(R.ROOT / row['path'] for row in old_review['files'])
for path in paths:
    row = R.file_row(path)
    files[row['path']] = row
manifest = {'schema': 'nabt.completion-directed-runner-freeze.v3',
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'material_freeze_sha256': R.MATERIAL_SHA, 'runtime_freeze_sha256': R.RUNTIME_SHA,
            'source_counterexample_material_sha256': P.SOURCE_MATERIAL,
            'historical_first_result_sha256': P.FIRST_RESULT, 'historical_review_result_sha256': P.REVIEW_RESULT,
            'before_first_new_runtime_oracle_prediction': True, 'runtime_calls_performed_by_freezer': False,
            'historical_files_repinned': False, 'files': sorted(files.values(), key=lambda row: row['path'])}
path = HERE / 'runner_freeze_v3.json'
E.require(not path.exists(), 'Refusing to replace a continuation freeze')
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(), 'files': len(files)}))
