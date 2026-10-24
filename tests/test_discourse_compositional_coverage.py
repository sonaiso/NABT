"""Independent, authored boundary examples for bounded discourse composition.

The small teaching records below are explicit premises, not QAC quotations.
Expected Arabic roles and non-entailments are stated directly; these tests do
not call the production law tables to derive their expected verdicts.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse, verify_discourse_answer
from nabt.discourse_adverbs import adverb_candidates


ROOT = Path(__file__).resolve().parents[1]
TEACHING = (ROOT / "examples/discourse_training.tsv").read_bytes() + b"""\
(90:1:1:1)\tyaHozanu\tV\tSTEM|POS:V|IMPF|LEM:Hazina|ROOT:Hzn|3MS
(90:2:1:1)\tyaHozanu\tV\tSTEM|POS:V|IMPF|LEM:Hazina|ROOT:Hzn|3MP
(90:2:1:2)\twna\tPRON\tSUFFIX|PRON:3MP
(90:3:1:1)\tbaAHiv\tN\tSTEM|POS:N|LEM:baAHiv|ROOT:bHv|MS
(90:4:1:1)\tkariymN\tN\tSTEM|POS:N|LEM:kariym|ROOT:krm|MS
(90:5:1:1)\tkariymK\tN\tSTEM|POS:N|LEM:kariym|ROOT:krm|MS
"""
CONTEXT = json.loads((ROOT / "examples/discourse_context.json").read_text())


def analyses(report):
    return [a for c in report["clauses"] for a in c["analyses"]]


class DiscourseCompositionCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TEACHING, source_id="authored_composition")

    def read(self, text, **kwargs):
        return read_discourse(text, lexical_model=self.model, **kwargs)

    def test_unresolved_reference_does_not_erase_witnessed_jussive(self):
        report = self.read("لَمْ يَحْزَنُوا.")
        rows = [a for a in analyses(report) if not a["rejected_candidate"]]
        self.assertTrue(rows)
        self.assertTrue(all(a["licensed_syntax"] and not a["references_complete"] for a in rows))
        self.assertTrue(all("REFERENCE_NOT_UNIQUELY_LICENSED" in a["obligations"] for a in rows))
        mood = [a for row in rows for a in row["assignments"] if a["role"] == "imperfect_jussive"]
        self.assertTrue(mood)
        self.assertTrue(all(a["activated"] and a["inflected_case"] == "jazm" for a in mood))
        nuns = [n for o in report["occurrences"] for r in o["readings"] for n in r["nun_readings"]]
        self.assertTrue(any(n["kind"] == "radical" and n["span"] is not None for n in nuns))
        self.assertTrue(any(n["kind"] == "five_verb_raf" and n["span"] is None for n in nuns))
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])
        self.assertFalse(any(a["assertion_allowed"] for a in rows))
        self.assertTrue(verify_discourse(report, lexical_model=self.model)["valid"])

    def test_reference_separation_does_not_clear_case_conflict(self):
        report = self.read("لَمْ يَحْزَنُونَ.")
        self.assertTrue(analyses(report))
        self.assertFalse(any(a["licensed_syntax"] for a in analyses(report)))
        self.assertFalse(any(a["activated"] for row in analyses(report) for a in row["assignments"]))
        self.assertEqual(report["claims"], [])

    def test_unknown_predicate_construction_remains_a_syntax_obligation(self):
        report = self.read("هُوَ بَاحِث.")
        self.assertTrue(analyses(report))
        self.assertFalse(any(a["licensed_syntax"] for a in analyses(report)))
        self.assertTrue(all("PREDICATE_CONSTRUCTION_EVIDENCE_REQUIRED" in a["obligations"]
                            for a in analyses(report)))
        self.assertEqual(report["claims"], [])

    def test_unknown_reference_cannot_be_promoted_by_editing_receipt(self):
        report = self.read("هُوَ عَالِمٌ.")
        self.assertTrue(any(a["licensed_syntax"] for a in analyses(report)))
        forged = deepcopy(report)
        for row in analyses(forged):
            row["references_complete"] = True
            row["assertion_allowed"] = True
        self.assertFalse(verify_discourse(forged, lexical_model=self.model)["valid"])

    def test_attached_question_hamza_preserves_source_and_is_nonassertive(self):
        question = "أَزَيْدٌ عَالِمٌ؟"
        report = self.read(question, context=CONTEXT)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(report["claims"], [])
        relations = [r for a in analyses(report) for r in a["relations"]
                     if r["kind"] == "interrogative_prefix"]
        self.assertTrue(relations)
        raw = question.encode("utf-8")
        for relation in relations:
            prefix, remainder, parent = [relation[k] for k in ("prefix_span", "remainder_span", "parent_span")]
            self.assertEqual(raw[prefix["start"]:prefix["end"]].decode(), "أَ")
            self.assertEqual(raw[remainder["start"]:remainder["end"]].decode(), "زَيْدٌ")
            self.assertEqual(prefix["start"], parent["start"])
            self.assertEqual(prefix["end"], remainder["start"])
            self.assertEqual(remainder["end"], parent["end"])
        answer = ask_discourse("زَيْدٌ عَالِمٌ.", question, lexical_model=self.model, context=CONTEXT)
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertTrue(verify_discourse_answer(answer, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_lexical_hamza_and_competing_named_remainder_are_retained(self):
        context = deepcopy(CONTEXT)
        context["entities"] += [
            {"id": "ahmad", "name": "أحمد", "kind": "person", "gender": "masculine", "number": "singular"},
            {"id": "hamad", "name": "حمد", "kind": "person", "gender": "masculine", "number": "singular"},
        ]
        report = self.read("أَحْمَد عَالِمٌ؟", context=context)
        self.assertEqual(report["status"], "DEFER")
        viable = [a for a in analyses(report) if not a["rejected_candidate"]]
        self.assertEqual({c["args"][0] for a in viable for c in a["claims"]}, {"ahmad", "hamad"})
        self.assertEqual(report["claims"], [])

    def test_hamza_prefix_requires_its_vocalization_and_written_question_scope(self):
        for text in ("أُزَيْدٌ عَالِمٌ؟", "أَزَيْدٌ عَالِمٌ."):
            with self.subTest(text=text):
                report = self.read(text, context=CONTEXT)
                self.assertEqual(report["status"], "DEFER")
                self.assertEqual(report["claims"], [])

    def test_all_complete_question_interpretations_must_agree(self):
        question = "مَنْ كَرِيمٌ؟"
        inquiry = self.read(question, context=CONTEXT)
        self.assertEqual(inquiry["status"], "DEFER")  # the N/ADJ interpretations remain distinct
        answer = ask_discourse("زَيْدٌ كَرِيمٌ.", question, lexical_model=self.model, context=CONTEXT)
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertIsNone(answer["query"])
        self.assertEqual(answer["answer_basis"], "ALL_COMPLETE_QUERY_INTERPRETATIONS_AGREE")
        self.assertEqual([b["values"] for b in answer["bindings"]], [{"?person": "zayd"}])
        alternatives = answer["question_interpretations"]
        self.assertGreater(len(alternatives), 1)
        self.assertTrue(any(type(a["query"]["args"][0]) is dict for a in alternatives))
        self.assertTrue(any(a["query"]["args"] == ["?person"] for a in alternatives))
        for alternative in alternatives:
            self.assertEqual(alternative["status"], "SUPPORTED")
            self.assertEqual([b["values"] for b in alternative["bindings"]], [{"?person": "zayd"}])
            self.assertTrue(all(p["question_analysis_id"] == alternative["analysis_id"]
                                for p in alternative["proofs"]))
        self.assertTrue(verify_discourse_answer(answer, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_one_question_reading_cannot_lend_a_binding_to_another(self):
        # A noun predication is licensed, while the masculine ADJ alternative
        # is incompatible with Hind. The typed question cannot borrow the N
        # reading's untyped source fact as an adjective-agreement witness.
        answer = ask_discourse("هِنْد كَرِيمٌ.", "مَنْ كَرِيمٌ؟",
                               lexical_model=self.model, context=CONTEXT)
        self.assertEqual(answer["status"], "DEFER")
        self.assertIn("QUESTION_INTERPRETATION_OUTCOMES_DISAGREE", answer["missing_premises"])
        self.assertEqual({a["status"] for a in answer["question_interpretations"]}, {"SUPPORTED", "UNKNOWN"})
        self.assertEqual(answer["bindings"], [])
        self.assertEqual(answer["proofs"], [])
        self.assertEqual(answer["counterproofs"], [])

    def test_query_consensus_does_not_complete_an_unread_source(self):
        answer = ask_discourse("زَيْدٌ كَرِيمٌ. هُوَ بَاحِث.", "مَنْ كَرِيمٌ؟",
                               lexical_model=self.model, context=CONTEXT)
        self.assertEqual(answer["status"], "DEFER")
        self.assertIn("COMPLETE_SOURCE_DISCOURSE_READING", answer["missing_premises"])
        self.assertEqual(answer["proofs"], [])
        self.assertTrue(all(not a["proofs"] and a["status"] == "DEFER"
                            for a in answer["question_interpretations"]))

    def test_query_consensus_receipt_cannot_hide_a_disagreeing_alternative(self):
        answer = ask_discourse("هِنْد كَرِيمٌ.", "مَنْ كَرِيمٌ؟",
                               lexical_model=self.model, context=CONTEXT)
        forged = deepcopy(answer)
        forged["question_interpretations"] = [a for a in forged["question_interpretations"]
                                              if a["status"] == "SUPPORTED"]
        forged["status"] = "SUPPORTED"
        self.assertFalse(verify_discourse_answer(forged, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_nominal_relative_returns_to_its_own_head_without_inner_assertion(self):
        text = "هِنْد عَالِمٌ. زَيْدٌ الَّذِي هُوَ كَرِيمٌ عَالِمٌ."
        report = self.read(text, context=CONTEXT)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        relative_rows = [a for a in analyses(report) if a["frame"] == "nominal_relative_subject_predication"]
        self.assertTrue(relative_rows)
        for row in relative_rows:
            returns = [r for r in row["references"] if r["origin"] == "relative_return"]
            self.assertEqual({r["bound_entity_id"] for r in returns}, {"zayd"})
            self.assertTrue(all(r["candidate_entity_ids"] == ["zayd"] for r in returns))
        self.assertEqual({c["predicate"] for c in report["claims"]}, {"عالِم"})
        for question in ("هَلْ زَيْدٌ كَرِيمٌ؟", "هَلْ هِنْد كَرِيمٌ؟"):
            with self.subTest(question=question):
                self.assertEqual(ask_discourse(text, question, lexical_model=self.model,
                                              context=CONTEXT)["status"], "UNKNOWN")
        self.assertTrue(verify_discourse(report, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_relative_return_gender_conflict_is_not_replaced_by_context_recency(self):
        report = self.read("هِنْد عَالِمٌ. زَيْدٌ الَّذِي هِيَ كَرِيمٌ عَالِمٌ.", context=CONTEXT)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual({tuple(c["args"]) for c in report["claims"]}, {("hind",)})
        self.assertFalse(any(a["assertion_allowed"] for a in report["clauses"][-1]["analyses"]))

    def test_relative_clause_requires_its_inner_predicate_construction(self):
        report = self.read("زَيْدٌ الَّذِي هُوَ بَاحِث عَالِمٌ.", context=CONTEXT)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])
        self.assertTrue(all("PREDICATE_CONSTRUCTION_EVIDENCE_REQUIRED" in a["obligations"]
                            for a in analyses(report)))


class DiscourseTemporalCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The old T classification of ams is deliberately absent. Its N
        # identity and the primary grammar's bounded example are both needed.
        cls.raw = b"\n".join(line for line in TEACHING.splitlines() if b"\t>amosi\tT\t" not in line) + b"\n" + b"""\
