"""Occurrence-local valency and scoped complement readings for a finite written profile."""
from hashlib import sha256
import json
from pathlib import Path

from .classical_roles import compatible
from .operations import ROOT, exact_terms
from .source_evidence_view import pinned_excerpts
from . import passive_relation

DATA = Path(__file__).with_name("data") / "valency_sources_v1.json"
# Each row selects one lexical sense. Arity counts direct object positions of the
# active verb, not the nominative subject or the number of written accusatives.
FRAMES = (
    ("جَلَسَ","جلوس","sitter",(),("arity",)),
    ("سَارَ","سير","mover",(),("arity",)),
    ("فَتَحَ","فتح","opener",("opened_entity",),("arity",)),
    ("أَعْطَى","إعطاء","giver",("recipient","transferred_item"),("arity",)),
    ("رَأَى","رؤية بصرية","perceiver",("perceived",),("perception",)),
    ("رَأَى","رأي قلبي","believer",("embedded_subject","embedded_predicate"),("perception",)),
    ("ظَنَّ","ظنّ","believer",("embedded_subject","embedded_predicate"),("arity",)),
    ("أَعْلَمَ","إعلام","informer",("addressee","embedded_subject","embedded_predicate"),("inform",)),
    ("ازْدَادَ","ازدياد","property_bearer",(),("specification","arity")),
)
PEOPLE=("الْحَارِس","الطَّالِب","الْمُعَلِّم","الْعَامِل","الْمُدِير","الْمُهَنْدِس","الطِّفْل")
THINGS=("الْبَاب","الْمِفْتَاح","الصُّنْدُوق","الْكِتَاب","الْمَكْتَب")
LEXICON=PEOPLE+THINGS+("النَّيْل","الْجِدَار")
DOMAIN={"sitter":PEOPLE,"perceiver":PEOPLE,"perceived":LEXICON,"mover":PEOPLE,"opener":PEOPLE,"giver":PEOPLE,"believer":PEOPLE,
        "informer":PEOPLE,"property_bearer":LEXICON,"recipient":PEOPLE,"addressee":PEOPLE,
        "opened_entity":("الْبَاب","الصُّنْدُوق"),"transferred_item":THINGS,"embedded_subject":LEXICON}
CLAIM_LICENSE="SOURCE_RELATIVE_WRITTEN_READING"


def marked(surface, expected, marks="ًٌٍَُِْ"):
    return compatible(surface,expected) and any(m in surface for m in marks)


def nominal(token, role, ending):
    if role=="embedded_predicate":
        return any(marked(token["surface"],s,"ً") for s in ("مَفْتُوحًا","حَاضِرًا","مُغْلَقًا"))
    return any(marked(token["surface"],stem+ending,ending) and token["surface"].endswith(ending)
               for stem in DOMAIN[role])


def span(text, terms):
    a=terms[0]["codepoint_span"][0]
    b=terms[-1]["codepoint_span"][1]
    return {"surface":text[a:b],"utf8_span":[terms[0]["utf8_span"][0],terms[-1]["utf8_span"][1]]}


def edge(name,syntax,witness,scope="matrix"):
    return {"role":name,"syntax":syntax,"witness":witness,"scope":scope}


def opening(text, terms):
    """A passive subjunctive clause has its own subject even when its whole is a matrix object."""
    if len(terms)!=3:
        return None
    cue,verb,bearer=terms
    if not marked(cue["surface"],"أَنْ") and not compatible(cue["surface"],"لِكَيْ"):
        return None
    if not (marked(verb["surface"],"يُفْتَحَ","ُ") and verb["surface"].endswith("َ")
            and nominal(bearer,"opened_entity","ُ")):
        return None
    return {"clause":span(text,terms),"cue":cue,"verb":verb,"bearer":bearer,"masdar":"فتح",
            "voice":"passive","inner_role":"نائب فاعل","specific_agent":None,"wording_mood":"مضارع مبني للمجهول منصوب في هذا الوجه",
            "time_from_masdar":None,"world_occurrence":False}


def projection(masdar, force, arity, roles, refs, **extra):
    return {"masdar":masdar,"force":force,"active_object_arity":arity,"roles":roles,
            "rule_ids":list(dict.fromkeys(refs)),"world_occurrence_established":False,
            "empirical_cause_established":False,"external_effect_established":False,
            "genus_membership_established":False,"inherited_property_established":False,**extra}


