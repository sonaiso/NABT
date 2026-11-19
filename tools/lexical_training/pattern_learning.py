"""Root-contrast template induction and trained, non-authoritative NTP proposals."""
import base64
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from math import prod
from pathlib import Path
import struct

from nabt import derivation
from nabt.corpus_evidence import lookup_clusters
from nabt.errors import resource_limit
from tools.grammar_catalog.operations import exact_terms

NOMINAL_PATH = "evidence/meaning_preservation_v1/research/morphology_inventory.json"
NOMINAL_SHA = "8c6dfee3ec18b79575b4a5d9a6d1123fc8d2c6fe0bf2a8fb499e1009635201fd"
MODEL_PATH = "evidence/ntl_pattern_learning_v1/model.json"
DIRECTORY = Path(__file__).resolve().parents[2] / Path(MODEL_PATH).parent
MODEL_SHA = "60d3c3b5b9e0e10fde2ff8e68fec48ba940aba3f2853c0985dbff8179dee39bc"
MARKS = "ًٌٍَُِّْٰ"
CARRIERS = derivation.RADICALS + "اأإآؤئىةٱ"
POSITIONS = 9
WIDTH = 1 + len(CARRIERS) + len(MARKS)
SHAPE_INPUTS = POSITIONS * WIDTH
GUARD_INPUTS = len(CARRIERS) + 3


def induce(pairs):
    """All literal/slot templates consistent with aligned exact (root, stem) pairs."""
    if (not isinstance(pairs, (list, tuple)) or not 1 <= len(pairs) <= 128
            or any(not isinstance(pair, (tuple, list)) or len(pair) != 2
                   or any(type(s) is not str for s in pair) for pair in pairs)):
        raise ValueError("Expected 1..128 aligned root and stem pairs")
    arity, width = map(len, pairs[0])
    if arity not in (3, 4, 5) or not 1 <= width <= 32:
        raise ValueError("Unsupported aligned template domain")
    if any(len(r) != arity or len(s) != width or any(c not in derivation.RADICALS for c in r)
           for r, s in pairs):
        raise ValueError("Alignment or formal radical domain differs")
    columns = []
    for i in range(width):
        first = pairs[0][1][i]
        opts = [first] if all(stem[i] == first for _, stem in pairs) else []
        opts.extend(slot for slot in range(arity) if all(stem[i] == root[slot] for root, stem in pairs))
        columns.append(opts)
    if prod(map(len, columns)) > 65536:
        raise resource_limit("Template alignment search exceeds 65536 combinations")
    required = set(range(arity))
    return [list(tokens) for tokens in product(*columns) if required.issubset(tokens)]


@lru_cache(maxsize=1)
def inventory():
    raw = (DIRECTORY.parents[1] / NOMINAL_PATH).read_bytes()
    if sha256(raw).hexdigest() != NOMINAL_SHA:
        raise ValueError("Printed nominal source inventory changed")
    patterns = list(derivation.installed_registry()["patterns"])
    for row in json.loads(raw)["nominal_stem_inventory"]["patterns"]:
        tokens = []
        for char in row["expanded_template"]:
            if char in MARKS:
                tokens.append(char)
            else:
                tokens.append(sum(type(v) is int for v in tokens))
        patterns.append({"id": "nominal.stem." + row["id"], "label": row["expanded_template"],
                         "arity": row["root_slots"], "tokens": tokens, "endings": list("ًٌٍَُِ"),
                         "root_domain": "written_nominal_slots", "profile": row["profile"],
                         "source_contract": "nominal_stem_inventory/" + row["id"],
                         "slot_vowels": row["slot_vowels"], "example": row["example"]})
    return tuple(patterns)


def features(word):
    clusters = lookup_clusters(word)
    if not clusters or len(clusters) > POSITIONS:
        return []
    active = []
    for j, (_, marks, start, _) in enumerate(clusters):
        base = WIDTH * j
        active.append(base)
        carrier = CARRIERS.find(word[start])
        if carrier >= 0:
            active.append(base + 1 + carrier)
        active.extend(base + 1 + len(CARRIERS) + i for i, char in enumerate(MARKS) if char in marks)
    return active


def guard_features(verb, count, limit):
    clusters = lookup_clusters(verb)
    if not clusters:
        raise ValueError("Malformed report verb")
    carriers = {verb[start] for _, _, start, _ in clusters}
    return [i for i, ch in enumerate(CARRIERS) if ch in carriers] + [
        len(CARRIERS) + (count > limit) - (count < limit) + 1]


def pack_matrix(matrix):
    flat = [int(v) for v in matrix.ravel()]
    return base64.b64encode(struct.pack(f"<{len(flat)}h", *flat)).decode("ascii")


def _matrix(value, rows, cols):
    raw = base64.b64decode(value, validate=True)
    flat = struct.unpack(f"<{rows * cols}h", raw)
    return [flat[i:i + cols] for i in range(0, len(flat), cols)]


