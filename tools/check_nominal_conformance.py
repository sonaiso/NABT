#!/usr/bin/env python3
"""Fresh Lean export, complete nominal tables, and bounded public projections.

The reference relations below use named grammatical dimensions and explicit
cardinal families; they do not read the runtime acceptance table as answers.
This gate certifies correspondence at the installed-law boundary, not an
unrestricted Arabic reader, truth of source assertions, or world cardinality.
The independent evaluation corpus is deliberately not loaded here.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt import nominal


GENDERS = ("masculine", "feminine")
NUMBERS = ("singular", "dual", "plural")
FORMS = ("singular", "dual", "sound_masculine_plural",
         "sound_feminine_plural", "broken_plural", "other_plural")
DEFINITENESS = ("indefinite", "definite")
CONDITIONS = (("gender", "masculine"), ("gender", "feminine"),
              ("number", "singular"), ("number", "dual"), ("number", "plural"),
              ("form", "sound_masculine_plural"), ("form", "sound_feminine_plural"),
              ("form", "broken_plural"), ("form", "other_plural"),
              ("definiteness", "definite"), ("definiteness", "indefinite"))
RECEIPT_BITS = ("source_match", "scope_match", "occurrence_match", "reading_match",
                "active", "blocked", "noun_domain")
MANQUS_BITS = ("noun", "inflected", "necessary_final_yaa", "preceding_kasra",
               "final_yaa_unshaddad")
WEAK_CLASSES = {frozenset(): "sound", frozenset({0}): "mithal",
                frozenset({1}): "ajwaf", frozenset({2}): "naqis",
                frozenset({0, 2}): "lafif_mafruq", frozenset({1, 2}): "lafif_maqrun",
                frozenset({0, 1}): "initial_adjacent_residual",
                frozenset({0, 1, 2}): "triple_weak_residual"}
# New Unicode projection fixture, not a claim of independently proved A116
# decoding. Identical dual surfaces intentionally retain both gender rows.
PRONOUNS = (("هُوَ", 3, 0, 0), ("هُمَا", 3, 0, 1), ("هُمْ", 3, 0, 2),
            ("هِيَ", 3, 1, 0), ("هُمَا", 3, 1, 1), ("هُنَّ", 3, 1, 2),
            ("أَنْتَ", 2, 0, 0), ("أَنْتُمَا", 2, 0, 1), ("أَنْتُمْ", 2, 0, 2),
            ("أَنْتِ", 2, 1, 0), ("أَنْتُمَا", 2, 1, 1), ("أَنْتُنَّ", 2, 1, 2),
            ("أَنَا", 1, 2, 0), ("نَحْنُ", 1, 2, 2))


def canonical(value):
    """Type-sensitive JSON equality: true, 1 and 1.0 remain different."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate export key: " + key)
        result[key] = value
    return result


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-JSON constant")))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def semantic_profiles():
    """A typed relational universe, independent of the exported accepts bits."""
    result = []
    for gender, form, definite in product(GENDERS, FORMS, DEFINITENESS):
        if gender == "feminine" and form == "sound_masculine_plural":
            continue
        result.append({"gender": gender, "form": form, "definiteness": definite,
                       "number": form if form in ("singular", "dual") else "plural"})
    return result


def encode_profile(p):
    g, f, d = GENDERS.index(p["gender"]), FORMS.index(p["form"]), DEFINITENESS.index(p["definiteness"])
    return {"code": 12 * g + 2 * f + d, "gender": g, "form": f, "definiteness": d,
            "number": NUMBERS.index(p["number"]),
            "accepts": [p[axis] == value for axis, value in CONDITIONS]}


def logical_candidates(codes):
    return [encode_profile(p) for p in semantic_profiles()
            if all(p[CONDITIONS[c][0]] == CONDITIONS[c][1] for c in codes)]


def logical_cardinal(q, gender):
    """Explicit semantic families; no reuse of production modulo branches."""
    same = {1, 2, 11, 12} | {ten + unit for ten in (20, 30, 40, 50, 60, 70, 80, 90) for unit in (1, 2)}
    opposite = set(range(3, 11)) | set(range(13, 20)) | {
        ten + unit for ten in (20, 30, 40, 50, 60, 70, 80, 90) for unit in range(3, 10)}
    independent = {20, 30, 40, 50, 60, 70, 80, 90, 100, 1000}
    require(q in same | opposite | independent, "Reference quantity outside its domain")
    require(not (same & opposite or same & independent or opposite & independent), "Reference families overlap")
    unit = gender if q in same else 1 - gender if q in opposite else None
    number = 1 if q == 2 else 2 if q in set(range(3, 11)) else 0
    case = "contextual" if q in {1, 2} else "genitive" if q in set(range(3, 11)) | {100, 1000} else "accusative"
    return {"quantity": q, "singular_gender": gender, "counted_number": number,
            "counted_case": case, "unit_gender": unit,
            "ten_gender": gender if q in set(range(11, 20)) else None}


