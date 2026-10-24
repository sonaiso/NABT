#!/usr/bin/env python3
"""Pin an execution adapter without importing or calling the production runtime."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_completion_runner',HERE/'run_oracle_v1.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
R.load_material()
manifest=R.ROOT/'evidence/arabic_completion_v3/code_freeze_v1.json'
snapshot=R.E.runtime_snapshot(manifest,R.ROOT)
files={row['path']:row for row in snapshot['files'][snapshot['runtime_file_count']:]}
for name in ('run_oracle_v1.py','oracle_checks_v1.py','oracle_mutations_v1.py','test_oracle_runner_v1.py',
             'freeze_runner_v1.py','RUNNER_CONTRACT_v1.md','runner_tests_before_execution.log'):
    row=R.file_row(HERE/name);files[row['path']]=row
# Both evaluator adapters are present in source-witness test imports.
row=R.file_row(R.ROOT/'tools/discourse_evaluation.py');files[row['path']]=row
freeze={'schema':'nabt.completion-directed-runner-freeze.v1','created_utc':datetime.now(timezone.utc).isoformat(),
    'material_freeze_sha256':R.MATERIAL_SHA,'runtime_freeze_sha256':R.RUNTIME_SHA,
    'before_first_24_case_prediction':True,'runtime_calls_performed_by_freezer':False,
    'files':sorted(files.values(),key=lambda row:row['path'])}
path=HERE/'runner_freeze_v1.json'
R.E.require(not path.exists(),'Refusing to replace runner freeze')
path.write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
from hashlib import sha256
print(json.dumps({'path':str(path),'sha256':sha256(path.read_bytes()).hexdigest(),'files':len(freeze['files'])}))
