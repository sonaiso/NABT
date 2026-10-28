"""Independent examples and adversarial metadata, not linguistic acceptance gold."""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
from io import StringIO
import hashlib
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


def row(value, kind, identity):
    return next(item for item in value[kind] if item["id"] == identity)


def declared_pass(gate_id="G0", value=None):
    """Invented, self-consistent claims: deliberately no real proof or run."""
    value = registry() if value is None else value
    gate = row(value, "gates", gate_id)
    if gate["dataset"]["status"] != "frozen":
        gate["dataset"] = {"status": "frozen", "unit": "synthetic-check", "size": 1,
                           "version": "test-suite.v1", "sha256": "a" * 64}
    identity = f"invented-{gate_id}"
    gate["measurement"] = {
        "state": "MEASURED", "reported_outcome": "PASS", "reason": None,
        "evidence_ids": [identity, *gate["measurement"]["evidence_ids"]],
    }
    value["evidence_records"].insert(0, {
        "id": identity, "gate_id": gate["id"], "scope": gate["scope"],
        "reported_outcome": "PASS", "reference": "not-a-real-run.json",
        "run_identity": {
            "code_commit": "b" * 40, "toolchain": "test-toolchain",
            "suite_version": gate["dataset"]["version"], "evaluator_version": "test-evaluator.v1",
            "dataset_sha256": gate["dataset"]["sha256"], "gold_sha256": "c" * 64,
            "evaluator_sha256": "d" * 64,
        },
        "required_checks": {"passed": 1, "failed": 0, "skipped": 0, "missing": 0},
    })
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
    def test_current_plan_preserves_baseline_and_records_scoped_measurement(self):
        value = registry()
        result = validate_registry(value)
        self.assertEqual(result["schema"], "nabt.entropy-framework.validation.v2")
        self.assertEqual(value["baseline"]["nabt_commit"], "b7442580e7e681a68a85f40bc247be8ee286e7e3")
        self.assertEqual(result["gates"], 7)
        self.assertEqual(result["tasks"], 25)
        g1 = row(value, "gates", "G1")
        self.assertEqual(g1["measurement"]["state"], "MEASURED")
        self.assertEqual(g1["measurement"]["reported_outcome"], "PASS")
        self.assertEqual(g1["dataset"]["positive_distinct_frames"], 50)
        cap = row(value, "capabilities", "productive-clause-v1")
        self.assertEqual(cap["state"], "EVALUATED")
        measured = row(value, "evidence_records", cap["evidence_ids"][0])
        self.assertEqual(measured["phase"], "exposed")
        self.assertEqual(measured["run_identity"]["code_commit"],
                         "c694a5ae1e8ad851fd1aaded6ab6c00b0aea3623")
        self.assertEqual(measured["reported_measurements"]["syntax_contracts"],
                         {"correct": 200, "total": 200})
        self.assertEqual(measured["required_checks"],
                         {"passed": 9, "failed": 0, "skipped": 0, "missing": 0})
        self.assertFalse(result["evidence_verified"])

    def test_historical_baseline_and_evidence_objects_are_unchanged(self):
        # Fixed digests of the parsed objects at c2c072e, independent of v2 logic.
        value = registry()
        cap = row(value, "capabilities", "productive-clause-v1")
        historical = [row(value, "evidence_records", cap["evidence_ids"][0])]
        for obj, expected in (
            (value["baseline"], "3d6a9c189cfd19090d5c335797d5a38ed325e18296ca499522e03d4411d33358"),
            (historical, "d5625a6e345132ef27f0a7504f9790a31104a926c9358fb6d232d234a1aa29c2"),
        ):
            raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
        migration = value["migration"]
        self.assertEqual(migration["source_commit"], "c2c072e17802b62c13109cee7c087b7b58895a1a")
        self.assertEqual(migration["source_sha256"],
                         "09ad43d5602e5f00fa3ea50b8bae89dbea2aa064b77a604dea1a80a910a8c8bb")
        self.assertEqual(migration["previous_g4_proposal"]["dataset"]["status"], "not_created")

    def test_frozen_lifecycle_population_is_not_a_run(self):
        value = registry()
        g4 = row(value, "gates", "G4")
        self.assertEqual(g4["scope"], "nabt.evidence-lifecycle.v1")
        self.assertEqual(g4["dataset"]["status"], "frozen")
        self.assertEqual(g4["dataset"]["size"], 40)
        self.assertEqual(g4["dataset"]["frozen_commit"], "1295da3349b50190dc6f68606f918054e7bbfdf2")
        self.assertEqual(g4["dataset"]["sha256"],
                         "04609a848ddd4336d600253997b0d79523b28f6475be47f064845769083486be")
        self.assertEqual(g4["dataset"]["additional_denominators"],
                         {"episode_steps": 79, "verification_pairs": 73,
                          "separate_historical_prefix_steps": 7})
        self.assertEqual(g4["measurement"]["state"], "NOT_MEASURED")
        self.assertEqual(g4["measurement"]["evidence_ids"], [])
        self.assertEqual(row(value, "capabilities", "evidence-lifecycle-v1")["state"], "IMPLEMENTED_AWAITING_EVALUATION")
        self.assertNotEqual(row(value, "tasks", "T16-LC1")["work_status"], "DELIVERED")

    def test_scoped_measurement_and_blocked_admission_are_separate(self):
        value = registry()
        original = copy.deepcopy(value)
        report = report_registry(value)
        gate = row(report, "gates", "G1")
        self.assertEqual(gate["measurement"]["reported_outcome"], "PASS")
        self.assertEqual(gate["admission"], {
            "readiness": "BLOCKED_DEPENDENCIES", "blockers": ["G0", "GM"],
            "decision": "NOT_EVALUATED", "evidence_verified": False,
        })
        cap = row(report, "scoped_capabilities", "productive-clause-v1")
        self.assertEqual(cap["measurement"], gate["measurement"])
        self.assertEqual(cap["admission"], gate["admission"])
        self.assertEqual(report["baseline"], original["baseline"])
        self.assertEqual(value, original)  # Reporting itself is read-only.

    def test_synthetic_lifecycle_result_does_not_admit_other_goals(self):
        value = declared_pass("G4")
        cap = row(value, "capabilities", "evidence-lifecycle-v1")
        cap["state"] = "EVALUATED"
        cap["evidence_ids"] = ["invented-G4"]
        report = report_registry(value)
        self.assertEqual(row(report, "gates", "G4")["admission"]["readiness"], "BLOCKED_DEPENDENCIES")
        for identity in ("G2", "G3"):
            self.assertEqual(row(report, "gates", identity)["measurement"]["state"], "NOT_MEASURED")
        self.assertTrue(all(g["admission"]["decision"] == "NOT_EVALUATED" for g in report["gates"]))
        self.assertEqual(report["release_admission"], "NOT_EVALUATED")

    def test_order_respects_all_dependency_edges(self):
        value = registry()
        result = validate_registry(value)
        for kind, key in (("tasks", "task_order"), ("gates", "gate_order")):
            positions = {i: n for n, i in enumerate(result[key])}
            for item in value[kind]:
                for dependency in item["depends_on"]:
                    self.assertLess(positions[dependency], positions[item["id"]])

    def test_dependency_readiness_propagates_and_preserves_direct_blocker_order(self):
        value = registry()
        value["gates"].reverse()  # Input order cannot become execution order.
        self.assertEqual(row(report_registry(value), "gates", "G1")["admission"]["blockers"], ["G0", "GM"])
        declared_pass("G0", value)
        report = report_registry(value)
        self.assertEqual(row(report, "gates", "G1")["admission"]["blockers"], ["GM"])
        self.assertEqual(row(report, "gates", "GM")["admission"]["readiness"], "BLOCKED_MEASUREMENT")
        declared_pass("GM", value)
        report = report_registry(value)
        self.assertEqual(row(report, "gates", "G1")["admission"]["readiness"], "READY_FOR_REVIEW")
        self.assertEqual(row(report, "gates", "G1")["admission"]["decision"], "NOT_EVALUATED")
        row(value, "gates", "G0")["measurement"].update(state="STALE", reason="source changed")
        report = report_registry(value)
        self.assertEqual(row(report, "gates", "GM")["admission"]["readiness"], "BLOCKED_DEPENDENCIES")
        self.assertEqual(row(report, "gates", "G1")["admission"]["blockers"], ["G0", "GM"])

    def test_duplicate_ids_and_references_are_rejected(self):
        for kind in ("roles", "layers", "gates", "tasks", "capabilities", "evidence_records"):
            value = registry()
            value[kind].append(copy.deepcopy(value[kind][0]))
            with self.subTest(kind=kind), self.assertRaisesRegex(FrameworkError, "duplicate id"):
                validate_registry(value)
        value = registry()
        row(value, "gates", "G1")["measurement"]["evidence_ids"] *= 2
        with self.assertRaisesRegex(FrameworkError, "duplicate member"):
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
        for field in ("slice", "pair", "boolean", "step_boolean", "step_negative"):
            value = registry()
            if field == "slice":
                row(value, "gates", "G1")["dataset"]["slices"]["positive_in_scope"] = 99
            elif field == "pair":
                row(value, "gates", "G3")["dataset"]["individual_inputs"] = 80
            elif field == "boolean":
                row(value, "gates", "G1")["dataset"]["size"] = True
            else:
                row(value, "gates", "G4")["dataset"]["additional_denominators"]["episode_steps"] = (
                    True if field == "step_boolean" else -1)
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
        value = registry()
        value["tasks"][0]["evidence_ids"] = ["productive-clause-v1.exposed-review1.c694a5a"]
        with self.assertRaisesRegex(FrameworkError, "unlinked gate"):
            validate_registry(value)

    def test_delivered_scope_does_not_complete_parent_or_gate(self):
        report = report_registry(registry())
        child = row(report, "tasks", "T02-PCV1")
        parent = row(report, "tasks", "T02")
        self.assertEqual(child["work_status"], "DELIVERED")
        self.assertEqual(child["parent_task_id"], "T02")
        self.assertIn("T02-PCV1", parent["children"])
        self.assertEqual(parent["work_status"], "IN_PROGRESS")
        self.assertEqual(row(report, "gates", "G0")["measurement"]["state"], "NOT_MEASURED")
        self.assertEqual(report["release_admission"], "NOT_EVALUATED")

    def test_delivery_and_ready_require_explicit_prerequisites(self):
        for state in ("READY", "DELIVERED"):
            value = registry()
            row(value, "tasks", "T01")["work_status"] = "IN_PROGRESS"
            row(value, "tasks", "T02-PCV1")["work_status"] = state
            with self.subTest(state=state), self.assertRaisesRegex(FrameworkError, "before prerequisites"):
                validate_registry(value)
        value = registry()
        row(value, "tasks", "T10")["depends_on"].append("T06")
        with self.assertRaisesRegex(FrameworkError, "T10: DELIVERED before prerequisites"):
            validate_registry(value)

    def test_parent_delivery_waits_for_children(self):
        value = registry()
        row(value, "tasks", "T04")["work_status"] = "DELIVERED"
        row(value, "tasks", "T04-LC1")["work_status"] = "IN_PROGRESS"
        with self.assertRaisesRegex(FrameworkError, "before children"):
            validate_registry(value)

    def test_parent_references_and_hierarchy_cycles_are_checked_separately(self):
        for parent in ("missing", [], "T02-PCV1"):
            value = registry()
            row(value, "tasks", "T02-PCV1")["parent_task_id"] = parent
            with self.subTest(parent=parent), self.assertRaises(FrameworkError):
                validate_registry(value)
        value = registry()
        row(value, "tasks", "T02")["parent_task_id"] = "T02-PCV1"
        with self.assertRaisesRegex(FrameworkError, "task parents: dependency cycle"):
            validate_registry(value)
        value = registry()
        del row(value, "tasks", "T02-PCV1")["scope"]
        with self.assertRaisesRegex(FrameworkError, "scope"):
            validate_registry(value)

    def test_consistent_but_invented_pass_is_still_not_verified(self):
        report = report_registry(declared_pass())
        gate = row(report, "gates", "G0")
        self.assertEqual(gate["measurement"]["reported_outcome"], "PASS")
        self.assertEqual(gate["admission"]["readiness"], "READY_FOR_REVIEW")
        self.assertEqual(gate["admission"]["decision"], "NOT_EVALUATED")
        self.assertEqual(gate["verification_status"], "NOT_PERFORMED")
        self.assertFalse(report["evidence_verified"])
        self.assertEqual(report["semantic_authority"], "NONE")
        self.assertEqual(report["release_admission"], "NOT_EVALUATED")

    def test_pass_requires_frozen_nonempty_data_and_zero_required_skips(self):
        for field in ("draft", "empty", "skipped", "missing", "failed"):
            value = declared_pass()
            if field == "draft":
                row(value, "gates", "G0")["dataset"]["status"] = "draft"
            elif field == "empty":
                value["evidence_records"][0]["required_checks"]["passed"] = 0
            else:
                value["evidence_records"][0]["required_checks"][field] = 1
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                validate_registry(value)

    def test_cannot_borrow_evidence_from_another_scope_or_suite(self):
        for field in ("scope", "suite_version", "dataset_sha256", "gate_id"):
            value = declared_pass()
            evidence = value["evidence_records"][0]
            if field in ("scope", "gate_id"):
                evidence[field] = "G1" if field == "gate_id" else "other-scope"
            else:
                evidence["run_identity"][field] = "e" * 64 if field.endswith("sha256") else "other.v1"
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                validate_registry(value)

    def test_measurement_states_are_consistent_with_selected_results(self):
        for change in ({"state": "NOT_MEASURED"}, {"state": "NOT_APPLICABLE", "reason": "excluded"},
                       {"reported_outcome": "FAIL"}, {"evidence_ids": []}, {"extra_status": "verified"}):
            value = declared_pass()
            row(value, "gates", "G0")["measurement"].update(change)
            with self.subTest(change=change), self.assertRaises(FrameworkError):
                validate_registry(value)
        value = declared_pass()
        value["evidence_records"][0]["reported_outcome"] = "FAIL"
        value["evidence_records"][0]["required_checks"]["failed"] = 1
        with self.assertRaisesRegex(FrameworkError, "outcome differs"):
            validate_registry(value)
        row(value, "gates", "G0")["measurement"]["reported_outcome"] = "FAIL"
        self.assertEqual(row(report_registry(value), "gates", "G0")["admission"]["readiness"],
                         "BLOCKED_MEASUREMENT")

    def test_stale_evidence_keeps_history_without_satisfying_new_dataset(self):
        value = declared_pass()
        gate = row(value, "gates", "G0")
        gate["dataset"]["sha256"] = "f" * 64
        gate["measurement"].update(state="STALE", reason="independently revised dataset")
        report = report_registry(value)
        self.assertEqual(row(report, "gates", "G0")["admission"]["readiness"], "BLOCKED_MEASUREMENT")
        gate["measurement"]["reason"] = None
        with self.assertRaisesRegex(FrameworkError, "requires a reason"):
            validate_registry(value)

    def test_not_applicable_does_not_waive_dependencies(self):
        value = registry()
        row(value, "gates", "G0")["measurement"].update(state="NOT_APPLICABLE", reason="caller exemption")
        report = report_registry(value)
        self.assertEqual(row(report, "gates", "G1")["admission"]["blockers"], ["G0", "GM"])
        self.assertEqual(row(report, "gates", "G0")["admission"]["readiness"], "BLOCKED_MEASUREMENT")

    def test_cannot_claim_authority_as_registry_input(self):
        for place in ("gate", "measurement", "evidence"):
            for field in ("admission", "evidence_verified", "semantic_authority", "authenticated"):
                value = declared_pass()
                target = {"gate": row(value, "gates", "G0"),
                          "measurement": row(value, "gates", "G0")["measurement"],
                          "evidence": value["evidence_records"][0]}[place]
                target[field] = True
                with self.subTest(place=place, field=field), self.assertRaisesRegex(FrameworkError, "authority"):
                    validate_registry(value)

    def test_capability_cannot_carry_a_result_absent_from_gate_measurement(self):
        value = registry()
        row(value, "gates", "G1")["measurement"] = {
            "state": "NOT_MEASURED", "reported_outcome": None, "evidence_ids": [], "reason": None}
        with self.assertRaisesRegex(FrameworkError, "not part of its gate measurement"):
            validate_registry(value)
        value = registry()
        row(value, "capabilities", "productive-clause-v1")["scope"] = "another-law"
        with self.assertRaisesRegex(FrameworkError, "scope differs"):
            validate_registry(value)

    def test_v1_schema_and_obsolete_overloaded_fields_are_rejected(self):
        value = registry()
        value["schema"] = "nabt.entropy-framework.registry.v1"
        with self.assertRaisesRegex(FrameworkError, "unsupported registry schema"):
            validate_registry(value)
        for kind, field in (("gates", "status"), ("gates", "baseline"), ("gates", "evidence_ids"),
                            ("tasks", "gate_status"), ("tasks", "scoped_evidence_ids")):
            value = registry()
            value[kind][0][field] = None
            with self.subTest(kind=kind, field=field), self.assertRaisesRegex(FrameworkError, "legacy"):
                validate_registry(value)

    def test_migration_requires_identity_unique_changes_and_known_affected_items(self):
        for mutation in ("source", "hash", "empty", "duplicate", "unknown", "reason"):
            value = registry()
            migration = value["migration"]
            if mutation == "source":
                migration["source_schema"] = "unknown"
            elif mutation == "hash":
                migration["source_sha256"] = "0" * 63
            elif mutation == "empty":
                migration["changes"] = []
            elif mutation == "duplicate":
                migration["changes"].append(copy.deepcopy(migration["changes"][0]))
            elif mutation == "unknown":
                migration["changes"][0]["affected_ids"] = ["missing"]
            else:
                migration["changes"][0]["reason"] = " "
            with self.subTest(mutation=mutation), self.assertRaises(FrameworkError):
                validate_registry(value)

    def test_migration_rejects_well_formed_but_alternate_history(self):
        for field, alternate in (
            ("source_schema", "nabt.entropy-framework.registry.v2"),
            ("source_commit", "1" * 40),
            ("source_path", "tools/entropy_framework/alternate_registry.json"),
            ("source_sha256", "f" * 64),
        ):
            value = registry()
            value["migration"][field] = alternate
            with self.subTest(field=field), self.assertRaisesRegex(FrameworkError, "installed source identity"):
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
                value["gates"][0]["measurement"]["state"] = []
            else:
                value["tasks"][0]["owner_role"] = []
            with self.subTest(field=field), self.assertRaises(FrameworkError):
                validate_registry(value)

    def test_missing_dependency_state_is_a_diagnostic_regardless_of_row_order(self):
        value = registry()
        value["tasks"].reverse()
        del row(value, "tasks", "T01")["work_status"]
        with self.assertRaises(FrameworkError):
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
