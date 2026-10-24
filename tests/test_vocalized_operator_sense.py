"""Source withdrawal and contrary vowels for a bounded lexical-sense rule.

These are authored development fixtures. Their lexical records are explicit
premises, not independent observations or an Arabic accuracy estimate.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse

ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/construction_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/construction_context.json").read_text())
HASIBA = b"(9:80:1:1)\tHasiba\tV\tSTEM|POS:V|PERF|LEM:Hasiba|ROOT:Hsb|3MS\n"
ALIMA = b"(9:81:1:1)\tEalima\tV\tSTEM|POS:V|PERF|LEM:Ealima|ROOT:Elm|3MS\n"


class VocalizedOperatorSenseTests(unittest.TestCase):
    def read(self, text="حَسِبَ زيدٌ سالمًا حكيمًا.", records=HASIBA):
        model = learn_qac_lexicon(TRAINING + records)
        report = read_discourse(text, lexical_model=model, context=CONTEXT)
        self.assertTrue(verify_discourse(report, lexical_model=model, context=CONTEXT)["valid"])
        return report, model

    def test_written_kasra_licenses_only_the_belief_frame(self):
        report, _ = self.read()
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        witnesses = [r["independent_sense_witness"] for c in report["clauses"]
                     for a in c["analyses"] for r in a["relations"]
                     if "independent_sense_witness" in r]
        self.assertTrue(witnesses)
        self.assertTrue(all(w["source"]["passage"]["source_id"] == "mukhtar_sihah" for w in witnesses))
        self.assertTrue(all(w["target_role_used_as_sense_evidence"] is False for w in witnesses))
        self.assertTrue(all(w["embedded_fact_projection"] is False for w in witnesses))

    def test_unmarked_and_contrary_vowels_do_not_choose_the_desired_sense(self):
        for operator in ("حسب", "حَسَبَ", "حَسُبَ", "حَسِّبَ", "حَسِبُ",
                         "حسِب", "حَسِب", "حسِبَ", "حُسِبَ"):
            with self.subTest(operator=operator):
                report, _ = self.read(operator + " زيدٌ سالمًا حكيمًا.")
                self.assertFalse(report["claims"])

    def test_lexical_withdrawal_and_wrong_person_prevent_application(self):
        for records in (b"", HASIBA.replace(b"|3MS", b"|2MS"),
                        HASIBA.replace(b"|PERF|", b"|PERF|PASS|")):
            report, _ = self.read(records=records)
            self.assertFalse(report["claims"])

    def test_alima_keeps_independent_polysemy_obligation(self):
        report, _ = self.read("عَلِمَ زيدٌ سالمًا حكيمًا.", records=ALIMA)
        self.assertFalse(report["claims"])
        obligations = {o for c in report["clauses"] for a in c["analyses"] for o in a["obligations"]}
        self.assertIn("POLYSEMOUS_OPERATOR_SENSE_REQUIRES_INDEPENDENT_CONTEXT", obligations)

    def test_matrix_belief_does_not_establish_the_embedded_fact(self):
        text = "حَسِبَ زيدٌ سالمًا حكيمًا."
        _, model = self.read(text)
        embedded = ask_discourse(text, "هل سالمٌ حكيمٌ؟", lexical_model=model, context=CONTEXT)
        matrix = ask_discourse(text, "هل حَسِبَ زيدٌ سالمًا حكيمًا؟", lexical_model=model, context=CONTEXT)
        self.assertEqual(embedded["status"], "UNKNOWN")
        self.assertEqual(matrix["status"], "SUPPORTED")

    def test_forged_receipt_cannot_pass_replay(self):
        report, model = self.read()
        forged = deepcopy(report)
        witness = next(r["independent_sense_witness"] for c in forged["clauses"]
                       for a in c["analyses"] for r in a["relations"]
                       if "independent_sense_witness" in r)
        witness["operator_reading_id"] = "0" * 64
        self.assertFalse(verify_discourse(forged, lexical_model=model, context=CONTEXT)["valid"])


if __name__ == "__main__":
    unittest.main()
