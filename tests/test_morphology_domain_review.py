"""Post-open counterexamples for categorical and reading-domain consistency.

These are review tests, not a new independent linguistic evaluation corpus.
The frozen morphology cases and conditional Lean tables remain unchanged.
"""

from copy import deepcopy
import unittest

from nabt.morphology_reader import (decode_morphology, morphology_number,
                                    read_morphology, verify_morphology)


NOUN = "يدل على معنى مستقل غير مقترن بزمن لهيئته"
VERB = "يدل على حدث مقترن بزمن بهيئته"
PARTICLE = "يدل على معنى غير مستقل"


def description(*clauses, reading="r1", word="عَلَم"):
    return f"قراءة «{reading}» للفظ «{word}»:\n" + "\n".join(c + "." for c in clauses) + "\n"


class MorphologyDomainReview(unittest.TestCase):
    def assert_no_approval(self, reading):
        axes = reading["axes"]
        for axis in (*axes.values(), axes["diptote"]["genitive"],
                     axes["diptote"]["cause_prediction"]):
            self.assertNotEqual(axis["status"], "LICENSED")
            self.assertTrue(axis["blocked_by_source_conflict"])

    def test_categorical_contradictions_survive_every_kind_branch(self):
        pairs = (("tense", "فعله ماض", "فعله مضارع"),
                 ("nun", "تتصل به نون الإناث", "لا تتصل به نون إناث ولا نون توكيد"))
        for kind in (None, NOUN, PARTICLE, VERB):
            for name, first, last in pairs:
                with self.subTest(kind=kind, property=name):
                    clauses = ([kind] if kind else []) + [first, last]
                    report = read_morphology(description(*clauses))
                    reading = report["readings"][0]
                    self.assertEqual(report["status"], "CONFLICT")
                    found = [c for c in reading["source_conflicts"]
                             if c["code"] == "CATEGORICAL_PROPERTY_CONFLICT" and c["property"] == name]
                    self.assertEqual(len(found), 1)
                    self.assertEqual(len(found[0]["values"]), 2)
                    self.assert_no_approval(reading)

    def test_noun_and_particle_cannot_accept_positive_verbal_properties(self):
        for kind in (NOUN, PARTICLE):
            for clause in ("فعله ماض", "فعله مضارع", "فعله أمر",
                           "تتصل به نون الإناث", "تتصل به نون التوكيد مباشرة",
                           "تفصل بينه وبين نون التوكيد فاصل"):
                with self.subTest(kind=kind, clause=clause):
                    report = read_morphology(description(kind, clause))
                    reading = report["readings"][0]
                    blockers = [c for c in reading["source_conflicts"]
                                if c["code"] == "PROPERTY_DOMAIN_MISMATCH"]
                    self.assertEqual(report["status"], "CONFLICT")
                    self.assertEqual(len(blockers), 1)
                    self.assertEqual(blockers[0]["expected_kind"], "verb")
                    self.assertEqual(blockers[0]["candidate_kinds"], ["noun"] if kind == NOUN else ["particle"])
                    self.assert_no_approval(reading)

    def test_missing_kind_is_not_filled_by_tense_or_positive_nun(self):
        for clause in ("فعله ماض", "تتصل به نون الإناث"):
            with self.subTest(clause=clause):
                reading = read_morphology(description(clause))["readings"][0]
                self.assertEqual(reading["source_conflicts"], [])
                self.assertEqual(reading["axes"]["kind"]["candidates"], ["noun", "particle", "verb"])
                self.assertEqual(reading["axes"]["kind"]["status"], "DEFER")

    def test_temporal_noun_content_does_not_become_verbal_time(self):
        reading = read_morphology(description(NOUN, "يدل على حدث مقترن بزمن",
                                             "يسلم من شبه الحرف", word="يَوْم"))["readings"][0]
        self.assertEqual(reading["source_conflicts"], [])
        self.assertEqual(reading["axes"]["kind"]["candidates"], ["noun"])
        self.assertEqual(reading["axes"]["kind"]["status"], "LICENSED")
        self.assertEqual(reading["axes"]["construction"]["status"], "LICENSED")

    def test_absent_nun_alone_is_not_a_positive_verbal_connection(self):
        for kind in (NOUN, PARTICLE):
            with self.subTest(kind=kind):
                reading = read_morphology(description(kind, "لا تتصل به نون إناث ولا نون توكيد"))["readings"][0]
                self.assertEqual(reading["source_conflicts"], [])
                self.assertEqual(reading["axes"]["kind"]["status"], "LICENSED")

    def test_repeated_consistent_tense_does_not_create_a_conflict(self):
        report = read_morphology(description(VERB, "فعله ماض", "فعله ماض", word="كَتَبَ"))
        reading = report["readings"][0]
        self.assertEqual(report["status"], "READ")
        self.assertEqual(reading["source_conflicts"], [])
        self.assertEqual(reading["axes"]["construction"]["candidates"], ["built"])
        self.assertEqual(len([e for e in reading["evidence"] if e["property"] == "tense"]), 2)

    def test_same_spelling_keeps_independent_readings_and_supports(self):
        text = (description(PARTICLE, "فعله ماض", reading="bad", word="ما") +
                description(PARTICLE, reading="good_particle", word="ما") +
                description(VERB, "فعله مضارع", "تتصل به نون الإناث",
                            reading="good_verb", word="ما"))
        report = read_morphology(text)
        bad, particle, verb = report["readings"]
        self.assertEqual(bad["status"], "CONFLICT")
        for good in (particle, verb):
            self.assertEqual(good["status"], "READ")
            self.assertEqual(good["source_conflicts"], [])
            self.assertEqual(good["axes"]["construction"]["status"], "LICENSED")
            self.assertTrue(all(e["reading_id"] == good["reading_id"] for e in good["evidence"]))
        self.assertEqual(len({r["occurrence_id"] for r in report["readings"]}), 3)
        foreign = {e["support_id"] for r in (particle, verb) for e in r["evidence"]}
        self.assertTrue(all(not foreign.intersection(c["support_ids"]) for c in bad["source_conflicts"]))

    def test_conflict_record_references_the_exact_source_witnesses(self):
        text = description(PARTICLE, "فعله ماض", "فعله مضارع")
        reading = read_morphology(text, source_id="audit_source", scope="entry_a")["readings"][0]
        evidence = {e["support_id"]: e for e in reading["evidence"]}
        for conflict in reading["source_conflicts"]:
            self.assertEqual(conflict["occurrence_id"], reading["occurrence_id"])
            self.assertEqual(conflict["reading_id"], reading["reading_id"])
            self.assertTrue(conflict["support_ids"])
            for support_id in conflict["support_ids"]:
                item = evidence[support_id]
                span = item["span"]
                self.assertEqual(text.encode("utf-8")[span["start"]:span["end"]].decode("utf-8"), item["text"])
                self.assertEqual(item["source_id"], "audit_source")
                self.assertEqual(item["scope"], "entry_a")

    def test_conflicting_diptote_description_cannot_keep_a_nested_approval(self):
        report = read_morphology(description(NOUN, "يسلم من شبه الحرف", "فعله ماض",
                                             "آخره ألف التأنيث", "دخلت عليه أل"))
        reading = report["readings"][0]
        self.assert_no_approval(reading)
        diptote = reading["axes"]["diptote"]
        self.assertEqual(diptote["cause_prediction"]["candidates"], ["diptote"])
        self.assertEqual(diptote["genitive"]["candidates"], ["kasra"])
        self.assertIn("CONSISTENT_SOURCE_READING", diptote["prerequisites"])
        self.assertIn("CONSISTENT_SOURCE_READING", diptote["genitive"]["prerequisites"])
        self.assertFalse(diptote["genitive"]["applied_to_occurrence"])

    def test_replay_rejects_conflict_removal_status_promotion_and_old_version(self):
        text = description(PARTICLE, "فعله ماض", "فعله مضارع")
        report = read_morphology(text)
        self.assertEqual(report["reader_version"], "nabt.morphology-reader.v2")
        self.assertTrue(verify_morphology(report, text=text)["valid"])
        self.assertEqual(decode_morphology(morphology_number(report)), report)
        for action in ("erase_conflicts", "erase_support", "promote", "old_version"):
            with self.subTest(action=action):
                changed = deepcopy(report)
                if action == "erase_conflicts":
                    changed["readings"][0]["source_conflicts"] = []
                elif action == "erase_support":
                    changed["readings"][0]["source_conflicts"][0]["support_ids"] = []
                elif action == "promote":
                    changed["readings"][0]["axes"]["kind"]["status"] = "LICENSED"
                else:
                    changed["reader_version"] = "nabt.morphology-reader.v1"
                self.assertFalse(verify_morphology(changed, text=text)["valid"])

    def test_corrected_source_is_recomputed_without_reusing_conflict_authority(self):
        old_text = description(PARTICLE, "فعله ماض")
        new_text = description(PARTICLE)
        old = read_morphology(old_text)
        new = read_morphology(new_text)
        self.assertEqual(old["status"], "CONFLICT")
        self.assertEqual(new["status"], "READ")
        self.assertNotEqual(old["readings"][0]["occurrence_id"], new["readings"][0]["occurrence_id"])
        self.assertFalse(verify_morphology(old, text=new_text)["valid"])
        self.assertTrue(verify_morphology(new, text=new_text)["valid"])


if __name__ == "__main__":
    unittest.main()
