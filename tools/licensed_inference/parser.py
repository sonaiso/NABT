"""Untrusted proposer for the finite explicit-subject Arabic grammar.

Only the listed whole-token spellings are aliases. Passive, causative or
contradictory vocalizations are never normalized into an accepted verb.
Lean independently parses the original bytes before checking a certificate.
"""
from __future__ import annotations

import hashlib
import re

ALIASES = {
    "سار": "سار", "سَارَ": "سار", "لم": "لم", "لَمْ": "لم",
    "يسر": "يسر", "يَسِرْ": "يسر", "عرف": "عرف", "عَرَفَ": "عرف",
    "يعرف": "يعرف", "يَعْرِفْ": "يعرف", "زيد": "زيد", "زَيْدٌ": "زيد",
    "عمرو": "عمرو", "عَمْرٌو": "عمرو", "الحق": "الحق", "الْحَقَّ": "الحق",
    "إن": "إن", "إِنْ": "إن", "أمامك": "أمامك", "أَمَامَكَ": "أمامك",
    "خلف": "خلف", "خَلْفَ": "خلف", "الدار": "الدار", "الدَّارِ": "الدار",
    "هل": "هل", "هَلْ": "هل",
}
NAMES = {"زيد", "عمرو"}
ASCII_SPACE = " \t\r\n"
WORD = re.compile(r"[^ \t\r\n]+")


def literal(predicate, arguments, positive=True):
    return {"predicate": predicate, "arguments": arguments, "positive": positive}


def tokens(text):
    raw = [m.group() for m in WORD.finditer(text)]
    return [ALIASES.get(word, word) for word in raw]


def motion(words):
    positive = True
    if words[:2] == ["لم", "يسر"]:
        positive, rest = False, words[2:]
    elif words[:1] == ["سار"]:
        rest = words[1:]
    else:
        return None
    if not rest or rest[0] not in NAMES:
        return None
    modifiers = {(): None, ("أمامك",): "أمامك", ("خلف", "الدار"): "خلف_الدار",
                 ("أمامك", "خلف", "الدار"): "أمامك_خلف_الدار"}
    if tuple(rest[1:]) not in modifiers:
        return None
    location = modifiers[tuple(rest[1:])]
    return literal("سار", [rest[0]] + ([location] if location else []), positive)


def knowledge(words):
    positive = True
    if words[:2] == ["لم", "يعرف"]:
        positive, rest = False, words[2:]
    elif words[:1] == ["عرف"]:
        rest = words[1:]
    else:
        return None
    if len(rest) == 2 and rest[0] in NAMES and rest[1] == "الحق":
        return literal("عرف", [rest[0], "الحق"], positive)
    return None


def read_literal(words):
    return motion(words) or knowledge(words)


def clause(words):
    if words.count("إن") != 1:
        atom = read_literal(words)
        return ({"kind": "fact", "atom": atom}, None) if atom else (None, "OUTSIDE_FRAGMENT")
    index = words.index("إن")
    if index:
        head = motion(words[:index])
        body = knowledge(words[index + 1:])
        if head and body:
            return {"kind": "rule", "body": [body], "head": head}, None
        if head and words[index + 1:] in (["عرف", "الحق"], ["لم", "يعرف", "الحق"]):
            return {"kind": "unresolved_conditional", "head": head,
                    "antecedent_subject": None, "premise_asserted": False}, "UNRESOLVED_REFERENCE"
        return None, "OUTSIDE_FRAGMENT"
    # Exact lexical classes fix the boundary; none is guessed from punctuation.
    for length in (3, 4):
        body, head = knowledge(words[1:1 + length]), motion(words[1 + length:])
        if body and head:
            return {"kind": "rule", "body": [body], "head": head}, None
    for prefix in (["عرف", "الحق"], ["لم", "يعرف", "الحق"]):
        if words[1:1 + len(prefix)] == prefix:
            head = motion(words[1 + len(prefix):])
            if head:
                return {"kind": "unresolved_conditional", "head": head,
                        "antecedent_subject": None, "premise_asserted": False}, "UNRESOLVED_REFERENCE"
    return None, "OUTSIDE_FRAGMENT"


def span(raw, start, end):
    return {"start_byte": start, "end_byte": end, "sha256": hashlib.sha256(raw[start:end]).hexdigest(),
            "raw_text": raw[start:end].decode("utf-8")}


def read_source(text):
    raw = text.encode()
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode()))
    segments, clauses, errors = [], [], []
    parts = text.split(".")
    if parts and not parts[-1].strip(ASCII_SPACE):
        parts.pop()
    cursor = 0
    for part in parts:
        start, end = cursor, cursor + len(part)
        entry = {"span": span(raw, offsets[start], offsets[end]), "tokens": []}
        for token in WORD.finditer(part):
            entry["tokens"].append({"span": span(raw, offsets[start + token.start()], offsets[start + token.end()]),
                                    "canonical": ALIASES.get(token.group(), token.group())})
        parsed, error = clause(tokens(part))
        if not part.strip(ASCII_SPACE):
            parsed, error = None, "OUTSIDE_FRAGMENT"
        entry.update(proposal=parsed, status="PROPOSED" if error is None else "UNKNOWN", reason=error)
        segments.append(entry)
        if error:
            errors.append(error)
        elif parsed:
            clauses.append(parsed)
        cursor = end + 1
    if not parts:
        errors.append("OUTSIDE_FRAGMENT")
    error = "OUTSIDE_FRAGMENT" if "OUTSIDE_FRAGMENT" in errors else errors[0] if errors else None
    return {"segments": segments, "clauses": clauses if error is None else None,
            "status": "PROPOSED" if error is None else "UNKNOWN", "reason": error}


def read_query(text):
    value = text.strip(ASCII_SPACE)
    if not value.endswith("؟"):
        return None
    words = tokens(value[:-1])
    return read_literal(words[1:]) if words[:1] == ["هل"] else None
