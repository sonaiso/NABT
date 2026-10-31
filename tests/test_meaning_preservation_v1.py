"""Independent authored controls for the finite observation/transport boundary.

The mathematical expectations below are literal examples, not results obtained
from the producer or a copy of its recurrence. Native integration is separately
identified and is mandatory when NABT_REQUIRE_MEANING_PRESERVATION_NATIVE=1.
"""
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import meaning_preservation_v1 as meaning
from tools import meaning_preservation_cli as cli


def context(**changes):
    return {"speaker": "alice", "addressee": "bob", "time": "t1", "place": "p1", **changes}


def reading(subject="A", object="X", **changes):
    return {"predicate": "hit", "subject": {"kind": "entity", "value": subject},
            "object": {"kind": "entity", "value": object}, "positive": True,
            "tense": "past", "voice": "active", "force": "asserted", **changes}


def packet(alternatives=None, **changes):
    return {"binding": {"source_id": "s1", "revision": "r1", "scope": "episode",
                        "source_text": "نص مؤلف", "convention": "authored-test.v1"},
            "source_context": context(), "alternatives": [reading()] if alternatives is None else alternatives,
            **changes}


def source_request(original=None, decoded=None):
    original = packet() if original is None else deepcopy(original)
    decoded = original if decoded is None else decoded
    # Independent stdlib encoder, not the production encode_packet helper.
    return {"law_id": "nabt.meaning-preservation.v1", "query_id": "joint-readings.v1",
            "codec_id": "strict-json-packet.v1", "cases": [{"case_id": "c1",
            "original": original, "transported_payload": json.dumps(decoded, ensure_ascii=False)}],
            "recipient_context": context(speaker="carol", time="t2", place="p2")}


def native_success():
    return {"schema": "nabt.meaning-preservation.native-response.v1",
            "law_id": "nabt.meaning-preservation.v1", "query_id": "joint-readings.v1",
            "codec_id": "strict-json-packet.v1", "status": "FINITE_CONTRACT_VERIFIED",
            "reason": "ALL_FINITE_CONTRACTS_PRESERVED", "case_id": None,
            "other_case_id": None, "case_count": 1, "world_truth_established": False,
            "whole_arabic_completeness_established": False}


class MeaningObservationTests(unittest.TestCase):
    def test_installed_query_has_hand_authored_whole_tuple(self):
        observed = meaning.observe_packet(packet())
        self.assertEqual(observed, [{"predicate": "hit", "subject": {"kind": "entity", "value": "A"},
            "object": {"kind": "entity", "value": "X"}, "positive": True, "tense": "past",
            "voice": "active", "force": "asserted", "scope": "episode", "convention": "authored-test.v1",
            "time": "t1", "place": "p1"}])

    def test_deixis_uses_source_context_and_keeps_its_tag(self):
        original = packet([reading(subject={})])
        original["alternatives"][0]["subject"] = {"kind": "speaker", "value": ""}
        result = meaning.observe_packet(original)
        self.assertEqual(result[0]["subject"], {"kind": "speaker", "value": "alice"})
        request = source_request(original)
        self.assertEqual(meaning.propose(request)["status"], "FINITE_CONTRACT_VERIFIED")
        request["recipient_context"] = context(speaker="different", time="next-century")
        self.assertEqual(meaning.propose(request)["status"], "FINITE_CONTRACT_VERIFIED")

    def test_alternatives_remain_correlated(self):
        original = packet([reading("A", "X"), reading("B", "Y")])
        swapped = packet([reading("A", "Y"), reading("B", "X")])
        crossed = packet([reading("A", "X"), reading("A", "Y"), reading("B", "X"), reading("B", "Y")])
        for target in (swapped, crossed):
            with self.subTest(target=target):
                self.assertEqual(meaning.propose(source_request(original, target))["reason"], "OBSERVATION_CHANGED")
        self.assertEqual({(row["subject"]["value"], row["object"]["value"])
                          for row in meaning.observe_packet(original)}, {("A", "X"), ("B", "Y")})

    def test_alternative_order_is_irrelevant(self):
        original = packet([reading("A", "X"), reading("B", "Y")])
        decoded = deepcopy(original)
        decoded["alternatives"].reverse()
        self.assertEqual(meaning.propose(source_request(original, decoded))["status"], "FINITE_CONTRACT_VERIFIED")

    def test_role_polarity_tense_voice_force_and_null_object_are_distinct(self):
        variants = [reading("X", "A"), reading(positive=False), reading(tense="future"),
                    reading(voice="passive"), reading(force="quoted"), reading(object=None)]
        # The helper normally constructs entity objects; null is a distinct valid value.
        variants[-1]["object"] = None
        for changed in variants:
            with self.subTest(changed=changed):
                self.assertEqual(meaning.propose(source_request(decoded=packet([changed])))["reason"], "OBSERVATION_CHANGED")

    def test_exact_source_binding_and_context_are_independent_obligations(self):
        for name in ("source_id", "revision", "scope", "source_text", "convention"):
            decoded = packet()
            decoded["binding"][name] += "changed"
            self.assertEqual(meaning.propose(source_request(decoded=decoded))["reason"], "SOURCE_BINDING_CHANGED")
        for name in ("speaker", "addressee", "time", "place"):
            decoded = packet()
            decoded["source_context"][name] += "changed"
            self.assertEqual(meaning.propose(source_request(decoded=decoded))["reason"], "SOURCE_CONTEXT_CHANGED")

    def test_actual_payload_collision_precedes_per_case_difference(self):
        request = source_request()
        second = deepcopy(request["cases"][0])
        second["case_id"] = "c2"
        second["original"]["alternatives"][0]["positive"] = False
        request["cases"].append(second)
        decision = meaning.propose(request)
        self.assertEqual((decision["status"], decision["reason"], decision["case_id"], decision["other_case_id"]),
                         ("CONTRACT_VIOLATION", "FIBER_COLLISION", "c1", "c2"))

    def test_equal_observations_can_share_actual_payload(self):
        request = source_request()
        second = deepcopy(request["cases"][0])
        second["case_id"] = "c2"
        request["cases"].append(second)
        self.assertEqual(meaning.propose(request)["status"], "FINITE_CONTRACT_VERIFIED")

    def test_different_json_layout_is_actually_decoded(self):
        original = packet()
        request = source_request(original)
        request["cases"][0]["transported_payload"] = json.dumps(original, indent=3, ensure_ascii=True)
        self.assertEqual(meaning.propose(request)["status"], "FINITE_CONTRACT_VERIFIED")
        self.assertEqual(meaning.decode_packet(meaning.encode_packet(original)), original)


