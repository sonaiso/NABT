"""Authored bridge oracles: a proposition uses only its selected predication.

These examples test the runtime handoff, not completeness of the Arabic
reader. The independent answer validator imports no runtime link helper.
Historical frozen counterexamples remain byte-identical.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import (_query_agreement_witnesses,
                            ask_discourse, read_discourse, verify_discourse, verify_discourse_answer)
from nabt.discourse_context import identity
from tools import discourse_evaluation
from tools.question_answer_validation import (CLAIM_FIELDS, source_agreement_witnesses,
                                               validate_interpretations)


ROOT = Path(__file__).resolve().parents[1]
QUESTION = "من حكيمٌ؟"
JOINED = "زيدٌ حكيمٌ و سالمٌ حكيمٌ."
REQUIRED = {"gender": "masculine", "number": "singular"}


def claim_view(claim):
    return {field: deepcopy(claim[field]) for field in CLAIM_FIELDS}


def source_analyses(document):
    return [analysis for clause in document["clauses"] for analysis in clause["analyses"]]


class ClaimPredicationBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon((ROOT / "examples/construction_training.tsv").read_bytes(),
                                     source_id="authored_claim_link_tests")
        cls.context = json.loads((ROOT / "examples/construction_context.json").read_text())
        cls.options = {"lexical_model": cls.model, "context": cls.context}
        cls.joined = read_discourse(JOINED, **cls.options)
        cls.inquiry = read_discourse(QUESTION, source_id="question", **cls.options)
        cls.answer = ask_discourse(JOINED, QUESTION, **cls.options)

    def check_independently(self, answer, document, inquiry):
        validate_interpretations(answer, document, inquiry, {"context": self.context}, claim_view=claim_view)

    def test_conjoined_distinct_claims_answer_with_their_own_edges(self):
        self.assertEqual(self.joined["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.answer["status"], "SUPPORTED")
        self.assertEqual({b["values"]["?person"] for b in self.answer["bindings"]}, {"zayd", "salim"})
        self.assertEqual(self.answer["missing_premises"], [])
        self.check_independently(self.answer, self.joined, self.inquiry)
        self.assertTrue(verify_discourse_answer(self.answer, **self.options)["valid"])
        rows = {row["analysis_id"]: row for row in source_analyses(self.joined)}
        for proof in self.answer["proofs"]:
            for receipt in proof["predicate_agreement_bindings"]:
                for witness in receipt["source_witnesses"]:
                    row = rows[witness["analysis_id"]]
                    binding = next(b for b in row["claim_bindings"]
                                   if b["binding_id"] == witness["predication_binding_id"])
                    self.assertEqual(binding["claim_path"], [])
                    self.assertEqual(row["claims"][binding["claim_index"]]["args"], [receipt["entity_id"]])
                    self.assertEqual(binding["predicate_reading_id"], witness["dependent_reading_id"])
                    self.assertIn(witness["reference_id"], binding["subject_reference_ids"])

    def test_alternative_local_binding_ids_do_not_create_semantic_disagreement(self):
        viable = [row for row in source_analyses(self.joined) if not row["rejected_candidate"]]
        self.assertGreater(len(viable), 1)
        self.assertEqual(len({identity(row["claims"]) for row in viable}), 1)
        self.assertGreater(len({binding["binding_id"] for row in viable for binding in row["claim_bindings"]}), 2)
        self.assertTrue(all(len(row["claim_bindings"]) == 2 for row in viable))

    def test_separate_clause_and_conjunction_have_the_same_person_answers(self):
        answer = ask_discourse("زيدٌ حكيمٌ. سالمٌ حكيمٌ.", QUESTION, **self.options)
        self.assertEqual([b["values"] for b in answer["bindings"]], [b["values"] for b in self.answer["bindings"]])

    def test_operator_embedded_predication_is_retained_without_projection(self):
        text = "زيدٌ حكيمٌ و ظن زيدٌ سالمًا حكيمًا."
        document = read_discourse(text, **self.options)
        self.assertEqual(document["status"], "LICENSED_DISCOURSE")
        for row in source_analyses(document):
            if row["rejected_candidate"]:
                continue
            self.assertTrue(any(b["claim_path"] == ["restriction", 0, "embedded", 0]
                                for b in row["claim_bindings"]))
            self.assertTrue(any(r["kind"] == "operator" for r in row["relations"]))
        answer = ask_discourse(text, QUESTION, **self.options)
        self.assertEqual([b["values"] for b in answer["bindings"]], [{"?person": "zayd"}])
        self.check_independently(answer, document, self.inquiry)
        self.assertEqual(ask_discourse(text, "هل سالمٌ حكيمٌ؟", **self.options)["status"], "UNKNOWN")
        self.assertEqual(ask_discourse(text, "هل ظن زيدٌ سالمًا حكيمًا؟", **self.options)["status"], "SUPPORTED")

    def test_relative_inner_predicate_cannot_replace_the_selected_outer_edge(self):
        text = "زيدٌ الذي هو حكيمٌ حكيمٌ."
        document = read_discourse(text, **self.options)
        answer = ask_discourse(text, QUESTION, **self.options)
        self.assertEqual(answer["status"], "SUPPORTED")
        self.check_independently(answer, document, self.inquiry)
        for row in source_analyses(document):
            if row["rejected_candidate"]:
                continue
            inner = {r["inner_predicate_reading_id"] for r in row["relations"]
                     if r["kind"] == "relative_clause" and "inner_predicate_reading_id" in r}
            self.assertTrue(inner)
            self.assertTrue(all(b["predicate_reading_id"] not in inner for b in row["claim_bindings"]))
        other = "زيدٌ الذي هو حكيمٌ كريمٌ."
        self.assertEqual(ask_discourse(other, QUESTION, **self.options)["status"], "UNKNOWN")

    def test_qualifier_counterexample_stays_unknown_and_names_missing_witness(self):
        folder = ROOT / "evidence/constructions/query_agreement_review/claim_edge_supplement"
        case = json.loads((folder / "material_v1.json").read_text())
        model = learn_qac_lexicon((folder / case["source"]).read_bytes())
        context = json.loads((folder / case["context"]).read_text())
        options = {"lexical_model": model, "context": context}
        answer = ask_discourse(case["text"], case["question"], **options)
        self.assertEqual(answer["status"], "UNKNOWN")
        self.assertEqual(answer["proofs"], [])
        self.assertEqual(answer["missing_premises"], ["CLAIM_PREDICATION_AGREEMENT_WITNESS_REQUIRED"])
        validate_interpretations(answer, read_discourse(case["text"], **options),
            read_discourse(case["question"], source_id="question", **options),
            {"context": context}, claim_view=claim_view)

    def test_tense_and_negated_conjunction_are_not_erased(self):
        answer = ask_discourse("زيدٌ حكيمٌ و كان سالمٌ حكيمًا.", QUESTION, **self.options)
        self.assertEqual([b["values"] for b in answer["bindings"]], [{"?person": "zayd"}])
        negative = read_discourse("ليس زيدٌ حكيمًا و سالمٌ حكيمٌ.", **self.options)
        self.assertFalse(any(c["args"] == ["salim"] and c["positive"] for c in negative["claims"]))

    def test_missing_binding_does_not_fall_back_to_lemma_matching(self):
        altered = deepcopy(self.joined)
        for row in source_analyses(altered):
            row["claim_bindings"] = []
        with patch("nabt.discourse.read_discourse", side_effect=[altered, self.inquiry]):
            answer = ask_discourse(JOINED, QUESTION, **self.options)
        self.assertEqual(answer["status"], "UNKNOWN")
        self.assertEqual(answer["missing_premises"], ["CLAIM_PREDICATION_AGREEMENT_WITNESS_REQUIRED"])
        self.assertFalse(verify_discourse(altered, **self.options)["valid"])
        for claim in altered["claims"]:
            self.assertEqual(source_agreement_witnesses(claim, REQUIRED, claim["args"][0], altered), [])

    def test_rehashed_wrong_claim_index_is_rejected_by_both_consumers(self):
        for invalid in (True, -1, 2, 1):
            document = deepcopy(self.joined)
            claim = next(c for c in document["claims"] if c["args"] == ["zayd"])
            for proof in claim["proofs"]:
                proof["claim_index"] = invalid
            with self.subTest(index=invalid):
                self.assertIsNone(_query_agreement_witnesses(self.answer["query"], claim,
                    {"?person": "zayd"}, document))
                self.assertEqual(source_agreement_witnesses(claim, REQUIRED, "zayd", document), [])

    def test_rehashed_changed_predication_anchors_cannot_reuse_old_agreement(self):
        for field, value in (("predicate_reading_id", "foreign"), ("subject_reference_ids", ["foreign"]),
                             ("scope", "foreign"), ("claim_path", ["restriction", 0, "embedded", 0]),
                             ("predicate_span", {}), ("claim_key", "0" * 64)):
            document = deepcopy(self.joined)
            replacements = {}
            for row in source_analyses(document):
                for binding in row["claim_bindings"]:
                    old = binding["binding_id"]
                    binding[field] = value
                    binding["binding_id"] = identity({k: v for k, v in binding.items() if k != "binding_id"})
                    replacements[old] = binding["binding_id"]
            for claim in document["claims"]:
                for proof in claim["proofs"]:
                    proof["predication_binding_ids"] = [replacements[value] for value in proof["predication_binding_ids"]]
                with self.subTest(field=field, person=claim["args"][0]):
                    self.assertIsNone(_query_agreement_witnesses(self.answer["query"], claim,
                        {"?person": claim["args"][0]}, document))
                    self.assertEqual(source_agreement_witnesses(claim, REQUIRED, claim["args"][0], document), [])

    def test_source_or_context_withdrawal_invalidates_the_previous_answer(self):
        self.assertFalse(verify_discourse_answer(self.answer, context=self.context)["valid"])
        self.assertFalse(verify_discourse_answer(self.answer, lexical_model=self.model)["valid"])
        self.assertFalse(verify_discourse_answer(self.answer, text=JOINED + "\n", **self.options)["valid"])

    def test_current_answer_cannot_downgrade_by_omitting_interpretation_inventory(self):
        altered = deepcopy(self.answer)
        del altered["question_interpretations"]
        altered["answer_id"] = identity({key: value for key, value in altered.items() if key != "answer_id"})
        with self.assertRaisesRegex(ValueError, "Question interpretation inventory must be a list"):
            discourse_evaluation.validate_answer(altered, self.joined, self.inquiry,
                {"context": self.context, "text": JOINED, "scope": "default", "source_id": "input"}, QUESTION)


if __name__ == "__main__":
    unittest.main()
