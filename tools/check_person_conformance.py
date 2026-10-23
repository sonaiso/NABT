#!/usr/bin/env python3
"""Fresh Lean/person registry correspondence, with an independent finite oracle.

This gate checks the complete conditional table. It does not verify QAC
annotation truth, acquire a lexical class, prove the Python source bridge,
or settle attachment, discourse reference, case, role or unrestricted Arabic.
It does not open independent evaluation material.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "src/nabt/data/person_evidence.json"

# Each row is one correlated reading, rather than the Cartesian product of
# separately observed persons/genders/numbers. Prefix/family is a premise.
PARADIGM = (
    ("1S", 1, 2, 0, "plain", "أ"),
    ("1P", 1, 2, 2, "plain", "ن"),
    ("2MS", 2, 0, 0, "plain", "ت"),
    ("2MD", 2, 0, 1, "dual", "ت"),
    ("2MP", 2, 0, 2, "masculine_plural", "ت"),
    ("2FS", 2, 1, 0, "feminine_singular", "ت"),
    ("2FD", 2, 1, 1, "dual", "ت"),
    ("2FP", 2, 1, 2, "feminine_plural", "ت"),
    ("3MS", 3, 0, 0, "plain", "ي"),
    ("3MD", 3, 0, 1, "dual", "ي"),
    ("3MP", 3, 0, 2, "masculine_plural", "ي"),
    ("3FS", 3, 1, 0, "plain", "ت"),
    ("3FD", 3, 1, 1, "dual", "ت"),
    ("3FP", 3, 1, 2, "feminine_plural", "ي"),
)
FAMILIES = ("plain", "dual", "masculine_plural", "feminine_singular", "feminine_plural")
SEPARATE = (
    ("هُوَ", 3, 0, 0), ("هُمَا", 3, 0, 1), ("هُمْ", 3, 0, 2),
    ("هِيَ", 3, 1, 0), ("هُمَا", 3, 1, 1), ("هُنَّ", 3, 1, 2),
    ("أَنْتَ", 2, 0, 0), ("أَنْتُمَا", 2, 0, 1), ("أَنْتُمْ", 2, 0, 2),
    ("أَنْتِ", 2, 1, 0), ("أَنْتُمَا", 2, 1, 1), ("أَنْتُنَّ", 2, 1, 2),
    ("أَنَا", 1, 2, 0), ("نَحْنُ", 1, 2, 2),
)
ATTACHED = (
    ("ي", "1S", "noun"), ("نِي", "1S", "verb"), ("نَا", "1P", "either"),
    ("كَ", "2MS", "either"), ("كِ", "2FS", "either"),
    ("كُمَا", "2MD", "either"), ("كُمَا", "2FD", "either"),
    ("كُمْ", "2MP", "either"), ("كُنَّ", "2FP", "either"),
    ("هُ", "3MS", "either"), ("هِ", "3MS", "either"), ("هَا", "3FS", "either"),
    ("هُمَا", "3MD", "either"), ("هُمَا", "3FD", "either"),
    ("هِمَا", "3MD", "either"), ("هِمَا", "3FD", "either"),
    ("هُمْ", "3MP", "either"), ("هِمْ", "3MP", "either"),
    ("هُنَّ", "3FP", "either"), ("هِنَّ", "3FP", "either"),
)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key: " + key)
        obj[key] = value
    return obj


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-JSON constant")))


def equal(actual, expected, message):
    if canonical(actual) != canonical(expected):
        raise ValueError(message)


def check_table(export):
    raw = TABLE.read_bytes()
    equal(export, parse(raw), "Complete fresh Lean export differs from installed JSON")
    equal(export["law_id"], "nabt.person-evidence.v1", "Law identity differs")
    equal(export["profiles"], [{"qac": q, "person": p, "gender": g, "number": n}
                               for q, p, g, n, _family, _prefix in PARADIGM], "Profile inventory differs")
    equal(export["prefixes"], ["أ", "ن", "ي", "ت"], "Prefix domain differs")
    expected = [{"family": family, "prefix": prefix,
                 "profiles": [q for q, _p, _g, _n, f, pre in PARADIGM if (f, pre) == (family, prefix)]}
                for family in FAMILIES for prefix in ("أ", "ن", "ي", "ت")]
    equal(export["prefix_rows"], expected, "Conditional family/prefix oracle differs")
    for row in export["families"]:
        # Family code order is presentation only; correlation is the set of
        # whole profile codes, not independent component intersections.
        equal(sorted(row["profiles"]), sorted(q for q, _p, _g, _n, f, _pre in PARADIGM if f == row["id"]),
              "Family profile inventory differs")
        equal(row["five_verb"], row["id"] in ("dual", "masculine_plural", "feminine_singular"),
              "Five-verb family scope differs")
    equal(export["separate_pronouns"], [{"surface": s, "person": p, "gender": g, "number": n}
                                       for s, p, g, n in SEPARATE], "Separate pronoun projection differs")
    equal(export["attached_forms"], [{"surface": s, "qac": p, "host": host} for s, p, host in ATTACHED],
          "Attached allomorph projection differs")
    sys.path.insert(0, str(ROOT / "src"))
    from nabt.person_evidence import installed_registry, person_catalog
    digest = sha256(raw).hexdigest()
    equal(installed_registry(), export, "Runtime registry differs")
    catalog = person_catalog()
    equal(catalog["table"], export, "Runtime catalog differs")
    equal(catalog["table_sha256"], digest, "Runtime catalog digest differs")
    equal(catalog["law_id"], export["law_id"], "Runtime law differs")
    return {"ok": True, "law_id": export["law_id"], "packaged_sha256": digest,
            "fresh_full_json_matches_packaged": True, "type_sensitive_comparison": True,
            "counts": {"correlated_profiles": 14, "family_prefix_rows": 20,
                       "separate_pronouns": 14, "attached_allomorphs": 20},
            "runtime_registry_correspondence": True, "runtime_source_reader_verified": False,
            "scope": "Finite conditional person/shape registry, not source truth, acquisition, reference, case or role."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build"], cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        result = subprocess.run([args.lake, "env", "lean", "--run", "ExportPersonEvidence.lean"],
                                cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        report = check_table(parse(result.stdout))
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
