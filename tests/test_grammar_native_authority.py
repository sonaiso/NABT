"""Routing authority needs live bounded Lean evidence, not Python success.

These are boundary and regression checks. They do not supply new linguistic
gold, and a checked conditional control equation is not a language license.
"""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch

from nabt import classical_certified, foundation
from nabt.errors import NabtError, resource_limit
from tools.grammar_catalog import __main__ as cli
from tools.grammar_catalog.catalog import build_catalog
from tools.grammar_catalog.retrieval import RetrievalError, SearchIndex
from tools.grammar_catalog.routing import evaluate_candidates, evaluate_diagnostic_candidates

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "nabt.classical-rule-inventory.v1::"
RID = "HAMZA-LEXICAL-COMMAND"
FRAME = {"root": ["ء", "ك", "ل"], "profile": "all_attested"}
NATIVE_EXPORTS = tuple(ROOT / "formal/.lake/build/bin" / name
                       for name in classical_certified._EXPORTS.values())


class NativeRoutingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = SearchIndex(build_catalog())

    def route(self, rid=RID, frame=None, **kwargs):
        return evaluate_candidates(self.index, [PREFIX + rid],
                                   {rid: FRAME if frame is None else frame}, **kwargs)

    @skipUnless(all(path.is_file() for path in NATIVE_EXPORTS), "four native classical exports required")
    def test_default_route_requires_native_and_keeps_every_fallback(self):
        result = self.route()
        self.assertEqual(result["schema"], "nabt.conditional-rule-routing.v2")
        self.assertTrue(result["native_required"])
        self.assertEqual(len(set(result["schedule"])), 24)
        self.assertEqual(result["examined_rule_count"], 24)
        self.assertTrue(result["inventory_exhausted"])
        self.assertFalse(result["conditional_evaluation_complete"])
        row = result["rows"][0]
        self.assertEqual(row["status"], "CHECKED_CONDITIONAL_CONTROL")
        self.assertTrue(row["native_receipt"]["native_checked"])
        self.assertEqual(row["diagnostic"]["authority"], "PYTHON_DIAGNOSTIC_ONLY")
        self.assertTrue(row["diagnostic"]["verification"]["valid"])
        self.assertEqual(row["claims"][0]["equation_result"]["outputs"],
                         [["ك", "ل"], ["ء", "و", "ك", "ل"]])
        for field in ("strict_language_accepted", "grants_language_license",
                      "source_to_control_proved", "exhaustive_language_claim", "whole_book_completeness"):
            self.assertFalse(result[field])
        self.assertTrue(all(not item["claims"] for item in result["rows"][1:]))

    def test_missing_failed_or_timed_out_native_cannot_borrow_python_success(self):
        for failure, expected in ((FileNotFoundError("absent"), "VERIFICATION_UNAVAILABLE"),
                                  (ValueError("mismatch"), "VERIFICATION_UNAVAILABLE"),
                                  (OverflowError("large"), "RESOURCE_EXHAUSTED"),
                                  (subprocess.TimeoutExpired("native", 60), "RESOURCE_EXHAUSTED")):
            with self.subTest(failure=type(failure).__name__), \
                    patch.object(classical_certified, "_native_export", side_effect=failure):
                result = self.route()
                row = result["rows"][0]
                self.assertTrue(row["diagnostic"]["verification"]["valid"])
                self.assertEqual(result["status"], expected)
                self.assertEqual(row["status"], expected)
                self.assertFalse(row["claims"])
                self.assertFalse(row["native_receipt"]["claims"])
                self.assertFalse(result["native_control_complete"])
                self.assertEqual(result["authority"], "DIAGNOSTIC_ONLY")

    @skipUnless(all(path.is_file() for path in NATIVE_EXPORTS), "four native classical exports required")
    def test_changed_complete_export_is_rejected_before_any_claim(self):
        actual, binary = classical_certified._native_export("classical_hamza")
        for mutation in ("missing", "duplicate", "altered"):
            changed = deepcopy(actual)
            if mutation == "missing":
                changed["rows"].pop()
            elif mutation == "duplicate":
                changed["rows"].append(deepcopy(changed["rows"][0]))
            else:
                changed["rows"][0]["operations"] = ["forged"]
            with self.subTest(mutation=mutation), \
                    patch.object(classical_certified, "_native_export", return_value=(changed, binary)):
                row = self.route()["rows"][0]
                self.assertEqual(row["status"], "VERIFICATION_UNAVAILABLE")
                self.assertFalse(row["claims"])

    @skipUnless(all(path.is_file() for path in NATIVE_EXPORTS), "four native classical exports required")
    def test_unexported_frame_remains_distinct_from_native_failure(self):
        frame = {"prefix": ["ر", "ج"], "glide": "waw", "alif_origin": "added", "suffix": []}
        result = self.route("HAMZA-FINAL-LONG", frame)
        row = result["rows"][0]
        self.assertEqual(row["status"], "OUTSIDE_NATIVE_DOMAIN")
        self.assertTrue(row["native_receipt"]["native_checked"])
        self.assertFalse(row["native_receipt"]["bounded_rule_checked"])
        self.assertFalse(row["claims"])
        self.assertEqual(result["status"], "INCOMPLETE_PREMISES_OR_RESULTS")

    @skipUnless(all(path.is_file() for path in NATIVE_EXPORTS), "four native classical exports required")
    def test_empty_action_equation_does_not_reject_arabic(self):
        row = self.route(frame={"root": ["ء", "س", "ر"], "profile": "all_attested"})["rows"][0]
        # The native empty equation is checked; the parent diagnostic still
        # defers its unresolved lexical result. Neither status rejects Arabic.
        self.assertEqual(row["status"], "PARTIAL")
        self.assertTrue(row["native_receipt"]["bounded_rule_checked"])
        self.assertEqual(row["claims"][0]["equation_result"]["operations"], [])
        self.assertFalse(row["native_receipt"]["strict_language_accepted"])

    @skipUnless(all(path.is_file() for path in NATIVE_EXPORTS), "four native classical exports required")
    def test_partial_source_result_never_becomes_complete(self):
        gold = json.loads((ROOT / "evidence/arabic_completion_v6/independent_review/benchmark_v1.json").read_bytes())
        for case in (c for c in gold["cases"] if c["kind"] == "partial"):
            with self.subTest(rule=case["rule_id"]):
                result = self.route(case["rule_id"], case["frame"])
                row = result["rows"][0]
                if case["rule_id"] == "AFFIX-LIGHT-NUN-PAUSE":
                    # This independent dual-form example is not among the
                    # exact frames of the finite boundary export.
                    self.assertEqual(row["status"], "OUTSIDE_NATIVE_DOMAIN")
                    self.assertFalse(row["native_receipt"]["bounded_rule_checked"])
                    self.assertFalse(row["claims"])
                else:
                    self.assertEqual(row["status"], "PARTIAL")
                    self.assertTrue(row["native_receipt"]["bounded_rule_checked"])
                self.assertFalse(result["conditional_evaluation_complete"])

    @skipUnless(all(path.is_file() for path in NATIVE_EXPORTS), "four native classical exports required")
    def test_full_scan_receipts_do_not_depend_on_retrieval_order(self):
        gold = json.loads((ROOT / "evidence/arabic_completion_v6/independent_review/benchmark_v1.json").read_bytes())
        frames = {}
        for case in gold["cases"]:
            if case["kind"] == "positive":
                frames.setdefault(case["rule_id"], case["frame"])
        self.assertEqual(len(frames), 24)
        first = evaluate_candidates(self.index, [], frames)
        reverse = evaluate_candidates(self.index, [PREFIX + rid for rid in reversed(first["schedule"])], frames)
        self.assertEqual({r["rule_id"]: r for r in first["rows"]},
                         {r["rule_id"]: r for r in reverse["rows"]})
        self.assertTrue(first["native_checked"])
        self.assertFalse(first["strict_language_accepted"])

    @skipUnless(all(path.is_file() for path in NATIVE_EXPORTS), "four native classical exports required")
    def test_supplied_profile_changes_the_native_bound_claim(self):
        all_profiles = self.route()["rows"][0]["claims"][0]
        common = self.route(frame={**FRAME, "profile": "named_common"})["rows"][0]["claims"][0]
        self.assertNotEqual(all_profiles["binding"]["frame_sha256"], common["binding"]["frame_sha256"])
        self.assertNotEqual(all_profiles["binding"]["native_row_sha256"], common["binding"]["native_row_sha256"])
        self.assertEqual(common["equation_result"]["outputs"], [["ك", "ل"]])

    def test_budget_frames_and_source_denial_are_not_proof_inputs(self):
        for budget in (True, 1.0, -1, 25):
            with self.subTest(budget=budget), self.assertRaises(RetrievalError):
                self.route(budget=budget)
        with patch.object(classical_certified, "evaluate_certified") as native:
            result = self.route(budget=0)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertEqual(len(result["pending_rule_ids"]), 24)
            native.assert_not_called()
        row = self.route(frame={"approved": True})["rows"][0]
        self.assertEqual(row["status"], "FRAME_ERROR")
        self.assertFalse(row["claims"])
        with patch.object(classical_certified, "evaluate_certified", side_effect=resource_limit("large")):
            self.assertEqual(self.route()["rows"][0]["status"], "RESOURCE_EXHAUSTED")
        with patch.object(foundation, "require_foundation", side_effect=NabtError("DENIED", "denied")), \
                patch.object(classical_certified, "evaluate_certified") as native:
            with self.assertRaises(NabtError):
                self.route()
            native.assert_not_called()

    def test_public_route_cannot_take_caller_authority_or_checker(self):
        for field in ("proof", "native_checked", "checker", "ledger", "receipt", "root"):
            with self.subTest(field=field), self.assertRaises(TypeError):
                evaluate_candidates(self.index, [], {}, **{field: True})

    def test_named_diagnostic_contract_remains_v1_without_native(self):
        with patch.object(classical_certified, "evaluate_certified") as native:
            result = evaluate_diagnostic_candidates(self.index, [PREFIX + RID], {RID: FRAME})
            self.assertEqual(result["schema"], "nabt.conditional-rule-routing.v1")
            self.assertEqual(result["rows"][0]["status"], "CHECKED_CONDITIONAL")
            self.assertNotIn("claims", result["rows"][0])
            self.assertNotIn("native_checked", result)
            native.assert_not_called()

    def test_cli_migration_and_failure_exit_are_explicit(self):
        with TemporaryDirectory() as directory:
            frames = Path(directory) / "frames.json"
            frames.write_text(json.dumps({RID: FRAME}, ensure_ascii=False), encoding="utf-8")
            for command, expected_code, schema in (
                    ("route", 2, "nabt.conditional-rule-routing.v2"),
                    ("route-diagnostic", 0, "nabt.conditional-rule-routing.v1")):
                stdout = StringIO()
                with self.subTest(command=command), \
                        patch("sys.argv", ["grammar_catalog", command, "همزة", "--frames", str(frames)]), \
                        patch.object(classical_certified, "_native_export", side_effect=FileNotFoundError("absent")), \
                        redirect_stdout(stdout):
                    code = cli.main()
                result = json.loads(stdout.getvalue())
                self.assertEqual(code, expected_code)
                self.assertEqual(result["schema"], schema)
                self.assertFalse(result["grants_language_license"])

    def test_json_rejects_duplicate_escaped_fields_and_nonfinite_numbers(self):
        with TemporaryDirectory() as directory:
            frames = Path(directory) / "frames.json"
            for raw in ('{"rule":{},"rule":{}}', '{"rule":{"x":1,"\\u0078":2}}',
                        '{"rule":{"x":NaN}}', '{"rule":{"x":Infinity}}'):
                with self.subTest(raw=raw):
                    frames.write_text(raw, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        cli._frames_json(frames)
            frames.write_text('{"rule":{"x":1.5}}', encoding="utf-8")
            self.assertEqual(cli._frames_json(frames)["rule"]["x"], 1.5)
            # Parsing preserves the value; the domain evaluator must reject it,
            # never truncate/coerce it into an integer or an authority flag.
            row = self.route(frame={**FRAME, "profile": 1.5})["rows"][0]
            self.assertEqual(row["status"], "FRAME_ERROR")

