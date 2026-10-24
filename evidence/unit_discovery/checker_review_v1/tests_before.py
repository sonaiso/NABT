"""Adversarial adapter tests; these do not stand in for running the Lean probe."""

import copy
import importlib.util
import contextlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nabt_unit_discovery_checker", ROOT / "tools/check_unit_discovery.py")
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def envelope(op, **values):
    return {"law_id": checker.LAW_ID, "scope": checker.SCOPE,
            "conditional": True, "status": "OK", "op": op, **values}


def partition_example():
    request = {"op": "partitions", "atoms": ["a", "b", "c"]}
    response = envelope("partitions", count=4,
                        position_groups=[[[0, 1, 2]], [[0], [1, 2]], [[0, 1], [2]], [[0], [1], [2]]],
                        parts=[[["a", "b", "c"]], [["a"], ["b", "c"]], [["a", "b"], ["c"]], [["a"], ["b"], ["c"]]],
                        cut_sets=[[], [1], [2], [1, 2]])
    return request, response


def ledger_example(request):
    return envelope("ledger", well_formed=True, verdict="UNKNOWN", conflict=False,
                    admitted_ids=[], requirements=[0, *request["target"]["requirements"]],
                    receipt_checks=[{"witness_id": r["witness_id"], "accepted": False, "reason": "FOREIGN_TARGET"}
                                    for r in request["offered"]],
                    per_requirement=[],
                    stages=[{"requirements": [0, *r], "verdict": "UNKNOWN", "conflict": False}
                            for r in request["stage_requirements"]])


class UnitDiscoveryCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = checker.load_material()

    def case(self, case_id):
        return copy.deepcopy(next(c for c in self.material["cases"] if c["id"] == case_id))

    def test_active_v2_preserves_all_expected_values(self):
        old = checker.parse((checker.MATERIAL_DIR / "material_v1.json").read_bytes())
        self.assertEqual([c["expected"] for c in old["cases"]],
                         [c["expected"] for c in self.material["cases"]])
        changed = [x["id"] for x, y in zip(old["cases"], self.material["cases"]) if x != y]
        self.assertEqual(changed, ["UD-A13"])
        self.assertEqual(self.case("UD-A13")["input"]["raw_text"], "حَمْزَةُ")

    def test_expected_answers_cannot_change_probe_requests(self):
        altered = copy.deepcopy(self.material)
        for c in altered["cases"]:
            c["expected"] = {"arbitrary_answer": ["LICENSED", True, 17, {"gender": "invented"}]}
        a, b = checker.make_plan(self.material), checker.make_plan(altered)
        self.assertEqual(a.requests, b.requests)
        self.assertEqual(a.ids.rows, b.ids.rows)

    def test_identifier_map_is_a_bijection_before_execution(self):
        plan = checker.make_plan(self.material)
        ids = [x["id"] for x in plan.ids.rows]
        keys = [(x["namespace"], checker.canonical(x["value"])) for x in plan.ids.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(ids, list(range(1, len(ids) + 1)))
        self.assertEqual(checker.REQUIREMENTS["surface_covered"], 0)

    def test_proper_name_is_not_silently_replaced_by_definite(self):
        plan = checker.make_plan(self.material)
        for item in plan.requests:
            if item["case_id"] in {"UD-A13", "UD-A14"} and item["request"]["op"] == "nominal_profiles":
                self.assertNotIn("proper_name", item["request"]["constraints"])
                self.assertNotIn("definite", item["request"]["constraints"])
                self.assertNotIn("indefinite", item["request"]["constraints"])

    def test_declared_atom_bytes_are_not_normalized(self):
        plan = checker.make_plan(self.material)
        item = next(x for x in plan.requests if x["case_id"] == "UD-A06" and x["label"] == "partitions")
        self.assertEqual("".join(item["request"]["atoms"]), "أَلْوَانٌ")
        item = next(x for x in plan.requests if x["case_id"] == "UD-M08" and x["label"] == "partitions")
        self.assertEqual(item["request"]["byte_offsets"], [2])

    def test_template_literal_comes_from_input_not_surface_or_gold(self):
        plan = checker.make_plan(self.material)
        req = next(x["request"] for x in plan.requests if x["case_id"] == "UD-A04" and x["label"] == "root")
        self.assertIn({"literal": "ِ"}, req["pattern"])
        self.assertNotIn({"literal": "ُ"}, req["pattern"])
        self.assertEqual(req["surface"], "كَاتُبٌ")

    def test_json_types_are_not_python_coercions(self):
        self.assertFalse(checker.equal(True, 1))
        self.assertFalse(checker.equal(False, 0))
        with self.assertRaises(ValueError): checker.parse('{"a":1,"a":2}')
        with self.assertRaises(ValueError): checker.parse('{"a":NaN}')

    def test_valid_complete_partition_fixture(self):
        req, reply = partition_example()
        checker.validate_response(req, reply)

    def test_noncontiguous_or_reordered_positions_rejected(self):
        for groups in ([[0, 2], [1]], [[1, 2], [0]], [[0], [2]]):
            req, reply = partition_example()
            reply["position_groups"][1] = groups
            with self.assertRaises(ValueError): checker.validate_response(req, reply)

    def test_duplicate_partition_cannot_inflate_count(self):
        req, reply = partition_example()
        for key in ("position_groups", "parts", "cut_sets"):
            reply[key][1] = copy.deepcopy(reply[key][0])
        with self.assertRaisesRegex(ValueError, "Duplicate partitions"):
            checker.validate_response(req, reply)

    def test_changed_atom_or_cut_is_not_hidden_by_matching_count(self):
        for mode in ("atom", "cut"):
            req, reply = partition_example()
            if mode == "atom": reply["parts"][0][0][1] = "other"
            else: reply["cut_sets"][0] = [1]
            with self.assertRaises(ValueError): checker.validate_response(req, reply)

    def test_response_must_belong_to_operation_and_conditional_law(self):
        for key, value in (("op", "ledger"), ("conditional", False), ("law_id", "other"), ("status", "ERROR")):
            req, reply = partition_example()
            reply[key] = value
            with self.assertRaises(ValueError): checker.validate_response(req, reply)

    def test_stage_cannot_omit_mandatory_source_requirement(self):
        plan = checker.make_plan(self.material)
        req = next(x["request"] for x in plan.requests if x["case_id"] == "UD-E05" and x["label"] == "ledger")
        reply = ledger_example(req)
        checker.validate_response(req, reply)
        reply["stages"][0]["requirements"] = []
        with self.assertRaisesRegex(ValueError, "Stage requirement correlation"):
            checker.validate_response(req, reply)

    def test_receipt_inventory_and_ids_cannot_be_replaced(self):
        plan = checker.make_plan(self.material)
        req = next(x["request"] for x in plan.requests if x["case_id"] == "UD-E05" and x["label"] == "ledger")
        for mode in ("missing", "foreign_id"):
            reply = ledger_example(req)
            if mode == "missing": reply["receipt_checks"].pop()
            else: reply["receipt_checks"][0]["witness_id"] += 10000
            with self.assertRaises(ValueError): checker.validate_response(req, reply)

    def test_missing_output_is_unmeasured_even_when_expected_is_none(self):
        result = checker.score_case(self.case("UD-A10"), {})
        check = next(x for x in result["checks"] if x["field"] == "actual_case")
        self.assertEqual(check["status"], "UNMEASURED")
        self.assertFalse(result["fully_passed"])

    def test_one_supplied_gender_check_is_not_full_arabic_success(self):
        obs = {"declared_gender": {"value": "masculine", "request_ids": ["fixture"],
                                   "evidence_kind": "SUPPLIED_GENDER_CONSTRAINT"}}
        result = checker.score_case(self.case("UD-A13"), obs)
        self.assertEqual(result["case_status"], "PARTIALLY_MEASURED")
        self.assertEqual(result["measured_check_count"], 1)
        self.assertFalse(result["fully_passed"])
        self.assertEqual(next(x for x in result["checks"] if x["field"] == "declared_definiteness")["status"], "UNMEASURED")

    def test_forbidden_licensing_is_reported_as_false_accept(self):
        c = self.case("UD-E07")
        obs = {"fresh_attachment_status": {"value": "LICENSED", "request_ids": ["fixture"], "evidence_kind": "DIRECT_PROBE_JUDGMENT"}}
        result = checker.score_case(c, obs)
        self.assertEqual(result["failed_check_count"], 1)
        self.assertEqual(result["false_accept_count"], 1)

    def test_all_unknown_cannot_pass_contract_gate(self):
        cases = [checker.score_case(c, {}) for c in self.material["cases"]]
        summary = checker.summarize(cases, [])
        self.assertFalse(summary["gate_pass"])
        self.assertFalse(summary["strict_pass"])
        self.assertEqual(summary["fully_passed_cases"], 0)
        self.assertEqual(len(summary["required_core_judgments_missing"]), 16)

    def test_partial_contract_gate_keeps_missing_arabic_judgments_visible(self):
        cases = []
        for c in self.material["cases"]:
            fields = checker.CORE_REQUIRED_FIELDS.get(c["id"], set())
            obs = {k: {"value": c["expected"][k], "request_ids": ["test_fixture"], "evidence_kind": "TEST_ONLY"}
                   for k in fields}
            cases.append(checker.score_case(c, obs))
        partial = checker.summarize(cases, [])
        strict = checker.summarize(cases, [], require_complete=True)
        self.assertTrue(partial["measured_contract_gate_pass"])
        self.assertFalse(partial["coverage_complete"])
        self.assertFalse(partial["strict_pass"])
        self.assertFalse(strict["gate_pass"])
        self.assertGreater(partial["unmeasured_checks"], 0)
        self.assertLess(partial["fully_passed_cases"], 40)

    def test_source_snapshot_exists_before_process_and_omits_large_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            probe = directory / "synthetic_probe_identity"
            probe.write_bytes(b"not executed: unit-test identity only")
            output = directory / "measurement.json"

            def process_stub(*args, **kwargs):
                before = output.with_suffix(".sources.tar.gz")
                self.assertTrue(before.is_file())
                with tarfile.open(before, "r:gz") as archive:
                    names = archive.getnames()
                    self.assertTrue(any(n.endswith("measurement.requests.json") for n in names))
                    self.assertTrue(any(n.endswith("tools/check_unit_discovery.py") for n in names))
                    self.assertFalse(any(n.endswith(probe.name) for n in names))
                # This is a failed synthetic transport, not a Lean measurement.
                return SimpleNamespace(returncode=1, stdout=b"", stderr=b"synthetic failure")

            with patch.object(checker.subprocess, "run", side_effect=process_stub):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = checker.main(["--probe", str(probe), "--output", str(output)])
            self.assertEqual(code, 1)
            saved = checker.parse(output.read_bytes())
            self.assertFalse(saved["summary"]["gate_pass"])
            self.assertTrue(saved["errors"])
            self.assertFalse(saved["probe_binary_archived"])
            self.assertEqual(saved["probe"]["bytes"], probe.stat().st_size)


if __name__ == "__main__":
    unittest.main()
