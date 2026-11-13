"""Source-bound reading of Q2:282 over a measured Hokom projection and NABT's graph head."""
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json

from .ayat_import import DATA, HOKOM, VENDOR
from . import ayat_cognition
from .licensed_speech import SpeechGraph, surviving_nodes
from tools.lexical_training import graph_interventions

SOURCE_ID = "quran:2:282:user-orthography"
SOURCE_SHA = "ab7f79ca76a47f5595ecda2cf167b9d07706af62059d9db67166c9424ad3aa1e"
OBS_SHA = "e73035d723db9f0d08d90f1074f32337133af0ef40188cc8b4e1de51f05f8337"
QAC = "https://corpus.quran.com/wordmorphology.jsp?location=(2:282:{})"
# Reviewed occurrence readings, separate from all measurements made by Hokom.
# Each coordinate is explicit: the corpus joins يا/أيها in its first word.
REVIEWS = {
    2:(1,"ISM","VOCATIVE_NOUN_WITH_ATTENTION_PARTICLE",None,None),
    4:(3,"FI3L","PERFECT_IV","آمَنَ","ءمن"),
    5:(4,"ISM","TIME_CONDITION",None,None),
    6:(5,"FI3L","PERFECT_VI_2MP","تَدَايَنَ","دين"),
    23:(22,"ISM","PROPER_NAME_NOM",None,None),
    25:(24,"FI3L","JUSSIVE_IV_DICTATION","أَمَلَّ","ملل"),
    27:(26,"HARF","PREPOSITION_WITH_PRONOUN",None,None),
    29:(28,"FI3L","JUSSIVE_VIII","اتَّقَى","وقي"),
    30:(29,"ISM","PROPER_NAME_ACC",None,None),
    31:(30,"ISM","NOUN_ACC_POSSESSIVE","رَبّ","ربب"),
    39:(38,"HARF","PREPOSITION_WITH_PRONOUN",None,None),
    46:(45,"FI3L","IMPERFECT_X","اسْتَطَاعَ","طوع"),
    50:(49,"FI3L","JUSSIVE_IV_DICTATION","أَمَلَّ","ملل"),
    76:(75,"ISM","TIME_CONDITION",None,None),
    78:(77,"FI3L","PERFECT_PASSIVE_3MP","دَعَا","دعو"),
    91:(90,"ISM","PROPER_NAME_GEN",None,None),
    95:(94,"HARF","SUBORDINATOR_PLUS_NEGATION",None,None),
    97:(96,"HARF","EXCEPTION",None,None),
    105:(104,"HARF","PREPOSITION_WITH_PRONOUN",None,None),
    107:(106,"HARF","SUBORDINATOR_PLUS_NEGATION",None,None),
    110:(109,"ISM","TIME_CONDITION",None,None),
    123:(122,"ISM","PROPER_NAME_ACC",None,None),
    125:(124,"ISM","PROPER_NAME_NOM",None,None),
    126:(125,"ISM","CONJUNCTION_PLUS_PROPER_NAME",None,None),
}
# Authored clause boundaries and role bindings for this verse. Captures are original
# one-based verse coordinates. Templates are decoded only after all spans and guards bind.
# guards name a source surface (#), an actual post-segmentation host (@), or an independent reading (%).
@dataclass(frozen=True)
class Frame:
    key: str
    first: int
    last: int
    force: str
    guards: tuple
    roles: dict
    template: str
    debt: str = ""


