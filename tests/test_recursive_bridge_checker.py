"""Adversarial checker regressions, separate from frozen independent material.

These tests challenge the evaluator itself. They are not added to the forty
authored material cases and are not evidence of held-out Arabic acquisition.
"""

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nabt_recursive_bridge_checker", ROOT / "tools/check_recursive_bridge.py")
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def envelope(op, **values):
    return {"law_id": checker.LAW, "scope": checker.SCOPE, "conditional": True,
            "acquisition_measured": False, "grammar_certified": False,
            "status": "OK", "op": op, **values}


def bridge_output(request):
    return envelope("bridge_assess", **checker.bridge_oracle(request),
                    atomization_domain="unicode-scalar-exact.v1", node=deepcopy(request["node"]),
                    erased_tree=checker.erase(request["node"]), nodes=len(checker.preorder(request["node"])),
                    semantic_obligation="explicit_PR14_host_Licensed_and_Grammar_Certified_and_RealizationAligned_contracts_required")


def zero_number():
    tree = {"op": "leaf", "seed": {"kind": "root3", "radicals": [0, 0, 0]}}
    request = {"op": "core_number", "registry_id": "authored.numeric-regression.v1", "tree": tree}
    output = envelope("core_number", number_domain=checker.NUMBER_DOMAIN, registry_id=request["registry_id"],
                      tree=deepcopy(tree), number="0", estimated_max_number_bits=17, number_bit_budget=4096,
                      structural_only=True, linguistically_licensed=False, height=0, nodes=1)
    return request, output


def one_enumeration():
    tree = {"op": "leaf", "seed": {"kind": "lexical", "entry": 0}}
    inventory = {"seeds": [tree["seed"]], "unary_rules": [], "binary_rules": []}
    request = {"op": "core_enumerate", "registry_id": "authored.enumeration-regression.v1",
               "inventory": inventory, "height": 2, "max_candidates": 20}
    output = envelope("core_enumerate", number_domain=checker.NUMBER_DOMAIN, registry_id=request["registry_id"],
                      enumeration="COMPLETE", search_complete=True, linguistic_rejection=False, structural_only=True,
                      inventory=deepcopy(inventory), removed_duplicate_seeds=0, removed_duplicate_unary_rules=0,
                      removed_duplicate_binary_rules=0, estimated_max_number_bits=6, number_bit_budget=4096,
                      height=2, candidate_count=1, candidates=[{"tree": tree, "number": "6"}])
    return request, output


class RecursiveBridgeCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = checker.load_material()

    def case(self, case_id):
        return deepcopy(next(case for case in self.material["cases"] if case["case_id"] == case_id))

    def plan(self, case_id):
        case = self.case(case_id)
        return checker.build_case_plan(case["operation"], case["input"], self.material["fixtures"])

    def request(self, case_id):
        return self.plan(case_id)["requests"][0]["request"]

    def test_all_forty_plans_ignore_mutated_gold_contract_and_case_group(self):
        changed = deepcopy(self.material)
        for case in changed["cases"]:
            case["expected"] = {"LICENSED": True, "carrier_map": "gold-only-answer", "root": [999]}
            case["contract"] = "gold-only-gate"
            case["group"] = "gold-only-group"
        self.assertEqual(checker.build_plans(changed), checker.build_plans(self.material))
        self.assertNotIn("gold-only", checker.canonical(checker.build_plans(changed)))

    def test_frozen_material_digest_is_enforced_not_only_embedded_metadata(self):
        self.assertEqual(sha256(checker.MATERIAL.read_bytes()).hexdigest(), checker.MATERIAL_SHA)
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "material.json"
            changed.write_bytes(checker.MATERIAL.read_bytes() + b"\n")
            with patch.object(checker, "MATERIAL", changed), self.assertRaisesRegex(ValueError, "Frozen material changed"):
                checker.load_material()

    def test_planning_does_not_mutate_the_frozen_fixtures(self):
        before = checker.canonical(self.material)
        checker.build_plans(self.material)
        self.assertEqual(before, checker.canonical(self.material))

    def test_omitted_literal_is_not_repaired_by_rebuilding_a_shorter_template(self):
        positive, omitted = self.request("A01"), self.request("A07")
        original = positive["node"]["metadata"]["morphology"]
        broken = omitted["node"]["metadata"]["morphology"]
        self.assertEqual(original["reading"]["pattern"], broken["reading"]["pattern"])
        self.assertEqual(len(original["alignment"]), 8)
        self.assertEqual(len(broken["alignment"]), 7)
        self.assertFalse(checker.bridge_oracle(omitted)["source_bound"])

    def test_utf8_split_goes_to_real_byte_span_adapter_without_invented_scalar(self):
        plan = self.plan("A06")
        self.assertEqual(len(plan["requests"]), 1)
        self.assertEqual(plan["requests"][0]["backend"], "native")
        request = plan["requests"][0]["request"]
        self.assertEqual(request["byte_span"], [2, 3])
        output = checker.worker(request)
        checker.validate_native(request, output)
        self.assertFalse(output["span_valid"])
        output["error"] = "UNRELATED_IMPORT_FAILURE"
        with self.assertRaises(ValueError):
            checker.validate_native(request, output)

    def test_noncontiguous_radicals_use_complete_host_and_independent_fibers(self):
        request = self.request("A01")
        meta = request["node"]["metadata"]
        value = checker.host_value(meta["host_tree"], request["inventory"])
        self.assertEqual("".join(value["raw"]), "مَكْتُوب")
        self.assertEqual(len(meta["morphology"]["alignment"]), 8)
        self.assertTrue(checker.bridge_oracle(request)["source_bound"])
        self.assertFalse(checker.bridge_oracle(self.request("A02"))["source_bound"])

    def test_repeated_middle_radical_keeps_four_occurrences_and_three_slots(self):
        request = self.request("A03")
        morph = request["node"]["metadata"]["morphology"]
        self.assertEqual(morph["reading"]["arity"], 3)
        self.assertEqual([row["source_position"] for row in morph["alignment"]
                          if row["origin"] == {"kind": "radical", "index": 1}], [2, 4])
        self.assertTrue(checker.bridge_oracle(request)["source_bound"])

    def test_alias_revision_literal_and_boundary_errors_remain_distinct_inputs(self):
        for case_id in ("A08", "A09", "A10", "A11", "A14"):
            with self.subTest(case_id=case_id):
                self.assertFalse(checker.bridge_oracle(self.request(case_id))["source_bound"])
        self.assertEqual(self.request("A09")["node"]["metadata"]["morphology"]["alignment"][-1]["source_position"], 4)
        self.assertEqual(self.request("A11")["node"]["metadata"]["source"]["revision"], 2)
        self.assertEqual(self.request("A11")["inventory"][0]["revision"], 1)

    def test_no_implicit_alphabet_map_for_opaque_ledger_radicals(self):
        request = self.request("W01")
        root = request["node"]["child"]["seed"]["radicals"]
        self.assertEqual(root, [0, 1, 2])
        self.assertEqual(request["node"]["metadata"]["morphology"]["reading"]["root"], list("كتب"))
        self.assertFalse(checker.bridge_oracle(request)["source_bound"])
        output = bridge_output(request)
        observed = checker.observations(self.plan("W01"), [output])
        self.assertEqual(observed, {})
        self.assertTrue(all(row["status"] == "UNMEASURED" for row in checker.score_assertions(self.case("W01")["expected"], observed)))

    def test_missing_role_or_inverse_inputs_do_not_receive_fabricated_receipts(self):
        for case_id in ("W02", "W03", "W04", "W05", "W06", "W07", "W08", "U01", "U02", "U03", "R02", "R03"):
            with self.subTest(case_id=case_id):
                self.assertEqual(self.plan(case_id)["requests"], [])

    def test_same_registry_number_and_different_registry_version_stay_separate(self):
        plan = self.plan("I04")
        left, right = (item["request"] for item in plan["requests"])
        self.assertEqual(left["tree"], right["tree"])
        self.assertNotEqual(left["registry_id"], right["registry_id"])

    def test_zero_is_a_valid_canonical_structural_number(self):
        request, output = zero_number()
        checker.validate_lean(request, output)
        for broken in (0, False, 0.0, "00", "+0", " 0", "0.0"):
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                checker.validate_lean(request, {**output, "number": broken})

    def test_fixed_small_cantor_examples_are_independent_of_probe_outputs(self):
        leaf = {"op": "leaf", "seed": {"kind": "lexical", "entry": 0}}
        self.assertEqual(checker.structural_number(leaf), 6)
        self.assertEqual(checker.structural_number({"op": "unary", "rule": 0, "child": leaf}), 82)
        self.assertEqual(checker.structural_number({"op": "binary", "rule": 1, "left": leaf, "right": leaf}), 11219)

    def test_boolean_integer_and_float_substitution_fail_strict_scoring(self):
        rows = checker.score_assertions({"bool": False, "count": 1, "nested": [False]},
                                        {"bool": 0, "count": True, "nested": [0]})
        self.assertEqual([row["status"] for row in rows], ["FAIL"] * 3)
        self.assertEqual(checker.score_assertions({"count": 1}, {"count": 1.0})[0]["status"], "FAIL")

    def test_no_implicit_default_false_for_missing_output(self):
        rows = checker.score_assertions({"licensed": False}, {})
        self.assertEqual(rows[0]["status"], "UNMEASURED")
        self.assertNotIn("actual", rows[0])

    def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(self):
        for value in ('{"status":"OK","status":"ERROR"}', '{"n":NaN}', '{"n":Infinity}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                checker.parse(value)

    def test_core_scope_and_every_typed_claim_are_checked(self):
        request, output = zero_number()
        changes = ({"conditional": 1}, {"grammar_certified": True}, {"acquisition_measured": True},
                   {"structural_only": False}, {"linguistically_licensed": True}, {"nodes": True},
                   {"height": 0.0}, {"number_domain": "foreign"}, {"estimated_max_number_bits": False})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                checker.validate_lean(request, {**deepcopy(output), **change})

    def test_out_of_envelope_license_claim_cannot_hide_beside_false_flags(self):
        request, output = zero_number()
        with self.assertRaisesRegex(ValueError, "Undeclared output fields"):
            checker.validate_lean(request, {**output, "licensed": True})
        request = self.request("A01")
        output = bridge_output(request)
        with self.assertRaises(ValueError):
            checker.validate_lean(request, {**output, "necessary": True})
        request, output = one_enumeration()
        output["inventory"]["licensed"] = True
        with self.assertRaises(ValueError):
            checker.validate_lean(request, output)

    def test_ordered_children_and_full_metadata_echo_cannot_be_replaced(self):
        request = self.request("A01")
        output = bridge_output(request)
        output["node"]["metadata"]["section"] = "noun"
        with self.assertRaises(ValueError):
            checker.validate_lean(request, output)
        request, output = zero_number()
        output["tree"]["seed"]["radicals"] = [False, 0, 0]
        with self.assertRaises(ValueError):
            checker.validate_lean(request, output)

    def test_invalid_binding_cannot_become_coherently_flagged_license(self):
        request = self.request("A09")
        output = bridge_output(request)
        output.update(verdict="CONDITIONALLY_LICENSED", source_bound=True, conditional_licensed=True,
                      all_premises=True, negative=False, linguistic_ready=True)
        for step in output["steps"]:
            step.update(source_bound=True, positive_complete=True, missing_requirements=[])
        with self.assertRaises(ValueError):
            checker.validate_lean(request, output)

    def native_interpreted_request(self):
        request = self.request("A01")
        node = request["node"]
        node["metadata"]["provenance"] = "native_tree"
        node["metadata"]["unresolved"] = []
        node["metadata"]["required"] = [3]
        support = {"source": deepcopy(node["metadata"]["source"]), "span": deepcopy(node["metadata"]["host"])}
        request["interpreted"] = [{"target": deepcopy(node), "requirement": req, "positive": True,
                                   "witness_id": 10 + req, "supports": [support]} for req in (0, 3)]
        request["offered"] = deepcopy(request["interpreted"])
        return request

    def test_hidden_negative_is_independently_closed_over_interpreted_ledger(self):
        request = self.native_interpreted_request()
        negative = {**deepcopy(request["interpreted"][1]), "positive": False, "witness_id": 99}
        request["interpreted"].append(negative)
        output = bridge_output(request)
        self.assertEqual(output["verdict"], "REJECTED")
        checker.validate_lean(request, output)
        output.update(verdict="CONDITIONALLY_LICENSED", conditional_licensed=True, negative=False)
        output["steps"][0].update(negative=False, known_negative_witness_ids=[])
        with self.assertRaises(ValueError):
            checker.validate_lean(request, output)

    def test_withdrawn_receipt_cannot_survive_in_offered_cache(self):
        request = self.native_interpreted_request()
        self.assertEqual(checker.bridge_oracle(request)["verdict"], "CONDITIONALLY_LICENSED")
        stale = bridge_output(request)
        request["interpreted"] = request["interpreted"][:1]
        self.assertEqual(checker.bridge_oracle(request)["verdict"], "UNKNOWN")
        with self.assertRaises(ValueError):
            checker.validate_lean(request, stale)

    def test_foreign_full_node_identity_cannot_reuse_a_matching_number_receipt(self):
        request = self.native_interpreted_request()
        request["node"]["metadata"]["reading_id"] = "foreign.reading"
        self.assertEqual(checker.bridge_oracle(request)["verdict"], "UNKNOWN")

    def test_substitution_and_lift_entry_conditions_are_checked(self):
        request = self.request("A01")
        meta = request["node"]["metadata"]
        raw = checker.host_value(meta["host_tree"], request["inventory"])["raw"]
        meta["host_tree"] = {"op": "substitute", "tag": deepcopy(checker.TAG),
                             "replacement": raw, "child": meta["host_tree"]}
        self.assertFalse(checker.bridge_oracle(request)["source_bound"])
        meta["host_tree"]["replacement"] = []
        self.assertTrue(checker.bridge_oracle(request)["source_bound"])
        meta["host_tree"] = {"op": "lift", "tag": deepcopy(checker.TAG), "child": meta["host_tree"]}
        self.assertFalse(checker.bridge_oracle(request)["source_bound"])

    def test_thirteen_term_authored_enumeration_has_exact_shapes(self):
        request = self.request("E02")
        terms = list(checker.enumeration_universe(request["inventory"], 2).values())
        self.assertEqual(len(terms), 13)
        self.assertEqual(sum(t["op"] == "leaf" for t in terms), 1)
        self.assertEqual(sum(t["op"] == "unary" for t in terms), 3)
        self.assertEqual(sum(t["op"] == "binary" for t in terms), 9)
        self.assertEqual(len({checker.structural_number(t) for t in terms}), 13)

    def test_normalized_enumeration_does_not_claim_raw_duplicate_count(self):
        plan = self.plan("E03")
        self.assertEqual(len(plan["requests"][0]["request"]["inventory"]["seeds"]), 2)
        request, output = one_enumeration()
        request["inventory"]["seeds"].append(deepcopy(request["inventory"]["seeds"][0]))
        output["removed_duplicate_seeds"] = 1
        checker.validate_lean(request, output)
        self.assertNotIn("raw_kernel_count", checker.observations(plan, [output]))

    def test_duplicated_or_incomplete_candidates_fail_even_with_selfconsistent_counts(self):
        request, output = one_enumeration()
        checker.validate_lean(request, output)
        output["candidates"].append(deepcopy(output["candidates"][0]))
        output["candidate_count"] = 2
        with self.assertRaises(ValueError):
            checker.validate_lean(request, output)
        request, output = one_enumeration()
        output["candidates"] = []
        output["candidate_count"] = 0
        with self.assertRaisesRegex(ValueError, "Incomplete structural set"):
            checker.validate_lean(request, output)

    def test_forged_exhaustion_and_exhaustion_as_rejection_are_rejected(self):
        request, _ = one_enumeration()
        output = envelope("core_enumerate", enumeration="EXHAUSTED", search_complete=False,
                          linguistic_rejection=False, registry_id=request["registry_id"], height=2,
                          candidate_budget=20, required_candidates_at_least=21, candidates=[])
        with self.assertRaisesRegex(ValueError, "finite universe fits"):
            checker.validate_lean(request, output)
        request = self.request("E05")
        output.update(registry_id=request["registry_id"], candidate_budget=2, required_candidates_at_least=3)
        checker.validate_lean(request, output)
        for change in ({"search_complete": True}, {"linguistic_rejection": True}, {"grammar_certified": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                checker.validate_lean(request, {**output, **change})

    def test_actual_python_transport_ambiguity_is_measured_from_returned_forest(self):
        plan = self.plan("A12")
        requests = plan["requests"]
        responses = [bridge_output(item["request"]) if item["backend"] == "lean" else checker.worker(item["request"])
                     for item in requests]
        for item, response in zip(requests, responses):
            (checker.validate_lean if item["backend"] == "lean" else checker.validate_native)(item["request"], response)
        observed = checker.observations(plan, responses)
        self.assertEqual(observed["retained_alternatives"], 2)
        self.assertFalse(observed["unique_analysis"])

    def test_native_rehashing_does_not_hide_a_grammar_flag_or_changed_source(self):
        request = next(item["request"] for item in self.plan("A01")["requests"] if item["backend"] == "native")
        output = checker.worker(request)
        checker.validate_native(request, output)
        output["morphology_nodes"][0]["section"] = "noun"
        node = output["morphology_nodes"][0]
        node["node_id"] = sha256(checker.canonical({k: v for k, v in node.items() if k != "node_id"}).encode()).hexdigest()
        output["report_id"] = sha256(checker.canonical({k: v for k, v in output.items() if k != "report_id"}).encode()).hexdigest()
        with self.assertRaises(ValueError):
            checker.validate_native(request, output)

    def test_native_combining_order_is_exact_not_normalized(self):
        plan = self.plan("A13")
        responses = [checker.worker(item["request"]) for item in plan["requests"]]
        observed = checker.observations(plan, responses)
        self.assertEqual(observed, {"same_original_bytes": False, "source_identity_equal": False,
                                    "normalization_grants_identity": False})

    def test_response_integrity_failure_cannot_silently_become_only_unmeasured(self):
        case = self.case("I01")
        material = {"cases": [case], "fixtures": self.material["fixtures"]}
        plan = {"case_id": case["case_id"], **self.plan("I01")}
        result = checker.score_measurement(material, [plan], [[{"status": "OK"}, {"status": "OK"}]])
        self.assertEqual(result["cases"][0]["status"], "FAIL")
        self.assertEqual(result["summary"]["response_integrity_errors"], 2)
        self.assertFalse(result["summary"]["measured_contract_gate"])

    def test_replay_uses_relocated_repository_artifacts_without_running_production(self):
        with tempfile.TemporaryDirectory() as folder:
            old_root = Path(folder) / "old"
            old_root.mkdir()
            new_root = Path(folder) / "new"
            seed = {"kind": "leaf", "seed": {"kind": "root3", "values": [0, 0, 0]}}
            case = {"case_id": "development.replay", "group": "checker", "operation": "compare_tree_identity",
                    "input": {"left": seed, "right": seed, "registry_left": ["development", 1], "registry_right": ["development", 1]},
                    "expected": {"same_structural_number": True}}
            material = {"cases": [case], "fixtures": {}}
            plans = checker.build_plans(material)
            requests = [item["request"] for item in plans[0]["requests"]]
            outputs = []
            for request in requests:
                _, out = zero_number()
                out["registry_id"] = request["registry_id"]
                outputs.append(out)
            with patch.object(checker, "ROOT", old_root):
                paths = {key: old_root / (key + ".jsonl") for key in ("stdin", "stdout", "stderr")}
                paths["stdin"].write_text("".join(checker.canonical(r) + "\n" for r in requests))
                paths["stdout"].write_text("".join(checker.canonical(r) + "\n" for r in outputs))
                paths["stderr"].write_text("")
                archive = old_root / "sources.tar.gz"
                with tarfile.open(archive, "w:gz"):
                    pass
                record = {"schema": checker.SCHEMA, "material": {"sha256": checker.MATERIAL_SHA},
                          "source_archive": checker.file_ref(archive), "source_files_before": [], "source_files_after": [],
                          "probe_before": {"sha256": "development-only"}, "probe_after": {"sha256": "development-only"},
                          "sources_stable_during_run": True, "plans": plans,
                          "measurement": checker.score_measurement(material, plans, [outputs]),
                          "backends": {"lean": {"positions": [[0, 0], [0, 1]],
                                                **{key: checker.file_ref(path) for key, path in paths.items()}}}}
                checker.write_json(old_root / "run.json", record)
            shutil.copytree(old_root, new_root)
            shutil.rmtree(old_root)
            with patch.object(checker, "ROOT", new_root), patch.object(checker, "load_material", return_value=material), \
                    patch.object(checker.subprocess, "run", side_effect=AssertionError("Replay must not execute a probe")):
                result = checker.replay(new_root / "run.json", new_root / "audit.json")
            self.assertTrue(result["scores_reproduced"])
            self.assertFalse(result["probe_executed"])

    def test_replay_repository_paths_cannot_escape_or_bypass_content_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "repo"
            root.mkdir()
            outside = Path(folder) / "outside.json"
            outside.write_text("{}")
            with patch.object(checker, "ROOT", root):
                reference = checker.file_ref(outside)
                for path in ("../outside.json", str(outside)):
                    with self.subTest(path=path), self.assertRaises(ValueError):
                        checker.resolve_ref({**reference, "repository_path": path})
                with self.assertRaises(ValueError):
                    checker.resolve_ref({**reference, "sha256": "0" * 64})


if __name__ == "__main__":
    unittest.main()
