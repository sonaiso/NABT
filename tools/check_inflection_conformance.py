#!/usr/bin/env python3
"""Compare a fresh Lean export with the complete installed inflection law.

The named grammatical families below are an independent reference fixture,
not calls into the Python reader or copies of its branch decisions. This gate
checks the finite conditional law, not lexical class discovery, grammatical
segmentation, relation acquisition, source truth or unrestricted Arabic.
No independent evaluation gold is opened.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "src/nabt/data/inflection_evidence_table.json"
SIGNS = ("damma", "fatha", "kasra", "sukun", "waw", "alif", "ya",
         "nun_retained", "nun_deleted", "weak_deleted")
MODES = ("overt", "estimated", "deletion")
ORIGINS = ("original", "substitute")
SURFACES = ("damma", "fatha", "kasra", "sukun", "waw", "alif", "ya",
            "ani", "ayni", "una", "ina")
CASE = {"nasb": 0, "raf": 1, "jarr": 2, "jazm": 3}
BASE_SIGNS = {"nasb": "fatha", "raf": "damma", "jarr": "kasra", "jazm": "sukun"}
NUNS = ("radical", "nominal_dual_plural", "five_verb_raf", "feminine_subject",
        "emphatic_direct", "emphatic_separated", "protective")
RECEIPT_BITS = ("identity_match", "rule_match", "active", "blocked", "support_present",
                "support_valid", "kind_match", "construction_known")

# Entries in each family are ordered nominative, accusative, then genitive for
# nouns or jussive for verbs. Class code is the existing Words ABI. Signs and
# surface endings are independent columns: weak deletion deliberately differs
# from the surviving vowel, and the noun nun is not a sign of nominative case.
FAMILIES = (
    ("iSahih", "noun", ("damma", "fatha", "kasra"),
     ("overt", "overt", "overt"), ("damma", "fatha", "kasra")),
    ("iSitta", "noun", ("waw", "alif", "ya"),
     ("overt", "overt", "overt"), ("waw", "alif", "ya")),
    ("iMuthanna", "noun", ("alif", "ya", "ya"),
     ("overt", "overt", "overt"), ("ani", "ayni", "ayni")),
    ("iJamM", "noun", ("waw", "ya", "ya"),
     ("overt", "overt", "overt"), ("una", "ina", "ina")),
    ("iJamF", "noun", ("damma", "kasra", "kasra"),
     ("overt", "overt", "overt"), ("damma", "kasra", "kasra")),
    ("iMamnu", "noun", ("damma", "fatha", "fatha"),
     ("overt", "overt", "overt"), ("damma", "fatha", "fatha")),
    ("iMaqsur", "noun", ("damma", "fatha", "kasra"),
     ("estimated", "estimated", "estimated"), ("alif", "alif", "alif")),
    ("iManqus", "noun", ("damma", "fatha", "kasra"),
     ("estimated", "overt", "estimated"), ("ya", "fatha", "ya")),
    ("fSahih", "verb", ("damma", "fatha", "sukun"),
     ("overt", "overt", "overt"), ("damma", "fatha", "sukun")),
    ("fKhamsaA", "verb", ("nun_retained", "nun_deleted", "nun_deleted"),
     ("overt", "deletion", "deletion"), ("ani", "alif", "alif")),
    ("fKhamsaW", "verb", ("nun_retained", "nun_deleted", "nun_deleted"),
     ("overt", "deletion", "deletion"), ("una", "waw", "waw")),
    ("fKhamsaY", "verb", ("nun_retained", "nun_deleted", "nun_deleted"),
     ("overt", "deletion", "deletion"), ("ina", "ya", "ya")),
    ("fMutalAlif", "verb", ("damma", "fatha", "weak_deleted"),
     ("estimated", "estimated", "deletion"), ("alif", "alif", "fatha")),
    ("fMutalW", "verb", ("damma", "fatha", "weak_deleted"),
     ("estimated", "overt", "deletion"), ("waw", "fatha", "damma")),
    ("fMutalY", "verb", ("damma", "fatha", "weak_deleted"),
     ("estimated", "overt", "deletion"), ("ya", "fatha", "kasra")),
)

RELATIONS = (
    ("preposition_object", "noun", "jarr"),
    ("idafa_complement", "noun", "jarr"),
    ("active_subject", "noun", "raf"),
    ("passive_subject", "noun", "raf"),
    ("direct_object", "noun", "nasb"),
    ("inna_subject", "noun", "nasb"),
    ("inna_predicate", "noun", "raf"),
    ("kana_subject", "noun", "raf"),
    ("kana_predicate", "noun", "nasb"),
    ("imperfect_subjunctive", "verb", "nasb"),
    ("imperfect_jussive", "verb", "jazm"),
)


def canonical(value):
    """Equality in JSON, keeping booleans, integers and floats distinct."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-JSON constant")))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expected_rows():
    result = []
    for cls, (_label, kind, signs, modes, surfaces) in enumerate(FAMILIES):
        cases = ("raf", "nasb", "jarr" if kind == "noun" else "jazm")
        for case, sign, mode, surface in zip(cases, signs, modes, surfaces):
            origin = "original" if sign == BASE_SIGNS[case] else "substitute"
            result.append({"class": cls, "case": CASE[case], "sign": SIGNS.index(sign),
                           "mode": MODES.index(mode), "origin": ORIGINS.index(origin),
                           "surface": SURFACES.index(surface)})
    return sorted(result, key=lambda row: (row["class"], row["case"]))


