"""Lesson boundaries and source-only end-to-end oracles, not model accuracy."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import reasoning_curriculum as c, teaching as t

ROOT = Path(__file__).resolve().parents[1]
NATIVES = ("verifiedReading", "classicalSemanticProbe", "evidenceLifecycleV1", "epistemicMeasurement")
READY = all((ROOT / "formal/.lake/build/bin" / n).is_file() for n in NATIVES)
if os.environ.get("NABT_REQUIRE_COGNITIVE_NATIVE") == "1" and not READY:
    raise RuntimeError("Cognitive teaching gate requires all four installed native owners")


def lesson():
    sources = [
        {"id": "positive", "text": "بشر هو قارئ. بشر هو متعلم.", "parents": []},
        {"id": "counter", "text": "ليس صخر هو قارئ. ليس صخر هو متعلم.", "parents": []},
        {"id": "rule_a", "text": "كل قارئ هو متعلم.", "parents": []},
        {"id": "rule_b", "text": "إذا كان ?ش هو قارئ فإن ?ش هو متعلم.", "parents": []},
        {"id": "case", "text": "هدى هو قارئ.", "parents": []}]
    return {"schema": t.SCHEMA, "lesson_id": "new-person", "domain_id": "communication",
            "matrix_id": "generality", "adapter": "source_learning", "payload": {
                "schema": t.source_learning_connection.REQUEST_SCHEMA, "scope": "lesson",
                "sources": sources, "query": "هل هدى هو متعلم؟",
                "initial_active": ["positive", "rule_a", "rule_b", "case"],
                "events": [{"id": "observe-counter", "kind": "activate", "target": "counter"},
                           {"id": "lose-one", "kind": "withdraw", "target": "rule_a"},
                           {"id": "lose-shared", "kind": "withdraw", "target": "case"},
                           {"id": "restore", "kind": "activate", "target": "case"}]}}


def qualified():
    def atom(name, positive=True):
        return {"predicate": name, "arguments": ["ليلى"], "positive": positive}
    return {"schema": t.SCHEMA, "lesson_id": "explicit-guard", "domain_id": "usul",
            "matrix_id": "condition", "adapter": "qualified_inference", "payload": {
                "source_text": "ليلى هو سبب.\nليلى هو شرط.\nليس ليلى هو مانع.\n"
                    "إذا ليلى هو سبب و ليلى هو شرط و ليس ليلى هو مانع فإن ليلى هو نتيجة.\n",
                "query_text": "هل ليلى هو نتيجة؟\n", "source_id": "authored_guard", "revision": "1",
                "scope": "conditional", "context": "authored", "time": "unspecified",
                "plan": {"schema": t.source_bound.PLAN_SCHEMA, "policy_id": "guarded_cause",
                         "requirements": [{"slot": "cause", "atom": atom("سبب")},
                                          {"slot": "condition", "atom": atom("شرط")},
                                          {"slot": "blockerAbsence", "atom": atom("مانع", False)}],
                         "bridge_clause": "c3"}}}


class CurriculumTests(unittest.TestCase):
    def test_distinct_axes_and_source_attribution(self):
        result = c.matrix()
        self.assertEqual(result["matrix_count"], 19)
        self.assertEqual(len(result["domains"]), 8)
        rows = {r["id"]: r for r in result["matrices"]}
        self.assertIn("Selected passages only", result["source_review"]["scope"])
        self.assertEqual(rows["unrestricted"]["runtime_adapters"], [])
        self.assertEqual(c.POLICY_MATRICES["agreement"], {"mafhum", "fahwa"})
        self.assertNotEqual(c.POLICY_MATRICES["agreement"], c.POLICY_MATRICES["opposition"])
        self.assertFalse(any(r["learning_complete"] for r in rows.values()))
        files = {r["library_file_id"] for r in result["source_review"]["passages"]}
        self.assertEqual(len(files), 4)
        self.assertEqual(result["routing_policy_id"], "nabt.cognitive-evidence-routing.v2")
        self.assertEqual(result["domain_role"], "CURRICULUM_CONTEXT_NOT_EVIDENCE_AUTHORITY")
        self.assertTrue(all(set(r["runtime_adapters"]) == t.ADAPTERS for r in result["domains"]))
        foundation = result["shared_foundation"]
        self.assertFalse(foundation["facts_or_axioms_created"])
        self.assertEqual({r["id"] for r in foundation["rows"]},
                         {"existence", "designation", "kind_nature", "property", "spatial_relation",
                          "temporal_relation", "change", "causal_relation"})

    def test_targets_and_checker_commands_cannot_be_injected(self):
        for key in ("answer", "label", "features", "checker", "expected", "expertise_certified"):
            request = lesson(); request[key] = True
            with patch.object(t.source_learning_connection, "evaluate") as run:
                self.assertEqual(t.run_lesson(request)["status"], "INVALID_INPUT")
                run.assert_not_called()
        request = lesson(); request["payload"]["label"] = True
        self.assertEqual(t.run_lesson(request)["status"], "INVALID_INPUT")

    def test_cause_cannot_be_relabelled_illah_or_fahwa(self):
        for identity in ("illah", "origin", "fahwa", "lahn"):
            request = qualified(); request["matrix_id"] = identity
            with patch.object(t.source_bound, "evaluate_source") as run:
                self.assertEqual(t.run_lesson(request)["status"], "INVALID_INPUT")
                run.assert_not_called()

    def test_unimplemented_matrix_is_defer_not_a_successful_empty_run(self):
        request = lesson(); request["matrix_id"] = "restricted"
        with patch.object(t.source_learning_connection, "evaluate") as run:
            result = t.run_lesson(request)
            self.assertEqual(result["status"], "DEFER")
            self.assertFalse(result["execution_measured"])
            self.assertIsNone(result["owner_result"])
            run.assert_not_called()

    def test_invalid_identifiers_and_duplicate_json_keys(self):
        for key in ("matrix_id", "domain_id", "adapter"):
            for value in (True, [], "missing"):
                request = lesson(); request[key] = value
                self.assertEqual(t.run_lesson(request)["status"], "INVALID_INPUT")
        with self.assertRaises(ValueError):
            t.wire_owner.strict_loads('{"schema":"a","schema":"b"}')

    def test_cli_preserves_transport_exhaustion_and_malformed_input(self):
        cases = [(b'"' + b'a' * t.wire_owner.MAX_REQUEST_BYTES + b'"', "RESOURCE_LIMIT"),
                 (b'[' * 33 + b'null' + b']' * 33, "RESOURCE_LIMIT"),
                 (b'{', "INVALID_INPUT")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            for raw, status in cases:
                with self.subTest(status=status, size=len(raw)):
                    path.write_bytes(raw)
                    run = subprocess.run([sys.executable, "-m", "tools.lexical_training.teaching",
                                          "--request", str(path)], cwd=ROOT,
                                         capture_output=True, text=True, check=False, timeout=30)
                    self.assertEqual(run.returncode, 3, run.stderr)
                    result = json.loads(run.stdout)
                    self.assertEqual(result["status"], status)
                    self.assertFalse(result["execution_measured"])


@unittest.skipUnless(READY, "build cognitive lesson native owners")
class NativeLessonTests(unittest.TestCase):
    def test_prior_evidence_is_reusable_across_domains_without_promoting_authority(self):
        request = json.loads((ROOT / "examples/cognitive_teaching/world_prior.json").read_text())
        first = None
        for identity, *_ in c.DOMAINS:
            with self.subTest(domain=identity):
                request["domain_id"] = identity
                result = t.run_lesson(request)
                self.assertEqual(result["status"], "SUPPORTED", result)
                self.assertTrue(result["execution_measured"])
                self.assertTrue(result["owner_result"]["conditional_consequence"])
                self.assertFalse(result["limits"]["world_truth_established"])
                self.assertFalse(result["limits"]["empirical_causality_established"])
                self.assertFalse(result["limits"]["domain_label_grants_authority"])
                if first is None:
                    first = result["owner_result"]
                else:
                    self.assertEqual(result["owner_result"], first)

    def test_world_priors_require_their_witness_and_causal_bridge(self):
        request = json.loads((ROOT / "examples/cognitive_teaching/world_prior.json").read_text())
        missing = deepcopy(request)
        missing["payload"]["source_text"] = missing["payload"]["source_text"].replace("عينة هو موجودة.\n", "")
        missing["payload"]["plan"]["bridge_clause"] = "c6"
        result = t.run_lesson(missing)
        self.assertEqual(result["status"], "UNKNOWN", result)
        self.assertFalse(result["owner_result"]["conditional_consequence"])
        # Every described property, including adjacency/order, remains present.
        # With no attested transfer rule the role labels cannot supply a bridge.
        request["payload"]["source_text"] = '\n'.join(request["payload"]["source_text"].splitlines()[:-1]) + '\n'
        request["payload"]["plan"]["bridge_clause"] = None
        result = t.run_lesson(request)
        self.assertEqual(result["status"], "UNKNOWN", result["owner_result"]["reason"])
        self.assertFalse(result["owner_result"]["conditional_consequence"])
        self.assertEqual(result["next_step"]["action"], "ACQUIRE_SOURCE_BOUND_RELATION")
        self.assertEqual(result["owner_result"]["conditional_result"]["readings"][0]["reason"], "BRIDGE_MISSING")
        text = request["payload"]["source_text"]
        for changed_text, status in ((text + "ليس عينة هو قابلة.\n", "CONFLICT"),
                                     (text.replace("عينة هو قابلة.\n", "ليس عينة هو قابلة.\n"), "REFUTED"),
                                     (text.replace("عينة هو قابلة.\n", ""), "UNKNOWN"),
                                     (text + "ليس عينة هو متمددة.\n", "UNKNOWN")):
            with self.subTest(source=changed_text, status=status):
                changed = deepcopy(request)
                changed["payload"]["source_text"] = changed_text
                blocked = t.run_lesson(changed)
                self.assertEqual(blocked["status"], status)
                self.assertFalse(blocked["owner_result"]["conditional_consequence"])
                self.assertEqual(blocked["next_step"]["action"], "ASSESS_CONTRAST_AND_WITHDRAWAL")

    def test_empirical_domain_retains_acquired_learning_and_withdrawal(self):
        request = lesson(); request["domain_id"] = "empirical_science"
        result = t.run_lesson(request)
        self.assertTrue(result["execution_measured"], result)
        self.assertEqual([s["status"] for s in result["measurements"]["steps"]],
                         ["SUPPORTED", "SUPPORTED", "SUPPORTED", "UNKNOWN", "SUPPORTED"])

    def test_observation_identity_time_place_and_kind_are_not_domain_labels(self):
        rows = json.loads((ROOT / "evidence/epistemic_measurement_v1/reference.json").read_text())["cases"]
        case = next(r for r in rows if r["expected"]["status"] == "SUPPORTED"
                    and r["input"]["query"]["key"]["axis"] == "recorded_observation")
        request = {"schema": t.SCHEMA, "lesson_id": "qualified-observation", "domain_id": "usul",
                   "matrix_id": "cognitive_concept", "adapter": "epistemic_ledger",
                   "payload": {"source_profile": case["source_profile"], "input": case["input"]}}
        supported = t.run_lesson(request)
        self.assertEqual(supported["status"], "SUPPORTED", supported)
        for field, value in (("entity", "other:entity"), ("time", "99999"), ("place", "other:place")):
            changed = deepcopy(request)
            changed["payload"]["input"]["query"]["key"][field] = value
            result = t.run_lesson(changed)
            self.assertEqual(result["status"], "UNKNOWN", result)
        changed = deepcopy(request)
        for evidence in changed["payload"]["input"]["interpretations"]:
            evidence["kind"] = "lexical"
        self.assertEqual(t.run_lesson(changed)["status"], "UNKNOWN")

    def test_new_occurrence_counterexample_and_independent_support(self):
        result = t.run_lesson(lesson())
        self.assertTrue(result["execution_measured"], result.get("error"))
        steps = result["measurements"]["steps"]
        self.assertEqual([s["status"] for s in steps], ["SUPPORTED", "SUPPORTED", "SUPPORTED", "UNKNOWN", "SUPPORTED"])
        self.assertEqual([s["surviving_candidates"] for s in steps[:2]], [2, 1])
        self.assertEqual([s["support_count"] for s in steps], [2, 2, 1, 0, 1])
        self.assertTrue(steps[-1]["application_established"])
        learner = result["owner_result"]["history"][-1]["learning"]
        self.assertNotIn("هدى", {o["entity"] for o in learner["observations"]})
        self.assertEqual(result["next_step"]["action"], "ASSESS_INDEPENDENT_NEW_OCCURRENCE")
        self.assertFalse(result["limits"]["matrix_complete"])

    def test_consensus_does_not_authorize_generalization(self):
        request = lesson(); request["payload"]["events"] = []
        request["payload"]["initial_active"] = ["positive", "counter", "case"]
        result = t.run_lesson(request)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertTrue(result["execution_measured"])
        self.assertEqual(result["next_step"]["action"], "ACQUIRE_ADOPTION_AND_CASE_WITNESSES")
        self.assertFalse(result["measurements"]["steps"][0]["application_established"])

    def test_replay_binds_explanation_inputs_and_domain(self):
        request = lesson(); result = t.run_lesson(request)
        self.assertTrue(t.verify_lesson(result, expected_lesson=request)["valid"])
        forged = deepcopy(result); forged["next_step"]["action"] = "EXPERT"
        self.assertFalse(t.verify_lesson(forged, expected_lesson=request)["valid"])
        changed = deepcopy(request); changed["domain_id"] = "mathematics"
        self.assertFalse(t.verify_lesson(result, expected_lesson=changed)["valid"])

    def test_exhausted_hypothesis_language_does_not_request_rule_adoption(self):
        request = lesson()
        request["payload"].update(sources=[
            {"id": "a", "parents": [], "text": "بشر هو قارئ. ليس بشر هو كاتب. بشر هو متعلم."},
            {"id": "b", "parents": [], "text": "ليس سالم هو قارئ. سالم هو كاتب. سالم هو متعلم."},
            {"id": "c", "parents": [], "text": "نادر هو قارئ. نادر هو كاتب. ليس نادر هو متعلم."},
            {"id": "case", "parents": [], "text": "هدى هو قارئ. ليس هدى هو كاتب."}],
            initial_active=["a", "b", "c", "case"], events=[])
        result = t.run_lesson(request)
        self.assertTrue(result["execution_measured"], result)
        self.assertEqual(result["measurements"]["steps"][0]["surviving_candidates"], 0)
        self.assertEqual(result["next_step"]["action"], "REVIEW_DECLARED_HYPOTHESIS_LANGUAGE")

    def test_blocker_absence_requires_evidence(self):
        request = qualified(); result = t.run_lesson(request)
        self.assertEqual(result["status"], "SUPPORTED", result)
        self.assertTrue(result["execution_measured"])
        self.assertFalse(result["measurements"]["learner_trained"])
        request["payload"]["source_text"] = request["payload"]["source_text"].replace("ليس ليلى هو مانع.\n", "")
        request["payload"]["plan"]["bridge_clause"] = "c2"
        missing = t.run_lesson(request)
        self.assertEqual(missing["status"], "UNKNOWN", missing)
        self.assertFalse(missing["measurements"]["conditional_consequence"])

    def test_hidden_motive_is_not_established_from_authored_report(self):
        rows = json.loads((ROOT / "evidence/epistemic_measurement_v1/reference.json").read_text())["cases"]
        case = next(r for r in rows if r["input"]["query"]["key"]["axis"] == "hidden_motive")
        request = {"schema": t.SCHEMA, "lesson_id": "hidden-is-not-reported", "domain_id": "personal_relations",
                   "matrix_id": "cognitive_concept", "adapter": "epistemic_ledger",
                   "payload": {"source_profile": case["source_profile"], "input": case["input"]}}
        result = t.run_lesson(request)
        self.assertTrue(result["execution_measured"], result)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["owner_result"]["hidden_motive_established"])

    def test_checked_resource_exhaustion_is_not_a_completed_lesson(self):
        request = json.loads((ROOT / "examples/cognitive_teaching/epistemic.json").read_text())
        request["payload"]["input"]["budget"] = 0
        result = t.run_lesson(request)
        self.assertEqual(result["status"], "RESOURCE_LIMIT")
        self.assertTrue(result["owner_result"]["native_checked"])
        self.assertTrue(result["owner_result"]["certificate_checked"])
        self.assertFalse(result["execution_measured"])
        self.assertEqual(result["next_step"]["action"], "RESOLVE_OWNER_OBLIGATION")
        replay = t.verify_lesson(result, expected_lesson=request)
        self.assertTrue(replay["replay_matches"])
        self.assertFalse(replay["valid"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            path.write_text(json.dumps(request))
            run = subprocess.run([sys.executable, "-m", "tools.lexical_training.teaching",
                                  "--request", str(path)], cwd=ROOT,
                                 capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(run.returncode, 3, run.stderr)
            self.assertEqual(json.loads(run.stdout)["status"], "RESOURCE_LIMIT")

    def test_missing_native_and_free_text_cannot_pass_a_lesson(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(t.source_learning_connection.life,
                "NATIVE", Path(directory) / "missing"):
            result = t.run_lesson(lesson())
            self.assertFalse(result["execution_measured"])
        request = lesson(); request["payload"]["sources"][0]["text"] = "نص جديد لم يحلل بعد."
        result = t.run_lesson(request)
        self.assertEqual(result["status"], "DEFER")
        self.assertEqual(result["next_step"]["action"], "RESOLVE_OWNER_OBLIGATION")


if __name__ == "__main__":
    unittest.main()
