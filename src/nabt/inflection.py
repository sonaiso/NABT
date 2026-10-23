"""Original/substitute inflection signs under independently supplied premises.

The Lean table does not classify a word. Sign, surface realization, local case
of a built form, and the role assigned by a qualified relation are distinct.
"""

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError, natural
from .words import CASES

LAW_ID = "nabt.inflection-evidence.v1"
EXPECTED_TABLE_SHA256 = "f8bc2f04fc1225a4f495d71a4c283289a3e8e9c74b9949008eb51e6445e7deb5"
SIGNS = ("damma", "fatha", "kasra", "sukun", "waw", "alif", "ya",
         "nun_retained", "nun_deleted", "weak_deleted")
MODES = ("overt", "estimated", "deletion")
ORIGINS = ("original", "substitute")
NUMBER_DOMAIN = "nabt.inflection.class-case.v1"


def installed_registry():
    try:
        raw = files("nabt").joinpath("data/inflection_evidence_table.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
            raise ValueError("table digest differs")
        table = json.loads(raw)
        if table["law_id"] != LAW_ID:
            raise ValueError("law domain differs")
        for key, size in (("rows", 45), ("diptote_rows", 16), ("nun_rows", 7),
                          ("relation_rows", 11), ("receipt_rows", 256), ("construction_rows", 2)):
            if type(table[key]) is not list or len(table[key]) != size:
                raise ValueError("inventory differs")
        return table
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed inflection law cannot be replayed",
                        status="DEFER") from error


def inflection_catalog():
    return {"law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
            "table": installed_registry(), "authority": "CONDITIONAL_SIGN_LAW_NOT_LEXICAL_TRUTH"}


def sign_candidates(classes, *, cases=None, al=0, idhafa=0):
    """Retain correlated class/case/sign alternatives; 0 evidence is unknown.

    Diptote genitive is kasra only with positive al/idafa evidence, and fatha
    only with both negative. Unknown evidence keeps both possible realizations
    without declaring either observed. No actual case or role is returned.
    """
    if type(classes) not in (list, tuple) or len(classes) > 15:
        raise NabtError("INVALID_DECLENSION_CLASSES", "Use a finite list of distinct class codes")
    for cls in classes:
        natural(cls, "declension_class", maximum=14)
    if len(set(classes)) != len(classes):
        raise NabtError("INVALID_DECLENSION_CLASSES", "Repeated classes are not evidence")
    if cases is None:
        cases = (0, 1, 2, 3)
    if type(cases) not in (list, tuple) or len(cases) > 4:
        raise NabtError("INVALID_CASES", "Use distinct case codes")
    for case in cases:
        natural(case, "grammatical_case", maximum=3)
    if len(set(cases)) != len(cases):
        raise NabtError("INVALID_CASES", "Repeated cases are not evidence")
    natural(al, "al_evidence", maximum=3)
    natural(idhafa, "idhafa_evidence", maximum=3)
    table = installed_registry()
    results = []
    for row in table["rows"]:
        if row["class"] not in classes or row["case"] not in cases:
            continue
        options = [row]
        context = None
        if row["class"] == 5 and row["case"] == 2:
            context_row = table["diptote_rows"][al + 4 * idhafa]
            context = context_row["status"]
            options = [{**row, **realization} for realization in context_row["realizations"]]
        for option in options:
            results.append({**deepcopy(option), "case_name": CASES[option["case"]],
                            "sign_name": SIGNS[option["sign"]], "mode_name": MODES[option["mode"]],
                            "origin_name": ORIGINS[option["origin"]], "context_status": context,
                            "authority": "CONDITIONAL_REALIZATION"})
    return results


def relation_candidate(label, *, kind, construction):
    """Conditional role law; an actual relation must be built by a source reader."""
    table = installed_registry()
    if type(label) is not str or not any(row["label"] == label for row in table["relation_rows"]):
        raise NabtError("INVALID_RELATION", "Use an installed relation label")
    if kind not in ("noun", "verb") or type(kind) is not str:
        raise NabtError("INVALID_KIND", "A relation needs a declared nominal/verbal reading")
    if construction not in (None, "built", "inflected"):
        raise NabtError("INVALID_CONSTRUCTION", "Construction is built, inflected or unknown")
    row = next(row for row in table["relation_rows"] if row["label"] == label)
    compatible = row["kind"] == (0 if kind == "noun" else 1)
    return {**row, "compatible": compatible, "case_name": CASES[row["case"]],
            "case_domain": None if construction is None else "local_case" if construction == "built" else "inflected_case",
            "activated": False, "authority": "CONDITIONAL_RELATION_NOT_AN_ATTACHMENT_WITNESS"}


def receipt_activated(mask):
    natural(mask, "relation_receipt", maximum=255)
    return installed_registry()["receipt_rows"][mask]["activated"]
