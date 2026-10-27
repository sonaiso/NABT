"""Gateway authority mutations and real native replay, not Arabic coverage."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt import foundation
from nabt.errors import NabtError
from tools import licensed_workflow as workflow
from tests._transport_native import require_native

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "formal/.lake/build/bin"


def request(op="classical_control", **arguments):
    if not arguments:
        arguments = {"rule_id": "HAMZA-LEXICAL-COMMAND",
                     "frame": {"root": ["ء", "ك", "ل"], "profile": "all_attested"}}
    return {"schema": workflow.REQUEST_SCHEMA, "op": op, "input": arguments}


def result():
    return {"schema": "nabt.classical-certified-control.v1", "status": "VERIFICATION_UNAVAILABLE",
            "native_checked": False, "strict_language_accepted": False, "claims": []}


class LicensedWorkflowPortableTests(unittest.TestCase):
    def test_caller_cannot_import_result_checker_or_authority(self):
        original = request()
        mutations = []
        for key in ("result", "checker", "native_checked", "claims", "proof", "root"):
            changed = deepcopy(original)
            changed["input"][key] = True
            mutations.append(changed)
            changed = deepcopy(original)
            changed[key] = True
            mutations.append(changed)
        with patch.object(workflow, "_execute") as execute:
            for changed in mutations:
                with self.subTest(changed=changed):
                    response = workflow.run_request(changed)
                    self.assertEqual(response["status"], "INVALID_INPUT")
                    self.assertEqual(response["claims"], [])
            execute.assert_not_called()

    def test_unknown_operation_is_deferred_not_language_rejected(self):
        with patch.object(workflow, "_execute") as execute:
            response = workflow.run_request(request("legacy_free_reader", text="زَيْدٌ"))
            self.assertEqual(response["status"], "DEFER")
            self.assertEqual(response["reason"], "UNMIGRATED_OR_UNKNOWN_OPERATION")
            self.assertFalse(response["strict_language_accepted"])
            execute.assert_not_called()

    def test_numeric_arguments_reject_bool_float_and_string_without_rounding(self):
        with patch.object(workflow, "_execute") as execute:
            for number in (True, 0.0, "0", -1):
                response = workflow.run_request(request("lexical_surface", text="عَيْنَ", start_byte=number))
                self.assertEqual(response["status"], "INVALID_INPUT")
            execute.assert_not_called()

    def test_budget_is_a_bounded_object_and_cannot_carry_flags(self):
        with patch.object(workflow, "_execute") as execute:
            for budget in (5, True, {"max_readings": True}, {"max_readings": 1.5},
                           {"max_native_scan": 4097}, {"max_input_bytes": -1}, {"checker": 0}):
                response = workflow.run_request(request("lexical_candidates", text="قَرْءُ",
                    profile_id="linguistic", budget=budget))
                self.assertEqual(response["status"], "INVALID_INPUT")
            execute.assert_not_called()

    def test_nonfinite_and_unpaired_surrogate_never_enter_adapters(self):
        with patch.object(workflow, "_execute") as execute:
            for text in (float("nan"), "\ud800"):
                response = workflow.run_request(request("lexical_surface", text=text))
                self.assertEqual(response["status"], "INVALID_INPUT")
            execute.assert_not_called()

    def test_request_resource_limit_is_not_a_linguistic_rejection(self):
        with patch.object(workflow, "_execute") as execute:
            response = workflow.run_request(request("lexical_surface", text="x" * workflow.MAX_REQUEST_BYTES))
            self.assertEqual(response["status"], "RESOURCE_EXHAUSTED")
            execute.assert_not_called()

    def test_direct_api_boundary_is_checked_before_dispatch(self):
        denial = NabtError("TEST_FOUNDATION_DENIED", "denied", status="DEFER")
        with patch.object(foundation, "require_foundation", side_effect=denial), \
                patch.object(workflow, "_execute") as execute:
            with self.assertRaises(NabtError):
                workflow.run_request(request())
            with self.assertRaises(NabtError):
                workflow.migration_inventory()
            execute.assert_not_called()

    def test_claim_with_false_native_and_universal_promotions_are_rejected(self):
        claim = {"kind": "FORGED", "scope": "not accepted",
                 "proof": {"law_id": "forged", "theorems": ["Nabt.Forged"]}}
        for key, value in (("claims", [claim]), ("strict_language_accepted", True),
                           ("strict_language_accepted", "false"), ("native_checked", 1),
                           ("tawatur_established", True), ("whole_arabic_complete", True),
                           ("intended_sense_established", True)):
            changed = {**result(), key: value}
            with self.subTest(key=key, value=value), patch.object(workflow, "_execute", return_value=changed):
                response = workflow.run_request(request())
                self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
                self.assertEqual(response["claims"], [])
                self.assertFalse(response["strict_language_accepted"])

    def test_native_boolean_alone_is_not_a_proof(self):
        changed = {**result(), "native_checked": True, "status": "DEFER"}
        with patch.object(workflow, "_execute", return_value=changed):
            response = workflow.run_request(request())
        self.assertTrue(response["native_checked"])
        self.assertEqual(response["claims"], [])
        self.assertEqual(response["workflow_status"], "NO_SCOPED_CLAIMS")
        self.assertNotIn("proof", response)

    def test_claim_kind_and_law_cannot_be_promoted_while_global_flags_stay_false(self):
        for kind, law in (("ALL_ARABIC_COMPLETE", "nabt.classical-hamza.v1"),
                          ("CLASSICAL_FINITE_CONTROL_EQUATION", "nabt.unrelated-law.v1")):
            changed = {**result(), "native_checked": True, "claims": [{
                "kind": kind, "scope": "An unlicensed adapter claim", "proof": {
                    "law_id": law, "theorems": ["Nabt.ClassicalHamza.enumeration_exact"]}}]}
            with self.subTest(kind=kind, law=law), patch.object(workflow, "_execute", return_value=changed):
                response = workflow.run_request(request())
            self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(response["reason"], "UNREGISTERED_CLAIM_OR_LAW_FOR_OPERATION")
            self.assertEqual(response["claims"], [])

    def test_source_or_adapter_error_is_not_blamed_on_input(self):
        with patch.object(workflow, "_execute", side_effect=ValueError("SOURCE_BYTES_CHANGED")):
            response = workflow.run_request(request())
        self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(response["reason"], "SOURCE_BYTES_CHANGED")

    def test_missing_adapter_registration_blocks_even_existing_callable(self):
        registry, digest = workflow._registry()
        registry["surfaces"] = [row for row in registry["surfaces"]
            if row["id"] != "nabt.classical_certified.evaluate_certified"]
        with patch.object(workflow, "_registry", return_value=(registry, digest)), \
                patch.object(workflow, "_execute") as execute:
            response = workflow.run_request(request())
        self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(response["reason"], "ADAPTER_NOT_REGISTERED")
        execute.assert_not_called()

    def test_inventory_covers_each_registered_surface_once_without_promoting_checked_kind(self):
        inventory = workflow.migration_inventory()
        registry, digest = workflow._registry()
        self.assertEqual(inventory["registry_sha256"], digest)
        self.assertEqual([row["surface_id"] for row in inventory["surfaces"]],
                         [row["id"] for row in registry["surfaces"]])
        self.assertEqual(sum(inventory["states"].values()), inventory["surface_count"])
        self.assertFalse(inventory["all_interfaces_migrated"])
        old = next(row for row in inventory["surfaces"] if row["surface_id"] == "nabt.word_reader.read_words")
        self.assertEqual(old["migration_state"], "ACQUISITION_AND_REFINEMENT_REVIEW_REQUIRED")
        self.assertTrue(all(row["runtime_availability"] == "NOT_MEASURED_BY_INVENTORY"
                            for row in inventory["surfaces"]))


@unittest.skipUnless((BIN / "exportClassicalHamza").is_file(), "native gateway CI builds classical exports")
class LicensedWorkflowNativeControlTests(unittest.TestCase):
    def test_default_control_route_executes_native_and_preserves_exact_claim(self):
        response = workflow.run_request(request())
        self.assertEqual(response["status"], "CHECKED_CONDITIONAL_CONTROL")
        self.assertTrue(response["native_checked"])
        self.assertEqual(len(response["claims"]), 1)
        forwarded = dict(response["claims"][0])
        self.assertEqual(forwarded.pop("origin_path"), "claims[0]")
        self.assertEqual(forwarded, response["result"]["claims"][0])
        self.assertEqual(response["result_sha256"], workflow._digest(response["result"]))
        self.assertFalse(response["strict_language_accepted"])

    def test_missing_native_control_returns_no_claim(self):
        from nabt import classical_certified
        with patch.object(classical_certified, "_native_export", side_effect=FileNotFoundError):
            response = workflow.run_request(request())
        self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(response["claims"], [])


@unittest.skipUnless(all((BIN / name).is_file() for name in ("lexicalSourceRows", "lexicalSurface")),
                     "native gateway CI builds source and surface checkers")
class LicensedWorkflowNativeSourceTests(unittest.TestCase):
    def test_source_and_surface_claims_stay_separate(self):
        response = workflow.run_request(request("lexical_surface", text="عَيْنَ", context="مقام جديد"))
        self.assertEqual(response["status"], "CHECKED_EXACT_SURFACE")
        self.assertEqual([claim["origin_path"] for claim in response["claims"]],
                         ["source_acquisition", "claims[0]"])
        self.assertEqual(len(response["result"]["matches"]), 3)
        self.assertFalse(response["result"]["intended_sense_established"])

    def test_later_failure_keeps_only_independently_checked_source_claim(self):
        from tools.linguistic_truth import surface
        with patch.object(surface, "_native", side_effect=FileNotFoundError):
            response = workflow.run_request(request("lexical_surface", text="عَيْنَ"))
        self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(response["native_checked"])
        self.assertEqual([claim["origin_path"] for claim in response["claims"]], ["source_acquisition"])
        self.assertEqual(response["workflow_status"], "SCOPED_CLAIMS_AVAILABLE")


class LicensedWorkflowAllNativeAdaptersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_native("exportClassicalHamza", "lexicalSourceRows", "lexicalSurface", "linguisticTruth",
                       "lexicalTransmission", "scopeAcquisition", "licensedInference", "discourseBoundaryCue",
                       "sixNounAcquisition")

    def test_supplied_lexical_budget_is_converted_to_fixed_typed_budget(self):
        response = workflow.run_request(request("lexical_candidates", text="قَرْءُ",
            profile_id="linguistic", budget={"max_native_scan": 4096}))
        self.assertTrue(response["native_checked"], response)
        self.assertIn("A116_EXACT_INSTALLED_CANDIDATE_SET", [c["kind"] for c in response["claims"]])
        self.assertEqual(response["effective_budget"], {
            "max_input_bytes": 65536, "max_occurrences": 256, "max_readings": 2048, "max_native_scan": 4096})
        limited = workflow.run_request(request("lexical_candidates", text="قَرْءُ",
            profile_id="linguistic", budget={"max_input_bytes": 0}))
        self.assertEqual(limited["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(limited["claims"], [])

    def test_all_registered_raw_request_adapters_replay_their_actual_claim_contract(self):
        examples = [
            (request(), "CHECKED_CONDITIONAL_CONTROL", "CLASSICAL_FINITE_CONTROL_EQUATION"),
            (request("lexical_surface", text="عَيْنَ", context="مقام جديد"),
             "CHECKED_EXACT_SURFACE", "EXACT_WITNESSED_FORM_WITH_DECLARED_ANNOTATION"),
            (request("lexical_candidates", text="قَرْءُ", profile_id="linguistic", context="مقام جديد"),
             "DEFER", "A116_EXACT_INSTALLED_CANDIDATE_SET"),
            (request("lexical_transmission", entry="فرس", context="مقام جديد"),
             "DOCUMENTARY_REPORTS", "SOURCE_BOUND_REPORT_INVENTORY_AND_DEPENDENCY_CLASSIFICATION"),
            (request("scope_acquisition", text="قَالَ زَيْدٌ: «أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ».",
                     context="قول محكي"), "CHECKED_SCOPE_ENVELOPE", "EXACT_SCOPE_ENVELOPE"),
            (request("six_noun_acquisition", text="جَاءَ أَبُو زَيْدٍ", context="قراءة إتمام محددة"),
             "CHECKED_SIX_NOUN", "SOURCE_BOUND_SIX_NOUN_CONSTRUCTION"),
            (request("source_inference", source="سار زيد أمامك خلف الدار", query="هل سار زيد أمامك خلف الدار؟"),
             "SUPPORTED", "SOURCE_BOUND_FINITE_INFERENCE"),
            (request("discourse_boundary", text="لم يخرج خالد؛ وأقصد بالأسد الحيوان المفترس.",
                     context="مقام مستقل"), "CHECKED_DISCOURSE_BOUNDARY", "EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE"),
        ]
        self.assertEqual({case[0]["op"] for case in examples}, set(workflow._OPERATIONS))
        for incoming, status, claim_kind in examples:
            with self.subTest(operation=incoming["op"]):
                response = workflow.run_request(incoming)
                self.assertEqual(response["status"], status, response.get("reason"))
                self.assertTrue(response["native_checked"])
                self.assertIn(claim_kind, [claim["kind"] for claim in response["claims"]])
                self.assertEqual(response["request_sha256"], workflow._digest(incoming))
                self.assertEqual(response["result_sha256"], workflow._digest(response["result"]))
                self.assertFalse(response["strict_language_accepted"])
                self.assertFalse(response["whole_arabic_complete"])
                self.assertNotIn("proof", response)


if __name__ == "__main__":
    unittest.main()
