"""Installed source lifecycle controls; not the independent acceptance matrix."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import evidence_lifecycle_v1 as life
from tools import productive_lifecycle_v1 as productive

TEXT = "ضَرَبَ زَيْدٌ عَمْرًا."
BINDING = dict(source_id="lifecycle-test", revision="1", scope="declared-utterance", ending="wasl", onset="word_initial")
READY = all((productive.ROOT / "formal/.lake/build/bin" / name).is_file() for name in productive.NATIVE_NAMES)


def event(identity, kind, target):
    return {"event_id": identity, "kind": kind, "target": target, "reason": "Explicit development source operation."}


class SourceProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets = productive.installed_targets()

    def test_full_installed_inventory_and_explicit_byte_only_erratum(self):
        rows = self.targets["targets"]
        self.assertEqual(len(rows), 50)
        self.assertEqual([row["target"] for row in rows[:7]],
                         ["sibawayhi", "qatr", "mukhtar_sihah", "sabban", "ibn_aqil", "linguistic_inventory", "maqayis"])
        passages = self.targets["source_replay"]["passages"]
        self.assertEqual(len(passages), 38)
        byte_only = {p["target"] for p in passages if p["line_start"] is None or p["line_end"] is None}
        self.assertEqual(byte_only, {"acquisition-passage:natural_eye_senses",
                                   "acquisition-passage:natural_eye_definition",
                                   "acquisition-passage:natural_spring_definition"})
        for row in passages:
            if row["target"] in byte_only:
                self.assertIsNone(row["line_start"])
                self.assertIsNone(row["line_end"])
            else:
                self.assertIs(type(row["line_start"]), int)
                self.assertIs(type(row["line_end"]), int)
            self.assertEqual(sha256(row["raw_text"].encode()).hexdigest(), row["span_sha256"])

    def test_missing_expected_line_metadata_is_not_generalized_to_null(self):
        raw = "سطر\nآخر\n".encode()
        row = {"id": "another_passage", "source_id": "example", "raw_text": raw.decode(),
               "source_sha256": sha256(raw).hexdigest(), "span_sha256": sha256(raw).hexdigest(),
               "byte_start_0based": 0, "byte_end_0based_exclusive": len(raw),
               "line_start_1based": 1, "line_end_1based_inclusive": 2}
        self.assertEqual(productive._quotation(row, raw, "acquisition")["line_start"], 1)
        for field in ("line_start_1based", "line_end_1based_inclusive"):
            missing = {key: value for key, value in row.items() if key != field}
            with self.assertRaises((KeyError, ValueError)):
                productive._quotation(missing, raw, "acquisition")
            with self.assertRaises(ValueError):
                productive._quotation({**row, field: None}, raw, "acquisition")

    def test_graph_is_whole_packet_dependency_not_sentence_selection(self):
        inventory = productive._inventory()
        request = productive.clause._request(TEXT, **BINDING)
        episode = productive._episode(request, [], inventory)
        self.assertEqual(len(episode["origins"]), 53)
        self.assertEqual(len(episode["bindings"]), 53)
        self.assertEqual(len(episode["interpretations"]), 1)
        grammar = episode["interpretations"][0]
        self.assertEqual(grammar["kind"], "grammar")
        self.assertEqual(len(grammar["ancestry"]), 52)
        self.assertNotIn("origin:query:productive-clause-v1", grammar["ancestry"])
        ranks = {b["origin_id"]: b["rank"] for b in episode["bindings"]}
        for node in episode["origins"]:
            self.assertTrue(all(ranks[p] < ranks[node["id"]] for p in node["parents"]))
        self.assertEqual(episode["origins"][-1]["parents"],
                         ["origin:input:productive-clause-v1", "origin:packet:sourced-acquisition-v3", "origin:packet:productive-clause-v1"])
        self.assertEqual(life.propose_episode(episode)["steps"][0]["receipt"]["status"], "UNKNOWN")

    def test_missing_or_modified_retained_source_blocks_current_chain(self):
        original = productive._read
        def unavailable(path, maximum):
            if path.endswith("qatr.txt"):
                raise FileNotFoundError("controlled missing retained book")
            return original(path, maximum)
        with patch.object(productive, "_read", side_effect=unavailable):
            result = productive.evaluate_clause(TEXT, **BINDING)
        self.assertEqual(result["status"], "SOURCE_EVIDENCE_UNAVAILABLE")
        self.assertFalse(result["chain_complete"])
        self.assertIsNone(result["source_replay"])
        self.assertFalse(result["chain_history"])
        def changed(path, maximum):
            raw = original(path, maximum)
            return raw + b" " if path.endswith("qatr.txt") else raw
        with patch.object(productive, "_read", side_effect=changed):
            self.assertEqual(productive.evaluate_clause(TEXT, **BINDING)["status"], "SOURCE_EVIDENCE_UNAVAILABLE")

    def test_caller_cannot_supply_graph_sources_or_unknown_targets(self):
        for events in ([{**event("x", "withdraw", "qatr"), "verified": True}],
                       [event("x", "replace", "qatr")], [event("x", "withdraw", "input:productive-clause-v1")],
                       [event("x", "withdraw", "uninstalled")], [event("x", "withdraw", "qatr")] * 2):
            result = productive.evaluate_clause(TEXT, events=events, **BINDING)
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertFalse(result["chain_complete"])

    def test_explicit_null_or_nonarray_events_are_invalid_before_dependencies(self):
        with patch.object(productive, "_inventory") as inventory:
            for events in (None, (), {}, True, "[]"):
                self.assertEqual(productive.evaluate_clause(TEXT, events=events, **BINDING)["status"], "INVALID_INPUT")
            inventory.assert_not_called()


@unittest.skipUnless(READY, "build all lifecycle and productive clause native dependencies")
class NativeConnectionTests(unittest.TestCase):
    def test_every_installed_target_withdraws_and_restores_checked_clause(self):
        targets = productive.installed_targets()["targets"]
        self.assertEqual(len(targets), 50)
        for target in targets:
            identity = target["target"]
            with self.subTest(target=identity):
                events = [event("withdraw", "withdraw", identity), event("restore", "activate", identity)]
                result = productive.evaluate_clause(TEXT, events=events, **BINDING)
                self.assertEqual(result["status"], "LICENSED_CLAUSE", result["error"])
                self.assertTrue(result["chain_complete"])
                self.assertEqual([h["status"] for h in result["chain_history"]],
                                 ["LICENSED_CLAUSE", "PENDING_DEPENDENCIES", "LICENSED_CLAUSE"])
                pending = result["chain_history"][1]
                self.assertEqual(pending["candidate_space"]["count"], 1)
                self.assertEqual(pending["candidate_space"]["candidates"][0]["state"], "PENDING")
                self.assertFalse(pending["chain_complete"])
                self.assertTrue(result["original_clause"]["chain_complete"])
                for step in result["lifecycle"]["observed"]["steps"]:
                    self.assertEqual(step["receipt"]["status"], "UNKNOWN")

    def test_source_blocked_rejection_is_pending_and_restores_without_license(self):
        events = [event("withdraw", "withdraw", "qatr"), event("restore", "activate", "qatr")]
        text = "ضَرَبَ زَيْدٌ بَكْرٌ."
        result = productive.evaluate_clause(text, events=events, **BINDING)
        self.assertEqual(result["original_clause"]["status"], "REJECTED_IN_SCOPE")
        self.assertEqual([h["status"] for h in result["chain_history"]],
                         ["REJECTED_IN_SCOPE", "PENDING_DEPENDENCIES", "REJECTED_IN_SCOPE"])
        for row in result["chain_history"]:
            self.assertEqual(row["candidate_space"]["count"], 0)
            self.assertFalse(row["chain_complete"])
        suspended = productive.evaluate_clause(text, events=events[:1], **BINDING)
        self.assertEqual(suspended["status"], "PENDING_DEPENDENCIES")
        self.assertFalse(suspended["verified"])
        self.assertIsNone(suspended["reading"])

    def test_vos_multiple_sources_partial_restore_and_unknown_stay_separate(self):
        events = [event("wq", "withdraw", "qatr"), event("ws", "withdraw", "sibawayhi"),
                  event("aq", "activate", "qatr"), event("as", "activate", "sibawayhi")]
        result = productive.evaluate_clause("ضَرَبَ عَمْرًا زَيْدٌ.", events=events, **BINDING)
        self.assertEqual([h["chain_complete"] for h in result["chain_history"]], [True, False, False, False, True])
        self.assertEqual(result["reading"]["subject_index"], 2)
        self.assertEqual(result["reading"]["object_index"], 1)
        unknown = productive.evaluate_clause("ضرب زيد عمرا", events=events[:1], **BINDING)
        self.assertEqual(unknown["status"], "DEFER")
        self.assertIsNone(unknown["candidate_space"]["count"])
        self.assertFalse(unknown["chain_complete"])

    def test_replay_binds_original_clause_and_complete_current_history(self):
        events = [event("w", "withdraw", "qatr"), event("a", "activate", "qatr")]
        report = productive.evaluate_clause(TEXT, events=events, **BINDING)
        self.assertTrue(productive.verify_clause(report, text=TEXT, events=events, **BINDING)["valid"])
        later = events + [event("noop", "activate", "qatr")]
        self.assertFalse(productive.verify_clause(report, text=TEXT, events=later, **BINDING)["replay_matches"])
        self.assertFalse(productive.verify_clause(report, text=TEXT, events=events,
                                                  **{**BINDING, "scope": "other"})["valid"])
        for mutate in (lambda r: r["original_clause"]["reading"].update(subject_index=True),
                       lambda r: r["chain_history"][1].update(status="LICENSED_CLAUSE"),
                       lambda r: r["candidate_space"].update(count=True)):
            forged = deepcopy(report)
            mutate(forged)
            self.assertFalse(productive.verify_clause(forged, text=TEXT, events=events, **BINDING)["replay_matches"])

    def test_missing_or_changed_native_does_not_reuse_original_license(self):
        with patch.object(life, "NATIVE", Path("/nonexistent/evidenceLifecycleV1")):
            result = productive.evaluate_clause(TEXT, events=[], **BINDING)
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertFalse(result["chain_complete"])
        self.assertEqual(result["candidate_space"]["candidates"][0]["state"], "PENDING")
        def corrupted(episode):
            proposed = life.propose_episode(episode)
            proposed["steps"][0]["step"] = False
            return proposed
        with patch.object(life, "_native", side_effect=corrupted):
            result = productive.evaluate_clause(TEXT, **BINDING)
        self.assertEqual(result["status"], "VERIFICATION_FAILED")
        self.assertIsNone(result["reading"])
        self.assertFalse(result["chain_history"])

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            source, events, receipt = (Path(directory) / n for n in ("input.txt", "events.json", "report.json"))
            source.write_text(TEXT)
            events.write_text("[]")
            command = [sys.executable, "-B", "-m", "tools.productive_lifecycle_cli"]
            read = subprocess.run(command + ["read", str(source), "--events", str(events)],
                                  cwd=productive.ROOT, capture_output=True, check=False)
            self.assertEqual(read.returncode, 0, read.stdout[:512].decode())
            receipt.write_bytes(read.stdout)
            verified = subprocess.run(command + ["verify", str(receipt), "--source", str(source), "--events", str(events)],
                                      cwd=productive.ROOT, capture_output=True, check=False)
            self.assertEqual(verified.returncode, 0, verified.stdout[:512].decode())


if __name__ == "__main__":
    unittest.main()
