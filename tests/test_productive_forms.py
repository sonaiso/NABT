"""Authored conditional contract tests; not a blind Arabic accuracy sample."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import read_discourse, verify_discourse
from nabt.errors import NabtError
from nabt.person_evidence import person_candidates
from nabt.productive_forms import replay_policy, installed_shapes
from test_person_evidence import corpus, verb
from test_source_bound_nominal_bridges import record


NOMINAL = record(1, "kariymN", "N", "kariym", "krm") + record(2, "kariymK", "N", "kariym", "krm")


class ProductiveImperativeTests(unittest.TestCase):
    def read(self, surface, form="yakotubu", root="ktb", lemma="kataba", extra="", excluded=()):
        model = learn_qac_lexicon(corpus([verb(form, root=root, lemma=lemma, extra=extra)]),
                                 excluded_verses=excluded)
        return person_candidates(surface, lexical_model=model)

    def test_three_independent_vowel_examples(self):
        for target, form, root, lemma in (("اُكْتُبْ", "yakotubu", "ktb", "kataba"),
                ("اِضْرِبْ", "yaDoribu", "Drb", "Daraba"),
                ("اِفْتَحْ", "yafo taHu".replace(" ", ""), "ftH", "fataHa")):
            with self.subTest(target=target):
                rows = self.read(target, form, root, lemma)
                self.assertTrue(rows)
                self.assertTrue(all(r["aspect"] == "IMPV" and r["construction"] == "built" for r in rows))
                self.assertEqual({r["profile_id"] for r in rows}, {"2MS"})

    def test_wrong_initial_vowel_is_not_a_reading(self):
        self.assertEqual(self.read("اِكْتُبْ"), [])

    def test_wrong_final_vowel_is_not_a_reading(self):
        self.assertEqual(self.read("اُكْتُبُ"), [])

    def test_unvocalized_and_partial_inputs_do_not_select_this_bridge(self):
        for target in ("اكتب", "اكْتُبْ", "اُكتبْ", "اُكْتبْ"):
            self.assertEqual(self.read(target), [])

    def test_wrong_internal_vowel_is_not_a_reading(self):
        self.assertEqual(self.read("اِكْتِبْ"), [])

    def test_source_withdrawal(self):
        self.assertEqual(self.read("اُكْتُبْ", excluded=("1:1",)), [])

    def test_passive_source_does_not_license_command(self):
        self.assertEqual(self.read("اُكْتُبْ", extra="|PASS"), [])

    def test_incomplete_source_does_not_supply_missing_vowels(self):
        self.assertEqual(self.read("اُكْتُبْ", form="yktb"), [])

    def test_nonmatching_source_root_is_not_repaired(self):
        self.assertEqual(self.read("اُكْتُبْ", root="ktm"), [])

    def test_weak_hamzated_geminate_sources_outside_scope(self):
        for target, form, root, lemma in (("اُدْعُوْ", "yadoEuwu", "dEw", "daEaA"),
                ("اُأْكُلْ", "ya>okulu", "Akl", ">akala"),
                ("اُمْدُدْ", "yamodudu", "mdd", "mad~a")):
            self.assertEqual(self.read(target, form, root, lemma), [])

    def test_attestation_and_derivation_are_explicitly_distinct(self):
        row = self.read("اُكْتُبْ")[0]
        witness = row["productive_derivation"]
        self.assertFalse(witness["target_attested"])
        self.assertFalse(witness["target_role_labels_used"])
        self.assertEqual(witness["source_form"], "يَكْتُبُ")
        self.assertTrue(witness["source_support_ids"])
        self.assertEqual(row["valency_witnesses"], [])

    def test_source_contract_rechecked_with_warm_cache(self):
        self.assertTrue(self.read("اُكْتُبْ"))
        with patch("nabt.productive_forms.POLICY_SHA256", "0" * 64):
            with self.assertRaises(NabtError):
                self.read("اُكْتُبْ")

    def test_lean_export_integrity(self):
        self.assertEqual(len(installed_shapes()["imperative"]), 3)
        with patch("nabt.productive_forms.TABLE_SHA256", "0" * 64):
            with self.assertRaises(NabtError):
                installed_shapes()

    def test_source_passages_replay(self):
        self.assertEqual(len(replay_policy()["passages"]), 3)


class ProductiveNominalTests(unittest.TestCase):
    def read(self, text="كَرِيمًا", raw=NOMINAL, excluded=()):
        model = learn_qac_lexicon(("LOCATION\tFORM\tTAG\tFEATURES\n" + raw).encode(),
                                 excluded_verses=excluded, source_id="authored_productive")
        report = read_discourse(text, lexical_model=model, source_id="productive_target")
        self.assertTrue(verify_discourse(report, lexical_model=model)["valid"])
        rows = [r for o in report["occurrences"] for r in o["readings"]
                if r.get("variant") == "productive_accusative_alif"]
        return rows, report, model

    def test_unseen_carrier_has_independent_paired_premise(self):
        rows, _, _ = self.read()
        self.assertTrue(rows)
        for row in rows:
            witness = row["nominal_case_carrier"]
            self.assertTrue(witness["generated_form"])
            self.assertFalse(witness["target_attested"])
            self.assertEqual(row["possible_cases"], [0])
            self.assertEqual(len(witness["base_paradigm_supports"]), 2)

    def test_carrier_spans_conserve_exact_input_bytes(self):
        rows, _, _ = self.read()
        for row in rows:
            witness = row["nominal_case_carrier"]
            raw = "كَرِيمًا".encode()
            for name in ("base", "carrier"):
                span = witness[name + "_span"]
                self.assertEqual(raw[span["start"]:span["end"]].decode(), witness[name + "_surface"])
            self.assertEqual(witness["base_span"]["end"], witness["carrier_span"]["start"])

    def test_single_source_form_is_insufficient(self):
        self.assertEqual(self.read(raw=record(1, "kariymN", "N", "kariym", "krm"))[0], [])

    def test_source_pair_withdrawal_removes_generation(self):
        self.assertEqual(self.read(excluded=("1:2",))[0], [])

    def test_missing_number_is_not_assumed_singular(self):
        self.assertEqual(self.read(raw=NOMINAL.replace("|MS", "|M"))[0], [])

    def test_mismatched_source_templates_do_not_pair(self):
        self.assertEqual(self.read(raw=NOMINAL.replace("kariymK", "kuriymK"))[0], [])

    def test_wrong_vowels_and_partial_targets_do_not_generate(self):
        for target in ("كُرِيمًا", "كَريمًا", "كَرِيمٌا", "كَرِيمًاَ"):
            self.assertEqual(self.read(text=target)[0], [])

    def test_consonantal_waw_and_yaa_cannot_lose_their_vowels(self):
        for stem, root, full, partial in (("Sawar", "Swr", "صَوَرًا", "صَورًا"),
                                          ("bayat", "byt", "بَيَتًا", "بَيتًا")):
            # Authored lexical premises isolate the written-shape contract.
            raw = record(1, stem + "N", "N", stem, root) + record(2, stem + "K", "N", stem, root)
            self.assertTrue(self.read(text=full, raw=raw)[0])
            self.assertEqual(self.read(text=partial, raw=raw)[0], [])

    def test_existing_full_form_retains_its_original_path(self):
        rows, report, _ = self.read(raw=NOMINAL + record(3, "kariymFA", "N", "kariym", "krm"))
        self.assertEqual(rows, [])
        self.assertTrue(any(r.get("nominal_case_carrier", {}).get("rule") == "attested_accusative_alif"
                            for o in report["occurrences"] for r in o["readings"]))

    def test_forged_premise_fails_report_replay(self):
        rows, report, model = self.read()
        self.assertTrue(rows)
        forged = deepcopy(report)
        for o in forged["occurrences"]:
            for r in o["readings"]:
                if r.get("variant") == "productive_accusative_alif":
                    r["nominal_case_carrier"]["base_paradigm_supports"][0]["record_id"] = "0" * 64
        self.assertFalse(verify_discourse(forged, lexical_model=model)["valid"])

    def test_generated_word_does_not_create_a_sentence_claim(self):
        rows, report, _ = self.read()
        self.assertTrue(rows)
        self.assertNotEqual(report["status"], "LICENSED_DISCOURSE")

    def test_productive_case_carriers_enable_complete_kana_and_inna_clauses(self):
        raw = (NOMINAL + record(3, "zayodN", "PN", "zayod", "zyd") +
               record(4, "zayodK", "PN", "zayod", "zyd") +
               record(5, "kaAna", "V", "kaAna", "kwn", "PERF|3MS"))
        model = learn_qac_lexicon(("LOCATION\tFORM\tTAG\tFEATURES\n" + raw).encode())
        context = {"entities": [{"id": "z", "name": "زيد", "gender": "masculine",
                                  "number": "singular", "kind": "person"}]}
        for text in ("كَانَ زَيْدٌ كَرِيمًا.", "إِنَّ زَيْدًا كَرِيمٌ."):
            report = read_discourse(text, lexical_model=model, context=context)
            self.assertEqual(report["status"], "LICENSED_DISCOURSE")
            self.assertTrue(report["claims"])
            self.assertTrue(verify_discourse(report, lexical_model=model, context=context)["valid"])
        for text in ("كَانَ زَيْدٌ كَرِيمٌ.", "إِنَّ زَيْدًا كَرِيمًا."):
            report = read_discourse(text, lexical_model=model, context=context)
            self.assertNotEqual(report["status"], "LICENSED_DISCOURSE")

    def test_independent_validator_rejects_forged_source_and_shifted_spans(self):
        from tools.discourse_evaluation import SourceAudit
        from tools.productive_form_validation import validate_nominal
        rows, _, _ = self.read()
        source = ("LOCATION\tFORM\tTAG\tFEATURES\n" + NOMINAL).encode()
        audit = SourceAudit(source, source_id="authored_productive")
        inputs = {"text": "كَرِيمًا", "source_id": "productive_target"}
        validate_nominal(rows[0], inputs, audit)
        for field in ("record_id", "span"):
            changed = deepcopy(rows[0])
            if field == "record_id":
                changed["nominal_case_carrier"]["base_paradigm_supports"][0]["record_id"] = "0" * 64
            else:
                changed["nominal_case_carrier"]["carrier_span"]["start"] -= 2
            with self.assertRaises(ValueError):
                validate_nominal(changed, inputs, audit)


if __name__ == "__main__":
    unittest.main()
