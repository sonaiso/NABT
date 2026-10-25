"""Source-scoped weak-letter transformations over explicit morphophonemic cells.

These functions never license a word or acquire its grammatical/lexical premises.
They compute CONDITIONAL consequences of an explicitly supplied analysis. Source
bytes, original cells and the unestablished premises are retained in the result.
Cells use 29 written carriers and four states; long vowels remain abstract cells,
so this module does not choose final-alif spelling or infer an unvocalized root.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json
from itertools import product

from .errors import NabtError

LAW_ID = "nabt.classical-weak.v1"
RULE_IDS = (
    "WEAK-INITIAL-WAW", "WEAK-INITIAL-OPEN-EXCEPTION", "WEAK-WAW-TO-YA",
    "WEAK-YA-TO-WAW", "WEAK-MOVE-TO-ALIF", "WEAK-AFWAL-BLOCK",
    "WEAK-IFTIAL-RECIPROCAL", "WEAK-TWO-ELIGIBLE",
    "WEAK-NOMINAL-SUFFIX-BLOCK", "WEAK-VOWEL-TRANSFER",
)
INVENTORY_SHA256 = "6de39f04e6981ec646a9af98ed3ebb600d1c60bcd498ddfc925d6ba44664061d"
CARRIERS = frozenset("ءابتثجحخدذرزسشصضطظعغفقكلمنهوي")
VOWELS = ("a", "i", "u", "0")
CONTEXTS = ("ordinary", "simple_imperfect", "singular", "ful_plural",
            "afal_quality", "reciprocal_iftial", "nominal_augment", "verb",
            "exclamation", "geminate", "weak_final", "recorded_reverse")
POSITIONS = ("fa", "ayn", "lam")
LETTERS = ("waw", "ya", "other")
NEXTS = ("moving", "sakin", "alif", "double_ya", "end")
OPEN_ROOTS = ("wata", "wasia", "wadaa", "other")
CONTROL_DOMAINS = (
    (LETTERS, VOWELS, VOWELS, (False, True)),
    (OPEN_ROOTS, VOWELS, VOWELS, (False, True)),
    (LETTERS, VOWELS, VOWELS, (False, True)),
    (LETTERS, VOWELS, VOWELS, ("singular", "plural", "other"), (False, True)),
    (LETTERS, VOWELS, VOWELS, (False, True), POSITIONS, NEXTS, (False, True)),
    (LETTERS, VOWELS, VOWELS, (False, True)),
    (LETTERS, VOWELS, VOWELS, (False, True)),
    (LETTERS, LETTERS, VOWELS, VOWELS, VOWELS, ("regular", "ghaya", "other"), (False, True)),
    (LETTERS, VOWELS, VOWELS, (False, True)),
    (LETTERS, VOWELS, VOWELS, (False, True), (False, True)),
)


def replay_sources():
    """Replay installed inventory and source spans; caller hashes grant no trust."""
    directory = files("nabt").joinpath("data/source_evidence")
    try:
        raw = directory.joinpath("classical_rule_inventory_v1.json").read_bytes()
        if sha256(raw).hexdigest() != INVENTORY_SHA256:
            raise ValueError("weak inventory digest")
        inventory = json.loads(raw)
        wanted = [r for r in inventory["rules"] if r["rule_id"] in RULE_IDS]
        if {r["rule_id"] for r in wanted} != set(RULE_IDS):
            raise ValueError("weak inventory IDs")
        source_records = {s["source_id"]: s for s in inventory["sources"]}
        cache = {}
        for rule in wanted:
            for span in rule["source_spans"]:
                sid = span["source_id"]
                if sid not in cache:
                    source = source_records[sid]
                    data = directory.joinpath(source["local_file"]).read_bytes()
                    if sha256(data).hexdigest() != source["raw_sha256"]:
                        raise ValueError("weak source digest")
                    cache[sid] = data
                selected = cache[sid][span["start"]:span["end"]]
                if (sha256(selected).hexdigest() != span["sha256"] or
                        selected.decode("utf-8") != span["raw_text"]):
                    raise ValueError("weak source span")
        return {r["rule_id"]: deepcopy(r["source_spans"]) for r in wanted}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Weak-law source replay failed",
                        status="DEFER") from exc


def _invalid(message):
    raise NabtError("INVALID_WEAK_FRAME", message)


def _validate(frame):
    keys = {"cells", "index", "context", "position", "origin", "lexeme"}
    if type(frame) is not dict or set(frame) != keys:
        _invalid("Expected cells/index/context/position/origin/lexeme exactly")
    if type(frame["cells"]) not in (list, tuple) or not frame["cells"]:
        _invalid("Expected a nonempty cell sequence")
    if len(frame["cells"]) > 256:
        raise NabtError("RESOURCE_LIMIT", "Weak-law cell bound exceeded", status="DEFER")
    cells = []
    for cell in frame["cells"]:
        if (type(cell) not in (list, tuple) or len(cell) != 2 or
                type(cell[0]) is not str or cell[0] not in CARRIERS or
                type(cell[1]) is not str or cell[1] not in VOWELS):
            _invalid("A cell is a declared carrier and a/i/u/0")
        cells.append(tuple(cell))
    i = frame["index"]
    if type(i) is not int or not 0 <= i < len(cells):
        _invalid("Index must be an actual in-range integer")
    for key, choices in (("context", CONTEXTS), ("position", POSITIONS),
                         ("origin", ("original", "transferred"))):
        if type(frame[key]) is not str or frame[key] not in choices:
            _invalid("Invalid " + key)
    if type(frame["lexeme"]) is not str or len(frame["lexeme"]) > 64:
        _invalid("Lexeme must be an explicit short string")
    return tuple(cells), i


def _letter(c):
    return "waw" if c == "و" else "ya" if c == "ي" else "other"


def _moving(v):
    return v in ("a", "i", "u")


def control_frame(rule_id, frame):
    """Derive the finite Lean control frame from validated cells and premises."""
    if type(rule_id) is not str or rule_id not in RULE_IDS:
        raise NabtError("UNKNOWN_WEAK_RULE", "Unknown weak-law ID", status="DEFER")
    cells, i = _validate(frame)
    letter, vowel = cells[i]
    previous = cells[i - 1] if i else None
    following = cells[i + 1] if i + 1 < len(cells) else None
    # A missing predecessor is encoded by the nonmatching sukun state, while
    # shape guards below prevent it granting a transfer or initial deletion.
    pv = previous[1] if previous else "0"
    if following is None:
        nxt = "end"
    elif following[0] == "ا":
        nxt = "alif"
    elif (following == ("ي", "0") and i + 2 < len(cells) and
          cells[i + 2][0] == "ي" and _moving(cells[i + 2][1])):
        nxt = "double_ya"
    elif _moving(following[1]):
        nxt = "moving"
    else:
        nxt = "sakin"
    ctx, pos = frame["context"], frame["position"]
    original = frame["origin"] == "original"
    l = _letter(letter)
    initial_shape = (i == 1 and len(cells) == 4 and cells[0] == ("ي", "a") and
                     pos == "fa" and ctx == "simple_imperfect" and original)
    if rule_id == RULE_IDS[0]:
        return [0, l, vowel, following[1] if following else "0", initial_shape]
    if rule_id == RULE_IDS[1]:
        root = "".join(c[0] for c in cells[1:])
        named = {"وطء": "wata", "وسع": "wasia", "وضع": "wadaa"}.get(root, "other")
        return [1, named, vowel, following[1] if following else "0", initial_shape]
    if rule_id == RULE_IDS[2]:
        return [2, l, pv, vowel, original and previous is not None]
    if rule_id == RULE_IDS[3]:
        number = "singular" if ctx == "singular" else "plural" if ctx == "ful_plural" else "other"
        return [3, l, pv, vowel, number, original and previous is not None]
    if rule_id == RULE_IDS[4]:
        # These competing branches must use their own law; a local two-cell
        # rewrite cannot silently defeat the lexical/semantic blocker.
        ordinary = ctx in ("ordinary", "verb", "singular", "simple_imperfect")
        two_eligible = (pos == "ayn" and vowel == "a" and following is not None and
                        following[0] in "وي" and _moving(following[1]))
        return [4, l, pv, vowel, original, pos, nxt,
                ordinary and previous is not None and not two_eligible]
    if rule_id == RULE_IDS[5]:
        return [5, l, pv, vowel, ctx == "afal_quality" and pos == "ayn" and original]
    if rule_id == RULE_IDS[6]:
        visible_iftial = (i == 3 and len(cells) >= 5 and cells[0] == ("ا", "i") and
                         cells[1][1] == "0" and cells[2] == ("ت", "a"))
        return [6, l, pv, vowel, ctx == "reciprocal_iftial" and pos == "ayn" and
                original and nxt == "moving" and visible_iftial]
    if rule_id == RULE_IDS[7]:
        next_letter = _letter(following[0]) if following else "other"
        next_vowel = following[1] if following else "0"
        named_reverse = (frame["lexeme"] == "غاية" and i == 1 and
                         tuple(c[0] for c in cells) == ("غ", "ي", "ي", "ت") and
                         cells[0][1] == "a")
        profile = "regular" if ctx == "ordinary" else (
            "ghaya" if ctx == "recorded_reverse" and named_reverse else "other")
        following_final_blocked = (i + 2 < len(cells) and
                                  (cells[i + 2][0] == "ا" or
                                   (cells[i + 2] == ("ي", "0") and i + 3 < len(cells) and
                                    cells[i + 3][0] == "ي" and _moving(cells[i + 3][1]))))
        bound = pos == "ayn" and original and previous is not None and not following_final_blocked
        return [7, l, next_letter, pv, vowel, next_vowel, profile, bound]
    if rule_id == RULE_IDS[8]:
        suffix = (len(cells) >= i + 4 and cells[-2] == ("ا", "0") and cells[-1][0] == "ن")
        scope = (ctx == "nominal_augment" and pos == "ayn" and original and suffix and
                 frame["lexeme"] not in ("ماهان", "داران"))
        return [8, l, pv, vowel, scope]
    sound_previous = previous is not None and previous[0] not in "اوي"
    sound_final = following is not None and following[0] not in "اوي"
    repeated_final = (following is not None and i + 2 < len(cells) and
                      following[0] == cells[i + 2][0])
    return [9, l, pv, vowel, sound_previous,
            ctx == "verb" and pos == "ayn" and original and sound_final and not repeated_final]


def control_actions(control):
    """Independent Python realization of the finite control relation exported by Lean.

    This low-level function is a conformance utility, not a public licensing API.
    Controls passed by evaluate are derived by control_frame, never caller status.
    """
    if (type(control) not in (list, tuple) or not control or type(control[0]) is not int or
            not 0 <= control[0] < len(CONTROL_DOMAINS)):
        _invalid("Invalid finite weak control")
    tag, *x = control
    domains = CONTROL_DOMAINS[tag]
    if len(x) != len(domains) or any(type(v) is not type(d[0]) or v not in d for v, d in zip(x, domains)):
        _invalid("Invalid finite weak control fields")
    if tag == 0:
        l, v, n, scope = x
        return ["drop"] if l == "waw" and v == "0" and n == "i" and scope else []
    if tag == 1:
        root, v, n, scope = x
        return ["drop"] if root in OPEN_ROOTS[:3] and v == "0" and n == "a" and scope else []
    if tag == 2:
        l, p, v, scope = x
        return ["to_ya"] if l == "waw" and p == "i" and v == "0" and scope else []
    if tag == 3:
        l, p, v, number, scope = x
        if l != "ya" or p != "u" or v != "0" or not scope:
            return []
        return ["to_waw"] if number == "singular" else ["lower_previous"] if number == "plural" else []
    if tag == 4:
        l, p, v, original, pos, nxt, scope = x
        eligible_next = (pos == "ayn" and nxt == "moving") or (
            pos == "lam" and nxt not in ("alif", "double_ya"))
        return ["to_alif"] if l != "other" and p == "a" and _moving(v) and original and eligible_next and scope else []
    if tag == 5:
        l, p, v, scope = x
        return ["keep"] if l != "other" and p == "a" and _moving(v) and scope else []
    if tag == 6:
        l, p, v, scope = x
        if p != "a" or not _moving(v) or not scope:
            return []
        return ["keep"] if l == "waw" else ["to_alif"] if l == "ya" else []
    if tag == 7:
        first, second, p, v, nv, profile, scope = x
        if first == "other" or second == "other" or p != "a" or v != "a" or not _moving(nv) or not scope:
            return []
        return ["second_to_alif"] if profile == "regular" else ["to_alif"] if profile == "ghaya" else []
    if tag == 8:
        l, p, v, scope = x
        return ["keep"] if l != "other" and p == "a" and _moving(v) and scope else []
    if tag == 9:
        l, p, v, sound, scope = x
        return ["transfer"] if l != "other" and p == "0" and _moving(v) and sound and scope else []
    raise ValueError("Unknown weak control tag")


def finite_export_rows():
    """All finite control inputs in the native export's deterministic order."""
    controls = []
    for l, p, v, b in product(LETTERS, VOWELS, VOWELS, (False, True)):
        controls.extend(([0, l, v, p, b], [2, l, p, v, b], [5, l, p, v, b],
                         [6, l, p, v, b], [8, l, p, v, b]))
        controls.extend([3, l, p, v, n, b] for n in ("singular", "plural", "other"))
        controls.extend([9, l, p, v, s, b] for s in (False, True))
        controls.extend([4, l, p, v, o, q, n, b]
                        for o, q, n in product((False, True), POSITIONS, NEXTS))
        controls.extend([7, l, r, p, v, n, profile, b]
                        for r, n, profile in product(LETTERS, VOWELS, ("regular", "ghaya", "other")))
    controls.extend([1, r, v, n, b] for r, v, n, b in product(OPEN_ROOTS, VOWELS, VOWELS, (False, True)))
    return {"law_id": LAW_ID,
            "rows": [{"frame": f, "actions": control_actions(f)} for f in controls],
            "scope": "complete finite conditional control domain; not Arabic lexical membership"}