def modifier(text, terms, pos, masdar):
    tail=terms[pos:]
    t=tail[0]; s=t["surface"]
    def bind(n,role,syntax,ref):
        return n,[edge(role,syntax,span(text,tail[:n]))],ref
    if any(marked(s,e,"ً") for e in ("صَبَاحًا","مَسَاءً","لَيْلًا")):
        return bind(1,"time","مفعول فيه زمان","adverb")
    if len(tail)>=2 and marked(s,"أَمَامَ") and any(marked(tail[1]["surface"],x+"ِ","ِ") and
            tail[1]["surface"].endswith("ِ") for x in THINGS):
        return bind(2,"place","مفعول فيه مكان مع مضاف إليه","adverb")
    if masdar=="فتح" and marked(s,"فَتْحًا","ً"):
        return bind(1,"event_emphasis","مفعول مطلق مؤكد","absolute")
    if masdar=="جلوس" and marked(s,"جُلُوسًا","ً"):
        return bind(1,"event_emphasis","مفعول مطلق مؤكد","absolute")
    if masdar in {"فتح","جلوس"} and len(tail)>=2 and marked(s,"إِكْرَامًا","ً") and any(
            compatible(tail[1]["surface"],form) for form in ("لِلضَّيْفِ","لِلطَّالِبِ")):
        return bind(2,"stated_motive","مفعول لأجله مع متعلّقه","motive")
    if masdar=="سير" and marked(s,"وَالنَّيْلَ") and s.endswith("َ"):
        return bind(1,"companion","مفعول معه","with")
    if masdar=="ازدياد" and any(marked(s,x,"ً") for x in ("عِلْمًا","طُولًا","وَزْنًا")):
        return bind(1,"property_dimension","تمييز نسبة","specification")
    if masdar=="فتح" and marked(s,"بِالْمِفْتَاحِ","ِ"):
        return bind(1,"instrument","جار ومجرور في قراءة الآلة","arity")
    return None


def finite_clause(text, terms):
    head=terms[0]
    if len(terms)==3 and compatible(head["surface"],"سَارَ") and nominal(terms[1],"mover","ُ"):
        word=terms[2]["surface"]
        if word.startswith("و"):
            rest=word[1:].lstrip("َ")
            companion=any(compatible(rest,stem+"َ") for stem in PEOPLE)
            coactor=any(compatible(rest,stem+"ُ") for stem in PEOPLE)
            if companion or coactor:
                alternatives=[name for yes,name in ((companion,"المعية"),(coactor,"العطف على الفاعل")) if yes]
                return projection("سير","ALTERNATIVE_READINGS" if len(alternatives)>1 else "REPORTED_MATRIX_EVENT",0,
                         [edge("mover","فاعل",terms[1]),edge("waw_dependent"," أو ".join(alternatives),terms[2])],
                         ["agent","with","arity"],waw_alternatives=alternatives,governor=head)
    for verb,masdar,actor,slots,rules in FRAMES:
        if not marked(head["surface"],verb) or len(terms)<2+len(slots):
            continue
        # Keep the finite licensed order explicit; the general grammatical owner
        # can retain separate analyses for other orders and omitted arguments.
        if not nominal(terms[1],actor,"ُ"):
            continue
        args=terms[2:2+len(slots)]
        if not all(nominal(t,slot,"َ") for t,slot in zip(args,slots,strict=True)):
            continue
        roles=[edge(actor,"فاعل",terms[1])]
        roles.extend(edge(slot,"مفعول به "+str(i),token) for i,(slot,token) in enumerate(zip(slots,args),1))
        refs=["agent",*rules]
        pos=2+len(slots)
        nested=None
        while pos<len(terms):
            if compatible(terms[pos]["surface"],"لِكَيْ"):
                nested=opening(text,terms[pos:])
                if nested:
                    roles.append(edge("purpose","المصدر المؤول في محل جر بلام التعليل",nested["clause"]))
                    refs.append("nominalization")
                    pos=len(terms)
                break
            result=modifier(text,terms,pos,masdar)
            if not result:
                break
            n,add,ref=result
            if any(r["role"]==add[0]["role"] for r in roles):
                break
            roles.extend(add); refs.append(ref); pos+=n
        if pos!=len(terms):
            continue
        scoped=None
        if "embedded_subject" in slots:
            scoped={"bearer":args[-2],"predicate":args[-1],
                    "scope":"CONTENT_OF_BELIEF" if masdar in {"ظنّ","رأي قلبي"} else "CONTENT_OF_REPORT",
                    "independent_property_assertion":False}
        return projection(masdar,"REPORTED_MATRIX_EVENT",len(slots),roles,refs,governor=head,tense="past",
                          embedded_predication=scoped,nominal_clause=nested)
    return None


