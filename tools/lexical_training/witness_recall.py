"""Local proposal of evidence order followed by source-bound decoding in a finite event profile."""
from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path

from . import shared_encoder as shared
from .contextual_alignment import occurrence_vectors
from tools.grammar_catalog import question_answer_cycle as cycle, question_cognition, question_frames
from tools.grammar_catalog.operations import digest

MODEL = Path(__file__).with_name("data") / "witness_recall_v1.json"
MODEL_SHA = "256d0afb7c9067f19e7cc119e6fe15ff62ad92141cee69d3b949df13ab70b6f7"
DIM = 4 * shared.HIDDEN
LABELS = tuple(question_frames.REQUIRED)
AXES = ("instrument", "arrival_condition")


def vector(model, text):
    rows, _ = occurrence_vectors(model, text)
    if not rows:
        raise ValueError("No encodable occurrence")
    return [sum(col)/len(rows) for col in zip(*(r["vector"] for r in rows), strict=True)]


@lru_cache(maxsize=1)
def _weights(encoder_bytes, head_bytes):
    if sha256(head_bytes).hexdigest() != MODEL_SHA:
        raise ValueError("Witness readout identity changed")
    head = json.loads(head_bytes)
    if sha256(encoder_bytes).hexdigest() != head["encoder_sha256"]:
        raise ValueError("Encoder and witness readout disagree")
    model = shared.validate_model(json.loads(encoder_bytes))
    if (head["schema"] != "nabt.witness-readout.v1"
        or head["question_labels"] != list(LABELS) or head["cue_labels"] != list(AXES)
        or not shared._shape(head["question"], (len(LABELS), DIM+1))
        or not shared._shape(head["cue"], (len(AXES), DIM+1))):
        raise ValueError("Invalid witness readout")
    return model, head


def load():
    if MODEL.stat().st_size > 100_000 or shared.MODEL.stat().st_size > 2_000_000:
        raise ValueError("Readout exceeds model budget")
    return _weights(shared.MODEL.read_bytes(), MODEL.read_bytes())


def distribution(rows, x):
    scores = [sum(a*b for a,b in zip(row,x+[1.0],strict=True)) for row in rows]
    values = [math.exp(s-max(scores)) for s in scores]
    return [v/sum(values) for v in values]


def propose(question, witnesses):
    try:
        encoder, head = load()
        q = distribution(head["question"], vector(encoder, question))
        # Joint queries may attend to either cue axis; occurrence has no textual evidence.
        mix = [q[0]+q[3], q[1]+q[3]]
        ranking = []
        for i, w in enumerate(witnesses):
            cue = distribution(head["cue"], vector(encoder, w["text"]))
            ranking.append({"index":i,"score":sum(a*b for a,b in zip(mix,cue,strict=True)),
                            "cue_distribution":dict(zip(AXES,cue,strict=True))})
        return {"status":"PROPOSED","authority":"NONE","model_sha256":MODEL_SHA,
                "encoder_sha256":head["encoder_sha256"],"question_distribution":dict(zip(LABELS,q,strict=True)),
                "rows":sorted(ranking,key=lambda a:(-a["score"],a["index"]))}
    except (ValueError,OSError,KeyError) as err:
        return {"status":"MODEL_UNAVAILABLE","authority":"NONE","rows":[],"reason":type(err).__name__}


def recall(text, question, source_id="input"):
    owner = question_cognition.analyze(text, question, source_id)
    report={"schema":"nabt.witness-recall.v1","source_id":source_id,"source_sha256":owner["source_sha256"],
            "question":question,"operation":owner["operation"],"status":owner["decision"]["status"],
            "world_truth_established":False,"owner":owner,"decoding":None}
    d=owner["decision"]
    if owner["operation"] not in LABELS or d["status"] not in cycle.SURFACES:
        return report
    raw=text.encode()
    memory=[]
    for i,r in enumerate(d["evidence"]):
        w=r["witness"]
        left,right=w["utf8_span"]
        if not 0<=left<right<=len(raw) or raw[left:right]!=w["text"].encode():
            raise ValueError("Evidence is not this source occurrence")
        occurrence=digest([source_id,report["source_sha256"],left,right])
        memory.append({"index":i,"occurrence":occurrence,"utf8_span":[left,right],"text":w["text"],
                       "axis":r["axis"],"positive":r["positive"]})
    neural=propose(question,[{"text":w["text"]} for w in memory])
    order=[row["index"] for row in neural["rows"]] if neural["status"]=="PROPOSED" else list(range(len(memory)))
    certificates=[p["evidence_ids"] for p in d["minimal_supports"]]
    if d["status"]=="OPEN":
        selected=[]
        reason=cycle.TWO
    else:
        # Prefer shortest complete support, using learned order only among valid alternatives.
        selected=min(certificates,key=lambda group:(len(group), sorted(order.index(i) for i in group),group))
        reason="الشاهد "+" و".join("«"+memory[i]["text"]+"»" for i in selected)
    answer=cycle.SURFACES[d["status"]]+"؛ "+reason+"."
    grade=cycle.grade_event(answer,d)
    if not grade["complete"]:
        raise ValueError("Decoded answer failed independent owner grading")
    report.update(memory=memory,proposal=neural,decoding={"answer":answer,"grade":grade,
                 "selected_occurrences":[memory[i]["occurrence"] for i in selected],"selected_indices":selected,
                 "all_minimal_supports":certificates,"countermodels":d["alternatives"],
                 "fixed_premises":d["fixed_premises"],"source_frame":d["frame"],
                 "preserved_conflicts":d["conflicting_axes"],"complete_source_retained":text})
    return report
