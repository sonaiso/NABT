"""Scoped, written, post-verbal argument binding. Permute roles, never the source."""
from hashlib import sha256
from itertools import permutations
import json

from nabt.corpus_evidence import lookup_clusters, lookup_key
from nabt.inflection import EXPECTED_TABLE_SHA256, relation_candidate, sign_candidates
from .operations import ROOT, exact_terms
from .source_evidence_view import pinned_excerpts

LAW = "nabt.classical-role-bridge.v1"
INVENTORY = "tools/grammar_catalog/data/classical_roles_v1.json"
INVENTORY_SHA256 = "6e328d6bee7786fabe71d04ce1b23120466b066b7e5629bb9d6ab0e28bc69c2b"


def inventory():
    raw = (ROOT / INVENTORY).read_bytes()
    if sha256(raw).hexdigest() != INVENTORY_SHA256:
        raise ValueError("Classical role inventory differs")
    return json.loads(raw)


def compatible(written, exemplar):
    a, b = lookup_clusters(written), lookup_clusters(exemplar)
    return bool(a and b and len(a) == len(b) and all(
        written[x[2]] == exemplar[y[2]] and x[1] <= y[1] for x, y in zip(a, b)))


def source_frame(text):
    tokens = exact_terms(text)
    if len(tokens) not in (3, 4):
        return None
    ask = len(tokens) == 4
    if ask and not compatible(tokens[0]["surface"], "هَلْ"):
        return None
    start, stop = tokens[0]["codepoint_span"][0], tokens[-1]["codepoint_span"][1]
    if text[:start].strip() or text[stop:].strip() not in (("", "؟", "?") if ask else ("", ".")):
        return None
    for a, b in zip(tokens, tokens[1:]):
        gap = text[a["codepoint_span"][1]:b["codepoint_span"][0]]
        if not gap or any(c not in " \t" for c in gap):
            return None
    return tokens, ask


def noun_reading(token, stems):
    surface = token["surface"]
    clusters = lookup_clusters(surface)
    if not clusters:
        return None
    for stem in stems:
        for ending, cls, sign in (("ُ", 0, "damma"), ("َ", 0, "fatha"), ("َانِ", 2, "alif"), ("َيْنِ", 2, "ya")):
            if not compatible(surface, stem + ending):
                continue
            if cls == 0 and ending not in clusters[-1][1]:
                continue
            if sign == "ya" and "َ" not in clusters[-3][1] and "ِ" not in clusters[-1][1]:
                # The unmarked oblique spelling could also be a sound plural.
                continue
            if cls == 0:
                at = surface.index(ending, clusters[-1][2])
            else:
                at = clusters[-2][2]
            start = token["utf8_span"][0] + len(surface[:at].encode())
            stop = start + len(surface[at].encode())
            rows = [r for r in sign_candidates([cls]) if r["sign_name"] == sign]
            return {"term": token, "concept": "noun:" + lookup_key(stem), "number": "dual" if cls == 2 else "singular",
                    "sign": sign, "sign_span": [start, stop], "case_rows": rows,
                    "rule_ref": "dual" if cls == 2 else "primary"}
    return None


def interpret(text, bank, preferred=None):
    """The caller has authenticated the grammar/lexical bank; raw text determines the premises."""
    frame = source_frame(text)
    if not frame:
        return None
    tokens, ask = frame
    verb, *arguments = tokens[-3:]
    written = lookup_clusters(verb["surface"])
    if not written or len(written) < 3 or "َ" not in written[-2][1]:
        return None
    senses = [key for key, form in bank["verbs"].items() if compatible(verb["surface"], form[0])]
    if len(senses) != 1:
        return None
    nouns = [noun_reading(t, bank["nouns"]) for t in arguments]
    if not all(nouns):
        return None
    orders = list(permutations(nouns))
    if preferred is not None:
        orders.sort(key=lambda pair: [n["term"]["utf8_span"] for n in pair] != preferred)
    required = [relation_candidate(role, kind="noun", construction="inflected")
                for role in ("active_subject", "direct_object")]
    bindings = [(s, o) for s, o in orders
                if any(r["case_name"] == required[0]["case_name"] for r in s["case_rows"])
                and any(r["case_name"] == required[1]["case_name"] for r in o["case_rows"])]
    if len(bindings) != 1:
        return None
    subject, obj = bindings[0]
    return {"verb": verb, "sense": senses[0], "subject": subject, "object": obj,
            "force": "ask" if ask else "assert", "cue": tokens[0] if ask else None,
            "relation_premises": required, "checked_orders": [[n["term"]["utf8_span"] for n in pair] for pair in orders]}


