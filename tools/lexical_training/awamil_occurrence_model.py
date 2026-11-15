"""Portable learned occurrence proposals. Inputs are written features only."""
from array import array
from base64 import b64decode
from functools import lru_cache
from hashlib import sha256
import json
import math
import unicodedata
from zlib import crc32, decompress

from tools.grammar_catalog.operations import ROOT, exact_terms
from .features import features

PATH = "evidence/awamil_occurrence_v1/weights_v1_1.json"
MODEL_SHA = "224932df2e93b163ae83a73c1af98ef1601dd276ca62b6ef47924af4d51bc05b"
WIDTH = 640
TOKEN_LIMIT = 12


def observed(text):
    terms = exact_terms(text)
    counts = {k: min(float(v),3) for k,v in features(text,WIDTH).items()}
    def add(key, weight=1.0):
        col = crc32(key.encode()) % WIDTH
        counts[col] = counts.get(col,0.) + weight
    for i,term in enumerate(terms):
        w = term["surface"]
        bare = "".join(c for c in w if not unicodedata.category(c).startswith("M"))
        marks = "".join(c for c in w if unicodedata.category(c).startswith("M"))
        for feature in ("shape="+marks, "end="+w[-1:], "head="+bare[:1], "article="+str(bare.startswith("ال"))):
            add(str(i)+feature,2.)
        add(str(i)+"word="+w,2.)
    add("length="+str(len(terms)),2.)
    for c in "«»:؟":
        if c in text:
            add("punct="+c,3.)
    norm = math.sqrt(sum(v*v for v in counts.values())) or 1
    return terms, {i:v/norm for i,v in counts.items()}


def unpack(data):
    vals = array("b",decompress(b64decode(data["q"])))
    rows,cols = data["shape"]
    if len(vals) != rows*cols:
        raise ValueError("Weight shape mismatch")
    return [[n*data["scale"] for n in vals[r*cols:(r+1)*cols]] for r in range(rows)]


@lru_cache(maxsize=1)
def decode(raw):
    obj = json.loads(raw)
    return obj["classes"], {k:unpack(v) for k,v in obj["weights"].items()}


def predict(text, fitted):
    terms,x = observed(text)
    classes,w = fitted
    hidden = w["bias"][0].copy()
    for i,v in x.items():
        for j,b in enumerate(w["projection"][i]):
            hidden[j] += v*b
    hidden = [math.tanh(v) for v in hidden]
    output = {}
    for name,options in classes.items():
        row = w[name+"_bias"][0].copy()
        for v,vec in zip(hidden,w[name],strict=True):
            for j,b in enumerate(vec):
                row[j] += v*b
        best = max(row)
        winners = [i for i,s in enumerate(row) if s==best]
        output[name] = options[winners[0]] if len(winners)==1 else None
    for name in ("governor","dependent"):
        idx=output[name]
        output[name+"_span"] = terms[idx-1]["utf8_span"] if isinstance(idx,int) and 0<idx<=len(terms) else None
    return output


def propose(text):
    if len(text.encode())>1024 or len(exact_terms(text))>TOKEN_LIMIT:
        return {"status":"OUTSIDE_BUDGET","authority":"NONE"}
    try:
        raw=(ROOT/PATH).read_bytes()
        if sha256(raw).hexdigest()!=MODEL_SHA:
            raise ValueError("Checkpoint identity differs")
        result=predict(text,decode(raw))
    except (OSError,ValueError) as exc:
        return {"status":"MODEL_UNAVAILABLE","authority":"NONE","reason":str(exc)}
    return {"status":"PROPOSED" if result["factor"] else "DEFER","authority":"NONE",
            "source_sha256":sha256(text.encode()).hexdigest(),"model_sha256":MODEL_SHA,**result}
