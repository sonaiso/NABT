"""Frozen-protocol CPU experiment; native Lean owns the finite reading relation."""
from collections import Counter, defaultdict
import copy
import json
from pathlib import Path
import random
import resource
import subprocess
import time

import numpy as np
import torch
from torch import nn

from tools.arabic_training.data import ROOT, sha
from tools.arabic_training.experiment import scalar_metrics
from tools.arabic_training.model import save_weights, load_weights
from .data import export_teacher, index_teacher, native_checks, prepare
from .model import QatrModel

CASE_LABELS=['nasb','raf','jarr','jazm']


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def vocabulary(train,teacher):
    if any(e['split']!='train' for e in train):
        raise ValueError('vocabulary requires training split only')
    words=sorted({w['text'] for e in train for w in e['words']})
    # Closed formal output vocabulary, declared before seeing any corpus labels.
    readings=sorted(k for k,v in index_teacher(teacher).items() if v['rows'])
    return dict(words=['<PAD>','<UNK>',*words],chars=['<PAD>','<UNK>',*sorted(set(''.join(words)))],readings=readings)


def encode(examples,vocab):
    wi={v:i for i,v in enumerate(vocab['words'])};ci={v:i for i,v in enumerate(vocab['chars'])}
    li={v:i for i,v in enumerate(vocab['readings'])}
    return [dict(example=e,words=[wi.get(w['text'],1) for w in e['words']],
                 chars=[[ci.get(c,1) for c in w['text'][:32]] for w in e['words']],
                 readings=[li.get(w['qatr'],-100) for w in e['words']],
                 cases=[CASE_LABELS.index(w['case']) if w['case'] is not None else -100 for w in e['words']]) for e in examples]


def batches(items,size,rng=None):
    order=sorted(range(len(items)),key=lambda i:len(items[i]['words']))
    groups=[order[i:i+size] for i in range(0,len(order),size)]
    if rng:rng.shuffle(groups)
    for group in groups:yield [items[i] for i in group]


def collate(items):
    b=len(items);t=max(len(x['words']) for x in items)
    c=max(3,max(len(w) for x in items for w in x['chars']))
    words=torch.zeros((b,t),dtype=torch.long);chars=torch.zeros((b,t,c),dtype=torch.long)
    readings=torch.full((b,t),-100,dtype=torch.long);cases=torch.full((b,t),-100,dtype=torch.long)
    for i,item in enumerate(items):
        n=len(item['words']);words[i,:n]=torch.tensor(item['words'])
        for j,cs in enumerate(item['chars']):chars[i,j,:len(cs)]=torch.tensor(cs)
        readings[i,:n]=torch.tensor(item['readings']);cases[i,:n]=torch.tensor(item['cases'])
    return words,chars,torch.tensor([len(x['words']) for x in items]),readings,cases


@torch.no_grad()
def predict(model,items,vocab):
    model.eval();out={}
    for group in batches(items,24):
        words,chars,lengths,_,_=collate(group)
        a,b=model(words,chars,lengths)
        readings=a.argmax(-1).tolist();cases=b.argmax(-1).tolist()
        for i,item in enumerate(group):
            out[item['example']['id']]=[(vocab['readings'][readings[i][j]],CASE_LABELS[cases[i][j]]) for j in range(len(item['words']))]
    return out


def baselines(train,part):
    globals_=[Counter(),Counter()];tables=[defaultdict(Counter),defaultdict(Counter)]
    for e in train:
        for w in e['words']:
            for i,key in enumerate(['qatr','case']):
                if w[key] is not None:
                    globals_[i][w[key]]+=1;tables[i][w['text']][w[key]]+=1
    result={}
    for lexical in (False,True):
        result['lexical' if lexical else 'majority']={e['id']:[tuple((tables[i][w['text']] if lexical and w['text'] in tables[i] else globals_[i]).most_common(1)[0][0] for i in range(2)) for w in e['words']] for e in part}
    return result


