"""Read a bounded Arabic two-day length problem. No supplied roles or target labels.

The exact question selects the operation. A missing error bound is unknown.
Readings and source spans are rebuilt on each request, in original UTF-8 bytes.
"""
from hashlib import sha256
import re

from nabt.alphabet import ALPHABET_ID, parse_word
from tools import evidence_lifecycle_v1 as wire

PROFILE = "nabt.arabic-length-question.v1"
UNITS = {"مم": "mm", "سم": "cm", "م": "m"}
# Each reading explicitly names its specimen. No pronoun resolution is assumed.
OBSERVATION = re.compile(
    r"اليوم[ \t]+(?P<day>[0-9٠-٩]{1,4})[ \t]*:[ \t]*"
    r"طول[ \t]+(?P<object>القضيب|السلك|اللوح|الشريط|العمود|الحبل)[ \t]+"
    r"(?P<value>[0-9٠-٩]{1,6})(?:[ \t]*±[ \t]*(?P<error>[0-9٠-٩]{1,6}))?"
    r"(?:[ \t]+(?P<unit>مم|سم|م))?[ \t]*\.[ \t\n]*"
)
QUESTIONS = {
    ("هل", "زاد الطول"): "increase",
    ("هل", "ازداد الطول"): "increase",
    ("كم", "تغيرت القراءة الاسمية بالملليمتر"): "signed_delta",
    ("هل", "سببت الحرارة زيادة الطول"): "heating_cause",
}
MARKED_HEADS = {tuple(parse_word(marked)): plain for marked, plain in
                (("هَلْ", "هل"), ("كَمْ", "كم"))}
SUBTRACTION = re.compile(
    r"ناتج طرح القراءة (?P<subtrahend>الأولى|الثانية) من (?P<minuend>الأولى|الثانية) بالملليمتر"
)
QUESTION = re.compile(r"(?P<head>هل|كم|هَلْ|كَمْ)[ \t]+(?P<body>[^؟\n]+)؟")


def read(source):
    wire._text(source, "Arabic length question", 2048, content=True)
    raw = source.encode("utf-8")
    offsets = [0]
    for char in source:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))

    def witness(match, field):
        start, end = match.span(field)
        return {"text": match[field], "utf8_span": [offsets[start], offsets[end]]}

    trace = {"profile": PROFILE, "source_sha256": sha256(raw).hexdigest(),
             "observations": [], "question": None, "unread_from_byte": None,
             "world_truth_established": False}
    rows = []
    pos = 0
    while len(rows) < 2 and (match := OBSERVATION.match(source, pos)):
        spans = {k: witness(match, k) for k, value in match.groupdict().items() if value is not None}
        row = {k: int(match[k]) if match[k] is not None else None for k in ("day", "value", "error")}
        row.update(object=match["object"], unit=UNITS.get(match["unit"]))
        if row["error"] is not None and row["error"] > row["value"]:
            raise ValueError("Measurement uncertainty exceeds the recorded value")
        rows.append(row)
        trace["observations"].append(spans)
        pos = match.end()
    match = QUESTION.fullmatch(source, pos)
    if match:
        head = match["head"]
        cells = None
        if head not in ("هل", "كم"):
            cells = parse_word(head)
            head = MARKED_HEADS[cells]
        operation = QUESTIONS.get((head, match["body"]))
        trace["question"] = {"head": witness(match, "head"), "body": witness(match, "body"),
                             "operation": operation, "alphabet_id": ALPHABET_ID,
                             "head_cells": list(cells) if cells is not None else None}
        if head == "كم" and (roles := SUBTRACTION.fullmatch(source, *match.span("body"))):
            operation = "ordered_subtraction"
            trace["question"].update(operation=operation, operands={
                name: {**witness(roles, name), "row": 0 if roles[name] == "الأولى" else 1}
                for name in ("minuend", "subtrahend")
            })
    else:
        operation = None
    if operation is None:
        trace["unread_from_byte"] = offsets[pos]
    return rows, operation, trace


def missing(rows, *, precision):
    fields = ("unit", "error") if precision else ("unit",)
    result = [f"R{i}.{field}" for i, row in enumerate(rows, 1)
              for field in fields if row[field] is None]
    result.extend(f"R{i}" for i in range(len(rows) + 1, 3))
    return result
