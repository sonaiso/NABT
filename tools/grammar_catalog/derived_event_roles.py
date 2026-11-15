"""Bounded, source-bound transfer of a selected verbal sense to its argument frame."""
from functools import lru_cache
from hashlib import sha256
from itertools import permutations
import json

from nabt.corpus_evidence import lookup_clusters, lookup_key, template_matches
from nabt.derivation import generate_derivation
from . import event_scene, literal_event_roles as roles
from .operations import ROOT, exact_terms

DATA = ROOT / "tools/grammar_catalog/data/derived_event_roles_v1.json"
CATALOG_QUERY = "شبكة المصادر والأوزان"
NAMES = {"II": "فَعَّلَ", "IV": "أَفْعَلَ", "VII": "اِنْفَعَلَ",
         "VIII": "اِفْتَعَلَ", "IX": "اِفْعَلَّ", "X": "اِسْتَفْعَلَ"}
MASDAR = {"II": "taf3il", "IV": "if3al", "VII": "infi3al", "VIII": "ifti3al", "X": "istif3al"}
CHANGES = {"VII", "VIII", "IX"}
AR_STATUS = {"LICENSED": "مرخّص", "BLOCKED": "ممتنع في القراءة المحددة",
             "UNRESOLVED": "معلّق", "CONFLICT": "تعارض الشواهد", "DEFERRED_SENSE": "مرجأ لغياب شاهد المعنى"}
CASE = {"agent": "ُ", "causer": "ُ", "bearer": "ُ", "patient": "َ",
        "first_object": "َ", "second_object": "َ"}
APPLY = {"COMPATIBLE": "LICENSED", "INCOMPATIBLE": "BLOCKED", "DEFER": "UNRESOLVED", "CONFLICT": "CONFLICT"}
PREPS = {"مِنْ": "من", "مِنَ": "من", "إِلَى": "إلى", "عَلَى": "على", "فِي": "في"}


GATES = {"II": ("intensify", "التكثير في التجزئة المادية"),
         "VII": ("result", "مطاوعة العلاج"), "VIII": ("result", "مطاوعة العلاج"),
         "IX": ("colour_change", "التغيّر اللوني"), "X": ("extraction", "قراءة الاستخراج أو الطلب في الدرس")}
BOOKS = ("mukhtar_sihah", "ibn_aqil", "sibawayhi")


@lru_cache(maxsize=6)
def book_lines(path, identity):
    if identity is None:
        return None, ()
    raw = path.read_bytes()
    return sha256(raw).hexdigest(), raw.decode().splitlines()


def sources():
    books = {}
    for name in BOOKS:
        path = ROOT / "src/nabt/data/source_evidence" / (name + ".txt")
        try:
            st = path.stat()
            books[name] = book_lines(path, (st.st_dev, st.st_ino, st.st_ctime_ns, st.st_size))
        except OSError:
            books[name] = (None, ())
    return books


@lru_cache(maxsize=128)
def shapes(root, form):
    if form == "IX":
        a, b, c = root
        return {"past": f"اِ{a}ْ{b}َ{c}َّ", "masdar": f"اِ{a}ْ{b}ِ{c}َا{c}",
                "active": f"مُ{a}ْ{b}َ{c}ّ", "passive": None,
                "source": "lesson.sound-triliteral.IX", "generated_only": True}
    names = ["past." + form, f"grammar.masdar.{form}.{MASDAR[form]}", "imperfect." + form]
    past = generate_derivation(root, names[0], ending="َ")
    surface = past["surface"]
    if form == "IV":
        surface = "أ" + surface[1:]
    elif form in ("VII", "VIII", "X"):
        surface = "اِ" + surface[1:]
    imperfect = generate_derivation(root, names[2])["stem"]
    active = "مُ" + imperfect[2:]
    passive = active[:-2] + "َ" + active[-1] if form not in CHANGES else None
    return {"past": surface, "masdar": generate_derivation(root, names[1])["stem"],
            "active": active, "passive": passive, "past_before_display": past["surface"],
            "source": names, "table_sha256": past["table_sha256"], "generated_only": True}


