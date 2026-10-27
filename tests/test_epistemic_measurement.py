"""Protocol properties and exact native certificates, independent of Arabic claims."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from unittest import TestCase, skipUnless
from unittest.mock import patch

from tools import epistemic_measurement as runtime
from tools import benchmark_epistemic_measurement as benchmark


def ledger():
    key = {"axis": "reported_motive", "entity": "speaker", "predicate": "declared_goal",
           "value": "study", "unit": "purpose", "context": "occasion-a", "time": "-1", "place": "hall"}
    source = {"identity": "declared-source", "revision": "v1", "content": "Authored self-report premise."}
    return {"query": {"key": key, "positive": True, "origin": "query"},
            "active_sources": [source],
            "origins": [{"id": "query", "parents": []}, {"id": "record", "parents": []}],
            "interpretations": [{"id": "witness", "source": deepcopy(source), "key": deepcopy(key),
                                 "positive": True, "kind": "self_report", "origin": "record", "ancestry": ["record"]}],
            "budget": 128, "certificate": None}


class EpistemicWireTests(TestCase):
    def test_domain_json_rejects_duplicate_decoded_keys_and_noninteger_numbers(self):
        for raw in ('{"budget":1,"budget":2}', '{"budget":1,"\\u0062udget":2}',
                    '{"budget":1.0}', '{"budget":1e0}', '{"budget":NaN}',
                    '{"budget":-0}', '{"budget":9007199254740992}'):
            with self.subTest(raw=raw), self.assertRaises(runtime.InputError):
                runtime.strict_loads(raw)

    def test_numbers_are_not_coerced(self):
        for bad in (True, False, 1.0, "1", -1, None):
            request = ledger()
            request["budget"] = bad
            with self.subTest(bad=bad), self.assertRaises(runtime.InputError):
                runtime.validate_request(request)

    def test_time_is_exact_canonical_signed_text(self):
        for bad in (0, True, 0.0, "-0", "00", "+1", "1.0", "1e1", " 1", "9007199254740992"):
            request = ledger()
            request["query"]["key"]["time"] = bad
            with self.subTest(bad=bad), self.assertRaises(runtime.InputError):
                runtime.validate_request(request)
        for valid in ("0", "-1", "9007199254740991", "-9007199254740991"):
            request = ledger()
            request["query"]["key"]["time"] = valid
            runtime.validate_request(request)

    def test_no_hidden_status_or_authority_fields(self):
        for target in ("request", "query", "key", "source", "interpretation"):
            request = ledger()
            obj = {"request": request, "query": request["query"], "key": request["query"]["key"],
                   "source": request["active_sources"][0], "interpretation": request["interpretations"][0]}[target]
            obj["verified"] = True
            with self.subTest(target=target), self.assertRaises(runtime.InputError):
                runtime.validate_request(request)

    def test_complete_scope_is_required_for_matching(self):
        for field in runtime.KEY_FIELDS:
            request = ledger()
            request["query"]["key"][field] = "hidden_motive" if field == "axis" else "2" if field == "time" else "elsewhere"
            with self.subTest(field=field):
                self.assertEqual(runtime.propose(request)["status"], "UNKNOWN")

    def test_source_content_revision_and_registration_all_matter(self):
        for mutation in ("content", "revision", "identity", "revoked"):
            request = ledger()
            if mutation == "revoked":
                request["active_sources"] = []
            else:
                request["interpretations"][0]["source"][mutation] += " changed"
            self.assertEqual(runtime.propose(request)["status"], "UNKNOWN")

    def test_parent_closure_blocks_transitive_query_laundering(self):
        request = ledger()
        request["origins"].extend([{"id": "copied", "parents": ["query"]}, {"id": "independent", "parents": []}])
        request["origins"][1]["parents"] = ["copied", "independent"]
        for ancestry in (["record"], ["record", "copied"], ["record", "independent"], ["record", "copied", "independent", "query"]):
            request["interpretations"][0]["ancestry"] = ancestry
            self.assertEqual(runtime.propose(request)["status"], "UNKNOWN")

    def test_disconnected_closed_cycle_terminates_without_inventing_authority(self):
        request = ledger()
        request["origins"].append({"id": "parent", "parents": ["record"]})
        request["origins"][1]["parents"] = ["parent"]
        self.assertEqual(runtime.propose(request)["status"], "UNKNOWN")
        request["interpretations"][0]["ancestry"].append("parent")
        self.assertEqual(runtime.propose(request)["status"], "SUPPORTED")
        # This is conditional provenance closure, not proof of external independence.
        self.assertIn("AUTHORED_SCENARIO", runtime.PROOF_SCOPE[runtime.AUTHORED_PROFILE])

    def test_missing_or_duplicate_origin_identity_is_invalid(self):
        for mutate in (lambda x: x["origins"][1]["parents"].append("missing"),
                       lambda x: x["origins"].append(deepcopy(x["origins"][1])),
                       lambda x: x["interpretations"][0]["ancestry"].append("record")):
            request = ledger()
            mutate(request)
            with self.assertRaises(runtime.InputError):
                runtime.validate_request(request)

    def test_resource_exhaustion_has_no_partial_witnesses(self):
        request = ledger()
        request["budget"] = 0
        self.assertEqual(runtime.propose(request), {"status": "RESOURCE_LIMIT", "support_ids": [], "refutation_ids": [], "selected_ids": []})

    def test_refutation_requires_explicit_same_key_negative(self):
        request = ledger()
        request["interpretations"][0]["key"]["value"] = "another-goal"
        self.assertEqual(runtime.propose(request)["status"], "UNKNOWN")
        request = ledger()
        request["interpretations"][0]["positive"] = False
        self.assertEqual(runtime.propose(request)["status"], "REFUTED")

    def test_original_query_is_not_mutated_by_request_or_proposal(self):
        request = ledger()
        before = deepcopy(request)
        built, _ = runtime.build_request(request)
        built["query"]["key"]["value"] = "changed"
        self.assertEqual(request, before)
        runtime.propose(request)
        self.assertEqual(request, before)

    def test_installed_agency_profile_uses_exact_projection_and_no_client_ledger(self):
        query = {"key": {"axis": "recorded_observation", "entity": runtime.USGS_EVENT,
                         "predicate": "magnitude:mww", "value": "9.1", "unit": "dimensionless",
                         "context": "usgs.preferred-event.v1", "time": "1299822384120", "place": "142.373,38.297,29"},
                 "positive": True, "origin": "query"}
        request, bindings = runtime.build_request({"query": query, "budget": 128}, source_profile=runtime.USGS_PROFILE)
        content = json.loads(request["active_sources"][0]["content"])
        self.assertEqual(content, {"source_sha256": runtime.USGS_RAW_SHA256, "pointer": "/properties/mag", "value": "9.1", "revision": runtime.USGS_REVISION})
        self.assertEqual(bindings[0]["raw_sha256"], runtime.USGS_RAW_SHA256)
        self.assertLess(len(runtime.wire(request).encode()), 4096)
        with self.assertRaises(runtime.InputError):
            runtime.build_request({"query": query, "budget": 128, "active_sources": []}, source_profile=runtime.USGS_PROFILE)

    def test_unavailable_checker_is_unmeasured_with_replayable_input(self):
        with patch.object(runtime, "NATIVE", Path("/unavailable/epistemicMeasurement")):
            result = runtime.execute_request(ledger())
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertIsNone(result["observed"])
        self.assertFalse(result["native_checked"])
        self.assertEqual(result["execution"]["proposal"]["status"], "SUPPORTED")
        self.assertEqual(result["execution"]["input_sha256"], runtime.digest(result["execution"]["input"]))

    def test_full_input_and_source_changes_affect_replay_hash(self):
        first = ledger()
        second = ledger()
        second["query"]["key"]["context"] = "occasion-b"
        third = ledger()
        third["active_sources"][0]["content"] += " source change"
        hashes = set()
        with patch.object(runtime, "NATIVE", Path("/unavailable/epistemicMeasurement")):
            for request in (first, second, third):
                hashes.add(runtime.execute_request(request)["execution"]["input_sha256"])
        self.assertEqual(len(hashes), 3)


@skipUnless(runtime.NATIVE.is_file(), "Build the pinned epistemicMeasurement executable")
class EpistemicNativeTests(TestCase):
    def test_native_preserves_conflict_and_order_of_all_witnesses(self):
        request = ledger()
        negative = deepcopy(request["interpretations"][0])
        negative.update(id="negative", positive=False)
        last = deepcopy(request["interpretations"][0])
        last["id"] = "last"
        request["interpretations"].extend([negative, last])
        result = runtime.execute_request(request)
        self.assertTrue(result["native_checked"], result)
        self.assertEqual(result["observed"], {"status": "CONFLICT", "support_ids": ["witness", "last"],
                                            "refutation_ids": ["negative"], "selected_ids": ["witness", "negative", "last"]})

    def test_native_rejects_omission_and_reordered_certificate(self):
        request = ledger()
        other = deepcopy(request["interpretations"][0])
        other["id"] = "second"
        request["interpretations"].append(other)
        correct = runtime.propose(request)
        for ids in (["witness"], ["second", "witness"], ["witness", "witness"]):
            request["certificate"] = {**correct, "selected_ids": ids}
            result = runtime._native(request)
            self.assertEqual(result["status"], "INVALID_CERTIFICATE")
            self.assertFalse(result["certificate_checked"])
            self.assertEqual(result["selected_ids"], ["witness", "second"])


class EpistemicBenchmarkTests(TestCase):
    def test_frozen_denominators_separate_safety_from_positive_capability(self):
        references = benchmark.load_reference()
        self.assertEqual(len(references), 43)
        expected = {"authored_controls": (32, 7, 20), "agency_record": (11, 1, 8)}
        for group, counts in expected.items():
            cases = [case for case in references if case["group"] == group]
            self.assertEqual((len(cases), sum(case["expected"]["status"] == "SUPPORTED" for case in cases),
                              sum(case["expected"]["status"] == "UNKNOWN" for case in cases)), counts)

    def test_missing_native_does_not_make_unknown_cases_pass(self):
        with patch.object(runtime, "NATIVE", Path("/missing/native")):
            report = benchmark.run(require_native=True)
        self.assertFalse(report["all_cases_native_checked"])
        for case in report["cases"]:
            self.assertEqual(case["comparison"], "UNMEASURED")
            self.assertEqual(case["receipt_sha256"], runtime.digest({key: value for key, value in case.items() if key != "receipt_sha256"}))
        for group in report["groups"].values():
            for metric in group["metrics"].values():
                self.assertEqual(metric["passed"], 0)
                self.assertEqual(metric["unmeasured"], metric["eligible"])

    def test_reference_tampering_is_rejected_not_renormalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.json"
            path.write_bytes(benchmark.REFERENCE.read_bytes() + b" ")
            with patch.object(benchmark, "REFERENCE", path), self.assertRaises(ValueError):
                benchmark.load_reference()

    def test_every_source_and_reference_is_bound_to_installed_identity(self):
        identity = benchmark.identity()
        self.assertEqual(identity["reference_sha256"], runtime.digest({"authored_controls": benchmark.REFERENCE_SHA256, "agency_record": benchmark.AGENCY_REFERENCE_SHA256}))
        self.assertEqual(identity["runtime_sha256"], sha256(Path(runtime.__file__).read_bytes()).hexdigest())
