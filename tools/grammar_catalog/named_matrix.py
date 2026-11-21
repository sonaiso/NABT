"""Typed binary observations projected into the installed signed ground checker.

One source ledger denotes one time/place/reference frame. Occurrence identity,
agent, patient and instruments are binary edges on an event, never a product
of two unrelated event rows. Only the fixed rules below are admitted.
"""
from collections import defaultdict
from hashlib import sha256
import re

from nabt.text_reader import parse_document
from tools import explainable_pilot as pilot, verified_reading as ground
from tools.licensed_inference.runtime import aggregate_evidence
from . import lineage_roles, role_forms, usul_ledger
from .genus_chains import ancestors
from .operations import ROOT

# Arguments carry explicit sorts. Material types and the types of their
# bearers share the sort نوع but enter different predicates.
THRESHOLDS = {
    "حد_السعة_مترمربع": ("مساحة_مترمربع","صفة_واسع","ge"),
    "حد_الصغر_كممربع": ("مساحة_كممربع","صفة_صغير_المساحة","lt"),
    "حد_الكبر_كم": ("قطر_كم","صفة_كبير_القطر","ge"),
    "حد_القرب_متر": ("مسافة_متر","صفة_قريب","le"),
    "حد_البعد_متر": ("مسافة_متر","صفة_بعيد","ge"),
}
BASE = {
    **{name: ("نوع","عدد") for name in THRESHOLDS},
    "قطر_كم": ("عين","عدد"), "مساحة_كممربع": ("عين","عدد"),
    "يباين": ("نوع","نوع"), "وجود_مشهود": ("عين","نطاق"),
    "نوع": ("نوع", "نوع"), "عضوية": ("عين", "نوع"), "لازم": ("نوع", "صفة"),
    "خاصية": ("عين", "صفة"), "اسم_كلي": ("لفظ", "نوع"), "علم": ("لفظ", "عين"),
    "جنس_حيوي": ("عين", "جنس"), "مرحلة": ("عين", "عمر"), "والد": ("عين", "عين"),
    "زوج": ("عين", "عين"), "مادة": ("عين", "نوع"), "مكون": ("عين", "نوع"),
    "غذاء_لصنف": ("عين", "نوع"), "طول_سم": ("عين", "عدد"), "مساحة_مترمربع": ("عين", "عدد"),
    "مسافة_متر": ("عين", "عدد"), "قوة_نيوتن": ("عين", "عدد"), "عمر_شهر": ("عين", "عدد"),
    "نمط": ("حدث", "عمل"), "فاعل": ("حدث","عين"), "محل": ("حدث","عين"),
    "وسيلة": ("حدث","عين"), "مادة_داخلة": ("حدث","نوع"), "ناتج": ("حدث","عين"),
    "شرط": ("حدث","عمل"), "مانع": ("حدث","عمل"), "وقع": ("حدث","عمل"),
    "قابلية_النوع": ("نوع","عمل"), "تلائم": ("نوع","عمل"),
}
DERIVED = {
    **{p: ("عين","عين") for p in ("أب","أم","ابن","ابنة","إخوة_بوالد","أخ","أخت","عم","زوجية","حمو_والد_الزوج","سلف","سلف_مشترك","اشتراك_بخاصية","أطول","أوسع","أقرب","أقوى","أكبر_عمرا")},
    "يشترك_بأصل": ("نوع","نوع"), "يسمى": ("عين","لفظ"), "مادة_من_فئة": ("عين","نوع"),
    "أثر_على": ("حدث","عين"), "قابل": ("عين","عمل"), "ممكن_بشروطه": ("حدث","عمل"), "أثر_مروي": ("حدث","عمل"),
}
# The neutral sibling predicate means at least one shared parent, never full siblinghood.
BASE.update(usul_ledger.BASE)
DERIVED.update(usul_ledger.DERIVED)
BASE.update(lineage_roles.BASE)
DERIVED.update(lineage_roles.DERIVED)
SORTS = BASE | DERIVED
MEASURES = {"طول_سم":"أطول", "مساحة_مترمربع":"أوسع", "مسافة_متر":"أقرب",
            "قوة_نيوتن":"أقوى", "عمر_شهر":"أكبر_عمرا"}
