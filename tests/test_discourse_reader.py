"""End-to-end regressions for bounded, source-replayed discourse contracts.

The teaching corpus is authored; these tests are not the independent transfer
measurement. They exercise source withdrawal, correlated ambiguity, scope,
qualifiers and query certificates rather than reimplementing the Lean tables.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import (ask_discourse, read_discourse, verify_discourse,
                            verify_discourse_answer)
from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/discourse_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/discourse_context.json").read_text())


def accepted_analyses(report):
    return [a for c in report["clauses"] if c["status"] == "LICENSED"
            for a in c["analyses"] if not a["rejected_candidate"] and a["licensed_syntax"] and a["references_complete"]]


def claims(report):
    return [{k: v for k, v in c.items() if k not in ("claim_id", "proofs")} for c in report["claims"]]


class DiscourseReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def read(self, text, **kwargs):
        return read_discourse(text, lexical_model=kwargs.pop("lexical_model", self.model),
                               context=kwargs.pop("context", CONTEXT), **kwargs)

    def ask(self, text, question, **kwargs):
        return ask_discourse(text, question, lexical_model=kwargs.pop("lexical_model", self.model),
                              context=kwargs.pop("context", CONTEXT), **kwargs)

    def test_speaker_to_predication_to_named_question_and_replay(self):
        answer = self.ask("أنا عالم.", "هل زيد عالم؟")
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertTrue(answer["proofs"])
        self.assertTrue(verify_discourse_answer(answer, lexical_model=self.model, context=CONTEXT)["valid"])
        self.assertEqual(answer["world_truth"], "NOT_ESTABLISHED")

    def test_context_is_not_a_lexical_or_answer_dictionary(self):
        self.assertEqual(self.read("زيد زلفخ.")["claims"], [])
        for key in ("facts", "case", "root", "answers", "roles"):
            with self.subTest(key=key), self.assertRaises(NabtError):
                self.read("زيد عالم.", context={**CONTEXT, key: []})

    def test_unwitnessed_morphology_never_comes_from_name_traits(self):
        report = self.read("زيد عالم.", lexical_model=None)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])

    def test_closed_antecedent_loop(self):
        answer = self.ask("زيد عالم. هو كاتب.", "هل زيد كاتب؟")
        self.assertEqual(answer["status"], "SUPPORTED")
        report = self.read("زيد عالم. هو كاتب.")
        reference = accepted_analyses(report)[-1]["references"][0]
        self.assertEqual(reference["origin"], "antecedent")
        self.assertEqual(reference["candidate_entity_ids"], ["zayd"])
        self.assertEqual(reference["bound_entity_id"], "zayd")

    def test_default_open_universe_does_not_resolve_single_previous_candidate(self):
        context = deepcopy(CONTEXT)
        context.pop("closed_reference_scope")
        report = self.read("زيد عالم. هو كاتب.", context=context)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(len(report["claims"]), 1)
        self.assertNotEqual(self.ask("زيد عالم. هو كاتب.", "هل زيد كاتب؟", context=context)["status"], "SUPPORTED")

    def test_unknown_competitor_is_not_removed_or_replaced_by_nearest(self):
        context = deepcopy(CONTEXT)
        context["entities"][1]["gender"] = "unknown"
        report = self.read("هند عالم. زيد عالم. هو كاتب.", context=context)
        last = report["clauses"][-1]
        self.assertEqual(last["status"], "DEFER")
        self.assertTrue(any(set(r["candidate_entity_ids"]) == {"hind", "zayd"}
                            for a in last["analyses"] for r in a["references"]))
        self.assertFalse(any(c["predicate"] == "كَاتِب" for c in report["claims"]))

    def test_homonymous_declared_names_remain_ambiguous(self):
        context = deepcopy(CONTEXT)
        context["entities"].append({"id": "other_zayd", "name": "زيد", "gender": "masculine", "number": "singular", "kind": "person"})
        report = self.read("زيد عالم.", context=context)
        self.assertEqual(report["claims"], [])
        self.assertEqual(report["status"], "DEFER")

    def test_quotation_is_not_antecedent_or_assertion(self):
        report = self.read("«زيد عالم». هو كاتب.")
        self.assertEqual(report["claims"], [])
        self.assertEqual(report["clauses"][0]["force"], "QUOTED")

    def test_question_does_not_introduce_asserted_antecedent(self):
        report = self.read("هل زيد عالم؟ هو كاتب.")
        self.assertEqual(report["claims"], [])
        self.assertEqual(report["status"], "DEFER")

    def test_demonstrative_requires_explicit_deixis_and_replays_it(self):
        report = self.read("هذا عالم.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(report["claims"][0]["args"], ["zayd"])
        context = deepcopy(CONTEXT)
        context["deixis"] = []
        self.assertEqual(self.read("هذا عالم.", context=context)["claims"], [])
        self.assertFalse(verify_discourse(report, lexical_model=self.model, context=context)["valid"])

    def test_demonstrative_dual_is_not_declared_built(self):
        report = self.read("هذان")
        readings = [r for o in report["occurrences"] for r in o["readings"] if r["lexical_features"].get("pos") == "DEM"]
        self.assertTrue(readings)
        self.assertTrue(all(r["construction"] == "inflected" and r["class_candidates"] == [2] for r in readings))

    def test_inna_built_subject_has_local_accusative(self):
        report = self.read("إنَّ هذا عالم.")
        rows = [a for analysis in accepted_analyses(report) for a in analysis["assignments"] if a["role"] == "inna_subject"]
        self.assertTrue(rows)
        self.assertTrue(all(a["local_case"] == "nasb" and a["inflected_case"] is None for a in rows))
        self.assertEqual(self.ask("إنَّ هذا عالم.", "هل زيد عالم؟")["status"], "SUPPORTED")

    def test_conditional_in_is_not_automatically_inna(self):
        report = self.read("إن هذا عالم.")
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])

    def test_wh_subject_is_explicit_variable_not_known_answer(self):
        answer = self.ask("زيد عالم.", "من عالم؟")
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertEqual([b["values"] for b in answer["bindings"]], [{"?person": "zayd"}])
        self.assertEqual(answer["query"]["args"], ["?person"])

    def test_where_uses_source_place_and_context_kind(self):
        answer = self.ask("زيد في مكة.", "أين زيد؟")
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertEqual(answer["bindings"][0]["values"], {"?place": "makkah"})
        context = deepcopy(CONTEXT)
        context["entities"][3]["kind"] = "unknown"
        self.assertEqual(self.ask("زيد في مكة.", "أين زيد؟", context=context)["status"], "DEFER")

    def test_time_adverb_requires_a_full_predicate(self):
        self.assertEqual(self.read("زيد أمس.")["claims"], [])
        answer = self.ask("كتب زيد أمس.", "متى كتب زيد؟")
        self.assertEqual(answer["status"], "SUPPORTED")
        value = answer["bindings"][0]["values"]["?time"]
        self.assertEqual(value["form"], "أمس")
        self.assertFalse(value["source_article"])

    def test_qualification_is_not_erased_to_match_an_unqualified_question(self):
        for text, question in (("كتب زيد أمس.", "هل كتب زيد؟"),
                               ("زيد عالم في مكة.", "هل زيد عالم؟"),
                               ("سوف يكتب زيد.", "هل يكتب زيد؟")):
            with self.subTest(text=text):
                self.assertEqual(self.ask(text, question)["status"], "UNKNOWN")

    def test_lam_negation_yields_signed_past_claim_without_mood_labels(self):
        answer = self.ask("لَمْ يكتب زيد.", "هل كتب زيد؟")
        self.assertEqual(answer["status"], "REFUTED")
        self.assertTrue(answer["counterproofs"])
        self.assertFalse(answer["proofs"])

    def test_signed_conflict_does_not_make_unrelated_claim_true(self):
        answer = self.ask("كتب زيد. لَمْ يكتب زيد.", "هل كتب زيد؟")
        self.assertEqual(answer["status"], "CONFLICT")
        self.assertEqual(self.ask("كتب زيد. لَمْ يكتب زيد.", "هل زيد عالم؟")["status"], "UNKNOWN")

    def test_nonassertive_wish_hope_and_questions_do_not_add_facts(self):
        for text in ("ليت هذا عالم.", "لعل هذا عالم.", "هل زيد عالم؟"):
            with self.subTest(text=text):
                self.assertEqual(self.read(text)["claims"], [])

    def test_negative_and_disjunctive_scope_does_not_distribute_individual_facts(self):
        for text in ("ليس زيد عالم و هند كاتب.", "زيد عالم أو هند كاتب.", "لا يكتب زيد."):
            with self.subTest(text=text):
                self.assertEqual(self.read(text)["claims"], [])

    def test_two_complete_clauses_keep_separate_subjects_and_events(self):
        report = self.read("زيد عالم و هند كاتب.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual({(c["predicate"], tuple(c["args"])) for c in report["claims"]},
                         {("عالِم", ("zayd",)), ("كَاتِب", ("hind",))})
        self.assertEqual(self.ask("زيد عالم و هند كاتب.", "هل زيد كاتب؟")["status"], "UNKNOWN")

    def test_correlated_ta_person_readings_can_use_explicit_addressee(self):
        report = self.read("أنتِ تكتبين.")
        # A singular base does not manufacture a second feminine five-verb base.
        self.assertEqual(report["status"], "DEFER")
        report = self.read("أنت تكتب.")
        self.assertEqual(report["status"], "DEFER")
        masculine = deepcopy(CONTEXT)
        masculine["addressee"] = "zayd"
        self.assertEqual(self.read("أنت تكتب.", context=masculine)["status"], "LICENSED_DISCOURSE")

    def test_five_verb_nun_needs_the_right_closed_governor(self):
        context = deepcopy(CONTEXT)
        context["entities"].append({"id": "group", "name": "قوم", "gender": "masculine", "number": "plural", "kind": "person"})
        context["addressee"] = "group"
        licensed = self.read("لَمْ تكتبوا.", context=context)
        self.assertEqual(licensed["status"], "LICENSED_DISCOURSE")
        signs = [s["sign_name"] for a in accepted_analyses(licensed) for d in a["assignments"] for s in d["sign_candidates"]]
        self.assertIn("nun_deleted", signs)
        self.assertEqual(self.read("تكتبوا.", context=context)["claims"], [])

    def test_attached_object_and_protective_nun_bind_actual_source_bytes(self):
        text = "ضَرَبَنِي زَيْدٌ."
        report = self.read(text)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(report["claims"][0]["args"], ["zayd", "zayd"])
        nuns = [n for o in report["occurrences"] for r in o["readings"] for n in r["nun_readings"] if n["kind"] == "protective"]
        self.assertTrue(nuns)
        for nun in nuns:
            span = nun["span"]
            self.assertEqual(span["source_sha256"], report["source_sha256"])
            self.assertEqual(text.encode()[span["start"]:span["end"]].decode(), "نِ")
        assignments = [d for a in accepted_analyses(report) for d in a["assignments"] if d["role"] == "direct_object"]
        self.assertTrue(all(d["local_case"] == "nasb" for d in assignments))

    def test_attached_host_withdrawal_invalidates_old_answer(self):
        answer = self.ask("ضربني زيد.", "هل ضربني زيد؟")
        self.assertEqual(answer["status"], "SUPPORTED")
        removed = b"\n".join(line for line in TRAINING.split(b"\n") if not line.startswith(b"(1:17:"))
        model = learn_qac_lexicon(removed)
        self.assertFalse(verify_discourse_answer(answer, lexical_model=model, context=CONTEXT)["valid"])

    def test_idafa_retains_relation_without_claiming_world_ownership(self):
        report = self.read("كتابك واسع.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(report["claims"][0]["args"], ["book"])
        self.assertEqual(report["claims"][0]["restriction"], [{"kind": "idafa", "complement": "hind"}])
        relations = [r for a in accepted_analyses(report) for r in a["relations"]]
        self.assertTrue(all(not r["ownership_asserted"] for r in relations))
        self.assertEqual(self.ask("كتابك واسع.", "هل كتابك واسع؟")["status"], "SUPPORTED")

    def test_relative_return_requires_a_full_matching_clause(self):
        report = self.read("زيد الذي يكتب عالم.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(len(report["claims"]), 1)
        self.assertEqual(report["claims"][0]["predicate_kind"], "property")
        self.assertEqual(self.read("زيد الذي عالم.")["claims"], [])

    def test_source_partition_preserves_exact_bytes(self):
        text = "  زيد عالم.\n«زيد كاتب»\t"
        report = self.read(text)
        self.assertEqual("".join(p["surface"] for p in report["partition"]), text)
        for p in report["partition"]:
            self.assertEqual(text.encode()[p["span"]["start"]:p["span"]["end"]].decode(), p["surface"])

    def test_case_mood_poison_cannot_supply_role_or_person_answers(self):
        model = learn_qac_lexicon(TRAINING.replace(b"|NOM", b"|MOOD:JUS").replace(b"|GEN", b"|ACC"))
        for text in ("زيد عالم.", "لَمْ يكتب زيد.", "ضربني زيد."):
            with self.subTest(text=text):
                self.assertEqual(claims(self.read(text)), claims(self.read(text, lexical_model=model)))

    def test_replay_rejects_changed_text_context_model_scope_and_forged_claim(self):
        report = self.read("أنا عالم.")
        self.assertTrue(verify_discourse(report, lexical_model=self.model, context=CONTEXT)["valid"])
        for changes in ({"text": "أنا كاتب."}, {"context": {}}, {"lexical_model": None},
                        {"scope": "foreign"}, {"source_id": "other"}):
            args = {"lexical_model": self.model, "context": CONTEXT, **changes}
            self.assertFalse(verify_discourse(report, **args)["valid"])
        changed = deepcopy(report)
        changed["claims"][0]["args"] = ["hind"]
        self.assertFalse(verify_discourse(changed, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_question_replacement_and_proof_tampering_invalidates_answer(self):
        answer = self.ask("زيد عالم.", "هل زيد عالم؟")
        self.assertFalse(verify_discourse_answer(answer, question="هل زيد كاتب؟", lexical_model=self.model, context=CONTEXT)["valid"])
        changed = deepcopy(answer)
        changed["proofs"][0]["claim_id"] = "0" * 64
        self.assertFalse(verify_discourse_answer(changed, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_context_scalars_and_resource_limits_do_not_become_linguistic_rejection(self):
        with self.assertRaises(NabtError):
            self.read("زيد عالم.", context={"closed_reference_scope": 1})
        with self.assertRaises(NabtError) as caught:
            self.read("زيد " * 3000)
        self.assertEqual(caught.exception.status, "DEFER")
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")


if __name__ == "__main__":
    unittest.main()
