#!/usr/bin/env python3
"""Train a tiny CPU proposal ranker; Lean alone judges each original certificate.

This is a public development experiment, not LoRA, Arabic acquisition, RLVR,
or a replacement for the existing deterministic proposer. No external packages.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import explainable_pilot as pilot
from tools import verified_reading as ground
from tools.training_readiness import digest, intake, machine

PROTOCOL = ROOT / 'evidence/training_readiness/protocol.json'
CASES = ROOT / 'evidence/explainable_pilot/cases.json'
FEATURES = ['bias', 'source_equal', 'query_equal', 'identity_equal', 'revision_equal',
            'scope_equal', 'clause_count_equal', 'trace_size_equal', 'clean_trace_size_equal']
KINDS = ('changed_source', 'changed_query', 'changed_identity', 'extra_clause', 'original')


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def strict_receipt(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def bad(_):
        raise ValueError('noncanonical numeric token')
    def integer(token):
        if not token.isascii() or not token.isdigit():
            return bad(token)
        return int(token)
    if len(raw) > 4 * 1048576:
        raise ValueError('receipt too large')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                       parse_int=integer, parse_float=bad, parse_constant=bad)
    wire(value).encode('utf-8')
    if type(value) is not dict:
        raise ValueError('receipt must be object')
    return value


def check(raw, query, certificate, checker, *, identity='text', revision='1', scope='default', timeout=20):
    """Separate kernel rejection from outages, crashes and budgets.

    No model-supplied label, score, source path or truth flag is consulted.
    Failed measurements cannot provide positive *or negative* training rewards.
    """
    foundation.require_foundation('tools.train_certificate_ranker.check')
    start = time.perf_counter()
    row = {'measurement': 'UNMEASURED', 'label': None, 'semantic_status': None, 'error': None}
    try:
        pilot.validate_inputs(raw, query, identity, revision, scope, timeout)
        encoded = wire(certificate).encode('utf-8')
        if len(encoded) > 1048576:
            raise pilot.PilotError('RESOURCE_LIMIT', 'certificate size')
        binary = pilot.checker_path(checker)
        fingerprint = pilot.file_sha(binary)
        with tempfile.TemporaryDirectory() as temp:
            paths = [Path(temp) / n for n in ('source', 'query', 'certificate')]
            for path, data in zip(paths, (raw, query, encoded), strict=True):
                path.write_bytes(data)
            run = subprocess.run([str(binary), *map(str, paths), identity, revision, scope],
                                 capture_output=True, timeout=timeout)
        if pilot.file_sha(binary) != fingerprint:
            raise pilot.PilotError('CHECKER_CHANGED', 'checker changed')
        receipt = strict_receipt(run.stdout)
        common = {'law_id': ground.LAW_ID, 'scope': 'canonical_ground_source_entailment',
                  'world_truth_established': False, 'all_arabic_complete': False}
        if any(wire(receipt.get(k)) != wire(v) for k, v in common.items()):
            raise pilot.PilotError('CHECKER_PROTOCOL_ERROR', 'receipt scope differs')
        if run.returncode == 0 and receipt.get('verified') is True:
            expected = {'source_id': identity, 'revision': revision, 'source_scope': scope,
                        'source_text': raw.decode(), 'query_text': query.decode()}
            if any(wire(receipt.get(k)) != wire(v) for k, v in expected.items()) or receipt.get('status') not in pilot.STATUSES:
                raise pilot.PilotError('CHECKER_PROTOCOL_ERROR', 'receipt input differs')
            row.update(measurement='MEASURED', label=1, semantic_status=receipt['status'])
        elif run.returncode == 1 and receipt.get('verified') is False and receipt.get('error') in {'CERTIFICATE_REJECTED', 'INVALID_INPUT'}:
            row.update(measurement='MEASURED', label=0, error=receipt['error'])
        else:
            row['error'] = 'RESOURCE_LIMIT' if receipt.get('error') == 'RESOURCE_LIMIT' else 'CHECKER_EXECUTION_ERROR'
        row.update(checker_sha256=fingerprint, receipt=receipt, exit_code=run.returncode)
    except pilot.PilotError as exc:
        row['error'] = exc.code
    except subprocess.TimeoutExpired:
        row['error'] = 'RESOURCE_LIMIT'
    except OSError:
        row['error'] = 'CHECKER_UNAVAILABLE'
    except (ValueError, TypeError, RecursionError):
        row['error'] = 'INVALID_INPUT_OR_RECEIPT'
    row['elapsed_seconds'] = time.perf_counter() - start
    return row


def candidates(certificate):
    changes = [
        lambda c: c['source'].update(text=c['source']['text'] + 'سالم هو مخترع.\n'),
        lambda c: c.update(query_text='هل سالم هو مخترع؟\n'),
        lambda c: c['source'].update(identity='other'),
        lambda c: c['clauses'].append(deepcopy(c['clauses'][0])),
        lambda c: None,
    ]
    for kind, change in zip(KINDS, changes, strict=True):
        altered = deepcopy(certificate)
        change(altered)
        yield kind, altered


def features(raw, query, certificate):
    """Cheap visible proposal consistency only; no labels/native results as inputs."""
    source = certificate['source']
    return [1.0, float(source['text'].encode() == raw), float(certificate['query_text'].encode() == query),
            float(source['identity'] == 'text'), float(source['revision'] == '1'),
            float(source['scope'] == 'default'), float(len(certificate['clauses']) == raw.count(b'.\n')),
            float(len(certificate['known']) == len(certificate['steps'])),
            float(len(certificate['clean_known']) == len(certificate['clean_steps']))]


def score(weights, vector):
    return sum(a*b for a, b in zip(weights, vector, strict=True))


def fit(rows, *, epochs=120, learning_rate=0.1, seed=19):
    """Binary logistic SGD. Refuse unavailable labels, including false/true as ints."""
    if type(epochs) is not int or not 1 <= epochs <= 10000:
        raise ValueError('invalid epoch count')
    if type(learning_rate) not in (int, float) or not math.isfinite(learning_rate) or not 0 < learning_rate <= 1:
        raise ValueError('invalid learning rate')
    if not rows or any(r['measurement'] != 'MEASURED' or type(r['label']) is not int or r['label'] not in (0, 1) for r in rows):
        raise ValueError('only independently measured labels may train')
    weights = [0.0] * len(FEATURES)
    rng = random.Random(seed)
    order = list(range(len(rows)))
    history = []
    for epoch in range(epochs):
        rng.shuffle(order)
        for index in order:
            row = rows[index]
            z = max(-40, min(40, score(weights, row['features'])))
            error = 1 / (1 + math.exp(-z)) - row['label']
            for j, value in enumerate(row['features']):
                weights[j] -= learning_rate * error * value
        loss = sum(max(score(weights, r['features']), 0) - r['label'] * score(weights, r['features']) +
                   math.log1p(math.exp(-abs(score(weights, r['features'])))) for r in rows) / len(rows)
        history.append({'epoch': epoch + 1, 'log_loss': loss})
    return weights, history


def ranked_indices(weights, vectors):
    # A permutation preserves every candidate, including ties and bad scores.
    scores = [score(weights, x) for x in vectors]
    if any(not math.isfinite(x) for x in scores):
        raise ValueError('nonfinite rank score')
    return sorted(range(len(vectors)), key=lambda i: (-scores[i], i))


def rank_and_check(raw, query, proposals, model, checker):
    """Reusable inference boundary: learned order, fresh native decisions.

    This pool contains competing certificates for ONE canonical reading. It
    does not stand for the free reader's linguistic alternatives. An unavailable
    measurement blocks selection; no ranked score is an entailment receipt.
    """
    foundation.require_foundation('tools.train_certificate_ranker.rank_and_check')
    if type(proposals) is not list or not 1 <= len(proposals) <= 16:
        raise ValueError('expected 1..16 certificate proposals')
    if type(model) is not dict or model.get('schema') != 'nabt.certificate-ranker.v1' or model.get('features') != FEATURES or model.get('authority') != 'proposal-order-only':
        raise ValueError('unsupported ranker contract')
    weights = model.get('weights')
    if type(weights) is not list or len(weights) != len(FEATURES) or any(type(w) not in (int, float) or not math.isfinite(w) for w in weights):
        raise ValueError('invalid weights')
    vectors = []
    for certificate in proposals:
        try:
            vectors.append(features(raw, query, certificate))
        except (KeyError, TypeError, AttributeError, UnicodeError):
            vectors.append([0.0] * len(FEATURES))
    order = ranked_indices(weights, vectors)
    attempts = [{'original_index': index, **check(raw, query, proposals[index], checker)} for index in order]
    accepted = [a for a in attempts if a['label'] == 1]
    complete = all(a['measurement'] == 'MEASURED' for a in attempts)
    statuses = {a['semantic_status'] for a in accepted}
    selected = accepted[0]['original_index'] if complete and accepted and len(statuses) == 1 else None
    return {'schema': 'nabt.ranked-certificate-replay.v1', 'attempts': attempts,
            'selected_original_index': selected,
            'semantic_status': accepted[0]['semantic_status'] if selected is not None else None,
            'all_attempts_measured': complete, 'linguistic_reading_completeness': False,
            'world_truth_established': False}


def summarize(rows, weights):
    groups = {}
    for row in rows:
        groups.setdefault(row['case_id'], []).append(row)
    ordered = []
    for identity, group in groups.items():
        indices = ranked_indices(weights, [r['features'] for r in group])
        measured = all(r['measurement'] == 'MEASURED' for r in group)
        accepted = [i for i in indices if group[i]['label'] == 1]
        ordered.append({'case_id': identity, 'candidate_order': [group[i]['kind'] for i in indices],
                        'measurement': 'MEASURED' if measured else 'UNMEASURED',
                        'first_accepted_rank': indices.index(accepted[0]) + 1 if measured and accepted else None,
                        'top1_accepted': group[indices[0]]['label'] == 1 if measured else None})
    measured = [r for r in ordered if r['measurement'] == 'MEASURED']
    return {'planned_groups': len(groups), 'measured_groups': len(measured),
            'unmeasured_groups': len(groups) - len(measured),
            'top1_accepted': sum(r['top1_accepted'] for r in measured),
            'top1_rate': sum(r['top1_accepted'] for r in measured) / len(measured) if measured else None,
            'mean_first_accepted_rank': sum(r['first_accepted_rank'] for r in measured) / len(measured) if measured and all(r['first_accepted_rank'] is not None for r in measured) else None,
            'groups': ordered}


def execute(output, checker):
    # Refuse replacement *before* any compute, preserving first-run evidence.
    foundation.require_foundation('tools.train_certificate_ranker.execute')
    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(PROTOCOL.read_bytes())
    if protocol['candidate_kinds'] != list(KINDS):
        raise ValueError('candidate protocol differs from implementation')
    material = json.loads(CASES.read_bytes())
    definitions = material['cases'] + material['ablations']
    if set(protocol['validation_case_ids']) - {c['id'] for c in definitions}:
        raise ValueError('unknown preregistered validation case')
    rows = []
    inputs = []
    for case in definitions:
        raw = (ROOT / case['source_path']).read_bytes() if 'source_path' in case else case['source'].encode()
        query = (ROOT / case['query_path']).read_bytes() if 'query_path' in case else case['query'].encode()
        split = 'validation' if case['id'] in protocol['validation_case_ids'] else 'train'
        inputs.append({'id': case['id'], 'source_utf8': raw.decode(), 'query_utf8': query.decode(),
                       'source_sha256': digest(raw), 'query_sha256': digest(query), 'split': split,
                       'authored_expected_status': case['expected']})
        try:
            proposed = ground.propose(raw, query)
            variants = list(candidates(proposed))
        except (ValueError, pilot.NabtError):
            variants = [(kind, None) for kind in KINDS]
        for kind, certificate in variants:
            result = check(raw, query, certificate, checker) if certificate is not None else {
                'measurement': 'UNMEASURED', 'label': None, 'semantic_status': None, 'error': 'PROPOSER_ERROR', 'elapsed_seconds': 0}
            row = {'case_id': case['id'], 'kind': kind, 'split': split,
                   'source_sha256': digest(raw), 'query_sha256': digest(query),
                   'certificate': certificate, 'certificate_sha256': digest(wire(certificate).encode()),
                   'features': features(raw, query, certificate) if certificate is not None else None, **result}
            rows.append(row)
            with (output / 'candidates.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(wire(row) + '\n')
    training = [r for r in rows if r['split'] == 'train']
    validation = [r for r in rows if r['split'] == 'validation']
    overlap = {r['source_sha256'] for r in training} & {r['source_sha256'] for r in validation}
    setup_passed = not overlap and all(r['measurement'] == 'MEASURED' and
        r['label'] == int(r['kind'] == 'original') for r in rows)
    # Gold status assertions were authored before the experiment, not obtained
    # by converting verifier output into independent truth labels.
    expected = {c['id']: c['expected'] for c in definitions}
    status_match = all(r['semantic_status'] == expected[r['case_id']] for r in rows if r['kind'] == 'original')
    model = None
    learning = []
    timings = {'training_seconds': None}
    summaries = None
    inference_replays = []
    if setup_passed and status_match:
        start = time.perf_counter()
        weights, learning = fit(training, **protocol['optimizer'])
        timings['training_seconds'] = time.perf_counter() - start
        model = {'schema': 'nabt.certificate-ranker.v1', 'features': FEATURES, 'weights': weights,
                 'authority': 'proposal-order-only', 'protocol_sha256': digest(PROTOCOL.read_bytes()),
                 'training_rows_sha256': digest(wire(training).encode())}
        summaries = {split: {'trained': summarize(part, weights),
                             'fixed_input_order': summarize(part, [0.0] * len(FEATURES))}
                     for split, part in [('train', training), ('validation', validation)]}
        for item in inputs:
            if item['split'] != 'validation':
                continue
            proposals = [r['certificate'] for r in validation if r['case_id'] == item['id']]
            replay = rank_and_check(item['source_utf8'].encode(), item['query_utf8'].encode(), proposals, model, checker)
            inference_replays.append({'case_id': item['id'], **replay})
    times = sorted(r['elapsed_seconds'] for r in rows)
    timings.update(native_attempt_p50_seconds=times[(len(times)-1)//2],
                   native_attempt_p95_seconds=times[math.ceil(0.95*len(times))-1],
                   planned_attempts=len(rows))
    result = {'schema': 'nabt.training-run.v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'experiment': 'public-development-certificate-ranking',
              'base_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'protocol_sha256': digest(PROTOCOL.read_bytes()), 'cases_sha256': digest(CASES.read_bytes()),
              'code_sha256': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in
                              [Path(__file__), ROOT / 'tools/training_readiness.py', ROOT / 'tools/verified_reading.py', ROOT / 'tools/explainable_pilot.py']},
              'environment': machine(), 'timing': timings,
              'planned_examples': len(rows), 'planned_source_cases': len(definitions),
              'measurements': dict(Counter(r['measurement'] for r in rows)),
              'labels': dict(Counter(str(r['label']) for r in rows)),
              'original_status_matches_authored_expectations': status_match,
              'exact_source_overlap': sorted(overlap), 'metrics': summaries,
              'training_executed': model is not None,
              'passed': setup_passed and status_match and all(
                  r['all_attempts_measured'] and r['selected_original_index'] == len(KINDS)-1 and
                  r['semantic_status'] == expected[r['case_id']] for r in inference_replays),
              'limits': {'all_arabic_complete': False, 'world_truth_established': False,
                         'arabic_acquisition_measured': False, 'independent_held_out_measured': False,
                         'root_ood_measured': False, 'template_ood_measured': False,
                         'lora_executed': False, 'rlvr_executed': False, 'neural_model_measured': False,
                         'improvement_over_current_proposer_measured': False},
              'current_proposer_baseline': 'One already valid proposal per case; ranking an adversarial pool cannot establish an improvement over this proposer.'}
    for name, value in [('run.json', result), ('inputs.json', inputs), ('model.json', model),
                        ('learning_curve.json', learning), ('intake_queue.json', intake()),
                        ('inference_replay.json', inference_replays)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--checker', type=Path)
    args = parser.parse_args()
    result = execute(args.output_dir.resolve(), args.checker)
    print(wire({k: result[k] for k in ('planned_examples', 'measurements', 'training_executed', 'passed')}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
