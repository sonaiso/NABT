#!/usr/bin/env python3
"""Replay six existing capability probes and retain their bounded observations.

These inputs and expected projections were already exposed in the organization
audit. This is a baseline recorder, not a new evaluator, engine, or independent
held-out test. It calls the existing APIs and their installed native checkers;
it never builds Lean. Output files are created exclusively so that a replay
cannot silently replace a retained historical observation.

Example replay, with an isolated new destination:
    python -B evidence/rule_policy_organization_v1/baseline_capability_probe.py \
        --output /tmp/nabt-rule-policy-baseline-replay.json
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from nabt.learning import GuardLanguage, LearningSession, default_pilot, observation_schema
from nabt.learning.arabic_six_nouns import APPROVED_SOURCE_PINS
from nabt.rational_inquiry import audit_inquiry, verify_inquiry
from nabt.semantics import SemanticKernel
from tests.test_evidence_lifecycle_v1 import event, scenario
from tests.test_epistemic_measurement import ledger
from tests.test_rational_inquiry import sample
from tools import epistemic_measurement as em
from tools import evidence_lifecycle_v1 as life
from tools.grammar_catalog.routing import schedule


BASE_COMMIT = "181dec466ccfad5b6a63ec9750f149ea58829eda"
FORMAL_PATHS = (
    "formal/lean-toolchain", "formal/lakefile.lean",
    "formal/EpistemicMeasurementMain.lean", "formal/EvidenceLifecycleV1Main.lean",
    "formal/Nabt/RuleLearning.lean", "formal/Nabt/PropertyEvidence.lean",
    "formal/Nabt/SourceSemantics.lean", "formal/Nabt/SemanticInference.lean",
    "formal/Nabt/VerifiedReading.lean", "formal/Nabt/RationalInquiry.lean",
    "formal/Nabt/EpistemicMeasurement.lean", "formal/Nabt/EvidenceLifecycleV1.lean",
    "formal/Nabt/RuleRouting.lean",
)
SOURCE_PATHS = tuple(f"src/nabt/data/source_evidence/{name}.txt" for name in APPROVED_SOURCE_PINS)

# These literal projections reproduce the outcomes already observed in the
# audit. They are compared only after execution and never enter an API request.
EXPECTED = {
    "finite-guard-withdrawal-restoration": {
        "counts": [8, 4, 2, 1], "prediction": "conditional_consensus",
        "withdrawn_count": 2, "withdrawn_prediction": "underdetermined",
        "restored_count": 1, "restored_revision": True, "degree3_survivors": 5,
    },
    "concept-definition-application-withdrawal": {
        "admitted": True, "case_status": "SUPPORTED", "new_instance_status": "UNKNOWN",
        "certificate_accepted": True, "after_withdrawal": "UNKNOWN",
        "old_certificate_accepted": False,
    },
    "inquiry-world-boundary": {
        "status": "LICENSED", "authorized_rank": 2,
        "verified": {"valid": True, "status": "VERIFIED", "claim_status": "LICENSED",
                     "authority": "EXACT_INQUIRY_REPLAY", "world_truth": "NOT_ESTABLISHED"},
        "world_status": "DEFER",
        "formation_authority": "DECLARED_SOURCE_LINKS_NOT_PROOF_OF_HOW_THE_CANDIDATE_WAS_PRODUCED",
    },
    "native-epistemic-conflict-hidden-motive": {
        "native_checked": True,
        "supported": {"status": "SUPPORTED", "support_ids": ["witness"],
                      "refutation_ids": [], "selected_ids": ["witness"]},
        "conflict": {"status": "CONFLICT", "support_ids": ["witness"],
                     "refutation_ids": ["negative"], "selected_ids": ["witness", "negative"]},
        "hidden_motive": {"status": "UNKNOWN", "support_ids": [],
                          "refutation_ids": [], "selected_ids": []},
    },
    "native-lifecycle-replay-changed-episode": {
        "native_checked": True, "statuses": ["SUPPORTED", "UNKNOWN", "SUPPORTED"],
        "verified": True, "changed_episode_verified": False,
    },
    "routing-complete-declared-inventory": {"schedule": ["r2", "r1", "r3"]},
}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(wire(value).encode("utf-8")).hexdigest()


def snapshot(paths):
    result = {}
    for relative in sorted(set(paths)):
        path = ROOT / relative
        raw = path.read_bytes() if path.is_file() else None
        result[relative] = {"sha256": sha256(raw).hexdigest() if raw is not None else None,
                            "bytes": len(raw) if raw is not None else None}
    return result


def loaded_project_paths():
    paths = set()
    for module in tuple(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT) and path.suffix == ".py":
                paths.add(path.relative_to(ROOT).as_posix())
    return paths


def finite_guard():
    pilot = default_pilot()
    observations = tuple(pilot.observations("observed_example"))
    session = LearningSession(GuardLanguage(observation_schema(), 1))
    counts, revisions = [len(session.survivors)], [session.revision]
    for observation in observations:
        session = session.observe(observation)
        counts.append(len(session.survivors))
        revisions.append(session.revision)
    withdrawn = session.revise_evidence(observations[-1].evidence_id, None)
    restored = withdrawn.observe(observations[-1])
    richer = LearningSession(GuardLanguage(observation_schema(), 3), observations)
    observed = {
        "counts": counts, "prediction": session.predict(observations[-1].case).status.value,
        "withdrawn_count": len(withdrawn.survivors),
        "withdrawn_prediction": withdrawn.predict(observations[-1].case).status.value,
        "restored_count": len(restored.survivors), "restored_revision": restored.revision == session.revision,
        "degree3_survivors": len(richer.survivors),
    }
    inputs = {"schema": asdict(observation_schema()), "degrees": [1, 3],
              "observations": [asdict(item) for item in observations],
              "withdrawn_evidence_id": observations[-1].evidence_id,
              "query_case": asdict(observations[-1].case)}
    details = {"source_records": [asdict(record) for record in pilot.observed_records()],
               "approved_source_pins": dict(APPROVED_SOURCE_PINS), "revisions": revisions,
               "withdrawn_revision": withdrawn.revision, "restored_revision": restored.revision,
               "survivor_codes": [rule.code for rule in session.survivors],
               "withdrawn_survivor_codes": [rule.code for rule in withdrawn.survivors],
               "degree3_survivor_codes": [rule.code for rule in richer.survivors],
               "independent_heldout_examples": 0, "new_linguistic_rule_adopted": False}
    return inputs, observed, details


def concept_application():
    inputs = {"definition": "تعريف نوع هو أول و ثان.", "case": "زيد هو أول. زيد هو ثان.",
              "definition_source_id": "definition", "case_source_id": "case", "scope": "default",
              "query": "هل زيد هو نوع؟", "new_instance_query": "هل جديد هو نوع؟"}
    kernel = SemanticKernel()
    admission = kernel.add_source(inputs["definition"], source_id="definition")
    case_admission = kernel.add_source(inputs["case"], source_id="case")
    before = kernel.query(inputs["query"])
    new_instance = kernel.query(inputs["new_instance_query"])
    certificate = before.proofs["query"]
    checked = kernel.verify_certificate(certificate)
    revision = kernel.remove_source("case")
    after = kernel.query(inputs["query"])
    stale = kernel.verify_certificate(certificate)
    observed = {"admitted": admission.accepted, "case_status": before.status,
                "new_instance_status": new_instance.status, "certificate_accepted": checked["accepted"],
                "after_withdrawal": after.status, "old_certificate_accepted": stale["accepted"]}
    details = {"definition_admission": admission.as_dict(), "case_admission": case_admission.as_dict(),
               "before": before.as_dict(), "new_instance": new_instance.as_dict(),
               "certificate_verification": checked, "revision": revision.as_dict(),
               "after": after.as_dict(), "stale_certificate_verification": stale,
               "native_checked": False, "execution_kind": "EXISTING_PYTHON_SEMANTIC_KERNEL"}
    return inputs, observed, details


def inquiry_boundary():
    plan, sources = sample()
    report = audit_inquiry(plan, sources)
    verified = verify_inquiry(report, plan, sources)
    world_plan = deepcopy(plan)
    world_plan["claim"]["kind"] = "WORLD_CORRESPONDENCE"
    world_report = audit_inquiry(world_plan, sources)
    observed = {"status": report["status"], "authorized_rank": report["authorized_rank"],
                "verified": verified, "world_status": world_report["status"],
                "formation_authority": report["formation_authority"]}
    return {"plan": plan, "sources": sources, "world_plan": world_plan}, observed, {
        "fixture": "tests/test_rational_inquiry.py::sample", "report": report,
        "world_report": world_report, "native_checked": False,
    }


def epistemic_boundary():
    request = ledger()
    inputs = {"supported": deepcopy(request)}
    support = em.execute_request(request)
    opposite = deepcopy(request["interpretations"][0])
    opposite.update(id="negative", positive=False)
    request["interpretations"].append(opposite)
    inputs["conflict"] = deepcopy(request)
    conflict = em.execute_request(request)
    request["query"]["key"]["axis"] = "hidden_motive"
    inputs["hidden_motive"] = deepcopy(request)
    hidden = em.execute_request(request)
    observed = {"native_checked": support["native_checked"], "supported": support["observed"],
                "conflict": conflict["observed"], "hidden_motive": hidden["observed"]}
    return inputs, observed, {"fixture": "tests/test_epistemic_measurement.py::ledger",
        "reports": {"supported": support, "conflict": conflict, "hidden_motive": hidden},
        "all_three_native_checked": all(r["native_checked"] for r in (support, conflict, hidden)),
        "native_transport_retained_as": "EXISTING_ADAPTER_INPUT_AND_PARSED_NATIVE_RESULT_WITH_HASHES",
    }


def lifecycle_boundary():
    episode = scenario()
    source = episode["active_sources"][1]
    episode["updates"] = [event("w", "withdraw", source), event("a", "activate", source)]
    report = life.evaluate_episode(episode)
    changed = deepcopy(episode)
    changed["updates"].append(event("noop", "activate", source))
    verified = life.verify_episode(report, expected_episode=episode)
    stale = life.verify_episode(report, expected_episode=changed)
    observed = {"native_checked": report["native_checked"],
                "statuses": [step["receipt"]["status"] for step in report["observed"]["steps"]]
                if report["observed"] is not None else None,
                "verified": verified["valid"], "changed_episode_verified": stale["valid"]}
    return {"episode": episode, "changed_episode": changed}, observed, {
        "fixture": "tests/test_evidence_lifecycle_v1.py::scenario,event", "report": report,
        "verification": verified, "changed_episode_verification": stale,
        "native_transport_retained_as": "EXISTING_ADAPTER_INPUT_AND_PARSED_NATIVE_RESULT_WITH_HASHES",
    }


def routing_boundary():
    inventory, ranked = ["r1", "r2", "r3"], ["unknown", "r2", "r2"]
    return {"inventory": inventory, "ranked": ranked}, {"schedule": schedule(inventory, ranked)}, {
        "scope": "Authored three-ID inventory; not a scan of the installed Arabic rule inventory.",
        "native_checked": False,
    }


PROBES = (
    ("finite-guard-withdrawal-restoration", finite_guard),
    ("concept-definition-application-withdrawal", concept_application),
    ("inquiry-world-boundary", inquiry_boundary),
    ("native-epistemic-conflict-hidden-motive", epistemic_boundary),
    ("native-lifecycle-replay-changed-episode", lifecycle_boundary),
    ("routing-complete-declared-inventory", routing_boundary),
)


def record():
    native_paths = [path.relative_to(ROOT).as_posix() for path in (em.NATIVE, life.NATIVE)]
    code_paths = loaded_project_paths() | {"src/nabt/text_reader.py"}
    paths = code_paths | set(FORMAL_PATHS) | set(SOURCE_PATHS) | set(native_paths)
    before = snapshot(paths)
    rows = []
    for name, probe in PROBES:
        row = {"id": name, "expected": EXPECTED[name]}
        try:
            inputs, observed, details = probe()
            row.update(input=inputs, input_sha256=digest(inputs), observed=observed, details=details,
                       matches_expected=wire(observed) == wire(EXPECTED[name]), error=None)
        except Exception as error:
            row.update(input=None, input_sha256=None, observed=None, details=None,
                       matches_expected=False, error={"type": type(error).__name__, "message": str(error)})
        rows.append(row)
    after = snapshot(paths)
    extra_code = loaded_project_paths() - code_paths
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()
    return {
        "schema": "nabt.rule-policy-baseline-capability-probes.v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {"evidence_class": "EXPOSED_ENGINEERING_BASELINE",
            "expectations_already_exposed": True, "independently_frozen_evaluation": False,
            "fresh_lean_build_performed": False, "full_test_suite_run": False,
            "all_capabilities_executed": False, "semantic_authority": "NONE",
            "world_truth_established": False, "whole_arabic_complete": False,
            "note": "Six previously executed bounded probes; no new engine, inference license, or rule adoption. Expected projections never enter the runtime requests."},
        "run_identity": {"audit_base_commit": BASE_COMMIT, "observed_head_commit": commit,
            "python": sys.version, "platform": platform.platform(),
            "pinned_toolchain": (ROOT / "formal/lean-toolchain").read_text().strip(),
            "code_paths": sorted(code_paths), "formal_contract_paths": list(FORMAL_PATHS),
            "source_paths": list(SOURCE_PATHS), "native_paths": native_paths,
            "files_before": before, "files_after": after, "inputs_unchanged_during_run": before == after,
            "additional_loaded_project_code": snapshot(extra_code),
            "native_build_provenance": "Existing binary bytes measured; no fresh compilation or binary-to-current-source refinement asserted."},
        "probes": rows,
        "summary": {"probe_count": len(rows), "matching_expected_probes": sum(r["matches_expected"] for r in rows),
            "all_expected_projections_match": all(r["matches_expected"] for r in rows),
            "inputs_unchanged_during_run": before == after},
        "replay_command": "python -B evidence/rule_policy_organization_v1/baseline_capability_probe.py --output /tmp/nabt-rule-policy-baseline-replay.json",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new JSON file; an existing file is never replaced")
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error("output already exists; choose a new destination for this replay")
    report = record()
    serialized = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(serialized, end="")
    else:
        with args.output.open("x", encoding="utf-8") as output:
            output.write(serialized)
        print(json.dumps({"output": str(args.output), **report["summary"]}, ensure_ascii=False))
    return 0 if report["summary"]["all_expected_projections_match"] and report["summary"]["inputs_unchanged_during_run"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