# Patterns use named join columns; identifiers with '_' here are constants.
RULES = [
    ("عضوية_صاعدة", "عضوية x h", ["عضوية x g","نوع g h"]),
    ("تباين_أمامي", "!عضوية x b", ["عضوية x a","يباين a b"]),
    ("تباين_عكسي", "!عضوية x a", ["عضوية x b","يباين a b"]),
    ("سلف_مشترك","سلف_مشترك x y",["سلف a x","سلف a y"]),
    ("خاصية_مشتركة","اشتراك_بخاصية x y",["خاصية x p","خاصية y p"]),
    ("صفة_لازمة", "خاصية x p", ["عضوية x g","لازم g p"]),
    ("اسم_كلي", "يسمى x w", ["عضوية x g","اسم_كلي w g"]),
    ("علم_معين", "يسمى x w", ["علم w x"]),
    ("فئة_المادة", "مادة_من_فئة x g", ["مادة x g"]),
    ("أصل_المادة", "مادة_من_فئة x h", ["مادة_من_فئة x g","نوع g h"]),
    ("سلف_مباشر", "سلف x y", ["والد x y"]),
    ("سلف_متعد", "سلف x z", ["سلف x y","والد y z"]),
    ("أبوة", "أب x y", ["والد x y","جنس_حيوي x جنس_ذكر"]),
    ("أمومة", "أم x y", ["والد x y","جنس_حيوي x جنس_أنثى"]),
    ("بنوة", "ابن y x", ["والد x y","جنس_حيوي y جنس_ذكر"]),
    ("بنت", "ابنة y x", ["والد x y","جنس_حيوي y جنس_أنثى"]),
    ("والد_مشترك", "إخوة_بوالد x y", ["والد p x","والد p y"]),
    ("أخوة", "أخ x y", ["إخوة_بوالد x y","جنس_حيوي x جنس_ذكر"]),
    ("أختية", "أخت x y", ["إخوة_بوالد x y","جنس_حيوي x جنس_أنثى"]),
    ("عمومة", "عم u c", ["أخ u f","أب f c"]),
    ("زوجية_مباشرة", "زوجية x y", ["زوج x y"]),
    ("زوجية_متناظرة", "زوجية y x", ["زوج x y"]),
    ("مصاهرة_مقيدة", "حمو_والد_الزوج p x", ["زوجية x s","أب p s"]),
    ("لبوة", "يسمى x لفظ_لبوة", ["عضوية x نوع_أسد","جنس_حيوي x جنس_أنثى"]),
    ("شبل", "يسمى x لفظ_شبل", ["عضوية x نوع_أسد","مرحلة x عمر_صغير"]),
    ("نمرة", "يسمى x لفظ_نمرة", ["عضوية x نوع_نمر","جنس_حيوي x جنس_أنثى"]),
    ("صغير_النمر", "يسمى x لفظ_صغير_النمر", ["عضوية x نوع_نمر","مرحلة x عمر_صغير"]),
    ("قردة", "يسمى x لفظ_قردة", ["عضوية x نوع_قرد","جنس_حيوي x جنس_أنثى"]),
    ("صغير_القرد", "يسمى x لفظ_قرد_صغير", ["عضوية x نوع_قرد","مرحلة x عمر_صغير"]),
    ("طفولة", "يسمى x لفظ_طفل", ["عضوية x نوع_إنسان","مرحلة x عمر_طفولة"]),
    ("رجل", "يسمى x لفظ_رجل", ["عضوية x نوع_إنسان","مرحلة x عمر_راشد","جنس_حيوي x جنس_ذكر"]),
    ("امرأة", "يسمى x لفظ_امرأة", ["عضوية x نوع_إنسان","مرحلة x عمر_راشد","جنس_حيوي x جنس_أنثى"]),
    ("شيخ_سنا", "يسمى x لفظ_شيخ_سنا", ["عضوية x نوع_إنسان","مرحلة x عمر_شيخوخة","جنس_حيوي x جنس_ذكر"]),
    ("شيخوخة_رشد", "مرحلة x عمر_راشد", ["مرحلة x عمر_شيخوخة"]),
    ("قابلية_منصوصة", "قابل x a", ["عضوية x g","قابلية_النوع g a"]),
    ("قابلية_مشهد", "ممكن_بشروطه e a", ["نمط e a","محل e x","قابل x a","وسيلة e v","عضوية v g","تلائم g a","شرط e a","!مانع e a"]),
    ("حامل_الأثر","أثر_على e x",["أثر_مروي e a","محل e x"]),
    ("حدوث_في_النص", "أثر_مروي e a", ["نمط e a","وقع e a"]),
]
class MatrixLimit(ValueError):
    pass


