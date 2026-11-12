"""Occurrence-scoped dictionary lookup; source selection, interpretation and intent are independent."""
import csv
from functools import lru_cache
from hashlib import sha256
import json
import re
import subprocess
import unicodedata

from nabt.corpus_evidence import lookup_clusters
from tools import lexical_testimony as testimony
from .operations import ROOT, exact_terms
from .root_sense import INDICATIONS, PROFILE

LAW = "nabt.dictionary-reading.v1"
SOURCE = ROOT / "src/nabt/data/source_evidence/mukhtar_sihah.txt"
TABLE = ROOT / "tools/grammar_catalog/data/mukhtar_indications_v1.tsv"
SOURCE_SHA = "e93f4054f3cddb826a7b3fafd01eac8c4b39b25ed2d92ece7ea093b755776691"
MEMBERS_SHA = "8da1eb7203c1597ee3901b73241033aa865c5b42970a2fcbb58d4f8a66870cf2"
SUN = "تثدذرزسشصضطظلن"
QUERY = re.compile(r"ما (معنى|دلالة|أصل مادة) «([^«»\s]{1,40})»(?: على «([^«»\n]{1,180})»)?(?: في «([^«»\n]{1,400})»)?[؟?]?")
# These are written-form alignments to existing source-qualified owners. The
# Maqayis origin entries have a separate query scope.
LEGACY = {"أَسَد":("أسد","جنس"),"عَمَى":("عمي","خاصية"),"قَلَم":("قلم","جنس"),
          "سَمْع":("سمع","حاسة أو عضو"),"بَصَر":("بصر","خاصية"),"فَرَس":("فرس","جنس"),
          "فَهْم":("فهم","مصدر أو اسم"),"سَقْف":("سقف","جنس"),"إِنْسَان":("إنسان","جنس")}
PROFILE_FORMS = ("رَجُل","مِفْتَاح","عَقْرَب","دَحْرَجَة","مُدَحْرِج","مُدَحْرَج","أَسْرَعَ","جَرْبَزَ")
ORIGINS = {"بيت","سيف","سقف","كتب","فهم"}
ROLES = {"back":{"عظم":"جنس","ذو فقار":"خاصية","بالظهر":"قيد موضعي"},
         "pillow":{"وسادة":"جنس","صغيرة":"صفة"},"sour":{"طعم":"جنس الخاصية"},
         "sweet":{"الماء":"جنس","الطيب":"صفة"},"case":{"وعاء":"جنس","الأقلام":"متعلّق"},
         "eye":{"حاسة":"جنس","الرؤية":"وظيفة"}}


def letters(s):
    return "".join(c for c in s if not unicodedata.category(c).startswith("M"))


def forms(lemma):
    if lemma in ("أَسْرَعَ","جَرْبَزَ"):
        return (lemma,)
    head = lemma[0]
    article = "اَلْ"+lemma if head not in SUN else "اَل"+head+"ّ"+lemma[1:]
    return (lemma,article)


def compatible(written, lemma):
    """Original carriers agree and every written mark is licensed by the exemplar."""
    src = lookup_clusters(written)
    if not src:
        return False
    for base in forms(lemma):
        # The article excludes tanwin. Final alif/maqsura have no ordinary overt ending here.
        ends = ("",) if base.endswith(("َ","ا","ى")) else ("","ُ","ِ","َ")
        if base==lemma and len(ends)>1:
            ends += ("ٌ","ٍ","ً" if base.endswith("ة") else "ًا")
        for end in ends:
            exemplar=base+end
            if letters(written)!=letters(exemplar):
                continue
            other=lookup_clusters(exemplar)
            if other and len(src)==len(other) and all(a[1]<=b[1] for a,b in zip(src,other)):
                return True
    return False


def resources():
    raw,tsv=SOURCE.read_bytes(),TABLE.read_bytes()
    if sha256(raw).hexdigest()!=SOURCE_SHA or sha256(tsv).hexdigest()!=MEMBERS_SHA:
        raise ValueError("DICTIONARY_SOURCE_OR_ALIGNMENT_CHANGED")
    return _resources(raw,tsv)


