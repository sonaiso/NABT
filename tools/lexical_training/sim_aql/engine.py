"""SIM-AQL 0.2: bounded, typed workflow over an unchanged v0.5 Guardian.

Motive belongs to planning/audit. The deterministic evaluator has no motive
argument or mutable instance state. External reviews and rank certificates are
attributed inputs, not proofs of truth, independence, or human cognition.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import Any, Mapping

from .guardian import (Assessment, Assumption, Claim, Evidence, Guardian,
                     PolicyProfile, canonical, digest, utc_time)

VERSION = "0.2.0"
INTENTS = {"DESCRIBE_REALITY", "ASSESS_SUITABILITY", "ISSUE_NORMATIVE", "REPORT_NORMATIVE"}
ASPECTS = {"EXISTENCE", "PROPERTY_EXISTENCE", "PROPERTY", "ESSENCE", "SUITABILITY", "REPORT_OCCURRENCE", "LINGUISTIC_RELATION"}
SPEC_ONLY = {"CLASSIFICATION", "OBSERVATION_INDUCTION", "CONTROLLED_EXPERIMENT",
             "LEGAL_QIYAS", "RESEMBLANCE_ANALOGY", "EMPIRICAL_CAUSAL_ANALOGY"}


@dataclass(frozen=True)
class Motive:
    id: str
    description: str
    classification: str = "UNCLASSIFIED"
    classification_source_ref: str = ""


@dataclass(frozen=True)
class Reception:
    id: str
    payload: str
    channel: str
    source_ref: str
    received_at: str


@dataclass(frozen=True)
class SubjectState:
    id: str
    subject_id: str
    description: str
    source_ref: str
    as_of: str


@dataclass(frozen=True)
class Question:
    id: str
    claim_id: str
    domain: str
    target_id: str
    intent: str
    aspect: str
    research_mode: str = "TENTATIVE"


@dataclass(frozen=True)
class ClaimScope:
    claim_id: str
    intent: str
    aspect: str
    subject_state_id: str | None = None
    subject_id: str | None = None


@dataclass(frozen=True)
class EvidenceRecord:
    evidence: Evidence
    role: str = "INDEPENDENT_REVIEW"
    prior_id: str | None = None
    subject_state_id: str | None = None
    subject_state_fingerprint: str | None = None
    independence_review_ref: str = ""
    declared_prior_dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class RankCertificate:
    id: str
    claim_id: str
    profile_id: str
    profile_version: str
    rank: str
    source_ref: str
    review_ref: str
    review_status: str
    trace: tuple[str, ...]
    valid_from: str
    expires_at: str | None = None
    domain: str = ""
    target_id: str = ""
    claim_fingerprint: str = ""
    policy_fingerprint: str = ""
    evidence_bindings: tuple[tuple[str, int, str], ...] = ()


@dataclass(frozen=True)
class PriorRecord:
    id: str
    claim_id: str
    kind: str
    source_ref: str
    evidence_ids: tuple[str, ...]
    claimed_rank: str = "UNRANKED"
    rank_certificate_id: str | None = None


@dataclass(frozen=True)
class AffectRecord:
    id: str
    label: str
    subject_state_id: str
    source_ref: str


@dataclass(frozen=True)
class LexicalBridge:
    id: str
    claim_id: str
    namespace: str
    relation: str
    signifier: str
    sense_id: str
    attestation_kind: str
    source_ref: str
    locator: str
    context: str
    review_ref: str
    review_status: str
    usage_ref: str
    necessity_ref: str = ""
    stipulation_ref: str = ""
    local_namespace: str = ""


@dataclass(frozen=True)
class Opposition:
    id: str
    disputed_claim_id: str
    opposing_claim_id: str
    evidence_ids: tuple[str, ...]
    relation_review_ref: str


@dataclass(frozen=True)
class Step:
    id: str
    operation: str
    claim_id: str
    face_ref: str
    evidence_ids: tuple[str, ...] = ()
    prior_id: str | None = None
    assumption_id: str | None = None
    antecedent_step_id: str | None = None
    implication_step_id: str | None = None
    inference_mode: str = "FACTUAL"
    bridge_id: str | None = None


@dataclass(frozen=True)
class EvaluationContext:
    question: Question
    reception: Reception
    claims: tuple[Claim, ...]
    scopes: tuple[ClaimScope, ...]
    evidence: tuple[EvidenceRecord, ...]
    steps: tuple[Step, ...]
    final_step_id: str
    as_of: str
    policy: PolicyProfile = PolicyProfile()
    scope_profile: str = "PRE_SHAR"
    protocol_version: str = VERSION
    assumptions: tuple[Assumption, ...] = ()
    priors: tuple[PriorRecord, ...] = ()
    rank_certificates: tuple[RankCertificate, ...] = ()
    affect: tuple[AffectRecord, ...] = ()
    bridges: tuple[LexicalBridge, ...] = ()
    oppositions: tuple[Opposition, ...] = ()
    subject_state: SubjectState | None = None
    untrusted_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecallDecision:
    prior_id: str
    status: str
    reason: str
    rank_certificate_id: str | None = None


@dataclass(frozen=True)
class StageRecord:
    stage: str
    status: str
    reasons: tuple[str, ...] = ()
    refs: tuple[str, ...] = ()
    details: str = ""


@dataclass(frozen=True)
class EpistemicDecision:
    question: Question
    claim_expression: str
    status: str
    verdict: str
    framework_rank: str
    assumptions: tuple[str, ...]
    evidence_versions: tuple[tuple[str, int], ...]
    evidence_fingerprints: tuple[tuple[str, str], ...]
    assumption_fingerprints: tuple[tuple[str, str], ...]
    used_claim_fingerprints: tuple[tuple[str, str], ...]
    justification_fingerprints: tuple[tuple[str, str], ...]
    reasons: tuple[str, ...]
    policy_id: str
    policy_version: str
    policy_fingerprint: str
    scope_profile: str
    protocol_version: str
    as_of: str
    subject_state: SubjectState | None
    reception_fingerprint: str
    conditional: bool
    opposition_ids: tuple[str, ...]
    opposition_fingerprints: tuple[tuple[str, str], ...]
    used_claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class Evaluation:
    decision: EpistemicDecision
    stages: tuple[StageRecord, ...]
    recall: tuple[RecallDecision, ...]
    guardian_log_json: str


@dataclass(frozen=True)
class Run:
    format: str
    input_context_json: str
    motive_json: str
    evaluation: Evaluation
    audit_digest: str


@dataclass(frozen=True)
class _StepResult:
    claim_id: str
    status: str
    verdict: str
    reasons: tuple[str, ...]
    assumption_ids: tuple[str, ...] = ()
    evidence_versions: tuple[tuple[str, int], ...] = ()
    used_claim_ids: tuple[str, ...] = ()
    guardian_assessment_id: str | None = None


def epistemic_projection(value: Evaluation | Run | EpistemicDecision) -> dict[str, Any]:
    """No run ID or motive audit; retains all declared epistemic output fields."""
    if isinstance(value, Run):
        value = value.evaluation
    if isinstance(value, Evaluation):
        value = value.decision
    return asdict(value)


def epistemic_digest(value: Evaluation | Run | EpistemicDecision) -> str:
    return digest(epistemic_projection(value))


def _tuples(cls, value: Mapping[str, Any], names: tuple[str, ...] = ()):
    data = dict(value)
    for name in names:
        if name in data:
            data[name] = (tuple(tuple(x) for x in data[name]) if name == "evidence_bindings"
                          else tuple(data[name]))
    return cls(**data)


def context_from_dict(value: Mapping[str, Any]) -> EvaluationContext:
    """Strict dataclass construction; a JSON round trip detaches caller objects."""
    x = dict(value)
    x["question"] = Question(**x["question"])
    x["reception"] = Reception(**x["reception"])
    x["policy"] = _tuples(PolicyProfile, x.get("policy", {}), ("source_refs",))
    x["claims"] = tuple(Claim(**v) for v in x["claims"])
    x["scopes"] = tuple(ClaimScope(**v) for v in x["scopes"])
    evidences = []
    for record in x["evidence"]:
        r = dict(record)
        r["evidence"] = _tuples(Evidence, r["evidence"], ("trace", "blocking_residuals"))
        r["declared_prior_dependencies"] = tuple(r.get("declared_prior_dependencies", ()))
        evidences.append(EvidenceRecord(**r))
    x["evidence"] = tuple(evidences)
    x["steps"] = tuple(_tuples(Step, v, ("evidence_ids",)) for v in x["steps"])
    for name, cls, tuple_fields in (
        ("assumptions", Assumption, ()), ("priors", PriorRecord, ("evidence_ids",)),
        ("rank_certificates", RankCertificate, ("trace", "evidence_bindings")),
        ("affect", AffectRecord, ()), ("bridges", LexicalBridge, ()),
        ("oppositions", Opposition, ("evidence_ids",))):
        x[name] = tuple(_tuples(cls, v, tuple_fields) for v in x.get(name, ()))
    if x.get("subject_state") is not None:
        x["subject_state"] = SubjectState(**x["subject_state"])
    x["untrusted_labels"] = tuple(x.get("untrusted_labels", ()))
    return EvaluationContext(**x)


def _snapshot(context: EvaluationContext) -> EvaluationContext:
    return context_from_dict(json.loads(canonical(asdict(context))))


def _unique(items, key):
    result = {}
    for item in items:
        identity = key(item)
        if not identity or identity in result:
            raise ValueError("Duplicate or empty identity")
        result[identity] = item
    return result


def _scope_issue(intent: str, profile: str) -> tuple[str, str] | None:
    if profile != "PRE_SHAR":
        return "DEFER", "UNKNOWN_SCOPE_PROFILE"
    if intent not in INTENTS:
        return "DEFER", "MISSING_OR_UNKNOWN_SCOPE"
    if intent == "ISSUE_NORMATIVE":
        return "BLOCK", "PRE_SHAR_SCOPE"
    return None


def _claim_scope_issue(claim: Claim, scope: ClaimScope,
                       context: EvaluationContext) -> tuple[str, str] | None:
    issue = _scope_issue(scope.intent, context.scope_profile)
    if issue:
        return issue
    if scope.aspect not in ASPECTS:
        return "DEFER", "UNKNOWN_JUDGMENT_ASPECT"
    if scope.intent == "REPORT_NORMATIVE":
        if claim.kind != "REPORT" or scope.aspect != "REPORT_OCCURRENCE":
            return "BLOCK", "REPORT_INTENT_REQUIRES_REPORT_CLAIM"
    elif claim.kind == "REPORT" and scope.aspect != "REPORT_OCCURRENCE":
        return "BLOCK", "REPORT_CLAIM_ASPECT_MISMATCH"
    if scope.intent == "ASSESS_SUITABILITY":
        if scope.aspect != "SUITABILITY":
            return "BLOCK", "SUITABILITY_INTENT_ASPECT_MISMATCH"
        state = context.subject_state
        if state is None or not all((state.id, state.subject_id, state.source_ref, state.description)):
            return "DEFER", "MISSING_SUBJECT_STATE"
        if not scope.subject_id:
            return "DEFER", "MISSING_SUITABILITY_SUBJECT_IDENTITY"
        if scope.subject_id != state.subject_id:
            return "BLOCK", "SUITABILITY_SUBJECT_IDENTITY_MISMATCH"
        if scope.subject_state_id != state.id:
            return "BLOCK", "CLAIM_SUBJECT_STATE_MISMATCH"
        if utc_time(state.as_of) > utc_time(context.as_of):
            return "DEFER", "SUBJECT_STATE_NOT_YET_AVAILABLE"
    elif scope.aspect == "SUITABILITY":
        return "BLOCK", "SUITABILITY_ASPECT_REQUIRES_SUITABILITY_INTENT"
    return None


def _certificate_issue(cert: RankCertificate | None, prior: PriorRecord,
                       context: EvaluationContext) -> str | None:
    if cert is None:
        return "MISSING_EXTERNAL_RANK_REVIEW"
    if (cert.claim_id, cert.profile_id, cert.profile_version, cert.rank) != (
            prior.claim_id, context.policy.id, context.policy.version, "CERTAIN"):
        return "RANK_CERTIFICATE_SCOPE_MISMATCH"
    if not all((cert.source_ref, cert.review_ref, cert.trace)) or cert.review_status != "ACCEPTED":
        return "RANK_CERTIFICATE_UNREVIEWED"
    claim = next((x for x in context.claims if x.id == prior.claim_id), None)
    if claim is None or (cert.domain, cert.target_id, cert.claim_fingerprint) != (
            claim.domain, claim.target_id, digest(asdict(claim))):
        return "RANK_CERTIFICATE_CLAIM_CONTENT_MISMATCH"
    if cert.policy_fingerprint != digest(asdict(context.policy)):
        return "RANK_CERTIFICATE_POLICY_CONTENT_MISMATCH"
    records = {x.evidence.id: x for x in context.evidence}
    if not prior.evidence_ids or any(eid not in records for eid in prior.evidence_ids):
        return "RANK_CERTIFICATE_EVIDENCE_UNAVAILABLE"
    actual_bindings = tuple(sorted((eid, records[eid].evidence.version, digest(asdict(records[eid])))
                                   for eid in prior.evidence_ids))
    if tuple(sorted(tuple(x) for x in cert.evidence_bindings)) != actual_bindings:
        return "RANK_CERTIFICATE_EVIDENCE_CONTENT_OR_VERSION_MISMATCH"
    if utc_time(context.as_of) < utc_time(cert.valid_from):
        return "RANK_CERTIFICATE_NOT_YET_VALID"
    if cert.expires_at and utc_time(context.as_of) >= utc_time(cert.expires_at):
        return "RANK_CERTIFICATE_EXPIRED"
    return None


def recall_priors(context: EvaluationContext) -> tuple[RecallDecision, ...]:
    """Eligibility to seek evidence admission; never a certificate of truth."""
    certs = _unique(context.rank_certificates, lambda x: x.id)
    out = []
    for prior in context.priors:
        if prior.kind == "INFORMATION":
            out.append(RecallDecision(prior.id, "ELIGIBLE", "INFORMATION_REQUIRES_EVIDENCE"))
        elif prior.kind != "OPINION":
            out.append(RecallDecision(prior.id, "DEFER", "UNKNOWN_PRIOR_KIND"))
        elif context.question.research_mode == "CERTAIN":
            out.append(RecallDecision(prior.id, "EXCLUDED", "PRIOR_STANCE_EXCLUDED_FOR_CERTAIN_INQUIRY"))
        elif not prior.rank_certificate_id and prior.claimed_rank != "CERTAIN":
            out.append(RecallDecision(prior.id, "EXCLUDED", "TENTATIVE_PRIOR_OPINION_EXCLUDED"))
        else:
            issue = _certificate_issue(certs.get(prior.rank_certificate_id), prior, context)
            out.append(RecallDecision(prior.id, "DEFER" if issue else "ELIGIBLE",
                issue or "ELIGIBLE_UNDER_ATTRIBUTED_RANK_REVIEW", prior.rank_certificate_id))
    return tuple(out)


def _bridge_issue(bridge: LexicalBridge) -> tuple[str, str] | None:
    if bridge.relation not in {"MATCHING", "INCLUSION", "MENTAL_ENTAILMENT"}:
        return "DEFER", "UNKNOWN_LEXICAL_RELATION"
    if not all((bridge.signifier, bridge.sense_id, bridge.usage_ref)):
        return "DEFER", "MISSING_SIGNIFIER_SENSE_OR_USAGE"
    if bridge.relation == "MENTAL_ENTAILMENT" and not bridge.necessity_ref:
        return "DEFER", "MISSING_MENTAL_NECESSITY_REVIEW"
    if bridge.namespace == "PUBLIC_LANGUAGE":
        if bridge.attestation_kind != "TRANSMITTED":
            return "BLOCK", "PUBLIC_LANGUAGE_REQUIRES_TRANSMITTED_ATTESTATION"
        if not all((bridge.source_ref, bridge.locator, bridge.context, bridge.review_ref)):
            return "DEFER", "INCOMPLETE_TRANSMITTED_ATTESTATION"
        if bridge.review_status != "ACCEPTED":
            return "DEFER", "ATTESTATION_REVIEW_PENDING"
    elif bridge.namespace == "LOCAL_STIPULATION":
        if bridge.attestation_kind != "STIPULATED" or not all((bridge.stipulation_ref, bridge.local_namespace)):
            return "DEFER", "MISSING_LOCAL_STIPULATION"
    elif bridge.namespace == "EDUCATIONAL_EXAMPLE":
        return "DEFER", "AUTHORED_EXAMPLE_NOT_PUBLIC_ATTESTATION"
    else:
        return "DEFER", "UNKNOWN_LEXICAL_NAMESPACE"
    return None


def _justification_fingerprints(context: EvaluationContext,
                                opposition_ids: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """Fingerprint the selected declared proof path, excluding unsigned rank labels.

    A fingerprint preserves the supplied warrant identity; it does not certify
    the source or the truth of the warrant. Excluded opinions remain in audit.
    """
    steps = {x.id: x for x in context.steps}
    priors = {x.id: x for x in context.priors}
    certificates = {x.id: x for x in context.rank_certificates}
    bridges = {x.id: x for x in context.bridges}
    evidence = {x.evidence.id: x for x in context.evidence}
    claims = {x.id: x for x in context.claims}
    scopes = {x.claim_id: x for x in context.scopes}
    assumptions = {x.id: x for x in context.assumptions}
    found: dict[str, str] = {}
    seen_steps: set[str] = set()
    seen_priors: set[str] = set()

    def add_prior(identity):
        if identity in seen_priors or identity not in priors:
            return
        seen_priors.add(identity)
        prior = priors[identity]
        value = asdict(prior)
        value.pop("claimed_rank", None)  # Audit metadata, not an external warrant.
        found["prior:" + prior.id] = digest(value)
        if prior.rank_certificate_id in certificates:
            cert = certificates[prior.rank_certificate_id]
            found["rank_certificate:" + cert.id] = digest(asdict(cert))
        for eid in prior.evidence_ids:
            if eid in evidence:
                for dep in evidence[eid].declared_prior_dependencies:
                    add_prior(dep)

    def add_step(identity):
        if identity in seen_steps or identity not in steps:
            return
        seen_steps.add(identity)
        step = steps[identity]
        found["step:" + step.id] = digest(asdict(step))
        if step.claim_id in claims:
            found["claim:" + step.claim_id] = digest(asdict(claims[step.claim_id]))
        if step.claim_id in scopes:
            found["claim_scope:" + step.claim_id] = digest(asdict(scopes[step.claim_id]))
        if step.operation == "ASSUME" and step.assumption_id in assumptions:
            assumption = assumptions[step.assumption_id]
            found["assumption:" + assumption.id] = digest(asdict(assumption))
        add_prior(step.prior_id)
        if step.bridge_id in bridges:
            bridge = bridges[step.bridge_id]
            found["lexical_bridge:" + bridge.id] = digest(asdict(bridge))
        for eid in step.evidence_ids:
            if eid in evidence:
                for dep in evidence[eid].declared_prior_dependencies:
                    add_prior(dep)
        for parent in (step.antecedent_step_id, step.implication_step_id):
            add_step(parent)

    add_step(context.final_step_id)
    for opposition in context.oppositions:
        if opposition.id not in opposition_ids:
            continue
        found["opposition:" + opposition.id] = digest(asdict(opposition))
        if opposition.opposing_claim_id in claims:
            claim = claims[opposition.opposing_claim_id]
            found["opposing_claim:" + claim.id] = digest(asdict(claim))
        for eid in opposition.evidence_ids:
            if eid in evidence:
                found["opposing_evidence:" + eid] = digest(asdict(evidence[eid]))
    return tuple(sorted(found.items()))


class Simulator:
    """Stateless evaluator. Planning motives are passed only to run(), not evaluate()."""

    def evaluate(self, supplied_context: EvaluationContext) -> Evaluation:
        context = _snapshot(supplied_context)
        stages: list[StageRecord] = []
        recalls: tuple[RecallDecision, ...] = ()
        g = Guardian(context.policy)
        claims = {c.id: c for c in context.claims}
        evidences = {e.evidence.id: e for e in context.evidence}

        def finish(status: str, verdict: str, reasons: tuple[str, ...],
                   selected: _StepResult | None = None,
                   opposition_ids: tuple[str, ...] = ()) -> Evaluation:
            used_versions = selected.evidence_versions if selected else ()
            fingerprints = tuple(sorted((eid, digest(asdict(evidences[eid])))
                for eid, _ in used_versions if eid in evidences))
            assumption_fingerprints = tuple(sorted((a.id, digest(asdict(a)))
                for a in context.assumptions if selected and a.id in selected.assumption_ids))
            used_claim_fingerprints = tuple(sorted((cid, digest(asdict(claims[cid])))
                for cid in (selected.used_claim_ids if selected else ()) if cid in claims))
            opposition_fingerprints = tuple(sorted((o.id, digest(asdict(o)))
                for o in context.oppositions if o.id in opposition_ids))
            final_scope = _scope_issue(context.question.intent, context.scope_profile)
            if final_scope is not None:
                status, reason = final_scope
                verdict, reasons = "UNASSESSED", tuple(sorted(set(reasons + (reason,))))
            decision = EpistemicDecision(context.question,
                claims[context.question.claim_id].expression if context.question.claim_id in claims else "",
                status, verdict, "NOT_ASSIGNED", selected.assumption_ids if selected else (),
                used_versions, fingerprints, assumption_fingerprints, used_claim_fingerprints,
                _justification_fingerprints(context, opposition_ids) if selected else (),
                tuple(sorted(set(reasons))),
                context.policy.id, context.policy.version, digest(asdict(context.policy)), context.scope_profile,
                context.protocol_version, context.as_of, context.subject_state,
                digest(asdict(context.reception)), bool(selected and
                    (selected.assumption_ids or selected.verdict == "CONDITIONAL_ONLY")),
                tuple(sorted(opposition_ids)), opposition_fingerprints, selected.used_claim_ids if selected else ())
            stages.append(StageRecord("S7_ASSESSMENT", status, decision.reasons,
                                      details="Framework rank remains NOT_ASSIGNED; external reviews are attributed inputs."))
            stages.append(StageRecord("S8_SCOPE_FINAL", "ALLOW" if final_scope is None else status,
                                      () if final_scope is None else (final_scope[1],)))
            return Evaluation(decision, tuple(stages), recalls, canonical(g.export_log()))

        scope_issue = _scope_issue(context.question.intent, context.scope_profile)
        stages.append(StageRecord("SCOPE_PRE", "ALLOW" if scope_issue is None else scope_issue[0],
                                  () if scope_issue is None else (scope_issue[1],)))
        if scope_issue:
            return finish(scope_issue[0], "UNASSESSED", (scope_issue[1],))
        try:
            utc_time(context.as_of)
            received = utc_time(context.reception.received_at)
            if received > utc_time(context.as_of):
                return finish("DEFER", "UNASSESSED", ("RECEPTION_NOT_YET_AVAILABLE",))
            if context.protocol_version != VERSION:
                return finish("DEFER", "UNASSESSED", ("UNSUPPORTED_PROTOCOL_VERSION",))
            if context.question.research_mode not in {"TENTATIVE", "CERTAIN"}:
                return finish("DEFER", "UNASSESSED", ("UNKNOWN_RESEARCH_MODE",))
            if context.question.aspect not in ASPECTS:
                return finish("DEFER", "UNASSESSED", ("UNKNOWN_JUDGMENT_ASPECT",))
            if not all((context.reception.id, context.reception.payload,
                        context.reception.source_ref, context.reception.channel)):
                return finish("DEFER", "UNASSESSED", ("INCOMPLETE_RECEPTION",))
            claims = _unique(context.claims, lambda x: x.id)
            scopes = _unique(context.scopes, lambda x: x.claim_id)
            evidences = _unique(context.evidence, lambda x: x.evidence.id)
            priors = _unique(context.priors, lambda x: x.id)
            assumptions = _unique(context.assumptions, lambda x: x.id)
            bridges = _unique(context.bridges, lambda x: x.id)
            _unique(context.steps, lambda x: x.id)
            _unique(context.oppositions, lambda x: x.id)
            if context.question.claim_id not in claims:
                return finish("DEFER", "UNASSESSED", ("UNKNOWN_QUESTION_CLAIM",))
            target = claims[context.question.claim_id]
            if (context.question.domain, context.question.target_id) != (target.domain, target.target_id):
                return finish("BLOCK", "UNASSESSED", ("QUESTION_SCOPE_MISMATCH",))
            final_meta = scopes.get(target.id)
            if final_meta is None:
                return finish("DEFER", "UNASSESSED", ("MISSING_CLAIM_SCOPE",))
            if (final_meta.intent, final_meta.aspect) != (context.question.intent, context.question.aspect):
                return finish("BLOCK", "UNASSESSED", ("QUESTION_CLAIM_ACT_MISMATCH",))
            if issue := _claim_scope_issue(target, final_meta, context):
                return finish(issue[0], "UNASSESSED", (issue[1],))
            for claim in context.claims:
                g.register_claim(claim)
            for row in context.evidence:
                g.register_evidence(row.evidence)
            recalls = recall_priors(context)
        except (ValueError, TypeError, KeyError) as exc:
            return finish("BLOCK", "UNASSESSED", ("INVALID_TYPED_INPUT:" + type(exc).__name__,))

        stages.append(StageRecord("S1_RECEPTION", "ALLOW", refs=(context.reception.id,),
            details="Received representation retained; no automatic truth or certainty about its content."))
        stages.append(StageRecord("S2_AFFECT", "ALLOW", refs=tuple(x.id for x in context.affect),
            details="Affect annotations retained separately; not admitted as identity/essence evidence."))
        stages.append(StageRecord("S3_RECALL", "ALLOW", refs=tuple(x.prior_id for x in recalls),
            details=canonical([asdict(x) for x in recalls])))
        stages.append(StageRecord("S4_TYPED_REPRESENTATION", "ALLOW", refs=tuple(claims),
            details="Claims and roles are supplied typed inputs; no automatic Arabic concept induction."))
        recall_by_id = {x.prior_id: x for x in recalls}
        step_results: dict[str, _StepResult] = {}

        def from_assessment(a: Assessment, used: tuple[str, ...]) -> _StepResult:
            return _StepResult(a.claim_id, a.status, a.verdict, a.reasons, a.assumptions,
                               a.evidence_versions, tuple(sorted(set(used))), a.id)

        def failure(step: Step, status: str, reason: str) -> _StepResult:
            return _StepResult(step.claim_id, status, "UNASSESSED", (reason,), used_claim_ids=(step.claim_id,))

        def evidence_guard(step: Step, ids: tuple[str, ...]) -> tuple[str, str] | None:
            step_scope = scopes[step.claim_id]
            for evidence_id in ids:
                row = evidences.get(evidence_id)
                if row is None:
                    continue  # Guardian will defer unknown evidence.
                for dependency in row.declared_prior_dependencies:
                    prior_status = recall_by_id.get(dependency)
                    if prior_status is None:
                        return "DEFER", "UNKNOWN_DECLARED_PRIOR_DEPENDENCY"
                    if prior_status.status == "EXCLUDED":
                        return "BLOCK", "DECLARED_DEPENDENCE_ON_EXCLUDED_OPINION"
                    if prior_status.status != "ELIGIBLE":
                        return "DEFER", "DECLARED_PRIOR_DEPENDENCY_NOT_ELIGIBLE"
                if row.declared_prior_dependencies:
                    # Eligibility to seek admission is not admission into Gamma.
                    # Derived evidence must use explicit, dependency-preserving
                    # inference steps; this wrapper does not accept recursive
                    # prior warrants inside an allegedly independent review.
                    return "DEFER", "DECLARED_DEPENDENCIES_REQUIRE_EXPLICIT_INFERENCE"
                if row.role == "AFFECT_SIGNAL":
                    return "BLOCK", "AFFECT_SIGNAL_IS_NOT_FACTUAL_EVIDENCE"
                if row.role == "SUBJECTIVE_REPORT":
                    if step_scope.intent != "ASSESS_SUITABILITY" or step_scope.aspect != "SUITABILITY":
                        return "BLOCK", "SUBJECTIVE_REPORT_NOT_IDENTITY_EVIDENCE"
                elif row.role == "PRIOR_OPINION":
                    if step.prior_id != row.prior_id or step.prior_id not in recall_by_id:
                        return "BLOCK", "PRIOR_OPINION_CANNOT_BYPASS_RECALL"
                    if recall_by_id[step.prior_id].status != "ELIGIBLE":
                        return "BLOCK", "EXCLUDED_PRIOR_OPINION"
                elif row.role not in ("INDEPENDENT_REVIEW", "NABT_OWNER_REPLAY"):
                    return "DEFER", "UNKNOWN_EVIDENCE_ROLE"
                # Every evidence role for a suitability claim is state-bound.
                # State IDs alone do not license changed state contents.
                if step_scope.intent == "ASSESS_SUITABILITY":
                    state = context.subject_state
                    if state is None:
                        return "DEFER", "MISSING_SUBJECT_STATE"
                    if row.subject_state_id != state.id:
                        return "BLOCK", "EVIDENCE_SUBJECT_STATE_MISMATCH"
                    if not row.subject_state_fingerprint:
                        return "DEFER", "MISSING_EVIDENCE_SUBJECT_STATE_FINGERPRINT"
                    if row.subject_state_fingerprint != digest(asdict(state)):
                        return "BLOCK", "EVIDENCE_SUBJECT_STATE_CONTENT_CHANGED"
                opinions_about_claim = {p.id for p in context.priors
                                        if p.kind == "OPINION" and p.claim_id == step.claim_id}
                if row.role == "INDEPENDENT_REVIEW" and opinions_about_claim:
                    if not row.independence_review_ref:
                        return "DEFER", "INDEPENDENCE_REVIEW_REQUIRED"
                    if set(row.declared_prior_dependencies) & opinions_about_claim:
                        return "BLOCK", "DECLARED_DEPENDENCE_ON_EXCLUDED_OPINION"
            return None

        for step in context.steps:
            if step.claim_id not in claims:
                result = failure(step, "DEFER", "UNKNOWN_STEP_CLAIM")
            elif not step.face_ref:
                result = failure(step, "DEFER", "MISSING_LINK_FACE")
            elif step.claim_id not in scopes:
                result = failure(step, "DEFER", "MISSING_STEP_SCOPE")
            elif (issue := _claim_scope_issue(claims[step.claim_id], scopes[step.claim_id], context)):
                result = failure(step, *issue)
            elif step.operation in SPEC_ONLY:
                result = failure(step, "DEFER", "SPEC_ONLY:" + step.operation)
            else:
                try:
                    if step.operation == "ADMIT_REGISTERED_EVIDENCE":
                        ids = step.evidence_ids
                        if step.prior_id:
                            prior = priors.get(step.prior_id)
                            recalled = recall_by_id.get(step.prior_id)
                            if prior is None or recalled is None:
                                result = failure(step, "DEFER", "UNKNOWN_PRIOR")
                            elif prior.claim_id != step.claim_id:
                                result = failure(step, "BLOCK", "PRIOR_CLAIM_MISMATCH")
                            elif recalled.status != "ELIGIBLE":
                                result = failure(step, "DEFER", recalled.reason)
                            elif ids and ids != prior.evidence_ids:
                                result = failure(step, "BLOCK", "PRIOR_EVIDENCE_OVERRIDE")
                            else:
                                ids = prior.evidence_ids
                                issue = evidence_guard(step, ids)
                                result = failure(step, *issue) if issue else from_assessment(
                                    g.admit(step.claim_id, ids, context.as_of), (step.claim_id,))
                        else:
                            issue = evidence_guard(step, ids)
                            result = failure(step, *issue) if issue else from_assessment(
                                g.admit(step.claim_id, ids, context.as_of), (step.claim_id,))
                    elif step.operation == "ASSUME":
                        a = assumptions.get(step.assumption_id)
                        if a is None:
                            result = failure(step, "DEFER", "UNKNOWN_ASSUMPTION")
                        elif a.claim_id != step.claim_id:
                            result = failure(step, "BLOCK", "ASSUMPTION_CLAIM_MISMATCH")
                        else:
                            result = from_assessment(g.assume(a, context.as_of), (step.claim_id,))
                    elif step.operation == "MODUS_PONENS":
                        p = step_results.get(step.antecedent_step_id)
                        rule = step_results.get(step.implication_step_id)
                        if p is None or rule is None:
                            result = failure(step, "DEFER", "UNKNOWN_PREDECESSOR_STEP")
                        elif not p.guardian_assessment_id or not rule.guardian_assessment_id:
                            result = failure(step, "BLOCK", "PREDECESSOR_IS_NOT_INFERENCE_PREMISE")
                        elif claims[rule.claim_id].consequent_id != step.claim_id:
                            result = failure(step, "BLOCK", "DECLARED_CONCLUSION_MISMATCH")
                        else:
                            a = g.modus_ponens(p.guardian_assessment_id, rule.guardian_assessment_id,
                                               step.inference_mode, context.as_of)
                            result = from_assessment(a, p.used_claim_ids + rule.used_claim_ids + (step.claim_id,))
                    elif step.operation == "LEXICAL_BRIDGE":
                        bridge = bridges.get(step.bridge_id)
                        if scopes[step.claim_id].aspect != "LINGUISTIC_RELATION":
                            result = failure(step, "BLOCK", "LEXICAL_BRIDGE_REQUIRES_LINGUISTIC_SCOPE")
                        elif bridge is None:
                            result = failure(step, "DEFER", "UNKNOWN_LEXICAL_BRIDGE")
                        elif bridge.claim_id != step.claim_id:
                            result = failure(step, "BLOCK", "BRIDGE_CLAIM_MISMATCH")
                        elif (issue := _bridge_issue(bridge)):
                            result = failure(step, *issue)
                        else:
                            verdict = ("PUBLIC_LEXICAL_LINK_CANDIDATE" if bridge.namespace == "PUBLIC_LANGUAGE"
                                       else "LOCAL_STIPULATION_REGISTERED")
                            result = _StepResult(step.claim_id, "ALLOW", verdict,
                                ("ATTRIBUTED_REVIEW_NOT_AUTOMATIC_NECESSITY_PROOF",),
                                used_claim_ids=(step.claim_id,))
                    else:
                        result = failure(step, "DEFER", "UNKNOWN_OPERATION")
                except (ValueError, TypeError, KeyError) as exc:
                    result = failure(step, "BLOCK", "INVALID_OPERATION_INPUT:" + type(exc).__name__)
            step_results[step.id] = result
            stages.append(StageRecord("S5:" + step.id, result.status, result.reasons,
                                      result.used_claim_ids, canonical(asdict(result))))

        selected = step_results.get(context.final_step_id)
        if selected is None:
            return finish("DEFER", "UNASSESSED", ("UNKNOWN_FINAL_STEP",))
        if selected.claim_id != context.question.claim_id:
            return finish("BLOCK", "UNASSESSED", ("FINAL_CLAIM_MISMATCH",), selected)
        stages.append(StageRecord("S6_JUDGMENT", selected.status, selected.reasons, (selected.claim_id,)))
        relevant_opposition = tuple(o.id for o in context.oppositions
                                   if o.disputed_claim_id in selected.used_claim_ids)
        if relevant_opposition:
            stages.append(StageRecord("COUNTEREVIDENCE_REVIEW", "DEFER",
                ("CONFLICT_PENDING_REVIEW",), relevant_opposition,
                canonical([asdict(o) for o in context.oppositions if o.id in relevant_opposition])))
            # No automatic preference for a label CERTAIN over opposing records.
            status = "BLOCK" if selected.status == "BLOCK" else "DEFER"
            verdict = "UNASSESSED" if status == "BLOCK" else "CONFLICT_PENDING_REVIEW"
            return finish(status, verdict, selected.reasons + ("CONFLICT_PENDING_REVIEW",),
                          selected, relevant_opposition)
        return finish(selected.status, selected.verdict, selected.reasons, selected)

    def run(self, context: EvaluationContext, motive: Motive) -> Run:
        """Planning envelope records the motive, then calls the motive-free evaluator."""
        context_json = canonical(asdict(_snapshot(context)))
        motive_json = canonical(asdict(motive))
        m = Motive(**json.loads(motive_json))
        if not m.id or not m.description:
            raise ValueError("Motive identity and description are required")
        if m.classification != "UNCLASSIFIED" and not m.classification_source_ref:
            raise ValueError("A motive classification needs an attributed source")
        evaluation = self.evaluate(context_from_dict(json.loads(context_json)))
        envelope = {"format": "SIM-AQL-run-v0.2", "input_context_json": context_json,
                    "motive_json": motive_json, "evaluation": asdict(evaluation)}
        return Run(**{**envelope, "evaluation": evaluation, "audit_digest": digest(envelope)})

    @classmethod
    def replay(cls, payload: Mapping[str, Any]) -> Run:
        data = dict(payload)
        if data.get("format") != "SIM-AQL-run-v0.2":
            raise ValueError("Unsupported SIM-AQL audit format")
        check = {k: v for k, v in data.items() if k != "audit_digest"}
        if digest(check) != data.get("audit_digest"):
            raise ValueError("SIM-AQL audit integrity failure")
        reproduced = cls().run(context_from_dict(json.loads(data["input_context_json"])),
                               Motive(**json.loads(data["motive_json"])))
        if canonical(asdict(reproduced)) != canonical(data):
            raise ValueError("SIM-AQL replay result mismatch")
        return reproduced
