"""Compose finite opening-domain readings over the observed text and its compatible vocalizations."""
from dataclasses import dataclass, field
import json

from nabt.corpus_evidence import lookup_clusters
from nabt.productive_forms import replay_policy
from . import awamil_occurrence, classical_roles, passive_relation, valency
from .source_evidence_view import pinned_excerpts


# These are authored lexical restrictions for this reading, not corpus-frequency or world facts.
# Keep the feminine inflection on the lexical head even when the construct's dependent has another gender.
OBJECTS = (("الْبَاب","بَاب","m"), ("الصُّنْدُوق","صُنْدُوق","m"),
           ("النَّافِذَة","نَافِذَة","f"), ("الْبَوَّابَة","بَوَّابَة","f"))
LOCATIONS = ("الْمَدْرَسَة", "الْقَرْيَة", "الْبَيْت", "الْمَكْتَب")
COLLECTIVES = ("أَهْل","طُلَّاب","عُمَّال")
TIME_WORDS = ("الظُّهْرِ","الْعَصْرِ","الْفَجْرِ","الْمَغْرِبِ")
LAW = "nabt.partial-opening-speech.v1"


def face(token, *exemplars):
    written = token["surface"]
    return next((v for v in exemplars if classical_roles.compatible(written,v)),None)


@dataclass
class Phrase:
    end: int
    gender: str
    forms: list


def noun(terms, i, ending):
    if i >= len(terms):
        return None
    for definite, stem, gender in OBJECTS:
        full = face(terms[i], definite+ending)
        if full:
            return Phrase(i+1, gender, [full])
        head = face(terms[i], stem+ending)
        if head and i+1<len(terms):
            genitive = face(terms[i+1], *(v+"ِ" for v in LOCATIONS))
            if genitive:
                return Phrase(i+2, gender, [head,genitive])
    return None


@dataclass
class Reading:
    force: str
    content: str
    begin: int
    end: int
    cue: int | None = None
    roles: list = field(default_factory=list)
    forms: dict = field(default_factory=dict)
    rules: set = field(default_factory=set)
    details: dict = field(default_factory=dict)

    def bind(self, role, start, exemplar_forms, family="predication_argument"):
        end = start+len(exemplar_forms)
        self.roles.append((role,start,end,family))
        self.forms.update(zip(range(start,end),exemplar_forms))


def adjunct(terms, i):
    if i==len(terms):
        return []
    if i+1==len(terms):
        for role,forms in (("time",("أَمْسِ","غَدًا","غَداً","صَبَاحًا","مَسَاءً")),
                           ("instrument",("بِالْمِفْتَاحِ",))):
            exemplar=face(terms[i],*forms)
            if exemplar:
                return [(role,i,[exemplar],"restriction")]
    if i+2==len(terms):
        before_after = face(terms[i],"قَبْلَ","بَعْدَ")
        limit = face(terms[i+1],*TIME_WORDS)
        if before_after and limit:
            return [("time",i,[before_after,limit],"restriction")]
    return None


def state(terms, start, force, cue=None):
    n=noun(terms,start,"َ" if force in ("hope","wish") else "ُ")
    if not n or n.end+1!=len(terms):
        return None
    suffix = "َةٌ" if n.gender=="f" else "ٌ"
    for stem,sense in (("مَفْتُوح","open"),("مُغْلَق","close")):
        pred=face(terms[n.end],stem+suffix)
        if pred:
            r=Reading(force,"STATE_ASCRIBED",start,len(terms),cue)
            r.rules.update(("predication","participle",sense))
            r.bind("property_bearer",start,n.forms)
            r.bind("state",n.end,[pred])
            if len(n.forms)>1:
                r.bind("possessor",start+1,n.forms[1:],"restriction")
            return r
    return None


