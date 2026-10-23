"""Source-bound evidence records and a small, explicit license calculation.

Content hashes bind bytes to a selected pin; they do not prove a book truthful.
The generic admission function below compares a proposal with a *replayed*
record. A domain adapter must independently reopen/check its approved sources
before supplying that record. Neither a receipt nor a caller-created dataclass
is an authority token. No ProofRank or Certificate is issued here.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, fields
from enum import Enum
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from types import MappingProxyType

from nabt.errors import resource_limit

MAX_SOURCE_BYTES = 8_000_000
MAX_EVIDENCE_WIDTH = 32


def content_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity_digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return content_digest(encoded.encode("utf-8"))


def _nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def _natural(value: int, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer, not a Boolean")


def _sha256(value: str, name: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be a complete lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True)
class SourceBlob:
    """An immutable original byte sequence. Its computed hash grants no trust."""

    source_id: str
    raw_bytes: bytes
    sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if re.fullmatch(r"[a-z][a-z0-9_]*", self.source_id) is None:
            raise ValueError("invalid source identity")
        if not isinstance(self.raw_bytes, bytes) or not self.raw_bytes:
            raise ValueError("source must be a nonempty byte sequence")
        if len(self.raw_bytes) > MAX_SOURCE_BYTES:
            raise resource_limit("source byte budget exceeded")
        self.raw_bytes.decode("utf-8", errors="strict")
        object.__setattr__(self, "sha256", content_digest(self.raw_bytes))


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """A nonempty half-open interval in the original UTF-8 bytes."""

    source_id: str
    source_sha256: str
    start: int
    end: int
    span_sha256: str

    def __post_init__(self) -> None:
        _nonempty(self.source_id, "source_id")
        _sha256(self.source_sha256, "source_sha256")
        _sha256(self.span_sha256, "span_sha256")
        _natural(self.start, "span start")
        _natural(self.end, "span end")
        if self.end <= self.start:
            raise ValueError("source span must be nonempty")

    def extract(self, source: SourceBlob) -> bytes:
        if source.source_id != self.source_id or source.sha256 != self.source_sha256:
            raise ValueError("source identity or source digest mismatch")
        if self.end > len(source.raw_bytes):
            raise ValueError("source span exceeds original bytes")
        raw = source.raw_bytes[self.start : self.end]
        raw.decode("utf-8", errors="strict")
        if content_digest(raw) != self.span_sha256:
            raise ValueError("source span digest mismatch")
        return raw


@dataclass(frozen=True, slots=True)
class SourceStore:
    """Checked original snapshots; later changes on disk do not alter a snapshot."""

    sources: Mapping[str, SourceBlob]

    def __post_init__(self) -> None:
        copied = dict(self.sources)
        if any(key != source.source_id for key, source in copied.items()):
            raise ValueError("source index identity mismatch")
        object.__setattr__(self, "sources", MappingProxyType(copied))

    @classmethod
    def from_directory(
        cls, directory: str | Path, approved_pins: Mapping[str, str]
    ) -> SourceStore:
        """Pins must come from the application's policy, never from a proposal."""
        return cls._from_location(Path(directory), approved_pins)

    @classmethod
    def from_resources(
        cls, package: str, directory: str, approved_pins: Mapping[str, str]
    ) -> SourceStore:
        """Read installed package data, including zip-backed package resources.

        Resource locations do not confer authority. As with ``from_directory``,
        the application supplies its independently selected source pins.
        """
        return cls._from_location(files(package).joinpath(directory), approved_pins)

    @classmethod
    def _from_location(
        cls, directory: Path | Traversable, approved_pins: Mapping[str, str]
    ) -> SourceStore:
        sources: dict[str, SourceBlob] = {}
        for source_id, expected in approved_pins.items():
            if re.fullmatch(r"[a-z][a-z0-9_]*", source_id) is None:
                raise ValueError("invalid approved source identity")
            _sha256(expected, "approved source pin")
            path = directory.joinpath(f"{source_id}.txt")
            # Bound the actual read for both ordinary files and package archives.
            # A file's prior size is not a reliable bound on a concurrent read.
            with path.open("rb") as source_file:
                raw = source_file.read(MAX_SOURCE_BYTES + 1)
            if len(raw) > MAX_SOURCE_BYTES:
                raise resource_limit("source byte budget exceeded")
            source = SourceBlob(source_id, raw)
            if source.sha256 != expected:
                raise ValueError(f"source digest mismatch: {source_id}")
            sources[source_id] = source
        return cls(sources)

    def span(self, source_id: str, start: int, end: int) -> SourceSpan:
        source = self.sources[source_id]
        _natural(start, "span start")
        _natural(end, "span end")
        if not start < end <= len(source.raw_bytes):
            raise ValueError("invalid source span bounds")
        raw = source.raw_bytes[start:end]
        raw.decode("utf-8", errors="strict")
        return SourceSpan(source_id, source.sha256, start, end, content_digest(raw))

    def text(self, span: SourceSpan) -> str:
        return span.extract(self.sources[span.source_id]).decode("utf-8")


@dataclass(frozen=True, slots=True)
class EvidenceBinding:
    occurrence_id: str
    reading_id: str
    source_sha256: str
    context_sha256: str
    definition_id: str
    policy_id: str
    schema_id: str
    checker_version: str

    def __post_init__(self) -> None:
        for item in fields(self):
            _nonempty(getattr(self, item.name), item.name)
        _sha256(self.source_sha256, "source_sha256")
        _sha256(self.context_sha256, "context_sha256")


