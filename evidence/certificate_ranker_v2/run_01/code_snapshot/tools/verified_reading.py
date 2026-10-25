#!/usr/bin/env python3
"""Untrusted certificate proposer for the verified ground-reading path.

Use the Lean verifiedReading executable to obtain a verified verdict. This
program's output alone is NOT proof, even when its proposal appears complete.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt.text_reader import parse_document, parse_query

LAW_ID = "nabt.verified-ground-reading.v1"
RESERVED = {"ليس", "هو", "إذا", "فإن", "و", "هل", "كل", "كان", "تعريف", "مفهوم", "علاقة", "فرد"}


def literal(a):
    return {"predicate": a.predicate, "arguments": list(a.args), "positive": a.positive}


def key(a):
    return a["predicate"], tuple(a["arguments"]), a["positive"]


def opposite(a):
    return a[0], a[1], not a[2]


def valid_name(s):
    return bool(s) and s not in RESERVED and all(
        "a" <= c <= "z" or "A" <= c <= "Z" or "0" <= c <= "9" or c == "_"
        or "ء" <= c <= "غ" or "ف" <= c <= "ي" or "ً" <= c <= "ْ" for c in s)


def render_atom(a):
    names = [a["predicate"], *a["arguments"]]
    if not all(valid_name(s) for s in names) or len(a["arguments"]) not in (1, 2):
        raise ValueError("OUTSIDE_VERIFIED_LANGUAGE: invalid ground name or arity")
    words = ([a["arguments"][0], "هو", a["predicate"]] if len(a["arguments"]) == 1
             else [a["arguments"][0], a["predicate"], a["arguments"][1]])
    return ("" if a["positive"] else "ليس ") + " ".join(words)


def render_clause(c):
    if c["kind"] == "fact":
        return render_atom(c["atom"]) + ".\n"
    if not c["body"]:
        raise ValueError("OUTSIDE_VERIFIED_LANGUAGE: empty rule")
    return "إذا " + " و ".join(map(render_atom, c["body"])) + " فإن " + render_atom(c["head"]) + ".\n"


def closure(facts, rules):
    """Propose a trace, not authority; Lean replays it and checks saturation."""
    seen, known, steps = set(), [], []
    def add(a, kind, index):
        k = key(a)
        if k in seen:
            return False
        seen.add(k)
        known.append(a)
        steps.append({"kind": kind, "index": index})
        return True
    for i, f in enumerate(facts):
        add(f, "fact", i)
    changed = True
    while changed:
        changed = False
        for i, r in enumerate(rules):
            if all(key(a) in seen for a in r["body"]):
                changed |= add(r["head"], "rule", i)
    if len(known) > 512:
        raise ValueError("RESOURCE_LIMIT: closure exceeds 512 atoms")
    return known, steps


def propose(raw: bytes, query_raw: bytes, identity="text", revision="1", scope="default"):
    if len(raw) > 65536 or len(query_raw) > 8192:
        raise ValueError("RESOURCE_LIMIT: source or query too large")
    doc = parse_document(raw, source_id=identity, scope=scope)
    query = parse_query(query_raw, scope=scope)
    if not doc.accepted or doc.declarations or doc.definitions or doc.queries:
        raise ValueError("OUTSIDE_VERIFIED_LANGUAGE: requires ground facts/rules only")
    clauses = [(f.span.start, {"kind": "fact", "atom": literal(f.atom)}) for f in doc.facts]
    clauses += [(r.span.start, {"kind": "rule", "body": list(map(literal, r.body)),
                              "head": literal(r.head)}) for r in doc.rules]
    cs = [c for _, c in sorted(clauses, key=lambda pair: pair[0])]
    if not cs or len(cs) > 256 or any(len(c.get("body", [])) > 16 for c in cs):
        raise ValueError("OUTSIDE_VERIFIED_LANGUAGE: clause count or body bound")
    if "".join(map(render_clause, cs)).encode("utf-8") != raw:
        raise ValueError("OUTSIDE_VERIFIED_LANGUAGE: source must use exact canonical spacing and .\\n")
    qa = literal(query.atom)
    if ("هل " + render_atom(qa) + "؟\n").encode("utf-8") != query_raw:
        raise ValueError("OUTSIDE_VERIFIED_LANGUAGE: query must use exact canonical spelling")
    facts = [c["atom"] for c in cs if c["kind"] == "fact"]
    rules = [c for c in cs if c["kind"] == "rule"]
    known, steps = closure(facts, rules)
    signed = {key(a) for a in known}
    blocked = {a for a in signed if opposite(a) in signed}
    clean_facts = [a for a in facts if key(a) not in blocked]
    clean_rules = [r for r in rules if all(key(a) not in blocked for a in [*r["body"], r["head"]])]
    clean_known, clean_steps = closure(clean_facts, clean_rules)
    return {"law_id": LAW_ID,
            "source": {"identity": identity, "revision": revision, "scope": scope,
                       "text": raw.decode("utf-8")},
            "query_text": query_raw.decode("utf-8"), "clauses": cs, "query": qa,
            "known": known, "steps": steps, "clean_known": clean_known, "clean_steps": clean_steps}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("query", type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--source-id", default="text")
    p.add_argument("--revision", default="1")
    p.add_argument("--scope", default="default")
    args = p.parse_args()
    with args.source.open("rb") as f:
        raw = f.read(65537)
    with args.query.open("rb") as f:
        query = f.read(8193)
    result = propose(raw, query, args.source_id, args.revision, args.scope)
    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 1048576:
        raise ValueError("RESOURCE_LIMIT: certificate exceeds 1 MiB")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded + "\n", encoding="utf-8")
    print(json.dumps({"proposal_written": str(args.output), "verified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
