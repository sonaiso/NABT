"""Passive relational proposal scope, alternative retention and frozen experimental record."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog.operations import exact_terms
from tools.lexical_training import passive_transfer as model
from tools.lexical_training import passive_transfer_evaluation as experiment
from tools.lexical_training import passive_transfer_training as training


class PassiveRelationProposalTests(unittest.TestCase):
    def test_complete_ordered_hypotheses_reference_distinct_occurrences(self):
        text = "لم  فتح فتح"
        observed = {tuple(t["utf8_span"]) for t in exact_terms(text)}
        answer = model.propose(text)
        self.assertEqual(answer["authority"], "NONE")
        self.assertFalse(answer["world_truth_established"])
        self.assertEqual(answer["source_sha256"], sha256(text.encode()).hexdigest())
        self.assertEqual(len(answer["candidates"]), 1 + 3*2 + 3*2*1)
        for candidate in answer["candidates"]:
            spans = [tuple(candidate[k]) for k in ("verb_span","patient_span","cue_span") if candidate[k]]
            self.assertTrue(set(spans) <= observed)
            self.assertEqual(len(set(spans)), len(spans))
        self.assertEqual(answer, model.propose(text))

    def test_missing_changed_checkpoint_and_budget_do_not_invent_a_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            with patch.object(model,"MODEL",path):
                for attempt in range(2):
                    if attempt:
                        path.write_text("{}")
                    answer = model.propose("كلمة")
                    self.assertEqual(answer["status"], "MODEL_UNAVAILABLE")
                    self.assertIsNone(answer["relation"])
        for text in ("فتح " * (model.MAX_TERMS+1), "بٌ" * model.MAX_BYTES):
            result = model.propose(text)
            self.assertEqual((result["status"],result["candidates"]), ("RESOURCE_LIMIT",[]))

    def test_training_partition_and_first_measurement_are_reproducible(self):
        train_rows = training.examples(training.TRAIN)
        identity = sha256(training.encoded(train_rows)).hexdigest()
        self.assertEqual(model.load_model()["training_sha256"], identity)
        retained = json.loads((model.DIRECTORY/"FIRST_TEST.json").read_bytes())
        fresh = experiment.evaluate()
        for key in ("holdout_sha256","training_sha256","model_sha256","counts","pair_counts","cases"):
            self.assertEqual(fresh[key],retained[key],key)
        self.assertFalse(retained["gold_used_as_model_input"])
        self.assertGreater(fresh["counts"]["trained"]["control"]["outside_false_positive"], 0)
        with self.assertRaises(TypeError):
            model.propose("كلمة", relation=model.ASSERT)


if __name__ == "__main__":
    unittest.main()