class MeaningWireTests(unittest.TestCase):
    def test_duplicate_decoded_keys_rejected_in_outer_and_inner_json(self):
        for raw in ('{"a":1,"a":2}', '{"a":1,"\\u0061":2}'):
            with self.assertRaises(meaning.InputError):
                meaning.strict_loads(raw)
        request = source_request()
        request["cases"][0]["transported_payload"] = '{"binding":{},"\\u0062inding":{}}'
        self.assertEqual(meaning.propose(request)["status"], "INVALID_INPUT")

    def test_bool_integer_confusion_never_satisfies_polarity(self):
        for value in (1, 0, "true", None, [], 1.0):
            request = source_request()
            request["cases"][0]["original"]["alternatives"][0]["positive"] = value
            self.assertEqual(meaning.propose(request)["status"], "INVALID_INPUT")

    def test_unknown_field_law_query_codec_and_claimed_authority_rejected(self):
        for field in ("law_id", "query_id", "codec_id"):
            request = source_request()
            request[field] = "foreign"
            self.assertEqual(meaning.propose(request)["status"], "INVALID_INPUT")
        for key, value in (("verified", True), ("native_path", "/tmp/alternate"),
                           ("world_truth_established", True), ("sha256", "f" * 64)):
            request = source_request()
            request[key] = value
            self.assertEqual(meaning.propose(request)["status"], "INVALID_INPUT")

    def test_empty_arrays_duplicate_ids_and_readings_rejected(self):
        requests = []
        empty_cases = source_request()
        empty_cases["cases"] = []
        requests.append(empty_cases)
        empty_alts = source_request()
        empty_alts["cases"][0]["original"]["alternatives"] = []
        requests.append(empty_alts)
        duplicate = source_request()
        duplicate["cases"].append(deepcopy(duplicate["cases"][0]))
        requests.append(duplicate)
        duplicate_reading = source_request()
        duplicate_reading["cases"][0]["original"]["alternatives"].append(reading())
        requests.append(duplicate_reading)
        for request in requests:
            self.assertEqual(meaning.propose(request)["status"], "INVALID_INPUT")

    def test_resource_bounds_remain_exhaustion(self):
        cases = source_request()
        cases["cases"] = [{**deepcopy(cases["cases"][0]), "case_id": "case-" + str(n)} for n in range(65)]
        metadata = source_request()
        metadata["recipient_context"]["speaker"] = "ع" * 257
        alternatives = source_request()
        alternatives["cases"][0]["original"]["alternatives"] = [reading("entity-" + str(n)) for n in range(65)]
        for request in (cases, metadata, alternatives):
            self.assertEqual(meaning.propose(request)["status"], "RESOURCE_EXHAUSTED")
        with self.assertRaises(meaning.ResourceLimit):
            meaning.strict_loads(b" " * (meaning.MAX_REQUEST_BYTES + 1))

    def test_strict_unicode_and_context_controls_preserve_source(self):
        for raw in (b'"\xff"', '"\\ud800"', '"\\udfff"'):
            with self.assertRaises(meaning.InputError):
                meaning.strict_loads(raw)
        for bad in ("x\x00", "x\x7f", "x\x85"):
            request = source_request()
            request["recipient_context"]["speaker"] = bad
            self.assertEqual(meaning.propose(request)["status"], "INVALID_INPUT")
        original = packet()
        original["binding"]["source_text"] = " \n\t\x00نص "
        original["source_context"]["speaker"] = " "
        self.assertEqual(meaning.decode_packet(meaning.encode_packet(original)), original)

    def test_depth_is_root_zero_json_value_depth(self):
        value = 0
        for _ in range(32):
            value = [value]
        self.assertEqual(meaning.strict_loads(json.dumps(value)), value)
        with self.assertRaises(meaning.ResourceLimit):
            meaning.strict_loads(json.dumps([value]))
        empty = []
        for _ in range(32):
            empty = [empty]
        self.assertEqual(meaning.strict_loads(json.dumps(empty)), empty)

    def test_numbers_are_strict_and_no_entity_can_impersonate_deictic_term(self):
        for raw in ("-0", "1.0", "1e0", "NaN", "Infinity"):
            with self.assertRaises(meaning.InputError):
                meaning.strict_loads(raw)
        request = source_request()
        request["cases"][0]["original"]["alternatives"][0]["subject"] = {"kind": "speaker", "value": "alice"}
        self.assertEqual(meaning.propose(request)["status"], "INVALID_INPUT")


