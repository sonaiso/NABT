"""Authored end-to-end contracts for existing noun evidence consumers.

These examples test replay, exact-source attribution and retained alternatives;
they are not an independent Arabic coverage or world-truth measurement.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse, verify_discourse_answer
from nabt.inflection_reader import read_inflection, verify_inflection
from nabt.person_evidence import person_candidates

ROOT = Path(__file__).resolve().parents[1]
TRAINING = (ROOT / "examples/interpretive_links_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/interpretive_links_context.json").read_text())
LEXICAL = (ROOT / "examples/interpretive_links_lexical.txt").read_text()
SOURCE = "زَيْدٌ رَجُلٌ. سَالِمٌ كَاتِبٌ."
QUESTION = "هل سَالِمٌ كَاتِبٌ؟"


class NominalInterpretationFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def options(self, **changes):
        return {"lexical_model": self.model, "context": CONTEXT, "lexical_text": LEXICAL, **changes}

    def test_derivation_tags_survive_both_existing_reading_producers(self):
        inflection = read_inflection("كَاتِبٌ", lexical_model=self.model)
        self.assertTrue(verify_inflection(inflection, lexical_model=self.model)["valid"])
        rows = [r for occurrence in inflection["occurrences"] for r in occurrence["readings"]]
        self.assertTrue(rows)
        self.assertTrue(all(r["lexical_features"]["nominal_derivation_features"] == ["ACT", "PCPL"]
                            for r in rows))
        person = person_candidates("كَاتِبٌ", lexical_model=self.model)
        self.assertTrue(person)
        self.assertTrue(all(r["nominal_derivation_features"] == ["ACT", "PCPL"] for r in person))
        report = read_discourse(SOURCE, **self.options())
        selected = [r for o in report["occurrences"] if o["surface"] == "كَاتِبٌ" for r in o["readings"]]
        self.assertEqual({bool(r.get("person_evidence")) for r in selected}, {False, True})
        self.assertTrue(all(r["lexical_features"]["nominal_derivation_features"] == ["ACT", "PCPL"]
                            for r in selected))
        self.assertTrue(verify_discourse(report, **self.options())["valid"])

    def test_each_answer_consumes_its_own_nominal_evidence(self):
        for question, lemma, denotation, tags in (
                ("هل زَيْدٌ رَجُلٌ؟", "رَجُل", "jins_jamid", []),
                (QUESTION, "كَاتِب", "mushtaq", ["ACT", "PCPL"])):
            with self.subTest(question=question):
                answer = ask_discourse(SOURCE, question, **self.options())
                self.assertEqual(answer["status"], "SUPPORTED")
                self.assertTrue(verify_discourse_answer(answer, **self.options())["valid"])
                rows = answer["predicate_interpretations"]
                self.assertTrue(rows)
                self.assertEqual({r["predicate"] for r in rows}, {lemma})
                self.assertEqual({tuple(r["derivation"]["features"]) for r in rows}, {tuple(tags)})
                self.assertTrue(all(r["grammatical_kind"] == "noun" for r in rows))
                self.assertTrue(all(r["grammatical_profile"]["gender"] == "masculine" for r in rows))
                self.assertTrue(all(not r["nominal_denotation"]["sense_equivalence_established"] for r in rows))
                alternatives = [a for r in rows for a in r["nominal_denotation"]["alternatives"]]
                self.assertTrue(alternatives)
                self.assertTrue(all(a["nominal_semantics"]["candidates"] == [denotation] for a in alternatives))
                self.assertTrue(all(a["nominal_semantics"]["status"] == "LICENSED" for a in alternatives))
                self.assertTrue(all(a["premises"] and a["lexical_link"]["source_reading_id"] for a in alternatives))
                ids = {r["interpretation_id"] for r in rows}
                self.assertTrue(all(set(p["predicate_interpretation_ids"]) <= ids for p in answer["proofs"]))
                self.assertEqual(answer["world_truth"], "NOT_ESTABLISHED")

    def test_missing_nominal_descriptions_leave_denotation_open(self):
        answer = ask_discourse(SOURCE, QUESTION, **self.options(lexical_text=None))
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertIsNone(answer["nominal_description_source"])
        self.assertTrue(answer["predicate_interpretations"])
        for row in answer["predicate_interpretations"]:
            self.assertEqual(row["derivation"]["features"], ["ACT", "PCPL"])
            self.assertEqual(row["nominal_denotation"]["status"], "DEFER")
            self.assertEqual(row["nominal_denotation"]["alternatives"], [])
            self.assertIn("LEXICAL_UNIVERSAL_AND_PROPERTY_BEARING_WITNESS", row["nominal_denotation"]["missing"])

    def test_withdrawn_or_replaced_descriptions_invalidate_old_results(self):
        report = read_discourse(SOURCE, **self.options())
        answer = ask_discourse(SOURCE, QUESTION, **self.options())
        replacements = (None, LEXICAL.replace("يدل على ذات باعتبار صفة", "يدل على ذات دون اعتبار صفة"))
        for lexical in replacements:
            with self.subTest(lexical=lexical):
                self.assertFalse(verify_discourse(report, **self.options(lexical_text=lexical))["valid"])
                self.assertFalse(verify_discourse_answer(answer, **self.options(lexical_text=lexical))["valid"])
        self.assertFalse(verify_discourse_answer(answer, **self.options(lexical_source_id="other"))["valid"])
        # Embedded original source is preserved for inspection, not reused as
        # verifier authority when the caller no longer supplies that premise.
        self.assertFalse(verify_discourse_answer(answer, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_same_surface_descriptive_alternatives_are_not_crossed_or_selected(self):
        rival = LEXICAL + "\nقراءة «katib_genus_rival» للفظ «كَاتِبٌ»:\n" + \
            "يدل على معنى مستقل غير مقترن بزمن\nيسلم من شبه الحرف\nلا يمنع تصوره الشركة\nيدل على ذات دون اعتبار صفة\n"
        answer = ask_discourse(SOURCE, QUESTION, **self.options(lexical_text=rival))
        self.assertEqual(answer["status"], "SUPPORTED")
        for row in answer["predicate_interpretations"]:
            alternatives = row["nominal_denotation"]["alternatives"]
            self.assertEqual(len(alternatives), 2)
            self.assertEqual({tuple(a["nominal_semantics"]["candidates"]) for a in alternatives},
                             {("mushtaq",), ("jins_jamid",)})
            self.assertEqual(len({a["reading_id"] for a in alternatives}), 2)
            self.assertFalse(row["nominal_denotation"]["sense_equivalence_established"])
            self.assertEqual(row["derivation"]["features"], ["ACT", "PCPL"])
            self.assertIn("DESCRIPTIVE_READING_TO_LEXICAL_SENSE_CORRESPONDENCE", row["nominal_denotation"]["missing"])

    def test_description_is_not_reused_by_lemma_or_stripped_spelling(self):
        answer = ask_discourse("سَالِمٌ كاتب.", "هل سَالِمٌ كاتب؟", **self.options())
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertTrue(answer["predicate_interpretations"])
        self.assertTrue(all(not r["nominal_denotation"]["alternatives"] for r in answer["predicate_interpretations"]))
        self.assertTrue(all(r["derivation"]["features"] == ["ACT", "PCPL"] for r in answer["predicate_interpretations"]))

    def test_equal_lemma_readings_do_not_merge_derivation_properties(self):
        # A deliberately authored rival tags the same form differently. This
        # tests preservation, not whether that annotation is linguistically true.
        rival = TRAINING + (
            "(1:11:1:1)\tkaAtibN\tN\tSTEM|POS:N|LEM:kaAtib|ROOT:ktb|MS|VN\n"
            "(1:12:1:1)\tkaAtibK\tN\tSTEM|POS:N|LEM:kaAtib|ROOT:ktb|MS|VN\n").encode()
        model = learn_qac_lexicon(rival)
        answer = ask_discourse("سَالِمٌ كَاتِبٌ.", QUESTION, **self.options(lexical_model=model))
        self.assertEqual(answer["status"], "SUPPORTED")
        rows = answer["predicate_interpretations"]
        self.assertEqual({tuple(r["derivation"]["features"]) for r in rows}, {("ACT", "PCPL"), ("VN",)})
        for row in rows:
            self.assertTrue(row["source_lexical_id"])
            for receipt in row["derivation"]["support_records"]:
                original = rival[receipt["byte_start"]:receipt["byte_end"]].decode()
                tokens = original.strip().split("\t")[-1].split("|")
                for feature in row["derivation"]["features"]:
                    self.assertIn(feature, tokens)

    def test_source_annotations_are_not_inferred_when_withdrawn(self):
        answer = ask_discourse(SOURCE, QUESTION, **self.options())
        plain = learn_qac_lexicon(TRAINING.replace(b"|ACT|PCPL", b""))
        self.assertFalse(verify_discourse_answer(answer, **self.options(lexical_model=plain))["valid"])
        fresh = ask_discourse(SOURCE, QUESTION, **self.options(lexical_model=plain))
        self.assertEqual(fresh["status"], "SUPPORTED")
        self.assertTrue(all(r["derivation"]["features"] == [] for r in fresh["predicate_interpretations"]))

    def test_embedded_nominal_explanation_retains_its_operator_scope(self):
        model = learn_qac_lexicon((ROOT / "examples/construction_training.tsv").read_bytes())
        context = json.loads((ROOT / "examples/construction_context.json").read_text())
        lexical = ("قراءة «hakim_quality» للفظ «حكيمًا»:\n"
                   "يدل على معنى مستقل غير مقترن بزمن\nيسلم من شبه الحرف\n"
                   "لا يمنع تصوره الشركة\nيدل على ذات باعتبار صفة")
        options = {"lexical_model": model, "context": context, "lexical_text": lexical}
        source = "ظن زيدٌ سالمًا حكيمًا."
        answer = ask_discourse(source, "هل ظن زيدٌ سالمًا حكيمًا؟", **options)
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertTrue(answer["predicate_interpretations"])
        for row in answer["predicate_interpretations"]:
            self.assertEqual(row["claim_path"], ["restriction", 0, "embedded", 0])
            self.assertEqual(row["assertion_scope"], "EMBEDDED_IN_OWNER_CLAIM_NOT_ASSERTED_SEPARATELY")
            self.assertEqual(row["predicate_claim"]["predicate_kind"], "property")
            self.assertTrue(row["nominal_denotation"]["alternatives"])
        bare = ask_discourse(source, "هل سالمٌ حكيمٌ؟", **options)
        self.assertEqual(bare["status"], "UNKNOWN")
        self.assertEqual(bare["predicate_interpretations"], [])

    def test_modified_meaning_receipt_is_not_authority(self):
        answer = ask_discourse(SOURCE, QUESTION, **self.options())
        variants = []
        changed = deepcopy(answer)
        changed["predicate_interpretations"][0]["derivation"]["features"] = ["VN"]
        variants.append(changed)
        changed = deepcopy(answer)
        changed["predicate_interpretations"][0]["nominal_denotation"]["alternatives"][0]["nominal_semantics"]["candidates"] = ["jins_jamid"]
        variants.append(changed)
        changed = deepcopy(answer)
        changed["predicate_interpretations"][0]["predicate_reading_id"] = "0" * 64
        variants.append(changed)
        for changed in variants:
            self.assertFalse(verify_discourse_answer(changed, **self.options())["valid"])

    def test_cli_accepts_and_explicitly_replays_description_source(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "answer.json"
            common = ["--qac", str(ROOT / "examples/interpretive_links_training.tsv"),
                      "--context", str(ROOT / "examples/interpretive_links_context.json")]
            lexical = ["--lexical-source", str(ROOT / "examples/interpretive_links_lexical.txt")]
            env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
            process = subprocess.run([sys.executable, "-m", "nabt.cli", "ask-discourse",
                str(ROOT / "examples/interpretive_links_source.txt"), QUESTION, *common, *lexical],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stderr)
            answer = json.loads(process.stdout)
            self.assertTrue(answer["predicate_interpretations"])
            report_path.write_text(process.stdout)
            verify = [sys.executable, "-m", "nabt.cli", "verify-discourse-answer", str(report_path),
                "--source", str(ROOT / "examples/interpretive_links_source.txt"), "--question", QUESTION, *common]
            good = subprocess.run(verify + lexical, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertTrue(json.loads(good.stdout)["valid"])
            absent = subprocess.run(verify, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(absent.returncode, 2)
            self.assertFalse(json.loads(absent.stdout)["valid"])


class NominalInterpretationNativeTests(unittest.TestCase):
    def test_native_consensus_binds_both_original_lexical_sources(self):
        sys.path.insert(0, str(ROOT))
        from tools import source_semantics as bridge
        try:
            probe = bridge.executable()
        except RuntimeError:
            if "NABT_CLASSICAL_SEMANTIC_PROBE" in os.environ:
                raise
            self.skipTest("build classicalSemanticProbe for native source binding")
        calls = []
        original = bridge.native
        def capture(requests, **kwargs):
            calls.extend(deepcopy(requests))
            return original(requests, **kwargs)
        with patch.object(bridge, "native", side_effect=capture):
            audit = bridge.audit_discourse(SOURCE, TRAINING, CONTEXT, lexical_text=LEXICAL, probe=probe)
        self.assertTrue(audit["source_replay_pass"])
        self.assertTrue(audit["contract_checks_pass"])
        consensus = [r for r in calls if r["op"] == "consensus"]
        self.assertTrue(consensus)
        for request in consensus:
            payload = json.loads(request["expected"]["lexicon"])
            self.assertEqual(payload["qac"], TRAINING.decode())
            self.assertEqual(payload["nominal_descriptions"]["raw_text"], LEXICAL)
            changed = deepcopy(request)
            changed["expected"] = {**changed["expected"], "lexicon": TRAINING.decode()}
            self.assertFalse(original([changed], probe=probe)[0]["contract_verified"])
        report = read_discourse(SOURCE, lexical_model=learn_qac_lexicon(TRAINING), context=CONTEXT, lexical_text=LEXICAL)
        with self.assertRaisesRegex(ValueError, "REPORT_CHANGED"):
            bridge.audit_discourse(SOURCE, TRAINING, CONTEXT, lexical_text=None, report=report, probe=probe)


if __name__ == "__main__":
    unittest.main()
