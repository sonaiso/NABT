"""Readout arithmetic, isolation and failure boundaries, not a semantic oracle."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import apprentice_readout as readout
from tools.lexical_training import shared_encoder as shared, train_apprentice as trainer

HAS_NUMPY = importlib.util.find_spec("numpy") is not None


class ApprenticeReadout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.encoder = readout.load()

    def test_installed_artifact_identities_and_nonzero_learned_heads(self):
        self.assertEqual(sha256(readout.MODEL.read_bytes()).hexdigest(), readout.MODEL_SHA256)
        self.assertEqual(sha256(shared.MODEL.read_bytes()).hexdigest(), readout.ENCODER_SHA256)
        self.assertEqual(self.model["authority"], "NONE")
        self.assertFalse(self.model["fit"]["encoder_updated"])
        self.assertFalse(self.model["fit"]["none_targets_are_negative"])
        self.assertEqual(self.model["fit"]["normalization_split"], "train")
        self.assertTrue(any(value for row in self.model["action_weights"] for value in row))
        for name in readout.OBLIGATIONS:
            self.assertTrue(any(value for row in self.model["obligation_weights"][name] for value in row))

    def test_text_only_proposal_has_no_authority_and_preserves_source_identity(self):
        for text in ("The second reading has no object label.", "  القراءة الثانية بلا هوية للنبتة.\n"):
            result = readout.propose(text)
            self.assertIn(result["status"], ("PROPOSED", "DEFER"))
            self.assertEqual(result["source_sha256"], sha256(text.encode("utf-8")).hexdigest())
            self.assertEqual(result["source_byte_length"], len(text.encode("utf-8")))
            self.assertEqual(result["authority"], "NONE")
            self.assertEqual(result["release_policy"], "REVIEW_ONLY")
            self.assertIs(result["automatic_selection_permitted"], False)
            self.assertEqual(result["permissions_granted"], [])
            self.assertEqual(result["means_executed"], [])
            for field in ("owner_evidence_modified", "world_truth_established", "human_mastery_established",
                          "encoder_updated", "score_is_probability_of_correctness", "out_of_domain_detection_established"):
                self.assertIs(result[field], False)
            self.assertEqual(set(result["obligations"]), set(readout.OBLIGATIONS))
            self.assertEqual({r["label"] for r in result["action_ranking"]}, set(readout.ACTIONS))
            self.assertAlmostEqual(sum(r["score"] for r in result["action_ranking"]), 1.)
        with self.assertRaises(TypeError):
            readout.propose("text", gold_action="inspect_source")
        with self.assertRaises(TypeError):
            readout.propose("text", role="manager")

    def test_external_result_mutation_does_not_poison_cached_calibration(self):
        original = deepcopy(self.model["calibration"])
        result = readout.propose("Compare the two recorded measurements.")
        result["calibration"]["obligation_thresholds"]["identity"] = 1.
        result["calibration"]["min_action_score"] = 1.
        self.assertEqual(readout.load()[0]["calibration"], original)

    def test_utf8_byte_limit_and_source_limits_precede_model_loading(self):
        malformed = [None, 1, {"text": "x"}, "", " \n", "\ud800", "ا" * 1025,
                     "a" * (readout.MAX_TEXT_BYTES + 1), "term " * 129, "أ" * 129]
        with patch.object(readout, "load", side_effect=AssertionError("must not load")):
            for value in malformed:
                result = readout.propose(value)
                self.assertEqual(result["status"], "INPUT_DEFER")
                self.assertIsNone(result["action"])
                self.assertTrue(all(v is None for v in result["obligations"].values()))
        # Exactly 2048 UTF-8 bytes, with a short token and harmless whitespace.
        boundary = "أ" + " " * (readout.MAX_TEXT_BYTES - 2)
        with patch.object(readout, "load", side_effect=OSError("observed boundary")) as loader:
            result = readout.propose(boundary)
            self.assertEqual(result["status"], "MODEL_UNAVAILABLE")
            self.assertEqual(result["source_byte_length"], readout.MAX_TEXT_BYTES)
            loader.assert_called_once_with()

    def test_model_and_encoder_changes_fail_closed(self):
        good_model, good_encoder = readout.MODEL.read_bytes(), shared.MODEL.read_bytes()
        with self.assertRaisesRegex(ValueError, "MODEL_IDENTITY_CHANGED"):
            readout._decode(good_model + b" ", good_encoder)
        with self.assertRaisesRegex(ValueError, "ENCODER_IDENTITY_CHANGED"):
            readout._decode(good_model, good_encoder + b" ")
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "changed.json"
            changed.write_bytes(good_model + b" ")
            with patch.object(readout, "MODEL", changed):
                result = readout.propose("Inspect the cited source.")
            self.assertEqual(result["status"], "MODEL_UNAVAILABLE")
            self.assertIsNone(result["action"])
            self.assertEqual(result["permissions_granted"], [])
        with patch.object(readout, "load", side_effect=OSError("unavailable")):
            result = readout.propose("Inspect the cited source.")
        self.assertEqual(result["status"], "MODEL_UNAVAILABLE")

    def test_tensor_and_label_contract_rejects_hostile_shapes(self):
        mutations = [
            lambda m: m["action_weights"][0].__setitem__(0, float("nan")),
            lambda m: m["action_weights"][0].__setitem__(0, True),
            lambda m: m["feature_scale"].__setitem__(0, 0.),
            lambda m: m["actions"].reverse(),
            lambda m: m["obligation_weights"].pop("identity"),
            lambda m: m["calibration"].__setitem__("min_action_score", True),
            lambda m: m.__setitem__("authority", "ALLOW"),
            lambda m: m.__setitem__("input_answer", "INCREASE"),
        ]
        for change in mutations:
            candidate = deepcopy(self.model)
            change(candidate)
            with self.assertRaises(ValueError):
                readout.validate_model(candidate)
        for vector in ([0.] * (readout.DIM - 1), [float("inf")] * readout.DIM,
                       [True] * readout.DIM):
            with self.assertRaises(ValueError):
                readout.vector_scores(self.model, vector)

    def test_zero_head_tie_is_defer_and_portable_bias_has_known_softmax(self):
        model = deepcopy(self.model)
        model["action_weights"] = [[0.] * (readout.DIM + 1) for _ in readout.ACTIONS]
        decision = readout.decide(model, [0.] * readout.DIM)
        self.assertEqual(decision["status"], "DEFER")
        self.assertEqual(decision["abstention_reason"], "TIED_ACTION_SCORES")
        self.assertIsNone(decision["action"])
        model["action_weights"][0][-1] = math.log(2.)
        scores, _ = readout.vector_scores(model, [0.] * readout.DIM)
        self.assertAlmostEqual(scores[0], 2. / 8.)
        for score in scores[1:]:
            self.assertAlmostEqual(score, 1. / 8.)

    def test_runtime_inference_does_not_require_numpy(self):
        script = """
