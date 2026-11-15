"""Source-bound composition of controlled action descriptions and natural changes."""
from functools import lru_cache
from hashlib import sha256
import json
import re
import unicodedata

from nabt.corpus_evidence import lookup_clusters, lookup_key, template_matches
from . import literal_event_roles as roles
from .operations import ROOT
from .water_saturation import compare as compare_saturation

DATA = ROOT / "tools/grammar_catalog/data/event_scene_v1.json"
CHANGE = {"change_of_colour", "biological_growth", "phase_change", "dissolution"}
EXTRA_SLOTS = {"cut": {"instrument": "edge"}, "cut_repeated": {"instrument": "edge"},
               "drink": {"vessel": "vessel"}, "sit": {"support": "seat"},
               "dissolve": {"medium": "medium"}}
CASES = {"nom": "ُ", "acc": "َ", "gen": "ِ"}


class Outside(ValueError):
    """A source gap or contradiction excludes this controlled analysis."""


class Lexicon:
    def __init__(self, base_bytes, scene_bytes):
        base = json.loads(base_bytes)
        spec = json.loads(scene_bytes)
        self.version = spec["version"]
        self.identity = sha256(base_bytes + b"\0" + scene_bytes).hexdigest()
        self.inventory = {k: {**base[k], **spec[k]} for k in ("parents", "lexemes")}
        self.inventory["properties"] = {k: dict(v) for k, v in base["properties"].items()}
        for kind, facts in spec["properties"].items():
            self.inventory["properties"].setdefault(kind, {}).update(facts)
        self.models = {k: roles.train(k, v, version) for table, version in
                       ((base["lessons"], base["version"]), (spec["lessons"], self.version))
                       for k, v in table.items()}
        self.water_hypothesis = roles.train("growth_water_candidate", spec["hypothesis_lesson"],
                                           self.version, degree=2)
        self.frames = spec["frames"]
        self.adjectives = spec["adjectives"]

    def verb(self, word):
        if word == "أخضر":
            return "green", ["احتمال الصفة أخضر", "قراءة الفعل اخضرّ مشروطة بتصحيح همزة الوصل"]
        matches = [k for k, v in self.frames.items()
                   if any(template_matches(word, form, mutable_last=False) for form in v["forms"])]
        if matches == ["cut", "cut_repeated"]:
            marked = all(c[1] & set("َُِ") for c in lookup_clusters(word))
            return "cut", [] if marked else ["التقطيع عند قراءة قطّع"]
        return (matches[0], []) if len(matches) == 1 else (None, [])

    def dossier(self, mention):
        lineage, facts = roles.profile(mention["kind"], self.inventory)
        profile = mention, lineage, facts
        options = []
        for event, frame in self.frames.items():
            slots = {"bearer" if frame["family"] in CHANGE else "actor": frame["subject"],
                     "patient": frame["object"], **EXTRA_SLOTS.get(event, {})}
            for slot, lesson in slots.items():
                if lesson and roles.apply_role(profile, self.models[lesson])["status"] == "COMPATIBLE":
                    options.append({"event": event, "masdar": frame["masdar"], "role": slot})
        adjectives = []
        for adj in self.adjectives:
            if adj["grammar"].startswith("رسم"):
                continue
            slot = "patient" if adj["grammar"] == "اسم مفعول" else None
            if (adj["event"] == "yellow" and any(r["value"] for r in facts.get("له لون مشاهد", []))
                    or any(o["event"] == adj["event"] and
                           (o["role"] == slot if slot else o["role"] in ("actor", "bearer"))
                           for o in options)):
                adjectives.append({"surface": adj["form"], "masdar": adj["masdar"], "event": adj["event"]})
        return {"lineage": lineage, "property_witnesses": facts, "possible_roles": options,
                "possible_descriptions": adjectives}


@lru_cache(maxsize=2)
def compiled(base_bytes, scene_bytes):
    return Lexicon(base_bytes, scene_bytes)


def lexicon():
    return compiled(roles.DATA.read_bytes(), DATA.read_bytes())


def number(surface):
    if not re.fullmatch(r"\d{1,8}(?:[.٫]\d{1,4})?", surface or ""):
        return None
    return "".join("." if c in ".٫" else str(unicodedata.decimal(c)) for c in surface)


