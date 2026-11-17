"""Fixed-protocol CPU forward/backward training; no test-driven selection."""
from hashlib import sha256
from copy import deepcopy
import argparse
import json
import math
from pathlib import Path
import tempfile

from . import ntp_recursive as net

DIRECTORY = net.ROOT / 'evidence/ntp_recursive_v1'
SOURCE = 'evidence/shared_cell_reading_v1/train.json'
PROTOCOL_SHA256 = '1a3cbce83fcadaf4e000e50c76de454ef12df833ba0c68e2543313bdcc45ccfc'
SOURCE_SHA256 = 'be50e2833343e1db286b9e404292403e73647b6012ca5a80dc052212e445e1d0'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'


def validate_protocol(protocol):
    fields = {'schema', 'seed', 'dimension', 'epochs', 'learning_rate', 'source',
              'train_roots', 'development_roots', 'test_roots', 'selection',
              'tree', 'heads', 'scope', 'release_policy', 'authority'}
    if (type(protocol) is not dict or set(protocol) != fields
            or protocol['schema'] != 'nabt.ntp-recursive-training.v1'
            or type(protocol['seed']) is not int or not 0 <= protocol['seed'] < 2**32
            or type(protocol['dimension']) is not int or protocol['dimension'] != net.DIM
            or type(protocol['epochs']) is not int or not 1 <= protocol['epochs'] <= 10000
            or type(protocol['learning_rate']) not in (int, float)
            or not 0 < protocol['learning_rate'] <= 1
            or not math.isfinite(protocol['learning_rate'])
            or protocol['source'] != SOURCE
            or protocol['heads'] != list(net.LABELS)
            or protocol['selection'] != 'FIXED_FINAL_EPOCH_NO_TEST_SELECTION'
            or protocol['tree'] != 'ORDERED_LEFT_FOLD_SHARED_BINARY_COMPOSITION'
            or protocol['scope'] != 'AUTHORED_CELL_DIAGNOSTIC_NOT_BLIND_OR_GENERAL_IFADAH'
            or protocol['release_policy'] != 'REVIEW_ONLY' or protocol['authority'] != 'NONE'):
        raise ValueError('Invalid fixed recursive training protocol')
    for split in ('train', 'development', 'test'):
        roots = protocol[split + '_roots']
        if (type(roots) is not list or not 1 <= len(roots) <= 1024
                or any(type(root) is not str or not root or len(root.encode()) > 64 for root in roots)
                or len(set(roots)) != len(roots)):
            raise ValueError('Invalid root partition')
    return protocol


def validate_rows(rows, protocol):
    validate_protocol(protocol)
    if type(rows) is not list or not 1 <= len(rows) <= 1024:
        raise ValueError('Invalid source row collection')
    seen = set()
    for row in rows:
        if (type(row) is not dict or set(row) != {'cells', 'labels', 'provenance', 'root', 'text'}
                or type(row['root']) is not str or not row['root'] or len(row['root'].encode()) > 64
                or row['provenance'] != 'AUTHORED_NOT_LEXICAL_ATTESTATION'
                or type(row['labels']) is not dict or set(row['labels']) != set(net.LABELS)
                or any(type(row['labels'][h]) is not str or row['labels'][h] not in labels
                       for h, labels in net.LABELS.items())
                or type(row['cells']) is not list):
            raise ValueError('Invalid supervised source row')
        text, cells, _ = net.source({'text': row['text']})
        if net.validate_cells(row['cells']) != cells:
            raise ValueError('Cell/source mismatch')
        if text in seen:
            raise ValueError('Duplicate source row')
        seen.add(text)
    splits = {s: [r for r in rows if r['root'] in protocol[s + '_roots']]
              for s in ('train', 'development', 'test')}
    roots = [set(protocol[s + '_roots']) for s in splits]
    if any(roots[i] & roots[j] for i in range(3) for j in range(i)):
        raise ValueError('Root leakage')
    if sum(map(len, splits.values())) != len(rows) or any(not v for v in splits.values()):
        raise ValueError('Incomplete split')
    if set().union(*roots) != {row['root'] for row in rows}:
        raise ValueError('Declared root has no retained source')
    return splits


def inputs():
    raw_protocol = (DIRECTORY / 'protocol.json').read_bytes()
    if sha256(raw_protocol).hexdigest() != PROTOCOL_SHA256:
        raise ValueError('Frozen training protocol changed')
    protocol = validate_protocol(json.loads(raw_protocol))
    raw_source = (net.ROOT / SOURCE).read_bytes()
    if sha256(raw_source).hexdigest() != SOURCE_SHA256:
        raise ValueError('Frozen training source changed')
    splits = validate_rows(json.loads(raw_source), protocol)
    return protocol, splits