def special(text,terms,passive_cards):
    # Explicitly bound the five opening profiles, including noun-headed clauses
    # and the dependent purpose fragment where the matrix action is not given.
    if len(terms) in (2,3) and nominal(terms[0],"opened_entity","ُ"):
        bearer=terms[0]
        if len(terms)==2 and marked(terms[1]["surface"],"مَفْتُوحٌ","ٌ"):
            return projection("فتح","STATE_ASCRIBED",None,[edge("property_bearer","مبتدأ",bearer),
                    edge("state","خبر اسم مفعول",terms[1])],["participle"], specific_time=None)
        if len(terms)==3 and marked(terms[1]["surface"],"قَابِلٌ","ٌ") and compatible(terms[2]["surface"],"لِلْفَتْحِ"):
            return projection("فتح","DISPOSITION_ASCRIBED",None,[edge("disposition_bearer","مبتدأ",bearer),
                    edge("disposition","خبر ومتعلّقه",span(text,terms[1:]))],["participle"],realization=None)
    if (len(terms)==4 and nominal(terms[0],"opened_entity","ُ") and marked(terms[1]["surface"],"أَكْبَرُ","ُ")
            and compatible(terms[2]["surface"],"مِنْهُ") and marked(terms[3]["surface"],"حَجْمًا","ً")):
        return projection("كِبَر","COMPARATIVE_PROPERTY",None,
                 [edge("property_bearer","مبتدأ",terms[0]),edge("scale","خبر: اسم تفضيل",terms[1]),
                  edge("comparison_standard","جار ومجرور: مرجع الضمير يحتاج سياقا",terms[2]),
                  edge("property_dimension","تمييز يوضح جهة التفضيل",terms[3])],["specification"])
    if compatible(terms[0]["surface"],"لِكَيْ"):
        inner=opening(text,terms)
        if inner:
            return projection("فتح","GOAL_ONLY",None,[edge("purpose","مصدر مؤول في محل جر باللام",inner["clause"])],
                              ["nominalization"],nominal_clause=inner,matrix_event=None)
    if len(terms)==5 and marked(terms[0]["surface"],"أَرَادَ") and nominal(terms[1],"believer","ُ"):
        inner=opening(text,terms[2:])
        if inner and compatible(terms[2]["surface"],"أَنْ"):
            return projection("إرادة","REPORTED_DESIRE",1,[edge("desirer","فاعل",terms[1]),
                    edge("desired_content","مفعول به: مصدر مؤول",inner["clause"])],["nominalization","arity"],
                    nominal_clause=inner)
    if len(terms)==4 and terms[0]["surface"] in ("يَسُرُّنِي","يسرّني","يسرني"):
        inner=opening(text,terms[1:])
        if inner and compatible(terms[1]["surface"],"أَنْ"):
            # Only the pronoun Ya is the matrix object. The preceding nun is protective.
            last=terms[0]["codepoint_span"][1]
            pronoun={"surface":text[last-1:last],"utf8_span":[len(text[:last-1].encode()),len(text[:last].encode())]}
            return projection("سرور","SOURCE_AS_SUBJECT",1,[edge("experiencer","ياء المتكلم: مفعول به",pronoun),
                    edge("pleasing_content","فاعل: مصدر مؤول",inner["clause"])],["nominalization","agent"],
                    nominal_clause=inner)
    for item in passive_cards:
        ev=item["evidence"]
        if ev["event_family"]=="فتح":
            return projection("فتح",ev["relation"],1,[edge("opened_entity","نائب فاعل",terms[-1])],
                    ["arity"],passive_owner=ev, specific_agent=None, surface_direct_object_count=0,
                    conditional_cue=ev["operator_reading_conditional"],governor=terms[-2])
    return None