@lru_cache(maxsize=1)
def _resources(raw,tsv):
    records=[]
    for entry in csv.DictReader(tsv.decode().splitlines(),delimiter="\t"):
        h,a,b=(int(entry[k]) for k in ("heading_start","gloss_start","gloss_end"))
        root=entry["root"]
        header=" ".join(root).encode()
        if raw[h-2:h]!=b"# " or raw[h:h+len(header)+1]!=header+b" ":
            raise ValueError("ROOT_HEADING_MISMATCH")
        limit=raw.find(b"\n# ",h)
        if limit<0: limit=len(raw)
        if not h+len(header)<a<b<=limit:
            raise ValueError("GLOSS_OUTSIDE_ENTRY")
        gloss=raw[a:b].decode()
        parts=entry["components"].split("|")
        if " ".join(parts)!=gloss:
            raise ValueError("DEFINITION_ANALYSIS_DIFFERS")
        records.append({"id":entry["id"],"root":root,"lemma":entry["lemma"],"axis":entry["axis"],
                        "components":parts,"gloss":gloss,"gloss_span":[a,b],"entry_span":[h+len(header)+1,limit],
                        "heading_span":[h,h+len(header)]})
    return raw,records


def mukhtar_indices():
    # Lookup indices only; full replay happens after a request has a focus.
    tsv=TABLE.read_bytes()
    if sha256(tsv).hexdigest()!=MEMBERS_SHA:
        raise ValueError("FORM_INDEX_UNAVAILABLE")
    bank=csv.DictReader(tsv.decode().splitlines(),delimiter="\t")
    return {r["lemma"] for r in bank}


def indices_for(word,lemmas,*,clitic=False):
    def exact(w):
        key=letters(w)
        return {l for l in lemmas if any(key.startswith(letters(s)[:2]) for s in forms(l)) and compatible(w,l)}
    found=exact(word)
    if found or not clitic:
        return found
    # A bounded citation alignment for بالـ. The prefix is not assigned any grammatical authority.
    m=re.fullmatch(r"بِ?(ال.+)",word)
    return exact(m[1]) if m else set()


def focus(text):
    m=QUERY.fullmatch(text)
    if m:
        mode,word,target,context=m.groups()
        if (mode=="دلالة")!=(target is not None) or (mode=="أصل مادة" and context):
            return {"status":"INVALID_QUERY"}
        return {"mode":mode,"word":word,"target":target,"context":context,
                "citation_span":[len(text[:i].encode()) for i in m.span(2)],
                "context_offset":len(text[:m.start(4)].encode()) if context else None}
    ts=exact_terms(text)
    if len(ts)==1 and ts[0]["surface"]==text and len(text.encode())<=100:
        return {"mode":"معنى","word":text,"context":None,"target":None,"citation_span":ts[0]["utf8_span"],"context_offset":None}
    return None


def targets(target,components):
    if target is None: return []
    if target==" ".join(components): return components.copy()
    return [s.strip() for s in target.split("+")] if "+" in target else [target]


def mukhtar_reading(row,target):
    components=row["components"]
    chosen=targets(target,components)
    citation={"work":"مختار الصحاح","path":str(SOURCE.relative_to(ROOT)),"source_sha256":SOURCE_SHA,
              "heading_span":row["heading_span"],"gloss_span":row["gloss_span"],"quotation":row["gloss"]}
    out={"sense_id":"mukhtar:"+row["id"],"root":row["root"],"lemma":row["lemma"],"lexical_axis":row["axis"],
         "gloss":row["gloss"],"components":components,"component_roles":ROLES.get(row["id"],{}),
         "citation":citation,"target":chosen,"indications":[],"alignment":"AUTHORED_SOURCE_BOUND_READING"}
    if target is not None:
        req={"id":out["sense_id"],"root":row["root"],"quotation":row["gloss"],"source_sha256":SOURCE_SHA,
             "components":components,"target":chosen,"start_byte":row["gloss_span"][0],"end_byte":row["gloss_span"][1]}
        ans=testimony._native(PROFILE,{"op":"dictionary_components","value":req})
        expected={"id":req["id"],"root":req["root"],"components":components,"citation":{
            "work":"mukhtar","revision":"written-v1","source_sha256":SOURCE_SHA,"start_byte":req["start_byte"],
            "end_byte":req["end_byte"],"quotation":req["quotation"]}}
        kinds=testimony._indications({"id":req["id"],"components":components},chosen,[])
        if (ans.get("sense")!=expected or ans.get("target")!=chosen or ans.get("indications")!=kinds
                or ans.get("authority")!="CONDITIONAL_COMPONENT_CALCULUS_ONLY"):
            raise ValueError("COMPONENT_CHECKER_DISAGREEMENT")
        out.update(indications=kinds,native_checked=True)
    return out


