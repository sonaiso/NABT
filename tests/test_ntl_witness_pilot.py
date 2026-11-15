"""Golden source controls, independent proof checks, and the supported I/O entrance."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt.semantics import decode_atom_number
from tools.grammar_catalog import gateway
from tools.lexical_training import ntl_witness_pilot as pilot, teaching

ROWS = {r["id"]: r for r in pilot.ranker.origins()}
NATIVE = Path(__file__).resolve().parents[1] / "formal/.lake/build/bin/scopedCompositionProbe"


def lesson(text, source_id="probe", withdraw=()):
    return dict(schema=pilot.SCHEMA, text=text, source_id=source_id, withdraw=list(withdraw))


def claims(result):
    return {q["id"]: q for q in result["questions"]}


class WitnessPilot(unittest.TestCase):
    def test_split_and_training_manifest(self):
        head = json.loads(pilot.ranker.MODEL.read_bytes())
        self.assertEqual(len(ROWS), 60)
        self.assertEqual(set(head["train_ids"]), {k for k, r in ROWS.items() if r["split"] == "train"})
        for prefix in ("door", "seed", "num", "doc"):
            split = Counter(r["split"] for k, r in ROWS.items() if k.startswith(prefix))
            self.assertEqual(dict(split), {"train": 9, "dev": 3, "test": 3})

    def test_fold_scope_and_restore(self):
        row = ROWS["seed13"]
        text = row["text"]
        init = lesson(text)
        base = pilot.run(init)
        cut = pilot.run(dict(init, withdraw=["binding"]))
        _, original = decode_atom_number(base["source_number"])
        self.assertEqual(original.args, ("probe", text))
        first, second = claims(base), claims(cut)
        self.assertEqual(cut["lost"], ["reading"])
        self.assertEqual(cut["kept"], ["context"])
        self.assertTrue({"surface", "cue", "concept"} <= set(cut["surviving_evidence"]))
        self.assertEqual(second["reading"]["after"]["missing"], ["binding"])
        self.assertIsNone(second["reading"]["after"]["answer"])
        self.assertEqual(first["context"], second["context"])
        self.assertNotEqual(second["reading"]["before"]["number"], second["reading"]["after"]["number"])
        self.assertEqual(decode_atom_number(first["reading"]["structure_number"])[1].args,
                         (row["carrier"], row["value"]))
        other = claims(pilot.run(dict(init, source_id="other")))["reading"]
        self.assertEqual(other["structure_number"], first["reading"]["structure_number"])
        self.assertNotEqual(other["occurrence_number"], first["reading"]["occurrence_number"])
        for item in cut["evidence"].values():
            if "utf8_span" in item:
                self.assertEqual(text.encode()[slice(*item["utf8_span"])].decode(), item["surface"])
        self.assertEqual(pilot.run(init), base)

    def test_new_compositions_and_scope_controls(self):
        for text, relation, carrier in (
            ("لم يُفتح باب المختبر؛ مكان الرصد في المختبر.", "negative", "باب المختبر"),
            ("لم تنبت بذرة الخيار؛ مكان الرصد في المشتل.", "negative", "بذرة الخيار"),
            ("سَجِّلْ وثيقة الإعارة؛ مكان الرصد في الأرشيف.", "request", "وثيقة الإعارة"),
            ("العدد 82 زوجي؛ مكان الرصد في الفصل.", "even", "82"),
        ):
            with self.subTest(text=text):
                r = teaching.run_lesson(lesson(text))
                self.assertEqual(r["binding"], "FINITE_COMPOSITION_RULE")
                self.assertNotIn(text, {r["text"] for r in ROWS.values()})
                self.assertEqual(r["evidence"]["concept"]["relation"], relation)
                self.assertIn(carrier, claims(r)["reading"]["before"]["answer"])
                self.assertFalse(r["world_occurrence_established"])
                self.assertFalse(r["empirical_causality_established"])
                self.assertEqual(r["neural"]["authority"], "NONE")
        for unknown in ('قالت المعلمة «سَجِّلْ وثيقة الإعارة».', "إن سجلت الوثيقة فاحتفظ بها.",
                        "لم تنبت بذرة الخيار؛ نبتت بذرة الخيار."):
            r = teaching.run_lesson(lesson(unknown))
            self.assertEqual((r["status"], r["questions"]), ("UNBOUND_READING", []))

    @unittest.skipUnless(NATIVE.is_file(), "native arithmetic owner required")
    def test_proof_withdrawal_false_witness_and_changed_subject(self):
        for eq, proven in [("82 = 2 × 41", True), ("82 = 2 × 42", False),
                           ("80 = 2 × 40", False), ("81 = 2 × 40 + 1", False)]:
            req = lesson("العدد 82 زوجي؛ " + eq + ".")
            r = teaching.run_lesson(req)
            self.assertIn("reading", r["kept"])
            self.assertEqual("demonstrated" in r["kept"], proven)
            if proven:
                proof = claims(r)["demonstrated"]
                self.assertEqual(set(proof["sufficient_support"]),
                                 {"surface", "cue", "concept", "binding", "proof.surface", "proof.check"})
                cut = teaching.run_lesson(dict(req, withdraw=["proof.surface"]))
                self.assertEqual(cut["kept"], ["reading"])
                self.assertEqual(cut["lost"], ["demonstrated"])
                self.assertIn("NO_SURVIVING_VALID_PROOF", cut["residuals"])
        invalid = teaching.run_lesson(lesson(ROWS["num15"]["text"]))
        self.assertEqual(invalid["proof_owner"]["answer"]["decision"], "FALSE")
        self.assertEqual(invalid["kept"], ["reading", "context"])

    def test_unsupported_inputs_and_absent_model(self):
        req = lesson(ROWS["doc13"]["text"])
        for delta in ({"withdraw": ["proof.check"]}, {"withdraw": ["cue", "cue"]}, {"source_id": ""},
                      {"binding": "ASSERTED"}, {"text": "سطر\nثان"}):
            self.assertEqual(teaching.run_lesson(dict(req, **delta))["status"], "INVALID_INPUT")
        with patch.object(pilot.ranker, "MODEL", Path("/no/such/model")):
            r = teaching.run_lesson(req)
        self.assertEqual(r["neural"]["status"], "MODEL_UNAVAILABLE")
        self.assertEqual(r["kept"], ["reading", "context"])

    def test_public_gateway_replays_and_rejects_changed_answer(self):
        req = {"schema": gateway.REQUEST_SCHEMA, "route": "cognitive.lesson",
               "payload": {"lesson": lesson(ROWS["door11"]["text"], withdraw=["binding"])}}
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        altered = deepcopy(receipt)
        altered["execution"]["owner_result"]["questions"][0]["after"]["answer"] = "وقع الفتح"
        self.assertFalse(gateway.accept_output(altered, expected_request=req)["valid"])
