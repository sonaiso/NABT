#!/usr/bin/env python3
"""CPU hard-negative proposal ranking. Only native Lean accepts certificates.

This secondary development experiment keeps all candidates and changes only
proposal order. The held-out mutation family is not a blind Arabic benchmark.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import train_certificate_ranker as prior
from tools import verified_reading as ground

FEATURES = prior.FEATURES + ['law_equal', 'proof_indices_in_bounds']
TRAIN_KINDS = ['bad_step_index', 'wrong_law', *prior.KINDS]
VALIDATION_KINDS = ['bad_clean_step_index', *TRAIN_KINDS]
SCHEMA = 'nabt.certificate-ranker.v2'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def mutate(certificate, kind):
    value = deepcopy(certificate)
    if kind in prior.KINDS:
        return dict(prior.candidates(certificate))[kind]
    if kind == 'wrong_law':
        value['law_id'] = 'nabt.uninstalled-law.v0'
    elif kind in {'bad_step_index', 'bad_clean_step_index'}:
        trace = 'steps' if kind == 'bad_step_index' else 'clean_steps'
        known = 'known' if trace == 'steps' else 'clean_known'
        if value[trace]:
            value[trace][0]['index'] = 1048576
        else:
            # Keep the old length feature unchanged, including empty closures.
            value[trace].append({'kind': 'fact', 'index': 1048576})
            value[known].append(deepcopy(value['query']))
    else:
        raise ValueError('unknown mutation')
    return value


def indices_in_bounds(certificate):
    """Syntactic index bounds only: not proof checking or semantic truth."""
    try:
        clauses = certificate['clauses']
        if type(clauses) is not list:
            return False
        bounds = {kind: sum(type(c) is dict and c.get('kind') == kind for c in clauses)
                  for kind in ('fact', 'rule')}
        for field in ('steps', 'clean_steps'):
            if type(certificate[field]) is not list:
                return False
            for step in certificate[field]:
                if type(step) is not dict or step.get('kind') not in bounds:
                    return False
                n = step.get('index')
                if type(n) is not int or not 0 <= n < bounds[step['kind']]:
                    return False
        return True
    except (KeyError, TypeError):
        return False


def features(source, query, certificate):
    try:
        old = prior.features(source, query, certificate)
    except (KeyError, TypeError, AttributeError, UnicodeError):
        old = [0.0] * len(prior.FEATURES)
    return old + [float(type(certificate) is dict and certificate.get('law_id') == ground.LAW_ID),
                  float(indices_in_bounds(certificate))]


def fit(rows, *, epochs, learning_rate, seed):
    if type(epochs) is not int or not 1 <= epochs <= 10000:
        raise ValueError('epoch limit')
    if type(learning_rate) not in (int, float) or not math.isfinite(learning_rate) or not 0 < learning_rate <= 1:
        raise ValueError('learning rate')
    if type(seed) is not int:
        raise ValueError('seed type')
    if not rows or any(r.get('measurement') != 'MEASURED' or type(r.get('label')) is not int
                       or r['label'] not in (0, 1) for r in rows):
        raise ValueError('only native measured certificate labels may train')
    if any(type(r['features']) is not list or len(r['features']) != len(FEATURES)
           or any(type(x) not in (int, float) or not math.isfinite(x) for x in r['features']) for r in rows):
        raise ValueError('invalid feature vector')
    weights = [0.0] * len(FEATURES)
    order = list(range(len(rows))); rng = random.Random(seed); history = []
    for epoch in range(epochs):
        rng.shuffle(order)
        for index in order:
            row = rows[index]
            z = max(-40, min(40, prior.score(weights, row['features'])))
            error = 1 / (1 + math.exp(-z)) - row['label']
            for i, value in enumerate(row['features']):
                weights[i] -= learning_rate * error * value
        loss = sum(max(prior.score(weights,r['features']),0) - r['label']*prior.score(weights,r['features'])
                   + math.log1p(math.exp(-abs(prior.score(weights,r['features'])))) for r in rows)/len(rows)
        history.append({'epoch':epoch+1,'log_loss':loss})
    return weights, history


def rank_and_check(source, query, proposals, model, checker):
    """All proposals are freshly checked. Missing measurements block selection."""
    if type(proposals) is not list or not 1 <= len(proposals) <= 16:
        raise ValueError('proposal count')
    if type(model) is not dict or model.get('schema') != SCHEMA or model.get('features') != FEATURES or model.get('authority') != 'proposal-order-only':
        raise ValueError('model contract')
    weights = model.get('weights')
    if type(weights) is not list or len(weights) != len(FEATURES) or any(type(w) not in (int,float) or not math.isfinite(w) for w in weights):
        raise ValueError('weights')
    order = prior.ranked_indices(weights, [features(source,query,p) for p in proposals])
    attempts = [{'original_index':i,**prior.check(source,query,proposals[i],checker)} for i in order]
    measured = all(a['measurement'] == 'MEASURED' for a in attempts)
    accepted = [a for a in attempts if a['label'] == 1]
    selected = accepted[0] if measured and accepted and len({a['semantic_status'] for a in accepted}) == 1 else None
    return {'schema':'nabt.ranked-certificate-replay.v2','candidate_order':order,'attempts':attempts,
            'all_attempts_measured':measured,'selected_original_index':selected['original_index'] if selected else None,
            'semantic_status':selected['semantic_status'] if selected else None,
            'linguistic_reading_completeness':False,'world_truth_established':False,'authority':'native-checks-only'}


def execute(protocol_path, output, checker):
    protocol_raw = protocol_path.read_bytes(); p = json.loads(protocol_raw)
    if p['features'] != FEATURES or p['train_candidate_kinds'] != TRAIN_KINDS or p['validation_candidate_kinds'] != VALIDATION_KINDS:
        raise ValueError('protocol drift')
    source_path=ROOT/'evidence/explainable_pilot/cases.json'
    source_raw=source_path.read_bytes()
    if digest(source_raw) != p['cases_sha256']:
        raise ValueError('case fixture drift')
    old_path=ROOT/'evidence/training_readiness/integrated_run/model.json'
    if digest(old_path.read_bytes()) != p['prior_model_sha256']:
        raise ValueError('baseline weight drift')
    output.mkdir(parents=True,exist_ok=False)
    (output/'protocol.json').write_bytes(protocol_raw)
    source=json.loads(source_raw); definitions=source['cases']+source['ablations']
    if not set(p['validation_case_ids']) <= {x['id'] for x in definitions}:
        raise ValueError('unknown validation id')
    rows=[]; inputs=[]; started=time.perf_counter()
    for case in definitions:
        raw=(ROOT/case['source_path']).read_bytes() if 'source_path' in case else case['source'].encode()
        query=(ROOT/case['query_path']).read_bytes() if 'query_path' in case else case['query'].encode()
        split='validation' if case['id'] in p['validation_case_ids'] else 'train'
        certificate=ground.propose(raw,query)
        inputs.append({'id':case['id'],'source':raw.decode(),'query':query.decode(),'split':split,'authored_expected':case['expected']})
        for kind in (TRAIN_KINDS if split=='train' else VALIDATION_KINDS):
            proposal=mutate(certificate,kind)
            row={'case_id':case['id'],'kind':kind,'split':split,'source_sha256':digest(raw),
                 'certificate':proposal,'features':features(raw,query,proposal),**prior.check(raw,query,proposal,checker)}
            rows.append(row)
    write(output/'inputs.json',inputs)
    (output/'candidates.jsonl').write_text(''.join(prior.wire(r)+'\n' for r in rows))
    train=[r for r in rows if r['split']=='train']; validation=[r for r in rows if r['split']=='validation']
    overlap={r['source_sha256'] for r in train}&{r['source_sha256'] for r in validation}
    expected={c['id']:c['expected'] for c in definitions}
    gate=not overlap and all(r['measurement']=='MEASURED' and r['label']==int(r['kind']=='original') for r in rows)
    gate=gate and all(r['semantic_status']==expected[r['case_id']] for r in rows if r['kind']=='original')
    result={'schema':'nabt.certificate-ranker-v2-run.v1','created_utc':datetime.now(timezone.utc).isoformat(),
            'protocol_sha256':digest(protocol_raw),'code_sha256':digest(Path(__file__).read_bytes()),
            'base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'native_sha256':prior.pilot.file_sha(prior.pilot.checker_path(checker)),
            'planned_candidates':len(rows),'train_candidates':len(train),'validation_candidates':len(validation),
            'exact_source_overlap':sorted(overlap),'native_label_gate':gate,'training_executed':False,
            'test_status':'SECONDARY_DEVELOPMENT_WITH_HELD_OUT_CLEAN_TRACE_MUTATION','authority':'proposal-order-only',
            'all_arabic_complete':False,'world_truth_established':False,'runtime_acceptance_changed':False}
    if gate:
        weights,curve=fit(train,**p['optimizer'])
        model={'schema':SCHEMA,'features':FEATURES,'weights':weights,'authority':'proposal-order-only',
               'protocol_sha256':digest(protocol_raw),'training_rows_sha256':digest(prior.wire(train).encode())}
        write(output/'model.json',model);write(output/'curve.json',curve)
        old=json.loads(old_path.read_text())['weights']+[0.0,0.0]
        result['metrics']={name:prior.summarize(validation,w) for name,w in [('fixed_input_order',[0.0]*len(FEATURES)),('prior_v1',old),('trained_v2',weights)]}
        replays=[]
        for item in inputs:
            if item['split']!='validation':continue
            proposals=[r['certificate'] for r in validation if r['case_id']==item['id']]
            replays.append({'case_id':item['id'],**rank_and_check(item['source'].encode(),item['query'].encode(),proposals,model,checker)})
        write(output/'inference_replay.json',replays)
        result.update(training_executed=True,selected_statuses_match=all(r['semantic_status']==expected[r['case_id']] for r in replays),
                      fresh_replay_attempts=sum(len(r['attempts']) for r in replays))
    result['duration_seconds']=time.perf_counter()-started
    write(output/'RESULTS.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--protocol',type=Path,default=ROOT/'evidence/certificate_ranker_v2/protocol.json')
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--checker',type=Path,default=ROOT/'formal/.lake/build/bin/verifiedReading')
    args=p.parse_args();result=execute(args.protocol,args.output_dir,args.checker)
    print(json.dumps({k:v for k,v in result.items() if k!='metrics'},ensure_ascii=False,indent=2))
    return 0 if result['training_executed'] and result['selected_statuses_match'] else 1

if __name__=='__main__':raise SystemExit(main())
