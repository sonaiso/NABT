"""School contracts, independent numerical keys, revisions and gateway replay."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway
from tools.lexical_training import apprentice_readout, ntl_core, school_apprentice as school
from tools.lexical_training import school_curriculum as curriculum, teaching

ROOT = Path(__file__).resolve().parents[1]


def context(programme="MYP", role="student"):
    return {"role": role, "programme": programme,
            "profile_id": {"PYP": "ib.pyp.2026", "MYP": "ib.myp.2026", "CP": "ib.cp.2027"}[programme],
            "assessment_session": "2027-05" if programme == "CP" else None,
            "programme_year": 1 if programme == "CP" else 3, "national_grade": 8,
            "national_subject": "science", "subject_group": "sciences",
            "outcome_ids": ["jordan.general.inquiry_problem_solving"],
            "tok_lens": {"aok": "natural_sciences", "focus": "methods_and_tools"}}


def measurement():
    return {"readings": [
        {"object": "قضيب", "day": 1, "unit": "cm", "value": 3, "error": 0},
        {"object": "قضيب", "day": 2, "unit": "mm", "value": 40, "error": 0}]}


def problem(unit="measurement", task=None):
    return {"case_id": "local-example-1", "revision": 0, "unit": unit,
            "text": "ما حدود الحكم بزيادة الطول من القراءتين ودقة القياس؟",
            "task": measurement() if task is None else task, "response": None}


def request(**changes):
    return {"schema": school.SCHEMA, "action": "inquire", "context": context(),
            "problem": problem(), **changes}


def proposal(action="compare_measurements"):
    # Deliberately overconfident: this may propose, never supply an owner premise.
    return {"schema": apprentice_readout.SCHEMA, "status": "PROPOSED", "authority": "NONE",
            "action": action, "action_ranking": [{"label": action, "score": 1.0}],
            "obligations": dict.fromkeys(apprentice_readout.OBLIGATIONS, False)}


class SchoolInputAndEvidence(unittest.TestCase):
    def setUp(self):
        self.neural = patch.object(apprentice_readout, "propose", return_value=proposal())
        self.neural.start()
        self.addCleanup(self.neural.stop)

    def test_independent_units_precision_and_identity_keys(self):
        cases = [({}, "INCREASE"), ({"unit": "mm", "value": 30}, "SAME"),
                 ({"value": 29}, "DECREASE"), ({"value": 30, "error": 1}, "UNRESOLVED_PRECISION"),
                 ({"object": "لوح"}, "UNALIGNED"), ({"day": 1}, "UNALIGNED")]
        for changes, key in cases:
            task = measurement()
            task["readings"][1].update(changes)
            with self.subTest(changes=changes):
                result = school.run(request(problem=problem(task=task)))
                self.assertEqual(result["explanation"]["claim"], key)
                self.assertEqual(result["owner_result"], ntl_core.measurement(task))
                self.assertFalse(result["explanation"]["world_truth_established"])

    def test_missing_identity_is_not_a_negative_or_confident_proposal(self):
        p = problem()
        p["task"]["readings"][1]["object"] = None
        with patch.object(ntl_core, "measurement") as owner:
            result = school.run(request(problem=p))
        owner.assert_not_called()
        self.assertEqual(result["status"], "DEFER")
        self.assertEqual(result["verified_obligations"]["missing"], ["identity"])
        self.assertEqual(result["pedagogical_action"]["selected"], "request_evidence")
        self.assertFalse(result["pedagogical_action"]["proposal_admitted"])
        self.assertIsNone(result["explanation"]["claim"])

    def test_missing_zero_and_unavailable_are_distinct(self):
        for value, expected in ((None, "DEFER"), (0, "CHECKED_CONDITIONAL")):
            p = problem()
            p["task"]["readings"][0]["value"] = value
            r = school.run(request(problem=p))
            self.assertEqual(r["status"], expected)
        for rows in ([], measurement()["readings"][:1]):
            r = school.run(request(problem=problem(task={"readings": rows})))
            self.assertEqual(r["status"], "DEFER")
            self.assertIsNone(r["owner_result"])

    def test_types_authority_injection_and_resources_rejected_before_owner(self):
        invalid = []
        for value in (True, 1.2, float("nan"), float("inf"), -1, 1000000):
            p = problem()
            p["task"]["readings"][0]["value"] = value
            invalid.append(request(problem=p))
        invalid.extend((request(model_path="/tmp/model"), request(approved=True),
                        request(problem=dict(problem(), unit="uninstalled_medical_inference")),
                        request(problem=dict(problem(), text="x" * 3000))))
        for value in invalid:
            with self.subTest(value=str(value)[:100]), patch.object(ntl_core, "measurement") as owner:
                result = teaching.run_lesson(value)
                self.assertIn(result["status"], ("INVALID_INPUT", "RESOURCE_LIMIT"))
                owner.assert_not_called()

    def test_complete_task_executes_original_owner_once(self):
        with patch.object(ntl_core, "measurement", wraps=ntl_core.measurement) as owner:
            result = school.run(request())
        self.assertEqual(owner.call_count, 1)
        self.assertEqual(result["explanation"]["claim"], "INCREASE")
        self.assertTrue(result["pedagogical_action"]["proposal_compatible"])
        self.assertFalse(result["pedagogical_action"]["proposal_admitted"])
        self.assertEqual(result["pedagogical_action"]["neural_release_policy"], "REVIEW_ONLY")

    def test_model_cannot_enable_automatic_selection_even_when_compatible(self):
        proposed = dict(proposal("independent_transfer"), automatic_selection_permitted=True, release_policy="ACTIVE")
        with patch.object(apprentice_readout, "propose", return_value=proposed):
            result = school.run(request())
        self.assertTrue(result["pedagogical_action"]["proposal_compatible"])
        self.assertEqual(result["pedagogical_action"]["selected"], "compare_measurements")
        self.assertFalse(result["pedagogical_action"]["proposal_admitted"])

    def test_unavailable_neural_observation_does_not_suppress_owner(self):
        with patch.object(apprentice_readout, "propose", return_value={"status": "MODEL_UNAVAILABLE", "action": None}):
            result = school.run(request())
        self.assertEqual(result["explanation"]["claim"], "INCREASE")
        self.assertFalse(result["pedagogical_action"]["proposal_admitted"])

    def test_exact_randomization_is_conditional_and_design_is_preserved(self):
        task = {"assignment": "fair_independent_within_pair", "intervention": "A", "control": "B",
                "endpoint": "prespecified endpoint", "outcome_unit": "points", "pairs": [
                    {"ids": ["a" + str(i), "b" + str(i)], "treated": 0, "values": [12, 10]} for i in range(6)]}
        result = school.run(request(problem=problem("experiment", task)))
        self.assertEqual(result["explanation"]["claim"], "REJECT_SHARP_NULL")
        self.assertEqual(result["owner_result"]["trace"]["exact_p"], "1/32")
        self.assertEqual(result["pedagogical_action"]["selected"], "inspect_causal_design")
        task["assignment"] = "observer_selected"
        r = school.run(request(problem=problem("experiment", task)))
        self.assertEqual(r["explanation"]["claim"], "DESIGN_INSUFFICIENT")
        task["pairs"][0]["values"][1] = None
        with patch.object(ntl_core, "paired_trial") as owner:
            r = school.run(request(problem=problem("experiment", task)))
        owner.assert_not_called()
        self.assertEqual(r["status"], "DEFER")

    def test_source_task_uses_original_owner_with_complete_raw_text(self):
        task = {"text": "كلُّ باحثٍ مدققٌ. أنس هو باحث.", "query": "هل أنس هو مدقق؟"}
        result = school.run(request(problem=problem("passage", task)))
        self.assertEqual(result["problem"]["task"], task)
        self.assertEqual(result["owner_result"], ntl_core.passage(task))
        self.assertFalse(result["verified_obligations"]["source_truth_verified"])

    def test_open_reflection_never_turns_a_perspective_into_verified_truth(self):
        task = {"question": "هل نغيّر سياسة استعمال الماء؟", "sources": [
            {"id": "s1", "text": "وردت ملاحظة محلية تحتاج مراجعة.", "citation": "authored classroom example"}],
            "perspectives": ["الطالب", "مسؤول المرافق"]}
        r = school.run(request(problem=problem("reflection", task)))
        self.assertEqual(r["status"], "OPEN_REFLECTION")
        self.assertIsNone(r["owner_result"])
        self.assertIsNone(r["explanation"]["claim"])
        self.assertIn("argument_quality", r["explanation"]["open_obligations"])
        task["perspectives"] = ["الطالب", "الطالب"]
        self.assertEqual(teaching.run_lesson(request(problem=problem("reflection", task)))["status"], "INVALID_INPUT")


class CurriculumAndFormative(unittest.TestCase):
    def test_all_roles_and_programmes_are_presentation_only(self):
        with patch.object(apprentice_readout, "propose", return_value=proposal()):
            for programme in curriculum.PROGRAMMES:
                for role in curriculum.ROLES:
                    r = school.run(request(context=context(programme, role)))
                    self.assertEqual(r["role_view"]["permissions_granted"], [])
                    self.assertFalse(r["role_view"]["school_records_updated"])
                    self.assertFalse(r["curriculum_alignment"]["tok"]["official_tok_requirement"])

    def test_unknown_and_grade_mismatched_outcomes_are_visible_gaps(self):
        c = context()
        c["outcome_ids"] = ["not-installed-grade-outcome", "jordan.science.g8.water_human_impact"]
        c["national_grade"] = 7
        result = curriculum.align(c)
        self.assertEqual(result["status"], "REFERENCE_GAPS")
        self.assertEqual(result["missing_outcome_ids"], ["not-installed-grade-outcome"])
        self.assertEqual(result["incompatible_outcome_ids"], ["jordan.science.g8.water_human_impact"])
        self.assertFalse(result["alignment_approved"])

    def test_national_and_ib_profiles_are_independent_and_subject_bound(self):
        c = context()
        c["outcome_ids"] = ["jordan.science.g8.water_human_impact", "ib.myp.evidence.evaluate"]
        result = curriculum.align(c)
        self.assertEqual(result["status"], "LOCAL_ALIGNMENT_CANDIDATE")
        self.assertEqual(len(result["selected_outcomes"]), 2)
        self.assertTrue(result["national_source_profiles"])
        c["national_subject"] = "mathematics"
        c["subject_group"] = "mathematics"
        result = curriculum.align(c)
        self.assertEqual(set(result["incompatible_outcome_ids"]), set(c["outcome_ids"]))
        self.assertEqual(result["selected_outcomes"], [])

    def test_programme_year_and_cohort_are_explicit(self):
        for changes in ({"programme_year": None}, {"programme_year": True}, {"programme_year": 6},
                        {"profile_id": "ib.cp.2027"}, {"national_grade": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                curriculum.validate_context(dict(context(), **changes))
        c = context("CP")
        for changes in ({"assessment_session": None}, {"assessment_session": "2026-11"},
                        {"assessment_session": "2027-01"}, {"assessment_session": "2027-11"},
                        {"profile_id": "ib.cp.2026"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                curriculum.validate_context(dict(c, **changes))
        old = dict(c, profile_id="ib.cp.2026", assessment_session="2026-11")
        self.assertEqual(curriculum.validate_context(old), old)

    def test_source_registry_is_not_a_grade_or_bok_component(self):
        r = school.run({"schema": school.SCHEMA, "action": "catalog"})
        self.assertFalse(r["catalog"]["body_of_knowledge"]["official_ib_component"])
        self.assertFalse(r["catalog"]["all_subject_outcomes_loaded"])
        self.assertFalse(r["catalog"]["official_grade_authority"])
        tok = r["catalog"]["epistemic_frameworks"][0]
        self.assertEqual((len(tok["axes"]), len(tok["areas_of_knowledge"]), len(tok["concepts"])), (4, 5, 12))
        self.assertTrue(tok["source_ids"])
        self.assertFalse(tok["required_for_other_programmes"])

    def test_surface_response_features_are_not_claimed_as_semantic_mastery(self):
        p = problem()
        p["response"] = {"origin": "simulation", "decision": "INCREASE", "evidence_refs": ["R1", "R2"],
                         "explanation": "unrelated words", "counterexample": "", "reflection": "", "transfer": ""}
        with patch.object(apprentice_readout, "propose", return_value=proposal()):
            r = school.run(request(problem=p))
        assessment = r["formative_assessment"]
        self.assertTrue(assessment["observations"]["decision_matches_owner"])
        self.assertTrue(assessment["observations"]["references_match_owner"])
        self.assertTrue(assessment["observations"]["has_explanation"])
        self.assertEqual(assessment["semantic_quality_of_explanation"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(assessment["human_learning_measured"])
        self.assertIsNone(assessment["official_grade"])
        self.assertFalse(r["verified_obligations"]["interpretive_understanding_measured"])

    def test_observed_answer_error_requires_evidence_review_before_transfer(self):
        p = problem()
        p["response"] = {"origin": "human_reported", "decision": "DECREASE", "evidence_refs": ["R1"],
                         "explanation": "", "counterexample": "", "reflection": "", "transfer": ""}
        with patch.object(apprentice_readout, "propose", return_value=proposal("independent_transfer")):
            r = school.run(request(problem=p))
        self.assertEqual(r["formative_assessment"]["observations"]["missing_expected_refs"], ["R2"])
        self.assertFalse(r["formative_assessment"]["observations"]["decision_matches_owner"])
        self.assertNotIn("independent_transfer", r["pedagogical_action"]["eligible"])
        self.assertEqual(r["pedagogical_action"]["selected"], "request_evidence")


class EvidenceRevisionAndLearning(unittest.TestCase):
    def test_withdraw_and_restore_replays_original_evidence(self):
        before = problem()
        withdrawn = deepcopy(before)
        withdrawn["revision"] = 1
        withdrawn["task"]["readings"].pop()
        with patch.object(apprentice_readout, "propose", return_value=proposal()):
            r = school.run(request(action="revise", previous=before, problem=withdrawn))
            restored = deepcopy(before)
            restored["revision"] = 2
            s = school.run(request(action="revise", previous=withdrawn, problem=restored))
        self.assertEqual(r["status"], "DEFER")
        self.assertIsNone(r["explanation"]["claim"])
        self.assertEqual(r["revision_comparison"]["previous_replayed"]["explanation"]["claim"], "INCREASE")
        self.assertTrue(r["revision_comparison"]["judgment_changed"])
        self.assertFalse(r["revision_comparison"]["prior_judgment_carried_forward"])
        self.assertEqual(s["explanation"]["claim"], "INCREASE")

    def test_mismatched_revision_and_injected_old_receipt_are_rejected_before_execution(self):
        previous = problem()
        after = deepcopy(previous)
        after["case_id"] = "different"
        after["revision"] = 1
        with patch.object(ntl_core, "measurement") as owner:
            self.assertEqual(teaching.run_lesson(request(action="revise", previous=previous, problem=after))["status"], "INVALID_INPUT")
            previous["owner_result"] = {"answer": "INCREASE"}
            self.assertEqual(teaching.run_lesson(request(action="revise", previous=previous))["status"], "INVALID_INPUT")
        owner.assert_not_called()

    def test_existing_guard_induction_and_missing_probe_are_preserved(self):
        old = json.loads((ROOT / "examples/io_gateway/ntl_minimum_induction.json").read_text())["payload"]["lesson"]
        req = {"schema": school.SCHEMA, "action": "induce", "context": context(),
               "examples": old["examples"], "probes": old["probes"]}
        r = school.run(req)
        self.assertEqual(r["owner_result"], ntl_core.learn_measurement(old))
        self.assertEqual(r["metacognition"]["hypothesis_count"], [28, 8, 4, 2, 1])
        self.assertEqual(r["metacognition"]["version_space_bits"][-1], 0.0)
        self.assertEqual(r["owner_result"]["probes"][-1]["status"], "MISSING_READING")
        self.assertEqual(r["owner_result"]["probes"][-1]["possible"], [])
        withdrawn = school.run(dict(req, examples=old["examples"][:-1]))
        self.assertEqual(withdrawn["metacognition"]["hypothesis_count"][-1], 2)
        self.assertFalse(r["metacognition"]["neural_weights_changed"])

    def test_internal_lesson_replay_accepts_output_floats_without_loosening_inputs(self):
        old = json.loads((ROOT / "examples/io_gateway/ntl_minimum_induction.json").read_text())["payload"]["lesson"]
        req = {"schema": school.SCHEMA, "action": "induce", "context": context(),
               "examples": old["examples"], "probes": old["probes"]}
        result = teaching.run_lesson(req)
        self.assertTrue(teaching.verify_lesson(result, expected_lesson=req)["valid"])
        result["metacognition"]["version_space_bits"][0] += 0.1
        self.assertFalse(teaching.verify_lesson(result, expected_lesson=req)["valid"])
        with patch.object(apprentice_readout, "propose", return_value=proposal()):
            result = teaching.run_lesson(request())
            self.assertTrue(teaching.verify_lesson(result, expected_lesson=request())["valid"])


class SchoolGateway(unittest.TestCase):
    def test_verified_external_receipt_and_tamper_rejection(self):
        req = {"schema": gateway.REQUEST_SCHEMA, "route": "cognitive.lesson", "payload": {"lesson": request()}}
        receipt = gateway.run(req)
        self.assertEqual(receipt["status"], "EXECUTED")
        owner = receipt["execution"]["owner_result"]
        self.assertEqual(owner["explanation"]["claim"], "INCREASE")
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        self.assertFalse(gateway.accept_output(owner, expected_request=req)["valid"])
        changed_request = deepcopy(req)
        changed_request["payload"]["lesson"]["problem"]["task"]["readings"][1]["value"] = 20
        self.assertFalse(gateway.accept_output(receipt, expected_request=changed_request)["valid"])
        tampered = deepcopy(receipt)
        tampered["execution"]["owner_result"]["explanation"]["claim"] = "DECREASE"
        self.assertFalse(gateway.accept_output(tampered, expected_request=req)["valid"])


if __name__ == "__main__":
    unittest.main()