def legacy_readings(root,axis,target,origin):
    # The target can name an entire contiguous gloss as well as explicit components.
    raw=(ROOT/testimony.CATALOG).read_bytes()
    if sha256(raw).hexdigest()!=testimony.CATALOG_SHA:
        raise ValueError("LEXICAL_CATALOGUE_CHANGED")
    rows=[s for s in json.loads(raw)["senses"] if s["root"]==root and
          (s["citation"]["work"]=="maqayis")==origin]
    results=[]
    checked={}
    for s in rows:
        chosen=targets(target,s["components"])
        key=tuple(chosen)
        if key not in checked:
            a=testimony.assess(root,chosen)
            if not a["native_checked"]:
                raise ValueError("TESTIMONY_"+a["status"])
            checked[key]=a["rows"]
        row=next(x for x in checked[key] if x["sense_id"]==s["id"])
        source=row["testimony"]
        results.append({"sense_id":s["id"],"root":None if root=="إنسان" else root,"entry_index":root,
                        "lexical_axis":axis,"gloss":" ".join(row["components"]),"components":row["components"],
                        "citation":source,"indications":[k for k,v in row["indications"].items() if v],"target":chosen,
                        "necessity_records":row["commitment_conditions"],"native_checked":True,
                        "alignment":row["interpretation_status"]})
    return results


def profile_readings(lemmas,word,target,required_root=None):
    if not lemmas.intersection(PROFILE_FORMS): return []
    def export(t):
        d=testimony._native(PROFILE,{"op":"root_sense_profile","value":t})
        if d.get("schema")!="nabt.root-sense.profile.v1" or d["target"]!=t:
            raise ValueError("ROOT_PROFILE_UNAVAILABLE")
        return {r["sense"]["id"]:r for r in d["rows"]}
    available=export([])
    reports={():available}
    output=[]
    for sid,r in available.items():
        if r["surface"] not in lemmas or not sid.startswith("root-profile:") or not compatible(word,r["surface"]):continue
        s=r["sense"]
        if required_root is not None and s["root"]!=required_root:continue
        chosen=targets(target,s["components"])
        key=tuple(chosen)
        if key not in reports: reports[key]=export(chosen)
        c=reports[key][sid]
        if c["sense"]!=s: raise ValueError("PROFILE_SENSE_CHANGED")
        output.append({"sense_id":sid,"root":s["root"],"lemma":r["surface"],"lexical_axis":r["category"],
                       "genus":r["genus"],"property":r["property"],"role":r["role"],"gloss":" ".join(s["components"]),
                       "components":s["components"],"citation":testimony._citation(s["citation"],ROOT),
                       "target":chosen,"indications":c["indications"],"native_checked":True,"alignment":"AUTHORED_TEACHING_PROFILE"})
    return output


def entry_proposal(text, word, root, raw):
    """An exact header and local spelling provide a search window, never an attested derivation."""
    from tools.lexical_training import dictionary_indication as net
    if re.fullmatch(r"[ء-غف-ي]{3,4}",root) is None:
        return None
    heading=("# "+" ".join(root)+" ").encode()
    at=raw.find(b"\n"+heading)
    if at<0: return None
    begin=at+1+len(heading)
    end=raw.find(b"\n# ",begin)
    end=len(raw) if end<0 else end
    word_key=net.stem(word)
    tokens=exact_terms(raw[begin:min(end,begin+8192)].decode(errors="ignore"))[:100]
    if not any(net.stem(t["surface"])==word_key for t in tokens):return None
    row={"lemma":word_key,"id":"unreviewed","root":root,"entry_span":[begin,end]}
    return {"dictionary_source_sha256":SOURCE_SHA,"root_heading_span":[at+3,begin-1],
            "root_index":root,"word":word,"alignment":"SPELLING_IN_ENTRY_ONLY",
            "proposals":net.propose(raw,[row],[],None,None)}


