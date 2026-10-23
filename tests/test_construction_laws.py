"""Counterexample boundaries for the conditional law, not parser accuracy."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from nabt import construction_laws as laws
from nabt.errors import NabtError


class ConstructionLawsTests(unittest.TestCase):
    def test_case_requirement_never_supplies_missing_attachment(self):
        self.assertEqual(laws.role_case("zanna_object1"), 0)
        self.assertEqual(laws.role_case("zanna_object2"), 0)
        self.assertFalse(laws.construction_allowed("zanna"))
        complete = dict.fromkeys(laws.ACTIVATION_BITS, True)
        self.assertTrue(laws.construction_allowed("zanna", **complete))
        for missing in ("source_supported", "attachment_licensed", "frame_complete", "sense_licensed"):
            with self.subTest(missing=missing):
                self.assertFalse(laws.construction_allowed("zanna", **{**complete, missing: False}))

    def test_inheritance_does_not_guess_unknown_head_case(self):
        for role in ("naat", "badal", "tawkeed"):
            self.assertIsNone(laws.role_case(role))
            self.assertEqual(laws.role_case(role, 2), 2)
        for invalid in (True, False, 3, -1, "1", 1.0):
            with self.subTest(invalid=invalid), self.assertRaises(NabtError):
                laws.role_case("naat", invalid)

    def test_kada_predicate_requirement_names_clause_not_internal_verb(self):
        rows = [r for r in laws.installed_registry()["role_rows"] if r["label"] == "kada_predicate"]
        self.assertTrue(all(row["target"] == "clause_local_case" and row["case"] == 0 for row in rows))
        self.assertEqual(laws.operator_slots("kada"),
                         [{"role": "kada_subject", "case": 1}, {"role": "kada_predicate", "case": 0}])
        with self.assertRaises(NabtError):
            laws.role_case("kada_internal_verb")

    def test_real_adjective_unknown_axis_is_not_confirmed(self):
        confirmed = dict.fromkeys(laws.AGREEMENT_AXES, "confirmed")
        for missing in laws.AGREEMENT_AXES:
            with self.subTest(missing=missing):
                self.assertEqual(laws.agreement_status(**{**confirmed, missing: "possible"}), "possible")
        self.assertEqual(laws.agreement_status(case="conflict", gender="possible"), "conflict")
        self.assertEqual(laws.agreement_status(**confirmed), "confirmed")

    def test_hal_tamyiz_case_does_not_identify_construction(self):
        self.assertEqual(laws.role_case("hal"), laws.role_case("tamyiz"))
        self.assertIn("hal", laws.installed_registry()["roles"])
        self.assertIn("tamyiz", laws.installed_registry()["roles"])
        # Counted nouns keep their independent cardinal-number case contract.
        from nabt.nominal import number_rule
        self.assertEqual(number_rule(3, "masculine")["counted_case"], "genitive")
        self.assertEqual(laws.role_case("tamyiz"), 0)

    def test_idafa_unknown_does_not_mean_tanwin_or_nun_absent(self):
        self.assertEqual(laws.idafa_head_status("semantic"), "possible")
        self.assertEqual(laws.idafa_head_status("semantic", "unknown", "denied", "denied"), "possible")
        self.assertEqual(laws.idafa_head_status("semantic", "denied", "unknown", "denied"), "possible")
        self.assertEqual(laws.idafa_head_status("semantic", "denied", "denied", "denied"), "confirmed")
        self.assertEqual(laws.idafa_head_status("semantic", "denied", "conflict", "denied"), "conflict")

    def test_verbal_article_exception_cannot_override_semantic_idafa(self):
        self.assertEqual(laws.idafa_head_status("verbal", "denied", "denied", "affirmed"), "conflict")
        self.assertEqual(laws.idafa_head_status("verbal", "denied", "denied", "affirmed", article_exception=True), "confirmed")
        self.assertEqual(laws.idafa_head_status("semantic", "denied", "denied", "affirmed", article_exception=True), "conflict")
        self.assertEqual(laws.idafa_head_status("verbal", "affirmed", "denied", "affirmed", article_exception=True), "conflict")

    def test_rare_an_pattern_is_not_rejected_by_preference(self):
        for label in ("كاد", "كرب"):
            self.assertFalse(laws.complement_an_preferred_present(label))
            self.assertTrue(laws.complement_an_allowed(label, True))
        for label in ("عسى", "أوشك"):
            self.assertTrue(laws.complement_an_preferred_present(label))
            self.assertTrue(laws.complement_an_allowed(label, False))
        self.assertFalse(laws.complement_an_allowed("inception", True))
        for label in ("حرى", "اخلولق"):
            self.assertFalse(laws.complement_an_allowed(label, False))
        with self.assertRaises(NabtError):
            laws.complement_an_policy("جعل")  # The surface alone is not the inception-sense license.

    def test_case_and_relation_do_not_create_coreference(self):
        self.assertEqual(laws.role_case("badal", 1), 1)
        self.assertFalse(laws.identity_preservation_allowed("badal_total", relation_licensed=True))
        self.assertTrue(laws.identity_preservation_allowed("badal_total", relation_licensed=True, identity_licensed=True))
        self.assertFalse(laws.identity_preservation_allowed("tawkeed", identity_licensed=True))
        for label in ("badal_part", "badal_association"):
            self.assertFalse(laws.identity_preservation_allowed(label, relation_licensed=True, identity_licensed=True))

    def test_scoped_claim_requires_outer_metadata_and_never_projects_bare(self):
        for scope in laws.SCOPES:
            with self.subTest(scope=scope):
                self.assertFalse(laws.bare_projection_allowed(scope))
                self.assertFalse(laws.scoped_projection_allowed(scope, source_supported=True, frame_complete=True))
                self.assertTrue(laws.scoped_projection_allowed(scope, metadata_preserved=True,
                                                              source_supported=True, frame_complete=True))
        with self.assertRaises(NabtError):
            laws.bare_projection_allowed("unclassified")

    def test_boolean_flags_require_actual_booleans(self):
        for invalid in (0, 1, "true", None):
            with self.subTest(invalid=invalid):
                for call in (lambda: laws.construction_allowed("kana", unblocked=invalid),
                             lambda: laws.complement_an_allowed("كاد", invalid),
                             lambda: laws.identity_preservation_allowed("tawkeed", identity_licensed=invalid),
                             lambda: laws.scoped_projection_allowed("belief", frame_complete=invalid),
                             lambda: laws.idafa_head_status("verbal", article_exception=invalid)):
                    with self.assertRaises(NabtError):
                        call()

    def test_registry_and_slot_copies_cannot_mutate_law(self):
        registry = laws.installed_registry()
        original = deepcopy(registry)
        registry["role_rows"][0]["case"] = 2
        self.assertEqual(laws.installed_registry(), original)
        slots = laws.operator_slots("kana")
        slots[0]["case"] = 2
        self.assertEqual(laws.role_case("kana_subject"), 1)
        self.assertEqual(laws.operator_slots("kana")[0]["case"], 1)

    def test_changed_installed_bytes_fail_closed(self):
        laws._table.cache_clear()
        laws._indexes.cache_clear()
        try:
            with patch.object(laws, "files") as mocked:
                mocked.return_value.joinpath.return_value.read_bytes.return_value = b'{"law_id":"nabt.construction-evidence.v1"}'
                with self.assertRaises(NabtError) as raised:
                    laws.installed_registry()
                self.assertEqual(raised.exception.code, "INSTALLED_CONTRACT_FAILED")
                self.assertEqual(raised.exception.status, "DEFER")
        finally:
            laws._table.cache_clear()
            laws._indexes.cache_clear()


if __name__ == "__main__":
    unittest.main()
