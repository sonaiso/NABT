"""Fit frozen-GRU utterance-program readouts using only the committed train split."""
import argparse
from collections import Counter
import json
from pathlib import Path

from . import ifadah_programs as net


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')


def fit_matrix(x, labels, names, alpha):
    import numpy as np
    x = np.asarray(x)
    targets = np.asarray([[float(label == name) for name in names] for label in labels])
    # Dual form keeps training cost bounded by the number of authored examples.
    w = x.T @ np.linalg.solve(x @ x.T + alpha * np.eye(len(x)), targets)
    return w.T.round(10).tolist()


def train(output):
    import numpy as np
    data = net.dataset()
    protocol = json.loads((net.DIRECTORY / 'protocol.json').read_bytes())
    encoder = net.shared.MODEL.read_bytes()
    net.shared.validate_model(json.loads(encoder))
    read_rows = data['rows']
    goal_rows = []
    for name, prompts in data['goal_prompts'].items():
        force, frame = net.PROGRAMS[name]
        for i, text in enumerate(prompts):
            goal_rows.append({'id': name + '-prompt-' + str(i), 'text': text, 'program': name,
                              'force': force, 'frame': frame, 'subject': 0, 'predicate': 0,
                              'split': 'structure_test' if name in protocol['withheld_programs']
                              else 'train' if i < 2 else 'dev' if i == 2 else 'paraphrase_test'})
    all_rows = {'understand': read_rows, 'produce': goal_rows}
    local_protocol = json.loads((net.DIRECTORY/'protocol_local.json').read_bytes())
    local_heads, token_counts = {}, {}
    for mode, rows in all_rows.items():
        examples = []
        for r in rows:
            if r['split'] != 'train':
                continue
            for i, term in enumerate(net.exact_terms(r['text'])):
                force, frame = 'assert', 'plain'
                if mode == 'understand':
                    if i == 0 and r['force'] != 'assert': force = r['force']
                    if i == 0 and r['frame'] != 'plain': frame = r['frame']
                else:
                    annotation = local_protocol['goal_training_cues'].get(term['surface'])
                    if annotation in net.FORCES: force = annotation
                    if annotation in net.FRAMES: frame = annotation
                examples.append((net.token_vector(encoder, term['surface']) + [1.], force, frame))
        token_counts[mode] = len(examples)
        local_heads[mode] = {key: fit_matrix([e[0] for e in examples], [e[index] for e in examples], labels,
                                             local_protocol['alpha'])
                            for key,index,labels in (('force',1,net.FORCES),('frame',2,net.FRAMES))}

    # No dev/test rows participate in target formation, solving, or hyperparameter selection.
    vectors = {mode: {r['id']: net.features(encoder, r['text']) for r in rows} for mode, rows in all_rows.items()}
    heads, flat, initial, tag, train_ids = {}, {}, {}, {}, {}
    rng = np.random.default_rng(protocol['seed'])
    for mode, rows in all_rows.items():
        training = [r for r in rows if r['split'] == 'train']
        train_ids[mode] = [r['id'] for r in training]
        x = [vectors[mode][r['id']] for r in training]
        heads[mode] = {key: fit_matrix(x, [r[key] for r in training], names, protocol['alpha'])
                       for key, names in (('force', net.FORCES), ('frame', net.FRAMES))}
        flat[mode] = {'labels': protocol['train_programs'], 'weights': fit_matrix(
            x, [r['program'] for r in training], protocol['train_programs'], protocol['alpha'])}
        initial[mode] = {key: rng.normal(0, .01, (4, net.WIDTH)).tolist() for key in ('force', 'frame')}
        tag[mode] = {'force': heads[mode]['force'], 'default_frame': Counter(r['frame'] for r in training).most_common(1)[0][0]}
    random_local = {mode: {key: np.random.default_rng(protocol['seed'] + index).normal(0, .01, (4, 4*net.shared.HIDDEN+1)).tolist()
                            for index,key in enumerate(('force','frame'))} for mode in all_rows}
    model = {'schema': 'ntl.ifadah-heads.v2', 'authority': 'NONE', 'heads': heads, 'local_heads': local_heads,
             'local_protocol_sha256': net.identity(net.DIRECTORY/'protocol_local.json'),
             'token_training_counts': token_counts,
             'encoder_sha256': net.identity(net.shared.MODEL), 'data_sha256': net.identity(net.DIRECTORY / 'data.json'),
             'protocol_sha256': net.identity(net.DIRECTORY / 'protocol.json'), 'train_ids': train_ids,
             'frozen_protocol_commit': 'fec22fd', 'binding': protocol['binding']}
    write(output / 'model.json', model)
    evaluations = {}
    for mode, rows in all_rows.items():
        measured = []
        for r in rows:
            x = vectors[mode][r['id']]
            scores = [sum(a*b for a,b in zip(w,x,strict=True)) for w in flat[mode]['weights']]
            flat_name = flat[mode]['labels'][max(range(len(scores)), key=lambda i: scores[i])]
            tag_force = net.predict(heads[mode], x)['force']
            tag_name = next((n for n, v in net.PROGRAMS.items() if v == (tag_force, tag[mode]['default_frame'])), None)
            predictions = {'untrained_heads': net.predict(initial[mode], x)['name'],
                           'flat_program_head': flat_name, 'force_tag_only': tag_name,
                           'factorized_program_heads': net.predict(heads[mode], x)['name'],
                           'local_program_heads': net.local_predict(local_heads[mode], encoder, r['text'])['name'],
                           'untrained_local_heads': net.local_predict(random_local[mode], encoder, r['text'])['name']}
            if mode == 'understand':
                owner = net.understand(r['text'], r['id'])
                checked = [a['name'] for a in owner['readings']]
                owner_exact = net.program(r['program'], r['subject'], r['predicate']) in [a['program'] for a in owner['readings']]
            else:
                # Known goal gold is used only for evaluation of the reference realization ceiling.
                rendered = net.realize(net.program(r['program'], r['subject'], r['predicate']))
                owner = net.understand(rendered, r['id'])
                owner_exact = net.program(r['program'], r['subject'], r['predicate']) in [a['program'] for a in owner['readings']]
                checked = [a['name'] for a in owner['readings']]
            proposed = predictions['local_program_heads']
            outcome = {'id': r['id'], 'split': r['split'], 'gold': r['program'], 'predictions': predictions,
                       'raw_correct': proposed == r['program'],
                       'force_correct': net.local_predict(local_heads[mode], encoder, r['text'])['force'] == r['force'],
                       'frame_correct': net.local_predict(local_heads[mode], encoder, r['text'])['frame'] == r['frame'],
                       'oracle_bindings': True, 'reference_owner_exact': owner_exact}
            if mode == 'understand':
                admitted = proposed in checked if proposed is not None else False
                outcome.update(admitted=admitted, false_admission=admitted and proposed != r['program'],
                               correct_abstention=not admitted and proposed != r['program'],
                               false_abstention=not admitted and proposed == r['program'])
            else:
                # Any well-typed proposal may roundtrip; this does NOT correct a misunderstood purpose.
                valid = proposed is not None
                realized = net.realize(net.program(proposed, r['subject'], r['predicate'])) if valid else None
                matches = bool(valid and any(a['program'] == net.program(proposed, r['subject'], r['predicate'])
                                            for a in net.understand(realized, r['id'])['readings']))
                outcome.update(realization_roundtrip=matches, goal_preserved=matches and proposed == r['program'])
            measured.append(outcome)
        summaries = {}
        for split in sorted({r['split'] for r in rows}):
            group = [r for r in measured if r['split'] == split]
            metrics = {'n': len(group), 'correct_by_model': {key: sum(r['predictions'][key] == r['gold'] for r in group)
                       for key in ('untrained_heads', 'flat_program_head', 'force_tag_only', 'factorized_program_heads', 'local_program_heads', 'untrained_local_heads')},
                       'force_correct': sum(r['force_correct'] for r in group),
                       'frame_correct': sum(r['frame_correct'] for r in group),
                       'exact_reader_ceiling': sum(r['reference_owner_exact'] for r in group)}
            for key in ('admitted', 'false_admission', 'correct_abstention', 'false_abstention',
                        'realization_roundtrip', 'goal_preserved'):
                if key in group[0]: metrics[key] = sum(r[key] for r in group)
            summaries[split] = metrics
        evaluations[mode] = {'summary': summaries, 'cases': measured}
    report = {'schema': 'ntl.ifadah-evaluation.v1', 'authority': 'EXPOSED_AUTHORED_DIAGNOSTIC',
              'protocol': protocol, 'local_protocol': local_protocol, 'local_protocol_commit': '14bab2d', 'model_sha256': net.identity(output/'model.json'),
              'data_sha256': model['data_sha256'], 'train_ids': train_ids, 'evaluation': evaluations,
              'frozen_protocol_commit': 'fec22fd', 'native_checked': False,
              'test_used_for_selection': True, 'test_used_for_parameter_fitting': False,
              'test_used_for_architecture_revision': True, 'general_arabic_mastery_established': False,
              'goal_owner_ceiling_uses_gold_program': True,
              'comparison_limits': ['FLAT_HEAD_CANNOT_NAME_UNTRAINED_COMBINATIONS',
                                    'EXACT_READER_IS_CEILING_NOT_LEARNED_COMPETITOR',
                                    'NO_COMPUTE_MATCHED_LLM_BASELINE',
                                    'ALL_BINDINGS_FROM_FIXED_LEXICAL_OWNER',
                                    'NO_INDEPENDENT_HUMAN_GOLD_OR_EXTERNAL_WORLD_WITNESS'],
              'code_sha256': {str(p.relative_to(net.shared.ROOT)):net.identity(p) for p in (Path(__file__), Path(net.__file__))},
              'runtime': {'python': __import__('platform').python_version(), 'numpy': np.__version__}}
    write(output/'evaluation.json', report)
    print(json.dumps({k:v['summary'] for k,v in evaluations.items()}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Output must be a new directory')
    train(args.output)


if __name__ == '__main__':
    main()
