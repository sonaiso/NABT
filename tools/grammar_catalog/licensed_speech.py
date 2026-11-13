"""Source-bound speech, relations and lexical senses over the installed graded proof graph."""
import re

import json

from nabt.errors import NabtError
from nabt.text_morphology import read_text_morphology
from tools.lexical_training import speech_force
from . import awamil_occurrence, classical_roles, dictionary_reading, lexical_ontolex, passive_relation, valency
from .graded_questions import Chain, LING
from .operations import exact_terms
from .source_evidence_view import pinned_excerpts

LABEL_AR = {"assert":"خبر", "ask":"استفهام", "request":"طلب فعل", "prohibit":"نهي", "vocative":"نداء",
            "wish":"تمنٍّ", "hope":"ترجٍّ", "praise":"مدح", "blame":"ذم", "dependent":"غاية تابعة", "oath":"قسم"}
ACT = {"wish":"wish", "hope":"hope", "vocative":"vocative", "command":"request", "request":"request",
       "prohibit":"prohibit", "praise":"praise", "blame":"blame", "ask_quantity":"ask", "oath":"oath",
       "passive_participle":"ask"}
EMBEDDED = {"embedded", "embedded_belief", "embedded_claim", "embedded_knowledge", "purpose",
            "desired_content", "pleasing_content", "embedded_subject", "embedded_predicate"}
RESTRICTIONS = {"time", "place", "instrument", "companion", "origin", "goal", "measure", "property_dimension",
                "comparison_standard", "stated_motive", "event_emphasis", "time_origin", "purpose", "dependent"}


def validate(option):
    if type(option) is not dict or set(option) - {"lexical", "withdraw", "graph_learning"}:
        raise ValueError("Expected optional dictionary question and withdrawal IDs")
    if "graph_learning" in option and option["graph_learning"] is not True:
        raise ValueError("Expected explicit graph learning switch")
    if "lexical" in option:
        lexical_ontolex.validate(option["lexical"])
    keys = option.get("withdraw", [])
    if (type(keys) is not list or len(keys) > 24 or any(type(k) is not str or not 0 < len(k) <= 190 for k in keys)
            or len(set(keys)) != len(keys)):
        raise ValueError("Invalid withdrawal set")


def under_question(text):
    """A complete retained هل plus an independently readable matrix proposition."""
    m = re.fullmatch(r"(هَلْ|هَلِ|هل)[ \t]+([^؟?\n.]+?)[ \t]*[؟?]?", text)
    if not m or (m[1] == "هَلِ" and not m[2].startswith("ال")):
        return None
    start = len(text[:m.start(2)].encode())
    return m[2], start, [0, len(m[1].encode())]


def surviving_nodes(nodes, removed):
    """Replay the original signed owner graph under a withdrawal of licensed evidence."""
    live=set()
    for node in nodes:
        key=node["id"]
        if (node["status"]=="LICENSED" and key not in removed
                and any(all(p in live for p in path) for path in node["satisfied_paths"])):
            live.add(key)
    return live


