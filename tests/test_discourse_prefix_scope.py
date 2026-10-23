"""Frozen authored checks for antecedent closure across an incomplete prefix.

No independent gold or natural-corpus examples enter this teaching fixture.
An unresolved earlier clause may hide a competitor; it must not make the
remaining antecedent uniquely resolved. Explicit speaker identity is separate.
"""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse_reader import read_discourse


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "discourse" / "prefix_scope_review"
CASES = json.loads((EVIDENCE / "cases_v1.json").read_text(encoding="utf-8"))["cases"]
OBSERVATIONS = {}
REPORTS = {}


class DiscoursePrefixScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        freeze = json.loads((EVIDENCE / "material_freeze_v1.json").read_text(encoding="utf-8"))
        for record in freeze["frozen_inputs"]:
            raw = (ROOT / record["path"]).read_bytes()
            if len(raw) != record["bytes"] or sha256(raw).hexdigest() != record["sha256"]:
                raise AssertionError("Frozen prefix-scope input changed: " + record["path"])
        cls.model = learn_qac_lexicon((EVIDENCE / "training_v1.tsv").read_bytes(),
                                     source_id="authored_prefix_scope")
        cls.context = json.loads((EVIDENCE / "context_v1.json").read_text(encoding="utf-8"))

    def _check(self, case_id):
        case = next(c for c in CASES if c["id"] == case_id)
        context = deepcopy(self.context)
        if "closed_reference_scope" in case:
            context["closed_reference_scope"] = case["closed_reference_scope"]
        report = read_discourse(case["text"], lexical_model=self.model, context=context,
                                source_id="prefix_scope_input")
        REPORTS[case_id] = report
        final = report["clauses"][-1]
        references = [r for a in final["analyses"] for r in a["references"]
                      if r["origin"] == case["origin"]]
        final_proofs = [p for claim in report["claims"] for p in claim["proofs"]
                        if p["clause_id"] == final["clause_id"]]
        observed = {
            "document_status": report["status"],
            "clause_statuses": [c["status"] for c in report["clauses"]],
            "final_reference_count": len(references),
            "final_references": [{k: r[k] for k in ("origin", "candidate_entity_ids",
                                  "bound_entity_id", "closed_scope", "status")} for r in references],
            "final_assertion_allowed_count": sum(bool(a["assertion_allowed"]) for a in final["analyses"]),
            "final_claim_proof_count": len(final_proofs),
            "claim_count": len(report["claims"]),
        }
        OBSERVATIONS[case_id] = observed
        self.assertEqual(report["status"], case["expect_document"], observed)
        self.assertTrue(references, "The final pronoun reading must be present")
        if "known_clause_index" in case:
            self.assertEqual(report["clauses"][case["known_clause_index"]]["status"], "LICENSED", observed)
        if "deferred_clause_index" in case:
            deferred = report["clauses"][case["deferred_clause_index"]]
            self.assertEqual(deferred["status"], "DEFER", observed)
            if case["incomplete_kind"] == "unknown_predicate":
                assignments = [assignment for analysis in deferred["analyses"]
                               for assignment in analysis["assignments"]
                               if assignment["role"] == "nominal_predicate"]
                self.assertTrue(assignments, "The unknown predicate must reach its construction guard")
                self.assertTrue(all("PREDICATE_CONSTRUCTION_EVIDENCE_REQUIRED" in a["obligations"]
                                    for a in assignments), assignments)
        if case["kind"] == "deferred_prefix":
            self.assertTrue(any(case["known_entity"] in r["candidate_entity_ids"] for r in references), observed)
            self.assertTrue(all(r["bound_entity_id"] is None and r["status"] != "RESOLVED"
                                for r in references), observed)
            self.assertTrue(all(not r["closed_scope"] for r in references), observed)
            self.assertEqual(observed["final_assertion_allowed_count"], 0, observed)
            self.assertEqual(final_proofs, [], observed)
        else:
            self.assertTrue(all(r["bound_entity_id"] == case["expect_binding"] and r["status"] == "RESOLVED"
                                for r in references), observed)
            self.assertTrue(final_proofs, observed)
            self.assertGreater(observed["final_assertion_allowed_count"], 0, observed)
        self.assertEqual(final["status"], case["expect_final_clause"], observed)

    def test_unknown_predicate_before_known_antecedent_does_not_close_scope(self):
        self._check("PREFIX-01")

    def test_unknown_predicate_between_antecedent_and_pronoun_does_not_close_scope(self):
        self._check("PREFIX-02")

    def test_unparsed_name_before_known_antecedent_does_not_close_scope(self):
        self._check("PREFIX-03")

    def test_unparsed_name_between_antecedent_and_pronoun_does_not_close_scope(self):
        self._check("PREFIX-04")

    def test_complete_document_still_resolves_its_antecedent(self):
        self._check("PREFIX-05")

    def test_explicit_speaker_does_not_require_closed_antecedent_search(self):
        self._check("PREFIX-06")


if __name__ == "__main__":
    unittest.main()
