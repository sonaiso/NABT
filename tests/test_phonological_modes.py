"""Source-linked, hand-authored boundary oracles; not a blind speech benchmark."""
import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from nabt.phonological_modes import Mode, Profile, realize, realize_imperative_onset, replay_policy
from nabt.corpus_evidence import learn_qac_lexicon
from test_person_evidence import corpus, verb


def surfaces(report):
    return {tuple(v["segments"]) for v in report["alternatives"]}


class PhonologicalModeTests(unittest.TestCase):
    def test_initial_wasl_vowel_independent_examples(self):
        self.assertEqual(surfaces(realize("idrib")), {("ʔ", "i", "ḍ", "r", "i", "b")})
        self.assertEqual(surfaces(realize("uqtul")), {("ʔ", "u", "q", "t", "u", "l")})
        self.assertEqual(surfaces(realize("alqawm")), {("ʔ", "a", "l", "q", "a", "w", "m", "u")})

    def test_noun_damma_does_not_choose_initial_damma(self):
        self.assertEqual(surfaces(realize("imru")), {("ʔ", "i", "m", "r", "u", "ʔ", "u", "n")})

    def test_connected_wasl_omits_only_initial_helping_hamza(self):
        self.assertEqual(surfaces(realize("idrib", start="wasl")), {("ḍ", "r", "i", "b")})
        self.assertEqual(realize("idrib", start="wasl")["written_form"], "اِضْرِبْ")

    def test_restart_reintroduces_onset_without_mutating_source(self):
        connected = realize("uqtul", start="wasl")
        initial = realize("uqtul", start="ibtida")
        self.assertEqual(initial["written_form"], connected["written_form"])
        self.assertEqual(surfaces(initial), {("ʔ", "u", "q", "t", "u", "l")})

    def test_qata_hamza_is_not_elided(self):
        self.assertEqual(surfaces(realize("akhraja", start="wasl")), {("ʔ", "a", "kh", "r", "a", "j", "a")})

    def test_pause_final_vowel_and_tanwin(self):
        self.assertEqual(surfaces(realize("akhraja", end="waqf")), {("ʔ", "a", "kh", "r", "a", "j")})
        self.assertEqual(surfaces(realize("khalid", end="waqf")), {("kh", "a:", "l", "i", "d")})
        self.assertEqual(surfaces(realize("zayd_acc", end="waqf")), {("z", "a", "y", "d", "a:")})

    def test_feminine_t_does_not_generalize_to_radical_t(self):
        self.assertEqual(surfaces(realize("talha", end="waqf")), {("ṭ", "a", "l", "ḥ", "a", "h")})
        self.assertEqual(surfaces(realize("bint", end="waqf")), {("b", "i", "n", "t")})
        self.assertEqual(surfaces(realize("talha", end="wasl")), {("ṭ", "a", "l", "ḥ", "a", "t", "u")})

    def test_independent_onset_and_pause_can_both_apply(self):
        self.assertEqual(surfaces(realize("ism", start="ibtida", end="waqf")), {("ʔ", "i", "s", "m")})
        self.assertEqual(surfaces(realize("ism", start="wasl", end="waqf")), {("s", "m")})

    def test_transient_contact_never_restores_deleted_weak_radical(self):
        for key,expected,deleted in (("yaqul_jussive", ("y", "a", "q", "u", "l", "i"), ["w"]),
                                     ("yabi_jussive", ("y", "a", "b", "i", "ʕ", "i"), ["y"]),
                                     ("yakhaf_jussive", ("y", "a", "kh", "a", "f", "i"), ["w"])):
            with self.subTest(key=key):
                report=realize(key, following_id="alqawm")
                self.assertEqual(surfaces(report), {expected})
                self.assertEqual(report["deleted_radicals"], deleted)
                self.assertNotIn("a:", expected)

    def test_ordinary_contact_kasra_preserves_spelling(self):
        report = realize("idrib", following_id="ibn")
        self.assertEqual(surfaces(report), {("ʔ", "i", "ḍ", "r", "i", "b", "i")})
        self.assertEqual(report["written_form"], "اِضْرِبْ")

    def test_weak_pause_alternatives_are_retained_per_profile(self):
        simple = realize("irmi", end="waqf")
        historical = realize("irmi", end="waqf", profile=Profile.SIBAWAYHI_OPTIONS)
        self.assertEqual(surfaces(simple), {("ʔ", "i", "r", "m")})
        self.assertEqual(surfaces(historical), {("ʔ", "i", "r", "m"), ("ʔ", "i", "r", "m", "i", "h")})
        self.assertFalse(historical["acoustic_validation"])
        self.assertFalse(historical["complete_for_arabic"])

    def test_single_consonant_pause_keeps_ha_sakt(self):
        self.assertEqual(surfaces(realize("i_single", end="waqf")), {("ʕ", "i", "h")})
        self.assertEqual(surfaces(realize("i_single", end="wasl")), {("ʕ", "i")})

    def test_unknown_is_not_arabic_rejection(self):
        self.assertEqual(realize("unreviewed_form")["status"], "UNKNOWN")
        self.assertEqual(realize("irmi", following_id="alqawm")["status"], "UNKNOWN")
        self.assertEqual(realize("idrib", following_id="akhraja")["status"], "UNKNOWN")

    def test_invalid_boundaries_are_separate(self):
        for kwargs in ({"start":"waqf"},{"end":"ibtida"},{"profile":"all_arabic"},
                       {"end":"waqf","following_id":"ibn"},{"start":True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(NabtError):
                realize("idrib", **kwargs)

    def test_source_and_policy_rechecked(self):
        policy = replay_policy()
        self.assertEqual(len(policy["examples"]), 20)
        self.assertEqual(len(policy["passages"]), 20)
        with patch("nabt.phonological_modes.POLICY_SHA256", "0"*64):
            with self.assertRaises(NabtError) as err:
                realize("idrib")
        self.assertEqual(err.exception.code, "INSTALLED_CONTRACT_FAILED")
        self.assertEqual(err.exception.status, "DEFER")


class VerifiedImperativeOnsetTests(unittest.TestCase):
    def model(self):
        return learn_qac_lexicon(corpus([verb("yakotubu",root="ktb",lemma="kataba")]))

    def test_rederives_singular_onset(self):
        report=realize_imperative_onset("اُكْتُبْ", lexical_model=self.model(), profile_id="2MS", start="wasl")
        self.assertEqual(report["status"], "CONDITIONAL_PROJECTION")
        self.assertEqual(report["surface"]["onset_segments"], [])
        self.assertEqual(report["surface"]["observed_vocalized_remainder"], "كْتُبْ")
        self.assertEqual(report["written_form"], "اُكْتُبْ")
        self.assertEqual(report["end"], "unprojected")

    def test_unvocalized_or_wrong_initial_not_licensed(self):
        for surface in ("اكتب", "اِكْتُبْ"):
            self.assertEqual(realize_imperative_onset(surface, lexical_model=self.model(),
                                                    profile_id="2MS")["status"], "UNKNOWN")

    def test_all_verified_address_profiles_and_plural_spelling_preserved(self):
        cases = (("اُكْتُبْ", "2MS"), ("اُكْتُبِي", "2FS"), ("اُكْتُبَا", "2MD"),
                 ("اُكْتُبَا", "2FD"), ("اُكْتُبُوا", "2MP"), ("اُكْتُبْنَ", "2FP"))
        for form, code in cases:
            with self.subTest(code=code):
                report=realize_imperative_onset(form, lexical_model=self.model(), profile_id=code, start="wasl")
                self.assertEqual(report["status"], "CONDITIONAL_PROJECTION")
                self.assertEqual(report["written_form"], form)
                self.assertEqual(report["surface"]["observed_vocalized_remainder"], form[2:])
                self.assertEqual(report["end"], "unprojected")

    def test_source_withdrawal_removes_reusable_projection(self):
        model=learn_qac_lexicon(corpus([verb("yakotubu",root="ktb",lemma="kataba")]), excluded_verses=("1:1",))
        self.assertEqual(realize_imperative_onset("اُكْتُبُوا", lexical_model=model,
                                                profile_id="2MP")["status"], "UNKNOWN")

    def test_claimed_profile_is_not_enough(self):
        self.assertEqual(realize_imperative_onset("اُكْتُبْ", lexical_model=self.model(),
                                                profile_id="2FP")["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