def analyze(text, source_id="input", *, retained_passives=None):
    terms=exact_terms(text)
    if not 1<=len(terms)<=24:
        return None
    if text[:terms[0]["codepoint_span"][0]].strip() or text[terms[-1]["codepoint_span"][1]:].strip() not in ("","."):
        return None
    if any(not text[a["codepoint_span"][1]:b["codepoint_span"][0]].isspace()
           for a,b in zip(terms,terms[1:])):
        return None
    row=finite_clause(text,terms)
    if not row:
        if retained_passives is None:
            # Only vowel-compatible passive candidates need the independent discourse replay.
            possible=len(terms) in (2,3) and any(compatible(t["surface"],v) for t in terms[:2]
                     for v in ("فُتِحَ","يُفْتَحْ"))
            retained_passives=passive_relation.analyze(text) if possible else []
        row=special(text,terms,retained_passives)
    if not row:
        return None
    row["role_context"]={"source_claim_only":True,"external_time":None,"external_place":None,
                         "time_expressions":[r["witness"] for r in row["roles"] if r["role"]=="time"],
                         "place_expressions":[r["witness"] for r in row["roles"] if r["role"]=="place"],
                         "instruments":[r["witness"] for r in row["roles"] if r["role"]=="instrument"]}
    row["rule_witnesses"]=pinned_excerpts(json.loads(DATA.read_text()),row["rule_ids"])
    return {"schema":"nabt.scoped-valency.v1","authority":CLAIM_LICENSE,"source_id":source_id,
            "source_sha256":sha256(text.encode()).hexdigest(),"reading":row,"arabic_complete":False}


def evidence_frame(text, record, source_id):
    """Bind ledger claims to this exact occurrence. Native verification is relative to supplied sources."""
    from tools import verified_reading as ground
    row=record["reading"]
    nested=row.get("nominal_clause")
    if nested:
        target = nested["clause"]
        bearer = nested["bearer"]
        meaning = nested["masdar"]
    else:
        target = row.get("governor")
        roles = [r for r in row["roles"] if r["role"] in
                 {"property_bearer","opened_entity","disposition_bearer"}]
        if not roles:
            return {"status":"NO_SINGLE_PROPERTY_BEARER"}
        bearer = roles[0]["witness"]
        target = target or span(text,exact_terms(text))
        meaning = row["masdar"]
    if not ground.valid_name(meaning):
        return {"status":"UNBOUND_SENSE"}
    scope = "valency_context_v1"
    raw = text.encode()
    event = "e_"+str(target["utf8_span"][0])+"_"+str(target["utf8_span"][1])
    bearer_id = "b_"+str(bearer["utf8_span"][0])+"_"+str(bearer["utf8_span"][1])
    # The exact span anchor plus target bytes and source identity must occur IN the ledger.
    # User-declared context is evidence, not verification of the external referent.
    digest=sha256(raw).hexdigest()
    return {"event":event,"bearer":bearer_id,"meaning":meaning,"span":target["utf8_span"],"bearer_span":bearer["utf8_span"],
            "binding":[event,"نص","s_"+digest],"context_source":source_id,
            "source_binding":[event,"هوية_المصدر","id_"+sha256(source_id.encode()).hexdigest()],"scope":scope}


