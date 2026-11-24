"""Witnesses for checkpoint retention, changed fields, and continuation."""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from tools.grammar_catalog import gateway, ntp
from tools.lexical_training import teaching, v13_occurrence as owner

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/io_gateway/v13_occurrence.json"


class V13Occurrence(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(EXAMPLE.read_text())
        self.lesson = self.request["payload"]["input"]["lesson"]

    def test_frozen_example_preserves_source_ancestry_and_change(self):
        result = teaching.run_lesson(self.lesson)
        self.assertEqual(result["status"], "PROPOSED")
        self.assertEqual(result["authority"], "NONE")
        self.assertTrue(result["predicted_units_changed"])
        self.assertEqual([u["source116_parent_ids"] for u in result["before"]["units"]], [[11], [8], [99]])
        self.assertEqual([u["source116_parent_ids"] for u in result["after"]["units"]], [[11], [8, 3]])
        self.assertTrue(teaching.verify_lesson(result, expected_lesson=self.lesson)["valid"])
        other = deepcopy(self.lesson)
        other["before"]["boundary"] = "FASL"
        self.assertFalse(teaching.verify_lesson(result, expected_lesson=other)["valid"])

    def test_ineffective_withdrawal_and_reverse(self):
        for first in (False, True):
            one = dict(self.lesson["after"], source116_id=9, tanwin=first)
            result = teaching.run_lesson(dict(self.lesson, before=one, after=dict(one, tanwin=not first)))
            self.assertEqual(result["changed_field"], "tanwin")
            self.assertFalse(result["predicted_units_changed"])
            self.assertEqual(result["before"]["units"], result["after"]["units"])

    def test_invalid_and_outside_are_separate(self):
        for field, value in (("source116_id", False), ("source116_id", 116), ("shadda", 1), ("boundary", None)):
            one = dict(self.lesson["before"], **{field: value})
            self.assertEqual(teaching.run_lesson(dict(self.lesson, before=one))["status"], "INVALID_INPUT")
        for value in (0, 3, 11, 115):
            one = dict(self.lesson["before"], source116_id=value)
            self.assertEqual(teaching.run_lesson(dict(self.lesson, before=one))["status"], "DEFER_OUTSIDE_PROBE")
        for after in (self.lesson["before"], dict(self.lesson["before"], source116_id=12),
                      dict(self.lesson["after"], tanwin=False)):
            self.assertEqual(teaching.run_lesson(dict(self.lesson, after=after))["status"], "INVALID_INPUT")

    def test_missing_or_changed_child_keeps_old_observations(self):
        original = owner.DIRECTORY
        with TemporaryDirectory() as directory, patch.object(owner, "DIRECTORY", Path(directory)):
            for name in ("parent.json", "protocol.json"):
                (owner.DIRECTORY / name).write_bytes((original / name).read_bytes())
            for damaged in (False, True):
                if damaged:
                    (owner.DIRECTORY / "checkpoint.json").write_text("{}")
                result = teaching.run_lesson(self.lesson)
                self.assertEqual(result["status"], "READOUT_UNAVAILABLE")
                self.assertIn("after", result)
                self.assertNotIn("predicted_units_changed", result)
                self.assertEqual(teaching.run_lesson({"schema": owner.SCHEMA, "before": self.lesson["before"]})["status"], "PROPOSED")
            (owner.DIRECTORY / "parent.json").write_text("{}")
            self.assertEqual(teaching.run_lesson(self.lesson)["status"], "MODEL_UNAVAILABLE")

    def test_public_replay_and_catalog(self):
        report = gateway.run(self.request)
        self.assertEqual(report["status"], "EXECUTED")
        observation = report["execution"]["owner_result"]
        self.assertTrue(observation["owner_result"]["predicted_units_changed"])
        self.assertTrue(gateway.accept_output(report, expected_request=self.request)["valid"])
        forged = deepcopy(self.request)
        forged["payload"]["input"]["lesson"]["before"]["boundary"] = "FASL"
        self.assertFalse(gateway.accept_output(report, expected_request=forged)["valid"])
        self.assertEqual(ntp._lesson_sources(self.lesson, observation["owner_result"]), ([], "NO_REQUEST_TEXT_SOURCE"))

    def test_shipped_weights_against_all_original_occurrences_and_contrasts(self):
        # Uses stdlib only, so the release regression also runs without the trainer.
        archive = owner.DIRECTORY / "NABT_V13_Learning_Probe_01.zip"
        with ZipFile(archive) as source:
            rows = json.loads(source.read("NABT_V13_Learning_Probe_01/results/dataset.json"))
        nets = owner.checked_json("parent.json", owner.PARENT_SHA)["nets"]
        child = owner.checked_json("checkpoint.json", owner.MODEL_SHA)
        groups = defaultdict(list)
        for row in rows:
            f = row["input"]
            item = {"source116_id": row["source116_input_id"], "boundary": owner.BOUNDS[f["boundary"]],
                    "tanwin": bool(f["tanwin"]), "shadda": bool(f["shadda"])}
            actual, hidden = owner.observe(nets, item)
            self.assertEqual(actual["units"], row["expected_units"])
            groups[f["carrier"]].append((item, hidden, row["expected_units"]))
        count = 0
        for group in groups.values():
            for (a, left, gold_a), (b, right, gold_b) in combinations(group, 2):
                if sum(a[k] != b[k] for k in a) == 1:
                    self.assertEqual(owner.changed(child, owner.difference(left, right)), gold_a != gold_b)
                    count += 1
        self.assertEqual((len(rows), count), (1008, 3024))

    def test_parent_replay_and_checkpoint_resume(self):
        try:
            from tools.lexical_training import train_v13_occurrence as trainer
        except ModuleNotFoundError as exc:
            if exc.name == "numpy":
                self.skipTest("NumPy needed for the offline training regression")
            raise
        # Two uninterrupted steps and a saved, reloaded one-step run must agree.
        first, _ = trainer.experiment(steps=1)
        raw = trainer.json_bytes(first)
        continued, evaluation = trainer.experiment(raw, steps=1)
        direct, _ = trainer.experiment(steps=2)
        self.assertEqual(continued["started_from_sha256"], sha256(raw).hexdigest())
        self.assertEqual(continued["steps"], 2)
        self.assertEqual(continued["weights"], direct["weights"])
        self.assertEqual(continued["bias"], direct["bias"])
        self.assertEqual(list(evaluation["old_checkpoint_exact"].values()), [1008]*9)
        self.assertEqual(evaluation["deployed_parent_ancestry_exact"], 1008)
        self.assertEqual(evaluation["splits"]["train_familiar"]["distinct_functional_pairs"], 72)
        with self.assertRaises(ValueError):
            trainer.resume(trainer.json_bytes(dict(first, parent_sha256="0"*64)))