def evaluate(part,pred,teacher,train_words):
    lookup=index_teacher(teacher);rp=[];cp=[];novel=[];covered=0;total=0;annotated=0;kept=0;subset=0
    by_sura=defaultdict(lambda:[0,0]);ambiguous=[0,0]
    for e in part:
        if len(pred[e['id']])!=len(e['words']):raise ValueError('prediction denominator')
        for w,(r,c) in zip(e['words'],pred[e['id']],strict=True):
            if w['qatr'] is None:continue
            gold=lookup[w['qatr']];proposal=lookup[r]
            correct=w['qatr']==r;rp.append((w['qatr'],r));total+=1
            by_sura[str(e['sura'])][0]+=correct;by_sura[str(e['sura'])][1]+=1
            gold_rows={x['id'] for x in gold['rows']};pred_rows={x['id'] for x in proposal['rows']}
            kept+=len(gold_rows&pred_rows);subset+=len(gold_rows)
            if len(gold['cases'])>1:ambiguous[0]+=correct;ambiguous[1]+=1
            if w['text'] not in train_words:novel.append((w['qatr'],r))
            if w['case'] is not None:
                cp.append((w['case'],c));annotated+=1;covered+=w['case'] in proposal['cases']
    return dict(reading_set=scalar_metrics(rp),case_ranking=scalar_metrics(cp),
                unseen_surface_reading_set=scalar_metrics(novel),
                compatible_row_recall=kept/subset if subset else None,
                annotated_case_retained=dict(correct=covered,total=annotated,recall=covered/annotated if annotated else None),
                ambiguous_reading_set=dict(correct=ambiguous[0],total=ambiguous[1],accuracy=ambiguous[0]/ambiguous[1] if ambiguous[1] else None),
                by_sura=dict(by_sura))


def interval(neural,baseline):
    rng=random.Random(971);groups=sorted(neural['by_sura']);d=[]
    for _ in range(2000):
        selected=rng.choices(groups,k=len(groups))
        a=sum(neural['by_sura'][s][0] for s in selected);b=sum(baseline['by_sura'][s][0] for s in selected)
        n=sum(neural['by_sura'][s][1] for s in selected)
        d.append((a-b)/n)
    d.sort();return dict(unit='whole sura',samples=2000,low=d[49],high=d[1949])


def verify_predictions(executable,part,pred,teacher):
    lookup=index_teacher(teacher);requests=[]
    for e in part:
        for w,(r,_) in zip(e['words'],pred[e['id']],strict=True):
            if w['qatr'] is None:continue
            q=lookup[w['qatr']]
            requests.append(dict(kind=q['kind'],mark=q['mark'],classes=None,
                                 proposed=[x['id'] for x in lookup[r]['rows']]))
    replies=native_checks(executable,requests)
    accepted=sum(x.get('complete_proposal') is True for x in replies)
    if any('complete_proposal' not in x for x in replies):raise ValueError('native validation error')
    return dict(checked=len(replies),conditional_exact_set_accepted=accepted,
                conditional_set_rejected=len(replies)-accepted,
                authority='CONDITIONAL_TABLE_ONLY; independent corpus premises supplied by evaluator',
                linguistic_certificates_accepted=0,world_truth_established=False)


def book_evaluation(model,vocab,teacher):
    book=json.loads((ROOT/'evidence/qatr_lean_training/book_probe.json').read_text())
    raw=(ROOT/'src/nabt/data/source_evidence/qatr.txt').read_bytes()
    examples=[]
    for i,row in enumerate(book['examples']):
        if sha(raw)!=row['source_sha256'] or raw[row['source_start']:row['source_end']].decode()!=row['literal']:
            raise ValueError('book probe source binding changed')
        words=[dict(text=s,qatr=None,case=None) for s in row['editorial'].split()]
        words[row['target']].update(qatr=row['label'],case=row['case'])
        examples.append(dict(id=row['id'],sura=i,words=words))
    predictions=predict(model,encode(examples,vocab),vocab)
    records=[dict(id=r['id'],target=r['target'],expected=r['label'],
                  proposed=predictions[r['id']][r['target']][0],
                  proposed_case=predictions[r['id']][r['target']][1]) for r in book['examples']]
    return dict(scope=book['scope'],metrics=evaluate(examples,predictions,teacher,set(vocab['words'][2:])),records=records)


