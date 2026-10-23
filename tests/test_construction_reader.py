"""Authored regressions for acquired construction evidence, not transfer gold.

The independent evaluation is frozen separately. These examples test actual
source withdrawal, scope, attachment, contrary morphology and replay changes.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import (read_discourse, ask_discourse, verify_discourse,
                            verify_discourse_answer, discourse_catalog)

ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/construction_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/construction_context.json").read_text())


def accepted(report):
    return [a for c in report["clauses"] for a in c["analyses"]
            if a["licensed_syntax"] and a["references_complete"] and not a["rejected_candidate"]]


def obligations(report):
    return {o for c in report["clauses"] for a in c["analyses"] for o in a["obligations"]}


def without_forms(*forms):
    return learn_qac_lexicon(b"\n".join(line for line in TRAINING.splitlines()
        if not any(b"\t" + form.encode() + b"\t" in line for form in forms)) + b"\n")


class ConstructionReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def read(self, text, **kwargs):
        return read_discourse(text, lexical_model=kwargs.pop("lexical_model", self.model),
                              context=kwargs.pop("context", CONTEXT), **kwargs)

    def ask(self, text, question, **kwargs):
        return ask_discourse(text, question, lexical_model=kwargs.pop("lexical_model", self.model),
                             context=kwargs.pop("context", CONTEXT), **kwargs)

    def test_four_operator_families_activate_source_bound_roles(self):
        cases = [
            ("كان زيدٌ حكيمًا.", {"kana_subject": "raf", "kana_predicate": "nasb"}),
            ("إنَّ زيدًا حكيمٌ.", {"inna_subject": "nasb", "inna_predicate": "raf"}),
            ("ظن زيدٌ سالمًا حكيمًا.", {"zanna_subject": "raf", "zanna_object1": "nasb", "zanna_object2": "nasb"}),
            ("كاد زيدٌ يكتبُ.", {"kada_subject": "raf", "kada_predicate": "nasb", "imperfect_indicative": "raf"}),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                report = self.read(text)
                self.assertEqual(report["status"], "LICENSED_DISCOURSE")
                for row in accepted(report):
                    roles = {a["actual_role"]: a["inflected_case"] or a["local_case"] for a in row["assignments"]}
                    self.assertEqual(roles, expected)
                    gate = next(r for r in row["relations"] if r["kind"] == "construction_gate")
                    self.assertTrue(gate["allowed"])
                    self.assertTrue(all(gate["premises"].values()))
                    self.assertTrue(all(e["head"]["reading_id"] in row["reading_ids"] and
                        e["target"]["reading_id"] in row["reading_ids"] for e in gate["edges"]))

    def test_rejected_case_candidates_never_activate_or_answer(self):
        for text in ("كان زيدًا حكيمٌ.", "إنَّ زيدٌ حكيمًا.", "ظن زيدٌ سالمٌ حكيمٌ."):
            with self.subTest(text=text):
                report = self.read(text)
                self.assertEqual(report["claims"], [])
                self.assertFalse(accepted(report))
                self.assertTrue(all(a["actual_role"] is None for c in report["clauses"]
                    for row in c["analyses"] for a in row["assignments"]))
                self.assertNotEqual(self.ask(text, "هل " + text[:-1] + "؟")["status"], "SUPPORTED")

    def test_kada_local_case_is_separate_from_internal_mood(self):
        for text, mood in (("كاد زيدٌ يكتبُ.", "raf"), ("كاد زيدٌ أن يكتبَ.", "nasb")):
            with self.subTest(text=text):
                report = self.read(text)
                self.assertEqual(report["status"], "LICENSED_DISCOURSE")
                for row in accepted(report):
                    clause = next(a for a in row["assignments"] if a["role"] == "kada_predicate")
                    verb = next(a for a in row["assignments"] if a["role"].startswith("imperfect_"))
                    self.assertEqual((clause["case_domain"], clause["local_case"], clause["inflected_case"]),
                                     ("clause_local_case", "nasb", None))
                    self.assertEqual(verb["inflected_case"], mood)
        for text in ("حرى زيدٌ يكتبُ.", "أخذ زيدٌ أن يكتبَ.", "كاد زيدٌ أن يكتبُ."):
            self.assertEqual(self.read(text)["claims"], [])

    def test_scoped_operators_do_not_entail_their_embedded_fact(self):
        for text, question in (("ظن زيدٌ سالمًا حكيمًا.", "هل سالمٌ حكيمٌ؟"),
                               ("كاد زيدٌ يكتبُ.", "هل زيدٌ يكتبُ؟"),
                               ("عسى زيدٌ أن يكتبَ.", "هل زيدٌ يكتبُ؟"),
                               ("صار زيدٌ حكيمًا.", "هل زيدٌ حكيمٌ؟")):
            with self.subTest(text=text):
                report = self.read(text)
                self.assertEqual(report["status"], "LICENSED_DISCOURSE")
                self.assertEqual(report["claims"][0]["predicate_kind"], "scoped")
                self.assertFalse(report["claims"][0]["restriction"][0]["embedded_fact_projection"])
                self.assertEqual(self.ask(text, question)["status"], "UNKNOWN")
                self.assertEqual(self.ask(text, "هل " + text[:-1] + "؟")["status"], "SUPPORTED")

    def test_tense_does_not_disappear_and_nonassertive_force_is_kept(self):
        self.assertEqual(self.ask("كان زيدٌ حكيمًا.", "هل زيدٌ حكيمٌ؟")["status"], "UNKNOWN")
        for text in ("ليت زيدًا حكيمٌ.", "لعل زيدًا حكيمٌ."):
            report = self.read(text)
            self.assertEqual(report["claims"], [])
            self.assertIn(report["clauses"][0]["force"], ("WISH", "HOPE"))

    def test_future_copula_keeps_operator_roles_tense_and_own_mood(self):
        witness = b"(9:50:1:1)\tyakuwnu\tV\tSTEM|POS:V|IMPF|LEM:kaAna|ROOT:kwn|3MS\n"
        model = learn_qac_lexicon(TRAINING + witness)
        for text, tense in (("سوف يكونُ زيدٌ حكيمًا.", "future"), ("يكونُ زيدٌ حكيمًا.", "nonpast")):
            with self.subTest(text=text):
                report = self.read(text, lexical_model=model)
                self.assertEqual(report["status"], "LICENSED_DISCOURSE")
                self.assertEqual([(c["predicate_kind"], c["tense"]) for c in report["claims"]], [("property", tense)])
                for row in accepted(report):
                    self.assertEqual({a["actual_role"] for a in row["assignments"]},
                                     {"kana_subject", "kana_predicate", "imperfect_indicative"})
                    self.assertFalse(any(r["kind"] == "hal" for r in row["relations"]))
        self.assertEqual(self.ask("سوف يكونُ زيدٌ حكيمًا.", "هل سوف يكونُ زيدٌ حكيمًا؟",
                                  lexical_model=model)["status"], "SUPPORTED")
        self.assertEqual(self.ask("سوف يكونُ زيدٌ حكيمًا.", "هل يكونُ زيدٌ حكيمًا؟",
                                  lexical_model=model)["status"], "UNKNOWN")
        for text in ("سوف يكونَ زيدٌ حكيمًا.", "سوف كان زيدٌ حكيمًا.", "سُوفَ يكونُ زيدٌ حكيمًا."):
            self.assertEqual(self.read(text, lexical_model=model)["claims"], [])

    def test_light_inna_and_continuative_prayer_are_not_silently_resolved(self):
        self.assertEqual(self.read("إن زيدًا حكيمٌ.")["claims"], [])
        report = self.read("لا زال زيدٌ حكيمًا.")
        self.assertEqual(report["claims"], [])
        self.assertIn("CONTINUATIVE_LA_PERF_PRAYER_OR_ASSERTION_REQUIRES_CONTEXT", obligations(report))
        self.assertEqual(self.read("ما زال زيدٌ حكيمًا.")["status"], "LICENSED_DISCOURSE")

    def test_operator_person_voice_and_polysemous_sense_stay_in_the_frame(self):
        witness = (b"(9:1:1:1)\tkunotu\tV\tSTEM|POS:V|PERF|LEM:kaAna|ROOT:kwn|1S\n"
                   b"(9:2:1:1)\tZun~a\tV\tSTEM|POS:V|PERF|PASS|LEM:Zan~a|ROOT:Znn|3MS\n"
                   b"(9:3:1:1)\tra>aY\tV\tSTEM|POS:V|PERF|LEM:ra>aY|ROOT:r>y|3MS\n"
                   b"(9:4:1:1)\tra>aY\tV\tSTEM|POS:V|PERF|LEM:ra>aY|ROOT:r>y|3MS\n"
                   b"(9:4:1:2)\tka\tPRON\tSUFFIX|PRON:2MS\n")
        model = learn_qac_lexicon(TRAINING + witness)
        for text, reason in (("كُنْتُ زيدٌ حكيمًا.", "CONSTRUCTION_CONFLICT"),
                             ("ظُنَّ زيدٌ سالمًا حكيمًا.", "PASSIVE_OPERATOR_REQUIRES_DIFFERENT_ARGUMENT_FRAME"),
                             ("رَأَى زيدٌ سالمًا حكيمًا.", "POLYSEMOUS_OPERATOR_SENSE_REQUIRES_INDEPENDENT_CONTEXT")):
            with self.subTest(text=text):
                report = self.read(text, lexical_model=model)
                self.assertEqual(report["claims"], [])
                self.assertIn(reason, obligations(report))

    def test_accusative_carrier_requires_both_independent_forms(self):
        text = "إنَّ زيدًا حكيمٌ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        for model in (without_forms("zayodFA"), without_forms("zayodN", "zayodK")):
            self.assertEqual(self.read(text, lexical_model=model)["claims"], [])
            self.assertFalse(verify_discourse(report, lexical_model=model, context=CONTEXT)["valid"])

    def test_carrier_preserves_original_bytes_and_referent_link(self):
        text = "إنَّ زيدًا حكيمٌ."
        report = self.read(text)
        carriers = [r["nominal_case_carrier"] for o in report["occurrences"] for r in o["readings"]
                    if "nominal_case_carrier" in r]
        self.assertTrue(carriers)
        for receipt in carriers:
            raw = text.encode()
            span = receipt["carrier_span"]
            self.assertEqual(raw[span["start"]:span["end"]].decode(), "ا")
            self.assertFalse(receipt["generated_form"])
            self.assertTrue(receipt["full_form_supports"] and receipt["base_paradigm_supports"])
        self.assertTrue(any(r.get("written_surface") == "زيدًا" and r["bound_entity_id"] == "zayd"
                            for a in accepted(report) for r in a["references"]))

    def test_nested_idafa_has_two_distinct_genitive_edges(self):
        report = self.read("كِتَابُ طالبِ زيدٍ جديدٌ.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        for row in accepted(report):
            edges = [r for r in row["relations"] if r["kind"] == "idafa"]
            self.assertEqual(len(edges), 2)
            self.assertNotEqual(edges[0]["head_span"], edges[1]["head_span"])
            self.assertTrue(all(not e["ownership_asserted"] for e in edges))
            self.assertEqual([a["inflected_case"] for a in row["assignments"]
                              if a["role"] == "idafa_complement"], ["jarr", "jarr"])
        self.assertNotEqual(self.read("كِتَابٌ طالبِ زيدٍ جديدٌ.")["status"], "LICENSED_DISCOURSE")

    def test_naat_keeps_head_agreement_and_qualification(self):
        text = "كِتَابٌ جديدٌ واسعٌ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertTrue(all(any(a["actual_role"] == "naat" and a["inflected_case"] == "raf"
                               for a in row["assignments"]) for row in accepted(report)))
        self.assertTrue(report["claims"][0]["restriction"])
        self.assertEqual(self.read("كِتَابٌ حكيمةٌ واسعٌ.")["claims"], [])

    def test_badal_requires_independent_identity_not_just_adjacent_names(self):
        text = "هذا زيدٌ حكيمٌ."
        self.assertEqual(self.read(text)["status"], "LICENSED_DISCOURSE")
        context = deepcopy(CONTEXT)
        context["deixis"] = []
        self.assertEqual(self.read(text, context=context)["claims"], [])
        self.assertEqual(self.read("هذا سالمٌ حكيمٌ.")["claims"], [])
        self.assertEqual(self.read("زيدٌ سالمٌ حكيمٌ.")["claims"], [])

    def test_tawkeed_repetition_and_attested_attached_return(self):
        for text in ("زيدٌ زيدٌ حكيمٌ.", "زيدٌ نفسُه حكيمٌ."):
            report = self.read(text)
            self.assertEqual(report["status"], "LICENSED_DISCOURSE")
            self.assertTrue(all(any(a["actual_role"] == "tawkeed" for a in row["assignments"])
                                for row in accepted(report)))
        self.assertEqual(self.read("زيدٌ نفسُه حكيمٌ.", lexical_model=without_forms("nafosu"))["claims"], [])

    def test_hal_is_qualified_by_event_and_cannot_become_timeless_property(self):
        report = self.read("جاء زيدٌ راكبًا.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(report["claims"][0]["restriction"][0]["kind"], "hal")
        self.assertEqual(self.ask("جاء زيدٌ راكبًا.", "هل زيدٌ راكبٌ؟")["status"], "UNKNOWN")
        self.assertEqual(self.read("جاء هندٌ راكبًا.")["claims"], [])

    def test_nisba_uses_replayed_exemplified_pair_not_any_noun(self):
        for text in ("امتلأ الإناءُ ماءً.", "اشتعل الرأسُ شيبًا."):
            report = self.read(text)
            self.assertEqual(report["status"], "LICENSED_DISCOURSE")
            self.assertTrue(any(a["actual_role"] == "tamyiz" and a["inflected_case"] == "nasb"
                                for row in accepted(report) for a in row["assignments"]))
        report = self.read("اشتعل كتابٌ يومًا.")
        self.assertEqual(report["claims"], [])
        self.assertIn("TAMYIZ_VERSUS_OTHER_NOMINAL_USE_REQUIRES_SOURCE_FRAME", obligations(report))

    def test_quantified_nominal_keeps_tamyiz_and_does_not_invent_person_binding(self):
        text = "جاء عشرون رجلًا."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(report["claims"][0]["args"][0]["kind"], "quantified_nominal")
        self.assertEqual(self.ask(text, "هل جاء عشرون رجلًا؟")["status"], "SUPPORTED")
        self.assertEqual(self.ask(text, "من جاء؟")["status"], "UNKNOWN")
        self.assertEqual(self.read(text, lexical_model=without_forms("Ei$oriyna"))["claims"], [])

    def test_spatial_and_temporal_attachment_use_actual_predicate_head(self):
        for text, role, field in (("زيدٌ كتب عندَ المكتبِ.", "place_adverb", "place"),
                                  ("كتب زيدٌ يومَ الخميسِ.", "time_adverb", "time")):
            report = self.read(text)
            self.assertEqual(report["status"], "LICENSED_DISCOURSE")
            self.assertTrue(report["claims"][0][field])
            for row in accepted(report):
                assigned = next(a for a in row["assignments"] if a["actual_role"] == role)
                self.assertEqual(assigned["inflected_case"], "nasb")
                span = assigned["head_span"]
                self.assertEqual(text.encode()[span["start"]:span["end"]].decode(), "كتب")
        self.assertEqual(self.read("زيدٌ فوقَ المكتبِ.")["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask("زيدٌ فوقَ المكتبِ.", "أين زيد؟")["status"], "UNKNOWN")

    def test_preposition_on_numeral_cannot_disappear_into_direct_object(self):
        witness = (b"(9:31:1:1)\tkataba\tV\tSTEM|POS:V|PERF|LEM:kataba|ROOT:ktb|3MS\n"
                   b"(9:31:1:2)\tka\tPRON\tSUFFIX|PRON:2MS\n")
        model = learn_qac_lexicon(TRAINING + witness)
        self.assertEqual(self.read("كتب زيدٌ عشرين كتابًا.", lexical_model=model)["status"], "LICENSED_DISCOURSE")
        report = self.read("كتب زيدٌ بعشرين كتابًا.", lexical_model=model)
        self.assertEqual(report["claims"], [])
        self.assertFalse(any(a["actual_role"] == "direct_object" and a["surface"] == "بعشرين"
                             for row in accepted(report) for a in row["assignments"]))

    def test_changed_source_context_and_receipt_fail_replay(self):
        text = "ظن زيدٌ سالمًا حكيمًا."
        report = self.read(text)
        self.assertTrue(verify_discourse(report, lexical_model=self.model, context=CONTEXT)["valid"])
        changed = deepcopy(report)
        gate = next(r for r in changed["clauses"][0]["analyses"][0]["relations"] if r["kind"] == "construction_gate")
        gate["edges"][0]["target"]["reading_id"] = gate["edges"][0]["head"]["reading_id"]
        self.assertFalse(verify_discourse(changed, lexical_model=self.model, context=CONTEXT)["valid"])
        answer = self.ask(text, "هل ظن زيدٌ سالمًا حكيمًا؟")
        self.assertTrue(verify_discourse_answer(answer, lexical_model=self.model, context=CONTEXT)["valid"])
        self.assertFalse(verify_discourse_answer(answer, text="صار سالمٌ حكيمًا.",
                                               lexical_model=self.model, context=CONTEXT)["valid"])
        context = deepcopy(CONTEXT)
        context["entities"] = [e for e in context["entities"] if e["id"] != "salim"]
        self.assertFalse(verify_discourse_answer(answer, lexical_model=self.model, context=context)["valid"])

    def test_catalog_exposes_conditional_law_and_source_scope(self):
        catalog = discourse_catalog()
        self.assertEqual(catalog["language_id"], "nabt.arabic-discourse-frames.v2")
        self.assertEqual(catalog["constructions"]["law"]["law_id"], "nabt.construction-evidence.v1")
        self.assertEqual(len(catalog["constructions"]["grammar_sources"]["rules"]), 17)
        self.assertEqual({o["family"] for o in catalog["constructions"]["operators"]},
                         {"kana", "inna", "zanna", "kada"})


if __name__ == "__main__":
    unittest.main()
