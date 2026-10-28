"""Synthetic development controls, separate from the frozen forty scenarios."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import evidence_lifecycle_v1 as life


def scenario():
    query_source = {"identity": "question", "revision": "1", "content": "A question, not its evidence."}
    root = {"identity": "record", "revision": "1", "content": "A synthetic record."}
    copy = {"identity": "copy", "revision": "1", "content": "A declared copy of record."}
    key = {"axis": "recorded_observation", "entity": "fixture", "predicate": "flag",
           "value": "on", "unit": "state", "context": "development-control", "time": "3", "place": "fixture"}
    return {"schema": life.EPISODE_SCHEMA, "episode_id": "development-only",
        "query": {"key": key, "positive": True, "origin": "question"},
        "active_sources": [query_source, root, copy],
        "origins": [{"id": "question", "parents": []}, {"id": "record", "parents": []},
                    {"id": "copy", "parents": ["record"]}],
        "bindings": [{"origin_id": name, "source": source, "rank": rank}
                     for name, source, rank in (("question", query_source, 0), ("record", root, 0), ("copy", copy, 1))],
        "interpretations": [{"id": "copied-evidence", "source": copy, "key": key, "positive": True,
                             "kind": "observation", "origin": "copy", "ancestry": ["record", "copy"]}],
        "budget": 1, "updates": []}


def event(identity, kind, source, replacement=None):
    return {"event_id": identity, "kind": kind, "source": deepcopy(source),
            "replacement": deepcopy(replacement), "reason": "Synthetic development operation."}


class ProposalTests(unittest.TestCase):
    def test_parent_withdrawal_idempotence_and_restore_order(self):
        episode = scenario()
        source = episode["active_sources"][1]
        episode["updates"] = [event("w1", "withdraw", source), event("w2", "withdraw", source),
                              event("a", "activate", source)]
        original = deepcopy(episode)
        steps = life.propose_episode(episode)["steps"]
        self.assertEqual(episode, original)
        self.assertEqual([s["receipt"]["status"] for s in steps], ["SUPPORTED", "UNKNOWN", "UNKNOWN", "SUPPORTED"])
        self.assertEqual([s["affected_ids"] for s in steps], [[], ["copied-evidence"], [], ["copied-evidence"]])
        self.assertEqual([s["identity"] for s in steps[-1]["active_sources"]], ["question", "copy", "record"])
        self.assertEqual(steps[1]["dependency_blocked_ids"], ["copied-evidence"])

    def test_replacement_does_not_rewrite_old_binding(self):
        episode = scenario()
        source = episode["active_sources"][1]
        replacement = {**source, "revision": "2", "content": "Replacement record."}
        episode["updates"] = [event("r", "replace", source, replacement)]
        result = life.propose_episode(episode)
        self.assertEqual(result["steps"][-1]["receipt"]["status"], "UNKNOWN")
        self.assertEqual(result["binding"]["bindings"][1]["source"], source)
        self.assertEqual(result["steps"][-1]["active_sources"][-1], replacement)

    def test_budget_applies_before_dependency_filter(self):
        episode = scenario()
        episode["budget"] = 0
        episode["active_sources"] = []
        row = life.propose_episode(episode)["steps"][0]
        self.assertEqual(row["receipt"], {"status": "RESOURCE_LIMIT", "support_ids": [], "refutation_ids": [], "selected_ids": []})
        for name in ("dependency_ready_ids", "dependency_blocked_ids", "affected_ids"):
            self.assertIsNone(row[name])

    def test_later_invalid_event_does_not_publish_partial_history(self):
        episode = scenario()
        source = episode["active_sources"][1]
        episode["updates"] = [event("w", "withdraw", source), event("bad", "activate", {**source, "revision": "missing"})]
        report = life.evaluate_episode(episode)
        self.assertEqual(report["status"], "INVALID_INPUT")
        self.assertIsNone(report["observed"])
        self.assertIsNone(report["execution"]["input"])

    def test_direct_python_depth_matches_wire_container_limit(self):
        value = {}
        for _ in range(31):
            value = [value]
        life._json_shape(value)
        with self.assertRaises(life.ResourceLimit):
            life._json_shape([value])
        with self.assertRaises(life.ResourceLimit):
            life.strict_loads("[" * 32 + "{}" + "]" * 32)


@unittest.skipUnless(life.NATIVE.is_file(), "build evidenceLifecycleV1")
class NativeTests(unittest.TestCase):
    def test_complete_native_replay_and_independent_expected_episode(self):
        episode = scenario()
        source = episode["active_sources"][1]
        episode["updates"] = [event("w", "withdraw", source), event("a", "activate", source)]
        report = life.evaluate_episode(episode)
        self.assertTrue(report["native_checked"], report["execution"]["error"])
        self.assertTrue(report["decision_complete"])
        self.assertEqual(life.wire(report["observed"]), life.wire(life.propose_episode(episode)))
        self.assertTrue(life.verify_episode(report, expected_episode=episode)["valid"])
        later = deepcopy(episode)
        later["updates"].append(event("noop", "activate", source))
        self.assertFalse(life.verify_episode(report, expected_episode=later)["replay_matches"])

    def test_active_source_binding_content_collision_isolated(self):
        episode = scenario()
        episode["bindings"][1]["source"] = {**episode["active_sources"][1], "content": "Different bytes at same identity/revision."}
        self.assertEqual(life.evaluate_episode(episode)["status"], "INVALID_INPUT")
        native = life._native(episode)
        self.assertEqual(native["status"], "INVALID_INPUT")
        self.assertNotIn("steps", native)

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path, receipt = Path(directory) / "episode.json", Path(directory) / "receipt.json"
            path.write_text(json.dumps(scenario()))
            command = [sys.executable, "-B", "-m", "tools.evidence_lifecycle_cli"]
            result = subprocess.run(command + ["evaluate", str(path)], cwd=life.ROOT, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout.decode())
            receipt.write_bytes(result.stdout)
            result = subprocess.run(command + ["verify", str(receipt), "--episode", str(path)],
                                    cwd=life.ROOT, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout.decode())


if __name__ == "__main__":
    unittest.main()
