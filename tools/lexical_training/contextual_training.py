"""Train one shared encoder for contextual occurrences plus the existing tasks.

The final epoch is fixed. Validation alone chooses abstention thresholds. The
retained test is evaluated once afterward, including every failure and unknown.
"""
import argparse
from copy import deepcopy
from difflib import SequenceMatcher
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json

from . import contextual_alignment as runtime, contextual_data as data
from . import shared_encoder as shared, shared_training as previous

PROTOCOL = {"id":"nabt.contextual-alignment-training.v1", "seed":117, "epochs":120,
            "learning_rate":0.003, "selection":"FIXED_FINAL_EPOCH",
            "initialization":"INSTALLED_SHARED_V1_WEIGHTS",
            "supervision":"AUTHORED_EXACT_OCCURRENCES_WITH_NATIVE_DEFINITION_IDS",
            "validation":"F1_MAXIMUM_WITH_BACKGROUND_FALSE_POSITIVE_RATE_AT_MOST_0.10",
            "threshold_grid":[0.0,0.2,0.35,0.5,0.65,0.8,1.0], "margin_grid":[0.0,0.05,0.1,0.2,1.0],
            "test_selection":False, "independent_semantic_adjudication":False}


def make_model(base):
    import torch
    model=previous.torch_model(base["labels"])
    model.load_state_dict({k:torch.tensor(v,dtype=torch.float32) for k,v in base["parameters"].items()})
    model.alignment=torch.nn.Linear(4*shared.HIDDEN, len(base["labels"]["concept"])+1)
    return model


def trajectories(model,texts,reverse=False):
    import torch
    encoded=[shared.byte_ids(text) for text in texts]
    if reverse:
        encoded=[list(reversed(row)) for row in encoded]
    lengths=torch.tensor([len(row) for row in encoded])
    tokens=torch.zeros((len(texts),int(lengths.max())),dtype=torch.long)
    for i,row in enumerate(encoded):tokens[i,:len(row)]=torch.tensor(row)
    packed=torch.nn.utils.rnn.pack_padded_sequence(model.embedding(tokens),lengths,batch_first=True,enforce_sorted=False)
    output,hidden=model.gru(packed)
    padded,_=torch.nn.utils.rnn.pad_packed_sequence(output,batch_first=True)
    return torch.cat((torch.zeros(len(texts),1,shared.HIDDEN),padded),dim=1), hidden[0]


def score_occurrences(model,rows):
    import torch
    from tools.grammar_catalog.operations import exact_terms
    texts=[r["text"] for r in rows]
    forward,_=trajectories(model,texts)
    reverse,_=trajectories(model,texts,reverse=True)
    features=[]
    for i,text in enumerate(texts):
        length=len(text.encode())
        for term in exact_terms(text):
            start,end=term["utf8_span"]
            features.append(torch.cat((forward[i,start],forward[i,end],reverse[i,length-end],reverse[i,length-start])))
    return model.alignment(torch.stack(features))


def summarize(rows,scores,model):
    tp=fp=fn=background=background_fp=ranked=positive=0
    predictions=[]
    for row,values in zip(rows,scores):
        d=runtime.decide(model,values)
        gold=row["gold"];is_positive=runtime.NULL not in gold
        correct=d["proposed_id"] in gold
        positive+=is_positive; ranked+=int(is_positive and d["top_label"] in gold)
        tp+=int(is_positive and correct)
        fp+=int(d["proposed_id"] is not None and not correct)
        fn+=int(is_positive and not correct)
        background+=not is_positive
        background_fp+=int(not is_positive and d["proposed_id"] is not None)
        predictions.append({**row,"status":d["status"],"proposed_id":d["proposed_id"],
                            "top_label":d["top_label"],"margin":d["margin"],"scores":values,
                            "correct":bool(correct) if is_positive else d["proposed_id"] is None})
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    return {"tokens":len(rows),"gold_mentions":positive,"true_positive":tp,"false_positive":fp,
            "false_negative":fn,"precision":precision,"recall":recall,
            "f1":2*precision*recall/(precision+recall) if precision+recall else 0.0,
            "mention_top1_correct":ranked,"background_tokens":background,
            "background_false_positive":background_fp},predictions


