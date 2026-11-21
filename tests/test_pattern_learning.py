from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway
from tools.grammar_catalog.ntp import request
from tools.lexical_training import corpus_verbs, pattern_learning as net, pattern_lesson, report_draft
from tools.lexical_training import train_pattern_learning as train


class PatternLearningTests(unittest.TestCase):
    def test_contrast_induces_unlisted_templates_and_keeps_ambiguity(self):
        # The extra middle radical could be literal ج or a second use of slot 1.
        a = net.induce([("سجد", "سججد")])
        self.assertIn([0, 1, 1, 2], a)
        self.assertIn([0, "ج", 1, 2], a)
        self.assertEqual(net.induce([("سجد", "سججد"), ("كتب", "كتتب")]), [[0, 1, 1, 2]])
        self.assertNotIn([0, 1, 1, 2], [p["tokens"] for p in net.inventory()])
        self.assertEqual(net.induce([("سجد", "سجدد"), ("كتب", "كتتب")]), [])
        with self.assertRaises(ValueError):
            net.induce([("كتب", "كتبا"), ("حفظ", "حفظ")])

    def test_exhaustive_licensed_and_printed_families(self):
        report = json.loads((net.DIRECTORY / "training.json").read_bytes())
        learned = train.aligned_inventory()
        self.assertEqual(len(learned), 91)
        self.assertEqual({tuple(p["tokens"]) for p in learned}, {tuple(p["tokens"]) for p in net.inventory()})
        self.assertEqual(len({tuple(p["tokens"]) for p in learned}), 81)
        for p in net.inventory():
            if "example" in p:
                self.assertIn(p["id"], {v["pattern"] for _, v in net.alternatives(p["example"])})
        self.assertTrue(all(row["target_recovered"] for row in report["nominal_examples"]))
        self.assertEqual(net.MODEL_SHA, report["model_sha256"])
        self.assertGreater(report["patterns"]["final_test"]["correct_top1_compatible"],
                           report["patterns"]["initial_test"]["correct_top1_compatible"])
        for roots in (3, 4, 5):
            self.assertFalse(set(report["train_roots"][str(roots)]) & set(report["test_roots"][str(roots)]))

    def test_marks_roots_and_stable_witnesses(self):
        self.assertEqual(net.alternatives("كُِتب"), [])
        source = "X  كُتِبَ / كاتب / سَفَرْجَل"
        ranked = net.read(source)
        self.assertEqual(ranked["ranking"], "TRAINED")
        rows = ranked["occurrences"]
        self.assertEqual([source.encode()[slice(*o["utf8_span"])].decode() for o in rows],
                         ["كُتِبَ", "كاتب", "سَفَرْجَل"])
        self.assertEqual(rows[0]["alternatives"][0]["pattern"], "passive.I")
        self.assertNotIn("past.I.a", {r["pattern"] for r in rows[0]["alternatives"]})
        self.assertTrue({"grammar.sifa.faa3il", "nominal.faail"} <= {r["pattern"] for r in rows[1]["alternatives"]})
        self.assertEqual(rows[2]["alternatives"][0]["root"], "سفرجل")
        with patch.object(net, "model", return_value=None):
            unranked = net.read(source)
        self.assertEqual(unranked["ranking"], "MODEL_UNAVAILABLE")
        for left, right in zip(rows, unranked["occurrences"], strict=True):
            self.assertEqual(sorted(left["alternatives"], key=lambda x: x["pattern"]),
                             sorted(right["alternatives"], key=lambda x: x["pattern"]))

    def test_agent_checks_neural_decisions_before_execution(self):
        text = "راجع أحدث تقرير وأعد مسودة تنبيه إذا بلغت الطلبات المعلقة ثلاثة ولا ترسلها"
        lesson = {"schema": report_draft.SCHEMA, "task_id": "boundary", "instruction": text,
                  "reports": [{"id": "r", "issued_utc": "2026-01-01T00:00:00Z",
                               "rows": [{"id": str(i), "status": "معلق"} for i in range(3)]}]}
        for verb, expected in (("تجاوزت", False), ("بلغت", True)):
            lesson["instruction"] = text.replace("بلغت", verb)
            result = report_draft.run(lesson)
            obs = result["comparison"]["neural"]
            self.assertEqual(obs["prediction"], expected)
            self.assertEqual(obs["selection"], "VERIFIED_NEURAL_PROPOSAL")
            self.assertEqual(lesson["instruction"].encode()[slice(*obs["utf8_span"])].decode(), verb)
            self.assertEqual(result["status"] == "DRAFT_PLANNED", expected)
            with patch.object(net, "guard_proposal", return_value={"prediction": not expected}):
                alt = report_draft.run(lesson)
            self.assertEqual(alt["status"], result["status"])
            self.assertEqual(alt["comparison"]["neural"]["selection"], "INDEPENDENT_OWNER_FALLBACK")

    def test_missing_or_tampered_weights_and_budget(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(net, "DIRECTORY", Path(folder)):
            self.assertIsNone(net.model())
            (Path(folder) / "model.json").write_text("{}")
            self.assertIsNone(net.model())
        r = net.read(" ".join(["فعل"] * 129))
        self.assertEqual((r["total_terms"], r["terms_examined"]), (129,128))

    def test_lesson_learns_new_weights_and_applies_withdrawal(self):
        pairs = [["خبز", "خَبَّاز"], ["نجر", "نَجَّار"]]
        lesson = {"schema": pattern_lesson.SCHEMA, "pairs": pairs, "probe": "حَدَّاد"}
        result = pattern_lesson.run(lesson)
        learned, = result["alternatives"]
        self.assertNotIn(learned["tokens"], [p["tokens"] for p in net.inventory()])
        self.assertEqual(learned["probe_root"], "حدد")
        fitted = result["readout"]
        self.assertEqual((fitted["prediction"], len(fitted["weights"])), (True, 48))
        changed = pattern_lesson.run(dict(lesson, probe="حُدَّاد"))
        self.assertEqual(changed["status"], "NO_EXACT_REFILL")
        self.assertFalse(changed["readout"]["prediction"])
        self.assertEqual(fitted["weights"], changed["readout"]["weights"])
        self.assertTrue(fitted["score"] > 0 > changed["readout"]["score"])
        self.assertEqual(pattern_lesson.run(dict(lesson, pairs=[]))["status"], "DEFER_NO_DEMONSTRATIONS")
        self.assertEqual(pattern_lesson.run(dict(lesson, pairs=[["سجد","سججد"]]))["status"], "AMBIGUOUS_TEMPLATES")
        self.assertEqual(pattern_lesson.run(dict(lesson, pairs=pairs[:1]))["readout"]["status"], "INSUFFICIENT_EXAMPLES")
        other = pattern_lesson.run(dict(lesson, pairs=[["كتب","مَكْتُوب"],["حفظ","مَحْفُوظ"]], probe="مَفْتُوح"))
        self.assertNotEqual(other["readout"]["weights"], fitted["weights"])
        with patch.object(net, "model", return_value=None):
            self.assertEqual(pattern_lesson.run(lesson)["readout"]["status"], "ENCODER_UNAVAILABLE")

    def test_teach_and_probe_through_ntp(self):
        lesson = {"schema": pattern_lesson.SCHEMA, "pairs": [["خبز","خَبَّاز"],["نجر","نَجَّار"]],
                  "probe":"حَدَّاد"}
        req = request("cognitive.lesson", {"lesson": lesson})
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        owner = receipt["execution"]["owner_result"]["owner_result"]
        self.assertTrue(owner["readout"]["agrees_with_refill"])
        self.assertFalse(owner["global_model_updated"])
        tampered = deepcopy(receipt)
        tampered["execution"]["owner_result"]["owner_result"]["readout"]["weights"][0] += 1
        self.assertFalse(gateway.accept_output(tampered, expected_request=req)["valid"])

    def test_source_trained_root_projection_and_counterexamples(self):
        from tools.lexical_training.train_corpus_verbs import root_script
        heads = corpus_verbs.model()
        for word, root in (("يَعۡدِلُونَ", "عدل"), ("قَالَ", "قول")):
            obs = corpus_verbs.analyze(heads, word)
            self.assertEqual((obs["root"], obs["voice"], obs["family"]), (root, "ACT", "I"))
            self.assertEqual(corpus_verbs.apply_script(obs["script"], obs["radical_carriers"]), root)
        self.assertEqual(corpus_verbs.analyze(heads, "ثُمَّ"), None)
        self.assertIsNone(corpus_verbs.apply_script([0, 1, 8], "كتب"))
        self.assertEqual(root_script("مد", "مدد"), (0, 1, 1))
        self.assertIsNone(root_script("فل", "فعل"))
        report = json.loads((net.DIRECTORY / "corpus_training.json").read_bytes())
        self.assertEqual(report["model_sha256"], corpus_verbs.PIN)
        for population in report["test"].values():
            self.assertGreater(population["joint_correct"], population["fixed_template_ranker_joint_correct"])
            self.assertLess(population["joint_correct"], population["verbs"])
        with patch.object(corpus_verbs, "model", return_value=None):
            view = net.read("كُتِبَ")
        self.assertTrue(view["occurrences"])
        self.assertIsNone(view["corpus_verbs"]["model_sha256"])

    def test_free_written_root_question_through_ntp(self):
        word = "يَعۡدِلُونَ"
        text = "ما جذر " + word + "؟"
        req = request("think", {"text":text})
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        view = receipt["execution"]["owner_result"]["owner_result"]
        card, = [row for row in view["cards"] if row["scope"] == "neural_root"]
        obs = card["evidence"]["proposal"]
        self.assertEqual(text.encode()[slice(*obs["utf8_span"])].decode(), word)
        self.assertEqual((obs["root"], obs["aspect"], obs["script"]), ("عدل","IMPF",[1,2,3]))

    def test_weight_question_through_public_ntp(self):
        req = request("think", {"text": "ما وزن سَفَرْجَل؟"})
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        view = receipt["execution"]["owner_result"]["owner_result"]
        row, = [r for r in view["cards"] if r["scope"] == "pattern_reading"]
        self.assertIn("فَعَلْلَل", row["understood"])
        self.assertEqual(view["learned_patterns"]["model_sha256"], net.MODEL_SHA)
