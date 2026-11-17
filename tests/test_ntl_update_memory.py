"""Independent source-owner replay, finite witnesses and update counterexamples."""
from copy import deepcopy
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, ntp
from tools.lexical_training import ntl_update_memory as lesson, teaching
from tools.lexical_training import update_memory_model as model, train_update_memory as training

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "formal/.lake/build/bin/updateMemoryProbe"
if os.environ.get("NABT_REQUIRE_UPDATE_MEMORY_NATIVE") == "1" and not NATIVE.is_file():
    raise RuntimeError("Build updateMemoryProbe for required conformance")


def request(active=(), updates=(), family="breaking", entity="كأس أ", event="حادثة أ"):
    templates, _, _ = lesson.profile(family, entity, event)
    return {"schema": lesson.SCHEMA, "family": family, "entity": entity, "event": event, "scope": "trial",
            "sources": [{"id": role, "text": text} for role, text in templates.items()],
            "active": list(active), "updates": list(updates)}


class UpdateMemory(unittest.TestCase):
    def test_all_states_against_existing_source_kernel(self):
        now, future = set(), set()
        for bits in product((0, 1), repeat=5):
            active = [r for r, v in zip(model.ROLES, bits) if v]
            r = lesson.run(request(active))
            value = r["history"][0]
            self.assertEqual(value["answer_projection"], training.reference(bits))
            self.assertEqual(value["neural_observation"]["prediction"], value["answer_projection"])
            now.add(tuple(value["answer_projection"]))
            future.add(tuple(tuple(training.reference(training.apply(bits, a))) for a in training.contexts()))
            self.assertFalse(r["world_truth_established"])
            for answer in value["questions"].values():
                self.assertTrue(all(c["accepted"] for c in answer["certificate_checks"].values()))
        self.assertEqual((len(now), len(future)), (16, 32))

    def test_same_answer_different_updates_and_exact_fold(self):
        update = {"op": "activate", "source_id": "law"}
        a = lesson.run(request(["property"], [update]))
        b = lesson.run(request(["law"], [update]))
        self.assertEqual(a["history"][0]["answer_projection"], b["history"][0]["answer_projection"])
        self.assertNotEqual(a["history"][1]["answer_projection"], b["history"][1]["answer_projection"])
        restored = lesson.unfold(a["history"][0]["memory"], [update])
        self.assertEqual(lesson.run(restored)["history"], a["history"])
        changed = deepcopy(a["history"][0]["memory"])
        changed["payload"]["active"] = ["law"]
        with self.assertRaises(ValueError): lesson.unfold(changed, [])

    def test_alternate_support_conflict_and_independent_state(self):
        q = request(["property", "law", "other_law", "event_positive", "event_negative", "state"],
                    [{"op": "withdraw", "source_id": s} for s in ("law", "other_law", "event_positive")])
        q["sources"].append({"id": "other_law", "text": q["sources"][1]["text"]})
        r = lesson.run(q)
        self.assertEqual([x["answer_projection"] for x in r["history"]],
                         [[1,1,1,1],[1,1,1,1],[0,1,1,1],[0,0,1,1]])
        self.assertEqual(r["history"][0]["questions"]["event"]["owner_result"]["status"], "CONFLICT")
        self.assertEqual(r["history"][-1]["questions"]["event"]["owner_result"]["status"], "REFUTED")
        self.assertEqual(r["history"][-1]["questions"]["state"]["owner_result"]["status"], "SUPPORTED")

    def test_no_fact_from_source_registration_or_declarations(self):
        r = lesson.run(request())
        self.assertEqual(r["history"][0]["answer_projection"], [0,0,0,0])
        self.assertEqual({v["owner_result"]["status"] for v in r["history"][0]["questions"].values()}, {"UNKNOWN"})
        self.assertEqual(len(r["history"][0]["memory"]["payload"]["sources"]), 5)

    def test_source_binding_entity_event_scope_and_unsupported_tail(self):
        for field in ("entity", "event"):
            q = request(["property"])
            q[field] = "هوية أخرى"
            self.assertEqual(lesson.run(q)["status"], "DEFER_READING")
        q = request(["property"])
        q["sources"][0]["text"] += " وربما خلاف ذلك."
        self.assertEqual(lesson.run(q)["history"], [])
        q = request(["property", "law"], family="opening", entity="باب جديد", event="فتح جديد")
        r = lesson.run(q)
        self.assertEqual(r["history"][0]["answer_projection"], [1,0,0,0])
        self.assertEqual(r["history"][0]["questions"]["capacity"]["owner_result"]["scope"], "trial")

    def test_invalid_inputs_and_budgets(self):
        cases = [dict(request(), active=[True]), dict(request(), active=["missing"]),
                 dict(request(), active=["law", "law"]), dict(request(), updates=[True]),
                 dict(request(), updates=[{"op":"activate", "source_id": True}]),
                 dict(request(), updates=[{"op":"replace", "source_id":"law"}]),
                 dict(request(), family=True), dict(request(), scope=""), dict(request(), authority="LICENSED")]
        duplicate = request(); duplicate["sources"].append(duplicate["sources"][0]); cases.append(duplicate)
        for q in cases:
            with self.subTest(q=q):
                self.assertEqual(teaching.run_lesson(q)["status"], "INVALID_INPUT")
        q = request(updates=[{"op":"activate", "source_id":"law"}] * 17)
        self.assertEqual(teaching.run_lesson(q)["status"], "RESOURCE_LIMIT")

    def test_missing_or_wrong_model_preserves_owner(self):
        q = request(["property", "law"])
        baseline = lesson.run(q)
        with patch.object(model, "MODEL", Path("/nonexistent/ntl_model.json")):
            r = lesson.run(q)
        self.assertEqual(r["history"][0]["questions"], baseline["history"][0]["questions"])
        self.assertEqual(r["history"][0]["neural_observation"]["status"], "MODEL_UNAVAILABLE")
        with patch.object(model, "MODEL_SHA256", "0" * 64):
            self.assertEqual(model.propose([], set())["status"], "MODEL_UNAVAILABLE")

    def test_model_never_reads_the_post_update_owner_answer(self):
        original = model.predict
        seen = []
        def observe(parameters, sources, active):
            seen.append((deepcopy(sources), set(active)))
            return original(parameters, sources, active)
        with patch.object(model, "predict", side_effect=observe):
            lesson.run(request(["property"], [{"op":"activate", "source_id":"law"}]))
        self.assertEqual([active for _, active in seen], [{"property"}, {"property", "law"}])
        self.assertTrue(all("answer" not in s and "questions" not in s for rows,_ in seen for s in rows))

    def test_retained_neural_composition_error_cannot_authorize_answer(self):
        q = request()
        templates, _, _ = lesson.profile(q["family"], q["entity"], q["event"])
        q["sources"] = ([{"id": f"new_p{i}", "text": templates["property"]} for i in range(10)] +
                        [{"id": f"new_l{i}", "text": templates["law"]} for i in range(2)])
        q["active"] = ["new_l0"]
        result = lesson.run(q)["history"][0]
        self.assertEqual(result["answer_projection"], [0,0,0,0])
        self.assertEqual(result["questions"]["capacity"]["owner_result"]["status"], "UNKNOWN")
        proposal = result["neural_observation"]
        self.assertEqual(proposal["prediction"], [1,0,0,0])
        self.assertFalse(proposal["matches_owner"])
        self.assertEqual(proposal["authority"], "NONE")

    @unittest.skipUnless(NATIVE.is_file(), "Build updateMemoryProbe")
    def test_native_finite_contract_and_signatures(self):
        native = json.loads(subprocess.check_output([str(NATIVE)], text=True))
        self.assertEqual(native["law"], "nabt.update-memory.v1")
        self.assertEqual(len(native["rows"]), 32)
        for row in native["rows"]:
            self.assertEqual(row["answer"], training.reference(row["memory"]))
            self.assertEqual(row["signature"], [training.reference(training.apply(row["memory"], a))
                                               for a in (None, [0,1], [1,1])])


