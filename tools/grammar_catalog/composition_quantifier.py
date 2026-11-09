"""Compile a nonempty declared finite scope to existing signed Horn rules.

The supplied list is a scope boundary, never evidence of genus membership or
of completeness of a real-world class. Absence of a positive is not a negative.
"""
import re

from tools import verified_reading as ground
from .composition_arithmetic import fail

POLICY_SOURCE = "scope_policy"
GOAL = {"predicate": "نتيجة_النطاق", "arguments": ["النطاق", "القضية"], "positive": True}
RESERVED = {"نتيجة_النطاق", "النطاق", "القضية"}
ALIASES = {"ليس كل طالب مجتهدًا": ("not_all", "طالب", "مجتهد"),
           "كل طالب غير مجتهد": ("all_not", "طالب", "مجتهد")}


def parse(text):
    force = "question" if text.startswith("هل ") else "assertion_target"
    prefix = 3 if force == "question" else 0
    core = text[prefix:]
    if core.endswith("؟" if force == "question" else "."):
        core = core[:-1]
    if core in ALIASES:
        kind, genus, prop = ALIASES[core]
        alignment = "AUTHORED_LITERAL_ALIAS_V1"
    else:
        words = core.split(" ")
        if len(words) == 4 and words[0] == "كل" and words[2] == "هو":
            kind, genus, prop = "all", words[1], words[3]
        elif len(words) == 5 and words[:2] == ["ليس", "كل"] and words[3] == "هو":
            kind, genus, prop = "not_all", words[2], words[4]
        elif len(words) == 5 and words[0] == "كل" and words[2:4] == ["ليس", "هو"]:
            kind, genus, prop = "all_not", words[1], words[4]
        else:
            fail("DEFER", "Outside the declared quantifier grammar")
        if not all(ground.valid_name(s) and len(s) <= 64 for s in (genus, prop)):
            fail("DEFER", "Noncanonical quantifier concept")
        alignment = "CONTROLLED_COPULA_V1"
    if genus in RESERVED or prop in RESERVED:
        fail("INVALID_INPUT", "Reserved scope symbols")
    rows = []
    for m in re.finditer(r"[^ ]+", core):
        start = len(text[:prefix + m.start()].encode())
        rows.append({"raw": m.group(), "span": [start, start + len(m.group().encode())]})
    return {"kind": kind, "genus": genus, "property": prop, "force": force,
            "alignment": alignment, "tokens": rows,
            "scope_tree": (["not", ["all", genus, prop]] if kind == "not_all" else
                           ["all", genus, ["not", prop]] if kind == "all_not" else ["all", genus, prop])}


def project(text, domain):
    frame = parse(text)
    def atom(name, concept, positive=True):
        return {"predicate": concept, "arguments": [name], "positive": positive}
    def rule(body, positive):
        return {"kind": "rule", "body": body, "head": {**GOAL, "positive": positive}}
    members = [atom(n, frame["genus"]) for n in domain]
    positives = [atom(n, frame["property"]) for n in domain]
    negatives = [atom(n, frame["property"], False) for n in domain]
    kind = frame["kind"]
    universal = rule([a for pair in zip(members, negatives if kind == "all_not" else positives) for a in pair],
                     kind != "not_all")
    counters = [rule([member, pred], kind == "not_all") for member, pred in
                zip(members, positives if kind == "all_not" else negatives)]
    clauses = [universal, *counters]
    return {"frame": frame, "domain": domain, "clauses": clauses,
            "policy_text": "".join(ground.render_clause(c) for c in clauses),
            "query_text": "هل " + ground.render_atom(GOAL) + "؟\n"}
