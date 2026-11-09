"""Fixed-protocol educational sense alignment, with a retained first test.

Only a linear head is fitted; the existing GRU and native schemas are frozen.
These authored samples do not establish independent lexical adjudication.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog.operations import exact_terms
from tools.grammar_catalog.relational_bridge import schema_catalogue
from . import relational_alignment as runtime, shared_encoder as shared
from .contextual_alignment import occurrence_vectors

PROTOCOL = {"id":"nabt.relational-ranking-training.v1", "seed":116117, "epochs":400,
            "learning_rate":0.035, "l2":0.001, "selection":"FIXED_FINAL_EPOCH",
            "features":"FROZEN_EXISTING_GRU_96_BOUNDARY_COORDINATES",
            "test_used_for_selection":False, "supervision":"AUTHORED_EDUCATIONAL_SENSE_ALIGNMENT",
            "native_schema_is_trainable":False, "independent_semantic_adjudication":False}

# Explicit authored labels, not generated from model output or runtime lookup.
LEXEMES = [("اصفرّ", ["اصفرار"]), ("اِصْفَرَّ", ["اصفرار"]),
           ("مُصْفَرّ", ["اصفرار"]), ("مصفرّ", ["اصفرار"]), ("اصفرار", ["اصفرار"]),
           ("كَبِرَ", ["كبر_السن"]), ("كبر_السن", ["كبر_السن"]),
           ("كَبُرَ", ["عظم"]), ("عظم", ["عظم"]), ("كبر", ["كبر_السن", "عظم"]),
           ("كتب", [runtime.NULL]), ("كبير", [runtime.NULL]), ("اللون", [runtime.NULL])]
TEMPLATES = {
    "train":["{}", "ورد {} هنا", "نتعلم {} اليوم", "مثالنا عن {}", "فسر {} في الدرس",
             "قال الطالب {}", "نناقش معنى {}", "تأمل {} جيدا"],
    "validation":["يتناول الحوار {} الآن", "نقرأ في الصفحة {}"],
    "test_context":["سأل المعلم عن {} صباحا", "لاحظنا استعمال {} في الشرح", "ناقشنا أمس لفظ {}"]}


def dataset():
    result = {}
    for split, templates in TEMPLATES.items():
        rows = []
        for ti, template in enumerate(templates):
            for li, (surface, labels) in enumerate(LEXEMES):
                text = template.format(surface); start = len(template.split("{}")[0])
                rows.append({"id":f"{split}:{ti}:{li}", "text":text, "surface":surface,
                             "span":[start, start+len(surface)], "gold":labels,
                             "provenance":"AUTHORED_EDUCATIONAL_EXAMPLE_NOT_SOURCE_TESTIMONY"})
        result[split] = rows
    # Known senses, spellings absent from fitting/validation; no new-root claim.
    result["test_spelling"] = [{"id":f"test_spelling:{i}", "text":"ناقش الصغار "+s,
                               "surface":s, "span":[12,12+len(s)], "gold":["اصفرار"],
                               "provenance":"AUTHORED_HELDOUT_SPELLING"}
                              for i,s in enumerate(["اصفر", "اصفرَّ", "مصفر"])]
    for row in result["test_spelling"]:
        row["span"] = [len("ناقش الصغار "), len(row["text"])]
    sets = [{r["text"] for r in rows} for rows in result.values()]
    if any(a & b for i,a in enumerate(sets) for b in sets[i+1:]):
        raise ValueError("Partition text leakage")
    return result


def features(base, rows, labels):
    import numpy as np
    vectors, targets, metadata = [], [], []
    for row in rows:
        if row["text"][slice(*row["span"])] != row["surface"]:
            raise ValueError("Authored occurrence boundary changed")
        tokens, _ = occurrence_vectors(base, row["text"])
        for token in tokens:
            gold = row["gold"] if token["codepoint_span"] == row["span"] else [runtime.NULL]
            vectors.append(token["vector"])
            targets.append([1/len(gold) if label in gold else 0 for label in labels])
            metadata.append({"id":row["id"], "text":row["text"], "surface":token["surface"],
                             "span":token["codepoint_span"], "gold":gold})
    return np.asarray(vectors), np.asarray(targets), metadata


def metrics(rows, scores, labels):
    predictions = []
    for row, score in zip(rows, scores, strict=True):
        label = labels[max(range(len(labels)), key=lambda i:(score[i], -i))]
        predictions.append({**row, "top_label":label, "correct":label in row["gold"]})
    positives = [r for r in predictions if runtime.NULL not in r["gold"]]
    background = [r for r in predictions if runtime.NULL in r["gold"]]
    return {"tokens":len(rows), "top1_correct":sum(r["correct"] for r in predictions),
            "positive_tokens":len(positives), "positive_top1_correct":sum(r["correct"] for r in positives),
            "background_tokens":len(background), "background_false_positive":sum(not r["correct"] for r in background)}, predictions


def save(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n")


def train_run(directory):
    import numpy as np
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    partitions = dataset(); meanings = runtime.definitions(schema_catalogue())
    labels = list(meanings)+[runtime.NULL]; base, base_sha = shared.load_model()
    # Record protocol and partitions before the optimizer or test evaluation.
    save(directory/"protocol.json", PROTOCOL)
    for name, rows in partitions.items(): save(directory/(name+".json"), rows)
    x, y, training_rows = features(base, partitions["train"], labels)
    mean, scale = x.mean(0), np.maximum(x.std(0), 0.02)
    z = (x-mean)/scale
    rng = np.random.default_rng(PROTOCOL["seed"])
    w = rng.normal(0,0.01,(len(labels),runtime.DIM)); b = np.zeros(len(labels)); initial=w.copy()
    m = np.zeros_like(w); v = m.copy(); mb = b.copy(); vb = b.copy()
    positive = y[:,-1] == 0
    sample = np.where(positive, .5/max(1,positive.sum()), .5/max(1,(~positive).sum()))
    history = []
    for epoch in range(1, PROTOCOL["epochs"]+1):
        score = z@w.T+b; score -= score.max(1,keepdims=True)
        prob = np.exp(score); prob /= prob.sum(1,keepdims=True)
        error = (prob-y)*sample[:,None]
        gw = error.T@z + PROTOCOL["l2"]*w; gb = error.sum(0)
        m=.9*m+.1*gw; v=.999*v+.001*gw*gw; mb=.9*mb+.1*gb; vb=.999*vb+.001*gb*gb
        rate=PROTOCOL["learning_rate"]
        w-=rate*(m/(1-.9**epoch))/(np.sqrt(v/(1-.999**epoch))+1e-8)
        b-=rate*(mb/(1-.9**epoch))/(np.sqrt(vb/(1-.999**epoch))+1e-8)
        if epoch == 1 or epoch % 50 == 0:
            history.append({"epoch":epoch,"cross_entropy":float(-(sample[:,None]*y*np.log(np.maximum(prob,1e-30))).sum())})
    model={"schema":runtime.SCHEMA, "authority":"NONE", "labels":labels,
           "shared_model_sha256":base_sha, "schema_sha256":runtime.digest(meanings),
           "mean":mean.tolist(), "scale":scale.tolist(), "weight":w.tolist(), "bias":b.tolist(),
           "protocol":PROTOCOL, "training_sha256":runtime.digest(partitions["train"])}
    save(directory/"model.json",model)
    report={"protocol":PROTOCOL, "partition_counts":{k:len(v) for k,v in partitions.items()},
            "partition_sha256":{k:runtime.digest(v) for k,v in partitions.items()},
            "parameter_delta_l2":float(np.linalg.norm(w-initial)), "encoder_parameter_delta_l2":0,
            "optimizer_steps":PROTOCOL["epochs"], "history":history, "metrics":{}, "exact_lookup_baseline":{},
            "numpy_version":np.__version__, "shared_model_sha256":base_sha,
            "model_sha256":sha256((directory/"model.json").read_bytes()).hexdigest(),
            "world_truth_established":False, "new_roots_measured":False, "independent_semantic_adjudication":False}
    seen={}
    for row in training_rows: seen.setdefault(row["surface"],set()).update(row["gold"])
    parity=0
    for split in ("validation","test_context","test_spelling"):
        f, _, rows = features(base,partitions[split],labels)
        scores=(f-mean)/scale@w.T+b
        portable=np.asarray([runtime.logits(model,vec) for vec in f.tolist()])
        parity=max(parity,float(np.max(np.abs(scores-portable))))
        result,predictions=metrics(rows,portable.tolist(),labels)
        report["metrics"][split]=result
        baseline=[[1.0 if label in seen.get(r["surface"],{runtime.NULL}) else 0.0 for label in labels] for r in rows]
        report["exact_lookup_baseline"][split]=metrics(rows,baseline,labels)[0]
        save(directory/(split+"_predictions.json"),predictions)
    report["portable_max_abs_error"]=parity
    if parity>1e-9 or not report["parameter_delta_l2"]>0:raise ValueError("Training or portable parity failed")
    save(directory/"FIRST_TEST.json",report)
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-dir",required=True)
    args=parser.parse_args(); print(json.dumps(train_run(args.output_dir),ensure_ascii=False))