class Scene:
    def __init__(self, text, lex):
        self.text, self.lex = text, lex
        end = len(text.rstrip())
        if text[:end].endswith("."):
            end -= 1
        self.words = [self.span(m.start(), m.end()) for m in re.finditer(r"\S+", text[:end])]
        self.i = 0
        self.entities, self.events, self.links, self.pending = {}, [], [], []
        self.scope = "matrix_report"
        self.physical = []

    def span(self, start, end):
        return {"surface": self.text[start:end], "codepoint_span": [start, end],
                "utf8_span": [len(self.text[:start].encode()), len(self.text[:end].encode())]}

    def word(self, offset=0):
        i = self.i + offset
        return self.words[i]["surface"] if 0 <= i < len(self.words) else ""

    def key(self, offset=0):
        return lookup_key(self.word(offset)) or self.word(offset)

    def take(self):
        if self.i >= len(self.words):
            raise Outside("MISSING_CONSTITUENT")
        self.i += 1
        return self.words[self.i-1]

    def prefix(self, letter, marks):
        cells = lookup_clusters(self.word())
        if not cells or len(cells) < 2 or cells[0][0] != letter or cells[0][1] - set(marks):
            return None
        return cells[0][3]

    def split_prefix(self, length):
        token = self.words[self.i]
        start, end = token["codepoint_span"]
        self.words[self.i] = self.span(start + length, end)
        return self.span(start, start + length)

    def entity(self, case=None):
        token = self.take()
        mention = roles.noun(self.text, token, self.lex.inventory)
        if not mention or (case and mention["case_vowel"] not in (None, CASES[case])):
            raise Outside("NOUN_OR_CASE_OUTSIDE_FRAGMENT")
        ref = "n" + str(token["codepoint_span"][0])
        self.entities[ref] = {"mention": mention, **self.lex.dossier(mention)}
        if mention["kind"] is None:
            item = {"reason": "LEXICAL_KIND_UNKNOWN", "source": token}
            if lookup_key(token["surface"]) == "الحرسي":
                item["spelling_hypothesis"] = "الكرسي"
                item["substitution_applied"] = False
            self.pending.append(item)
        return ref

    def link(self, head, relation, obj, syntax, cue, **details):
        self.links.append({"head": head, "relation": relation, "target": obj, "syntax": syntax,
                           "cue": cue, **details})

    def bind(self, event, role, target, syntax, cue, lesson=None):
        if any(b["role"] == role for b in event["bindings"]):
            raise Outside("DUPLICATE_ROLE")
        binding = {"role": role, "target": target, "syntax": syntax, "cue": cue}
        if lesson and target:
            entity = self.entities[target]
            profile = entity["mention"], entity["lineage"], entity["property_witnesses"]
            binding["selection"] = roles.apply_role(profile, self.lex.models[lesson])
        event["bindings"].append(binding)
        return binding

    def spatial_np(self, head):
        marker = self.take()
        form = lookup_key(self.entities[head]["mention"]["surface"])
        feminine = {"التفاحة", "البرتقالة", "الفراولة", "الطاولة", "الملعقة"}
        if (form in feminine and lookup_key(marker["surface"]) != "التي"
                or form in {"التفاح", "الكعك", "الخبز"} and lookup_key(marker["surface"]) != "الذي"):
            raise Outside("RELATIVE_AGREEMENT_DISAGREES")
        if self.key() not in ("فوق", "تحت"):
            raise Outside("UNSUPPORTED_RELATIVE_CLAUSE")
        prep = self.take()
        landmark = self.entity("gen")
        self.link(head, "relative_position", landmark, "ظرف مكان في صلة الموصول", prep,
                  relative_marker=marker, direction=lookup_key(prep["surface"]))

    def noun_modifiers(self, head):
        if self.key() in ("الذي", "التي"):
            self.spatial_np(head)
        for adj in self.lex.adjectives:
            if template_matches(self.word(), adj["form"]):
                marked = lookup_clusters(self.word())[-1][1] & set("َُِ")
                host_case = self.entities[head]["mention"]["case_vowel"]
                if host_case and marked and host_case not in marked:
                    raise Outside("ADJECTIVE_CASE_DISAGREES")
                dossier = self.entities[head]
                if adj["event"] == "yellow":
                    support = dossier["property_witnesses"].get("له لون مشاهد", [])
                else:
                    support = [opt for opt in dossier["possible_roles"] if opt["event"] == adj["event"]
                               and (opt["role"] == "patient" if adj["grammar"] == "اسم مفعول"
                                    else opt["role"] in ("actor", "bearer"))]
                self.link(head, "described_as", adj["description"], "نعت", self.take(),
                          capability_basis=support, kind_support="SUPPORTED" if support else "OPEN",
                          masdar=adj["masdar"], lexical_event=adj["event"], form=adj["grammar"],
                          event_occurrence_inferred=False)
                break

    def measure(self, event):
        cue = self.take()
        if self.key() != "درجة" or self.key(1) != "حرارة":
            raise Outside("UNKNOWN_MEASUREMENT")
        self.take()
        self.take()
        token = self.take()
        value = number(token["surface"])
        if value is None and token["surface"] != "كذا":
            raise Outside("UNSUPPORTED_QUANTITY")
        if self.key() == "درجة":
            self.take()
        unit_key = self.key()
        unit = self.take() if unit_key in ("مئوية", "كلفن") else None
        self.link(event["id"], "temperature", value, "ظرف متعلق بحدث الغليان", cue,
                  written_value=token, unit=unit, unit_key=unit_key if unit else None, evidence_level="reported_condition")
        if value is None or unit is None:
            self.pending.append({"reason": "TEMPERATURE_VALUE_OR_UNIT_MISSING", "source": token})

    def adjunct(self, event, subject):
        key, frame = self.key(), event["frame"]
        eid = event["id"]
        grammar_forms = {"مع": "مَعَ", "بعد": "بَعْدَ", "في": "فِي", "على": "عَلَى", "بسبب": "بِسَبَبِ",
                         "عند": "عِنْدَ", "تحت": "تَحْتَ", "صباحا": "صَبَاحًا", "مساء": "مَسَاءً"}
        if key in grammar_forms and not template_matches(self.word(), grammar_forms[key], mutable_last=False):
            raise Outside("CONTRADICTORY_CUE_VOWELS")
        if key == "مع":
            cue = self.take()
            other = self.entity("gen")
            self.link(eid, "accompaniment", other, "مع ظرف للمصاحبة وما بعده مضاف إليه", cue)
            self.noun_modifiers(other)
        elif key in ("بعد", "بسبب", "في", "على"):
            cue = self.take()
            target = self.entity("gen")
            lineage = self.entities[target]["lineage"]
            if key == "على" and frame == "sit":
                self.bind(event, "support", target, "جار ومجرور متعلق بالجلوس", cue, "seat")
            elif key == "في" and frame == "dissolve":
                self.bind(event, "medium", target, "جار ومجرور", cue, "medium")
            elif key == "بسبب":
                self.link(eid, "reported_cause", target, "تعليل مصرح به في النص", cue,
                          empirically_verified=False)
            elif key == "بعد":
                self.link(eid, "after", target, "ظرف زمان مضاف", cue, cause_inferred=False)
            else:
                rel = "event_time" if "فصل" in lineage else "event_place" if "مكان" in lineage else "pp_attachment"
                details = {}
                if key == "في" and rel == "event_place" and event["bindings"][-1]["role"] in ("instrument", "vessel"):
                    details["alternative_head"] = event["bindings"][-1]["target"]
                self.link(eid, rel, target, "جار ومجرور", cue, **details)
            self.noun_modifiers(target)
        elif self.prefix("ب", "ِ") and self.key().startswith("بال"):
            if frame not in ("cut", "cut_repeated", "drink"):
                return False
            cue = self.split_prefix(self.prefix("ب", "ِ"))
            target = self.entity("gen")
            role = "vessel" if frame == "drink" else "instrument"
            self.bind(event, role, target, "جار ومجرور بباء الاستعانة", cue, EXTRA_SLOTS[frame][role])
            self.noun_modifiers(target)
        elif key in ("صباحا", "مساء", "مساءً"):
            self.link(eid, "event_time", self.word(), "مفعول فيه منصوب", self.take())
        elif key in ("رغبة", "رغبةً"):
            cue = self.take()
            if not template_matches(cue["surface"], "رَغْبَةً", mutable_last=False) or self.key() != "في":
                raise Outside("UNSUPPORTED_PURPOSE_NOUN")
            self.take()
            goal = self.entity("gen")
            self.link(eid, "purpose", goal, "مفعول لأجله، مصدر قلبي", cue,
                      understood_subject=subject, realized=False)
        elif key == "عند" and frame == "boil":
            self.measure(event)
        elif key == "تحت" and frame == "boil" and self.key(1) == "ضغط":
            cue = self.take()
            self.take()
            quantity = self.take()
            value = number(quantity["surface"])
            if value is None or self.key() != "باسكال":
                raise Outside("PRESSURE_VALUE_OR_UNIT_MISSING")
            self.link(eid, "pressure", value, "قيد قياس", cue, written_value=quantity, unit=self.take())
        elif frame == "walk" and self.key().startswith("وال") and self.prefix("و", "َ"):
            cue = self.split_prefix(self.prefix("و", "َ"))
            target = self.entity()
            vowel = self.entities[target]["mention"]["case_vowel"]
            if vowel == "َ":
                self.link(eid, "accompaniment", target, "مفعول معه منصوب بعد واو المعية", cue)
            elif vowel is None:
                self.link(eid, "waw_ambiguous", target, "واو تحتمل المعية والعطف", cue)
            elif vowel == "ُ":
                self.link(eid, "coordinated_subject", target, "معطوف مرفوع", cue)
            else:
                raise Outside("WAW_CASE_MISMATCH")
        else:
            return False
        return True

    def clause(self, subject=None, *, mode="matrix_report", inherited=False, purpose_frame=None):
        verb = self.take()
        frame, alternatives = (purpose_frame, []) if purpose_frame else self.lex.verb(verb["surface"])
        if not frame:
            raise Outside("VERB_SENSE_UNRESOLVED")
        spec = self.lex.frames[frame]
        event = {"id": "e" + str(verb["codepoint_span"][0]), "frame": frame, "family": spec["family"],
                 "masdar": spec["masdar"], "verb": verb, "scope": mode, "alternatives": alternatives,
                 "lexical_source": {"path": roles.DICTIONARY, "line": spec["line"]}, "bindings": []}
        self.events.append(event)
        if "قراءة الفعل اخضرّ مشروطة بتصحيح همزة الوصل" in alternatives:
            self.pending.append({"reason": "ADJECTIVE_OR_VERB_READING", "source": verb})
        first_noun = self.key().startswith("ال") and self.key() not in ("الذي", "التي")
        second_noun = self.key(1).startswith("ال") and self.key(1) not in ("الذي", "التي")
        second_adj = any(template_matches(self.word(1), adj["form"]) for adj in self.lex.adjectives)
        patient = None
        if first_noun and (not subject or (inherited and (not spec["object"] or (second_noun and not second_adj)))):
            first_mark = lookup_clusters(self.word())[-1][1]
            if spec["object"] and "َ" in first_mark and second_noun and "ُ" in lookup_clusters(self.word(1))[-1][1]:
                patient = self.entity("acc")
            subject = self.entity("nom")
            subject_syntax = "فاعل ظاهر"
            if not patient and spec["object"] and second_noun and not second_adj and not first_mark & set("َُ"):
                event["alternatives"].append("ترتيب اسمي الفاعل والمفعول غير محسوم بالضبط وحده")
        else:
            subject_syntax = "ضمير عائد على المذكور" if subject else "فاعل مستتر غير معيّن"
        subject_role = "bearer" if spec["family"] in CHANGE else "actor"
        cue = self.entities[subject]["mention"]["token"] if subject_syntax == "فاعل ظاهر" else verb
        self.bind(event, subject_role, subject, subject_syntax, cue, spec["subject"])
        if subject is None:
            self.pending.append({"reason": "UNBOUND_SUBJECT", "source": verb})
        if patient:
            self.bind(event, "patient", patient, "مفعول به مقدّم", self.entities[patient]["mention"]["token"], spec["object"])
        while self.word():
            if self.adjunct(event, subject):
                continue
            if spec["object"] and patient is None and self.key().startswith("ال"):
                patient = self.entity("acc")
                self.bind(event, "patient", patient, "مفعول به", self.entities[patient]["mention"]["token"], spec["object"])
                self.noun_modifiers(patient)
                continue
            break
        if spec["object"] and patient is None:
            self.pending.append({"reason": "PATIENT_UNEXPRESSED", "source": verb})
        if frame == "drink" and patient:
            for relation in list(self.links):
                if relation["head"] == event["id"] and relation["relation"] == "accompaniment":
                    companion = relation["target"]
                    self.disposition(companion, patient, relation["cue"], stated=False)
        if frame == "grow":
            event["mechanism_candidates"] = self.growth_hypotheses(event, subject)
        if frame == "boil":
            conditions = [r for r in self.links if r["head"] == event["id"]]
            if not any(r["relation"] == "pressure" for r in conditions):
                self.pending.append({"reason": "PRESSURE_UNSPECIFIED", "source": verb})
            bearer = self.entities[subject]["mention"]["kind"] if subject else None
            self.physical.append({"event": event["id"], **compare_saturation(bearer, conditions)})
        if frame == "dissolve" and not any(b["role"] == "medium" for b in event["bindings"]):
            event["alternatives"].append("لم يُذكر وسط يعيّن الإذابة في محلول دون الانصهار")
        return event, subject

    def growth_hypotheses(self, event, subject):
        model = self.lex.water_hypothesis
        schema = model.language.schema
        candidates = []
        for relation in self.links:
            if relation["head"] != event["id"] or relation["relation"] not in ("after", "reported_cause"):
                continue
            values, witnesses = {}, {}
            for ref, name in zip((subject, relation["target"]), schema.predicates, strict=True):
                rows = self.entities[ref]["property_witnesses"].get(name, []) if ref else []
                witnesses[name] = rows
                evidence = {r["value"] for r in rows}
                if len(evidence) == 1:
                    values[name] = evidence.pop()
            prediction = model.predict(schema.case(event["id"], relation["target"], values))
            if prediction.possible == (True,):
                candidates.append({"event": event["id"], "candidate_factor": relation["target"],
                                   "mechanism_ar": "احتمال مساهمة الماء في رطوبة موضع النمو",
                                   "status": "HYPOTHESIS_ONLY", "empirically_verified": False,
                                   "training_revision": prediction.evidence_revision, "witnesses": witnesses,
                                   "guard": [r.render(schema) for r in model.survivors],
                                   "needed": ["تعيين النبات والموضع والمرحلة",
                                              "شاهد وصول الماء وتغيّر الرطوبة",
                                              "مقارنة أو دليل يميّز السبب من العوامل المنافسة"]})
        return candidates

    def disposition(self, solute, medium, cue, *, stated):
        def check(ref, lesson):
            ent = self.entities[ref]
            return roles.apply_role((ent["mention"], ent["lineage"], ent["property_witnesses"]),
                                    self.lex.models[lesson])
        guards = [check(solute, "solute"), check(medium, "medium")]
        if stated or all(g["status"] == "COMPATIBLE" for g in guards):
            self.link(solute, "stated_disposition" if stated else "possible_dissolution_in",
                      medium, "قابلية مذكورة" if stated else "قابلية مستعادة من المعجم", cue,
                      masdar="الذوبان", conditions=["وسط مائي بظروف تسمح بمزيد من الذوبان"],
                      guards=guards, occurrence_inferred=False)

    def disposition_clause(self, subject):
        start = self.i
        terms = ("قابل", "للذوبان", "في") if self.key() == "قابل" else (
            "جنس", "له", "خاصية", "الذوبان", "في")
        for term in terms:
            if self.key() != term:
                raise Outside("UNSUPPORTED_DISPOSITION")
            self.take()
        cue = self.span(self.words[start]["codepoint_span"][0], self.words[self.i-1]["codepoint_span"][1])
        self.disposition(subject, self.entity("gen"), cue, stated=True)

    def parse(self):
        subject = None
        if self.key().startswith("ال"):
            subject = self.entity()
            if not self.word():
                self.scope = "lexical_mention"
                return
            if self.key() in ("قابل", "جنس"):
                self.disposition_clause(subject)
                if self.word():
                    raise Outside("UNCONSUMED_DISPOSITION")
                self.scope = "reported_disposition"
                return
            relative = None
            if self.key() in ("الذي", "التي"):
                relative = self.take()
                self.scope = "relative_description"
            elif not self.lex.verb(self.word())[0]:
                self.noun_modifiers(subject)
                self.scope = "lexical_mention"
                if self.word():
                    raise Outside("UNCONSUMED_NOUN_PHRASE")
                return
            if self.entities[subject]["mention"]["case_vowel"] not in (None, CASES["nom"]) and self.scope == "matrix_report":
                raise Outside("TOPIC_CASE_MISMATCH")
        event, subject = self.clause(subject, mode=self.scope)
        if self.scope == "relative_description":
            self.link(subject, "relative_clause", event["id"], "صلة الموصول", relative)
        while self.word():
            waw = self.prefix("و", "َ")
            lam = self.prefix("ل", "ِ")
            if waw and self.key().startswith("وال") and self.key(1) in ("قابل", "جنس"):
                cue = self.split_prefix(waw)
                topic = self.entity("nom")
                self.disposition_clause(topic)
                self.link(event["id"], "coordinated_description", topic, "جملة اسمية معطوفة", cue)
                continue
            purpose_frame = next((k for k, f in self.lex.frames.items() if lam and f.get("purpose_form")
                                  and template_matches(self.word()[lam:], f["purpose_form"], mutable_last=False)), None)
            if (waw and self.lex.verb(self.word()[waw:])[0]) or (self.key() == "و" and self.lex.verb(self.word(1))[0]):
                cue = self.split_prefix(waw) if waw else self.take()
                child, subject = self.clause(subject, mode=event["scope"], inherited=True)
                self.link(event["id"], "coordination", child["id"], "عطف جملة", cue)
            elif purpose_frame:
                cue = self.split_prefix(lam)
                child, subject = self.clause(subject, mode="intended", inherited=True, purpose_frame=purpose_frame)
                self.link(event["id"], "purpose", child["id"], "لام التعليل مع المضارع", cue, realized=False)
            else:
                raise Outside("UNCONSUMED_CONSTITUENT")
            if purpose_frame and not waw:
                first = next((b["target"] for b in event["bindings"] if b["role"] == "patient"), None)
                second = next((b["target"] for b in child["bindings"] if b["role"] == "patient"), None)
                if first and second:
                    kind = self.entities[first]["mention"]["kind"]
                    if kind and kind == self.entities[second]["mention"]["kind"]:
                        self.link(second, "candidate_coreference", first, "تكرر اسم الجنس في جملة الغاية",
                                  self.entities[second]["mention"]["token"], individual_identity_verified=False)
            event = child