FRAMES = (
    Frame("address",1,4,"نداء",("#1=يَا","%2=VOCATIVE_NOUN_WITH_ATTENTION_PARTICLE","%4=PERFECT_IV"),
          {"group":(3,4)}, "يتوجه النداء إلى «{group}»."),
    Frame("debt",5,11,"طلب مشروط",("%5=TIME_CONDITION","%6=PERFECT_VI_2MP","@7=دَيْنٍ","#11=فَاكْتُبُوهُ"),
          {"event":(6,7),"term":(8,10),"action":(11,11)}, "يربط النص طلب الكتابة «{action}» بالتداين «{event}» المحدّد بـ«{term}»."),
    Frame("scribe",12,15,"طلب",("@12=يَكْتُبْ","#14=كَاتِبٌ"),{"agent":(14,14),"between":(13,13),"manner":(15,15)},
          "يسند الكتابة إلى «{agent}» ويقيّدها بـ«{between}» و«{manner}»."),
    Frame("no_refusal",16,24,"نهي وطلب",("@16=لَا","#17=يَأْبَ","%23=PROPER_NAME_NOM","@24=يَكْتُبْ"),
          {"agent":(18,18),"infinitive":(19,20),"instruction":(21,24)}, "يتعلق النهي بإباء «{agent}» عن «{infinitive}»، ويتبعه «{instruction}»."),
    Frame("dictation",25,28,"طلب",("%25=JUSSIVE_IV_DICTATION","%27=PREPOSITION_WITH_PRONOUN"),{"agent":(26,28),"verb":(25,25)},
          "يسند «{verb}» الإملال إلى «{agent}»."),
    Frame("no_reduction",29,35,"طلب ونهي",("%29=JUSSIVE_VIII","%31=NOUN_ACC_POSSESSIVE","@32=لَا"),
          {"piety":(29,31),"ban":(32,35)},"يجمع الخطاب بين «{piety}» والنهي «{ban}»."),
    Frame("guardian",36,52,"شرط وبديل",("@36=إِنْ","#42=أَوْ","#44=أَوْ","%46=IMPERFECT_X","%50=JUSSIVE_IV_DICTATION"),
          {"bearer":(38,40),"first":(41,41),"second":(43,43),"third":(45,49),"agent":(51,51),"manner":(52,52)},
          "إذا تحقق في «{bearer}» أحد الأوصاف «{first}» أو «{second}» أو «{third}»، يسند الجواب الإملال إلى «{agent}» ويقيّده بـ«{manner}»."),
    Frame("witnesses",53,72,"طلب واستبدال مشروط",("#53=وَاسْتَشْهِدُوا","@57=إِنْ","#58=لَمْ","#61=فَرَجُلٌ"),
          {"first":(54,56),"condition":(57,60),"alternative":(61,66),"explanation":(67,72)},
          "يطلب الاستشهاد بـ«{first}». ويذكر عند «{condition}» البديل «{alternative}»، ثم يورد «{explanation}»."),
    Frame("summons",73,78,"نهي مقيّد",("@73=لَا","%76=TIME_CONDITION","%78=PERFECT_PASSIVE_3MP"),
          {"agent":(75,75),"condition":(76,78)},"يتعلق النهي عن الإباء بـ«{agent}» عند «{condition}». الداعي غير مسمّى."),
    Frame("record_size",79,87,"نهي",("@79=لَا","#82=تَكْتُبُوهُ"),{"writing":(81,82),"size":(83,85),"term":(86,87)},
          "يتعلق النهي عن السآمة بـ«{writing}» في الحالين «{size}» ويمتد القيد إلى «{term}»."),
    Frame("reasons",88,96,"خبر وتعليل",("#89=أَقْسَطُ","#92=وَأَقْوَمُ","%95=SUBORDINATOR_PLUS_NEGATION"),
          {"justice":(89,91),"witness":(92,93),"doubt":(94,96)},"يذكر النص ثلاث جهات «{justice}»، و«{witness}»، و«{doubt}»."),
    Frame("trade",97,108,"استثناء",("%97=EXCEPTION","#100=تِجَارَةً","#104=فَلَيْسَ","%107=SUBORDINATOR_PLUS_NEGATION"),
          {"scope":(100,103),"consequence":(104,108)},"يخصّ «{scope}» بقوله «{consequence}». يتعلّق الضمير في «تكتبوها» بالتجارة."),
    Frame("sale",109,111,"طلب مقيّد",("#109=وَأَشْهِدُوا","%110=TIME_CONDITION"),{"action":(109,109),"condition":(110,111)},
          "يعود طلب الإشهاد «{action}» عند «{condition}»."),
    Frame("harm",112,116,"نهي",("@112=لَا","#113=يُضَارَّ"),{"first":(114,114),"second":(116,116)},
          "يرد النهي عن المضارّة في صلة «{first}» و«{second}».","جهة الضرر من الكاتب والشهيد أو عليهما مؤجّلة في هذا التحليل."),
    Frame("consequence",117,121,"شرط وجواب",("@117=إِنْ","#119=فَإِنَّهُ","#121=بِكُمْ"),{"condition":(117,118),"result":(119,121)},
          "يربط النص «{condition}» بجوابه «{result}»."),
    Frame("close",122,129,"طلب وخبر",("#122=وَاتَّقُوا","%123=PROPER_NAME_ACC","%125=PROPER_NAME_NOM","%126=CONJUNCTION_PLUS_PROPER_NAME"),
          {"order":(122,123),"teaching":(124,125),"knowledge":(126,129)},
          "يتعاقب طلب «{order}»، وخبر «{teaching}»، وخبر «{knowledge}».","التعاقب والواو وحدهما لا يعيّنان علاقة سببية."),
)


def source():
    raw=(DATA/"source.txt").read_bytes()
    if sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError("Ayat source identity changed")
    return raw.decode()


