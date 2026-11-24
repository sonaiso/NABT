"""Cumulative V14: a residual learner over the retained PR-143 task memory.

The installed parent and all 164 of its heads remain intact. Learned residuals
are observations, not owner licenses. Deployment needs only the standard library.
"""

from functools import lru_cache
import gzip
from hashlib import sha256
import json
import math
from pathlib import Path

from . import cumulative_features as features, cumulative_lesson as previous, corpus_verbs

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "evidence/cumulative_v14"
PARENT_COMMIT = "2d00f81975ea2ff9d0a4864f16ffe122b2d410bf"
SCHEMA = "nabt.cumulative-v14-weights.v1"
ABLATIONS = {"v13", "ntp_recursive", "v13_change_readout_only", "task_memory", "parent_heads_only"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(raw):
    return sha256(raw).hexdigest()


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")))


def check_lower_parents():
    """Reattest bytes even when text features have already been cached."""
    for path, pin in (
        (features.v13.DIRECTORY / "parent.json", features.v13.PARENT_SHA),
        (features.v13.DIRECTORY / "checkpoint.json", features.v13.MODEL_SHA),
        (features.v13.DIRECTORY / "protocol.json", features.v13.PROTOCOL_SHA),
        (features.recursive.MODEL, features.recursive.MODEL_SHA256),
    ):
        if digest(path.read_bytes()) != pin:
            raise ValueError("Changed retained lower parent: " + path.name)
    recursive = read(features.recursive.MODEL)
    for path, field in (
        (ROOT / "evidence/ntp_recursive_v1/protocol.json", "protocol_sha256"),
        (ROOT / "evidence/shared_cell_reading_v1/train.json", "source_sha256"),
    ):
        if digest(path.read_bytes()) != recursive[field]:
            raise ValueError("Changed recursive provenance")


def parent():
    check_lower_parents()
    manifest, model = previous.artifact("manifest.json"), previous.artifact("weights.json.gz")
    if manifest["final_stage"] != 143:
        raise ValueError("V14 requires the complete PR-143 parent")
    for name, pin in manifest["inputs"].items():
        if digest((previous.DIRECTORY / name).read_bytes()) != pin:
            raise ValueError("Changed inherited cumulative input: " + name)
    if (manifest["v13_parent"], manifest["v13_readout"], manifest["ntp_parent"]) != (
        features.v13.PARENT_SHA, features.v13.MODEL_SHA, features.recursive.MODEL_SHA256
    ):
        raise ValueError("Changed retained lower parent")
    return manifest, model


def make_layout(manifest, model):
    hidden = len(model["shared_columns"])
    offset = features.DIM + hidden
    heads = []
    for task in manifest["tasks"]:
        labels = manifest["labels"][task]
        heads.append({"task": task, "labels": labels, "start": offset, "end": offset + len(labels)})
        offset += len(labels)
    return {
        "schema": "nabt.cumulative-v14-skill-layout.v1",
        "raw": [0, features.DIM],
        "parent_hidden": [features.DIM, features.DIM + hidden],
        "parent_skills": [features.DIM + hidden, offset],
        "heads": heads,
        "dimension": offset,
        "normalization": "PER_HEAD_SOFTMAX_MINUS_UNIFORM",
        "authority": "OBSERVATION_ONLY",
    }


def softmax(values):
    top = max(values)
    out = [math.exp(v - top) for v in values]
    norm = sum(out)
    return [v / norm for v in out]


def _matrix(value, rows, columns, name):
    if type(value) is not list or len(value) != rows:
        raise ValueError("Invalid shape: " + name)
    for row in value:
        if type(row) is not list or len(row) != columns:
            raise ValueError("Invalid shape: " + name)
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in row):
            raise ValueError("Non-finite or non-numeric weight: " + name)


def validate_weights(weights, layout, labels, hidden):
    if set(weights) != {"adapter_columns", "adapter_bias", "residual_heads", "gates"}:
        raise ValueError("Unexpected residual weight fields")
    _matrix(weights["adapter_columns"], hidden, layout["dimension"], "adapter_columns")
    _matrix([weights["adapter_bias"]], 1, hidden, "adapter_bias")
    if set(weights["residual_heads"]) != set(labels) or set(weights["gates"]) != set(labels):
        raise ValueError("Missing or extra inherited task head")
    for task, names in labels.items():
        _matrix(weights["residual_heads"][task], len(names), hidden + 1, task)
        gate = weights["gates"][task]
        if type(gate) not in (float, int) or not math.isfinite(gate) or gate not in (0, .25, .5, 1):
            raise ValueError("Invalid calibrated residual gate")


