"""Hand-specified source examples/counterexamples; not a blind corpus benchmark."""
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nabt.classical_gemination import RULE_IDS, evaluate, finite_export_rows, replay_sources
from nabt.errors import NabtError


def command(dialect="attested_union"):
    # Sibawayhi 14385–14411: اردد / رد, with authored explicit vowel transcription.
    return {"prefix": [["ٱ", "u"], ["ر", "s"]], "first": ["د", "u"],
            "second": ["د", "s"], "suffix": [], "context": "command", "dialect": dialect}


def operations(report):
    return [a["operation"] for a in report["alternatives"]]


class ClassicalGeminationTests(unittest.TestCase):
    def test_voweled_final_contracts_with_both_radicals_retained(self):
        f = command()
        f.update(prefix=[["ر", "a"]], first=["د", "a"], second=["د", "a"], context="ordinary")
        a = evaluate(RULE_IDS[0], f)["alternatives"][0]
        self.assertEqual(a["cells"], [["ر", "a"], ["د", "s"], ["د", "a"]])

    def test_suffix_is_not_discarded(self):
        f = command()
        f.update(second=["د", "i"], suffix=[["ي", "s"]], context="ordinary")
        a = evaluate(RULE_IDS[0], f)["alternatives"][0]
        self.assertEqual(a["cells"], [["ر", "u"], ["د", "s"], ["د", "i"], ["ي", "s"]])

    def test_sukun_final_outside_voweled_rule(self):
        f = command(); f["context"] = "ordinary"
        self.assertEqual(evaluate(RULE_IDS[0], f)["status"], "OUTSIDE_SCOPE")

    def test_hijaz_retains_split_and_initial_wasl(self):
        a = evaluate(RULE_IDS[1], command("hijaz"))["alternatives"][0]
        self.assertEqual(a["cells"], [["ٱ", "u"], ["ر", "s"], ["د", "u"], ["د", "s"]])
        self.assertEqual(a["operation"], "split")

    def test_tamim_preserves_two_attested_vowel_policies(self):
        r = evaluate(RULE_IDS[1], command("tamim"))
        self.assertEqual(operations(r), ["contract_a", "contract_u"])
        self.assertEqual([a["cells"] for a in r["alternatives"]], [
            [["ر", "u"], ["د", "s"], ["د", "a"]],
            [["ر", "u"], ["د", "s"], ["د", "u"]]])

    def test_union_does_not_erase_hijaz_or_kasra_group(self):
        self.assertEqual(operations(evaluate(RULE_IDS[1], command())),
                         ["split", "contract_a", "contract_i", "contract_u"])

    def test_kab_ghani_explicit_kasra(self):
        a = evaluate(RULE_IDS[1], command("kab_ghani"))["alternatives"][0]
        self.assertEqual(a["cells"][-1], ["د", "i"])

    def test_no_duplicate_fatha_policy(self):
        f = command("tamim"); f["first"] = ["د", "a"]
        self.assertEqual(operations(evaluate(RULE_IDS[1], f)), ["contract_a"])

    def test_hamza_removed_only_at_direct_newly_vocalized_onset(self):
        f = command("tamim")
        f.update(prefix=[["ٱ", "i"], ["ط", "s"], ["م", "a"], ["ء", "s"]],
                 first=["ن", "i"], second=["ن", "s"])
        a = evaluate(RULE_IDS[1], f)["alternatives"][0]
        self.assertEqual(a["cells"], [["ٱ", "i"], ["ط", "s"], ["م", "a"], ["ء", "i"], ["ن", "s"], ["ن", "a"]])
        self.assertFalse(a["initial_wasl_removed"])
        self.assertTrue(a["vowel_transferred"])

    def test_qat_hamza_not_removed(self):
        f = command("tamim"); f["prefix"] = [["أ", "a"], ["م", "s"]]
        self.assertEqual(evaluate(RULE_IDS[1], f)["alternatives"][0]["cells"][0], ["أ", "a"])

    def test_existing_prefix_vowel_not_replaced(self):
        f = command("tamim"); f["prefix"] = [["ر", "a"]]
        a = evaluate(RULE_IDS[1], f)["alternatives"][0]
        self.assertEqual(a["cells"][0], ["ر", "a"])
        self.assertFalse(a["vowel_transferred"])

    def test_following_policy_uses_actual_preceding_vowel_not_deleted_vowel(self):
        # Independent review counterexample: اجترر has تَ before the pair;
        # its moving vowel remains and must not be replaced by the first رِ.
        f = command("tamim")
        f.update(prefix=[["ٱ", "i"], ["ج", "s"], ["ت", "a"]],
                 first=["ر", "i"], second=["ر", "s"])
        r = evaluate(RULE_IDS[1], f)
        self.assertEqual(operations(r), ["contract_a"])
        self.assertEqual(r["alternatives"][0]["cells"],
                         [["ٱ", "i"], ["ج", "s"], ["ت", "a"], ["ر", "s"], ["ر", "a"]])
        self.assertEqual(len(r["source_spans"]), 2)

    def test_long_alif_predecessor_is_not_assigned_the_deleted_vowel(self):
        f = command("tamim")
        f.update(prefix=[["م", "a"], ["ا", "s"]], first=["د", "i"])
        r = evaluate(RULE_IDS[1], f)
        self.assertEqual(operations(r), ["contract_a"])
        self.assertEqual(r["alternatives"][0]["cells"][1], ["ا", "s"])

    def test_execution_bound_is_not_linguistic_failure(self):
        f = command(); f["prefix"] = [["ب", "a"]] * 129
        with self.assertRaises(NabtError) as e: evaluate(RULE_IDS[1], f)
        self.assertEqual(e.exception.code, "RESOURCE_LIMIT")
        self.assertEqual(e.exception.status, "DEFER")

    def test_bakr_passage_not_general_jussive_authority(self):
        self.assertEqual(evaluate(RULE_IDS[1], command("bakr"))["status"], "OUTSIDE_SCOPE")

    def test_feminine_suffix_keeps_split_for_majority(self):
        f = command("hijaz"); f.update(context="feminine", suffix=[["ن", "a"]])
        a = evaluate(RULE_IDS[2], f)["alternatives"][0]
        self.assertEqual(a["cells"], [["ٱ", "u"], ["ر", "s"], ["د", "u"], ["د", "s"], ["ن", "a"]])

    def test_feminine_bakr_variant_is_retained_without_fabricated_vowel(self):
        f = command("bakr"); f.update(context="feminine", suffix=[["ن", "a"]])
        a = evaluate(RULE_IDS[2], f)["alternatives"][0]
        self.assertEqual(a["operation"], "bakr_contraction_unvocalized")
        self.assertIsNone(a["cells"]); self.assertIsNone(a["segments"])
        self.assertFalse(a["surface_complete"])

    def test_feminine_union_keeps_both_readings(self):
        f = command(); f.update(context="feminine", suffix=[["ن", "a"]])
        self.assertEqual(operations(evaluate(RULE_IDS[2], f)), ["split", "bakr_contraction_unvocalized"])

    def test_feminine_label_without_nun_does_not_suffice(self):
        f = command(); f["context"] = "feminine"
        self.assertEqual(evaluate(RULE_IDS[2], f)["status"], "OUTSIDE_SCOPE")

    def test_af_il_exclamation_split(self):
        f = command("tamim")
        f.update(prefix=[["أ", "a"], ["ح", "s"]], first=["ب", "i"], second=["ب", "s"], context="exclamation")
        a = evaluate(RULE_IDS[3], f)["alternatives"][0]
        self.assertEqual(a["cells"], [["أ", "a"], ["ح", "s"], ["ب", "i"], ["ب", "s"]])

    def test_exclamation_label_on_other_shape_is_insufficient(self):
        f = command(); f["context"] = "exclamation"
        self.assertEqual(evaluate(RULE_IDS[3], f)["status"], "OUTSIDE_SCOPE")

    def test_hallumma_exception_is_exact_lexical_shape(self):
        f = command(); f.update(prefix=[["ه", "a"], ["ل", "u"]], first=["م", "s"], second=["م", "a"], context="hallumma")
        self.assertEqual(operations(evaluate(RULE_IDS[3], f)), ["retain_hallumma"])
        f["prefix"][0] = ["ك", "a"]
        self.assertEqual(evaluate(RULE_IDS[3], f)["status"], "OUTSIDE_SCOPE")

    def test_mismatched_radicals_and_glides_outside_scope(self):
        for first, second in ((["د", "u"], ["ب", "s"]), (["ي", "i"], ["ي", "s"])):
            f = command(); f.update(first=first, second=second)
            self.assertEqual(evaluate(RULE_IDS[1], f)["status"], "OUTSIDE_SCOPE")

    def test_unknown_suffix_or_internal_wasl_outside_scope(self):
        f = command(); f["suffix"] = [["ه", "u"]]
        self.assertEqual(evaluate(RULE_IDS[1], f)["status"], "OUTSIDE_SCOPE")
        f = command(); f["prefix"].append(["ٱ", "i"])
        self.assertEqual(evaluate(RULE_IDS[1], f)["status"], "OUTSIDE_SCOPE")

    def test_malformed_frames_are_not_linguistic_rejections(self):
        for mutate in (lambda x:x.update(dialect=True), lambda x:x.update(extra=True),
                       lambda x:x.update(first=["د", True]), lambda x:x.update(prefix="رد")):
            f = command(); mutate(f)
            with self.assertRaises(NabtError) as e: evaluate(RULE_IDS[1], f)
            self.assertEqual(e.exception.code, "INVALID_GEMINATION_FRAME")

    def test_original_input_and_non_authority_preserved(self):
        f = command(); old = deepcopy(f)
        r = evaluate(RULE_IDS[1], f)
        self.assertEqual(f, old); self.assertEqual(r["original_frame"], old)
        self.assertFalse(r["premises_established"])
        self.assertFalse(r["word_attestation_established"])

    def test_nun_before_ba_inside_word_and_across_wasl(self):
        for connection in ("within_word", "word_boundary_wasl"):
            r = evaluate(RULE_IDS[-1], {"left": ["ن", "s"], "right": ["ب", "a"], "connection": connection})
            self.assertEqual(r["alternatives"][0]["cells"], [["م", "s"], ["ب", "a"]])
            self.assertTrue(r["textual_discrepancy_retained"])
            self.assertEqual({s["source_id"] for s in r["source_spans"]}, {"alfiyya", "ibn_aqil", "sibawayhi"})

    def test_nun_never_to_mim_before_ya_or_across_pause(self):
        for right, connection in (("ي", "within_word"), ("د", "within_word"), ("ب", "word_boundary_waqf")):
            r = evaluate(RULE_IDS[-1], {"left": ["ن", "s"], "right": [right, "a"], "connection": connection})
            self.assertEqual(r["status"], "OUTSIDE_SCOPE")

    def test_vocalized_nun_blocked(self):
        for vowel in ("a", "i", "u"):
            r = evaluate(RULE_IDS[-1], {"left": ["ن", vowel], "right": ["ب", "a"], "connection": "within_word"})
            self.assertEqual(r["alternatives"], [])

    def test_pinned_inventory_tamper_defers(self):
        with patch("nabt.classical_gemination.INVENTORY_SHA256", "0" * 64):
            with self.assertRaises(NabtError) as e: evaluate(RULE_IDS[1], command())
        self.assertEqual(e.exception.status, "DEFER")

    def test_source_tamper_with_unchanged_inventory_defers(self):
        original = files("nabt").joinpath("data/source_evidence")
        with TemporaryDirectory() as tmp:
            directory = Path(tmp) / "data/source_evidence"
            directory.mkdir(parents=True)
            (directory / "classical_rule_inventory_v1.json").write_bytes(
                original.joinpath("classical_rule_inventory_v1.json").read_bytes())
            raw = original.joinpath("sibawayhi.txt").read_bytes()
            # Same-length corruption: a retained hash alone cannot grant authority.
            (directory / "sibawayhi.txt").write_bytes(b"X" + raw[1:])
            with patch("nabt.classical_gemination.files", return_value=Path(tmp)):
                with self.assertRaises(NabtError) as e: evaluate(RULE_IDS[1], command())
            self.assertEqual(e.exception.code, "INSTALLED_CONTRACT_FAILED")
            self.assertEqual(e.exception.status, "DEFER")

    def test_unknown_rule_and_malformed_rule_are_separate(self):
        with self.assertRaises(NabtError) as e: evaluate("unreviewed", command())
        self.assertEqual(e.exception.status, "DEFER")
        with self.assertRaises(NabtError) as e: evaluate(True, command())
        self.assertEqual(e.exception.code, "INVALID_GEMINATION_RULE")

    def test_exact_source_reading_still_contains_ya(self):
        raw = files("nabt").joinpath("data/source_evidence/alfiyya.txt").read_bytes()
        self.assertEqual(sha256(raw[95037:95134]).hexdigest(), "bf01fdbde1d23f2a10db757de3a7f69dc125cd9b56654a7ff39e5442bf11442a")
        self.assertIn("وقبل يا", raw[95037:95134].decode())
        self.assertEqual(len(replay_sources(RULE_IDS[-1])), 3)

    def test_finite_denominators_do_not_claim_language_coverage(self):
        rows = finite_export_rows()
        self.assertEqual(len(rows["morphology"]), 1920)
        self.assertEqual(len(rows["assimilation"]), 72)
        self.assertEqual(len(rows["projections"]), 504)
        self.assertEqual(len({json.dumps(r, sort_keys=True) for r in rows["morphology"]}), 1920)


if __name__ == "__main__":
    unittest.main()
