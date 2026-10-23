#!/usr/bin/env python3
"""Complete Lean/Python construction-law correspondence, not a parser metric.

Independent finite oracles encode the licensed role and evidence contracts.
No evaluation gold is opened. All source reading, sense/attachment acquisition,
world truth and completeness of a discourse analysis are outside this check.
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
TABLE = ROOT / "src/nabt/data/construction_evidence.json"
FAMILIES = ("kana", "inna", "zanna", "kada")
ROLE_CASES = {
    "kana_subject": 1, "kana_predicate": 0, "inna_subject": 0, "inna_predicate": 1,
    "zanna_subject": 1, "zanna_object1": 0, "zanna_object2": 0,
    "kada_subject": 1, "kada_predicate": 0, "idafa_complement": 2,
    "naat": None, "hal": 0, "tamyiz": 0, "badal": None, "tawkeed": None,
    "time_adverb": 0, "place_adverb": 0,
}
OPERATOR_ROLES = {
    "kana": ("kana_subject", "kana_predicate"),
    "inna": ("inna_subject", "inna_predicate"),
    "zanna": ("zanna_subject", "zanna_object1", "zanna_object2"),
    "kada": ("kada_subject", "kada_predicate"),
}
INHERITED = (None, 0, 1, 2)
STATES = ("possible", "confirmed", "conflict")
AXES = ("case", "definiteness", "gender", "number")
EVIDENCE = ("unknown", "affirmed", "denied", "conflict")
IDAFA_MODES = ("semantic", "verbal")
AN_POLICY = {
    "كاد": ("permitted", False), "كرب": ("permitted", False),
    "عسى": ("permitted", True), "أوشك": ("permitted", True),
    "حرى": ("required", True), "اخلولق": ("required", True),
    "inception": ("forbidden", False),
}
ACTIVATION_BITS = ("identity_bound", "source_supported", "attachment_licensed",
                   "frame_complete", "sense_licensed", "unblocked")
IDENTITIES = ("badal_total", "badal_part", "badal_association", "tawkeed")
IDENTITY_BITS = ("relation_licensed", "identity_licensed")
SCOPES = ("belief", "certainty", "transformation", "proximity", "hope", "inception",
          "wish", "similitude", "continuation", "duration", "time_transition")
SCOPE_BITS = ("metadata_preserved", "source_supported", "frame_complete")
SCOPE_METADATA = ("family", "sense", "tense", "time", "place", "polarity", "restriction", "operator_binding")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


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


def all_required(mask, names):
    present = {name for name, value in flags(mask, names).items() if value}
    return present == set(names)


def agreement_oracle(values):
    # The set of explicit failures takes precedence over unresolved axes.
    return "conflict" if "conflict" in values else "possible" if "possible" in values else "confirmed"


def idafa_oracle(mode, tanwin, nun, article, exception):
    evidence = {"tanwin": tanwin, "nun": nun, "article": article}
    forbidden = {"tanwin", "nun"}
    if (mode, exception) != ("verbal", True):
        forbidden.add("article")
    contradictory = {key for key, value in evidence.items()
                     if value == "conflict" or (key in forbidden and value == "affirmed")}
    if contradictory:
        return "conflict"
    return "possible" if "unknown" in evidence.values() else "confirmed"


def expected_rows():
    return {
        "operator_rows": [{"family": family, "slots": [{"role": role, "case": ROLE_CASES[role]}
                                                          for role in OPERATOR_ROLES[family]]}
                          for family in FAMILIES],
        "role_rows": [{"label": role, "inherited_case": inherited,
                       "case": inherited if case is None else case, "inherits": case is None,
                       "target": "clause_local_case" if role == "kada_predicate" else "licensed_constituent"}
                      for role, inherited in product(ROLE_CASES, INHERITED) for case in (ROLE_CASES[role],)],
        "agreement_rows": [{**dict(zip(AXES, values)), "status": agreement_oracle(values)}
                           for values in product(STATES, repeat=4)],
        "idafa_rows": [{"mode": mode, "tanwin": t, "nun": n, "article": a, "article_exception": exception,
                        "status": idafa_oracle(mode, t, n, a, exception)}
                       for mode, t, n, a, exception in product(IDAFA_MODES, EVIDENCE, EVIDENCE, EVIDENCE, (False, True))],
        "an_rows": [{"label": label, "policy": policy, "preferred_present": preferred,
                     "allows_absent": policy != "required", "allows_present": policy != "forbidden"}
                    for label, (policy, preferred) in AN_POLICY.items()],
        "activation_rows": [{"family": family, "mask": mask, "allowed": all_required(mask, ACTIVATION_BITS)}
                            for family, mask in product(FAMILIES, range(64))],
        "identity_rows": [{"label": label, "mask": mask,
                           "allowed": label in {"badal_total", "tawkeed"} and all_required(mask, IDENTITY_BITS)}
                          for label, mask in product(IDENTITIES, range(4))],
        "scope_rows": [{"scope": scope, "mask": mask, "allowed": all_required(mask, SCOPE_BITS),
                        "bare_projection": False} for scope, mask in product(SCOPES, range(8))],
    }


def check_table(export):
    raw = TABLE.read_bytes()
    equal(export, parse(raw), "Complete fresh Lean export differs from installed JSON")
    require(type(export["schema_version"]) is int and export["schema_version"] == 1, "Wrong schema")
    require(export["law_id"] == "nabt.construction-evidence.v1", "Wrong law identity")
    require(export["source_policy_id"] == "nabt.construction-grammar-sources.v1", "Wrong source-policy identity")
    for key, values in (("families", FAMILIES), ("roles", tuple(ROLE_CASES)), ("inherited_cases", INHERITED),
                        ("compatibilities", STATES), ("agreement_axes", AXES), ("evidence_states", EVIDENCE),
                        ("idafa_modes", IDAFA_MODES), ("activation_bits", ACTIVATION_BITS),
                        ("identity_relations", IDENTITIES), ("identity_bits", IDENTITY_BITS),
                        ("scopes", SCOPES), ("scope_bits", SCOPE_BITS), ("scope_metadata", SCOPE_METADATA)):
        equal(export[key], values, "Named domain differs: " + key)
    expected = expected_rows()
    for key, rows in expected.items():
        equal(export[key], rows, "Independent finite oracle differs: " + key)

    sys.path.insert(0, str(ROOT / "src"))
    from nabt import construction_laws as laws
    equal(laws.installed_registry(), export, "Installed runtime registry differs")
    require(laws.EXPECTED_TABLE_SHA256 == sha256(raw).hexdigest(), "Runtime digest differs")
    for row in expected["operator_rows"]:
        equal(laws.operator_slots(row["family"]), row["slots"], "Runtime operator slots differ")
    for row in expected["role_rows"]:
        equal(laws.role_case(row["label"], row["inherited_case"]), row["case"], "Runtime constituent case differs")
    for row in expected["agreement_rows"]:
        equal(laws.agreement_status(**{key: row[key] for key in AXES}), row["status"], "Runtime agreement differs")
    for row in expected["idafa_rows"]:
        equal(laws.idafa_head_status(row["mode"], row["tanwin"], row["nun"], row["article"],
                                    article_exception=row["article_exception"]), row["status"], "Runtime idafa differs")
    for row in expected["an_rows"]:
        equal(laws.complement_an_policy(row["label"]), row["policy"], "Runtime an policy differs")
        equal(laws.complement_an_preferred_present(row["label"]), row["preferred_present"], "Runtime an preference differs")
        for present in (False, True):
            equal(laws.complement_an_allowed(row["label"], present),
                  row["allows_present" if present else "allows_absent"], "Runtime permissible an form differs")
    for row in expected["activation_rows"]:
        equal(laws.construction_allowed(row["family"], **flags(row["mask"], ACTIVATION_BITS)),
              row["allowed"], "Runtime conditional activation differs")
    for row in expected["identity_rows"]:
        equal(laws.identity_preservation_allowed(row["label"], **flags(row["mask"], IDENTITY_BITS)),
              row["allowed"], "Runtime identity preservation differs")
    for row in expected["scope_rows"]:
        equal(laws.scoped_projection_allowed(row["scope"], **flags(row["mask"], SCOPE_BITS)),
              row["allowed"], "Runtime scoped projection differs")
        equal(laws.bare_projection_allowed(row["scope"]), row["bare_projection"], "Runtime bare projection differs")
    return {
        "ok": True, "law_id": export["law_id"], "packaged_sha256": sha256(raw).hexdigest(),
        "fresh_full_json_matches_packaged": True, "type_sensitive_comparison": True,
        "runtime_table_adapters_checked": True, "runtime_reader_checked": False,
        "counts": {key: len(rows) for key, rows in expected.items()},
        "total_rows": sum(map(len, expected.values())),
        "scope": "Conditional constituent, evidence and scoped-projection algebra only; not source acquisition, parser correctness, linguistic coverage or external truth.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build", "Nabt.ConstructionEvidence"], cwd=ROOT / "formal",
                       check=True, capture_output=True, text=True)
        result = subprocess.run([args.lake, "env", "lean", "--run", "ExportConstructionEvidence.lean"],
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