def check_atom(a, allowed):
    pred, left, right = a
    if pred not in allowed:
        raise ValueError("Unknown or non-input predicate: " + str(pred))
    for val, sort in zip((left,right), SORTS[pred], strict=True):
        prefix = sort + "_"
        if not isinstance(val,str) or not val.startswith(prefix) or not val[len(prefix):] or len(val)>64 or not ground.valid_name(val):
            raise ValueError("Invalid typed term for " + pred)
        if sort == "عدد" and not re.fullmatch(r"(0|[1-9][0-9]{0,8})",val[len(prefix):]):
            raise ValueError("Expected a canonical nonnegative integer in the named unit")

def validate(p):
    if type(p) is not dict or set(p)!={"ledger","time","place","reference","known_at","queries"}:
        raise ValueError("Supply one complete observation frame, ledger and queries")
    for k in ("time","place","reference","known_at"):
        if type(p[k]) is not str or not p[k].strip() or len(p[k])>100:
            raise ValueError("Missing observation coordinate: "+k)
    if type(p["ledger"]) is not str or not 0<len(p["ledger"].encode())<=16000:
        raise ValueError("Expected a finite exact source ledger")
    if type(p["queries"]) is not list or not 1<=len(p["queries"])<=32:
        raise ValueError("Expected one to 32 typed questions")
    for q in p["queries"]:
        if type(q) is not list or len(q)!=3 or not all(isinstance(t,str) for t in q):
            raise ValueError("A question is a binary typed atom")
        check_atom(q,SORTS)

def wire_atom(triple):
    name,left,right=triple
    return {"predicate":name.lstrip("!"),"arguments":[left,right],"positive":not name.startswith("!")}

def read_ledger(text):
    doc=parse_document(text, source_id="names")
    if not doc.accepted or not 1<=len(doc.facts)<=80 or doc.rules or doc.definitions or doc.declarations or doc.queries:
        raise ValueError("Expected up to 80 ground source observations")
    out=[]
    for f in doc.facts:
        a=f.atom
        if len(a.args)!=2 or not a.ground:
            raise ValueError("A source row must be a ground binary relation")
        check_atom((a.predicate,*a.args),BASE)
        out.append(((("" if a.positive else "!")+a.predicate,*a.args),[f.span.start,f.span.end]))
    return out

def instantiate(pattern, binding):
    return (pattern[0],*(binding[t] if "_" not in t else t for t in pattern[1:]))

def match(body,index,binding,premises,budget):
    if not body:
        yield binding, premises
        return
    rel,*arguments=body[0]
    for row in index.get(rel,()):
        budget[0] -= 1
        if budget[0] < 0:
            raise MatrixLimit("Named matrix join budget exceeded")
        extended=binding.copy()
        for term,val in zip(arguments,row[1:],strict=True):
            if (term if "_" in term else extended.setdefault(term,val))!=val:
                break
        else:
            yield from match(body[1:],index,extended,premises+(row,),budget)

