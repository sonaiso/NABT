"""Source-bound, finite teaching readings over the deposited Jurjani inventory."""
import csv
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
import re

from nabt.inflection import EXPECTED_TABLE_SHA256, sign_candidates
from tools.mantuq_mafhum import load_awamil_inventory
from . import passive_relation
from .operations import ROOT
from .source_evidence_view import pinned_excerpts

LAW = "nabt.awamil-occurrence.v1"
DATA = ROOT / "tools/grammar_catalog/data"
SOURCES = (("awamil_occurrences_v1.tsv", "dc383881e3a886870ea81941a3ecb780238df8ae7e0494d14e86c736d74a2395"),
           ("awamil_occurrence_bank_v1.json", "87d1809de2a639b384af1d33d80fcf977599c139fbe256ef4173568d1ad775e7"))
FIELDS = re.compile(r"\{([a-z_]+)=([^{}]+)\}")
GROUP_WITNESS = ("jarr", "inna", "negative_predicate", "vocative", "subjunctive", "jussive",
                 "conditional", "measure", "verb_name", "kana", "near", "praise", "mental")
SPECIAL = {**dict.fromkeys((15,16,17), "exception_jarr"), 26:"with", 27:"except", 37:"conditional",
           92:"governed", 93:"active_participle", 94:"passive_participle", 95:"attribute",
           96:"source", 97:"possession", 98:"measure", 99:"predication", 100:"indicative"}
AR = dict(actor="الفاعل في هذا الوجه", patient="المتعلّق به الفعل", subject="المسند إليه أو المعمول الأول",
          predicate="المحمول أو الفعل", condition="فعل الشرط", consequence="الجواب", place="المكان",
          time="الزمن", recipient="المنتفع", goal="الغاية", origin="المبدأ", topic="الموضوع",
          standard="المشبَّه به", instrument="الآلة", measure="التمييز", excluded="المستثنى",
          companion="المصاحَب", addressee="المنادى", designated="المخصوص", oath="المقسم به",
          possessor="المضاف إليه", dependent="المعمول", participant="المجرور", purpose="الغاية المقصودة",
          first="الطرف الأول", second="الطرف الثاني", holder="حامل الصفة", cue="أداة النفي", g="العامل الملفوظ")


@dataclass(frozen=True)
class Pattern:
    factor: int
    relation: str
    gloss: str
    template: str
    sense: str = ""
    voice: str = ""
    polarity: str = ""


def event_patterns(bank):
    for sense, forms in bank["event_forms"].items():
        for i, form in enumerate(forms):
            negative, passive = i >= 2, i % 2 == 1
            polarity = "deny" if negative else "assert"
            voice = "passive" if passive else "active"
            parts = ["{cue=لَمْ}"] if negative else []
            parts.append("{g=" + form + "}")
            if not passive:
                parts.append("{actor=$person_u}")
            parts.append("{patient=$" + sense + ("_u}" if passive else "_a}"))
            orders = [parts]
            if not passive:
                orders.append(parts[:-2] + [parts[-1], parts[-2]])
            for order in orders:
                yield Pattern(38 if negative else 92, "event_" + voice + "_" + polarity,
                              "نفي الحدث" if negative else "إخبار بالحدث", " ".join(order), sense, voice, polarity)


@lru_cache(maxsize=1)
def _compile(tsv, raw):
    bank = json.loads(raw)
    patterns = [Pattern(int(r["factor"]), r["relation"], r["reading"], r["pattern"])
                for r in csv.DictReader(tsv.decode().splitlines(), delimiter="\t")]
    if [p.factor for p in patterns] != list(range(1,101)):
        raise ValueError("Incomplete occurrence curriculum")
    for sense, stems in bank["event_patient_stems"].items():
        for suffix,mark in (("_a","َ"),("_u","ُ")):
            bank["slots"][sense+suffix] = [s+mark for s in stems]
    patterns.extend(event_patterns(bank))
    compiled = []
    for p in patterns:
        chunks, end = [], 0
        for m in FIELDS.finditer(p.template):
            role, expression = m.groups()
            if role not in AR:
                raise ValueError("Unknown role: " + role)
            choices = bank["slots"][expression[1:]] if expression.startswith("$") else [expression]
            chunks.extend((re.escape(p.template[end:m.start()]), "(?P<"+role+">"+"|".join(map(re.escape, choices))+")"))
            end = m.end()
        chunks.append(re.escape(p.template[end:]))
        compiled.append((p,re.compile("".join(chunks))))
    return bank, tuple(compiled)


def curriculum():
    data = []
    for name, expected in SOURCES:
        raw = (DATA/name).read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise ValueError("Occurrence curriculum identity differs: " + name)
        data.append(raw)
    return _compile(*data)


def primary_span(p, bindings):
    """Principal governed participant for scoring; the full graph keeps every role."""
    if p.sense:
        return bindings["patient"]["utf8_span"]
    return next(v["utf8_span"] for k,v in bindings.items() if k != "g")


def bound_fields(text, match):
    bindings = {}
    for key,surface in match.groupdict().items():
        a,b = match.span(key)
        bindings[key] = {"surface":surface, "utf8_span":[len(text[:a].encode()),len(text[:b].encode())]}
    return bindings