@lru_cache(maxsize=1)
def observations(raw):
    if sha256(raw).hexdigest()!=OBS_SHA:
        raise ValueError("Hokom observation identity changed")
    obj=json.loads(raw)
    if (obj["commit"],obj["vendor"],obj["source_sha256"])!=(HOKOM,VENDOR,SOURCE_SHA):
        raise ValueError("Different Hokom producer or text")
    return obj


def validate(p):
    if type(p["text"]) is not str or len(p["text"].encode())>8192:
        raise ValueError("Expected bounded verse text")
    if "scene" in p:
        ayat_cognition.validate_scene(p["scene"])
    context=p.get("withdraw_context",[])
    if (type(context) is not list or len(context)>len(ayat_cognition.CONTEXT)
            or any(type(k) is not str or k not in ayat_cognition.CONTEXT for k in context)
            or len(context)!=len(set(context))):
        raise ValueError("Expected unique installed context premise identifiers")
    if "question" in p and (type(p["question"]) is not str or not p["question"].strip() or len(p["question"].encode())>256):
        raise ValueError("Expected a nonblank question of at most 256 bytes")
    cuts=p.get("withdraw",[])
    if (type(cuts) is not list or len(cuts)>129 or any(type(i) is not int or not 1<=i<=129 for i in cuts)
            or len(cuts)!=len(set(cuts))):
        raise ValueError("Withdrawal requires unique one-based integer positions")


def route_word(r):
    i=r["position"]
    seg=r["segment"]
    directive=r["routing_slots"]["PATH_DIRECTIVE_SLOT"]
    review=REVIEWS.get(i)
    reading=None
    if review:
        qac,wordclass,tag,lemma,root=review
        reading={"class":wordclass,"tag":tag,"lemma":lemma,"root":root,"source":QAC.format(qac),
                 "authority":"REVIEWED_OCCURRENCE","class_relation":(
                     "DEFERRED_UPSTREAM" if r["class"] is None else "AGREES" if r["class"]==wordclass else "CONFLICT")}
    blocked=seg["clitic_only"] or not seg["host_surface"] or directive[0]=="BLOCKED"
    closed=blocked or (reading["class"] if reading else r["class"])=="HARF" or r["layers"]["RADICAL"]=="NOT_OPENED"
    status="BLOCKED_NO_LEXICAL_HOST" if blocked else "CLOSED" if closed else "OPEN"
    root_agrees=not reading or not reading["root"] or r["root"]==reading["root"]
    emitted=(root_agrees and status=="OPEN" and r["layers"]["RADICAL"]=="LICENSED" and r["root_state"]=="KNOWN"
             and all("RADICAL_R"+str(n) in r["licensed"] for n in (1,2,3)))
    return {"position":i,"surface":r["surface"],"source_segment":seg,"upstream_class":r["class"],
            "upstream_root_state":r["root_state"],"upstream_root":r["root"],"upstream_weight_display":r["weight_display"],
            "layers":r["layers"],"licensed_claims":r["licensed"],"deferred_claims":r["deferred"],
            "review":reading,"root_route":status,"root_input":seg["host_surface"] if status=="OPEN" else None,
            "root_review_status":"CONFLICT" if not root_agrees and r["root"] else "NO_RECORDED_CONFLICT",
            "reported_root_claim":r["root"] if emitted else None,"live_upstream_in_recording":r["gate_executed"]}


