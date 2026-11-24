"""Independent small reference sets for the training/completion contract.

These fixtures test a measurement policy.  They are not Arabic attestations,
blind population samples, or native owner certificates.
"""

from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import completion_criteria as criteria


class CompletionCriteria(unittest.TestCase):
    def setUp(self):
        self.reference = {
            "schema": "acb.reference.v1", "version": "independent-fixture-1",
            "scope": "fixture-measurement-only", "required_families": ["F"],
            "cases": [
                self.case("p", "positive", ["reading-p"]),
                self.case("a", "ambiguity", ["reading-a1", "reading-a2"]),
                self.case("n", "negative", []),
                self.case("u", "needs_context", []),
            ],
        }
        self.predictions = [
            {"id": "p", "status": "licensed", "readings": ["reading-p"]},
            {"id": "a", "status": "licensed_multiple", "readings": ["reading-a1", "reading-a2"]},
            {"id": "n", "status": "rejected", "readings": []},
            {"id": "u", "status": "defer", "readings": []},
        ]
        rows = [self.row(part + "-" + case["id"], part, case["kind"])
                for part in ("train", "calibration") for case in self.reference["cases"]]
        rows += [self.row(case["id"], "test", case["kind"]) for case in self.reference["cases"]]
        self.experiment = {
            "schema": "nabt.learning-completion-experiment.v1",
            "scope_id": "fixture-measurement-only", "required_objective_ids": ["trace.identity"],
            "holdout_axes": ["text_groups", "root_groups", "source_groups"],
            "independence_axes": ["text_groups", "root_groups", "source_groups"],
            "exposure": "PUBLIC_RETROSPECTIVE",
            "sampling": {"kind": "AUTHORED", "population": "authored fixture cases",
                         "frame_ref": "fixture:frame", "design_ref": "fixture:design"},
            "rows": rows, "interventions": [],
        }

    @staticmethod
    def case(identity, kind, readings, family="F"):
        return {"id": identity, "kind": kind, "family": family,
                "source_ref": "fixture:" + identity, "gold_readings": readings,
                "gold_complete": kind != "needs_context"}

    @staticmethod
    def row(identity, split, kind, *, mode="raw"):
        return {
            "id": identity, "split": split, "objective_id": "trace.identity", "stage_id": "L01",
            "text": "نص تجريبي مستقل " + identity, "question": "ما القراءة؟ " + identity,
            "input_mode": mode, "kind": kind,
            "root_groups": ["root:" + identity], "source_groups": ["source:" + identity],
            "template_groups": ["template:" + identity], "lexeme_groups": ["lexeme:" + identity],
            "provenance_ref": "fixture:" + identity,
        }

    def evaluate(self, **kwargs):
        return criteria.evaluate_benchmark(self.reference, self.predictions, self.experiment, **kwargs)

    @staticmethod
    def gate(result, identity):
        return next(g for g in result["gates"] if g["id"] == identity)

    def test_installed_contract_resolves_all_existing_objectives(self):
        contract = criteria.load_contract()
        self.assertEqual(len(contract["objectives"]), 66)
        self.assertEqual([s["id"] for s in contract["stages"]], [f"L{i:02d}" for i in range(1, 14)])
        self.assertEqual(set().union(*(set(s["objective_ids"]) for s in contract["stages"])),
                         set(contract["objectives"]))
        self.assertIn("trace.identity", contract["stages"][0]["objective_ids"])

    def test_perfect_reference_agreement_cannot_certify_an_owner_or_world(self):
        result = self.evaluate()
        self.assertEqual(result["integrity_status"], "PASS")
        self.assertEqual(self.gate(result, "finite_reference_agreement")["status"], "PASS")
        self.assertEqual(result["licensed_completion"]["status"], "NOT_MEASURED")
        self.assertEqual(result["authority"], "REFERENCE_AGREEMENT_ONLY")
        self.assertEqual(result["universal_arabic_completeness"], "NOT_INFERRED")
        self.assertEqual(result["reference_scores"]["certificate_verification"], "NOT_PERFORMED_BY_THIS_SCORER")
        self.assertTrue(all(x["licensed_path"] == "NOT_MEASURED" for x in result["stage_measurements"]))
        self.assertFalse(result["statistical_gates_eligible_on_declared_design"])
        self.assertEqual(self.gate(result, "raw_quality")["status"], "NOT_MEASURED")

    def test_missing_outputs_stay_in_the_denominator(self):
        self.predictions.pop(0)
        result = self.evaluate()
        self.assertEqual(result["mode_scores"]["raw"], {"numerator": 3, "denominator": 4, "value": 0.75})
        row = next(r for r in result["reference_scores"]["cases"] if r["id"] == "p")
        self.assertEqual(row["status"], "missing")
        self.assertEqual(self.gate(result, "finite_reference_agreement")["status"], "FAIL")

    def test_all_deferral_does_not_become_completeness(self):
        self.predictions = [{"id": p["id"], "status": "defer", "readings": []} for p in self.predictions]
        result = self.evaluate()
        self.assertEqual(result["mode_scores"]["raw"]["numerator"], 1)
        self.assertEqual(result["reference_scores"]["metrics"]["positive_exact_set_coverage"]["value"], 0.0)
        self.assertEqual(self.gate(result, "finite_reference_agreement")["status"], "FAIL")
        self.assertEqual(self.gate(result, "no_forbidden_finalization_observed")["status"], "PASS")
        self.assertEqual(result["licensed_completion"]["status"], "NOT_MEASURED")

    def test_ambiguity_requires_the_entire_reference_reading_set(self):
        self.predictions[1] = {"id": "a", "status": "licensed", "readings": ["reading-a1"]}
        result = self.evaluate()
        self.assertEqual(result["reference_scores"]["metrics"]["ambiguity_exact_set_coverage"]["value"], 0)
        self.assertEqual(result["reference_scores"]["metrics"]["licensed_reading_recall"]["numerator"], 2)
        self.assertEqual(result["reference_scores"]["metrics"]["licensed_reading_recall"]["denominator"], 3)
        self.assertEqual(self.gate(result, "finite_reference_agreement")["status"], "FAIL")

    def test_unsupported_extra_reading_is_counted_even_on_positive_input(self):
        self.predictions[0] = {"id": "p", "status": "licensed_multiple", "readings": ["reading-p", "invented"]}
        result = self.evaluate()
        self.assertEqual(result["reference_scores"]["metrics"]["licensed_reading_precision"]["value"], 0.75)
        self.assertEqual(self.gate(result, "finite_reference_agreement")["status"], "FAIL")
        # A good negative stratum cannot conceal a bad accepted positive reading.
        self.assertEqual(result["reference_scores"]["metrics"]["false_accept_rate_on_negative"]["value"], 0.0)
        self.assertEqual(result["cluster_metrics"]["unsupported_accept_upper_counts"],
                         {"errors": 1, "accepted_groups": 2})
        self.assertEqual(self.gate(result, "no_forbidden_finalization_observed")["status"], "FAIL")

    def test_negative_acceptance_and_premature_finalization_are_separate(self):
        self.predictions[2] = {"id": "n", "status": "licensed", "readings": ["invented"]}
        self.predictions[3] = {"id": "u", "status": "rejected", "readings": []}
        result = self.evaluate()
        self.assertEqual(result["reference_scores"]["metrics"]["false_accept_rate_on_negative"]["value"], 1.0)
        self.assertEqual(result["reference_scores"]["metrics"]["premature_finalization_on_context"]["value"], 1.0)
        self.assertEqual(self.gate(result, "no_forbidden_finalization_observed")["measurement"],
                         {"numerator": 2, "denominator": 4, "value": 0.5})

    def test_resource_error_is_not_a_linguistic_negative(self):
        self.predictions[2] = {"id": "n", "status": "resource_error", "readings": []}
        result = self.evaluate()
        self.assertEqual(result["reference_scores"]["metrics"]["negative_rejection_rate"]["value"], 0.0)
        self.assertEqual(result["reference_scores"]["metrics"]["execution_error_rate"]["value"], 0.25)
        self.assertEqual(self.gate(result, "finite_reference_agreement")["status"], "FAIL")

    def test_empty_scope_empty_required_objectives_and_absent_predictions(self):
        original = deepcopy(self.reference)
        self.reference["cases"] = []
        with self.assertRaises(ValueError):
            self.evaluate()
        self.reference = original
        self.experiment["required_objective_ids"] = []
        with self.assertRaises(ValueError):
            self.evaluate()
        self.experiment["required_objective_ids"] = ["trace.identity"]
        self.predictions = []
        result = self.evaluate()
        self.assertEqual(result["mode_scores"]["raw"]["denominator"], 4)
        self.assertEqual(result["mode_scores"]["raw"]["numerator"], 0)
        self.assertEqual(result["licensed_completion"]["status"], "NOT_MEASURED")

    def test_reference_inventory_and_metadata_cannot_be_silently_trimmed(self):
        original = deepcopy(self.experiment)
        for mutate in (
            lambda e: e["rows"].pop(),
            lambda e: e["rows"].append(deepcopy(e["rows"][-1])),
            lambda e: e["rows"][-1].update(kind="negative"),
            lambda e: e["rows"][-1].update(stage_id="L02"),
            lambda e: e.update(scope_id="other-scope"),
        ):
            with self.subTest(mutation=mutate):
                self.experiment = deepcopy(original)
                mutate(self.experiment)
                with self.assertRaises(ValueError):
                    self.evaluate()

    def test_model_flags_and_supplied_hash_axes_do_not_grant_authority(self):
        for field, value in (("authority", "LICENSED"), ("certificate", True), ("correct", True)):
            with self.subTest(field=field):
                extra = deepcopy(self.predictions)
                extra[0][field] = value
                with self.assertRaises(ValueError):
                    criteria.evaluate_benchmark(self.reference, extra, self.experiment)
        self.experiment["rows"][0]["text_groups"] = ["caller-picked"]
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_duplicate_surface_with_another_question_still_leaks(self):
        train = self.experiment["rows"][0]
        target = next(r for r in self.experiment["rows"] if r["id"] == "p")
        train["text"] = target["text"]
        self.assertNotEqual(train["question"], target["question"])
        result = self.evaluate()
        self.assertEqual(result["split_audit"]["status"], "FAIL")
        self.assertTrue(any(set(g) == {"train-p", "p"} for g in result["split_audit"]["overlaps"]))

    def test_split_audit_follows_transitive_root_source_connections(self):
        rows = {r["id"]: r for r in self.experiment["rows"]}
        rows["train-p"]["root_groups"] = ["bridge-root"]
        rows["calibration-p"]["root_groups"] = ["bridge-root"]
        rows["calibration-p"]["source_groups"] = ["bridge-source"]
        rows["p"]["source_groups"] = ["bridge-source"]
        result = self.evaluate()
        self.assertEqual(result["split_audit"]["status"], "FAIL")
        self.assertIn(["calibration-p", "p", "train-p"], result["split_audit"]["overlaps"])

    def test_unknown_group_identity_never_counts_as_independence(self):
        next(r for r in self.experiment["rows"] if r["id"] == "p")["root_groups"] = []
        result = self.evaluate()
        self.assertEqual(result["split_audit"]["status"], "NOT_MEASURED")
        self.assertIsNone(result["cluster_metrics"]["raw_exact_lower"])
        self.assertEqual(self.gate(result, "raw_quality")["status"], "NOT_MEASURED")

    def test_shared_source_cases_form_one_independent_cluster(self):
        rows = {r["id"]: r for r in self.experiment["rows"]}
        rows["p"]["source_groups"] = ["shared-test-source"]
        rows["a"]["source_groups"] = ["shared-test-source"]
        result = self.evaluate()
        self.assertEqual(len(result["cluster_metrics"]["groups"]["groups"]), 3)
        self.assertIn(["a", "p"], result["cluster_metrics"]["groups"]["groups"])

    def test_assisted_bridge_preserves_transitive_independence_of_raw_cases(self):
        self.reference["cases"].append(self.case("bridge", "positive", ["reading-bridge"]))
        self.predictions.append({"id": "bridge", "status": "licensed", "readings": ["reading-bridge"]})
        bridge = self.row("bridge", "test", "positive", mode="assisted")
        rows = {r["id"]: r for r in self.experiment["rows"]}
        rows["p"]["source_groups"] = bridge["source_groups"] = ["transitive-source"]
        rows["a"]["root_groups"] = bridge["root_groups"] = ["transitive-root"]
        self.experiment["rows"].append(bridge)
        result = self.evaluate()
        clusters = result["cluster_metrics"]["groups"]["groups"]
        self.assertIn(["a", "p"], clusters)
        self.assertEqual(len(clusters), 3)
        self.assertTrue(all("bridge" not in group for group in clusters))

    def test_training_floor_does_not_split_a_component_when_filtering_kind_and_stage(self):
        rows = {r["id"]: r for r in self.experiment["rows"]}
        another = self.row("another-positive", "train", "positive")
        rows["train-p"]["source_groups"] = rows["train-n"]["source_groups"] = ["training-bridge-source"]
        rows["train-n"]["root_groups"] = another["root_groups"] = ["training-bridge-root"]
        rows["train-n"]["stage_id"] = "L02"
        rows["train-n"]["objective_id"] = "base.a116"
        self.experiment["rows"].append(another)
        result = self.evaluate()
        planning = next(q for q in result["training_queue"]
                        if q["stage_id"] == "L01" and q["kind"] == "positive" and q["split"] == "train")
        self.assertEqual(planning["available_groups"], 1)

    def test_authored_and_public_assessments_do_not_get_population_gates(self):
        for exposure, sampling in (("SEALED_NEW", "AUTHORED"), ("PUBLIC_RETROSPECTIVE", "PROBABILITY_SAMPLE")):
            with self.subTest(exposure=exposure, sampling=sampling):
                self.experiment["exposure"] = exposure
                self.experiment["sampling"]["kind"] = sampling
                result = self.evaluate()
                self.assertFalse(result["statistical_gates_eligible_on_declared_design"])
                for gate_id in ("raw_quality", "false_accept_risk", "premature_finalization_risk"):
                    self.assertEqual(self.gate(result, gate_id)["status"], "NOT_MEASURED")

    def test_a_tiny_declared_blind_sample_cannot_pass_large_accuracy_claims(self):
        self.experiment["exposure"] = "SEALED_NEW"
        self.experiment["sampling"]["kind"] = "PROBABILITY_SAMPLE"
        result = self.evaluate(parent_predictions=deepcopy(self.predictions), control_predictions=deepcopy(self.predictions))
        self.assertTrue(result["statistical_gates_eligible_on_declared_design"])
        for identity in ("raw_quality", "false_accept_risk", "premature_finalization_risk", "retention",
                         "gain_over_parent", "gain_over_control"):
            self.assertEqual(self.gate(result, identity)["status"], "FAIL")
        self.assertEqual(result["sampling_verification"], "DECLARED_DESIGN_NOT_INDEPENDENTLY_ATTESTED")
        self.assertEqual(result["licensed_completion"]["status"], "NOT_MEASURED")

    def test_assisted_answers_cannot_supply_a_raw_population_denominator(self):
        for row in self.experiment["rows"]:
            if row["split"] == "test":
                row["input_mode"] = "assisted"
        result = self.evaluate()
        self.assertEqual(result["mode_scores"]["raw"]["denominator"], 0)
        self.assertEqual(result["mode_scores"]["assisted"]["value"], 1.0)
        self.assertIsNone(result["cluster_metrics"]["raw_exact_lower"])
        self.assertEqual(self.gate(result, "raw_quality")["status"], "NOT_MEASURED")
        self.assertNotEqual(self.gate(result, "finite_reference_agreement")["status"], "PASS")

    def test_assisted_only_family_cannot_complete_raw_family_coverage(self):
        self.reference["required_families"].append("ASSISTED_ONLY")
        self.reference["cases"].append(self.case("assisted", "positive", ["reading-helped"], "ASSISTED_ONLY"))
        self.experiment["rows"].append(self.row("assisted", "test", "positive", mode="assisted"))
        self.predictions.append({"id": "assisted", "status": "licensed", "readings": ["reading-helped"]})
        result = self.evaluate()
        self.assertEqual(result["mode_scores"]["raw"]["value"], 1.0)
        self.assertNotEqual(self.gate(result, "finite_reference_agreement")["status"], "PASS")

    def test_a_missing_assisted_target_cannot_disappear_from_finite_agreement(self):
        self.reference["cases"].append(self.case("assisted-missing", "positive", ["required-reading"]))
        self.experiment["rows"].append(self.row("assisted-missing", "test", "positive", mode="assisted"))
        result = self.evaluate()
        self.assertEqual(result["mode_scores"]["raw"]["value"], 1.0)
        self.assertEqual(result["mode_scores"]["assisted"]["denominator"], 1)
        self.assertEqual(result["mode_scores"]["assisted"]["numerator"], 0)
        self.assertEqual(self.gate(result, "finite_reference_agreement")["status"], "FAIL")

    def test_an_unmeasured_objective_remains_in_the_declared_scope(self):
        self.experiment["required_objective_ids"].append("base.a116")
        result = self.evaluate()
        measured = self.gate(result, "finite_reference_agreement")
        self.assertEqual(measured["status"], "FAIL")
        self.assertEqual(measured["measurement"]["missing_objectives"], ["base.a116"])
        self.assertIn({"objective_id": "base.a116", "split": "train"}, result["missing_training_objectives"])
        l02 = next(s for s in result["stage_measurements"] if s["stage_id"] == "L02")
        self.assertEqual(l02["raw_exact"]["denominator"], 0)
        self.assertEqual(l02["licensed_path"], "NOT_MEASURED")

    def test_other_objective_rows_cannot_fill_the_training_objective_gap(self):
        test = [r for r in self.experiment["rows"] if r["split"] == "test"]
        rows = []
        for part, count in (("train", 20), ("calibration", 5)):
            for case in self.reference["cases"]:
                for i in range(count):
                    row = self.row(f"{part}-{case['id']}-{i}", part, case["kind"])
                    if part == "train":
                        row["objective_id"] = "trace.utf8"
                    rows.append(row)
        self.experiment["rows"] = rows + test
        result = self.evaluate()
        self.assertTrue(all(q["additional_groups"] == 0 for q in result["training_queue"]))
        self.assertEqual(result["missing_training_objectives"], [{"objective_id": "trace.identity", "split": "train"}])
        self.assertNotEqual(self.gate(result, "training_intake")["status"], "PASS")

    def test_missing_negative_stratum_never_has_a_zero_risk_bound(self):
        self.reference["cases"] = [c for c in self.reference["cases"] if c["id"] != "n"]
        self.predictions = [p for p in self.predictions if p["id"] != "n"]
        self.experiment["rows"] = [r for r in self.experiment["rows"] if r["id"] != "n"]
        self.experiment["exposure"] = "SEALED_NEW"
        self.experiment["sampling"]["kind"] = "PROBABILITY_SAMPLE"
        result = self.evaluate()
        self.assertIsNone(result["cluster_metrics"]["false_accept_upper"])
        self.assertEqual(self.gate(result, "false_accept_risk")["status"], "NOT_MEASURED")
        self.assertNotEqual(self.gate(result, "finite_reference_agreement")["status"], "PASS")

    def test_gains_cannot_hide_lost_parent_correct_answers(self):
        parent = deepcopy(self.predictions)
        self.predictions[0] = {"id": "p", "status": "defer", "readings": []}
        parent[1] = {"id": "a", "status": "defer", "readings": []}
        result = self.evaluate(parent_predictions=parent)
        measured = result["cluster_metrics"]["parent"]
        self.assertEqual((measured["gained"], measured["lost"], measured["retained"]), (1, 1, 2))
        self.assertEqual(measured["delta"], 0.0)
        self.assertEqual(measured["parent_correct"], 3)
        self.assertLess(measured["retention_lower"], 0.99)

    def test_interventions_are_reference_agreement_and_cannot_reference_themselves(self):
        self.experiment["interventions"] = [{"id": "withdraw", "before": "p", "after": "u", "type": "withdraw_last_support"}]
        result = self.evaluate()
        pair = result["interventions"][0]
        self.assertTrue(pair["reference_pair_correct"])
        self.assertEqual(pair["authority"], "REFERENCE_INTERVENTION_AGREEMENT_ONLY")
        self.assertEqual(self.gate(result, "interventions")["status"], "NOT_MEASURED")
        for change in ({"after": "p"}, {"after": "unknown"}, {"after": "n"}, {"type": "coordinate_reprojection"}):
            self.experiment["interventions"][0] = {"id": "withdraw", "before": "p", "after": "u", "type": "withdraw_last_support", **change}
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.evaluate()

    def test_current_status_and_completion_exit_code_preserve_open_obligations(self):
        result = criteria.current_report()
        self.assertEqual(result["stage_count"], 13)
        self.assertEqual(result["objective_count"], 66)
        self.assertEqual(result["baseline_replay"], "NOT_RUN")
        self.assertEqual(result["licensed_completion"]["status"], "NOT_MEASURED")
        with patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(criteria.main([]), 0)
            self.assertEqual(criteria.main(["--require-completion"]), 2)

    def test_cli_binds_benchmark_bytes_and_preserves_the_first_output(self):
        pack = {"reference": self.reference, "predictions": self.predictions, "experiment": self.experiment,
                "parent_predictions": None, "control_predictions": None}
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "benchmark.json"
            output = Path(name) / "report.json"
            raw = json.dumps(pack, ensure_ascii=False).encode()
            path.write_bytes(raw)
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(criteria.main(["--benchmark", str(path), "--benchmark-sha256", "0" * 64]), 1)
                self.assertEqual(criteria.main(["--benchmark", str(path), "--benchmark-sha256", sha256(raw).hexdigest(),
                                               "--output", str(output), "--require-completion"]), 2)
            first = output.read_bytes()
            with patch("sys.stdout", new_callable=io.StringIO), self.assertRaises(FileExistsError):
                criteria.main(["--output", str(output)])
            self.assertEqual(output.read_bytes(), first)

    def test_json_duplicate_keys_nonfinite_numbers_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "case.json"
            for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
                path.write_text(raw)
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    criteria.read_json(path)
            path.write_text('{}')
            link = Path(name) / "link.json"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                criteria.read_json(link)

    def test_reference_identity_fields_are_typed_not_truthy_flags(self):
        original = deepcopy(self.reference)
        for field, value in (("scope", True), ("scope", {"name": "scope"}), ("version", True)):
            self.reference = deepcopy(original)
            self.reference[field] = value
            self.experiment["scope_id"] = self.reference["scope"]
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.evaluate()
        self.reference = original
        self.experiment["scope_id"] = original["scope"]
        self.reference["cases"][0]["source_ref"] = True
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_installed_policy_has_strict_types_and_the_actual_seven_claims(self):
        policy = criteria.load_contract()["policy"]
        criteria.validate_policy(policy)
        self.assertEqual(policy["simultaneous_statistical_claims"], 7)
        invalid = [
            ("simultaneous_statistical_claims", value) for value in (True, 0, 6, 8, 7.0)
        ] + [
            ("confidence_family_alpha", value) for value in (True, 0, 1, float("nan"))
        ] + [
            (key, value) for key in ("raw_exact_lower_min", "false_accept_upper_max", "unsupported_accept_upper_max",
                                    "premature_finalization_upper_max", "retention_lower_min")
            for value in (True, -0.1, 1.1, float("nan"), float("inf"))
        ] + [
            ("required_kinds", []), ("required_kinds", ["positive", "ambiguity", "needs_context"]),
            ("required_interventions", ["withdraw_last_support"]),
            ("train_groups_per_stage_kind_min", True), ("calibration_groups_per_stage_kind_min", 0),
            ("critical_errors_max", False), ("critical_errors_max", 1),
            ("finite_reference_exact_required", True), ("finite_reference_exact_required", 0.99),
        ]
        for key, value in invalid:
            edited = deepcopy(policy)
            edited[key] = value
            with self.subTest(key=key, value=value), self.assertRaises((TypeError, ValueError)):
                criteria.validate_policy(edited)
        with self.assertRaises(ValueError):
            criteria.validate_policy(dict(policy, caller_authority="COMPLETE"))

    def test_removing_a_full_path_obligation_invalidates_the_contract(self):
        original_reader = criteria.read_json

        def missing_obligation(path):
            document = original_reader(path)
            if Path(path).name == "stages.json":
                document["full_path_obligations"].pop()
            return document

        with patch.object(criteria, "read_json", side_effect=missing_obligation), self.assertRaises(ValueError):
            criteria.load_contract()

    def test_cli_commitment_is_bound_to_the_bytes_actually_scored(self):
        pack = {"reference": self.reference, "predictions": self.predictions, "experiment": self.experiment,
                "parent_predictions": None, "control_predictions": None}
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "benchmark.json"
            output = Path(name) / "report.json"
            raw = json.dumps(pack, ensure_ascii=False).encode()
            path.write_bytes(raw)
            changed = deepcopy(pack)
            changed["predictions"].pop(0)
            original_reader = criteria.read_json

            def concurrent_replace(candidate):
                # Simulate a writer replacing a file after its first read.
                # The parser must consume the committed bytes, or reject it.
                if Path(candidate) == path:
                    path.write_text(json.dumps(changed, ensure_ascii=False))
                return original_reader(candidate)

            with patch.object(criteria, "read_json", side_effect=concurrent_replace), patch("sys.stdout", new_callable=io.StringIO):
                status = criteria.main(["--benchmark", str(path), "--benchmark-sha256", sha256(raw).hexdigest(),
                                        "--output", str(output)])
            if status == 0:
                report = json.loads(output.read_text())
                self.assertEqual(report["mode_scores"]["raw"]["numerator"], 4)
                self.assertEqual(report["benchmark_bytes_sha256"], sha256(raw).hexdigest())
            else:
                self.assertEqual(status, 1)


if __name__ == "__main__":
    unittest.main()
