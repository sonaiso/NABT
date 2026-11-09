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
MAX_SOURCE_BYTES, MAX_SOURCE_TERMS = 8192, 128
SOURCE_WINDOW_LAW = "nabt.shared-source-windows.v1"
CELL_MODEL = ROOT / "evidence/shared_cell_reading_v1/model.json"
CELL_SCHEMA = "nabt.shared-a116-gru.v1"
CELL_HEADS = ("reading", "morphology", "attachment")


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


def validate_source_request(request):
    if type(request) is not dict or set(request)!={'text'}:
        raise ValueError('Expected only source text')
    source_windows(request['text'])
    return request['text']


def source_windows(text):
    """Partition the exact parent source at token boundaries for the same GRU.

    The trained 256-byte encoder is unchanged. Windows reset its state; no
    cross-window semantic/context completeness is claimed. Never split a word,
    combining mark, UTF-8 scalar, or silently discard the remaining source.
    """
    from bisect import bisect_right
    from tools.grammar_catalog.operations import exact_terms
    from tools.evidence_lifecycle_v1 import ResourceLimit
    if type(text) is not str or not text.strip():
        raise ValueError("Expected nonempty UTF-8 source text")
    raw = text.encode("utf-8", errors="strict")
    if len(raw) > MAX_SOURCE_BYTES:
        raise ResourceLimit("Shared source byte budget exceeded")
    terms = exact_terms(text)
    if len(terms) > MAX_SOURCE_TERMS:
        raise ResourceLimit("Shared source occurrence budget exceeded")
    if any(t["utf8_span"][1]-t["utf8_span"][0] > MAX_BYTES for t in terms):
        raise ValueError("A single term exceeds the trained encoder window")
    offsets = [0]
    for c in text: offsets.append(offsets[-1]+len(c.encode()))
    windows, start = [], 0
    while start < len(text):
        end = bisect_right(offsets, offsets[start]+MAX_BYTES)-1
        for term in terms:
            a,b = term["codepoint_span"]
            if a < end < b:
                end = a
                break
        if end <= start:
            raise ResourceLimit("No whole-token encoder window fits")
        part = text[start:end]
        windows.append({"index":len(windows), "text":part,
                        "codepoint_span":[start,end], "utf8_span":[offsets[start],offsets[end]],
                        "sha256":sha256(part.encode()).hexdigest()})
        start = end
    return windows


def _shape(value, dims):
    if not dims:
        return type(value) in (int, float) and math.isfinite(value) and abs(value) <= 1000
    return type(value) is list and len(value) == dims[0] and all(_shape(x, dims[1:]) for x in value)


def load_model(path=MODEL):
    if path.stat().st_size > 2_000_000:
        raise ValueError("Model byte limit")
    raw = path.read_bytes()
    m = owner._strict_json(raw)
    validate_model(m)
    return m, sha256(raw).hexdigest()


def validate_model(m):
    """Validate the installed shared representation, also used by its extension."""
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
    return m


def _linear(w, b, x):
    return [bias + sum(a * v for a, v in zip(row, x)) for row, bias in zip(w, b)]


def _sigmoid(x):
    return 1 / (1 + math.exp(-max(-700, min(700, x))))


def states_for_ids(model, tokens):
    """Internal encoder trajectory; callers retain the original byte trace."""
    p = model["parameters"]
    hidden = [0.] * HIDDEN
    states = [hidden]
    for token in tokens:
        i = _linear(p["gru.weight_ih_l0"], p["gru.bias_ih_l0"], p["embedding.weight"][token])
        h = _linear(p["gru.weight_hh_l0"], p["gru.bias_hh_l0"], hidden)
        r = [_sigmoid(i[j] + h[j]) for j in range(HIDDEN)]
        z = [_sigmoid(i[j + HIDDEN] + h[j + HIDDEN]) for j in range(HIDDEN)]
        n = [math.tanh(i[j + 2*HIDDEN] + r[j] * h[j + 2*HIDDEN]) for j in range(HIDDEN)]
        hidden = [(1-z[j]) * n[j] + z[j] * hidden[j] for j in range(HIDDEN)]
        states.append(hidden)
    return states


def cell_ids(cells):
    """The kernel's exact A116 codes, shifted once to reserve neural PAD=0."""
    from nabt.alphabet import validate_cells
    value = validate_cells(cells)
    if not value or len(value)>64:
        raise ValueError("Expected one to 64 canonical A116 cells")
    return [c+1 for c in value]


