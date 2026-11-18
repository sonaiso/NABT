"""Frozen comparison data and strict offline scoring; never a semantic authority.

Public answers still use tools.ntp and independently verified gateway receipts.
This developer harness shares source partitions and inputs with future BERT runs.
"""
from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from itertools import product
import gzip
import json
from pathlib import Path

from . import ntp_recursive as cells, ntp_ifadah as operators, ifadah_programs as owner
from . import train_ntp_recursive as recursive, train_ntp_ifadah as ifadah
from . import train_update_memory as memory, update_memory_model

DIRECTORY = cells.ROOT / 'evidence/nabt_comparison_v1'
PROTOCOL_SHA256 = 'a381a3c91b69e392104a14dbc3a16ad2dc7c156c809ecd6b898e4f850931b0aa'
PROTOCOL_COMMIT = '3005948757b5674e042298e3d48dbfccbb829ad7'
OPERATOR_LABELS = ('negation', 'wish', 'ask')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


def protocol():
    raw = (DIRECTORY / 'protocol.json').read_bytes()
    if sha256(raw).hexdigest() != PROTOCOL_SHA256:
        raise ValueError('Comparison protocol changed after preregistration')
    result = json.loads(raw)
    for path, expected in result['sources'].items():
        if sha256((cells.ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('Comparison source changed: ' + path)
    return result


def row(task, split, source, features, target, *, eligible=True):
    return {'id': sha256((task + ':' + source).encode()).hexdigest()[:24],
            'task': task, 'split': split, 'source': source, 'input': features,
            'input_sha256': digest(features), 'target': target, 'eligible': eligible}


@lru_cache(maxsize=1)
def _dataset():
    protocol()
    _, partitions = recursive.inputs()
    _, program_splits, _ = ifadah.inputs()  # independently replay the source owner
    result = []
    for split, values in partitions.items():
        for value in values:
            result.append(row('cell_reading', {'development': 'dev', 'test': 'root_test'}.get(split, split),
                              'shared_cell_reading_v1:' + value['text'],
                              {'text': value['text'], 'cells': value['cells']}, value['labels']))
    for split, values in program_splits.items():
        for value in values:
            leaf = value['target_tree']
            while leaf['op'] != 'predication':
                leaf = leaf['body']
            # Only exact source spans/cells and supplied referent bindings cross
            # into features. No target operator, owner tree, score or rule ID.
            groups = [{key: occurrence[key] for key in ('surface', 'cells', 'utf8_span')}
                      for occurrence in value['operator_occurrences'] if occurrence['status'] == 'EXACT_A116']
            features = {'text': value['text'], 'operator_groups': groups,
                        'operator_count': len(value['operator_occurrences']),
                        'bindings': {key: leaf[key] for key in ('subject', 'predicate')}}
            result.append(row('program_composition', split, 'ntp_ifadah_v1:' + value['id'], features,
                              value['target_program'], eligible=value['status'] == 'ELIGIBLE'))
    for i, value in enumerate(memory.primitive_rows()):
        result.append(row('memory_primitive', 'train', 'update_memory_v1:primitive:' + str(i),
                          {'operator': value['operator'], 'operands': value['input']}, value['target']))
    actions = memory.contexts()
    for state in product((0, 1), repeat=5):
        for a, first in enumerate(actions):
            for b, second in enumerate(actions):
                features = {'roles': list(update_memory_model.ROLES), 'initial_memory': list(state),
                            'actions': [first, second]}
                target = memory.reference(memory.apply(memory.apply(state, first), second))
                result.append(row('memory_update', 'update_test', canonical(features), features, target))
    for width in (2, 4, 8, 12):
        sources = ([{'id': f'new_p{i}', 'role': 'property'} for i in range(width - 2)] +
                   [{'id': 'new_l0', 'role': 'law'}, {'id': 'new_l1', 'role': 'law'}])
        for mask in range(1 << width):
            active = [s['id'] for i, s in enumerate(sources) if mask & (1 << i)]
            target = [int(any(s['role'] == 'property' and s['id'] in active for s in sources)
                          and any(s['role'] == 'law' and s['id'] in active for s in sources)), 0, 0, 0]
            features = {'sources': sources, 'active': active}
            result.append(row('memory_alternatives', 'alternative_test', canonical(features), features, target))
    if len({r['id'] for r in result}) != len(result):
        raise ValueError('Duplicate comparison identity')
    return result


def dataset():
    # Reusing projected rows must not mask a later change to frozen sources.
    protocol()
    retained = json.loads((operators.DIRECTORY / 'supervision.json').read_bytes())
    if owner.identity(owner.awamil.DATA / 'awamil_occurrence_bank_v1.json') != retained['slot_source_sha256']:
        raise ValueError('Comparison lexical binding source changed')
    return deepcopy(_dataset())


def operator_training(rows):
    """Only atomic training programs supervise local operators; deduplicate inputs."""
    examples = {}
    for r in rows:
        if r['split'] != 'train' or r['task'] != 'program_composition' or not r['eligible']:
            continue
        groups = r['input']['operator_groups']
        if len(groups) != 1 or r['target'] not in OPERATOR_LABELS:
            raise ValueError('Atomic training assumption changed')
        key = tuple(groups[0]['cells'])
        if key in examples and examples[key] != r['target']:
            raise ValueError('Conflicting primitive supervision')
        examples[key] = r['target']
    if set(examples.values()) != set(OPERATOR_LABELS):
        raise ValueError('Incomplete primitive supervision')
    return [{'cells': list(key), 'target': value} for key, value in sorted(examples.items())]


def compose(labels, bindings):
    """Retain order. Validate predicted trees using the installed program owner.

    This yields a candidate name, not a grammar license for the original text.
    """
    if not labels or any(label not in OPERATOR_LABELS for label in labels):
        return None
    tree = owner.program('plain', bindings['subject'], bindings['predicate'])
    for label in reversed(labels):
        tree = {'op': label, 'body': tree}
    try:
        return owner.program_name(tree)[0]
    except ValueError:
        return None


def predict_language(parameters, task, features):
    """Target-free prediction. Gold, source IDs and split labels are inaccessible."""
    import numpy as np
    if task == 'cell_reading':
        hidden, _ = recursive.encode_tape(parameters, features['cells'])
        return {head: values[int(np.argmax(parameters['head_' + head] @ hidden))]
                for head, values in cells.LABELS.items()}
    if task != 'program_composition':
        raise ValueError('Unknown language task')
    groups = features['operator_groups']
    if not groups or len(groups) != features['operator_count']:
        return None
    labels = []
    for group in groups:
        hidden, _ = recursive.encode_tape(parameters, group['cells'])
        labels.append(OPERATOR_LABELS[int(np.argmax(parameters['head_operator'] @ hidden))])
    return compose(labels, features['bindings'])


def envelope(rows, name, values=None):
    return {'schema': 'nabt.comparison-predictions.v1', 'protocol_sha256': PROTOCOL_SHA256,
            'dataset_sha256': digest(rows), 'model': name,
            'status': 'NOT_RUN' if values is None else 'COMPLETED',
            'rows': [] if values is None else [
                {'id': r['id'], 'input_sha256': r['input_sha256'], 'value': value}
                for r, value in zip(rows, values, strict=True)]}


def valid_value(task, value):
    if value is None:
        return True
    if task == 'cell_reading':
        return (type(value) is dict and value.keys() == cells.LABELS.keys()
                and all(type(value[h]) is str and value[h] in labels for h, labels in cells.LABELS.items()))
    if task == 'program_composition':
        return type(value) is str and value in owner.PROGRAMS
    if task == 'memory_primitive':
        return type(value) is int and value in (0, 1)
    return type(value) is list and len(value) == 4 and all(type(v) is int and v in (0, 1) for v in value)


def score(rows, predictions):
    """Reject stale/duplicate identities; missing, deferred and invalid values fail."""
    required = {'schema', 'protocol_sha256', 'dataset_sha256', 'model', 'status', 'rows'}
    if (type(predictions) is not dict or set(predictions) != required
            or predictions['schema'] != 'nabt.comparison-predictions.v1'
            or predictions['protocol_sha256'] != PROTOCOL_SHA256
            or predictions['dataset_sha256'] != digest(rows)
            or type(predictions['model']) is not str or not 1 <= len(predictions['model']) <= 256
            or type(predictions['rows']) is not list
            or predictions['status'] not in ('NOT_RUN', 'COMPLETED')):
        raise ValueError('Invalid or stale comparison envelope')
    if predictions['status'] == 'NOT_RUN':
        if predictions['rows']:
            raise ValueError('NOT_RUN cannot contain predictions')
        return {'status': 'NOT_RUN', 'model': predictions['model'], 'metrics': None}
    expected = {r['id']: r for r in rows}
    received = {}
    for p in predictions['rows']:
        if (type(p) is not dict or set(p) != {'id', 'input_sha256', 'value'}
                or type(p['id']) is not str or p['id'] not in expected or p['id'] in received
                or p['input_sha256'] != expected[p['id']]['input_sha256']):
            raise ValueError('Unknown, duplicate or source-detached prediction')
        received[p['id']] = p['value']
    metrics = defaultdict(lambda: dict(count=0, correct=0, answered=0, missing=0, invalid=0))
    for r in rows:
        value = received.get(r['id'])
        valid = valid_value(r['task'], value)
        keys = [r['task'] + '/' + r['split']]
        if r['task'] == 'program_composition' and r['eligible']:
            keys.append(r['task'] + '_eligible/' + r['split'])
        if r['task'] == 'cell_reading':
            keys += ['cell_head_' + head + '/' + r['split'] for head in cells.LABELS]
        for key in keys:
            m = metrics[key]
            m['count'] += 1
            exact = valid and value is not None and value == r['target']
            if r['task'] == 'cell_reading' and not key.startswith('cell_reading/'):
                head = key.split('/')[0].removeprefix('cell_head_')
                exact = valid and value is not None and value[head] == r['target'][head]
            m['correct'] += int(exact)
            m['answered'] += int(valid and value is not None)
            m['missing'] += int(r['id'] not in received)
            m['invalid'] += int(not valid)
    for m in metrics.values():
        m['accuracy'] = m['correct'] / m['count']
        m['coverage'] = m['answered'] / m['count']
    return {'status': 'COMPLETED', 'model': predictions['model'], 'metrics': dict(metrics)}


def write_json(path, value):
    Path(path).write_text(canonical(value))


def write_rows(path, rows):
    raw = ''.join(canonical(r) for r in rows).encode()
    Path(path).write_bytes(gzip.compress(raw, mtime=0))


def export(directory, rows):
    """Input-only evaluation files; keys are retained separately for the scorer."""
    directory = Path(directory)
    directory.mkdir()
    write_rows(directory / 'answer_key.jsonl.gz', rows)
    partitions = sorted({r['split'] for r in rows})
    for split in partitions:
        selected = []
        for r in rows:
            if r['split'] == split:
                item = {k: r[k] for k in ('id', 'task', 'split', 'input', 'input_sha256')}
                if split in ('train', 'dev'):
                    item['target'] = r['target']
                selected.append(item)
        write_rows(directory / (split + '.jsonl.gz'), selected)
    subsets = {'language': [r for r in rows if r['task'] in ('cell_reading', 'program_composition')],
               'memory': [r for r in rows if r['task'].startswith('memory_')]}
    for name, subset in subsets.items():
        write_json(directory / ('bert_' + name + '_template.json'), envelope(subset, 'BERT'))
    write_json(directory / 'manifest.json', {
        'schema': 'nabt.comparison-dataset.v1', 'protocol_sha256': PROTOCOL_SHA256,
        'dataset_sha256': digest(rows), 'rows': len(rows),
        'subsets': {name: {'rows': len(subset), 'sha256': digest(subset)} for name, subset in subsets.items()},
        'files': {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(directory.iterdir())},
        'test_status': 'PUBLISHED_REGRESSION_NOT_BLIND',
        'side_information': 'OWNER_OPERATOR_SPANS_BINDINGS_AND_MEMORY_ROLES_SUPPLIED_TO_BOTH',
        'authority': 'NONE'})