def case_signs(p, bindings):
    """The paradigm supplies a class premise; the actual mark has its own span."""
    results = []
    endings = {"u":(1,"ٌُ"), "a":(0,"ًَ"), "i":(2,"ٍِ"), "j":(3,"ْ")}
    for match in FIELDS.finditer(p.template):
        role,val = match.groups()
        if val == "$cond" or (p.sense and p.polarity == "deny" and role == "g"):
            suffix,cls = "j",8
        elif val.startswith("$") and val[-2:-1]=="_" and val[-1] in endings:
            suffix = val[-1]
            cls = 8 if val.startswith(("$first_","$third_")) else 0
        else:
            continue
        case,marks = endings[suffix]
        bound = bindings[role]
        word = bound["surface"].split()[0]
        pos = len(word)-1
        if word.endswith("ًا"):
            pos -= 1
        if word[pos] not in marks:
            raise ValueError("Case witness disagrees with the authored slot")
        begin = bound["utf8_span"][0] + len(word[:pos].encode())
        rows = sign_candidates([cls], cases=[case])
        if len(rows)!=1:
            raise ValueError("Expected one conditional sign in this paradigm")
        results.append({"role":role,"observed":word[pos],"utf8_span":[begin,begin+len(word[pos].encode())],
                        "conditional_sign":rows[0],"class_premise":"AUTHORED_PARADIGM",
                        "sign_table_sha256":EXPECTED_TABLE_SHA256})
    return results


def edges(factors,bindings,p):
    # Each occurrence is identified in the parent source. An implicit governor
    # has a rule identity but no invented span in the written input.
    result=[]
    frame=f"frame:{p.relation}"
    for f in factors:
        result.append({"from":f["id"],"to":frame,"type":"licenses_teaching_frame",
                       "operator_span":f["occurrence"]["utf8_span"] if f["occurrence"] else None})
    if p.sense and p.polarity=="deny":
        result.append({"from":"jurjani:038","to":"jurjani:092","type":"negates_event_in_text",
                       "depends_on":["cue","g"]})
    for role,occ in bindings.items():
        if role in ("g","cue"):
            continue
        result.append({"from":frame,"to":occ["utf8_span"],"type":role,"depends_on":[role],
                       "interpretation_scope":"within_authored_face"})
    return result


def read(text, passive_cards=()):
    """Full source match before source claims. Weights cannot select or delete a reading."""
    if len(text.encode()) > 1024:
        return [], "OUTSIDE_BUDGET"
    bank, patterns = curriculum()
    matched = [(p,m) for p,regex in patterns if (m:=regex.fullmatch(text))]
    if not matched:
        return [], "OUTSIDE_AUTHORED_PATTERNS"
    inv = load_awamil_inventory()
    source = sha256(text.encode()).hexdigest()
    results = []
    for p,m in matched:
        bindings = bound_fields(text,m)
        factors = [38,92] if p.sense and p.polarity == "deny" else [p.factor]
        anchors = []
        keys = set()
        for fid in factors:
            row = inv["rows"][fid-1]
            keys.add(SPECIAL[fid] if fid in SPECIAL else GROUP_WITNESS[row["group"]-1])
            anchor = bindings.get("cue" if fid == 38 and p.sense else "g")
            anchors.append({"id":f"jurjani:{fid:03}", "label":row["name"], "scan_page":row["page"],
                            "inventory_row":fid, "occurrence":anchor, "family":row["family"]})
        witnesses = pinned_excerpts(bank,sorted(keys))
        event = None
        if p.sense:
            lexicon = passive_relation._inventory()
            family = next(f for f in lexicon["families"] if f["sense_witness"] == p.sense)
            lexical_witness = pinned_excerpts(lexicon,[p.sense])[p.sense]
            if p.voice == "passive":
                eligible = [c["evidence"] for c in passive_cards if c.get("scope") == "source_event_relation"]
                eligible = [e for e in eligible if e["source_sha256"] == source and e["patient_span"] == bindings["patient"]["utf8_span"]
                            and e["verb_span"] == bindings["g"]["utf8_span"] and e["cue_span"] == (bindings.get("cue") or {}).get("utf8_span")
                            and e["event_sense_id"] == passive_relation.SCHEMA+":"+p.sense
                            and e["relation"] == ("DENY_PASSIVE" if p.polarity=="deny" else "ASSERT_PASSIVE")]
                if not eligible:
                    continue
            event = {"sense":p.sense, "masdar":family["masdar"], "voice":p.voice, "polarity":p.polarity,
                     "patient":bindings["patient"], "patient_key":passive_relation.lookup_key(bindings["patient"]["surface"]),
                     "actor":bindings.get("actor"), "lexical_witness":lexical_witness,
                     "patient_syntax":"passive_subject" if p.voice == "passive" else "direct_object",
                     "cause_established":False}
        results.append({"factor":p.factor, "factors":anchors,"relation":p.relation,"reading_ar":p.gloss,
                        "source_sha256":source,"bindings":bindings,"principal_span":primary_span(p,bindings),
                        "witnesses":witnesses,"event":event,"template":p.template,"inventory_sha256":inv["inventory_sha256"],
                        "rule_version":LAW,"signs":case_signs(p,bindings), "edges":edges(anchors,bindings,p), "rule_inputs":dict(SOURCES),
                        "premise":"AUTHORED_FULL_PATTERN_AND_LEXICAL_FACE",
                        "customary_use_established":False,"world_truth_established":False})
    return results, "MATCHED_AUTHORED_READING" if results else "OWNER_OBLIGATION_OPEN"