def unpack(model):
    labels = [p["id"] for p in inventory()]
    if (model["schema"] != "ntl.surface-weights.v1" or model["table"] != derivation.EXPECTED_TABLE_SHA256
            or model["nominal_table"] != NOMINAL_SHA or model["patterns"]["labels"] != labels or model["guard"]["labels"] != [False, True]):
        raise ValueError("Model and owner disagree on label domain")
    heads = {}
    for name, size in (("patterns", SHAPE_INPUTS), ("guard", GUARD_INPUTS)):
        net = model[name]
        hidden = net["hidden"]
        if type(hidden) is not int or not 1 <= hidden <= 128:
            raise ValueError("Unsupported hidden dimension")
        heads[name] = (_matrix(net["input"], size + 1, hidden),
                       _matrix(net["output"], len(net["labels"]), hidden + 1))
    return heads


@lru_cache(maxsize=1)
def decode_pinned(raw):
    if sha256(raw).hexdigest() != MODEL_SHA:
        raise ValueError("Trained pattern weights changed")
    return unpack(json.loads(raw))


def model():
    try:
        return decode_pinned((DIRECTORY / "model.json").read_bytes())
    except (OSError, ValueError):
        return None


def logits(head, active):
    # Last input row is the bias. Quantization uses 128 units per real unit.
    weights, output = head
    hidden = list(weights[-1])
    for i in active:
        for j, value in enumerate(weights[i]):
            hidden[j] += value
    hidden = [max(0, v) for v in hidden] + [128]
    return [sum(x * w for x, w in zip(hidden, row, strict=True)) for row in output]


@lru_cache(maxsize=1)
def skeletons():
    index = {}
    for pos, p in enumerate(inventory()):
        skeleton = [v for v in p["tokens"] if type(v) is int or v not in MARKS]
        index.setdefault(len(skeleton), []).append((pos, p, skeleton))
    return index


def alternatives(word):
    """Inverse under missing marks. Check every visible carrier and all endings."""
    clusters = lookup_clusters(word)
    if not clusters:
        return []
    bases = [word[start] for _, _, start, _ in clusters]
    readings = []
    for index, p, skeleton in skeletons().get(len(bases), ()):
        root = [""] * p["arity"]
        for token, ch in zip(skeleton, bases):
            if type(token) is int:
                if root[token] and root[token] != ch:
                    break
                root[token] = ch
            elif ch != token:
                break
        else:
            root = "".join(root)
            valid = (all(ch in CARRIERS for ch in root) if p["root_domain"] == "written_nominal_slots"
                     else derivation._root_ok(root, p))
            if not valid:
                continue
            stem = derivation._fill(p, root)
            looked = lookup_clusters(stem)
            if any(not a[1] <= b[1] for a, b in zip(clusters[:-1], looked[:-1])):
                continue
            endings = [e for e in ("", *p["endings"]) if clusters[-1][1] <= looked[-1][1] | set(e)]
            if endings:
                readings.append((index, {"pattern": p["id"], "root": root, "stem": stem,
                                          "profile": p.get("profile", "derivation"), "label": p["label"],
                                          "exact": any(word == stem + e for e in endings),
                                          "endings": endings, "source_contract": p["source_contract"]}))
    return readings


def read(text):
    trained = model()
    observations = []
    terms = exact_terms(text)
    try:
        patterns = inventory()
    except (ValueError, OSError) as error:
        return {"ranking": "SOURCE_UNAVAILABLE", "reason": str(error), "occurrences": [],
                "authority": "NONE", "terms_examined": 0, "total_terms": len(terms)}
    for term in terms[:128]:
        candidates = alternatives(term["surface"])
        if not candidates:
            continue
        if trained:
            scores = logits(trained["patterns"], features(term["surface"]))
            candidates.sort(key=lambda pair: (-scores[pair[0]], pair[0]))
        observations.append({**term, "alternatives": [r for _, r in candidates]})
    return {"model_sha256": MODEL_SHA if trained else None, "table_sha256": derivation.EXPECTED_TABLE_SHA256,
            "nominal_sha256": NOMINAL_SHA, "pattern_count": len(patterns), "ranking": "TRAINED" if trained else "MODEL_UNAVAILABLE",
            "authority": "CONDITIONAL_SHAPE_ONLY", "terms_examined": min(len(terms), 128),
            "total_terms": len(terms), "occurrences": observations}


def guard_proposal(verb, count, limit):
    trained = model()
    if not trained:
        return {"status": "MODEL_UNAVAILABLE", "prediction": None}
    no, yes = logits(trained["guard"], guard_features(verb, count, limit))
    return {"status": "PROPOSED" if yes != no else "TIED", "prediction": yes > no if yes != no else None,
            "verb": verb, "model_sha256": MODEL_SHA, "authority": "NONE"}
