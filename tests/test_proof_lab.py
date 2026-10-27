"""Adversarial transport cases and native end-to-end proof-lab examples."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import proof_lab as lab

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Fixed public test fixture, never a deployment key.
TEST_KEY = bytes(range(32))


def request(**updates):
    value = json.loads(lab.SMOKE_PAYLOAD)
    value.update(updates)
    return json.dumps(value, ensure_ascii=False)


def fake_identity():
    return {"code_sha": "a" * 40, "native_sha256": "b" * 64,
            "runner_sha256": "c" * 64, "runtime_sha256": "d" * 64,
            "toolchain": "leanprover/lean4:v4.34.1"}


def unknown_result():
    return {**{key: False for key in lab.BOOLEAN_FLAGS},
            "status": "UNKNOWN", "authority": "UNVERIFIED_PROPOSAL",
            "schema": "nabt.licensed-inference-result.v1", "law_id": lab.SCOPE["law_id"],
            "accepted_language": lab.SCOPE["accepted_language"]}


def dispatch_event(payload, request_id=lab.SMOKE_ID):
    envelope = lab.encrypt_envelope(request_id, payload.encode("utf-8"), TEST_KEY,
                                    maximum=lab.MAX_PAYLOAD_BYTES)
    return {"inputs": {"request_id": request_id, "payload": json.dumps(envelope)}}


class TransportValidation(unittest.TestCase):
    def test_exact_source_and_whitespace_are_preserved(self):
        source = " \nإِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ.\t "
        self.assertEqual(lab.validate_payload(request(source_text=source))["source_text"], source)

    def test_canonical_uuid4_required(self):
        for value in (None, 1, True, "not-a-uuid", lab.SMOKE_ID.replace("-", ""),
                      "11111111-1111-1111-1111-111111111111", "AAAA0000-0000-4000-8000-000000000001"):
            with self.subTest(value=value), self.assertRaises(lab.RequestError):
                lab.validate_id(value)
        self.assertEqual(lab.validate_id(lab.SMOKE_ID), lab.SMOKE_ID)

    def test_duplicate_keys_and_nonfinite_constants_are_rejected(self):
        base = '{"schema":"nabt.proof-lab-request.v1","mode":"benchmark"'
        for text in (base + ',"mode":"benchmark"}', base + ',"m\\u006fde":"benchmark"}',
                     request(budget={"max_atoms": float("nan")}),
                     request(budget={"max_atoms": float("inf")}),
                     request().replace('"budget": {}', '"budget":{"max_atoms":1,"max_atoms":2}')):
            if text == request():
                continue
            with self.subTest(text=text), self.assertRaises(lab.RequestError):
                lab.validate_payload(text)
        duplicate = request(budget={}).replace('"budget": {}', '"budget":{"max_atoms":1,"max_atoms":2}')
        with self.assertRaises(lab.RequestError):
            lab.validate_payload(duplicate)

    def test_unknown_fields_cannot_supply_code_or_authority(self):
        for key in ("verified", "all_arabic_complete", "source_id", "executable", "path", "rules", "lean_code"):
            with self.subTest(key=key), self.assertRaises(lab.RequestError):
                lab.validate_payload(request(**{key: True}))

    def test_budgets_reject_booleans_and_out_of_range_values(self):
        for key, maximum in lab.BUDGET_LIMITS.items():
            for value in (True, False, -1, maximum + 1, 1.0, "1", None):
                with self.subTest(key=key, value=value), self.assertRaises(lab.RequestError):
                    lab.validate_payload(request(budget={key: value}))
            self.assertEqual(lab.validate_payload(request(budget={key: 0}))["budget"][key], 0)
        for value in (None, [], True, {"max_source_bytes": 1}):
            with self.assertRaises(lab.RequestError):
                lab.validate_payload(request(budget=value))

    def test_benchmark_accepts_no_user_gold_or_source(self):
        payload = json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "benchmark"})
        self.assertEqual(lab.validate_payload(payload)["mode"], "benchmark")
        for extra in ({"source_text": "سار زيد"}, {"budget": {}}, {"gold": []}):
            with self.assertRaises(lab.RequestError):
                lab.validate_payload(json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "benchmark", **extra}))

    def test_unknown_mode_or_schema_or_non_object(self):
        for text in (request(mode="aggregate_fixture"), request(mode=True),
                     request(schema="future"), "[]", "null", "true", "{}"):
            with self.assertRaises(lab.RequestError):
                lab.validate_payload(text)

    def test_utf8_byte_limits_are_not_character_limits(self):
        for text in (request(source_text="س" * (lab.MAX_SOURCE_BYTES // 2 + 1)),
                     request(query_text="س" * (lab.MAX_QUERY_BYTES // 2 + 1)),
                     " " * (lab.MAX_PAYLOAD_BYTES + 1), b"\xff", request(source_text="\ud800")):
            with self.assertRaises(lab.RequestError):
                lab.validate_payload(text)

    def test_blank_text_and_malformed_json_are_rejected(self):
        for text in (request(source_text=" \n\t"), request(query_text=42), "{", '"unterminated', "[" * 10000):
            with self.assertRaises(lab.RequestError):
                lab.validate_payload(text)

    def test_invalid_input_never_calls_engine(self):
        with patch.object(lab, "evaluate", side_effect=AssertionError("must not run")):
            result = lab.run_payload(lab.SMOKE_ID, request(verified=True))
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertIs(result["all_arabic_complete"], False)
        self.assertNotIn("result", result)

    def test_payload_digest_binds_exact_wire_text(self):
        left, right = lab.SMOKE_PAYLOAD, " " + lab.SMOKE_PAYLOAD + "\n"
        with patch.object(lab, "_identity", side_effect=fake_identity):
            a = lab.run_payload(lab.SMOKE_ID, left, prepare=True)
            b = lab.run_payload(lab.SMOKE_ID, right, prepare=True)
        self.assertEqual(a["payload_sha256"], hashlib.sha256(left.encode()).hexdigest())
        self.assertNotEqual(a["payload_sha256"], b["payload_sha256"])
        self.assertEqual(a["status"], "PREPARED")


class AuthorityAndFailure(unittest.TestCase):
    def test_missing_native_binary_is_not_a_proof(self):
        identity = fake_identity() | {"native_sha256": None}
        with patch.object(lab, "_identity", return_value=identity), patch.object(lab, "evaluate") as engine:
            response = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
        engine.assert_not_called()
        self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
        self.assertNotIn("result", response)

    def test_engine_flags_cannot_be_promoted(self):
        for forged in (
            {"status": "SUPPORTED", "all_arabic_complete": True, "world_truth_established": False},
            {"status": "SUPPORTED", "all_arabic_complete": False, "world_truth_established": True},
            {"status": "SUPPORTED", "all_arabic_complete": False, "world_truth_established": False,
             "verified": True, "native_checked": False},
        ):
            with patch.object(lab, "_identity", side_effect=fake_identity), patch.object(lab, "evaluate", return_value=forged):
                response = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
            self.assertEqual(response["status"], "EXECUTION_FAILED")
            self.assertNotIn("result", response)
            self.assertIs(response["all_arabic_complete"], False)

    def test_non_boolean_authority_flags_and_unknown_statuses_are_rejected(self):
        for field in lab.BOOLEAN_FLAGS:
            for value in (0, 1, "false", None):
                with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                    lab._authority_guard(unknown_result() | {field: value})
        for status in ("PREPARED", "FAKE_SUCCESS", 1, None, []):
            with self.assertRaises(RuntimeError):
                lab._authority_guard(unknown_result() | {"status": status})
        with self.assertRaises(RuntimeError):
            lab._authority_guard(unknown_result() | {"status": "SUPPORTED"})

    def test_internal_exception_does_not_echo_private_input(self):
        with patch.object(lab, "_identity", side_effect=fake_identity), patch.object(lab, "evaluate", side_effect=ValueError("PRIVATE_SECRET_TEXT")):
            response = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
        self.assertEqual(response["status"], "EXECUTION_FAILED")
        self.assertNotIn("PRIVATE_SECRET_TEXT", json.dumps(response))

    def test_changed_execution_identity_discards_result(self):
        raw = unknown_result()
        with patch.object(lab, "_identity", side_effect=[fake_identity(), fake_identity() | {"native_sha256": "f" * 64}]), patch.object(lab, "evaluate", return_value=raw):
            response = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
        self.assertEqual(response["status"], "EXECUTION_FAILED")
        self.assertNotIn("result", response)

    def test_result_budget_is_a_resource_stop_not_a_linguistic_rejection(self):
        raw = unknown_result() | {"unclassified_spans": ["x" * lab.MAX_RESULT_BYTES]}
        with patch.object(lab, "_identity", side_effect=fake_identity), patch.object(lab, "evaluate", return_value=raw):
            response = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
        self.assertEqual(response["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(response["error"], "RESULT_BYTE_LIMIT")
        self.assertNotIn("result", response)
        self.assertLess(len(json.dumps(response).encode()), lab.MAX_RESULT_BYTES)


@unittest.skipUnless(CRYPTO_AVAILABLE, "optional encrypted transport dependencies are installed by proof-lab workflow")
class EventTransport(unittest.TestCase):
    def test_dispatch_inputs_are_read_as_data_and_not_logged(self):
        private_text = "$(touch /tmp/nabt-unwanted-command) PRIVATE_SENTINEL"
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            event, out, metadata = [directory / name for name in ("event.json", "result.json", "github-output")]
            payload = request(source_text=private_text)
            event.write_text(json.dumps(dispatch_event(payload)))
            stream = io.StringIO()
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "NABT_LAB_TRANSPORT_KEY": TEST_KEY.hex()}), patch.object(lab, "_identity", side_effect=fake_identity), redirect_stdout(stream):
                status = lab.main(["--event-file", str(event), "--output", str(out), "--prepare", "--github-output", str(metadata)])
            self.assertEqual(status, 0)
            decoded = lab.decrypt_envelope(lab.SMOKE_ID, out.read_text(), TEST_KEY, lab.MAX_RESULT_BYTES)
            self.assertEqual(json.loads(decoded)["status"], "PREPARED")
            self.assertEqual(json.loads(decoded)["payload_sha256"], hashlib.sha256(payload.encode()).hexdigest())
            self.assertNotIn(private_text, stream.getvalue())
            self.assertNotIn("payload_sha256", stream.getvalue())
            self.assertNotIn(private_text, out.read_text())
            self.assertNotIn("PREPARED", out.read_text())
            self.assertEqual(metadata.read_text(), "valid=true\nartifact_name=nabt-lab-" + lab.SMOKE_ID + "\nattested_source=false\n")

    def test_bad_uuid_cannot_inject_github_output(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            event, out, metadata = [directory / name for name in ("event.json", "result.json", "github-output")]
            event.write_text(json.dumps({"inputs": {"request_id": "bad\nvalid=true", "payload": lab.SMOKE_PAYLOAD}}))
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch"}), redirect_stdout(io.StringIO()):
                status = lab.main(["--event-file", str(event), "--output", str(out), "--prepare", "--github-output", str(metadata)])
            self.assertEqual(status, 2)
            self.assertFalse(metadata.exists())
            self.assertFalse(out.exists())

    def test_missing_or_unexpected_event_input_is_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            event, out = directory / "event.json", directory / "result.json"
            for data in ({}, {"inputs": {"request_id": lab.SMOKE_ID}}, {"inputs": {"request_id": lab.SMOKE_ID, "payload": lab.SMOKE_PAYLOAD, "code": "bad"}}):
                event.write_text(json.dumps(data))
                with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch"}), redirect_stdout(io.StringIO()):
                    self.assertEqual(lab.main(["--event-file", str(event), "--output", str(out)]), 2)
                self.assertFalse(out.exists())

    def test_encrypt_decrypt_roundtrip_nonce_fresh_and_wrong_aad_rejected(self):
        plaintext = lab.SMOKE_PAYLOAD.encode()
        first = lab.encrypt_envelope(lab.SMOKE_ID, plaintext, TEST_KEY)
        second = lab.encrypt_envelope(lab.SMOKE_ID, plaintext, TEST_KEY)
        self.assertNotEqual(first["nonce"], second["nonce"])
        self.assertEqual(lab.decrypt_envelope(lab.SMOKE_ID, json.dumps(first), TEST_KEY), plaintext)
        for key, request_id in ((bytes(reversed(TEST_KEY)), lab.SMOKE_ID),
                                (TEST_KEY, "00000000-0000-4000-8000-000000000002")):
            with self.assertRaises(lab.RequestError):
                lab.decrypt_envelope(request_id, json.dumps(first), key)

    def test_tampering_and_noncanonical_base64_are_rejected(self):
        envelope = lab.encrypt_envelope(lab.SMOKE_ID, lab.SMOKE_PAYLOAD.encode(), TEST_KEY)
        replacement = "B" if envelope["ciphertext"].startswith("A") else "A"
        for changed in (envelope | {"ciphertext": replacement + envelope["ciphertext"][1:]},
                        envelope | {"nonce": envelope["nonce"] + "="},
                        envelope | {"nonce": "AAAA"}, envelope | {"ciphertext": "AAAA"},
                        envelope | {"extra": True}, envelope | {"schema": lab.REQUEST_SCHEMA}):
            with self.assertRaises(lab.RequestError):
                lab.decrypt_envelope(lab.SMOKE_ID, json.dumps(changed), TEST_KEY)

    def test_crypto_size_and_key_boundaries(self):
        for key in (None, "", "00" * 31, "00" * 33, " " + TEST_KEY.hex(), "g" * 64):
            with self.assertRaises(lab.RequestError):
                lab.transport_key(key)
        self.assertEqual(lab.transport_key(TEST_KEY.hex()), TEST_KEY)
        with self.assertRaises(lab.RequestError):
            lab.encrypt_envelope(lab.SMOKE_ID, b"x" * 5, TEST_KEY, maximum=4)
        envelope = lab.encrypt_envelope(lab.SMOKE_ID, b"x" * 5, TEST_KEY)
        with self.assertRaises(lab.RequestError):
            lab.decrypt_envelope(lab.SMOKE_ID, json.dumps(envelope), TEST_KEY, maximum=4)

    def test_plaintext_dispatch_and_missing_key_never_fall_back(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            event, out = directory / "event.json", directory / "result.json"
            for value, key in (({"inputs": {"request_id": lab.SMOKE_ID, "payload": lab.SMOKE_PAYLOAD}}, TEST_KEY.hex()),
                               (dispatch_event(lab.SMOKE_PAYLOAD), "")):
                event.write_text(json.dumps(value))
                with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "NABT_LAB_TRANSPORT_KEY": key}), redirect_stdout(io.StringIO()):
                    self.assertEqual(lab.main(["--event-file", str(event), "--output", str(out)]), 2)
                self.assertFalse(out.exists())


@unittest.skipUnless((lab.ROOT / "formal/.lake/build/bin/licensedInference").is_file(), "native Lean checker is built by proof-lab workflow")
class NativeProofLab(unittest.TestCase):
    @unittest.skipUnless(CRYPTO_AVAILABLE, "optional encrypted transport dependencies are installed by proof-lab workflow")
    def test_encrypted_dispatch_runs_native_and_retains_only_ciphertext(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            event, out = directory / "event.json", directory / "result.json"
            event.write_text(json.dumps(dispatch_event(lab.SMOKE_PAYLOAD)))
            stream = io.StringIO()
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "NABT_LAB_TRANSPORT_KEY": TEST_KEY.hex()}), redirect_stdout(stream):
                status = lab.main(["--event-file", str(event), "--output", str(out)])
            self.assertEqual(status, 0)
            encrypted_text = out.read_text()
            decoded = json.loads(lab.decrypt_envelope(lab.SMOKE_ID, encrypted_text, TEST_KEY, lab.MAX_RESULT_BYTES))
            self.assertEqual(decoded["status"], "SUPPORTED")
            self.assertIs(decoded["result"]["native_checked"], True)
            self.assertEqual(decoded["payload_sha256"], hashlib.sha256(lab.SMOKE_PAYLOAD.encode()).hexdigest())
            self.assertNotIn("SUPPORTED", stream.getvalue())
            self.assertNotIn("source_text", encrypted_text)
            self.assertEqual(set(json.loads(encrypted_text)), {"schema", "nonce", "ciphertext"})

    def test_fully_vowelized_forward_inference(self):
        response = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
        self.assertEqual(response["status"], "SUPPORTED")
        self.assertIs(response["result"]["native_checked"], True)
        self.assertIs(response["all_arabic_complete"], False)
        self.assertIs(response["world_truth_established"], False)

    def test_denied_antecedent_does_not_prove_denied_consequent(self):
        payload = request(source_text="إن عرف زيد الحق سار زيد. لم يعرف زيد الحق.", query_text="هل لم يسر زيد؟")
        response = lab.run_payload(lab.SMOKE_ID, payload)
        self.assertEqual(response["status"], "UNKNOWN")
        self.assertIs(response["result"]["native_checked"], True)

    def test_hidden_subject_and_resource_stop_remain_distinct(self):
        hidden = lab.run_payload(lab.SMOKE_ID, request(source_text="سار زيد إن عرف الحق"))
        limited = lab.run_payload(lab.SMOKE_ID, request(budget={"max_clauses": 0}))
        self.assertEqual(hidden["status"], "UNKNOWN")
        self.assertEqual(hidden["result"]["parse_reason"], "UNRESOLVED_REFERENCE")
        self.assertEqual(limited["status"], "RESOURCE_EXHAUSTED")

    def test_fixed_benchmark_reexecutes_and_retains_every_outcome(self):
        response = lab.run_payload(lab.SMOKE_ID, json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "benchmark"}))
        self.assertEqual(response["status"], "BENCHMARK_COMPLETE")
        report = response["benchmark"]
        self.assertEqual(report["summary"]["cases"], 38)
        self.assertEqual(len(report["rows"]), 38)
        self.assertEqual(sum(report["summary"][key] for key in ("pass", "fail", "unmeasured")), 38)
        self.assertEqual(report["summary"]["fail"], 1)
        self.assertEqual(report["summary"]["authority"]["overclaims"], 0)
        self.assertEqual(report["summary"]["target_observations"]["false_supported_literals"], 0)
        self.assertTrue(any(row["outcome"] == "FAIL" for row in report["rows"]))
        self.assertIs(response["all_arabic_complete"], False)


if __name__ == "__main__":
    unittest.main()