@dataclass(frozen=True, slots=True)
class EvidenceProposal:
    """Untrusted candidate. There is deliberately no passed/rank/trusted field."""

    record_id: str
    binding: EvidenceBinding
    known: int
    value: int
    label: bool | None

    def __post_init__(self) -> None:
        _nonempty(self.record_id, "record_id")
        _natural(self.known, "known mask")
        _natural(self.value, "value mask")
        if self.value & ~self.known:
            raise ValueError("unknown bits may not carry values")
        if self.label is not None and type(self.label) is not bool:
            raise ValueError("label must be bool or None")


@dataclass(frozen=True, slots=True)
class ReplayRecord:
    """A domain adapter's source projection, including distinct input/output spans."""

    record_id: str
    kind: str
    binding: EvidenceBinding
    known: int
    value: int
    label: bool | None
    width: int
    context_span: SourceSpan
    cue_spans: tuple[SourceSpan, ...]
    target_span: SourceSpan
    marker_span: SourceSpan
    cue: str
    target: str
    marker: str
    interpretation_note: str

    def __post_init__(self) -> None:
        _nonempty(self.record_id, "record_id")
        _nonempty(self.kind, "kind")
        _natural(self.width, "record width")
        if not 1 <= self.width <= MAX_EVIDENCE_WIDTH:
            raise ValueError("invalid replay record width")
        self.proposal()  # Check masks/label without assuming a well-typed caller.
        if self.known >= 1 << self.width:
            raise ValueError("record feature bit outside schema")
        object.__setattr__(self, "cue_spans", tuple(self.cue_spans))
        if not self.cue_spans:
            raise ValueError("a source replay must retain its input cue spans")

    def proposal(self) -> EvidenceProposal:
        return EvidenceProposal(self.record_id, self.binding, self.known, self.value, self.label)


class CheckStatus(str, Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class CheckResult:
    status: CheckStatus
    reasons: tuple[str, ...]
    record: ReplayRecord | None = None
    receipt_id: str | None = None

    @property
    def accepted(self) -> bool:
        return self.status is CheckStatus.ACCEPTED


def compare_replayed_record(expected: ReplayRecord, proposal: EvidenceProposal) -> CheckResult:
    """Pure binding check; callers must obtain expected by approved source replay.

    Unknown/partial proposals are named pending, never ready observations.
    A syntactically well-formed receipt is not a substitute for this comparison.
    """
    reasons = []
    if proposal.record_id != expected.record_id:
        reasons.append("record_identity_mismatch")
    for item in fields(EvidenceBinding):
        if getattr(proposal.binding, item.name) != getattr(expected.binding, item.name):
            reasons.append(f"binding_mismatch:{item.name}")
    full = (1 << expected.width) - 1
    if proposal.known & ~full:
        reasons.append("feature_mask_outside_schema")
    if proposal.known & ~expected.known:
        reasons.append("unsupported_known_feature")
    if (proposal.value ^ expected.value) & proposal.known:
        reasons.append("feature_value_mismatch")
    if proposal.label is not None and proposal.label is not expected.label:
        reasons.append("label_mismatch")
    if reasons:
        return CheckResult(CheckStatus.REJECTED, tuple(reasons))
    pending = []
    if proposal.known != full:
        pending.append("unknown_properties")
    if proposal.label is None:
        pending.append("unknown_label")
    if pending:
        return CheckResult(CheckStatus.PENDING, tuple(pending))
    return CheckResult(
        CheckStatus.ACCEPTED,
        (),
        expected,
        identity_digest(("nabt-source-receipt-v1", asdict(expected))),
    )


class LicenseStatus(str, Enum):
    LICENSED = "licensed"
    PENDING = "pending"
    REJECTED = "rejected"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class EvidenceLedger:
    """Finite evidence arithmetic, not authority for caller-supplied bits.

    A bit may occur in both masks. That conflict must not be collapsed to true.
    Domain adapters are responsible for binding actual witnesses to each bit.
    """

    width: int
    positive: int = 0
    negative: int = 0

    def __post_init__(self) -> None:
        _natural(self.width, "ledger width")
        _natural(self.positive, "positive mask")
        _natural(self.negative, "negative mask")
        if not 1 <= self.width <= MAX_EVIDENCE_WIDTH:
            raise ValueError("invalid ledger width")
        if (self.positive | self.negative) >= 1 << self.width:
            raise ValueError("ledger bit outside schema")


@dataclass(frozen=True, slots=True)
class LicenseDecision:
    status: LicenseStatus
    missing: int
    conflicts: int
    negative: int

    @property
    def licensed(self) -> bool:
        return self.status is LicenseStatus.LICENSED


def evaluate_license(required: int, ledger: EvidenceLedger) -> LicenseDecision:
    """Conjunction of required atoms, checking relevant conflict before negation.

    Empty requirements are arithmetically satisfied. An application must check
    that a matching rule exists *before* using this operation. Conflict outside
    the required set remains in the ledger but does not decide this claim.
    """
    _natural(required, "required mask")
    if required >= 1 << ledger.width:
        raise ValueError("required bit outside schema")
    conflicts = required & ledger.positive & ledger.negative
    negative = required & ledger.negative & ~ledger.positive
    missing = required & ~(ledger.positive | ledger.negative)
    if conflicts:
        status = LicenseStatus.CONFLICT
    elif negative:
        status = LicenseStatus.REJECTED
    elif missing:
        status = LicenseStatus.PENDING
    else:
        status = LicenseStatus.LICENSED
    return LicenseDecision(status, missing, conflicts, negative)


__all__ = [
    "CheckResult",
    "CheckStatus",
    "EvidenceBinding",
    "EvidenceLedger",
    "EvidenceProposal",
    "LicenseDecision",
    "LicenseStatus",
    "ReplayRecord",
    "SourceBlob",
    "SourceSpan",
    "SourceStore",
    "compare_replayed_record",
    "content_digest",
    "evaluate_license",
    "identity_digest",
]
