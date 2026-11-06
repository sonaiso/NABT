"""External admission counterexamples and real existing-owner integrations.

Mocks cover resource transport only. Linguistic outputs come from installed
owners and native checkers, not from the earlier synthetic algebra laboratory.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, gateway_routes, gateway_links
from tools.grammar_catalog.operation_rag import invoke_bounded
from tools.entropy_framework.reuse import current_catalog

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_NATIVE = ("verifiedReading", "classicalSemanticProbe", "progressiveUnitProbe",
                   "alignedAcquisition", "temporalContextProbe", "recursiveBridgeProbe", "epistemicMeasurement")
NATIVE = all(os.access(ROOT / "formal/.lake/build/bin" / p, os.X_OK) for p in REQUIRED_NATIVE)
if os.environ.get("NABT_REQUIRE_IO_GATEWAY_NATIVE") == "1" and not NATIVE:
    raise RuntimeError("The I/O gate requires all seven installed native owners")


def read(relative):
    return json.loads((ROOT / relative).read_text())


def request(route, payload):
    return {"schema": gateway.REQUEST_SCHEMA, "route": route, "payload": payload}


class InputBoundary(unittest.TestCase):
    def test_outer_shape_and_unknown_route_rejected(self):
        good = request("grammar.search", {"query": "النفي"})
        for bad in (None, [], dict(good, extra=True), dict(good, schema="v0"),
                    dict(good, route="os.system"), dict(good, route=[]), dict(good, payload=[])):
            with self.subTest(bad=bad), self.assertRaises((ValueError, TypeError)):
                gateway.validate_request(bad)

    def test_duplicate_keys_and_unpaired_surrogates_rejected(self):
        for raw in (b'{"schema":"x","schema":"y"}',
                    b'{"schema":"nabt.io.request.v1","route":"grammar.search","payload":{"query":"\\ud800"}}'):
            with self.assertRaises(ValueError):
                gateway.request_from_bytes(raw)

    def test_never_accept_caller_authority_or_native_path(self):
        base = request("mantuq.source", {"source": "سالم هو كاتب.", "query": "هل سالم هو كاتب؟", "plan": {}})
        for name in ("checker", "semantic_probe", "root", "approved", "theorems", "tests_passed"):
            bad = deepcopy(base); bad["payload"][name] = "/tmp/caller"
            with self.subTest(field=name), self.assertRaises(ValueError):
                gateway.validate_request(bad)

    def test_limits_and_boolean_integer_confusion(self):
        for limit in (True, 0, -1, 101, "3"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                gateway.validate_request(request("grammar.search", {"query": "اسم", "limit": limit}))
        for frames, budget in (([], 1), ({}, True), ({}, -1)):
            with self.assertRaises(ValueError):
                gateway.validate_request(request("grammar.route", {"query": "اسم", "frames": frames, "budget": budget}))

    def test_worker_names_not_user_selectable(self):
        with self.assertRaises(ValueError):
            invoke_bounded("anything-else", {})

    def test_native_hash_cache_does_not_hide_same_size_change_or_replacement(self):
        import tempfile
        from tools.grammar_catalog.operations import _file_identity, _native_digest
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native"
            path.write_bytes(b"old")
            first_stat = path.stat()
            first = _native_digest(path, _file_identity(path))
            path.write_bytes(b"new")
            os.utime(path, ns=(first_stat.st_atime_ns, first_stat.st_mtime_ns))
            second = _native_digest(path, _file_identity(path))
            path.unlink(); path.write_bytes(b"alt")
            third = _native_digest(path, _file_identity(path))
            self.assertEqual(len({first, second, third}), 3)


class UnifiedProofGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = gateway_links.build()

    def test_exact_current_declaration_population_and_identity(self):
        compiled, _, _, _ = current_catalog(ROOT)
        expected = {r["name"] for r in compiled["theorems"]}
        self.assertEqual({r["name"] for r in self.graph["declarations"]}, expected)
        self.assertEqual(len(self.graph["declarations"]), len(expected))
        for row in self.graph["declarations"]:
            self.assertIn(row["canonical_name"], expected)
            self.assertEqual(len(row["statement_sha256"]), 64)

    def test_source_and_policy_edges_resolve_without_inventing_coverage(self):
        names = {r["name"] for r in self.graph["declarations"]}
        for key in ("source_links", "policy_links"):
            self.assertTrue(self.graph[key])
            self.assertTrue(all(r["referenced_declaration"] in names for r in self.graph[key]))
        self.assertTrue(self.graph["unlinked_source_records"])
        self.assertFalse(self.graph["formal_application_established"])

    def test_tests_have_exact_files_and_method_references_not_runs(self):
        self.assertFalse(self.graph["test_execution_performed"])
        for test in self.graph["tests"]:
            self.assertEqual(test["sha256"], sha256((ROOT / test["path"]).read_bytes()).hexdigest())
            self.assertTrue(test["test_ids"])
            self.assertEqual(test["execution_status"], "NOT_RUN_BY_GATEWAY")
        self.assertIn("tests/test_io_gateway.py", {r["path"] for r in self.graph["tests"]})

    def test_every_route_resolves_existing_families(self):
        known = {r["family"] for r in self.graph["family_test_links"]}
        for _, (families, _, _) in gateway_routes.ROUTES.items():
            self.assertTrue(set(families) <= known)

    def test_lesson_bridges_cover_cognitive_and_empirical_owners(self):
        graph = gateway_links.build("operation")
        expected = {"Nabt.ThinkingRules", "Nabt.Shakhsiyya1Rules", "Nabt.Shakhsiyya3Rules",
                    "Nabt.RationalInquiry", "Nabt.EpistemicMeasurement", "Nabt.GroundedPassage",
                    "Nabt.EvidenceLifecycleV1", "Nabt.TemporalContext"}
        self.assertTrue(expected <= {r["module"] for r in graph["declarations"]})
        self.assertEqual(graph["curriculum_links"]["authority"], "CURRICULUM_ONLY")
        self.assertTrue(all(not r["learning_complete"] for r in graph["curriculum_links"]["matrices"]))
        self.assertIn("tests/test_cognitive_teaching.py", {r["path"] for r in graph["tests"]})


class GatewayReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = request("operation", read("examples/operation_rag/contrast.json"))
        cls.receipt = gateway.run(cls.request)

    def test_real_contrast_preserves_independent_numeric_oracle(self):
        self.assertEqual(self.receipt["status"], "EXECUTED")
        original = self.receipt["execution"]["owner_result"]
        self.assertEqual(original["status"], "EXECUTED")
        observations = original["execution"]["owner_result"]["observations"]
        self.assertEqual([int(r["result"]["numeric_code"]) for r in observations],
                         [1144809, 1158497, 1114538, 1114537, 1114539])
        self.assertFalse(self.receipt["limits"]["semantic_rank_promoted"])

    def test_independent_replay_admits_only_current_complete_receipt(self):
        result = gateway.accept_output(self.receipt, expected_request=self.request)
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["semantic_rank_promoted"])

    def test_raw_owner_output_and_changed_request_rejected(self):
        raw = self.receipt["execution"].get("owner_result", {})
        self.assertFalse(gateway.accept_output(raw, expected_request=self.request)["valid"])
        changed = request("grammar.search", {"query": "اسم"})
        self.assertFalse(gateway.accept_output(self.receipt, expected_request=changed)["valid"])

    def test_tampered_claims_rejected_after_rehash(self):
        for field in ("owner", "test", "proof"):
            bad = deepcopy(self.receipt)
            if field == "owner":
                bad["execution"]["owner_result"]["status"] = "FORGED_LICENSE"
            elif field == "test":
                bad["proof_test_links"]["test_execution_performed"] = True
            else:
                bad["proof_test_links"]["declarations"][0]["statement_sha256"] = "0"*64
            graph = {k: v for k, v in bad["proof_test_links"].items() if k != "links_sha256"}
            bad["proof_test_links"]["links_sha256"] = gateway.digest(graph)
            with self.subTest(field=field):
                self.assertFalse(gateway.accept_output(bad, expected_request=self.request)["valid"])

    def test_stale_source_snapshot_rejected(self):
        bad = deepcopy(self.receipt); bad["snapshot_sha256"] = "0"*64
        result = gateway.accept_output(bad, expected_request=self.request)
        self.assertEqual(result["message"], "STALE_IO_SNAPSHOT")

    def test_resource_failure_is_not_semantic_rejection_or_acceptance(self):
        with patch.object(gateway, "invoke_bounded", return_value={"execution_status": "RESOURCE_LIMIT", "code": "WORKER_TIMEOUT"}):
            result = gateway.run(self.request)
        self.assertEqual(result["status"], "RESOURCE_LIMIT")
        self.assertFalse(gateway.accept_output(result, expected_request=self.request)["valid"])


class InstalledAdapters(unittest.TestCase):
    def test_operation_in_gateway_does_not_spawn_detached_nested_worker(self):
        from tools.grammar_catalog import operation_rag
        with patch.object(operation_rag, "invoke_bounded", side_effect=AssertionError("nested worker")):
            result = gateway_routes.execute("operation", read("examples/operation_rag/contrast.json"), inside_worker=True)
        self.assertEqual(result["status"], "EXECUTED")

    def test_retrieval_uses_all_installed_owners(self):
        for route in ("grammar.search", "awamil.search", "agents.search", "units.search", "irab.search", "mantuq.search"):
            with self.subTest(route=route):
                result = gateway_routes.execute(route, {"query": "اسم الفاعل", "limit": 2})
                self.assertIsInstance(result, dict)
                self.assertTrue(result)

    def test_utf_original_and_governor_premise_qualification(self):
        result = gateway.run(request("agents.transport", read("examples/progressive_agents/utf16.json")))
        self.assertEqual(result["status"], "EXECUTED")
        from tools.grammar_catalog.unicode_transport import transcode
        self.assertEqual(result["execution"]["owner_result"], transcode(read("examples/progressive_agents/utf16.json")))
        case = gateway_routes.execute("awamil.check", read("examples/awamil_agent/case.json"))
        self.assertFalse(case["application_certified"])
        self.assertEqual(case["premise_origin"], "CALLER_SUPPLIED_NOT_ACQUIRED_FROM_SENTENCE")

    def test_readers_keep_their_original_nonpromotion_fields(self):
        for route, path in (("awamil.analyze", "examples/awamil_agent/nominal.json"),
                            ("agents.gate", "examples/awamil_agent/nominal.json"),
                            ("irab.analyze", "examples/irab_agent/jussive.json")):
            with self.subTest(route=route):
                result = gateway_routes.execute(route, read(path))
                self.assertIsInstance(result, dict)
                self.assertTrue(result)
        routed = gateway_routes.execute("grammar.route", {"query": "اسم", "frames": {}, "budget": 0})
        self.assertTrue(routed)


@unittest.skipUnless(NATIVE, "Build all seven native owners; io-gateway-native makes absence fatal")
class NativeSourceAdmission(unittest.TestCase):
    def test_cognitive_lessons_keep_hidden_motive_and_empirical_bridge_unknown(self):
        for name in ("epistemic", "world_prior"):
            lesson = read("examples/cognitive_teaching/"+name+".json")
            if name == "world_prior":
                # Spatial/temporal descriptions cannot invent a causal bridge.
                lesson["payload"]["source_text"] = "\n".join(lesson["payload"]["source_text"].splitlines()[:-1])+"\n"
                lesson["payload"]["plan"]["bridge_clause"] = None
            operation = {"schema": "nabt.operation-rag.request.v1", "query": "درس معرفي",
                         "operation": "lesson", "inputs": {"lesson": lesson}}
            with self.subTest(lesson=name):
                receipt = gateway.run(request("operation", operation))
                self.assertEqual(receipt["status"], "EXECUTED", receipt["execution"])
                rag = receipt["execution"]["owner_result"]
                self.assertEqual(rag["status"], "EXECUTED", rag["execution"])
                owner = rag["execution"]["owner_result"]
                self.assertEqual(owner["status"], "UNKNOWN", owner)
                self.assertTrue(owner["execution_measured"])
                self.assertFalse(owner["limits"]["empirical_causality_established"])
                self.assertFalse(owner["limits"]["world_truth_established"])

    def test_mantuq_clean_withdrawn_blocked_and_conflicted_source(self):
        contract = read("evidence/mantuq_source_fold_v1/acceptance_contract.json")
        cases = {r["id"]: r for r in contract["cases"]}
        for name in ("clean_explicit_requirements", "absent_negative_blocker_witness", "blocker_present", "blocker_conflict", "derived_tainted_requirement"):
            row = cases[name]
            payload = {"source": row["source"], "query": contract["query"],
                "plan": {"schema": "nabt.mantuq-source-plan.v1", "policy_id": "guarded_cause",
                         "requirements": contract["requirements"], "bridge_clause": row["bridge_clause"]},
                "source_id": "fixture", "scope": "s", "context": "speaker=salim", "time": "t1"}
            with self.subTest(name=name):
                receipt = gateway.run(request("mantuq.source", payload))
                self.assertEqual(receipt["status"], "EXECUTED", receipt["execution"])
                owner = receipt["execution"]["owner_result"]
                self.assertEqual(owner["status"], row["conditional_status"])
                self.assertEqual(owner["conditional_consequence"], row["conditional_consequence"])
                self.assertFalse(receipt["limits"]["world_truth_established"])
                if owner["status"] == "DEFER":
                    replay = gateway.accept_output(receipt, expected_request=request("mantuq.source", payload))
                    self.assertTrue(replay["valid"], replay)
                    self.assertFalse(replay["semantic_rank_promoted"])

    def test_units_time_and_application_use_native_owners(self):
        for route, path in (("units.run", "examples/unit_composition/long_vowel.json"),
                            ("application.temporal", "examples/context_application/yesterday.json"),
                            ("application.analyze", "examples/context_application/application.json")):
            with self.subTest(route=route):
                receipt = gateway.run(request(route, read(path)))
                self.assertEqual(receipt["status"], "EXECUTED", receipt["execution"])
                self.assertFalse(receipt["limits"]["semantic_rank_promoted"])
                self.assertTrue(receipt["execution"]["owner_result"])
                if route == "application.analyze":
                    self.assertEqual(receipt["execution"]["owner_result"]["bridge"]["status"], "DEFER")
                    self.assertFalse(receipt["execution"]["owner_result"]["bridge"]["application_license_granted"])


if __name__ == "__main__":
    unittest.main()