def active_question(terms, i, cue):
    verb=face(terms[i],"فَتَحَ")
    if not verb or i+3>len(terms):
        return None
    # Explore both postverbal orders. An actor/patient can bind only its licensed lexical slot.
    for obj_first in (False,True):
        if obj_first:
            patient=noun(terms,i+1,"َ")
            who=patient.end if patient else len(terms)
        else:
            who=i+1
            patient=noun(terms,i+2,"َ")
        if not patient or who>=len(terms):
            continue
        actor=face(terms[who],*(v+"ُ" for v in valency.PEOPLE))
        end=max(who+1,patient.end)
        modifiers=adjunct(terms,end)
        if not actor or modifiers is None:
            continue
        r=Reading("ask","REPORTED_MATRIX_EVENT",i,len(terms),cue)
        r.bind("verb_governor",i,[verb],"governor")
        r.bind("opener",who,[actor])
        r.bind("opened_entity",i+1 if obj_first else i+2,patient.forms)
        for args in modifiers:
            r.bind(*args)
        r.rules.update(("question","open","agent","arity"))
        return r
    return None


def directive(terms, start, *, plural_only=False):
    if start+1>=len(terms):
        return None
    plural=face(terms[start],"اِفْتَحُوا")
    contact=terms[start+1]["surface"].startswith("ال")
    singular_forms = ("اِفْتَحِ","اِفْتَحْ") if contact else ("اِفْتَحْ",)
    singular = face(terms[start],*singular_forms)
    verb=plural or (None if plural_only else singular)
    patient=noun(terms,start+1,"َ")
    if not verb or not patient:
        return None
    modifiers=adjunct(terms,patient.end)
    if modifiers is None:
        return None
    r=Reading("request","فتح",start,len(terms),start)
    r.bind("verb_governor",start,[verb],"governor")
    r.bind("opened_entity",start+1,patient.forms)
    for args in modifiers:
        r.bind(*args)
    r.rules.update(("open","imperative","arity"))
    r.details.update(addressed_profile="2MP" if plural else "2MS",specific_addressee=None)
    return r


def negative(terms):
    if len(terms)<3:
        return None
    forms = ["يُفْتَحْ","تُفْتَحْ"]
    if terms[2]["surface"].startswith("ال"):
        forms.extend(("يُفْتَحِ","تُفْتَحِ"))
    verb=face(terms[1],*forms)
    first=lookup_clusters(terms[1]["surface"])
    if not verb or not first or "ُ" not in first[0][1]:
        return None
    patient=noun(terms,2,"ُ")
    if not patient or (verb.startswith("ت") != (patient.gender=="f")):
        return None
    modifiers=adjunct(terms,patient.end)
    if modifiers is None:
        return None
    r=Reading("assert","DENY_PASSIVE",0,len(terms),0)
    r.bind("negation",0,["لَمْ"],"governor")
    r.bind("verb_governor",1,[verb],"governor")
    r.bind("passive_subject",2,patient.forms)
    for args in modifiers:
        r.bind(*args)
    r.rules.update(("lam","open","passive_pattern","passive_subject"))
    r.details.update(voice="passive",polarity="denied",specific_actor=None,
                     operator_conditional=terms[0]["surface"]!="لَمْ",
                     competing_operator="لِمَ" if face(terms[0],"لِمَ") else None)
    return r


