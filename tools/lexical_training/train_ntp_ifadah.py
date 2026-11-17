"""Frozen, source-attested program selection loss through the shared A116 graph."""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import tempfile

from . import ifadah_programs as owner, ntp_ifadah as net, ntp_recursive as base
from . import train_ntp_recursive as recursive

DIRECTORY = net.DIRECTORY
SPLITS = ('train', 'dev', 'lexical_test', 'structure_test')
canonical = recursive.canonical


def inputs():
    raw = (DIRECTORY / 'protocol.json').read_bytes()
    if sha256(raw).hexdigest() != net.PROTOCOL_SHA256:
        raise ValueError('Frozen program-choice protocol changed')
    protocol = json.loads(raw)
    raw = (DIRECTORY / 'supervision.json').read_bytes()
    if sha256(raw).hexdigest() != net.SUPERVISION_SHA256:
        raise ValueError('Frozen source supervision changed')
    retained = json.loads(raw)
    source = base.ROOT / protocol['source']
    slot_source = owner.awamil.DATA / 'awamil_occurrence_bank_v1.json'
    if (sha256(source.read_bytes()).hexdigest() != protocol['source_sha256']
            or sha256(base.MODEL.read_bytes()).hexdigest() != protocol['initial_model_sha256']
            or sha256(slot_source.read_bytes()).hexdigest() != retained['slot_source_sha256']):
        raise ValueError('Retained program source or initial model changed')
    rebuilt = {key: retained[key] for key in ('schema', 'source', 'source_sha256', 'slot_source_sha256')}
    rebuilt['rows'] = []
    for index, row in enumerate(owner.dataset()['rows']):
        source_id = 'ifadah:' + row['id']
        projected = net.project(row['text'], source_id)
        if len(projected['observations']) != 1:
            raise ValueError('Training source lacks a unique retained reading')
        observation = projected['observations'][0]
        target = owner.program(row['program'], row['subject'], row['predicate'])
        if observation['owner_tree'] != target:
            raise ValueError('Target disagrees with the independent source owner')
        rebuilt['rows'].append({'id': row['id'], 'source_pointer': '/rows/' + str(index),
            'source_id': source_id, 'text': row['text'], 'text_sha256': projected['source_sha256'],
            'split': row['split'], 'target_program': row['program'], 'target_tree': target,
            'operator_occurrences': observation['operator_occurrences'], 'status': observation['status']})
    if canonical(rebuilt) != canonical(retained):
        raise ValueError('Retained supervision no longer replays from its source')
    rows = retained['rows']
    if len({row['id'] for row in rows}) != len(rows) or len({row['text_sha256'] for row in rows}) != len(rows):
        raise ValueError('Duplicate source identity')
    splits = {split: [row for row in rows if row['split'] == split] for split in SPLITS}
    eligible = {split: [row for row in values if row['status'] == 'ELIGIBLE']
                for split, values in splits.items()}
    if ({split: len(values) for split, values in eligible.items()} != protocol['eligible_split_counts']
            or sum(len(v) for v in splits.values()) != len(rows)
            or sum(row['status'] != 'ELIGIBLE' for row in rows) != protocol['excluded_rows']
            or any(row['target_program'] not in net.CANDIDATES for values in eligible.values() for row in values)):
        raise ValueError('Changed source split or eligibility population')
    return protocol, splits, eligible


def initialize(seed):
    import numpy as np
    original = base.load()['parameters']
    p = {key: np.array(original[key], dtype=float) for key in base.shared_shapes()}
    rng = np.random.default_rng(seed)
    for key in ('program_force', 'program_frame'):
        p[key] = rng.normal(0., .12, net.shapes()[key])
    return p


