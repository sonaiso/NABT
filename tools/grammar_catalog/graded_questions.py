"""Typed question dependencies over the existing readers. Each citation is resolved on construction."""
import re
from hashlib import sha256

from . import definition_network, interpretation_chains, question_answer_cycle as cycle
from . import question_cognition, question_frames, relational_bridge, usage_witness
from .operations import digest

LAW = "nabt.graded-question-chains.v1"
LING = "linguistic"
PHYS = "natural_observation"
MATH = "mathematical"
CUSTOM = "customary"




class Chain:
    def __init__(self, text, source_id):
        self.owners = {"input": text}
        self.nodes = {}
        self.report = {"law": LAW, "source_id": source_id, "source_sha256": sha256(text.encode()).hexdigest(),
                       "nodes": [], "owners": self.owners, "world_truth_established": False,
                       "community_practice_established": False}

    def add(self, key, domain, role, question, status, value, ref, *, parents=(), paths=None, missing=None, negative_parents=()):
        """OR of AND parent proofs. Only determinate, scope-local answers discharge a parent."""
        routes = [list(parents)] if paths is None else paths
        if key in self.nodes or not routes or any(p not in self.nodes for route in routes for p in route):
            raise ValueError("Duplicate or unresolved question dependency")
        # ref is a typed path into the retained owner payload, never a caller-supplied pointer.
        original = self.owners
        for part in ref:
            original = original[part]
        if not ref:
            raise ValueError("Missing evidence path")
        grade = 1 + max((self.nodes[p]["grade"] for path in routes for p in path), default=-1)
        # Only a signed answer required by the edge discharges the prerequisite.
        admitted = [path for path in routes if all(self.nodes[p]["status"] == ("REFUTED" if p in negative_parents else "LICENSED") for p in path)]
        if status == "LICENSED" and not admitted:
            raise ValueError("Question owner and prerequisite license disagree")
        node = {"id": key, "domain": domain, "role": role, "grade": grade, "question": question,
                "status": status, "value": value, "prerequisite_paths": routes, "requires_refuted": list(negative_parents), "satisfied_paths": admitted,
                "evidence_path": ref, "evidence_sha256": digest(original), "missing": missing or []}
        self.report["nodes"].append(node)
        self.nodes[key] = node
        return key


def event_chain(g, text, source_id, event):
    result = cycle.run(text, source_id)
    g.owners["cycle"] = result
    base = ["cycle", "items", 0, "question_parts", "event"]
    root = g.add("event", LING, "event", "ما الحدث الذي تتعلق به هذه الأسئلة؟", "LICENSED",
                 event["event"]["text"], base + ["event"])
    for role, question in (("agent", "من المسند إليه الفعل؟"), ("patient", "ما المعمول المتعلّق بالفعل؟")):
        g.add(role, LING, role, question, "LICENSED", event[role], base + [role], parents=[root])
    g.add("time", LING, "time", "ما جهة الزمن في صيغة الفعل؟", "LICENSED", "استقبال", base + ["verb"], parents=[root])
    g.add("place", LING, "place", "أين يقع الفعل الموصوف؟", "OPEN", None, base, parents=[root], missing=["شاهد المكان"])
    for i, item in enumerate(result["items"]):
        op = item["operation"]
        decision = item["owner"]["decision"]
        status = {"SUPPORTED": "LICENSED", "REFUTED": "REFUTED"}.get(item["status"], item["status"])
        if op == "joint":
            # One refuted conjunct decides a conjunction, even if the other is open.
            paths = [["instrument", "condition"]]
            if status == "REFUTED":
                paths = [[axis] for axis in ("instrument","condition") if g.nodes[axis]["status"] == "REFUTED"]
        else:
            paths = [[root]]
        g.add(op, PHYS if op == "occurrence" else LING, op, item["question"], status,
              decision["value"], ["cycle", "items", i], paths=paths,
              negative_parents=[p[0] for p in paths] if op == "joint" and status == "REFUTED" else [])
    g.add("cause", PHYS, "cause", "هل عُيّن سبب فيزيائي للفعل؟", "OPEN", None, base,
          parents=["occurrence"], missing=["شاهد الوقوع والجسر السببي"])
    g.add("effect", PHYS, "effect", "ما الأثر الناشئ عن السبب؟", "OPEN", None, base,
          parents=["cause"], missing=["شاهد الأثر واتجاه التأثير"])


