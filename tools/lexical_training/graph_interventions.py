"""Inductive node and edge proposals over the *prior* licensed NABT proof graph.

Portable inference. The network never reads the post-withdrawal result, node IDs
as features, lexical strings, or held-out labels. All predictions are advisory.
"""
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path

from tools.lexical_training import shared_encoder

MODEL = Path(__file__).with_name("data") / "graph_interventions_v1.json"
MODEL_SHA = "8c7e3baeae59fa5fb17ae26721a27cd8211cea1270342ac55e0664e28c6e8294"
SPACES = ("sign","concept","joint","ledger")
ROLES = ("sign","a116","word_kind","content","force","speech_particle","sense","indication",
         "candidate_sense","conditional_indication","ledger_premise","definition_witness","other")
WIDTH = len(SPACES)+len(ROLES)+2
HIDDEN = 8
EDGE_WIDTH = 5
MAX_NODES = 192


@dataclass
class Graph:
    ids: list
    spaces: list
    spans: list
    grades: list
    paths: list
    features: list


def encode(nodes):
    rows = sorted((n for n in nodes if n["status"]=="LICENSED"),key=lambda n:n["grade"])
    if len(rows)>MAX_NODES:
        raise ValueError("Graph exceeds inference budget")
    ids=[n["id"] for n in rows]
    pos={key:i for i,key in enumerate(ids)}
    spaces=[]; spans=[]; paths=[]; features=[]
    grades=[n["grade"] for n in rows]
    for i,n in enumerate(rows):
        space=n["transition"]["view"]
        role=n["role"] if n["role"] in ROLES else "other"
        span=n["transition"]["position"].get("utf8_span")
        routes=[[pos[p] for p in route] for route in n["satisfied_paths"]]
        if not routes or any(parent>=i for route in routes for parent in route):
            raise ValueError("Expected a prior licensed directed acyclic support graph")
        paths.append(routes)
        spaces.append(space)
        spans.append(span)
        features.append([float(space==s) for s in SPACES]+[float(role==r) for r in ROLES]+
                        [min(n["grade"],8)/8.,float(span is not None)])
    return Graph(ids,spaces,spans,grades,paths,features)


def geometry(g,i,j):
    """Features allowed even when the candidate edge is withheld."""
    a,b=g.spans[i],g.spans[j]
    overlap=0.
    if a is not None and b is not None:
        overlap=max(0,min(a[1],b[1])-max(a[0],b[0])) / max(1,max(a[1],b[1])-min(a[0],b[0]))
    gap=g.grades[j]-g.grades[i]
    return [1.,float(gap==1),1./gap,overlap,float(g.spaces[i]==g.spaces[j])]


def dot(a,b):
    return sum(x*y for x,y in zip(a,b,strict=True))


def sigmoid(value):
    return 1./(1.+math.exp(-max(-50., min(50., value))))


def representations(g,w):
    return [[math.tanh(dot(x,row)+bias) for row,bias in zip(w["projection"],w["bias"],strict=True)]
            for x in g.features]


def message(routes, values):
    # A conjunction can lose any premise; alternative supports must all be affected.
    return min(max((values[i] for i in route),default=0.) for route in routes)


def effects(g,z,w,removed,*,use_edges=True):
    values=[]
    for i,routes in enumerate(g.paths):
        m=message(routes,values) if use_edges else 0.
        values.append(sigmoid(dot(w["effect"],[1.,float(i in removed),m,*z[i]])))
    return values


def links(g,z,w):
    queries=[[dot(row,v) for row in w["relation"]] for v in z]
    result=[]
    for j in range(len(z)):
        candidates=[]
        for i in range(j):
            if g.grades[i]<g.grades[j]:
                score=dot(z[i],queries[j])+dot(w["geometry"],geometry(g,i,j))
                candidates.append((i,sigmoid(score)))
        result.append(sorted(candidates,key=lambda p:-p[1]))
    return result


@lru_cache(maxsize=1)
def load(raw):
    if sha256(raw).hexdigest()!=MODEL_SHA:
        raise ValueError("Graph model identity changed")
    obj=json.loads(raw)
    if (obj["schema"]!="nabt.graph-intervention-weights.v1" or obj["spaces"]!=list(SPACES)
            or obj["roles"]!=list(ROLES) or obj["hidden"]!=HIDDEN):
        raise ValueError("Invalid graph readout")
    w=obj["parameters"]
    shapes={"projection":(HIDDEN,WIDTH),"bias":(HIDDEN,),"relation":(HIDDEN,HIDDEN),
            "geometry":(EDGE_WIDTH,),"effect":(3+HIDDEN,)}
    if set(w)!=set(shapes) or not all(shared_encoder._shape(w[k],shape) for k,shape in shapes.items()):
        raise ValueError("Invalid graph tensors")
    return w


def propose(nodes,withdraw):
    try:
        g=encode(nodes)
        if not g.ids:
            return {"status":"NO_LICENSED_NODES","authority":"NONE"}
        known={n["id"] for n in nodes}
        if any(key not in known for key in withdraw):
            return {"status":"UNBOUND_WITHDRAWAL","authority":"NONE"}
        w=load(MODEL.read_bytes())
        z=representations(g,w)
        removed={i for i,key in enumerate(g.ids) if key in withdraw}
        scores=effects(g,z,w,removed)
        neighbors=links(g,z,w)
        return {"status":"PROPOSED","authority":"NONE","model_sha256":MODEL_SHA,"hidden_dimension":HIDDEN,
                "rows":[{"id":key,"space":g.spaces[i],"vector":[round(x,8) for x in z[i]],
                         "withdrawn":i in removed,"loss_score":round(scores[i],8),"proposed_lost":scores[i]>=.5,
                         "candidate_edges":[{"from":g.ids[k],"to":key,"score":round(p,8)}
                                            for k,p in neighbors[i][:3]]} for i,key in enumerate(g.ids)],
                "admitted_edges_added":0,"world_truth_established":False}
    except (ValueError,OSError,KeyError) as err:
        return {"status":"MODEL_UNAVAILABLE","authority":"NONE","reason":str(err)}