(91:1:1:1)\t>amosi\tN\tSTEM|POS:N|LEM:>amos|M
(91:2:1:1)\tgadFA\tN\tSTEM|POS:N|LEM:gad|ROOT:gdw|M
(91:3:1:1)\tgadK\tN\tSTEM|POS:N|LEM:gad|ROOT:gdw|M
(91:4:1:1)\tAl\tDET\tPREFIX|Al+
(91:4:1:2)\tyawoma\tT\tSTEM|POS:T|LEM:yawom|ROOT:ywm|M
"""
        cls.model = learn_qac_lexicon(cls.raw, source_id="authored_temporal")

    def test_primary_temporal_noun_example_preserves_lexical_pos_and_qualification(self):
        text = "كَتَبَ زَيْدٌ أَمْسِ."
        report = read_discourse(text, lexical_model=self.model, context=CONTEXT)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertTrue(report["claims"])
        self.assertTrue(all(c["time"][0]["form"] == "أمس" and c["tense"] == "past"
                            for c in report["claims"]))
        rows = {r["reading_id"]: r for o in report["occurrences"] for r in o["readings"]}
        rows.update({r["reading_id"]: r for r in report["derived_readings"]})
        assigned = [x for a in analyses(report) if a["licensed_syntax"] for x in a["assignments"]
                    if x["role"] == "time_adverb"]
        self.assertTrue(assigned)
        self.assertTrue(all(rows[x["reading_id"]]["lexical_features"]["pos"] == "N" for x in assigned))
        self.assertTrue(all(x["local_case"] == "nasb" and x["inflected_case"] is None for x in assigned))
        self.assertTrue(all(rows[x["reading_id"]]["construction_premise"]["dialect"] == "Hijazi"
                            for x in assigned))
        original = [r for o in report["occurrences"] if o["surface"] == "أَمْسِ" for r in o["readings"]]
        self.assertTrue(original)
        self.assertTrue(all(r["construction"] is None for r in original))
        answer = ask_discourse(text, "هَلْ كَتَبَ زَيْدٌ؟", lexical_model=self.model, context=CONTEXT)
        self.assertEqual(answer["status"], "UNKNOWN")

    def test_future_particle_and_temporal_noun_remain_distinct_qualifiers(self):
        text = "سَوْفَ يَكْتُبُ زَيْدٌ غَدًا."
        answer = ask_discourse(text, "مَتَى سَوْفَ يَكْتُبُ زَيْدٌ؟",
                               lexical_model=self.model, context=CONTEXT)
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertEqual([b["values"]["?time"]["form"] for b in answer["bindings"]], ["غدا"])
        self.assertEqual(ask_discourse(text, "هَلْ يَكْتُبُ زَيْدٌ غَدًا؟",
                         lexical_model=self.model, context=CONTEXT)["status"], "UNKNOWN")

    def test_medial_witnessed_time_qualifies_its_whole_predication(self):
        text = "زَيْدٌ الْيَوْمَ عَالِمٌ."
        report = read_discourse(text, lexical_model=self.model, context=CONTEXT)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertTrue(all(c["time"][0]["form"] == "اليوم" for c in report["claims"]))
        self.assertEqual(ask_discourse(text, "هَلْ زَيْدٌ عَالِمٌ؟",
                         lexical_model=self.model, context=CONTEXT)["status"], "UNKNOWN")

    def test_repeated_adverb_attestations_keep_supports_without_duplicate_alternatives(self):
        candidates = adverb_candidates("الْيَوْمَ", lexical_model=self.model)
        self.assertEqual(len(candidates), 1)
        stem_supports = [s for s in candidates[0]["supports"] if s["locator"][3] == 2]
        self.assertEqual({tuple(s["locator"]) for s in stem_supports}, {(1, 20, 1, 2), (91, 4, 1, 2)})

    def test_temporal_examples_do_not_turn_nouns_into_complete_predicates(self):
        for text in ("زَيْدٌ أَمْسِ.", "زَيْدٌ غَدًا.", "أَمْسِ."):
            with self.subTest(text=text):
                report = read_discourse(text, lexical_model=self.model, context=CONTEXT)
                self.assertEqual(report["status"], "DEFER")
                self.assertEqual(report["claims"], [])

    def test_hijazi_temporal_reading_does_not_replace_other_dialect_or_vowel_possibilities(self):
        for form in ("أَمْسَ", "أَمْسُ", "أمس"):
            with self.subTest(form=form):
                report = read_discourse("كَتَبَ زَيْدٌ " + form + ".", lexical_model=self.model, context=CONTEXT)
                self.assertEqual(report["status"], "DEFER")
                self.assertEqual(report["claims"], [])
                self.assertFalse(any(r.get("construction_premise", {}).get("rule") == "temporal_ams_built"
                                     for r in report["derived_readings"]))

    def test_temporal_reading_loses_authority_when_lexical_source_is_withdrawn(self):
        without_examples = b"\n".join(line for line in self.raw.splitlines()
                                       if not line.startswith((b"(91:1:", b"(91:2:", b"(91:3:"))) + b"\n"
        model = learn_qac_lexicon(without_examples, source_id="authored_temporal")
        report = read_discourse("كَتَبَ زَيْدٌ أَمْسِ.", lexical_model=self.model, context=CONTEXT)
        self.assertFalse(verify_discourse(report, lexical_model=model, context=CONTEXT)["valid"])
        self.assertEqual(read_discourse("كَتَبَ زَيْدٌ أَمْسِ.", lexical_model=model, context=CONTEXT)["claims"], [])

    def test_final_time_reading_preserves_an_independent_nominal_object_reading(self):
        folder = ROOT / "evidence/arabic_coverage/temporal_ambiguity_review_v1"
        model = learn_qac_lexicon((folder / "source.tsv").read_bytes(), source_id="authored_time_ambiguity")
        context = json.loads((folder / "context.json").read_text())
        text = "كَتَبَ زَيْدٌ الْيَوْمَ."
        report = read_discourse(text, lexical_model=model, context=context)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])
        complete = [a for a in analyses(report) if a["licensed_syntax"] and a["references_complete"]
                    and not a["rejected_candidate"]]
        self.assertTrue(any(c["args"] == ["zayd"] and c["time"] for a in complete for c in a["claims"]))
        self.assertTrue(any(c["args"] == ["zayd", "alyawm"] and not c["time"]
                            for a in complete for c in a["claims"]))
        answer = ask_discourse(text, "مَتَى كَتَبَ زَيْدٌ؟", lexical_model=model, context=context)
        self.assertEqual(answer["status"], "DEFER")
        self.assertEqual(answer["proofs"], [])

    def test_time_lexeme_alone_does_not_manufacture_a_nominal_competitor(self):
        raw = (ROOT / "examples/discourse_training.tsv").read_bytes() + b"""\
(92:1:1:1)\tkataba\tV\tSTEM|POS:V|PERF|LEM:kataba|ROOT:ktb|3MS
(92:1:1:2)\thu\tPRON\tSUFFIX|PRON:3MS
"""
        model = learn_qac_lexicon(raw, source_id="authored_t_only")
        report = read_discourse("كَتَبَ زَيْدٌ الْيَوْمَ.", lexical_model=model, context=CONTEXT)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertTrue(all(c["args"] == ["zayd"] and c["time"] for c in report["claims"]))
        self.assertFalse(any(a["frame"] == "active_verb_subject_object" for a in analyses(report)))

    def test_unresolved_nominal_competitor_is_not_discarded_for_time_reading(self):
        folder = ROOT / "evidence/arabic_coverage/temporal_ambiguity_review_v1"
        model = learn_qac_lexicon((folder / "source.tsv").read_bytes(), source_id="authored_time_ambiguity")
        report = read_discourse("كَتَبَ زَيْدٌ الْيَوْمَ.", lexical_model=model, context=CONTEXT)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])
        self.assertTrue(any(a["frame"] == "active_verb_subject_object" and not a["references_complete"]
                            for a in analyses(report)))


if __name__ == "__main__":
    unittest.main()
