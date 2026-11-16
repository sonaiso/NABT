"""Provenance and authority boundaries for the partial Jordan source catalogue.

These offline checks protect the reviewed dataset, not live web authenticity,
school adoption, teaching effectiveness or the gateway's admission contract.
"""
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit


CATALOGUE = (
    Path(__file__).resolve().parents[1]
    / "tools/lexical_training/data/ntl_jordan_framework_v1.json"
)


class JordanFrameworkCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
        cls.sources = {row["id"]: row for row in cls.catalogue["sources"]}
        cls.outcomes = {row["id"]: row for row in cls.catalogue["outcomes"]}
        cls.profiles = {row["id"]: row for row in cls.catalogue["profiles"]}

    def test_provenance_resolves_to_official_hosts_and_specific_locators(self):
        self.assertEqual(self.catalogue["schema"], "ntl.framework-catalog.v1")
        self.assertEqual(self.catalogue["catalog_id"], "jordan.public-frameworks")
        self.assertEqual(len(self.sources), len(self.catalogue["sources"]))
        self.assertEqual(len(self.outcomes), len(self.catalogue["outcomes"]))
        for source in self.sources.values():
            with self.subTest(source=source["id"]):
                url = urlsplit(source["url"])
                self.assertEqual(url.scheme, "https")
                self.assertIn(url.hostname, {"www.nccd.gov.jo", "moe.gov.jo", "moehrd.gov.jo"})
                for field in ("title", "publisher", "edition", "locator", "authority_status"):
                    self.assertTrue(source[field])
        for outcome in self.outcomes.values():
            with self.subTest(outcome=outcome["id"]):
                self.assertTrue(set(outcome["source_ids"]) <= self.sources.keys())
                self.assertEqual(len(outcome["source_ids"]), 1)
                self.assertTrue(set(outcome["profile_ids"]) <= self.profiles.keys())
                pages = outcome["source_locator"]["printed_pages"]
                self.assertTrue(pages)
                self.assertTrue(all(type(page) is int and page > 0 for page in pages))
                self.assertTrue(outcome["source_locator"]["section"])
                self.assertTrue(outcome["evidence_kinds"])
                self.assertTrue(outcome["assessment_methods"])

    def test_official_adoption_is_document_specific(self):
        general = self.sources["jordan.source.general.2024"]
        science = self.sources["jordan.source.science.2024"]
        self.assertEqual(general["adoption"]["education_council_decision"], "2024/138")
        self.assertEqual(general["adoption"]["education_council_date"], "2024-08-13")
        self.assertEqual(science["adoption"]["education_council_decision"], "2024/62")
        self.assertEqual(science["adoption"]["education_council_date"], "2024-06-26")
        self.assertNotEqual(general["document_kind"], science["document_kind"])

    def test_general_competencies_are_not_grade_specific_outcomes(self):
        records = [r for r in self.outcomes.values() if r["kind"] == "framework_competency"]
        self.assertEqual(len(records), 3)
        for record in records:
            self.assertIsNone(record["grade"])
            self.assertEqual(record["statement_form"], "LOCAL_PARAPHRASE")
            self.assertEqual(record["source_ids"], ["jordan.source.general.2024"])

    def test_water_outcome_and_indicator_remain_different_records(self):
        outcome = self.outcomes["jordan.science.g8.water_human_impact"]
        indicator = self.outcomes["jordan.science.g8.water_quality_conservation"]
        self.assertEqual(outcome["kind"], "grade_learning_outcome")
        self.assertEqual(indicator["kind"], "grade_performance_indicator")
        self.assertEqual(indicator["parent_outcome_id"], outcome["id"])
        self.assertEqual(outcome["indicator_ids"], [indicator["id"]])
        self.assertEqual(outcome["statement_ar"], "يستكشف تأثير استخدام الإنسان للمياه على الأنظمة البيئية")
        self.assertEqual(indicator["statement_ar"], "يقترح طرائق للمحافظة على نوعية المياه")
        for record in (outcome, indicator):
            self.assertEqual(record["grade"], 8)
            self.assertEqual(record["grade_system"], "JO")
            self.assertEqual(record["source_locator"]["printed_pages"], [130])
            self.assertIsNone(record["source_locator"]["pdf_pages_1_based"])
            self.assertTrue(record["source_locator"]["visual_table_review_pending"])
        self.assertLessEqual(sum(len(r["statement_ar"].split()) for r in (outcome, indicator)), 25)

    def test_proposed_assessment_is_not_promoted_to_operational_policy(self):
        source = self.sources["jordan.source.assessment.2024"]
        record = self.outcomes["jordan.assessment.proposed.standards_first"]
        proposed = next(s for s in source["sections"] if s["id"] == "part_ii")
        self.assertEqual(proposed["first_printed_page"], 49)
        self.assertEqual(proposed["status"], "PROPOSED_NOT_ESTABLISHED_AS_ENACTED_POLICY")
        self.assertIsNone(source["adoption"])
        self.assertFalse(source["operational_grading_authority"])
        self.assertEqual(record["authority_status"], "OFFICIAL_PROPOSED_ASSESSMENT_PARAPHRASE")
        self.assertFalse(record["enacted_policy_established"])
        self.assertFalse(record["operational_grading_authority"])
        self.assertEqual(record["source_locator"]["printed_pages"], [49, 60])

    def test_unread_current_rules_cannot_supply_an_outcome_or_numeric_rule(self):
        source_id = "jordan.source.progression_rules.2026_2027.listing"
        source = self.sources[source_id]
        self.assertEqual(source["authority_status"], "OFFICIAL_LISTING_CONTENT_UNREAD")
        self.assertFalse(source["content_available"])
        self.assertFalse(source["operational_grading_authority"])
        self.assertFalse(any(source_id in r["source_ids"] for r in self.outcomes.values()))
        self.assertFalse(self.catalogue["coverage"]["current_numeric_grading_rules_installed"])
        forbidden = {"grading_weights", "pass_threshold", "equivalency_rule", "promotion_rule"}

        def keys(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield key
                    yield from keys(child)
            elif isinstance(value, list):
                for child in value:
                    yield from keys(child)

        self.assertFalse(forbidden.intersection(keys(self.catalogue)))

    def test_local_ids_and_national_scope_do_not_create_ib_alignment(self):
        for record in self.outcomes.values():
            self.assertTrue(record["id"].startswith("jordan."))
            self.assertIsNone(record["official_code"])
            self.assertEqual(record["id_origin"], "LOCAL_CATALOGUE_IDENTIFIER")
            self.assertEqual(record["programmes"], [])
            self.assertIsNone(record["programme_year"])
            self.assertTrue(record["requires_school_binding"])
            self.assertEqual(record["pedagogical_mapping_status"], "LOCAL_CANDIDATE_REQUIRES_TEACHER_REVIEW")
        self.assertEqual(self.catalogue["local_mapping_policy"]["ib_mappings"], [])
        self.assertFalse(self.catalogue["coverage"]["national_to_ib_alignment_established"])

    def test_unknown_coverage_remains_unknown_instead_of_a_full_curriculum_claim(self):
        coverage = self.catalogue["coverage"]
        self.assertTrue(coverage["partial"])
        self.assertFalse(coverage["whole_school_coverage"])
        self.assertFalse(coverage["all_jordan_learning_outcomes"])
        self.assertIsNone(coverage["official_grade_outcome_denominator"])
        self.assertIsNone(coverage["coverage_ratio"])
        self.assertEqual(coverage["unknown_target_status"], "UNSUPPORTED_CURRICULUM_TARGET")
        grade_records = [r for r in self.outcomes.values() if r["kind"] == "grade_learning_outcome"]
        self.assertEqual([(r["grade"], r["subject"]) for r in grade_records], [(8, "science")])
        for unknown in ("jordan.science.g7.water_human_impact", "jordan.mathematics.g8.all", "jordan.all"):
            self.assertNotIn(unknown, self.outcomes)
        self.assertEqual(coverage["grade_learning_outcome_records"], len(grade_records))

    def test_unretrieved_binary_is_not_given_a_fabricated_hash_or_pdf_page(self):
        for source in self.sources.values():
            self.assertIsNone(source["binary_sha256"])
            self.assertIsNone(source["locator"]["pdf_pages_1_based"])
        for source_id in ("jordan.source.general.2024", "jordan.source.science.2024", "jordan.source.assessment.2024"):
            self.assertEqual(self.sources[source_id]["binary_verification"], "NOT_RETRIEVED_HTTP_503")
            self.assertEqual(self.sources[source_id]["visual_page_verification"], "NOT_COMPLETED_IN_THIS_REVIEW")


if __name__ == "__main__":
    unittest.main()
