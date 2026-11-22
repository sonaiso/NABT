"""Bounded v0.5 epistemic transition guardian (stdlib only).

This is a record/transition validator, not an empirical truth oracle. An
accepted evidence review is an external, attributed assessment. The guardian
checks its identity, scope, version, trace and applicability; it does not prove
that the reviewer or instrument is correct. No certainty is inferred from a
sensory channel, an existence label, a source count or a policy name.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping


def canonical(value: Any) -> str:
    """Canonical representation for this prototype; not RFC 8785/JCS."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utc_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("A timezone-aware timestamp is required")
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class PolicyProfile:
    id: str = "rational_method_nabhani_candidate"
    version: str = "0.5.0"
    framework: str = "Attributed interpretation; not a universal scientific claim"
    source_review_status: str = "UNVERIFIED"
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Claim:
    id: str
    domain: str
    target_id: str
    expression: str
    kind: str = "ATOM"
    antecedent_id: str | None = None
    consequent_id: str | None = None
    reported_claim_id: str | None = None


@dataclass(frozen=True)
class Evidence:
    id: str
    version: int
    claim_id: str
    domain: str
    target_id: str
    kind: str
    source_ref: str
    review_ref: str
    review_status: str
    trace: tuple[str, ...]
    payload: str
    expires_at: str | None = None
    blocking_residuals: tuple[str, ...] = ()


@dataclass(frozen=True)
class Assumption:
    id: str
    claim_id: str
    kind: str = "HYPOTHESIS"
    source_ref: str = "declared scenario"


@dataclass(frozen=True)
class Assessment:
    id: str
    claim_id: str
    operation: str
    status: str
    verdict: str
    assumptions: tuple[str, ...]
    evidence_versions: tuple[tuple[str, int], ...]
    parent_ids: tuple[str, ...]
    policy_id: str
    policy_version: str
    policy_source_status: str
    framework_rank: str
    as_of: str
    reasons: tuple[str, ...]
    trace: tuple[str, ...]


