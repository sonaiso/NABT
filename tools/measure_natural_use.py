"""Stage-wise measurements of the frozen, now-known linguistic diagnostic.

Never changes gold or sends expected labels to the runtime. A passing safety
gate is not a passing natural-use case. Imported reports are consistency-checked
measurements, not newly verified Lean receipts or deployment authorization.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from tools import benchmark_linguistic_truth as benchmark
from tools.lexical_testimony import _strict_json

SCHEMA = 'nabt.natural-use-measurement.v2'
LEGACY_REPORT = 'nabt.linguistic-truth.benchmark-result.v1'
CURRENT_REPORT = 'nabt.linguistic-truth.benchmark-result.v2'
LEGACY_OBSERVATION = 'nabt.lexical-occurrence-observation.v1'
CURRENT_OBSERVATION = 'nabt.lexical-occurrence-observation.v2'
REPORT_LIMIT = 20 * 1024 * 1024
CAUSES = {
    'M05': ['NEGATIVE_BAL_CORRECTION'],
    'M07': ['REPEATED_CUE_REFERENCE', 'SAME_CONTEXT_CONFLICT_LINK'],
    'M08': ['REPORTED_SPEAKER_SCOPE'],
    'M10': ['QUOTATION_SCOPE', 'CROSS_CLAUSE_INTENT_REFERENCE'],
    'H06': ['SOURCE_BOUND_SENSE_ALIAS'],
    'N01': ['ACCUSATIVE_FORM_RETRIEVAL', 'CONTEXT_LICENSE', 'FOCUS_OBSERVER_ASYMMETRY'],
    'N02': ['CONTEXT_LICENSE', 'INDEPENDENT_ORACLE_ADJUDICATION'],
    'N03': ['MISSING_READER_LEXICON_ENTRY', 'CONTEXT_LICENSE'],
    'N04': ['MISSING_READER_LEXICON_ENTRY', 'ATTACHMENT_AND_COREFERENCE_LICENSE'],
    'N05': ['MISSING_READER_LEXICON_ENTRY', 'ACCUSATIVE_FORM_RETRIEVAL', 'PRESERVE_AMBIGUITY'],
    'N06': ['ACCUSATIVE_FORM_RETRIEVAL', 'INTENT_VERB_AND_CONJUNCTION', 'SOURCE_BOUND_SENSE_ALIAS', 'NEGATION_SCOPE'],
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_report(path):
    path = Path(path)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rb') as stream:
        raw = stream.read(REPORT_LIMIT + 1)
    if len(raw) > REPORT_LIMIT:
        raise ValueError('REPORT_TOO_LARGE')
    return _strict_json(raw)


def _observation_contract(report):
    """A report version selects one observation law, never a caller's scorer."""
    schema = report.get('schema')
    if schema == LEGACY_REPORT:
        # Historical v1 did not declare a contract. An injected v2 declaration
        # must not silently reinterpret its observations or check outcomes.
        if 'observation_contract' in report:
            raise ValueError('CONTRADICTORY_OBSERVATION_CONTRACT')
        return LEGACY_OBSERVATION
    if schema == CURRENT_REPORT:
        if report.get('observation_contract') != CURRENT_OBSERVATION:
            raise ValueError('WRONG_OBSERVATION_CONTRACT')
        return CURRENT_OBSERVATION
    raise ValueError('WRONG_FROZEN_DIAGNOSTIC')


def _observation(raw, contract):
    if contract == CURRENT_OBSERVATION:
        if benchmark.OBSERVATION_CONTRACT != CURRENT_OBSERVATION:
            raise ValueError('INSTALLED_OBSERVATION_CONTRACT_CHANGED')
        return benchmark.observation(raw)
    if contract != LEGACY_OBSERVATION:
        raise ValueError('WRONG_OBSERVATION_CONTRACT')
    # Reconstruct the historical observer exactly: expression took precedence
    # over observed spelling, and no separate expression focus fallback existed.
    # The current scorer sees no expression field, so its additional fallback
    # cannot retroactively improve an archived v1 result.
    observed = benchmark.observation(raw)
    observed.pop('observation_contract', None)
    for original, item in zip(raw.get('occurrences', []), observed.get('occurrences', []), strict=True):
        item['surface'] = original.get('expression', original.get('surface',
            original.get('text', original.get('token', original.get('span', {}).get('raw_text', '')))))
        item.pop('expression', None)
    return observed


def _row_observation(row, contract):
    observed = _observation(row['raw_result'], contract)
    if row['id'] == 'B06':
        observed['metamorphic'] = row['scenario']['observation']
    return observed


