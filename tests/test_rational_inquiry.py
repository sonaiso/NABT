"""Independently authored adversarial inquiry-contract probes.

These are authored finite tests, not held-out natural language or external
world-truth evaluation. Expected outcomes follow the declared contract and
counterexamples, rather than reproducing the production decision recurrence.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nabt.errors import NabtError
from nabt.rational_inquiry import audit_inquiry, decide_gate, verify_inquiry


LAW_ID = "nabt.rational-inquiry.v1"


def sample():
    """A candidate and a separate declared record, with one discriminating rival."""
    scope = {"domain": "bounded-text-record", "referent": "record-17",
             "time": "snapshot-1", "unit": "exact-utf8-text"}
    plan = {
        "version": LAW_ID,
        "claim": {"claim_id": "reading-17", "kind": "TEXT_CORRESPONDENCE",
                  "candidate": "عدد السجلات ثلاثة.", "scope": scope,
                  "origin_sources": [{"source_id": "formation", "revision": 1}]},
        "formation": {
            "purpose": "التحقق من قراءة سجل محدد",
            "interpretation": "القضية عن محتوى السجل، لا عن عدد أشياء العالم",
            "inference": "مقارنة النص المقترح بكامل نص السجل المرجعي",
            "prior": [],
        },
        "review": {
            "depth": "DEEP", "context": [], "conditions": [],
            "alternatives": [{"alternative_id": "four-records",
                              "candidate": "عدد السجلات أربعة."}],
            "limitations": ["المطابقة تخص السجل المقدم ونسبته المصرح بها فقط"],
            "unresolved": [],
        },
        "requested_rank": 2,
    }
    sources = [
        {"source_id": "formation", "revision": 1, "scope": deepcopy(scope),
         "content": "قراءة مرشحة تحتاج إلى مقارنة مستقلة.",
         "origin": "proposal-run-A", "parents": [], "role": "MATERIAL", "active": True},
        {"source_id": "reference", "revision": 1, "scope": deepcopy(scope),
         "content": "عدد السجلات ثلاثة.", "origin": "record-snapshot-B",
         "parents": [], "role": "REFERENCE", "active": True},
    ]
    return plan, sources


def source_like(source, source_id, **changes):
    result = deepcopy(source)
    result.update(source_id=source_id, **changes)
    return result


def codes(report):
    return {item["code"] for item in report["residuals"]}


class BoundedComparisonTests(unittest.TestCase):
    def test_record_comparison_executes_and_preserves_authority_boundary(self):
        plan, sources = sample()
        report = audit_inquiry(plan, sources)
        self.assertEqual((report["status"], report["authorized_rank"]), ("LICENSED", 2))
        self.assertEqual(report["authority"], "SNAPSHOT_COMPARISON")
        self.assertTrue(report["box_opened"])
        self.assertTrue(report["coverage_complete"])
        self.assertTrue(report["review_complete"])
        self.assertEqual(report["world_truth"], "NOT_ESTABLISHED")
        self.assertIs(report["external_truth_certified"], False)
        checked = report["checks"]
        self.assertEqual([(c["purpose"], c["passed"]) for c in checked],
                         [("claim", True), ("alternative", False)])
        self.assertEqual(checked[0]["actual_sha256"],
                         sha256(sources[1]["content"].encode("utf-8")).hexdigest())

    def test_a_single_differing_character_is_a_record_counterexample(self):
        plan, sources = sample()
        sources[1]["content"] += "!"
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "REFUTED")
        self.assertEqual(report["authorized_rank"], 0)
        self.assertFalse(report["checks"][0]["passed"])

    def test_both_reference_records_are_checked_and_conflict_is_order_independent(self):
        plan, sources = sample()
        sources.append(source_like(sources[1], "counter-record", content="عدد السجلات اثنان.",
                                   origin="record-snapshot-C"))
        forward = audit_inquiry(plan, sources)
        reverse = audit_inquiry(plan, list(reversed(sources)))
        self.assertEqual(forward["status"], "CONFLICT")
        self.assertEqual(forward, reverse)
        self.assertEqual({c["source_id"] for c in forward["checks"]},
                         {"reference", "counter-record"})

    def test_world_claim_never_inherits_matching_or_mismatching_record_authority(self):
        for contents in (("عدد السجلات ثلاثة.",), ("عدد السجلات اثنان.",),
                         ("عدد السجلات ثلاثة.", "عدد السجلات اثنان.")):
            with self.subTest(contents=contents):
                plan, sources = sample()
                plan["claim"]["kind"] = "WORLD_CORRESPONDENCE"
                sources[1]["content"] = contents[0]
                if len(contents) == 2:
                    sources.append(source_like(sources[1], "other-record", content=contents[1],
                                               origin="record-snapshot-C"))
                report = audit_inquiry(plan, sources)
                self.assertEqual(report["status"], "DEFER")
                self.assertEqual(report["authorized_rank"], 0)
                self.assertEqual(report["world_truth"], "NOT_ESTABLISHED")
                self.assertIs(report["external_truth_certified"], False)
                self.assertFalse(report["box_opened"])
                self.assertGreater(report["checks_performed"], 0)
                self.assertIn("WORLD_BRIDGE_UNAVAILABLE", codes(report))

    def test_each_scope_coordinate_must_match(self):
        for coordinate in ("domain", "referent", "time", "unit"):
            with self.subTest(coordinate=coordinate):
                plan, sources = sample()
                sources[1]["scope"][coordinate] += "-different"
                report = audit_inquiry(plan, sources)
                self.assertEqual(report["status"], "DEFER")
                self.assertFalse(report["box_opened"])
                self.assertFalse(report["coverage_complete"])
                self.assertEqual(report["authorized_rank"], 0)
                self.assertIn("NO_SCOPED_REFERENCE", codes(report))

    def test_zero_and_partial_budget_never_close_the_check(self):
        for budget in (0, 1):
            with self.subTest(budget=budget):
                plan, sources = sample()
                report = audit_inquiry(plan, sources, max_checks=budget)
                self.assertEqual(report["status"], "RESOURCE_LIMIT")
                self.assertEqual(report["authorized_rank"], 0)
                self.assertFalse(report["coverage_complete"])
                self.assertFalse(report["review_complete"])
                self.assertEqual(report["box_opened"], budget == 1)

    def test_exactly_sufficient_budget_is_not_reported_as_exhausted(self):
        plan, sources = sample()
        report = audit_inquiry(plan, sources, max_checks=2)
        self.assertEqual(report["status"], "LICENSED")
        self.assertFalse(report["gates"]["exhausted"])

    def test_human_rank_label_does_not_upgrade_evidence(self):
        plan, sources = sample()
        plan["requested_rank"] = 3
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["authorized_rank"], 0)
        self.assertEqual(report["gates"]["evidenceRank"], 2)


class DeclaredProvenanceTests(unittest.TestCase):
    def test_new_identifier_with_shared_origin_does_not_create_independence(self):
        plan, sources = sample()
        sources[1]["origin"] = sources[0]["origin"]
        sources.append(source_like(sources[1], "duplicate-reference"))
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["gates"]["evidenceRank"], 1)
        self.assertIn("SHARED_DECLARED_ORIGIN", codes(report))

    def test_reference_descended_from_formation_is_not_independent(self):
        plan, sources = sample()
        sources[1]["parents"] = [{"source_id": "formation", "revision": 1}]
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["gates"]["evidenceRank"], 1)
        self.assertIn(sources[0]["origin"],
                      report["provenance"]["reference_origins"]["reference"])

    def test_shared_ancestor_of_two_differently_named_records_is_found(self):
        plan, sources = sample()
        ancestor = source_like(sources[0], "shared-ancestor", origin="common-acquisition")
        sources.append(ancestor)
        parent = [{"source_id": "shared-ancestor", "revision": 1}]
        sources[0]["parents"] = deepcopy(parent)
        sources[1]["parents"] = deepcopy(parent)
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "DEFER")
        self.assertIn("common-acquisition", report["provenance"]["candidate_origins"])

    def test_circular_provenance_is_rejected_including_inactive_rows(self):
        for active in (True, False):
            with self.subTest(active=active):
                plan, sources = sample()
                sources[0]["parents"] = [{"source_id": "reference", "revision": 1}]
                sources[1]["parents"] = [{"source_id": "formation", "revision": 1}]
                sources[1]["active"] = active
                with self.assertRaises(NabtError) as caught:
                    audit_inquiry(plan, sources)
                self.assertEqual(caught.exception.code, "CYCLIC_PROVENANCE")

    def test_missing_dependency_cannot_be_silently_omitted_from_coverage(self):
        plan, sources = sample()
        sources.append(source_like(sources[1], "unusable-counter-record",
                                   content="عدد السجلات اثنان.", origin="record-snapshot-C",
                                   parents=[{"source_id": "missing-parent", "revision": 1}]))
        report = audit_inquiry(plan, sources)
        self.assertFalse(report["coverage_complete"])
        self.assertNotEqual(report["status"], "LICENSED")
        self.assertEqual(report["authorized_rank"], 0)
        self.assertIn("REFERENCE_DEPENDENCY_UNAVAILABLE", codes(report))

    def test_partial_negative_inventory_does_not_authorize_refutation(self):
        plan, sources = sample()
        sources[1]["content"] = "عدد السجلات اثنان."
        sources.append(source_like(sources[1], "unusable-other-record",
                                   content=plan["claim"]["candidate"], origin="record-snapshot-C",
                                   parents=[{"source_id": "missing-parent", "revision": 1}]))
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "DEFER")
        self.assertTrue(report["gates"]["counterevidence"])
        self.assertFalse(report["coverage_complete"])
        self.assertEqual(report["authorized_rank"], 0)

    def test_stale_reference_ancestor_is_not_live_evidence(self):
        plan, sources = sample()
        sources[1]["parents"] = [{"source_id": "formation", "revision": 0}]
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "DEFER")
        self.assertFalse(report["box_opened"])

    def test_revoked_support_invalidates_old_report_and_preserves_an_independent_route(self):
        plan, sources = sample()
        sources.append(source_like(sources[1], "independent-reference", origin="record-snapshot-C"))
        previous = audit_inquiry(plan, sources)
        sources[1]["active"] = False
        current = audit_inquiry(plan, sources)
        self.assertEqual(current["status"], "LICENSED")
        self.assertEqual({c["source_id"] for c in current["checks"]}, {"independent-reference"})
        self.assertFalse(verify_inquiry(previous, plan, sources)["valid"])
        self.assertTrue(verify_inquiry(current, plan, sources)["valid"])
        sources[2]["active"] = False
        self.assertEqual(audit_inquiry(plan, sources)["status"], "DEFER")

    def test_missing_or_stale_formation_prevents_formation(self):
        for mutation in ("inactive", "revision", "empty"):
            with self.subTest(mutation=mutation):
                plan, sources = sample()
                if mutation == "inactive":
                    sources[0]["active"] = False
                elif mutation == "revision":
                    sources[0]["revision"] += 1
                else:
                    plan["claim"]["origin_sources"] = []
                self.assertEqual(audit_inquiry(plan, sources)["status"], "UNFORMED")


class ReviewAndReplayTests(unittest.TestCase):
    def test_context_only_comparison_does_not_open_the_claim_box(self):
        plan, sources = sample()
        sources.pop()
        context = source_like(sources[0], "context", role="CONTEXT", origin="context-C")
        sources.append(context)
        plan["review"]["context"] = [{"source_id": "context", "revision": 1,
                                        "expected": context["content"]}]
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["checks_performed"], 1)
        self.assertEqual(report["checks"][0]["purpose"], "context")
        self.assertFalse(report["box_opened"])
        self.assertFalse(report["coverage_complete"])
        self.assertNotEqual(report["status"], "LICENSED")

    def test_asserted_unresolved_issue_blocks_licensing(self):
        plan, sources = sample()
        plan["review"]["unresolved"] = ["هوية السجل لم تحسم"]
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "UNREVIEWED")
        self.assertFalse(report["review_complete"])

    def test_enlightened_label_requires_executed_context_and_condition_checks(self):
        plan, sources = sample()
        plan["review"]["depth"] = "ENLIGHTENED"
        empty = audit_inquiry(plan, sources)
        self.assertEqual(empty["status"], "UNREVIEWED")
        context = source_like(sources[0], "context", role="CONTEXT", origin="context-C",
                              content="هذا سجل مكتمل.")
        sources.append(context)
        for field in ("context", "conditions"):
            plan["review"][field] = [{"source_id": "context", "revision": 1,
                                      "expected": context["content"]}]
        checked = audit_inquiry(plan, sources)
        self.assertEqual(checked["status"], "LICENSED")
        self.assertEqual([c["purpose"] for c in checked["checks"]],
                         ["claim", "alternative", "context", "conditions"])
        sources[-1]["content"] = "هذا سجل مبتور."
        failed = audit_inquiry(plan, sources)
        self.assertEqual(failed["status"], "UNREVIEWED")
        self.assertIn("REVIEW_CHECK_FAILED", codes(failed))

    def test_context_for_a_different_time_cannot_complete_review(self):
        plan, sources = sample()
        sources.append(source_like(sources[0], "context", role="CONTEXT", origin="context-C"))
        sources[-1]["scope"]["time"] = "obsolete-snapshot"
        plan["review"]["context"] = [{"source_id": "context", "revision": 1,
                                        "expected": sources[-1]["content"]}]
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "UNREVIEWED")
        self.assertIn("REVIEW_SOURCE_UNAVAILABLE", codes(report))

    def test_replay_binds_every_target_coordinate_and_review_criterion(self):
        plan, sources = sample()
        report = audit_inquiry(plan, sources)
        self.assertTrue(verify_inquiry(report, plan, sources)["valid"])
        for field in ("domain", "referent", "time", "unit"):
            with self.subTest(field=field):
                changed = deepcopy(plan)
                changed["claim"]["scope"][field] += "-changed"
                self.assertFalse(verify_inquiry(report, changed, sources)["valid"])
        changed = deepcopy(plan)
        changed["claim"]["candidate"] += "!"
        self.assertFalse(verify_inquiry(report, changed, sources)["valid"])
        changed = deepcopy(plan)
        changed["requested_rank"] = 1
        self.assertFalse(verify_inquiry(report, changed, sources)["valid"])
        changed = deepcopy(plan)
        changed["review"]["alternatives"][0]["candidate"] += "!"
        self.assertFalse(verify_inquiry(report, changed, sources)["valid"])

    def test_replay_recomputes_source_bytes_not_applicant_hashes(self):
        plan, sources = sample()
        report = audit_inquiry(plan, sources)
        sources[1]["content"] += "!"
        forged = deepcopy(report)
        new_digest = sha256(sources[1]["content"].encode("utf-8")).hexdigest()
        for check in forged["checks"]:
            check["actual_sha256"] = new_digest
        for source in forged["sources_used"]:
            if source["source_id"] == "reference":
                source["content_sha256"] = new_digest
        self.assertFalse(verify_inquiry(report, plan, sources)["valid"])
        self.assertFalse(verify_inquiry(forged, plan, sources)["valid"])

    def test_self_declared_world_truth_or_missing_checks_do_not_verify(self):
        plan, sources = sample()
        report = audit_inquiry(plan, sources)
        for changes in ({"world_truth": "ESTABLISHED"}, {"external_truth_certified": True},
                        {"authorized_rank": 3}, {"checks": []}, {"RealityWitness": True}):
            with self.subTest(changes=changes):
                forged = deepcopy(report)
                forged.update(changes)
                self.assertFalse(verify_inquiry(forged, plan, sources)["valid"])

    def test_verified_refutation_does_not_verify_the_claim(self):
        plan, sources = sample()
        sources[1]["content"] = "نص آخر."
        report = audit_inquiry(plan, sources)
        verified = verify_inquiry(report, plan, sources)
        self.assertTrue(verified["valid"])
        self.assertEqual(verified["claim_status"], "REFUTED")
        self.assertEqual(verified["world_truth"], "NOT_ESTABLISHED")


class SourceEntailmentTests(unittest.TestCase):
    def semantic_sample(self):
        plan, sources = sample()
        plan["claim"].update(kind="SOURCE_ENTAILMENT", candidate="هل سالم هو محفوظ؟")
        plan["requested_rank"] = 1
        plan["review"].update(depth="SURFACE", alternatives=[])
        sources[1]["content"] = "سالم هو نقي\nكل نقي هو محفوظ"
        return plan, sources

    def test_entailment_reextracts_text_but_remains_source_relative(self):
        plan, sources = self.semantic_sample()
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "LICENSED")
        self.assertEqual(report["authorized_rank"], 1)
        self.assertEqual(report["authority"], "SOURCE_RELATIVE_INFERENCE")
        self.assertEqual(report["checks"][0]["status"], "SUPPORTED")
        self.assertEqual(report["world_truth"], "NOT_ESTABLISHED")

    def test_entailment_conflict_is_retained(self):
        plan, sources = self.semantic_sample()
        sources.append(source_like(sources[1], "negative", origin="negative-C",
                                   content="ليس سالم هو محفوظ"))
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "CONFLICT")
        self.assertEqual(report["authorized_rank"], 0)

    def test_negative_derivation_through_contested_premise_does_not_refute(self):
        plan, sources = self.semantic_sample()
        sources[1]["content"] = ("سالم هو نقي\nليس سالم هو نقي\n"
                                  "إذا كان ?س هو نقي فإن ليس ?س هو محفوظ")
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["checks"][0]["status"], "DEFER")
        self.assertEqual(report["status"], "DEFER")
        self.assertFalse(report["gates"]["counterevidence"])
        self.assertFalse(report["gates"]["exhausted"])
        self.assertEqual(report["authorized_rank"], 0)

    def test_unknown_alternative_is_unresolved_not_eliminated(self):
        plan, sources = self.semantic_sample()
        plan["review"].update(depth="DEEP", alternatives=[
            {"alternative_id": "another-reading", "candidate": "هل سالم هو بعيد؟"}])
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "DEFER")
        self.assertIn("ALTERNATIVE_UNRESOLVED", codes(report))

    def test_unread_reference_blocks_full_coverage_even_when_another_supports(self):
        plan, sources = self.semantic_sample()
        sources.append(source_like(sources[1], "unparsed", origin="unparsed-C",
                                   content="هذا نص عربي خارج القواعد المركبة حاليًا."))
        report = audit_inquiry(plan, sources)
        self.assertFalse(report["coverage_complete"])
        self.assertNotEqual(report["status"], "LICENSED")
        self.assertIn("SEMANTIC_SOURCE_NOT_ADMITTED", codes(report))

    def test_semantic_fact_budget_exhaustion_is_a_resource_result(self):
        plan, sources = self.semantic_sample()
        sources[1]["content"] = "\n".join(f"«شخص{i}» هو حاضر" for i in range(513))
        plan["claim"]["candidate"] = "هل «شخص0» هو حاضر؟"
        report = audit_inquiry(plan, sources)
        self.assertEqual(report["status"], "RESOURCE_LIMIT")
        self.assertFalse(report["coverage_complete"])
        self.assertEqual(report["authorized_rank"], 0)


class StrictInquiryInputTests(unittest.TestCase):
    def test_path_shaped_identifiers_and_code_shaped_content_are_inert(self):
        plan, sources = sample()
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "must-not-exist"
            program = f"__import__('pathlib').Path({str(marker)!r}).write_text('executed')"
            plan["claim"]["candidate"] = program
            sources[1].update(source_id="../../untrusted-reference", content=program)
            report = audit_inquiry(plan, sources)
            self.assertEqual(report["status"], "LICENSED")
            self.assertFalse(marker.exists())
            self.assertEqual(report["checks"][0]["source_id"], "../../untrusted-reference")

    def test_caller_status_booleans_are_not_installed_fields(self):
        for place, field in (("plan", "box_opened"), ("claim", "world_truth"),
                             ("source", "independent"), ("source", "sha256"),
                             ("review", "complete")):
            with self.subTest(place=place, field=field):
                plan, sources = sample()
                target = {"plan": plan, "claim": plan["claim"],
                          "source": sources[1], "review": plan["review"]}[place]
                target[field] = True
                with self.assertRaises(NabtError):
                    audit_inquiry(plan, sources)

    def test_booleans_are_not_revision_rank_or_budget_numbers(self):
        for field in ("revision", "rank", "budget"):
            with self.subTest(field=field):
                plan, sources = sample()
                kwargs = {}
                if field == "revision":
                    sources[1]["revision"] = True
                elif field == "rank":
                    plan["requested_rank"] = True
                else:
                    kwargs["max_checks"] = True
                with self.assertRaises(NabtError):
                    audit_inquiry(plan, sources, **kwargs)

    def test_inert_json_surrogates_and_nonfinite_numbers_are_rejected(self):
        for value in ("\ud800", float("nan"), float("inf"), object()):
            with self.subTest(kind=type(value).__name__):
                plan, sources = sample()
                sources[1]["content"] = value
                with self.assertRaises(NabtError):
                    audit_inquiry(plan, sources)

    def test_duplicate_live_identity_and_duplicate_parent_are_rejected(self):
        plan, sources = sample()
        with self.assertRaises(NabtError):
            audit_inquiry(plan, sources + [deepcopy(sources[1])])
        sources[1]["parents"] = [{"source_id": "formation", "revision": 1}] * 2
        with self.assertRaises(NabtError):
            audit_inquiry(plan, sources)

    def test_gate_inputs_are_checked_not_coerced(self):
        gate = {"formed": True, "reviewed": True, "provenance": True,
                "scopeCovered": True, "supported": True, "counterevidence": False,
                "requiresWorldBridge": False, "worldBridge": False, "exhausted": False,
                "requestedRank": 2, "evidenceRank": 2}
        for key, value in (("formed", 1), ("requestedRank", True), ("evidenceRank", 4)):
            with self.subTest(key=key):
                changed = dict(gate, **{key: value})
                with self.assertRaises(NabtError):
                    decide_gate(changed)

    def test_world_bridge_and_exhaustion_prevent_either_truth_polarity(self):
        gate = {"formed": True, "reviewed": True, "provenance": True,
                "scopeCovered": True, "supported": True, "counterevidence": True,
                "requiresWorldBridge": True, "worldBridge": False, "exhausted": False,
                "requestedRank": 2, "evidenceRank": 2}
        self.assertEqual(decide_gate(gate), {"verdict": "DEFER", "authorized_rank": 0})
        gate["exhausted"] = True
        self.assertEqual(decide_gate(gate), {"verdict": "RESOURCE_LIMIT", "authorized_rank": 0})


class InquiryCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.plan, self.sources = sample()
        self.plan_path = self.directory / "plan.json"
        self.sources_path = self.directory / "sources.json"
        self.report_path = self.directory / "report.json"
        self.write_inputs()

    def write(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def write_inputs(self):
        self.write(self.plan_path, self.plan)
        self.write(self.sources_path, self.sources)

    def cli(self, *arguments):
        result = subprocess.run([sys.executable, "-m", "nabt", *map(str, arguments)],
                                check=False, capture_output=True, text=True, timeout=15)
        self.assertNotEqual(bool(result.stdout), bool(result.stderr),
                            "CLI must return one JSON result on stdout or stderr")
        return result.returncode, json.loads(result.stdout or result.stderr)

    def test_cli_executes_checks_and_verifies_separate_expected_inputs(self):
        code, report = self.cli("inquire", self.plan_path, "--sources", self.sources_path)
        self.assertEqual((code, report["status"]), (0, "LICENSED"))
        self.write(self.report_path, report)
        code, verified = self.cli("verify-inquiry", self.report_path, "--plan", self.plan_path,
                                  "--sources", self.sources_path)
        self.assertEqual((code, verified["valid"]), (0, True))
        self.sources[1]["content"] += "!"
        self.write_inputs()
        code, rejected = self.cli("verify-inquiry", self.report_path, "--plan", self.plan_path,
                                  "--sources", self.sources_path)
        self.assertEqual((code, rejected["valid"]), (2, False))

    def test_cli_preserves_world_deferral_and_record_refutation_exit_codes(self):
        self.plan["claim"]["kind"] = "WORLD_CORRESPONDENCE"
        self.write_inputs()
        code, world = self.cli("inquire", self.plan_path, "--sources", self.sources_path)
        self.assertEqual((code, world["status"], world["box_opened"]), (3, "DEFER", False))
        self.plan["claim"]["kind"] = "TEXT_CORRESPONDENCE"
        self.sources[1]["content"] += "!"
        self.write_inputs()
        code, negative = self.cli("inquire", self.plan_path, "--sources", self.sources_path)
        self.assertEqual((code, negative["status"]), (2, "REFUTED"))

    def test_cli_rejects_duplicate_json_keys_and_noninteger_budget(self):
        code, result = self.cli("inquire", self.plan_path, "--sources", self.sources_path,
                                "--max-checks", "true")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "REJECT")
        self.plan_path.write_text('{"version":"one","version":"two"}', encoding="utf-8")
        code, result = self.cli("inquire", self.plan_path, "--sources", self.sources_path)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "REJECT")


class ConformanceCheckerTests(unittest.TestCase):
    """Mutation probes for the evidence checker, separate from the gate oracle."""

    def row(self):
        # No formation and no observations cannot authorize any rank.
        return {"law_id": LAW_ID, "mask": 0, "requested_rank": 0,
                "evidence_rank": 0, "verdict": "UNFORMED", "authorized_rank": 0}

    def export_with_first(self, first):
        filler = json.dumps(self.row())
        return "\n".join([first] + [filler] * 8191)

    def test_incomplete_table_is_not_a_success(self):
        from tools.check_rational_inquiry import check_export
        with self.assertRaisesRegex(ValueError, "Expected 8192"):
            check_export(json.dumps(self.row()))

    def test_duplicate_tuple_cannot_replace_a_missing_tuple(self):
        from tools.check_rational_inquiry import check_export
        with self.assertRaisesRegex(ValueError, "duplicate input tuple"):
            check_export(self.export_with_first(json.dumps(self.row())))

    def test_boolean_input_cannot_impersonate_zero(self):
        from tools.check_rational_inquiry import check_export
        row = self.row()
        row["mask"] = False
        with self.assertRaisesRegex(ValueError, "Non-integer mask"):
            check_export(self.export_with_first(json.dumps(row)))

    def test_duplicate_json_key_is_not_silently_overwritten(self):
        from tools.check_rational_inquiry import check_export
        first = json.dumps(self.row()).replace('"mask": 0', '"mask": 1, "mask": 0')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            check_export(self.export_with_first(first))

    def test_forged_export_verdict_is_compared_with_the_runtime_law(self):
        from tools.check_rational_inquiry import check_export
        row = self.row()
        row.update(verdict="LICENSED", authorized_rank=3)
        with self.assertRaisesRegex(ValueError, "decision mismatch"):
            check_export(self.export_with_first(json.dumps(row)))


if __name__ == "__main__":
    unittest.main()