def analyze(text, proposal=None):
    """Return an evidence graph, granting only the authored, witnessed interpretation."""
    if not source_frame(text):
        return None
    bank = inventory()
    source_hash = sha256(text.encode()).hexdigest()
    preferred = None
    if proposal and proposal.get("source_sha256") == source_hash and proposal.get("status") == "PROPOSED":
        preferred = [proposal["heads"][name]["span"] for name in ("subject", "object")]
    reading = interpret(text, bank, preferred)
    if not reading:
        return None
    sense = reading["sense"]
    verb, subject, obj = (reading[k] for k in ("verb", "subject", "object"))
    refs = {"jurjani:092", "governed_roles", "object_first", "predication", sense,
            subject["rule_ref"], obj["rule_ref"]}
    if reading["cue"]:
        refs.add("question")
    sources = pinned_excerpts(bank, sorted(refs))
    form, masdar, agent, recipient = bank["verbs"][sense]
    nodes = []

    def node(kind, term, **attrs):
        left, right = term["utf8_span"]
        identity = f"{source_hash}/{kind}/{left}-{right}"
        nodes.append({"id": identity, "kind": kind, "span": [left, right], **attrs})
        return identity

    occurrence = node("governor_occurrence", verb, space="S", governor_id="jurjani:092")
    event = node("event", verb, space="A", sense="lexical:" + sense, masdar=masdar, lexical_form=form)
    force = reading["force"]
    clause = node("clause", {"utf8_span": [0, len(text.encode())]}, space="M", force=force)
    # Concept/type identities can be shared, while argument occurrences stay distinct.
    concepts = {n["concept"] for n in (subject, obj)}
    nodes.extend({"id": c, "kind": "nominal_concept", "space": "C"} for c in sorted(concepts))
    nodes.extend([{"id": "lexical:" + sense, "space": "C", "kind": "event_concept"},
                  {"id": "type:person", "space": "G", "kind": "authored_lexical_type"}])
    edges = [{"from": occurrence, "to": event, "type": "evokes", "evidence": [sense]},
             {"from": event, "to": "lexical:" + sense, "type": "sense_candidate", "evidence": [sense]}]
    for noun, role, case, sem in ((subject, "subject", "raf", agent), (obj, "object", "nasb", recipient)):
        arg = node("argument_occurrence", noun["term"], space="S", reading=noun)
        edges.append({"from": occurrence, "to": arg, "type": role, "case": case,
                      "evidence": ["jurjani:092", "governed_roles", "object_first", noun["rule_ref"]],
                      "sign_span": noun["sign_span"]})
        edges.append({"from": arg, "to": noun["concept"], "type": "nominal_reading",
                      "premise": INVENTORY_SHA256, "number": noun["number"]})
        edges.append({"from": event, "to": arg, "type": "semantic_role", "value": sem,
                      "depends_on_role": role, "evidence": [sense]})
    edges.extend({"from": c, "to": "type:person", "type": "type_in_authored_reading",
                  "premise": INVENTORY_SHA256} for c in sorted(concepts))
    edges.append({"from": clause, "to": event, "type": "asks_about" if force == "ask" else "asserts",
                  "cue_span": reading["cue"]["utf8_span"] if reading["cue"] else None,
                  "evidence": ["question", "predication"] if force == "ask" else ["predication"]})
    return {"law": LAW, "authority": "SCOPED_WRITTEN_INTERPRETATION", "source_sha256": source_hash,
            "inventory_sha256": INVENTORY_SHA256, "inflection_table_sha256": EXPECTED_TABLE_SHA256,
            "reading": reading, "witnesses": sources, "nodes": nodes, "edges": edges,
            "world_truth_established": False, "external_causation_established": False,
            "customary_use_established": False,
            "customary_obligation": "INDEPENDENT_OCCURRENCE_LOCAL_CONVENTION_AND_USAGE_WITNESS"}


def usage_handoff(graph, usage):
    """Link exact occurrences to the independent usage owner, preserving its authority."""
    if graph["source_sha256"] != (usage.get("source") or {}).get("sha256"):
        return {"status": "UNBOUND_USAGE_SOURCE", "customary_use_established": False}
    if not usage["acquisition_scan_complete"] or usage["status"] in {
            "RESOURCE_EXHAUSTED", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE", "INVALID_INPUT"}:
        return {"status": "USAGE_SCAN_INCOMPLETE", "customary_use_established": False}
    eligible = {tuple(n["span"]): n["id"] for n in graph["nodes"]
                if n["kind"] in ("argument_occurrence", "governor_occurrence")}
    links = []
    for i, item in enumerate(usage["occurrences"]):
        span = item["span"]
        key = (span["start_byte"], span["end_byte"])
        if key in eligible:
            links.append({"node": eligible[key], "occurrence_id": item["occurrence_id"],
                          "owner_ref": f"/use_owner/occurrences/{i}",
                          "available_senses": item["available_senses"]})
    if links and not usage["native_checked"]:
        return {"status": "USAGE_VERIFICATION_UNAVAILABLE", "usage_owner_ref": "/use_owner",
                "customary_use_established": False}
    return {"status": "SENSE_ALIGNMENT_REQUIRED" if links else "NO_MATCHING_USAGE_OCCURRENCE",
            "usage_owner_ref": "/use_owner", "links": links, "customary_use_established": False,
            "obligations": ["SAME_SENSE", "INDEPENDENT_CONVENTION_WITNESS", "LOCAL_USE_WITNESS"]}