class Lesson:
    def __init__(self, raw, previous, books):
        self.data = json.loads(raw)
        spec = self.data
        book_ids = [books[book][0] for book in BOOKS]
        self.revision = sha256(raw + previous.identity.encode() + json.dumps(book_ids).encode()).hexdigest()
        self.inventory = {key: {**previous.inventory[key], **spec[key]} for key in ("parents", "lexemes")}
        self.inventory["properties"] = {key: {**previous.inventory["properties"].get(key, {}),
                                              **spec["properties"].get(key, {})}
                                        for key in previous.inventory["properties"].keys() | spec["properties"].keys()}
        self.previous = previous
        self.gates = {key: roles.train(key, value, spec["version"]) for key, value in spec["gate_lessons"].items()}
        self.missing_witnesses = {}
        for group in ("sense_witnesses", "other_witnesses", "additional_uses", "syntax_witnesses"):
            for key, witness in list(spec[group].items()):
                if "url" in witness:
                    witness["basis"] = "FIXED_EXTERNAL_EXCERPT"
                    continue
                book, line = witness["book"], witness["line"]
                digest, lines = books[book]
                if (digest != spec["source_digests"][book] or not 1 <= line <= len(lines)
                        or witness["quote"] not in lines[line-1]):
                    self.missing_witnesses[group, key] = spec[group].pop(key)
                else:
                    witness["sha256"] = digest
        self.forms_by_key = {}
        for root in spec["bases"]:
            for form in spec["forms"]:
                surface = shapes(root, form)["past"]
                self.forms_by_key.setdefault(lookup_key(surface), []).append((root, form, surface))

    def cell(self, root, form):
        base = self.data["bases"][root]
        key = root + "." + form
        gate = None
        reason = "التعدية بالنسبة إلى المعنى الأساس"
        if form in GATES:
            gate_id, reason = GATES[form]
            model = self.gates[gate_id]
            schema = model.language.schema
            values = {feature: (base["valency"] == "change" if feature == "change" else feature in base["features"])
                      for feature in schema.predicates}
            prediction = model.predict(schema.case(root, form, values))
            gate = {"lesson": gate_id, "features": values, "revision": prediction.evidence_revision,
                    "conditions": [r.render(schema) for r in model.survivors]}
            allowed = {(True,): True, (False,): False}.get(prediction.possible)
        else:
            allowed = True
        witness = self.data["sense_witnesses"].get(key)
        alternate = self.data["other_witnesses"].get(key)
        redirect = form == "VII" and root in ("نقل", "لبس")
        if redirect:
            status = "REDIRECT"
        elif allowed is None:
            status = "WEIGHT_UNRESOLVED"
        elif not allowed:
            status = "BLOCKED_TRANSFORMATION"
        elif witness:
            status = "ATTESTED"
        elif alternate:
            status = "OTHER_SENSE"
        else:
            status = "NO_TARGET_WITNESS"
        return {"root": root, "form": form, "pattern": NAMES[form], "weight_allows": allowed,
                "weight_reason": reason, "learned_gate": gate, "status": status, "target_witness": witness,
                "other_witness": alternate or self.data["additional_uses"].get(key),
                "missing_target_source": ("sense_witnesses", key) in self.missing_witnesses,
                "redirect_to": "VIII" if redirect else None}

    def candidates(self, word):
        cells = lookup_clusters(word)
        if not cells:
            return []
        complete_simple = all(c[1] & set("َُِ") for c in cells) and "ّ" not in word
        return [(root, form) for root, form, canonical in self.forms_by_key.get(lookup_key(word), [])
                if not (form == "II" and complete_simple)
                and template_matches(word, canonical, mutable_last=False)]


@lru_cache(maxsize=2)
def compiled(raw, previous, digests):
    return Lesson(raw, previous, sources())


def lesson():
    return compiled(DATA.read_bytes(), event_scene.lexicon(), tuple(v[0] for v in sources().values()))


