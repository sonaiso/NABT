"""Interpret one lexical sense at a time through a typed, witnessed subclass graph."""
from collections import defaultdict, deque
from functools import lru_cache
from hashlib import sha256
import json
import re

from tools import explainable_pilot as pilot, verified_reading as ground
from . import dictionary_reading as dictionary
from .operations import ROOT

LAW = "nabt.definition-inheritance.v1"
SOURCE_PATH = dictionary.SOURCE.relative_to(ROOT)
RESOURCE = ROOT / "tools/grammar_catalog/data/definition_inheritance_v1.json"
RESOURCE_SHA = "dcce5187a048a16c1c290a1e128ac7e47916ff0ca240a0cbb6f6a0a8d9fd1f3c"
AXES = {"G":"جنس", "P":"خاصية", "A":"صفة"}
RELATIONS = ("is_a","has_attribute","has_property","denotes_property")
# A predicate arrived at along a path retains its type. These are the only
# permitted compositions; containment, part-of, synonymy and causes are absent.
PRODUCT = {
    **{("self", r):r for r in RELATIONS},
    **{("is_a", r):r for r in RELATIONS},
    ("has_attribute","is_a"):"has_attribute", ("has_property","is_a"):"has_property",
    ("denotes_property","is_a"):"denotes_property",
    ("has_attribute","denotes_property"):"has_property",
}
QUERY = re.compile(r"ما شبكة «([^«»\s]{1,40})»(?: بعد سحب شاهد «([^«»\n]{1,140})»)?[؟?]?")
CHECKER = ROOT / "formal/.lake/build/bin/verifiedReading"


def axis(node):
    return node.split(":",1)[0]


def label(node):
    return node.split(":",1)[1].replace("_"," ")


def edge_key(e):
    return "/".join(e[k] for k in ("child","relation","parent","witness"))


def inventory():
    raw=RESOURCE.read_bytes()
    if sha256(raw).hexdigest()!=RESOURCE_SHA:
        raise ValueError("DEFINITION_REVIEW_IDENTITY_CHANGED")
    return compile_review(raw)


@lru_cache(maxsize=1)
def compile_review(raw):
    data=json.loads(raw)
    nodes={n["id"]:n for n in data["nodes"]}
    if len(nodes)!=len(data["nodes"]) or any(axis(k) not in AXES for k in nodes):
        raise ValueError("Invalid definition nodes")
    by_child=defaultdict(list)
    for e in data["edges"]:
        u,r,v=e["child"],e["relation"],e["parent"]
        if u not in nodes or v not in nodes or e["witness"] not in data["witnesses"]:
            raise ValueError("Undefined endpoint or witness")
        axes=(axis(u),axis(v))
        valid=(r=="is_a" and axes[0]==axes[1]) or (r,axes) in {
            ("has_attribute",("G","A")),("has_property",("G","P")),("denotes_property",("A","P"))}
        if not valid:raise ValueError("Unlicensed relation signature")
        by_child[u].append(e)
    complete=set()
    def visit(node,trail):
        if node in trail:raise ValueError("Cyclic definition review")
        if node not in complete:
            for e in by_child[node]:visit(e["parent"],trail|{node})
            complete.add(node)
    for node in nodes:visit(node,set())
    return nodes,by_child,data["witnesses"]


def witness_rows(refs, raw, withdrawn):
    rows={}
    for key,ref in refs.items():
        a,b=ref["span"]
        chunk=raw[a:b]
        if len(chunk)!=b-a or sha256(chunk).hexdigest()!=ref["sha256"]:
            rows[key]={**ref,"status":"SOURCE_UNAVAILABLE"}
        else:
            quote=chunk.decode()
            rows[key]={**ref,"quote":quote,"status":"WITHDRAWN_IN_SCENARIO" if quote==withdrawn else "REPLAYED",
                       "source_path":str(SOURCE_PATH)}
    return rows