def loss_grad(p, groups, target):
    """Joint program CE; gold is used only after all candidate logits exist."""
    import numpy as np
    if target not in net.CANDIDATES:
        raise ValueError('Target outside the frozen candidate domain')
    if type(groups) not in (list, tuple) or not 1 <= len(groups) <= 2:
        raise ValueError('Expected one or two exact operator word groups')
    hidden, tape = recursive.group_tape(p, groups)
    force = p['program_force'] @ hidden
    frame = p['program_frame'] @ hidden
    logits = np.array([force[f] + frame[g] for f, g in net.AXES])
    shifted = logits - logits.max()
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum()
    target_index = net.CANDIDATES.index(target)
    loss = float(-shifted[target_index] + np.log(np.exp(shifted).sum()))
    probabilities[target_index] -= 1
    df = np.zeros(len(net.FORCES))
    dg = np.zeros(len(net.FRAMES))
    for value, (f, g) in zip(probabilities, net.AXES, strict=True):
        df[f] += value
        dg[g] += value
    grad = {key: np.zeros_like(value) for key, value in p.items()}
    grad['program_force'] = np.outer(df, hidden)
    grad['program_frame'] = np.outer(dg, hidden)
    d = p['program_force'].T @ df + p['program_frame'].T @ dg
    recursive.backward_groups(p, tape, d, grad)
    return loss, grad


def model(p, protocol):
    return {'schema': 'nabt.ntp-ifadah-model.v1', 'alphabet_id': base.ALPHABET_ID,
        'candidates': list(net.CANDIDATES), 'forces': list(net.FORCES), 'frames': list(net.FRAMES),
        'parameters': {key: value.tolist() for key, value in p.items()},
        'protocol_sha256': net.PROTOCOL_SHA256, 'supervision_sha256': net.SUPERVISION_SHA256,
        'initial_model_sha256': protocol['initial_model_sha256'],
        'source_sha256': protocol['source_sha256'], 'authority': 'NONE', 'release_policy': 'REVIEW_ONLY'}


def fit(protocol, rows, *, frozen=False):
    retained_protocol, _, eligible = inputs()
    if (type(frozen) is not bool or canonical(protocol) != canonical(retained_protocol)
            or type(rows) is not list or canonical(rows) != canonical(eligible['train'])):
        raise ValueError('Only the frozen ordered eligible training sources may fit')
    import numpy as np
    p = initialize(protocol['seed'])
    initial = {key: value.copy() for key, value in p.items()}
    moments = {key: np.zeros_like(value) for key, value in p.items()}
    squares = {key: np.zeros_like(value) for key, value in p.items()}
    first_gradient = None
    for step in range(1, protocol['epochs'] + 1):
        grad = {key: np.zeros_like(value) for key, value in p.items()}
        for row in rows:
            _, row_grad = loss_grad(p, net.groups(row), row['target_program'])
            for key in grad:
                grad[key] += row_grad[key] / len(rows)
        if first_gradient is None:
            first_gradient = {key: float(np.linalg.norm(value)) for key, value in grad.items()}
        for key in p:
            if frozen and not key.startswith('program_'):
                continue
            moments[key] = .9 * moments[key] + .1 * grad[key]
            squares[key] = .999 * squares[key] + .001 * grad[key] ** 2
            p[key] -= protocol['learning_rate'] * (moments[key] / (1 - .9 ** step)) / (
                np.sqrt(squares[key] / (1 - .999 ** step)) + 1e-8)
    return p, {'initial_gradient_l2': first_gradient,
               'parameter_change_l2': {key: float(np.linalg.norm(p[key] - initial[key])) for key in p}}


def evaluate(m, rows):
    predictions = []
    for row in rows:
        item = {key: row[key] for key in ('id', 'text_sha256', 'split', 'target_program', 'status')}
        if row['status'] == 'ELIGIBLE':
            choices = net.scores(m, net.groups(row))
            best = max(value['score'] for value in choices)
            winners = [value['name'] for value in choices if value['score'] == best]
            guessed = winners[0] if len(winners) == 1 else None
            item.update(predicted_program=guessed, correct=guessed == row['target_program'],
                        scores=choices, all_candidates_scored=True)
        predictions.append(item)
    eligible_count = sum(row['status'] == 'ELIGIBLE' for row in rows)
    return {'all_source_rows': len(rows), 'eligible_rows': eligible_count,
            'deferred_rows': len(rows) - eligible_count,
            'correct_programs': sum(row.get('correct', False) for row in predictions),
            'predictions': predictions}


