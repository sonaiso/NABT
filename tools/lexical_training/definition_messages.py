"""Masked relational message passing over admitted, sense-specific evidence edges."""
from functools import lru_cache
from hashlib import sha256
import json
import math

from tools.grammar_catalog.operations import ROOT

MODEL="evidence/definition_inheritance_v1/weights.json"
MODEL_SHA='30c802154509ea1fa1a6072a77da1fd1074af69313484d53812e92393f910e20'
REL=("is_a","has_attribute","has_property","denotes_property")
LABELS=("Q", "M", "G", "P", "A")
# Directed subtype messages preserve the current semantic role. A bridge to
# property/attribute changes the state carried along that path.
STATES=("G","P","A","has_property","has_attribute","denotes_property")


def transition_input(state,relation):
    return [1.,*(float(s==state) for s in STATES),*(float(r==relation) for r in REL)]


def state_label(state):
    return {"has_property":"Q","denotes_property":"M","has_attribute":"A"}.get(state,state)


def scores(x,weights):
    hidden=[math.tanh(sum(a*b for a,b in zip(x,w,strict=True))) for w in weights["hidden"]]
    return [sum(a*b for a,b in zip([1.,*hidden],w,strict=True)) for w in weights["out"]]


@lru_cache(maxsize=1)
def decode(raw):
    return json.loads(raw)


def predict_paths(focus,edges,claims,weights):
    """Predict only on proof paths already authenticated by the owner."""

    from tools.grammar_catalog.definition_network import axis
    vectors={}
    for claim in claims:
        proposals=[]
        for path in claim["proofs"]:
            state=axis(focus)
            for eid in path:
                r=edges[eid]["relation"]
                logits=scores(transition_input(state,r),weights)
                best=max(logits)
                probs=[math.exp(v-best) for v in logits]
                z=sum(probs)
                winner=LABELS[logits.index(best)]
                if winner=="Q":state="has_property"
                elif winner=="M":state="denotes_property"
                elif winner=="A" and (state=="has_attribute" or r=="has_attribute"):state="has_attribute"
                else:state=winner
            proposals.append([v/z for v in probs])
        # Keep meanings reached by distinct licensed relations separate.
        vector=[sum(v)/len(proposals) for v in zip(*proposals,strict=True)]
        vectors[claim["relation"]+"/"+claim["node"]]={"coordinates":[round(x,8) for x in vector],
                  "proposal":LABELS[vector.index(max(vector))],"support_count":len(proposals)}
    return {"status":"PROPOSALS","coordinate_ids":list(LABELS),
            "coordinate_meanings":["خاصية يحملها الجنس","خاصية تدل عليها الصفة","جنس","نوع خاصية","صفة"],
            "vectors":vectors,"authority":"NONE"}


def propagate(focus,edges,claims):
    try:
        raw=(ROOT/MODEL).read_bytes()
        if sha256(raw).hexdigest()!=MODEL_SHA:
            raise ValueError("DEFINITION_WEIGHTS_CHANGED")
        weights=decode(raw)
    except (OSError,ValueError) as exc:
        return {"status":"WEIGHTS_UNAVAILABLE","reason":str(exc),"authority":"NONE"}
    return {**predict_paths(focus,edges,claims,weights),"model_sha256":MODEL_SHA}