class SpeechGraph(Chain):
    def __init__(self, text, source_id):
        super().__init__(text, source_id)
        self.text = text
        self.raw = text.encode()
        self.report.update(schema="nabt.licensed-speech.v1", decoded=[], intended_sense_established=False,
                           empirical_causality_established=False, world_truth_established=False)
        self.owners["terms"] = exact_terms(text)
        self.spans = []
        for i, t in enumerate(self.owners["terms"]):
            self.spans.append(t["utf8_span"])
            self.node(f"sign/{i}", "sign", t["surface"], ["terms", i], (), "sign", t["utf8_span"])

    def node(self, key, role, value, ref, parents, view, pos=None, *, status="LICENSED", scope="source", missing=None, paths=None):
        question = {"sign":"ما اللفظ المشاهد؟", "force":"ماذا فعل المتكلم بالنسبة؟",
                    "indication":"بأي وجه يدل اللفظ؟", "word_kind":"ما قسم الكلمة في هذا الوجه؟"}.get(role, "ما شاهد هذه النسبة؟")
        self.add(key, LING if view != "ledger" else "reported_observation", role, question,
                 status, value, ref, parents=parents, paths=paths, missing=missing)
        node = self.nodes[key]
        position = {"source_id":self.report["source_id"], "source_sha256":self.report["source_sha256"],
                    "utf8_span":pos} if pos is not None else {"owner_path":ref}
        node["transition"] = {"carrier":list(dict.fromkeys(p for path in node["prerequisite_paths"] for p in path)) or [ref[0]], "state":{"role":role,"status":status,"value":value}, "position":position,
                              "view":view, "scope":scope}
        return key

    def terms_at(self, span):
        a, b = span
        if not 0 <= a < b <= len(self.raw):
            raise ValueError("Unbound span in parent source")
        return [f"sign/{i}" for i,(x,y) in enumerate(self.spans) if x < b and a < y]

    def bound_span(self, w, offset=0):
        a,b = w["utf8_span"]
        span = [a+offset,b+offset]
        if self.raw[slice(*span)] != w["surface"].encode():
            raise ValueError("Owner witness is detached from the parent source")
        return span

    def reading(self, name, record, force, relation, roles, *, offset=0, cue=None, scope_span=None):
        """Role witnesses stay in the hypothesized content whether asserted, requested or asked."""
        self.owners[name] = record
        extent = scope_span or [0, len(self.raw)]
        base = self.node(name+"/content", "content", relation, [name], self.terms_at(extent), "joint", extent,
                         scope="represented_content")
        deps = [base]
        if cue:
            deps.extend(self.terms_at(cue))
        if name=="valency" and "operator" in record:
            deps.append(self.node(name+"/operator","speech_particle",record["operator"]["surface"],[name,"operator"],
                                  self.terms_at(cue),"joint",cue,scope="interrogative_particle"))
        fid = self.node(name+"/force", "force", force, [name], list(dict.fromkeys(deps)), "joint", cue or extent,
                        scope="speech_act")
        projected = []
        for i,(role, witness, ref, family, local_scope) in enumerate(roles):
            pos = self.bound_span(witness, offset)
            key = self.node(f"{name}/role/{i}", role, witness["surface"], [name]+ref,
                            [base, *self.terms_at(pos)], "joint", pos, scope=local_scope)
            if role == "verb_governor" or (name=="classical" and role=="verb"):
                self.node(key+"/kind","word_kind",["verb"],[name]+ref,[key],"joint",pos,scope="governor_in_this_reading")
            projected.append({"node":key, "relation":family, "role":role, "surface":witness["surface"],
                              "utf8_span":pos, "scope":local_scope})
        self.report["decoded"].append({"owner":name,"content":relation,"force":force,"force_ar":LABEL_AR[force],
                "force_node":fid,"roles":projected,"matrix_assertion":force=="assert",
                "world_truth_established":False})

    def surviving_after(self, removed):
        return surviving_nodes(self.report["nodes"],removed)

    def decisive_signs(self):
        # Exercise the proof graph rather than labelling the first token as decisive.
        for reading in self.report["decoded"]:
            force_id = reading["force_node"]
            content_id = reading["owner"] + "/content"
            probes = []
            for i, term in enumerate(self.owners["terms"]):
                wid = f"sign/{i}"
                live = self.surviving_after({wid})
                if force_id not in live:
                    probes.append({"witness":wid,"surface":term["surface"],"utf8_span":term["utf8_span"],
                                   "content_survives":content_id in live})
            reading["decisive_written_witnesses"] = probes

    def revise(self, requested):
        unknown = sorted(set(requested)-self.nodes.keys())
        removed = set(requested)
        before = {key for key,n in self.nodes.items() if n["status"]=="LICENSED"}
        surviving = self.surviving_after(removed)
        self.report["revision"] = {"status":"UNBOUND_WITHDRAWAL" if unknown else "REPLAYED_DEPENDENCIES",
            "requested":requested,"unbound":unknown,"lost":None if unknown else sorted(before-surviving),
            "surviving":None if unknown else sorted(surviving),
            "scope":"DEPENDENCIES_OF_THIS_RETAINED_READING"}