def gradient_check(protocol, groups, target):
    import numpy as np
    p = initialize(protocol['seed'])
    _, gradients = loss_grad(p, groups, target)
    errors = {}
    for key in p:
        index = np.unravel_index(np.abs(gradients[key]).argmax(), gradients[key].shape)
        original = p[key][index]
        epsilon = 1e-5
        p[key][index] = original + epsilon
        plus = loss_grad(p, groups, target)[0]
        p[key][index] = original - epsilon
        minus = loss_grad(p, groups, target)[0]
        p[key][index] = original
        errors[key] = abs(float(gradients[key][index]) - (plus - minus) / (2 * epsilon))
    return {'absolute_errors': errors, 'passed': max(errors.values()) < protocol['gradient_check_tolerance']}


def input_novelty(eligible):
    signatures = {split: {canonical(net.groups(row)) for row in rows} for split, rows in eligible.items()}
    train = signatures['train']
    return {split: {'rows': len(eligible[split]), 'distinct_operator_inputs': len(values),
                    'seen_in_training': len(values & train), 'new_operator_inputs': len(values - train)}
            for split, values in signatures.items()}


def train(directory):
    protocol, splits, eligible = inputs()
    initial = model(initialize(protocol['seed']), protocol)
    fitted, audit = fit(protocol, eligible['train'])
    frozen, frozen_audit = fit(protocol, eligible['train'], frozen=True)
    learned = net.validate_model(model(fitted, protocol))
    first = eligible['train'][0]
    report = {'schema': 'nabt.ntp-ifadah-evaluation.v1', 'protocol': protocol,
        'conditioning': 'EXISTING_OWNER_OPERATOR_SEGMENTATION_AND_SOURCE_ATTESTED_TARGETS',
        'input_novelty': input_novelty(eligible),
        'gradient_check': gradient_check(protocol, net.groups(first), first['target_program']),
        'training': audit, 'frozen_training': frozen_audit,
        'before': {split: evaluate(initial, rows) for split, rows in splits.items()},
        'trained': {split: evaluate(learned, rows) for split, rows in splits.items()},
        'frozen': {split: evaluate(model(frozen, protocol), rows) for split, rows in splits.items()},
        'all_source_rows': sum(len(rows) for rows in splits.values()),
        'excluded_rows': [row for rows in splits.values() for row in rows if row['status'] != 'ELIGIBLE'],
        'subject_predicate_binding_learned': False, 'instruction_intent_learned': False,
        'general_ifadah_established': False, 'neural_selection_permitted': False, 'authority': 'NONE'}
    repeat, _ = fit(protocol, eligible['train'])
    report['byte_identical_repeat'] = canonical(learned) == canonical(model(repeat, protocol))
    report['model_sha256'] = sha256(canonical(learned).encode()).hexdigest()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'model.json').write_text(canonical(learned))
    (directory / 'evaluation.json').write_text(canonical(report))
    return report


def check():
    from .train_apprentice import _difference
    with tempfile.TemporaryDirectory() as folder:
        destination = Path(folder) / 'fit'
        report = train(destination)
        proposed_model = json.loads((destination / 'model.json').read_bytes())
        model_error = _difference(net.load(), proposed_model)
        retained = json.loads((DIRECTORY / 'evaluation.json').read_bytes())
        actual = dict(report)
        retained.pop('model_sha256')
        actual.pop('model_sha256')
        evaluation_error = _difference(retained, actual)
        if max(model_error, evaluation_error) > report['protocol']['replay_tolerance']:
            raise ValueError('Program-choice training replay differs')
        return {'maximum_parameter_error': model_error, 'maximum_evaluation_error': evaluation_error,
                'tolerance': report['protocol']['replay_tolerance'], 'installed_artifacts_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path)
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = check() if args.check else train(args.output)
    print(canonical(result if args.check else {key: result[key] for key in
        ('gradient_check', 'input_novelty', 'byte_identical_repeat', 'model_sha256')}))
