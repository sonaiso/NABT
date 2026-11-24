"""Independent outcome fixtures for the cumulative V14 replay boundary."""

from copy import deepcopy
import csv
import gzip
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.lexical_training import cumulative_v14_audit as audit


class CumulativeV14Audit(unittest.TestCase):
    def setUp(self):
        pulls = [
            {"number": n, "title": "PR " + str(n), "head": "head-" + str(n),
             "state": "open" if n in (123, 138, 143) else "closed" if n == 65 else "merged"}
            for n in range(1, 144)
        ]
        history = [
            {"pr": n, "files": 0 if n == 55 else 1, "touched_tests": []}
            for n in range(1, 144)
        ]
        history[2]["touched_tests"] = ["F::yes", "F::no"]
        train = [
            self.row(1, "T", "train A", "A", split="train"),
            self.row(1, "T", "train B", "B", split="train"),
            self.row(3, "S", "train yes", "yes", split="train"),
            self.row(3, "S", "train no", "no", split="train"),
            self.row(142, "U", "train singleton", "A", split="train"),
        ]
        test = [
            self.row(1, "T", "heldout a", "A"),
            self.row(1, "T", "heldout b", "B"),
            self.row(1, "T", "heldout c", "B"),
            self.row(2, "T", "heldout b", "B"),
            self.row(3, "S", "heldout yes", "yes", source="fixture:F::yes"),
            self.row(3, "S", "heldout no", "no", source="fixture:F::no"),
            self.row(142, "U", "heldout unknown", "B", lane="masked_public_contract"),
        ]
        self.answers = {
            ("T", "heldout a"): ("A", "B"),  # lost a formerly correct answer
            ("T", "heldout b"): ("A", "B"),  # gain, attributed to two PRs
            ("T", "heldout c"): ("B", "B"),  # retained
            ("S", "heldout yes"): ("yes", "yes"),
            ("S", "heldout no"): ("yes", "no"),
        }
        self.parent = {"labels": {"T": ["A", "B"], "S": ["yes", "no"]},
                       "weights_sha256": "retained-parent"}
        saved = []
        for r in test:
            if r["task"] not in self.parent["labels"]:
                continue
            parent, final = self.answers[r["task"], r["text"]]
            baseline = "A" if r["task"] == "T" else "yes"
            saved.append({
                **{k: r[k] for k in ("pr", "task", "source", "lane", "gold")},
                "text_sha256": audit.digest(r["text"].encode()),
                "prediction": parent, "initial": baseline,
                "majority": baseline, "first": baseline,
            })
        self.source = {
            "manifest": self.parent, "pulls": pulls,
            "history": {"pull_requests": history},
            "evaluation": {"pulls": [{"pr": n} for n in range(1, 144)]},
            "pack": {"rows": train + test, "excluded": {"fixture": 1}},
            "predictions": saved,
        }
        self.bundle = {
            "parent_manifest": deepcopy(self.parent),
            "manifest": {"variant": "full", "weights_sha256": "fixture-residual",
                         "inputs": {"protocol.json": "fixture-protocol"}},
        }
        self.calls = []
        self.learner = SimpleNamespace(load=lambda directory: self.bundle, propose=self.propose)
        self.enterContext(patch.object(audit, "_learner", return_value=self.learner))
        self.enterContext(patch.object(audit, "_source_snapshot", side_effect=lambda: deepcopy(self.source)))

    @staticmethod
    def row(pr, task, text, gold, split="test", source=None, lane="source_split"):
        return {"pr": pr, "task": task, "text": text, "gold": gold,
                "split": split, "source": source or "fixture:" + text, "lane": lane}

    def propose(self, bundle, task, text, *, ablate=None):
        self.calls.append((task, text, ablate))
        parent, value = self.answers[task, text]
        if ablate is not None:
            value = parent
        return {"label": value, "value": value, "parent_label": parent,
                "parent_value": parent, "changed": value != parent,
                "authority": "NONE", "review_only": True}

    @staticmethod
    def save(directory, report):
        audit.save_report(directory, report)

    def test_preserves_every_pr_and_missing_head_in_denominator(self):
        report = audit.build_report()
        self.assertEqual([p["pr"] for p in report["pulls"]], list(range(1, 144)))
        self.assertEqual(report["pulls"][54]["outcome_status"], "EMPTY_HISTORICAL_DIFF")
        self.assertEqual(report["pulls"][64]["pull_state"], "closed")
        self.assertEqual([p["pr"] for p in report["pulls"] if p["pull_state"] == "open"], [123, 138, 143])
        self.assertEqual(report["summary"]["all_heldout"], 7)
        self.assertEqual(report["summary"]["measured_rows"], 6)
        self.assertEqual(report["summary"]["no_trained_head"], 1)
        self.assertEqual(len(report["predictions"]), 7)
        self.assertEqual(report["predictions"][-1]["status"], "DEFER_NO_TRAINED_HEAD")
        self.assertIsNone(report["predictions"][-1]["prediction"])
        self.assertFalse(any(task == "U" for task, _, _ in self.calls))
        self.assertEqual(report["lanes"]["masked_public_contract"]["no_trained_head"], 1)
        self.assertIn("NOT_ARABIC_UNDERSTANDING", report["lanes"]["masked_public_contract"]["interpretation"])
        self.assertIn("RETROSPECTIVE", report["assessment"])
        self.assertFalse(report["summary"]["necessary_gate_passed"])

    def test_parent_retention_deduplicates_inputs_and_does_not_hide_losses(self):
        report = audit.build_report()
        s = report["summary"]
        self.assertEqual((s["parent_correct_rows"], s["final_correct_rows"]), (3, 5))
        self.assertEqual(s["unique_task_inputs"], 5)
        self.assertEqual((s["parent_correct_unique"], s["final_correct_unique"]), (3, 4))
        self.assertEqual((s["lost_from_parent_unique"], s["gained_from_parent_unique"]), (1, 2))
        self.assertFalse(s["no_parent_correct_lost"])
        self.assertEqual(report["tasks"]["T"]["retained_parent_correct"], 1)
        self.assertEqual(report["tasks"]["T"]["prediction_changes"], 2)

    def test_balanced_recall_and_necessary_coverage_use_original_controls(self):
        report = audit.build_report()
        t, s = report["tasks"]["T"], report["tasks"]["S"]
        self.assertEqual(t["final"]["correct"], 2)
        self.assertEqual(t["initial"]["correct"], 1)
        self.assertEqual(t["final"]["balanced"], .5)
        self.assertEqual(t["initial"]["balanced"], .5)
        self.assertFalse(t["passed"])
        self.assertTrue(s["passed"])
        self.assertTrue(s["improved_over_parent"])
        self.assertEqual(report["pulls"][2]["changed_tests_without_passing_probe"], 0)
        self.assertTrue(report["pulls"][2]["necessary_coverage_gate"])
        self.assertEqual(report["summary"]["prs_meeting_necessary_coverage"], 1)

    def test_legacy_first_stage_can_differ_for_repeated_input(self):
        self.source["predictions"][3]["first"] = "B"
        report = audit.build_report()
        self.assertEqual(report["tasks"]["T"]["first"]["correct"], 2)
        self.assertEqual(report["summary"]["gained_from_parent_unique"], 2)

    def test_rejects_changed_parent_outcome_and_invalid_authority(self):
        original = self.learner.propose
        self.learner.propose = lambda *args, **kwargs: dict(original(*args, **kwargs), parent_value="B", parent_label="B")
        with self.assertRaisesRegex(ValueError, "Retained parent prediction changed"):
            audit.build_report()
        self.learner.propose = lambda *args, **kwargs: dict(original(*args, **kwargs), authority="ACCEPTED")
        with self.assertRaisesRegex(ValueError, "acceptance authority"):
            audit.build_report()

    def test_rejects_changed_source_parent_and_split_leakage(self):
        self.bundle["parent_manifest"]["weights_sha256"] = "other-parent"
        with self.assertRaisesRegex(ValueError, "retained cumulative parent"):
            audit.build_report()
        self.bundle["parent_manifest"] = deepcopy(self.parent)
        self.source["pack"]["rows"][0]["text"] = "heldout a"
        with self.assertRaisesRegex(ValueError, "occurs in training"):
            audit.build_report()

    def test_rejects_dropped_pr_and_duplicate_baseline_conflict(self):
        removed = self.source["pulls"].pop()
        with self.assertRaisesRegex(ValueError, "inherited PR"):
            audit.build_report()
        self.source["pulls"].append(removed)
        self.source["predictions"][3]["majority"] = "B"
        with self.assertRaisesRegex(ValueError, "Inconsistent repeated task/input"):
            audit.build_report()

    def test_replay_detects_score_coverage_and_pending_row_changes(self):
        report = audit.build_report()
        with tempfile.TemporaryDirectory() as path:
            directory = Path(path)
            self.save(directory, report)
            replay = audit.replay(directory)
            self.assertEqual((replay["replay"], replay["checked_all_heldout_rows"]), ("PASS", 7))
            for mutate in (
                lambda r: r["summary"].update(final_correct_unique=5),
                lambda r: r["pulls"][0].update(necessary_coverage_gate=True),
                lambda r: r["tasks"]["T"]["parent"].update(correct=0),
                lambda r: r.update(model_variant="without_task_memory"),
            ):
                edited = deepcopy(report)
                mutate(edited)
                self.save(directory, edited)
                with self.assertRaisesRegex(ValueError, "evaluation, scores, baselines, or coverage"):
                    audit.replay(directory)
            self.save(directory, report)
            rows = deepcopy(report["predictions"])
            rows[-1]["status"] = "PROPOSED"
            (directory / "predictions.json.gz").write_bytes(gzip.compress(audit.canonical(rows).encode(), mtime=0))
            with self.assertRaisesRegex(ValueError, "prediction rows, order, or pending"):
                audit.replay(directory)
            self.save(directory, report)
            csv_path = directory / "coverage.csv"
            csv_path.write_text(csv_path.read_text().replace("false", "true", 1))
            with self.assertRaisesRegex(ValueError, "CSV coverage, denominators, or gates"):
                audit.replay(directory)

    def test_csv_preserves_all_prs_quoting_and_unmeasured_rows(self):
        self.source["pulls"][0]["title"] = 'Arabic, title "quoted"\ncontinued'
        report = audit.build_report()
        rows = list(csv.DictReader(io.StringIO(audit.coverage_csv(report))))
        self.assertEqual([int(r["pr"]) for r in rows], list(range(1, 144)))
        self.assertEqual(rows[0]["title"], self.source["pulls"][0]["title"])
        self.assertEqual((rows[141]["heldout_examples"], rows[141]["scored"], rows[141]["unmeasured_heldout"]), ("1", "0", "1"))
        self.assertEqual(rows[141]["strict_cumulative_gate"], "false")
        self.assertEqual(rows[2]["legacy_necessary_coverage_gate"], "true")

    def test_complete_gate_command_returns_two_while_regular_replay_succeeds(self):
        with tempfile.TemporaryDirectory() as path:
            directory = Path(path)
            self.save(directory, audit.build_report())
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(audit.main(["--directory", path]), 0)
                self.assertEqual(audit.main(["--directory", path, "--require-every-pr"]), 2)
        # Even a passing legacy aggregate must not bypass the stronger gate.
        with patch.object(audit, "replay", return_value={"necessary_gate_passed": True,
                                                        "strict_cumulative_gate_passed": False}):
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(audit.main(["--require-every-pr"]), 2)

    def test_no_head_row_blocks_strict_gate_even_when_legacy_probe_passes(self):
        self.source["pack"]["rows"].append(self.row(3, "U", "another heldout unknown", "A"))
        report = audit.build_report()
        pr = report["pulls"][2]
        self.assertTrue(pr["legacy_necessary_coverage_gate"])
        self.assertTrue(pr["necessary_coverage_gate"])
        self.assertFalse(pr["all_assessment_rows_measured"])
        self.assertFalse(pr["strict_cumulative_gate"])
        self.assertEqual(pr["unmeasured_assessment_examples"], 1)

    def test_fixed_weight_ablations_preserve_parent_and_show_counterfactual_losses(self):
        report = audit.build_report(ablate=True)
        ablations = report["fixed_weight_inference_ablation"]
        self.assertEqual(set(ablations), set(audit.ABLATIONS))
        for channel in audit.ABLATIONS:
            self.assertEqual(ablations[channel]["all_rows"], {
                "tested": 6, "prediction_changed": 4, "correct_full": 5,
                "correct_masked": 3, "lost": 3, "gained": 1,
            })
        self.assertEqual(report["summary"]["parent_correct_unique"], 3)
        original = self.learner.propose
        def changed_tracking(*args, **kwargs):
            p = original(*args, **kwargs)
            return dict(p, parent_label="B", parent_value="B") if kwargs.get("ablate") else p
        self.learner.propose = changed_tracking
        with self.assertRaisesRegex(ValueError, "tracking identity"):
            audit.build_report(ablate=True)

    def test_distinguishes_boolean_and_numeric_answers(self):
        self.assertEqual(audit.score([False, 0], [0, False]), {
            "n": 2, "correct": 0, "classes": 2, "balanced": 0.0,
        })


if __name__ == "__main__":
    unittest.main()
