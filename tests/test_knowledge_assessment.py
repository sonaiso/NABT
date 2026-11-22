"""Conformance of the supplied interval/implication lesson through the NTP boundary."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.grammar_catalog import gateway
from tools.lexical_training import knowledge_lesson, ntl_core, teaching
from tools.lexical_training.knowledge_records import Packed, canonical, unfold

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/io_gateway/ntl_knowledge_assessment.json"


def example():
    return json.loads(EXAMPLE.read_text())["payload"]["input"]["lesson"]


def records_at_steps(result):
    records = {(r["ref"]["id"], r["ref"]["version"]): r for r in result["records"]}
    return [records[(ref["id"], ref["version"])] for ref in result["history"]]


def assess_one(lesson, ids):
    assessment = lesson["steps"][0]
    assessment["evidence"] = ids
    lesson["steps"] = [assessment]
    return records_at_steps(knowledge_lesson.run(lesson))[0]


class KnowledgeAssessment(unittest.TestCase):
    def test_public_episode_and_replay(self):
        req = json.loads(EXAMPLE.read_text())
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        envelope = receipt["execution"]["owner_result"]
        self.assertEqual(envelope["observation_coverage"], "NO_REQUEST_TEXT_SOURCE")
        owner = envelope["owner_result"]
        self.assertEqual(owner["status"], "ASSESSED_EPISODE")
        conflict, refuted, q, forward, converse, withdrawn, pending = records_at_steps(owner)
        self.assertEqual(conflict["content"]["status"], "CONFLICTED")
        self.assertEqual(refuted["content"]["status"], "REFUTED")
        self.assertEqual(q["content"]["status"], "SUPPORTED")
        self.assertEqual(refuted["content"]["previous_assessment"], conflict["ref"])
        self.assertEqual(withdrawn["content"]["previous_assessment"], refuted["ref"])
        self.assertEqual(withdrawn["content"]["status"], "UNDETERMINED")
        self.assertEqual(forward["content"]["formal_check"]["formal_status"], "VALID")
        self.assertEqual(forward["content"]["route_status"], "BLOCK")
        self.assertIn("PREMISE_REFUTED:claim/p", forward["content"]["defects"])
        self.assertEqual(forward["content"]["independent_conclusion_assessments"],
                         [{"ref": q["ref"], "status": "SUPPORTED"}])
        self.assertEqual(converse["content"]["formal_check"]["countermodel"], {"P": False, "Q": True})
        self.assertEqual(converse["content"]["route_status"], "BLOCK")
        self.assertEqual(pending["content"]["route_status"], "DEFER")
        self.assertFalse(owner["world_truth_established"])
        changed = deepcopy(req)
        changed["payload"]["input"]["lesson"]["steps"][1]["evidence"] = ["high"]
        self.assertFalse(gateway.accept_output(receipt, expected_request=changed)["valid"])
        forward["content"]["route_status"] = "LICENSED"
        self.assertFalse(gateway.accept_output(receipt, expected_request=req)["valid"])

    def test_strict_threshold_against_integer_oracle(self):
        for lo in range(2, 7):
            for hi in range(lo, 7):
                task = example()
                task["occurrences"][0].update(lower=lo, upper=hi)
                possible = {x > 4 for x in range(lo, hi + 1)}
                expected = {frozenset([True]): "SUPPORTED", frozenset([False]): "REFUTED",
                            frozenset([True, False]): "UNDETERMINED"}[frozenset(possible)]
                self.assertEqual(assess_one(task, ["low"])["content"]["status"], expected, (lo, hi))

    def test_identity_scope_origin_and_selection(self):
        for field in knowledge_lesson.SCOPE:
            with self.subTest(field=field):
                task = example()
                task["occurrences"][1][field] += "-different"
                result = assess_one(task, ["high"])["content"]
                self.assertEqual(result["status"], "UNDETERMINED")
                self.assertEqual(result["evaluations"][0]["reason"], field + "_mismatch")
        task = example()
        task["occurrences"][1]["channel"] = "reported_interval"
        self.assertEqual(assess_one(task, ["high"])["content"]["evaluations"][0]["reason"],
                         "occurrence_not_accepted_by_policy")
        task = example()
        task["information"].append({"id": "copy", "occurrence": "high"})
        result = assess_one(task, ["copy", "high", "absent"])["content"]
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertEqual(result["distinct_occurrence_count"], 1)
        self.assertEqual([r["relation"] for r in result["evaluations"]],
                         ["SUPPORTS", "DUPLICATE_OCCURRENCE", "INAPPLICABLE"])

    def test_closed_interval_intersection_and_opposing_evidence(self):
        for bounds, expected, common in [((7, 9), "SUPPORTED", {"lower": 7, "upper": 7}),
                                         ((2, 3), "CONFLICTED", None), ((8, 9), "CONFLICTED", None)]:
            task = example()
            task["occurrences"][2].update(lower=bounds[0], upper=bounds[1])
            result = assess_one(task, ["high", "higher"])["content"]
            self.assertEqual((result["status"], result["common_interval"]), (expected, common))

    def test_forward_on_good_premise_and_both_defects_on_converse(self):
        task = example()
        task["steps"][1]["evidence"] = ["high"]
        task["steps"][2]["evidence"] = []
        result = records_at_steps(knowledge_lesson.run(task))
        self.assertEqual(result[3]["content"]["route_status"], "LICENSED")
        self.assertEqual(result[3]["content"]["independent_conclusion_assessments"][0]["status"], "UNDETERMINED")
        task["occurrences"][3].update(lower=1, upper=2)
        task["steps"][2]["evidence"] = ["other"]
        bad = records_at_steps(knowledge_lesson.run(task))[4]["content"]
        self.assertIn("LINK_INVALID", bad["defects"])
        self.assertIn("PREMISE_REFUTED:claim/q", bad["defects"])

    def test_changed_interpretation_needs_its_own_assessment_and_binding(self):
        task = example()
        revised = deepcopy(task["claims"][0])
        revised["ref"]["version"] = 2
        revised["subject"] = "حامل آخر"
        task["claims"].append(revised)
        task["steps"][3]["premise"] = revised["ref"]
        audit = records_at_steps(knowledge_lesson.run(task))[3]["content"]
        self.assertEqual(audit["formal_check"]["formal_status"], "VALID")
        self.assertEqual(audit["premise_reviews"][1]["status"], "UNASSESSED")
        self.assertIn("SYMBOL_BINDING_CONFLICT:P", audit["defects"])
        self.assertEqual(audit["route_status"], "BLOCK")

    def test_complete_reversible_history_and_typed_information(self):
        result = knowledge_lesson.run(example())
        transport = result["snapshot"]
        packed = Packed(canonical(transport["manifest"]), bytes.fromhex(transport["compressed_hex"]))
        restored = unfold(packed).value
        self.assertCountEqual([r.data() for r in restored.records.values()], result["records"])
        self.assertCountEqual([op.data() for op in restored.operations.values()], result["operations"])
        by_id = {r["ref"]["id"]: r for r in result["records"]}
        self.assertEqual(by_id["interpret/info/high"]["dependencies"], [by_id["info/high"]["ref"]])
        self.assertIn(by_id["interpret/info/high"]["ref"], records_at_steps(result)[0]["dependencies"])
        self.assertNotIn("status", by_id["info/high"]["content"])
        self.assertEqual(by_id["info/high"]["content"], example()["occurrences"][1])
        self.assertFalse(result["neural_training_performed"])

    def test_closed_input_contract_and_event_order(self):
        for edit in (lambda x: x["steps"][0].update(status="SUPPORTED"),
                     lambda x: x["claims"][0].update(threshold=True),
                     lambda x: x["occurrences"][1].update(received_at="2030-01-01T00:00:00Z"),
                     lambda x: x["steps"][-1].update(at="2020-01-01T00:00:00Z"),
                     lambda x: x["steps"][0].update(at="now"),
                     lambda x: x["information"].append(x["information"][0])):
            task = example()
            edit(task)
            self.assertEqual(teaching.run_lesson(task)["status"], "INVALID_INPUT")

    def test_existing_length_course_uses_derived_bounds(self):
        first = {"object": "قضيب", "day": 1, "value": 3, "error": 0, "unit": "cm"}
        second = {"object": "قضيب", "day": 2, "value": 40, "error": 1, "unit": "mm"}
        result = ntl_core.measurement({"readings": [first, second]})
        self.assertEqual(result["answer"]["decision"], "INCREASE")
        assessment = result["trace"]["increase_assessment"]
        self.assertEqual((assessment["bounds"], assessment["relation"]), ([9, 11], "SUPPORTS"))
        second["day"] = 1
        self.assertNotIn("increase_assessment", ntl_core.measurement({"readings": [first, second]})["trace"])