def lexical_chain(g, text, source_id):
    result = question_cognition.owner_view("genus", text, source_id)
    g.owners["lexicon"] = result
    status = result["status"]
    for i, r in enumerate(result.get("owner", {}).get("readings", [])):
        ref = ["lexicon", "owner", "readings", i]
        root = g.add("sense/" + r["focus"], LING, "lexical_sense", "بأي وجه نقرأ التعريف؟",
                     "LICENSED", r["focus"], ref + ["focus"])
        prefixes = {(): root}
        answers = sorted(enumerate(r["claims"]), key=lambda item: min(map(len, item[1]["proofs"])))
        # A proof prefix is itself an attested subpath. Separate alternative proofs and senses.
        for j, claim in answers:
            for proof in sorted(claim["proofs"], key=len):
                previous = root
                for k, eid in enumerate(proof, 1):
                    prefix = tuple(proof[:k])
                    if prefix in prefixes:
                        previous = prefixes[prefix]
                        continue
                    edge = r["edges"][eid]
                    key = root + "/path/" + digest(list(prefix))[:24]
                    label = {"is_a":"ما الأصل الأعم؟","has_attribute":"بأي صفة اتصف الجنس؟",
                             "has_property":"ما الخاصية المنسوبة إلى الجنس؟","denotes_property":"أي خاصية تدل عليها الصفة؟"}
                    previous = g.add(key, LING, "definition_edge", label[edge["relation"]], "LICENSED",
                                     edge, ref + ["witnesses", edge["witness"]], parents=[previous])
                    prefixes[prefix] = previous
            g.add(root + "/claim/" + claim["relation"] + "/" + claim["node"], LING, claim["relation"],
                  "ما الذي يرثه هذا الوجه أو يدلّ عليه؟", "LICENSED", claim["node"], ref + ["claims", j],
                  paths=[[prefixes[tuple(p)]] for p in claim["proofs"]])
        g.add(root + "/instance", PHYS, "instance", "هل يثبت التعريف انطباق الصفة على فرد معين؟",
              "OPEN", None, ref + ["focus"], parents=[root], missing=["شاهد هوية الفرد والانطباق"])
    return status


def arithmetic_chain(g, text, source_id):
    report = question_cognition.owner_view("arithmetic", text, source_id)["owner"]
    g.owners["arithmetic"] = report
    if not report["chain_complete"]:
        return report["status"]
    projection = report["projection"]
    trace = iter(enumerate(projection["trace"]))
    raw = text.encode()
    def visit(tree):
        children = [visit(child) for child in tree["children"]]
        i, row = next(trace)
        if (row["span"], row["op"]) != (tree["span"], tree["op"]):
            raise ValueError("Trace order differs from the checked expression")
        a, b = tree["span"]
        expr = raw[a:b].decode()
        return g.add("expr/" + str(i), MATH, "operand" if not children else "operation",
                     f"ما قيمة «{expr}» في هذه الشجرة؟", "LICENSED" if row["status"] == "COMPUTED" else row["status"],
                     row["value"] if row["value"] is not None else row["truth"], ["arithmetic", "projection", "trace", i],
                     parents=children, missing=[row["reason"]] if row["reason"] else [])
    root = visit(projection["tree"])
    g.add("formal_result", MATH, "formal_result", "ما الناتج الذي أجازه فاحص الحساب؟",
          g.nodes[root]["status"], projection["result"], ["arithmetic", "native_check"], parents=[root])
    return report["status"]


