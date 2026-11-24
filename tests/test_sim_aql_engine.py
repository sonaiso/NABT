"""Counterexample and metamorphic tests of bounded contracts, not cognition."""
from dataclasses import asdict, replace
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.lexical_training.sim_aql import guardian

from tools.lexical_training.sim_aql.guardian import Claim, Evidence, canonical, digest
from tests.sim_aql_fixtures import (NOW, PAST, FUTURE, conditional_context, factual_context, lexical_context,
                      motives, prior_context, report_context, review, suitability_context)
from tools.lexical_training.sim_aql.engine import (AffectRecord, ClaimScope, EvidenceRecord, Motive, Opposition, PriorRecord, Simulator,
                     Step, context_from_dict, epistemic_digest, epistemic_projection)


def motive_independent(simulator, context):
    return len({epistemic_digest(simulator.run(context, m)) for m in motives()}) == 1


class MotiveDependentMutant(Simulator):
    def run(self, context, motive):
        run = super().run(context, motive)
        if motive.id == "m1":
            d = replace(run.evaluation.decision, status="ALLOW", verdict="MOTIVE_WANTED_TRUE")
            return replace(run, evaluation=replace(run.evaluation, decision=d))
        return run


class ConstantMutant(Simulator):
    def evaluate(self, context):
        return super().evaluate(factual_context())