def load_cell_model(path=CELL_MODEL):
    from nabt.alphabet import ALPHABET_ID
    if path.stat().st_size>2_000_000: raise ValueError("Cell model byte limit")
    raw = path.read_bytes(); model = owner._strict_json(raw)
    if (type(model) is not dict or set(model)!={"schema","alphabet_id","architecture","labels",
            "parameters","training_sha256","protocol","authority"}
            or model["schema"]!=CELL_SCHEMA or model["alphabet_id"]!=ALPHABET_ID
            or model["authority"]!="NONE" or model["architecture"]!={
                "embedding":EMBEDDING,"hidden":HIDDEN,"vocabulary":117,"max_cells":64,"pad":0,"cell_offset":1}
            or any(type(v) is not int for v in model['architecture'].values())
            or type(model["labels"]) is not dict or set(model["labels"])!=set(CELL_HEADS)):
        raise ValueError("Cell model identity changed")
    shapes={"embedding.weight":(117,EMBEDDING),"gru.weight_ih_l0":(3*HIDDEN,EMBEDDING),
            "gru.weight_hh_l0":(3*HIDDEN,HIDDEN),"gru.bias_ih_l0":(3*HIDDEN,),"gru.bias_hh_l0":(3*HIDDEN,)}
    for head,labels in model["labels"].items():
        if (type(labels) is not list or not 2<=len(labels)<=64 or any(type(x) is not str or not x for x in labels)
                or len(labels)!=len(set(labels))):raise ValueError("Cell labels invalid")
        shapes[f"heads.{head}.weight"]=(len(labels),HIDDEN);shapes[f"heads.{head}.bias"]=(len(labels),)
    if (type(model["parameters"]) is not dict or set(model["parameters"])!=set(shapes)
            or any(not _shape(model["parameters"][k],v) for k,v in shapes.items())):
        raise ValueError("Cell model tensors invalid")
    training=path.with_name("train.json")
    if training.stat().st_size>2_000_000:raise ValueError("Cell training budget exceeded")
    from tools.evidence_lifecycle_v1 import wire
    if sha256(wire(owner._strict_json(training.read_bytes())).encode()).hexdigest()!=model["training_sha256"]:
        raise ValueError("Cell training provenance changed")
    return model,sha256(raw).hexdigest()


def cell_logits(model, cells):
    return head_logits(model,states_for_ids(model,cell_ids(cells))[-1])


def head_logits(model, hidden):
    p = model["parameters"]
    return {head: _linear(p[f"heads.{head}.weight"], p[f"heads.{head}.bias"], hidden)
            for head in model["labels"]}


def logits(model, text):
    return head_logits(model, states_for_ids(model, byte_ids(text))[-1])


def propose(request):
    text = validate_source_request(request)
    raw = text.encode()
    result = {"schema": "nabt.shared-neural-proposal.v1", "status": "DEFER",
              "raw_text": text, "utf8_hex": raw.hex(), "byte_ids": [b+1 for b in raw],
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
        def ranked(scores):
            return {head: sorted(
                [{"label": label, "score": score,
                  **({"concept_reference": refs[label]} if head == "concept" else {})}
                 for label, score in zip(m["labels"][head], scores[head])],
                key=lambda row: (-row["score"], row["label"])) for head in HEADS}
        if len(raw)<=MAX_BYTES:
            result['heads']=ranked(logits(m,text))
        else:
            result['window_proposals']=[{**window,'heads':ranked(head_logits(m,
                states_for_ids(m,[b+1 for b in window['text'].encode()])[-1]))}
                for window in source_windows(text)]
            result.update(source_window_law=SOURCE_WINDOW_LAW,source_restored=True,
                          context_scope='WITHIN_WINDOW_ONLY',cross_window_context_established=False)
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
        if index >= 8 or len(raw)>MAX_SOURCE_BYTES:
            row["status"]="NEURAL_BUDGET_DEFER"
        else:
            from tools.evidence_lifecycle_v1 import ResourceLimit
            try:
                row["proposal"]=propose({"text":text})
                row["status"]=row["proposal"]["status"]
            except ResourceLimit:
                row['status']='NEURAL_BUDGET_DEFER'
            except ValueError:
                row['status']='NEURAL_INPUT_DEFER'
        rows.append(row)
    return {"status":"OBSERVED" if all(r["status"]=="PROPOSED" for r in rows) else "PARTIAL",
            "observations":rows,"owner_evidence_modified":False,
            "concept_alignment":"PROPOSALS_ONLY_REQUIRES_OCCURRENCE_WITNESS",
            "revision_owner":"EXISTING_OWNER_HISTORY_AND_ACTIVE_SOURCES"}
