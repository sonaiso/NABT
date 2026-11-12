"""Fit three Q/K cross-attention heads on source-bound teacher pointers. No holdout file is read."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import classical_roles as owner
from tools.grammar_catalog.source_evidence_view import pinned_excerpts
from . import classical_attention as net

PROTOCOL = {"seed": 31092, "epochs": 200, "learning_rate": 0.035, "width": net.WIDTH,
            "objective": "mean negative log likelihood of role occurrence including NULL",
            "selection": "fixed final epoch, no challenge selection",
            "training_senses": ["praise", "support"], "training_stems": ["الْحَارِس","الْكَاتِب","الْمُهَنْدِس","الْعَامِل"]}


def corpus(bank):
    rows = {}
    for sense in PROTOCOL["training_senses"]:
        verb = bank["verbs"][sense][0]
        stems = PROTOCOL["training_stems"]
        for stem, other in zip(stems, stems[1:] + stems[:1]):
            for nom, acc in (("ُ","َ"), ("َانِ","َيْنِ")):
                a, b = stem + nom, other + acc
                for end1, end2 in ((a,b),(b,a)):
                    positive = f"{verb} {end1} {end2}"
                    rows[positive] = True
                    rows["هل " + positive + "؟"] = True
                for negative in (f"{verb} {stem+nom} {other+nom}", f"{verb} {stem+acc} {other+acc}",
                                 f"لم {verb} {a} {b}", f"«{verb} {a} {b}»", f"{verb} {a} {b}؟",
                                 f"{verb} {stem} {other}"):
                    rows[negative] = False
    examples = []
    for text, in_scope in rows.items():
        reading = owner.interpret(text, bank)
        if bool(reading) != in_scope:
            raise ValueError("Mismatch between authored frame and source teacher: " + text)
        terms, _, _ = net.encode(text)
        spans = [None, *(t["utf8_span"] for t in terms)]
        targets = [0, 0, 0]
        if reading:
            pointers = [reading[k]["term"] for k in ("subject","object")] + [reading["cue"]]
            targets = [spans.index(t["utf8_span"]) if t else 0 for t in pointers]
        examples.append({"text": text, "target_indices": targets})
    return examples


def wire(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False) + "\n").encode()


def fit():
    import numpy as np
    bank = owner.inventory()
    laws = ["jurjani:092","governed_roles","object_first","predication","primary","dual","question",
            *PROTOCOL["training_senses"]]
    witnesses = pinned_excerpts(bank, laws)
    examples = corpus(bank)
    # The model sees raw query/key features only; the separate teacher provides labels.
    n, h, d = len(examples), len(net.HEADS), net.WIDTH
    qin = np.zeros((n,len(net.QUERIES)))
    kin = np.zeros((n,5,len(net.KEYS)))
    live = np.zeros((n,5),dtype=bool)
    targets = np.array([row["target_indices"] for row in examples])
    for i,row in enumerate(examples):
        _, query, keys = net.encode(row["text"])
        qin[i] = query
        kin[i,:len(keys)] = keys
        live[i,:len(keys)] = True
    rng = np.random.default_rng(PROTOCOL["seed"])
    wq = rng.normal(0,.2,(h,len(net.QUERIES),d))
    wk = rng.normal(0,.2,(h,len(net.KEYS),d))
    states = [(np.zeros_like(w), np.zeros_like(w)) for w in (wq,wk)]
    history = []
    for t in range(1, PROTOCOL["epochs"] + 1):
        q = np.einsum("ni,hid->nhd",qin,wq)
        k = np.einsum("nmi,hid->nhmd",kin,wk)
        logits = np.einsum("nhd,nhmd->nhm",q,k)/np.sqrt(d)
        logits = np.where(live[:,None,:], logits, -np.inf)
        p = np.exp(logits-logits.max(axis=2,keepdims=True))
        p /= p.sum(axis=2,keepdims=True)
        indices = np.arange(n)[:,None], np.arange(h)[None,:], targets
        if t in (1,50,100,150,200):
            history.append([t,round(float(-np.log(p[indices]).mean()),8)])
        p[indices] -= 1
        dz = p/(n*h*np.sqrt(d))
        dq = np.einsum("nhm,nhmd->nhd",dz,k)
        dk = np.einsum("nhm,nhd->nhmd",dz,q)
        grads = (np.einsum("ni,nhd->hid",qin,dq), np.einsum("nmi,nhmd->hid",kin,dk))
        for w, (m,v), grad in zip((wq,wk),states,grads,strict=True):
            m *= .9
            m += .1 * grad
            v *= .999
            v += .001 * grad**2
            w -= PROTOCOL["learning_rate"]*(m/(1-.9**t))/(np.sqrt(v/(1-.999**t))+1e-8)
    return {"schema":"nabt.classical-roles.weights.v1", "protocol":PROTOCOL, "training_count":n,
            "numpy":np.__version__, "loss_curve":history, "dataset_sha256":sha256(wire(examples)).hexdigest(),
            "source_table":owner.INVENTORY_SHA256, "teacher_witnesses":{k:w["sha256"] for k,w in witnesses.items()},
            "keys":net.KEYS,"queries":net.QUERIES,"values":"one-hot occurrence pointers plus NULL",
            "heads":{name:{"Wq": wq[i].round(9).tolist(),"Wk":wk[i].round(9).tolist()}
                     for i,name in enumerate(net.HEADS)}, "authority":"NONE"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    path = parser.parse_args().output
    raw = wire(fit())
    with path.open("xb") as out:
        out.write(raw)
    print(sha256(raw).hexdigest())
