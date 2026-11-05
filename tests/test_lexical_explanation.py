"""Independent attribution accounting, semantic identities and native replay."""
from copy import deepcopy
import importlib.util
from itertools import permutations
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HAS_NUMPY = importlib.util.find_spec("numpy") is not None
if HAS_NUMPY:
    import numpy as np
    from tools.lexical_training import acquisition as a
    from tools.lexical_training import explanation as e
    from tools.lexical_training.senses import catalogue, encode

ROOT = Path(__file__).resolve().parents[1]
MODEL = Path(os.environ.get("NABT_LEXICAL_ACQUISITION_RUN",
                           ROOT / "evidence/lexical_acquisition_v1/run_01"))
NATIVE = all((ROOT / "formal/.lake/build/bin" / name).is_file()
             for name in ("lexicalDenotation", "linguisticTruth"))


@unittest.skipUnless(HAS_NUMPY, "optional NumPy learner dependency")
class LexicalExplanationTests(unittest.TestCase):
    def test_scores_match_public_predictor_and_every_label_is_preserved(self):
        result = e.score_attribution("أداة نكتب بها", MODEL)
        proposal = a.propose("أداة نكتب بها", MODEL)
        for head, rows in proposal["ranking"].items():
            values = result["heads"][head]
            expected = dict(zip(values["labels"], values["score"]))
            self.assertEqual(set(expected), {r["id"] for r in rows})
            for row in rows:
                self.assertAlmostEqual(expected[row["id"]], row["score"], places=12)

    def test_all_permutation_paths_independently_account_for_contributions(self):
        result = e.score_attribution("أداة نكتب بها", MODEL)
        self.assertEqual(result["evaluations"], 8)
        for head in result["heads"].values():
            table = np.array(head["coalition_scores"])
            marginal_totals = np.zeros_like(head["contributions"])
            orders = list(permutations(range(3)))
            for order in orders:
                mask = 0
                for feature in order:
                    enlarged = mask | (1 << feature)
                    marginal_totals[feature] += table[enlarged] - table[mask]
                    mask = enlarged
            np.testing.assert_allclose(marginal_totals / len(orders), head["contributions"], atol=1e-12)
            np.testing.assert_allclose(np.sum(head["contributions"], axis=0),
                                       table[-1] - table[0], atol=1e-12)

    def test_repeated_words_retain_distinct_occurrences_and_equal_contributions(self):
        text = "  وبِقَلَمٍ\nقلم قلم"
        result = e.score_attribution(text, MODEL)
        self.assertEqual(len(result["groups"]), 3)
        for group in result["groups"]:
            self.assertEqual(text.encode()[slice(*group["bytes"])].decode(), group["text"])
        self.assertEqual(result["groups"][0]["text"], "وبِقَلَمٍ")
        self.assertNotEqual(result["groups"][1]["bytes"], result["groups"][2]["bytes"])
        for head in result["heads"].values():
            np.testing.assert_allclose(head["contributions"][1], head["contributions"][2], atol=1e-12)

    def test_lost_vowel_distinctions_remain_visible_as_a_model_limitation(self):
        # Independently specified minimal Arabic contrasts in the old scorer.
        for first, second in [("كَتَبَ", "كُتِبَ"), ("كَتَبْتُ", "كَتَبْتَ"),
                              ("قُمْتَ", "قُمْتِ")]:
            x = encode([first, second])
            np.testing.assert_array_equal(x[0], x[1])
        result = e.score_attribution("كَتَبْتُ", MODEL)
        self.assertFalse(result["linguistic_interpretation_from_attribution"])
        self.assertFalse(result["score_is_calibrated_probability"])
        self.assertFalse(result["masked_texts_linguistically_licensed"])

    def test_alif_wasla_is_retained_and_each_coalition_matches_the_scorer(self):
        models, _, _ = a.load_model(MODEL)
        for text, views in [("ٱ", [None, "ٱ"]),
                            ("ٱ قلم", [None, "ٱ", "قلم", "ٱ قلم"])]:
            with self.subTest(text=text):
                result = e.score_attribution(text, MODEL)
                self.assertEqual([g["text"] for g in result["groups"]], text.split())
                vectors = np.vstack([np.zeros_like(encode([text])) if view is None
                                     else encode([view]) for view in views])
                for head, model in models.items():
                    np.testing.assert_allclose(result["heads"][head]["coalition_scores"],
                                               e.forward(model, vectors), atol=1e-12)

    def test_limits_and_empty_input_stop_before_model_loading(self):
        with patch.object(a, "load_model") as load:
            for text in ["", "English", True, "ب " * 9, "ب" * 9000]:
                with self.subTest(text=str(text)[:30]), self.assertRaises(ValueError):
                    e.score_attribution(text, MODEL)
            load.assert_not_called()

    def test_graph_roundtrip_preserves_source_specific_senses_and_mental_conditions(self):
        graph = e.dictionary_graph()
        nodes = {n["@id"]: n for n in graph["@graph"]}
        self.assertEqual(len(nodes), len(graph["@graph"]))
        restored = [n["nabt:record"]["@value"] for n in nodes.values() if "nabt:record" in n]
        self.assertEqual(restored, catalogue()["senses"])
        self.assertEqual(graph["nabt:necessities"]["@value"], catalogue()["necessities"])
        self.assertEqual(len(graph["nabt:unresolvedLexicalEntries"]), 5)
        for node in nodes.values():
            if "nabt:record" not in node:
                continue
            sense = node["nabt:record"]["@value"]
            self.assertNotIn("ontolex:reference", node)
            if sense["id"] in graph["nabt:unresolvedLexicalEntries"]:
                self.assertEqual(node["@type"], "nabt:DictionaryInterpretation")
                self.assertNotIn("ontolex:isSenseOf", node)
            else:
                entry = nodes[node["ontolex:isSenseOf"]["@id"]]
                form = nodes[entry["ontolex:canonicalForm"]["@id"]]
                self.assertIn(form["ontolex:writtenRep"]["@value"], sense["citation"]["quotation"])
        blindness = nodes[e._id("sense", "lisan:ama")]
        entry = nodes[blindness["ontolex:isSenseOf"]["@id"]]
        form = nodes[entry["ontolex:canonicalForm"]["@id"]]
        self.assertEqual(entry["nabt:dictionaryIndex"], "عمي")
        self.assertEqual(form["ontolex:writtenRep"]["@value"], "العمى")

    def test_alignment_mismatch_is_rejected(self):
        matrix, digest = e.loader._installed_matrix()
        matrix = deepcopy(matrix)
        matrix["entries"][0]["components"] = ["fabricated"]
        with patch.object(e.loader, "_installed_matrix", return_value=(matrix, digest)):
            with self.assertRaisesRegex(ValueError, "disagree"):
                e.dictionary_graph()

    def test_mutating_an_export_cannot_change_the_next_graph(self):
        graph = e.dictionary_graph()
        graph["@context"]["ontolex"] = "urn:forged:"
        self.assertEqual(e.dictionary_graph()["@context"]["ontolex"],
                         "http://www.w3.org/ns/lemon/ontolex#")