class Training(unittest.TestCase):
    def test_retained_fit_gradients_and_composition_failures(self):
        current, report, evaluation = training.train()
        retained = model.load()
        self.assertEqual({k:v for k,v in current.items() if k != "parameters"},
                         {k:v for k,v in retained.items() if k != "parameters"})
        for op in ("and", "or"):
            for actual, expected in zip(current["parameters"][op], retained["parameters"][op]):
                self.assertAlmostEqual(actual, expected, delta=2e-9)
        self.assertLess(report["max_gradient_error"], 1e-6)
        self.assertTrue(all(abs(v) > 0 for values in report["parameter_changes"].values() for v in values))
        self.assertEqual(evaluation["metrics"]["single_step"]["trained_correct"], 352)
        self.assertEqual(evaluation["metrics"]["two_step"]["trained_correct"], 3872)
        self.assertEqual(evaluation["metrics"]["answer_only_best_single_step_correct"], 336)
        # Freeze observed errors instead of retuning after viewing this test.
        failures = [r for r in evaluation["alternative_support"] if r["prediction"] != r["reference"]]
        self.assertEqual(len(failures), 3)

    def test_frozen_protocol_rejects_changes_before_fitting(self):
        p = json.loads((model.DIRECTORY / "protocol.json").read_bytes())
        for key, value in (("seed", True), ("seed", 116.0), ("epochs", 10), ("threshold", 0.4), ("authority", "APPROVED")):
            with self.assertRaises(ValueError): training.fit(dict(p, **{key: value}))


class PublicBoundary(unittest.TestCase):
    def test_ntp_lesson_replay_tampering_and_separate_sources(self):
        q = request(["property"], [{"op":"activate", "source_id":"law"}])
        external = ntp.request("cognitive.lesson", {"lesson": q})
        report = gateway.run(external)
        self.assertEqual(report["status"], "EXECUTED")
        self.assertTrue(gateway.accept_output(report, expected_request=external)["valid"])
        owner = report["execution"]["owner_result"]
        self.assertEqual(owner["owner_result"]["history"][-1]["answer_projection"], [1,0,0,0])
        self.assertEqual(len(owner["source_traces"]), 5)
        for i, trace in enumerate(owner["source_traces"]):
            self.assertEqual(trace["request_path"], f"/payload/input/lesson/sources/{i}/text")
            self.assertEqual(trace["source_id"], q["sources"][i]["id"])
        forged = deepcopy(report)
        forged["execution"]["owner_result"]["owner_result"]["history"][-1]["answer_projection"] = [1,1,0,1]
        self.assertFalse(gateway.accept_output(forged, expected_request=external)["valid"])
        changed = deepcopy(external); changed["payload"]["input"]["lesson"]["scope"] = "another_trial"
        self.assertFalse(gateway.accept_output(report, expected_request=changed)["valid"])

    def test_ntl_verification_requires_the_independent_lesson(self):
        q = request(["state"])
        report = teaching.run_lesson(q)
        self.assertTrue(teaching.verify_lesson(report, expected_lesson=q)["valid"])
        changed = deepcopy(q); changed["active"] = ["event_positive"]
        self.assertFalse(teaching.verify_lesson(report, expected_lesson=changed)["valid"])