class Guardian:
    """Owns registrations and assesses only the declared bounded operations."""

    def __init__(self, policy: PolicyProfile | None = None):
        self.policy = policy or PolicyProfile()
        self._initial_policy = self.policy
        self.claims: dict[str, Claim] = {}
        self.evidence: dict[str, Evidence] = {}
        self.evidence_history: dict[tuple[str, int], Evidence] = {}
        self.assumptions: dict[str, Assumption] = {}
        self.assessments: dict[str, Assessment] = {}
        self.events: list[dict[str, Any]] = []

    def _event(self, action: str, payload: Mapping[str, Any], result: Any = None) -> None:
        event = {"sequence": len(self.events), "action": action,
                 "payload": dict(payload), "result": result,
                 "previous_hash": self.events[-1]["event_hash"] if self.events else None}
        event["event_hash"] = digest(event)
        # A round trip detaches caller-owned mutable objects.
        self.events.append(json.loads(canonical(event)))

    def register_claim(self, claim: Claim) -> None:
        if not all((claim.id, claim.domain, claim.target_id, claim.expression)):
            raise ValueError("Incomplete claim identity or scope")
        if claim.kind not in {"ATOM", "EXISTENCE", "IMPLIES", "REPORT"}:
            raise ValueError("Unsupported claim kind")
        if claim.id in self.claims and self.claims[claim.id] != claim:
            raise ValueError("Claim identity collision: use a new claim/revision")
        if claim.kind == "IMPLIES":
            if not claim.antecedent_id or not claim.consequent_id:
                raise ValueError("Implication needs registered operands")
            for operand_id in (claim.antecedent_id, claim.consequent_id):
                operand = self.claims.get(operand_id)
                if operand is None:
                    raise ValueError("Unknown implication operand")
                if (operand.domain, operand.target_id) != (claim.domain, claim.target_id):
                    raise ValueError("This bounded implication rule is within one scope")
        if claim.kind == "REPORT" and claim.reported_claim_id not in self.claims:
            raise ValueError("Unknown quoted claim")
        self.claims[claim.id] = claim
        self._event("register_claim", asdict(claim))

    def register_evidence(self, evidence: Evidence) -> None:
        if evidence.claim_id not in self.claims:
            raise ValueError("Unknown supported claim")
        if evidence.version < 1 or not evidence.id:
            raise ValueError("Invalid evidence identity/version")
        if evidence.review_status not in {"ACCEPTED", "UNREVIEWED", "REJECTED"}:
            raise ValueError("Unknown external review status")
        if evidence.expires_at is not None:
            utc_time(evidence.expires_at)
        current = self.evidence.get(evidence.id)
        if current and evidence.version <= current.version:
            raise ValueError("Evidence revisions must strictly increase the version")
        if current and (current.claim_id, current.domain, current.target_id) != (
                evidence.claim_id, evidence.domain, evidence.target_id):
            raise ValueError("Evidence identity changed: use a new evidence ID")
        self.evidence[evidence.id] = evidence
        self.evidence_history[(evidence.id, evidence.version)] = evidence
        self._event("register_evidence", asdict(evidence))

    def revise_policy(self, policy: PolicyProfile) -> None:
        if policy.id == self.policy.id and policy.version == self.policy.version:
            raise ValueError("A policy revision requires a new version")
        self.policy = policy
        self._event("revise_policy", asdict(policy))

    def _result(self, claim_id: str, operation: str, status: str, verdict: str,
                as_of: str, reasons: tuple[str, ...] = (),
                assumptions: tuple[str, ...] = (),
                versions: tuple[tuple[str, int], ...] = (),
                parents: tuple[str, ...] = (), trace: tuple[str, ...] = ()) -> Assessment:
        utc_time(as_of)
        record = dict(claim_id=claim_id, operation=operation, status=status,
                      verdict=verdict, assumptions=tuple(sorted(set(assumptions))),
                      evidence_versions=tuple(sorted(set(versions))),
                      parent_ids=parents, policy_id=self.policy.id,
                      policy_version=self.policy.version,
                      policy_source_status=self.policy.source_review_status,
                      framework_rank="NOT_ASSIGNED", as_of=as_of,
                      reasons=reasons, trace=tuple(sorted(set(trace))))
        assessment_id = "a_" + digest({"record": record, "event": len(self.events)})[:24]
        result = Assessment(id=assessment_id, **record)
        self.assessments[result.id] = result
        return result

    def _evidence_issues(self, claim: Claim, evidence: Evidence,
                         as_of: str) -> list[tuple[str, str]]:
        issues: list[tuple[str, str]] = []
        if evidence.claim_id != claim.id:
            issues.append(("BLOCK", "EVIDENCE_CLAIM_MISMATCH"))
        if evidence.domain != claim.domain:
            issues.append(("BLOCK", "EVIDENCE_DOMAIN_MISMATCH"))
        if evidence.target_id != claim.target_id:
            issues.append(("BLOCK", "EVIDENCE_TARGET_MISMATCH"))
        if evidence.blocking_residuals:
            issues.append(("BLOCK", "BLOCKING_RESIDUAL:" + ",".join(evidence.blocking_residuals)))
        if evidence.review_status == "REJECTED":
            issues.append(("BLOCK", "EXTERNAL_REVIEW_REJECTED"))
        elif evidence.review_status != "ACCEPTED":
            issues.append(("DEFER", "EXTERNAL_REVIEW_UNRESOLVED"))
        if not evidence.trace:
            issues.append(("DEFER", "MISSING_TRACE"))
        if not evidence.source_ref or not evidence.review_ref or not evidence.payload:
            issues.append(("DEFER", "MISSING_SOURCE_REVIEW_OR_PAYLOAD"))
        if evidence.expires_at and utc_time(as_of) >= utc_time(evidence.expires_at):
            issues.append(("DEFER", "EVIDENCE_EXPIRED"))
        return issues

    def admit(self, claim_id: str, evidence_ids: tuple[str, ...], as_of: str) -> Assessment:
        """Admit for evidence-backed use, not certify correspondence to reality."""
        utc_time(as_of)
        claim = self.claims[claim_id]
        issues: list[tuple[str, str]] = []
        versions: list[tuple[str, int]] = []
        trace: list[str] = []
        if not evidence_ids:
            issues.append(("DEFER", "NO_EVIDENCE"))
        for evidence_id in evidence_ids:
            item = self.evidence.get(evidence_id)
            if item is None:
                issues.append(("DEFER", "UNKNOWN_EVIDENCE:" + evidence_id))
                continue
            issues.extend(self._evidence_issues(claim, item, as_of))
            versions.append((item.id, item.version))
            trace.extend(item.trace)
        status = "BLOCK" if any(x[0] == "BLOCK" for x in issues) else "DEFER" if issues else "ALLOW"
        verdict = "SUPPORTED_BY_REGISTERED_REVIEW" if status == "ALLOW" else "UNASSESSED"
        result = self._result(claim_id, "FACTUAL_ADMISSION", status, verdict, as_of,
                              tuple(x[1] for x in issues), versions=tuple(versions),
                              trace=tuple(trace))
        self._event("admit", {"claim_id": claim_id, "evidence_ids": evidence_ids,
                              "as_of": as_of}, asdict(result))
        return result

    def assume(self, assumption: Assumption, as_of: str) -> Assessment:
        # Validate the entire request before changing any in-memory register.
        utc_time(as_of)
        if not assumption.id.strip() or not assumption.source_ref.strip():
            raise ValueError("Assumption ID and source reference are required")
        if assumption.claim_id not in self.claims:
            raise ValueError("Unknown assumed claim")
        if assumption.kind not in {"HYPOTHESIS", "OPINION", "SCENARIO_ASSUMPTION"}:
            raise ValueError("Unsupported assumption kind")
        if assumption.id in self.assumptions:
            raise ValueError("Assumption ID already exists")
        self.assumptions[assumption.id] = assumption
        result = self._result(assumption.claim_id, "ASSUMPTION_REGISTRATION", "ALLOW",
                              "CONDITIONAL_ONLY", as_of, assumptions=(assumption.id,),
                              trace=(assumption.source_ref,))
        self._event("assume", {"assumption": asdict(assumption), "as_of": as_of}, asdict(result))
        return result

    def current_issues(self, assessment_id: str, as_of: str) -> tuple[str, ...]:
        """Assessments remain in history; changes suspend their current usability."""
        utc_time(as_of)
        item = self.assessments.get(assessment_id)
        if item is None:
            return ("UNKNOWN_ASSESSMENT",)
        issues: list[str] = []
        if item.status != "ALLOW":
            issues.append("PREDECESSOR_NOT_ALLOWED")
        if utc_time(as_of) < utc_time(item.as_of):
            issues.append("ASSESSMENT_NOT_YET_AVAILABLE")
        if (item.policy_id, item.policy_version) != (self.policy.id, self.policy.version):
            issues.append("POLICY_VERSION_CHANGED")
        for evidence_id, version in item.evidence_versions:
            current = self.evidence.get(evidence_id)
            if current is None or current.version != version:
                issues.append("EVIDENCE_VERSION_CHANGED:" + evidence_id)
            elif current.expires_at and utc_time(as_of) >= utc_time(current.expires_at):
                issues.append("EVIDENCE_EXPIRED:" + evidence_id)
        return tuple(sorted(set(issues)))

    def modus_ponens(self, antecedent_result_id: str, implication_result_id: str,
                     mode: str, as_of: str) -> Assessment:
        if mode not in {"FACTUAL", "CONDITIONAL"}:
            raise ValueError("Unknown inference mode")
        p = self.assessments[antecedent_result_id]
        rule = self.assessments[implication_result_id]
        rule_claim = self.claims[rule.claim_id]
        assumptions = tuple(sorted(set(p.assumptions + rule.assumptions)))
        versions = tuple(sorted(set(p.evidence_versions + rule.evidence_versions)))
        issues: list[tuple[str, str]] = []
        for item in (p, rule):
            for problem in self.current_issues(item.id, as_of):
                issues.append(("DEFER", problem))
            if item.verdict not in {"SUPPORTED_BY_REGISTERED_REVIEW", "CONDITIONAL_ONLY"}:
                issues.append(("BLOCK", "PREDECESSOR_IS_NOT_AN_INFERENCE_PREMISE"))
        if rule_claim.kind != "IMPLIES" or rule_claim.antecedent_id != p.claim_id:
            issues.append(("BLOCK", "MODUS_PONENS_OPERAND_MISMATCH"))
        if mode == "FACTUAL" and assumptions:
            issues.append(("BLOCK", "UNDISCHARGED_ASSUMPTIONS"))
        conclusion_id = rule_claim.consequent_id or rule.claim_id
        status = "BLOCK" if any(x[0] == "BLOCK" for x in issues) else "DEFER" if issues else "ALLOW"
        verdict = ("CONDITIONAL_ONLY" if assumptions or mode == "CONDITIONAL"
                   else "SUPPORTED_BY_REGISTERED_REVIEW") if status == "ALLOW" else "UNASSESSED"
        result = self._result(conclusion_id, "MODUS_PONENS_" + mode, status, verdict,
                              as_of, tuple(x[1] for x in issues), assumptions,
                              versions, (p.id, rule.id), p.trace + rule.trace)
        self._event("modus_ponens", {"antecedent_result_id": antecedent_result_id,
                                    "implication_result_id": implication_result_id,
                                    "mode": mode, "as_of": as_of}, asdict(result))
        return result

    def linguistic_link(self, evidence_id: str, utterance_ref: str,
                         usage_ref: str, mental_necessity_ref: str,
                         as_of: str) -> Assessment:
        evidence = self.evidence[evidence_id]
        claim = self.claims[evidence.claim_id]
        issues = self._evidence_issues(claim, evidence, as_of)
        if evidence.kind != "MENTAL_LINGUISTIC":
            issues.append(("BLOCK", "EXTERNAL_RELATION_IS_NOT_LEXICAL_ILTIZAM"))
        if not utterance_ref or not usage_ref or not mental_necessity_ref:
            issues.append(("DEFER", "MISSING_UTTERANCE_USAGE_OR_MENTAL_RELATION"))
        status = "BLOCK" if any(x[0] == "BLOCK" for x in issues) else "DEFER" if issues else "ALLOW"
        result = self._result(claim.id, "LINGUISTIC_LINK_REGISTRATION", status,
                              "LINGUISTIC_LINK_CANDIDATE" if status == "ALLOW" else "UNASSESSED",
                              as_of, tuple(x[1] for x in issues),
                              versions=((evidence.id, evidence.version),),
                              trace=evidence.trace + tuple(x for x in
                                  (utterance_ref, usage_ref, mental_necessity_ref) if x))
        self._event("linguistic_link", {"evidence_id": evidence_id,
                    "utterance_ref": utterance_ref, "usage_ref": usage_ref,
                    "mental_necessity_ref": mental_necessity_ref, "as_of": as_of}, asdict(result))
        return result

    def gamma(self, as_of: str, domain: str | None = None,
              target_id: str | None = None) -> tuple[str, ...]:
        """Scope-filtered admission inventory, not a globally consistent theory.

        Without filters this is an inventory across scopes, never permission to
        combine those scopes in an inference. No counter-evidence solver exists.
        """
        utc_time(as_of)
        return tuple(x.id for x in self.assessments.values()
                     if x.status == "ALLOW" and not x.assumptions
                     and x.verdict == "SUPPORTED_BY_REGISTERED_REVIEW"
                     and (domain is None or self.claims[x.claim_id].domain == domain)
                     and (target_id is None or self.claims[x.claim_id].target_id == target_id)
                     and not self.current_issues(x.id, as_of))

    def delta(self) -> tuple[str, ...]:
        return tuple(self.assumptions)

    def export_log(self) -> dict[str, Any]:
        return {"format": "bounded-epistemic-audit-v0.5", "initial_policy": asdict(self._initial_policy),
                "events": json.loads(canonical(self.events))}

    @classmethod
    def replay(cls, log: Mapping[str, Any]) -> Guardian:
        if log.get("format") != "bounded-epistemic-audit-v0.5":
            raise ValueError("Unsupported audit format")
        policy = _from_dict(PolicyProfile, log["initial_policy"])
        engine = cls(policy)
        previous_hash: str | None = None
        for sequence, stored in enumerate(log["events"]):
            envelope = {k: v for k, v in stored.items() if k != "event_hash"}
            if (stored.get("sequence") != sequence or stored.get("previous_hash") != previous_hash
                    or digest(envelope) != stored.get("event_hash")):
                raise ValueError("Audit integrity failure")
            action, payload = stored["action"], stored["payload"]
            if action == "register_claim":
                engine.register_claim(_from_dict(Claim, payload))
            elif action == "register_evidence":
                engine.register_evidence(_from_dict(Evidence, payload))
            elif action == "revise_policy":
                engine.revise_policy(_from_dict(PolicyProfile, payload))
            elif action == "admit":
                engine.admit(payload["claim_id"], tuple(payload["evidence_ids"]), payload["as_of"])
            elif action == "assume":
                engine.assume(_from_dict(Assumption, payload["assumption"]), payload["as_of"])
            elif action == "modus_ponens":
                engine.modus_ponens(**payload)
            elif action == "linguistic_link":
                engine.linguistic_link(**payload)
            else:
                raise ValueError("Unknown replay action")
            if canonical(engine.events[-1]) != canonical(stored):
                raise ValueError("Replay result mismatch")
            previous_hash = stored["event_hash"]
        return engine


def _from_dict(cls: type, data: Mapping[str, Any]) -> Any:
    known = {item.name for item in fields(cls)}
    if set(data) - known:
        raise ValueError("Unexpected contract fields")
    value = dict(data)
    for name in ("source_refs", "trace", "blocking_residuals"):
        if name in value:
            value[name] = tuple(value[name])
    return cls(**value)