def _transform(cells, i, action):
    out = list(cells)
    if action == "drop":
        del out[i]
    elif action == "to_ya":
        out[i] = ("ي", out[i][1])
    elif action == "to_waw":
        out[i] = ("و", out[i][1])
    elif action == "to_alif":
        out[i] = ("ا", "0")
    elif action == "second_to_alif":
        out[i + 1] = ("ا", "0")
    elif action == "lower_previous":
        out[i - 1] = (out[i - 1][0], "i")
    elif action == "transfer":
        out[i - 1] = (out[i - 1][0], out[i][1])
        out[i] = (out[i][0], "0")
    elif action != "keep":
        raise ValueError("Unknown weak action")
    return [list(c) for c in out]


def evaluate(rule_id, frame):
    """Compute only the consequence of the supplied, still-unproved analysis."""
    control = control_frame(rule_id, frame)
    sources = replay_sources()[rule_id]
    cells, i = _validate(frame)
    actions = control_actions(control)
    return {
        "law_id": LAW_ID, "rule_id": rule_id,
        "status": "CONDITIONAL" if actions else "OUTSIDE_RULE_DOMAIN",
        "application_established": False, "free_text_analysis": False,
        "input": deepcopy(frame), "control": control,
        "alternatives": [{"action": a, "cells": _transform(cells, i, a)} for a in actions],
        "source_spans": sources,
        "unestablished_premises": ["root alignment and morphological position", "lexical and semantic class", "vowel origin"],
        "output_layer": "morphophonemic_cells_not_final_orthography",
        "global_arabic_completeness": False,
    }


