"""Portable ordered-byte GRU proposals over the existing definition identities.

No normalization, token sorting, pickle, caller model path, or acceptance head.
The raw trace is exact; the learned hidden state is not claimed to be lossless.
Training lives separately so external replay needs only Python's standard library.
"""
from hashlib import sha256
import math
import subprocess
from pathlib import Path

from tools import lexical_testimony as owner
from . import concepts

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "evidence/shared_cognition_v1/model.json"
SCHEMA = "nabt.shared-byte-gru.v1"
HEADS = ("reading", "morphology", "concept", "attachment", "witness")
EMBEDDING, HIDDEN, MAX_BYTES = 12, 24, 256


def validate_request(request):
    if type(request) is not dict or set(request) != {"text"}:
        raise ValueError("Expected only text; model paths and labels are not inputs")
    text = request["text"]
    if type(text) is not str or not text.strip() or len(text.encode()) > MAX_BYTES:
        raise ValueError("Expected nonempty UTF-8 text within 256 bytes")
    return text


def byte_ids(text):
    validate_request({"text": text})
    return [b + 1 for b in text.encode("utf-8")]


def _shape(value, dims):
    if not dims:
        return type(value) in (int, float) and math.isfinite(value) and abs(value) <= 1000
    return type(value) is list and len(value) == dims[0] and all(_shape(x, dims[1:]) for x in value)


def load_model(path=MODEL):
    if path.stat().st_size > 2_000_000:
        raise ValueError("Model byte limit")
    raw = path.read_bytes()
    m = owner._strict_json(raw)
    if (type(m) is not dict or set(m) != {"schema", "architecture", "labels", "parameters", "concept_references",
                   "training_sha256", "protocol", "authority"}
            or m["schema"] != SCHEMA or m["authority"] != "NONE"
            or m["architecture"] != {"embedding": EMBEDDING, "hidden": HIDDEN,
                                      "vocabulary": 257, "max_bytes": MAX_BYTES}
            or type(m["labels"]) is not dict or set(m["labels"]) != set(HEADS)
            or type(m["parameters"]) is not dict or type(m["concept_references"]) is not dict):
        raise ValueError("Model contract changed")
    for h, labels in m["labels"].items():
        if (type(labels) is not list or not 1 <= len(labels) <= 64
                or any(type(x) is not str or not x or len(x) > 128 for x in labels)
                or len(set(labels)) != len(labels)):
            raise ValueError("Model labels invalid")
    shapes = {"embedding.weight": (257, EMBEDDING),
              "gru.weight_ih_l0": (3 * HIDDEN, EMBEDDING),
              "gru.weight_hh_l0": (3 * HIDDEN, HIDDEN),
              "gru.bias_ih_l0": (3 * HIDDEN,), "gru.bias_hh_l0": (3 * HIDDEN,)}
    for h in HEADS:
        shapes[f"heads.{h}.weight"] = (len(m["labels"][h]), HIDDEN)
        shapes[f"heads.{h}.bias"] = (len(m["labels"][h]),)
    if set(m["parameters"]) != set(shapes) or any(
            not _shape(m["parameters"][k], dims) for k, dims in shapes.items()):
        raise ValueError("Model tensor shape or finite value invalid")
    return m, sha256(raw).hexdigest()


def _linear(w, b, x):
    return [bias + sum(a * v for a, v in zip(row, x)) for row, bias in zip(w, b)]


def _sigmoid(x):
    return 1 / (1 + math.exp(-max(-700, min(700, x))))


def logits(model, text):
    p = model["parameters"]
    hidden = [0.] * HIDDEN
    for token in byte_ids(text):
        i = _linear(p["gru.weight_ih_l0"], p["gru.bias_ih_l0"], p["embedding.weight"][token])
        h = _linear(p["gru.weight_hh_l0"], p["gru.bias_hh_l0"], hidden)
        r = [_sigmoid(i[j] + h[j]) for j in range(HIDDEN)]
        z = [_sigmoid(i[j + HIDDEN] + h[j + HIDDEN]) for j in range(HIDDEN)]
        n = [math.tanh(i[j + 2*HIDDEN] + r[j] * h[j + 2*HIDDEN]) for j in range(HIDDEN)]
        hidden = [(1-z[j]) * n[j] + z[j] * hidden[j] for j in range(HIDDEN)]
    return {head: _linear(p[f"heads.{head}.weight"], p[f"heads.{head}.bias"], hidden)
            for head in HEADS}


def propose(request):
    text = validate_request(request)
    raw = text.encode()
    result = {"schema": "nabt.shared-neural-proposal.v1", "status": "DEFER",
              "raw_text": text, "utf8_hex": raw.hex(), "byte_ids": byte_ids(text),
              "trace_sha256": sha256(raw).hexdigest(), "heads": {},
              "authority": "NONE", "intended_sense_established": False,
              "world_truth_established": False, "grammar_certified": False,
              "hidden_state_is_lossless": False, "all_installed_concepts_retained": False}
    try:
        m, identity = load_model()
        definitions = concepts.catalogue()
        refs = {r["identity"]["id"]: r["reference"] for r in definitions["concepts"]}
        if m["concept_references"] != refs or set(m["labels"]["concept"]) != set(refs):
            raise ValueError("Model definition identities are stale")
        scores = logits(m, text)
        for head in HEADS:
            result["heads"][head] = sorted(
                [{"label": label, "score": score,
                  **({"concept_reference": refs[label]} if head == "concept" else {})}
                 for label, score in zip(m["labels"][head], scores[head])],
                key=lambda row: (-row["score"], row["label"]))
        result.update(status="PROPOSED", model_sha256=identity,
                      all_installed_concepts_retained=True,
                      next_obligation="BIND_OCCURRENCE_AND_CHECK_EVIDENCE_WITH_EXISTING_OWNER")
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result["reason"] = type(error).__name__
    return result


def observe_lesson(adapter, payload):
    """Attach proposals to original owner inputs, without rewriting premises.

    A supplied source ID is a trace locator, not an accepted concept alignment.
    Long sources are deferred intact rather than silently clipped or normalized.
    """
    if adapter == "source_learning":
        sources = [(r["id"], r["text"], f"/payload/sources/{i}/text")
                   for i,r in enumerate(payload["sources"])]
    elif adapter == "qualified_inference":
        sources = [(payload["source_id"], payload["source_text"], "/payload/source_text")]
    else:
        return {"status":"UNMAPPED_INPUT_CONTRACT", "observations":[],
                "owner_evidence_modified":False}
    rows=[]
    for index,(source_id,text,pointer) in enumerate(sources):
        raw=text.encode()
        row={"source_id":source_id,"input_pointer":pointer,"source_sha256":sha256(raw).hexdigest(),
             "source_byte_length":len(raw),"source_text":text,"proposal":None}
        if index >= 8 or len(raw)>MAX_BYTES:
            row["status"]="NEURAL_BUDGET_DEFER"
        else:
            row["proposal"]=propose({"text":text})
            row["status"]=row["proposal"]["status"]
        rows.append(row)
    return {"status":"OBSERVED" if all(r["status"]=="PROPOSED" for r in rows) else "PARTIAL",
            "observations":rows,"owner_evidence_modified":False,
            "concept_alignment":"PROPOSALS_ONLY_REQUIRES_OCCURRENCE_WITNESS",
            "revision_owner":"EXISTING_OWNER_HISTORY_AND_ACTIVE_SOURCES"}