def frame(lesson, root, form):
    base = lesson.data["bases"][root]
    args = base["arguments"]
    before = (["agent", "patient"] if len(args) == 2 else
              ["bearer"] if base["valency"] == "change" else ["agent"])
    if form in CHANGES:
        slots = {"bearer": args[-1]}
        moves = {before[-1]: "bearer"}
    elif form == "II":
        slots = dict(zip(before, args, strict=True))
        moves = dict(zip(before, before, strict=True))
    else:
        required = "يتولى الإنبات" if root == "نبت" else "يقصد الاستخراج" if form == "X" else "ذو إرادة"
        shifted = ["first_object", "second_object"] if len(args) == 2 else ["patient"]
        slots = {"causer": required, **dict(zip(shifted, args, strict=True))}
        moves = dict(zip(before, shifted, strict=True))
    adjuncts = dict(lesson.data["adjuncts"].get(root, {}))
    if form in CHANGES:
        adjuncts.pop("instrument", None)
    return {"family": "change" if form in CHANGES else "action", "roles": slots,
            "transfer": moves, "added": ["cause"] if form in CHANGES and form != "IX" else
            ["causer"] if "causer" in slots else [], "adjuncts": adjuncts,
            "open_cause_slot": form in CHANGES}


def assess(lesson, noun, prop):
    lineage, facts = roles.profile(noun["kind"], lesson.inventory)
    rows = facts.get(prop, [])
    taught = {"يوجّه آلة القطع": "operator", "يقبل الفصل بالحدّ": "sliceable", "يسند الجالس": "seat",
              "له حدّ عامل": "edge", "قابل للنمو النباتي": "growth", "قابل لاخضرار النسيج النباتي": "green",
              "يستطيع الجلوس": "posture"}
    model = lesson.previous.models.get(taught.get(prop))
    if model is not None:
        out = roles.apply_role((noun, lineage, facts), model)
        state = APPLY[out["status"]]
        revision = out["learning_revision"]
    else:
        values = {r["value"] for r in rows}
        state = ("CONFLICT" if len(values) > 1 else "LICENSED" if values == {True}
                 else "BLOCKED" if values == {False} else "UNRESOLVED")
        revision = None
    return {"status": state, "property": prop, "lineage": lineage, "witnesses": rows, "learned_revision": revision}


def selection(lesson, noun, prop):
    result = assess(lesson, noun, prop)
    if prop == "يتولى الإنبات":
        water = assess(lesson, noun, "مصدر محتمل لرطوبة التربة")
        states = {result["status"], water["status"]}
        result = {"status": ("LICENSED" if "LICENSED" in states else "CONFLICT" if "CONFLICT" in states
                             else "BLOCKED" if states == {"BLOCKED"} else "UNRESOLVED"),
                  "property": "مُنمٍّ في الدرس أو مصدر محتمل للرطوبة", "alternatives": [result, water],
                  "authority": "COURSE_CAUSATIVE_READING_ONLY"}
    return result


def adjunct_property(lesson, root, role):
    return "آلة كسر" if root == "كسر" and role == "instrument" else lesson.data["adjunct_properties"][role]


def network(lesson):
    # Count distinct named kinds, deduplicating surface aliases. Unknowns are counted separately.
    kinds = sorted(set(lesson.inventory["lexemes"].values()))
    matrix, counts = [], {}
    for root in lesson.data["bases"]:
        for form in NAMES:
            cell = lesson.cell(root, form)
            if cell["redirect_to"]:
                cell["redirect_status"] = lesson.cell(root, cell["redirect_to"])["status"]
            matrix.append(cell)
            if cell["status"] != "ATTESTED":
                continue
            f = frame(lesson, root, form)
            props = {**f["roles"], **{r: adjunct_property(lesson, root, r) for r in f["adjuncts"]}}
            row = {}
            for role, prop in props.items():
                by_state = {s: [] for s in ("LICENSED", "BLOCKED", "UNRESOLVED", "CONFLICT")}
                for kind in kinds:
                    state = selection(lesson, {"kind": kind, "surface": kind}, prop)["status"]
                    by_state[state].append(kind)
                row[role] = {"property": prop, "accepted": len(by_state["LICENSED"]), "by_status": by_state}
            counts[root + "." + form] = row
    return {"matrix": matrix, "role_counts": counts, "domain": kinds, "denominator": len(kinds),
            "rule": "كل جنس معجمي مسمى مرة واحدة، والمفتوح لا يُحتسب في المقبول",
            "role_labels": lesson.data["labels"], "role_counts_scope": "PER_SLOT_COMPATIBILITY"}


