"""A bounded, source-bound Arabic passage adapter, not a general Arabic parser.

Two paths are deliberately separate. Qatr/Alfiyya prescriptions are authored
rule compilation. Three actual Sibawayhi examples supply literal cue features
and independently observed ending labels. Neither path establishes grammatical
roles for arbitrary text, independent held-out accuracy, or a ProofRank.

The source allowlist and extraction policy are shipped below. JSON manifests
alongside the original texts document provenance; they cannot grant authority.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from itertools import islice
from pathlib import Path
from types import MappingProxyType

from nabt.errors import resource_limit
from nabt.learning.finite_guard import FeatureCase, FeatureSchema, Observation
from nabt.learning.source_evidence import (
    CheckResult,
    CheckStatus,
    EvidenceBinding,
    EvidenceLedger,
    EvidenceProposal,
    LicenseDecision,
    ReplayRecord,
    SourceSpan,
    SourceStore,
    compare_replayed_record,
    evaluate_license,
    identity_digest,
)

CHECKER_VERSION = "nabt-six-nouns-source-v1"
APPROVED_SOURCE_PINS = MappingProxyType(
    {
        "qatr": "2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d",
        "alfiyya": "13b351a0a02d9060fdedbb5db568544718eb4e89bef323f5572b8a26c0921ca0",
        "sibawayhi": "a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625",
    }
)

# Each tuple is (source id, raw byte start, raw byte end, raw span SHA-256).
_CONTEXTS = MappingProxyType(
    {
        "qatr_case_letters": (
            "qatr",
            4240,
            4494,
            "c90fcc9731204d5eee0fc7e0f0db01a3dae779ae22ead6ea6e9732292dbb372f",
        ),
        "alfiyya_case_letters": (
            "alfiyya",
            3825,
            3929,
            "00e805367d0f23d5e19b7688c5caf7d4eb272e3e3a8eb09ba9daec1f01d6e6ff",
        ),
        "alfiyya_special_conditions": (
            "alfiyya",
            3929,
            4022,
            "5cb486906139d18c547650e9c214a3199d43aa69b5243eb7e0a559b6d1ae3bde",
        ),
        "alfiyya_han_preference": (
            "alfiyya",
            4022,
            4106,
            "112d6e5126636c5d14646d279a2ef78e409fb940adb0ba295f421eab6d8d763e",
        ),
        "alfiyya_qasr": (
            "alfiyya",
            4106,
            4186,
            "b2a67cd7ccef1cf2fa4d8c49dc86fa3742edca79c87bb4a88a9e8b375d7ed1d5",
        ),
        "alfiyya_idafa": (
            "alfiyya",
            4186,
            4287,
            "86dfa9203b92c99b3e322b1c82e03226cdb7c8810f5c3d026a9f0f73383d1952",
        ),
        "qatr_dhu_relative": (
            "qatr",
            10509,
            10895,
            "572921732bca69a23725ace3825f6e1989e4d0f08a0c5c2c4559ef65630be4a7",
        ),
        "sibawayhi_han_examples": (
            "sibawayhi",
            1460416,
            1460684,
            "a85164fea6a5b2f90c460d19fda816c2085d9213bd901308f78bc34799db197a",
        ),
    }
)

_PRESCRIPTION_CUES = MappingProxyType(
    {"فترفع": 0, "ارفع": 0, "تنصب": 1, "انصبن": 1, "تجر": 2, "اجرر": 2}
)
_LETTER_NAMES = MappingProxyType({"واو": "و", "ألف": "ا", "ياء": "ي"})
_OBSERVED_CUES = MappingProxyType({("هذا",): 0, ("رأيت",): 1, ("مررت", "ب"): 2})

_PRESCRIPTION_DEFINITION = identity_digest(
    (
        "authored_source_prescription_projection_v1",
        tuple(_PRESCRIPTION_CUES.items()),
        tuple(_LETTER_NAMES.items()),
        "features read operation token only; label selects waw in source clause",
    )
)
_OBSERVATION_DEFINITION = identity_digest(
    (
        "literal_sibawayhi_han_examples_v1",
        tuple(_OBSERVED_CUES.items()),
        "features read cue spans only; label reads carrier before kaf in target",
        "no grammatical case assigned; three examples, one lexeme, no heldout",
    )
)


from nabt import foundation

def prescription_schema() -> FeatureSchema:
    return FeatureSchema(
        "source_prescription.six_nouns",
        _PRESCRIPTION_DEFINITION,
        ("operation_is_raf", "operation_is_nasb", "operation_is_jarr"),
    )


def observation_schema() -> FeatureSchema:
    return FeatureSchema(
        "observed_text.sibawayhi_han",
        _OBSERVATION_DEFINITION,
        ("cue_is_hadha", "cue_is_raaytu", "cue_is_marartu_ba"),
    )


@dataclass(frozen=True, slots=True)
class _RecordSpec:
    record_id: str
    kind: str
    context_id: str
    clause: str
    cues: tuple[str, ...]
    target: str
    letter_name: str | None = None


_RECORDS = (
    _RecordSpec(
        "qatr_raf",
        "prescription",
        "qatr_case_letters",
        "فترفع بالواو",
        ("فترفع",),
        "بالواو",
        "واو",
    ),
    _RecordSpec(
        "qatr_nasb",
        "prescription",
        "qatr_case_letters",
        "وتنصب بالألف",
        ("تنصب",),
        "بالألف",
        "ألف",
    ),
    _RecordSpec(
        "qatr_jarr", "prescription", "qatr_case_letters", "وتجر بالياء", ("تجر",), "بالياء", "ياء"
    ),
    _RecordSpec(
        "alfiyya_raf",
        "prescription",
        "alfiyya_case_letters",
        "وارفع بواو",
        ("ارفع",),
        "بواو",
        "واو",
    ),
    _RecordSpec(
        "alfiyya_nasb",
        "prescription",
        "alfiyya_case_letters",
        "وانصبن بالألف",
        ("انصبن",),
        "بالألف",
        "ألف",
    ),
    _RecordSpec(
        "alfiyya_jarr",
        "prescription",
        "alfiyya_case_letters",
        "واجرر بياء",
        ("اجرر",),
        "بياء",
        "ياء",
    ),
    _RecordSpec(
        "sibawayhi_han_hadha",
        "observed_example",
        "sibawayhi_han_examples",
        "هذا هنوك",
        ("هذا",),
        "هنوك",
    ),
    _RecordSpec(
        "sibawayhi_han_raaytu",
        "observed_example",
        "sibawayhi_han_examples",
        "رأيت هناك",
        ("رأيت",),
        "هناك",
    ),
    _RecordSpec(
        "sibawayhi_han_marartu_ba",
        "observed_example",
        "sibawayhi_han_examples",
        "مررت بهنيك",
        ("مررت", "ب"),
        "هنيك",
    ),
)
_RECORD_INDEX = MappingProxyType({spec.record_id: spec for spec in _RECORDS})
POLICY_ID = identity_digest(
    (
        CHECKER_VERSION,
        dict(APPROVED_SOURCE_PINS),
        dict(_CONTEXTS),
        tuple(asdict(spec) for spec in _RECORDS),
        _PRESCRIPTION_DEFINITION,
        _OBSERVATION_DEFINITION,
    )
)

APPLICATION_PREDICATES = (
    "idafa",
    "not_first_person_ya",
    "companionship",
    "mim_absent",
)
_LEXEMES = frozenset(("أب", "أخ", "حم", "هن", "فم", "ذو"))


def read_prescription_operation(cue_text: str) -> int | None:
    """Authored literal-operation lexicon; receives no marker or target."""
    return _PRESCRIPTION_CUES.get(cue_text)


def read_prescription_marker(letter_name: str) -> str | None:
    """Authored letter-name lexicon; receives no operation or case feature."""
    return _LETTER_NAMES.get(letter_name)


def read_observed_cue(cue_parts: tuple[str, ...]) -> int | None:
    """Literal context features; no claim about nominative/accusative/genitive."""
    return _OBSERVED_CUES.get(cue_parts)


def read_observed_ending(target_text: str) -> str | None:
    """Read the actual carrier before kaf in this declared four-codepoint shape."""
    if (
        len(target_text) == 4
        and target_text[:2] == "هن"
        and target_text[-1] == "ك"
        and target_text[-2] in ("و", "ا", "ي")
    ):
        return target_text[-2]
    return None


@dataclass(frozen=True, slots=True)
class FamilyAssessment:
    """Preserve alternatives; a family is never a conjunction of observations."""

    status: CheckStatus
    alternatives: tuple[EvidenceProposal, ...]
    observations: tuple[Observation, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApplicationAssessment:
    noun: str
    status: str
    required: int
    ledger: EvidenceLedger
    decision: LicenseDecision | None
    missing_predicates: tuple[str, ...]
    alternatives: tuple[str, ...]
    source_spans: tuple[SourceSpan, ...]
    scope_note: str


@dataclass(frozen=True, slots=True)
class SixNounPilot:
    """Fixed approved source policy. No candidate-selectable source authority."""

    sources: SourceStore

    def __post_init__(self) -> None:
        if set(self.sources.sources) != set(APPROVED_SOURCE_PINS):
            raise ValueError("source set does not match the fixed pilot policy")
        for source_id, digest in APPROVED_SOURCE_PINS.items():
            if self.sources.sources[source_id].sha256 != digest:
                raise ValueError(f"source digest mismatch: {source_id}")

    @classmethod
    def from_directory(cls, directory: str | Path) -> SixNounPilot:
        return cls(SourceStore.from_directory(Path(directory), APPROVED_SOURCE_PINS))

    @classmethod
    def from_package(cls) -> SixNounPilot:
        """Load the approved complete sources shipped inside the installed wheel."""
        return cls(
            SourceStore.from_resources("nabt", "data/source_evidence", APPROVED_SOURCE_PINS)
        )

    def _context(self, context_id: str) -> SourceSpan:
        source_id, start, end, digest = _CONTEXTS[context_id]
        span = SourceSpan(source_id, APPROVED_SOURCE_PINS[source_id], start, end, digest)
        self.sources.text(span)
        return span

    def _within(self, context: SourceSpan, literal: str) -> SourceSpan:
        raw = context.extract(self.sources.sources[context.source_id])
        needle = literal.encode("utf-8")
        if not needle or raw.count(needle) != 1:
            raise ValueError("authorized literal is missing or ambiguous in its context")
        start = context.start + raw.index(needle)
        return self.sources.span(context.source_id, start, start + len(needle))

    def _replay(self, spec: _RecordSpec) -> ReplayRecord:
        context = self._context(spec.context_id)
        clause = self._within(context, spec.clause)
        cues = tuple(self._within(clause, cue) for cue in spec.cues)
        target = self._within(clause, spec.target)
        cue_text = tuple(self.sources.text(cue) for cue in cues)
        target_text = self.sources.text(target)
        if spec.kind == "prescription":
            if spec.letter_name is None:
                raise ValueError("prescription lacks a letter-name span")
            marker_span = self._within(target, spec.letter_name)
            feature_index = read_prescription_operation(cue_text[0])
            marker = read_prescription_marker(self.sources.text(marker_span))
            schema = prescription_schema()
            definition_id = _PRESCRIPTION_DEFINITION
            note = "authored source-prescription compilation; operation and letter-name read separately"
        else:
            feature_index = read_observed_cue(cue_text)
            marker = read_observed_ending(target_text)
            schema = observation_schema()
            definition_id = _OBSERVATION_DEFINITION
            if marker is None:
                raise ValueError("observed target has unsupported shape or missing ending")
            start = target.start + len(target_text[:-2].encode("utf-8"))
            marker_span = self.sources.span(
                target.source_id, start, start + len(marker.encode("utf-8"))
            )
            note = "literal cue and observed carrier before kaf; no grammatical case inferred"
        if feature_index is None or marker is None:
            raise ValueError("unsupported source interpretation; no fact asserted")
        if any(cue.start < target.end and target.start < cue.end for cue in cues):
            raise ValueError("input cue and output target spans overlap")
        occurrence = identity_digest(
            (
                context.source_sha256,
                asdict(context),
                tuple(asdict(cue) for cue in cues),
                asdict(target),
            )
        )
        binding = EvidenceBinding(
            occurrence,
            identity_digest((occurrence, definition_id, CHECKER_VERSION)),
            context.source_sha256,
            context.span_sha256,
            definition_id,
            POLICY_ID,
            schema.fingerprint,
            CHECKER_VERSION,
        )
        return ReplayRecord(
            spec.record_id,
            spec.kind,
            binding,
            7,
            1 << feature_index,
            marker == "و",
            3,
            context,
            cues,
            target,
            marker_span,
            " ".join(cue_text),
            target_text,
            marker,
            note,
        )

    def prescription_records(self) -> tuple[ReplayRecord, ...]:
        return tuple(self._replay(spec) for spec in _RECORDS if spec.kind == "prescription")

    def observed_records(self) -> tuple[ReplayRecord, ...]:
        return tuple(self._replay(spec) for spec in _RECORDS if spec.kind == "observed_example")

    def propose(self, record_id: str) -> EvidenceProposal:
        foundation.require_foundation('nabt.learning.arabic_six_nouns.sixnounpilot.propose')
        return self._replay(_RECORD_INDEX[record_id]).proposal()

    def check(self, proposal: EvidenceProposal) -> CheckResult:
        foundation.require_foundation('nabt.learning.arabic_six_nouns.sixnounpilot.check')
        spec = _RECORD_INDEX.get(proposal.record_id)
        if spec is None:
            return CheckResult(CheckStatus.REJECTED, ("record_outside_approved_policy",))
        expected = self._replay(spec)
        return compare_replayed_record(expected, proposal)

    def to_observation(self, proposal: EvidenceProposal) -> Observation | None:
        """Replays again; a caller-created receipt/ReplayRecord cannot bypass it."""
        checked = self.check(proposal)
        if not checked.accepted or checked.record is None or checked.receipt_id is None:
            return None
        record = checked.record
        case = FeatureCase(
            record.binding.occurrence_id,
            record.binding.reading_id,
            record.binding.schema_id,
            record.width,
            record.known,
            record.value,
        )
        return Observation(
            checked.receipt_id, f"sha256:{record.binding.source_sha256}", case, record.label
        )

    def observations(self, kind: str, source_id: str | None = None) -> tuple[Observation, ...]:
        if kind not in ("prescription", "observed_example"):
            raise ValueError("unknown source-observation kind")
        observations = []
        for spec in _RECORDS:
            if spec.kind != kind:
                continue
            if source_id is not None and _CONTEXTS[spec.context_id][0] != source_id:
                continue
            observation = self.to_observation(self.propose(spec.record_id))
            if observation is None:
                raise ValueError("source replay did not yield a ready observation")
            observations.append(observation)
        return tuple(observations)

    def assess_family(self, alternatives: Iterable[EvidenceProposal]) -> FamilyAssessment:
        """An unresolved family never emits each alternative as an asserted fact."""
        foundation.require_foundation('nabt.learning.arabic_six_nouns.sixnounpilot.assess_family')
        retained = tuple(islice(alternatives, 33))
        if not retained:
            return FamilyAssessment(CheckStatus.PENDING, (), (), ("no_interpretation_supplied",))
        if len(retained) > 32:
            raise resource_limit("interpretation family exceeds resource budget")
        checks = tuple(self.check(proposal) for proposal in retained)
        if any(check.status is CheckStatus.REJECTED for check in checks):
            return FamilyAssessment(
                CheckStatus.REJECTED, retained, (), ("unverified_interpretation",)
            )
        if len({proposal.binding.occurrence_id for proposal in retained}) != 1:
            return FamilyAssessment(
                CheckStatus.REJECTED, retained, (), ("alternative_occurrence_mismatch",)
            )
        if len(retained) != 1:
            return FamilyAssessment(
                CheckStatus.AMBIGUOUS, retained, (), ("unresolved_interpretation_family",)
            )
        observation = self.to_observation(retained[0])
        if observation is None:
            return FamilyAssessment(CheckStatus.PENDING, retained, (), checks[0].reasons)
        return FamilyAssessment(CheckStatus.ACCEPTED, retained, (observation,), ())

    def application_assessment(
        self, noun: str, *, alternatives: tuple[str, ...] = ()
    ) -> ApplicationAssessment:
        """Name unmet application obligations; bare strings supply no truth bits.

        This is only the source-described four-condition fragment. Nominality,
        singularity, requested case and complete disambiguation are not proved.
        Caller-supplied alternative names can add possibilities, never erase the
        alternatives attested by this policy.
        """
        foundation.require_foundation('nabt.learning.arabic_six_nouns.sixnounpilot.application_assessment')
        if len(alternatives) > 32:
            raise resource_limit("application alternatives exceed resource budget")
        if any(not isinstance(name, str) or not name.strip() for name in alternatives):
            raise ValueError("invalid application alternative")
        ledger = EvidenceLedger(len(APPLICATION_PREDICATES))
        if noun not in _LEXEMES:
            return ApplicationAssessment(
                noun,
                "no_matching_rule",
                0,
                ledger,
                None,
                (),
                alternatives,
                (),
                "no matching lexical entry; an empty rule lookup grants no license",
            )
        required = 3 | (4 if noun == "ذو" else 0) | (8 if noun == "فم" else 0)
        decision = evaluate_license(required, ledger)
        missing = tuple(
            name
            for index, name in enumerate(APPLICATION_PREDICATES)
            if decision.missing & (1 << index)
        )
        contexts = [self._context("alfiyya_idafa")]
        readings = ["tamam"]
        if noun in ("أب", "أخ", "حم"):
            readings += ["qasr", "naqs"]
            contexts.append(self._context("alfiyya_qasr"))
        if noun == "هن":
            readings.append("naqs_preferred_not_exclusive")
            contexts.append(self._context("alfiyya_han_preference"))
        if noun in ("ذو", "فم"):
            contexts.append(self._context("alfiyya_special_conditions"))
        if noun == "ذو":
            readings.append("relative_pronoun")
            contexts.append(self._context("qatr_dhu_relative"))
        retained = tuple(dict.fromkeys((*readings, *alternatives)))
        return ApplicationAssessment(
            noun,
            "pending",
            required,
            ledger,
            decision,
            missing,
            retained,
            tuple(contexts),
            "source-described prerequisites only; bare form does not establish nominality, singularity, non-diminutive form, case or semantic reading",
        )


def default_pilot() -> SixNounPilot:
    """Return a fresh, pinned snapshot using installed NABT package resources.

    No current working directory, external repository, download, or caller
    manifest is consulted. Every proposal is replayed again when consumed.
    """
    return SixNounPilot.from_package()


__all__ = [
    "APPLICATION_PREDICATES",
    "APPROVED_SOURCE_PINS",
    "ApplicationAssessment",
    "CHECKER_VERSION",
    "FamilyAssessment",
    "POLICY_ID",
    "SixNounPilot",
    "default_pilot",
    "observation_schema",
    "prescription_schema",
    "read_observed_cue",
    "read_observed_ending",
    "read_prescription_marker",
    "read_prescription_operation",
]
