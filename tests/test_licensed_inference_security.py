"""Independent adversarial boundaries, authored without benchmark gold.

These tests do not derive an oracle by rerunning the production parser. They
exercise complete original text, replayed native output and raw subprocess
transport. Native tests require the real installed executable; CI enforces its
presence before discovery. Passing this finite suite is not Arabic completeness.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.licensed_inference import InferenceBudget, evaluate
from tools.licensed_inference import runtime, sources


FACT = "سار زيد."
QUESTION = "هل سار زيد؟"
NATIVE = runtime.ROOT / "formal/.lake/build/bin/licensedInference"


def failure(**changes):
    return {"law_id": runtime.LAW_ID, "verified": False, "status": "UNKNOWN",
            "error": "OUTSIDE_FRAGMENT", "message": "outside the installed fragment",
            "authority": runtime.AUTHORITY, "all_arabic_complete": False,
            "world_truth_established": False, **changes}


class SafetyAssertions:
    def no_world_claim(self, result):
        self.assertIs(result["world_truth_established"], False)
        self.assertIs(result["premise_world_truth_established"], False)
        self.assertIs(result["all_arabic_complete"], False)

    def no_certificate(self, result, status=None):
        if status is not None:
            self.assertEqual(result["status"], status, result.get("reason"))
        self.assertIs(result["verified"], False)
        self.assertIs(result["all_readings_complete"], False)
        self.assertIs(result["closures_checked"], False)
        self.assertEqual(result["readings"], [])
        self.assertEqual(result["closure_records"], [])
        self.no_world_claim(result)


class NativeTransportSecurity(SafetyAssertions, unittest.TestCase):
    def test_malformed_failure_scalar_types_never_escape(self):
        for field in ("status", "error"):
            for value in ([], {}, None, 0, False):
                with self.subTest(field=field, value=value), patch.object(
                        runtime, "_native", return_value=failure(**{field: value})):
                    result = evaluate("سار زيد ربما", QUESTION)
                self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_duplicate_native_keys_and_trailing_json_are_rejected(self):
        encoded = runtime.wire(failure())
        variants = [encoded[:-1] + ',"verified":false}', encoded + encoded,
                    encoded + "not-json", encoded.replace('"message":"outside the installed fragment"',
                                                            '"message":NaN')]
        for stdout in variants:
            with self.subTest(stdout=stdout), patch.object(runtime.subprocess, "run",
                    return_value=SimpleNamespace(stdout=stdout, returncode=0)):
                result = evaluate("سار زيد ربما", QUESTION)
            self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_nonobject_native_json_is_rejected(self):
        for stdout in ("[]", "null", "true", "1", '"SUPPORTED"'):
            with self.subTest(stdout=stdout), patch.object(runtime.subprocess, "run",
                    return_value=SimpleNamespace(stdout=stdout, returncode=0)):
                result = evaluate(FACT, QUESTION)
            self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_missing_native_binary_is_not_a_linguistic_verdict(self):
        with patch.object(runtime.subprocess, "run", side_effect=FileNotFoundError("checker absent")):
            result = evaluate(FACT, QUESTION)
        self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_timeout_is_not_complete_or_linguistic_rejection(self):
        with patch.object(runtime.subprocess, "run", side_effect=subprocess.TimeoutExpired("native", 60)):
            result = evaluate(FACT, QUESTION)
        self.no_certificate(result, "RESOURCE_EXHAUSTED")

    def test_missing_scholarly_replay_prevents_native_execution(self):
        with tempfile.TemporaryDirectory() as root, patch.object(runtime, "_native") as native:
            result = evaluate(FACT, QUESTION, root=Path(root))
        native.assert_not_called()
        self.no_certificate(result, "SOURCE_UNAVAILABLE")

    def test_source_byte_mutation_prevents_native_execution(self):
        document = json.loads((sources.ROOT / sources.REVIEW_PATH).read_text())
        paths = [sources.REVIEW_PATH]
        paths += [row["path"] for row in document["source_registries"]]
        paths += [row["local_path"] for row in document["sources"]]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in paths:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(sources.ROOT / relative, target)
            target = root / document["sources"][0]["local_path"]
            raw = bytearray(target.read_bytes())
            raw[-1] ^= 1
            target.write_bytes(raw)
            with patch.object(runtime, "_native") as native:
                result = evaluate(FACT, QUESTION, root=root)
        native.assert_not_called()
        self.no_certificate(result, "SOURCE_UNAVAILABLE")

    def test_utf8_byte_budget_is_checked_before_parser_and_source_replay(self):
        # Character count fits; UTF-8 byte count does not.
        with patch.object(runtime, "read_source") as parser, patch.object(sources, "build_inventory") as replay:
            result = evaluate(FACT, QUESTION, budget=InferenceBudget(max_source_bytes=len(FACT)))
        parser.assert_not_called()
        replay.assert_not_called()
        self.no_certificate(result, "RESOURCE_EXHAUSTED")

    def test_no_caller_authority_switches(self):
        for name in ("verified", "all_readings_complete", "world_truth_established",
                     "is_empirical_reality", "proof_of_completeness"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                evaluate(FACT, QUESTION, **{name: True})

    def test_environment_cannot_redirect_installed_native_binary(self):
        with patch.dict(os.environ, {"NABT_LICENSED_INFERENCE": "/tmp/untrusted-native"}), patch.object(
                runtime.subprocess, "run", return_value=SimpleNamespace(
                    stdout=runtime.wire(failure()), returncode=0)) as run:
            result = evaluate("سار زيد ربما", QUESTION)
        self.assertEqual(run.call_args.args[0][0], str(NATIVE))
        self.no_certificate(result, "UNKNOWN")


class ActualNativeSecurity(SafetyAssertions, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NATIVE.is_file():
            raise unittest.SkipTest("build installed licensedInference; CI must enforce presence")
        cls.baseline = evaluate(FACT, QUESTION, source_id="security-source", revision="r1",
                                scope="review-scope", time="t1")
        if cls.baseline.get("verified") is not True or cls.baseline.get("status") != "SUPPORTED":
            raise AssertionError("real native positive control failed: " + str(cls.baseline.get("reason")))

    def bound_evaluate(self, source=FACT, query=QUESTION, **changes):
        options = dict(source_id="security-source", revision="r1", scope="review-scope", time="t1")
        options.update(changes)
        return evaluate(source, query, **options)

    def expected_binding(self):
        # Independently retained CLI expectation; never derive it from a
        # certificate under mutation.
        return {"identity": "security-source", "revision": "r1",
                "scope": runtime.wire({"scope": "review-scope", "time": "t1"})}

    def test_supported_prefix_cannot_hide_unknown_text_anywhere(self):
        cases = ["سار زيد ربما.", "قال عمرو. سار زيد.", "سار زيد. قال عمرو.",
                 "سار زيد..", "سار زيد. . عرف زيد الحق.",
                 "«سار زيد. عرف زيد الحق.»", '"سار زيد.". عرف زيد الحق.',
                 "```\nسار زيد.\n```", "سار زيد.\u200b", "سار زيد\u202e."]
        for source in cases:
            with self.subTest(source=source):
                result = self.bound_evaluate(source)
                self.no_certificate(result, "UNKNOWN")
                self.assertEqual(result["proposal"]["readings"], [])

    def test_query_is_consumed_in_full(self):
        for query in (QUESTION + " ثم شيء", "قال عمرو " + QUESTION, QUESTION + "؟", "«" + QUESTION + "»"):
            with self.subTest(query=query):
                self.no_certificate(self.bound_evaluate(query=query), "UNKNOWN")

    def test_same_byte_payload_and_spans_survive_unicode_and_ascii_spacing(self):
        source = " \tسَارَ زَيْدٌ.\r\n"
        query = " هَلْ سَارَ زَيْدٌ؟\n"
        result = self.bound_evaluate(source.encode(), query.encode())
        self.assertIs(result["verified"], True)
        self.assertEqual(result["native_result"]["source_text"], source)
        self.assertEqual(result["native_result"]["query_text"], query)
        for record, text in ((result["source"], source), (result["query"], query)):
            self.assertEqual(record["sha256"], hashlib.sha256(text.encode()).hexdigest())
            self.assertEqual(record["bytes"], len(text.encode()))
        for segment in result["source_segments"]:
            for record in [segment["span"], *(token["span"] for token in segment["tokens"])]:
                raw = source.encode()[record["start_byte"]:record["end_byte"]]
                self.assertEqual(record["raw_text"].encode(), raw)
                self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())
        self.no_world_claim(result)

    def test_replayed_native_success_cannot_cross_source_query_or_context(self):
        cases = [dict(source="سار عمرو."), dict(query="هل سار عمرو؟"),
                 dict(source_id="other-source"), dict(revision="r2"),
                 dict(scope="other-scope"), dict(time="t2")]
        for changes in cases:
            with self.subTest(changes=changes), patch.object(runtime, "_native",
                    return_value=deepcopy(self.baseline["native_result"])):
                result = self.bound_evaluate(**changes)
            self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_native_success_types_identity_and_authority_are_exact(self):
        variants = []
        for key, value in (("verified", 1), ("reading_count", 1.0),
                           ("world_truth_established", True), ("all_arabic_complete", 0),
                           ("law_id", "other-law"), ("authority", "WORLD_TRUTH"),
                           ("source_text", FACT + " "), ("rows", []), ("status", "REFUTED")):
            response = deepcopy(self.baseline["native_result"])
            response[key] = value
            variants.append((key, response))
        response = deepcopy(self.baseline["native_result"])
        response["aggregate"]["credulous_positive"] = 1
        variants.append(("aggregate_bool_alias", response))
        response = deepcopy(self.baseline["native_result"])
        response["rows"][0]["clauses"][0]["atom"]["positive"] = 1
        variants.append(("atom_bool_alias", response))
        response = deepcopy(self.baseline["native_result"])
        response["proof_of_completeness"] = "caller text"
        variants.append(("extra_field", response))
        for name, response in variants:
            with self.subTest(name=name), patch.object(runtime, "_native", return_value=response):
                result = self.bound_evaluate()
            self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_native_process_failure_cannot_return_success(self):
        with patch.object(runtime.subprocess, "run", return_value=SimpleNamespace(
                stdout=runtime.wire(self.baseline["native_result"]), returncode=1)):
            result = self.bound_evaluate()
        self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_native_reopens_original_source_and_query_files(self):
        real_run = subprocess.run
        for index, replacement in ((1, b"\xff"), (1, "لم يسر زيد.".encode()),
                                   (2, "هل سار عمرو؟".encode())):
            def mutate_then_run(args, **kwargs):
                Path(args[index]).write_bytes(replacement)
                return real_run(args, **kwargs)
            with self.subTest(index=index, replacement=replacement), patch.object(
                    runtime.subprocess, "run", side_effect=mutate_then_run):
                result = self.bound_evaluate()
            self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_native_rejects_missing_or_forged_closure_certificate(self):
        for mutate in (lambda r: r["readings"].clear(),
                       lambda r: r["readings"][0]["steps"].clear(),
                       lambda r: r["readings"][0]["known"].clear(),
                       lambda r: r["readings"][0]["clean_steps"].clear(),
                       lambda r: r["readings"][0]["steps"][0].update(index=True)):
            certificate = deepcopy(self.baseline["proposal"])
            mutate(certificate)
            result = runtime._native(FACT.encode(), QUESTION.encode(), certificate,
                                     self.expected_binding())
            self.assertIs(result["verified"], False)
            self.assertIs(result["world_truth_established"], False)

    def test_certificate_cannot_supply_its_own_expected_metadata(self):
        for key in ("identity", "revision", "scope"):
            certificate = deepcopy(self.baseline["proposal"])
            certificate["source"][key] = "different-certificate-binding"
            result = runtime._native(FACT.encode(), QUESTION.encode(), certificate,
                                     self.expected_binding())
            self.assertIs(result["verified"], False)
            self.assertEqual(result["error"], "BINDING_MISMATCH")
            self.assertIs(result["world_truth_established"], False)

    def test_native_file_byte_limits_are_independent_of_python_preflight(self):
        for source, query in ((b"x" * 65537, QUESTION.encode()),
                              (FACT.encode(), b"x" * 8193)):
            result = runtime._native(source, query, deepcopy(self.baseline["proposal"]),
                                     self.expected_binding())
            self.assertIs(result["verified"], False)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertEqual(result["error"], "RESOURCE_LIMIT")
            self.assertIs(result["world_truth_established"], False)

    def test_native_certificate_duplicate_keys_are_rejected_before_decoding(self):
        real_run = subprocess.run
        mutations = [lambda text: '{"law_id":"forged-law",' + text[1:],
                     lambda text: r'{"law_\u0069d":"forged-law",' + text[1:],
                     lambda text: text.replace('"index":0', '"index":999,"index":0', 1)]
        for mutate in mutations:
            def mutate_then_run(args, **kwargs):
                path = Path(args[3])
                path.write_text(mutate(path.read_text()))
                return real_run(args, **kwargs)
            with patch.object(runtime.subprocess, "run", side_effect=mutate_then_run):
                result = self.bound_evaluate()
            self.no_certificate(result, "VERIFICATION_UNAVAILABLE")

    def test_native_object_member_budget_precedes_full_schema_parse(self):
        real_run = subprocess.run
        def mutate_then_run(args, **kwargs):
            path = Path(args[3])
            encoded = path.read_text()
            extras = ",".join('"extra_%d":0' % index for index in range(1000))
            path.write_text(encoded[:-1] + "," + extras + "}")
            kwargs["timeout"] = 3
            return real_run(args, **kwargs)
        with patch.object(runtime.subprocess, "run", side_effect=mutate_then_run):
            result = self.bound_evaluate()
        self.no_certificate(result, "RESOURCE_EXHAUSTED")
        # Distinguish the native budget response from our outer timeout guard.
        self.assertEqual(result["native_result"]["error"], "RESOURCE_LIMIT")

    def test_conflicting_premise_cannot_cleanly_authorize_its_consequence(self):
        source = "عرف زيد الحق. لم يعرف زيد الحق. إن عرف زيد الحق سار زيد."
        result = self.bound_evaluate(source)
        self.assertEqual(result["status"], "DEFER")
        self.assertIs(result["verified"], True)
        self.assertIs(result["aggregate"]["credulous_positive"], True)
        self.assertIs(result["aggregate"]["skeptical_clean_positive"], False)
        self.no_world_claim(result)


if __name__ == "__main__":
    unittest.main()