def initialize(seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    p = {k: rng.normal(0., .12, dims) for k, dims in net.shapes().items()}
    p['bias'] *= 0
    return p


def encode_tape(p, cells):
    """A116 word forward tape shared by the existing and program objectives."""
    import numpy as np
    values = net.validate_cells(cells)
    if not 1 <= len(values) <= net.MAX_CELLS:
        raise ValueError('Expected 1..64 A116 cells')
    leaves, joins = [], []
    hidden = None
    for c in values:
        bit = np.array(net.bits(c), dtype=float)
        atom = np.tanh(p['bits'] @ bit + p['carrier'][c // 4] + p['mark'][c % 4])
        leaves.append((c, bit, atom))
        if hidden is None:
            hidden = atom
        else:
            joined = np.concatenate((hidden, atom))
            hidden = np.tanh(p['compose'] @ joined + p['bias'])
            joins.append((joined, hidden))
    return hidden, (leaves, joins)


def backward_joins(p, joins, d, grad, leaf_count):
    """Reverse a shared ordered composition, preserving child order."""
    import numpy as np
    leaf_grads = [None] * leaf_count
    for i in range(len(joins) - 1, -1, -1):
        joined, value = joins[i]
        local = d * (1 - value * value)
        grad['compose'] += np.outer(local, joined)
        grad['bias'] += local
        children = p['compose'].T @ local
        d, leaf_grads[i + 1] = children[:net.DIM], children[net.DIM:]
    leaf_grads[0] = d
    return leaf_grads


def backward_tape(p, tape, d, grad):
    import numpy as np
    leaves, joins = tape
    leaf_grads = backward_joins(p, joins, d, grad, len(leaves))
    for (c, bit, value), d in zip(leaves, leaf_grads):
        local = d * (1 - value * value)
        grad['bits'] += np.outer(local, bit)
        grad['carrier'][c // 4] += local
        grad['mark'][c % 4] += local


def group_tape(p, groups):
    """Neural word composition only; no exact Machine effect crosses a word."""
    import numpy as np
    if type(groups) not in (list, tuple) or not 1 <= len(groups) <= 128:
        raise ValueError('Invalid ordered word groups')
    words, joins, hidden = [], [], None
    for cells in groups:
        word, tape = encode_tape(p, cells)
        words.append(tape)
        if hidden is None:
            hidden = word
        else:
            joined = np.concatenate((hidden, word))
            hidden = np.tanh(p['compose'] @ joined + p['bias'])
            joins.append((joined, hidden))
    return hidden, (words, joins)


def backward_groups(p, tape, d, grad):
    words, joins = tape
    word_grads = backward_joins(p, joins, d, grad, len(words))
    for word, incoming in zip(words, word_grads, strict=True):
        backward_tape(p, word, incoming, grad)


def loss_grad(p, row):
    """Analytic reverse mode through every shared join and A116 leaf."""
    import numpy as np
    hidden, tape = encode_tape(p, row['cells'])
    grad = {k: np.zeros_like(v) for k, v in p.items()}
    d = np.zeros(net.DIM)
    loss = 0.
    for head, labels in net.LABELS.items():
        key = 'head_' + head
        logits = p[key] @ hidden
        shifted = logits - logits.max()
        prob = np.exp(shifted); prob /= prob.sum()
        target = labels.index(row['labels'][head])
        loss += float(-shifted[target] + np.log(np.exp(shifted).sum())) / len(net.LABELS)
        prob[target] -= 1
        prob /= len(net.LABELS)
        grad[key] += np.outer(prob, hidden)
        d += p[key].T @ prob
    backward_tape(p, tape, d, grad)
    return loss, grad


def model(p, protocol):
    return {'schema': 'nabt.ntp-recursive-model.v1', 'alphabet_id': net.ALPHABET_ID,
            'labels': deepcopy(net.LABELS), 'parameters': {k: v.tolist() for k, v in p.items()},
            'protocol_sha256': sha256((DIRECTORY / 'protocol.json').read_bytes()).hexdigest(),
            'source_sha256': sha256((net.ROOT / protocol['source']).read_bytes()).hexdigest(),
            'authority': 'NONE', 'release_policy': 'REVIEW_ONLY'}


def evaluate(m, rows):
    predictions = []
    for row in rows:
        scores = net.scores(m, row['cells'])
        guessed = {h: max(v, key=lambda x: x['score'])['label'] for h, v in scores.items()}
        predictions.append({'text': row['text'], 'root': row['root'], 'gold': row['labels'],
                            'predicted': guessed, 'joint_correct': guessed == row['labels']})
    return {'rows': len(rows), 'joint_correct': sum(r['joint_correct'] for r in predictions),
            'heads_correct': {h: sum(r['gold'][h] == r['predicted'][h] for r in predictions)
                              for h in net.LABELS}, 'predictions': predictions}


def fit(protocol, rows, *, frozen=False):
    retained, splits = inputs()
    if (type(frozen) is not bool or canonical(protocol) != canonical(retained)
            or type(rows) is not list or canonical(rows) != canonical(splits['train'])):
        raise ValueError('Fit accepts only the frozen protocol and ordered training source rows')
    import numpy as np
    p = initialize(protocol['seed'])
    initial = {k: v.copy() for k, v in p.items()}
    moments = {k: np.zeros_like(v) for k, v in p.items()}
    squares = {k: np.zeros_like(v) for k, v in p.items()}
    first_grad = None
    for step in range(1, protocol['epochs'] + 1):
        grad = {k: np.zeros_like(v) for k, v in p.items()}
        for row in rows:
            _, g = loss_grad(p, row)
            for k in grad: grad[k] += g[k] / len(rows)
        if first_grad is None: first_grad = {k: float(np.linalg.norm(v)) for k, v in grad.items()}
        for k in p:
            if frozen and not k.startswith('head_'): continue
            moments[k] = .9 * moments[k] + .1 * grad[k]
            squares[k] = .999 * squares[k] + .001 * grad[k] ** 2
            p[k] -= protocol['learning_rate'] * (moments[k] / (1 - .9 ** step)) / (
                np.sqrt(squares[k] / (1 - .999 ** step)) + 1e-8)
    return p, {'initial_gradient_l2': first_grad,
               'parameter_change_l2': {k: float(np.linalg.norm(p[k] - initial[k])) for k in p}}


def gradient_check(protocol, row):
    import numpy as np
    p = initialize(protocol['seed'])
    _, grad = loss_grad(p, row)
    errors = {}
    for k in p:
        index = np.unravel_index(np.abs(grad[k]).argmax(), grad[k].shape)
        old = p[k][index]; eps = 1e-5
        p[k][index] = old + eps; plus = loss_grad(p, row)[0]
        p[k][index] = old - eps; minus = loss_grad(p, row)[0]
        p[k][index] = old
        errors[k] = abs(float(grad[k][index]) - (plus - minus) / (2 * eps))
    return {'absolute_errors': errors, 'passed': max(errors.values()) < 1e-7}


def train(directory):
    protocol, splits = inputs()
    before = model(initialize(protocol['seed']), protocol)
    trained, audit = fit(protocol, splits['train'])
    frozen, frozen_audit = fit(protocol, splits['train'], frozen=True)
    learned = model(trained, protocol)
    net.validate_model(learned)
    report = {'schema': 'nabt.ntp-recursive-evaluation.v1', 'protocol': protocol,
              'gradient_check': gradient_check(protocol, splits['train'][0]), 'training': audit,
              'frozen_training': frozen_audit,
              'before': {s: evaluate(before, r) for s, r in splits.items()},
              'trained': {s: evaluate(learned, r) for s, r in splits.items()},
              'frozen': {s: evaluate(model(frozen, protocol), r) for s, r in splits.items()},
              'general_ifadah_established': False, 'authority': 'NONE'}
    # Fresh independent repeat; neither development nor test enters fitting.
    repeat, _ = fit(protocol, splits['train'])
    report['byte_identical_repeat'] = canonical(learned) == canonical(model(repeat, protocol))
    report['model_sha256'] = sha256(canonical(learned).encode()).hexdigest()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'model.json').write_text(canonical(learned))
    (directory / 'evaluation.json').write_text(canonical(report))
    return report


def check():
    # Reuse the installed exact-structure/float-only replay comparator.
    from .train_apprentice import _difference
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'fit'
        report = train(target)
        new_model = json.loads((target / 'model.json').read_bytes())
        model_error = _difference(net.load(), new_model)
        retained = json.loads((DIRECTORY / 'evaluation.json').read_bytes())
        actual = dict(report)
        # A different float-only serialization has a different hash; compare
        # actual parameters above, while never changing the installed artifact.
        retained.pop('model_sha256'); actual.pop('model_sha256')
        evaluation_error = _difference(retained, actual)
        if max(model_error, evaluation_error) > 2e-9:
            raise ValueError('Recursive training replay differs')
        return {'maximum_parameter_error': model_error, 'maximum_evaluation_error': evaluation_error,
                'tolerance': 2e-9, 'installed_model_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path)
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        print(canonical(check()))
    else:
        result = train(args.output)
        print(canonical({k: result[k] for k in ('gradient_check', 'byte_identical_repeat', 'model_sha256')}))