def pronoun_dict(row):
    return dict(zip(("surface", "person", "gender", "number"), row))


def check_table(export):
    raw = (ROOT / "src/nabt/data/nominal_evidence.json").read_bytes()
    packaged = parse_json(raw)
    require(canonical(export) == canonical(packaged), "Fresh Lean export differs from packaged full JSON")
    require(canonical(export) == canonical(nominal.installed_registry()), "Runtime registry differs from fresh full JSON")
    require(export["law_id"] == nominal.LAW_ID == "nabt.nominal-evidence.v1", "Law identifier differs")
    require(sha256(raw).hexdigest() == nominal.EXPECTED_TABLE_SHA256, "Runtime registry pin differs")
    for name, expected in (("GENDERS", GENDERS), ("NUMBERS", NUMBERS), ("FORMS", FORMS), ("DEFINITENESS", DEFINITENESS)):
        require(canonical(getattr(nominal, name)) == canonical(expected), "Runtime named dimension differs: " + name)
    require(canonical(export["profile_rows"]) == canonical(logical_candidates(())),
            "Profile relation differs from independent grammatical dimensions")

    # All possible constraint subsets; duplicates/order additionally exercise
    # bounded public input lists rather than assuming a set-valued API.
    subset_checks = 0
    for width in range(12):
        for codes in combinations(range(11), width):
            require(canonical(nominal.nominal_candidates(codes)) == canonical(logical_candidates(codes)),
                    f"Public profile projection disagrees for {codes}")
            subset_checks += 1
    list_checks = deletion_checks = duplication_checks = 0
    for width in range(3):
        for codes in product(range(11), repeat=width):
            expected = logical_candidates(codes)
            actual = nominal.nominal_candidates(codes)
            require(canonical(actual) == canonical(expected), "Short constraint sequence differs")
            list_checks += 1
            for index, code in enumerate(codes):
                without = codes[:index] + codes[index + 1:]
                wider = nominal.nominal_candidates(without)
                require(canonical(wider) == canonical(logical_candidates(without)) and
                        {r["code"] for r in actual} <= {r["code"] for r in wider},
                        "Deleting evidence narrowed the profile relation")
                deletion_checks += 1
                duplicate = codes[:index] + (code,) + codes[index:]
                require(canonical(nominal.nominal_candidates(duplicate)) == canonical(actual),
                        "Duplicating evidence changed its authority")
                duplication_checks += 1

    require(canonical(export["receipt_bits"]) == canonical(RECEIPT_BITS), "Receipt bit interpretation differs")
    require(canonical([r["mask"] for r in export["receipt_rows"]]) == canonical(list(range(128))),
            "Receipt mask inventory is incomplete or reordered")
    receipt_checks = 0
    required = {"source_match", "scope_match", "occurrence_match", "reading_match", "active", "noun_domain"}
    for flags in product((False, True), repeat=7):
        present = {name for name, flag in zip(RECEIPT_BITS, flags) if flag}
        mask = sum(2 ** i for i, flag in enumerate(flags) if flag)
        expected = required <= present and "blocked" not in present
        require(canonical(export["receipt_rows"][mask]) == canonical({"mask": mask, "activated": expected}),
                "Receipt activation differs from named prerequisites")
        receipt_checks += 1

    quantities = list(range(1, 100)) + [100, 1000]
    expected_numerals = [logical_cardinal(q, g) for q in quantities for g in range(2)]
    require(canonical(export["numeral_rows"]) == canonical(expected_numerals),
            "Numeral table differs from independent cardinal families")
    for expected in expected_numerals:
        actual = nominal.number_rule(expected["quantity"], GENDERS[expected["singular_gender"]])
        projected = {key: actual[key] for key in expected}
        interpreted = {**expected,
                       "singular_gender": GENDERS[expected["singular_gender"]],
                       "counted_number": NUMBERS[expected["counted_number"]],
                       "unit_gender": None if expected["unit_gender"] is None else GENDERS[expected["unit_gender"]],
                       "ten_gender": None if expected["ten_gender"] is None else GENDERS[expected["ten_gender"]]}
        require(canonical(projected) == canonical(interpreted), "Public numeral rule differs")
        require(actual["numeral_kind"] == "cardinal" and
                all(actual[name] is None for name in ("actual_case", "actual_role", "ordinal", "world_cardinality")),
                "Conditional cardinal rule acquired sentence or world authority")

    require(canonical([r["mask"] for r in export["weak_rows"]]) == canonical(list(range(8))),
            "Weak-position inventory is incomplete or reordered")
    for positions, label in WEAK_CLASSES.items():
        mask = sum(2 ** i for i in positions)
        require(canonical(export["weak_rows"][mask]) == canonical({"mask": mask, "class": label}),
                "Weak-position row differs from explicit slot relation")
    root_checks = 0
    for letters in product("كوي", repeat=3):
        root = "".join(letters)
        positions = frozenset(i for i, radical in enumerate(letters) if radical in {"و", "ي"})
        actual = nominal.weak_root_profile(root)
        observed = {name: actual[name] for name in ("class", "mask", "weak_positions")}
        expected = {"class": WEAK_CLASSES[positions], "mask": sum(2 ** i for i in positions),
                    "weak_positions": sorted(positions)}
        require(canonical(observed) == canonical(expected),
                "Public weak-root projection differs")
        require(actual["attested_root"] is False and actual["nominal_manqus"] is None and
                actual["surface_realization"] is None, "Weak slots acquired lexical or realization authority")
        root_checks += 1

    require(canonical(export["manqus_bits"]) == canonical(MANQUS_BITS), "Manqus bit interpretation differs")
    require(canonical([r["mask"] for r in export["manqus_rows"]]) == canonical(list(range(32))),
            "Manqus complete-model inventory is incomplete or reordered")
    manqus_checks = 0
    for flags in product((False, True), repeat=5):
        witnessed = {name for name, flag in zip(MANQUS_BITS, flags) if flag}
        mask = sum(2 ** i for i, flag in enumerate(flags) if flag)
        expected = set(MANQUS_BITS) <= witnessed
        require(canonical(export["manqus_rows"][mask]) == canonical({"mask": mask, "accepted": expected}),
                "Manqus row differs from five independent defining properties")
        manqus_checks += 1

    expected_pronouns = [pronoun_dict(p) for p in PRONOUNS]
    require(canonical(export["pronoun_rows"]) == canonical(expected_pronouns),
            "New Unicode pronoun projection differs from its explicit inventory")
    require(export["pronoun_source_kind"] == "NEW_UNICODE_PROJECTION", "Projection provenance was lost")
    pronoun_checks = 0
    for p in expected_pronouns:
        reading = nominal.read_nominal(p["surface"])["occurrences"][0]["readings"][0]
        expected = [r for r in expected_pronouns if r["surface"] == p["surface"]]
        require(canonical(reading["pronoun_candidates"]) == canonical(expected),
                "Canonical pronoun reading lost an alternative or admitted a conflicting form")
        require(reading["actual_case"] is None and reading["actual_role"] is None and
                reading["declension_class"] is None, "Pronoun number granted a declension class")
        pronoun_checks += 1

    return {"ok": True, "law_id": nominal.LAW_ID, "table_sha256": sha256(raw).hexdigest(),
            "profile_rows": 22, "profile_constraint_subsets": subset_checks,
            "bounded_constraint_lists": list_checks, "max_source_list_length": 2,
            "single_deletion_checks": deletion_checks, "duplicate_constraint_checks": duplication_checks,
            "receipt_masks": receipt_checks, "cardinal_rows": len(expected_numerals),
            "weak_position_masks": len(WEAK_CLASSES), "bounded_root_projections": root_checks,
            "manqus_complete_models": manqus_checks, "pronoun_projection_rows": len(expected_pronouns),
            "canonical_pronoun_reader_checks": pronoun_checks,
            "scope": "Complete finite generated-law correspondence; public nominal/cardinal projections; "
                     "bounded weak-root and canonical-pronoun checks. Receipt and manqus truth tables are checked, "
                     "not unrestricted source qualification, partial-mark reader correctness, lexical attestation, "
                     "actual syntactic case, ordinal meaning, or world cardinality."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build"], cwd=ROOT / "formal", check=True,
                       capture_output=True, text=True)
        process = subprocess.run([args.lake, "env", "lean", "--run", "ExportNominalEvidence.lean"],
                                 cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        report = check_table(parse_json(process.stdout))
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
