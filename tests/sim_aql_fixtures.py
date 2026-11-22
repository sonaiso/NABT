"""Synthetic, attributed fixtures for SIM-AQL demonstrations; not observations."""
from dataclasses import asdict, replace

from tools.lexical_training.sim_aql.guardian import Assumption, Claim, Evidence, digest
from tools.lexical_training.sim_aql.engine import (AffectRecord, ClaimScope, EvaluationContext, EvidenceRecord,
                     LexicalBridge, Motive, PriorRecord, Question, RankCertificate,
                     Reception, Step, SubjectState)

NOW = "2026-11-22T12:00:00Z"
PAST = "2026-11-22T11:00:00Z"
FUTURE = "2026-11-23T12:00:00Z"


def review(claim_id: str, identity: str | None = None, *, domain="demo",
           target="sample-1", status="ACCEPTED", **changes) -> EvidenceRecord:
    e = Evidence(identity or "e-" + claim_id, 1, claim_id, domain, target,
                 "SYNTHETIC_EXTERNAL_REVIEW", "synthetic-source", "synthetic-review",
                 status, ("synthetic-original-trace",), "Synthetic evidence, no external truth claim.")
    return EvidenceRecord(replace(e, **changes))


def factual_context() -> EvaluationContext:
    claim = Claim("p", "demo", "sample-1", "قضية وصفية مصطنعة عن العينة")
    return EvaluationContext(
        question=Question("q1", "p", "demo", "sample-1", "DESCRIBE_REALITY", "PROPERTY"),
        reception=Reception("a1", "نص مصطنع، لا يمثل ملاحظة خارجية", "TEXT", "fixture", PAST),
        claims=(claim,), scopes=(ClaimScope("p", "DESCRIBE_REALITY", "PROPERTY"),),
        evidence=(review("p"),), steps=(Step("admit-p", "ADMIT_REGISTERED_EVIDENCE", "p",
            "registered evidence applies to this exact claim", ("e-p",)),),
        final_step_id="admit-p", as_of=NOW)


def conditional_context(mode="CONDITIONAL") -> EvaluationContext:
    c = factual_context()
    claims = (c.claims[0], Claim("q", "demo", "sample-1", "نتيجة أولى مصطنعة"),
              Claim("r", "demo", "sample-1", "نتيجة ثانية مصطنعة"),
              Claim("pq", "demo", "sample-1", "إذا p فإن q", "IMPLIES", "p", "q"),
              Claim("qr", "demo", "sample-1", "إذا q فإن r", "IMPLIES", "q", "r"))
    return replace(c, question=replace(c.question, claim_id="r"), claims=claims,
        scopes=tuple(ClaimScope(x.id, "DESCRIBE_REALITY", "PROPERTY") for x in claims),
        evidence=(review("pq"), review("qr")), assumptions=(Assumption("h-p", "p"),),
        steps=(Step("assume-p", "ASSUME", "p", "declared hypothesis", assumption_id="h-p"),
               Step("admit-pq", "ADMIT_REGISTERED_EVIDENCE", "pq", "registered implication", ("e-pq",)),
               Step("derive-q", "MODUS_PONENS", "q", "exact antecedent", antecedent_step_id="assume-p",
                    implication_step_id="admit-pq", inference_mode=mode),
               Step("admit-qr", "ADMIT_REGISTERED_EVIDENCE", "qr", "registered implication", ("e-qr",)),
               Step("derive-r", "MODUS_PONENS", "r", "exact antecedent", antecedent_step_id="derive-q",
                    implication_step_id="admit-qr", inference_mode=mode)), final_step_id="derive-r")


