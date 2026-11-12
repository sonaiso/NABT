"""Source-level checks on the finite passive frame, independent of neural ranking."""
import hashlib
from unittest import TestCase, mock

from tools.grammar_catalog import passive_relation as owner


class WrittenPassiveFrames(TestCase):
    def one(self, text):
        card, = owner.analyze(text)
        ev = card["evidence"]
        self.assertEqual(ev["source_sha256"], hashlib.sha256(text.encode()).hexdigest())
        raw = text.encode()
        for row in ev["analyzed_source"]["mapping"]:
            a, b = row["source_span"]
            self.assertEqual(raw[a:b].decode(), row["observed"])
        self.assertFalse(ev["world_truth_established"])
        return card, ev

    def test_argument_and_event_are_preserved_while_sign_and_cue_change(self):
        _, before = self.one("  فُتِحَ   البابُ.")
        _, after = self.one(" لَمْ  يُفْتَحْ\tالبابُ. ")
        self.assertEqual([v["relation"] for v in (before, after)], ["ASSERT_PASSIVE", "DENY_PASSIVE"])
        self.assertEqual((before["event_family"], before["patient_key"]), ("فتح", "باب"))
        self.assertEqual((after["event_family"], after["patient_key"]), ("فتح", "باب"))
        self.assertEqual(before["event_sense_id"], owner.SCHEMA + ":open")
        self.assertEqual(before["event_sense_id"], after["event_sense_id"])
        self.assertIsNone(before["cue_span"])
        a, b = after["cue_span"]
        self.assertEqual(" لَمْ  يُفْتَحْ\tالبابُ. ".encode()[a:b].decode(), "لَمْ")
        self.assertFalse(after["operator_reading_conditional"])
        self.assertTrue(after["written_case_observed"])
        for analysis in after["owner_analyses"]:
            self.assertIn("REFERENCE_NOT_UNIQUELY_LICENSED", analysis["obligations"])

    def test_unvocalized_particle_is_an_explicit_conditional_not_observed_marks(self):
        card, evidence = self.one("  لم يُفتَح الباب")
        self.assertTrue(evidence["operator_reading_conditional"])
        self.assertIn("مشروطة", card["degree"])
        self.assertIn("الاستفهامية", card["unresolved"])
        self.assertNotEqual(evidence["source_sha256"], evidence["analyzed_source"]["sha256"])
        cue, verb, patient = evidence["analyzed_source"]["mapping"]
        self.assertEqual((cue["observed"], cue["analyzed"]), ("لم", "لَمْ"))
        self.assertEqual(verb["observed"], verb["analyzed"])
        self.assertTrue(cue["analyzed_span"][1] > cue["source_span"][1])
        self.assertFalse(evidence["written_case_observed"])

    def test_shared_passive_stem_does_not_select_one_lexical_lemma(self):
        _, perfect = self.one("أُغْلِقَ القُفْلُ")
        _, imperfect = self.one("لَمْ يُغْلَقْ القُفْلُ")
        self.assertEqual(perfect["event_family"], imperfect["event_family"])
        self.assertEqual(set(imperfect["lexical_lemmas"]), {"أَغْلَقَ", "غَلَقَ"})
        self.assertFalse(imperfect["all_lexical_senses_established"])
        self.assertFalse(imperfect["external_referent_established"])
        for key in ("passive_pattern", "passive_subject", "lam", "close"):
            w = imperfect["witnesses"][key]
            a, b = w["utf8_span"]
            raw = (owner.ROOT / w["path"]).read_bytes()[a:b]
            self.assertEqual(hashlib.sha256(raw).hexdigest(), w["sha256"])
            self.assertEqual(raw.decode().strip(), w["quote"])

    def test_no_assertion_without_a_complete_supported_written_frame(self):
        for source in (
            "فتح الباب", "فَتَحَ الباب", "فُتِحَ البابَ", "فُتِحَ البابِ",
            "فُتِحَ البابٌ", "فُتِحَ الْبَاَبُ",
            "لَمْ يُفْتَحَ البابُ", "لَمْ يُفْتَحُ البابُ", "لَمْ يُفْتَحِ البَابُ", "لم يفتح الباب",
            "لِمَ يُفْتَحُ البابُ", "لن يُفْتَحَ البابُ", "لكي يُفْتَحَ البابُ",
            "جئت لكي يُفْتَحَ البابُ", "هل فُتِحَ البابُ", "فُتِحَ البابُ؟",
            "«فُتِحَ البابُ»", "لم أقل فُتِحَ البابُ", "فُتِحَ. البابُ",
            "فُتِحَ\nالبابُ", "فُتِحَ البابُ ثم كُسِرَ القلمُ", "فُتِحَ الرجلُ",
        ):
            with self.subTest(source=source):
                self.assertEqual(owner.analyze(source), [])

    def test_sun_letter_diacritics_are_checked_locally(self):
        for surface in ("الزُّجَاجُ", "الزجاج"):
            _, evidence = self.one("كُسِرَ " + surface)
            self.assertEqual(evidence["patient_key"], "زجاج")
        self.assertEqual(owner.analyze("كُسِرَ الزَّجَاجُ"), [])

    def test_feature_agreement_cannot_bypass_the_discourse_checker(self):
        with mock.patch.object(owner, "read_discourse", return_value={"clauses": []}):
            self.assertEqual(owner.analyze("كَسَرَ القَلَمَ"), [])
            self.assertEqual(owner.analyze("كُسِرَ القَلَمُ"), [])
