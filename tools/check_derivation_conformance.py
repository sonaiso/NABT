#!/usr/bin/env python3
"""Compare fresh Lean registry with installed bytes and bounded inverse oracles.

The authored, frozen source examples live in derivation_evaluation.py. These
checks address the registry/runtime boundary and complete three-cell paradigm
algebra; they are not a measurement of natural Arabic coverage.
"""

import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt import derivation
from nabt.verb_paradigm import availability_candidates


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate export key: " + key)
        result[key] = value
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_table(export):
    installed = derivation.installed_registry()
    require(canonical(export) == canonical(installed), "Fresh Lean export differs from installed registry")
    patterns = export["patterns"]
    observed_ids = [p["id"] for p in patterns]
    require(len(set(observed_ids)) == len(observed_ids), "Pattern identities collapsed")
    require(all(derivation.RADICALS.count(c) == 1 for c in derivation.RADICALS)
            and len(derivation.RADICALS) == 28, "Radical alphabet is not 28 distinct letters")
    # The language is finite for a fixed arity. Build a bounded independent
    # preimage relation by joining each slot column with a small root universe.
    # Compare the production inverse with that relation, including non-images.
    preimages = negative_checks = root_domain_checks = 0
    for pattern in patterns:
        universe = list(product("كتب", repeat=pattern["arity"]))
        relation = {}
        for columns in universe:
            root = "".join(columns)
            if pattern["root_domain"] == "sound_triliteral_distinct" and columns[1] == columns[2]:
                continue
            rendered_columns = [columns[t] if type(t) is int else t for t in pattern["tokens"]]
            surface = "".join(rendered_columns)
            relation.setdefault(surface, set()).add(root)
        for surface, expected in relation.items():
            actual = derivation._recover(pattern, surface)
            require(expected == {actual}, "Inverse disagrees with bounded preimage relation: " + pattern["id"])
            require(derivation.generate_derivation(actual, pattern["id"])["surface"] == surface,
                    "Public generation disagrees with bounded template relation")
            preimages += 1
            # Neither ignoring a literal nor accepting an extra character is
            # an inverse of this entire pattern.
            literal_positions = [i for i, token in enumerate(pattern["tokens"]) if type(token) is str]
            for position in literal_positions:
                altered = surface[:position] + "x" + surface[position + 1:]
                require(derivation._recover(pattern, altered) is None, "Inverse skipped a mismatching literal")
                negative_checks += 1
            for altered in (surface + "ب", surface[:-1]):
                require(derivation._recover(pattern, altered) is None, "Inverse ignored complete length")
                negative_checks += 1
        for invalid in ("ا" * pattern["arity"], "x" * pattern["arity"], "َ" * pattern["arity"]):
            surface = "".join(invalid[t] if type(t) is int else t for t in pattern["tokens"])
            require(derivation._recover(pattern, surface) is None, "Invalid radical domain was accepted")
            root_domain_checks += 1
    # A separate adversarial template exercises repeated slots even when a
    # catalog writes gemination with a literal shadda rather than repetition.
    repeat = {"arity": 2, "tokens": [0, "َ", 1, "ْ", 1, "َ"], "root_domain": "radicals28_shape_only"}
    require(derivation._recover(repeat, "كَتْتَ") == "كت", "Repeated slot positive fails")
    require(derivation._recover(repeat, "كَتْبَ") is None, "Repeated slot equality was not enforced")

    # Explicit truth-set oracle; this is not copied from Lean's count or the
    # Python row lookup. Unobserved is never absent.
    model_sets = {1: {"past"}, 2: {"imperfect"}, 3: {"past", "imperfect"},
                  4: {"imperative"}, 5: {"past", "imperative"},
                  6: {"imperfect", "imperative"}, 7: {"past", "imperfect", "imperative"}}
    model_classes = {1: "jamid", 2: "jamid", 3: "partial", 4: "jamid", 5: "partial", 6: "partial", 7: "full"}
    named = ((1, "past"), (2, "imperfect"), (4, "imperative"))
    require(len(export["paradigm_rows"]) == 64, "Paradigm law is not complete")
    paradigm_checks = 0
    for positive, negative in product(range(8), repeat=2):
        present = {name for bit, name in named if positive & bit}
        absent = {name for bit, name in named if negative & bit}
        models = [model for model, available in model_sets.items()
                  if present <= available and not available & absent]
        classes = [c for c in ("jamid", "partial", "full")
                   if any(model_classes[m] == c for m in models)]
        expected = {"positive_mask": positive, "negative_mask": negative,
                    "models": models, "categories": classes}
        require(canonical(availability_candidates(positive, negative)) == canonical(expected),
                "Paradigm row differs from independent truth-set oracle")
        paradigm_checks += 1
    raw = (ROOT / "src/nabt/data/derivation_patterns.json").read_bytes()
    return {"ok": True, "law_id": derivation.LAW_ID, "table_sha256": sha256(raw).hexdigest(),
            "patterns": len(patterns), "bounded_preimage_checks": preimages,
            "literal_and_length_counterexamples": negative_checks,
            "root_domain_counterexamples": root_domain_checks, "repeated_slot_checks": 2,
            "paradigm_truth_set_rows": paradigm_checks,
            "scope": "Fresh Lean registry equality; bounded inverse refinement; complete conditional availability algebra. "
                     "No unrestricted Arabic reader, lexical classification, weak-form realization, or linguistic completeness claim."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build"], cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        process = subprocess.run([args.lake, "env", "lean", "--run", "ExportDerivation.lean"],
                                 cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        exported = json.loads(process.stdout, object_pairs_hook=unique_object,
                              parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Invalid JSON constant")))
        report = check_table(exported)
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
