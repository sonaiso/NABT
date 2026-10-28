"""Independent examples and adversarial metadata, not linguistic acceptance gold."""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from tools.entropy_framework import (FrameworkError, load_json, measure_candidates,
                                     report_registry, validate_registry)
from tools.entropy_framework.__main__ import main
from tools.entropy_framework.registry import (DEFAULT_REGISTRY, MAX_JSON_BYTES,
                                             MAX_INTEGER_DIGITS, FrameworkResourceError)


def ledger():
    return {
        "schema": "nabt.candidate-ledger.v1",
        "frame": {
            "domain_id": "test-finite-readings.v1", "element_type": "reading-id",
            "equivalence_version": "exact-test-id.v1", "unit": "distinct reading",
            "source_binding": {"source_id": "synthetic-example", "sha256": "0" * 64,
                               "span_bytes": [0, 20]},
            "law_version": "test-law.v1", "grammar_version": "test-grammar.v1",
            "lexicon_version": "test-lexicon.v1", "convention": "explicit-test-convention",
            "context_version": "test-context.v1", "evidence_revision": "test-evidence.v1",
            "enumeration_bounds": {"max_nodes": 12},
        },
        "enumeration_status": "DECLARED_COMPLETE",
        "candidates": [
            {"id": "reading-a", "state": "licensed"},
            {"id": "reading-b", "state": "pending"},
            {"id": "reading-c", "state": "refuted"},
        ],
    }


def registry():
    return load_json(DEFAULT_REGISTRY)


def declared_pass():
    """Invented, self-consistent claims: deliberately no real proof or run."""
    value = registry()
    gate = value["gates"][0]
    gate["dataset"] = {"status": "frozen", "unit": "synthetic-check", "size": 1,
                       "version": "test-suite.v1", "sha256": "a" * 64}
    gate["status"] = "PASS"
    gate["evidence_ids"] = ["invented-evidence"]
    value["evidence_records"] = [{
        "id": "invented-evidence", "gate_id": gate["id"], "scope": gate["scope"],
        "reported_outcome": "PASS", "reference": "not-a-real-run.json",
        "run_identity": {
            "code_commit": "b" * 40, "toolchain": "test-toolchain",
            "suite_version": "test-suite.v1", "evaluator_version": "test-evaluator.v1",
            "dataset_sha256": "a" * 64, "gold_sha256": "c" * 64,
            "evaluator_sha256": "d" * 64,
        },
        "required_checks": {"passed": 1, "failed": 0, "skipped": 0, "missing": 0},
    }]
    return value


