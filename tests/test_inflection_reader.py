"""Adversarial checks independent of the held-out transfer evaluation."""

from copy import deepcopy
from pathlib import Path
import unittest

from nabt.corpus_evidence import (buckwalter_to_arabic, learn_qac_lexicon,
                                  lexical_index, lookup_key)
from nabt.errors import NabtError
from nabt.inflection_reader import read_inflection, verify_inflection

ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/inflection_training.tsv").read_bytes()


def contents(report):
    return [r for o in report["occurrences"] for r in o["readings"] if r["kind"] != "particle"]


def semantics(report):
    return sorted((r["kind"], r["construction"], r["lexical_features"]["root"],
                   r["lexical_features"]["gender"], tuple(r["class_candidates"]),
                   tuple((s["class"], s["case"], s["sign"]) for s in r["sign_candidates"]),
                   r["actual_role"], r["actual_case"], r["local_case"])
                  for r in contents(report))


class InflectionReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def read(self, text, model=None):
        return read_inflection(text, lexical_model=self.model if model is None else model)

    def test_source_learned_noun_new_case(self):
        report = self.read("مِنْ رَجُلٍ")
        licensed = [r for r in contents(report) if r["actual_case"] == "jarr"]
        self.assertTrue(licensed)
        self.assertEqual(licensed[0]["actual_role"], "preposition_object")
        self.assertEqual(licensed[0]["sign_candidates"][0]["sign_name"], "kasra")
        self.assertEqual(licensed[0]["lexical_features"]["gender"], "masculine")

    def test_nun_deletion_needs_retained_base_and_person(self):
        report = self.read("لَمْ يَكْتُبُوا")
        rows = [r for r in contents(report) if r["actual_case"] == "jazm"]
        self.assertTrue(rows)
        self.assertTrue(any(r["variant"] == "nun_deleted_from_retained_base" for r in rows))
        self.assertEqual({s["sign_name"] for r in rows for s in r["sign_candidates"]}, {"nun_deleted"})
        without = b"\n".join(l for l in TRAINING.split(b"\n") if not l.startswith(b"(1:4:"))
        self.assertEqual(self.read("لَمْ يَكْتُبُوا", learn_qac_lexicon(without))["assignments"], [])

    def test_weak_deleted_sign_is_not_residual_damma(self):
        rows = contents(self.read("لَمْ يَدْعُ"))
        self.assertTrue(rows)
        licensed = [r for r in rows if r["actual_case"] == "jazm"]
        self.assertTrue(licensed)
        self.assertEqual(licensed[0]["sign_candidates"][0]["sign_name"], "weak_deleted")
        self.assertEqual(licensed[0]["sign_candidates"][0]["surface"], 0)
        self.assertEqual(licensed[0]["weak_root_profile"]["mask"], 4)
        self.assertFalse(self.read("لَمْ يَدْعِ")["assignments"])

    def test_feminine_nun_remains_built_with_local_case(self):
        rows = contents(self.read("لَمْ يَكْتُبْنَ"))
        self.assertTrue(any(r["local_case"] == "jazm" and r["actual_case"] is None for r in rows))
        self.assertTrue(any(r["nun_readings"][0]["kind"] == "feminine_subject" for r in rows))
        self.assertTrue(all(not r["sign_candidates"] for r in rows))

    def test_noun_dual_and_feminine_plural(self):
        dual = contents(self.read("مِنْ طَالِبَيْنِ"))
        self.assertTrue(any(r["actual_case"] == "jarr" and r["class_candidates"] == [2] for r in dual))
        feminine = contents(self.read("مِنْ كَاتِبَاتٍ"))
        self.assertTrue(any(r["class_candidates"] == [4] for r in feminine))

    def test_abyat_not_sound_feminine_plural_and_singular_attested(self):
        rows = contents(self.read("مِنْ أَبْيَاتٍ"))
        self.assertTrue(rows)
        self.assertTrue(all(4 not in r["class_candidates"] for r in rows))
        self.assertTrue(any(r["lexical_features"]["singular_witnesses"] for r in rows))
        without = b"\n".join(l for l in TRAINING.split(b"\n") if not l.startswith(b"(1:9:"))
        rows = contents(self.read("مِنْ أَبْيَاتٍ", learn_qac_lexicon(without)))
        self.assertTrue(all(not r["lexical_features"]["singular_witnesses"] for r in rows))

    def test_radical_nun_does_not_supply_case(self):
        rows = contents(self.read("نُونٌ"))
        self.assertTrue(rows)
        self.assertEqual(rows[0]["nun_readings"][0]["kind"], "radical")
        self.assertIsNone(rows[0]["actual_case"])
        self.assertIsNone(rows[0]["lexical_features"]["number"])

    def test_prefix_segmentation_conserves_bytes(self):
        report = self.read("بِالرَّجُلِ")
        self.assertTrue(report["assignments"])
        for row in contents(report):
            self.assertEqual("".join(p["surface"] for p in row["segmentation"]["parts"]), "بِالرَّجُلِ")
            self.assertTrue(row["segmentation"]["coverage_valid"])
        for text in ("بِّالرَّجُلِ", "بِالُرَّجُلِ"):
            self.assertEqual(self.read(text)["assignments"], [])

    def test_built_and_weak_paradigms_reject_explicitly_conflicting_vowels(self):
        self.assertEqual(self.read("لَمْ يَكْتُبْنِ")["assignments"], [])
        wrong = TRAINING.replace(b"yadoEuw", b"yadoEaw")
        self.assertEqual(self.read("لَمْ يَدْعُ", learn_qac_lexicon(wrong))["assignments"], [])
        geminate = TRAINING.replace(b"yadoEuw", b"yadoEuw~")
        self.assertEqual(self.read("لَمْ يَدْعُ", learn_qac_lexicon(geminate))["assignments"], [])

    def test_tanwin_alone_and_deleted_nominal_yaa_do_not_prove_ordinary_declension(self):
        raw = b"LOCATION\tFORM\tTAG\tFEATURES\n(1:1:1:1)\tqaADK\tN\tSTEM|POS:N|LEM:qaADiy|ROOT:qDy|MS|GEN\n"
        rows = contents(self.read("قَاضٍ", learn_qac_lexicon(raw)))
        self.assertTrue(rows)
        self.assertEqual(rows[0]["class_candidates"], [])
        self.assertEqual(rows[0]["lexical_features"]["root"], "قضي")
        singleton = b"\n".join(l for l in TRAINING.split(b"\n") if not l.startswith(b"(1:2:"))
        self.assertEqual(self.read("مِنْ رَجُلٍ", learn_qac_lexicon(singleton))["assignments"], [])

    def test_no_unknown_word_or_unqualified_operator_authority(self):
        for text in ("مِنْ زَلْفَخٍ", "من رَجُلٍ", "لم يَكْتُبْ", "رَجُلٍ"):
            with self.subTest(text=text):
                self.assertEqual(self.read(text)["assignments"], [])
        self.assertEqual(read_inflection("مِنْ رَجُلٍ")["assignments"], [])

    def test_closed_attachment_does_not_cross_scope_boundaries(self):
        for text in ("مِنْ\nرَجُلٍ", "مِنْ؛ رَجُلٍ", "«مِنْ» رَجُلٍ", "مِنْ رَجُلٍ يَكْتُبُ", "مِنْ (رَجُلٍ)"):
            with self.subTest(text=text):
                self.assertEqual(self.read(text)["assignments"], [])

    def test_training_case_and_mood_labels_are_not_predictor_features(self):
        poisoned = TRAINING.replace(b"|NOM", b"|ACC").replace(b"|GEN", b"|MOOD:JUS")
        second = learn_qac_lexicon(poisoned)
        for text in ("مِنْ رَجُلٍ", "لَنْ يَكْتُبَ", "لَمْ يَدْعُ"):
            self.assertEqual(semantics(self.read(text)), semantics(self.read(text, second)))

    def test_grouped_exclusion_and_source_withdrawal(self):
        excluded = learn_qac_lexicon(TRAINING, excluded_verses=("1:1", "1:2"))
        self.assertEqual(self.read("مِنْ رَجُلٍ", excluded)["assignments"], [])
        report = self.read("مِنْ رَجُلٍ")
        self.assertTrue(verify_inflection(report, lexical_model=self.model)["valid"])
        self.assertFalse(verify_inflection(report)["valid"])
        self.assertFalse(verify_inflection(report, lexical_model=excluded)["valid"])

    def test_replay_binds_source_scope_and_every_claim(self):
        report = self.read("لَمْ يَدْعُ")
        for kwargs in ({"text": "لَنْ يَدْعُ"}, {"scope": "foreign"}, {"source_id": "other"}):
            self.assertFalse(verify_inflection(report, lexical_model=self.model, **kwargs)["valid"])
        changed = deepcopy(report)
        changed["assignments"][0]["inflected_case"] = "raf"
        self.assertFalse(verify_inflection(changed, lexical_model=self.model)["valid"])

    def test_single_vowel_noun_is_not_silently_declared_inflected(self):
        raw = b"LOCATION\tFORM\tTAG\tFEATURES\n(1:1:1:1)\trajulu\tN\tSTEM|POS:N|LEM:rajul|ROOT:rjl|M|NOM\n"
        report = self.read("مِنْ رَجُلِ", learn_qac_lexicon(raw))
        self.assertEqual(report["assignments"], [])
        self.assertTrue(all(r["construction"] is None for r in contents(report)))

    def test_caller_cannot_inject_authoritative_entries(self):
        index, _ = lexical_index(self.model)
        with self.assertRaises(TypeError):
            index["زلفخ"] = ()
        with self.assertRaises(NabtError):
            read_inflection("مِنْ رَجُلٍ", lexical_model={"valid": True, "entries": {}})

    def test_declared_transliteration_is_reversible_instead_of_hamza_collapse(self):
        self.assertEqual(buckwalter_to_arabic("'>&<}A"), "ءأؤإئا")
        self.assertEqual(lookup_key("ٱلْبَيْتِ"), "البيت")
        self.assertNotEqual(lookup_key("أَكَلَ"), lookup_key("اَكَلَ"))
        self.assertIsNone(lookup_key("كِتَٰب\u06df"))


if __name__ == "__main__":
    unittest.main()