def validate_report(report):
    gold = benchmark.load_gold()
    expected_ids = {c['id']: c for c in gold['cases']}
    contract = _observation_contract(report)
    if report.get('gold_sha256') != benchmark.GOLD_SHA256:
        raise ValueError('WRONG_FROZEN_DIAGNOSTIC')
    rows = report.get('rows')
    if type(rows) is not list or len(rows) != len(expected_ids):
        raise ValueError('MISSING_CASES')
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids) or set(ids) != set(expected_ids):
        raise ValueError('CASE_IDENTITY_CHANGED')
    for row in rows:
        if row['family'] != expected_ids[row['id']]['family'] or type(row['executed']) is not bool:
            raise ValueError('CASE_IDENTITY_CHANGED')
        checks = row['checks']
        if (len({c['name'] for c in checks}) != len(checks)
                or any(c['outcome'] not in {'PASS', 'FAIL', 'UNMEASURED'} for c in checks)
                or row['outcome'] != benchmark.case_outcome(checks)):
            raise ValueError('CONTRADICTORY_CHECKS')
        if row['executed']:
            obs = _row_observation(row, contract)
            if ((contract == CURRENT_OBSERVATION or 'observation' in row)
                    and canonical(row.get('observation')) != canonical(obs)):
                raise ValueError('OBSERVATION_DIFFERS_FROM_DECLARED_CONTRACT')
            if canonical(checks) != canonical(benchmark.evaluate(expected_ids[row['id']], obs)):
                raise ValueError('CHECKS_DIFFER_FROM_OBSERVATION')
    if canonical(report['summary']) != canonical(benchmark.summarize(rows)):
        raise ValueError('SUMMARY_DIFFERS_FROM_ROWS')
    execution = report['execution_evidence']
    integrity = benchmark.integrity_check(execution['before'], execution['after'])
    if canonical(execution['integrity']) != canonical(integrity):
        raise ValueError('CONTRADICTORY_EXECUTION_INTEGRITY')
    gate = benchmark.contract_gate(rows, report['summary'], integrity)
    if canonical(report['contract_gate']) != canonical(gate):
        raise ValueError('CONTRADICTORY_CONTRACT_GATE')
    return {r['id']: r for r in rows}


def ratio(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'fraction': numerator / denominator if denominator else None}


def natural_metrics(rows):
    selected = [r for r in rows.values() if r['family'] == 'natural_use_holdout']
    capture = all_candidates = native = source = candidate_hits = candidate_total = 0
    positive_ok = positive_total = ambiguous_ok = ambiguous_total = 0
    true_predictions = false_predictions = 0
    for row in selected:
        raw = row.get('raw_result', {})
        occurrences = raw.get('occurrences', [])
        capture += bool(occurrences)
        eligible = [o for o in occurrences if o.get('candidates')]
        native += bool(eligible) and all(o.get('native_checked') is True for o in eligible)
        expected_text = next(c for c in benchmark.load_gold()['cases'] if c['id'] == row['id'])['input']['text']
        blob = expected_text.encode()
        identity = raw.get('source', {})
        source += (identity.get('raw_text') == expected_text and type(identity.get('bytes')) is int
                   and identity['bytes'] == len(blob)
                   and identity.get('sha256') == hashlib.sha256(blob).hexdigest())
        checks = {c['name']: c for c in row['checks']}
        candidates = [c for name, c in checks.items() if name.startswith('candidate_recall.')]
        candidate_total += len(candidates)
        candidate_hits += sum(c['outcome'] == 'PASS' for c in candidates)
        all_candidates += bool(candidates) and all(c['outcome'] == 'PASS' for c in candidates)
        choice = checks.get('selected_senses')
        if choice:
            if choice['expected']:
                positive_total += 1
                positive_ok += choice['outcome'] == 'PASS'
            if choice['outcome'] != 'UNMEASURED':
                actual, expected = set(choice['actual']), set(choice['expected'])
                true_predictions += len(actual & expected)
                false_predictions += len(actual - expected)
        ambiguity = checks.get('semantics.ambiguous')
        if ambiguity:
            ambiguous_total += 1
            ambiguous_ok += ambiguity['outcome'] == 'PASS'
    count = len(selected)
    return {
        'full_case_success': ratio(sum(r['outcome'] == 'PASS' for r in selected), count),
        'any_lexical_occurrence': ratio(capture, count),
        'all_required_candidate_cases': ratio(all_candidates, count),
        'required_candidate_obligations': ratio(candidate_hits, candidate_total),
        'positive_intended_selection': ratio(positive_ok, positive_total),
        'required_ambiguity_preserved': ratio(ambiguous_ok, ambiguous_total),
        'native_checked_candidate_cases': ratio(native, count),
        'source_identity_preserved': ratio(source, count),
        'selection_precision': ratio(true_predictions, true_predictions + false_predictions),
        'false_selected_senses': false_predictions,
        'precision_note': 'No selections gives null precision, not 100%; abstention does not pass positive cases.',
    }