def analyze(text,withdraw=(),withdraw_context=(),question=None,scene=None):
    fields={"text":text,"withdraw":list(withdraw),"withdraw_context":list(withdraw_context)}
    if question is not None:
        fields["question"]=question
    if scene is not None:
        fields["scene"]=scene
    validate(fields)
    expected=source()
    if text!=expected:
        return {"status":"SOURCE_MISMATCH","expected_sha256":SOURCE_SHA,"received_sha256":sha256(text.encode()).hexdigest(),
                "cards":[],"world_truth_established":False}
    obj=observations((DATA/"hokom.json").read_bytes())
    g=SpeechGraph(text,SOURCE_ID)
    terms=g.owners["terms"]
    if len(terms)!=len(obj["rows"]):
        raise ValueError("Token count mismatch")
    words=[]
    for i,(t,r) in enumerate(zip(terms,obj["rows"],strict=True),1):
        if r["position"]!=i or t["surface"]!=r["surface"]:
            raise ValueError("Misaligned token replay")
        words.append({**route_word(r),"utf8_span":t["utf8_span"]})
    cards=[]
    g.owners["routing"]=words
    g.owners["frames"]={}
    for frame in FRAMES:
        def span(a,b):
            lo,hi=terms[a-1]["utf8_span"][0],terms[b-1]["utf8_span"][1]
            return {"positions":[a,b],"utf8_span":[lo,hi],"surface":g.raw[lo:hi].decode()}
        guards=[]
        for guard in frame.guards:
            marker,rest=guard[0],guard[1:]
            loc,value=rest.split("=",1)
            word=words[int(loc)-1]
            observed={"#":word["surface"],"@":word["source_segment"]["host_surface"],
                      "%":(word["review"] or {}).get("tag")}[marker]
            guards.append({"position":int(loc),"field":{"#":"surface","@":"segment_host","%":"reviewed_tag"}[marker],
                           "expected":value,"matched":observed==value})
        roles={k:span(a,b) for k,(a,b) in frame.roles.items()}
        # A card recounts the entire reviewed clause. Withdrawing any of its written
        # premises suspends that full reading. Raw roles can still be inspected.
        deps=range(frame.first,frame.last+1)
        evidence={"guards":guards,"roles":roles,"clause":span(frame.first,frame.last)}
        g.owners["frames"][frame.key]=evidence
        status="LICENSED" if all(v["matched"] for v in guards) else "OPEN"
        key=g.node("clause/"+frame.key,"force",frame.force,["frames",frame.key],
                   ["sign/"+str(i-1) for i in sorted(deps)],"joint",evidence["clause"]["utf8_span"],
                   status=status,scope="authored_verse_reading")
        cards.append({"id":key,"force":frame.force,"roles":roles,"scope":evidence["clause"],"guards":guards,
                      "supports":sorted(deps),"debt":frame.debt,"bound":status=="LICENSED",
                      "text":frame.template.format(**{k:v["surface"] for k,v in roles.items()})})
    claims=ayat_cognition.build(g,words,SOURCE_SHA)
    removed=["sign/"+str(i-1) for i in withdraw]+["ctx/"+k for k in withdraw_context]
    neural=graph_interventions.propose(g.report["nodes"],removed)
    live=surviving_nodes(g.report["nodes"],set(removed))
    ranks={n["id"]:n for n in neural.get("rows",[])}
    for c in cards:
        active=c["id"] in live
        c["status"]="SUPPORTED_TEXT_READING" if active else "WITHDRAWN" if c["bound"] else "DEFERRED"
        c["explanation_ar"]=c.pop("text") if active else None
        c["withdrawn_supports"]=sorted(set(c["supports"]).intersection(withdraw))
        candidates=ranks.get(c["id"],{}).get("candidate_edges",[])
        c["neural_top_witnesses"]=[{"position":int(e["from"][5:])+1,"score":e["score"],
            "in_checked_support":int(e["from"][5:])+1 in c["supports"]} for e in candidates if e["from"].startswith("sign/")]
        c["predicted_loss"]=ranks.get(c["id"],{}).get("loss_score")
        focus=next((w for w in c["neural_top_witnesses"] if active and w["in_checked_support"]
                    and w["position"] not in withdraw),None)
        c["focus_witness"]=None if focus is None else {
            **focus,"surface":words[focus["position"]-1]["surface"],"utf8_span":words[focus["position"]-1]["utf8_span"]}
        c["answer_ar"]=c["explanation_ar"]
        if c["focus_witness"]:
            c["answer_ar"] += " ومن شواهد هذه القراءة «"+c["focus_witness"]["surface"]+"»."
    return {"schema":"nabt.ayat-al-dayn.v1","status":"SOURCE_BOUND","source":{"id":SOURCE_ID,"sha256":SOURCE_SHA,"text":text},
            "upstream":{"commit":HOKOM,"vendor":VENDOR,"mode":"PINNED_REPLAY_OF_MEASURED_EXPORT","projection_sha256":OBS_SHA},
            "counts":{"positions":len(words),"gate_executed":sum(r["gate_executed"] for r in obj["rows"]),
                      "root_states":dict(Counter(w["upstream_root_state"] for w in words)),
                      "clauses":len(cards),"active":sum(c["status"]=="SUPPORTED_TEXT_READING" for c in cards)},
            "tokens":words,"cards":cards,"withdraw":list(withdraw),"withdraw_context":list(withdraw_context),
            "cognition":ayat_cognition.decode(claims,g,live,ranks,question),
            "scene_result":ayat_cognition.apply_scene(scene or {},live),
            "neural":{k:v for k,v in neural.items() if k!="rows"},"nodes":g.report["nodes"],
            "semantic_authority":"VERSE_SPECIFIC_REVIEWED_LINGUISTIC_READING","world_truth_established":False,
            "legal_ruling_established":False,"resources_used_in_decision":[]}
