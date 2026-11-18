"""Train NABT and retain a source-bound benchmark for subsequent BERT comparison.

Offline developer experiment, not an alternate NABT external answer boundary.
No installed model, theorem, source split or owner decision is overwritten.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import tempfile
import time

from . import comparison_simulation as experiment
from . import train_ntp_recursive as recursive, ntp_recursive as cells
from . import train_update_memory as memory, update_memory_model


def initialize(seed):
    import numpy as np
    parameters = recursive.initialize(seed)
    parameters['head_operator'] = np.random.default_rng(seed + 1).normal(
        0., .12, (len(experiment.OPERATOR_LABELS), cells.DIM))
    return parameters


def operator_loss_gradient(parameters, row):
    import numpy as np
    hidden, tape = recursive.encode_tape(parameters, row['cells'])
    logits = parameters['head_operator'] @ hidden
    shifted = logits - logits.max()
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum()
    target = experiment.OPERATOR_LABELS.index(row['target'])
    loss = float(-shifted[target] + np.log(np.exp(shifted).sum()))
    probabilities[target] -= 1
    gradient = {key: np.zeros_like(value) for key, value in parameters.items()}
    gradient['head_operator'] = np.outer(probabilities, hidden)
    recursive.backward_tape(parameters, tape, parameters['head_operator'].T @ probabilities, gradient)
    return loss, gradient


def training_examples():
    rows = experiment.dataset()
    word_rows = [{'cells': r['input']['cells'], 'labels': r['target']}
                 for r in rows if r['task'] == 'cell_reading' and r['split'] == 'train']
    return word_rows, experiment.operator_training(rows)


def batch_loss_gradient(parameters, words, operators):
    import numpy as np
    total = 0.
    gradient = {key: np.zeros_like(value) for key, value in parameters.items()}
    for rows, function in ((words, recursive.loss_grad), (operators, operator_loss_gradient)):
        for row in rows:
            loss, part = function(parameters, row)
            total += .5 * loss / len(rows)
            for key in gradient:
                gradient[key] += .5 * part[key] / len(rows)
    return total, gradient


def fit(seed, *, frozen=False):
    import numpy as np
    protocol = experiment.protocol()
    if type(seed) is not int or seed not in protocol['seeds'] or type(frozen) is not bool:
        raise ValueError('Only preregistered seeds and ablations may fit')
    words, operators = training_examples()
    parameters = initialize(seed)
    initial = {key: value.copy() for key, value in parameters.items()}
    moments = {key: np.zeros_like(value) for key, value in parameters.items()}
    squares = {key: np.zeros_like(value) for key, value in parameters.items()}
    history = []
    first_gradient = None
    for step in range(protocol['epochs'] + 1):
        loss, gradient = batch_loss_gradient(parameters, words, operators)
        if first_gradient is None:
            first_gradient = {key: float(np.linalg.norm(value)) for key, value in gradient.items()}
        if step % 50 == 0 or step == protocol['epochs']:
            history.append({'epoch': step, 'loss': loss})
        if step == protocol['epochs']:
            break
        for key in parameters:
            if frozen and key in cells.shared_shapes():
                continue
            moments[key] = .9 * moments[key] + .1 * gradient[key]
            squares[key] = .999 * squares[key] + .001 * gradient[key] ** 2
            parameters[key] -= protocol['learning_rate'] * (moments[key] / (1 - .9 ** (step + 1))) / (
                np.sqrt(squares[key] / (1 - .999 ** (step + 1))) + 1e-8)
    return parameters, {'seed': seed, 'frozen_encoder': frozen, 'history': history,
        'training_words': len(words), 'distinct_training_operators': len(operators),
        'parameter_count': sum(value.size for value in parameters.values()),
        'initial_gradient_l2': first_gradient,
        'parameter_change_l2': {key: float(np.linalg.norm(value - initial[key])) for key, value in parameters.items()}}


def gradient_check(seed):
    import numpy as np
    parameters = initialize(seed)
    words, operators = training_examples()
    _, gradient = batch_loss_gradient(parameters, words, operators)
    errors = {}
    for key in parameters:
        index = np.unravel_index(np.abs(gradient[key]).argmax(), gradient[key].shape)
        original = parameters[key][index]
        epsilon = 1e-5
        parameters[key][index] = original + epsilon
        plus = batch_loss_gradient(parameters, words, operators)[0]
        parameters[key][index] = original - epsilon
        minus = batch_loss_gradient(parameters, words, operators)[0]
        parameters[key][index] = original
        errors[key] = abs(float(gradient[key][index]) - (plus - minus) / (2 * epsilon))
    return {'absolute_errors': errors, 'passed': max(errors.values()) < experiment.protocol()['gradient_check_tolerance']}


def memory_prediction(parameters, task, features):
    if task == 'memory_primitive':
        weights = parameters[features['operator']]
        value = weights[0] + sum(w * x for w, x in zip(weights[1:], features['operands'], strict=True))
        return int(update_memory_model.sigmoid(value) >= .5)
    if task == 'memory_update':
        state = list(features['initial_memory'])
        for action in features['actions']:
            state = memory.apply(state, action)
        sources = [{'id': f's{i}', 'role': role} for i, role in enumerate(features['roles'])]
        active = {f's{i}' for i, value in enumerate(state) if value}
    elif task == 'memory_alternatives':
        sources, active = features['sources'], set(features['active'])
    else:
        raise ValueError('Unknown memory task')
    return update_memory_model.predict(parameters, sources, active)['prediction']


def train(directory):
    import numpy as np
    protocol = experiment.protocol()
    rows = experiment.dataset()
    language = [r for r in rows if r['task'] in ('cell_reading', 'program_composition')]
    memory_rows = [r for r in rows if r['task'].startswith('memory_')]
    directory = Path(directory)
    directory.mkdir(exist_ok=False, parents=True)
    (directory / 'models').mkdir()
    (directory / 'predictions').mkdir()
    experiment.export(directory / 'dataset', rows)
    report = {'schema': 'nabt.comparison-training.v1', 'protocol_commit': experiment.PROTOCOL_COMMIT,
        'protocol_sha256': experiment.PROTOCOL_SHA256, 'dataset_sha256': experiment.digest(rows),
        'scope': protocol['evaluation_status'], 'authority': 'NONE', 'language': {},
        'bert': {name: experiment.score(subset, experiment.envelope(subset, 'BERT'))
                 for name, subset in (('language', language), ('memory', memory_rows))},
        'gradient_check': gradient_check(protocol['seeds'][0]),
        'limits': protocol['claims_not_established'],
        'side_information': protocol['bert']['assistance']}
    if not report['gradient_check']['passed']:
        raise ValueError('Analytic gradients failed independent finite differences')
    for seed in protocol['seeds']:
        report['language'][str(seed)] = {}
        for mode in protocol['ablations']:
            if mode == 'untrained':
                parameters, audit = initialize(seed), None
            else:
                parameters, audit = fit(seed, frozen=mode == 'frozen_encoder')
            values = [experiment.predict_language(parameters, r['task'], r['input']) for r in language]
            predictions = experiment.envelope(language, f'NABT/{mode}/{seed}', values)
            entry = experiment.score(language, predictions)
            entry['training'] = audit
            report['language'][str(seed)][mode] = entry
            stem = f'{seed}-{mode}'
            experiment.write_json(directory / 'predictions' / (stem + '.json'), predictions)
            experiment.write_json(directory / 'models' / (stem + '.json'), {
                'schema': 'nabt.comparison-language-model.v1', 'protocol_sha256': experiment.PROTOCOL_SHA256,
                'seed': seed, 'mode': mode, 'authority': 'NONE', 'release_policy': 'EXPERIMENT_ONLY',
                'parameters': {key: value.tolist() for key, value in parameters.items()}})
        print(json.dumps({'completed_seed': seed}), flush=True)
    # This is a separate frozen memory experiment, not another seed of the
    # language encoder. It is refitted, not copied from retained predictions.
    model, training, evaluation = memory.train()
    report['memory'] = {'training': training, 'metrics': evaluation['metrics'], 'scores': {}}
    experiment.write_json(directory / 'models' / 'memory.json', model)
    for name, parameters in (('untrained', training['initial_parameters']), ('trained', model['parameters'])):
        values = [memory_prediction(parameters, r['task'], r['input']) for r in memory_rows]
        predictions = experiment.envelope(memory_rows, 'NABT/memory/' + name, values)
        report['memory']['scores'][name] = experiment.score(memory_rows, predictions)
        # Lossless compact retention; the scoring envelope is retained intact.
        experiment.write_rows(directory / 'predictions' / ('memory-' + name + '.jsonl.gz'), [predictions])
    report['input_novelty'] = {}
    for split in sorted({r['split'] for r in language}):
        selected = [r for r in language if r['task'] == 'program_composition' and r['split'] == split and r['eligible']]
        signatures = {experiment.canonical([g['cells'] for g in r['input']['operator_groups']]) for r in selected}
        train_signatures = {experiment.canonical([g['cells'] for g in r['input']['operator_groups']])
                            for r in language if r['task'] == 'program_composition' and r['split'] == 'train' and r['eligible']}
        report['input_novelty'][split] = {'eligible_rows': len(selected), 'distinct_operator_inputs': len(signatures),
                                          'new_operator_inputs': len(signatures - train_signatures)}
    experiment.write_json(directory / 'evaluation.json', report)
    experiment.write_json(directory / 'runtime.json', {'python': platform.python_version(), 'numpy': np.__version__,
        'device': 'CPU', 'platform': platform.platform(), 'installed_weights_replaced': False})
    return report


def check(directory):
    """Refit all seeds/ablations; compare every model, prediction and score."""
    from .train_apprentice import _difference
    with tempfile.TemporaryDirectory() as temporary:
        candidate = Path(temporary) / 'replay'
        train(candidate)
        expected_files = {str(p.relative_to(directory)) for p in Path(directory).rglob('*') if p.is_file()}
        actual_files = {str(p.relative_to(candidate)) for p in candidate.rglob('*') if p.is_file()}
        # NTP receipts are independently replayed by their own native gate.
        expected_files = {f for f in expected_files if not f.startswith('ntp/')}
        if actual_files != expected_files:
            raise ValueError('Training artifact set changed')
        for relative in sorted(actual_files):
            if relative == 'runtime.json':
                continue
            old, new = Path(directory) / relative, candidate / relative
            if relative.endswith('.gz'):
                import gzip
                left = [json.loads(line) for line in gzip.decompress(old.read_bytes()).splitlines()]
                right = [json.loads(line) for line in gzip.decompress(new.read_bytes()).splitlines()]
            else:
                left, right = json.loads(old.read_bytes()), json.loads(new.read_bytes())
            if _difference(left, right) > 2e-9:
                raise ValueError('Retained result changed: ' + relative)
    return {'reproduced': True, 'protocol_sha256': experiment.PROTOCOL_SHA256}


def replay_ntp(directory):
    """Exercise the unchanged public boundary, retaining original requests.

    These are owner/gateway transport controls. Experimental learned weights
    remain offline proposals and are not silently installed by this replay.
    """
    import gzip
    import subprocess
    import sys
    rows = experiment.dataset()
    cases = [('active', {'schema': 'nabt.io.request.v1', 'route': 'ntp',
                        'payload': {'operation': 'forward', 'input': {'text': 'كَتَبَ'}}}),
             ('passive', {'schema': 'nabt.io.request.v1', 'route': 'ntp',
                         'payload': {'operation': 'forward', 'input': {'text': 'كُتِبَ'}}})]
    for name in ('ask_negation', 'wish'):
        source = next(r for r in rows if r['task'] == 'program_composition' and r['target'] == name)
        cases.append((name, {'schema': 'nabt.io.request.v1', 'route': 'ntp', 'payload': {
            'operation': 'cognitive.lesson', 'input': {'lesson': {
                'schema': experiment.owner.SCHEMA, 'mode': 'understand',
                'source_id': 'comparison:' + source['id'], 'text': source['input']['text']}}}}))
    cases.append(('memory_update', json.loads((cells.ROOT / 'examples/io_gateway/ntl_update_memory.json').read_bytes())))
    directory = Path(directory)
    directory.mkdir(exist_ok=False, parents=True)
    summary = {'schema': 'nabt.comparison-ntp-controls.v1', 'cases': [],
               'scope': 'UNCHANGED_OWNER_TRANSPORT_NOT_EXPERIMENTAL_WEIGHT_ADMISSION', 'authority': 'NONE'}
    for name, request in cases:
        request_path = directory / (name + '.request.json')
        experiment.write_json(request_path, request)
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / 'receipt.json'
            verification = Path(temporary) / 'verification.json'
            prefix = [sys.executable, '-m', 'tools.ntp']
            commands = [prefix + ['run', '--request', str(request_path), '--output', str(receipt)],
                        prefix + ['verify', '--request', str(request_path), '--receipt', str(receipt),
                                  '--output', str(verification)]]
            for command in commands:
                process = subprocess.run(command, cwd=cells.ROOT, check=False, timeout=120, capture_output=True)
                if process.returncode:
                    failure = {'case': name, 'action': command[3], 'returncode': process.returncode,
                               'stderr': process.stderr.decode(errors='replace'),
                               'stdout': process.stdout.decode(errors='replace')}
                    experiment.write_json(directory / (name + '.failure.json'), failure)
                    raise RuntimeError('NTP control failed; retained diagnostics: ' + name + '.failure.json')
            verified = json.loads(verification.read_bytes())
            if verified.get('valid') is not True:
                raise ValueError('NTP replay did not independently verify')
            raw = receipt.read_bytes()
            (directory / (name + '.receipt.json.gz')).write_bytes(gzip.compress(raw, mtime=0))
            experiment.write_json(directory / (name + '.verification.json'), verified)
            summary['cases'].append({'name': name, 'request_sha256': sha256(request_path.read_bytes()).hexdigest(),
                                     'receipt_sha256': sha256(raw).hexdigest(), 'verified': True})
    experiment.write_json(directory / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--output', type=Path)
    action.add_argument('--check', action='store_true')
    action.add_argument('--score', type=Path)
    action.add_argument('--replay-ntp', type=Path)
    parser.add_argument('--subset', choices=('language', 'memory'))
    args = parser.parse_args()
    if args.score:
        if args.subset is None:
            parser.error('--score requires --subset')
        from tools.evidence_lifecycle_v1 import strict_loads
        rows = [r for r in experiment.dataset() if (r['task'].startswith('memory_')) == (args.subset == 'memory')]
        with args.score.open('rb') as source:
            predictions = strict_loads(source.read(8 * 1048576 + 1), maximum_bytes=8 * 1048576)
        result = experiment.score(rows, predictions)
    elif args.replay_ntp:
        if args.subset:
            parser.error('--subset is only for scoring')
        result = replay_ntp(args.replay_ntp.resolve())
    elif args.check:
        if args.subset:
            parser.error('--subset is only for scoring')
        result = check(experiment.DIRECTORY / 'run')
    else:
        if args.subset:
            parser.error('--subset is only for scoring')
        started = time.monotonic()
        result = train(args.output)
        result = {'trained': True, 'seconds': round(time.monotonic() - started, 3),
                  'gradient_check': result['gradient_check'], 'bert': result['bert']}
    print(experiment.canonical(result), end='')


if __name__ == '__main__':
    main()
