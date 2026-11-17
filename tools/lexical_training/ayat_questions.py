"""Licensed-speech GRU features and a fixed question-family readout for the debt-verse reader."""
import argparse
import csv
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

from . import shared_encoder as shared
from .speech_force import features
from .witness_recall import distribution

DATA=shared.ROOT/"evidence/ayat_cognition_v1"
MODEL=Path(__file__).with_name("data")/"ayat_questions_v1.json"
MODEL_SHA="f2e235ee0f6d162a9f07ce693189b9a2b2565716d8fa1af908cd8b8c3a5e8d58"
LABELS=("maqam","ontology","force","requirement","alert","condition","endpoint","number","agreement","opposition")


def rows(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f,delimiter="\t"))


def fit():
    import numpy as np
    train=rows(DATA/"train.tsv")
    if len({r["question"] for r in train})!=len(train) or {r["family"] for r in train}!=set(LABELS):
        raise ValueError("Invalid training split")
    encoder,identity=shared.load_model()
    x=np.array([features(encoder,r["question"])+[1.] for r in train])
    y=np.array([[float(k==r["family"]) for k in LABELS] for r in train])
    w=np.array([1/sum(t["family"]==r["family"] for t in train) for r in train])
    weights=np.linalg.solve((x.T*w)@x+.1*np.eye(x.shape[1]),(x.T*w)@y).T
    return {"schema":"nabt.ayat-query-ranker.v1","encoder":identity,"labels":list(LABELS),"alpha":.1,
            "training_sha256":sha256((DATA/"train.tsv").read_bytes()).hexdigest(),"n":len(x),
            "weights":weights.round(10).tolist()}


@lru_cache(maxsize=1)
def checked(enc,raw):
    if sha256(raw).hexdigest()!=MODEL_SHA:
        raise ValueError("Wrong question model")
    data=json.loads(raw)
    if (data["encoder"]!=sha256(enc).hexdigest() or data["labels"]!=list(LABELS)
            or not shared._shape(data["weights"],(len(LABELS),8*shared.HIDDEN+1))):
        raise ValueError("Unbound question readout")
    return shared.validate_model(json.loads(enc)),data["weights"]


def rank(question):
    try:
        enc,weights=checked(shared.MODEL.read_bytes(),MODEL.read_bytes())
        probs=distribution(weights,features(enc,question))
        ordered=sorted(zip(LABELS,probs,strict=True),key=lambda p:-p[1])
        return {"status":"PROPOSED","authority":"NONE","query":question,"model_sha256":MODEL_SHA,
                "ranking":[{"family":k,"score":round(p,8)} for k,p in ordered]}
    except (ValueError,OSError,KeyError) as exc:
        return {"status":"MODEL_UNAVAILABLE","authority":"NONE","reason":type(exc).__name__,"ranking":[]}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    with parser.parse_args().output.open("x",encoding="utf-8") as f:
        json.dump(fit(),f,sort_keys=True,separators=(",",":"),ensure_ascii=False)
        f.write("\n")
