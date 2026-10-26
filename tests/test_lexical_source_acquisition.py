"""Independent record mutations and fail-closed composition of native laws."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from tools.linguistic_truth import surface

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "formal/.lake/build/bin/lexicalSourceRows"
RECORD = "(2:187:28:1)\tkataba\tV\tSTEM|POS:V|LEM:kataba|ROOT:ktb\r\n"


def request_for(record=RECORD, prefix="مصدر الاختبار\r\n"):
    start = len(prefix.encode())
    return {"source": {"id": "independent-record-control", "revision": "declared-not-authenticated",
                       "text": prefix + record},
            "row_spans": [{"start_byte": start, "end_byte": start + len(record.encode())}]}


@unittest.skipUnless(NATIVE.is_file(), "built lexicalSourceRows required")
class NativeRecordControls(unittest.TestCase):
    def call(self, request):
        raw = request if isinstance(request, bytes) else surface._wire(request)
        result = subprocess.run([str(NATIVE)], input=raw, capture_output=True, timeout=60)
        return result.returncode, json.loads(result.stdout)

    def test_utf8_global_span_and_local_form_binding_are_distinct(self):
        request = request_for()
        rc, report = self.call(request)
        self.assertEqual(rc, 0, report)
        row = report["rows"][0]
        self.assertEqual(row["start_byte"], len("مصدر الاختبار\r\n".encode()))
        self.assertEqual(row["raw_line"], RECORD)
        self.assertEqual(row["form"], "kataba")
        self.assertEqual(row["lemma"], "kataba")
        self.assertEqual(RECORD.encode()[row["lemma_start_byte"]:row["lemma_end_byte"]], b"kataba")
        binding = row["witness"]["binding"]
        self.assertEqual(binding["source"]["text"], RECORD)
        self.assertEqual(RECORD.encode()[binding["start_byte"]:binding["end_byte"]], b"kataba")
        self.assertFalse(report["source_authenticity_established"])
        self.assertFalse(report["intended_sense_established"])

    def test_annotation_is_computed_from_bytes_not_a_known_lemma_table(self):
        altered = RECORD.replace("LEM:kataba", "LEM:declared_annotation")
        rc, report = self.call(request_for(altered))
        self.assertEqual(rc, 0, report)
        self.assertEqual(report["rows"][0]["witness"]["expression"], "declared_annotation")
        self.assertFalse(report["intended_sense_established"])

    def test_duplicate_empty_missing_and_conflicting_annotations_rejected(self):
        changes = [
            ("LEM:kataba", "LEM:kataba|LEM:other"),
            ("LEM:kataba", "LEM:"), ("|LEM:kataba", ""),
            ("POS:V", "POS:N"), ("POS:V", "POS:V|POS:V"),
            ("STEM|", "PREFIX|"), ("ROOT:ktb", "ROOT:ktb\textra"),
            ("\r\n", "\n"), ("\r\n", "\r\nextra\r\n"),
            ("kataba\t", "ktb\t"),
        ]
        for old, new in changes:
            with self.subTest(new=new):
                rc, report = self.call(request_for(RECORD.replace(old, new)))
                self.assertNotEqual(rc, 0)
                self.assertEqual(report["error"], "INVALID_INPUT")
                self.assertNotIn("rows", report)

    def test_midline_or_out_of_range_source_interval_cannot_be_attested(self):
        cases = [(1, len(RECORD.encode())), (0, len(RECORD.encode())-1),
                 (0, len(RECORD.encode())+1), (False, len(RECORD.encode())),
                 (0.0, len(RECORD.encode())), (0, True), (-1, 3)]
        for start, end in cases:
            request = request_for(prefix="")
            request["row_spans"] = [{"start_byte": start, "end_byte": end}]
            with self.subTest(start=start, end=end):
                rc, report = self.call(request)
                self.assertNotEqual(rc, 0)
                self.assertNotIn("rows", report)

    def test_no_empty_vacuous_certificate_or_partial_batch(self):
        empty = request_for(); empty["row_spans"] = []
        repeated = request_for(); repeated["row_spans"] *= 2
        mixed = request_for(); mixed["row_spans"].append({"start_byte": 1, "end_byte": 4})
        for request in (empty, repeated, mixed):
            with self.subTest(spans=request["row_spans"]):
                rc, report = self.call(request)
                self.assertNotEqual(rc, 0)
                self.assertNotIn("rows", report)

    def test_transport_rejects_repeated_fields_and_forged_derived_data(self):
        request = request_for(); request["rows"] = [{"lemma": "approved"}]
        for raw in (surface._wire(request), b'{"source":{},"source":{},"row_spans":[]}'):
            rc, report = self.call(raw)
            self.assertNotEqual(rc, 0)
            self.assertEqual(report["error"], "INVALID_INPUT")

    def test_native_resource_receipt_with_failure_exit_remains_resource_exhaustion(self):
        request = request_for()
        request["row_spans"] *= 129
        rc, report = self.call(request)
        self.assertEqual(rc, 2)
        self.assertEqual(report["error"], "RESOURCE_LIMIT")
        self.assertNotIn("rows", report)
        with self.assertRaises(OverflowError):
            surface._native_source_rows(request)

    def test_full_source_byte_budget_is_enforced_before_record_acquisition(self):
        request = request_for()
        request["source"]["text"] = "x" * (8388608 + 1)
        rc, report = self.call(request)
        self.assertEqual(rc, 2)
        self.assertEqual(report["error"], "RESOURCE_LIMIT")
        self.assertNotIn("rows", report)


@unittest.skipUnless(NATIVE.is_file() and surface.source_loader.DEFAULT_SOURCE.is_file(),
                     "native acquisition and pinned corpus required")
class InstalledSourceComposition(unittest.TestCase):
    def test_entire_installed_corpus_and_all_eleven_witnesses_are_replayed(self):
        ledger, witnesses, request, expected = surface._installed()
        actual, _ = surface._native_source_rows(request)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual["rows"]), 11)
        self.assertEqual(actual["source_bytes"], 6309503)
        self.assertEqual([row["witness"] for row in actual["rows"]], witnesses)
        self.assertEqual(sum(row["form"] == "Eayona" for row in actual["rows"]), 3)

    def test_spelling_claim_requires_source_acquisition_and_exact_receipt(self):
        with patch.object(surface, "_native_source_rows", side_effect=FileNotFoundError), \
                patch.object(surface, "_native") as later:
            report = surface.certify_surface("عَيْنَ")
            self.assertEqual(report["status"], "VERIFICATION_UNAVAILABLE")
            self.assertFalse(report["source_row_extraction_kernel_proved"])
            self.assertEqual(report["claims"], [])
            later.assert_not_called()
        original = surface._native_source_rows
        def altered(request):
            response, digest = original(request)
            response = deepcopy(response)
            response["rows"][0]["witness"]["expression"] = "forged"
            return response, digest
        with patch.object(surface, "_native_source_rows", side_effect=altered):
            report = surface.certify_surface("عَيْنَ")
            self.assertEqual(report["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(report["claims"], [])

    def test_source_resource_exhaustion_is_not_a_linguistic_rejection(self):
        with patch.object(surface, "_native_source_rows", side_effect=OverflowError):
            report = surface.certify_surface("عَيْنَ")
            self.assertEqual(report["status"], "RESOURCE_EXHAUSTED")
            self.assertEqual(report["claims"], [])

    def test_proved_row_extraction_does_not_establish_semantic_acquisition(self):
        report = surface.certify_surface("عَيْنَ", context="unresolved-context")
        self.assertEqual(report["status"], "CHECKED_EXACT_SURFACE")
        self.assertTrue(report["source_row_extraction_kernel_proved"])
        self.assertTrue(report["annotation_field_extraction_kernel_proved"])
        for flag in ("annotation_acquisition_kernel_proved", "source_authenticity_kernel_proved",
                     "intended_sense_established", "strict_language_accepted", "whole_arabic_complete"):
            self.assertFalse(report[flag], flag)
        self.assertEqual(len(report["matches"]), 3)


if __name__ == "__main__":
    unittest.main()
