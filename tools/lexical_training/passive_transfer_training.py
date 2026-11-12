"""Reproduce the authored, root-disjoint development experiment. No holdout input in training."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import random

from tools.grammar_catalog.operations import exact_terms
from . import passive_transfer as runtime

PROTOCOL = {"schema": "nabt.passive-relation-training.v1", "seed": 57119, "epochs": 45,
            "learning_rate": 0.035, "hidden": runtime.HIDDEN, "selection": "FIXED_FINAL_EPOCH",
            "objective": "SENTENCE_GROUPED_SOFTMAX_OVER_SOURCE_ASSIGNMENTS_AND_OUTSIDE",
            "features": "OBSERVED_ROLE_TYPED_CARRIER_MARKS_POSITION_AND_CONTEXT",
            "supervision": "AUTHORED_CONTROLLED_ARABIC_NOT_ATTESTED_CORPUS",
            "external_pretraining": False, "holdout_used_for_selection": False}

# Each record supplies observed forms and noun. Sources below are pedagogical,
# not lexical rules or an inference lexicon. Final vowels are retained only
# where written; the training set includes partially marked forms.
TRAIN = [
    ("فتح", "فُتِحَ", "يُفْتَحْ", "فَتَحَ", "يَفْتَحْ", "الباب"),
    ("رفع", "رُفِعَ", "يُرْفَعْ", "رَفَعَ", "يَرْفَعْ", "العلم"),
    ("حمل", "حُمِلَ", "يُحْمَلْ", "حَمَلَ", "يَحْمِلْ", "الحجر"),
    ("جمع", "جُمِعَ", "يُجْمَعْ", "جَمَعَ", "يَجْمَعْ", "المال"),
    ("طبع", "طُبِعَ", "يُطْبَعْ", "طَبَعَ", "يَطْبَعْ", "الكتاب"),
    ("خرج", "أُخْرِجَ", "يُخْرَجْ", "أَخْرَجَ", "يُخْرِجْ", "الجهاز"),
]
DEV = [("غسل", "غُسِلَ", "يُغْسَلْ", "غَسَلَ", "يَغْسِلْ", "الثوب"),
       ("كرم", "أُكْرِمَ", "يُكْرَمْ", "أَكْرَمَ", "يُكْرِمْ", "الضيف")]


def examples(families):
    rows = []
    for root, past, jussive, active, active_jussive, noun in families:
        short_past, short_jussive = past[:-1], jussive[:-1].replace("ْ", "")
        plain = runtime.observed(past)[0]
        has_object = noun + "َ"
        # Role IDs here only supervise indices; preprocessing and features never
        # receive root, targets, construction name, or a lexical testimony.
        for text, relation, roles in [
            (f"{past} {noun}ُ", runtime.ASSERT, (0, 1, None)),
            (f"{short_past} {noun}", runtime.ASSERT, (0, 1, None)),
            (f"{past} {noun}.", runtime.ASSERT, (0, 1, None)),
            (f"لَمْ {jussive[:-1]}ِ {noun}ُ", runtime.DENY, (1, 2, 0)),
            (f"لم {short_jussive} {noun}", runtime.DENY, (1, 2, 0)),
            (f"لم {jussive[:-1]} {noun}.", runtime.DENY, (1, 2, 0)),
            (f"{active} {has_object}", runtime.OUTSIDE, None),
            (f"لَمْ {active_jussive[:-1]}ِ {has_object}", runtime.OUTSIDE, None),
            (f"لم {runtime.observed(active_jussive)[0]} {noun}", runtime.OUTSIDE, None),
            (f"{plain} {noun}", runtime.OUTSIDE, None),
            (f"هل {past} {noun}؟", runtime.OUTSIDE, None),
            (f"{short_past} {noun}؟", runtime.OUTSIDE, None),
            (f"«{past} {noun}»", runtime.OUTSIDE, None),
            (f"هل لم {short_jussive} {noun}؟", runtime.OUTSIDE, None),
            (f"لكي {jussive[:-1]}َ {noun}", runtime.OUTSIDE, None),
            (f"لِمَ {jussive[:-1]}ُ {noun}؟", runtime.OUTSIDE, None),
            (f"لِمَ {jussive[:-1]}ُ {noun}", runtime.OUTSIDE, None),
            (f"{noun} معلوم", runtime.OUTSIDE, None),
            (f"{past} {noun} وخرج زيد", runtime.OUTSIDE, None),
            (f"زيد قال «لم {short_jussive} {noun}»", runtime.OUTSIDE, None),
        ]:
            term_spans = [t["utf8_span"] for t in exact_terms(text)]
            binding = [term_spans[i] if i is not None else None for i in roles] if roles else [None]*3
            rows.append({"text": text, "root": root, "relation": relation,
                         **dict(zip(("verb_span", "patient_span", "cue_span"), binding, strict=True))})
    return rows


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def target(row):
    return {k:row[k] for k in ("relation","verb_span","patient_span","cue_span")}


def train():
    train_rows, dev_rows = examples(TRAIN), examples(DEV)
    if {r["root"] for r in train_rows} & {r["root"] for r in dev_rows}:
        raise ValueError("Root leakage")
    training = [(runtime.candidates(r["text"]), target(r)) for r in train_rows]
    features = sorted({f for rows,_ in training for _,context,shape in rows for f in context+shape})
    indices = {f:i for i,f in enumerate(features)}
    groups = []
    for rows, gold in training:
        candidates = [c for c,_,_ in rows]
        expected = None if gold["relation"] == runtime.OUTSIDE else candidates.index(gold)
        groups.append(([[indices[f] for f in context + shape] for _,context,shape in rows], expected))
    rng = random.Random(PROTOCOL["seed"])
    h = runtime.HIDDEN
    model = {"schema": runtime.SCHEMA, "authority":"NONE", "features":features,
             "embedding":[[rng.uniform(-.1,.1) for _ in range(h)] for _ in features],
             "bias":[0.0]*h, "readout":[rng.uniform(-.2,.2) for _ in range(h)], "offset":0.0,
             "training_sha256":sha256(encoded(train_rows)).hexdigest(), "protocol":PROTOCOL}
    # Shared nonlinear role composition, optimized on complete sentence groups.
    # The outside candidate has a fixed zero logit and no role assignments.
    history = []
    for epoch in range(PROTOCOL["epochs"]):
        rng.shuffle(groups)
        loss = 0.0
        for rows, expected in groups:
            states = [runtime.hidden_state(row, model) for row in rows]
            scores = [model["offset"] + sum(a*b for a,b in zip(s,model["readout"])) for s in states] + [0.]
            gold = len(rows) if expected is None else expected
            high = max(scores)
            exp = [math.exp(s-high) for s in scores]
            total = sum(exp)
            loss += math.log(total)+high-scores[gold]
            errors = [exp[i]/total - int(i == gold) for i in range(len(rows))]
            gw = [0.]*h
            gb = [0.]*h
            ge = {}
            for ids, state, err in zip(rows, states, errors, strict=True):
                grad = [err * model["readout"][k] * (1.-state[k]**2) for k in range(h)]
                for k in range(h):
                    gw[k] += err*state[k]
                    gb[k] += grad[k]
                for i in ids:
                    acc = ge.setdefault(i,[0.]*h)
                    for k in range(h):
                        acc[k] += grad[k]
            rate = PROTOCOL["learning_rate"]
            for i, values in ge.items():
                for k in range(h):
                    model["embedding"][i][k] -= rate*values[k]
            for k in range(h):
                model["bias"][k] -= rate*gb[k]
                model["readout"][k] -= rate*gw[k]
            model["offset"] -= rate*sum(errors)
        if epoch in (0, PROTOCOL["epochs"]-1):
            history.append({"epoch":epoch+1,"mean_cross_entropy":round(loss/len(groups),8)})
    # Explicit precision in the portable checkpoint avoids storing float print noise.
    model["embedding"] = [[round(v,8) for v in e] for e in model["embedding"]]
    model["bias"] = [round(v,8) for v in model["bias"]]
    model["readout"] = [round(v,8) for v in model["readout"]]
    model["offset"] = round(model["offset"],8)
    report = {"schema":"nabt.passive-relation-development.v1", "history":history, "protocol":PROTOCOL,
              "initialization_seed":PROTOCOL["seed"], "model_sha256":sha256(encoded(model)).hexdigest(),
              "training_sha256":model["training_sha256"], "dev_sha256":sha256(encoded(dev_rows)).hexdigest()}
    for split, rows in (("train",train_rows),("dev",dev_rows)):
        correct = sum(target(runtime.rank(runtime.candidates(r["text"]), model)[0]) == target(r) for r in rows)
        report[split] = {"roots":sorted({r["root"] for r in rows}),"correct":correct,"total":len(rows)}
    return model,report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    directory = parser.parse_args().output_dir
    directory.mkdir(parents=True,exist_ok=False)
    model,report = train()
    (directory/"model.json").write_bytes(encoded(model))
    (directory/"development.json").write_bytes(encoded(report))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