def expected_diptote(al, idhafa):
    # Four evidence states are sets of possible facts. Conflict has no model;
    # unknown has both. This independently evaluates the context relation.
    values = ((False, True), (True,), (False,), ())
    possible = {"kasra" if a or i else "fatha" for a, i in product(values[al], values[idhafa])}
    status = "conflict" if not possible else next(iter(possible)) if len(possible) == 1 else "pending"
    realizations = [{"sign": SIGNS.index(sign), "mode": MODES.index("overt"),
                     "origin": ORIGINS.index("original" if sign == "kasra" else "substitute"),
                     "surface": SURFACES.index(sign)}
                    for sign in ("fatha", "kasra") if sign in possible]
    return {"code": al + 4 * idhafa, "al": al, "idhafa": idhafa,
            "status": status, "realizations": realizations}


def verify_oracles(table):
    require(table["schema_version"] == 1 and type(table["schema_version"]) is int, "Wrong schema version")
    require(table["law_id"] == "nabt.inflection-evidence.v1", "Wrong inflection law")
    require(table["surface_law_id"] == "nabt.words.v1", "Wrong surface law")
    require(table["convention"] == "common_letter_substitution", "Undeclared sign convention")
    for key, expected in (("signs", SIGNS), ("modes", MODES), ("origins", ORIGINS),
                          ("case_domains", ("inflected_case", "local_case")),
                          ("receipt_bits", RECEIPT_BITS)):
        require(canonical(table[key]) == canonical(expected), "Named codes differ: " + key)
    expected = expected_rows()
    require(canonical(table["rows"]) == canonical(expected), "Sign/surface relation differs from grammatical families")
    require(len({(row["class"], row["case"]) for row in table["rows"]}) == 45,
            "Class/case relation is not unique")
    inverse_checks = 0
    for cls, surface in product(range(15), range(11)):
        actual = [r["case"] for r in table["rows"] if r["class"] == cls and r["surface"] == surface]
        reference = [r["case"] for r in expected if r["class"] == cls and r["surface"] == surface]
        require(canonical(actual) == canonical(reference), "Conditional surface ambiguity was lost")
        inverse_checks += 1

    diptotes = [expected_diptote(al, idhafa) for idhafa in range(4) for al in range(4)]
    require(canonical(table["diptote_rows"]) == canonical(diptotes), "Four-state diptote context differs")
    require(canonical(table["nun_rows"]) == canonical([{"code": i, "label": label} for i, label in enumerate(NUNS)]),
            "Nun inventory differs or has acquired case authority")
    require(canonical(table["relation_rows"]) == canonical([
        {"code": i, "label": label, "kind": ("noun", "verb").index(kind), "case": CASE[case]}
        for i, (label, kind, case) in enumerate(RELATIONS)]), "Conditional relation requirements differ")
    require(canonical(table["construction_rows"]) == canonical([
        {"construction": 0, "domain": 1}, {"construction": 1, "domain": 0}]),
        "Built/local and inflected cases were conflated")

    required = set(RECEIPT_BITS) - {"blocked"}
    receipts = []
    for mask in range(256):
        supplied = {name for i, name in enumerate(RECEIPT_BITS) if mask & (1 << i)}
        receipts.append({"mask": mask, "activated": required <= supplied and "blocked" not in supplied})
    require(canonical(table["receipt_rows"]) == canonical(receipts), "Receipt gate differs from named prerequisites")
    return {"sign_rows": 45, "conditional_surface_inverse_checks": inverse_checks,
            "diptote_contexts": 16, "nun_kinds": 7, "relation_requirements": 11,
            "receipt_masks": 256, "construction_domains": 2}


def expected_candidates(al, idhafa):
    """Independent family reference, with four-state genitive alternatives."""
    ordinary = [r for r in expected_rows() if (r["class"], r["case"]) != (5, 2)]
    diptote = expected_diptote(al, idhafa)
    conditional = [{"class": 5, "case": 2, **r} for r in diptote["realizations"]]
    values = sorted(ordinary + conditional, key=lambda r: (r["class"], r["case"], r["sign"]))
    case_names = {value: name for name, value in CASE.items()}
    return [{**r, "case_name": case_names[r["case"]], "sign_name": SIGNS[r["sign"]],
             "mode_name": MODES[r["mode"]], "origin_name": ORIGINS[r["origin"]],
             "context_status": diptote["status"] if (r["class"], r["case"]) == (5, 2) else None,
             "authority": "CONDITIONAL_REALIZATION"} for r in values]