def convention_chain(g, text, source_id):
    statuses = []
    for domain in (LING, CUSTOM):
        profile = "linguistic" if domain == LING else "customary"
        owner = usage_witness.run({"text": text, "source_id": source_id, "usage_context": {"profile_id": profile}})
        g.owners[profile] = owner
        statuses.append(owner["status"])
        inner = owner["owner_report"]
        for i, occurrence in enumerate(inner.get("occurrences", [])):
            ref = [profile, "owner_report", "occurrences", i]
            oid = occurrence["occurrence_id"]
            parent = g.add(profile + "/" + oid, LING, "occurrence_binding", "ما موضع اللفظ في النص؟",
                           "LICENSED", occurrence["span"], ref + ["span"])
            by_candidate = {a["owner_result_ref"]: a for a in owner["applications"]}
            for j, candidate in enumerate(occurrence["candidates"]):
                pointer = f"/owner_report/occurrences/{i}/candidates/{j}"
                application = by_candidate.get(pointer)
                key = parent + "/" + str(j)
                native_ok = occurrence["native_checked"] and inner["native_checked"] and inner["acquisition_scan_complete"]
                status = ("LICENSED" if application else "CONFLICT" if occurrence["signed_conflict"]
                          else owner["status"] if owner["status"] not in ("DEFER","SCOPED_SOURCE_USE_APPLICATIONS")
                          else "OPEN" if native_ok else "UNVERIFIED")
                evidence = [profile, "applications", owner["applications"].index(application)] if application else ref + ["candidates", j]
                g.add(key, domain, profile + "_use", f"هل يشهد السياق للوجه «{candidate['sense_id']}» في هذا الاصطلاح؟",
                      status, candidate["sense_id"], evidence, parents=[parent])
                if domain == CUSTOM:
                    g.add(key + "/community", CUSTOM, "community_practice", "هل استقر هذا المعنى عند جماعة معينة؟",
                          "OPEN", None, evidence, parents=[key], missing=["شاهد استعمال الجماعة المحددة لهذا المعنى"])
    failures = [status for status in statuses if status not in ("DEFER","SCOPED_SOURCE_USE_APPLICATIONS","CONFLICT")]
    if failures:
        return "PARTIAL_VERIFICATION" if len(failures) != len(statuses) else failures[0]
    if not any(g.owners[p]["owner_report"].get("occurrences") for p in ("linguistic", "customary")):
        return "DEFER"
    return "CONFLICT" if "CONFLICT" in statuses else "SCOPED_PROFILES"


def observation_chain(g, text):
    owner = interpretation_chains.analyze(text)
    g.owners["record"] = owner
    if owner["status"] not in ("SOURCE_RELATIVE_CHAIN", "PARTIAL_VERIFICATION"):
        return owner["status"]
    subject = owner["subject"]
    root = g.add("subject", PHYS, "identity", "ما الحامل الذي يعيّنه عنوان السجل؟", "LICENSED",
                 subject["entity"], ["record","subject"])
    location = g.add("place", PHYS, "place", "أين سُجّلت الصفة؟", "LICENSED", subject["place"],
                     ["record","subject","place"], parents=[root])
    kind = g.add("declared_kind", PHYS, "declared_genus", "إلى أي جنس ينسب السجل حامله؟", "LICENSED",
                 subject["kind"], ["record","subject","kind"], parents=[root])
    for i, row in enumerate(owner["records"]):
        if row["kind"] != "observation":
            continue
        key = row["id"]
        ref = ["record","records",i]
        day = g.add(key + "/time", PHYS, "time", "متى نُسب الوصف إلى هذا الحامل؟", "LICENSED",
                    row["day"], ref + ["fields","day"], parents=[root])
        g.add(key, PHYS, "observed_property", f"ماذا سجّل الراصد في محور «{row['axis']}»؟",
              "LICENSED", {"axis":row["axis"],"value":row["value"],"unit":row["unit"],"observer":row["origin"]},
              ref, parents=[kind, location, day])
    for i, row in enumerate(owner["conflicts"]):
        g.add("conflict/" + str(i), PHYS, "conflict", "أي قيم تعارضت في الخانة نفسها؟",
              "CONFLICT", row["values"], ["record","conflicts",i], parents=row["dependencies"])
    for i, row in enumerate(owner["changes"]):
        ref = ["record","changes",i]
        prefix = "difference/" + str(i)
        parents = list(row["dependencies"])
        if row.get("arithmetic_check"):
            check = row["arithmetic_check"]
            checked = (check.get("receipt") or {}).get("native_checked") is True and "difference" in row
            parents = [g.add(prefix + "/count", MATH, "count_difference", "ما فرق العدد بوحدة العد نفسها؟",
                             "LICENSED" if checked else "UNVERIFIED", row.get("difference"), ref + ["arithmetic_check"],
                             parents=parents)]
        status = row["status"]
        licensed = status in ("INCREASED","DECREASED","CHANGED","SAME_ENDPOINTS")
        g.add(prefix, PHYS, "change", "كيف تقارن الصفة بين الزمنين المرصودين؟",
                             "LICENSED" if licensed else status, {"comparison":status,"from":row["from_values"],
                             "to":row["to_values"]}, ref, parents=parents)
    g.add("cause", PHYS, "cause", "هل يعيّن السجل سبب التغيّر؟", "OPEN", None, ["record","limits"],
          parents=[root], missing=["شاهد مستقل للصلة السببية وانطباقها"])
    g.add("effect", PHYS, "effect", "هل ثبت إسناد هذا الأثر إلى ذلك السبب؟", "OPEN", None, ["record","limits"],
          parents=["cause"], missing=["ربط الأثر بالسبب في هذه الحالة"])
    return owner["status"]