def analyze(text, source_id="input"):
    if len(text) > 2048:
        return None
    lex = lexicon()
    scene = Scene(text, lex)
    if not 1 <= len(scene.words) <= 64:
        return None
    if not (lex.verb(scene.word())[0] or scene.key().startswith("ال")):
        return None
    # The simple VSO fragment retains its two full order readings in the existing owner.
    if len(scene.words) <= 4 and lex.verb(scene.word())[0] in ("cut", "cut_repeated", "eat"):
        old = roles.analyze(text, source_id)
        if old and old["status"] == "READINGS":
            return None
    try:
        scene.parse()
    except Outside:
        return None
    if scene.scope == "lexical_mention" and not any(e["lineage"] for e in scene.entities.values()):
        return None
    return {"law": lex.version, "lexicon_sha256": lex.identity, "source_id": source_id,
            "source_sha256": sha256(text.encode()).hexdigest(), "scope": scene.scope,
            "coverage": "COMPLETE_IN_FRAGMENT", "entities": scene.entities, "events": scene.events,
            "relations": scene.links, "open_questions": scene.pending, "physical_comparisons": scene.physical,
            "authority": "CONTROLLED_TEXT_READING_AND_TEACHER_KIND_PREMISES",
            "world_occurrence_verified": False, "empirical_cause_verified": False}