def _frame(cells, index, *, context="ordinary", position="ayn", origin="original", lexeme=""):
    return dict(cells=[list(c) for c in cells], index=index, context=context,
                position=position, origin=origin, lexeme=lexeme)


def source_examples():
    """Authored vocalized analyses of cited examples, not a held-out benchmark."""
    return [
        {"id": "waada", "rule_id": RULE_IDS[0], "surface": "يعد", "frame": _frame([("ي","a"),("و","0"),("ع","i"),("د","u")],1,context="simple_imperfect",position="fa",lexeme="وعد"), "expected_action": "drop"},
        {"id": "wasia", "rule_id": RULE_IDS[1], "surface": "يسع", "frame": _frame([("ي","a"),("و","0"),("س","a"),("ع","u")],1,context="simple_imperfect",position="fa",lexeme="وسع"), "expected_action": "drop"},
        {"id": "mizan", "rule_id": RULE_IDS[2], "surface": "ميزان", "frame": _frame([("م","i"),("و","0"),("ز","a"),("ا","0"),("ن","u")],1,context="singular",position="fa",lexeme="ميزان"), "expected_action": "to_ya"},
        {"id": "muqin", "rule_id": RULE_IDS[3], "surface": "موقن", "frame": _frame([("م","u"),("ي","0"),("ق","i"),("ن","u")],1,context="singular",position="fa",lexeme="موقن"), "expected_action": "to_waw"},
        {"id": "bid", "rule_id": RULE_IDS[3], "surface": "بيض", "frame": _frame([("ب","u"),("ي","0"),("ض","u")],1,context="ful_plural",lexeme="بيض"), "expected_action": "lower_previous"},
        {"id": "qala", "rule_id": RULE_IDS[4], "surface": "قال", "frame": _frame([("ق","a"),("و","a"),("ل","a")],1,lexeme="قال"), "expected_action": "to_alif"},
        {"id": "awira", "rule_id": RULE_IDS[5], "surface": "عور", "frame": _frame([("ع","a"),("و","i"),("ر","a")],1,context="afal_quality",lexeme="عور"), "expected_action": "keep"},
        {"id": "ishtawaru", "rule_id": RULE_IDS[6], "surface": "اشتوروا", "frame": _frame([("ا","i"),("ش","0"),("ت","a"),("و","a"),("ر","u"),("و","0"),("ا","0")],3,context="reciprocal_iftial",lexeme="اشتوروا"), "expected_action": "keep"},
        {"id": "ibtayu", "rule_id": RULE_IDS[6], "surface": "ابتاعوا", "frame": _frame([("ا","i"),("ب","0"),("ت","a"),("ي","a"),("ع","u"),("و","0"),("ا","0")],3,context="reciprocal_iftial",lexeme="ابتاعوا"), "expected_action": "to_alif"},
        {"id": "hawa", "rule_id": RULE_IDS[7], "surface": "الهوى", "frame": _frame([("ه","a"),("و","a"),("ي","u")],1,lexeme="هوى"), "expected_action": "second_to_alif"},
        {"id": "ghaya", "rule_id": RULE_IDS[7], "surface": "غاية", "frame": _frame([("غ","a"),("ي","a"),("ي","a"),("ت","u")],1,context="recorded_reverse",lexeme="غاية"), "expected_action": "to_alif"},
        {"id": "jawalan", "rule_id": RULE_IDS[8], "surface": "جولان", "frame": _frame([("ج","a"),("و","a"),("ل","a"),("ا","0"),("ن","u")],1,context="nominal_augment",lexeme="جولان"), "expected_action": "keep"},
        {"id": "yaqumu", "rule_id": RULE_IDS[9], "surface": "يقوم", "frame": _frame([("ي","a"),("ق","0"),("و","u"),("م","u")],2,context="verb",lexeme="يقوم"), "expected_action": "transfer"},
    ]