def best_reading(states):
    present = set(states)
    return next((s for s in ("LICENSED", "CONFLICT", "UNRESOLVED") if s in present), "BLOCKED")


def combined(states):
    return next((s for s in ("BLOCKED", "CONFLICT", "UNRESOLVED") if s in states), "LICENSED")


def take_arguments(lesson, text, words, f, root):
    arity = len(f["roles"])
    if len(words) < arity:
        return None
    nouns = [roles.noun(text, w, lesson.inventory) for w in words[:arity]]
    if any(n is None for n in nouns):
        return None
    adjuncts, purpose = [], None
    i = arity
    while i < len(words):
        cue = words[i]
        word = cue["surface"]
        if i + 1 == len(words) and template_matches(word, "لِيَنْفَعَ", mutable_last=False):
            purpose = cue
            break
        key = lookup_key(word)
        if (key or "").startswith("بال") and template_matches(word[:lookup_clusters(word)[0][3]], "بِ",
                                                               mutable_last=False):
            prep, target = "ب", roles.noun(text, cue, lesson.inventory, instrument=True)
            i += 1
        elif i + 1 < len(words) and any(template_matches(word, p, mutable_last=False) for p in PREPS):
            prep, target = key, roles.noun(text, words[i+1], lesson.inventory)
            i += 2
        else:
            return None
        if not target or target["case_vowel"] not in (None, "ِ"):
            return None
        options = [r for r, p in f["adjuncts"].items() if p == prep]
        if not options:
            return None
        choices = [{"role": r, **selection(lesson, target, adjunct_property(lesson, root, r))} for r in options]
        # Spatial and temporal fi are genuine alternatives until a kind witness distinguishes them.
        adjuncts.append({"cue": cue, "target": target, "choices": choices})
    return nouns, adjuncts, purpose


def analyze_form(lesson, text, verb, root, form, tail):
    base = lesson.data["bases"][root]
    cell = lesson.cell(root, form)
    result = {"verb": verb, "base": base, "weight": cell, "generated": shapes(root, form),
              "readings": []}
    deferred = cell["status"] in ("OTHER_SENSE", "NO_TARGET_WITNESS")
    if not deferred and cell["status"] != "ATTESTED":
        result["status"] = "UNRESOLVED" if cell["status"] == "WEIGHT_UNRESOLVED" else "BLOCKED"
        result["decision_scope"] = "REQUESTED_ROOT_SENSE_AND_FORM_ONLY"
        result["unevaluated_tail"] = tail
        return result
    f = frame(lesson, root, form)
    result["frame"] = f
    arguments = take_arguments(lesson, text, tail, f, root)
    if arguments is None:
        if deferred:
            return dict(result, status="DEFERRED_SENSE", unevaluated_tail=tail)
        return None
    nouns, adjuncts, purpose = arguments
    names = list(f["roles"])
    for order in permutations(range(len(nouns))):
        if any(nouns[j]["case_vowel"] not in (None, CASE[r]) for r, j in zip(names, order)):
            continue
        bindings = {r: {"mention": nouns[j], "grammar": "فاعل" if CASE[r] == "ُ" else "مفعول به",
                        **selection(lesson, nouns[j], prop)}
                    for (r, prop), j in zip(f["roles"].items(), order)}
        row = {"order": list(order), "bindings": bindings, "adjuncts": adjuncts,
               "cause": "OPEN" if f["open_cause_slot"] else None, "purpose": None}
        states = [b["status"] for b in bindings.values()]
        if "second_object" in names and order[-1] < order[-2]:
            row["order_witness"] = lesson.data["syntax_witnesses"].get("object_fronting")
            if row["order_witness"] is None:
                states.append("UNRESOLVED")
        for a in adjuncts:
            choices = {c["status"] for c in a["choices"]}
            states.append(best_reading(choices))
        if purpose:
            actor = bindings.get("causer") or bindings.get("agent")
            intent = selection(lesson, actor["mention"], "ذو إرادة") if actor else {"status": "BLOCKED"}
            row["purpose"] = {"cue": purpose, "reading": "قصد الفاعل المذكور", "intent": intent,
                              "other_readings_open": ["لام العاقبة", "قصد مسبب آخر"] if not actor else [],
                              "realized": False}
            states.append(intent["status"])
        row["status"] = combined(states)
        result["readings"].append(row)
    if not result["readings"]:
        result["status"] = "BLOCKED"
        result["reason"] = "EXPLICIT_CASE_MARKS_EXCLUDE_THESE_ROLES"
    else:
        result["status"] = best_reading(r["status"] for r in result["readings"])
        result["status_interpretation"] = "EXISTENCE_OF_A_READING_IN_THIS_LESSON"
    if deferred:
        for row in result["readings"]:
            row["hypothetical_slot_status"] = row["status"]
            row["status"] = "DEFERRED_SENSE"
        result["status"] = "DEFERRED_SENSE"
    return result