def source_code_manifest(output):
    paths=sorted([*ROOT.glob('tools/qatr_training/*.py'),ROOT/'tools/train_qatr_readings.py',
                  ROOT/'tools/arabic_training/data.py',ROOT/'tools/arabic_training/model.py',
                  ROOT/'tools/arabic_training/experiment.py',ROOT/'formal/Nabt/QatrReading.lean',
                  ROOT/'formal/QatrReadingMain.lean',ROOT/'formal/Nabt/Words.lean',
                  ROOT/'formal/Nabt/InflectionEvidence.lean',ROOT/'formal/Nabt/QatrRules.lean',ROOT/'formal/ProbeJson.lean',
                  ROOT/'evidence/qatr_lean_training/book_probe.json',ROOT/'evidence/qatr_lean_training/source_coverage.json'])
    manifest={}
    for p in paths:
        rel=str(p.relative_to(ROOT));raw=p.read_bytes();manifest[rel]=sha(raw)
        dest=output/'code_snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    write(output/'code_manifest.json',manifest)


def train(source,executable,output,protocol_path):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    protocol=json.loads(Path(protocol_path).read_text());write(output/'protocol.json',protocol)
    source_code_manifest(output)
    teacher=export_teacher(executable);write(output/'lean_teacher.json',teacher)
    examples,intake=prepare(source,teacher);write(output/'intake.json',intake)
    parts={s:[e for e in examples if e['split']==s] for s in ('train','dev','test')}
    vocab=vocabulary(parts['train'],teacher);write(output/'vocab.json',vocab)
    data={s:encode(part,vocab) for s,part in parts.items()}
    torch.set_num_threads(protocol['threads']);torch.manual_seed(protocol['seed']);np.random.seed(protocol['seed']);random.seed(protocol['seed'])
    torch.use_deterministic_algorithms(True)
    model=QatrModel(vocab);save_weights(model,output/'initial_weights.npz')
    counts=Counter(i for e in data['train'] for i in e['readings'] if i!=-100)
    # Sqrt inverse frequency, normalized and capped; fixed before training.
    weight=torch.tensor([1/(max(1,counts[i])**0.5) for i in range(len(vocab['readings']))])
    weight=(weight/weight.mean()).clamp(max=5)
    criterion=nn.CrossEntropyLoss(weight=weight);case_criterion=nn.CrossEntropyLoss()
    optimizer=torch.optim.AdamW(model.parameters(),lr=protocol['learning_rate'],weight_decay=0.01)
    training_words=set(vocab['words'][2:]);rng=random.Random(protocol['seed'])
    curve=[];best=-1;best_epoch=None;updates=0;started=time.monotonic()
    initial=evaluate(parts['dev'],predict(model,data['dev'],vocab),teacher,training_words)
    write(output/'initial_dev.json',initial)
    for epoch in range(1,protocol['epochs']+1):
        model.train();loss_sum=0;steps=0
        for group in batches(data['train'],protocol['batch_size'],rng):
            words,chars,lengths,y,c=collate(group)
            if not (y!=-100).any():continue
            a,b=model(words,chars,lengths)
            loss=criterion(a.reshape(-1,a.shape[-1]),y.reshape(-1))
            if (c!=-100).any():loss=loss+protocol['case_loss_weight']*case_criterion(b.reshape(-1,4),c.reshape(-1))
            optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);optimizer.step()
            loss_sum+=float(loss.detach());updates+=1;steps+=1
        dev=evaluate(parts['dev'],predict(model,data['dev'],vocab),teacher,training_words)
        score=dev['reading_set']['macro_f1'];curve.append(dict(epoch=epoch,loss=loss_sum/steps,dev=dev))
        print(json.dumps(dict(epoch=epoch,dev_reading_macro_f1=score,dev_case_accuracy=dev['case_ranking']['accuracy'])),flush=True)
        if score>best:best=score;best_epoch=epoch;save_weights(model,output/'weights.npz')
        write(output/'curve.json',curve)
    elapsed=time.monotonic()-started;load_weights(model,output/'weights.npz')
    predictions=predict(model,data['test'],vocab)
    bas=baselines(parts['train'],parts['test'])
    metrics=evaluate(parts['test'],predictions,teacher,training_words)
    baseline_metrics={k:evaluate(parts['test'],v,teacher,training_words) for k,v in bas.items()}
    verification=verify_predictions(executable,parts['test'],predictions,teacher)
    book=book_evaluation(model,vocab,teacher);write(output/'book_results.json',book)
    if verification['conditional_exact_set_accepted']!=metrics['reading_set']['correct']:
        raise ValueError('native and evaluation mismatch')
    with (output/'test_predictions.jsonl').open('w') as stream:
        for e in parts['test']:
            for w,pr in zip(e['words'],predictions[e['id']],strict=True):
                if w['qatr'] is None:continue
                stream.write(json.dumps(dict(address=w['address'],csv_rows=w['csv_rows'],text_sha256=w['text_sha256'],
                    gold_reading=w['qatr'],gold_case=w['case'],reading=pr[0],case_ranking=pr[1],
                    authority='NONE'),ensure_ascii=False)+'\n')
    result=dict(schema='nabt.qatr-lean-training.v1',protocol=protocol,selected_epoch=best_epoch,
                code_commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip(),
                parameters=sum(p.numel() for p in model.parameters()),updates=updates,training_seconds=elapsed,
                max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,torch_version=torch.__version__,
                numpy_version=np.__version__,cuda_available=torch.cuda.is_available(),
                initial_dev=initial['reading_set'],test=metrics,baselines=baseline_metrics,
                paired_reading_accuracy_difference_ci95=interval(metrics,baseline_metrics['lexical']),
                native_verification=verification,weights_sha256=sha((output/'weights.npz').read_bytes()),
                book_probe=book['metrics']['reading_set'],
                test_status='OBSERVED_REGRESSION_NOT_BLIND',arabic_complete=False,
                qatr_book_complete=False,semantic_coverage_measured=False,world_truth_established=False,
                authority='NONE',runtime_acceptance_changed=False)
    write(output/'RESULTS.json',result)
    print(json.dumps({k:result[k] for k in ['parameters','updates','training_seconds','selected_epoch','native_verification']}),flush=True)


