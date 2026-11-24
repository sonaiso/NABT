from copy import deepcopy
import gzip
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, ntp
from tools.lexical_training import cumulative_v14_lesson as owner, teaching


ROOT = Path(__file__).resolve().parents[1]


def request(lesson):
    return ntp.request("cognitive.lesson", {"lesson": lesson})


class CumulativeV14OwnerContract(unittest.TestCase):
    def test_exact_input_fields_and_typed_ranges(self):
        bad = [
            {"schema": owner.SCHEMA, "pr": value}
            for value in (False, True, 0, 144, "1", 1.0)
        ]
        bad.extend(
            [
                {"schema": owner.SCHEMA, "pr": 1, "path": "/tmp/weights.json"},
                {"schema": owner.SCHEMA, "task": "root_recipe", "text": "ضرب", "pr": 1},
                {"schema": owner.SCHEMA, "task": "root_recipe", "text": "ضرب", "authority": "PASS"},
                {"schema": owner.SCHEMA, "task": "root_recipe", "text": ""},
                {"schema": owner.SCHEMA, "task": "root_recipe", "text": " "},
                {"schema": owner.SCHEMA, "task": "root_recipe", "text": "ب" * 513},
                {"schema": owner.SCHEMA, "task": False, "text": "ضرب"},
                {"schema": owner.SCHEMA, "task": "", "text": "ضرب"},
                {"schema": owner.SCHEMA, "task": "t" * 257, "text": "ضرب"},
                {"schema": owner.SCHEMA, "task": "root_recipe", "text": 123},
            ]
        )
        with patch.object(owner, "_checked_bundle") as load:
            for lesson in bad:
                with self.subTest(lesson=lesson):
                    result = teaching.run_lesson(lesson)
                    self.assertEqual(result["status"], "INVALID_INPUT")
                    self.assertFalse(result["execution_measured"])
            load.assert_not_called()

    def test_missing_head_or_artifact_does_not_become_a_proposal(self):
        lesson = {"schema": owner.SCHEMA, "task": "not_trained", "text": "شرطي"}
        with patch.object(owner, "_checked_bundle", return_value=({"manifest": {"labels": {}}}, {})):
            result = teaching.run_lesson(lesson)
        self.assertEqual(result["status"], "DEFER_NO_TRAINED_HEAD")
        self.assertFalse(result["execution_measured"])
        self.assertTrue(result["review_only"])
        self.assertEqual(result["authority"], "NONE")
        with patch.object(owner, "_checked_bundle", side_effect=ValueError("Changed artifact")):
            result = teaching.run_lesson(lesson)
        self.assertEqual(result["status"], "ARTIFACT_UNAVAILABLE")
        self.assertFalse(result["execution_measured"])

    def test_only_installed_pinned_bytes_are_read(self):
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory)
            payload = {"fixture": "installed"}
            raw = json.dumps(payload).encode()
            pins = {}
            for name in owner.ARTIFACT_NAMES:
                data = gzip.compress(raw, mtime=0) if name.endswith(".gz") else raw
                (installed / name).write_bytes(data)
                pins[name] = sha256(data).hexdigest()
            with patch.object(owner, "DIRECTORY", installed), patch.object(owner, "PINS", pins):
                for name in owner.ARTIFACT_NAMES:
                    self.assertEqual(owner.artifact(name), payload)
                with self.assertRaises(ValueError):
                    owner.artifact("../manifest.json")
                (installed / "skill_layout.json").write_text('{"reordered":true}')
                with self.assertRaises(ValueError):
                    owner.artifact("skill_layout.json")
                # Replacing a file by a symlink also invalidates the installation.
                (installed / "protocol.json").unlink()
                (installed / "protocol.json").symlink_to(installed / "manifest.json")
                with self.assertRaises(ValueError):
                    owner.artifact("protocol.json")
            with patch.object(owner, "DIRECTORY", installed), patch.object(owner, "PINS", {}):
                with self.assertRaisesRegex(ValueError, "not installed"):
                    owner.artifact("manifest.json")

    def test_proposal_keeps_parent_prediction_but_cannot_grant_authority(self):
        from tools.lexical_training import cumulative_v14_model as model

        pins = {name: sha256(name.encode()).hexdigest() for name in owner.ARTIFACT_NAMES}
        bundle = {
            "manifest": {"labels": {"fixture": ["earlier", "continued"]}},
            "parent_manifest": {"weights_sha256": sha256(b"parent fixture").hexdigest()},
        }
        proposal = {
            "label": "continued", "value": "continued",
            "parent_label": "earlier", "parent_value": "earlier",
            "changed": True, "authority": "NONE", "review_only": True,
        }
        lesson = {"schema": owner.SCHEMA, "task": "fixture", "text": "نص"}
        with patch.object(owner, "PINS", pins), patch.object(
            owner, "_checked_bundle", return_value=(bundle, {})
        ), patch.object(model, "propose", return_value=proposal) as predict:
            result = teaching.run_lesson(lesson)
            predict.assert_called_once_with(bundle, "fixture", "نص")
            self.assertEqual(result["status"], "PROPOSED")
            self.assertEqual(result["parent_value"], "earlier")
            self.assertEqual(result["value"], "continued")
            self.assertTrue(result["changed"])
            proposal["authority"] = "PASS"
            rejected = teaching.run_lesson(lesson)
            self.assertEqual(rejected["status"], "ARTIFACT_UNAVAILABLE")
            self.assertEqual(rejected["authority"], "NONE")
            self.assertFalse(rejected["execution_measured"])

    def test_report_retains_parent_comparison_and_replays_float_metrics(self):
        measured = {
            "fixture": {
                "parent": {"correct": 2, "n": 4, "macro_recall": 0.5},
                "final": {"correct": 3, "n": 4, "macro_recall": 0.75},
                "passed": True,
                "lost_from_parent": 1,
                "gained_from_parent": 2,
            }
        }
        report = {
            "pr": 1,
            "measured": measured,
            "necessary_coverage_gate": False,
            "legacy_necessary_coverage_gate": False,
            "all_assessment_rows_measured": True,
            "strict_cumulative_gate": False,
            "prepared_examples": 8,
            "assessment_examples": 4,
            "unmeasured_assessment_examples": 0,
            "changed_tests": ["fixture_test"],
            "changed_tests_without_passing_probe": ["another_test"],
            "outcome_status": "PARTIAL",
            "scope": "FIXTURE_MEASURED_SLICES_ONLY",
        }
        parent_pin = sha256(b"parent fixture").hexdigest()
        pins = {name: sha256(name.encode()).hexdigest() for name in owner.ARTIFACT_NAMES}
        bundle = {"parent_manifest": {"weights_sha256": parent_pin}}
        lesson = {"schema": owner.SCHEMA, "pr": 1}
        with patch.object(owner, "PINS", pins), patch.object(
            owner, "_checked_bundle", return_value=(bundle, {"pulls": [report]})
        ):
            result = teaching.run_lesson(lesson)
            self.assertEqual(result["outcome_slices"], measured)
            self.assertFalse(result["necessary_coverage_gate"])
            self.assertFalse(result["strict_cumulative_gate"])
            self.assertTrue(result["all_assessment_rows_measured"])
            self.assertEqual(result["assessment_examples"], 4)
            self.assertEqual(result["parent_weights_sha256"], parent_pin)
            self.assertTrue(teaching.verify_lesson(result, expected_lesson=lesson)["valid"])
            changed = deepcopy(result)
            changed["outcome_slices"]["fixture"]["lost_from_parent"] = 0
            self.assertFalse(teaching.verify_lesson(changed, expected_lesson=lesson)["valid"])
            changed = deepcopy(result)
            changed["authority"] = "PASS"
            self.assertFalse(teaching.verify_lesson(changed, expected_lesson=lesson)["valid"])

    def test_source_contract_excludes_ids_labels_and_predictions(self):
        lesson = {"schema": owner.SCHEMA, "task": "root_recipe", "text": "ضَرَبَ"}
        result = {
            "schema": owner.RESULT,
            "status": "PROPOSED",
            "execution_measured": True,
            "label": "ضرب",
            "parent_label": "ضرب",
            "authority": "NONE",
        }
        sources, _ = ntp._lesson_sources(lesson, result)
        self.assertEqual(
            sources,
            [{"text": "ضَرَبَ", "request_path": "/payload/input/lesson/text", "role": "PROBE", "source_id": None}],
        )
        sources, reason = ntp._lesson_sources(
            {"schema": owner.SCHEMA, "pr": 1}, dict(result, status="MEASURED")
        )
        self.assertEqual(sources, [])
        self.assertEqual(reason, "NO_REQUEST_TEXT_SOURCE")
        sources, reason = ntp._lesson_sources(lesson, dict(result, execution_measured=False))
        self.assertEqual(sources, [])
        self.assertEqual(reason, "OWNER_INPUT_NOT_VALIDATED")