def projections(atoms, queries, *, text="", form_records=None):
    requested = {tuple(q) for q in queries}
    seen=set(atoms)
    traces={}
    def add(head,body,label):
        key=(head,body)
        if key not in traces:
            if len(traces)+len(atoms)>=246:
                raise MatrixLimit("Named matrix exceeds the ground owner's clause budget")
            traces[key]=label
        seen.add(head)
    for pred in ("نوع","والد"):
        edges=[(a,b) for p,a,b in atoms if p==pred]
        ancestors(edges,{x for edge in edges for x in edge})
    # Build class-ancestor paths with their actual edge evidence.
    for p,a,b in atoms:
        if p=="نوع":
            add(("سلسلة_نوع",a,b),((p,a,b),),"صعود_مباشر")
        if p in ("والد","زوج","يباين") and a==b:
            raise ValueError("Irreflexive relation")
    use_usul = (any(pred.lstrip("!") in usul_ledger.BASE for pred, _, _ in atoms)
                or any(q[0] in usul_ledger.DERIVED for q in queries))
    extra_rules = usul_ledger.RULES if use_usul else []
    if any(p.lstrip("!") in lineage_roles.BASE for p,_,_ in atoms) or any(q[0] in lineage_roles.DERIVED for q in queries):
        lineage_roles.prepare(atoms,add)
        occurrences = role_forms.compile_occurrences(atoms,text,add)
        if form_records is not None:
            form_records.extend(occurrences)
        extra_rules = extra_rules + lineage_roles.RULES
    rules=RULES+extra_rules+[("صعود_متعد","سلسلة_نوع x z",["سلسلة_نوع x y","نوع y z"]),
                 ("جنس_مشترك","يشترك_بأصل x y",["سلسلة_نوع x k","سلسلة_نوع y k"])]
    parsed=[(label,h.split(),[b.split() for b in body]) for label,h,body in rules]
    for rel,comparison in MEASURES.items():
        measurements=[row for row in atoms if row[0]==rel]
        for r in measurements:
            for s in measurements:
                if r[1]==s[1]:
                    if r[2]!=s[2]:
                        add(("!"+rel,r[1],r[2]),(s,),"قيمتان_لنفس_القياس")
                    continue
                a,b=int(r[2][4:]),int(s[2][4:])
                holds=a<b if comparison=="أقرب" else a>b
                add((comparison if holds else "!"+comparison,r[1],s[1]),(r,s),"مقارنة_"+rel)
    for bound,(metric,trait,op) in THRESHOLDS.items():
        for _,g,limit in (r for r in atoms if r[0]==bound):
            for _,x,v in (r for r in atoms if r[0]==metric):
                a,b=int(v[4:]),int(limit[4:])
                passed={"lt":a<b,"ge":a>=b,"le":a<=b}[op]
                body=(("عضوية",x,g),(metric,x,v),(bound,g,limit))
                add(("خاصية" if passed else "!خاصية",x,trait),body,"عتبة_"+metric)
    # In this declared sense, male and female are contrary assignments.
    for rel,x,v in atoms:
        if rel=="جنس_حيوي" and v in ("جنس_ذكر","جنس_أنثى"):
            other="جنس_ذكر" if v=="جنس_أنثى" else "جنس_أنثى"
            add(("!"+rel,x,other),((rel,x,v),),"تقابل_وسمي_الجنس")
    budget=[250000]
    while True:
        previous=len(seen)
        index=defaultdict(list)
        for row in sorted(seen):
            index[row[0]].append(row)
        for label,head,body in parsed:
            for binding,premises in match(body,index,{},(),budget):
                h=instantiate(head,binding)
                if h[0] in ("إخوة_بوالد","يشترك_بأصل","سلف_مشترك","اشتراك_بخاصية","عم","حمو_والد_الزوج") and h[1]==h[2]:
                    continue
                if h[0] in ("يشترك_بأصل","سلف_مشترك","اشتراك_بخاصية") and h not in requested:
                    continue
                add(h,premises,label)
        if len(seen)==previous:
            break
    if use_usul:
        usul_ledger.compile_scopes(atoms,add)
    return traces

