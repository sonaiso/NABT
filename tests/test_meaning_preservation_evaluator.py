"""Synthetic evaluator attacks; these tests never execute the frozen matrix."""
from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import evaluate_meaning_preservation_v1 as evaluator
from tools import freeze_meaning_preservation_v1 as freezer


def fixture():
    context = {"speaker": "origin-speaker", "addressee": "origin-listener", "time": "t0", "place": "origin"}
    reading = {"predicate": "p", "subject": {"kind": "speaker", "value": ""},
        "object": {"kind": "entity", "value": "B"}, "positive": True,
        "tense": "past", "voice": "active", "force": "quoted"}
    packet = {"binding": {"source_id": "synthetic", "revision": "1", "scope": "test",
                          "source_text": "original source", "convention": "test-convention"},
              "source_context": context, "alternatives": [reading]}
    payload = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    request = {"law_id": evaluator.LAW_ID, "query_id": evaluator.QUERY_ID, "codec_id": evaluator.CODEC_ID,
        "cases": [{"case_id": "synthetic-case", "original": packet, "transported_payload": payload}],
        "recipient_context": {"speaker": "recipient", "addressee": "other", "time": "t9", "place": "elsewhere"}}
    expected = {"status": "FINITE_CONTRACT_VERIFIED", "reason": "ALL_FINITE_CONTRACTS_PRESERVED",
                "authority": dict(evaluator.FLAGS), "local_finite_preservation": True}
    case = {"id": "synthetic", "family": "preservation_positive", "layer": "public_contract",
            "fixture": {"kind": "object_request", "request": request}, "expected": expected}
    native = {"schema": "nabt.meaning-preservation.native-response.v1", "law_id": evaluator.LAW_ID,
        "query_id": evaluator.QUERY_ID, "codec_id": evaluator.CODEC_ID, "status": "FINITE_CONTRACT_VERIFIED",
        "reason": "ALL_FINITE_CONTRACTS_PRESERVED", "case_id": None, "other_case_id": None, "case_count": 1,
        "world_truth_established": False, "whole_arabic_completeness_established": False}
    observed = {"predicate": "p", "subject": {"kind": "speaker", "value": "origin-speaker"},
        "object": {"kind": "entity", "value": "B"}, "positive": True, "tense": "past", "voice": "active",
        "force": "quoted", "scope": "test", "convention": "test-convention", "time": "t0", "place": "origin"}
    inner = {"files": {name: "pinned-code" for name in evaluator.CODE_IDENTITY_PATHS},
             "native": {evaluator.NATIVE: "pinned-native"}}
    report = {"schema": evaluator.REPORT_SCHEMA, "law_id": evaluator.LAW_ID, "query_id": evaluator.QUERY_ID,
        "codec_id": evaluator.CODEC_ID, "mode": "authored", "status": "FINITE_CONTRACT_VERIFIED",
        "reason": "ALL_FINITE_CONTRACTS_PRESERVED", "verified": True, "native_checked": True,
        "chain_complete": True, "finite_contract_verified": True, "authority": "AUTHORED_PREMISES_FINITE_CONTRACT",
        "input_request": deepcopy(request), "producer": None, "producer_chain_complete": False,
        "contract_request": deepcopy(request), "contract_request_sha256": evaluator.digest(evaluator.wire(request).encode()),
        "proposal": deepcopy(native), "native_result": deepcopy(native), "observations": [{"case_id": "synthetic-case",
            "original": [deepcopy(observed)], "decoded": [deepcopy(observed)], "payload_bytes": len(payload.encode()),
            "payload_sha256": evaluator.digest(payload.encode())}],
        "execution": {"code": dict(inner["files"]), "native_path": evaluator.NATIVE, "native_sha256": "pinned-native"},
        **evaluator.FLAGS}
    direct = {"response": native, "returncode": 0}
    return case, request, report, direct, inner


