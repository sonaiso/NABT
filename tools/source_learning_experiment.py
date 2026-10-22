#!/usr/bin/env python3
"""Replay pinned Arabic evidence, learn a finite relation, and revisit evidence.

This is a transparent bounded experiment: six explicit rule statements and
three actual quotations, one lexeme, and zero independently held-out examples.
It does not infer arbitrary grammatical cases or license a general Arabic rule.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nabt.learning.arabic_six_nouns import (  # noqa: E402
    APPROVED_SOURCE_PINS,
    CHECKER_VERSION,
    POLICY_ID,
    SixNounPilot,
    default_pilot,
    observation_schema,
    prescription_schema,
)
from nabt.learning.finite_guard import (  # noqa: E402
    FeatureSchema,
    GuardLanguage,
    LearningSession,
    LearningStatus,
    Observation,
)
from nabt.learning.source_evidence import (  # noqa: E402
    CheckStatus,
    ReplayRecord,
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def learn(
    schema: FeatureSchema, observations: tuple[Observation, ...]
) -> tuple[LearningSession, list[dict[str, object]]]:
    session = LearningSession(GuardLanguage(schema, degree=1))
    steps: list[dict[str, object]] = [
        {"step": "before_evidence", "surviving_count": len(session.survivors)}
    ]
    for observation in observations:
        session = session.observe(observation)
        steps.append(
            {
                "evidence_id": observation.evidence_id,
                "source_id": observation.source_id,
                "known": observation.case.known,
                "value": observation.case.value,
                "label": observation.label,
                "surviving_count": len(session.survivors),
                "rule_codes": [rule.code for rule in session.survivors],
                "revision": session.revision,
            }
        )
    return session, steps


def record_report(pilot: SixNounPilot, record: ReplayRecord) -> dict[str, object]:
    check = pilot.check(record.proposal())
    require(check.accepted, f"source replay failed: {record.record_id}")
    return {
        "record_id": record.record_id,
        "kind": record.kind,
        "cue": record.cue,
        "target": record.target,
        "independently_read_marker": record.marker,
        "cue_spans": [asdict(span) for span in record.cue_spans],
        "target_span": asdict(record.target_span),
        "marker_span": asdict(record.marker_span),
        "context_span": asdict(record.context_span),
        "binding": asdict(record.binding),
        "known_mask": record.known,
        "value_mask": record.value,
        "label_observed_marker_is_waw": record.label,
        "receipt_id": check.receipt_id,
        "interpretation": record.interpretation_note,
    }


def experiment(source_directory: Path | None = None) -> dict[str, object]:
    started = time.perf_counter()
    pilot = default_pilot() if source_directory is None else SixNounPilot.from_directory(source_directory)
    prescriptions = pilot.prescription_records()
    observed = pilot.observed_records()
    require(len(prescriptions) == 6 and len(observed) == 3, "unexpected evidence domain")
    record_reports = [record_report(pilot, record) for record in (*prescriptions, *observed)]

    # Explicit prescriptions: the learned Boolean selector re-expresses the
    # source mapping. Alfiyya supplies agreement, not a blind test or new pairs.
    qatr = pilot.observations("prescription", source_id="qatr")
    alfiyya = pilot.observations("prescription", source_id="alfiyya")
    compiled, compiled_steps = learn(prescription_schema(), qatr)
    agreement = [
        compiled.predict(observation.case).possible == (observation.label,)
        for observation in alfiyya
    ]
    require(all(agreement), "prescription sources do not agree on the declared mapping")

    # Actual examples: cue bytes are input; ending bytes are independently read
    # labels. No nominative/accusative/genitive role is inferred by this schema.
    observations = pilot.observations("observed_example")
    learned, steps = learn(observation_schema(), observations)
    require(
        [step["surviving_count"] for step in steps] == [8, 4, 2, 1],
        "unexpected version-space trajectory",
    )
    require(
        len(learned.survivors) == 1 and learned.survivors[0].code == 1,
        "unexpected surviving selector",
    )
    first_only = LearningSession(learned.language, observations[:1])
    second_query = first_only.predict(observations[1].case)
    require(second_query.status is LearningStatus.UNDERDETERMINED, "one example overgeneralized")
    require(
        any(rule.code == 0 for rule in first_only.survivors),
        "constant-true candidate absent too soon",
    )
    second_session = first_only.observe(observations[1])
    require(
        all(rule.code != 0 for rule in second_session.survivors),
        "observed counterexample did not remove constant true",
    )

    # Withdrawing support is a deliberate audit intervention, not a newly found
    # error in Sibawayhi. Rebuild from the full grammar; preserve old snapshots.
    withdrawn = learned.revise_evidence(observations[2].evidence_id, None)
    require(len(withdrawn.survivors) == 2, "withdrawal failed to restore a candidate")
    restored = withdrawn.observe(observations[2])
    require(
        restored.survivors == learned.survivors, "replay failed to restore the same hypothesis set"
    )
    require(
        restored.revision == learned.revision, "identical evidence changed extensional revision"
    )

    proposal = pilot.propose(observed[0].record_id)
    unknown_label = pilot.check(replace(proposal, label=None))
    unknown_features = pilot.check(replace(proposal, known=0, value=0))
    tampered_label = pilot.check(replace(proposal, label=False))
    transferred = pilot.check(replace(proposal, binding=observed[1].binding))
    require(unknown_label.status is CheckStatus.PENDING, "unknown label was asserted")
    require(unknown_features.status is CheckStatus.PENDING, "unknown features were asserted")
    require(tampered_label.status is CheckStatus.REJECTED, "unsupported label entered learner")
    require(transferred.status is CheckStatus.REJECTED, "another occurrence authorized this claim")
    family = pilot.assess_family([proposal, replace(proposal, label=None)])
    require(
        family.status is CheckStatus.AMBIGUOUS and not family.observations,
        "unresolved alternatives became independent facts",
    )
    mixed_family = pilot.assess_family([proposal, pilot.propose(observed[1].record_id)])
    require(
        mixed_family.status is CheckStatus.REJECTED and not mixed_family.observations,
        "different occurrences became alternative readings",
    )
    application = {
        noun: asdict(pilot.application_assessment(noun))
        for noun in ("أب", "ذو", "فم", "هن", "كتاب")
    }

    # A new literal cue has no checked feature extraction in this adapter.
    unsupported = observation_schema().case("unseen-cue", "unresolved-v1", {})
    unsupported_prediction = learned.predict(unsupported)
    require(
        unsupported_prediction.status is LearningStatus.UNDERDETERMINED,
        "unseen cue acquired invented bits",
    )
    return {
        "scope": {
            "prescription_compilation_records": 6,
            "distinct_prescription_operation_marker_pairs": 3,
            "actual_observed_examples": 3,
            "observed_lexemes": 1,
            "independent_heldout_examples": 0,
            "generated_forms_counted_as_observations": 0,
            "target": "observed/selected carrier is waw, within each separately typed schema",
            "general_arabic_accuracy_measured": False,
            "source_agreement_implies_independence": False,
        },
        "source_sha256": dict(APPROVED_SOURCE_PINS),
        "checker_version": CHECKER_VERSION,
        "policy_id": POLICY_ID,
        "source_records": record_reports,
        "prescription_compilation": {
            "steps": compiled_steps,
            "alfiyya_agreement": agreement,
            "independent_holdout": False,
            "rule": compiled.survivors[0].render(prescription_schema()),
        },
        "observational_learning": {
            "steps": steps,
            "rule_code": learned.survivors[0].code,
            "rule": learned.survivors[0].render(observation_schema()),
            "claim_strength": "conditional on the declared degree-one grammar and literal cue projection",
            "second_case_after_one_observation": second_query.status.value,
            "constant_true_removed_by_second_observation": True,
        },
        "revision": {
            "intervention": "withdraw and then restore the third actual source observation",
            "before": len(learned.survivors),
            "after_withdrawal": len(withdrawn.survivors),
            "after_replay": len(restored.survivors),
            "before_revision": learned.revision,
            "withdrawal_revision": withdrawn.revision,
            "restored_revision": restored.revision,
            "old_snapshot_unchanged": len(learned.survivors) == 1,
        },
        "admission_probes": {
            "unknown_label": unknown_label.status.value,
            "unknown_properties": unknown_features.status.value,
            "forged_label": tampered_label.status.value,
            "other_occurrence_binding": transferred.status.value,
            "alternative_family": family.status.value,
            "alternative_family_observations": len(family.observations),
            "alternative_probe_scope": "deliberately complete and incomplete proposals for one occurrence; not two independently parsed linguistic readings",
            "cross_occurrence_family": mixed_family.status.value,
            "unseen_literal_cue": unsupported_prediction.status.value,
        },
        "application_assessments": application,
        "elapsed_seconds_this_run": time.perf_counter() - started,
        "timing_scope": "one local end-to-end diagnostic run, not a latency benchmark",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, help="optional pinned source directory; defaults to installed package data")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = experiment(args.sources)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    summary = {
        "scope": report["scope"],
        "observational_learning": report["observational_learning"],
        "revision": report["revision"],
        "admission_probes": report["admission_probes"],
        "elapsed_seconds_this_run": report["elapsed_seconds_this_run"],
        "report": str(args.output) if args.output else None,
    }
    print(json.dumps(summary if args.output else report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
