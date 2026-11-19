"""Corpus-trained proposals for Arabic verb features and source-relative root recovery."""
from functools import lru_cache
from hashlib import sha256
import json
import unicodedata

from . import pattern_learning as net

PATH = "evidence/ntl_pattern_learning_v1/corpus_verbs.json"
PIN = "de17174202b42e9000afd876b1624a1000298a85b6cac98af4bffbdc061206d7"
QAC = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
# Spelling coordinates are a projection for this observer, never an edit of the source.
ROOT_GRAPH = str.maketrans({"أ": "ء", "إ": "ء", "ؤ": "ء", "ئ": "ء", "آ": "ء", "ى": "ي"})
SIGNS = str.maketrans({"ٱ":"ا", "ۡ":"ْ", "ـ":"", "ٓ":"", "ٰ":"", "۟":"", "ۢ":"",
                       "ۦ":"", "ۥ":"", "ۜ":"", "۫":"", "ۨ":""})


def project(word):
    text = unicodedata.normalize("NFC", word).translate(SIGNS)
    return text if net.features(text) else None


def carriers(projected):
    return "".join(ch for ch in projected if ch not in net.MARKS).translate(ROOT_GRAPH)


def apply_script(script, letters):
    if any(isinstance(op, int) and op >= len(letters) for op in script):
        return None
    return "".join(letters[op] if isinstance(op, int) else op for op in script)


def unpack(raw):
    value = json.loads(raw)
    if value["schema"] != "ntl.qac-verb-observer.v1" or value["source"] != QAC:
        raise ValueError("Corpus observer source mismatch")
    heads = {}
    for name in ("analysis", "root"):
        head = value[name]
        dim = head["hidden"]
        params = (net._matrix(head["input"], net.SHAPE_INPUTS + 1, dim),
                  net._matrix(head["output"], len(head["labels"]), dim + 1))
        heads[name] = (head["labels"], params)
    return heads


@lru_cache(maxsize=1)
def decode_pinned(raw):
    if sha256(raw).hexdigest() != PIN:
        raise ValueError("Corpus observer identity changed")
    return unpack(raw)


def model():
    try:
        return decode_pinned((net.DIRECTORY / "corpus_verbs.json").read_bytes())
    except (OSError, ValueError):
        return None


def analyze(heads, word):
    observed = project(word)
    if observed is None:
        return None
    x = net.features(observed)
    labels, params = heads["analysis"]
    scores = net.logits(params, x)
    label = labels[max(range(len(scores)), key=scores.__getitem__)]
    if label == "OTHER":
        return None
    labels, params = heads["root"]
    values = net.logits(params, x)
    letters = carriers(observed)
    for i in sorted(range(len(values)), key=lambda i: -values[i]):
        script = labels[i]
        root = apply_script(script, letters)
        if root is not None:
            aspect, voice, family = label.split("/")
            return {"aspect": aspect, "voice": voice, "family": family, "root": root,
                    "script": script, "projected_surface": observed, "radical_carriers": letters}
    return None