class EvidenceProjectionTests(unittest.TestCase):
    def setUp(self):
        self.guard = evaluator.load_bootstrap()

    def test_exact_native_and_source_identity_not_reported_status_alone(self):
        case, request, report, direct, inner = fixture()
        self.assertTrue(evaluator.audit_report(case, report, request, self.guard, inner, direct, 0)["match"])
        attacks = [
            lambda r: r["input_request"]["cases"][0]["original"]["binding"].update(source_text="borrowed source"),
            lambda r: r["contract_request"]["cases"][0]["original"]["source_context"].update(time="t9"),
            lambda r: r.update(contract_request_sha256="invented"),
            lambda r: r["execution"]["code"].update({evaluator.CODE_IDENTITY_PATHS[0]: "caller-hash"}),
            lambda r: r["execution"].update(native_sha256="other-native"),
            lambda r: r["native_result"].update(case_count=True),
            lambda r: r.update(verified=1),
            lambda r: r.update(world_truth_established=True),
            lambda r: r.update(authority="ALL_ARABIC_COMPLETE"),
        ]
        for attack in attacks:
            changed = deepcopy(report); attack(changed)
            with self.subTest(attack=attack):
                audit = evaluator.audit_report(case, changed, request, self.guard, inner, direct, 0)
                self.assertFalse(audit["match"])
                self.assertTrue(audit["false_authorization"])

    def test_trace_preserves_origin_context_types_and_joint_rows(self):
        case, request, report, direct, inner = fixture()
        for attack in (
                lambda r: r["observations"][0]["decoded"][0]["subject"].update(value="recipient"),
                lambda r: r["observations"][0]["decoded"][0].update(positive=1),
                lambda r: r["observations"][0].update(payload_bytes=True),
                lambda r: r["observations"][0]["decoded"].append(deepcopy(r["observations"][0]["decoded"][0]))):
            changed = deepcopy(report); attack(changed)
            self.assertFalse(evaluator.audit_report(case, changed, request, self.guard, inner, direct, 0)["match"])

    def test_missing_positive_native_is_a_miss_not_a_successful_abstention(self):
        case, request, report, _, inner = fixture()
        report.update(status="VERIFICATION_UNAVAILABLE", reason="unavailable", verified=False,
                      chain_complete=False, finite_contract_verified=False, native_checked=False,
                      authority="NO_FINITE_CONTRACT_AUTHORITY", native_result=None)
        audit = evaluator.audit_report(case, report, request, self.guard, inner)
        self.assertFalse(audit["match"])
        self.assertFalse(audit["false_authorization"])

    def test_native_response_requires_exact_typed_schema_and_return_code(self):
        case, request, _, direct, _ = fixture()
        self.assertTrue(evaluator.native_matches(case["expected"], request, direct))
        for mutation in (lambda d: d["response"].update(case_count=True),
                         lambda d: d["response"].update(world_truth_established=0),
                         lambda d: d["response"].update(extra="unlicensed"),
                         lambda d: d.update(returncode=2)):
            changed = deepcopy(direct); mutation(changed)
            self.assertFalse(evaluator.native_matches(case["expected"], request, changed))

    def test_minimal_cli_error_carries_no_claims(self):
        case = {"layer": "public_contract", "expected": {"status": "INVALID_INPUT", "reason": None}}
        report = {"status": "INVALID_INPUT", "reason": "invalid", **evaluator.FLAGS}
        self.assertTrue(evaluator.audit_report(case, report, None, self.guard, cli_exit=2)["match"])
        report["world_truth_established"] = 0
        self.assertFalse(evaluator.audit_report(case, report, None, self.guard, cli_exit=2)["match"])

    def test_frozen_fixture_expansion_preserves_raw_duplicates_and_byte_budget(self):
        duplicate = b'{"x":1,"x":2}'
        self.assertEqual(evaluator.fixture_bytes({"kind": "raw_json", "text": duplicate.decode()}), duplicate)
        self.assertEqual(evaluator.fixture_bytes({"kind": "raw_bytes_hex", "hex": "ff"}), b"\xff")
        padded = evaluator.fixture_bytes({"kind": "padded_json_with_trailing_spaces", "request": {"a": "أ"}, "total_bytes": 24})
        self.assertEqual(len(padded), 24)
        self.assertEqual(self.guard.parse_json(padded), {"a": "أ"})
        with self.assertRaises(ValueError):
            evaluator.fixture_bytes({"kind": "runtime_generated_expectation"})

    def test_producer_never_receives_gold_expected_fields(self):
        case, request, report, direct, inner = fixture()
        seen = []
        cli = SimpleNamespace(main=None)
        def invoke(_cli, guard, raw):
            supplied = guard.parse_json(raw)
            self.assertEqual(supplied, request)
            self.assertNotIn("expected", supplied)
            seen.append(supplied)
            return deepcopy(report), 0
        def verify(receipt, *, expected_request, mode):
            self.assertEqual(expected_request, request)
            self.assertIsNot(expected_request, receipt["input_request"])
            return {"replay_matches": True, "valid": True, **evaluator.FLAGS}
        reader = SimpleNamespace(verify=verify)
        with patch.object(evaluator, "call_cli", side_effect=invoke), patch.object(evaluator, "direct_native", return_value=direct):
            result = evaluator.evaluate_case(case, reader, cli, self.guard, inner)
        self.assertTrue(result["contract_match"])
        self.assertEqual(len(seen), 1)

    def test_productive_projection_cannot_invent_extra_cases_or_swap_vos_roles(self):
        _, _, report, _, _ = fixture()
        original = {"source_id": "producer-test", "revision": "1", "scope": "test", "text": "ضَرَبَ عَمْرًا زَيْدٌ",
                    "source_context": {"speaker": "s", "addressee": "a", "time": "t", "place": "p"},
                    "recipient_context": {"speaker": "r", "addressee": "a", "time": "t", "place": "p"},
                    "transported_payload": None}
        packet = {"binding": {"source_id": "producer-test", "revision": "1", "scope": "test",
            "source_text": original["text"], "convention": "nabt.productive-clause.v1"},
            "source_context": deepcopy(original["source_context"]), "alternatives": [{"predicate": "DARABA",
            "subject": {"kind": "entity", "value": "ZAYD"}, "object": {"kind": "entity", "value": "AMR"},
            "positive": True, "tense": "past", "voice": "active", "force": "asserted"}]}
        contract = {"law_id": evaluator.LAW_ID, "query_id": evaluator.QUERY_ID, "codec_id": evaluator.CODEC_ID,
            "cases": [{"case_id": "producer", "original": packet, "transported_payload": evaluator.wire(packet)}],
            "recipient_context": deepcopy(original["recipient_context"])}
        self.assertTrue(evaluator.productive_projection_matches("MP-A02", original, contract))
        bad = deepcopy(contract); bad["cases"].append(deepcopy(bad["cases"][0]))
        self.assertFalse(evaluator.productive_projection_matches("MP-A02", original, bad))
        bad = deepcopy(contract); bad["cases"][0]["original"]["alternatives"][0]["subject"]["value"] = "AMR"
        self.assertFalse(evaluator.productive_projection_matches("MP-A02", original, bad))


