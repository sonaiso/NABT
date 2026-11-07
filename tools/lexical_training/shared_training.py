"""Joint supervised experiment; fixed train/test split, no test-based selection."""
import argparse
from copy import deepcopy
from difflib import SequenceMatcher
from hashlib import sha256
import json
from pathlib import Path

from . import shared_encoder as runtime

PROTOCOL = {"id": "nabt.shared-cognition-pilot.v1", "seed": 116,
            "epochs": 100, "learning_rate": 0.015,
            "selection": "FINAL_EPOCH_FIXED_BEFORE_FIRST_EVALUATION",
            "train_roots": ["ضرب", "فتح", "حمل", "حفظ", "رفع", "جمع"],
            "test_roots": ["كتب", "غسل"], "held_out_person_stem": "قم",
            "scope": "AUTHORED_BOUNDED_MORPHOLOGY_AND_EXPOSED_LEXICAL_DIAGNOSTICS"}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    path.write_bytes(wire(value) + b"\n")


def dataset():
    from .acquisition import dataset as lexical_dataset, DIAGNOSTIC
    cat, _, quotes, _ = lexical_dataset()
    train, test = [], []
    for index, q in enumerate(quotes):
        train.append({"id": f"lexical:{index}", "text": q["text"], "group": "retained_quotation",
                      "provenance": q["sources"],
                      "labels": {"concept": q["sense_ids"], "witness": ["lexical_source_alignment"]}})
    diagnostic = json.loads(DIAGNOSTIC.read_text())
    for index, q in enumerate(diagnostic["queries"]):
        test.append({"id": f"lexical-diagnostic:{index}", "text": q["text"],
                     "group": "EXPOSED_AUTHORED_SEEN_SENSE_CONTEXT", "labels": {
                         "concept": q["expected_ids"], "witness": ["lexical_source_alignment"]}})
    def add(rows, text, group, **labels):
        rows.append({"id": f"authored:{len(rows)}", "text": text, "group": group,
                     "provenance": "AUTHORED_PEDAGOGICAL_ANNOTATION_NOT_ACQUIRED_READING",
                     "labels": {k:[v] for k,v in labels.items()}})
    for rows, roots in ((train, PROTOCOL["train_roots"]), (test, PROTOCOL["test_roots"])):
        for root in roots:
            a,b,c = root
            active, passive = a+"َ"+b+"َ"+c+"َ", a+"ُ"+b+"ِ"+c+"َ"
            for word, reading, morph, attach in ((active, "faala_marks", "active_past", "agent"),
                                                 (passive, "fuila_marks", "passive_past", "patient_subject")):
                for tail in ("", " زَيْدٌ", " سَالِمٌ"):
                    add(rows, word+tail, root, reading=reading, morphology=morph,
                        attachment=attach, witness="statement_world_evidence")
            for suffix, who, attach in (("ُ", "speaker", "speaker_suffix"),
                                         ("َ", "addressee_male", "addressee_suffix"),
                                         ("ِ", "addressee_female", "addressee_suffix")):
                for tail in ("", " أَمْسِ"):
                    add(rows, a+"َ"+b+"َ"+c+"ْت"+suffix+tail, root,
                        reading="suffix_t"+{"ُ":"u", "َ":"a", "ِ":"i"}[suffix],
                        morphology=who, attachment=attach, witness="statement_world_evidence")
    for suffix, who, attach in (("ُ", "speaker", "speaker_suffix"),
                                 ("َ", "addressee_male", "addressee_suffix"),
                                 ("ِ", "addressee_female", "addressee_suffix")):
        add(test, "قُمْت"+suffix, "قم", reading="suffix_t"+{"ُ":"u", "َ":"a", "ِ":"i"}[suffix],
            morphology=who, attachment=attach, witness="statement_world_evidence")
    for rows, commands in ((train, ("اُكْتُبْ", "اِفْتَحْ", "اِحْفَظْ", "اِجْمَعْ")),
                           (test, ("اِغْسِلْ", "اِحْمِلْ"))):
        for text in commands:
            add(rows, text, "speech_act", witness="request_execution_evidence")
    if set(r["text"] for r in train) & set(r["text"] for r in test):
        raise ValueError("Train/test exact text overlap")
    for row in train + test:
        runtime.byte_ids(row["text"])
    labels = {h: sorted({label for row in train for label in row["labels"].get(h, [])}) for h in runtime.HEADS}
    return train, test, labels


def torch_model(labels):
    import torch
    class SharedEncoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = torch.nn.Embedding(257, runtime.EMBEDDING, padding_idx=0)
            self.gru = torch.nn.GRU(runtime.EMBEDDING, runtime.HIDDEN, batch_first=True)
            self.heads = torch.nn.ModuleDict({h: torch.nn.Linear(runtime.HIDDEN, len(labels[h])) for h in runtime.HEADS})

        def forward(self, texts):
            rows = [runtime.byte_ids(text) for text in texts]
            lengths = torch.tensor([len(row) for row in rows])
            tokens = torch.zeros((len(rows), int(lengths.max())), dtype=torch.long)
            for i, row in enumerate(rows):
                tokens[i, :len(row)] = torch.tensor(row)
            packed = torch.nn.utils.rnn.pack_padded_sequence(self.embedding(tokens), lengths,
                                                            batch_first=True, enforce_sorted=False)
            _, hidden = self.gru(packed)
            return {h: layer(hidden[0]) for h, layer in self.heads.items()}
    return SharedEncoder()