def load(directory=None):
    directory = Path(directory) if directory is not None else DIRECTORY
    if directory.is_symlink():
        raise ValueError("V14 model directory is a symbolic link")

    def installed(name):
        path = directory / name
        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("V14 model input escapes its installed directory")
        return path

    manifest = read(installed("manifest.json"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError("Unknown V14 model")
    pm, pmodel = parent()
    expected_parent = {
        "commit": PARENT_COMMIT,
        "weights_sha256": previous.PINS["weights.json.gz"],
        "manifest_sha256": previous.PINS["manifest.json"],
        "final_stage": 143,
    }
    if canonical(manifest.get("parent")) != canonical(expected_parent):
        raise ValueError("V14 parent lineage does not match the installed ancestor")
    if (canonical(manifest.get("labels")) != canonical(pm["labels"])
            or canonical(manifest.get("tasks")) != canonical(pm["tasks"])):
        raise ValueError("V14 changed inherited task or label identities")
    for name, pin in manifest["inputs"].items():
        if name not in ("protocol.json", "skill_layout.json", "training.json"):
            raise ValueError("Unexpected model input path")
        if digest(installed(name).read_bytes()) != pin:
            raise ValueError("Changed V14 input: " + name)
    if set(manifest["inputs"]) != {"protocol.json", "skill_layout.json", "training.json"}:
        raise ValueError("Incomplete V14 input binding")
    raw = installed("weights.json.gz").read_bytes()
    if digest(raw) != manifest["weights_sha256"]:
        raise ValueError("Changed V14 residual weights")
    layout, protocol = read(installed("skill_layout.json")), read(installed("protocol.json"))
    if canonical(layout) != canonical(make_layout(pm, pmodel)):
        raise ValueError("Changed inherited skill layout")
    if manifest.get("variant") not in ("full", "without_task_memory"):
        raise ValueError("Unknown V14 feature variant")
    hidden = protocol.get("adapter_hidden")
    if type(hidden) is not int or not 1 <= hidden <= 256:
        raise ValueError("Invalid adapter width")
    weights = json.loads(gzip.decompress(raw))
    validate_weights(weights, layout, pm["labels"], hidden)
    return {"manifest":manifest,"weights":weights,"parent_manifest":pm,
            "parent_model":pmodel,"layout":layout,"protocol":protocol}


def parent_state(pmodel, x):
    if len(x) != features.DIM or any(type(v) not in (int,float) or not math.isfinite(v) for v in x):
        raise ValueError("Invalid parent feature vector")
    return [math.tanh(sum(a*b for a,b in zip(x,c,strict=True))) for c in pmodel["shared_columns"]]


def parent_logits(pmodel, task, hidden):
    return [r[-1]+sum(a*b for a,b in zip(hidden,r[:-1],strict=True)) for r in pmodel["heads"][task]]


def memory_features(pmodel, layout, x):
    hidden = parent_state(pmodel,x)
    out = list(x) + hidden
    for item in layout["heads"]:
        probabilities = softmax(parent_logits(pmodel,item["task"],hidden))
        out.extend(v - 1/len(probabilities) for v in probabilities)
    return out, hidden


def _mask_raw(x, channel):
    values = list(x)
    if channel == "v13":
        indices = [*range(features.HASH_DIM,features.HASH_DIM+32),features.DIM-3,features.DIM-1]
    elif channel == "ntp_recursive":
        indices = [*range(features.HASH_DIM+32,features.DIM-3),features.DIM-2]
    elif channel == "v13_change_readout_only":
        indices = [features.DIM-1]
    else:
        indices = []
    for i in indices:
        values[i] = 0.0
    return values


def observe(bundle, task, x, *, ablate=None):
    if task not in bundle["parent_manifest"]["labels"]:
        raise ValueError("No trained head for task")
    if ablate is not None and ablate not in ABLATIONS:
        raise ValueError("Unknown ablation channel")
    pmodel, weights, layout = bundle["parent_model"],bundle["weights"],bundle["layout"]
    original_hidden = parent_state(pmodel,x)
    original_logits = parent_logits(pmodel,task,original_hidden)
    changed_x = _mask_raw(x,ablate)
    values, hidden = memory_features(pmodel,layout,changed_x)
    base = parent_logits(pmodel,task,hidden)
    if bundle["manifest"].get("variant","full") == "without_task_memory" or ablate == "task_memory":
        for i in range(layout["parent_hidden"][0],layout["dimension"]):
            values[i] = 0.0
    elif ablate == "parent_heads_only":
        for i in range(*layout["parent_skills"]):
            values[i] = 0.0
    h = [math.tanh(b+sum(a*v for a,v in zip(col,values,strict=True)))
         for col,b in zip(weights["adapter_columns"],weights["adapter_bias"],strict=True)]
    delta = [row[-1]+sum(a*b for a,b in zip(h,row[:-1],strict=True))
             for row in weights["residual_heads"][task]]
    gate = weights["gates"][task]
    scores = [a+gate*b for a,b in zip(base,delta,strict=True)]
    labels = bundle["parent_manifest"]["labels"][task]
    chosen = labels[max(range(len(scores)),key=scores.__getitem__)]
    inherited = labels[max(range(len(original_logits)),key=original_logits.__getitem__)]
    return {"label":chosen,"parent_label":inherited,"changed":chosen!=inherited,
            "gate":gate,"authority":"NONE","review_only":True}


@lru_cache(maxsize=16384)
def _cached_text_features(text):
    return tuple(features.features(text,_cached_lower_models()))


@lru_cache(maxsize=1)
def _cached_lower_models():
    return features.parents()


def text_features(text):
    check_lower_parents()
    return _cached_text_features(text)


text_features.cache_clear = _cached_text_features.cache_clear


def project(task,text,label):
    return corpus_verbs.apply_script(json.loads(label),corpus_verbs.carriers(text)) if task == "root_recipe" else label


def propose(bundle,task,text,*,ablate=None):
    if type(text) is not str or not text.strip():
        raise ValueError("Expected source text")
    result = observe(bundle,task,list(text_features(text)),ablate=ablate)
    return dict(result,value=project(task,text,result["label"]),
                parent_value=project(task,text,result["parent_label"]))
