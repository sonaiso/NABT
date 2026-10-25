"""Integrity and scope regressions for the independent classical-source inventory."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("classical_rule_inventory", ROOT / "tools/classical_rule_inventory.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DIRECTORY = ROOT / "src/nabt/data/source_evidence"


class ClassicalInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads((DIRECTORY / "classical_rule_inventory_v1.json").read_text())

    def test_replays_scoped_denominator_without_language_claim(self):
        result = MODULE.validate_inventory(self.inventory, DIRECTORY)
        self.assertEqual(result["rule_denominator"], 38)
        self.assertEqual(result["source_count"], 6)
        self.assertEqual(result["reference_construction_count"], 6)
        self.assertEqual(result["reference_reading_count"], 12)
        self.assertEqual(result["source_review_statuses"]["textual_discrepancy"], 1)
        self.assertFalse(result["universal_completeness_claim"])
        self.assertEqual(result["reference_evaluation_status"], "not_run")

    def reject(self, mutate):
        inventory = deepcopy(self.inventory)
        mutate(inventory)
        with self.assertRaises(ValueError):
            MODULE.validate_inventory(inventory, DIRECTORY)

    def test_source_corruption_is_not_a_new_authority(self):
        self.reject(lambda d: d["sources"][0].update(raw_sha256="0" * 64))

    def test_source_quote_cannot_change_while_hash_stays(self):
        self.reject(lambda d: d["rules"][0]["source_spans"][0].update(raw_text="نص مفترض"))

    def test_line_and_byte_identity_must_agree(self):
        self.reject(lambda d: d["rules"][0]["source_spans"][0].update(line_end=64))

    def test_boolean_is_not_a_span_index(self):
        self.reject(lambda d: d["rules"][0]["source_spans"][0].update(start=True))

    def test_duplicate_rule_cannot_inflate_denominator(self):
        self.reject(lambda d: d["rules"].append(deepcopy(d["rules"][0])))

    def test_disputed_text_cannot_be_marked_implemented(self):
        disputed = next(i for i, r in enumerate(self.inventory["rules"]) if r["status"] == "textual_discrepancy")
        self.reject(lambda d: d["rules"][disputed].update(implementation={
            "status": "scoped_implemented", "paths": ["imaginary"], "scope": "forged"}))

    def test_reference_material_cannot_claim_an_executed_benchmark(self):
        self.reject(lambda d: d["reference_constructions"][0].update(evaluation_status="passed"))

    def test_duplicate_alternative_cannot_inflate_reading_count(self):
        self.reject(lambda d: d["reference_constructions"][0]["expected_alternatives"].append(
            deepcopy(d["reference_constructions"][0]["expected_alternatives"][0])))

    def test_original_text_discrepancy_remains_visible(self):
        disputed = next(r for r in self.inventory["rules"] if r["status"] == "textual_discrepancy")
        self.assertIn("وقبل يا", disputed["source_spans"][0]["raw_text"])
        self.assertIn("وقبل با", disputed["source_spans"][1]["raw_text"])
        self.assertEqual(disputed["implementation"]["status"], "not_evaluated")

    def test_editorial_appendix_is_not_attributed_to_ibn_aqil(self):
        for rule in self.inventory["rules"]:
            for span in rule["source_spans"]:
                if span["source_id"] == "ibn_aqil":
                    self.assertLess(span["line_end"], 9658)


if __name__ == "__main__":
    unittest.main()
