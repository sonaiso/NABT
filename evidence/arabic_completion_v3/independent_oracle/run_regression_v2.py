#!/usr/bin/env python3
"""Reproduce the frozen partial trace, then independently validate its review.

A fresh producer run is mandatory. Its known strict nonzero exit is followed
by the full raw-payload, source/certificate and documented-adapter checks.
The gate preserves every coverage failure and never reports full coverage.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('completion_regression_postreview',HERE/'postreview_v2.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)


def run(output_dir):
    P.E.require(not output_dir.exists(),'Refusing to replace a regression attempt')
    P.E.require(output_dir.is_relative_to(P.R.ROOT),'Outputs must be inside the repository')
    output_dir.mkdir(parents=True)
    strict=output_dir/'strict'
    command=[sys.executable,str(HERE/'run_oracle_v1.py'),'--output-dir',str(strict)]
    with (output_dir/'producer.stdout.log').open('wb') as stdout,(output_dir/'producer.stderr.log').open('wb') as stderr:
        producer=subprocess.run(command,stdout=stdout,stderr=stderr,cwd=P.R.ROOT,check=False)
    P.E.require(producer.returncode==1 and (strict/'result.json').is_file(),
                'Fresh frozen producer did not complete its documented strict-failure measurement')
    code=P.review(strict/'result.json',strict/'raw.jsonl.gz',output_dir/'postreview')
    review=json.loads((output_dir/'postreview/review.json').read_text())
    passed=bool(code==0 and review['review_valid'] and review['regression_gate']['gate_pass']
                and review['identical_raw_public_call_payloads_and_ordered_observations']
                and not review['unsafe_check_failures'] and not review['independent_integrity_failures'])
    receipt={'schema':'nabt.completion-regression-execution.v2','command':command,'producer_exit':producer.returncode,
        'fresh_runtime_prediction_performed':True,'not_a_new_blind_experiment':True,
        'same_frozen_runtime_and_material':True,'original_strict_result':str((strict/'result.json').relative_to(P.R.ROOT)),
        'postreview':str((output_dir/'postreview/review.json').relative_to(P.R.ROOT)),
        'fixed_cases':review['fixed_cases'],'questions':review['questions'],
        'conditional_provenance':review['conditional_provenance'],'strict_pass':False,
        'regression_gate_pass':passed,'scope':'Only this pinned runtime/material/complete observed trace; every known failure is still reported.'}
    (output_dir/'regression.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False))
    return 0 if passed else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();sys.exit(run(args.output_dir.resolve()))