def measure(before, after):
    old, new = validate_report(before), validate_report(after)
    before_contract, after_contract = _observation_contract(before), _observation_contract(after)
    expected_ids = {c['id']: c for c in benchmark.load_gold()['cases']}
    # Counterfactual measurement holds every old runtime byte/result fixed and
    # applies only the after-observer. It is not a new runtime or semantic gain.
    rescored = deepcopy(old)
    observation_changes = []
    for identifier, row in rescored.items():
        if not row['executed']:
            continue
        row['observation'] = _row_observation(row, after_contract)
        row['checks'] = benchmark.evaluate(expected_ids[identifier], row['observation'])
        row['outcome'] = benchmark.case_outcome(row['checks'])
        prior_checks = {check['name']: check for check in old[identifier]['checks']}
        for check in row['checks']:
            if canonical(check) != canonical(prior_checks[check['name']]):
                observation_changes.append({'id': identifier, 'check': check['name'],
                    'before': prior_checks[check['name']], 'after': check})
    changes, failures = [], []
    for identifier, prior in old.items():
        current = new[identifier]
        if current['outcome'] != prior['outcome']:
            same_runtime = (canonical(prior.get('raw_result')) == canonical(current.get('raw_result'))
                            and canonical(prior.get('scenario')) == canonical(current.get('scenario'))
                            and prior['executed'] == current['executed'])
            changes.append({'id': identifier, 'before': prior['outcome'], 'after': current['outcome'],
                'raw_runtime_result_changed': not same_runtime,
                'attribution': ('OBSERVATION_CONTRACT_ONLY' if same_runtime and before_contract != after_contract
                                else 'RUNTIME_RESULT_AND_OBSERVATION_CONTRACT' if before_contract != after_contract
                                else 'RUNTIME_RESULT_OR_MEASUREMENT_CHANGE'),
                'semantic_improvement_established': False})
        if prior['outcome'] == 'FAIL':
            failures.append({'id': identifier, 'family': prior['family'],
                             'before': prior['outcome'], 'after': current['outcome'],
                             'reviewed_causes': CAUSES.get(identifier, ['NEEDS_DIAGNOSIS']),
                             'remaining_failed_checks': [c['name'] for c in current['checks'] if c['outcome'] == 'FAIL']})
    return {'schema': SCHEMA, 'gold_sha256': benchmark.GOLD_SHA256,
            'evaluation_role': 'KNOWN_REGRESSION_NOT_NEW_BLIND_EVALUATION',
            'before_report_schema': before['schema'], 'after_report_schema': after['schema'],
            'before_observation_contract': before_contract, 'after_observation_contract': after_contract,
            'observation_contract_comparison': {
                'contract_changed': before_contract != after_contract,
                'runtime_executed_for_counterfactual': False,
                'before_raw_results_unchanged': True,
                'changed_checks': observation_changes,
                'changed_check_count': len(observation_changes),
                'changed_case_count': sum(old[key]['outcome'] != row['outcome'] for key, row in rescored.items()),
                'before_raw_under_after_observer': natural_metrics(rescored),
                'semantic_improvement_established': False},
            'before_measured_at': before['measured_at_utc'], 'after_measured_at': after['measured_at_utc'],
            'before_summary': before['summary'], 'after_summary': after['summary'],
            'natural_before': natural_metrics(old), 'natural_after': natural_metrics(new),
            'changed_cases': changes, 'original_failures': failures,
            'regressions': [c for c in changes if c['before'] == 'PASS' and c['after'] != 'PASS'],
            'after_execution_integrity': after['execution_evidence']['integrity'],
            'after_contract_gate': after['contract_gate'],
            'all_arabic_complete': False,
            'scope': 'Six known authored examples, partly unvowelized; no population accuracy or new production input policy.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', required=True, type=Path)
    parser.add_argument('--after', type=Path, help='Read an existing run instead of executing the frozen diagnostic')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--save-run', type=Path, help='Retain full executed report as reproducible gzip')
    args = parser.parse_args()
    before = read_report(args.before)
    after = read_report(args.after) if args.after else benchmark.run()
    result = measure(before, after)
    result['report_artifacts'] = {'before_sha256': digest(args.before),
                                'after_sha256': digest(args.after) if args.after else None}
    if args.save_run:
        args.save_run.parent.mkdir(parents=True, exist_ok=True)
        args.save_run.write_bytes(gzip.compress((canonical(after) + '\n').encode(), mtime=0))
        result['report_artifacts']['after_sha256'] = digest(args.save_run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'changed_cases': result['changed_cases'], 'natural_after': result['natural_after'],
                      'regressions': result['regressions']}, ensure_ascii=False))
    return 0 if (not result['regressions'] and result['after_contract_gate']['passed'] is True
                 and result['after_execution_integrity']['valid'] is True) else 2


if __name__ == '__main__':
    raise SystemExit(main())
