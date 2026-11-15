"""Blinded corpus integrity: paired meanings must point back into their own Arabic text."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import evaluate_passive_relation_gateway as scoring


HOLDOUT = Path(__file__).resolve().parents[1] / "evidence/passive_relation_transfer_v1/holdout.json"
FROZEN_SHA256 = "6aa167d831b38042b79e1f2367f0cd9647ebcae3647249129d7f2fd91e8cc7b5"


def witness(row, key):
    start, stop = row[key]
    return row["text"].encode("utf-8")[start:stop].decode("utf-8")


class PassiveRelationHoldout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = HOLDOUT.read_bytes()
        cls.gold = json.loads(cls.raw)

    def test_frozen_split_keeps_opening_anchors_out_of_transfer_score(self):
        self.assertEqual(sha256(self.raw).hexdigest(), FROZEN_SHA256)
        cases = self.gold["cases"]
        self.assertEqual(len({row["id"] for row in cases}), len(cases))
        self.assertEqual(len({row["text"] for row in cases}), len(cases))
        groups = defaultdict(set)
        for row in cases:
            groups[row["group"]].add(row["root"])
        self.assertEqual(groups["heldout"], set(self.gold["held_out_roots"]))
        self.assertEqual(groups["control"], groups["heldout"])
        self.assertFalse(groups["anchor"] & groups["heldout"])

    def test_polarity_intervention_preserves_patient_but_moves_evidence(self):
        pairs = defaultdict(dict)
        for row in self.gold["cases"]:
            if row["relation"] == "OUTSIDE":
                self.assertEqual(row["group"], "control")
                self.assertTrue(row["reason"])
                for key in ("cue_span", "verb_span", "patient_span"):
                    self.assertIsNone(row[key])
                continue
            self.assertNotIn(row["relation"], pairs[row["pair_id"]])
            pairs[row["pair_id"]][row["relation"]] = row
            for key in ("verb_span", "patient_span", "cue_span"):
                if row[key] is None:
                    continue
                start, stop = row[key]
                self.assertTrue(0 <= start < stop <= len(row["text"].encode("utf-8")))
                self.assertTrue(witness(row, key).strip())
            self.assertLess(row["verb_span"][1], row["patient_span"][0])

        for name, pair in pairs.items():
            with self.subTest(pair=name):
                self.assertEqual(set(pair), {"ASSERT_PASSIVE", "DENY_PASSIVE"})
                affirmative, denial = pair["ASSERT_PASSIVE"], pair["DENY_PASSIVE"]
                self.assertEqual(affirmative["group"], denial["group"])
                self.assertEqual(affirmative["root"], denial["root"])
                self.assertEqual(witness(affirmative, "patient_span"), witness(denial, "patient_span"))
                self.assertNotEqual(witness(affirmative, "verb_span"), witness(denial, "verb_span"))
                self.assertIsNone(affirmative["cue_span"])
                self.assertIn(witness(denial, "cue_span"), ("لم", "لَمْ"))
                self.assertLess(denial["cue_span"][1], denial["verb_span"][0])

    def test_scoring_rejects_wrong_sense_with_correct_spans(self):
        case = next(c for c in self.gold["cases"] if c["id"] == "h01")
        bound = sha256(case["text"].encode()).hexdigest()
        expected = {key: case[key] for key in scoring.FIELDS}
        substituted = {**expected, "event_family": case["root"], "event_sense_id": "another:meaning",
                       "patient_key": "باب", "operator_reading_conditional": False,
                       "source_sha256": bound, "world_truth_established": False}
        output = {"source": {"sha256": bound}, "world_truth_established": False,
                  "passive_relation_transfer": {"proposal": {**expected, "status": "PROPOSED", "model_sha256": "demo"},
                                                 "source_sha256": bound, "comparison": "MATCHES_SCOPED_READING"},
                  "cards": [{"scope": "source_event_relation", "evidence": substituted}]}
        receipt = {"status": "EXECUTED", "execution": {"owner_result": output}}
        replay = {"status": "VERIFIED_IO_REPLAY", "valid": True}
        with patch.object(scoring.gateway, "run", return_value=receipt), \
             patch.object(scoring.gateway, "accept_output", return_value=replay):
            row = scoring.evaluate_case(case)
        self.assertTrue(row["neural_exact"])
        self.assertFalse(row["gateway_exact"])

    def test_missing_execution_is_not_a_correct_control_abstention(self):
        control = next(c for c in self.gold["cases"] if c["group"] == "control")
        with patch.object(scoring.gateway, "run", return_value={"status": "RESOURCE_LIMIT"}), \
             patch.object(scoring.gateway, "accept_output", return_value={"valid": False, "status": "NOT_EXECUTED"}):
            row = scoring.evaluate_case(control)
        self.assertIsNone(row["gateway_exact"])
        self.assertIsNone(row["neural_exact"])
