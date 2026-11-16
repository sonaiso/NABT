"""Public IB references remain distinct from local outcomes and assessment authority.

These tests inspect static JSON only. They neither import an NTL runtime nor
assert that a student, school, or generated answer satisfies an IB requirement.
"""

import json
from pathlib import Path
import unittest


CATALOG_PATH = (Path(__file__).resolve().parents[1] / "tools" / "lexical_training"
                / "data" / "ntl_ib_framework_v1.json")


def identified_records(value):
    if isinstance(value, dict):
        if "id" in value:
            yield value
        for item in value.values():
            yield from identified_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from identified_records(item)


class SchoolIBCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.sources = {row["id"]: row for row in cls.catalog["sources"]}
        cls.profiles = {row["id"]: row for row in cls.catalog["profiles"]}
        cls.outcomes = {row["id"]: row for row in cls.catalog["outcomes"]}

    def test_scope_is_explicitly_partial_and_not_an_official_curriculum(self):
        self.assertEqual(self.catalog["schema"], "ntl.framework-catalog.v1")
        self.assertEqual(self.catalog["catalog_id"], "ib.public-frameworks")
        self.assertEqual(self.catalog["version"], "2026-11-16")
        coverage = self.catalog["coverage"]
        self.assertTrue(coverage["partial"])
        for key in ("complete_curriculum", "official_ib_catalog", "full_subject_guides_included",
                    "full_rubrics_included", "official_grade_awarding", "automated_mastery_certification"):
            self.assertIs(coverage[key], False, key)
        self.assertEqual(coverage["primary_target_programmes"], ["PYP", "MYP", "CP"])
        self.assertEqual(coverage["supplemental_programmes"], ["DP"])
        self.assertTrue(coverage["unavailable_in_this_catalog"])

    def test_declared_identity_namespace_is_unique(self):
        records = list(identified_records(self.catalog))
        identifiers = [row["id"] for row in records]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(identifier.startswith("ib.") for identifier in identifiers))
        self.assertIn("not official IB outcome codes", self.catalog["coverage"]["identifier_namespace_note"])

    def test_sources_have_official_provenance_and_versioned_locators(self):
        for source in self.sources.values():
            with self.subTest(source=source["id"]):
                self.assertEqual(source["publisher"], "International Baccalaureate Organization")
                self.assertEqual(source["authority_status"], "OFFICIAL_PUBLIC_SOURCE")
                self.assertTrue(source["url"].startswith(("https://www.ibo.org/", "https://ibo.org/")))
                self.assertTrue(source["title"])
                self.assertTrue(source["edition"])
                self.assertEqual(source["retrieved_on"], "2026-11-16")
                locator = source["locator"]
                self.assertTrue(locator["section"])
                self.assertEqual(locator["verification"], "OFFICIAL_WEB_TEXT_CHECKED")
                for key in ("printed_pages", "pdf_pages_1_based"):
                    pages = locator[key]
                    self.assertTrue(pages is None or all(type(p) is int and p > 0 for p in pages))

    def test_local_outcomes_keep_provenance_without_inventing_official_identifiers(self):
        for outcome in self.outcomes.values():
            with self.subTest(outcome=outcome["id"]):
                self.assertEqual(outcome["authority_status"], "LOCAL_PARAPHRASE_OF_OFFICIAL_PUBLIC_SOURCE")
                self.assertEqual(outcome["identifier_authority"], "NABT_LOCAL_IDENTIFIER")
                self.assertIs(outcome["official_ib_identifier"], False)
                self.assertTrue(outcome["source_ids"])
                self.assertLessEqual(set(outcome["source_ids"]), self.sources.keys())
                self.assertTrue(outcome["source_locator"]["section"])
                self.assertTrue(outcome["statement_ar"])
                self.assertTrue(outcome["statement_en"])
                self.assertTrue(outcome["evidence_kinds"])
                self.assertTrue(outcome["assessment_methods"])
                self.assertIs(outcome["requires_school_binding"], True)
                self.assertIs(outcome["automatic_official_grades"], False)
                self.assertIsNone(outcome["official_grade_scale"])
                self.assertNotIn("rubric_descriptors", outcome)
                self.assertNotIn("markbands", outcome)

    def test_profiles_and_outcomes_have_consistent_links(self):
        self.assertLessEqual({"ib.pyp.2026", "ib.myp.2026", "ib.cp.2026", "ib.cp.2027"}, self.profiles.keys())
        for profile in self.profiles.values():
            with self.subTest(profile=profile["id"]):
                self.assertTrue(profile["source_ids"])
                self.assertLessEqual(set(profile["source_ids"]), self.sources.keys())
                self.assertTrue(profile["outcome_ids"])
                self.assertLessEqual(set(profile["outcome_ids"]), self.outcomes.keys())
                self.assertTrue(profile["required_binding_fields"])
                self.assertIs(profile["automatic_official_grades"], False)
                self.assertIs(profile["full_criteria_available"], False)
                for identifier in profile["outcome_ids"]:
                    outcome = self.outcomes[identifier]
                    self.assertIn(profile["programme"], outcome["programmes"])
                    self.assertIn(profile["id"], outcome["profile_ids"])
        for outcome in self.outcomes.values():
            self.assertLessEqual(set(outcome["profile_ids"]), self.profiles.keys())
            for identifier in outcome["profile_ids"]:
                self.assertIn(outcome["id"], self.profiles[identifier]["outcome_ids"])

    def test_cp_cohorts_do_not_silently_share_changed_component_contracts(self):
        legacy, revised = self.profiles["ib.cp.2026"], self.profiles["ib.cp.2027"]
        self.assertEqual(legacy["assessment_sessions"], ["2026-05", "2026-11"])
        self.assertEqual(revised["first_teaching"], "2025-08")
        self.assertEqual(revised["first_assessment"], "2027-05")
        self.assertNotEqual(legacy["version"], revised["version"])
        self.assertIn("service_learning", legacy["core_components"])
        self.assertIn("language_development", legacy["core_components"])
        self.assertNotIn("community_engagement", legacy["core_components"])
        self.assertIn("community_engagement", revised["core_components"])
        self.assertIn("language_and_cultural_studies", revised["core_components"])
        self.assertNotIn("service_learning", revised["core_components"])
        self.assertEqual(legacy["reflective_project_assessment"], "TEACHER_MARKED_IB_MODERATED")
        self.assertEqual(revised["reflective_project_assessment"], "EXTERNALLY_ASSESSED_BY_IB")
        self.assertFalse(set(legacy["outcome_ids"]) & set(revised["outcome_ids"]))
        self.assertIn("ib.source.cp.regulations.2026", legacy["source_ids"])
        self.assertIn("ib.source.cp.core.brief.2027", revised["source_ids"])
        self.assertIs(legacy["dp_core_registration_allowed"], False)

    def test_myp_needs_subject_year_and_criteria_without_fabricated_full_rubrics(self):
        profile = self.profiles["ib.myp.2026"]
        self.assertLessEqual({"programme_year", "subject_group", "subject_guide_version", "criterion_reference"},
                             set(profile["required_binding_fields"]))
        self.assertIs(profile["criterion_binding_required"], True)
        self.assertIs(profile["criterion_descriptors_included"], False)
        self.assertEqual(set(profile["public_sciences_criterion_categories"]), {"A", "B", "C", "D"})
        for outcome in self.outcomes.values():
            if "public_alignment_hint" in outcome:
                self.assertEqual(outcome["programmes"], ["MYP"])
                self.assertEqual(outcome["subject_group"], "sciences")
                self.assertEqual(outcome["alignment_status"], "PROPOSED_LOCAL_ALIGNMENT_NOT_CRITERION_SCORE")
                self.assertIsNone(outcome["programme_year"])

    def test_tok_is_dp_specific_and_other_programmes_only_have_optional_adaptations(self):
        framework = self.catalog["epistemic_framework"]
        self.assertEqual(framework["official_applicability"], {"programmes": ["DP"], "component": "TOK"})
        self.assertEqual(framework["local_adaptation_programmes"], ["PYP", "MYP", "CP"])
        self.assertIs(framework["required_for_other_programmes"], False)
        self.assertEqual(framework["adaptation_authority_status"], "LOCAL_PEDAGOGICAL_ADAPTATION_ONLY")
        for profile in self.profiles.values():
            if profile["programme"] in ("PYP", "MYP", "CP"):
                self.assertIs(profile["tok_required"], False)
            else:
                self.assertEqual(profile["id"], "ib.dp.tok.2022")
                self.assertIs(profile["supplemental"], True)
        for outcome in self.outcomes.values():
            if outcome.get("component") == "TOK":
                self.assertEqual(outcome["programmes"], ["DP"])
                self.assertEqual(outcome["profile_ids"], ["ib.dp.tok.2022"])

    def test_tok_categories_match_the_public_guide_without_becoming_a_scoring_rule(self):
        framework = self.catalog["epistemic_framework"]
        self.assertEqual({row["key"] for row in framework["axes"]},
                         {"scope", "perspectives", "methods_and_tools", "ethics"})
        self.assertEqual({row["key"] for row in framework["areas_of_knowledge"]},
                         {"history", "human_sciences", "natural_sciences", "arts", "mathematics"})
        self.assertEqual({row["key"] for row in framework["concepts"]},
                         {"evidence", "certainty", "truth", "interpretation", "power", "justification",
                          "explanation", "objectivity", "perspective", "culture", "values", "responsibility"})
        self.assertEqual(len(framework["axes"]), 4)
        self.assertEqual(len(framework["areas_of_knowledge"]), 5)
        self.assertEqual(len(framework["concepts"]), 12)
        self.assertIn("ib.source.tok.guide.2022", framework["source_ids"])
        self.assertTrue(framework["assessment_boundary"])

    def test_bok_is_only_a_declared_local_content_model(self):
        bok = self.catalog["body_of_knowledge"]
        self.assertEqual(bok["authority_status"], "LOCAL_DESIGN_ONLY")
        self.assertIs(bok["official_ib_component"], False)
        self.assertIs(bok["official_ib_term_claimed"], False)
        self.assertIs(bok["mandatory"], False)
        self.assertTrue(bok["meaning"])
        for profile in self.profiles.values():
            self.assertNotIn("BOK", profile.get("core_components", []))
            self.assertNotIn(bok["id"], profile["outcome_ids"])

    def test_catalog_metadata_never_certifies_students_or_a_school(self):
        limits = self.catalog["assessment_boundaries"]
        for field in ("automatic_official_grades", "official_curriculum_coverage_certified",
                      "official_school_authorization_established", "local_feedback_is_official_assessment",
                      "model_generated_response_is_learner_evidence", "synthetic_response_proves_human_learning"):
            self.assertIs(limits[field], False, field)
        self.assertIs(limits["official_completion_requires_authorized_review"], True)
        self.assertTrue(limits["national_curriculum_alignment"])


if __name__ == "__main__":
    unittest.main()
