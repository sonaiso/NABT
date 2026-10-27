#!/usr/bin/env python3
"""Run a fresh versioned continuation and separate source counterexamples.

Historical successes alone cannot satisfy this command. Both producers run
afresh, then their stored calls are independently checked and rescored.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


P = module('regression_continuation_review', 'review_continuation_v1.py')
C = module('regression_source_counterexamples', 'run_source_counterexamples_v1.py')
E, R = P.E, P.R


def run(output_dir):
    E.require(not output_dir.exists(), 'Refusing to replace a continuation attempt')
    E.require(output_dir.is_relative_to(R.ROOT), 'Output directory must be inside the repository')
    before = R.check_runner_freeze(HERE / 'runner_freeze_v4.json')
    P.historical_reference()
    C.load_cases()
    output_dir.mkdir(parents=True)
    errors, executions = [], []
    for filename, folder, expected_exit in [('run_oracle_v1.py', 'strict', 1),
                                            ('run_source_counterexamples_v1.py', 'source_counterexamples', 0)]:
        command = [sys.executable, str(HERE / filename), '--output-dir', str(output_dir / folder)]
        with (output_dir / (folder + '.stdout.log')).open('wb') as stdout, \
                (output_dir / (folder + '.stderr.log')).open('wb') as stderr:
            process = subprocess.run(command, stdout=stdout, stderr=stderr, cwd=R.ROOT, check=False)
        executions.append({'kind': folder, 'command': command, 'exit': process.returncode})
        if process.returncode != expected_exit or not (output_dir / folder / 'result.json').is_file():
            errors.append({'phase': folder, 'reason': 'Fresh producer did not complete the declared measurement',
                           'expected_exit': expected_exit, 'observed_exit': process.returncode})
    reviewed = source_review = None
    try:
        reviewed = P.review(output_dir / 'strict/result.json', output_dir / 'strict/raw.jsonl.gz', output_dir / 'review')
    except Exception as error:
        errors.append({'phase': '24_case_review', 'type': type(error).__name__, 'message': str(error)})
    try:
        source_review = C.review_saved(output_dir / 'source_counterexamples/result.json',
                                      output_dir / 'source_counterexamples/raw.jsonl.gz')
        (output_dir / 'source_counterexamples/review.json').write_text(
            json.dumps(source_review, ensure_ascii=False, indent=2) + '\n')
    except Exception as error:
        errors.append({'phase': 'source_counterexample_review', 'type': type(error).__name__, 'message': str(error)})
    after = R.check_runner_freeze(HERE / 'runner_freeze_v4.json')
    stable = E.wire(before) == E.wire(after)
    passed = bool(not errors and stable and reviewed and reviewed['regression_gate_pass']
                  and source_review and source_review['gate_pass'])
    receipt = {'schema': 'nabt.source-acquisition.regression-execution.v1',
               'completed_utc': datetime.now(timezone.utc).isoformat(), 'executions': executions,
               'runtime_freeze_sha256': R.RUNTIME_SHA, 'material_freeze_sha256': R.MATERIAL_SHA,
               'dependency_freeze_sha256': before['sha256'], 'source_material_freeze_sha256': P.SOURCE_MATERIAL,
               'fresh_runtime_prediction_performed': True, 'not_a_new_blind_experiment': True,
               'historical_material_unchanged': True, 'historical_files_repinned': False,
               'strict_result': str((output_dir / 'strict/result.json').relative_to(R.ROOT)),
               'review': str((output_dir / 'review/review.json').relative_to(R.ROOT)),
               'source_counterexample_result': str((output_dir / 'source_counterexamples/result.json').relative_to(R.ROOT)),
               'source_counterexample_review': str((output_dir / 'source_counterexamples/review.json').relative_to(R.ROOT)),
               'fixed_cases': reviewed['fixed_cases'] if reviewed else None,
               'questions': reviewed['questions'] if reviewed else None,
               'conditional_provenance': reviewed['conditional_provenance'] if reviewed else None,
               'exact_historical_public_calls_and_case_records': bool(reviewed and
                    reviewed['exact_historical_public_calls_and_case_records']),
               'source_counterexamples': source_review['summary'] if source_review else None,
               'dependencies_unchanged': stable, 'errors': errors, 'strict_pass': False,
               'regression_gate_pass': passed,
               'scope': 'Retain the same partial 24-case/29-question result under a versioned classical-source runtime, plus six separate source-premise counterexamples. No failure is waived and no universal Arabic completeness is claimed.'}
    (output_dir / 'regression.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    sys.exit(run(args.output_dir.resolve()))