def prior_context(certified=False, query_mode="TENTATIVE", claimed_rank="CERTAIN") -> EvaluationContext:
    c = factual_context()
    p = PriorRecord("old-opinion", "p", "OPINION", "synthetic-speaker", ("e-p",), claimed_rank,
                    "cert-p" if certified else None)
    evidence = replace(c.evidence[0], role="PRIOR_OPINION", prior_id=p.id)
    cert = RankCertificate("cert-p", "p", c.policy.id, c.policy.version, "CERTAIN",
        "synthetic-source-of-rank", "external-rank-review", "ACCEPTED", ("rank-review-trace",), PAST,
        domain=c.claims[0].domain, target_id=c.claims[0].target_id,
        claim_fingerprint=digest(asdict(c.claims[0])), policy_fingerprint=digest(asdict(c.policy)),
        evidence_bindings=((evidence.evidence.id, evidence.evidence.version, digest(asdict(evidence))),))
    return replace(c, question=replace(c.question, research_mode=query_mode), priors=(p,),
        rank_certificates=(cert,) if certified else (),
        evidence=(evidence,),
        steps=(replace(c.steps[0], prior_id=p.id, evidence_ids=()),))


def suitability_context() -> EvaluationContext:
    c = factual_context()
    state = SubjectState("state-hungry", "person-1", "وصف حالة مصطنع: جوع", "subject-report", PAST)
    return replace(c, question=replace(c.question, intent="ASSESS_SUITABILITY", aspect="SUITABILITY"),
        scopes=(ClaimScope("p", "ASSESS_SUITABILITY", "SUITABILITY", state.id, state.subject_id),), subject_state=state,
        evidence=(replace(c.evidence[0], role="SUBJECTIVE_REPORT", subject_state_id=state.id,
                          subject_state_fingerprint=digest(asdict(state))),),
        affect=(AffectRecord("affect-1", "ملائم", state.id, "synthetic-subject"),))


def report_context() -> EvaluationContext:
    c = factual_context()
    n = Claim("norm", "demo", "sample-1", "مضمون معياري منسوب إلى قائل")
    r = Claim("report", "demo", "sample-1", "صدر عن القائل ذلك المضمون", "REPORT", reported_claim_id="norm")
    return replace(c, question=replace(c.question, claim_id=r.id, intent="REPORT_NORMATIVE", aspect="REPORT_OCCURRENCE"),
        claims=(n, r), scopes=(ClaimScope(n.id, "ISSUE_NORMATIVE", "PROPERTY"),
                              ClaimScope(r.id, "REPORT_NORMATIVE", "REPORT_OCCURRENCE")),
        evidence=(review(r.id),), steps=(Step("admit-report", "ADMIT_REGISTERED_EVIDENCE", r.id,
            "evidence addresses occurrence of the report", ("e-report",)),), final_step_id="admit-report")


def lexical_context(namespace="PUBLIC_LANGUAGE", attestation_kind="TRANSMITTED") -> EvaluationContext:
    c = factual_context()
    bridge = LexicalBridge("bridge-1", "p", namespace, "MATCHING", "لفظ-تعليمي", "sense-1",
        attestation_kind, "synthetic-source", "synthetic-page-location", "synthetic-context",
        "attributed-review", "ACCEPTED", "synthetic-usage", stipulation_ref="local-declaration",
        local_namespace="demo-local")
    return replace(c, question=replace(c.question, aspect="LINGUISTIC_RELATION"),
        scopes=(ClaimScope("p", "DESCRIBE_REALITY", "LINGUISTIC_RELATION"),), evidence=(),
        steps=(Step("bridge", "LEXICAL_BRIDGE", "p", "selected sense", bridge_id=bridge.id),),
        final_step_id="bridge", bridges=(bridge,))


def motives() -> tuple[Motive, ...]:
    return (Motive("m1", "أريد أن تؤيد النتيجة رأيي"),
            Motive("m2", "أريد أن تنفي النتيجة رأيي"),
            Motive("m3", "أستطلع الموضوع دون تعيين أصل غريزي"),
            Motive("m4", "دافع مصطنع منسوب إلى الحاجة العضوية", "ORGANIC", "synthetic-attribution"))