class FiniteCandidateMeasurements(unittest.TestCase):
    def test_pending_reading_survives_and_is_counted(self):
        result = measure_candidates(ledger())
        self.assertEqual(result["ledger_counts"],
                         {"total": 3, "licensed": 1, "pending": 1, "refuted": 1, "remaining": 2})
        self.assertEqual(result["remaining_ids"], ["reading-a", "reading-b"])
        self.assertEqual(result["ledger_hartley_bits"], 1.0)

    def test_four_declared_identities_have_two_bits(self):
        value = ledger()
        value["candidates"] = [{"id": i, "state": "pending"} for i in ["00", "01", "10", "11"]]
        self.assertEqual(measure_candidates(value)["ledger_hartley_bits"], 2.0)

    def test_singleton_has_zero_bits_but_no_linguistic_or_world_authority(self):
        value = ledger()
        value["candidates"] = [{"id": "only-authored-id", "state": "licensed"}]
        result = measure_candidates(value)
        self.assertEqual(result["ledger_hartley_bits"], 0.0)
        self.assertEqual(result["semantic_authority"], "NONE")
        self.assertFalse(result["candidate_states_verified"])
        self.assertFalse(result["identity_contract_verified"])

    def test_empty_is_not_zero_entropy_or_consensus(self):
        value = ledger()
        value["candidates"] = []
        result = measure_candidates(value)
        self.assertEqual(result["ledger_counts"]["remaining"], 0)
        self.assertIsNone(result["ledger_hartley_bits"])
        self.assertEqual(result["null_reason"], "EMPTY_REMAINING_LEDGER")
        self.assertFalse(result["linguistic_completeness_verified"])

    def test_all_declared_refuted_is_not_a_language_rejection(self):
        value = ledger()
        value["candidates"] = [{"id": "r", "state": "refuted"}]
        result = measure_candidates(value)
        self.assertIsNone(result["ledger_hartley_bits"])
        self.assertEqual(result["authority"], "COUNTED_SUPPLIED_LEDGER")
        self.assertFalse(result["candidate_states_verified"])

    def test_complete_partial_and_exhausted_claims_never_verify_completeness(self):
        for status in ("DECLARED_COMPLETE", "PARTIAL", "RESOURCE_LIMIT"):
            value = ledger()
            value["enumeration_status"] = status
            result = measure_candidates(value)
            self.assertEqual(result["declared_enumeration_status"], status)
            self.assertFalse(result["linguistic_completeness_verified"])
            self.assertEqual(result["count_mode"], "EXACT_FOR_SUPPLIED_LEDGER")

    def test_duplicate_identity_is_rejected_instead_of_overwritten(self):
        value = ledger()
        value["candidates"].append({"id": "reading-b", "state": "licensed"})
        with self.assertRaisesRegex(FrameworkError, "duplicate candidate"):
            measure_candidates(value)

    def test_hash_and_span_do_not_authenticate_source(self):
        result = measure_candidates(ledger())
        self.assertFalse(result["source_binding_verified"])

    def test_every_frame_dimension_is_required(self):
        for key in ledger()["frame"]:
            value = ledger()
            del value["frame"][key]
            with self.subTest(key=key), self.assertRaises(FrameworkError):
                measure_candidates(value)

    def test_boolean_is_not_a_count_or_position(self):
        for field in ("bound", "position"):
            value = ledger()
            if field == "bound":
                value["frame"]["enumeration_bounds"]["max_nodes"] = True
            else:
                value["frame"]["source_binding"]["span_bytes"][0] = False
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                measure_candidates(value)

    def test_reversed_span_and_noncanonical_hash_are_rejected(self):
        value = ledger()
        value["frame"]["source_binding"]["span_bytes"] = [21, 20]
        with self.assertRaises(FrameworkError):
            measure_candidates(value)
        value = ledger()
        value["frame"]["source_binding"]["sha256"] = "A" * 64
        with self.assertRaises(FrameworkError):
            measure_candidates(value)

    def test_invalid_state_and_unrecognized_completeness_field_are_rejected(self):
        value = ledger()
        value["candidates"][0]["state"] = "verified_by_hash"
        with self.assertRaises(FrameworkError):
            measure_candidates(value)
        value = ledger()
        value["all_arabic_complete"] = True
        with self.assertRaises(FrameworkError):
            measure_candidates(value)

    def test_unhashable_status_is_a_diagnostic_not_a_type_error(self):
        value = ledger()
        value["enumeration_status"] = []
        with self.assertRaises(FrameworkError):
            measure_candidates(value)

    def test_order_permutation_preserves_counts_without_losing_ids(self):
        left = measure_candidates(ledger())
        value = ledger()
        value["candidates"].reverse()
        right = measure_candidates(value)
        self.assertEqual(left["ledger_counts"], right["ledger_counts"])
        self.assertEqual(set(left["remaining_ids"]), set(right["remaining_ids"]))