class SimAqlTests(unittest.TestCase):
    def setUp(self):
        self.sim = Simulator()

    def test_01_inv01_motive_noninterference_across_six_contexts(self):
        """24 executions: motives vary; complete epistemic context is fixed per group."""
        empty = replace(factual_context(), evidence=())
        normative = replace(factual_context(), question=replace(factual_context().question, intent="ISSUE_NORMATIVE"))
        for context in (factual_context(), empty, conditional_context(), suitability_context(), lexical_context(), normative):
            with self.subTest(context=context.question.intent, verdict=context.final_step_id, empty=not context.evidence):
                self.assertTrue(motive_independent(self.sim, context))

    def test_02_motive_changes_full_audit_but_not_epistemic_projection(self):
        first, second = [self.sim.run(factual_context(), m) for m in motives()[:2]]
        self.assertEqual(epistemic_projection(first), epistemic_projection(second))
        self.assertNotEqual(first.audit_digest, second.audit_digest)
        self.assertNotEqual(first.motive_json, second.motive_json)
        self.assertEqual(first.evaluation.guardian_log_json, second.evaluation.guardian_log_json)

    def test_03_noninterference_detects_motive_dependent_mutant(self):
        self.assertFalse(motive_independent(MotiveDependentMutant(), factual_context()))

    def test_04_constant_mutant_passes_inv01_but_fails_evidence_sensitivity(self):
        mutant = ConstantMutant()
        self.assertTrue(motive_independent(mutant, factual_context()))
        empty = replace(factual_context(), evidence=())
        self.assertEqual(epistemic_projection(mutant.evaluate(factual_context())), epistemic_projection(mutant.evaluate(empty)))
        self.assertNotEqual(epistemic_projection(self.sim.evaluate(factual_context())), epistemic_projection(self.sim.evaluate(empty)))

    def test_05_missing_evidence_changes_support_to_defer(self):
        c = factual_context()
        self.assertEqual(self.sim.evaluate(c).decision.verdict, "SUPPORTED_BY_REGISTERED_REVIEW")
        result = self.sim.evaluate(replace(c, evidence=()))
        self.assertEqual(result.decision.status, "DEFER")
        self.assertEqual(result.decision.verdict, "UNASSESSED")

    def test_06_expired_evidence_cannot_support_current_result(self):
        c = factual_context()
        e = replace(c.evidence[0], evidence=replace(c.evidence[0].evidence, expires_at=NOW))
        result = self.sim.evaluate(replace(c, evidence=(e,)))
        self.assertEqual(result.decision.status, "DEFER")
        self.assertIn("EVIDENCE_EXPIRED", result.decision.reasons)

    def test_07_inv02_affect_annotation_is_not_a_factual_premise(self):
        c = factual_context()
        c = replace(c, evidence=(replace(c.evidence[0], role="AFFECT_SIGNAL"),),
                    affect=(AffectRecord("a", "ملائم", "state", "subject"),))
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.status, "BLOCK")
        self.assertIn("AFFECT_SIGNAL_IS_NOT_FACTUAL_EVIDENCE", r.decision.reasons)
        self.assertIn("a", next(s for s in r.stages if s.stage == "S2_AFFECT").refs)

    def test_08_subjective_report_can_support_scoped_suitability(self):
        r = self.sim.evaluate(suitability_context())
        self.assertEqual(r.decision.status, "ALLOW")
        self.assertEqual(r.decision.subject_state.id, "state-hungry")
        self.assertEqual(r.decision.framework_rank, "NOT_ASSIGNED")

    def test_09_subjective_report_cannot_establish_identity(self):
        c = factual_context()
        c = replace(c, evidence=(replace(c.evidence[0], role="SUBJECTIVE_REPORT", subject_state_id="s"),))
        self.assertIn("SUBJECTIVE_REPORT_NOT_IDENTITY_EVIDENCE", self.sim.evaluate(c).decision.reasons)

    def test_10_suitability_subject_state_is_semantic_input_not_motive(self):
        c = suitability_context()
        changed = replace(c, subject_state=replace(c.subject_state, id="state-full", description="شبع مصطنع"))
        self.assertEqual(self.sim.evaluate(c).decision.status, "ALLOW")
        self.assertEqual(self.sim.evaluate(changed).decision.status, "BLOCK")
        self.assertIn("CLAIM_SUBJECT_STATE_MISMATCH", self.sim.evaluate(changed).decision.reasons)

    def test_11_suitability_requires_state_and_evidence_state_match(self):
        c = suitability_context()
        self.assertIn("MISSING_SUBJECT_STATE", self.sim.evaluate(replace(c, subject_state=None)).decision.reasons)
        bad = replace(c, evidence=(replace(c.evidence[0], subject_state_id="different-state"),))
        self.assertIn("EVIDENCE_SUBJECT_STATE_MISMATCH", self.sim.evaluate(bad).decision.reasons)

    def test_12_inv03_no_automatic_rank_for_any_supported_aspect(self):
        c = factual_context()
        for aspect in ("EXISTENCE", "PROPERTY_EXISTENCE", "PROPERTY", "ESSENCE"):
            x = replace(c, question=replace(c.question, aspect=aspect),
                        scopes=(ClaimScope("p", "DESCRIBE_REALITY", aspect),),
                        reception=replace(c.reception, channel="SENSOR_DATA"))
            self.assertEqual(self.sim.evaluate(x).decision.framework_rank, "NOT_ASSIGNED")

    def test_13_inv08_unsigned_labels_do_not_assign_certainty(self):
        c = factual_context()
        labelled = replace(c, untrusted_labels=("CERTAIN", "TRUE", "قطعي", "100%"))
        self.assertEqual(epistemic_projection(self.sim.evaluate(c)), epistemic_projection(self.sim.evaluate(labelled)))

    def test_14_inv04_tentative_opinion_excluded_but_preserved_in_audit(self):
        c = prior_context(claimed_rank="TENTATIVE")
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.status, "DEFER")
        self.assertEqual(r.recall[0].status, "EXCLUDED")
        self.assertIn("old-opinion", canonical(asdict(r)))

    def test_15_certain_label_without_rank_certificate_is_not_eligible(self):
        r = self.sim.evaluate(prior_context(certified=False))
        self.assertIn("MISSING_EXTERNAL_RANK_REVIEW", r.decision.reasons)
        self.assertEqual(r.decision.status, "DEFER")

    def test_16_attributed_rank_certificate_allows_only_bounded_admission(self):
        r = self.sim.evaluate(prior_context(certified=True))
        self.assertEqual(r.decision.status, "ALLOW")
        self.assertEqual(r.decision.framework_rank, "NOT_ASSIGNED")
        self.assertEqual(r.recall[0].reason, "ELIGIBLE_UNDER_ATTRIBUTED_RANK_REVIEW")

    def test_17_certain_inquiry_excludes_prior_stance_even_if_certified(self):
        r = self.sim.evaluate(prior_context(certified=True, query_mode="CERTAIN"))
        self.assertEqual(r.recall[0].status, "EXCLUDED")
        self.assertIn("PRIOR_STANCE_EXCLUDED_FOR_CERTAIN_INQUIRY", r.decision.reasons)

    def test_18_independent_new_evidence_can_support_same_content(self):
        c = prior_context(certified=True, query_mode="CERTAIN")
        fresh = replace(review("p", "fresh-e"), independence_review_ref="external-independence-review")
        c = replace(c, evidence=c.evidence + (fresh,),
                    steps=(replace(c.steps[0], prior_id=None, evidence_ids=("fresh-e",)),))
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.status, "ALLOW")
        self.assertEqual(r.recall[0].status, "EXCLUDED")
        self.assertEqual(r.decision.evidence_versions, (("fresh-e", 1),))

    def test_19_renaming_prior_evidence_does_not_bypass_recall(self):
        c = prior_context(claimed_rank="TENTATIVE")
        c = replace(c, steps=(replace(c.steps[0], prior_id=None, evidence_ids=("e-p",)),))
        self.assertIn("PRIOR_OPINION_CANNOT_BYPASS_RECALL", self.sim.evaluate(c).decision.reasons)

    def test_20_independence_label_requires_review_and_no_declared_prior_dependency(self):
        c = prior_context(claimed_rank="TENTATIVE")
        fresh = review("p", "fresh-e")
        c = replace(c, evidence=(fresh,), steps=(replace(c.steps[0], prior_id=None, evidence_ids=("fresh-e",)),))
        self.assertIn("INDEPENDENCE_REVIEW_REQUIRED", self.sim.evaluate(c).decision.reasons)
        bad = replace(fresh, independence_review_ref="review", declared_prior_dependencies=("old-opinion",))
        self.assertIn("DECLARED_DEPENDENCE_ON_EXCLUDED_OPINION", self.sim.evaluate(replace(c, evidence=(bad,))).decision.reasons)

    def test_21_rank_certificate_identity_policy_time_and_review_are_checked(self):
        c = prior_context(certified=True)
        cases = (("claim_id", "other"), ("profile_version", "other"), ("review_status", "UNREVIEWED"),
                 ("valid_from", FUTURE), ("expires_at", NOW))
        for field, value in cases:
            with self.subTest(field=field):
                x = replace(c, rank_certificates=(replace(c.rank_certificates[0], **{field: value}),))
                self.assertEqual(self.sim.evaluate(x).decision.status, "DEFER")

    def test_22_inv05_normative_issue_blocked_before_guardian_admission(self):
        c = factual_context()
        c = replace(c, question=replace(c.question, intent="ISSUE_NORMATIVE"))
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.status, "BLOCK")
        self.assertIn("PRE_SHAR_SCOPE", r.decision.reasons)
        self.assertEqual(json.loads(r.guardian_log_json)["events"], [])

    def test_23_report_of_normative_speech_is_allowed_without_its_content(self):
        r = self.sim.evaluate(report_context())
        self.assertEqual(r.decision.status, "ALLOW")
        self.assertEqual(r.decision.question.claim_id, "report")
        log = json.loads(r.guardian_log_json)
        admissions = [e["payload"]["claim_id"] for e in log["events"] if e["action"] == "admit"]
        self.assertEqual(admissions, ["report"])

    def test_24_report_label_cannot_launder_normative_content(self):
        c = report_context()
        c = replace(c, question=replace(c.question, claim_id="norm"))
        self.assertEqual(self.sim.evaluate(c).decision.status, "BLOCK")

    def test_25_unknown_scope_defers_without_classifying_free_text(self):
        c = factual_context()
        for value in ("", "UNCLASSIFIED", "perhaps moral"):
            r = self.sim.evaluate(replace(c, question=replace(c.question, intent=value)))
            self.assertEqual(r.decision.status, "DEFER")

    def test_26_normative_conclusion_cannot_be_smuggled_through_inference(self):
        c = conditional_context()
        scopes = tuple(replace(s, intent="ISSUE_NORMATIVE") if s.claim_id == "q" else s for s in c.scopes)
        r = self.sim.evaluate(replace(c, scopes=scopes))
        self.assertEqual(r.decision.status, "BLOCK")
        self.assertTrue(any("PRE_SHAR_SCOPE" in s.reasons for s in r.stages))

    def test_27_inv06_conditional_taint_survives_two_steps(self):
        r = self.sim.evaluate(conditional_context())
        self.assertEqual(r.decision.status, "ALLOW")
        self.assertEqual(r.decision.verdict, "CONDITIONAL_ONLY")
        self.assertEqual(r.decision.assumptions, ("h-p",))

    def test_28_hypothesis_cannot_be_exported_as_factual_result(self):
        r = self.sim.evaluate(conditional_context(mode="FACTUAL"))
        self.assertEqual(r.decision.status, "BLOCK")
        self.assertIn("UNDISCHARGED_ASSUMPTIONS", r.decision.reasons)

    def test_reviewed_inputs_respect_the_inference_mode_at_each_step(self):
        c = conditional_context()
        admit_p = factual_context().steps[0]
        c = replace(c, evidence=(review("p"), *c.evidence), assumptions=())
        for first, last, status, verdict in (
                ("FACTUAL", "FACTUAL", "ALLOW", "SUPPORTED_BY_REGISTERED_REVIEW"),
                ("FACTUAL", "CONDITIONAL", "ALLOW", "CONDITIONAL_ONLY"),
                ("CONDITIONAL", "CONDITIONAL", "ALLOW", "CONDITIONAL_ONLY"),
                ("CONDITIONAL", "FACTUAL", "BLOCK", "UNASSESSED")):
            with self.subTest(first=first, last=last):
                steps = (admit_p, c.steps[1], replace(c.steps[2], antecedent_step_id=admit_p.id,
                         inference_mode=first), c.steps[3], replace(c.steps[4], inference_mode=last))
                result = self.sim.evaluate(replace(c, steps=steps))
                middle = next(s for s in result.stages if s.stage == "S5:derive-q")
                self.assertEqual(middle.status, "ALLOW")
                self.assertEqual(json.loads(middle.details)["verdict"],
                                 "CONDITIONAL_ONLY" if first == "CONDITIONAL" else "SUPPORTED_BY_REGISTERED_REVIEW")
                self.assertEqual(result.decision.assumptions, ())
                self.assertEqual((result.decision.status, result.decision.verdict), (status, verdict))
                if status == "BLOCK":
                    self.assertIn("CONDITIONAL_PREDECESSOR_IN_FACTUAL_INFERENCE", result.decision.reasons)

    def test_conditionally_derived_implication_cannot_supply_a_factual_rule(self):
        c = conditional_context()
        admit_p = factual_context().steps[0]
        # Given r and r → (p → q), derive p → q in conditional mode.
        higher_rule = Claim("r-pq", "demo", "sample-1", "r → (p → q)", "IMPLIES", "r", "pq")
        steps = (admit_p,
                 Step("admit-r", "ADMIT_REGISTERED_EVIDENCE", "r", "review", ("e-r",)),
                 Step("admit-r-pq", "ADMIT_REGISTERED_EVIDENCE", higher_rule.id, "review", ("e-r-pq",)),
                 Step("derive-pq", "MODUS_PONENS", "pq", "conditional rule",
                      antecedent_step_id="admit-r", implication_step_id="admit-r-pq", inference_mode="CONDITIONAL"),
                 Step("derive-q", "MODUS_PONENS", "q", "application",
                      antecedent_step_id=admit_p.id, implication_step_id="derive-pq", inference_mode="FACTUAL"))
        c = replace(c, claims=(*c.claims, higher_rule), question=replace(c.question, claim_id="q"),
                    scopes=(*c.scopes, replace(c.scopes[0], claim_id=higher_rule.id)),
                    evidence=tuple(review(k) for k in ("p", "r", higher_rule.id)), assumptions=(),
                    steps=steps, final_step_id="derive-q")
        result = self.sim.evaluate(c)
        rule = next(s for s in result.stages if s.stage == "S5:derive-pq")
        self.assertEqual((rule.status, json.loads(rule.details)["verdict"]), ("ALLOW", "CONDITIONAL_ONLY"))
        self.assertEqual((result.decision.status, result.decision.verdict), ("BLOCK", "UNASSESSED"))
        self.assertIn("CONDITIONAL_PREDECESSOR_IN_FACTUAL_INFERENCE", result.decision.reasons)

    def test_29_inv07_public_language_requires_transmitted_attestation(self):
        self.assertEqual(self.sim.evaluate(lexical_context()).decision.status, "ALLOW")
        for kind in ("AUTHORED", "STATISTICAL", "STIPULATED"):
            r = self.sim.evaluate(lexical_context(attestation_kind=kind))
            self.assertEqual(r.decision.status, "BLOCK")

    def test_30_public_attestation_needs_locator_context_and_review(self):
        c = lexical_context()
        for field, value in (("locator", ""), ("context", ""), ("review_ref", ""), ("review_status", "UNREVIEWED")):
            with self.subTest(field=field):
                r = self.sim.evaluate(replace(c, bridges=(replace(c.bridges[0], **{field: value}),)))
                self.assertEqual(r.decision.status, "DEFER")

    def test_31_local_stipulation_is_allowed_in_its_namespace_only(self):
        c = lexical_context("LOCAL_STIPULATION", "STIPULATED")
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.verdict, "LOCAL_STIPULATION_REGISTERED")
        public = replace(c, bridges=(replace(c.bridges[0], namespace="PUBLIC_LANGUAGE"),))
        self.assertEqual(self.sim.evaluate(public).decision.status, "BLOCK")

    def test_32_mental_entailment_requires_necessity_reference(self):
        c = lexical_context()
        c = replace(c, bridges=(replace(c.bridges[0], relation="MENTAL_ENTAILMENT"),))
        self.assertIn("MISSING_MENTAL_NECESSITY_REVIEW", self.sim.evaluate(c).decision.reasons)

    def test_33_lexical_candidate_cannot_be_used_as_factual_premise(self):
        c = conditional_context(mode="FACTUAL")
        lexical = lexical_context()
        b = lexical.bridges[0]
        scopes = tuple(lexical.scopes[0] if scope.claim_id == "p" else scope for scope in c.scopes)
        steps = (lexical.steps[0], c.steps[1], replace(c.steps[2], antecedent_step_id=lexical.steps[0].id))
        c = replace(c, question=replace(c.question, claim_id="q"), scopes=scopes,
                    steps=steps, final_step_id="derive-q", bridges=(b,), assumptions=())
        outcome = self.sim.evaluate(c)
        stages = {s.stage: s for s in outcome.stages}
        bridge = stages["S5:bridge"]
        self.assertEqual(bridge.status, "ALLOW")
        self.assertEqual(json.loads(bridge.details)["verdict"], "PUBLIC_LEXICAL_LINK_CANDIDATE")
        self.assertEqual(stages["S5:admit-pq"].status, "ALLOW")
        self.assertEqual(outcome.decision.status, "BLOCK")
        self.assertIn("PREDECESSOR_IS_NOT_INFERENCE_PREMISE", outcome.decision.reasons)

    def test_34_declared_opposition_suspends_final_assertion_and_preserves_both_sides(self):
        c = factual_context()
        neg = Claim("not-p", "demo", "sample-1", "دعوى معارضة مصطنعة")
        opp = Opposition("opp1", "p", neg.id, ("e-not-p",), "attributed-contradiction-review")
        c = replace(c, claims=c.claims + (neg,), evidence=c.evidence + (review("not-p"),), oppositions=(opp,))
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.status, "DEFER")
        self.assertEqual(r.decision.verdict, "CONFLICT_PENDING_REVIEW")
        self.assertEqual(r.decision.opposition_ids, (opp.id,))
        self.assertIn("not-p", canonical(asdict(r)))

    def test_35_opposition_to_a_premise_also_suspends_derived_conclusion(self):
        c = conditional_context()
        c = replace(c, oppositions=(Opposition("opp-p", "p", "unknown-opposing-claim", (), "pending-review"),))
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.verdict, "CONFLICT_PENDING_REVIEW")
        self.assertEqual(r.decision.assumptions, ("h-p",))

    def test_36_unimplemented_link_types_defer_and_keep_namespaces_distinct(self):
        c = factual_context()
        names = ("LEGAL_QIYAS", "RESEMBLANCE_ANALOGY", "EMPIRICAL_CAUSAL_ANALOGY", "CONTROLLED_EXPERIMENT")
        for name in names:
            r = self.sim.evaluate(replace(c, steps=(replace(c.steps[0], operation=name),)))
            self.assertEqual(r.decision.status, "DEFER")
            self.assertIn("SPEC_ONLY:" + name, r.decision.reasons)

    def test_37_incomplete_link_face_defers(self):
        c = factual_context()
        self.assertIn("MISSING_LINK_FACE", self.sim.evaluate(replace(c, steps=(replace(c.steps[0], face_ref=""),))).decision.reasons)

    def test_38_future_reception_and_timezone_naive_timestamps_rejected(self):
        c = factual_context()
        future = replace(c, reception=replace(c.reception, received_at=FUTURE))
        self.assertIn("RECEPTION_NOT_YET_AVAILABLE", self.sim.evaluate(future).decision.reasons)
        naive = replace(c, as_of="2026-11-22T12:00:00")
        self.assertEqual(self.sim.evaluate(naive).decision.status, "BLOCK")

    def test_39_replay_recomputes_outputs_and_preserves_projection(self):
        original = self.sim.run(conditional_context(), motives()[0])
        replay = Simulator.replay(asdict(original))
        self.assertEqual(asdict(original), asdict(replay))

    def test_40_tampered_result_even_with_recomputed_hash_fails_replay(self):
        original = asdict(self.sim.run(factual_context(), motives()[0]))
        original["evaluation"]["decision"]["framework_rank"] = "CERTAIN"
        original["audit_digest"] = digest({k: v for k, v in original.items() if k != "audit_digest"})
        with self.assertRaisesRegex(ValueError, "replay result mismatch"):
            Simulator.replay(original)

    def test_41_tampered_input_with_stale_hash_is_detected(self):
        original = asdict(self.sim.run(factual_context(), motives()[0]))
        original["motive_json"] = canonical(asdict(motives()[1]))
        with self.assertRaisesRegex(ValueError, "integrity failure"):
            Simulator.replay(original)

    def test_42_whole_record_regeneration_is_not_source_authentication(self):
        first = self.sim.run(factual_context(), motives()[0])
        replacement = self.sim.run(factual_context(), motives()[1])
        self.assertNotEqual(first.audit_digest, replacement.audit_digest)
        self.assertEqual(asdict(Simulator.replay(asdict(replacement))), asdict(replacement))

    def test_43_unclassified_motive_is_permitted_without_forcing_instinct(self):
        run = self.sim.run(factual_context(), Motive("curiosity", "سؤال بحثي دون نسبة غريزية مثبتة"))
        self.assertEqual(run.evaluation.decision.status, "ALLOW")
        with self.assertRaises(ValueError):
            self.sim.run(factual_context(), Motive("m", "مصنف بلا مصدر", "SURVIVAL"))

    def test_44_typed_context_snapshot_detaches_caller_mutable_lists(self):
        raw = asdict(factual_context())
        c = context_from_dict(raw)
        before = epistemic_projection(self.sim.evaluate(c))
        raw["evidence"][0]["evidence"]["payload"] = "changed caller object"
        self.assertEqual(before, epistemic_projection(self.sim.evaluate(c)))

    def test_45_supplied_conclusion_cannot_replace_registered_modus_ponens_target(self):
        c = conditional_context()
        steps = tuple(replace(s, claim_id="p") if s.id == "derive-r" else s for s in c.steps)
        r = self.sim.evaluate(replace(c, steps=steps, question=replace(c.question, claim_id="p")))
        self.assertIn("DECLARED_CONCLUSION_MISMATCH", r.decision.reasons)

    def test_46_base_v05_copy_has_original_recorded_sha256(self):
        expected = "615ac9868bb9b878f90343adb47f56f69deb5417b19d9a220ca24e98a5ddf000"
        self.assertEqual(hashlib.sha256(Path(guardian.__file__).read_bytes()).hexdigest(), expected)

    def test_47_independent_suitability_evidence_is_also_bound_to_state(self):
        c = suitability_context()
        independent = replace(c.evidence[0], role="INDEPENDENT_REVIEW")
        c = replace(c, evidence=(independent,))
        self.assertEqual(self.sim.evaluate(c).decision.status, "ALLOW")
        newstate = replace(c.subject_state, id="state-new", description="حالة جديدة")
        changed = replace(c, subject_state=newstate,
            scopes=(replace(c.scopes[0], subject_state_id=newstate.id),))
        self.assertIn("EVIDENCE_SUBJECT_STATE_MISMATCH", self.sim.evaluate(changed).decision.reasons)

    def test_48_same_state_id_with_changed_contents_invalidates_evidence_binding(self):
        c = suitability_context()
        changed = replace(c, subject_state=replace(c.subject_state, description="محتوى مختلف تحت المعرف نفسه"))
        self.assertIn("EVIDENCE_SUBJECT_STATE_CONTENT_CHANGED", self.sim.evaluate(changed).decision.reasons)

    def test_49_suitability_subject_identity_is_separate_from_target_identity(self):
        c = suitability_context()
        self.assertNotEqual(c.subject_state.subject_id, c.question.target_id)
        self.assertEqual(self.sim.evaluate(c).decision.status, "ALLOW")
        wrong = replace(c, scopes=(replace(c.scopes[0], subject_id="different-person"),))
        self.assertIn("SUITABILITY_SUBJECT_IDENTITY_MISMATCH", self.sim.evaluate(wrong).decision.reasons)

    def test_50_subjective_report_cannot_establish_intermediate_essence_for_suitability(self):
        c = conditional_context()
        state = suitability_context().subject_state
        scopes = tuple(ClaimScope(s.claim_id, "ASSESS_SUITABILITY", "SUITABILITY", state.id, state.subject_id)
                       if s.claim_id == "r" else replace(s, aspect="ESSENCE") if s.claim_id == "p" else s
                       for s in c.scopes)
        steps = (Step("admit-p", "ADMIT_REGISTERED_EVIDENCE", "p", "subjective premise", ("e-p",)),
                 c.steps[1], replace(c.steps[2], antecedent_step_id="admit-p"), *c.steps[3:])
        subjective = replace(review("p"), role="SUBJECTIVE_REPORT", subject_state_id=state.id,
                             subject_state_fingerprint=digest(asdict(state)))
        c = replace(c, question=replace(c.question, intent="ASSESS_SUITABILITY", aspect="SUITABILITY"),
                    scopes=scopes, subject_state=state, steps=steps, evidence=(subjective, *c.evidence))
        result = self.sim.evaluate(c)
        self.assertEqual(result.decision.status, "BLOCK")
        self.assertTrue(any("SUBJECTIVE_REPORT_NOT_IDENTITY_EVIDENCE" in s.reasons for s in result.stages))

    def test_51_scope_intent_aspect_and_report_type_checked_on_every_used_step(self):
        c = conditional_context()
        for intent, aspect in (("ASSESS_SUITABILITY", "ESSENCE"), ("REPORT_NORMATIVE", "REPORT_OCCURRENCE")):
            scopes = tuple(replace(s, intent=intent, aspect=aspect) if s.claim_id == "p" else s for s in c.scopes)
            result = self.sim.evaluate(replace(c, scopes=scopes))
            self.assertEqual(result.decision.status, "BLOCK")

    def test_52_rank_certificate_binds_claim_policy_and_evidence_contents(self):
        c = prior_context(certified=True)
        altered_evidence = replace(c.evidence[0], evidence=replace(c.evidence[0].evidence, payload="different evidence"))
        altered_version = replace(c.evidence[0], evidence=replace(c.evidence[0].evidence, version=2))
        changes = [replace(c, evidence=(altered_evidence,)), replace(c, evidence=(altered_version,)),
                   replace(c, claims=(replace(c.claims[0], expression="different claim"),)),
                   replace(c, policy=replace(c.policy, framework="different interpretation"))]
        for changed in changes:
            with self.subTest(changed=changed):
                self.assertEqual(self.sim.evaluate(changed).decision.status, "DEFER")

    def test_53_unsigned_prior_label_cannot_override_valid_rank_certificate(self):
        c = prior_context(certified=True)
        labelled = replace(c, priors=(replace(c.priors[0], claimed_rank="TENTATIVE"),))
        self.assertEqual(epistemic_projection(self.sim.evaluate(c)), epistemic_projection(self.sim.evaluate(labelled)))

    def test_54_declared_prior_dependency_cannot_leak_across_claims(self):
        c = prior_context(claimed_rank="TENTATIVE")
        q = Claim("q", "demo", "sample-1", "قضية أخرى تعتمد على الرأي المستبعد")
        eq = replace(review("q"), declared_prior_dependencies=("old-opinion",))
        c = replace(c, question=replace(c.question, claim_id="q"), claims=c.claims + (q,),
                    scopes=c.scopes + (ClaimScope("q", "DESCRIBE_REALITY", "PROPERTY"),),
                    evidence=c.evidence + (eq,), steps=(Step("admit-q", "ADMIT_REGISTERED_EVIDENCE", "q", "declared dependency", ("e-q",)),),
                    final_step_id="admit-q")
        self.assertIn("DECLARED_DEPENDENCE_ON_EXCLUDED_OPINION", self.sim.evaluate(c).decision.reasons)
        unknown = replace(c, evidence=(replace(eq, declared_prior_dependencies=("unknown-prior",)),))
        self.assertIn("UNKNOWN_DECLARED_PRIOR_DEPENDENCY", self.sim.evaluate(unknown).decision.reasons)

    def test_55_conditional_mode_without_assumptions_retains_conditional_flag(self):
        c = conditional_context()
        steps = (Step("admit-p", "ADMIT_REGISTERED_EVIDENCE", "p", "registered evidence", ("e-p",)),
                 c.steps[1], replace(c.steps[2], antecedent_step_id="admit-p"), *c.steps[3:])
        c = replace(c, assumptions=(), evidence=(review("p"), *c.evidence), steps=steps)
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.verdict, "CONDITIONAL_ONLY")
        self.assertEqual(r.decision.assumptions, ())
        self.assertTrue(r.decision.conditional)

    def test_56_opposition_does_not_downgrade_block_or_erase_reasons(self):
        c = factual_context()
        c = replace(c, evidence=(replace(c.evidence[0], role="AFFECT_SIGNAL"),),
                    oppositions=(Opposition("opp", "p", "not-p", (), "pending"),))
        r = self.sim.evaluate(c)
        self.assertEqual(r.decision.status, "BLOCK")
        self.assertIn("AFFECT_SIGNAL_IS_NOT_FACTUAL_EVIDENCE", r.decision.reasons)
        self.assertIn("CONFLICT_PENDING_REVIEW", r.decision.reasons)
        self.assertEqual(r.decision.opposition_ids, ("opp",))

    def test_57_projection_preserves_lexical_and_rank_review_warrants(self):
        lexical = lexical_context()
        changed = replace(lexical, bridges=(replace(lexical.bridges[0], review_ref="different-attributed-review"),))
        first, second = self.sim.evaluate(lexical), self.sim.evaluate(changed)
        self.assertEqual(first.decision.status, second.decision.status)
        self.assertNotEqual(first.decision.justification_fingerprints, second.decision.justification_fingerprints)
        prior = prior_context(certified=True)
        changed_prior = replace(prior, rank_certificates=(replace(prior.rank_certificates[0], review_ref="different-review"),))
        self.assertNotEqual(epistemic_projection(self.sim.evaluate(prior)), epistemic_projection(self.sim.evaluate(changed_prior)))
        chain = conditional_context()
        original_warrants = dict(self.sim.evaluate(chain).decision.justification_fingerprints)
        changed_claim = replace(chain, claims=tuple(replace(c, expression="different antecedent content") if c.id == "p" else c for c in chain.claims))
        changed_scope = replace(chain, scopes=tuple(replace(s, aspect="ESSENCE") if s.claim_id == "p" else s for s in chain.scopes))
        changed_assumption = replace(chain, assumptions=(replace(chain.assumptions[0], source_ref="different assumption source"),))
        for changed_context, key in ((changed_claim, "claim:p"), (changed_scope, "claim_scope:p"),
                                     (changed_assumption, "assumption:h-p")):
            with self.subTest(warrant=key):
                self.assertNotEqual(original_warrants[key], dict(self.sim.evaluate(changed_context).decision.justification_fingerprints)[key])
        conflict = replace(factual_context(), oppositions=(Opposition("opp", "p", "not-p", (), "review-1"),))
        changed_conflict = replace(conflict, oppositions=(replace(conflict.oppositions[0], relation_review_ref="review-2"),))
        first_opposition = dict(self.sim.evaluate(conflict).decision.justification_fingerprints)["opposition:opp"]
        second_opposition = dict(self.sim.evaluate(changed_conflict).decision.justification_fingerprints)["opposition:opp"]
        self.assertNotEqual(first_opposition, second_opposition)

    def test_58_suitability_aspect_cannot_bypass_state_contract_via_descriptive_intent(self):
        c = factual_context()
        c = replace(c, question=replace(c.question, aspect="SUITABILITY"),
                    scopes=(ClaimScope("p", "DESCRIBE_REALITY", "SUITABILITY"),))
        self.assertIn("SUITABILITY_ASPECT_REQUIRES_SUITABILITY_INTENT", self.sim.evaluate(c).decision.reasons)

    def test_59_prior_eligibility_is_not_admission_of_its_declared_dependents(self):
        c = factual_context()
        p = PriorRecord("info-prior", "p", "INFORMATION", "source", ())
        dependent = replace(c.evidence[0], declared_prior_dependencies=(p.id,))
        c = replace(c, priors=(p,), evidence=(dependent,))
        r = self.sim.evaluate(c)
        self.assertEqual(r.recall[0].status, "ELIGIBLE")
        self.assertEqual(r.decision.status, "DEFER")
        self.assertIn("DECLARED_DEPENDENCIES_REQUIRE_EXPLICIT_INFERENCE", r.decision.reasons)


if __name__ == "__main__":
    unittest.main(verbosity=2)