import builtins
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('numpy', 'torch'):
        raise AssertionError('training dependency imported at inference')
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
from tools.lexical_training.apprentice_readout import propose
r = propose('The source does not identify its author.')
assert r['status'] in ('PROPOSED', 'DEFER'), r
assert r['authority'] == 'NONE'
"""
        environment = dict(os.environ, PYTHONPATH=str(shared.ROOT / "src") + os.pathsep + str(shared.ROOT))
        result = subprocess.run([sys.executable, "-c", script], cwd=shared.ROOT, env=environment,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


class ApprenticeTrainingIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.protocol, cls.splits, cls.protocol_sha = trainer.inputs()

    def test_family_split_and_masked_target_accounting(self):
        families = [{r["family"] for r in self.splits[name]} for name in ("train", "development", "test")]
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertFalse(families[i] & families[j])
        model, _ = readout.load()
        self.assertEqual(model["training_sha256"], trainer.identity(self.splits["train"]))
        self.assertEqual(model["development_sha256"], trainer.identity(self.splits["development"]))
        self.assertEqual(model["protocol_sha256"], self.protocol_sha)
        self.assertEqual(model["fit"]["action_targets"]["observed"], 84)
        for name in readout.OBLIGATIONS:
            labels = [r["obligations"][name] for r in self.splits["train"]]
            count = model["fit"]["obligation_targets"][name]
            self.assertEqual(count["masked"], sum(v is None for v in labels))
            self.assertEqual(count["observed"], sum(type(v) is bool for v in labels))
            self.assertEqual(count["class_counts"], {"true": sum(v is True for v in labels),
                                                     "false": sum(v is False for v in labels)})

    def test_split_leak_and_duplicate_source_are_rejected(self):
        for change in (lambda d: d["rows"][0].__setitem__("split", "test"),
                       lambda d: d["rows"][1].__setitem__("text", d["rows"][0]["text"]),
                       lambda d: d["rows"][0]["obligations"].__setitem__("identity", 1)):
            corpus = deepcopy(self.data)
            change(corpus)
            with self.assertRaises(ValueError):
                trainer.validate_data(corpus, self.protocol)

    def test_test_rows_cannot_select_thresholds(self):
        for split in ("train", "test"):
            rows = self.splits[split]
            with self.assertRaisesRegex(ValueError, "development rows only"):
                trainer.calibrate({}, rows, [[0.] * readout.DIM for _ in rows], self.protocol)

    @unittest.skipUnless(HAS_NUMPY, "NumPy is a training-only dependency")
    def test_no_development_or_test_rows_can_fit_or_normalize(self):
        for split in ("development", "test"):
            rows = self.splits[split]
            with self.assertRaisesRegex(ValueError, "Only training rows"):
                trainer.fit_readouts(rows, [[0.] * readout.DIM for _ in rows], self.protocol, self.protocol_sha)

    @unittest.skipUnless(HAS_NUMPY, "NumPy is a training-only dependency")
    def test_none_target_does_not_enter_fit_design_response_or_class_counts(self):
        vectors = [[1., 0.], [float("nan"), 1e300], [0., 1.], [2., 1.]]
        weights, counts = trainer.fit_head(vectors, [False, None, True, False], (False, True))
        filtered, other_counts = trainer.fit_head([vectors[0], vectors[2], vectors[3]],
                                                 [False, True, False], (False, True))
        self.assertEqual(weights, filtered)
        self.assertEqual(counts["class_counts"], {"false": 2, "true": 1})
        self.assertEqual(counts["class_counts"], other_counts["class_counts"])
        self.assertEqual((counts["observed"], counts["masked"]), (3, 1))
        with self.assertRaises(ValueError):
            trainer.fit_head([[1., 0.]], [None], (False, True))

    @unittest.skipUnless(HAS_NUMPY, "NumPy is a training-only dependency")
    def test_independent_numpy_matrix_matches_portable_stored_weights(self):
        model, _ = readout.load()
        vectors = [[0.] * readout.DIM, [1.] * readout.DIM,
                   [(-1.) ** i * (i + 1) / readout.DIM for i in range(readout.DIM)]]
        result = trainer.numpy_parity(model, vectors)
        self.assertTrue(result["passed"])
        self.assertLessEqual(result["maximum_absolute_score_error"], 1e-12)

    def test_evaluation_preserves_failure_and_unknown_counts(self):
        record = json.loads(trainer.EVALUATION.read_text())
        self.assertEqual(record["model_sha256"], readout.MODEL_SHA256)
        self.assertEqual(record["fit_boundary"]["test_labels_used_for_selection"], 0)
        self.assertEqual(record["fit_boundary"]["outside_domain_labels_used_for_selection"], 0)
        self.assertFalse(record["fit_boundary"]["none_replaced_with_false"])
        test = record["splits"]["test"]
        self.assertEqual(test["actions"]["rows"], 28)
        self.assertEqual(len(test["predictions"]), 28)
        self.assertGreater(test["obligations"]["masked_targets"], 0)
        self.assertLess(test["actions"]["forced_correct"], 28)
        self.assertGreater(record["outside_scope"]["unsupported_proposals"], 0)
        self.assertEqual(record["release_decision"]["policy"], "REVIEW_ONLY")
        self.assertFalse(record["release_decision"]["automatic_action_selection"])
        self.assertFalse(record["release_decision"]["model_or_thresholds_changed_after_test"])
        for split in ("train", "development", "test"):
            self.assertEqual(len(record["splits"][split]["predictions"]), len(self.splits[split]))

    def test_replay_tolerance_never_accepts_identity_or_status_changes(self):
        self.assertLess(trainer._difference({"v": [1.]}, {"v": [1. + 1e-10]}), trainer.TOLERANCE)
        for left, right in (({"status": "DEFER"}, {"status": "PROPOSED"}),
                            ({"v": 1.}, {"v": True}), ({"v": [1.]}, {"v": [1., 2.]})):
            with self.assertRaises(ValueError):
                trainer._difference(left, right)


if __name__ == "__main__":
    unittest.main()