def calibrate(rows,scores,model):
    best=None
    for threshold in PROTOCOL["threshold_grid"]:
        for margin in PROTOCOL["margin_grid"]:
            candidate=deepcopy(model)
            candidate["calibration"].update(min_probability=threshold,min_margin=margin)
            result,_=summarize(rows,scores,candidate)
            if result["background_false_positive"] > 0.10*result["background_tokens"]:continue
            key=(result["f1"],result["precision"],threshold,margin)
            if best is None or key>best[0]:best=(key,candidate["calibration"],result)
    if best is None:raise ValueError("No validation-only abstention setting")
    return best[1],best[2]


def exported(model,base,train,validation):
    value=deepcopy(base)
    value["parameters"]={k:v.detach().tolist() for k,v in model.state_dict().items() if not k.startswith("alignment.")}
    value["training_sha256"]=data.digest(train)
    value["protocol"]=PROTOCOL
    return {"schema":runtime.SCHEMA,"features":runtime.FEATURES,"shared_model":value,
            "alignment_labels":value["labels"]["concept"]+[runtime.NULL],
            "alignment_weight":model.alignment.weight.detach().tolist(),
            "alignment_bias":model.alignment.bias.detach().tolist(),
            "calibration":{"min_probability":0.0,"min_margin":0.0,"validation_sha256":data.digest(validation)},
            "protocol":PROTOCOL,"training_sha256":data.digest(train),"authority":"NONE"}


@lru_cache(maxsize=100000)
def similarity(left,right):return SequenceMatcher(None,left,right).ratio()


def nearest_scores(train_tokens,rows,labels):
    scores=[]
    for row in rows:
        nearest=max(train_tokens,key=lambda r:(2*similarity(row["surface"],r["surface"])+similarity(row["text"],r["text"]),r["id"]))
        scores.append([10.0 if label in nearest["gold"] else -10.0 for label in labels])
    return scores


