"""Finite, source-bound learning with explicitly conditional conclusions.

The generic learner accepts external judgments. The Arabic source adapter is
the checked admission path for this package's nine pinned source records.
Neither path turns a supplied label, repetition, or a hash into a proof rank.
"""

from .arabic_six_nouns import (
    APPLICATION_PREDICATES,
    APPROVED_SOURCE_PINS,
    CHECKER_VERSION,
    POLICY_ID,
    ApplicationAssessment,
    FamilyAssessment,
    SixNounPilot,
    default_pilot,
    observation_schema,
    prescription_schema,
)
from .finite_guard import (
    FeatureCase,
    FeatureSchema,
    Guard,
    GuardLanguage,
    LearningSession,
    LearningStatus,
    Observation,
    Prediction,
    QueryChoice,
)
from .source_evidence import (
    CheckResult,
    CheckStatus,
    EvidenceBinding,
    EvidenceLedger,
    EvidenceProposal,
    LicenseDecision,
    LicenseStatus,
    ReplayRecord,
    SourceBlob,
    SourceSpan,
    SourceStore,
    compare_replayed_record,
    content_digest,
    evaluate_license,
    identity_digest,
)

__all__ = [
    "APPLICATION_PREDICATES",
    "APPROVED_SOURCE_PINS",
    "ApplicationAssessment",
    "CHECKER_VERSION",
    "CheckResult",
    "CheckStatus",
    "EvidenceBinding",
    "EvidenceLedger",
    "EvidenceProposal",
    "FamilyAssessment",
    "FeatureCase",
    "FeatureSchema",
    "Guard",
    "GuardLanguage",
    "LearningSession",
    "LearningStatus",
    "LicenseDecision",
    "LicenseStatus",
    "Observation",
    "POLICY_ID",
    "Prediction",
    "QueryChoice",
    "ReplayRecord",
    "SixNounPilot",
    "SourceBlob",
    "SourceSpan",
    "SourceStore",
    "compare_replayed_record",
    "content_digest",
    "default_pilot",
    "evaluate_license",
    "identity_digest",
    "observation_schema",
    "prescription_schema",
]
