"""Role selection under the stated literal food/fruit-cutting lesson premises."""
from hashlib import sha256
from itertools import permutations
import json

from nabt.corpus_evidence import lookup_clusters, lookup_key, template_matches
from nabt.learning.finite_guard import FeatureSchema, GuardLanguage, LearningSession, Observation
from .operations import ROOT, exact_terms

DATA = ROOT / "tools/grammar_catalog/data/literal_event_roles_v1.json"
DICTIONARY = "src/nabt/data/source_evidence/mukhtar_sihah.txt"
CASE = {"actor": "ُ", "patient": "َ", "instrument": "ِ"}


def train(lesson_id, spec, version, *, degree=1):
    schema = FeatureSchema(lesson_id, version, tuple(spec["features"]))
    observations = []
    for i, (description, *values, label) in enumerate(spec["examples"]):
        case = schema.case(description, version, dict(zip(schema.predicates, values, strict=True)))
        observations.append(Observation(f"{lesson_id}:{i+1}", "teacher:" + version, case, label))
    return LearningSession(GuardLanguage(schema, degree=degree), tuple(observations))


def span_word(source, word, start):
    left, right = word["codepoint_span"]
    return {"surface": source[left+start:right], "codepoint_span": [left+start, right],
            "utf8_span": [len(source[:left+start].encode()), word["utf8_span"][1]]}


def noun(source, word, inventory, *, instrument=False):
    surface = word["surface"]
    cells = lookup_clusters(surface)
    if not cells:
        return None
    start = 0
    if instrument:
        if cells[0][0] != "ب" or cells[0][1] not in (set(), {"ِ"}):
            return None
        start = cells[0][3]
    bound = span_word(source, word, start)
    form = bound["surface"]
    if not (lookup_key(form) or "").startswith("ال"):
        return None
    # A named reading may not erase an explicit contradictory vowel.
    candidates = [(canonical, kind) for canonical, kind in inventory["lexemes"].items()
                  if lookup_key(canonical) == lookup_key(form)]
    matches = [kind for canonical, kind in candidates if template_matches(form, canonical)]
    if candidates and not matches:
        return None
    marks = cells[-1][1] & set("ًٌٍَُِْ")
    return {**bound, "kind": matches[0] if matches else None,
            "case_vowel": next(iter(marks), None), "token": word}


def profile(kind, inventory):
    lineage, testimony = [], {}
    while kind is not None:
        if kind in lineage:
            raise ValueError("Cycle in teaching taxonomy")
        lineage.append(kind)
        for name, value in inventory["properties"].get(kind, {}).items():
            testimony.setdefault(name, []).append({"kind": kind, "value": value})
        kind = inventory["parents"].get(kind)
    return lineage, testimony


def apply_role(noun_reading, model):
    schema = model.language.schema
    noun, lineage, testimony = noun_reading
    witnesses = {p: testimony.get(p, []) for p in schema.predicates}
    values = {}
    conflicts = set()
    for p, rows in witnesses.items():
        alternatives = {r["value"] for r in rows}
        if len(alternatives) == 1:
            values[p] = alternatives.pop()
        elif alternatives:
            conflicts.add(p)
    case = schema.case(noun["surface"], "literal_kind_profile", values)
    decision = model.predict(case)
    rules = [{"id": r.code, "condition": r.render(schema)} for r in model.survivors]
    # A conflict in an unused distractor cannot veto a settled role.
    if not decision.possible:
        status = "CONFLICT"
    elif decision.possible == (True,):
        status = "COMPATIBLE"
    elif decision.possible == (False,):
        status = "INCOMPATIBLE"
    elif conflicts.intersection(p for i, p in enumerate(schema.predicates)
                               if any((r.positive | r.negative) & (1 << i) for r in model.survivors)):
        status = "CONFLICT"
    else:
        status = "DEFER"
    return {"mention": noun, "lineage": lineage, "property_witnesses": witnesses,
            "status": status, "property_rules": rules, "lesson": schema.domain,
            "learning_revision": decision.evidence_revision,
            "training_witnesses": [o.evidence_id for o in model.observations]}