def replay(source,executable,model_dir):
    model_dir=Path(model_dir)
    manifest=json.loads((model_dir/'code_manifest.json').read_text())
    for rel,digest in manifest.items():
        if sha((ROOT/rel).read_bytes())!=digest or sha((model_dir/'code_snapshot'/rel).read_bytes())!=digest:
            raise ValueError('experiment implementation changed: '+rel)
    teacher=export_teacher(executable)
    if teacher!=json.loads((model_dir/'lean_teacher.json').read_text()):raise ValueError('Lean teacher mismatch')
    examples,intake=prepare(source,teacher)
    if intake!=json.loads((model_dir/'intake.json').read_text()):raise ValueError('intake mismatch')
    result=json.loads((model_dir/'RESULTS.json').read_text());vocab=json.loads((model_dir/'vocab.json').read_text())
    if sha((model_dir/'weights.npz').read_bytes())!=result['weights_sha256']:raise ValueError('weights changed')
    torch.set_num_threads(result['protocol']['threads']);torch.use_deterministic_algorithms(True)
    model=QatrModel(vocab);load_weights(model,model_dir/'weights.npz')
    test=[e for e in examples if e['split']=='test'];train_part=[e for e in examples if e['split']=='train']
    if vocabulary(train_part,teacher)!=vocab:raise ValueError('vocabulary mismatch')
    predictions=predict(model,encode(test,vocab),vocab)
    metrics=evaluate(test,predictions,teacher,set(vocab['words'][2:]))
    if metrics!=result['test']:raise ValueError('prediction metrics differ')
    saved=[json.loads(line) for line in (model_dir/'test_predictions.jsonl').read_text().splitlines()]
    actual=[]
    for e in test:
        for w,p in zip(e['words'],predictions[e['id']],strict=True):
            if w['qatr'] is not None:actual.append((w['address'],p[0],p[1]))
    if actual!=[(r['address'],r['reading'],r['case_ranking']) for r in saved]:raise ValueError('prediction records differ')
    base={k:evaluate(test,v,teacher,set(vocab['words'][2:])) for k,v in baselines(train_part,test).items()}
    if base!=result['baselines']:raise ValueError('baseline mismatch')
    native=verify_predictions(executable,test,predictions,teacher)
    if native!=result['native_verification']:raise ValueError('native result mismatch')
    if book_evaluation(model,vocab,teacher)!=json.loads((model_dir/'book_results.json').read_text()):
        raise ValueError('book probe replay mismatch')
    return dict(ok=True,words=len(actual),native=native,weights_sha256=result['weights_sha256'])