def export(model, labels, rows):
    definitions = runtime.concepts.catalogue()
    return {"schema": runtime.SCHEMA, "architecture": {"embedding": runtime.EMBEDDING,
            "hidden": runtime.HIDDEN, "vocabulary": 257, "max_bytes": runtime.MAX_BYTES},
            "labels": labels, "parameters": {k:v.detach().tolist() for k,v in model.state_dict().items()},
            "concept_references": {r["identity"]["id"]: r["reference"] for r in definitions["concepts"]},
            "training_sha256": sha256(wire(rows)).hexdigest(), "protocol": PROTOCOL, "authority": "NONE"}


def train_run(directory):
    import torch
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(PROTOCOL["seed"])
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    train, test, labels = dataset()
    model = torch_model(labels)
    initial = deepcopy(model.state_dict())
    with torch.no_grad():
        baseline = {h:v.tolist() for h,v in model([r["text"] for r in test]).items()}
    optimizer = torch.optim.Adam(model.parameters(), lr=PROTOCOL["learning_rate"])
    targets, masks = {}, {}
    for h in runtime.HEADS:
        masks[h] = [i for i,r in enumerate(train) if r["labels"].get(h)]
        y = torch.zeros((len(masks[h]), len(labels[h])))
        for j,i in enumerate(masks[h]):
            gold = train[i]["labels"][h]
            for label in gold:
                y[j, labels[h].index(label)] = 1 / len(gold)
        targets[h] = y
    history = []
    for epoch in range(PROTOCOL["epochs"]):
        optimizer.zero_grad()
        scores = model([r["text"] for r in train])
        losses = {h: -(targets[h] * torch.log_softmax(scores[h][masks[h]], dim=1)).sum(1).mean()
                  for h in runtime.HEADS}
        loss = sum(losses.values()) / len(losses)
        loss.backward()
        optimizer.step()
        history.append({"epoch": epoch+1, **{h:float(v.detach()) for h,v in losses.items()}})
    model.eval()
    with torch.no_grad():
        scores = {h:v.tolist() for h,v in model([r["text"] for r in test]).items()}
    exported = export(model, labels, train)
    save(directory / "model.json", exported)
    portable, _ = runtime.load_model(directory / "model.json")
    portable_scores = [runtime.logits(portable, r["text"]) for r in test]
    parity = max(abs(portable_scores[i][h][j] - scores[h][i][j])
                 for i in range(len(test)) for h in runtime.HEADS for j in range(len(labels[h])))
    predictions, metrics = [], {method:{} for method in ("initial", "neural", "nearest_bytes")}
    for i,row in enumerate(test):
        answers = {}
        for h,gold in row["labels"].items():
            nearest = max((r for r in train if h in r["labels"]),
                          key=lambda r: SequenceMatcher(None, row["text"].encode(), r["text"].encode()).ratio())
            picks = {"initial": labels[h][max(range(len(labels[h])), key=lambda j:baseline[h][i][j])],
                     "neural": labels[h][max(range(len(labels[h])), key=lambda j:scores[h][i][j])],
                     "nearest_bytes": nearest["labels"][h][0]}
            answers[h] = {"gold": gold, "predictions": picks}
            for method,pick in picks.items():
                metric = metrics[method].setdefault(h, {"n":0, "top1_correct":0, "unseen_gold":0})
                metric["n"] += 1
                metric["top1_correct"] += int(pick in gold)
                metric["unseen_gold"] += int(not set(gold) <= set(labels[h]))
        predictions.append({"id": row["id"], "text": row["text"], "group": row["group"], "heads": answers})
    delta = float(sum((v-initial[k]).square().sum() for k,v in model.state_dict().items()).sqrt())
    report = {"schema":"nabt.shared-cognition-evaluation.v1", "protocol":PROTOCOL,
              "train_rows":len(train), "test_rows":len(test), "metrics":metrics,
              "parameters":sum(p.numel() for p in model.parameters()), "parameter_delta_l2":delta,
              "optimizer_steps":len(history), "portable_max_abs_error":parity,
              "torch_version":torch.__version__, "history":history,
              "training_sha256":sha256(wire(train)).hexdigest(), "test_sha256":sha256(wire(test)).hexdigest(),
              "weights_sha256":sha256((directory/"model.json").read_bytes()).hexdigest(),
              "independent_semantic_adjudication":False, "unseen_concepts_measured":False,
              "learned_predictions_grant_authority":False, "all_arabic_complete":False}
    if not delta > 0 or not parity < 1e-4:
        raise ValueError("Training update or portable parity failed")
    for name, data in (("FIRST_TEST.json",report), ("predictions.json",predictions),
                        ("train.json",train), ("test.json",test)):
        save(directory/name, data)
    return {k:v for k,v in report.items() if k != "history"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(train_run(args.run_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