def named_role(predicate):
    return {"عضوية":"genus_membership","خاصية":"bearer_property","يقبل":"genus_property",
            "حامل":"bearer","حالة":"attribute","مكان":"place","زمان":"time",
            "دليل_سببي":"causal_evidence","شروط":"condition","مانع":"blocker",
            "قابلية":"capability_premise","معنى":"sense","وقوع":"occurrence_premise"}.get(predicate, "ledger_premise")


def bridge_chain(g, text, bridge, retained):
    # Each stage is independently rerun with the same raw ledger, occurrence and scope.
    parent = None
    for stage, question in (("disposition","هل استوفت قابلية الجنس والخاصية شروط هذا الفرد؟"),
                            ("occurrence","هل يشهد السجل بوقوع الحدث هنا وفي هذا الزمن؟"),
                            ("causality","هل يشهد السجل بعلاقة موجهة بين السبب والأثر؟")):
        frame = {**bridge["frame"], "stage":stage}
        owner = (retained if retained is not None and stage == bridge["frame"]["stage"]
                 else relational_bridge.evaluate(text, {**bridge, "frame":frame}))
        g.owners[stage] = owner
        proof = owner["native_receipt"]
        dependencies = [parent] if parent else []
        if proof and proof.get("occurrence_bound") is not True:
            dependencies.append(g.add("binding/" + stage, LING, "binding", "هل تطابق إطار الدليل موضع اللفظ؟",
                                      "OPEN", None, [stage,"native_receipt","occurrence_bound"]))
        if proof:
            for i, req in enumerate(proof["requirements"]):
                ref = [stage,"native_receipt","requirements",i]
                key = "requirement/" + digest([req["predicate"],req["arguments"],req["positive"],req["scope"]])
                if key not in g.nodes:
                    status = ("CONFLICT" if req["opposed"] and req["present"] else "REFUTED" if req["opposed"]
                              else "LICENSED" if req["present"] and req["clean"] else "OPEN")
                    binding = {"نص","موضع","قراءة","معنى"}
                    domain = LING if req["predicate"] in binding else PHYS
                    g.add(key, domain, named_role(req["predicate"]), f"هل يشهد السجل بنسبة «{req['predicate']}» لهذين الطرفين؟",
                          status, {"predicate":req["predicate"],"arguments":req["arguments"],"positive":req["positive"]}, ref)
                dependencies.append(key)
        role = "cause" if stage == "causality" else stage
        parent = g.add("bridge/" + stage, PHYS, role, question,
                       "LICENSED" if owner["licensed"] else owner["status"], owner["ontology_assertions"],
                       [stage], parents=dependencies, missing=owner.get("missing", []))
    g.add("bridge/effect", PHYS, "effect", "إلى أي حدث يُسند أثر السبب في السجل؟",
          "LICENSED" if owner["licensed"] else owner["status"], frame["event"] if owner["licensed"] else None,
          ["causality"], parents=[parent], missing=owner.get("missing", []))
    return owner["status"]


def run(text, source_id="input", *, bridge=None, retained_bridge=None):
    g = Chain(text, source_id)
    key = "source"
    if bridge is not None:
        status = bridge_chain(g, text, relational_bridge.validate(bridge), retained_bridge)
        key = "source_relative_causal_ledger"
    elif text.startswith("سلسلة «"):
        status = observation_chain(g, text)
        key = "recorded_states"
    elif text.startswith("أعني "):
        status = convention_chain(g, text, source_id)
        key = "convention"
    elif definition_network.QUERY.fullmatch(text) or re.fullmatch(r"[ء-يَ-ْ]{1,40}", text):
        status = lexical_chain(g, text, source_id)
        key = "lexical_definition"
    elif cycle.ARITHMETIC.fullmatch(text) and text.strip():
        status = arithmetic_chain(g, text, source_id)
        key = "formal_expression"
    else:
        event, _ = question_frames.clauses(text)
        if event is None:
            status = "OUTSIDE_SOURCE"
        else:
            event_chain(g, text, source_id, event)
            status, key = "ASSESSABLE_EVENT", "described_event"
    g.report["nodes"].sort(key=lambda node: node["grade"])
    g.report["levels"] = [[n["id"] for n in g.report["nodes"] if n["grade"] == rank]
                          for rank in sorted({n["grade"] for n in g.report["nodes"]})]
    return {**g.report, "profile":key, "status":status}


