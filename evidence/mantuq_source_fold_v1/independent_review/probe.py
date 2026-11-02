"""Independent handwritten source/corruption probes; no checker mocks."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

REPO = Path('/workspace/scratch/84dbb26f30e1/NABT-mantuq-source-fold')
sys.path.insert(0, str(REPO))
from tools.mantuq_inference.source_bound import evaluate_source
from tools.mantuq_inference.source_fold import (
    fold_source, unfold_source, verify_fold, bounded_wire, strict_input,
    FOLD_DOMAIN, PAYLOAD_SCHEMA,
)
from tools.mantuq_inference.evaluator import EvaluationBudget
from tools.explainable_pilot import PilotError

OUT = Path('/tmp/nabt-source-fold-review')
BIN = Path('/tmp/nabt-lean-native-build/formal/.lake/build/bin')
OPTIONS = dict(checker=BIN/'verifiedReading', semantic_probe=BIN/'classicalSemanticProbe',
               source_id='independent_review', revision='1', scope='review')
QUERY = 'هل زيد هو مقبول؟\n'.encode()

def atom(name, positive=True):
    return dict(predicate=name, arguments=['زيد'], positive=positive)

def plan(index):
    return dict(schema='nabt.mantuq-source-plan.v1', policy_id='guarded_cause',
                bridge_clause=f'c{index}', requirements=[
                    dict(slot='cause', atom=atom('منبه')),
                    dict(slot='condition', atom=atom('مستوف')),
                    dict(slot='blockerAbsence', atom=atom('محظور', False)),
                ])

RULE = 'إذا زيد هو منبه و زيد هو مستوف و ليس زيد هو محظور فإن زيد هو مقبول.\n'
CLEAN = ('زيد هو منبه.\nزيد هو مستوف.\nليس زيد هو محظور.\n' + RULE).encode()
DIRTY = ('زيد هو أصل.\nليس زيد هو أصل.\nإذا زيد هو أصل فإن زيد هو منبه.\n'
         'زيد هو مستوف.\nليس زيد هو محظور.\n' + RULE).encode()
ALTERNATE = DIRTY + 'زيد هو منبه.\n'.encode()
OPPOSED = CLEAN + 'ليس زيد هو مقبول.\n'.encode()
rows = []

def reject(name, fn, expected=None):
    try:
        fn()
        row = dict(name=name, rejected=False)
    except PilotError as e:
        row = dict(name=name, rejected=True, code=e.code)
    if expected is not None:
        row['expected_code'] = expected
        row['matches'] = row.get('code') == expected
    rows.append(row)

files = ['tools/mantuq_inference/source_bound.py', 'tools/mantuq_inference/source_fold.py',
         'tools/mantuq_inference/__main__.py', 'tools/mantuq_inference/evaluator.py',
         'tools/mantuq_mafhum.py', 'tools/source_semantics.py']
before = {p: hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in files}

for name, raw, p, wanted in [
    ('clean', CLEAN, plan(3), 'SUPPORTED'),
    ('contested_ancestor', DIRTY, plan(5), 'DEFER'),
    ('independent_clean_support', ALTERNATE, plan(5), 'SUPPORTED'),
    ('opposed_conclusion', OPPOSED, plan(3), 'CONFLICT'),
]:
    result = evaluate_source(raw, QUERY, p, **OPTIONS)
    (OUT/f'{name}-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    (OUT/f'{name}-source.txt').write_bytes(raw)
    rows.append(dict(name=name, status=result['status'], reason=result['reason'],
                     conditional=result['conditional_consequence'], expected_status=wanted,
                     matches=result['status']==wanted,
                     source_status=(result.get('source_answer') or {}).get('status')))

packet = fold_source(CLEAN, QUERY, plan(3), **OPTIONS)
(OUT/'packet.json').write_bytes(bounded_wire(packet, 17*1048576))
restored = unfold_source(packet)
canonical = json.dumps({'schema': PAYLOAD_SCHEMA, 'domain': FOLD_DOMAIN, 'result': restored},
                       ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
rows.append(dict(name='sentinel_integer_identity', matches=int(packet['number_hex'], 16) ==
                 int.from_bytes(b'\x01'+canonical, 'big'), payload_bytes=len(canonical)))
verified = verify_fold(CLEAN, QUERY, plan(3), packet, **OPTIONS)
rows.append(dict(name='positive_replay', result=verified, matches=verified['verified'] is True))

reject('changed_revision', lambda: verify_fold(CLEAN, QUERY, plan(3), packet,
    **{**OPTIONS, 'revision': '2'}), 'FOLD_REJECTED')
reject('changed_unused_budget', lambda: verify_fold(CLEAN, QUERY, plan(3), packet,
    budget=EvaluationBudget(max_hypotheses=129), **OPTIONS), 'FOLD_REJECTED')
reject('changed_unused_source', lambda: verify_fold(CLEAN+'زيد هو زائد.\n'.encode(), QUERY,
    plan(3), packet, **OPTIONS), 'FOLD_REJECTED')
reject('changed_timeout', lambda: verify_fold(CLEAN, QUERY, plan(3), packet,
    **{**OPTIONS, 'timeout': 21}), 'FOLD_REJECTED')

for name, value in [('leading_zero', '0x0'+packet['number_hex'][2:]),
                    ('upper_prefix', '0X'+packet['number_hex'][2:]),
                    ('trailing_zero', packet['number_hex']+'00')]:
    forged = dict(packet, number_hex=value)
    reject(name, lambda forged=forged: unfold_source(forged))

forged_value = deepcopy(restored)
forged_value['limits']['world_truth_established'] = True
forged_raw = json.dumps({'schema': PAYLOAD_SCHEMA, 'domain': FOLD_DOMAIN, 'result': forged_value},
                       ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
forged_packet = dict(packet, number_hex=hex(int.from_bytes(b'\x01'+forged_raw, 'big')),
                     payload_sha256=hashlib.sha256(forged_raw).hexdigest())
reject('rehash_does_not_grant_authority', lambda: verify_fold(CLEAN, QUERY, plan(3),
    forged_packet, **OPTIONS), 'FOLD_REJECTED')

sample = {'s': ''.join(chr(i) for i in range(32))+'"\\\u007f\u0080\u07ff\u0800\uffff\U00010000\U0010ffff',
          'n': -9007199254740991, 'b': [True, False, None, [], {}]}
expected = json.dumps(sample, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
rows.append(dict(name='independent_string_size_boundary', matches=bounded_wire(sample, len(expected)) == expected,
                 bytes=len(expected)))
reject('one_byte_under_budget', lambda: bounded_wire(sample, len(expected)-1), 'RESOURCE_LIMIT')
shared = 'x'*40
for _ in range(14): shared = [shared, shared]
reject('shared_object_expansion', lambda: bounded_wire(shared, 1024), 'RESOURCE_LIMIT')
cycle = []; cycle.append(cycle)
reject('cyclic_python_input', lambda: bounded_wire(cycle), 'RESOURCE_LIMIT')
for name, raw in [('duplicate_keys', b'{"a":1,"a":2}'), ('negative_zero', b'-0'),
                  ('float', b'1.0'), ('surrogate', b'"\\ud800"'), ('nonfinite', b'NaN')]:
    reject(name, lambda raw=raw: strict_input(raw), 'INVALID_INPUT')
reject('oversized_integer', lambda: strict_input(b'9007199254740992'), 'RESOURCE_LIMIT')

after = {p: hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in files}
result = dict(schema='independent-source-fold-probe.v1', checker_mocks=False, before=before,
              after=after, source_changed_during_probe=before!=after, cases=rows,
              failed=[r['name'] for r in rows if r.get('matches') is False or r.get('rejected') is False])
(OUT/'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'source_changed_during_probe':before!=after, 'cases':rows, 'failed':result['failed']},
                 ensure_ascii=False, indent=2))
