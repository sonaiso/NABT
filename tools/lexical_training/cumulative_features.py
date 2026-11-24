"""Proposal-only features from text and two retained NABT parent representations."""
from functools import lru_cache
from hashlib import blake2b
import math
import re
import unicodedata

from nabt.alphabet import CARRIERS, HARAKAT, cell_id, parse_word
from nabt.errors import NabtError
from . import ntp_recursive as recursive, v13_occurrence as v13

HASH_DIM = 256
DIM = HASH_DIM + 32 + recursive.DIM + 3
CLUSTER = re.compile("(["+"".join(CARRIERS)+"])([\u064b-\u0652]+)")
VOWELS = "َُِ"
TANWIN = "ًٌٍ"


@lru_cache(maxsize=16384)
def hash_feature(token):
    b = blake2b(token.encode(),digest_size=4).digest()
    return int.from_bytes(b[:2],"big")%HASH_DIM, (1 if b[2]%2 else -1)


def hashed(text):
    vector = [0.]*HASH_DIM
    for word in text.split():
        padded = "^"+word+"$"
        tokens = [padded]+[padded[i:i+n] for n in (1,2,3) for i in range(len(padded)-n+1)]
        for token in tokens:
            i, sign = hash_feature(token)
            vector[i] += sign
    norm = math.sqrt(sum(v*v for v in vector)) or 1.
    return [v/norm for v in vector]


def parents():
    return (v13.checked_json("parent.json",v13.PARENT_SHA)["nets"],
            v13.checked_json("checkpoint.json",v13.MODEL_SHA),recursive.load()["parameters"])


def features(text, models):
    nets, readout, params = models
    sounds, contrasts, words = [], [], []
    previous = None
    for match in CLUSTER.finditer(text):
        letter, marks = match.groups()
        vowels = [m for m in marks if m in VOWELS+TANWIN]
        if letter=="ا" or len(vowels)!=1 or any(c not in VOWELS+TANWIN+"ّ" for c in marks):
            previous = None
            continue
        m = vowels[0]
        item = {"source116_id":cell_id(letter,(TANWIN if m in TANWIN else VOWELS).index(m)),
                "shadda":"ّ" in marks,"tanwin":m in TANWIN,"boundary":"WASL"}
        _,h = v13.observe(nets,item)
        sounds.append(h)
        if previous:
            end, old_letter, old, vec = previous
            if end==match.start() and old_letter==letter and sum(item[k]!=old[k] for k in old)==1:
                contrasts.append(v13.changed(readout,v13.difference(vec,h)))
        previous = match.end(),letter,item,h
    for word in text.split():
        try:
            cells = parse_word(word)
        except NabtError:
            continue
        if cells and len(cells)<=recursive.MAX_CELLS:
            words.append(recursive.encode_state(params,cells))
    def mean(rows,dim):
        return [sum(col)/len(rows) for col in zip(*rows)] if rows else [0.]*dim
    return hashed(text)+mean(sounds,32)+mean(words,recursive.DIM)+[
        float(bool(sounds)),float(bool(words)),sum(contrasts)/len(contrasts) if contrasts else 0.]
