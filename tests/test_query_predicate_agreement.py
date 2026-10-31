"""Frozen, independently authored query/agreement and claim-edge regressions."""

from hashlib import sha256
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import read_discourse, ask_discourse, verify_discourse_answer


FOLDER = Path(__file__).resolve().parents[1] / "evidence/constructions/query_agreement_review"


def frozen_material(folder):
    freeze = json.loads((folder / "material_freeze_v1.json").read_bytes())
    for row in freeze["files"]:
        raw = (folder / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha256(raw).hexdigest() != row["sha256"]:
            raise AssertionError("Frozen query material changed: " + row["path"])
    return json.loads((folder / "material_v1.json").read_bytes())


class QueryPredicateAgreementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {c["id"]: c for c in frozen_material(FOLDER)["cases"]}
        cls.supplement = frozen_material(FOLDER / "claim_edge_supplement")
        cls.models = {c["source"]: learn_qac_lexicon((FOLDER / c["source"]).read_bytes())
                      for c in cls.cases.values()}

    def check_case(self, case_id):
        case = self.cases[case_id]
        expected = case["expected"]
        context = json.loads((FOLDER / case["context"]).read_bytes())
        options = {"lexical_model": self.models[case["source"]], "context": context}
        document = read_discourse(case["text"], **options)
        inquiry = read_discourse(case["question"], source_id="question", **options)
        answer = ask_discourse(case["text"], case["question"], **options)
        self.assertEqual(document["status"], expected["document_status"])
        self.assertEqual(inquiry["status"], expected["inquiry_status"])
        if case_id == "WHR05" and answer["schema"] in (
                "nabt.discourse-answer.v2", "nabt.discourse-answer.v3"):
            # The historical gold is unchanged: this versioned contract change
            # is recorded in arabic_coverage/answer_contract_review_v1. Both
            # grammatical-gender readings have the identical empty answer;
            # no reading is selected and no proof is gained by the migration.
            self.assertEqual(expected["answer_statuses"], ["DEFER"])
            self.assertEqual(answer["status"], "UNKNOWN")
            self.assertEqual(answer["answer_basis"], "ALL_COMPLETE_QUERY_INTERPRETATIONS_AGREE")
            self.assertIsNone(answer["query"])
            viable = {a["analysis_id"] for c in inquiry["clauses"] for a in c["analyses"]
                      if not a["rejected_candidate"]}
            interpretations = answer["question_interpretations"]
            self.assertEqual({r["analysis_id"] for r in interpretations}, viable)
            self.assertTrue(interpretations)
            self.assertTrue(all(r["status"] == "UNKNOWN" and not r["bindings"]
                                and not r["proofs"] and not r["counterproofs"]
                                for r in interpretations))
            self.assertGreater(len({json.dumps(r["query"], sort_keys=True)
                                    for r in interpretations}), 1)
        else:
            self.assertIn(answer["status"], expected["answer_statuses"])
        self.assertEqual(sorted(b["values"]["?person"] for b in answer["bindings"]), expected["bound_person_ids"])
        self.assertEqual(bool(answer["proofs"]), bool(expected["bound_person_ids"]))
        self.assertEqual(answer["counterproofs"], [])
        self.assertEqual(inquiry["claims"], [])
        self.assertFalse(any(a["assertion_allowed"] for c in inquiry["clauses"] for a in c["analyses"]))
        interrogatives = [r for r in inquiry["derived_readings"] if r["lexical_features"].get("pos") == "INTG"]
        self.assertTrue(interrogatives)
        for reading in interrogatives:
            for axis in ("gender", "number"):
                self.assertIsNone(reading["lexical_features"].get(axis))
                self.assertIsNone(reading.get("profile", {}).get(axis))
        self.assertTrue(verify_discourse_answer(answer, **options)["valid"])
        self.assertFalse(verify_discourse_answer(answer, context=context)["valid"])
        self.assertFalse(verify_discourse_answer(answer, lexical_model=options["lexical_model"])["valid"])
        self.assertFalse(verify_discourse_answer(answer, text=case["text"] + "\n", **options)["valid"])
        for proof in answer["proofs"]:
            self.assertTrue(proof["predicate_agreement_bindings"])
            for receipt in proof["predicate_agreement_bindings"]:
                self.assertEqual(receipt["entity_id"], proof["bindings"][receipt["variable"]])
                self.assertEqual(receipt["context_sha256"], document["context"]["sha256"])
                self.assertTrue(receipt["source_witnesses"])

    def test_agreement_cannot_be_borrowed_across_claim_qualifiers(self):
        case = self.supplement
        folder = FOLDER / "claim_edge_supplement"
        options = {"lexical_model": learn_qac_lexicon((folder / case["source"]).read_bytes()),
                   "context": json.loads((folder / case["context"]).read_bytes())}
        self.assertEqual(read_discourse(case["text"], **options)["status"], "LICENSED_DISCOURSE")
        self.assertEqual(read_discourse(case["question"], **options)["status"], "LICENSED_DISCOURSE")
        answer = ask_discourse(case["text"], case["question"], **options)
        for key in ("answer_status", "bindings", "proofs", "counterproofs"):
            self.assertEqual(answer["status" if key == "answer_status" else key], case["expected"][key])
        self.assertTrue(verify_discourse_answer(answer, **options)["valid"])


def case_test(case_id):
    def test(self):
        self.check_case(case_id)
    return test


for _case_id in ("WHR01", "WHR02", "WHR03", "WHR04", "WHR05", "WHR06",
                 "WHR07", "WHR08", "WHR09", "WHR10", "WHR11"):
    setattr(QueryPredicateAgreementTests, "test_" + _case_id.lower(), case_test(_case_id))


if __name__ == "__main__":
    unittest.main()