def analyze(text):
    if len(text.encode())>1600:return None
    errors=[]
    explicit=re.fullmatch(r"ما معنى «([^«»\s]{1,40})» من مادة «([ء-غف-ي]{3,4})»[؟?]?",text)
    query=focus(text)
    if explicit:
        query={"mode":"بحث في المادة","word":explicit[1],"root_hint":explicit[2],"target":None,"context":None,
               "citation_span":[len(text[:i].encode()) for i in explicit.span(1)],"context_offset":None}
    try:
        local_forms=set() if query and query.get("mode")=="أصل مادة" else mukhtar_indices()
    except (ValueError,OSError) as err:
        local_forms=set()
        errors.append({"owner":"mukhtar","reason":str(err)})
    lemmas_available=local_forms | set(LEGACY) | set(PROFILE_FORMS)
    if query is None:
        # A metalinguistic quotation or an unresolved multi-focus source needs explicit focus.
        ts=exact_terms(text)
        if not 2<=len(ts)<=12 or any(c in text for c in '«»"\n'):return None
        found=[(t,indices_for(t["surface"],lemmas_available)) for t in ts]
        found=[(t,hits) for t,hits in found if hits]
        if len(found)!=1:return None
        t,_=found[0]
        query={"mode":"لفظ في السياق","word":t["surface"],"target":None,"context":text,
               "citation_span":t["utf8_span"],"context_offset":0}
    report={"schema":LAW,"query":query,"source_sha256":sha256(text.encode()).hexdigest(),"readings":[],
            "verification_debts":errors,"intended_sense_established":False,"world_truth_established":False,
            "customary_use_established":False,"all_arabic_senses_enumerated":False}
    if "status" in query:return {**report,"status":query["status"]}
    word,target=query["word"],query["target"]
    if target is not None and any(not x.strip() for x in target.split("+")):
        return {**report,"status":"INVALID_QUERY"}
    origin=query["mode"]=="أصل مادة"
    lemmas=indices_for(word,lemmas_available) if not origin else set()
    context=query["context"]
    if context and lemmas:
        aligned=[t for t in exact_terms(context) if indices_for(t["surface"],lemmas,clitic=True)]
        if len(aligned)!=1:
            return {**report,"status":"CONTEXT_OCCURRENCE_UNRESOLVED","context_candidates":aligned}
        token=aligned[0]
        lemmas &= indices_for(token["surface"],lemmas,clitic=True)
        report["context_occurrence"]={"surface":token["surface"],"utf8_span":[i+query["context_offset"] for i in token["utf8_span"]]}
    selected=[]
    raw=b""
    readings=report["readings"]
    failures=(OSError,ValueError,KeyError,StopIteration,subprocess.SubprocessError)
    try:
        needs_entry=not origin and (explicit or lemmas.intersection(local_forms) or not lemmas)
        raw,bank=resources() if needs_entry else (b"",[])
        selected=[r for r in bank if r["lemma"] in lemmas and (not explicit or r["root"]==explicit[2])]
        for row in selected:
            try:
                readings.append(mukhtar_reading(row,target))
            except failures as err:
                errors.append({"owner":"mukhtar","reading":row["id"],"reason":str(err)})
                retained=mukhtar_reading(row,None)
                retained.update(target=targets(target,row["components"]),indication_status="VERIFICATION_UNAVAILABLE")
                readings.append(retained)
        if not selected and not origin and (explicit or (not lemmas and query["mode"]=="معنى")):
            index=query.get("root_hint",letters(word).removeprefix("ال"))
            if context:
                local=[t for t in exact_terms(context) if t["surface"]==word]
                if len(local)!=1:
                    return {**report,"status":"CONTEXT_OCCURRENCE_UNRESOLVED","context_candidates":local}
                report["context_occurrence"]={"surface":word,"utf8_span":[i+query["context_offset"] for i in local[0]["utf8_span"]]}
            candidate=entry_proposal(text,word,index,raw)
            if candidate:
                report["entry"]=candidate
    except failures as err:
        errors.append({"owner":"mukhtar","reason":str(err)})
    roots=[(word,"أصل المادة عند ابن فارس")] if origin and word in ORIGINS else [
        LEGACY[l] for l in sorted(lemmas.intersection(LEGACY))]
    for root,axis in roots:
        if explicit and (root!=explicit[2] or root=="إنسان"):continue
        try:readings.extend(legacy_readings(root,axis,target,origin))
        except failures as err:errors.append({"owner":"lexical_testimony","index":root,"reason":str(err)})
    try:readings.extend(profile_readings(lemmas,word,target,explicit[2] if explicit else None))
    except failures as err:errors.append({"owner":"root_sense_profile","reason":str(err)})
    from tools.lexical_training import dictionary_indication as net
    report["proposals"]=net.propose(raw,selected,readings,context,target)
    if readings:status="PARTIAL_VERIFICATION" if errors else "SOURCE_BOUND_READINGS"
    elif errors:status="VERIFICATION_UNAVAILABLE"
    elif "entry" in report:status="UNREVIEWED_ENTRY_PROPOSAL"
    else:status="NO_SCOPED_LEXICAL_ENTRY"
    return {**report,"status":status}