def valency_reading(g, frame, wrapper):
    r = frame["reading"]
    offset = wrapper[1] if wrapper else 0
    extent = [offset, offset+len(wrapper[0].encode())] if wrapper else None
    cue = wrapper[2] if wrapper else None
    record = {"frame":frame}
    if wrapper:
        record["operator"] = {"surface":g.raw[slice(*cue)].decode(), "utf8_span":cue,
                              "witness":pinned_excerpts(classical_roles.inventory(), ["question"])}
    force = "ask" if wrapper else "dependent" if r["force"]=="GOAL_ONLY" else "assert"
    roles = []
    for i, item in enumerate(r["roles"]):
        role = item["role"]
        family = "embedding" if role in EMBEDDED else "restriction" if role in RESTRICTIONS else "predication_argument"
        scope = "embedded" if role in ("embedded_subject","embedded_predicate") else item["scope"]
        # Grammatical subject of a subordinate passive is retained inside the nominalization.
        roles.append((role,item["witness"],["frame","reading","roles",i],family,scope))
    if r.get("governor"):
        roles.append(("verb_governor",r["governor"],["frame","reading","governor"],"governor","matrix"))
    if r.get("nominal_clause"):
        nested = r["nominal_clause"]
        roles.append(("passive_subject",nested["bearer"],["frame","reading","nominal_clause","bearer"],
                      "predication_argument","embedded"))
    g.reading("valency", record, force, r["force"], roles, offset=offset, cue=cue, scope_span=extent)


def opening_directive(g):
    """A finite second-person reading sharing the same patient and modifier owner as past فتح."""
    from nabt.productive_forms import replay_policy
    terms = g.owners["terms"]
    if not 2 <= len(terms) <= 12:
        return
    negative = terms[0]["surface"] == "لَا"
    i = int(negative)
    if len(terms) < i+2 or terms[i]["surface"] not in (
            ("تَفْتَحْ","تَفْتَحِ") if negative else ("اِفْتَحْ","اِفْتَحِ","افْتَحْ","افْتَحِ")):
        return
    if (g.text[:terms[0]["codepoint_span"][0]].strip() or g.text[terms[-1]["codepoint_span"][1]:].strip() not in ("",".","!")
            or any(not g.text[a["codepoint_span"][1]:b["codepoint_span"][0]].isspace() for a,b in zip(terms,terms[1:]))):
        return
    if not valency.nominal(terms[i+1],"opened_entity","َ"):
        return
    items = [valency.edge("verb_governor","فعل مخاطب",terms[i]),valency.edge("opened_entity","مفعول به",terms[i+1])]
    pos = i+2
    rule_ids = ["arity"]
    while pos < len(terms):
        bound = valency.modifier(g.text,terms,pos,"فتح")
        if not bound:
            return
        size, roles, rule = bound
        if any(role["role"] in {r["role"] for r in items} for role in roles):
            return
        items.extend(roles)
        rule_ids.append(rule)
        pos += size
    witnesses = pinned_excerpts(json.loads(valency.DATA.read_text()), sorted(set(rule_ids)))
    if negative:
        bank,_ = awamil_occurrence.curriculum()
        witnesses.update(pinned_excerpts(bank, ["jussive"]))
    else:
        policy = replay_policy()
        witnesses["imperative"] = next(p for p in policy["passages"] if p["source_id"]=="qatr" and "الطلب" in p["raw_text"])
    witnesses.update(pinned_excerpts(passive_relation._inventory(),["open"]))
    record = {"witnesses":witnesses,"roles":items,"addressed_profile":"second_person_masculine_singular",
              "specific_addressee":None,"masdar":"فتح","direct_object_arity":1,
              "force_basis":"AUTHORED_MARKED_SECOND_PERSON_FACE","world_occurrence_established":False}
    roles = [(r["role"],r["witness"],["roles",j],"governor" if r["role"]=="verb_governor" else
             "predication_argument" if r["role"]=="opened_entity" else "restriction","directed_content")
             for j,r in enumerate(items)]
    g.reading("directive",record,"prohibit" if negative else "request","فتح",roles,cue=terms[0]["utf8_span"])


def factor_readings(g, retained):
    if retained is None:
        rows, status = awamil_occurrence.read(g.text, passive_relation.analyze(g.text))
    else:
        rows, status = retained["readings"], retained["status"]
    g.report["factor_status"] = status
    for i,r in enumerate(rows):
        rel = r["relation"]
        force = ACT.get(rel, "assert")
        # A conditional is reported as a conditional relation. Neither operand is a standalone fact.
        roles = []
        for role,w in r["bindings"].items():
            family = ("governor" if role in ("cue","g") else "embedding" if rel in EMBEDDED or role in EMBEDDED
                      else "restriction" if role in RESTRICTIONS or role in ("condition","consequence")
                      else "predication_argument")
            scope = "embedded" if rel in EMBEDDED and role not in ("cue","g") else (
                    "conditional" if role in ("condition","consequence") else "governed_content")
            roles.append((role,w,["bindings",role],family,scope))
        g.reading(f"factor/{i}",r,force,rel,roles)