def result_clause(lesson, text, words):
    if len(words) not in (4, 5):
        return None
    first, subject, patient, joined, *overt = words
    clusters = lookup_clusters(joined["surface"])
    if not clusters or clusters[0][0] != "ف" or clusters[0][1] - {"َ"}:
        return None
    split = clusters[0][3]
    verb = roles.span_word(text, joined, split)
    cue = {**joined, "surface": joined["surface"][:split],
           "codepoint_span": [joined["codepoint_span"][0], verb["codepoint_span"][0]],
           "utf8_span": [joined["utf8_span"][0], verb["utf8_span"][0]]}
    for root, form in lesson.candidates(verb["surface"]):
        if form != "VII" or root not in ("قطع", "كسر"):
            continue
        base = lesson.data["bases"][root]
        if not template_matches(first["surface"], base["verb"], mutable_last=False):
            continue
        nouns = [roles.noun(text, word, lesson.inventory) for word in (subject, patient)]
        explicit_bearer = roles.noun(text, overt[0], lesson.inventory) if overt else None
        if any(n is None for n in nouns) or (overt and (not explicit_bearer or explicit_bearer["case_vowel"] not in (None, "ُ"))):
            return None
        cell = lesson.cell(root, form)
        candidate = {"verb": verb, "base": base, "weight": cell, "generated": shapes(root, form), "readings": []}
        if cell["status"] != "ATTESTED":
            candidate["status"] = "DEFERRED_SENSE"
            return candidate
        candidate["frame"] = frame(lesson, root, form)
        witness = lesson.data["syntax_witnesses"].get("result_cut" if root == "قطع" else "result_break")
        for actor, affected in permutations(nouns):
            if actor["case_vowel"] not in (None, "ُ") or affected["case_vowel"] not in (None, "َ"):
                continue
            # The implicit subject refers back to the original accusative occurrence.
            bearer = explicit_bearer or affected
            eligible = selection(lesson, bearer, base["arguments"][1])
            source_roles = {name: {"mention": n, **selection(lesson, n, prop)}
                            for name, n, prop in zip(("agent", "patient"), (actor, affected), base["arguments"], strict=True)}
            status = combined([eligible["status"], *(r["status"] for r in source_roles.values())])
            connected = status == "LICENSED" and not overt and witness is not None
            candidate["readings"].append({
                "bindings": {"bearer": {"mention": bearer, "grammar": "فاعل ظاهر" if overt else "فاعل مستتر", **eligible}},
                "antecedent": {"verb": first, **source_roles}, "status": status,
                "cause": "PRIOR_EVENT_IN_RESULT_READING" if connected else "OPEN",
                "link": {"cue": cue, "argument_identity": "ANAPHORIC_READING" if not overt else "OPEN",
                         "witness": witness, "empirically_verified": False}})
        candidate["status"] = best_reading(r["status"] for r in candidate["readings"])
        return candidate
    return None


