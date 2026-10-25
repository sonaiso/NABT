"""Independent semantic controls and adversarial receipt boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import lexical_testimony as testimony
from tools import proof_lab


native_available = unittest.skipUnless(
    (testimony.ROOT / "formal/.lake/build/bin/lexicalDenotation").is_file(),
    "native lexicalDenotation executable is built in the Lean CI job")


class Testimony(unittest.TestCase):
    @native_available
    def test_three_distinct_indications_use_real_native_checker(self):
        for entry, target, indication in [
                ("فرس", ["واحد الخيل"], "mutabaqa"),
                ("بيت", ["المأوى"], "tadammun"),
                ("عمي", ["البصر"], "iltizam")]:
            result = testimony.assess(entry, target)
            self.assertTrue(result["native_checked"])
            self.assertEqual(result["common_indications"], [indication])
            self.assertFalse(result["world_truth_established"])
            self.assertFalse(result["intended_sense_established"])
            for row in result["rows"]:
                self.assertFalse(row["causal_or_legal_conclusion_established"])
                self.assertEqual(row["testimony"]["transmission_type"], "UNASSESSED")

    @native_available
    def test_no_invented_sun_or_tawatur_seed(self):
        result = testimony.assess("شمس", ["النهار"])
        self.assertEqual(result["status"], "UNMEASURED_ROOT")
        self.assertTrue(result["native_checked"])
        self.assertFalse(result["all_installed_readings_retained"])
        self.assertEqual(result["rows"], [])

    @native_available
    def test_all_three_qalam_senses_survive(self):
        result = testimony.assess("قلم", ["الذي يكتب به"])
        self.assertEqual([r["sense_id"] for r in result["rows"]],
                         ["lisan:qalam-writing", "lisan:qalam-lot", "lisan:qalam-gambling"])
        self.assertEqual(result["common_indications"], [])
        self.assertEqual(sum(r["indications"]["mutabaqa"] for r in result["rows"]), 1)

    @native_available
    def test_source_bytes_and_retained_quote_are_different_checks(self):
        house = testimony.assess("بيت", ["المأوى"])
        horse = testimony.assess("فرس", ["واحد الخيل"])
        self.assertTrue(house["rows"][0]["testimony"]["source_file_replayed"])
        self.assertFalse(horse["rows"][0]["testimony"]["source_file_replayed"])
        self.assertFalse(house["historical_authenticity_established"])

    @native_available
    def test_no_inverse_association_or_gloss_word_fragment(self):
        for entry, target in [("بصر", ["ذهاب البصر كله"]), ("فهم", ["القلب"]), ("أسد", ["العدالة"])]:
            result = testimony.assess(entry, target)
            self.assertTrue(result["native_checked"])
            self.assertEqual(result["common_indications"], [])
            self.assertTrue(all(not any(r["indications"].values()) for r in result["rows"]))

    @native_available
    def test_part_is_not_whole_and_duplicates_add_no_parts(self):
        result = testimony.assess("فرس", ["واحد الخيل", "واحد الخيل"])
        self.assertEqual(result["common_indications"], ["mutabaqa"])
        self.assertFalse(result["rows"][0]["indications"]["tadammun"])

    def test_malformed_inputs_never_call_native(self):
        with patch.object(testimony, "_native") as native:
            for entry, target in [(True, []), ("", []), ("بيت", [True]), ("بيت", "المأوى"),
                                  ("بيت", ["x"]*65), ("بيت", ["\ud800"]), ("\ud800", [])]:
                self.assertEqual(testimony.assess(entry, target)["status"], "INVALID_INPUT")
            native.assert_not_called()

    def test_missing_or_modified_catalogue_cannot_furnish_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(testimony.assess("بيت", ["المأوى"], root=root)["status"], "SOURCE_UNAVAILABLE")
            path = root / testimony.CATALOG
            path.parent.mkdir(parents=True)
            path.write_text('{"authority":"VERIFIED","senses":[]}')
            self.assertEqual(testimony.assess("بيت", ["المأوى"], root=root)["status"], "SOURCE_UNAVAILABLE")

    def test_corrupted_retained_source_blocks_before_native(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / testimony.CATALOG
            catalog.parent.mkdir(parents=True)
            catalog.write_bytes((testimony.ROOT / testimony.CATALOG).read_bytes())
            source = root / testimony.SOURCES["maqayis"][2]
            source.parent.mkdir(parents=True)
            source.write_text("ملف متغير")
            with patch.object(testimony, "_native") as native:
                self.assertEqual(testimony.assess("بيت", ["المأوى"], root=root)["status"], "SOURCE_UNAVAILABLE")
                native.assert_not_called()

    @native_available
    def test_native_forgery_dropped_with_no_positive_rows(self):
        real = testimony._native
        for mutation in ("flag", "omit", "world", "component", "indication"):
            def forged(exe, request=None):
                value = real(exe, request)
                if request is not None:
                    if mutation == "flag": value["complete_installed_proposal"] = 1
                    elif mutation == "omit": value["rows"] = []
                    elif mutation == "world": value["world_truth_asserted"] = True
                    elif mutation == "component": value["rows"][0]["sense"]["components"] = ["مزور"]
                    else: value["common_indications"] = ["iltizam"]
                return value
            with patch.object(testimony, "_native", side_effect=forged):
                result = testimony.assess("بيت", ["المأوى"])
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
                self.assertFalse(result["native_checked"])
                self.assertEqual(result["rows"], [])

    def test_transport_only_accepts_index_and_components(self):
        value = {"schema": proof_lab.REQUEST_SCHEMA, "mode": "testimony", "entry": "بيت", "target": ["المأوى"]}
        self.assertEqual(proof_lab.validate_payload(json.dumps(value)), value)
        for key in ("is_verified_by_app", "transmission_type", "reliability_weight", "source_text", "rules"):
            with self.assertRaises(proof_lab.RequestError):
                proof_lab.validate_payload(json.dumps({**value, key: True}))

    @native_available
    def test_actual_transport_receipt_uses_correct_binary_and_scope(self):
        value = {"schema": proof_lab.REQUEST_SCHEMA, "mode": "testimony", "entry": "بيت", "target": ["المأوى"]}
        result = proof_lab.run_payload(proof_lab.SMOKE_ID, json.dumps(value))
        self.assertEqual(result["status"], "CONDITIONAL_INTERPRETATIONS")
        self.assertEqual(result["native_sha256"], result["testimony"]["native_sha256"])
        self.assertEqual(result["scope"]["law_id"], testimony.LAW)
        self.assertNotIn("result", result)
        self.assertNotIn("benchmark", result)


if __name__ == "__main__":
    unittest.main()
