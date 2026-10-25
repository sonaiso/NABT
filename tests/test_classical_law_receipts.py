"""Cross-module authority, source replay and complete receipt boundaries."""
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase, mock

from nabt import classical_laws as C
from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[1]
FRAME = {"root": ["ء", "ك", "ل"], "profile": "all_attested"}
RID = "HAMZA-LEXICAL-COMMAND"


class ClassicalReceiptTests(TestCase):
    def test_catalog_exact_original_unimplemented_domain(self):
        previous = json.loads((ROOT / "evidence/arabic_completion_v5/rule_implementation_crosswalk.json").read_bytes())
        expected = {r["rule_id"] for r in previous["rows"]
                    if r["status"] == "not_implemented_by_this_extension"}
        catalog = C.catalog()
        self.assertEqual({r["rule_id"] for r in catalog["rules"]}, expected)
        self.assertEqual(catalog["rule_count"], 24)
        self.assertIsNone(catalog["natural_language_completeness"])
        self.assertFalse(catalog["whole_book_completeness"])

    def test_independent_lexical_alternatives_and_replay(self):
        frame = deepcopy(FRAME)
        report = C.evaluate(RID, frame)
        self.assertEqual([a["morphophonemes"] for a in report["result"]["alternatives"]],
                         [["ك", "ل"], ["ء", "و", "ك", "ل"]])
        self.assertEqual(frame, FRAME)
        self.assertEqual(report["input_frame"], FRAME)
        self.assertTrue(C.verify(report)["valid"])
        self.assertFalse(report["grants_language_license"])
        self.assertFalse(report["premises_established_from_free_text"])

    def test_replay_rejects_omission_premise_edits_and_authority_escalation(self):
        original = C.evaluate(RID, FRAME)
        mutations = []
        r = deepcopy(original); r["result"]["alternatives"].pop(); mutations.append(r)
        r = deepcopy(original); r["grants_language_license"] = True; mutations.append(r)
        r = deepcopy(original); r["premises_established_from_free_text"] = True; mutations.append(r)
        r = deepcopy(original); r["input_frame"]["root"][1] = "س"; mutations.append(r)
        r = deepcopy(original); r["inventory_sha256"] = "0" * 64; mutations.append(r)
        r = deepcopy(original); r["result"]["source_spans"] = []; mutations.append(r)
        r = deepcopy(original); r["source_text_status"] = "approved"; mutations.append(r)
        for report in mutations:
            with self.subTest(report=report), self.assertRaises(NabtError):
                C.verify(report)

    def test_untrusted_frame_cannot_inject_authority(self):
        for frame in (dict(FRAME, approved=True), dict(FRAME, source_hash=C.INVENTORY_SHA256),
                      {"root": [True, "ك", "ل"], "profile": "all_attested"}):
            with self.subTest(frame=frame), self.assertRaises(NabtError):
                C.evaluate(RID, frame)

    def test_discrete_json_and_exact_input_preservation(self):
        for frame in ([], {1: "x"}, {"x": 1.5}, {"x": float("nan")},
                      {"x": (1, 2)}, {"x": "\ud800"}):
            with self.subTest(frame=frame), self.assertRaises(NabtError):
                C.evaluate(RID, frame)

    def test_resource_exhaustion_is_defer(self):
        for frame in ({"x": "a" * (C.MAX_FRAME_BYTES + 1)}, {"x": [0] * 8193}):
            with self.subTest(kind=type(frame["x"])), self.assertRaises(NabtError) as caught:
                C.evaluate(RID, frame)
            self.assertEqual(caught.exception.status, "DEFER")
        nested = {}
        for _ in range(26):
            nested = {"nested": nested}
        with self.assertRaises(NabtError) as caught:
            C.evaluate(RID, nested)
        self.assertEqual(caught.exception.status, "DEFER")

    def test_unknown_rule_defers_without_rejecting_arabic(self):
        with self.assertRaises(NabtError) as caught:
            C.evaluate("UNREGISTERED-RULE", {})
        self.assertEqual(caught.exception.status, "DEFER")

    def test_changed_installed_inventory_defers_before_use(self):
        fake = mock.Mock()
        fake.joinpath.return_value = fake
        fake.read_bytes.return_value = b'{}'
        with mock.patch.object(C, "files", return_value=fake):
            with self.assertRaises(NabtError) as caught:
                C.evaluate(RID, FRAME)
        self.assertEqual(caught.exception.status, "DEFER")
        self.assertEqual(caught.exception.code, "INSTALLED_CONTRACT_FAILED")