def verify_runtime(export, digest):
    """Check the installed table adapters, without exercising a source reader.

    Expected results come from FAMILIES, finite evidence sets and named
    relation prerequisites above. The implementation's answer is never used
    to manufacture the oracle. Parser/replay/lexical authority is outside
    this correspondence gate.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from nabt.inflection import (inflection_catalog, installed_registry,
                                 receipt_activated, relation_candidate, sign_candidates)

    require(canonical(installed_registry()) == canonical(export), "Installed registry differs from Lean")
    catalog = inflection_catalog()
    require(catalog["law_id"] == export["law_id"] and catalog["table_sha256"] == digest,
            "Catalog law or table identity differs")
    require(canonical(catalog["table"]) == canonical(export), "Catalog table differs from Lean")
    require(catalog["authority"] == "CONDITIONAL_SIGN_LAW_NOT_LEXICAL_TRUTH", "Catalog authority differs")

    contexts = 0
    for al, idhafa in product(range(4), repeat=2):
        require(canonical(sign_candidates(list(range(15)), al=al, idhafa=idhafa)) ==
                canonical(expected_candidates(al, idhafa)), "Runtime sign alternatives differ")
        contexts += 1

    # All single class/case projections include impossible noun-jussive and
    # verb-genitive pairs. Reversing caller order must not change the canonical
    # order of correlated readings.
    projection_checks = 0
    reference = expected_candidates(0, 0)
    for cls, case in product(range(15), range(4)):
        expected = [r for r in reference if (r["class"], r["case"]) == (cls, case)]
        require(canonical(sign_candidates([cls], cases=[case])) == canonical(expected),
                "Runtime class/case projection differs")
        projection_checks += 1
    require(canonical(sign_candidates(list(reversed(range(15))), cases=[3, 2, 1, 0])) ==
            canonical(reference), "Runtime caller order changed correlated readings")
    require(sign_candidates([]) == [] and sign_candidates([0], cases=[]) == [],
            "Empty supplied domain created a realization")

    relation_checks = 0
    domains = {None: None, "built": "local_case", "inflected": "inflected_case"}
    for code, (label, required_kind, required_case) in enumerate(RELATIONS):
        for kind, construction in product(("noun", "verb"), domains):
            expected = {"code": code, "label": label, "kind": ("noun", "verb").index(required_kind),
                        "case": CASE[required_case], "compatible": kind == required_kind,
                        "case_name": required_case, "case_domain": domains[construction],
                        "activated": False, "authority": "CONDITIONAL_RELATION_NOT_AN_ATTACHMENT_WITNESS"}
            require(canonical(relation_candidate(label, kind=kind, construction=construction)) ==
                    canonical(expected), "Runtime relation requirement or authority differs")
            relation_checks += 1

    prerequisites = set(RECEIPT_BITS) - {"blocked"}
    for mask in range(256):
        supplied = {name for i, name in enumerate(RECEIPT_BITS) if mask & (1 << i)}
        expected = prerequisites <= supplied and "blocked" not in supplied
        actual = receipt_activated(mask)
        require(type(actual) is bool and actual == expected, "Runtime receipt predicate differs")
    return {"sign_contexts": contexts, "class_case_projections": projection_checks,
            "caller_order_checks": 1, "empty_domain_checks": 2,
            "relation_kind_construction_combinations": relation_checks, "receipt_masks": 256}


def check_table(export):
    raw = TABLE.read_bytes()
    packaged = parse_json(raw)
    require(canonical(export) == canonical(packaged), "Fresh complete Lean export differs from packaged JSON")
    counts = verify_oracles(export)
    # The existing domains are ABI references only. Their realization answers
    # are not used as the independent sign oracle above.
    words = parse_json((ROOT / "src/nabt/data/words.json").read_bytes())
    require(canonical(words["classes"]) == canonical([
        {"code": i, "kind": ("noun", "verb").index(family[1]), "label": family[0]}
        for i, family in enumerate(FAMILIES)]), "Existing class ABI differs")
    require(canonical(words["endings"]) == canonical([
        {"code": i, "label": label} for i, label in enumerate(SURFACES)]), "Existing ending ABI differs")
    require(canonical(words["case_codes"]) == canonical(CASE), "Existing case ABI differs")
    digest = sha256(raw).hexdigest()
    runtime_counts = verify_runtime(export, digest)
    return {"ok": True, "law_id": export["law_id"], "packaged_sha256": digest,
            "fresh_full_json_matches_packaged": True, "type_sensitive_comparison": True,
            "counts": counts, "runtime_correspondence": runtime_counts,
            "runtime_table_adapters_checked": True, "runtime_reader_checked": False,
            "scope": "Finite conditional law correspondence; not class/segmentation/relation acquisition, source truth or unrestricted Arabic."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build"], cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        result = subprocess.run([args.lake, "env", "lean", "--run", "ExportInflectionEvidence.lean"],
                                cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        report = check_table(parse_json(result.stdout))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stdout or "")
            print(error.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