class FrozenExecutionBoundaryTests(unittest.TestCase):
    def test_snapshot_must_match_validated_freeze_before_import_even_if_repeated(self):
        inner = {"files": {"source": "pinned"}, "native": {"native": "pinned-native"}, "commit": "head"}
        good = {"files": {"source": "pinned", "native": "pinned-native"}, "head": "head", "gold_sha256": evaluator.GOLD_SHA256}
        guard = SimpleNamespace(snapshot=lambda *args: deepcopy(good))
        self.assertEqual(evaluator.initial_snapshot(guard, inner, "first"), good)
        for mutation in (lambda s: s["files"].update(source="changed"),
                         lambda s: s["files"].update(native="changed"),
                         lambda s: s.update(gold_sha256="changed"), lambda s: s.update(head="other")):
            bad = deepcopy(good); mutation(bad)
            guard.snapshot = lambda *args: deepcopy(bad)
            with patch.object(evaluator, "load_bootstrap", return_value=guard), \
                    patch.object(evaluator.importlib, "import_module") as imports, \
                    patch.object(evaluator, "load_gold") as gold:
                with self.assertRaisesRegex(ValueError, "initial snapshot"):
                    evaluator.run({"baseline": inner}, {}, "first")
                imports.assert_not_called(); gold.assert_not_called()

    def test_forged_manifest_pins_fail_before_runtime(self):
        bad = {"schema": evaluator.SCHEMA, "evaluator_id": evaluator.EVALUATOR_ID,
               "source_commit": evaluator.SOURCE_COMMIT, "matrix_commit": evaluator.MATRIX_COMMIT,
               "content_pins": {}, "bootstrap": {"path": evaluator.BOOTSTRAP_PATH, "sha256": evaluator.BOOTSTRAP_SHA256}}
        guard = SimpleNamespace(load_json=lambda path: (bad, "manifest"))
        with patch.object(evaluator, "load_bootstrap", return_value=guard):
            with self.assertRaisesRegex(ValueError, "code-owned pins"):
                evaluator.verify_freeze(Path("unused"), "first")

    def test_preflight_attempt_is_retained_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "first.json"
            with patch.object(evaluator, "verify_freeze", side_effect=ValueError("changed source")), \
                    patch.object(evaluator, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluator.main(["--output", str(output), "--code-freeze", "unused", "--phase", "first"]), 2)
                run.assert_not_called()
            first = output.read_bytes()
            self.assertEqual(json.loads(first)["failure_stage"], "preflight")
            with self.assertRaises(FileExistsError):
                evaluator.main(["--output", str(output), "--code-freeze", "unused", "--phase", "exposed"])
            self.assertEqual(output.read_bytes(), first)

    def test_mid_execution_exception_retains_prior_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "first.json"
            error = evaluator.ScenarioExecutionError("second", [{"id": "first"}], RuntimeError("stopped"))
            with patch.object(evaluator, "verify_freeze", return_value=({}, {})), \
                    patch.object(evaluator, "run", side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                evaluator.main(["--output", str(output), "--code-freeze", "unused", "--phase", "first"])
            document = json.loads(output.read_text())
            self.assertEqual(document["completed_rows"], [{"id": "first"}])
            self.assertEqual(document["failed_case_id"], "second")
            self.assertFalse(document["acceptance_gate"]["passed"])

    def test_postflight_snapshot_audit_and_context_exit_keep_completed_rows(self):
        before = {"files": {}, "head": "head", "gold_sha256": evaluator.GOLD_SHA256}
        row = {"id": "synthetic-completed", "contract_match": True}
        for failure_point in ("snapshot", "audit", "context_exit"):
            with self.subTest(failure_point=failure_point):
                def fail():
                    raise RuntimeError("synthetic " + failure_point + " failure")
                imports = SimpleNamespace(executed={}, audit_origins=fail if failure_point == "audit" else lambda: None)
                @contextlib.contextmanager
                def frozen(_):
                    yield imports
                    if failure_point == "context_exit":
                        fail()
                guard = SimpleNamespace(frozen_runtime=frozen,
                    snapshot=lambda *args: fail() if failure_point == "snapshot" else deepcopy(before))
                with patch.object(evaluator, "load_bootstrap", return_value=guard), \
                        patch.object(evaluator, "initial_snapshot", return_value=before), \
                        patch.object(evaluator, "load_gold", return_value={"cases": [{"id": "synthetic"}]}), \
                        patch.object(evaluator.importlib, "import_module", return_value=object()), \
                        patch.object(evaluator, "evaluate_case", return_value=deepcopy(row)):
                    with self.assertRaises(evaluator.ScenarioExecutionError) as caught:
                        evaluator.run({"baseline": {"files": {}}}, {}, "first")
                failure = caught.exception
                self.assertEqual(failure.case_id, "__postflight__")
                self.assertEqual(failure.rows, [row])
                self.assertEqual(failure.cause_type, "RuntimeError")
                self.assertIn(failure_point, failure.cause_message)
                self.assertFalse(failure.execution_evidence["integrity_valid"])

    def test_validated_preflight_is_persisted_before_run_and_retained_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "first.json"
            freeze_path = Path(directory) / "freeze.json"
            evidence = {"manifest_sha256": "validated-freeze-hash", "commit": "validated-commit"}
            row = {"id": "retained-synthetic-row"}
            def fail_run(envelope, supplied, phase, *, checkpoint=None):
                persisted = json.loads(output.read_text())
                self.assertEqual(persisted["status"], "PREFLIGHT_VALIDATED")
                self.assertEqual(persisted["execution_evidence"]["manifest_sha256"], "validated-freeze-hash")
                self.assertEqual(supplied["code_freeze_path"], str(freeze_path.resolve()))
                checkpoint(row)
                raise evaluator.ScenarioExecutionError("__postflight__", [row], RuntimeError("origin audit"))
            with patch.object(evaluator, "verify_freeze", return_value=({}, evidence)), \
                    patch.object(evaluator, "run", side_effect=fail_run), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluator.main(["--output", str(output), "--code-freeze", str(freeze_path), "--phase", "first"]), 2)
            report = json.loads(output.read_text())
            self.assertEqual(report["completed_rows"], [row])
            self.assertEqual(report["execution_evidence"]["manifest_sha256"], "validated-freeze-hash")
            self.assertEqual(report["execution_evidence"]["code_freeze_path"], str(freeze_path.resolve()))
            self.assertIn("--code-freeze", report["execution_evidence"]["command"])
            self.assertFalse(report["execution_evidence"]["integrity_valid"])
            checkpoints = [json.loads(line) for line in Path(report["progress_log"]["path"]).read_text().splitlines()]
            self.assertEqual(checkpoints[-1], {"event": "case_completed", "row": row})

    def test_interruption_keeps_completed_checkpoint_without_success_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "interrupted.json"
            def interrupted(envelope, evidence, phase, *, checkpoint=None):
                checkpoint({"id": "durable-synthetic-row"})
                raise KeyboardInterrupt()
            with patch.object(evaluator, "verify_freeze", return_value=({}, {"manifest_sha256": "validated"})), \
                    patch.object(evaluator, "run", side_effect=interrupted), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(KeyboardInterrupt):
                    evaluator.main(["--output", str(output), "--code-freeze", "unused", "--phase", "first"])
            report = json.loads(output.read_text())
            self.assertEqual(report["status"], "PREFLIGHT_VALIDATED")
            self.assertNotIn("acceptance_gate", report)
            checkpoints = [json.loads(line) for line in Path(report["progress_log"]["path"]).read_text().splitlines()]
            self.assertEqual(checkpoints[-1]["row"], {"id": "durable-synthetic-row"})

    def test_freeze_does_not_overwrite_an_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freeze.json"; path.write_text("retained")
            with patch.object(freezer, "build_freeze", return_value={}):
                with self.assertRaises(FileExistsError):
                    freezer.main(["--output", str(path)])
            self.assertEqual(path.read_text(), "retained")

    def test_frozen_population_is_read_only_not_a_runtime_measurement(self):
        guard = evaluator.load_bootstrap()
        gold = evaluator.load_gold(guard)
        self.assertEqual(gold["counts"], evaluator.POPULATION)
        self.assertEqual(len(gold["cases"]), 73)
        self.assertFalse(evaluator.acceptance(evaluator.counts([]), True)["passed"])
        with self.assertRaises(ValueError):
            guard.parse_json(b'{"x":1,"x":2}')

    def test_freeze_inventory_covers_research_anchors_and_native_stays_disjoint(self):
        guard = evaluator.load_bootstrap()
        commit = guard.git("rev-parse", "HEAD")
        inventory = set(guard.git("ls-files", "-z").split("\0"))
        inference = guard.parse_json(guard.git("show", commit + ":" + guard.INFERENCE_SOURCE_PATH, binary=True))
        paths = evaluator.required_paths(guard, inventory, inference, evaluator.packets_at(guard, commit))
        self.assertIn("evidence/derivation/nominal_pattern_sources.json", paths)
        self.assertIn("evidence/semantic_axes_v1/source_review.json", paths)
        self.assertIn("evidence/meaning_preservation_v1/research/interpretation_contracts.json", paths)
        self.assertFalse(set(paths) & evaluator.NATIVE_PATHS)


if __name__ == "__main__":
    unittest.main()
