"""Public NTP replay and source-sensitive contrasts for the integrated lesson."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import unittest

from tests import sim_aql_fixtures as fx
from tools.grammar_catalog import gateway, ntp
from tools.lexical_training import sim_aql_lesson as owner, teaching
from tools.lexical_training.sim_aql import engine

ROOT = Path(__file__).resolve().parents[1]


def example(path):
    return json.loads((ROOT / path).read_text())["payload"]["input"]["lesson"]


def lesson(source, motive=None):
    return {"schema": owner.SCHEMA, "source": source, "motive": asdict(motive or fx.motives()[0])}


def authored(context):
    raw = json.loads(json.dumps(asdict(context)))
    return lesson({"kind": "authored_context", "context": raw})


def inspection(steps=None):
    episode = example("evidence/inspection_discourse_v1/example_request.json")
    if steps is not None:
        episode["steps"] = steps
    return lesson({"kind": "inspection", "as_of": fx.NOW, "lesson": episode})


def knowledge(claim="p"):
    episode = example("examples/io_gateway/ntl_knowledge_assessment.json")
    return lesson({"kind": "knowledge_assessment", "as_of": fx.NOW,
                   "claim": {"id": claim, "version": 1}, "lesson": episode})


def decision(result):
    return result["run"]["evaluation"]["decision"]


class IntegratedLesson(unittest.TestCase):
    def test_installed_dispatch_keeps_the_full_reference_run(self):
        chosen = authored(fx.conditional_context())
        result = teaching.run_lesson(chosen)
        self.assertEqual(result["status"], "SIMULATED")
        self.assertEqual(decision(result)["assumptions"], ["h-p"])
        self.assertEqual(decision(result)["verdict"], "CONDITIONAL_ONLY")
        self.assertEqual(engine.Simulator.replay(result["run"]).audit_digest, result["run"]["audit_digest"])

    def test_all_six_contexts_keep_their_projection_under_four_motives(self):
        base = fx.factual_context()
        contexts = (base, replace(base, evidence=()), fx.conditional_context(), fx.suitability_context(),
                    fx.lexical_context(), replace(base, question=replace(base.question, intent="ISSUE_NORMATIVE")))
        expected = ("ALLOW", "DEFER", "ALLOW", "ALLOW", "ALLOW", "BLOCK")
        for context, status in zip(contexts, expected):
            task = authored(context)
            results = [teaching.run_lesson({**task, "motive": asdict(m)}) for m in fx.motives()]
            self.assertTrue(all(decision(r)["status"] == status for r in results))
            self.assertTrue(all(decision(r) == decision(results[0]) for r in results))
            self.assertEqual(len({r["run"]["audit_digest"] for r in results}), 4)

    def test_subject_state_has_its_own_effect_and_rank_stays_open(self):
        task = authored(fx.suitability_context())
        self.assertEqual(decision(owner.run(task))["status"], "ALLOW")
        task["source"]["context"]["subject_state"]["description"] += " تغيرت"
        d = decision(owner.run(task))
        self.assertIn("EVIDENCE_SUBJECT_STATE_CONTENT_CHANGED", d["reasons"])
        self.assertEqual((d["status"], d["framework_rank"]), ("BLOCK", "NOT_ASSIGNED"))

    def test_lexical_candidate_cannot_answer_an_existence_question(self):
        task = authored(fx.lexical_context())
        self.assertEqual(decision(owner.run(task))["verdict"], "PUBLIC_LEXICAL_LINK_CANDIDATE")
        ctx = task["source"]["context"]
        ctx["question"]["aspect"] = ctx["scopes"][0]["aspect"] = "EXISTENCE"
        d = decision(owner.run(task))
        self.assertEqual((d["status"], d["verdict"]), ("BLOCK", "UNASSESSED"))
        self.assertIn("LEXICAL_BRIDGE_REQUIRES_LINGUISTIC_SCOPE", d["reasons"])

    def test_knowledge_uses_latest_review_for_exact_claim_and_keeps_conflict(self):
        for count, expected, gate in ((0, "UNASSESSED", "DEFER"), (1, "CONFLICTED", "DEFER"),
                                      (2, "REFUTED", "BLOCK"), (7, "UNDETERMINED", "DEFER")):
            task = knowledge()
            episode = task["source"]["lesson"]
            del episode["steps"][count:]
            result = owner.run(task)
            self.assertEqual(result["binding"]["state"], expected)
            self.assertEqual(decision(result)["status"], gate)
            if count == 1:
                self.assertEqual(result["binding"]["assessment"]["content"]["evidence_consistency"], "INCONSISTENT")
        result = owner.run(knowledge("q"))
        self.assertEqual((result["binding"]["state"], decision(result)["status"]), ("SUPPORTED", "ALLOW"))
        self.assertEqual(result["binding"]["assessment"]["content"]["claim"], {"id": "claim/q", "version": 1})

    def test_version_cannot_reuse_old_review_or_peek_at_future_inputs(self):
        task = knowledge("q")
        episode = task["source"]["lesson"]
        revised = deepcopy(episode["claims"][1])
        revised["ref"]["version"] = 2
        revised["threshold"] += 1
        episode["claims"].append(revised)
        task["source"]["claim"]["version"] = 2
        self.assertEqual(owner.run(task)["binding"]["state"], "UNASSESSED")
        task["source"]["as_of"] = "2020-01-01T00:00:00Z"
        self.assertEqual(teaching.run_lesson(task)["status"], "INVALID_INPUT")

    def test_inspection_respects_withdrawal_report_denial_and_opposition(self):
        task = inspection()
        rows = task["source"]["lesson"]["steps"]
        obs = rows[0]
        for steps, state, gate in (([], "MISSING", "DEFER"), ([obs], "SUPPORTED", "ALLOW"),
                    ([{**obs, "polarity": "deny"}], "DENIED", "BLOCK"),
                    ([obs, {**obs, "id": "second", "polarity": "deny"}], "CONFLICT", "DEFER"),
                    (rows, "MISSING", "DEFER")):
            result = owner.run(inspection(steps))
            self.assertEqual((result["binding"]["state"], decision(result)["status"]), (state, gate))
            self.assertEqual(result["upstream_owner"]["answers"]["reported"]["source"], "الحارس")
        self.assertEqual(len(result["upstream_owner"]["answers"]["performed"]), 1)
        self.assertEqual(result["action_authority"], "NONE")

    def test_authored_shape_rejects_coercion_and_injected_status(self):
        for change in (lambda c: c["evidence"][0]["evidence"].update(version=True),
                       lambda c: c["evidence"][0]["evidence"].update(trace="fake"),
                       lambda c: c["evidence"][0].update(role="NABT_OWNER_REPLAY"),
                       lambda c: c.update(status="ALLOW"), lambda c: c.pop("as_of"),
                       lambda c: c["policy"].update(version="uninstalled")):
            task = authored(fx.factual_context())
            change(task["source"]["context"])
            self.assertEqual(teaching.run_lesson(task)["status"], "INVALID_INPUT")
        task = inspection([])
        task["source"]["lesson"]["answers"] = {"inspection": {"status": "SUPPORTED"}}
        self.assertEqual(teaching.run_lesson(task)["status"], "INVALID_INPUT")

    def test_ntp_replays_original_request_and_observes_only_the_source_text(self):
        task = inspection()
        request = ntp.request("cognitive.lesson", {"lesson": task})
        receipt = gateway.run(request)
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])
        result = receipt["execution"]["owner_result"]
        self.assertEqual(result["observation_request_path"], "/payload/input/lesson/source/lesson/text")
        self.assertEqual(decision(result["owner_result"])["status"], "DEFER")
        changed = deepcopy(request)
        changed["payload"]["input"]["lesson"]["motive"]["description"] += " تغير"
        self.assertFalse(gateway.accept_output(receipt, expected_request=changed)["valid"])
        decision(result["owner_result"])["status"] = "ALLOW"
        self.assertFalse(gateway.accept_output(receipt, expected_request=request)["valid"])
