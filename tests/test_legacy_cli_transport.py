"""Legacy output compatibility and explicit scoped transport branches."""
import contextlib
from importlib import import_module
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.cli import main as core_main, parser
from nabt.transport_contract import validate_transport_envelope
from tests._transport_native import native_test


class LegacyCliTransportTests(unittest.TestCase):
    def invoke(self, module, arguments):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if module == "nabt":
                code = core_main(arguments)
            else:
                with patch.object(sys, "argv", [module, *arguments]):
                    code = import_module(module + ".__main__").main()
        self.assertFalse(out.getvalue() and err.getvalue())
        return code, json.loads(out.getvalue() or err.getvalue())

    def check_envelope(self, value):
        self.assertEqual(value["schema"], "nabt.transport-envelope.v1")
        self.assertTrue(validate_transport_envelope(value)["integrity_valid"])
        self.assertFalse(value["transport_contract"]["transport_binding_kernel_proved"])

    def test_core_encoding_preserves_legacy_bytes_and_typed_authority(self):
        code, legacy = self.invoke("nabt", ["encode", "كَتَبَ"])
        scoped_code, scoped = self.invoke("nabt", ["--response-contract", "scoped-v1", "encode", "كَتَبَ"])
        self.assertEqual(code, scoped_code)
        self.check_envelope(scoped)
        self.assertEqual(scoped["response"], legacy)
        self.assertEqual(scoped["transport_contract"]["named_claims"], [])
        self.assertEqual(scoped["transport_contract"]["input_binding"], "CLI_ARGUMENTS_ONLY")

    def test_core_failure_is_wrapped_without_changing_exit_status(self):
        code, legacy = self.invoke("nabt", ["decode", "-1"])
        new_code, scoped = self.invoke("nabt", ["--response-contract", "scoped-v1", "decode", "-1"])
        self.assertEqual(new_code, code)
        self.check_envelope(scoped)
        self.assertEqual(scoped["response"], legacy)
        self.assertEqual(scoped["transport_contract"]["named_claims"], [])

    @native_test("exportClassicalHamza")
    def test_classical_transform_switches_to_native_exact_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.json"
            frame = {"root": ["ء", "ك", "ل"], "profile": "all_attested"}
            path.write_text(json.dumps(frame))
            _, legacy = self.invoke("nabt", ["classical-transform", "HAMZA-LEXICAL-COMMAND", str(path)])
            code, scoped = self.invoke("nabt", ["--response-contract", "scoped-v1", "classical-transform", "HAMZA-LEXICAL-COMMAND", str(path)])
        self.assertEqual(code, 0)
        self.assertNotEqual(legacy["schema"], scoped["response"]["schema"])
        self.check_envelope(scoped)
        self.assertEqual(scoped["transport_contract"]["request"], {"rule_id": "HAMZA-LEXICAL-COMMAND", "frame": frame})
        self.assertEqual(scoped["transport_contract"]["named_claims"][0]["kind"], "CLASSICAL_FINITE_CONTROL_EQUATION")

    @native_test("linguisticTruth")
    def test_lexical_certify_retains_checked_partial_claim_without_strict_acceptance(self):
        code, scoped = self.invoke("tools.linguistic_truth", ["--response-contract", "scoped-v1", "certify", "--text", "قَرْءُ", "--profile", "linguistic"])
        self.assertEqual(code, 3)
        self.check_envelope(scoped)
        self.assertTrue(scoped["transport_contract"]["named_claims"])
        self.assertFalse(scoped["response"]["strict_language_accepted"])
        self.assertEqual(scoped["transport_contract"]["request"]["text"], "قَرْءُ")

    def test_lexical_diagnostic_no_claims_and_unchanged_child(self):
        args = ["acquire", "--text", "قَرْءُ", "--profile", "linguistic"]
        old_code, old = self.invoke("tools.linguistic_truth", args)
        code, scoped = self.invoke("tools.linguistic_truth", ["--response-contract", "scoped-v1", *args])
        self.assertEqual(code, old_code)
        self.assertEqual(scoped["response"], old)
        self.assertEqual(scoped["transport_contract"]["named_claims"], [])

    @native_test("exportClassicalHamza")
    def test_grammar_route_binds_fixed_native_child_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frames.json"
            frames = {"HAMZA-LEXICAL-COMMAND": {"root": ["ء", "ك", "ل"], "profile": "all_attested"}}
            path.write_text(json.dumps(frames))
            code, scoped = self.invoke("tools.grammar_catalog", ["--response-contract", "scoped-v1", "route", "همزة", "--frames", str(path)])
        self.assertEqual(code, 3)  # Remaining rule premises are intentionally absent.
        self.check_envelope(scoped)
        self.assertEqual(scoped["transport_contract"]["request"]["frames"], frames)
        claims = scoped["transport_contract"]["named_claims"]
        self.assertTrue(claims)
        self.assertTrue(all(".native_receipt.claims[" in c["child_path"] for c in claims))

    def test_grammar_diagnostic_does_not_promote_native_looking_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frames.json"
            path.write_text("{}")
            _, scoped = self.invoke("tools.grammar_catalog", ["--response-contract", "scoped-v1", "route-diagnostic", "همزة", "--frames", str(path)])
        self.check_envelope(scoped)
        self.assertEqual(scoped["transport_contract"]["named_claims"], [])

    @native_test("licensedInference")
    def test_licensed_inference_exact_file_bytes_and_scope_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            source, query = Path(directory) / "source", Path(directory) / "query"
            source.write_text("سار زيد أمامك خلف الدار")
            query.write_text("هل سار زيد أمامك خلف الدار؟")
            _, legacy = self.invoke("tools.licensed_inference", [str(source), str(query)])
            code, scoped = self.invoke("tools.licensed_inference", ["--response-contract", "scoped-v1", str(source), str(query)])
            self.assertEqual(bytes.fromhex(scoped["transport_contract"]["request"]["source"]["hex"]), source.read_bytes())
        self.assertEqual(code, 0)
        self.check_envelope(scoped)
        self.assertEqual(scoped["response"]["legacy_result"], legacy)
        self.assertEqual(scoped["transport_contract"]["named_claims"][0]["kind"], "SOURCE_BOUND_FINITE_INFERENCE")

    def test_mantuq_invalid_input_is_diagnostic_without_benchmark_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            path.write_text('{"native_checked":true,"verified":true,"proof":{"theorems":["fake"]}}')
            args = ["evaluate", str(path)]
            old_code, old = self.invoke("tools.mantuq_inference", args)
            code, scoped = self.invoke("tools.mantuq_inference", ["--response-contract", "scoped-v1", *args])
        self.assertEqual(code, old_code)
        self.check_envelope(scoped)
        self.assertEqual(scoped["response"], old)
        self.assertEqual(scoped["transport_contract"]["named_claims"], [])

    def test_every_core_command_has_explicit_review_metadata_not_blanket_migration(self):
        path = Path(__file__).parents[1] / "src/nabt/data/transport_command_contracts.json"
        data = json.loads(path.read_text())
        commands = {row["command"] for row in data["rows"] if row["entrypoint"] == "nabt.cli.run"}
        self.assertEqual(commands, set(parser()._subparsers._group_actions[0].choices))
        self.assertFalse(data["whole_surface_migration_claim"])
        self.assertTrue(all(row["unresolved_premises"] for row in data["rows"]))
