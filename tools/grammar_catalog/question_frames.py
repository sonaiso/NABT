"""Finite clause interpretation. Models express possibilities inside the stated profile."""
from itertools import combinations, product

from .interpretation_chains import witness

# Each instrument is bound to the role of this particular event and its own arrival verb.
FRAMES = (
    ("سيفتح", "الحارس", "الباب", "المفتاح", "وصل"),
    ("سيكتب", "الطالب", "الدرس", "القلم", "وصل"),
    ("سيرسم", "الرسام", "الخط", "القلم", "وصل"),
    ("سيقيس", "الفني", "الطول", "المسطرة", "وصلت"),
)
SLOTS = ("instrument", "arrival_condition", "external_occurrence")
REQUIRED = {"instrument": (0,), "condition": (1,), "occurrence": (2,), "joint": (0, 1)}
WORLDS = tuple(product((False, True), repeat=len(SLOTS)))


def model_row(world):
    return dict(zip(SLOTS, world, strict=True))


def clauses(text):
    for verb, agent, patient, instrument, arrival in FRAMES:
        head = " ".join((verb, agent, patient))
        if not text.startswith(head):
            continue
        cues = {
            "ب" + instrument: (0, True),
            "دون استعمال " + instrument: (0, False),
            "إذا " + arrival + " " + instrument: (1, True),
            "دون اشتراط وصول " + instrument: (1, False),
        }
        position = len(head)
        observations = []
        while position < len(text) and len(observations) < 4:
            match = next((s for s in cues if text.startswith(" " + s, position)), None)
            if match is None:
                break
            start = position + 1
            position = start + len(match)
            axis, value = cues[match]
            observations.append({"axis": SLOTS[axis], "positive": value,
                                 "witness": witness(text, start, position)})
        if text[position:] in ("", "."):
            return {"event": witness(text, 0, len(head)), "verb": verb, "agent": agent,
                    "patient": patient, "candidate_instrument": instrument}, observations
    return None, []


def assess(required, rows):
    facts = {axis: {r["positive"] for r in rows if r["axis"] == axis} for axis in SLOTS}
    goal_axes = {SLOTS[i] for i in required}
    conflicts = {axis for axis, values in facts.items() if len(values) == 2}
    if conflicts & goal_axes:
        return "CONFLICT", None, []
    # Keep *all* consistent evidence, including facts outside the queried axes.
    # An unrelated contradiction is projected away and shown explicitly as null.
    worlds = [w for w in WORLDS if all(not facts[axis] or axis in conflicts or w[i] in facts[axis]
                                       for i, axis in enumerate(SLOTS))]
    representatives = {}
    for world in worlds:
        answer = all(world[i] for i in required)
        shown = model_row(world)
        for axis in conflicts:
            shown[axis] = None
        representatives.setdefault(answer, shown)
    if len(representatives) == 2:
        return "OPEN", None, list(representatives.values())
    answer, = representatives
    return ("SUPPORTED" if answer else "REFUTED"), answer, []


def interpret(text, operation):
    event, rows = clauses(text)
    if event is None:
        return {"status": "OUTSIDE_SOURCE", "value": None}
    required = REQUIRED[operation]
    used = [i for i, row in enumerate(rows) if SLOTS.index(row["axis"]) in required]
    background = [row for i, row in enumerate(rows) if i not in used]
    status, answer, alternatives = assess(required, rows)
    # Supports are inclusion-minimal with the lexical frame and question fixed.
    # Countermodels quantify over the projection onto the question's axes.
    minimal = []
    if status != "OPEN":
        for size in range(1, len(used) + 1):
            for subset in combinations(used, size):
                if any(set(s["evidence_ids"]).issubset(subset) for s in minimal):
                    continue
                if assess(required, background + [rows[i] for i in subset])[:2] != (status, answer):
                    continue
                deletions = []
                for removed in subset:
                    step = assess(required, background + [rows[i] for i in subset if i != removed])
                    deletions.append({"removed": removed, "status": step[0], "alternatives": step[2]})
                minimal.append({"evidence_ids": list(subset), "single_deletions": deletions})
    return {"status": status, "value": answer, "frame": event, "evidence": rows,
            "required_axes": [SLOTS[i] for i in required], "minimal_supports": minimal,
            "alternatives": alternatives, "irrelevant_evidence": [i for i in range(len(rows)) if i not in used],
            "conflicting_axes": [s for s in SLOTS if len({r["positive"] for r in rows if r["axis"] == s}) > 1],
            "model_scope": "ALL_UNCONTESTED_EVIDENCE_FIXED; UNRELATED_CONFLICTS_SHOWN_AS_NULL",
            "fixed_premises": ["reviewed future-transitive frame", "local attachment of each explicit cue"],
            "support_scope": "all minimal local cue sets for this answer given the frame and question"}
