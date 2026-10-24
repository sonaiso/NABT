"""PR19 source bridges through the PR20 native semantic/enumeration checker.

Authored counterexamples, not a new held-out Arabic accuracy denominator.
No lexical truth or all-Arabic completeness is inferred from a checked claim.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from tools import mantuq_mafhum as mm
from tools import source_semantics as bridge
from nabt.discourse import ask_discourse

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "examples/construction_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/construction_context.json").read_text())
HASIBA = b"(9:80:1:1)\tHasiba\tV\tSTEM|POS:V|PERF|LEM:Hasiba|ROOT:Hsb|3MS\n"
BELIEF = "حَسِبَ زيدٌ سالمًا حكيمًا."
TEACHER = "الْمُعَلِّمُ كَرِيمٌ."
TEACHER_CONTEXT = {"entities": [{"id": "teacher", "name": "المعلم",
    "gender": "masculine", "number": "singular", "kind": "person"}]}
# Independently written premise ledger: both POS readings need their own
# tanwin; only the adjective has the pair licensing nominal inflectability.
NOMINAL = ("LOCATION\tFORM\tTAG\tFEATURES\n" + "".join(
    f"(1:{i}:1:1)\t{form}\t{pos}\tSTEM|POS:{pos}|LEM:{lemma}|ROOT:{root}|MS\n"
    for i, form, pos, lemma, root in [
        (1, "kariymK", "N", "kariym", "krm"),
        (2, "kariymN", "ADJ", "kariym", "krm"),
        (3, "kariymK", "ADJ", "kariym", "krm"),
        (4, "muEal~imN", "N", "muEal~im", "Elm"),
        (5, "muEal~imK", "N", "muEal~im", "Elm")])).encode()


class CompletionSemanticIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.probe = bridge.executable()
        except RuntimeError:
            if "NABT_CLASSICAL_SEMANTIC_PROBE" in os.environ:
                raise
            raise unittest.SkipTest("native classicalSemanticProbe is not built")

    def audit(self, text, raw, context, **kwargs):
        result = mm.audit_discourse(text, raw, context, probe=self.probe, **kwargs)
        self.assertTrue(result["source_replay_pass"])
        self.assertEqual(result["binding"]["source"].encode(), text.encode())
        self.assertEqual(result["binding"]["lexicon"].encode(), raw)
        self.assertEqual(json.loads(result["binding"]["context"]), context)
        for field in ("reader_enumeration_proved", "python_projection_proved",
                      "all_arabic_complete", "world_truth_established",
                      "acquisition_measured", "held_out_arabic_discovery_measured"):
            self.assertIs(result[field], False)
        return result

    def assert_unmeasured(self, result):
        for row in [*result["clauses"], result["document"]]:
            self.assertEqual(row["status"], "UNMEASURED")
            self.assertEqual(row["common_consequences"], [])

    def test_source_shadda_and_nominal_bridge_reach_native_all_readings(self):
        result = self.audit(TEACHER, NOMINAL, TEACHER_CONTEXT,
                            source_id="teacher_source", scope="classroom")
        self.assertEqual(result["binding"]["source_id"], "teacher_source")
        self.assertEqual(result["binding"]["scope"], "classroom")
        fresh = bridge.read_discourse(TEACHER, lexical_model=bridge.learn_qac_lexicon(NOMINAL),
            context=TEACHER_CONTEXT, source_id="teacher_source", scope="classroom")
        viable = [a["analysis_id"] for a in fresh["clauses"][0]["analyses"]
                  if not a["rejected_candidate"]]
        self.assertGreater(len(viable), 1)
        self.assertEqual(result["document"]["reading_ids"], [viable])
        self.assertEqual(result["document"]["combinations"], len(viable))
        self.assertTrue(result["document"]["supplied_pool_composition_proved"])
        for row in [result["clauses"][0], result["document"]]:
            self.assertTrue(row["common_consequences"])
            for consequence in row["common_consequences"]:
                claim = json.loads(consequence["formula"]["args"][0]["value"])["claim"]
                self.assertEqual(claim["args"], ["teacher"])
                self.assertEqual(claim["predicate"], "كَرِيم")

    def test_competing_referent_and_conflicting_shadda_block_common_meaning(self):
        rival = deepcopy(TEACHER_CONTEXT)
        rival["entities"].append({**rival["entities"][0], "id": "other_teacher"})
        contrary = deepcopy(TEACHER_CONTEXT)
        contrary["entities"][0]["name"] = "الْمُعَلَّم"
        for context in (rival, contrary):
            with self.subTest(context=context):
                result = self.audit(TEACHER, NOMINAL, context)
                self.assert_unmeasured(result)
                self.assertGreater(result["document"]["incomplete_alternatives"], 0)

    def test_withdrawing_donor_pair_blocks_the_semantic_bridge(self):
        withdrawn = b"\n".join(line for line in NOMINAL.split(b"\n")
                                if not line.startswith(b"(1:3:1:1)"))
        self.assert_unmeasured(self.audit(TEACHER, withdrawn, TEACHER_CONTEXT))

    def test_belief_scope_survives_native_consequence_without_fact_projection(self):
        result = self.audit(BELIEF, BASE + HASIBA, CONTEXT)
        for row in [result["clauses"][0], result["document"]]:
            self.assertTrue(row["common_consequences"])
            for c in row["common_consequences"]:
                claim = json.loads(c["formula"]["args"][0]["value"])["claim"]
                self.assertEqual(claim["predicate"], "@operator:حسب")
                self.assertEqual(claim["tense"], "past")
                scope = claim["restriction"][0]
                self.assertEqual(scope["sense"], "belief")
                self.assertIs(scope["embedded_fact_projection"], False)
                self.assertEqual(scope["embedded"][0]["args"], ["salim"])
        model = bridge.learn_qac_lexicon(BASE + HASIBA)
        self.assertEqual(ask_discourse(BELIEF, "هل سالمٌ حكيمٌ؟",
            lexical_model=model, context=CONTEXT)["status"], "UNKNOWN")

    def test_copilot_source_counterexamples_stay_unmeasured_and_defer_query(self):
        for raw in (HASIBA.replace(b"\tHasiba\t", b"\tHsb\t"),
                    HASIBA.replace(b"|PERF|", b"|PERF|(II)|")):
            with self.subTest(source=raw):
                self.assert_unmeasured(self.audit(BELIEF, BASE + raw, CONTEXT))
                model = bridge.learn_qac_lexicon(BASE + raw)
                self.assertEqual(ask_discourse(BELIEF, "هل حَسِبَ زيدٌ سالمًا حكيمًا؟",
                    lexical_model=model, context=CONTEXT)["status"], "DEFER")

    def test_forged_witness_or_stale_lexicon_cannot_enter_native_premises(self):
        raw = BASE + HASIBA
        fresh = bridge.read_discourse(BELIEF, lexical_model=bridge.learn_qac_lexicon(raw),
                                      context=CONTEXT)
        forged = deepcopy(fresh)
        witness = next(r["independent_sense_witness"] for c in forged["clauses"]
                       for a in c["analyses"] for r in a["relations"]
                       if "independent_sense_witness" in r)
        witness["operator_reading_id"] = "0" * 64
        for report, training in ((forged, raw), (fresh, raw + b"\n")):
            with self.subTest(forged=report is forged):
                with self.assertRaisesRegex(ValueError, "REPORT_CHANGED"):
                    mm.audit_discourse(BELIEF, training, CONTEXT, report=report, probe=self.probe)


if __name__ == "__main__":
    unittest.main()