def analyze(text, source_id="input"):
    if len(text) > 2048:
        return None
    lex = lesson()
    meta = {"law": lex.data["version"], "lesson_sha256": lex.revision, "source_id": source_id,
            "source_sha256": sha256(text.encode()).hexdigest(), "world_occurrence_established": False,
            "empirical_causality_established": False, "role_labels": lex.data["labels"]}
    if text.strip() == CATALOG_QUERY:
        return {**meta, **network(lex)}
    words = exact_terms(text)
    if not words or len(words) > 12 or text[:words[0]["codepoint_span"][0]].strip():
        return None
    if text[words[-1]["codepoint_span"][1]:].strip() not in ("", ".") or any(
        not text[a["codepoint_span"][1]:b["codepoint_span"][0]].isspace() for a, b in zip(words, words[1:])):
        return None
    paired = result_clause(lex, text, words)
    candidates = [paired] if paired else []
    if not paired:
        for root, form in lex.candidates(words[0]["surface"]):
            candidate = analyze_form(lex, text, words[0], root, form, words[1:])
            if candidate:
                if form == "II" and "ّ" not in words[0]["surface"]:
                    candidate["open_alternative"] = "الرسم يحتمل صيغة مجردة"
                candidates.append(candidate)
    for candidate in candidates:
        cell = candidate["weight"]
        candidate["decision_chain"] = [
            {"stage": "base", "field": "base", "status": "COURSE_PREMISE"},
            {"stage": "weight", "field": "weight", "status": cell["status"] if not cell["weight_allows"] else "ALLOWED"},
            {"stage": "lexical_sense", "field": "weight", "status": cell["status"]},
            {"stage": "forms", "field": "generated", "status": "GENERATED_SHAPES"},
            {"stage": "role_transfer", "field": "frame", "status": "NOT_APPLIED" if "frame" not in candidate
             else "ATTESTED_SENSE" if cell["status"] == "ATTESTED" else "HYPOTHETICAL"},
            {"stage": "kind_properties", "field": "readings", "status": "EVALUATED" if candidate["readings"] else "NOT_APPLIED"},
            {"stage": "decision", "field": "status", "status": candidate["status"]}]
    return {**meta, "candidates": candidates} if candidates else None


def cards(report):
    from .text_reading import card
    if "matrix" in report:
        return [card("derived_role_network", "شبكة الدرس", f"{len(report['matrix'])} خلية صرفية",
                     f"تُفحص خواص {report['denominator']} جنسًا مُسمّى لكل دور.",
                     "العدد مشروط بالمعجم والمعنى المختار.", reading_ref="/derived_event_roles/role_counts")]
    output = []
    for i, c in enumerate(report["candidates"]):
        prefix = f"/derived_event_roles/candidates/{i}"
        cell = c["weight"]
        description = f"{c['base']['masdar']}، {cell['pattern']}، {c['generated']['masdar']}"
        why = cell["weight_reason"]
        source = cell["target_witness"] or cell["other_witness"]
        if source:
            why += "، " + source["gloss"]
        output.append(card("derived_role_decision", AR_STATUS[c["status"]], description, why,
                           "الحكم للمعنى المحدد في الدرس.", reading_ref=prefix))
        for j, r in enumerate(c["readings"]):
            labels = report["role_labels"]
            bindings = "، ".join(f"{labels[k]} «{b['mention']['surface']}»" for k, b in r["bindings"].items())
            reasons = []
            for binding in r["bindings"].values():
                tests = binding.get("alternatives", [binding])
                for test in tests:
                    kinds = "، ".join(w["kind"] for w in test["witnesses"])
                    reasons.append(f"{test['property']} ({AR_STATUS[test['status']]}" + (f" بشاهد {kinds})" if kinds else ")"))
            if r.get("order_witness"):
                reasons.append(r["order_witness"]["gloss"])
            if r.get("purpose"):
                reasons.append("الغاية على قراءة قصد الفاعل المذكور " + AR_STATUS[r["purpose"]["intent"]["status"]])
            if r.get("cause"):
                reasons.append("سبب مفتوح" if r["cause"] == "OPEN" else "المطاوعة تربط الأثر بالحدث السابق في النص")
            output.append(card("derived_role_reading", AR_STATUS[r["status"]], bindings, "، ".join(reasons),
                               "وقوع الحدث في الخارج يحتاج إلى شاهد مستقل.", reading_ref=f"{prefix}/readings/{j}"))
    return output
