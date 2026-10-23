"""Frozen authored tests of query selection among retained alternatives.

Two cases use the actual reader end to end. Four isolate the consumer
contract using real reader reports with only rejected-analysis order/claim
count changed. They do not redefine natural-language expected results.
"""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse
from nabt.discourse_context import identity
from nabt.discourse_reader import read_discourse


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/discourse/query_selection_review"
MATERIAL = json.loads((EVIDENCE / "cases_v1.json").read_text(encoding="utf-8"))
OBSERVATIONS = {}
REPORTS = {}


def eligible(analysis):
    return (not analysis["rejected_candidate"] and analysis["licensed_syntax"]
            and analysis["references_complete"])


class DiscourseQuerySelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        freeze = json.loads((EVIDENCE / "material_freeze_v1.json").read_text(encoding="utf-8"))
        for record in freeze["frozen_inputs"]:
            raw = (ROOT / record["path"]).read_bytes()
            if len(raw) != record["bytes"] or sha256(raw).hexdigest() != record["sha256"]:
                raise AssertionError("Frozen query-selection input changed: " + record["path"])
        cls.model = learn_qac_lexicon((EVIDENCE / "training_v1.tsv").read_bytes(),
                                     source_id="authored_query_selection")
        cls.context = json.loads((EVIDENCE / "context_v1.json").read_text(encoding="utf-8"))

    def _check(self, case_id):
        case = next(c for c in MATERIAL["cases"] if c["id"] == case_id)
        options = {"lexical_model": self.model, "context": self.context}
        document = read_discourse(MATERIAL["text"], **options)
        inquiry = read_discourse(case["question"], source_id="question", **options)
        self.assertEqual(document["status"], "LICENSED_DISCOURSE")
        self.assertEqual(inquiry["status"], "LICENSED_DISCOURSE")
        self.assertEqual(len(inquiry["clauses"]), 1)
        clause = inquiry["clauses"][0]
        licensed = [a for a in clause["analyses"] if eligible(a)]
        rejected = [a for a in clause["analyses"] if a["rejected_candidate"]]
        self.assertTrue(licensed, "A genuinely licensed question must remain")
        self.assertTrue(all(a["claims"][0]["args"] == ["hind"] for a in licensed))
        if case["rejected_required"]:
            self.assertTrue(rejected, "The reader must actually retain rejected alternatives")
        if case["mode"] == "consumer_contract":
            for analysis in rejected:
                original = deepcopy(analysis["claims"][0])
                analysis["claims"] = [deepcopy(original) for _ in range(case["rejected_claim_count"])]
                analysis["analysis_id"] = identity({k: v for k, v in analysis.items() if k != "analysis_id"})
            clause["analyses"] = (rejected + licensed if case["order"] == "rejected_first"
                                  else licensed + rejected)
            clause["clause_id"] = identity({k: v for k, v in clause.items() if k != "clause_id"})
            inquiry["report_id"] = identity({k: v for k, v in inquiry.items() if k != "report_id"})

            def reader(value, **kwargs):
                return deepcopy(inquiry) if kwargs.get("source_id") == "question" else read_discourse(value, **kwargs)

            with patch("nabt.discourse.read_discourse", side_effect=reader):
                answer = ask_discourse(MATERIAL["text"], case["question"], **options)
        else:
            answer = ask_discourse(MATERIAL["text"], case["question"], **options)
        observation = {
            "mode": case["mode"], "document_status": document["status"],
            "inquiry_status": inquiry["status"],
            "analysis_order": [{"rejected": a["rejected_candidate"], "licensed_syntax": a["licensed_syntax"],
                "references_complete": a["references_complete"], "claim_count": len(a["claims"]),
                "claim_args": [c["args"] for c in a["claims"]]} for a in clause["analyses"]],
            "answer_status": answer["status"], "answer_kind": answer["kind"],
            "query_args": None if answer["query"] is None else answer["query"]["args"],
            "proof_count": len(answer["proofs"]), "missing_premises": answer["missing_premises"],
        }
        OBSERVATIONS[case_id] = observation
        REPORTS[case_id] = {"document": document, "inquiry": inquiry, "answer": answer}
        self.assertEqual(answer["status"], MATERIAL["expected"]["status"], observation)
        self.assertEqual(answer["kind"], MATERIAL["expected"]["kind"], observation)
        self.assertEqual(answer["query"]["args"], MATERIAL["expected"]["args"], observation)
        self.assertTrue(answer["proofs"], observation)
        self.assertEqual(answer["missing_premises"], [], observation)

    def test_unvocalized_addressee_uses_licensed_feminine_reading(self):
        self._check("QUERY-01")

    def test_explicit_feminine_addressee_remains_supported(self):
        self._check("QUERY-02")

    def test_rejected_first_does_not_choose_the_query(self):
        self._check("QUERY-03")

    def test_eligible_first_has_the_same_qualified_answer(self):
        self._check("QUERY-04")

    def test_zero_claims_in_rejected_analysis_do_not_block_licensed_query(self):
        self._check("QUERY-05")

    def test_multiple_claims_in_rejected_analysis_do_not_block_licensed_query(self):
        self._check("QUERY-06")


if __name__ == "__main__":
    unittest.main()
