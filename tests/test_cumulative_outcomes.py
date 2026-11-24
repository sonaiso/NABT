from copy import deepcopy
from pathlib import Path
import ast
import gzip
import json
import unittest

from tools.grammar_catalog import gateway
from tools.lexical_training import cumulative_assertions as masked, cumulative_history as history
from tools.lexical_training import (
    cumulative_lesson as owner,
    cumulative_sources as sources,
    teaching,
)


class CumulativeOutcomes(unittest.TestCase):
    def test_all_historical_numbers_and_source_partitions(self):
        manifest = json.loads((history.DATA / "manifest.json").read_bytes())
        for name, pin in manifest["inputs"].items():
            self.assertEqual(history.digest((history.DATA / name).read_bytes()), pin)
        pull = json.loads((history.DATA / "pulls.json").read_bytes())
        self.assertEqual([i["number"] for i in pull], list(range(1, 144)))
        self.assertEqual(pull[64]["state"], "closed")
        self.assertEqual(pull[142]["state"], "open")
        pack = json.loads(gzip.decompress((history.DATA / "examples.json.gz").read_bytes()))
        self.assertFalse(
            {r["text"] for r in pack["rows"] if r["split"] == "train"}
            & {r["text"] for r in pack["rows"] if r["split"] == "test"}
        )
        source = history.snapshot()
        self.assertEqual(len(source["pull_requests"]), 143)
        stages = json.loads(gzip.decompress((history.DATA / "stages.json.gz").read_bytes()))
        self.assertEqual(sorted(map(int, stages)), list(range(1, 144)))

    def test_single_label_holdout_and_repeated_evidence(self):
        r = {"pr": 1, "task": "T", "text": "x", "gold": "a", "split": "train", "source": "fixture"}
        rows, counts = sources.prepare(
            [r, dict(r, split="test", pr=2), dict(r, text="y"), dict(r, text="y", gold="b")]
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["split"], "test")
        self.assertEqual(counts, {"overlapping_train": 1, "conflicting": 2})
        q = masked.query(ast.parse('self.assertEqual(answer["status"], "BLOCK")', mode="eval").body)
        self.assertNotIn("BLOCK", ast.unparse(q[0]))
        self.assertEqual(q[1], "BLOCK")

    def test_gate_rejects_blanket_claim_and_nonmerged_status_is_preserved(self):
        out = teaching.run_lesson({"schema": owner.SCHEMA, "pr": 143})
        self.assertFalse(out["necessary_coverage_gate"])
        self.assertEqual(out["pull_state"], "open")
        self.assertEqual(out["outcome_slices"]["dictionary_source_status"]["n"], 48)
        self.assertFalse(out["outcome_slices"]["dictionary_source_status"]["passed"])
        for n in (False, 0, 144, "1"):
            self.assertEqual(
                teaching.run_lesson({"schema": owner.SCHEMA, "pr": n})["status"], "INVALID_INPUT"
            )
        for n in (22, 36, 53, 55, 60, 98, 125, 129):
            self.assertEqual(
                teaching.run_lesson({"schema": owner.SCHEMA, "pr": n})["status"], "UNMEASURED"
            )
        self.assertEqual(
            teaching.run_lesson(
                {"schema": owner.SCHEMA, "text": "شرطي", "task": "mixed_inference_admission"}
            )["status"],
            "DEFER_NO_TRAINED_HEAD",
        )

    def test_retained_weights_predict_a_real_root_without_lookup(self):
        s = teaching.run_lesson({"schema": owner.SCHEMA, "task": "root_recipe", "text": "ضَرَبَ"})
        self.assertEqual((s["status"], s["value"], s["authority"]), ("PROPOSED", "ضرب", "NONE"))

    def test_gateway_replays_source_and_refuses_a_swapped_pr(self):
        req = json.loads(
            (history.ROOT / "examples/io_gateway/ntl_cumulative_outcome.json").read_bytes()
        )
        out = gateway.run(req)
        self.assertTrue(gateway.accept_output(out, expected_request=req)["valid"])
        other = deepcopy(req)
        other["payload"]["input"]["lesson"]["pr"] = 142
        self.assertFalse(gateway.accept_output(out, expected_request=other)["valid"])