class MeaningRuntimeBoundaryTests(unittest.TestCase):
    def test_no_native_fallback(self):
        with patch.object(meaning, "_native", side_effect=FileNotFoundError):
            result = meaning.evaluate_authored(source_request())
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(result["verified"])
        self.assertFalse(result["native_checked"])
        self.assertEqual(result["proposal"]["status"], "FINITE_CONTRACT_VERIFIED")

    def test_unexpected_native_failure_and_timeout_are_different(self):
        for error, status in ((ValueError("process failed"), "VERIFICATION_FAILED"),
                              (subprocess.TimeoutExpired("native", 30), "RESOURCE_EXHAUSTED")):
            with patch.object(meaning, "_native", side_effect=error):
                result = meaning.evaluate_authored(source_request())
            self.assertEqual(result["status"], status)
            self.assertFalse(result["verified"])

    def test_typed_native_mutations_cannot_grant_authority(self):
        for field, changed in (("case_count", True), ("world_truth_established", True),
                                ("whole_arabic_completeness_established", True), ("law_id", "other")):
            native = native_success()
            native[field] = changed
            with patch.object(meaning, "_native", return_value=native):
                result = meaning.evaluate_authored(source_request())
            self.assertEqual(result["status"], "VERIFICATION_FAILED")

    def test_authority_is_finite_authored_even_when_decision_is_checked(self):
        # Explicit boundary mock, not native execution or an acceptance measurement.
        with patch.object(meaning, "_native", return_value=native_success()):
            result = meaning.evaluate_authored(source_request())
        self.assertEqual(result["authority"], "AUTHORED_PREMISES_FINITE_CONTRACT")
        self.assertIsNone(result["producer"])
        self.assertFalse(result["producer_chain_complete"])
        for flag in meaning.FLAGS:
            self.assertIs(result[flag], False)

    def test_exact_replay_uses_independent_request_and_no_mutable_aliases(self):
        request = source_request()
        with patch.object(meaning, "_native", return_value=native_success()):
            report = meaning.evaluate_authored(request)
            self.assertTrue(meaning.verify(report, expected_request=request)["valid"])
            modified = deepcopy(report)
            modified["world_truth_established"] = True
            self.assertFalse(meaning.verify(modified, expected_request=request)["valid"])
            foreign = deepcopy(request)
            foreign["recipient_context"]["speaker"] = "elsewhere"
            self.assertFalse(meaning.verify(report, expected_request=foreign)["valid"])
            request["cases"][0]["original"]["binding"]["source_text"] = "mutated"
            self.assertEqual(report["contract_request"]["cases"][0]["original"]["binding"]["source_text"], "نص مؤلف")

    def test_native_process_nonzero_is_not_a_checked_semantic_violation(self):
        def process(*args, **kwargs):
            kwargs["stdout"].write(json.dumps(native_success()).encode())
            return subprocess.CompletedProcess(args[0], 1)
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "present-native"
            fake.write_bytes(b"not executed")
            with patch.object(meaning, "NATIVE", fake), patch.object(meaning.subprocess, "run", side_effect=process):
                with self.assertRaises(ValueError):
                    meaning._native(source_request())

    def test_cli_strict_input_and_exit_categories(self):
        categories = {"FINITE_CONTRACT_VERIFIED": 0, "VERIFIED_RECEIPT": 0,
                      "INVALID_INPUT": 2, "INVALID_RECEIPT": 2, "CONTRACT_VIOLATION": 3,
                      "DEFER": 3, "REJECTED_IN_SCOPE": 3, "VERIFICATION_UNAVAILABLE": 4,
                      "VERIFICATION_FAILED": 4, "RESOURCE_EXHAUSTED": 5}
        for status, expected in categories.items():
            self.assertEqual(cli.exit_code({"status": status}), expected)
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "request.json"
            raw.write_text('{"a":1,"\\u0061":2}', encoding="utf-8")
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                code = cli.main(["authored", "--request", str(raw)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "INVALID_INPUT")


class MeaningNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not meaning.NATIVE.is_file():
            if os.environ.get("NABT_REQUIRE_MEANING_PRESERVATION_NATIVE") == "1":
                raise AssertionError("Required meaningPreservationV1 native executable is absent")
            raise unittest.SkipTest("meaningPreservationV1 is not built; no native success is claimed")

    def test_genuine_native_roundtrip_and_replay(self):
        request = source_request()
        result = meaning.evaluate_authored(request)
        self.assertEqual(result["status"], "FINITE_CONTRACT_VERIFIED")
        self.assertTrue(result["native_checked"])
        self.assertTrue(meaning.verify(result, expected_request=request)["valid"])

    def test_genuine_native_joint_correlation_counterexample(self):
        source = packet([reading("A", "X"), reading("B", "Y")])
        target = packet([reading("A", "Y"), reading("B", "X")])
        result = meaning.evaluate_authored(source_request(source, target))
        self.assertEqual(result["status"], "CONTRACT_VIOLATION")
        self.assertEqual(result["native_result"]["reason"], "OBSERVATION_CHANGED")
        self.assertTrue(result["native_checked"])
        self.assertFalse(result["verified"])

    def test_genuine_native_inner_duplicate_key_rejected(self):
        request = source_request()
        request["cases"][0]["transported_payload"] = '{"binding":{},"\\u0062inding":{}}'
        run = subprocess.run([str(meaning.NATIVE)], input=(json.dumps(request) + "\n").encode(),
                             capture_output=True, timeout=30, check=False)
        self.assertEqual(run.returncode, 2)
        report = json.loads(run.stdout)
        self.assertEqual(report["status"], "INVALID_INPUT")


class MeaningProductiveNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = ("meaningPreservationV1", "productiveClauseV1", "alignedAcquisition",
                 "licensedInference", "connectedAcquisitionV3")
        if not all((meaning.ROOT / "formal/.lake/build/bin" / name).is_file() for name in names):
            if os.environ.get("NABT_REQUIRE_MEANING_PRESERVATION_NATIVE") == "1":
                raise AssertionError("Required productive source chain is not built")
            raise unittest.SkipTest("Complete productive native chain is not built")

    def test_actual_vso_vos_and_mutated_channel(self):
        for text in ("ضَرَبَ زَيْدٌ عَمْرًا", "ضَرَبَ عَمْرًا زَيْدٌ"):
            with self.subTest(text=text):
                result = meaning.evaluate_productive(text, source_context=context(), recipient_context=context())
                self.assertEqual(result["status"], "FINITE_CONTRACT_VERIFIED")
                self.assertTrue(result["producer_chain_complete"])
                original = result["contract_request"]["cases"][0]["original"]
                self.assertEqual(original["alternatives"][0]["subject"]["value"], "ZAYD")
                self.assertEqual(original["alternatives"][0]["object"]["value"], "AMR")
                changed = deepcopy(original)
                row = changed["alternatives"][0]
                row["subject"], row["object"] = row["object"], row["subject"]
                wrong = meaning.evaluate_productive(text, source_context=context(), recipient_context=context(),
                                                     transported_payload=json.dumps(changed, ensure_ascii=False))
                self.assertEqual(wrong["status"], "CONTRACT_VIOLATION")
                self.assertTrue(wrong["producer_chain_complete"])

    def test_actual_pending_and_scoped_rejection_cannot_acquire_transport_authority(self):
        for text, expected in (("ضرب زيد عمرا", "DEFER"), ("ضَرَبَ زَيْدٌ بَكْرٌ", "REJECTED_IN_SCOPE")):
            with self.subTest(text=text):
                result = meaning.evaluate_productive(text, source_context=context(), recipient_context=context())
                self.assertEqual(result["status"], expected)
                self.assertFalse(result["verified"])
                self.assertFalse(result["native_checked"])
                self.assertIsNone(result["contract_request"])


if __name__ == "__main__":
    unittest.main()
