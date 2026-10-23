#!/usr/bin/env python3
"""Check complete Lean/Python discourse-law correspondence, not a reader.

The independent finite oracle uses required sets and truth valuations. It
opens no evaluation cases. Source replay validates byte windows; it does not
certify the interpretation or truth of a new utterance.
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
TABLE = ROOT / "src/nabt/data/discourse_evidence.json"
FEATURES = (None, 0, 1, 2, 3)
STATUSES = ("possible", "confirmed", "conflict")
ORIGINS = ("named", "antecedent", "speaker", "addressee", "deictic", "relative_return")
FORCES = ("ASSERT", "QUESTION", "COMMAND", "PROHIBITION", "WISH", "HOPE", "VOCATIVE", "AMBIGUOUS", "QUOTED")
POLARITIES = ("positive", "negative")
CONNECTORS = ("AND", "OR", "XOR", "IMPLIES")
REF_BITS = ("origin_licensed", "identity_bound", "source_supported", "scope_allowed",
            "quote_allowed", "order_licensed", "return_licensed")
ASSERT_BITS = ("licensed_syntax", "scope_complete", "references_complete", "qualifiers_preserved",
               "nonquoted", "source_supported")
CLAIM_FIELDS = ("predicate", "arguments", "polarity", "tense", "time", "place", "restriction")
CAUSE_BITS = ("relation_licensed", "source_supported", "scope_complete", "endpoints_resolved")


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key: " + key)
        value[key] = item
    return value


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-JSON number")))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal(actual, expected, label):
    require(canonical(actual) == canonical(expected), label)


def flags(mask, names):
    return {name: bool(mask & (1 << i)) for i, name in enumerate(names)}


def feature_oracle(a, b):
    return "possible" if None in (a, b) else "confirmed" if a == b else "conflict"


def combine_oracle(a, b):
    priority = {"confirmed": 0, "possible": 1, "conflict": 2}
    return max((a, b), key=priority.__getitem__)


def ref_oracle(origin, compatibility, mask):
    required = set(REF_BITS[:5])
    required |= {"order_licensed"} if origin == "antecedent" else set()
    required |= {"return_licensed"} if origin == "relative_return" else set()
    present = {name for name, active in flags(mask, REF_BITS).items() if active}
    return compatibility != "conflict" and required <= present


def selection_oracle(count, closed, confirmed):
    if not closed:
        return "OPEN_SCOPE"
    return {0: "NO_CANDIDATE", 1: "RESOLVED" if confirmed else "UNRESOLVED_FEATURES",
            2: "AMBIGUOUS"}[count]


def truth_oracle(operator, left, right):
    # Enumerate satisfying valuations; no supplied causal relation is encoded.
    satisfying = {"AND": {(True, True)},
                  "OR": {(False, True), (True, False), (True, True)},
                  "XOR": {(False, True), (True, False)},
                  "IMPLIES": {(False, False), (False, True), (True, True)}}
    return (left, right) in satisfying[operator]


def check_table(export):
    packaged_raw = TABLE.read_bytes()
    equal(export, parse(packaged_raw), "Complete fresh Lean export differs from installed JSON")
    require(type(export["schema_version"]) is int and export["schema_version"] == 1, "Wrong schema")
    require(export["law_id"] == "nabt.discourse-evidence.v1", "Wrong law domain")
    for key, expected in (("feature_values", FEATURES), ("compatibilities", STATUSES),
                          ("reference_origins", ORIGINS), ("reference_bits", REF_BITS),
                          ("forces", FORCES), ("assertion_bits", ASSERT_BITS),
                          ("polarities", POLARITIES), ("connectors", CONNECTORS),
                          ("claim_fields", CLAIM_FIELDS), ("causal_bits", CAUSE_BITS)):
        equal(export[key], expected, "Named domain differs: " + key)
    expected = {
        "role_rows": [{"label": name, "case": case} for name, case in
                      (("nominal_subject", 1), ("nominal_predicate", 1), ("time_adverb", 0), ("place_adverb", 0), ("imperfect_indicative", 1))],
        "feature_rows": [{"left": a, "right": b, "status": feature_oracle(a, b)}
                         for a, b in product(FEATURES, repeat=2)],
        "combine_rows": [{"left": a, "right": b, "status": combine_oracle(a, b)}
                         for a, b in product(STATUSES, repeat=2)],
        "reference_rows": [{"origin": origin, "compatibility": status, "mask": mask,
                            "allowed": ref_oracle(origin, status, mask)}
                           for origin, status, mask in product(ORIGINS, STATUSES, range(128))],
        "selection_rows": [{"count_class": count, "closed_scope": closed, "all_confirmed": confirmed,
                            "status": selection_oracle(count, closed, confirmed)}
                           for count, closed, confirmed in product(range(3), (False, True), (False, True))],
        "assertion_rows": [{"force": force, "mask": mask, "allowed": force == "ASSERT" and mask == 63}
                           for force, mask in product(FORCES, range(64))],
        "negation_rows": [{"input": "positive", "output": "negative"}, {"input": "negative", "output": "positive"}],
        "truth_rows": [{"operator": operator, "left": left, "right": right,
                        "value": truth_oracle(operator, left, right)}
                       for operator, left, right in product(CONNECTORS, (False, True), (False, True))],
        "coordination_rows": [{"operator": operator, "polarity": polarity,
                               "project_branches": operator == "AND" and polarity == "positive"}
                              for operator, polarity in product(CONNECTORS, POLARITIES)],
        "claim_projection_rows": [{"mask": mask, "allowed": mask == 127} for mask in range(128)],
        "causal_rows": [{"mask": mask, "allowed": mask == 15} for mask in range(16)],
    }
    for key, rows in expected.items():
        equal(export[key], rows, "Finite conditional relation differs: " + key)

    sys.path.insert(0, str(ROOT / "src"))
    from nabt import discourse_laws as laws
    equal(laws.installed_registry(), export, "Runtime installed registry differs")
    require(laws.EXPECTED_TABLE_SHA256 == sha256(packaged_raw).hexdigest(), "Runtime table pin differs")
    for row in expected["role_rows"]:
        equal(laws.role_case(row["label"]), row["case"], "Runtime role requirement differs")
    for row in expected["feature_rows"]:
        equal(laws.feature_compatibility(row["left"], row["right"]), row["status"], "Runtime feature relation differs")
    for row in expected["combine_rows"]:
        equal(laws.combine_compatibility([row["left"], row["right"]]), row["status"], "Runtime feature combination differs")
    equal(laws.combine_compatibility([]), "confirmed", "Empty constraints are not vacuous")
    for row in expected["reference_rows"]:
        equal(laws.reference_allowed(row["origin"], row["compatibility"], **flags(row["mask"], REF_BITS)),
              row["allowed"], "Runtime reference gate differs")
    for row in expected["selection_rows"]:
        equal(laws.selection_status(row["count_class"], closed_scope=row["closed_scope"], all_confirmed=row["all_confirmed"]),
              row["status"], "Runtime reference selection differs")
    for count in (3, 32, 4096):
        equal(laws.selection_status(count, closed_scope=True, all_confirmed=True), "AMBIGUOUS", "Multiplicity was collapsed")
    for row in expected["assertion_rows"]:
        equal(laws.assertion_allowed(row["force"], **flags(row["mask"], ASSERT_BITS)), row["allowed"], "Runtime assertion gate differs")
    for row in expected["negation_rows"]:
        equal(laws.negate_polarity(row["input"]), row["output"], "Runtime signed negation differs")
    for row in expected["truth_rows"]:
        equal(laws.connective_value(row["operator"], row["left"], row["right"]), row["value"], "Runtime valuation differs")
    for row in expected["coordination_rows"]:
        equal(laws.coordination_projection(row["operator"], row["polarity"]), row["project_branches"], "Runtime branch projection differs")
    for row in expected["claim_projection_rows"]:
        equal(laws.claim_projection_allowed(**{key + "_equal": value for key, value in flags(row["mask"], CLAIM_FIELDS).items()}),
              row["allowed"], "Runtime qualifier preservation differs")
    for row in expected["causal_rows"]:
        equal(laws.causal_allowed(**flags(row["mask"], CAUSE_BITS)), row["allowed"], "Runtime causal witness gate differs")
    policy = laws.replay_discourse_policy()
    require(len(policy["rules"]) == 22, "Source policy inventory differs")
    return {"ok": True, "law_id": export["law_id"], "packaged_sha256": sha256(packaged_raw).hexdigest(),
            "fresh_full_json_matches_packaged": True, "type_sensitive_comparison": True,
            "runtime_table_adapters_checked": True, "runtime_reader_checked": False,
            "counts": {key: len(rows) for key, rows in expected.items()},
            "source_policy_sha256": policy["policy_sha256"], "source_passages_replayed": len(policy["rules"]),
            "scope": "Conditional algebra correspondence and exact source windows; not acquisition, external reference, free-text correctness or external truth."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build", "Nabt.DiscourseEvidence"], cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        result = subprocess.run([args.lake, "env", "lean", "--run", "ExportDiscourseEvidence.lean"],
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
