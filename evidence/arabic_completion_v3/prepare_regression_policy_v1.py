#!/usr/bin/env python3
"""Narrow the existing debt policy after complete, checked strict measurements.

New failures cannot be authorized here: each retained failure must be an exact
member of the previously reviewed policy. No runtime/gold/score is rewritten.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
RUNTIME = 'eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089'
OLD_POLICY = 'cc4a05e19d516b548cc7f935e9506a3cbd85a97c5c0ad9def4dec1c2dbee274a'


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, raw):
    with path.open('xb') as handle:
        handle.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    require(run.is_relative_to(ROOT / 'artifacts/local'), 'Expected repository-local new measurement')
    old_bytes = (ROOT / 'evidence/arabic_coverage/regression_policy_v1.json').read_bytes()
    require(sha256(old_bytes).hexdigest() == OLD_POLICY, 'Old reviewed policy changed')
    old = json.loads(old_bytes)
    raw_freeze = (FOLDER / 'code_freeze_v1.json').read_bytes()
    require(sha256(raw_freeze).hexdigest() == RUNTIME, 'New runtime freeze changed')
    freeze = json.loads(raw_freeze)
    policy = {
        'schema': 'nabt.arabic-completion.regression-policy.v1',
        'runtime_freeze_sha256': RUNTIME,
        'runtime_snapshot_sha256': freeze['snapshot_sha256'],
        'runtime_file_count': len(freeze['files']),
        'baseline_receipt_sha256': sha256((FOLDER / 'baseline.json').read_bytes()).hexdigest(),
        'previous_policy_sha256': OLD_POLICY,
        'review_timing': 'After complete strict measurements and independent source-checker review; original results retained.',
        'meaning': 'Only exact residual coverage failures from the prior policy remain eligible. Scores and failed flags stay unchanged; no false acceptance, execution error, or all-Arabic completeness is waived.',
        'suites': {},
    }
    destination = FOLDER / 'strict_review_v2'
    destination.mkdir(exist_ok=False)
    comparisons = {}
    for suite in ('construction', 'discourse'):
        path = run / (suite + '.json')
        payload = path.read_bytes()
        result = json.loads(payload)
        previous = old['suites'][suite]
        previous_raw = (ROOT / previous['strict_measurement']).read_bytes()
        require(sha256(previous_raw).hexdigest() == previous['strict_measurement_sha256'], 'Prior strict result changed')
        baseline = json.loads(previous_raw)
        require(result['measurement_valid'] is True and result['strict_pass'] is False,
                'Expected a complete valid measurement with explicit residuals')
        require(result['execution_errors'] == result['question_execution_errors'] == []
                and result.get('finalization_errors', []) == []
                and result['false_accept_count'] == result['false_accept_case_count'] == 0,
                'Execution/checker errors and false accepts cannot become coverage debt')
        snapshot = result['snapshot']
        require(snapshot['runtime_freeze_sha256'] == RUNTIME
                and snapshot['runtime_snapshot_sha256'] == freeze['snapshot_sha256']
                and snapshot['runtime_file_count'] == len(freeze['files']), 'Measurement runtime differs')
        require(result['total'] == len(result['cases']) == previous['total'] == 86,
                'The full original denominator is required')
        require(result['passed'] == sum(c['passed'] is True for c in result['cases']), 'Pass count differs')
        require([c['id'] for c in result['cases']] == [c['id'] for c in previous['cases']],
                'Original ordered cases changed')
        for key in ('gold_freeze_sha256', 'source_sha256'):
            require(result[key] == previous[key], 'Original measurement material changed: ' + key)
        previous_cases = {c['id']: c for c in previous['cases']}
        baseline_cases = {c['id']: c for c in baseline['cases']}
        rows, improvements, remaining = [], [], []
        for case in result['cases']:
            reference = previous_cases[case['id']]
            require([c['check'] for c in case['checks']] == reference['checks'], 'Check inventory changed')
            require(all(type(c['passed']) is bool for c in case['checks']), 'Untyped check flag')
            failed = [c['check'] for c in case['checks'] if c['passed'] is False]
            require(failed == [f['check'] for f in case['failures']]
                    and case['passed'] is (not failed) and not case['false_accepts'], 'Case outcome differs')
            allowed = {wire(failure) for failure in reference['allowed_failures']}
            require(all(wire(failure) in allowed for failure in case['failures']),
                    'New or changed failure requires a separate review: ' + case['id'])
            old_checks = {c['check']: c['passed'] for c in baseline_cases[case['id']]['checks']}
            require(all(c['passed'] or not old_checks[c['check']] for c in case['checks']),
                    'A previously passed check regressed: ' + case['id'])
            if case['passed'] and not baseline_cases[case['id']]['passed']:
                improvements.append(case['id'])
            if not case['passed']:
                remaining.append(case['id'])
            rows.append({'id': case['id'], 'checks': reference['checks'], 'allowed_failures': case['failures']})
        raw_path = path.parent / result['raw_log']['filename']
        raw = raw_path.read_bytes()
        require(sha256(raw).hexdigest() == result['raw_log']['sha256'], 'Raw journal digest changed')
        decoded = gzip.decompress(raw)
        require(decoded.endswith(b'\n'), 'Raw journal is truncated')
        require(all(json.loads(line) is not None for line in decoded.splitlines()), 'Incomplete JSONL')
        require(sum(c['check'].startswith('question:') for case in result['cases'] for c in case['checks'])
                == previous['question_total'], 'Question inventory changed')
        raw_identities = ([{'kind': r['kind'], 'id': r['id']} for r in result['raw_log']['record_inventory']]
                          if suite == 'construction' else [r['identity'] for r in result['raw_log']['records']])
        require(raw_identities == previous['raw_record_identities'], 'Complete raw record inventory changed')
        for source in (path, raw_path, path.with_suffix('.code.tar.gz')):
            save(destination / source.name, source.read_bytes())
        selected = destination / path.name
        policy['suites'][suite] = {
            'gold_freeze_sha256': result['gold_freeze_sha256'], 'source_sha256': result['source_sha256'],
            'total': 86, 'question_total': previous['question_total'], 'observed_passed': result['passed'],
            'strict_measurement': str(selected.relative_to(ROOT)),
            'strict_measurement_sha256': sha256(payload).hexdigest(),
            'raw_record_identities': raw_identities, 'cases': rows,
        }
        comparisons[suite] = {'before': baseline['passed'], 'after': result['passed'], 'total': 86,
                              'improved_cases': improvements, 'remaining_cases': remaining,
                              'new_failure_signatures': [], 'previously_passed_checks_preserved': True}
    output = FOLDER / 'regression_policy_v1.json'
    save(output, json.dumps(policy, ensure_ascii=False, sort_keys=True, indent=2).encode() + b'\n')
    save(destination / 'comparison.json', json.dumps(comparisons, ensure_ascii=False, sort_keys=True, indent=2).encode() + b'\n')
    print(json.dumps({'policy_sha256': sha256(output.read_bytes()).hexdigest(), 'comparison': comparisons}, ensure_ascii=False))


if __name__ == '__main__':
    main()