def reading_status(roles):
    states = {r["status"] for r in roles.values()}
    for status in ("INCOMPATIBLE", "CONFLICT", "DEFER"):
        if status in states:
            return status
    return "COMPATIBLE"


def analyze(text, source_id="input"):
    words = exact_terms(text)
    if not words or lookup_key(words[0]["surface"]) not in {"أكل", "اكل", "قطع"}:
        return None
    raw = DATA.read_bytes()
    inventory = json.loads(raw)
    report = {"law": inventory["version"], "source_id": source_id, "source_sha256": sha256(text.encode()).hexdigest(),
              "lesson_sha256": sha256(raw).hexdigest(), "scope_ar": inventory["scope_ar"],
              "authority": "CONDITIONAL_ON_TEACHER_KIND_PROPERTIES_AND_ACTIVE_LITERAL_SENSE",
              "status": "OUTSIDE_FRAGMENT", "readings": [], "occurrence_established": False,
              "empirical_causality_established": False}
    if len(words) not in (3, 4) or text[:words[0]["codepoint_span"][0]].strip():
        return report
    if text[words[-1]["codepoint_span"][1]:].strip() not in ("", "."):
        return report
    if any(not all(c in " \t" for c in text[a["codepoint_span"][1]:b["codepoint_span"][0]])
           for a, b in zip(words, words[1:])):
        return report
    verb = words[0]["surface"]
    frames = [v for v in inventory["verbs"] if any(template_matches(verb, form, mutable_last=False)
                                                    for form in v["forms"])]
    if all(cell[1] & set("َُِ") for cell in lookup_clusters(verb)) and "ّ" not in verb:
        frames = [v for v in frames if v["event"] != "cut_repeated"]
    nouns = [noun(text, w, inventory, instrument=i == 2) for i, w in enumerate(words[1:])]
    if not frames or any(n is None for n in nouns):
        return report
    with_tool = len(nouns) == 3
    if with_tool and nouns[2]["case_vowel"] not in (None, CASE["instrument"]):
        return dict(report, status="CASE_MISMATCH")
    orders = [order for order in permutations((0, 1))
              if all(nouns[i]["case_vowel"] in (None, CASE[role])
                     for role, i in zip(("actor", "patient"), order))]
    if not orders:
        return dict(report, status="CASE_MISMATCH")
    slots = [(n, *profile(n["kind"], inventory)) for n in nouns]
    models = {name: train(name, spec, inventory["version"]) for name, spec in inventory["lessons"].items()}
    for frame in frames:
        if with_tool and "instrument" not in frame["roles"]:
            continue
        for order in orders:
            indices = dict(zip(("actor", "patient"), order))
            if with_tool:
                indices["instrument"] = 2
            roles = {role: apply_role(slots[i], models[frame["roles"][role]]) for role, i in indices.items()}
            report["readings"].append({
                "event": frame["event"], "masdar": frame["masdar"], "verb": words[0],
                "lexical_reference": {"path": DICTIONARY, "line": frame["dictionary_line"]},
                "agent_name": frame["actor"], "patient_name": frame["patient"],
                "order": "VSO" if order == (0, 1) else "VOS",
                "instrument_expression": "باء الآلة" if with_tool else None,
                "roles": roles, "status": reading_status(roles)})
    # Compatibility under one reading never deletes a competing grammatical reading.
    if report["readings"]:
        used = {role["lesson"] for row in report["readings"] for role in row["roles"].values()}
        report["lessons"] = {name: {
            "features": inventory["lessons"][name]["features"],
            "examples": [{"id": o.evidence_id, "description": o.case.case_id, "values": row[1:-1],
                          "compatible": o.label} for o, row in zip(models[name].observations,
                                      inventory["lessons"][name]["examples"], strict=True)]}
            for name in sorted(used)}
        report["status"] = "READINGS"
    return report