def context_evidence(text, source_id, record, context):
    from tools import explainable_pilot as pilot
    anchor=evidence_frame(text,record,source_id)
    if "event" not in anchor:
        return anchor
    ev,b=anchor["event"],anchor["bearer"]
    raw=context["ledger"].encode()
    scope=anchor["scope"]
    q=("هل "+ev+" حامل "+b+"؟\n").encode()
    result={"status":"DEFER","anchor":anchor,"world_occurrence_established":False,
            "empirical_causality_established":False,"bound":{},"profiles":{}}
    try:
        revision=sha256(raw).hexdigest()
        cert=pilot.propose_certificate(raw,q,source_id,revision,scope)
        receipt,checker=pilot.native(raw,q,cert,source_id,revision,scope,ROOT/"formal/.lake/build/bin/verifiedReading",15)
    except (pilot.PilotError,OSError,ValueError) as exc:
        return {**result,"status":getattr(exc,"code","VERIFICATION_UNAVAILABLE")}
    lines=raw.splitlines(keepends=True)
    atoms={}
    pos=0
    # Use direct source facts. A caller's inference rules may not authorize a missing observation.
    for clause,line in zip(cert["clauses"],lines,strict=True):
        if clause["kind"]=="fact":
            atom=clause["atom"]
            if len(atom["arguments"])==2:
                left,right=atom["arguments"]
                atoms.setdefault((left,atom["predicate"],right),[]).append(
                    {"positive":atom["positive"],"utf8_span":[pos,pos+len(line)],"text":line.decode().rstrip()})
        pos+=len(line)
    def check(triple):
        rows=atoms.get(tuple(triple),[])
        signs={r["positive"] for r in rows}
        verdict={frozenset():"OPEN",frozenset({True}):"SUPPORTED",frozenset({False}):"REFUTED",
                 frozenset({True,False}):"CONFLICT"}[frozenset(signs)]
        return {"status":verdict,"triple":list(triple),"witnesses":rows}
    def bind(name,left,predicate):
        candidates=[check(t) for t in atoms if t[:2]==(left,predicate)] if left else []
        usable=[c for c in candidates if c["status"]=="SUPPORTED"]
        bound=usable[0]["triple"][2] if len(usable)==1 and not any(c["status"]=="CONFLICT" for c in candidates) else None
        result["bound"][name]={"value":bound,"candidates":candidates}
        return bound
    requirements={"source":check(anchor["binding"]),"source_id":check(anchor["source_binding"]),"sense":check((ev,"معنى",anchor["meaning"])),
                  "bearer":check((ev,"حامل",b))}
    base=all(requirements[k]["status"]=="SUPPORTED" for k in ("source","source_id","sense","bearer"))
    kind=bind("kind",b,"عضوية"); prop=bind("property",ev,"محور")
    for slot,rel in (("time","زمان"),("place","مكان"),("instrument","آلة"),("actor","مباشر"),("cause","سبب_مصرح")):
        bind(slot,ev,rel)
    for name,triple in (("kind_accepts_property",(kind,"يقبل",prop)),("sense_property",(anchor["meaning"],"يتعلق",prop)),
                        ("kind_capability",(kind,"قابلية",anchor["meaning"])),("individual_capability",(b,"قابلية",anchor["meaning"])),
                        ("recorded_occurrence",(ev,"وقوع",b))):
        requirements[name]=check(triple)
    for value in result["bound"].values():
        value["value_scope"]="SOURCE_BOUND" if base else "UNBOUND_LEDGER_CANDIDATE"
    ok=lambda k: requirements[k]["status"]=="SUPPORTED"
    capability=base and bool(kind and prop) and all(ok(k) for k in ("kind_accepts_property","sense_property","kind_capability","individual_capability"))
    located=base and all(result["bound"][k]["value"] is not None for k in ("time","place"))
    actual=located and ok("recorded_occurrence")
    result.update(status="CONTEXT_CHECKED",requirements=requirements,native_receipt=receipt,checker_sha256=checker,
                  profiles={"text_binding":base,"capability_witnessed":capability,"located":located,
                            "occurrence_in_ledger":actual,"reported_instrument":base and bool(result["bound"]["instrument"]["value"]),
                            "reported_actor":base and bool(result["bound"]["actor"]["value"]),
                            "reported_causal_link":actual and bool(result["bound"]["cause"]["value"])})
    return result


def describe(record):
    row=record["reading"]
    fields=[r["syntax"]+" «"+r["witness"]["surface"]+"»" for r in row["roles"]]
    if row.get("nominal_clause"):
        inner=row["nominal_clause"]
        fields.append("في المصدر المؤول «"+inner["bearer"]["surface"]+"» نائب فاعل للفعل الداخلي")
    pending={
        "DISPOSITION_ASCRIBED":"نُسبت قابلية الفتح إلى الحامل؛ تحقق الفتح مفتوح",
        "STATE_ASCRIBED":"نُسبت حالة الفتح إلى الحامل؛ لم يعيّن النص من فتحه أو متى",
        "ASSERT_PASSIVE":"أخبر النص بفتح وقع على الحامل وترك المباشر غير مسمّى",
        "DENY_PASSIVE":"الفتح منفي في قراءة الأداة النافية",
        "GOAL_ONLY":"الفتح غاية، ووقوعه مفتوح",
        "REPORTED_DESIRE":"أُسندت الإرادة؛ الفتح مضمونها ووقوعه مفتوح",
        "SOURCE_AS_SUBJECT":"المصدر المؤول هو المسند إليه في الجملة الكبرى",
    }.get(row["force"])
    if pending:
        fields.append(pending)
    if row.get("embedded_predication"):
        fields.append("إسناد الوصف داخل مضمون الظن أو الإعلام؛ ثبوته في الخارج يحتاج شاهدًا")
    return "، ".join(fields)
