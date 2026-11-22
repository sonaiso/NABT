"""Adversarial, bounded scenarios; no claim of full epistemic coverage."""
from __future__ import annotations

from dataclasses import asdict, replace
import copy
import json
import unittest

from tools.lexical_training.sim_aql.guardian import (Assumption, Claim, Evidence, Guardian, PolicyProfile,
                     canonical, digest)

NOW = "2026-11-22T12:00:00Z"
LATER = "2026-11-23T12:00:00Z"


class GuardianTests(unittest.TestCase):
    def setUp(self):
        self.g = Guardian()
        for key in ("p", "q", "r"):
            self.g.register_claim(Claim(key, "demo", "sample-1", "synthetic proposition " + key))
        self.g.register_claim(Claim("pq", "demo", "sample-1", "if p then q",
                                    "IMPLIES", "p", "q"))
        self.g.register_claim(Claim("qr", "demo", "sample-1", "if q then r",
                                    "IMPLIES", "q", "r"))

    def evidence(self, claim_id="p", evidence_id=None, **changes):
        evidence = Evidence(evidence_id or "ev-" + claim_id, 1, claim_id, "demo",
                            "sample-1", "EXTERNAL_ASSESSMENT", "synthetic-source-1",
                            "synthetic-review-1", "ACCEPTED", ("trace-original",),
                            "Synthetic evidence record; not a real-world observation.")
        evidence = replace(evidence, **changes)
        self.g.register_evidence(evidence)
        return evidence

    def admit(self, claim_id="p", **changes):
        evidence = self.evidence(claim_id, **changes)
        return self.g.admit(claim_id, (evidence.id,), NOW)

    def test_01_reviewed_evidence_admission_is_not_certainty(self):
        """Valid bounded admission enters Gamma without granting certainty."""
        result = self.admit()
        self.assertEqual(result.status, "ALLOW")
        self.assertEqual(result.verdict, "SUPPORTED_BY_REGISTERED_REVIEW")
        self.assertEqual(result.framework_rank, "NOT_ASSIGNED")
        self.assertIn(result.id, self.g.gamma(NOW))

    def test_02_opinion_registration_is_allowed_outside_gamma(self):
        """ALLOW storing a prior opinion does not make it an admitted premise."""
        result = self.g.assume(Assumption("opinion-1", "p", "OPINION", "speaker-1"), NOW)
        self.assertEqual(result.status, "ALLOW")
        self.assertEqual(result.verdict, "CONDITIONAL_ONLY")
        self.assertNotIn(result.id, self.g.gamma(NOW))
        self.assertIn("opinion-1", self.g.delta())

    def test_03_hypothesis_cannot_yield_factual_assertion(self):
        """A correct inference form cannot remove an unproved hypothesis."""
        p = self.g.assume(Assumption("h1", "p"), NOW)
        rule = self.admit("pq")
        result = self.g.modus_ponens(p.id, rule.id, "FACTUAL", NOW)
        self.assertEqual(result.status, "BLOCK")
        self.assertIn("UNDISCHARGED_ASSUMPTIONS", result.reasons)

    def test_04_assumption_dependency_survives_two_inferences(self):
        """Taint is transitive through two valid conditional derivations."""
        p = self.g.assume(Assumption("h1", "p"), NOW)
        pq, qr = self.admit("pq"), self.admit("qr")
        q = self.g.modus_ponens(p.id, pq.id, "CONDITIONAL", NOW)
        r = self.g.modus_ponens(q.id, qr.id, "CONDITIONAL", NOW)
        self.assertEqual((q.status, r.status), ("ALLOW", "ALLOW"))
        self.assertEqual(r.assumptions, ("h1",))
        self.assertEqual(r.verdict, "CONDITIONAL_ONLY")
        blocked = self.g.modus_ponens(q.id, qr.id, "FACTUAL", NOW)
        self.assertEqual(blocked.status, "BLOCK")
        self.assertNotIn(r.id, self.g.gamma(NOW))

    def test_05_independent_evidence_can_admit_previously_held_opinion(self):
        """A prior stance remains in history while its content gains a distinct warrant."""
        old = self.g.assume(Assumption("opinion-1", "p", "OPINION", "speaker-1"), NOW)
        new = self.admit("p")
        self.assertNotEqual(old.id, new.id)
        self.assertEqual(old.assumptions, ("opinion-1",))
        self.assertEqual(new.assumptions, ())
        self.assertIn(new.id, self.g.gamma(NOW))
        self.assertIn("opinion-1", self.g.delta())

    def test_06_claim_domain_and_target_mismatches_are_blocked(self):
        """Evidence for another claim, field or individual cannot be transferred silently."""
        for index, changes in enumerate(({"claim_id": "q"},
                                         {"domain": "another-domain"},
                                         {"target_id": "sample-2"})):
            with self.subTest(changes=changes):
                ev = self.evidence(evidence_id="mismatch-" + str(index), **changes)
                result = self.g.admit("p", (ev.id,), NOW)
                self.assertEqual(result.status, "BLOCK")

    def test_07_missing_trace_defers_admission(self):
        """An accepted review label cannot replace the missing trace."""
        result = self.admit(trace=())
        self.assertEqual(result.status, "DEFER")
        self.assertIn("MISSING_TRACE", result.reasons)

    def test_08_expiry_blocks_current_use_of_previously_accepted_evidence(self):
        """Validity at a past time does not silently authorize later reuse."""
        result = self.admit(expires_at="2026-11-23T00:00:00Z")
        self.assertIn(result.id, self.g.gamma(NOW))
        self.assertNotIn(result.id, self.g.gamma(LATER))
        fresh = self.g.admit("p", ("ev-p",), LATER)
        self.assertEqual(fresh.status, "DEFER")

    def test_09_blocking_residual_overrides_accepted_review(self):
        """A recorded blocker prevents transition even with an accepted external review."""
        result = self.admit(blocking_residuals=("identity-not-resolved",))
        self.assertEqual(result.status, "BLOCK")

    def test_10_unreviewed_evidence_remains_unassessed(self):
        """Source availability is distinct from an applicable evidence assessment."""
        result = self.admit(review_status="UNREVIEWED")
        self.assertEqual((result.status, result.verdict), ("DEFER", "UNASSESSED"))

    def test_11_report_occurrence_does_not_establish_report_content(self):
        """Evidence of saying p must not be laundered into evidence for p."""
        self.g.register_claim(Claim("said-p", "testimony", "speaker-1", "speaker said p",
                                    "REPORT", reported_claim_id="p"))
        ev = self.evidence("said-p", domain="testimony", target_id="speaker-1")
        said = self.g.admit("said-p", (ev.id,), NOW)
        content = self.g.admit("p", (ev.id,), NOW)
        self.assertEqual(said.status, "ALLOW")
        self.assertEqual(content.status, "BLOCK")
        self.assertIn("EVIDENCE_CLAIM_MISMATCH", content.reasons)

    def test_12_empirical_link_is_not_linguistic_iltizam(self):
        """An experimental association remains outside lexical implication."""
        ev = self.evidence(kind="EMPIRICAL_ASSOCIATION")
        result = self.g.linguistic_link(ev.id, "utterance-1", "usage-1", "relation-1", NOW)
        self.assertEqual(result.status, "BLOCK")
        self.assertIn("EXTERNAL_RELATION_IS_NOT_LEXICAL_ILTIZAM", result.reasons)

    def test_13_mental_link_requires_utterance_usage_and_necessity_record(self):
        """A mental-link kind alone is insufficient; scoped licensing references are needed."""
        ev = self.evidence(kind="MENTAL_LINGUISTIC")
        missing = self.g.linguistic_link(ev.id, "", "usage-1", "relation-1", NOW)
        complete = self.g.linguistic_link(ev.id, "utterance-1", "usage-1", "relation-1", NOW)
        self.assertEqual(missing.status, "DEFER")
        self.assertEqual(complete.status, "ALLOW")
        self.assertEqual(complete.verdict, "LINGUISTIC_LINK_CANDIDATE")
        self.assertNotIn(complete.id, self.g.gamma(NOW))

    def test_14_modus_ponens_requires_exact_registered_antecedent(self):
        """The caller cannot substitute q for p just because both are admitted."""
        q, pq = self.admit("q"), self.admit("pq")
        result = self.g.modus_ponens(q.id, pq.id, "FACTUAL", NOW)
        self.assertEqual(result.status, "BLOCK")
        self.assertIn("MODUS_PONENS_OPERAND_MISMATCH", result.reasons)

    def test_15_evidence_revision_suspends_transitive_results_and_preserves_history(self):
        """Revised input invalidates current use of descendants without deleting their history."""
        p, pq, qr = self.admit("p"), self.admit("pq"), self.admit("qr")
        q = self.g.modus_ponens(p.id, pq.id, "FACTUAL", NOW)
        r = self.g.modus_ponens(q.id, qr.id, "FACTUAL", NOW)
        self.assertIn(r.id, self.g.gamma(NOW))
        old = self.g.evidence["ev-p"]
        self.g.register_evidence(replace(old, version=2, review_status="REJECTED"))
        for result in (p, q, r):
            self.assertNotIn(result.id, self.g.gamma(NOW))
            self.assertIn("EVIDENCE_VERSION_CHANGED:ev-p", self.g.current_issues(result.id, NOW))
            self.assertEqual(self.g.assessments[result.id].status, "ALLOW")
        self.assertEqual(self.g.evidence_history[("ev-p", 1)], old)

    def test_16_policy_change_requires_reassessment_and_replays(self):
        """A new policy revision cannot reuse old certificates silently."""
        p = self.admit("p")
        self.g.revise_policy(replace(self.g.policy, version="0.5.1"))
        self.assertNotIn(p.id, self.g.gamma(NOW))
        self.assertIn("POLICY_VERSION_CHANGED", self.g.current_issues(p.id, NOW))
        replayed = Guardian.replay(self.g.export_log())
        self.assertEqual(replayed.policy.version, "0.5.1")
        self.assertEqual(replayed.events, self.g.events)

    def test_17_no_or_unknown_evidence_defers(self):
        """A well-formed claim is not evidence for itself."""
        for refs in ((), ("unknown",)):
            with self.subTest(refs=refs):
                result = self.g.admit("p", refs, NOW)
                self.assertEqual(result.status, "DEFER")

    def test_18_sensory_existence_claim_never_gets_automatic_certainty(self):
        """Sensory and existence tags are not certainty-generating operators."""
        self.g.register_claim(Claim("exists", "demo", "sample-1", "sample exists", "EXISTENCE"))
        result = self.admit("exists", kind="SENSORY_REPORT")
        self.assertEqual(result.framework_rank, "NOT_ASSIGNED")
        self.assertEqual(result.policy_source_status, "UNVERIFIED")

    def test_19_replay_preserves_gates_assumptions_and_current_gamma(self):
        """A complete trace reproduces computed outcomes and premise segregation."""
        p = self.g.assume(Assumption("h1", "p"), NOW)
        pq, qr = self.admit("pq"), self.admit("qr")
        q = self.g.modus_ponens(p.id, pq.id, "CONDITIONAL", NOW)
        self.g.modus_ponens(q.id, qr.id, "FACTUAL", NOW)
        replayed = Guardian.replay(self.g.export_log())
        self.assertEqual(replayed.events, self.g.events)
        self.assertEqual(replayed.gamma(NOW), self.g.gamma(NOW))
        self.assertEqual(replayed.delta(), self.g.delta())

    def test_20_modified_audit_payload_is_detected(self):
        """Changing a stored event without recomputing its chain is detected."""
        self.admit("p")
        log = self.g.export_log()
        log["events"][0]["payload"]["expression"] = "tampered"
        with self.assertRaisesRegex(ValueError, "integrity"):
            Guardian.replay(log)

    def test_21_rehashed_forged_outcome_fails_reexecution(self):
        """Rehashing a false result is insufficient when replay recomputes the gate."""
        self.g.admit("p", (), NOW)
        log = self.g.export_log()
        log["events"][-1]["result"]["status"] = "ALLOW"
        previous = None
        for event in log["events"]:
            event["previous_hash"] = previous
            event["event_hash"] = digest({k: v for k, v in event.items() if k != "event_hash"})
            previous = event["event_hash"]
        with self.assertRaisesRegex(ValueError, "result mismatch"):
            Guardian.replay(log)

    def test_22_canonical_digest_ignores_dictionary_key_order(self):
        """Equivalent record key orders share the prototype's canonical digest."""
        self.assertEqual(digest({"a": 1, "b": [2, 3]}), digest({"b": [2, 3], "a": 1}))
        with self.assertRaises(ValueError):
            canonical({"not_finite": float("nan")})

    def test_23_identity_collision_and_version_rollback_are_rejected(self):
        """Stable IDs cannot silently change their content or move backwards in version."""
        with self.assertRaisesRegex(ValueError, "identity collision"):
            self.g.register_claim(Claim("p", "demo", "sample-1", "different assertion"))
        ev = self.evidence()
        with self.assertRaisesRegex(ValueError, "strictly increase"):
            self.g.register_evidence(replace(ev, payload="overwritten"))

    def test_24_many_records_do_not_create_tawatur_or_certainty(self):
        """Even multiple accepted records from one source do not imply a transmission rank."""
        records = [self.evidence(evidence_id="copy-" + str(i)) for i in range(12)]
        result = self.g.admit("p", tuple(x.id for x in records), NOW)
        self.assertEqual(result.framework_rank, "NOT_ASSIGNED")
        self.assertEqual(result.verdict, "SUPPORTED_BY_REGISTERED_REVIEW")

    def test_25_linguistic_link_candidate_cannot_be_used_as_factual_premise(self):
        """ALLOW a linguistic candidate must not grant factual inference authority."""
        ev = self.evidence(kind="MENTAL_LINGUISTIC")
        p = self.g.linguistic_link(ev.id, "utterance-1", "usage-1", "relation-1", NOW)
        rule = self.admit("pq")
        result = self.g.modus_ponens(p.id, rule.id, "FACTUAL", NOW)
        self.assertEqual(result.status, "BLOCK")
        self.assertIn("PREDECESSOR_IS_NOT_AN_INFERENCE_PREMISE", result.reasons)

    def test_26_missing_external_review_or_payload_defers(self):
        """A named evidence record alone cannot satisfy evidence admission."""
        for i, changes in enumerate(({"review_ref": ""}, {"payload": ""}, {"source_ref": ""})):
            ev = self.evidence(evidence_id="incomplete-" + str(i), **changes)
            self.assertEqual(self.g.admit("p", (ev.id,), NOW).status, "DEFER")

    def test_27_naive_timestamps_are_rejected(self):
        """Time-based validity cannot silently assume an unstated timezone."""
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.g.admit("p", (), "2026-11-22T12:00:00")

    def test_28_rejected_assumption_does_not_mutate_any_register(self):
        """Invalid assumption time, ID or provenance fails atomically before registration."""
        requests = [(Assumption("h1", "p"), "2026-11-22T12:00:00"),
                    (Assumption("", "p"), NOW),
                    (Assumption("h2", "p", source_ref=" "), NOW)]
        before = (dict(self.g.assumptions), dict(self.g.assessments), copy.deepcopy(self.g.events))
        for assumption, as_of in requests:
            with self.subTest(assumption=assumption, as_of=as_of):
                with self.assertRaises(ValueError):
                    self.g.assume(assumption, as_of)
                self.assertEqual((self.g.assumptions, self.g.assessments, self.g.events), before)

    def test_29_future_assessment_cannot_authorize_an_earlier_inference(self):
        """Evaluation as of a past time excludes judgments not available then."""
        evidence = self.evidence("p")
        future_p = self.g.admit("p", (evidence.id,), LATER)
        rule = self.admit("pq")
        self.assertNotIn(future_p.id, self.g.gamma(NOW))
        result = self.g.modus_ponens(future_p.id, rule.id, "FACTUAL", NOW)
        self.assertEqual(result.status, "DEFER")
        self.assertIn("ASSESSMENT_NOT_YET_AVAILABLE", result.reasons)

    def test_30_evidence_revision_cannot_change_claim_domain_or_target(self):
        """An evidence revision retains its supported identity; retargeting needs a new ID."""
        old = self.evidence("p")
        before_events = copy.deepcopy(self.g.events)
        for changes in ({"claim_id": "q"}, {"domain": "other"}, {"target_id": "sample-2"}):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, "identity changed"):
                    self.g.register_evidence(replace(old, version=2, **changes))
                self.assertEqual(self.g.evidence[old.id], old)
                self.assertEqual(self.g.events, before_events)

    def test_31_gamma_filters_preserve_domain_and_target_boundaries(self):
        """The inventory supports scope selection without implying cross-scope inference."""
        a = self.admit("p")
        self.g.register_claim(Claim("other-p", "other", "sample-2", "other proposition"))
        ev = self.evidence("other-p", domain="other", target_id="sample-2")
        b = self.g.admit("other-p", (ev.id,), NOW)
        self.assertEqual(set(self.g.gamma(NOW)), {a.id, b.id})
        self.assertEqual(self.g.gamma(NOW, domain="demo"), (a.id,))
        self.assertEqual(self.g.gamma(NOW, target_id="sample-2"), (b.id,))
        self.assertEqual(self.g.gamma(NOW, domain="demo", target_id="sample-2"), ())