def train_run(directory):
    import torch
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True);torch.manual_seed(PROTOCOL["seed"])
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    partitions=data.dataset()
    train,validation=partitions["train"],partitions["validation"]
    base,base_sha=shared.load_model()
    native=shared.concepts.catalogue()
    if base["concept_references"] != {r["identity"]["id"]:r["reference"] for r in native["concepts"]}:
        raise ValueError("Warm-start definitions are stale")
    model=make_model(base)
    initial=deepcopy(model.state_dict())
    labels=base["labels"]["concept"]+[runtime.NULL]
    train_tokens=data.token_rows(train)
    y=torch.zeros((len(train_tokens),len(labels)))
    positive=[];background=[]
    for i,row in enumerate(train_tokens):
        for label in row["gold"]:y[i,labels.index(label)]=1/len(row["gold"])
        (background if runtime.NULL in row["gold"] else positive).append(i)
    rehearsal,_,legacy_labels=previous.dataset()
    if legacy_labels!=base["labels"]:raise ValueError("Rehearsal labels changed")
    legacy_targets={};legacy_masks={}
    for h in shared.HEADS:
        mask=[i for i,r in enumerate(rehearsal) if h in r["labels"]]
        target=torch.zeros((len(mask),len(legacy_labels[h])))
        for j,i in enumerate(mask):
            gold=rehearsal[i]["labels"][h]
            for label in gold:target[j,legacy_labels[h].index(label)]=1/len(gold)
        legacy_targets[h]=target;legacy_masks[h]=mask
    optimizer=torch.optim.Adam(model.parameters(),lr=PROTOCOL["learning_rate"])
    history=[]
    for epoch in range(PROTOCOL["epochs"]):
        optimizer.zero_grad()
        scores=score_occurrences(model,train)
        losses=-(y*torch.log_softmax(scores,dim=1)).sum(dim=1)
        align_loss=(losses[positive].mean()+losses[background].mean())/2
        old=model([r["text"] for r in rehearsal])
        rehearsal_loss=sum(-(legacy_targets[h]*torch.log_softmax(old[h][legacy_masks[h]],dim=1)).sum(1).mean()
                           for h in shared.HEADS)/len(shared.HEADS)
        loss=align_loss+0.5*rehearsal_loss
        loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.0);optimizer.step()
        history.append({"epoch":epoch+1,"alignment_loss":float(align_loss.detach()),"rehearsal_loss":float(rehearsal_loss.detach())})
    model.eval()
    value=exported(model,base,train,validation)
    with torch.no_grad():validation_scores=score_occurrences(model,validation).tolist()
    value["calibration"],validation_metrics=calibrate(data.token_rows(validation),validation_scores,value)
    # No test statistic participates in fitting, epoch selection or calibration.
    test=partitions["test"];test_tokens=data.token_rows(test)
    with torch.no_grad():scores=score_occurrences(model,test).tolist()
    metrics,predictions=summarize(test_tokens,scores,value)
    nearest=nearest_scores(train_tokens,test_tokens,labels)
    baseline_model=deepcopy(value);baseline_model["calibration"].update(min_probability=0.0,min_margin=0.0)
    baseline,baseline_predictions=summarize(test_tokens,nearest,baseline_model)
    previous.save(directory/"model.json",value)
    portable,_=runtime.load_model(directory/"model.json")
    all_portable=[]
    for row in test:all_portable.extend(x["logits"] for x in runtime.occurrence_logits(portable,row["text"])[0])
    parity=max(abs(a-b) for left,right in zip(scores,all_portable) for a,b in zip(left,right))
    portable_metrics,portable_predictions=summarize(test_tokens,all_portable,value)
    if [r["proposed_id"] for r in predictions] != [r["proposed_id"] for r in portable_predictions]:
        raise ValueError("Portable inference changed a retained decision")
    delta=float(sum((v-initial[k]).square().sum() for k,v in model.state_dict().items()).sqrt())
    encoder_delta=float(sum((v-initial[k]).square().sum() for k,v in model.state_dict().items()
                            if k.startswith(("embedding.","gru."))).sqrt())
    if not encoder_delta>0 or not parity<1e-4:raise ValueError("Shared updates or portable parity failed")
    _,legacy_test,_=previous.dataset()
    with torch.no_grad():legacy_scores={h:v.tolist() for h,v in model([r["text"] for r in legacy_test]).items()}
    legacy_metrics={}
    for h in shared.HEADS:
        selected=[(i,r) for i,r in enumerate(legacy_test) if h in r["labels"]]
        legacy_metrics[h]={"n":len(selected),"top1_correct":sum(base["labels"][h][max(range(len(base["labels"][h])),key=lambda j:legacy_scores[h][i][j])] in r["labels"][h] for i,r in selected)}
    by_category={}
    for category in sorted({r["category"] for r in test_tokens}):
        inds=[i for i,r in enumerate(test_tokens) if r["category"]==category]
        by_category[category]=summarize([test_tokens[i] for i in inds],[scores[i] for i in inds],value)[0]
    report={"schema":"nabt.contextual-alignment-evaluation.v1","protocol":PROTOCOL,
            "partition_counts":{k:{"sentences":len(v),"tokens":len(data.token_rows(v)),"mentions":sum(len(r["annotations"]) for r in v)} for k,v in partitions.items()},
            "metrics":metrics,"nearest_context_baseline":baseline,"by_category":by_category,
            "validation_metrics":validation_metrics,"calibration":value["calibration"],
            "portable_metrics":portable_metrics,"portable_max_abs_error":parity,
            "legacy_exposed_diagnostic":legacy_metrics,"optimizer_steps":len(history),
            "parameters":sum(p.numel() for p in model.parameters()),"parameter_delta_l2":delta,
            "shared_encoder_delta_l2":encoder_delta,"history":history,"warm_start_sha256":base_sha,
            "partition_hashes":{k:data.digest(v) for k,v in partitions.items()},
            "weights_sha256":sha256((directory/"model.json").read_bytes()).hexdigest(),
            "torch_version":torch.__version__,"independent_semantic_adjudication":False,
            "unseen_senses_measured":False,"world_truth_established":False,"predictions_grant_authority":False}
    for name,obj in [("FIRST_TEST.json",report),("predictions.json",predictions),("baseline_predictions.json",baseline_predictions)]+[(k+".json",v) for k,v in partitions.items()]:
        previous.save(directory/name,obj)
    return {k:v for k,v in report.items() if k!="history"}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--run-dir",type=Path,required=True)
    args=parser.parse_args();print(json.dumps(train_run(args.run_dir),ensure_ascii=False,indent=2))


if __name__=="__main__":main()
