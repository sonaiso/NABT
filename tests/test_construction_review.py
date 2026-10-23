"""Post-review counterexamples; the before-fix matrices are frozen separately."""

import json
from copy import deepcopy
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse

ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/construction_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/construction_context.json").read_text())


class ConstructionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def read(self, text, *, model=None):
        return read_discourse(text, lexical_model=model or self.model, context=CONTEXT)

    def ask(self, text, question, *, model=None):
        return ask_discourse(text, question, lexical_model=model or self.model, context=CONTEXT)

    def test_contrary_operator_marks_cannot_return_to_a_legacy_frame(self):
        for text in ("كَانُ زيدٌ حكيمًا.", "كِانَ زيدٌ حكيمًا.",
                     "إِنُّ زيدًا حكيمٌ.", "لَيْسُ زيدٌ حكيمًا.",
                     "كَادُ زيدٌ يكتبُ.", "مُا زال زيدٌ حكيمًا."):
            with self.subTest(text=text):
                report = self.read(text)
                self.assertEqual(report["claims"], [])
                self.assertFalse(any(a["actual_role"] for clause in report["clauses"]
                                     for row in clause["analyses"] for a in row["assignments"]))
                self.assertNotEqual(self.ask(text, "هل " + text[:-1] + "؟")["status"], "SUPPORTED")

    def test_wh_operator_query_uses_the_same_source_bound_gate(self):
        text = "كان زيدٌ حكيمًا أمسِ."
        good = self.ask(text, "متى كَانَ زيدٌ حكيمًا؟")
        self.assertEqual(good["status"], "SUPPORTED")
        query = self.read("متى كَانَ زيدٌ حكيمًا؟")
        for clause in query["clauses"]:
            for row in clause["analyses"]:
                if row["licensed_syntax"] and not row["rejected_candidate"]:
                    self.assertEqual(row["question_kind"], "time")
                    self.assertTrue(any(r["kind"] == "construction_gate" and r["allowed"]
                                        for r in row["relations"]))
        self.assertNotEqual(self.ask(text, "متى كَانُ زيدٌ حكيمًا؟")["status"], "SUPPORTED")

    def test_source_inflected_operator_does_not_fall_through_with_bad_internal_marks(self):
        witness = b"(9:50:1:1)\tyakuwnu\tV\tSTEM|POS:V|IMPF|LEM:kaAna|ROOT:kwn|3MS\n"
        model = learn_qac_lexicon(TRAINING + witness)
        for text in ("يُكونُ زيدٌ حكيمًا.", "سوف يُكونُ زيدٌ حكيمًا."):
            with self.subTest(text=text):
                self.assertEqual(self.read(text, model=model)["claims"], [])

    def test_consumed_particles_keep_their_explicit_vocalization(self):
        good = "سَوْفَ يكتبُ زيدٌ."
        self.assertEqual(self.ask(good, "هل سوف يكتبُ زيدٌ؟")["status"], "SUPPORTED")
        self.assertEqual(self.read("سُوفَ يكتبُ زيدٌ.")["claims"], [])
        self.assertNotEqual(self.ask("كان زيدٌ حكيمًا.", "هُلْ كان زيدٌ حكيمًا؟")["status"], "SUPPORTED")
        self.assertEqual(self.read("ليس زيدٌ إِلُّا حكيمًا.")["claims"], [])
        self.assertEqual(self.ask("ليس زيدٌ إِلَّا حكيمًا.", "هل ليس زيدٌ إلا حكيمًا؟")["status"], "SUPPORTED")
        self.assertEqual(self.read("زيدٌ حكيمٌ وَ سالمٌ حكيمٌ.")["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.read("زيدٌ حكيمٌ وُ سالمٌ حكيمٌ.")["claims"], [])

    def test_known_adjective_conflicts_never_activate_the_predication(self):
        for text in ("كان زيدٌ حكيمةً.", "إنَّ زيدًا حكيمةٌ.",
                     "ظن زيدٌ سالمًا حكيمةً.", "زيدٌ حكيمةٌ."):
            with self.subTest(text=text):
                report = self.read(text)
                self.assertEqual(report["claims"], [])
                rows = [a for c in report["clauses"] for a in c["analyses"]]
                self.assertTrue(rows)
                self.assertTrue(all(a["rejected_candidate"] for a in rows))
                self.assertFalse(any(a["actual_role"] for row in rows for a in row["assignments"]))
                self.assertTrue(all(r["status"] == "conflict" for row in rows
                                    for r in row["relations"] if r["kind"] == "predicate_agreement"))
                self.assertNotEqual(self.ask(text, "هل " + text[:-1] + "؟")["status"], "SUPPORTED")

    def test_predicate_rule_keeps_unknown_features_and_ordinary_nouns_distinct(self):
        self.assertEqual(self.read("إنَّ هندًا حكيمةٌ.")["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.read("كان زيدٌ نفسًا.")["status"], "LICENSED_DISCOURSE")
        raw = b"\n".join(line.replace(b"|FS", b"") if b"Hakiymap" in line else line
                         for line in TRAINING.splitlines()) + b"\n"
        report = self.read("كان زيدٌ حكيمةً.", model=learn_qac_lexicon(raw))
        self.assertEqual(report["claims"], [])
        rows = [a for c in report["clauses"] for a in c["analyses"]]
        self.assertFalse(any(a["rejected_candidate"] for a in rows))
        self.assertTrue(any("PREDICATE_AGREEMENT_EVIDENCE_REQUIRED" in a["obligations"] for a in rows))

    def test_common_gender_pronoun_agreement_uses_its_resolved_referent(self):
        witness = b"(9:51:1:1)\t>anaA\tPRON\tSTEM|POS:PRON|1S\n"
        model = learn_qac_lexicon(TRAINING + witness)
        report = self.read("أنا حكيمٌ.", model=model)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.read("أنا حكيمةٌ.", model=model)["claims"], [])
        pronouns = [r for o in report["occurrences"] for r in o["readings"]
                    if r["lexical_features"].get("pos") == "PRON"]
        self.assertTrue(pronouns)
        self.assertTrue(all(r["lexical_features"]["gender"] is None for r in pronouns))
        context = deepcopy(CONTEXT)
        context["speaker"] = "hind"
        self.assertEqual(read_discourse("أنا حكيمةٌ.", lexical_model=model, context=context)["status"], "LICENSED_DISCOURSE")
        context["entities"][1]["gender"] = "unknown"
        self.assertEqual(read_discourse("أنا حكيمةٌ.", lexical_model=model, context=context)["claims"], [])

    @staticmethod
    def alif_model(full):
        rows = ("LOCATION\tFORM\tTAG\tFEATURES\n"
                "(1:1:1:1)\tzayodN\tPN\tSTEM|POS:PN|LEM:zayod|ROOT:zyd|MS\n"
                "(1:2:1:1)\tzayodK\tPN\tSTEM|POS:PN|LEM:zayod|ROOT:zyd|MS\n"
                "(1:3:1:1)\tEalamN\tN\tSTEM|POS:N|LEM:Ealam|ROOT:Elm|MS\n"
                "(1:4:1:1)\tEalamK\tN\tSTEM|POS:N|LEM:Ealam|ROOT:Elm|MS\n"
                f"(1:5:1:1)\t{full}\tN\tSTEM|POS:N|LEM:Ealam|ROOT:Elm|MS\n"
                "(1:6:1:1)\tkaAna\tV\tSTEM|POS:V|PERF|LEM:kaAna|ROOT:kwn|3MS\n")
        return learn_qac_lexicon(rows.encode())

    def test_unvocalized_input_cannot_join_incompatible_source_templates(self):
        bad = self.alif_model("EilomFA")
        good = self.alif_model("EalamFA")
        text = "كان زيد علما."
        report = self.read(text, model=good)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        self.assertEqual(self.read(text, model=bad)["claims"], [])
        self.assertNotEqual(self.ask(text, "هل كان زيد علما؟", model=bad)["status"], "SUPPORTED")
        self.assertFalse(verify_discourse(report, lexical_model=bad, context=CONTEXT)["valid"])

    def test_carrier_receipt_keeps_the_direct_template_witness(self):
        report = self.read("كان زيد علما.", model=self.alif_model("EalamFA"))
        receipts = [r["nominal_case_carrier"] for o in report["occurrences"]
                    for r in o["readings"] if "nominal_case_carrier" in r]
        self.assertTrue(receipts)
        for receipt in receipts:
            self.assertEqual(receipt["template_basis"], "DIRECT_SOURCE_TEMPLATE_EQUALITY_EXCEPT_CASE_ENDING")
            self.assertEqual(receipt["shared_internal_template"], [["ع", ["َ"]], ["ل", ["َ"]], ["م", []]])


if __name__ == "__main__":
    unittest.main()