def answer_text(node, evidence):
    role, value = node["role"], node["value"]
    if value is None:
        return "بقي الجواب غير محسوم."
    if role in ("instrument","condition","joint","occurrence") and "answer" in evidence:
        return evidence["answer"]
    if role == "definition_edge":
        a, b = (definition_network.label(value[k]) for k in ("child", "parent"))
        relation = {"is_a": "نوع من", "has_attribute": "يتصف بـ", "has_property": "له خاصية",
                    "denotes_property": "يدل على خاصية"}[value["relation"]]
        return f"{a} {relation} {b}."
    if role == "occurrence_binding":
        return value["raw_text"]
    if role in ("linguistic_use","customary_use"):
        local = [p["sense_span"]["raw_text"] for p in evidence.get("local_premises", [])
                 if p["positive"] and p["sense_id"] == value]
        if local:
            return "القراءة المشهودة «" + "، ".join(dict.fromkeys(local)) + "»."
        return "الوجه قيد الفحص: " + str(value)
    if role == "observed_property":
        return f"سجّل {value['observer']} في محور {value['axis']} القيمة {value['value']} ({value['unit']})."
    if role == "change":
        return "القيم في الرصد الأول «" + "، ".join(map(str,value["from"])) + "»، وفي الثاني «" + "، ".join(map(str,value["to"])) + "»."
    if isinstance(value, dict) and "predicate" in value and "arguments" in value:
        polarity = "" if value["positive"] else "نفي "
        return polarity + value["predicate"] + " (" + "، ".join(value["arguments"]) + ")."
    if role == "formal_result" and value["status"] != "COMPUTED":
        return "تعذّر حساب القيمة ضمن هذا المجال: " + str(value["reason"])
    if role == "formal_result":
        value = value["truth"] if value["sort"] == "proposition" else value["value"]
    if type(value) is bool:
        return "نعم." if value else "لا."
    if isinstance(value,dict) and "numerator" in value:
        return str(value["numerator"]) if str(value["denominator"]) == "1" else f'{value["numerator"]}/{value["denominator"]}'
    if isinstance(value,list):
        if not value:
            return "لا حكم مرخص لهذه المرحلة."
        if isinstance(value[0],dict) and "frame" in value[0]:
            f = value[0]["frame"]
            if role == "cause":
                return f"ينسب السجل السبب «{f['cause']}» إلى الحدث «{f['event']}»."
            return f"الحدث «{f['event']}» وحامله «{f['entity']}» في «{f['place']}» و«{f['time']}»."
        return "، ".join(map(str,value))
    return definition_network.label(value) if isinstance(value,str) and value[:2] in ("G:","P:","A:") else str(value)


def cards(graph):
    from .text_reading import card
    labels = {LING:"لغوي", CUSTOM:"عرفي مشروط", MATH:"رياضي", PHYS:"نسبي إلى الرصد أو السجل"}
    states = {"LICENSED":"مرخّص في نطاقه", "OPEN":"مفتوح", "CONFLICT":"متعارض",
              "REFUTED":"معارَض بشاهد", "DEFER":"مؤجّل", "BLOCKED":"محجوب"}
    if not graph["nodes"]:
        return [card("graded_questions",graph["status"],"تعذّر توليد سلسلة أسئلة مرخّصة لهذا المدخل.",
                     graph["status"],"تُراجع تغطية المصدر والفاحص.")]
    out = []
    positions = {n["id"]:str(i) for i,n in enumerate(graph["nodes"],1)}
    for n in graph["nodes"]:
        evidence = graph["owners"]
        for part in n["evidence_path"]:
            evidence = evidence[part]
        supports = ["، ".join(positions[k] for k in path) for path in n["prerequisite_paths"] if path]
        why = labels[n["domain"]] + " · " + states.get(n["status"],n["status"])
        if supports:
            why += ". يعتمد هذا السؤال على " + " أو ".join(supports) + "."
        if isinstance(evidence,dict) and evidence.get("quote"):
            why += " شاهد التعريف «" + evidence["quote"] + "»."
        gaps = [v if isinstance(v,str) else v["predicate"] for v in n["missing"]]
        out.append(card("graded_questions", positions[n["id"]] + ". " + n["question"], answer_text(n,evidence),
                        why,"، ".join(gaps) or "حدود الحكم محفوظة في شاهد هذه المرحلة.", node=n["id"], grade=n["grade"],
                        prerequisite_paths=n["prerequisite_paths"]))
    return out
