"""Authored counterexamples for the conditional Lean-generated law only.

No lexical reader, independent gold corpus, or implicit source authority is
used here. These cases distinguish a sign from an ending and a contextual
requirement from its externally licensed linguistic premises.
"""

from importlib.resources import files
import json
import unittest


TABLE = json.loads(files("nabt").joinpath("data/inflection_evidence_table.json").read_bytes())


def row(cls, case):
    return next(r for r in TABLE["rows"] if r["class"] == cls and r["case"] == case)


def named(cls, case):
    result = row(cls, case)
    return {key: TABLE[key + "s"][result[key]] for key in ("sign", "mode", "origin")}


def context(al, idhafa):
    return TABLE["diptote_rows"][al + 4 * idhafa]


class InflectionLawBoundaries(unittest.TestCase):
    def test_old_class_case_domains_are_retained_without_invalid_cross_pairs(self):
        self.assertEqual(len(TABLE["rows"]), 45)
        self.assertEqual(len({(r["class"], r["case"]) for r in TABLE["rows"]}), 45)
        for r in TABLE["rows"]:
            self.assertNotEqual(r["case"], 3 if r["class"] < 8 else 2)
            self.assertTrue(all(type(r[k]) is int for k in ("class", "case", "sign", "mode", "origin", "surface")))

    def test_common_letter_account_is_declared_as_a_convention(self):
        self.assertEqual(TABLE["convention"], "common_letter_substitution")
        self.assertEqual(named(1, 1), {"sign": "waw", "mode": "overt", "origin": "substitute"})
        self.assertEqual(named(1, 0)["sign"], "alif")
        self.assertEqual(named(1, 2)["sign"], "ya")

    def test_kasra_origin_depends_on_case_not_its_glyph(self):
        self.assertEqual(named(4, 0), {"sign": "kasra", "mode": "overt", "origin": "substitute"})
        self.assertEqual(named(4, 2), {"sign": "kasra", "mode": "overt", "origin": "original"})
        self.assertEqual(row(4, 0)["surface"], row(4, 2)["surface"])

    def test_fatha_origin_depends_on_case_not_its_glyph(self):
        self.assertEqual(named(5, 0)["origin"], "original")
        self.assertEqual(named(5, 2)["origin"], "substitute")
        self.assertEqual(row(5, 0)["surface"], row(5, 2)["surface"])

    def test_maqsur_alif_is_not_a_visible_case_mark(self):
        values = [row(6, c) for c in (0, 1, 2)]
        self.assertEqual({r["surface"] for r in values}, {5})
        self.assertEqual({r["mode"] for r in values}, {1})
        self.assertEqual({r["origin"] for r in values}, {0})
        self.assertEqual({r["sign"] for r in values}, {0, 1, 2})

    def test_manqus_only_accusative_fatha_is_overt_in_this_profile(self):
        self.assertEqual(named(7, 0), {"sign": "fatha", "mode": "overt", "origin": "original"})
        self.assertEqual(named(7, 1)["mode"], "estimated")
        self.assertEqual(named(7, 2)["mode"], "estimated")
        self.assertEqual(row(7, 1)["surface"], row(7, 2)["surface"])

    def test_weak_jussive_sign_is_deletion_not_remaining_vowel(self):
        for cls, remainder in ((12, 1), (13, 0), (14, 2)):
            with self.subTest(cls=cls):
                self.assertEqual(named(cls, 3), {"sign": "weak_deleted", "mode": "deletion", "origin": "substitute"})
                self.assertEqual(row(cls, 3)["surface"], remainder)

    def test_weak_alif_keeps_estimated_nominative_and_accusative(self):
        self.assertEqual(named(12, 1)["mode"], "estimated")
        self.assertEqual(named(12, 0)["mode"], "estimated")
        self.assertEqual(row(12, 1)["surface"], row(12, 0)["surface"])
        self.assertNotEqual(row(12, 1)["sign"], row(12, 0)["sign"])

    def test_five_verb_deletion_does_not_choose_accusative_or_jussive(self):
        for cls in (9, 10, 11):
            with self.subTest(cls=cls):
                self.assertEqual(named(cls, 1)["sign"], "nun_retained")
                self.assertEqual(named(cls, 0), named(cls, 3))
                self.assertEqual(named(cls, 3)["sign"], "nun_deleted")
                self.assertEqual(row(cls, 0)["surface"], row(cls, 3)["surface"])

    def test_nominal_nun_is_not_the_five_verb_case_sign(self):
        for cls, nominative in ((2, "alif"), (3, "waw")):
            self.assertEqual(named(cls, 1)["sign"], nominative)
            self.assertEqual(named(cls, 0)["sign"], "ya")
            self.assertEqual(named(cls, 2)["sign"], "ya")
        self.assertTrue(all(r["sign"] not in (7, 8) for r in TABLE["rows"] if r["class"] < 8))

    def test_unknown_diptote_context_is_not_bare_diptote_evidence(self):
        r = context(0, 0)
        self.assertEqual(r["status"], "pending")
        self.assertEqual([x["sign"] for x in r["realizations"]], [1, 2])
        self.assertEqual([x["origin"] for x in r["realizations"]], [1, 0])

    def test_diptote_fatha_requires_two_explicit_negatives(self):
        only_fatha = [r["code"] for r in TABLE["diptote_rows"] if r["status"] == "fatha"]
        self.assertEqual(only_fatha, [10])
        self.assertEqual(context(2, 2)["realizations"], [{"sign": 1, "mode": 0, "origin": 1, "surface": 1}])

    def test_witnessed_diptote_override_and_conflict_are_different(self):
        for al, idhafa in ((1, 0), (0, 1), (1, 2), (2, 1), (1, 1)):
            self.assertEqual(context(al, idhafa)["status"], "kasra")
        for al in range(4):
            for idhafa in range(4):
                if 3 in (al, idhafa):
                    self.assertEqual(context(al, idhafa)["status"], "conflict")
                    self.assertEqual(context(al, idhafa)["realizations"], [])

    def test_nun_kind_inventory_has_no_case_or_role_result(self):
        self.assertEqual([r["label"] for r in TABLE["nun_rows"]], [
            "radical", "nominal_dual_plural", "five_verb_raf", "feminine_subject",
            "emphatic_direct", "emphatic_separated", "protective"])
        self.assertTrue(all(set(r) == {"code", "label"} for r in TABLE["nun_rows"]))

    def test_same_case_does_not_identify_a_unique_role(self):
        nominatives = [r["label"] for r in TABLE["relation_rows"] if r["case"] == 1]
        self.assertEqual(nominatives, ["active_subject", "passive_subject", "inna_predicate", "kana_subject"])
        self.assertTrue(all("sign" not in r for r in TABLE["relation_rows"]))

    def test_relation_kind_is_independent_of_its_case(self):
        accusatives = [r for r in TABLE["relation_rows"] if r["case"] == 0]
        self.assertEqual({r["kind"] for r in accusatives}, {0, 1})
        self.assertEqual(TABLE["relation_rows"][9], {"code": 9, "label": "imperfect_subjunctive", "kind": 1, "case": 0})

    def test_each_receipt_prerequisite_is_required(self):
        full = 255 ^ (1 << 3)
        self.assertTrue(TABLE["receipt_rows"][full]["activated"])
        for i, name in enumerate(TABLE["receipt_bits"]):
            invalid = full | (1 << i) if name == "blocked" else full & ~(1 << i)
            with self.subTest(prerequisite=name):
                self.assertFalse(TABLE["receipt_rows"][invalid]["activated"])
        self.assertFalse(TABLE["receipt_rows"][0]["activated"])

    def test_unknown_construction_prevents_relation_activation(self):
        position = TABLE["receipt_bits"].index("construction_known")
        self.assertTrue(all(not r["activated"] for r in TABLE["receipt_rows"] if not r["mask"] & (1 << position)))

    def test_built_local_case_is_not_an_inflection_case(self):
        self.assertEqual(TABLE["case_domains"], ["inflected_case", "local_case"])
        self.assertEqual(TABLE["construction_rows"], [{"construction": 0, "domain": 1}, {"construction": 1, "domain": 0}])


if __name__ == "__main__":
    unittest.main()
