"""Independent protocol attacks, not linguistic or empirical reference answers.

The synthetic ledger below is deliberately labelled as a declared premise.
Passing these tests establishes bounded rejection/receipt behaviour only.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "formal/.lake/build/bin/epistemicMeasurement"


def declared_ledger():
    key = {"axis": "recorded_observation", "entity": "artifact-7", "predicate": "byte_count",
           "value": "12", "unit": "byte", "context": "synthetic-protocol-control",
           "time": "7", "place": "declared-fixture"}
    sources = [{"identity": "source-a", "revision": "r1", "content": "Declared fixture A."},
               {"identity": "source-b", "revision": "r1", "content": "Declared fixture B."}]
    return {"query": {"key": key, "positive": True, "origin": "claim"},
            "active_sources": sources,
            "origins": [{"id": name, "parents": []} for name in ("claim", "origin-a", "origin-b")],
            "interpretations": [{"id": "e-" + suffix, "source": deepcopy(source),
                "key": deepcopy(key), "positive": True, "kind": "observation",
                "origin": "origin-" + suffix, "ancestry": ["origin-" + suffix]}
                for suffix, source in zip(("a", "b"), sources)],
            "budget": 2, "certificate": None}


class NativeAdversarialEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NATIVE.is_file():
            raise unittest.SkipTest("Build the independent native checker with lake build epistemicMeasurement")

    def native(self, request):
        raw = request if isinstance(request, str) else json.dumps(request, ensure_ascii=False)
        run = subprocess.run([str(NATIVE)], input=raw + "\n", text=True,
                             capture_output=True, timeout=20, check=True)
        rows = run.stdout.splitlines()
        self.assertEqual(len(rows), 1, run.stderr)
        result = json.loads(rows[0])
        for field in ("world_truth_established", "hidden_motive_established", "all_arabic_complete"):
            self.assertIs(result[field], False, field)
        return result

    def test_positive_control_keeps_both_declared_witnesses(self):
        result = self.native(declared_ledger())
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertEqual(result["selected_ids"], ["e-a", "e-b"])
        self.assertIs(result["certificate_checked"], False)

    def test_exact_receipt_cannot_omit_duplicate_reorder_or_change_status(self):
        proper = {"status": "SUPPORTED", "support_ids": ["e-a", "e-b"],
                  "refutation_ids": [], "selected_ids": ["e-a", "e-b"]}
        request = declared_ledger()
        request["certificate"] = proper
        self.assertIs(self.native(request)["certificate_checked"], True)
        attacks = []
        for field in ("support_ids", "selected_ids"):
            for replacement in (["e-a"], ["e-a", "e-b", "e-a"], ["e-b", "e-a"]):
                changed = deepcopy(proper)
                changed[field] = replacement
                attacks.append(changed)
        attacks.extend([{**proper, "status": "REFUTED"}, {**proper, "refutation_ids": ["e-a"]}])
        for forged in attacks:
            with self.subTest(certificate=forged):
                request["certificate"] = forged
                result = self.native(request)
                self.assertEqual(result["status"], "INVALID_CERTIFICATE")
                self.assertIs(result["certificate_checked"], False)

    def test_transitive_laundering_is_rejected_even_with_a_cycle(self):
        request = declared_ledger()
        request["interpretations"] = request["interpretations"][:1]
        request["origins"] += [{"id": "launder", "parents": ["claim"]}]
        request["origins"][1]["parents"] = ["launder"]
        for ancestry in (["origin-a"], ["origin-a", "launder"], ["origin-a", "launder", "claim"]):
            request["interpretations"][0]["ancestry"] = ancestry
            self.assertEqual(self.native(request)["status"], "UNKNOWN")
        request["origins"][0]["parents"] = ["origin-a"]
        self.assertEqual(self.native(request)["status"], "UNKNOWN")

    def test_declared_cycle_without_query_does_not_create_truth_or_hang(self):
        request = declared_ledger()
        request["origins"][1]["parents"] = ["origin-b"]
        request["origins"][2]["parents"] = ["origin-a"]
        for evidence in request["interpretations"]:
            evidence["ancestry"] = ["origin-a", "origin-b"]
        self.assertEqual(self.native(request)["status"], "SUPPORTED")

    def test_each_scope_coordinate_must_match(self):
        for field in ("entity", "predicate", "value", "unit", "context", "time", "place"):
            request = declared_ledger()
            request["query"]["key"][field] = "8" if field == "time" else "other"
            with self.subTest(field=field):
                self.assertEqual(self.native(request)["status"], "UNKNOWN")

    def test_a_different_scalar_is_not_the_negation_of_the_original(self):
        request = declared_ledger()
        request["query"]["key"]["value"] = "13"
        self.assertEqual(self.native(request)["status"], "UNKNOWN")
        request = declared_ledger()
        request["query"]["positive"] = False
        result = self.native(request)
        self.assertEqual(result["status"], "REFUTED")
        self.assertEqual(result["refutation_ids"], ["e-a", "e-b"])

    def test_source_content_and_revision_are_not_replaceable_by_the_same_id(self):
        for field in ("content", "revision"):
            request = declared_ledger()
            for source in request["active_sources"]:
                source[field] = "different"
            self.assertEqual(self.native(request)["status"], "UNKNOWN")

    def test_metadata_cannot_make_hidden_motive_or_world_truth(self):
        request = declared_ledger()
        request["query"]["key"]["axis"] = "hidden_motive"
        for evidence in request["interpretations"]:
            evidence["key"]["axis"] = "hidden_motive"
            evidence["kind"] = "self_report"
        self.assertEqual(self.native(request)["status"], "UNKNOWN")
        for field in ("native_checked", "is_empirical_reality", "world_truth_established"):
            request = declared_ledger()
            request[field] = True
            self.assertEqual(self.native(request)["status"], "INVALID_INPUT")

    def test_invalid_numeric_encodings_never_enter_the_same_integer_slot(self):
        for value in ("-0", "+0", "00", "01", "1.0", "1e0", " 1", "9007199254740992", 1, True, 1.5):
            request = declared_ledger()
            request["query"]["key"]["time"] = value
            with self.subTest(time=value):
                self.assertEqual(self.native(request)["status"], "INVALID_INPUT")
        for value in (True, 2.0, 2.5, "2", -1):
            request = declared_ledger()
            request["budget"] = value
            with self.subTest(budget=value):
                self.assertEqual(self.native(request)["status"], "INVALID_INPUT")

    def test_duplicate_ids_and_escaped_duplicate_object_keys_are_invalid(self):
        for field in ("active_sources", "origins", "interpretations"):
            request = declared_ledger()
            request[field].append(deepcopy(request[field][0]))
            self.assertEqual(self.native(request)["status"], "INVALID_INPUT")
        raw = json.dumps(declared_ledger()).replace('"budget": 2', '"budget": 2, "bu\\u0064get": 2')
        self.assertEqual(self.native(raw)["status"], "INVALID_INPUT")

    def test_resource_limit_is_not_empty_complete_evidence(self):
        request = declared_ledger()
        request["budget"] = 1
        result = self.native(request)
        self.assertEqual(result["status"], "RESOURCE_LIMIT")
        self.assertEqual(result["selected_ids"], [])
        request["certificate"] = {"status": "UNKNOWN", "support_ids": [],
                                  "refutation_ids": [], "selected_ids": []}
        self.assertEqual(self.native(request)["status"], "INVALID_CERTIFICATE")


class InstalledCollectorAdversaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import epistemic_measurement
        cls.adapter = epistemic_measurement
        if not NATIVE.is_file():
            raise unittest.SkipTest("Build epistemicMeasurement for native collector replay")

    def agency_input(self):
        return {"query": {"key": {"axis": "recorded_observation",
                    "entity": "official20110311054624120_30", "predicate": "magnitude:mww",
                    "value": "9.1", "unit": "dimensionless", "context": "usgs.preferred-event.v1",
                    "time": "1299822384120", "place": "142.373,38.297,29"},
                "positive": True, "origin": "query"}, "budget": 1}

    def execute_agency(self, request=None):
        return self.adapter.execute_request(self.agency_input() if request is None else request,
                                            source_profile="usgs_snapshot_v1")

    def assert_no_authority(self, result):
        for field in ("world_truth_established", "hidden_motive_established",
                      "free_arabic_acquisition_measured", "whole_arabic_complete"):
            self.assertIs(result[field], False, field)

    def test_real_record_positive_control_is_narrowly_source_bound(self):
        result = self.execute_agency()
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertIs(result["native_checked"], True)
        self.assertEqual(result["evidence_class"], "AGENCY_RECORD")
        self.assert_no_authority(result)
        binding, = result["source_bindings"]
        self.assertEqual(binding["field_pointer"], "/properties/mag")
        self.assertEqual(binding["raw_sha256"],
                         "d9cf0301f748786d5ff881edba71e1b19c5b5008b3abeb893e8e88240433ba4a")
        source, = result["execution"]["input"]["active_sources"]
        projection = json.loads(source["content"])
        self.assertEqual(projection["pointer"], "/properties/mag")
        self.assertEqual(projection["value"], "9.1")
        self.assertEqual(projection["revision"], "1792147089160")

    def test_other_origin_value_never_replaces_preferred_field(self):
        request = self.agency_input()
        request["query"]["key"]["value"] = "9.0"
        result = self.execute_agency(request)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIs(result["native_checked"], True)
        self.assertEqual(result["observed"]["selected_ids"], [])
        self.assert_no_authority(result)

    def test_caller_cannot_supply_raw_pointer_digest_or_certificate(self):
        for key, value in (("raw_path", "/tmp/fake-source"),
                           ("raw_sha256", "0" * 64),
                           ("pointer", "/properties/products/origin/1/properties/magnitude"),
                           ("certificate", {"status": "SUPPORTED"}),
                           ("world_truth_established", True)):
            request = self.agency_input()
            request[key] = value
            with self.subTest(field=key):
                result = self.execute_agency(request)
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertIs(result["native_checked"], False)
                self.assert_no_authority(result)

    def test_changed_or_missing_original_snapshot_cannot_certify_projection(self):
        original = self.adapter.USGS_RAW_PATH.read_bytes()
        changed = json.loads(original)
        changed["properties"]["mag"] = 9.0
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "forged-source.json"
            path.write_text(json.dumps(changed), encoding="utf-8")
            with patch.object(self.adapter, "USGS_RAW_PATH", path):
                result = self.execute_agency()
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertIs(result["native_checked"], False)
            self.assertIn("digest mismatch", result["execution"]["error"])
            path.unlink()
            with patch.object(self.adapter, "USGS_RAW_PATH", path):
                result = self.execute_agency()
            self.assertEqual(result["status"], "UNMEASURED")
            self.assertIs(result["native_checked"], False)

    def test_native_response_cannot_bless_itself_with_contradictory_metadata(self):
        genuine = self.execute_agency()["execution"]["native_result"]
        mutations = [("world_truth_established", True), ("hidden_motive_established", True),
                     ("all_arabic_complete", True), ("certificate_checked", 1),
                     ("certificate_checked", False), ("observed_status", "UNKNOWN"),
                     ("support_ids", []), ("selected_ids", ["forged-witness"])]
        for field, value in mutations:
            forged = deepcopy(genuine)
            forged[field] = value
            with self.subTest(field=field, value=value), patch.object(self.adapter, "_native", return_value=forged):
                result = self.execute_agency()
                self.assertIs(result["native_checked"], False)
                self.assertIs(result["certificate_checked"], False)
                self.assertIsNone(result["observed"])
                self.assert_no_authority(result)

    def test_authored_record_cannot_enter_real_agency_scope(self):
        result = self.adapter.execute_request(declared_ledger(), source_profile="authored_controls_v1")
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertEqual(result["evidence_class"], "AUTHORED_SCENARIO")
        self.assert_no_authority(result)
        forged = self.adapter.execute_request(declared_ledger(), source_profile="usgs_snapshot_v1")
        self.assertEqual(forged["status"], "INVALID_INPUT")
        self.assertIs(forged["native_checked"], False)

    def test_missing_native_is_unmeasured_never_python_only_proof(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(self.adapter, "NATIVE", Path(temp) / "missing"):
            result = self.execute_agency()
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertIs(result["native_checked"], False)
        self.assertIsNone(result["observed"])
        self.assertEqual(result["execution"]["error"], "NATIVE_UNAVAILABLE")

    def test_malformed_profile_is_a_failure_receipt_not_an_exception(self):
        for profile in ([], {}, None, True, 1):
            with self.subTest(profile=profile):
                result = self.adapter.execute_request({}, source_profile=profile)
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertIs(result["native_checked"], False)
                self.assert_no_authority(result)

    def test_python_decoder_rejects_duplicate_and_lossy_numbers(self):
        for raw in ('{"budget":1,"bu\\u0064get":2}', '{"time":1.0}',
                    '{"time":1e0}', '{"time":-0}', '{"time":9007199254740992}',
                    '{"time":NaN}', '{"time":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(self.adapter.InputError):
                self.adapter.strict_loads(raw)
        for budget in (True, 1.0, 1.5):
            request = self.agency_input()
            request["budget"] = budget
            result = self.execute_agency(request)
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertIs(result["native_checked"], False)


class BenchmarkDenominatorAdversaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import benchmark_epistemic_measurement, epistemic_measurement
        cls.benchmark = benchmark_epistemic_measurement
        cls.adapter = epistemic_measurement

    def test_missing_native_keeps_all_declared_denominators_unmeasured(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(self.adapter, "NATIVE", Path(temp) / "missing"):
            report = self.benchmark.run(require_native=True)
        self.assertFalse(report["all_cases_native_checked"])
        self.assertEqual(report["groups"]["authored_controls"]["case_count"], 32)
        self.assertEqual(report["groups"]["agency_record"]["case_count"], 11)
        for group in report["groups"].values():
            self.assertEqual(sum(m["eligible"] for m in group["metrics"].values()), group["case_count"])
            for metric in group["metrics"].values():
                self.assertEqual(metric["measured"], 0)
                self.assertEqual(metric["passed"], 0)
                self.assertEqual(metric["unmeasured"], metric["eligible"])
        self.assertTrue(all(case["observed"] is None and case["comparison"] == "UNMEASURED"
                            for case in report["cases"]))

    def test_always_unknown_does_not_pass_positive_capability_or_refutation(self):
        if not NATIVE.is_file():
            self.skipTest("Build epistemicMeasurement for the universal-abstention probe")
        request = declared_ledger()
        request["interpretations"] = []
        unknown = self.adapter.execute_request(request)
        self.assertEqual(unknown["status"], "UNKNOWN")
        self.assertIs(unknown["native_checked"], True)
        with patch.object(self.adapter, "execute_request", side_effect=lambda *a, **k: deepcopy(unknown)):
            report = self.benchmark.run()
        for group in report["groups"].values():
            for category in ("positive_capability", "refutation", "conflict"):
                metric = group["metrics"][category]
                self.assertEqual(metric["passed"], 0)
                self.assertEqual(metric["failed"], metric["eligible"])
        self.assertEqual(report["groups"]["authored_controls"]["case_count"], 32)
        self.assertEqual(report["groups"]["agency_record"]["case_count"], 11)
        self.assertFalse(report["hidden_motive_measured"])
        self.assertFalse(report["world_truth_established"])

    def test_gold_labels_and_display_text_never_reach_runtime_boundary(self):
        references = self.benchmark.load_reference()
        seen = []
        with tempfile.TemporaryDirectory() as temp, patch.object(self.adapter, "NATIVE", Path(temp) / "missing"):
            original = self.adapter.execute_request
            def record(input_value, *, source_profile):
                seen.append((deepcopy(input_value), source_profile))
                return original(input_value, source_profile=source_profile)
            with patch.object(self.adapter, "execute_request", side_effect=record):
                self.benchmark.run()
        self.assertEqual(len(seen), len(references))
        for (input_value, profile), reference in zip(seen, references):
            self.assertEqual(input_value, reference["input"])
            self.assertEqual(profile, reference["source_profile"])
            self.assertNotIn("expected", input_value)
            self.assertNotIn("metric_category", input_value)
            self.assertNotIn("display_text_ar", input_value)

    def test_reference_mutation_cannot_change_denominators_with_its_own_label(self):
        original = json.loads(self.benchmark.REFERENCE.read_bytes())
        original["cases"] = original["cases"][:1]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reference.json"
            path.write_text(json.dumps(original), encoding="utf-8")
            with patch.object(self.benchmark, "REFERENCE", path), self.assertRaises(ValueError):
                self.benchmark.load_reference()
        for non_boolean in (0, 1, "true", None):
            with self.subTest(require_native=non_boolean), self.assertRaises(ValueError):
                self.benchmark.run(require_native=non_boolean)


if __name__ == "__main__":
    unittest.main()
