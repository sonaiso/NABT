"""Literal independent diagnostics and attacks on weak-law domain boundaries."""
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt import classical_weak as w
from nabt.errors import NabtError


class WeakLaws(unittest.TestCase):
    def setUp(self):
        self.examples = {e["id"]: e for e in w.source_examples()}

    def run_example(self, key, **changes):
        e = self.examples[key]
        f = deepcopy(e["frame"])
        f.update(changes)
        return w.evaluate(e["rule_id"], f)

    def test_literal_source_consequences(self):
        # These outputs were specified from the cited examples, independently of
        # _transform and control_actions. They are abstract cells, not spelling.
        expected = {
            "waada": [["ي","a"],["ع","i"],["د","u"]],
            "wasia": [["ي","a"],["س","a"],["ع","u"]],
            "mizan": [["م","i"],["ي","0"],["ز","a"],["ا","0"],["ن","u"]],
            "muqin": [["م","u"],["و","0"],["ق","i"],["ن","u"]],
            "bid": [["ب","i"],["ي","0"],["ض","u"]],
            "qala": [["ق","a"],["ا","0"],["ل","a"]],
            "awira": [["ع","a"],["و","i"],["ر","a"]],
            "ishtawaru": [["ا","i"],["ش","0"],["ت","a"],["و","a"],["ر","u"],["و","0"],["ا","0"]],
            "ibtayu": [["ا","i"],["ب","0"],["ت","a"],["ا","0"],["ع","u"],["و","0"],["ا","0"]],
            "hawa": [["ه","a"],["و","a"],["ا","0"]],
            "ghaya": [["غ","a"],["ا","0"],["ي","a"],["ت","u"]],
            "jawalan": [["ج","a"],["و","a"],["ل","a"],["ا","0"],["ن","u"]],
            "yaqumu": [["ي","a"],["ق","u"],["و","0"],["م","u"]],
        }
        self.assertEqual(set(expected), set(self.examples))
        for key, result in expected.items():
            with self.subTest(key=key):
                got = self.run_example(key)
                self.assertEqual([a["cells"] for a in got["alternatives"]], [result])
                self.assertEqual(got["status"], "CONDITIONAL")
                self.assertIs(got["application_established"], False)
                self.assertEqual(got["input"], self.examples[key]["frame"])

    def assert_blocked(self, key, **changes):
        result = self.run_example(key, **changes)
        self.assertEqual(result["status"], "OUTSIDE_RULE_DOMAIN")
        self.assertEqual(result["alternatives"], [])

    def test_initial_waw_does_not_delete_yawjal(self):
        self.assert_blocked("waada", cells=[["ي","a"],["و","0"],["ج","a"],["ل","u"]])

    def test_initial_ya_preserved(self):
        self.assert_blocked("waada", cells=[["ي","a"],["ي","0"],["س","i"],["ر","u"]])

    def test_open_exception_closed_names(self):
        self.assert_blocked("wasia", cells=[["ي","a"],["و","0"],["ج","a"],["ل","u"]], lexeme="وسع")

    def test_initial_scope_prefix_and_position(self):
        self.assert_blocked("waada", position="ayn")
        self.assert_blocked("waada", context="ordinary")
        self.assert_blocked("waada", cells=[["ت","a"],["و","0"],["ع","i"],["د","u"]])

    def test_waw_to_ya_requires_sukun_and_kasra(self):
        self.assert_blocked("mizan", cells=[["م","i"],["و","a"],["ز","a"],["ا","0"],["ن","u"]])
        self.assert_blocked("mizan", cells=[["م","u"],["و","0"],["ز","a"],["ا","0"],["ن","u"]])

    def test_plural_exception_changes_vowel_not_glide(self):
        result = self.run_example("bid")
        self.assertEqual(result["alternatives"][0]["action"], "lower_previous")
        self.assertEqual(result["alternatives"][0]["cells"][1], ["ي", "0"])
        self.assert_blocked("muqin", context="ordinary")

    def test_transferred_vowels_not_original(self):
        for key in ("qala", "jawalan", "awira", "yaqumu", "waada"):
            with self.subTest(key=key):
                self.assert_blocked(key, origin="transferred")

    def test_nonfinal_next_sukun_blocks(self):
        self.assert_blocked("qala", cells=[["ق","a"],["و","a"],["ل","0"]])

    def test_final_alif_and_double_ya_block(self):
        self.assert_blocked("qala", position="lam", cells=[["ر","a"],["م","a"],["ي","a"],["ا","0"]], index=2)
        self.assert_blocked("qala", position="lam", cells=[["ع","a"],["ل","a"],["و","i"],["ي","0"],["ي","u"]], index=2)

    def test_final_general_sukun_permitted_conditionally(self):
        result = self.run_example("qala", position="lam", cells=[["خ","0"],["ش","a"],["ي","a"],["و","0"]], index=2)
        self.assertEqual(result["alternatives"][0]["action"], "to_alif")
        self.assertEqual(result["alternatives"][0]["cells"][-1], ["و","0"])
        # This is an intermediate result, not the final khashaw orthography.
        self.assertEqual(result["output_layer"], "morphophonemic_cells_not_final_orthography")

    def test_afal_block_cannot_use_generic_alif(self):
        self.assert_blocked("qala", context="afal_quality")
        self.assert_blocked("awira", context="ordinary")

    def test_reciprocal_ya_not_preserved(self):
        self.assertEqual(self.run_example("ibtayu")["alternatives"][0]["action"], "to_alif")
        self.assertEqual(self.run_example("ishtawaru")["alternatives"][0]["action"], "keep")
        self.assert_blocked("ishtawaru", context="ordinary")

    def test_double_changes_only_one_glide(self):
        result = self.run_example("hawa")
        output = result["alternatives"][0]["cells"]
        self.assertEqual(output[1], ["و", "a"])
        self.assertEqual(sum(c[0] == "ا" for c in output), 1)
        self.assert_blocked("qala", cells=[["ه","a"],["و","a"],["ي","a"]])

    def test_named_reverse_requires_mechanical_root_binding(self):
        self.assert_blocked("ghaya", cells=[["ه","a"],["و","a"],["ي","a"],["ت","u"]])
        self.assert_blocked("ghaya", lexeme="غيره")
        self.assert_blocked("ghaya", cells=[["غ","a"],["ي","a"],["ي","a"],["ن","u"]])

    def test_double_lam_following_alif_block(self):
        self.assert_blocked("hawa", cells=[["ه","a"],["و","a"],["ي","a"],["ا","0"]])

    def test_nominal_augment_must_be_visible(self):
        self.assert_blocked("jawalan", cells=[["ج","a"],["و","a"],["ل","a"]])
        self.assert_blocked("jawalan", context="verb")
        self.assert_blocked("jawalan", lexeme="ماهان")
        self.assert_blocked("jawalan", lexeme="داران")

    def test_transfer_blockers(self):
        for context in ("exclamation", "geminate", "weak_final", "ordinary"):
            with self.subTest(context=context):
                self.assert_blocked("yaqumu", context=context)
        self.assert_blocked("yaqumu", cells=[["ي","a"],["ا","0"],["و","u"],["م","u"]])
        self.assert_blocked("yaqumu", cells=[["ي","a"],["ق","a"],["و","u"],["م","u"]])
        self.assert_blocked("yaqumu", cells=[["ي","a"],["ق","0"],["و","u"],["ي","a"]])
        self.assert_blocked("yaqumu", cells=[["ي","a"],["ق","0"],["و","u"],["م","0"],["م","u"]])

    def test_reciprocal_requires_visible_iftial_shape(self):
        self.assert_blocked("ishtawaru", cells=[["ق","a"],["و","a"],["ل","a"]], index=1)

    def test_transformation_preserves_outer_cells(self):
        f = deepcopy(self.examples["mizan"]["frame"])
        f["cells"] = [["ب","i"]] + f["cells"] + [["ه","i"]]
        f["index"] += 1
        r = w.evaluate(w.RULE_IDS[2], f)
        self.assertEqual(r["alternatives"][0]["cells"][0], ["ب","i"])
        self.assertEqual(r["alternatives"][0]["cells"][-1], ["ه","i"])

    def test_returned_source_and_input_are_not_aliased(self):
        e = self.examples["qala"]
        result = w.evaluate(e["rule_id"], e["frame"])
        e["frame"]["cells"][0][0] = "ك"
        self.assertEqual(result["input"]["cells"][0][0], "ق")
        result["source_spans"][0]["raw_text"] = "altered"
        self.assertNotEqual(w.replay_sources()[e["rule_id"]][0]["raw_text"], "altered")

    def test_bool_index_rejected(self):
        with self.assertRaises(NabtError) as error:
            self.run_example("qala", index=True)
        self.assertEqual(error.exception.code, "INVALID_WEAK_FRAME")

    def test_malformed_and_noncanonical_cells(self):
        for cells in ([["ق","a"],["و","a"],["ل",False]], [["أ","a"]], [["و", "fatha"]]):
            with self.subTest(cells=cells), self.assertRaises(NabtError):
                self.run_example("qala", cells=cells, index=0)

    def test_resource_exhaustion_is_not_rejection(self):
        with self.assertRaises(NabtError) as error:
            self.run_example("qala", cells=[["ق","a"]]*257)
        self.assertEqual(error.exception.code, "RESOURCE_LIMIT")
        self.assertEqual(error.exception.status, "DEFER")

    def test_extra_authority_fields_are_rejected(self):
        f = deepcopy(self.examples["qala"]["frame"])
        f["application_established"] = True
        with self.assertRaises(NabtError):
            w.evaluate(w.RULE_IDS[4], f)

    def test_unknown_rule_not_language_rejection(self):
        with self.assertRaises(NabtError) as error:
            w.evaluate("WEAK-NEW", self.examples["qala"]["frame"])
        self.assertEqual(error.exception.status, "DEFER")

    def test_finite_controls_are_exact_cartesian_domain(self):
        export = w.finite_export_rows()
        actual = {tuple(row["frame"]) for row in export["rows"]}
        expected = {(tag, *values) for tag, domain in enumerate(w.CONTROL_DOMAINS) for values in product(*domain)}
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), len(export["rows"]))
        self.assertEqual(len(actual), 7424)

    def test_boolean_control_must_be_boolean(self):
        for frame in ([0,"waw","0","i",1], [True,"wata","0","a",True], [4,"waw","a","a",True,"wrong","end",True]):
            with self.subTest(frame=frame), self.assertRaises(NabtError):
                w.control_actions(frame)

    def test_source_tamper_defers(self):
        from importlib.resources import files
        original = files("nabt").joinpath("data/source_evidence")
        inventory = original.joinpath("classical_rule_inventory_v1.json").read_bytes()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / "data/source_evidence"
            target.mkdir(parents=True)
            (target / "classical_rule_inventory_v1.json").write_bytes(inventory[:-1] + b" ")
            with patch.object(w, "files", return_value=root), self.assertRaises(NabtError) as error:
                self.run_example("qala")
            self.assertEqual(error.exception.status, "DEFER")
            self.assertEqual(error.exception.code, "INSTALLED_CONTRACT_FAILED")

    def test_same_length_original_source_tamper_defers(self):
        from importlib.resources import files
        original = files("nabt").joinpath("data/source_evidence")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / "data/source_evidence"
            target.mkdir(parents=True)
            for name in ("classical_rule_inventory_v1.json", "sibawayhi.txt", "ibn_aqil.txt"):
                data = original.joinpath(name).read_bytes()
                if name == "sibawayhi.txt":
                    data = b" " + data[1:]
                (target / name).write_bytes(data)
            with patch.object(w, "files", return_value=root), self.assertRaises(NabtError) as error:
                self.run_example("qala")
            self.assertEqual(error.exception.status, "DEFER")


if __name__ == "__main__":
    unittest.main()
