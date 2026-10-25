"""Source-authored gold and adversarial boundaries, not a mirrored recurrence."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt.classical_hamza import RULE_IDS, evaluate, finite_export_rows
from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "evidence/arabic_completion_v6/hamza/diagnostics.json"


class ClassicalHamzaTests(unittest.TestCase):
    def test_all_independent_diagnostics_exact(self):
        cases = json.loads(GOLD.read_text())["cases"]
        self.assertEqual(len(cases), 33)
        self.assertEqual({c["rule_id"] for c in cases}, set(RULE_IDS))
        for case in cases:
            with self.subTest(case=case["case_id"]):
                actual = evaluate(case["rule_id"], case["frame"])
                self.assertEqual(actual["status"], case["expected_status"])
                self.assertEqual([a["operation"] for a in actual["alternatives"]], case["expected_operations"])
                self.assertEqual([a["morphophonemes"] for a in actual["alternatives"]], case["expected_outputs"])
                self.assertFalse(actual["premises_established"])
                self.assertFalse(actual["language_license_granted"])
                self.assertEqual(actual["input_frame"], case["frame"])
                self.assertTrue(actual["source_replayed"])

    def test_interrogative_alternatives_remain_distinct_in_wasl(self):
        result = evaluate(RULE_IDS[0], {"tail": list("رجل"), "boundary": "wasl"})
        self.assertEqual(len(result["alternatives"]), 2)
        self.assertNotEqual(result["alternatives"][0], result["alternatives"][1])
        for alt in result["alternatives"]:
            self.assertEqual(alt["morphophonemes"][0], "ء")

    def test_singular_alignment_is_retained_and_not_caller_target(self):
        frame = {"singular": list("كتيبة"), "singular_long_origin": "added_long", "plural_template": "mafail"}
        result = evaluate(RULE_IDS[3], frame)
        self.assertEqual(result["input_morphophonemes"], list("كتايب"))
        self.assertEqual(result["alternatives"][0]["morphophonemes"], list("كتاءب"))
        self.assertEqual(result["input_frame"]["singular"], list("كتيبة"))
        frame["singular"][0] = "س"
        self.assertEqual(result["input_frame"]["singular"], list("كتيبة"))

    def test_no_unicode_normalization_or_unvowelized_input_parser(self):
        for bad in (["قَ"], ["أ"], ["ؤ"], ["ئ"], [True], "ق"):
            with self.subTest(bad=bad), self.assertRaises(NabtError) as ctx:
                evaluate(RULE_IDS[0], {"tail": bad, "boundary": "ibtida"})
            self.assertEqual(ctx.exception.code, "INVALID_CLASSICAL_HAMZA_FRAME")

    def test_extra_missing_and_unknown_fields_rejected(self):
        valid = {"first": "ق", "last": "ل", "glide": "waw", "verb_medial": "changed_to_alif"}
        for frame in (dict(valid, attested=True), {k:v for k,v in valid.items() if k != "glide"},
                      dict(valid, verb_medial=True), dict(valid, glide="alif")):
            with self.subTest(frame=frame), self.assertRaises(NabtError) as ctx:
                evaluate(RULE_IDS[2], frame)
            self.assertEqual(ctx.exception.code, "INVALID_CLASSICAL_HAMZA_FRAME")

    def test_arbitrary_feminine_ta_position_is_malformed(self):
        with self.assertRaises(NabtError):
            evaluate(RULE_IDS[3], {"singular": list("صةيفة"),
                     "singular_long_origin": "added_long", "plural_template": "mafail"})

    def test_resource_exhaustion_is_defer_not_rejection(self):
        with self.assertRaises(NabtError) as ctx:
            evaluate(RULE_IDS[0], {"tail": ["ر"] * 129, "boundary": "ibtida"})
        self.assertEqual((ctx.exception.code, ctx.exception.status), ("RESOURCE_LIMIT", "DEFER"))

    def test_unknown_rule_is_defer(self):
        with self.assertRaises(NabtError) as ctx:
            evaluate("HAMZA-ALL-ARABIC", {})
        self.assertEqual(ctx.exception.status, "DEFER")

    def test_installed_source_change_cannot_license(self):
        with patch("nabt.classical_hamza.INVENTORY_SHA256", "0" * 64):
            with self.assertRaises(NabtError) as ctx:
                evaluate(RULE_IDS[5], {"root": list("ءكل"), "profile": "all_attested"})
        self.assertEqual((ctx.exception.code, ctx.exception.status), ("INSTALLED_CONTRACT_FAILED", "DEFER"))

    def test_branch_controls_covered_once(self):
        rows = finite_export_rows()
        self.assertEqual(len(rows), 40)
        self.assertEqual(len({json.dumps(r["frame"], sort_keys=True, ensure_ascii=False) + r["rule_id"] for r in rows}), 40)

    def test_named_lexical_scope_does_not_delete_other_hamza(self):
        for root in ("ءسر", "ءمر", "ءكل", "ءخذ"):
            report = evaluate(RULE_IDS[5], {"root": list(root), "profile": "all_attested"})
            self.assertFalse(report["language_license_granted"])
        self.assertEqual(evaluate(RULE_IDS[5], {"root": list("ءسر"), "profile": "all_attested"})["alternatives"], [])


if __name__ == "__main__":
    unittest.main()