def analyze(text,source_id,p):
    validate(p)
    observations=read_ledger(p["ledger"])
    atoms=[row for row,_ in observations]
    form_records=[]
    try:
        traces=projections(atoms,p["queries"],text=text,form_records=form_records)
    except MatrixLimit as exc:
        return {"status":"DEFER","reason":str(exc),"answers":[],"world_truth_established":False}
    facts=[wire_atom(a) for a in atoms]
    rules=[{"kind":"rule","body":[wire_atom(b) for b in body],"head":wire_atom(h)} for h,body in traces]
    program="".join(ground.render_clause(c) for c in [
        *({"kind":"fact","atom":f} for f in facts),*rules]).encode()
    q=("هل "+ground.render_atom(wire_atom(p["queries"][0]))+"؟\n").encode()
    try:
        cert=pilot.propose_certificate(program,q,"names","1","frame")
    except pilot.PilotError as exc:
        return {"status":"DEFER","reason":exc.code,"answers":[],"world_truth_established":False}
    try:
        receipt, fingerprint=pilot.native(program,q,cert,"names","1","frame",ROOT/"formal/.lake/build/bin/verifiedReading",20)
        check={"status":"VERIFIED_GROUND_PROJECTION","checker_sha256":fingerprint,"receipt":receipt}
    except pilot.PilotError as exc:
        check={"status":exc.code}
    signed={ground.key(a) for a in cert["known"]}
    clean={ground.key(a) for a in cert["clean_known"]}
    blocked={k for k in signed if ground.opposite(k) in signed}
    clean_rules=[r for r in rules if all(ground.key(x) not in blocked for x in [*r["body"],r["head"]])]
    witness_ids=defaultdict(list)
    for i,f in enumerate(facts):
        witness_ids[ground.key(f)].append(i+1)
    rule_source={str(r):i for i,r in enumerate(rules,1)}
    def support(known,steps,active):
        paths={}
        for a,st in zip(known,steps,strict=True):
            k=ground.key(a)
            if st["kind"]=="fact":
                paths[k]=(set(witness_ids[k]),set())
            else:
                r=active[st["index"]]
                children=[paths[ground.key(b)] for b in r["body"]]
                paths[k]=(set().union(*(v[0] for v in children)),
                          {rule_source[str(r)]}.union(*(v[1] for v in children)))
        return paths
    paths=support(cert["known"],cert["steps"],rules)
    clean_paths=support(cert["clean_known"],cert["clean_steps"],clean_rules)
    def explain(k):
        chosen=clean_paths.get(k,paths.get(k))
        if chosen is None:
            return None
        return {"observation_ids":sorted(chosen[0]),"rule_ids":sorted(chosen[1]),"clean":k in clean}
    records=[{"id":i,"fact":list(a),"source_span":span} for i,(a,span) in enumerate(observations,1)]
    answers=[]
    for query in p["queries"]:
        yes=ground.key(wire_atom(query)); no=ground.opposite(yes)
        status=aggregate_evidence([{"positive":yes in signed,"negative":no in signed,
            "clean_positive":yes in clean,"clean_negative":no in clean}])["status"]
        answers.append({"query":query,"status":status,"positive":explain(yes),"negative":explain(no)})
    return {"schema":"nabt.named-matrix.v1","source_id":source_id,"frame":{k:p[k] for k in ("time","place","reference","known_at")},
        "text_sha256":sha256(text.encode()).hexdigest(),"ledger_sha256":sha256(p["ledger"].encode()).hexdigest(),
        "checker":check,"status":"VERIFIED_PROJECTION" if check["status"]=="VERIFIED_GROUND_PROJECTION" else "PROPOSAL_ONLY",
        "python_lean_refinement_proved":False,"world_truth_established":False,"surface_alignment_established":False,"observations":records,
        **({"occurrence_forms":form_records} if form_records else {}),
        "rule_instances":[{"head":list(h),"body":[list(b) for b in body],"rule":label} for (h,body),label in traces.items()],
        "answers":answers}