def parse(text, terms):
    if not 2<=len(terms)<=12:
        return [],None
    if any(not lookup_clusters(t["surface"]) for t in terms):
        return [],"INVALID_OR_OUTSIDE_WRITTEN_MARKS"
    start=terms[0]["codepoint_span"][0]
    stop=terms[-1]["codepoint_span"][1]
    if text[:start].strip(" \t"):
        return [],"UNCONSUMED_PREFIX"
    ending=text[stop:].strip(" \t")
    breaks=[]
    for i,(a,b) in enumerate(zip(terms,terms[1:])):
        gap=text[a["codepoint_span"][1]:b["codepoint_span"][0]]
        if gap.strip(" \t") in ("،",","):
            breaks.append(i+1)
        elif not gap or gap.strip(" \t"):
            return [],"UNCONSUMED_SEPARATOR"
    if breaks:
        if breaks!=[3] or len(terms)<5 or ending not in ("",".","!") or not face(terms[0],"يَا"):
            return [],"UNBOUND_CLAUSE_BOUNDARY"
        group=face(terms[1],*(v+"َ" for v in COLLECTIVES))
        place=face(terms[2],*(v+"ِ" for v in LOCATIONS))
        following=directive(terms,3,plural_only=True)
        if not group or not place or not following:
            return [],"INCOMPLETE_ADDRESSEE_OR_DIRECTIVE"
        r=Reading("vocative","ADDRESSED_GROUP",1,3,0)
        r.forms[0]="يَا"
        r.bind("addressee",1,[group,place])
        r.bind("possessor",2,[place],"restriction")
        r.rules.add("vocative")
        return [r,following],None
    ask=face(terms[0],"هَلْ","هَلِ")
    if ask and (ending in ("","؟","?")):
        if terms[0]["surface"].endswith("ِ") and not terms[1]["surface"].startswith("ال"):
            return [],"INCOMPATIBLE_CONNECTED_OPERATOR"
        r=active_question(terms,1,0) or state(terms,1,"ask",0)
        if r:
            r.forms[0]=ask
            r.rules.add("question")
            return [r],None
    if ending not in ("",".","!"):
        return [],"UNBOUND_PUNCTUATION"
    for form,force in (("لَيْتَ","wish"),("لَعَلَّ","hope")):
        if face(terms[0],form):
            r=state(terms,1,force,0)
            if r:
                r.forms[0]=form
                r.rules.add("inna")
                if force=="hope":
                    r.details["operator_face"]="ترجٍّ في الوجه التعليمي؛ تعيين المقام يحتاج قرينة"
                return [r],None
            return [],"CASE_AGREEMENT_OR_UNCOVERED_NOMINAL"
    if face(terms[0],"لَمْ"):
        r=negative(terms)
        return ([r],None) if r else ([],"PASSIVE_VOICE_OR_ARGUMENT_EVIDENCE_REQUIRED")
    r=directive(terms,0) or state(terms,0,"assert")
    return ([r],None) if r else ([],"NO_COMPLETE_REVIEWED_FRAME")


def citations(keys):
    awamil,_=awamil_occurrence.curriculum()
    sources=(awamil,passive_relation._inventory(),classical_roles.inventory(),json.loads(valency.DATA.read_bytes()))
    result={}
    for src in sources:
        selected=sorted((keys-result.keys()) & src["witnesses"].keys())
        result.update(pinned_excerpts(src,selected))
    if "imperative" in keys:
        result["imperative"]=next(p for p in replay_policy()["passages"] if p["source_id"]=="qatr" and "الطلب" in p["raw_text"])
    if result.keys()!=keys:
        raise ValueError("Missing support for a partial reading")
    return result


def extend(g):
    terms=g.owners["terms"]
    rows, debt=parse(g.text,terms)
    g.report["partial_speech"]={"law":LAW,"status":"CONDITIONAL_READING" if rows else "OPEN",
                                "missing":debt,"spelling_rewritten":False,"intended_sense_established":False}
    for index,r in enumerate(rows):
        roles=[]
        items=[]
        for role,begin,end,family in r.roles:
            w=valency.span(g.text,terms[begin:end])
            items.append({"role":role,"witness":w})
            roles.append((role,w,["roles",len(items)-1],family,"represented_content"))
            if role=="time":
                r.rules.add("adverb")
            if role=="instrument":
                r.rules.add("jarr")
            if end-begin>1 and role in ("opened_entity","passive_subject","property_bearer","addressee"):
                r.rules.add("possession")
        observed=[]
        for j,exemplar in sorted(r.forms.items()):
            t=terms[j]
            if not face(t,exemplar):
                raise ValueError("A written mark contradicts its retained reading")
            a,b=lookup_clusters(t["surface"]),lookup_clusters(exemplar)
            missing=[{"local_carrier_index":k,"marks":sorted(y[1]-x[1])} for k,(x,y) in enumerate(zip(a,b,strict=True)) if y[1]-x[1]]
            observed.append({"observed":t["surface"],"utf8_span":t["utf8_span"],"compatible_form":exemplar,
                             "unwritten_marks":missing})
        record={"law":LAW,"basis":"AUTHORED_LEXICAL_DOMAIN_AND_COMPLETE_CONSTRUCTION","forms":observed,"roles":items,
                "scope":"SOURCE_CONDITIONAL","world_truth_established":False,"witnesses":citations(r.rules),**r.details}
        cue=terms[r.cue]["utf8_span"] if r.cue is not None else None
        content=valency.span(g.text,terms[r.begin:r.end])["utf8_span"]
        g.reading("partial/"+str(index),record,r.force,r.content,roles,cue=cue,scope_span=content)
    if len(rows)==2:
        g.report["partial_speech"]["sequence"]=[d["force_node"] for d in g.report["decoded"]]