class InstalledCumulativeV14Gateway(unittest.TestCase):
    def test_installed_continuation_keeps_parent_and_untrained_task(self):
        result = teaching.run_lesson({"schema": owner.SCHEMA, "task": "root_recipe", "text": "ضَرَبَ"})
        self.assertEqual(result["status"], "PROPOSED")
        self.assertEqual(result["parent_value"], "ضرب")
        self.assertEqual(result["authority"], "NONE")
        self.assertTrue(result["review_only"])
        self.assertEqual(result["changed"], result["label"] != result["parent_label"])
        self.assertEqual(result["weights_sha256"], owner.PINS["weights.json.gz"])
        unknown = teaching.run_lesson(
            {"schema": owner.SCHEMA, "task": "mixed_inference_admission", "text": "شرطي"}
        )
        self.assertEqual(unknown["status"], "DEFER_NO_TRAINED_HEAD")

    def test_historical_denominator_and_open_pr_remain_visible(self):
        evaluation = owner.artifact("evaluation.json")
        self.assertEqual([row["pr"] for row in evaluation["pulls"]], list(range(1, 144)))
        result = teaching.run_lesson({"schema": owner.SCHEMA, "pr": 143})
        self.assertEqual(result["status"], "MEASURED")
        self.assertEqual(result["pull_state"], "open")
        self.assertFalse(result["necessary_coverage_gate"])
        stats = result["outcome_slices"]["dictionary_source_status"]
        self.assertEqual(stats["parent"]["n"], 48)
        self.assertEqual(stats["final"]["n"], 48)
        empty = teaching.run_lesson({"schema": owner.SCHEMA, "pr": 55})
        self.assertEqual(empty["status"], "UNMEASURED")
        self.assertFalse(empty["necessary_coverage_gate"])

    def test_gateway_replays_bound_text_and_refuses_changed_result(self):
        req = json.loads((ROOT / "examples/io_gateway/ntl_cumulative_v14.json").read_bytes())
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        result = receipt["execution"]["owner_result"]
        self.assertEqual(result["owner_result"]["status"], "PROPOSED")
        self.assertEqual(result["observation_request_path"], "/payload/input/lesson/text")
        other = deepcopy(req)
        other["payload"]["input"]["lesson"]["text"] = "كَتَبَ"
        self.assertFalse(gateway.accept_output(receipt, expected_request=other)["valid"])
        altered = deepcopy(receipt)
        altered["execution"]["owner_result"]["owner_result"]["parent_value"] = "بديل"
        self.assertFalse(gateway.accept_output(altered, expected_request=req)["valid"])
        altered = deepcopy(receipt)
        altered["execution"]["owner_result"]["owner_result"]["authority"] = "PASS"
        self.assertFalse(gateway.accept_output(altered, expected_request=req)["valid"])

    def test_gateway_pr_report_keeps_no_text_and_rejects_swapped_pr(self):
        req = request({"schema": owner.SCHEMA, "pr": 143})
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        result = receipt["execution"]["owner_result"]
        self.assertEqual(result["recursive_observations"], [])
        self.assertEqual(result["observation_limits"]["source_count"], 0)
        other = request({"schema": owner.SCHEMA, "pr": 142})
        self.assertFalse(gateway.accept_output(receipt, expected_request=other)["valid"])

    def test_gateway_snapshot_binds_layout_protocol_and_evaluation(self):
        snapshot = gateway.snapshot()
        for name, pin in owner.PINS.items():
            self.assertEqual(snapshot["files"]["evidence/cumulative_v14/" + name], pin)
        manifest = owner.artifact("manifest.json")
        self.assertEqual(
            snapshot["files"]["evidence/cumulative_v14/training.json"],
            manifest["inputs"]["training.json"],
        )
        self.assertEqual(len(gateway.CUMULATIVE_V14_INPUTS), 6)


if __name__ == "__main__":
    unittest.main()