class RegistryContracts(unittest.TestCase):
    def test_current_plan_reconciles_v3_without_claiming_target_measurement(self):
        value = registry()
        result = validate_registry(value)
        self.assertEqual(value["baseline"]["nabt_commit"], "b7442580e7e681a68a85f40bc247be8ee286e7e3")
        self.assertEqual(result["gates"], 7)
        self.assertEqual(result["tasks"], 18)
        self.assertTrue(all(g["status"] == "NOT_MEASURED" for g in value["gates"]))
        for g in value["gates"]:
            self.assertIsNone(g["baseline"])
        g1 = next(g for g in value["gates"] if g["id"] == "G1")
        self.assertEqual(g1["dataset"]["status"], "frozen")
        self.assertEqual(g1["dataset"]["positive_distinct_frames"], 50)
        self.assertEqual(value["development_checkpoints"]["independent_gold_commit"],
                         "7ca87dcda09427641ad346fa1108eb2c87382f22")
        self.assertFalse(value["development_checkpoints"]["evaluation_started"])
        self.assertFalse(result["evidence_verified"])

    def test_scoped_run_does_not_close_global_gates_or_rewrite_baseline(self):
        value = registry()
        original_baseline = copy.deepcopy(value["baseline"])
        cap = value["capabilities"][0]
        evidence = declared_pass()["evidence_records"][0]
        evidence["gate_id"] = cap["gate_id"]
        evidence["scope"] = cap["scope"]
        dataset = next(g["dataset"] for g in value["gates"] if g["id"] == cap["gate_id"])
        evidence["run_identity"]["dataset_sha256"] = dataset["sha256"]
        evidence["run_identity"]["suite_version"] = dataset["version"]
        value["evidence_records"] = [evidence]
        cap["state"] = "EVALUATED"
        cap["evidence_ids"] = [evidence["id"]]
        report = report_registry(value)
        self.assertEqual(report["baseline"], original_baseline)
        self.assertTrue(all(g["reported_status"] == "NOT_MEASURED" for g in report["gates"]))
        self.assertEqual(report["scoped_capabilities"][0]["state"], "EVALUATED")
        self.assertEqual(report["scoped_capabilities"][0]["parent_gate_admission"], "NOT_EVALUATED")
        self.assertFalse(report["scoped_capabilities"][0]["evidence_verified"])

    def test_order_respects_all_dependency_edges(self):
        value = registry()
        result = validate_registry(value)
        for kind, key in (("tasks", "task_order"), ("gates", "gate_order")):
            positions = {i: n for n, i in enumerate(result[key])}
            for row in value[kind]:
                for dependency in row["depends_on"]:
                    self.assertLess(positions[dependency], positions[row["id"]])

    def test_duplicate_ids_and_references_are_rejected(self):
        for kind in ("roles", "layers", "gates", "tasks"):
            value = registry()
            value[kind].append(copy.deepcopy(value[kind][0]))
            with self.subTest(kind=kind), self.assertRaisesRegex(FrameworkError, "duplicate id"):
                validate_registry(value)

    def test_unknown_dependency_and_cycle_are_rejected(self):
        for kind in ("tasks", "gates"):
            value = registry()
            value[kind][0]["depends_on"] = ["not-registered"]
            with self.subTest(kind=kind), self.assertRaises(FrameworkError):
                validate_registry(value)
            value = registry()
            a, b = value[kind][:2]
            a["depends_on"] = [b["id"]]
            b["depends_on"] = [a["id"]]
            with self.assertRaisesRegex(FrameworkError, "cycle"):
                validate_registry(value)

    def test_population_denominators_and_pair_units_are_checked(self):
        for field in ("slice", "pair", "boolean"):
            value = registry()
            if field == "slice":
                value["gates"][2]["dataset"]["slices"]["positive_in_scope"] = 99
            elif field == "pair":
                value["gates"][4]["dataset"]["individual_inputs"] = 80
            else:
                value["gates"][2]["dataset"]["size"] = True
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                validate_registry(value)

    def test_owner_review_separation_and_reference_integrity(self):
        value = registry()
        value["tasks"][0]["reviewer_role"] = value["tasks"][0]["owner_role"]
        with self.assertRaises(FrameworkError):
            validate_registry(value)
        value = registry()
        value["tasks"][0]["evidence_ids"] = ["missing"]
        with self.assertRaises(FrameworkError):
            validate_registry(value)

    def test_delivered_code_does_not_mark_gate_passed(self):
        value = registry()
        value["tasks"][0]["work_status"] = "DELIVERED"
        report = report_registry(value)
        self.assertEqual(report["tasks"][0]["work_status"], "DELIVERED")
        self.assertEqual(report["gates"][0]["reported_status"], "NOT_MEASURED")
        self.assertEqual(report["release_admission"], "NOT_EVALUATED")

    def test_consistent_but_invented_pass_is_still_not_verified(self):
        report = report_registry(declared_pass())
        gate = next(g for g in report["gates"] if g["id"] == "G0")
        self.assertEqual(gate["reported_status"], "PASS")
        self.assertEqual(gate["verification_status"], "NOT_PERFORMED")
        self.assertFalse(report["evidence_verified"])
        self.assertEqual(report["semantic_authority"], "NONE")
        self.assertEqual(report["release_admission"], "NOT_EVALUATED")

    def test_pass_requires_frozen_nonempty_data_and_zero_required_skips(self):
        for field in ("draft", "empty", "skipped", "missing", "failed"):
            value = declared_pass()
            if field == "draft":
                value["gates"][0]["dataset"]["status"] = "draft"
            elif field == "empty":
                value["evidence_records"][0]["required_checks"]["passed"] = 0
            else:
                value["evidence_records"][0]["required_checks"][field] = 1
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                validate_registry(value)

    def test_cannot_borrow_evidence_from_another_scope_or_suite(self):
        for field in ("scope", "suite_version", "dataset_sha256"):
            value = declared_pass()
            evidence = value["evidence_records"][0]
            if field == "scope":
                evidence[field] = "other-scope"
            else:
                evidence["run_identity"][field] = "e" * 64 if field.endswith("sha256") else "other.v1"
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                validate_registry(value)

    def test_unmeasured_target_cannot_take_old_diagnostic_baseline(self):
        value = registry()
        value["gates"][2]["baseline"] = {"reading_correct": 1, "cases": 25}
        with self.assertRaises(FrameworkError):
            validate_registry(value)

    def test_nabt_release_independence_is_enforced_in_registry_contract(self):
        value = registry()
        value["release_policy"]["nabt_depends_on_mashru_release"] = True
        with self.assertRaises(FrameworkError):
            validate_registry(value)

    def test_unknown_state_and_unhashable_role_are_diagnostics(self):
        for field in ("status", "owner"):
            value = registry()
            if field == "status":
                value["gates"][0]["status"] = []
            else:
                value["tasks"][0]["owner_role"] = []
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                validate_registry(value)