def cards_for(text):
    from .text_reading import card
    r=analyze(text)
    if not r:return [],None
    cards=[]
    kinds={"mutabaqa":"مطابقة","tadammun":"تضمّن","iltizam":"التزام"}
    for i,reading in enumerate(r["readings"]):
        citation=reading["citation"]
        title=citation.get("work") or citation["work_title"]
        quote=citation.get("quotation") or citation["citation"]["quotation"]
        outcome="، ".join(kinds[k] for k in reading["indications"])
        gloss=reading["gloss"]
        surface=r["query"]["word"]
        statement=f"«{surface}» في {title}، في هذا الوجه: «{gloss}»."
        why=f"الشاهد «{quote}»."
        if reading["root"]:why+=f" المادة «{reading['root']}»."
        ranking=r.get("proposals",{}).get("context",{})
        if ranking.get("top")==reading["sense_id"]:
            why+=" رجّح نموذج السياق هذا الوجه بين القراءات المدرّبة من مختار الصحاح."
        if r["query"]["target"] is not None:
            if reading.get("indication_status")=="VERIFICATION_UNAVAILABLE":
                statement+=" تعذّر فحص الدلالة على الهدف."
            elif outcome:
                statement+=f" يدل على «{r['query']['target']}» بدلالة {outcome} في هذا التفسير."
            else:statement+=" لم يثبت وجه دلالة على الهدف في هذا السجل."
            if "iltizam" in reading["indications"]:
                rule=next(n for n in reading["necessity_records"] if n["target"] in reading["target"])
                why+=" شاهد اللزوم المستقل: «"+rule["source"]["citation"]["quotation"]+"»."
        cards.append(card("dictionary_sense","قراءة معجمية مشروطة",statement,why,
                          "يبقى تعيين مراد المتكلم واستعمال الجماعة والوقوع الخارجي مفتوحًا.",
                          reading_ref=f"/dictionary_reading/readings/{i}",sense_id=reading["sense_id"]))
    if r.get("entry"):
        e=r["entry"]; prop=e["proposals"]; spans=prop.get("extractive",[])
        if spans and spans[0]["top_spans"]:
            g=spans[0]["top_spans"][0]["text"]
            cards.append(card("dictionary_candidate","اقتراح عصبي","يقترح النموذج المقطع «"+g+"».",
                              "وُجد الرسم في مادة "+e["root_index"]+" من مختار الصحاح.",
                              "يحتاج حدّ التعريف وتعلقه بهذا اللفظ إلى مراجعة.",entry_ref="/dictionary_reading/entry"))
    if r["status"] in {"VERIFICATION_UNAVAILABLE","PARTIAL_VERIFICATION"}:
        cards.append(card("technical","تعذّر التحقق","تعذّر فحص بعض الشواهد المعجمية.","ترد أسباب الإخفاق في سجل القراءة.",
                          "تؤجل الأحكام التابعة للشاهد المتعذر.",debt_ref="/dictionary_reading/verification_debts"))
    if not cards and r["status"]=="CONTEXT_OCCURRENCE_UNRESOLVED":
        cards.append(card("dictionary_pending","إرجاء","تعذّر تعيين وقوع واحد للفظ في السياق المطلوب.",
                          "فُحصت حدود اللفظ في نص السياق.","يلزم سياق يتعيّن فيه موضع اللفظ."))
    return cards,r