def lexical_reading(g, query):
    owner = lexical_ontolex.assess(query)
    g.owners["dictionary"] = owner
    terms = g.owners["terms"]
    word = terms[0]["surface"] if len(terms)==1 and terms[0]["surface"]==g.text else None
    matched = dictionary_reading.indices_for(word, dictionary_reading.LEGACY) if word else set()
    form_roots = sorted({dictionary_reading.LEGACY[lemma][0] for lemma in matched})
    for i,row in enumerate(owner["rows"] if owner["native_checked"] else []):
        ref = ["dictionary","rows",i]
        sense = g.node(f"sense/{i}", "sense", row["sense_id"], ref, (), "concept", scope="dictionary_sense")
        conditions = [g.node(f"sense/{i}/condition/{j}", "necessity_premise", c["target"],
                              ref+["commitment_conditions",j], [sense], "concept",scope="retained_necessity_premise")
                      for j,c in enumerate(row["commitment_conditions"])]
        for mode, value in row["indications"].items():
            if value:
                g.node(f"sense/{i}/{mode}", "indication", mode, ref, [sense] + (conditions if mode=="iltizam" else []),
                       "concept", scope="conditional_on_sense")
    # Restrict the form join to IDs returned by the independent occurrence dictionary.
    if word and query["entry"] in form_roots:
        analysis = dictionary_reading.analyze(word)
        g.owners["form_dictionary"] = analysis
        positions = {r["sense_id"]:j for j,r in enumerate(analysis.get("readings",[])) if r.get("native_checked")}
        for i,row in enumerate(owner["rows"] if owner["native_checked"] else []):
            sid = row["sense_id"]
            if sid not in positions:
                continue
            key = g.node(f"form/{i}", "candidate_sense", sid, ["form_dictionary","readings",positions[sid]],
                         ["sign/0",f"sense/{i}"], "joint", g.spans[0], scope="admissible_lexical_face")
            for mode, value in row["indications"].items():
                if value:
                    g.node(f"form/{i}/{mode}", "conditional_indication", mode, ["dictionary","rows",i],
                           [key,f"sense/{i}/{mode}"], "joint", g.spans[0], scope="conditional_on_sense")
    g.report["lexical_status"] = owner["status"]


def ledger_reading(g, ledger):
    g.owners["ledger"] = ledger
    if ledger.get("status") != "CONTEXT_CHECKED":
        return
    requirements = ledger["requirements"]
    def attach(key, value, ref, parents=(), *, ok=True, missing=None):
        return g.node("ledger/"+key, key, value, ["ledger"]+ref, parents, "ledger",
                      status="LICENSED" if ok else "OPEN", scope="supplied_ledger", missing=missing)
    for k,r in requirements.items():
        g.node("evidence/"+k, "ledger_premise", r["status"], ["ledger","requirements",k], (), "ledger",
               status={"SUPPORTED":"LICENSED","REFUTED":"REFUTED"}.get(r["status"],r["status"]),scope="supplied_ledger")
    profiles = ledger["profiles"]
    anchor = ledger["anchor"]
    binding = attach("binding",anchor["event"],["anchor"],["valency/content", *["evidence/"+k for k in
                  ("source","source_id","bearer","sense")]],ok=profiles["text_binding"])
    for key,b in ledger["bound"].items():
        attach(key,b["value"],["bound",key],[binding],ok=profiles["text_binding"] and b["value"] is not None)
    attach("capability", anchor["meaning"],["profiles","capability_witnessed"],
           ["ledger/kind","ledger/property",*["evidence/"+k for k in ("kind_accepts_property","sense_property",
            "kind_capability","individual_capability")]],ok=profiles["capability_witnessed"])
    attach("located",anchor["event"],["profiles","located"],["ledger/time","ledger/place"],ok=profiles["located"])
    event = attach("recorded_event",anchor["event"],["profiles","occurrence_in_ledger"],
                   ["ledger/located","evidence/recorded_occurrence"],ok=profiles["occurrence_in_ledger"])
    attach("cause_to_effect",{"cause":ledger["bound"]["cause"]["value"],"effect_event":anchor["event"]},
           ["profiles","reported_causal_link"],[event,"ledger/cause"],ok=profiles["reported_causal_link"])