def routes(focus,by_child):
    """All candidate paths in this finite, validated DAG. Each proof has its own witnesses."""
    pending=deque([(focus,"self",())])
    while pending:
        u,mode,path=pending.popleft()
        for e in by_child.get(u,()):
            new=PRODUCT.get((mode,e["relation"]))
            if new is None:continue
            extended=(*path,e)
            yield e["parent"],new,extended
            pending.append((e["parent"],new,extended))


def atom(predicate,node):
    return {"predicate":predicate,"arguments":[node],"positive":True}


def encode(node):
    return node.replace(":","_")


def prove(focus, paths, witnesses, identity, revision):
    """Ground rules are conditional on a source fact for every traversed edge."""
    seed=atom("reachable_self",encode(focus))
    clauses=[{"kind":"fact","atom":seed}]
    facts,rules=set(),set()
    for node,mode,path in paths:
        e=path[-1]
        tag="w_"+e["witness"]
        proof=atom("attested",tag)
        if tag not in facts and witnesses[e["witness"]]["status"]=="REPLAYED":
            clauses.append({"kind":"fact","atom":proof})
            facts.add(tag)
        previous="self"
        for step in path[:-1]:
            previous=PRODUCT[previous,step["relation"]]
        step=(e["child"],previous,node,mode,tag)
        if step in rules:continue
        rules.add(step)
        clauses.append({"kind":"rule","body":[atom("reachable_"+previous,encode(e["child"])),proof],
                        "head":atom("reachable_"+mode,encode(node))})
    raw="".join(ground.render_clause(c) for c in clauses).encode()
    query=("هل "+ground.render_atom(seed)+"؟\n").encode()
    scope="definition_inheritance_v1"
    cert=pilot.propose_certificate(raw,query,identity,revision,scope)
    receipt,checker=pilot.native(raw,query,cert,identity,revision,scope,CHECKER,20)
    clean={ground.key(a) for a in cert["clean_known"]}
    keys={(n,m) for n,m,_ in paths if ground.key(atom("reachable_"+m,encode(n))) in clean}
    return keys,{"checker_sha256":checker,"canonical_sha256":sha256(raw).hexdigest(),"receipt":receipt,
                 "scope":"CONDITIONAL_GROUND_PROJECTION","source_to_rule_refinement_proved":False}


def one_reading(focus,by_child,witnesses,identity,revision):
    paths=list(routes(focus,by_child))
    direct={edge_key(e):e for _,_,p in paths for e in p}
    desired=defaultdict(list)
    for node,mode,p in paths:
        if all(witnesses[e["witness"]]["status"]=="REPLAYED" for e in p):
            desired[node,mode].append([edge_key(e) for e in p])
    keys,replay=prove(focus,paths,witnesses,identity,revision)
    if keys!=set(desired):
        raise ValueError("INHERITANCE_AND_GROUND_REPLAY_DISAGREE")
    used={k for pp in desired.values() for path in pp for k in path}
    active={k:direct[k] for k in sorted(used)}
    claims=[{"node":n,"axis":axis(n),"relation":mode,"proofs":desired[n,mode]} for n,mode in sorted(keys)]
    # Coordinates keep their meaning between cases and after withdrawals.
    nodes,_,_=inventory()
    vocabulary=sorted(nodes)
    bits=[int(any(n==k for n,_ in keys)) for k in vocabulary]
    from tools.lexical_training.definition_messages import propagate
    return {"focus":focus,"claims":claims,"edges":active,
            "suspended_edges":sorted(set(direct)-used),
            "witnesses":{k:witnesses[k] for k in sorted({e["witness"] for e in direct.values()})},
            "focus_status":"QUERY_ASSUMPTION", "vector":{"basis":vocabulary,"mask":bits,"provenance":"NATIVE_CHECKED_WITNESS_PATHS"},
            "licensed_spaces":sorted({axis(k) for k,_ in keys}),
            "neural":propagate(focus,active,claims),"ground_check":replay}


