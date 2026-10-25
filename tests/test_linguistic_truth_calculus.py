"""Counterexamples for production finite-ledger checking; no Arabic claims."""
from copy import deepcopy
import unittest

from tools.linguistic_truth.calculus import (
    assess_candidate, canonical_json, enumerate_candidates, evaluate_request,
)


class CalculusBoundaries(unittest.TestCase):
    def setUp(self):
        self.citation = {"work": "fixture", "revision": "v1", "source_sha256": "digest",
                         "start_byte": 0, "end_byte": 1, "quotation": "x"}
        self.designation = {"id": "d", "expression": "word", "sense": "first",
                            "convention": "language", "origin": "original", "citation": self.citation}
        self.frame = {"occurrence": {"source": "user", "revision": "v1", "raw": "word",
                      "start_byte": 0, "end_byte": 4, "referent": "unspecified", "time": "now",
                      "context": "same-scope"}, "expression": "word", "convention": "language"}
        self.literal = {"designation": self.designation, "intended_sense": "first", "relation": None}
        self.relation = {"designation": self.designation, "target_sense": "second",
                         "kind": "similarity", "citation": self.citation}
        self.figurative = {"designation": self.designation, "intended_sense": "second", "relation": self.relation}

    def atom(self, kind, **fields):
        return {"value": {"kind": kind, **fields}, "positive": True, "scope": "same-scope"}

    def literal_evidence(self):
        return [self.atom("established", designation=self.designation),
                self.atom("used", frame=self.frame, sense="first")]

    def test_same_id_changed_citation_cannot_borrow_establishment(self):
        known = deepcopy(self.literal_evidence())
        known[0]["value"]["designation"]["citation"]["revision"] = "changed"
        self.assertEqual(assess_candidate(self.frame, self.literal, known), "UNKNOWN_PREMISE")
        self.assertEqual(assess_candidate(self.frame, self.literal, self.literal_evidence()), "SUPPORTED_PREMISES")

    def test_blocking_cue_and_explicit_negative_are_independent(self):
        known = [self.atom("established", designation=self.designation),
                 self.atom("used", frame=self.frame, sense="second"),
                 self.atom("related", relation=self.relation)]
        self.assertEqual(assess_candidate(self.frame, self.figurative, known), "UNKNOWN_PREMISE")
        exclusion = self.atom("excludes", frame=self.frame, designation=self.designation)
        self.assertEqual(assess_candidate(self.frame, self.figurative, known + [exclusion]), "SUPPORTED_PREMISES")
        opposite = {**exclusion, "positive": False}
        self.assertEqual(assess_candidate(self.frame, self.figurative, known + [opposite]), "REFUTED_PREMISE")
        self.assertEqual(assess_candidate(self.frame, self.figurative, known + [exclusion, opposite]), "CONFLICT")

    def test_scope_collision_does_not_merge_distinct_frames_or_structured_strings(self):
        known = self.literal_evidence()
        changed = deepcopy(self.frame)
        changed["occurrence"]["referent"] = 'x","time":"now'
        self.assertEqual(assess_candidate(changed, self.literal, known), "UNKNOWN_PREMISE")
        other = deepcopy(self.frame)
        other["occurrence"]["referent"] = "x"
        self.assertNotEqual(canonical_json(changed), canonical_json(other))
        self.assertNotEqual(canonical_json({"flag": False}), canonical_json({"flag": 0}))

    def test_duplicates_survive_while_empty_self_and_unbound_relations_are_excluded(self):
        unbound = deepcopy(self.relation)
        unbound["designation"]["id"] = "uninstalled"
        relations = [self.relation, {**self.relation, "kind": ""},
                     {**self.relation, "target_sense": "first"}, unbound]
        candidates = enumerate_candidates(self.frame, [self.designation, self.designation], relations)
        self.assertEqual(candidates, [self.literal, self.literal, self.figurative])
        request = {"frame": self.frame, "designations": [self.designation, self.designation],
                   "relations": relations, "known": [], "proposed": [self.literal, self.figurative], "budget": 6}
        self.assertFalse(evaluate_request(request)["complete_proposal"])
        limited = evaluate_request({**request, "budget": 5})
        self.assertEqual(limited["status"], "RESOURCE_EXHAUSTED")
        self.assertIsNone(limited["complete_proposal"])
        self.assertEqual(limited["rows"], [])

    def test_boolean_offsets_and_supplied_authority_flags_are_invalid(self):
        request = {"frame": self.frame, "designations": [self.designation], "relations": [],
                   "known": [], "proposed": [self.literal], "budget": 1}
        for mutation in ({**request, "budget": True}, {**request, "trusted": True}):
            with self.assertRaises(ValueError):
                evaluate_request(mutation)
        changed = deepcopy(request)
        changed["frame"]["occurrence"]["start_byte"] = False
        with self.assertRaises(ValueError):
            evaluate_request(changed)


if __name__ == "__main__":
    unittest.main()
