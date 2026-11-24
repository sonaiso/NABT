"""Independent parent oracle and adversarial contracts for cumulative V14.

The small residual fixture inherits the real installed PR-143 parent.  It is
not trained evidence: zero/controlled residuals isolate the inheritance and
validation contracts without deciding what V14 should score on a test set.
"""

from copy import deepcopy
import gzip
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import cumulative_lesson as previous
from tools.lexical_training import cumulative_v14_model as model


class CumulativeV14Model(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pm, cls.pmodel = model.parent()
        cls.layout = model.make_layout(cls.pm, cls.pmodel)
        cls.task = next(t for t in cls.pm["tasks"] if t != "root_recipe")

    def write_fixture(self, directory):
        directory = Path(directory)
        weights = {
            "adapter_columns": [[0.0] * self.layout["dimension"] for _ in range(2)],
            "adapter_bias": [0.0, 0.0],
            "residual_heads": {
                task: [[0.0, 0.0, 0.0] for _ in labels]
                for task, labels in self.pm["labels"].items()
            },
            "gates": {task: 1.0 for task in self.pm["tasks"]},
        }
        inputs = {
            "skill_layout.json": self.layout,
            "protocol.json": {"schema": "nabt.cumulative-v14-protocol.v1", "adapter_hidden": 2},
            "training.json": {"fixture": "untrained controlled residual"},
        }
        pins = {}
        for name, data in inputs.items():
            raw = (model.canonical(data) + "\n").encode()
            (directory / name).write_bytes(raw)
            pins[name] = model.digest(raw)
        raw = gzip.compress(model.canonical(weights).encode(), mtime=0)
        (directory / "weights.json.gz").write_bytes(raw)
        manifest = {
            "schema": model.SCHEMA,
            "parent": {
                "commit": model.PARENT_COMMIT,
                "weights_sha256": previous.PINS["weights.json.gz"],
                "manifest_sha256": previous.PINS["manifest.json"],
                "final_stage": 143,
            },
            "tasks": self.pm["tasks"],
            "labels": self.pm["labels"],
            "variant": "full",
            "inputs": pins,
            "weights_sha256": model.digest(raw),
        }
        (directory / "manifest.json").write_text(model.canonical(manifest) + "\n")
        return directory

    @staticmethod
    def mutate(directory, name, change, *, rebind=True):
        """Rebinding tests structural validation after the outer digest passes."""
        path = directory / name
        data = model.read(path)
        change(data)
        # Deliberately serialize malformed non-finite JSON for loader tests;
        # the production writer correctly refuses to emit it.
        raw = (json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=True) + "\n").encode()
        if name.endswith(".gz"):
            raw = gzip.compress(raw, mtime=0)
        path.write_bytes(raw)
        if rebind and name != "manifest.json":
            manifest = model.read(directory / "manifest.json")
            if name == "weights.json.gz":
                manifest["weights_sha256"] = model.digest(raw)
            else:
                manifest["inputs"][name] = model.digest(raw)
            (directory / "manifest.json").write_text(model.canonical(manifest) + "\n")

    def test_all_inherited_heads_keep_their_order_and_domain(self):
        self.assertEqual(len(self.pm["tasks"]), 164)
        self.assertEqual(len(self.pmodel["shared_columns"]), 48)
        self.assertEqual(sum(map(len, self.pm["labels"].values())), 692)
        self.assertEqual(self.layout["raw"], [0, 307])
        self.assertEqual(self.layout["parent_hidden"], [307, 355])
        self.assertEqual(self.layout["parent_skills"], [355, 1047])
        self.assertEqual(self.layout["dimension"], 1047)
        self.assertEqual([h["task"] for h in self.layout["heads"]], self.pm["tasks"])
        flat_expected = [
            (task, label) for task in self.pm["tasks"] for label in self.pm["labels"][task]
        ]
        flat_actual = [(h["task"], label) for h in self.layout["heads"] for label in h["labels"]]
        self.assertEqual(flat_actual, flat_expected)
        self.assertEqual(self.pm["final_stage"], 143)

    def test_zero_residual_matches_the_separate_parent_reader_for_every_head(self):
        x = [((i % 7) - 3) / 100 for i in range(307)]
        with tempfile.TemporaryDirectory() as temp:
            bundle = model.load(self.write_fixture(temp))
            for task in self.pm["tasks"]:
                with self.subTest(task=task):
                    oracle = previous.observe(self.pmodel, self.pm["labels"], task, x)
                    result = model.observe(bundle, task, x)
                    self.assertEqual((result["label"], result["parent_label"]), (oracle, oracle))
                    self.assertFalse(result["changed"])
                    self.assertEqual(result["authority"], "NONE")
                    self.assertIs(result["review_only"], True)

    def test_skill_values_are_centered_probabilities_with_separate_head_normalizers(self):
        # log(3) vs log(1) gives known probabilities .75/.25. The second
        # head is uniform; normalizing across heads would fail this oracle.
        toy = {
            "shared_columns": [[0.0] * 307, [0.0] * 307],
            "heads": {
                "two": [[0.0, 0.0, 0.0], [0.0, 0.0, math.log(3)]],
                "three": [[0.0, 0.0, 0.0] for _ in range(3)],
            },
        }
        layout = {"heads": [{"task": "two"}, {"task": "three"}]}
        values, hidden = model.memory_features(toy, layout, [0.0] * 307)
        self.assertEqual(hidden, [0.0, 0.0])
        self.assertEqual(len(values), 314)
        for actual, expected in zip(values[309:], [-0.25, 0.25, 0.0, 0.0, 0.0], strict=True):
            self.assertAlmostEqual(actual, expected)

    def test_controlled_residual_changes_only_the_proposal_and_gate_zero_keeps_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = model.load(self.write_fixture(temp))
            x = [0.0] * 307
            inherited = previous.observe(self.pmodel, self.pm["labels"], self.task, x)
            alternative = next(label for label in self.pm["labels"][self.task] if label != inherited)
            index = self.pm["labels"][self.task].index(alternative)
            bundle["weights"]["residual_heads"][self.task][index][-1] = 10000.0
            result = model.observe(bundle, self.task, x)
            self.assertEqual((result["label"], result["parent_label"]), (alternative, inherited))
            self.assertTrue(result["changed"])
            self.assertEqual(result["authority"], "NONE")
            self.assertIs(result["review_only"], True)
            bundle["weights"]["gates"][self.task] = 0.0
            self.assertEqual(model.observe(bundle, self.task, x)["label"], inherited)

    def test_root_projection_keeps_the_actual_parent_answer(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = model.load(self.write_fixture(temp))
            request = {"schema": previous.SCHEMA, "task": "root_recipe", "text": "ضَرَبَ"}
            oracle = previous.run(request)
            result = model.propose(bundle, request["task"], request["text"])
            self.assertEqual(oracle["status"], "PROPOSED")
            self.assertEqual((result["label"], result["value"]), (oracle["label"], oracle["value"]))
            self.assertEqual(result["parent_value"], oracle["value"])
            self.assertEqual(result["value"], "ضرب")

    def test_warm_feature_cache_does_not_hide_changed_lower_parent_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = self.write_fixture(temp)
            bundle = model.load(directory)
            model.propose(bundle, "root_recipe", "ضَرَبَ")
            actual_read = Path.read_bytes
            files = [
                model.features.v13.DIRECTORY / "parent.json",
                model.features.v13.DIRECTORY / "checkpoint.json",
                model.features.v13.DIRECTORY / "protocol.json",
                model.features.recursive.MODEL,
                model.ROOT / "evidence/ntp_recursive_v1/protocol.json",
                model.ROOT / "evidence/shared_cell_reading_v1/train.json",
            ]
            for target in files:
                with self.subTest(lower_parent=target.name):
                    def changed_bytes(path, selected=target):
                        raw = actual_read(path)
                        return raw + b"\n" if path == selected else raw

                    # No actual parent is modified, and the JSON stays valid.
                    # Fresh admission must check bytes even with warm features.
                    with patch.object(Path, "read_bytes", changed_bytes):
                        with self.assertRaises(ValueError):
                            model.load(directory)

    def test_changed_lineage_task_order_and_label_identities_are_rejected(self):
        changes = [
            lambda m: m["parent"].__setitem__("weights_sha256", "0" * 64),
            lambda m: m["parent"].__setitem__("final_stage", 142),
            lambda m: m["tasks"].reverse(),
            lambda m: m["labels"][self.task].reverse(),
        ]
        with tempfile.TemporaryDirectory() as temp:
            for i, change in enumerate(changes):
                with self.subTest(change=i):
                    directory = self.write_fixture(temp)
                    self.mutate(directory, "manifest.json", change)
                    with self.assertRaises(ValueError):
                        model.load(directory)

    def test_rebound_layout_changes_still_fail_semantic_layout_identity(self):
        changes = [
            lambda l: l["heads"].reverse(),
            lambda l: l["heads"][0]["labels"].reverse(),
            lambda l: l.__setitem__("dimension", l["dimension"] + 1),
            # Python equates False and 0; the serialized domain does not.
            lambda l: l["raw"].__setitem__(0, False),
        ]
        with tempfile.TemporaryDirectory() as temp:
            for i, change in enumerate(changes):
                with self.subTest(change=i):
                    directory = self.write_fixture(temp)
                    self.mutate(directory, "skill_layout.json", change)
                    with self.assertRaises(ValueError):
                        model.load(directory)

    def test_unbound_weight_change_and_unexpected_input_path_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = self.write_fixture(temp)
            self.mutate(directory, "weights.json.gz", lambda w: w["adapter_bias"].__setitem__(0, 0.1), rebind=False)
            with self.assertRaisesRegex(ValueError, "weights"):
                model.load(directory)
            directory = self.write_fixture(temp)
            self.mutate(directory, "manifest.json", lambda m: m["inputs"].__setitem__("../other.json", "0" * 64))
            with self.assertRaisesRegex(ValueError, "input path"):
                model.load(directory)

    def test_training_input_symlink_is_rejected_even_when_its_bytes_match(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            directory = self.write_fixture(temp)
            model.load(directory)
            training_path = directory / "training.json"
            raw = training_path.read_bytes()
            external = Path(outside) / "identical-training.json"
            external.write_bytes(raw)
            training_path.unlink()
            training_path.symlink_to(external)
            # The original input digest remains valid, so rejecting this
            # fixture requires the path boundary check rather than hashing.
            expected = model.read(directory / "manifest.json")["inputs"]["training.json"]
            self.assertEqual(model.digest(training_path.read_bytes()), expected)
            with self.assertRaisesRegex(ValueError, "escapes its installed directory"):
                model.load(directory)

    def test_rebound_malformed_weights_are_rejected_before_inference(self):
        changes = [
            lambda w: w["adapter_columns"].pop(),
            lambda w: w["adapter_columns"][0].pop(),
            lambda w: w["adapter_bias"].append(0.0),
            lambda w: w["residual_heads"][self.task].pop(),
            lambda w: w["residual_heads"][self.task][0].append(0.0),
            lambda w: w["residual_heads"].pop(self.task),
            lambda w: w["gates"].__setitem__("unseen", 0.0),
        ]
        for invalid in (True, float("nan"), float("inf"), -float("inf"), "0"):
            changes.append(lambda w, v=invalid: w["adapter_columns"][0].__setitem__(0, v))
            changes.append(lambda w, v=invalid: w["adapter_bias"].__setitem__(0, v))
            changes.append(lambda w, v=invalid: w["residual_heads"][self.task][0].__setitem__(0, v))
        for invalid in (True, float("nan"), float("inf"), -1, 0.125, 2):
            changes.append(lambda w, v=invalid: w["gates"].__setitem__(self.task, v))
        with tempfile.TemporaryDirectory() as temp:
            for i, change in enumerate(changes):
                with self.subTest(change=i):
                    directory = self.write_fixture(temp)
                    self.mutate(directory, "weights.json.gz", change)
                    with self.assertRaises(ValueError):
                        model.load(directory)

    def test_invalid_protocol_width_and_feature_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for invalid in (True, 0, 257, 2.0):
                with self.subTest(width=invalid):
                    directory = self.write_fixture(temp)
                    self.mutate(directory, "protocol.json", lambda p: p.__setitem__("adapter_hidden", invalid))
                    with self.assertRaises(ValueError):
                        model.load(directory)
            bundle = model.load(self.write_fixture(temp))
            invalid_vectors = [[0.0] * 306, [0.0] * 308]
            for invalid in (True, float("nan"), float("inf"), "0"):
                invalid_vectors.append([invalid] + [0.0] * 306)
            for i, x in enumerate(invalid_vectors):
                with self.subTest(vector=i):
                    with self.assertRaises(ValueError):
                        model.observe(bundle, self.task, x)
            with self.assertRaises(ValueError):
                model.observe(bundle, self.task, [0.0] * 307, ablate="answer_key")

    def test_ablation_preserves_full_parent_record_and_does_not_mutate_bundle(self):
        x = [((i % 11) - 5) / 10 for i in range(307)]
        with tempfile.TemporaryDirectory() as temp:
            bundle = model.load(self.write_fixture(temp))
            before_bundle, before_x = deepcopy(bundle), list(x)
            expected = previous.observe(self.pmodel, self.pm["labels"], self.task, x)
            baseline = model.observe(bundle, self.task, x)
            for channel in sorted(model.ABLATIONS):
                with self.subTest(channel=channel):
                    result = model.observe(bundle, self.task, x, ablate=channel)
                    self.assertEqual(result["parent_label"], expected)
                    self.assertEqual(bundle, before_bundle)
                    self.assertEqual(x, before_x)
                    self.assertEqual(model.observe(bundle, self.task, x), baseline)


@unittest.skipUnless(importlib.util.find_spec("numpy"), "training-only NumPy required")
class CumulativeV14Training(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        from tools.lexical_training import cumulative_v14_train as trainer

        cls.np, cls.trainer = np, trainer

    def setUp(self):
        self.protocol = model.read(self.trainer.PROTOCOL)
        self.protocol.update(adapter_hidden=3, updates=4)
        self.pm = {
            "tasks": ["fixture:a", "fixture:b"],
            "labels": {"fixture:a": ["A", "B"], "fixture:b": ["x", "y"]},
        }
        columns = [[0.0] * 307 for _ in range(2)]
        columns[0][0], columns[0][1], columns[1][2] = 0.3, -0.2, 0.5
        self.parent = {
            "shared_columns": columns,
            "heads": {
                "fixture:a": [[2.0, -0.5, 0.1], [-1.0, 0.75, -0.2]],
                "fixture:b": [[-0.4, 1.2, -0.1], [0.8, -0.6, 0.15]],
            },
        }
        self.pack = {"rows": []}
        for i in range(30):
            text = f"fixture-training-{i:02d}"
            for task, label in (("fixture:a", "AB"[i % 2]), ("fixture:b", "xy"[int(i % 3 == 0)])):
                self.pack["rows"].append({"task": task, "text": text, "gold": label, "split": "train"})
        for i in range(3):
            self.pack["rows"].append({
                "task": "fixture:a", "text": f"fixture-assessment-{i}", "gold": "AB"[i % 2], "split": "test"
            })

    @staticmethod
    def extract(text, _lower):
        # A deterministic feature fixture. It sees text only, never labels.
        raw = bytes.fromhex(model.digest(text.encode()))
        return [(v / 255) - 0.5 for v in raw[:8]] + [0.0] * 299

    def prepare(self, pack=None):
        with patch.object(model, "parent", return_value=(deepcopy(self.pm), deepcopy(self.parent))):
            with patch.object(self.trainer.features, "parents", return_value=()):
                with patch.object(self.trainer.features, "features", side_effect=self.extract) as extractor:
                    data = self.trainer.prepare(self.protocol, self.pack if pack is None else pack)
        self.assertEqual(set(call.args[0] for call in extractor.call_args_list), set(data["texts"]))
        return data

    def assert_same_state(self, a, b):
        self.assertEqual((a["step"], a["history"]), (b["step"], b["history"]))
        for field in ("parameters", "first_moments", "second_moments"):
            self.assertEqual(set(a[field]), set(b[field]))
            for name in a[field]:
                self.np.testing.assert_array_equal(a[field][name], b[field][name])

    def fit(self, data, updates=4):
        state = self.trainer.initial_state(data, self.protocol)
        view = self.trainer.feature_view(data, "full")
        for _ in range(updates):
            self.trainer.fit_step(state, data, self.protocol, view)
        return state

    def test_assessment_answers_cannot_change_training_partition_weights_or_calibration(self):
        changed = deepcopy(self.pack)
        for row in changed["rows"]:
            if row["split"] == "test":
                row["gold"] = {"unseen_class_and_answer": True}
        a, b = self.prepare(), self.prepare(changed)
        self.assertEqual(a["signature"], b["signature"])
        self.assertEqual(a["partition"], b["partition"])
        self.assertTrue(all("assessment" not in text for text in a["texts"]))
        self.np.testing.assert_array_equal(a["features"], b["features"])
        left, right = self.fit(a), self.fit(b)
        self.assert_same_state(left, right)
        self.assertEqual(
            self.trainer.calibrate(left, a, self.trainer.feature_view(a, "full")),
            self.trainer.calibrate(right, b, self.trainer.feature_view(b, "full")),
        )

    def test_partition_correction_moves_a_shared_text_globally(self):
        i = 0
        while True:
            forced = f"forced-development-{i}"
            if int(model.digest(("v14-development:" + forced).encode()), 16) % 5 == 0:
                break
            i += 1
        pack = deepcopy(self.pack)
        for row in pack["rows"]:
            if row["split"] == "train" and row["task"] == "fixture:a":
                row["gold"] = "A"
        pack["rows"].extend([
            {"task": "fixture:a", "text": forced, "gold": "B", "split": "train"},
            {"task": "fixture:b", "text": forced, "gold": "x", "split": "train"},
        ])
        data = self.prepare(pack)
        self.assertIn(model.digest(forced.encode()), data["partition"]["fit_text_sha256"])
        self.assertNotIn(model.digest(forced.encode()), data["partition"]["development_text_sha256"])
        self.assertIn(forced, data["groups"]["fixture:a", "fit"]["texts"])
        self.assertIn(forced, data["groups"]["fixture:b", "fit"]["texts"])
        assignments = {}
        for task in data["tasks"]:
            for split in ("fit", "development"):
                for text in data["groups"][task, split]["texts"]:
                    self.assertEqual(assignments.setdefault(text, split), split)

    def test_overlap_and_dropped_parent_class_are_rejected(self):
        overlap = deepcopy(self.pack)
        overlap["rows"].append(dict(overlap["rows"][0], split="test"))
        dropped = deepcopy(self.pack)
        dropped["rows"] = [
            row for row in dropped["rows"]
            if not (row["split"] == "train" and row["task"] == "fixture:a" and row["gold"] == "B")
        ]
        for pack in (overlap, dropped):
            with self.subTest(case="overlap" if pack is overlap else "dropped class"):
                with patch.object(model, "parent", return_value=(self.pm, self.parent)):
                    with self.assertRaises(ValueError):
                        self.trainer.prepare(self.protocol, pack)

    def test_four_updates_equal_two_then_serialized_resume_then_two(self):
        data = self.prepare()
        inherited_before = deepcopy(data["parent_model"])
        view = self.trainer.feature_view(data, "full")
        continuous, interrupted = self.fit(data, 4), self.fit(data, 2)
        with tempfile.TemporaryDirectory() as temp:
            self.trainer.save_checkpoint(temp, interrupted, data, "full")
            restored = self.trainer.restore_checkpoint(temp, data, self.protocol, "full")
            self.assert_same_state(interrupted, restored)
            for _ in range(2):
                self.trainer.fit_step(restored, data, self.protocol, view)
            self.assert_same_state(continuous, restored)
            self.assertEqual(
                self.trainer.calibrate(continuous, data, view),
                self.trainer.calibrate(restored, data, view),
            )
        self.assertEqual(data["parent_model"], inherited_before)
        fresh = self.trainer.initial_state(data, self.protocol)
        self.assertTrue(any(
            not self.np.array_equal(fresh["parameters"][name], continuous["parameters"][name])
            for name in fresh["parameters"]
        ))

    def test_calibration_keeps_parent_when_unchanged_or_insufficient(self):
        data = self.prepare()
        fresh = self.trainer.initial_state(data, self.protocol)
        gates, details = self.trainer.calibrate(fresh, data, self.trainer.feature_view(data, "full"))
        self.assertEqual(set(gates.values()), {0.0})
        # Removing calibration observations must retain a trained parent;
        # it must not silently choose a gate using assessment answers.
        group = data["groups"]["fixture:a", "development"]
        group["indices"] = self.np.array([], dtype=self.np.int64)
        group["targets"] = self.np.array([], dtype=self.np.int64)
        group["texts"] = []
        gates, details = self.trainer.calibrate(fresh, data, self.trainer.feature_view(data, "full"))
        self.assertEqual(gates["fixture:a"], 0.0)
        self.assertEqual(details["fixture:a"]["status"], "PARENT_RETAINED_INSUFFICIENT_CALIBRATION")

    def test_checkpoint_rejects_rebound_identity_and_malformed_optimizer_state(self):
        data = self.prepare()
        state = self.fit(data, 2)
        changes = [
            lambda c: c["signature"].__setitem__("parent_weights_sha256", "0" * 64),
            lambda c: c["signature"].__setitem__("partition_sha256", "0" * 64),
            lambda c: c["signature"].__setitem__("layout_sha256", "0" * 64),
            lambda c: c["tasks"].reverse(),
            lambda c: c.__setitem__("step", True),
            lambda c: c["history"][0].__setitem__("step", True),
            lambda c: c["parameters"]["adapter"].pop(),
            lambda c: c["first_moments"]["bias"].__setitem__(0, True),
            lambda c: c["second_moments"]["bias"].__setitem__(0, -1.0),
            lambda c: c["first_moments"]["bias"].__setitem__(0, float("nan")),
            lambda c: c["parameters"].pop("head:fixture:b"),
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "checkpoint.json.gz"
            for i, change in enumerate(changes):
                with self.subTest(change=i):
                    self.trainer.save_checkpoint(temp, state, data, "full")
                    altered = model.read(path)
                    change(altered)
                    path.write_bytes(gzip.compress(json.dumps(altered, allow_nan=True).encode(), mtime=0))
                    with self.assertRaises(ValueError):
                        self.trainer.restore_checkpoint(temp, data, self.protocol, "full")
            self.trainer.save_checkpoint(temp, state, data, "full")
            with self.assertRaises(ValueError):
                self.trainer.restore_checkpoint(temp, data, self.protocol, "without_task_memory")


if __name__ == "__main__":
    unittest.main()
