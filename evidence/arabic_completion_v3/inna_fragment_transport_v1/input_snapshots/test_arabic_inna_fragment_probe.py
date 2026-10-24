"""Adversarial review of the independent inna-probe transport checker.

These tests do not import the recognizer or turn example agreement into a
refinement theorem. The separately invoked checker executes the real Lean
binary and preserves its complete wire evidence.
"""

from copy import deepcopy
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "inna_fragment_checker", ROOT / "tools/check_arabic_inna_fragment.py")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


def response_for(case):
    """An authored wire fixture, not a computation of grammatical eligibility."""
    result = dict(CHECKER.ENVELOPE, status=case.status,
                  case_assignment_complete=case.status == CHECKER.COMPLETE)
    if case.status == "ERROR":
        return dict(result, error=case.error, message="authored transport rejection")
    request = case.request
    ledger = {r["id"]: r for r in request["lexicon"]}

    def pair(ids):
        left, right = ids
        start = len("إِنَّ ".encode())
        stop = start + len(bytes.fromhex(ledger[left]["surface_hex"]))
        end = stop + 1 + len(bytes.fromhex(ledger[right]["surface_hex"]))
        return {"subject_id": left, "predicate_id": right,
                "subject_witness": ledger[left]["witness"],
                "predicate_witness": ledger[right]["witness"],
                "subject_span": [start, stop], "predicate_span": [stop + 1, end],
                "required_subject_case": "nasb", "required_predicate_case": "raf"}

    result.update(
        source_hex=request["source_hex"], lexicon=deepcopy(request["lexicon"]),
        recognized=[pair(ids) for ids in case.recognized], pending=[pair(ids) for ids in case.pending],
        reference_equivalence="Nabt.ArabicInnaFragment.recognize_iff_reference",
        written_case_basis="literal_utf8_tanwin_endings_with_explicit_accusative_alif.v1",
        input_profile="exact_inna_prefix_single_ascii_spaces_no_final_punctuation.v1",
        scope="all_case_assignments_in_declared_inna_fragment_relative_to_supplied_lexicon",
    )
    return result


class InnaFragmentTransportCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = CHECKER.source_material()
        cls.cases = CHECKER.make_cases(cls.material)
        cls.by_id = {c.identity: c for c in cls.cases}

    def test_existing_lexical_records_are_exact_and_authorship_is_retained(self):
        material = self.material
        self.assertFalse(material["source_is_qac_quotation"])
        self.assertFalse(material["source_acquisition_established"])
        self.assertFalse(material["lexicon_exhaustiveness_established"])
        self.assertFalse(material["target_used_to_build_lexicon"])
        raw = (ROOT / CHECKER.LEXICAL_SOURCE).read_bytes()
        for row in material["lexical_source_records"]:
            part = raw[row["start"]:row["end"]]
            self.assertEqual(part.decode(), row["raw_text"])
            self.assertEqual(sha256(part).hexdigest(), row["span_sha256"])
        self.assertEqual([bytes.fromhex(r["surface_hex"]).decode() for r in material["lexicon"]],
                         ["زَيْدٌ", "زَيْدٍ", "زَيْدًا", "كَرِيمٌ", "كَرِيمٍ", "كَرِيمًا"])
        self.assertEqual({r["case"] for r in material["lexicon"]}, {"unknown"})

    def test_changed_source_is_not_promoted_by_a_claimed_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / CHECKER.LEXICAL_SOURCE
            path.parent.mkdir(parents=True)
            path.write_bytes((ROOT / CHECKER.LEXICAL_SOURCE).read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "pinned source changed"):
                CHECKER.source_material(root)

    def test_rule_passage_is_source_bytes_not_the_requested_case(self):
        part = self.material["rule_passage"]
        raw = (ROOT / CHECKER.QATR_SOURCE).read_bytes()[part["start"]:part["end"]]
        self.assertEqual(raw.decode(), part["raw_text"])
        self.assertEqual(sha256(raw).hexdigest(), CHECKER.QATR_PASSAGE_SHA)
        self.assertIn("ويرفعن الخبر", part["raw_text"])

    def test_request_stream_contains_recovery_and_final_eof(self):
        raw = CHECKER.request_stream(self.cases)
        self.assertEqual(len(self.cases), 32)
        self.assertFalse(raw.endswith(b"\n"))
        self.assertEqual(raw.count(b"\n"), len(self.cases) - 1)
        self.assertEqual(self.cases[-2].identity, "oversize_line")
        self.assertEqual(self.cases[-1].identity, "valid_request_after_overflow_at_eof")

    def test_authored_wire_fixtures_are_accepted_by_the_checker(self):
        raw = b"".join(CHECKER.canonical(response_for(c)) + b"\n" for c in self.cases)
        checked = CHECKER.check_wire(self.cases, raw, b"", 0)
        self.assertEqual(len(checked), len(self.cases))

    def test_missing_or_extra_response_and_eof_framing_are_rejected(self):
        case = self.cases[0]
        raw = CHECKER.canonical(response_for(case)) + b"\n"
        for bad in (b"", raw[:-1], raw + raw, raw + b"\n"):
            with self.subTest(bad_length=len(bad)), self.assertRaises(ValueError):
                CHECKER.check_wire([case], bad, b"", 0)

    def test_stderr_or_process_failure_cannot_be_passed_as_a_receipt(self):
        case = self.cases[0]
        raw = CHECKER.canonical(response_for(case)) + b"\n"
        with self.assertRaisesRegex(ValueError, "stderr"):
            CHECKER.check_wire([case], raw, b"unexpected warning", 0)
        with self.assertRaisesRegex(ValueError, "unsuccessfully"):
            CHECKER.check_wire([case], raw, b"", 1)

    def test_duplicate_json_key_and_noncanonical_output_are_rejected(self):
        case = self.cases[0]
        raw = CHECKER.canonical(response_for(case))
        duplicate = raw[:-1] + b',"world_truth":"NOT_ESTABLISHED"}\n'
        for bad in (duplicate, b" " + raw + b"\n"):
            with self.assertRaises(ValueError):
                CHECKER.check_wire([case], bad, b"", 0)

    def test_world_and_acquisition_escalation_are_rejected(self):
        case = self.cases[0]
        for key, value in (("world_truth", "ESTABLISHED"), ("source_acquisition_established", True),
                           ("lexicon_exhaustiveness_established", True),
                           ("authority", "WORLD_CERTIFIED"), ("linguistic_rejection", True)):
            r = response_for(case)
            r[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "authority boundary"):
                CHECKER.check_response(case, r)

    def test_integer_cannot_impersonate_boolean_and_boolean_cannot_impersonate_span(self):
        case = self.cases[0]
        r = response_for(case)
        r["case_assignment_complete"] = 1
        with self.assertRaisesRegex(ValueError, "mistyped"):
            CHECKER.check_response(case, r)
        r = response_for(case)
        r["recognized"][0]["subject_span"][0] = True
        with self.assertRaisesRegex(ValueError, "byte span"):
            CHECKER.check_response(case, r)

    def test_source_or_lexicon_substitution_is_rejected(self):
        case = self.cases[0]
        r = response_for(case)
        r["source_hex"] += "20"
        with self.assertRaisesRegex(ValueError, "source bytes"):
            CHECKER.check_response(case, r)
        r = response_for(case)
        r["lexicon"][0]["number"] = "other"
        with self.assertRaisesRegex(ValueError, "lexical ledger"):
            CHECKER.check_response(case, r)

    def test_missing_alternative_is_not_accepted_as_complete(self):
        case = self.by_id["all_registered_alternatives"]
        r = response_for(case)
        r["recognized"].pop()
        with self.assertRaisesRegex(ValueError, "omitted or invented"):
            CHECKER.check_response(case, r)

    def test_pending_competitor_cannot_be_dropped_or_outvoted(self):
        case = self.by_id["pending_competitor_blocks_completion"]
        r = response_for(case)
        r["pending"] = []
        with self.assertRaisesRegex(ValueError, "omitted or invented"):
            CHECKER.check_response(case, r)
        r = response_for(case)
        r["status"] = CHECKER.COMPLETE
        r["case_assignment_complete"] = True
        with self.assertRaisesRegex(ValueError, "wrong status"):
            CHECKER.check_response(case, r)

    def test_duplicate_and_foreign_reading_ids_are_rejected(self):
        case = self.cases[0]
        r = response_for(case)
        r["recognized"].append(deepcopy(r["recognized"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate analysis"):
            CHECKER.check_response(case, r)
        r = response_for(case)
        r["recognized"][0]["subject_id"] = "foreign"
        with self.assertRaisesRegex(ValueError, "unbound"):
            CHECKER.check_response(case, r)

    def test_changed_span_or_witness_is_rejected(self):
        case = self.cases[0]
        r = response_for(case)
        r["recognized"][0]["subject_span"][1] -= 1
        with self.assertRaisesRegex(ValueError, "restore"):
            CHECKER.check_response(case, r)
        r = response_for(case)
        r["recognized"][0]["subject_witness"] = "caller:replacement"
        with self.assertRaisesRegex(ValueError, "witness identity"):
            CHECKER.check_response(case, r)

    def test_no_reading_never_grants_ordinary_language_rejection(self):
        case = self.by_id["unknown_lexeme"]
        r = response_for(case)
        self.assertFalse(r["linguistic_rejection"])
        CHECKER.check_response(case, r)
        r["linguistic_rejection"] = True
        with self.assertRaises(ValueError):
            CHECKER.check_response(case, r)

    def test_a_different_execution_artifact_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.json"
            CHECKER.write_fixed(path, b"original\n")
            CHECKER.write_fixed(path, b"original\n")
            with self.assertRaisesRegex(ValueError, "refusing to rewrite"):
                CHECKER.write_fixed(path, b"changed\n")
            self.assertEqual(path.read_bytes(), b"original\n")

    def test_timeout_preserves_partial_wire_and_a_failed_receipt(self):
        failure = CHECKER.subprocess.TimeoutExpired(
            [sys.executable], 1, output=b"partial-response", stderr=b"partial-error")
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with patch.object(CHECKER.subprocess, "run", side_effect=failure):
                report = CHECKER.execute(Path(sys.executable), directory, timeout=1)
            self.assertFalse(report["ok"])
            self.assertIsNone(report["returncode"])
            self.assertEqual(report["checks"], [])
            self.assertIn("time budget", report["error"])
            self.assertEqual((directory / "responses.jsonl").read_bytes(), b"partial-response")
            self.assertEqual((directory / "stderr.bin").read_bytes(), b"partial-error")
            self.assertTrue((directory / "report.json").is_file())


if __name__ == "__main__":
    unittest.main()
