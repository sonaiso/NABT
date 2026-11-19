import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway
from tools.grammar_catalog.ntp import request
from tools.lexical_training import pattern_learning as net, report_draft
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

    def test_weight_question_through_public_ntp(self):
        req = request("think", {"text": "ما وزن سَفَرْجَل؟"})
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        view = receipt["execution"]["owner_result"]["owner_result"]
        row, = [r for r in view["cards"] if r["scope"] == "pattern_reading"]
        self.assertIn("فَعَلْلَل", row["understood"])
        self.assertEqual(view["learned_patterns"]["model_sha256"], net.MODEL_SHA)
