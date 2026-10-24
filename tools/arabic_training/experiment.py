"""Reproducible CPU morphology training, with a single final test evaluation."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import resource
import subprocess
import time

import numpy as np
import torch
from torch import nn

from .data import ROOT, TASKS, DATA_SHA256, book_evidence, read_source, sha, source_constraints
from .model import MorphologyModel, load_weights, save_weights


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def vocabulary(examples):
    if any(e['split'] != 'train' for e in examples):
        raise ValueError('vocabulary may see training examples only')
    words = sorted({w['text'] for e in examples for w in e['words']})
    chars = sorted({c for w in words for c in w})
    labels = {task: sorted({w['labels'][task] for e in examples for w in e['words'] if w['labels'][task] is not None}) for task in TASKS}
    affixes = sorted({a for e in examples for w in e['words'] for a in (w['affixes'] or [])})
    return dict(words=['<PAD>', '<UNK>', *words], chars=['<PAD>', '<UNK>', *chars], labels=labels, affixes=affixes)


def encode(examples, vocab):
    wi = {w: i for i, w in enumerate(vocab['words'])}
    ci = {w: i for i, w in enumerate(vocab['chars'])}
    li = {t: {w: i for i, w in enumerate(vocab['labels'][t])} for t in TASKS}
    ai = {a: i for i, a in enumerate(vocab['affixes'])}
    result = []
    for e in examples:
        item = dict(example=e, words=[wi.get(w['text'], 1) for w in e['words']],
                    chars=[[ci.get(c, 1) for c in w['text'][:32]] for w in e['words']],
                    labels={t: [li[t].get(w['labels'][t], -100) for w in e['words']] for t in TASKS},
                    affixes=[[ai[a] for a in w['affixes'] if a in ai] if w['affixes'] is not None else None for w in e['words']])
        result.append(item)
    return result


def batches(encoded, batch_size, rng=None):
    order = sorted(range(len(encoded)), key=lambda i: len(encoded[i]['words']))
    groups = [order[i:i+batch_size] for i in range(0, len(order), batch_size)]
    if rng is not None:
        rng.shuffle(groups)
    for indices in groups:
        yield [encoded[i] for i in indices]


def collate(items, num_affixes):
    b = len(items)
    t = max(len(x['words']) for x in items)
    c = max(3, max(len(w) for x in items for w in x['chars']))
    words = torch.zeros((b, t), dtype=torch.long)
    chars = torch.zeros((b, t, c), dtype=torch.long)
    labels = {task: torch.full((b, t), -100, dtype=torch.long) for task in TASKS}
    affixes = torch.zeros((b, t, num_affixes), dtype=torch.float32)
    affix_mask = torch.zeros((b, t), dtype=torch.bool)
    for i, item in enumerate(items):
        n = len(item['words'])
        words[i, :n] = torch.tensor(item['words'])
        for j, cs in enumerate(item['chars']):
            chars[i, j, :len(cs)] = torch.tensor(cs)
        for task in TASKS:
            labels[task][i, :n] = torch.tensor(item['labels'][task])
        for j, xs in enumerate(item['affixes']):
            if xs is not None:
                affix_mask[i, j] = True
                affixes[i, j, xs] = 1
    return words, chars, torch.tensor([len(x['words']) for x in items]), labels, affixes, affix_mask


@torch.no_grad()
def predict(model, encoded, vocab, *, batch_size=24):
    model.eval()
    result = {}
    for items in batches(encoded, batch_size):
        words, chars, lengths, _, _, _ = collate(items, len(vocab['affixes']))
        logits = model(words, chars, lengths)
        predicted = {t: logits[t].argmax(dim=-1).tolist() for t in TASKS}
        affix_prob = torch.sigmoid(logits['affixes']).cpu().numpy()
        for i, item in enumerate(items):
            rows = []
            for j in range(len(item['words'])):
                row = {t: vocab['labels'][t][predicted[t][i][j]] for t in TASKS}
                row['affixes'] = [a for a, p in zip(vocab['affixes'], affix_prob[i, j], strict=True) if p >= 0.5]
                rows.append(row)
            result[item['example']['id']] = rows
    return result


def scalar_metrics(pairs):
    if not pairs:
        return dict(total=0, correct=0, accuracy=None, macro_f1=None, per_class={})
    labels = sorted({g for g, _ in pairs} | {p for _, p in pairs})
    counts = {}
    for label in labels:
        tp = sum(g == label and p == label for g, p in pairs)
        fp = sum(g != label and p == label for g, p in pairs)
        fn = sum(g == label and p != label for g, p in pairs)
        counts[label] = dict(support=sum(g == label for g, _ in pairs),
                             precision=tp/(tp+fp) if tp+fp else 0,
                             recall=tp/(tp+fn) if tp+fn else 0,
                             f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
    # Macro denominator is gold-present classes. Prediction-only errors still
    # enter precision/false negatives and accuracy, never disappear.
    present = [v for v in counts.values() if v['support']]
    correct = sum(g == p for g, p in pairs)
    return dict(total=len(pairs), correct=correct, accuracy=correct/len(pairs),
                macro_f1=sum(v['f1'] for v in present)/len(present), per_class=counts)


def evaluate(examples, predictions, training_words):
    pairs = {t: [] for t in TASKS}
    novel = {t: [] for t in TASKS}
    grouped = {t: defaultdict(lambda: [0, 0]) for t in TASKS}
    joint = [0, 0]
    aff = dict(tp=0, fp=0, fn=0, exact=0, total=0)
    conflicts = 0
    for e in examples:
        if e['id'] not in predictions or len(predictions[e['id']]) != len(e['words']):
            raise ValueError('prediction denominator mismatch')
        for word, pred in zip(e['words'], predictions[e['id']], strict=True):
            if source_constraints(pred['tag'], pred['declension'], pred['case_mood']):
                conflicts += 1
            all_present = all(word['labels'][t] is not None for t in TASKS)
            if all_present:
                joint[1] += 1
                joint[0] += all(word['labels'][t] == pred[t] for t in TASKS)
            for task in TASKS:
                gold = word['labels'][task]
                if gold is None:
                    continue
                pairs[task].append((gold, pred[task]))
                grouped[task][e['sura']][0] += int(gold == pred[task])
                grouped[task][e['sura']][1] += 1
                if word['text'] not in training_words:
                    novel[task].append((gold, pred[task]))
            if word['affixes'] is not None:
                gold, proposed = set(word['affixes']), set(pred['affixes'])
                aff['tp'] += len(gold & proposed)
                aff['fp'] += len(proposed - gold)
                aff['fn'] += len(gold - proposed)
                aff['exact'] += int(gold == proposed)
                aff['total'] += 1
    aff['micro_f1'] = 2*aff['tp']/(2*aff['tp']+aff['fp']+aff['fn']) if aff['tp']+aff['fp']+aff['fn'] else None
    aff['exact_set_accuracy'] = aff['exact']/aff['total'] if aff['total'] else None
    return dict(tasks={t: scalar_metrics(pairs[t]) for t in TASKS},
                unseen_surface={t: scalar_metrics(novel[t]) for t in TASKS}, affixes=aff,
                joint=dict(correct=joint[0], total=joint[1], accuracy=joint[0]/joint[1] if joint[1] else None),
                source_constraint_conflicts=conflicts,
                by_sura={t: dict(grouped[t]) for t in TASKS})


def baseline_tables(train):
    global_counts = {t: Counter() for t in TASKS}
    words = {t: defaultdict(Counter) for t in TASKS}
    affixes = defaultdict(Counter)
    for e in train:
        for word in e['words']:
            for task in TASKS:
                value = word['labels'][task]
                if value is not None:
                    global_counts[task][value] += 1
                    words[task][word['text']][value] += 1
            if word['affixes'] is not None:
                affixes[word['text']][tuple(word['affixes'])] += 1
    return global_counts, words, affixes


def baseline_predict(examples, tables, *, lexical):
    counts, words, affixes = tables
    global_best = {t: counts[t].most_common(1)[0][0] for t in TASKS}
    result = {}
    for e in examples:
        result[e['id']] = []
        for word in e['words']:
            row = {t: words[t][word['text']].most_common(1)[0][0] if lexical and word['text'] in words[t] else global_best[t] for t in TASKS}
            row['affixes'] = list(affixes[word['text']].most_common(1)[0][0]) if lexical and word['text'] in affixes else []
            result[e['id']].append(row)
    return result


def paired_intervals(neural, baseline, *, samples=2000, seed=971):
    """Paired bootstrap of whole suras; no treating tokens as independent."""
    rng = random.Random(seed)
    result = {}
    for task in TASKS:
        a, b = neural['by_sura'][task], baseline['by_sura'][task]
        groups = sorted(a)
        if len(groups) < 5:
            result[task] = dict(status='UNMEASURED', reason='fewer than five test suras')
            continue
        diffs = []
        for _ in range(samples):
            chosen = rng.choices(groups, k=len(groups))
            denominator = sum(a[k][1] for k in chosen)
            if any(a[k][1] != b[k][1] for k in chosen):
                raise ValueError('paired denominator mismatch')
            if denominator:
                diffs.append(sum(a[k][0]-b[k][0] for k in chosen)/denominator)
        diffs.sort()
        result[task] = dict(status='MEASURED', suras=len(groups), resamples=len(diffs),
                            accuracy_gain=neural['tasks'][task]['accuracy']-baseline['tasks'][task]['accuracy'],
                            lower_95=diffs[int(0.025*len(diffs))], upper_95=diffs[min(len(diffs)-1, int(0.975*len(diffs)))] )
    return result


def train(source, output, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    for name, maximum in [('threads',8),('batch_size',128),('epochs',100),('seed',2**31-1)]:
        if type(protocol[name]) is not int or not 1 <= protocol[name] <= maximum:
            raise ValueError('invalid protocol integer: ' + name)
    if type(protocol['learning_rate']) not in (float,int) or not 0 < protocol['learning_rate'] <= 0.1:
        raise ValueError('invalid learning rate')
    if protocol['source_sha256'] != DATA_SHA256:
        raise ValueError('protocol source identity mismatch')
    if set(protocol['task_weights']) != {*TASKS, 'affixes'} or any(type(x) not in (int,float) or not 0 < x <= 10 for x in protocol['task_weights'].values()):
        raise ValueError('invalid task weights')
    output.mkdir(parents=True, exist_ok=False)
    training_head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code_hashes = {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}
    torch.set_num_threads(protocol['threads'])
    torch.set_num_interop_threads(1)
    torch.manual_seed(protocol['seed'])
    torch.use_deterministic_algorithms(True)
    rng = random.Random(protocol['seed'])
    examples, manifest, conflicts = read_source(source)
    books = book_evidence()
    partitions = {s: [e for e in examples if e['split'] == s] for s in ('train', 'dev', 'test')}
    vocab = vocabulary(partitions['train'])
    encoded = {s: encode(partitions[s], vocab) for s in ('train', 'dev', 'test')}
    write_json(output / 'intake.json', manifest)
    write_json(output / 'annotation_conflicts.json', conflicts)
    write_json(output / 'book_evidence.json', books)
    write_json(output / 'vocabulary.json', vocab)
    split_receipt = {s: [dict(id=e['id'], text_sha256=sha('\n'.join(w['text'] for w in e['words']).encode())) for e in partitions[s]] for s in partitions}
    write_json(output / 'splits.json', split_receipt)
    write_json(output / 'protocol.json', protocol)
    model = MorphologyModel(vocab)
    save_weights(model, output / 'initial_weights.npz')
    optimizer = torch.optim.AdamW(model.parameters(), lr=protocol['learning_rate'], weight_decay=0.01)
    all_affixes = [w['affixes'] for e in partitions['train'] for w in e['words'] if w['affixes'] is not None]
    frequencies = Counter(a for xs in all_affixes for a in xs)
    positive_weights = torch.tensor([min(20, math.sqrt(len(all_affixes)/max(1, frequencies[a]))) for a in vocab['affixes']])
    affix_loss = nn.BCEWithLogitsLoss(pos_weight=positive_weights)
    history, best, best_epoch = [], -1.0, None
    optimizer_steps, empty_batches = 0, 0
    start = time.perf_counter()
    for epoch in range(1, protocol['epochs']+1):
        model.train()
        losses = []
        epoch_start = time.perf_counter()
        for items in batches(encoded['train'], protocol['batch_size'], rng):
            words, chars, lengths, labels, affixes, mask = collate(items, len(vocab['affixes']))
            if not mask.any() and not any((labels[t] != -100).any() for t in TASKS):
                empty_batches += 1
                continue
            # No label-informed dropout or sample selection.
            dropped = words.clone()
            dropped[(torch.rand(words.shape) < 0.1) & (words != 0)] = 1
            values = model(dropped, chars, lengths)
            loss = sum(nn.functional.cross_entropy(values[t].reshape(-1, values[t].shape[-1]), labels[t].reshape(-1)) * protocol['task_weights'][t]
                       for t in TASKS if (labels[t] != -100).any())
            if mask.any():
                loss = loss + protocol['task_weights']['affixes'] * affix_loss(values['affixes'][mask], affixes[mask])
            if not torch.isfinite(loss):
                raise RuntimeError('nonfinite training loss')
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            optimizer_steps += 1
            losses.append(float(loss.detach()))
        dev_predictions = predict(model, encoded['dev'], vocab, batch_size=protocol['batch_size'])
        dev = evaluate(partitions['dev'], dev_predictions, set(vocab['words']))
        selection = sum(dev['tasks'][t]['macro_f1'] for t in TASKS) / len(TASKS)
        row = dict(epoch=epoch, mean_batch_loss=sum(losses)/len(losses), seconds=time.perf_counter()-epoch_start,
                   dev={t: {k: dev['tasks'][t][k] for k in ('accuracy','macro_f1','total')} for t in TASKS},
                   dev_affix_micro_f1=dev['affixes']['micro_f1'], selection_score=selection)
        history.append(row)
        write_json(output / 'learning_curve.json', history)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if selection > best:
            best, best_epoch = selection, epoch
            save_weights(model, output / 'weights.npz')
    training_seconds = time.perf_counter() - start
    # Test predictions are first requested only after the final checkpoint has
    # been selected by development scores. No test-based reranking or tuning.
    load_weights(model, output / 'weights.npz')
    inference_start = time.perf_counter()
    predictions = predict(model, encoded['test'], vocab, batch_size=protocol['batch_size'])
    inference_seconds = time.perf_counter() - inference_start
    neural = evaluate(partitions['test'], predictions, set(vocab['words']))
    tables = baseline_tables(partitions['train'])
    majority = evaluate(partitions['test'], baseline_predict(partitions['test'], tables, lexical=False), set(vocab['words']))
    lexical = evaluate(partitions['test'], baseline_predict(partitions['test'], tables, lexical=True), set(vocab['words']))
    trained_state = {k:v.detach().clone() for k,v in model.state_dict().items()}
    load_weights(model, output / 'initial_weights.npz')
    weight_change_l2 = sum(float((trained_state[k]-v).square().sum()) for k,v in model.state_dict().items())**0.5
    initial = evaluate(partitions['test'], predict(model, encoded['test'], vocab, batch_size=protocol['batch_size']), set(vocab['words']))
    with (output / 'test_predictions.jsonl').open('w', encoding='utf-8') as stream:
        for e in partitions['test']:
            for word, prediction in zip(e['words'], predictions[e['id']], strict=True):
                stream.write(json.dumps(dict(address=word['address'], csv_rows=word['csv_rows'], text_sha256=word['text_sha256'],
                                            gold=word['labels'], affix_gold=word['affixes'], prediction=prediction,
                                            excluded_reasons=word['excluded_reasons'],
                                            status='UNVERIFIED_MORPHOLOGY_PROPOSAL'), ensure_ascii=False, sort_keys=True)+'\n')
    report = dict(schema='nabt.source-morphology-training.v1', created_utc=datetime.now(timezone.utc).isoformat(),
                  head=training_head, code_sha256=code_hashes,
                  torch_version=torch.__version__, parameters=sum(p.numel() for p in model.parameters()),
                  device='cpu', threads=protocol['threads'], training_seconds=training_seconds,
                  optimizer_steps=optimizer_steps, skipped_empty_batches=empty_batches,
                  selected_weight_change_l2=weight_change_l2, peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  test_inference_seconds=inference_seconds, chosen_epoch=best_epoch,
                  test=dict(neural=neural, lexical_baseline=lexical, majority_baseline=majority, initial_network=initial),
                  paired_accuracy_intervals=paired_intervals(neural,lexical),
                  source_sha256=manifest['source_sha256'], model_sha256=sha((output/'weights.npz').read_bytes()),
                  protocol_sha256=sha(protocol_path.read_bytes()),
                  limits=dict(all_arabic_complete=False, world_truth_established=False,
                              neural_syntactic_or_semantic_training=False, independent_human_review=False,
                              unseen_suras=True, root_ood=False, template_ood=False, new_blind_independent_corpus=False,
                              segmentation_learned=False, training_data_is_source_mirror=True))
    write_json(output / 'RESULTS.json', report)
    print(json.dumps({k:report[k] for k in ('parameters','chosen_epoch','training_seconds','test_inference_seconds')}) ,flush=True)
    return report
