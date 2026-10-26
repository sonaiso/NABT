"""Actual native protocol regressions with explicitly synthetic premises.

These are conditional contract tests, not lexical attestations or measurements
of intended meaning. The cell numbers below are fixed independent spellings:
عَ=68, يْ=111, نُ=97 in the installed canonical A116 alphabet.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def fixture():
    text = "عَيْنُ"
    source = {"id": "synthetic-protocol", "revision": "fixture-v1", "text": text}
    frame = {"occurrence": {"source": source["id"], "revision": source["revision"],
             "raw": text, "start_byte": 0, "end_byte": 12,
             "referent": "unspecified", "time": "unspecified", "context": "fixture-context"},
             "expression": "عين", "convention": "synthetic-conformance"}
    citation = {"work": "synthetic-fixture-not-an-attestation", "revision": "fixture-v1",
                "source_sha256": "fixture-not-a-source-hash", "start_byte": 0,
                "end_byte": 7, "quotation": "fixture"}
    designations = [{"id": sense, "expression": "عين", "sense": sense,
                     "convention": "synthetic-conformance", "origin": "original",
                     "citation": deepcopy(citation)} for sense in ("eye", "spring")]
    candidates = [{"designation": deepcopy(designation), "intended_sense": designation["sense"],
                   "relation": None} for designation in designations]
    return {"op": "certify_a116", "source": source, "cells": [68, 111, 97],
            "request": {"frame": frame, "designations": designations, "relations": [],
                        "known": [], "proposed": candidates, "budget": 2}}


def with_usage(request):
    request = deepcopy(request)
    lexical = request["request"]
    lexical["known"] = [
        {"value": {"kind": "established", "designation": deepcopy(lexical["designations"][0])},
         "positive": True, "scope": "fixture-context"},
        {"value": {"kind": "used", "frame": deepcopy(lexical["frame"]), "sense": "eye"},
         "positive": True, "scope": "fixture-context"},
    ]
    return request


class CertifiedNativeProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        override = os.environ.get("NABT_LINGUISTIC_TRUTH")
        cls.binary = Path(override) if override else ROOT / "formal/.lake/build/bin/linguisticTruth"
        if not cls.binary.is_file():
            if override:
                raise AssertionError("requested native linguisticTruth executable is unavailable")
            raise unittest.SkipTest("native linguisticTruth executable not built")

    def run_lines(self, lines):
        completed = subprocess.run([str(self.binary)], input="\n".join(lines) + "\n",
                                   capture_output=True, text=True, timeout=30, check=True)
        output = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(len(output), len(lines))
        return output

    def check(self, request):
        return self.run_lines([json.dumps(request, ensure_ascii=False)])[0]

    def assert_deferred(self, request):
        result = self.check(request)
        self.assertEqual(result["status"], "DEFERRED")
        self.assertIs(result["candidate_set_checked"], False)
        self.assertIs(result["certified_from_a116"], False)
        self.assertEqual(result["accepted_candidates"], [])
        return result

    def test_exact_projection_preserves_finite_ambiguity(self):
        result = self.check(fixture())
        self.assertEqual(result["status"], "CHECKED_CANDIDATES")
        self.assertEqual(result["cells"], [68, 111, 97])
        self.assertEqual(result["source_number"], str(69 * 116**2 + 112 * 116 + 98))
        self.assertIs(result["candidate_set_checked"], True)
        self.assertIs(result["certified_from_a116"], False)
        self.assertEqual(len(result["semantic"]["rows"]), 2)
        self.assertEqual(result["accepted_candidates"], [])

    def test_explicit_premises_certify_only_conditional_usage(self):
        result = self.check(with_usage(fixture()))
        self.assertEqual(result["status"], "CERTIFIED_CONDITIONAL_USE")
        self.assertEqual([row["intended_sense"] for row in result["accepted_candidates"]], ["eye"])
        self.assertIs(result["candidate_set_checked"], True)
        for field in ("native_acquisition_proof", "all_arabic_complete", "world_truth_established"):
            self.assertIs(result[field], False)

    def test_wrong_or_missing_cell_cannot_use_semantic_support(self):
        for cells in ([69, 111, 97], [68, 111], []):
            with self.subTest(cells=cells):
                request = with_usage(fixture())
                request["cells"] = cells
                result = self.assert_deferred(request)
                self.assertEqual(result["semantic"]["rows"][0]["verdict"], "SUPPORTED_PREMISES")

    def test_cell_domain_rejects_boolean_float_string_and_out_of_range(self):
        for value in (True, False, -1, 116, 68.0, "68"):
            with self.subTest(value=value):
                request = fixture()
                request["cells"][0] = value
                self.assertEqual(self.check(request)["status"], "INVALID_INPUT")

    def test_changed_source_coordinates_cannot_borrow_premises(self):
        changes = {"source": "other", "revision": "other", "raw": "عَيْنَ",
                   "start_byte": 1, "end_byte": 2, "context": ""}
        for name, value in changes.items():
            with self.subTest(field=name):
                request = with_usage(fixture())
                request["request"]["frame"]["occurrence"][name] = value
                self.assert_deferred(request)

    def test_candidate_omission_reordering_and_empty_proposal_rejected(self):
        base = fixture()
        for candidates in (None, [], base["request"]["proposed"][:1],
                           list(reversed(base["request"]["proposed"]))):
            with self.subTest(candidates=candidates):
                request = with_usage(base)
                request["request"]["proposed"] = candidates
                self.assert_deferred(request)

    def test_missing_vowels_cannot_be_promoted_by_complete_semantics(self):
        request = with_usage(fixture())
        request["source"]["text"] = "عين"
        request["cells"] = []
        request["request"]["frame"]["occurrence"].update(raw="عين", end_byte=6)
        result = self.assert_deferred(request)
        self.assertEqual(result["projection_status"], "PARTIAL")

    def test_resource_exhaustion_is_not_a_linguistic_rejection(self):
        request = with_usage(fixture())
        request["request"]["budget"] = 0
        result = self.check(request)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertIs(result["candidate_set_checked"], False)
        self.assertEqual(result["accepted_candidates"], [])

    def test_duplicate_plain_and_escaped_keys_rejected_before_parsing(self):
        line = json.dumps(with_usage(fixture()), ensure_ascii=False, separators=(",", ":"))
        corrupted = [
            line.replace('"op":', '"op":"certify_a116","op":', 1),
            line.replace('"op":', '"\\u006fp":"certify_a116","op":', 1),
            line.replace('"text":', '"text":"other","text":', 1),
            line.replace('"budget":', '"\\u0062udget":0,"budget":', 1),
            line.replace('"cells":', '"cells":[0],"cells":', 1),
        ]
        for result in self.run_lines(corrupted):
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertIn("duplicate object key", result["message"])

    def test_duplicate_rejection_does_not_poison_following_request(self):
        line = json.dumps(fixture(), ensure_ascii=False, separators=(",", ":"))
        malformed = line.replace('"cells":', '"cells":[0],"cells":', 1)
        bad, good = self.run_lines([malformed, line])
        self.assertEqual(bad["status"], "INVALID_INPUT")
        self.assertEqual(good["status"], "CHECKED_CANDIDATES")


if __name__ == "__main__":
    unittest.main()
