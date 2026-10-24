"""Regression for a real inquiry producer/consumer byte-budget mismatch.

The bounded fixture expands declared provenance and retained review text.
Before the fix its compact report fit the API budget, while the CLI's
indented output exceeded the same verifier budget and could not be replayed.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nabt.rational_inquiry import (
    MAX_DOCUMENT_BYTES,
    MAX_REPORT_BYTES,
    audit_inquiry,
    verify_inquiry,
)


LAW_ID = "nabt.rational-inquiry.v1"
CHECK_BUDGET = 256


def large_snapshot():
    """A deterministic valid inventory; no external observations are claimed."""
    scope = {"domain": "bounded-text-record", "referent": "record-17",
             "time": "snapshot-1", "unit": "exact-utf8-text"}
    candidate = "x" * 6750
    repeated_check = {"source_id": "s00", "revision": 1, "expected": candidate}
    plan = {
        "version": LAW_ID,
        "claim": {"claim_id": "reading-17", "kind": "TEXT_CORRESPONDENCE",
                  "candidate": candidate, "scope": scope,
                  "origin_sources": [{"source_id": "s00", "revision": 1}]},
        "formation": {
            "purpose": "التحقق من قراءة سجل محدد",
            "interpretation": "القضية عن محتوى السجل، لا عن عدد أشياء العالم",
            "inference": "مقارنة النص المقترح بكامل نص السجل المرجعي",
            "prior": [],
        },
        "review": {
            "depth": "SURFACE",
            "context": [deepcopy(repeated_check) for _ in range(64)],
            "conditions": [deepcopy(repeated_check) for _ in range(64)],
            "alternatives": [],
            "limitations": ["المطابقة تخص السجل المقدم ونسبته المصرح بها فقط"],
            "unresolved": [],
        },
        "requested_rank": 1,
    }
    sources = [
        {"source_id": f"s{ordinal:02d}", "revision": 1, "scope": deepcopy(scope),
         "content": candidate, "origin": f"origin-{ordinal:02d}-" + "o" * 246,
         "parents": ([] if ordinal == 0 else
                     [{"source_id": f"s{ordinal - 1:02d}", "revision": 1}]),
         "role": "REFERENCE", "active": True}
        for ordinal in range(64)
    ]
    return plan, sources


class InquiryReportBudgetTests(unittest.TestCase):
    def test_large_valid_report_roundtrips_within_wire_budget(self):
        plan, sources = large_snapshot()
        report = audit_inquiry(plan, sources, max_checks=CHECK_BUDGET)
        self.assertEqual((report["version"], report["status"]), (LAW_ID, "LICENSED"))
        self.assertEqual(report["checks_performed"], 192)
        self.assertTrue(report["coverage_complete"])
        self.assertTrue(verify_inquiry(report, plan, sources, max_checks=CHECK_BUDGET)["valid"])
        compact = json.dumps(report, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.assertLessEqual(len(compact) + 1, MAX_REPORT_BYTES)
        # This fixture must keep exercising the actual old output expansion.
        indented = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
        self.assertGreater(len(indented) + 1, MAX_REPORT_BYTES)

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            plan_path, sources_path = directory / "plan.json", directory / "sources.json"
            report_path = directory / "report.json"
            for path, value in ((plan_path, plan), (sources_path, sources)):
                raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
                self.assertLessEqual(len(raw), MAX_DOCUMENT_BYTES)
                path.write_bytes(raw)
            made = subprocess.run(
                [sys.executable, "-m", "nabt", "inquire", str(plan_path),
                 "--sources", str(sources_path), "--max-checks", str(CHECK_BUDGET)],
                check=False, capture_output=True, timeout=20)
            self.assertEqual(made.returncode, 0, made.stderr.decode("utf-8"))
            self.assertFalse(made.stderr)
            self.assertLessEqual(len(made.stdout), MAX_REPORT_BYTES)
            self.assertEqual(json.loads(made.stdout), report)
            report_path.write_bytes(made.stdout)
            replayed = subprocess.run(
                [sys.executable, "-m", "nabt", "verify-inquiry", str(report_path),
                 "--plan", str(plan_path), "--sources", str(sources_path),
                 "--max-checks", str(CHECK_BUDGET)],
                check=False, capture_output=True, timeout=20)
            self.assertEqual(replayed.returncode, 0, replayed.stderr.decode("utf-8"))
            self.assertFalse(replayed.stderr)
            verified = json.loads(replayed.stdout)
            self.assertTrue(verified["valid"])
            self.assertEqual(verified["claim_status"], "LICENSED")


if __name__ == "__main__":
    unittest.main()