@unittest.skipUnless(HAS_NUMPY and (NATIVE or os.environ.get("NABT_LEXICAL_ACQUISITION_NATIVE")),
                     "native lexical owners required")
class ConnectedExplanationTests(unittest.TestCase):
    def test_normal_cli_and_replay_reject_forged_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            args = ["explain", "--text", "أداة نكتب بها", "--model", str(MODEL)]
            self.assertEqual(a.main(args + ["--output", str(output)]), 0)
            report = json.loads(output.read_text())
            self.assertTrue(report["connection"]["all_native_lexical_checks_completed"])
            self.assertFalse(report["accepted_sense_from_score"])
            self.assertEqual(report["connection"]["indication_application"]["status"], "DEFER")
            check = Path(directory) / "check.json"
            self.assertEqual(a.main(args + ["--verify-report", str(output), "--output", str(check)]), 0)
            report["accepted_sense_from_score"] = True
            output.write_text(json.dumps(report, ensure_ascii=False))
            self.assertEqual(a.main(args + ["--verify-report", str(output), "--output", str(check)]), 2)

    def test_identity_change_during_owner_run_is_rejected(self):
        with patch.object(e, "_identity", side_effect=[["before"], ["after"]]):
            with self.assertRaisesRegex(ValueError, "changed during execution"):
                e.explain("أداة نكتب بها", MODEL)

    def test_failed_native_replay_cannot_validate_a_repeatable_report(self):
        for lexical, usage in [(False, "DEFER"), (True, "VERIFICATION_UNAVAILABLE")]:
            report = {"connection": {"all_native_lexical_checks_completed": lexical,
                                     "usage_owner": {"status": usage}}}
            with patch.object(e, "explain", return_value=report):
                result = e.verify(report, text="أداة", directory=MODEL)
            self.assertTrue(result["replay_matches"])
            self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