def read(text,dictionary_report=None,identity="input"):
    query=QUERY.fullmatch(text)
    if not query and not (dictionary_report and dictionary_report.get("readings")):
        return None
    report={"schema":LAW,"source_sha256":sha256(text.encode()).hexdigest(),"readings":[],
            "authority":"CONDITIONAL_DEFINITION_INTERPRETATION","world_truth_established":False,
            "scope":"REVIEWED_SENSE_EDGES_ONLY","review_sha256":RESOURCE_SHA}
    try:
        nodes,by_child,refs=inventory()
        # Dictionary integration binds by specific sense ID. An explicit
        # network question additionally supports source-reviewed local senses.
        if query:
            word,withdrawn=query.groups()
            start,stop=query.span(1)
            occurrence=[len(text[:start].encode()),len(text[:stop].encode())]
            focuses=[k for k,n in nodes.items() if n["lemma"] and dictionary.compatible(word,n["lemma"])]
        else:
            if dictionary_report.get("source_sha256")!=report["source_sha256"]:
                raise ValueError("DICTIONARY_OCCURRENCE_MISMATCH")
            ids={r["sense_id"] for r in dictionary_report["readings"]}
            focuses=[k for k,n in nodes.items() if n["sense_id"] and n["sense_id"] in ids]
            occurrence=(dictionary_report.get("context_occurrence") or {}).get("utf8_span",
                         dictionary_report["query"]["citation_span"])
            withdrawn=None
        report.update(occurrence_span=occurrence,withdrawn=withdrawn)
        if not focuses:return {**report,"status":"NO_REVIEWED_NETWORK"}
        witnesses=witness_rows(refs,dictionary.SOURCE.read_bytes(),withdrawn)
        relevant={e["witness"] for f in focuses for _,_,path in routes(f,by_child) for e in path}
        if withdrawn and not any(witnesses[k].get("quote")==withdrawn for k in relevant):
            return {**report,"status":"WITHDRAWAL_NOT_BOUND_TO_READING"}
        for focus in focuses:
            r=one_reading(focus,by_child,witnesses,identity,report["source_sha256"])
            r["dictionary_sense_id"]=nodes[focus]["sense_id"]
            report["readings"].append(r)
        missing=any(witnesses[k]["status"]=="SOURCE_UNAVAILABLE" for k in relevant)
        return {**report,"status":"PARTIAL_SOURCE" if missing else "VERIFIED_CONDITIONAL_NETWORK"}
    except (ValueError,OSError) as exc:
        return {**report,"status":"VERIFICATION_UNAVAILABLE","reason":str(exc),"readings":[]}


def cards(report):
    from .text_reading import card
    if report["status"] not in {"PARTIAL_SOURCE","VERIFIED_CONDITIONAL_NETWORK"}:
        return [card("definition_network","إرجاء","تعذّر حسم السلسلة المطلوبة.",
                     report["status"],"يتطلب الوجه تعريفًا وشواهد مطابقة في النطاق المراجع.")]
    result=[]
    for r in report["readings"]:
        names="، ".join(label(c["node"]) for c in r["claims"])
        proof=max((p for c in r["claims"] for p in c["proofs"]),key=len,default=[])
        chain=[label(r["focus"])]+[label(r["edges"][e]["parent"]) for e in proof]
        result.append(card("definition_network","قراءة تعريفية مشروطة",
                           AXES[axis(r["focus"])]+" «"+label(r["focus"])+"»: "+(names or "لا نتيجة من الشواهد الباقية")+".",
                           "مسار الشاهد: "+" ← ".join(chain)+".",
                           "تخصّ الوراثة هذا الوجه من التعريف. ويبقى انطباقه على فرد محتاجًا إلى شاهد.",
                           focus=r["focus"],law=LAW))
    if report["status"]=="PARTIAL_SOURCE":
        result.append(card("technical","نقص في الشاهد","تعذّر فحص بعض شواهد السلسلة.",
                           "حُجبت المسارات التابعة للشاهد المتعذر.","تبقى المسارات المستقلة قابلة للفحص."))
    return result
