"""Post-review regressions for composition, separate from frozen transfer gold.

These authored lexical premises contain neither dependency labels nor answers.
They exercise different content words from the construction evaluation, source
withdrawal, contrary case marks, restriction preservation, and exact replay.
The tests are development regressions, not a new blind linguistic evaluation.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon, lookup_key
from nabt.discourse import read_discourse, ask_discourse, verify_discourse


ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/construction_training.tsv").read_bytes() + b"\n" + b"""\
(20:1:1:1)\tbaAbN\tN\tSTEM|POS:N|LEM:baAb|ROOT:bwb|MS
(20:2:1:1)\tbaAbK\tN\tSTEM|POS:N|LEM:baAb|ROOT:bwb|MS
(20:3:1:1)\tbaAbFA\tN\tSTEM|POS:N|LEM:baAb|ROOT:bwb|MS
(20:4:1:1)\tmar~a\tV\tSTEM|POS:V|PERF|LEM:mar~a|ROOT:mrr|3MS
(20:5:1:1)\tnafosi\tN\tSTEM|POS:N|LEM:nafos|ROOT:nfs|FS
(20:5:1:2)\thi\tPRON\tSUFFIX|PRON:3MS
(20:6:1:1)\tnafosu\tN\tSTEM|POS:N|LEM:nafos|ROOT:nfs|FS
(20:6:1:2)\thaA\tPRON\tSUFFIX|PRON:3FS
(20:7:1:1)\tkataba\tV\tSTEM|POS:V|PERF|LEM:kataba|ROOT:ktb|3MS
(20:7:1:2)\thu\tPRON\tSUFFIX|PRON:3MS
(20:8:1:1)\tniSofN\tN\tSTEM|POS:N|LEM:niSof|ROOT:nSf|MS
(20:9:1:1)\tniSofK\tN\tSTEM|POS:N|LEM:niSof|ROOT:nSf|MS
(20:10:1:1)\tniSofFA\tN\tSTEM|POS:N|LEM:niSof|ROOT:nSf|MS
(20:11:1:1)\tniSofa\tN\tSTEM|POS:N|LEM:niSof|ROOT:nSf|MS
(20:11:1:2)\thu\tPRON\tSUFFIX|PRON:3MS
(20:12:1:1)\tTaAba\tV\tSTEM|POS:V|PERF|LEM:TaAba|ROOT:Tyb|3MS
"""
CONTEXT = json.loads((ROOT / "examples/construction_context.json").read_text())
next(e for e in CONTEXT["entities"] if e["id"] == "desk")["kind"] = "place"
CONTEXT["entities"].append({"id": "door", "name": "باب", "gender": "masculine",
                            "number": "singular", "kind": "place"})


def complete(report):
    return [a for c in report["clauses"] for a in c["analyses"]
            if a["licensed_syntax"] and a["references_complete"] and not a["rejected_candidate"]]


def without_lemma(lemma):
    needle = ("|LEM:" + lemma + "|").encode()
    return learn_qac_lexicon(b"\n".join(line for line in TRAINING.splitlines() if needle not in line) + b"\n")


class ConstructionCoverageCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def read(self, text, **kwargs):
        return read_discourse(text, lexical_model=kwargs.pop("lexical_model", self.model),
                              context=kwargs.pop("context", CONTEXT), **kwargs)

    def ask(self, text, question):
        return ask_discourse(text, question, lexical_model=self.model, context=CONTEXT)

    def test_preposition_and_inner_idafa_have_distinct_source_heads(self):
        text = "يكتب زيدٌ في بابِ المكتبِ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "هل " + text[:-1] + "؟")["status"], "SUPPORTED")
        for row in complete(report):
            outer = next(a for a in row["assignments"] if a["role"] == "preposition_object")
            inner = next(a for a in row["assignments"] if a["role"] == "idafa_complement")
            self.assertEqual((outer["inflected_case"], inner["inflected_case"]), ("jarr", "jarr"))
            raw = text.encode()
            self.assertEqual(raw[outer["head_span"]["start"]:outer["head_span"]["end"]].decode(), "في")
            self.assertEqual(inner["head_span"], outer["span"])
            self.assertTrue(any(r["kind"] == "preposition_object" for r in row["relations"]))
            self.assertFalse(any(r.get("ownership_asserted") for r in row["relations"]))
        self.assertTrue(verify_discourse(report, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_prepositional_naat_stays_on_the_same_qualified_claim(self):
        text = "يكتب زيدٌ في المكتبِ الجديدِ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "هل يكتب زيدٌ في المكتبِ الجديدِ؟")["status"], "SUPPORTED")
        self.assertEqual(self.ask(text, "هل يكتب زيدٌ في المكتبِ؟")["status"], "UNKNOWN")
        for claim in report["claims"]:
            self.assertEqual(claim["place"], ["desk"])
            self.assertTrue(any(q["kind"] == "naat" and q["target"] == "desk" and
                                lookup_key(q["predicate"]) == "جديد" for q in claim["restriction"]))

    def test_composed_preposition_does_not_overrule_case_or_vocalization(self):
        for text in ("يكتب زيدٌ في بابُ المكتبِ.", "يكتب زيدٌ في بابِ المكتبُ.",
                     "يكتب زيدٌ في المكتبِ الجديدُ.", "يكتب زيدٌ فُي المكتبِ الجديدِ."):
            with self.subTest(text=text):
                self.assertFalse(complete(self.read(text)))
                self.assertEqual(self.read(text)["claims"], [])

    def test_composed_idafa_does_not_drop_tanwin_or_article_restrictions(self):
        for text in ("يكتب زيدٌ في بابٍ المكتبِ.", "يكتب زيدٌ في البابِ المكتبِ."):
            with self.subTest(text=text):
                self.assertFalse(complete(self.read(text)))

    def test_prepositional_named_context_does_not_replace_lexical_source(self):
        report = self.read("يكتب زيدٌ في بابِ المكتبِ.", lexical_model=without_lemma("baAb"))
        self.assertFalse(complete(report))
        self.assertEqual(report["claims"], [])

    def test_literal_place_requires_its_independent_context_premise(self):
        context = deepcopy(CONTEXT)
        next(e for e in context["entities"] if e["id"] == "desk")["kind"] = "thing"
        report = self.read("يكتب زيدٌ في المكتبِ الجديدِ.", context=context)
        self.assertEqual(report["claims"], [])
        self.assertFalse(complete(report))

    def test_complex_np_production_does_not_duplicate_atomic_named_place_debt(self):
        model = learn_qac_lexicon((ROOT / "examples/discourse_training.tsv").read_bytes())
        context = json.loads((ROOT / "examples/discourse_context.json").read_text())
        text = "زيد عالم في مكة."
        report = read_discourse(text, lexical_model=model, context=context)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertTrue(complete(report))
        self.assertFalse(any(a["frame"] == "composed_predication_with_literal_place"
                             for c in report["clauses"] for a in c["analyses"]))
        answer = ask_discourse(text, "هل زيد عالم؟", lexical_model=model, context=context)
        self.assertEqual(answer["status"], "UNKNOWN")

    def test_hal_and_final_time_both_survive_without_unqualified_projection(self):
        text = "جاء زيدٌ راكبًا أمسِ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "هل جاء زيدٌ راكبًا أمسِ؟")["status"], "SUPPORTED")
        for question in ("هل جاء زيدٌ أمسِ؟", "هل زيدٌ راكبٌ؟"):
            with self.subTest(question=question):
                self.assertEqual(self.ask(text, question)["status"], "UNKNOWN")
        for claim in report["claims"]:
            self.assertEqual([lookup_key(t["lemma"]) for t in claim["time"]], ["أمس"])
            self.assertTrue(any(q["kind"] == "hal" and q["owner"] == "zayd" for q in claim["restriction"]))
        for row in complete(report):
            hal = next(a for a in row["assignments"] if a["role"] == "hal")
            adverb = next(a for a in row["assignments"] if a["role"] == "time_adverb")
            self.assertEqual(hal["head_span"], adverb["head_span"])
            # A lexical T label did not manufacture a declension proof.
            self.assertIsNone(adverb["inflected_case"])

    def test_final_time_requires_exact_source_form_and_source_availability(self):
        self.assertFalse(complete(self.read("جاء زيدٌ راكبًا أمسُ.")))
        report = self.read("جاء زيدٌ راكبًا أمسِ.", lexical_model=without_lemma(">amos"))
        self.assertFalse(complete(report))
        self.assertEqual(report["claims"], [])

    def test_emphasis_is_preserved_as_a_claim_qualification(self):
        text = "جاء زيدٌ نفسُه."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "هل جاء زيدٌ نفسُه؟")["status"], "SUPPORTED")
        self.assertEqual(self.ask(text, "هل جاء زيدٌ؟")["status"], "UNKNOWN")
        self.assertTrue(all(any(q["kind"] == "tawkeed" and q["owner"] == "zayd"
                                for q in claim["restriction"]) for claim in report["claims"]))

    def test_emphasis_still_requires_case_and_same_pronominal_return(self):
        for text in ("جاء زيدٌ نفسِه.", "جاء زيدٌ نفسُها.", "جاء هندٌ نفسُه."):
            with self.subTest(text=text):
                self.assertFalse(complete(self.read(text)))
                self.assertEqual(self.read(text)["claims"], [])
        self.assertFalse(complete(self.read("جاء زيدٌ نفسُه.", lexical_model=without_lemma("nafos"))))

    def test_attached_preposition_keeps_emphasis_and_an_unspecified_relation(self):
        text = "مرَّ سالمٌ بزيدٍ نفسِهِ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "هل مرَّ سالمٌ بزيدٍ نفسِهِ؟")["status"], "SUPPORTED")
        for claim in report["claims"]:
            self.assertEqual(claim["place"], [])
            self.assertTrue(any(q["kind"] == "prepositional" and q["semantic_relation"] == "unspecified"
                                and q["object"] == "zayd" for q in claim["restriction"]))
            self.assertTrue(any(q["kind"] == "tawkeed" and q["owner"] == "zayd"
                                for q in claim["restriction"]))
        for row in complete(report):
            emphasis = next(a for a in row["assignments"] if a["role"] == "tawkeed")
            nominal = next(a for a in row["assignments"] if a["role"] == "preposition_object")
            self.assertEqual(emphasis["inflected_case"], "jarr")
            self.assertEqual(emphasis["head_span"], nominal["span"])
            edge = next(r for r in row["relations"] if r["kind"] == "tawkeed")
            self.assertEqual(edge["head_span"], nominal["span"])
            governed = next(r for r in row["relations"] if r["kind"] == "preposition_object")
            self.assertEqual(governed["dependent_span"], nominal["span"])
            self.assertEqual(governed["head_span"]["end"], nominal["span"]["start"])
            raw = text.encode()
            written = governed["written_token_span"]
            self.assertEqual(raw[written["start"]:written["end"]].decode(), "بزيدٍ")
            self.assertEqual(raw[nominal["span"]["start"]:nominal["span"]["end"]].decode(), "زيدٍ")

    def test_attached_preposition_cannot_disappear_or_bypass_evidence(self):
        for text in ("مرَّ سالمٌ بَزيدٍ نفسِهِ.", "مرَّ سالمٌ بزيدٌ نفسِهِ.",
                     "مرَّ سالمٌ بزيدٍ نفسُه."):
            with self.subTest(text=text):
                self.assertFalse(complete(self.read(text)))
                self.assertEqual(self.read(text)["claims"], [])
        self.assertFalse(complete(self.read("مرَّ سالمٌ بزيدٍ نفسِهِ.", lexical_model=without_lemma("zayod"))))

    def test_attached_preposition_and_idafa_keep_disjoint_case_target(self):
        report = self.read("مرَّ سالمٌ ببابِ المكتبِ.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        for row in complete(report):
            outer = next(a for a in row["assignments"] if a["role"] == "preposition_object")
            self.assertLessEqual(outer["head_span"]["end"], outer["span"]["start"])
            self.assertEqual(outer["surface"], "بابِ")
            self.assertEqual(outer["inflected_case"], "jarr")
            inner = next(a for a in row["assignments"] if a["role"] == "idafa_complement")
            self.assertEqual(inner["head_span"], outer["span"])
            self.assertEqual(next(r for r in row["relations"] if r["kind"] == "idafa")["head_span"], outer["span"])
        self.assertEqual(self.read("مرَّ سالمٌ ببابٍ المكتبِ.")["claims"], [])

    def test_prefixed_nominal_head_is_shared_by_naat_and_its_genitive_assignment(self):
        text = "مرَّ سالمٌ بزيدٍ الجديدِ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        for analysis in complete(report):
            head = next(a for a in analysis["assignments"] if a["role"] == "preposition_object")
            dependent = next(a for a in analysis["assignments"] if a["role"] == "naat")
            self.assertEqual(dependent["head_span"], head["span"])
            self.assertEqual((head["inflected_case"], dependent["inflected_case"]), ("jarr", "jarr"))
            self.assertEqual(next(r for r in analysis["relations"] if r["kind"] == "naat")["head_span"], head["span"])
        changed = deepcopy(report)
        for clause in changed["clauses"]:
            for analysis in clause["analyses"]:
                written = next((r["written_token_span"] for r in analysis["relations"]
                                if r["kind"] == "preposition_object" and "written_token_span" in r), None)
                if written is not None:
                    for assignment in analysis["assignments"]:
                        if assignment["role"] == "naat":
                            assignment["head_span"] = written
        self.assertFalse(verify_discourse(changed, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_replay_rejects_erased_qualification_or_changed_reference_context(self):
        report = self.read("يكتب زيدٌ في المكتبِ الجديدِ.")
        changed = deepcopy(report)
        changed["claims"][0]["restriction"] = []
        self.assertFalse(verify_discourse(changed, lexical_model=self.model, context=CONTEXT)["valid"])
        context = deepcopy(CONTEXT)
        context["entities"] = [e for e in context["entities"] if e["id"] != "desk"]
        self.assertFalse(verify_discourse(report, lexical_model=self.model, context=context)["valid"])

    def test_negative_matrix_does_not_negate_or_assert_embedded_property(self):
        text = "مَا ظَنَّ زيدٌ سالمًا حكيمًا."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "أَ مَا ظَنَّ زيدٌ سالمًا حكيمًا؟")["status"], "SUPPORTED")
        for claim in report["claims"]:
            self.assertEqual(claim["predicate_kind"], "scoped")
            self.assertFalse(claim["positive"])
            scope = next(q for q in claim["restriction"] if q["kind"] == "operator_scope")
            self.assertTrue(scope["embedded"][0]["positive"])
            self.assertFalse(scope["embedded_fact_projection"])
        for question in ("هل سالمٌ حكيمٌ؟", "هل ليس سالمٌ حكيمًا؟"):
            with self.subTest(question=question):
                self.assertEqual(self.ask(text, question)["status"], "UNKNOWN")
        self.assertNotEqual(self.ask(text, "هل ظَنَّ زيدٌ سالمًا حكيمًا؟")["status"], "SUPPORTED")

    def test_negative_matrix_keeps_source_shape_sense_and_complete_frame_gates(self):
        for text in ("مُا ظَنَّ زيدٌ سالمًا حكيمًا.", "لا ظَنَّ زيدٌ سالمًا حكيمًا.",
                     "مَا ظَنَّ زيدٌ سالمًا.", "مَا عَلِمَ زيدٌ سالمًا حكيمًا.",
                     "مَا حَسِبَ زيدٌ سالمًا حكيمًا."):
            with self.subTest(text=text):
                self.assertFalse(complete(self.read(text)))
                self.assertEqual(self.read(text)["claims"], [])

    def test_bayan_and_badal_candidates_do_not_merge_context_entities(self):
        context = deepcopy(CONTEXT)
        next(e for e in context["entities"] if e["id"] == "student")["name"] = "الطالب"
        text = "جاء الطالبُ زيدٌ."
        report = self.read(text, context=context)
        relations = [r for c in report["clauses"] for a in c["analyses"] for r in a["relations"]
                     if r["kind"] in ("badal", "bayan")]
        self.assertEqual({r["kind"] for r in relations}, {"badal", "bayan"})
        self.assertTrue(all(r["evidence_status"] == "CANDIDATE_ONLY" for r in relations))
        self.assertTrue(all(not r["identity_preserved"] for r in relations))
        self.assertTrue(all((r["head_entity"], r["dependent_entity"]) == ("student", "zayd") for r in relations))
        self.assertFalse(complete(report))
        self.assertEqual(report["claims"], [])
        self.assertTrue(all(not a["claims"] for c in report["clauses"] for a in c["analyses"]))

    def test_part_substitution_candidates_do_not_restate_event_about_whole(self):
        context = deepcopy(CONTEXT)
        next(e for e in context["entities"] if e["id"] == "book")["name"] = "الكتاب"
        text = "كتب زيدٌ الكتابَ نِصفَهُ."
        report = self.read(text, context=context)
        analyses = [a for c in report["clauses"] for a in c["analyses"]]
        relations = [r for a in analyses for r in a["relations"] if r["kind"] in ("badal_part", "badal_association")]
        self.assertEqual({r["kind"] for r in relations}, {"badal_part", "badal_association"})
        self.assertTrue(all(r["evidence_status"] == "CANDIDATE_ONLY" and r["part_entity"] is None for r in relations))
        self.assertTrue(all(not r["identity_preserved"] and not r["whole_event_projection"] for r in relations))
        self.assertTrue(all(not a["claims"] for a in analyses))
        self.assertFalse(complete(report))
        self.assertEqual(report["claims"], [])
        answer = ask_discourse(text, "هل كتب زيدٌ الكتابَ؟", lexical_model=self.model, context=context)
        self.assertEqual(answer["status"], "DEFER")
        self.assertEqual(answer["proofs"], [])
        self.assertIn("COMPLETE_SOURCE_DISCOURSE_READING", answer["missing_premises"])

    def test_sharaa_requires_its_separate_source_and_preserves_onset_scope(self):
        text = "شَرَعَ سالمٌ يكتبُ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "هل شَرَعَ سالمٌ يكتبُ؟")["status"], "SUPPORTED")
        self.assertEqual(self.ask(text, "هل سالمٌ يكتبُ؟")["status"], "UNKNOWN")
        for row in complete(report):
            support = next(s for s in row["supports"] if s.get("rule") == "inception_sharaa")
            self.assertEqual(support["passage"]["source_id"], "sabban")
            self.assertEqual(support["passage"]["source_layer"], "SABBAN_COMMENTARY_EXPLICIT_PROPOSED_ADDITION")
        for claim in report["claims"]:
            self.assertEqual(claim["predicate_kind"], "scoped")
            scope = next(q for q in claim["restriction"] if q["kind"] == "operator_scope")
            self.assertEqual(scope["sense"], "inception")
            self.assertFalse(scope["embedded_fact_projection"])

    def test_sharaa_extension_does_not_license_an_or_contrary_mood_or_agreement(self):
        for text in ("شَرَعَ سالمٌ أن يكتبَ.", "شَرَعَ سالمٌ يكتبَ.",
                     "شَرَعَ سالمًا يكتبُ.", "شَرَعَ هندٌ يكتبُ.", "شَرَعَ سالمٌ."):
            with self.subTest(text=text):
                self.assertFalse(complete(self.read(text)))
                self.assertEqual(self.read(text)["claims"], [])

    def test_taba_nafs_frame_is_acquired_from_quoted_ashmuni_passage(self):
        text = "طاب سالمٌ نفسًا."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.ask(text, "هل طاب سالمٌ نفسًا؟")["status"], "SUPPORTED")
        self.assertEqual(self.ask(text, "هل طاب سالمٌ؟")["status"], "UNKNOWN")
        for row in complete(report):
            relation = next(r for r in row["relations"] if r["kind"] == "tamyiz")
            self.assertEqual(relation["source_construction_example"]["source_rule"], "tamyiz_taba_nafs")
            support = next(s for s in row["supports"] if s.get("rule") == "tamyiz_taba_nafs")
            self.assertEqual(support["passage"]["source_layer"], "ASHMUNI_EXPOSITION_QUOTED_WITHIN_SABBAN_DIGITAL_SOURCE")
        self.assertTrue(all(any(q["kind"] == "tamyiz" for q in c["restriction"]) for c in report["claims"]))

    def test_new_nisba_frame_does_not_promote_any_noun_or_override_lexical_source(self):
        for text in ("طاب سالمٌ ماءً.", "طاب سالمٌ نفسٌ.", "جاء سالمٌ نفسًا."):
            with self.subTest(text=text):
                self.assertFalse(complete(self.read(text)))
                self.assertEqual(self.read(text)["claims"], [])
        self.assertFalse(complete(self.read("طاب سالمٌ نفسًا.", lexical_model=without_lemma("nafos"))))


if __name__ == "__main__":
    unittest.main()
