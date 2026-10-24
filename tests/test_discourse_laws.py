"""Authored boundary checks of the conditional law; no independent gold."""

import unittest

from nabt import discourse_laws as law
from nabt.errors import NabtError


class DiscourseLawBoundaries(unittest.TestCase):
    def test_unknown_feature_keeps_a_competitor_without_confirming_it(self):
        self.assertEqual(law.feature_compatibility(1, None), "possible")
        self.assertEqual(law.feature_compatibility(None, None), "possible")
        self.assertEqual(law.combine_compatibility(["confirmed", "possible"]), "possible")
        self.assertEqual(law.selection_status(2, closed_scope=True, all_confirmed=False), "AMBIGUOUS")

    def test_unspecified_pronoun_axis_can_be_omitted_not_fabricated(self):
        self.assertEqual(law.combine_compatibility([]), "confirmed")
        self.assertEqual(law.combine_compatibility([law.feature_compatibility(None, 1)]), "possible")

    def test_known_disagreement_is_not_merely_unknown(self):
        self.assertEqual(law.feature_compatibility(0, 1), "conflict")
        self.assertEqual(law.combine_compatibility(["possible", "conflict"]), "conflict")

    def test_unique_compatible_antecedent_in_open_scope_is_not_resolved(self):
        self.assertEqual(law.selection_status(1, closed_scope=False, all_confirmed=True), "OPEN_SCOPE")
        self.assertEqual(law.selection_status(1, closed_scope=True, all_confirmed=False), "UNRESOLVED_FEATURES")
        self.assertEqual(law.selection_status(1, closed_scope=True, all_confirmed=True), "RESOLVED")

    def test_no_nearest_candidate_tiebreak(self):
        self.assertEqual(law.selection_status(4096, closed_scope=True, all_confirmed=True), "AMBIGUOUS")

    def test_direct_context_identity_and_antecedent_order_have_distinct_premises(self):
        common = dict(origin_licensed=True, identity_bound=True, source_supported=True,
                      scope_allowed=True, quote_allowed=True)
        self.assertTrue(law.reference_allowed("speaker", "possible", **common))
        self.assertFalse(law.reference_allowed("antecedent", "confirmed", **common))
        self.assertTrue(law.reference_allowed("antecedent", "confirmed", order_licensed=True, **common))
        self.assertFalse(law.reference_allowed("relative_return", "confirmed", **common))
        self.assertTrue(law.reference_allowed("relative_return", "confirmed", return_licensed=True, **common))

    def test_context_cannot_override_conflict_or_quotation_barrier(self):
        bits = {name: True for name in law.REFERENCE_BITS}
        self.assertFalse(law.reference_allowed("deictic", "conflict", **bits))
        bits["quote_allowed"] = False
        self.assertFalse(law.reference_allowed("deictic", "confirmed", **bits))

    def test_nominative_or_accusative_cannot_choose_role(self):
        self.assertEqual(law.role_case("nominal_subject"), law.role_case("nominal_predicate"))
        self.assertEqual(law.role_case("time_adverb"), law.role_case("place_adverb"))
        self.assertEqual(law.role_case("imperfect_indicative"), 1)
        self.assertFalse(law.assertion_allowed("ASSERT", licensed_syntax=True))

    def test_nonassertive_forces_do_not_assert_even_with_licensed_internals(self):
        bits = {name: True for name in law.ASSERTION_BITS}
        self.assertTrue(law.assertion_allowed("ASSERT", **bits))
        for force in law.FORCES[1:]:
            self.assertFalse(law.assertion_allowed(force, **bits), force)

    def test_signed_assertion_needs_every_scope_and_source_guard(self):
        full = {name: True for name in law.ASSERTION_BITS}
        for name in full:
            self.assertFalse(law.assertion_allowed("ASSERT", **{**full, name: False}), name)
        self.assertEqual(law.negate_polarity("positive"), "negative")

    def test_negated_conjunction_does_not_make_both_negative(self):
        self.assertTrue(law.coordination_projection("AND", "positive"))
        self.assertFalse(law.coordination_projection("AND", "negative"))
        for operator in ("OR", "XOR", "IMPLIES"):
            for polarity in law.POLARITIES:
                self.assertFalse(law.coordination_projection(operator, polarity))

    def test_no_projection_erases_time_place_tense_or_restriction(self):
        full = {field + "_equal": True for field in law.CLAIM_FIELDS}
        self.assertTrue(law.claim_projection_allowed(**full))
        for key in full:
            self.assertFalse(law.claim_projection_allowed(**{**full, key: False}), key)

    def test_material_implication_does_not_prove_causation(self):
        self.assertTrue(law.connective_value("IMPLIES", False, False))
        self.assertFalse(law.causal_allowed(relation_licensed=False, source_supported=True,
                                          scope_complete=True, endpoints_resolved=True))

    def test_strict_domains_reject_bool_as_feature_and_integer_as_witness(self):
        calls = [lambda: law.feature_compatibility(True, 1),
                 lambda: law.feature_compatibility(1.0, 1),
                 lambda: law.assertion_allowed("ASSERT", licensed_syntax=1),
                 lambda: law.selection_status(1, closed_scope=1, all_confirmed=True),
                 lambda: law.reference_allowed("guessed", "confirmed")]
        for call in calls:
            with self.assertRaises(NabtError):
                call()

    def test_registry_copy_cannot_modify_subsequent_decisions(self):
        table = law.installed_registry()
        table["feature_rows"].clear()
        self.assertEqual(law.feature_compatibility(1, 1), "confirmed")
        self.assertEqual(len(law.installed_registry()["feature_rows"]), 25)

    def test_primary_source_windows_replay_without_new_word_answers(self):
        policy = law.replay_discourse_policy()
        self.assertEqual(len(policy["rules"]), 24)
        self.assertIn("relative_ayy_exception", policy["rules"])
        self.assertIn("force_nonassertive", policy["rules"])
        self.assertIn("temporal_noun_examples", policy["rules"])
        self.assertIn("temporal_ams_built", policy["rules"])
        self.assertTrue(all("span_sha256" in row for row in policy["rules"].values()))


if __name__ == "__main__":
    unittest.main()
