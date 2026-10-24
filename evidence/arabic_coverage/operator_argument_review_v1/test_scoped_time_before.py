"""Post-first-run review of scoped temporal composition, not new blind gold.

The first frozen result is retained separately. These use authored teaching
inputs with different words from the held-out failure and test a declared
embedded attachment profile without asserting exhaustive Arabic attachment.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon, lookup_key
from nabt.discourse import read_discourse, ask_discourse, verify_discourse


ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/construction_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/construction_context.json").read_text())


def complete(report):
    return [a for c in report["clauses"] for a in c["analyses"]
            if a["licensed_syntax"] and a["references_complete"] and not a["rejected_candidate"]]


class ConstructionScopedTimeReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def test_time_is_inside_scoped_event_and_has_the_internal_verb_head(self):
        for text in ("كاد سالمٌ يكتبُ أمسِ.", "كاد سالمٌ أن يكتبَ أمسِ.", "شرع سالمٌ يكتبُ أمسِ."):
            with self.subTest(text=text):
                report = read_discourse(text, lexical_model=self.model, context=CONTEXT)
                self.assertEqual(report["status"], "LICENSED_DISCOURSE")
                self.assertTrue(complete(report))
                for claim in report["claims"]:
                    self.assertEqual(claim["predicate_kind"], "scoped")
                    self.assertEqual(claim["time"], [])
                    scope = next(q for q in claim["restriction"] if q["kind"] == "operator_scope")
                    self.assertFalse(scope["embedded_fact_projection"])
                    self.assertEqual([lookup_key(t["lemma"]) for t in scope["embedded"][0]["time"]], ["أمس"])
                for analysis in complete(report):
                    temporal = next(a for a in analysis["assignments"] if a["role"] == "time_adverb")
                    internal = next(a for a in analysis["assignments"] if a["role"].startswith("imperfect_"))
                    clause = next(a for a in analysis["assignments"] if a["role"] == "kada_predicate")
                    self.assertEqual(temporal["head_span"], internal["span"])
                    self.assertEqual(clause["span"]["end"], temporal["span"]["end"])
                    edge = next(r for r in analysis["relations"] if r["kind"] == "time_adverb")
                    self.assertEqual(edge["scope"], "embedded_event")
                    self.assertFalse(edge["exhaustive_attachment_claimed"])
                self.assertTrue(verify_discourse(report, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_matching_scoped_query_works_without_time_erasure_or_realized_event(self):
        text = "كاد سالمٌ يكتبُ أمسِ."
        for question, expected in (("هل كاد سالمٌ يكتبُ أمسِ؟", "SUPPORTED"),
                                   ("هل كاد سالمٌ يكتبُ؟", "UNKNOWN"),
                                   ("هل يكتبُ سالمٌ أمسِ؟", "UNKNOWN")):
            with self.subTest(question=question):
                answer = ask_discourse(text, question, lexical_model=self.model, context=CONTEXT)
                self.assertEqual(answer["status"], expected)
                if expected == "UNKNOWN":
                    self.assertEqual(answer["proofs"], [])

    def test_scoped_temporal_extension_keeps_mood_case_and_source_gates(self):
        for text in ("كاد سالمٌ يكتبَ أمسِ.", "كاد سالمًا يكتبُ أمسِ.",
                     "شرع سالمٌ أن يكتبَ أمسِ.", "كاد سالمٌ يكتبُ أمسُ."):
            with self.subTest(text=text):
                report = read_discourse(text, lexical_model=self.model, context=CONTEXT)
                self.assertEqual(report["claims"], [])
                self.assertFalse(complete(report))
        source = b"\n".join(line for line in TRAINING.splitlines() if b"\t>amosi\t" not in line) + b"\n"
        report = read_discourse("كاد سالمٌ يكتبُ أمسِ.", lexical_model=learn_qac_lexicon(source), context=CONTEXT)
        self.assertEqual(report["claims"], [])

    def test_event_only_noun_time_example_does_not_license_nominal_operator_predicate(self):
        source = TRAINING.replace(b"\t>amosi\tT\tSTEM|POS:T|LEM:>amos|ROOT:'ms|M",
                                  b"\t>amosi\tN\tSTEM|POS:N|LEM:>amos|ROOT:'ms|MS")
        model = learn_qac_lexicon(source)
        event = read_discourse("كتب زيدٌ أمسِ.", lexical_model=model, context=CONTEXT)
        self.assertEqual(event["status"], "LICENSED_DISCOURSE")
        for text in ("كان زيدٌ حكيمًا أمسِ.", "إنَّ زيدًا حكيمٌ أمسِ."):
            with self.subTest(text=text):
                report = read_discourse(text, lexical_model=model, context=CONTEXT)
                self.assertFalse(complete(report))
                self.assertEqual(report["claims"], [])


if __name__ == "__main__":
    unittest.main()