def project(text, source_id, option, relatives, lexical_text=None):
    validate(option)
    g = SpeechGraph(text,source_id)
    from tools.lexical_training.cognitive_graph import sign_nodes
    g.owners["sign_cells"] = sign_nodes(text, source_id)
    for i, row in enumerate(g.owners["sign_cells"]):
        if row["a116"]["status"]=="REPRESENTED":
            g.node(f"cells/{i}", "a116", row["a116"]["cells"], ["sign_cells",i,"a116"], [f"sign/{i}"],
                   "sign", g.spans[i], scope="cell_representation")
    try:
        morph = read_text_morphology(text,source_id=source_id,scope="speech_graph",lexical_text=lexical_text)
        g.owners["word_kinds"] = [{"surface":o["surface"],"span":o["span"],"kind":o["axes"]["kind"],
                        "readings":[{"id":r["reading_id"],"kind":r["axes"]["kind"],"receipts":r["receipts"]}
                                    for r in o["readings"]]} for o in morph["occurrences"]]
        for i,o in enumerate(g.owners["word_kinds"]):
            pos = [o["span"]["start"],o["span"]["end"]]
            g.node(f"kind/{i}", "word_kind", o["kind"]["candidates"], ["word_kinds",i], g.terms_at(pos),
                   "joint", pos,status=o["kind"]["status"],missing=o["kind"]["missing"])
    except NabtError as exc:
        g.owners["word_kind_failure"] = exc.as_dict()
    g.report["neural"] = speech_force.propose(text)
    wrapper = under_question(text)
    frame = relatives.get("valency")
    if wrapper:
        proposal = valency.analyze(wrapper[0],source_id)
        if proposal and proposal["reading"]["force"]!="GOAL_ONLY":
            valency_reading(g,proposal,wrapper)
    elif frame:
        valency_reading(g,frame,None)
    classical = relatives["classical"] if "classical" in relatives else classical_roles.analyze(text)
    if classical:
        r = classical["reading"]
        roles = [(k,r[k]["term"],["reading",k],"predication_argument","governed_content") for k in ("subject","object")]
        roles.append(("verb",r["verb"],["reading","verb"],"governor","matrix"))
        g.reading("classical",classical,r["force"],r["sense"],roles,cue=r["cue"]["utf8_span"] if r["cue"] else None)
    opening_directive(g)
    factor_readings(g, relatives.get("factors"))
    if not g.report["decoded"]:
        from .partial_speech import extend
        extend(g)
    if "lexical" in option:
        lexical_reading(g, option["lexical"])
    if "definition_network" in relatives:
        d = relatives["definition_network"]
        g.owners["definition_network"] = d
        for i,r in enumerate(d["readings"]):
            if r["ground_check"]["receipt"]["verified"]:
                parent = g.node(f"definition/{i}","sense",r["focus"],["definition_network","readings",i,"focus"],
                                g.terms_at(d["occurrence_span"]), "joint",d["occurrence_span"],scope="query_assumption")
                evidence = {}
                for wid, witness in r["witnesses"].items():
                    if witness["status"]=="REPLAYED":
                        evidence[wid] = g.node(f"definition/{i}/witness/{wid}", "definition_witness", witness["quote"],
                                              ["definition_network","readings",i,"witnesses",wid], [], "concept",
                                              scope="dictionary_citation")
                for j,c in enumerate(r["claims"]):
                    paths = [[parent]+[evidence[r["edges"][e]["witness"]] for e in proof] for proof in c["proofs"]]
                    g.node(f"definition/{i}/{j}",c["relation"],c["node"],["definition_network","readings",i,"claims",j],
                           [],"concept",scope="conditional_definition",paths=paths)
    if "valency_context" in relatives:
        ledger_reading(g,relatives["valency_context"])
    proposal = g.report["neural"].get("top")
    # Rank only complete retained readings and keep every alternative.
    g.report["recall_order"] = [r["force_node"] for r in sorted(g.report["decoded"],key=lambda r:r["force"]!=proposal)]
    g.report["force_status"] = "SOURCE_BOUND" if g.report["decoded"] else "OPEN"
    if option.get("graph_learning"):
        from tools.lexical_training.graph_interventions import propose
        g.report["graph_learning"] = propose(g.report["nodes"],option.get("withdraw",[]))
    g.decisive_signs()
    g.revise(option.get("withdraw",[]))
    return g.report