class StrictJSONAndCLI(unittest.TestCase):
    def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            for raw in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'):
                path.write_text(raw)
                with self.subTest(raw=raw), self.assertRaises(FrameworkError):
                    load_json(path)

    def test_escaped_surrogates_are_rejected_in_values_and_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            for raw in ('{"name":"\\ud800"}', '{"\\udfff":1}', '{"extra":["\\ud800"]}'):
                path.write_text(raw)
                with self.subTest(raw=raw), self.assertRaises(FrameworkError):
                    load_json(path)
            path.write_text('{"name":"\\ud83d\\ude00\\n"}')
            self.assertEqual(load_json(path), {"name": "😀\n"})

    def test_declared_input_size_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            path.write_bytes(b" " * (MAX_JSON_BYTES + 1))
            with self.assertRaisesRegex(FrameworkResourceError, "8 MiB"):
                load_json(path)

    def test_integer_budget_preserves_supported_large_integers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            for sign in ("", "-"):
                path.write_text('{"n":' + sign + "9" * MAX_INTEGER_DIGITS + "}")
                self.assertIs(type(load_json(path)["n"]), int)
            path.write_text('{"n":' + "9" * (MAX_INTEGER_DIGITS + 1) + "}")
            with self.assertRaises(FrameworkResourceError):
                load_json(path)

    def test_cli_resource_budgets_do_not_become_invalid_or_linguistic_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            for raw in ('{"n":' + "9" * 5000 + "}", " " * (MAX_JSON_BYTES + 1)):
                path.write_text(raw)
                output = StringIO()
                with redirect_stdout(output):
                    code = main(["measure", str(path)])
                report = json.loads(output.getvalue())
                self.assertEqual(code, 3)
                self.assertEqual(report["status"], "RESOURCE_EXHAUSTED")
                self.assertEqual(report["semantic_authority"], "NONE")

    def test_duplicate_surrogate_error_is_itself_scalar_utf8(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            path.write_text('{"\\ud800":1,"\\ud800":2}')
            output = StringIO()
            with redirect_stdout(output):
                code = main(["measure", str(path)])
            encoded = output.getvalue().encode("utf-8", "strict")
            report = json.loads(encoded)
            report["reason"].encode("utf-8", "strict")
            self.assertEqual(code, 2)
            self.assertEqual(report["status"], "INVALID_INPUT")

    def test_cli_success_describes_tool_execution_only(self):
        for command in ("validate", "report"):
            output = StringIO()
            with redirect_stdout(output):
                code = main([command])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())["semantic_authority"], "NONE")

    def test_cli_measure_and_invalid_input_have_distinct_exit_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            path.write_text(json.dumps(ledger()))
            output = StringIO()
            with redirect_stdout(output):
                code = main(["measure", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())["ledger_counts"]["remaining"], 2)
            path.write_text('{"broken":')
            output = StringIO()
            with redirect_stdout(output):
                code = main(["measure", str(path)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
