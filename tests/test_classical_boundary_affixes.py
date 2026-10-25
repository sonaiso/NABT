"""Independent source-example expectations and adversarial boundary controls."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt import classical_boundary_affixes as laws
from nabt.errors import NabtError


def example_frame(key):
    return next(row["frame"] for row in laws.source_examples() if row["example_id"] == key)


class ClassicalBoundaryAffixTests(unittest.TestCase):
    def test_qatr_three_weak_endings(self):
        gold = {
            "qatr_irmi": ["i", "ر", "م", "i"],
            "qatr_ughzu": ["u", "غ", "ز", "u"],
            "qatr_ikhsha": ["i", "خ", "ش", "a"],
        }
        for key, expected in gold.items():
            with self.subTest(key=key):
                actual = laws.evaluate_example(key)
                self.assertEqual([x["segments"] for x in actual["alternatives"]], [expected])
                self.assertEqual(actual["output_layer"], "morphological_preboundary")
                self.assertFalse(actual["language_license"])
                self.assertFalse(actual["premises_established"])

    def test_weak_is_productive_conditional_operation(self):
        f = example_frame("qatr_irmi")
        f["segments"] = ["i", "ه", "د", "i:"]
        self.assertEqual(laws.evaluate(laws.RULE_IDS[0], f)["alternatives"][0]["segments"], ["i", "ه", "د", "i"])
        # Not an attestation claim for an arbitrary frame or a full-word recognizer.
        f["segments"] = ["ك", "ت", "ب", "ل", "م", "ي", "i:"]
        self.assertFalse(laws.evaluate(laws.RULE_IDS[0], f)["language_license"])

    def test_weak_subject_profiles_are_not_collapsed(self):
        for person in ("2fs", "2dual", "2mp", "2fp"):
            f = example_frame("qatr_irmi"); f["person"] = person
            with self.subTest(person=person):
                self.assertEqual(laws.evaluate(laws.RULE_IDS[0], f)["alternatives"], [])

    def test_weak_suffix_and_unsupported_radical_block(self):
        for suffix in ("subject", "object", "emphatic"):
            f = example_frame("qatr_irmi"); f["suffix"] = suffix
            self.assertEqual(laws.evaluate(laws.RULE_IDS[0], f)["alternatives"], [])
        for radical in ("و", "sound"):
            f = example_frame("qatr_irmi"); f["final_radical"] = radical
            self.assertEqual(laws.evaluate(laws.RULE_IDS[0], f)["alternatives"], [])

    def test_weak_shape_rejects_absent_or_unmatched_final_vowel(self):
        for shape in (["i", "ر", "م", "i"], ["i:"], ["ك", "a", "i:"]):
            f = example_frame("qatr_irmi"); f["segments"] = shape
            self.assertEqual(laws.evaluate(laws.RULE_IDS[0], f)["alternatives"], [])

    def test_weak_boundaries_recorded_not_silently_projected(self):
        f = example_frame("qatr_irmi"); f.update(start="wasl", end="waqf")
        r = laws.evaluate(laws.RULE_IDS[0], f)
        self.assertEqual(r["input"], f)
        self.assertEqual(r["output_layer"], "morphological_preboundary")
        self.assertEqual(r["alternatives"][0]["segments"], ["i", "ر", "م", "i"])

    def test_pausal_light_nun_gold(self):
        gold = {
            "sibawayhi_idriba": [["i", "ض", "ر", "i", "ب", "a:"]],
            "sibawayhi_idribi": [["i", "ض", "ر", "i", "ب", "i:"]],
            "sibawayhi_idribu": [["i", "ض", "ر", "i", "ب", "u:"]],
            "sibawayhi_ikhshay": [["i", "خ", "ش", "a", "ي"], ["i", "خ", "ش", "a", "ي", "i:"]],
            "sibawayhi_ikhshaw": [["i", "خ", "ش", "a", "و"], ["i", "خ", "ش", "a", "و", "u:"]],
        }
        for key, expected in gold.items():
            with self.subTest(key=key):
                self.assertEqual([x["segments"] for x in laws.evaluate_example(key)["alternatives"]], expected)

    def test_restore_indicative_nun_and_preserve_analogy_rank(self):
        for key, suffix in (("sibawayhi_tadribin", "i:"), ("sibawayhi_tadribun", "u:")):
            r = laws.evaluate_example(key)
            self.assertEqual([x["segments"][-2:] for x in r["alternatives"]], [[suffix, "ن"], ["ب", suffix]])
            self.assertEqual([x["evidence_kind"] for x in r["alternatives"]], ["reported_khalil", "source_analogical_yunus"])
        r = laws.evaluate_example("sibawayhi_tadriban")
        self.assertEqual(r["alternatives"][0]["segments"][-2:], ["a:", "ن"])

    def test_profile_filters_do_not_merge_the_variants(self):
        for profile, count, rank in (("khalil", 1, "reported_khalil"), ("yunus", 1, "reported_yunus"), ("both", 2, "reported_khalil")):
            f = example_frame("sibawayhi_ikhshay"); f["profile"] = profile
            r = laws.evaluate(laws.RULE_IDS[1], f)
            self.assertEqual(len(r["alternatives"]), count)
            self.assertEqual(r["alternatives"][0]["evidence_kind"], rank)

    def test_light_nun_in_connection(self):
        f = example_frame("sibawayhi_idribi"); f.update(end="wasl", following="consonant")
        self.assertEqual(laws.evaluate(laws.RULE_IDS[1], f)["alternatives"][0]["segments"], f["segments"])
        f["following"] = "hamzat_wasl"
        self.assertEqual(laws.evaluate(laws.RULE_IDS[1], f)["alternatives"][0]["segments"], ["i", "ض", "ر", "i", "ب", "i"])
        self.assertNotIn("i:", laws.evaluate(laws.RULE_IDS[1], f)["alternatives"][0]["segments"])

    def test_dual_source_nun_not_confused_with_light_nun(self):
        f = example_frame("sibawayhi_tadriban"); f.update(end="wasl", following="hamzat_wasl")
        self.assertEqual(laws.evaluate(laws.RULE_IDS[1], f)["alternatives"][0]["segments"], f["segments"])

    def test_heavy_and_feminine_nun_are_outside_rule(self):
        for kind in ("heavy", "feminine"):
            f = example_frame("sibawayhi_idriba"); f["nun_kind"] = kind
            r = laws.evaluate(laws.RULE_IDS[1], f)
            self.assertEqual(r["alternatives"], [])
            self.assertEqual(r["reason"], "heavy_and_feminine_nun_are_not_light_nun")

    def test_false_shape_not_licensed_by_label(self):
        f = example_frame("sibawayhi_idriba"); f["shape"] = "deleted_ya_command"
        self.assertEqual(laws.evaluate(laws.RULE_IDS[1], f)["alternatives"], [])

    def test_no_connected_follower_at_pause(self):
        for following in ("hamzat_wasl", "consonant"):
            f = example_frame("sibawayhi_idriba"); f["following"] = following
            with self.subTest(following=following), self.assertRaises(NabtError):
                laws.evaluate(laws.RULE_IDS[1], f)

    def test_ana_majority_and_reported_sukun(self):
        r = laws.evaluate_example("mughni_ana")
        self.assertEqual([x["segments"] for x in r["alternatives"]], [["ء", "a", "ن", "a"], ["ء", "a", "ن"]])
        f = example_frame("mughni_ana"); f.update(profile="majority", end="waqf")
        r = laws.evaluate(laws.RULE_IDS[2], f)
        self.assertEqual(r["alternatives"][0]["segments"], ["ء", "a", "ن", "a:"])

    def test_ana_is_not_masdariyya_particle(self):
        f = example_frame("mughni_ana"); f["analysis"] = "masdariyya_particle"
        self.assertEqual(laws.evaluate(laws.RULE_IDS[2], f)["alternatives"], [])
        f = example_frame("mughni_ana"); f["segments"] = ["ء", "a", "ن"]
        self.assertEqual(laws.evaluate(laws.RULE_IDS[2], f)["alternatives"], [])

    def test_unresolved_minority_pause_is_visible_even_in_union(self):
        for profile in ("minority_sukun", "both"):
            f = example_frame("mughni_ana"); f.update(profile=profile, end="waqf")
            r = laws.evaluate(laws.RULE_IDS[2], f)
            self.assertFalse(r["alternatives_complete_within_requested_profile"])
            self.assertEqual(r["unresolved_profiles"], ["minority_sukun_pause"])
            if profile == "minority_sukun": self.assertEqual(r["status"], "DEFER")

    def test_unresolved_yunus_dual_is_visible_even_in_union(self):
        for profile in ("yunus", "both"):
            f = example_frame("sibawayhi_tadriban"); f["profile"] = profile
            r = laws.evaluate(laws.RULE_IDS[1], f)
            self.assertFalse(r["alternatives_complete_within_requested_profile"])
            self.assertEqual(r["unresolved_profiles"], ["yunus_indicative_dual"])
            if profile == "yunus": self.assertEqual(r["status"], "DEFER")

    def test_strict_input_validation(self):
        f = example_frame("qatr_irmi")
        for field, value in (("segments", [True]), ("segments", [1]), ("segments", "ارمي"), ("start", True), ("person", True), ("suffix", 0), ("end", "ibtida")):
            mutated = deepcopy(f); mutated[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(NabtError):
                laws.evaluate(laws.RULE_IDS[0], mutated)
        for bad in (None, [], {**f, "authorized": True}, {k:v for k,v in f.items() if k != "suffix"}):
            with self.assertRaises(NabtError): laws.evaluate(laws.RULE_IDS[0], bad)
        with self.assertRaises(NabtError): laws.evaluate(True, f)
        with self.assertRaises(NabtError): laws.evaluate("NONEXISTENT", f)

    def test_resource_limit_is_defer(self):
        f = example_frame("qatr_irmi"); f["segments"] = ["ك"] * 257
        with self.assertRaises(NabtError) as caught: laws.evaluate(laws.RULE_IDS[0], f)
        self.assertEqual(caught.exception.status, "DEFER")
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")

    def test_outputs_and_catalog_are_defensive_copies(self):
        f = example_frame("qatr_irmi"); original = deepcopy(f)
        r = laws.evaluate(laws.RULE_IDS[0], f)
        r["input"]["segments"].append("ك")
        self.assertEqual(f, original)
        rows = laws.source_examples(); rows[0]["frame"]["person"] = "2fp"
        self.assertEqual(example_frame("qatr_irmi")["person"], "2ms")

    def test_all_installed_examples_replay_original_source(self):
        for row in laws.source_examples():
            with self.subTest(example=row["example_id"]):
                r = laws.evaluate_example(row["example_id"])
                self.assertEqual(r["status"], "CONDITIONAL")
                self.assertTrue(r["source_spans"])
                self.assertFalse(r["whole_word_automatically_acquired"])
        with self.assertRaises(NabtError): laws.evaluate_example("invented")

    def test_tampered_source_and_inventory_fail_closed(self):
        root = Path(__file__).resolve().parents[1] / "src/nabt"
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp); directory = package / "data/source_evidence"; directory.mkdir(parents=True)
            for name in ("classical_rule_inventory_v1.json", "qatr.txt"):
                (directory / name).write_bytes((root / "data/source_evidence" / name).read_bytes())
            with patch.object(laws, "files", return_value=package):
                self.assertEqual(laws.evaluate_example("qatr_irmi")["status"], "CONDITIONAL")
                source = directory / "qatr.txt"; raw = source.read_bytes(); source.write_bytes(b"!" + raw[1:])
                with self.assertRaises(NabtError) as caught: laws.evaluate_example("qatr_irmi")
                self.assertEqual(caught.exception.status, "DEFER")
                source.write_bytes(raw)
                inventory = directory / "classical_rule_inventory_v1.json"
                inventory.write_bytes(inventory.read_bytes() + b" ")
                with self.assertRaises(NabtError): laws.evaluate_example("qatr_irmi")

    def test_finite_table_counts_and_independent_specific_boundaries(self):
        rows = laws.finite_export_rows()
        self.assertEqual(len(rows), 486)
        self.assertEqual(sum(r["rule_id"] == laws.RULE_IDS[0] for r in rows), 180)
        self.assertEqual(sum(r["rule_id"] == laws.RULE_IDS[1] for r in rows), 288)
        self.assertEqual(sum(r["rule_id"] == laws.RULE_IDS[2] for r in rows), 18)
        for row in rows:
            if row["rule_id"] == laws.RULE_IDS[0] and row["frame"]["person"] != "2ms":
                self.assertEqual(row["alternatives"], [])
            if row["rule_id"] == laws.RULE_IDS[1] and row["frame"]["nun_kind"] != "light":
                self.assertEqual(row["alternatives"], [])

if __name__ == "__main__":
    unittest.main()
