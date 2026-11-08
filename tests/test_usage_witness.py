"""Real installed owner checks plus separate dispatch-policy integration tests."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from nabt.errors import NabtError

from tools.grammar_catalog import gateway, orchestration, usage_witness as u
from tools.grammar_catalog.operations import digest
from tools.lexical_training import cognitive_graph as graph

ROOT = Path(__file__).resolve().parents[1]
READY = all((ROOT/"formal/.lake/build/bin"/name).is_file() for name in ("linguisticTruth", "lexicalDenotation"))
if os.environ.get("NABT_REQUIRE_ORCHESTRATION_NATIVE") == "1" and not READY:
    raise RuntimeError("Usage witness tests require the real installed native owners")

LITERAL = "أعني بالأسد الحيوان المفترس"
INCOMPLETE = "أعني بالأسد الرجل الشجاع"
FIGURATIVE = INCOMPLETE + " لا الحيوان المفترس"


def request(text, context=None, sid="usage_test"):
    return {"text": text, "source_id": sid,
            "usage_context": {"profile_id": "linguistic"} if context is None else context}


class BoundaryTests(unittest.TestCase):
    def test_no_caller_witness_or_model_path(self):
        for field in ("accepted", "literal_excluded", "concept_id", "condition_mask", "witness", "model_path"):
            with self.assertRaises(ValueError):
                graph.validate_request({**request(LITERAL), "usage_context": {field: True}})
            with self.assertRaises(ValueError):
                orchestration.validate({**request(LITERAL), field: True})
        for value in (True, None, "", [], {"profile_id": False}):
            with self.assertRaises(ValueError):
                u.validate_context(value)

    def test_graph_keeps_supplied_context_without_mutating_it(self):
        p = request("زَيْدٌ حَكِيمٌ.")
        p.update(lexical_text="source", context={"entities": []})
        original = deepcopy(p)
        self.assertEqual(graph.validate_request(p), p)
        self.assertEqual(p, original)
        for p in ({"text": "كتب", "lexical_text": False}, {"text": "كتب", "context": {"licensed": True}}):
            with self.assertRaises((ValueError, NabtError)):
                graph.validate_request(p)


@unittest.skipUnless(READY, "build linguisticTruth and lexicalDenotation")
class NativeUsageWitnessTests(unittest.TestCase):
    def test_literal_reuses_existing_native_identity_and_reference(self):
        result = u.run(request(LITERAL))
        self.assertTrue(result["owner_report"]["native_checked"])
        self.assertEqual([r["concept_id"] for r in result["applications"]], ["lisan:asad-animal"])
        application = result["applications"][0]
        native = {r["identity"]["id"]: r for r in u.identities.catalogue()["concepts"]}
        self.assertEqual(application["concept_reference"], native["lisan:asad-animal"]["reference"])
        self.assertEqual(application["identity_alignment"]["status"], "SCOPED_EDITORIAL_ALIGNMENT")
        self.assertFalse(application["identity_alignment"]["independent_review"])
        self.assertNotIn("asad_animal", [r["id"] for r in result["concepts"]])
        self.assertFalse(result["world_truth_established"])

    def test_figurative_intent_needs_its_own_exclusion(self):
        incomplete, complete = u.run(request(INCOMPLETE)), u.run(request(FIGURATIVE))
        self.assertEqual(incomplete["applications"], [])
        self.assertTrue(incomplete["owner_report"]["intended_sense_acquired"])
        self.assertEqual([(a["concept_id"], a["use_kind"]) for a in complete["applications"]], [("asad_brave", "figurative")])
        self.assertTrue(complete["majaz_candidates"][0]["literal_excluded"])
        self.assertEqual(len(incomplete["owner_report"]["occurrences"][0]["candidates"]),
                         len(complete["owner_report"]["occurrences"][0]["candidates"]))
        self.assertFalse(complete["grammar_path_certified"])

    def test_missing_profile_is_not_silently_linguistic(self):
        result = u.run(request(FIGURATIVE, context={}))
        self.assertEqual(result["applications"], [])
        self.assertIsNone(result["owner_report"]["context"]["profile_id"])
        self.assertTrue(result["owner_report"]["pending_profiles"])

    def test_quote_unknown_and_conflict_never_become_positive(self):
        for text in ("«"+FIGURATIVE+"»", "رأيت الأسد", "زعبولا", LITERAL+" لا الحيوان المفترس"):
            with self.subTest(text=text):
                result = u.run(request(text))
                self.assertEqual(result["applications"], [])
                self.assertFalse(result["automatic_training_label"])
        mixed = u.run(request(LITERAL+". "+LITERAL+" لا الحيوان المفترس"))
        self.assertEqual(mixed["status"], "CONFLICT")
        self.assertEqual(len(mixed["applications"]), 1)

    def test_repetition_and_separate_clause_cannot_borrow_a_cue(self):
        text = INCOMPLETE+". "+FIGURATIVE
        result = u.run(request(text))
        self.assertEqual(len(result["applications"]), 1)
        self.assertEqual([b["accepted"] for b in result["majaz_candidates"]], [False, True])
        nodes = {r["id"] for r in graph.sign_nodes(text, "usage_test")}
        self.assertTrue(all(b["occurrence_id"] in nodes for b in result["majaz_candidates"]))
        for bundle in result["majaz_candidates"]:
            raw = text.encode(); span = bundle["span"]
            self.assertEqual(raw[span["start_byte"]:span["end_byte"]].decode(), span["raw_text"])
        detached = u.run(request(INCOMPLETE+". لا الحيوان المفترس"))
        self.assertEqual(detached["applications"], [])

    def test_context_time_and_source_version_change_witness_identity(self):
        baseline = u.run(request(FIGURATIVE))["applications"][0]
        variants = [request(FIGURATIVE, sid="another"), request(FIGURATIVE+"."),
                    request(FIGURATIVE, context={"profile_id": "linguistic", "time": "later"}),
                    request(FIGURATIVE, context={"profile_id": "linguistic", "context": "another"})]
        for p in variants:
            current = u.run(p)["applications"][0]
            self.assertNotEqual(current["witness_id"], baseline["witness_id"])

    def test_unavailable_native_or_source_never_supplies_witnesses(self):
        with patch.object(u.owner, "_verify_native", side_effect=OSError("unavailable")):
            result = u.run(request(FIGURATIVE))
        self.assertEqual(result["applications"], [])
        self.assertEqual(result["owner_report"]["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        with patch.object(u.identities, "catalogue", side_effect=OSError("missing identity owner")):
            result = u.run(request(FIGURATIVE))
        self.assertEqual(result["applications"], [])
        self.assertTrue(result["owner_report"]["native_checked"])
        self.assertEqual(result["status"], "IDENTITY_UNAVAILABLE")

    def test_invalid_profile_and_exhaustion_keep_their_status(self):
        result = u.run(request(LITERAL, context={"profile_id": "not_installed"}))
        self.assertEqual(result["status"], "INVALID_INPUT")
        acquire = u.owner.acquire
        with patch.object(u.owner, "acquire", side_effect=lambda *a, **kw:
                          acquire(*a, **kw, budget=u.owner.AcquisitionBudget(max_native_scan=0))):
            result = u.run(request(FIGURATIVE))
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(result["applications"], [])

    def test_forged_frame_or_cross_occurrence_premise_is_rejected(self):
        original = u.owner.acquire(FIGURATIVE, source_id="usage_test", profile_id="linguistic")
        for what in ("source", "span", "cue"):
            altered = deepcopy(original)
            if what == "source": altered["occurrences"][0]["frame"]["occurrence"]["source"] = "foreign"
            if what == "span": altered["occurrences"][0]["span"]["start_byte"] = True
            if what == "cue": altered["acquired_premises"][0]["cue_span"] = altered["acquired_premises"][0]["sense_span"]
            with patch.object(u.owner, "acquire", return_value=altered):
                with self.assertRaises(ValueError): u.run(request(FIGURATIVE))

    def test_policy_consumes_actual_bundle_but_still_requires_prior_layer(self):
        usage = u.run(request(FIGURATIVE))
        # A policy fixture, deliberately NOT represented as a syntax run.
        previous = {"name": "mantuq", "layer": 4, "closed": True,
                    "source_id": usage["source"]["id"], "source_sha256": usage["source"]["sha256"]}
        previous["record_id"] = digest(previous)
        result = u.dispatch_majaz(usage, source=usage["source"], cursor=5, predecessor=previous)
        self.assertEqual(result["records"][0]["dispatch"], "DISPATCH")
        self.assertEqual(result["records"][0]["condition_mask"], 63)
        incomplete = u.run(request(INCOMPLETE))
        prior = {**previous, "source_sha256": incomplete["source"]["sha256"]}
        prior["record_id"] = digest({k:v for k,v in prior.items() if k != "record_id"})
        refused = u.dispatch_majaz(incomplete, source=incomplete["source"], cursor=5, predecessor=prior)
        self.assertEqual(refused["records"][0]["dispatch"], "MAJAZ_BEFORE_TAADTHUR_OR_QARINA")
        wrong_layer = u.dispatch_majaz(usage, source=usage["source"], cursor=4, predecessor=previous)
        self.assertEqual(wrong_layer["records"][0]["dispatch"], "LAYER_SKIPPED")
        previous["closed"] = False
        previous["record_id"] = digest({k:v for k,v in previous.items() if k != "record_id"})
        stopped = u.dispatch_majaz(usage, source=usage["source"], cursor=5, predecessor=previous)
        self.assertEqual(stopped["records"][0]["dispatch"], "DISPATCH_WITHOUT_CONDITION")

    def test_orchestrator_does_not_call_usage_owner_across_an_open_lower_gate(self):
        with patch.object(u, "run", side_effect=AssertionError("layer skipped")):
            result = orchestration.run(request(FIGURATIVE))
        self.assertEqual(result["stopped_at"], "orthography")
        self.assertEqual(result["special_gates"][0]["dispatch"], "NOT_DISPATCHED")

    def test_graph_preserves_lexical_and_discourse_owner_report(self):
        p = json.loads((ROOT/"examples/awamil_agent/nominal.json").read_text())
        p["text"] = "زَيْدٌ حَكِيمٌ."; p["source_id"] = "context_test"
        result = graph.analyze(p)
        self.assertEqual(result["relational_owner"], graph.relational.analyze(p))
        old = graph.relational.analyze({"text": p["text"], "source_id": p["source_id"]})
        self.assertNotEqual(result["relational_owner"]["owner_reports"]["irab"], old["owner_reports"]["irab"])

    def test_orchestrator_passes_context_and_lexicon_into_concept_owner(self):
        p = json.loads((ROOT/"examples/awamil_agent/nominal.json").read_text())
        p.update(text="زَيْدٌ حَكِيمٌ.", source_id="context_test", usage_context={"profile_id": "linguistic"})
        result = orchestration.run(p)
        self.assertEqual(result["stopped_at"], "concept")
        expected = graph.relational.analyze({k:v for k,v in p.items() if k != "usage_context"})
        self.assertEqual(result["owner_reports"]["concept"]["relational_owner"], expected)
        self.assertFalse(result["dispatch_ledger"][-1]["closed"])

    def test_missing_optional_model_does_not_suppress_use_owner(self):
        with patch.object(graph, "MODEL", Path("/nonexistent/usage-model.json")):
            result = graph.analyze(request(LITERAL))
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual([r["concept_id"] for r in result["concept_graph"]["source_use_applications"]], ["lisan:asad-animal"])
        self.assertEqual(result["alignment_edges"], [])

    def test_graph_uses_one_identity_across_views_and_keeps_neural_proposals(self):
        result = graph.analyze(request(FIGURATIVE))
        nodes = result["concept_graph"]["nodes"]
        self.assertEqual(len({r["id"] for r in nodes}), len(nodes))
        self.assertEqual(sum(r["id"] == "lisan:asad-animal" for r in nodes), 1)
        self.assertEqual(len(result["concept_graph"]["source_use_applications"]), 1)
        self.assertEqual(result["concept_graph"]["admitted_concept_applications"], [])
        self.assertTrue(all(not r["accepted"] for r in result["alignment_edges"]))
        self.assertEqual(result["concept_graph"]["grounded_world_claims"], [])
        self.assertEqual(result["acceptance"]["status"], "DEFER")

    def test_gateway_replay_withdrawal_and_forged_application(self):
        p = {"schema": gateway.REQUEST_SCHEMA, "route": "neural.graph", "payload": request(FIGURATIVE)}
        result = gateway.run(p)
        self.assertEqual(result["status"], "EXECUTED", result["execution"])
        self.assertTrue(gateway.accept_output(result, expected_request=p)["valid"])
        changed = deepcopy(p); changed["payload"]["text"] = INCOMPLETE
        self.assertFalse(gateway.accept_output(result, expected_request=changed)["valid"])
        fresh = gateway.run(changed)
        self.assertEqual(fresh["execution"]["owner_result"]["concept_graph"]["source_use_applications"], [])
        forged = deepcopy(result)
        forged["execution"]["owner_result"]["concept_graph"]["source_use_applications"][0]["concept_id"] = "invented"
        self.assertFalse(gateway.accept_output(forged, expected_request=p)["valid"])

    def test_usage_source_availability_is_part_of_gateway_snapshot(self):
        path = ROOT/"evidence/linguistic_truth_v1/sources/thinking_cognition.txt"
        relative = path.relative_to(ROOT).as_posix()
        before = gateway.snapshot()["files"][relative]
        self.assertEqual(before, sha256(path.read_bytes()).hexdigest())
        original = Path.exists
        with patch.object(Path, "exists", lambda p: False if p == path else original(p)):
            self.assertEqual(gateway.snapshot()["files"][relative], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
