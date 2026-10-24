"""Fault injection at model/codec/checker boundaries; no neural model claims."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import explainable_pilot as pilot
from tools import licensed_decoding as decoding

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
if "NABT_VERIFIED_READING" in os.environ and not BINARY.is_file():
    raise RuntimeError("NABT_VERIFIED_READING must point to the built executable")
SOURCE = "سالم هو عالم.\n".encode()
QUERY = "هل سالم هو عالم؟\n".encode()


def proposal(raw=SOURCE, query=QUERY):
    return pilot.wire(pilot.propose_certificate(raw, query)).encode()


class BoundaryTests(unittest.TestCase):
    def test_invalid_budgets_and_oversized_candidates(self):
        for k, seconds in ((True, 20), (0, 20), (17, 20), (1, True), (1, 0),
                            (1, float("inf")), (1, float("nan")), (1, 61)):
            with self.assertRaises(pilot.PilotError):
                decoding.run_candidates(SOURCE, QUERY, [], k=k, seconds=seconds)
        for candidates in ([b"{}", b"{}"], [None], (b"{}",), [b"x" * (1048576 + 1)]):
            with self.assertRaises(pilot.PilotError):
                decoding.run_candidates(SOURCE, QUERY, candidates)

    def test_null_never_calls_the_implicit_proposer_or_checker(self):
        with patch.object(pilot, "answer") as check:
            report = decoding.run_candidates(SOURCE, QUERY, [b"null", b"[]", b"true"], k=3)
        check.assert_not_called()
        self.assertEqual([r["error"] for r in report["attempts"]], ["INVALID_INPUT"] * 3)
        self.assertEqual(report["decision"], "NO_VERIFIED_CANDIDATE")
        self.assertIsNone(report["answer"])

    def test_missing_and_expired_slots_keep_the_full_budget(self):
        # Independent simulated clock: source encoding has already exhausted budget.
        with patch.object(decoding.time, "monotonic", side_effect=[0, 2, 2]):
            report = decoding.run_candidates(SOURCE, QUERY, [b"{}"], k=3, seconds=1)
        self.assertEqual([r["error"] for r in report["attempts"]],
                         ["RESOURCE_LIMIT", "MISSING_CANDIDATE", "MISSING_CANDIDATE"])
        self.assertTrue(all(not row["executed"] for row in report["attempts"]))
        self.assertIsNone(report["answer"])

    def test_a_late_checker_result_is_not_published_as_an_answer(self):
        with patch.object(decoding.time, "monotonic", side_effect=[0, 0, 0, 0, 2, 2, 2, 2]), \
                patch.object(pilot, "answer", return_value={"answer": {"status": "SUPPORTED"}}):
            report = decoding.run_candidates(SOURCE, QUERY, [b'{}', b'{}'], k=2, seconds=1)
        self.assertIsNone(report["answer"])
        self.assertEqual([r["error"] for r in report["attempts"]], ["RESOURCE_LIMIT"] * 2)
        self.assertEqual([r["executed"] for r in report["attempts"]], [True, False])

    def test_contradictory_verifier_results_withhold_selection(self):
        with patch.object(pilot, "answer", side_effect=[{"answer": {"status": s}}
                                                      for s in ("SUPPORTED", "REFUTED")]):
            report = decoding.run_candidates(SOURCE, QUERY, [b'{}', b'{}'], k=2)
        self.assertEqual(report["decision"], "INCONSISTENT_VERIFIED_RESULTS")
        self.assertIsNone(report["selected_index"])
        self.assertIsNone(report["answer"])
        self.assertEqual([r["answer_status"] for r in report["attempts"]], ["SUPPORTED", "REFUTED"])

    def test_noncanonical_candidate_tokens_stay_visible(self):
        candidates = [b'{"index":-0}', b'{"x":1e400}', b'{"x":0,"x":1}', b'\xff']
        report = decoding.run_candidates(SOURCE, QUERY, candidates, k=4)
        self.assertEqual(len(report["attempts"]), 4)
        self.assertTrue(all(r["error"] == "INVALID_INPUT" for r in report["attempts"]))

    def test_json_report_reader_allows_timing_but_rejects_nonfinite_and_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.json"
            path.write_text('{"elapsed_seconds":0.1,"index":0}')
            self.assertEqual(decoding.read_report(path)["elapsed_seconds"], .1)
            for content in ('{"x":1e400}', '{"x":0,"x":1}', '{"index":-0}', '{"x":"\\ud800"}'):
                path.write_text(content)
                with self.assertRaises(pilot.PilotError):
                    decoding.read_report(path)

    def test_unavailable_checker_is_not_unknown(self):
        report = decoding.run_candidates(SOURCE, QUERY, [proposal()], checker="/missing")
        self.assertEqual(report["attempts"][0]["error"], "CHECKER_UNAVAILABLE")
        self.assertIsNone(report["attempts"][0]["answer_status"])


@unittest.skipUnless(BINARY.is_file(), "formal CI requires native verifiedReading")
class NativeDecodingTests(unittest.TestCase):
    def run_candidates(self, candidates, **options):
        return decoding.run_candidates(SOURCE, QUERY, candidates, checker=BINARY, **options)

    def test_bad_first_good_second_and_all_attempts_retained(self):
        candidates = [b'{}', proposal()]
        report = self.run_candidates(candidates, k=3)
        self.assertEqual(report["selected_index"], 1)
        self.assertEqual([r["accepted"] for r in report["attempts"]], [False, True, False])
        self.assertEqual(report["attempts"][2]["error"], "MISSING_CANDIDATE")
        self.assertEqual(report["answer"]["answer"]["status"], "SUPPORTED")
        self.assertTrue(decoding.verify_selected(SOURCE, QUERY, candidates, report, checker=BINARY)["verified"])

    def test_duplicate_valid_proposals_are_counted_and_not_ambiguity_claims(self):
        p = proposal()
        report = self.run_candidates([p, p], k=2)
        self.assertEqual(report["selected_index"], 0)
        self.assertEqual(sum(r["accepted"] for r in report["attempts"]), 2)
        self.assertFalse(report["limits"]["candidate_set_exhaustive"])

    def test_other_source_cannot_be_accepted_by_forged_binding(self):
        different = "سالم هو حكيم.\n".encode()
        report = self.run_candidates([proposal(different)], k=1)
        self.assertEqual(report["attempts"][0]["error"], "CERTIFICATE_REJECTED")
        self.assertIsNone(report["answer"])

    def test_false_native_claims_cannot_turn_into_success(self):
        report = self.run_candidates([b'{}'])
        self.assertEqual(report["decision"], "NO_VERIFIED_CANDIDATE")
        report.update(decision="ANSWER_AVAILABLE", selected_index=0,
                      answer={"schema": pilot.ANSWER_SCHEMA, "verified": True})
        with self.assertRaises(pilot.PilotError):
            decoding.verify_selected(SOURCE, QUERY, [b'{}'], report, checker=BINARY)

    def test_replay_binds_selected_certificate_answer_and_independent_source(self):
        p = proposal()
        report = self.run_candidates([p])
        for change in (lambda r: r["answer"]["answer"].update(text_ar="دليل مختلق"),
                       lambda r: r["source"]["binding"].update(revision="other"),
                       lambda r: r.update(selected_index=True)):
            altered = deepcopy(report)
            change(altered)
            with self.assertRaises(pilot.PilotError):
                decoding.verify_selected(SOURCE, QUERY, [p], altered, checker=BINARY)
        with self.assertRaises(pilot.PilotError):
            decoding.verify_selected(SOURCE, QUERY, [b'{}'], report, checker=BINARY)
        # Timings are telemetry, not authenticated proof. The verifier says so.
        report["elapsed_seconds"] = 0
        replay = decoding.verify_selected(SOURCE, QUERY, [p], report, checker=BINARY)
        self.assertFalse(replay["audit_log_authenticated"])

    def test_valid_unknown_and_conflict_are_preserved_as_semantic_answers(self):
        for text, status in (("سالم هو حكيم.\n", "UNKNOWN"),
                             ("سالم هو عالم.\nليس سالم هو عالم.\n", "CONFLICT")):
            raw = text.encode()
            p = proposal(raw)
            report = decoding.run_candidates(raw, QUERY, [p], checker=BINARY)
            self.assertEqual(report["answer"]["answer"]["status"], status)

    def test_cli_run_and_replay_with_decimal_telemetry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, query, candidate, output = [root / x for x in ("source", "query", "candidate", "report")]
            source.write_bytes(SOURCE)
            query.write_bytes(QUERY)
            candidate.write_bytes(proposal())
            base = [sys.executable, str(ROOT / "tools/licensed_decoding.py")]
            options = [str(source), str(query), "--candidate", str(candidate), "--checker", str(BINARY)]
            run = subprocess.run(base + ["run"] + options + ["--output", str(output)],
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            run = subprocess.run(base + ["verify"] + options + [str(output)],
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertTrue(json.loads(run.stdout)["verified"])


if __name__ == "__main__":
    unittest.main()
