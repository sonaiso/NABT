"""Adversarial tests of publication-receipt finalization, not linguistic gold."""

from copy import deepcopy
import gzip
from hashlib import sha256
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "completion_finalizer", ROOT / "evidence/arabic_completion_v3/finalize_validation_v1.py")
FINALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FINALIZER)


def coverage_fixture():
    """Two explicitly authored cases isolate receipt logic from a real score."""
    failure = {"check": "complete", "passed": False}
    references = [
        {"id": "A", "checks": ["complete", "question:0"], "allowed_failures": []},
        {"id": "B", "checks": ["complete", "question:0"], "allowed_failures": [failure]},
    ]
    policy = {"runtime_freeze_sha256": FINALIZER.RUNTIME_SHA256,
              "runtime_snapshot_sha256": FINALIZER.RUNTIME_SNAPSHOT_SHA256,
              "runtime_file_count": 80,
              "suites": {"construction": {"cases": references, "total": 2,
                         "observed_passed": 1, "question_total": 2,
                         "gold_freeze_sha256": "gold", "source_sha256": "source"}}}
    cases = [
        {"id": "A", "passed": True, "failures": [], "false_accepts": [],
         "checks": [{"check": "complete", "passed": True}, {"check": "question:0", "passed": True}]},
        {"id": "B", "passed": False, "failures": [deepcopy(failure)], "false_accepts": [],
         "checks": [deepcopy(failure), {"check": "question:0", "passed": True}]},
    ]
    result = {"measurement_valid": True, "false_accept_count": 0, "false_accept_case_count": 0,
              "execution_errors": [], "question_execution_errors": [], "finalization_errors": [],
              "snapshot": {k: v for k, v in policy.items() if k.startswith("runtime_")},
              "gold_freeze_sha256": "gold", "source_sha256": "source", "cases": cases,
              "total": 2, "passed": 1, "strict_pass": False, "gate_pass": True,
              "gate_integrity_errors": [], "unexpected_failures": [],
              "documented_boundary_inventory_sha256": FINALIZER.POLICY_SHA256,
              "documented_boundary_runtime_sha256": FINALIZER.RUNTIME_SHA256}
    return policy, result


class CompletionFinalizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "artifacts/local").mkdir(parents=True, exist_ok=True)

    def test_duplicate_json_and_nonfinite_constants_are_rejected(self):
        for raw in (b'{"passed":1,"passed":2}', b'{"passed":NaN}', b'{"passed":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                FINALIZER.parse(raw)

    def test_input_inventory_uses_the_runners_component_order_and_unique_paths(self):
        names = ["formal/Nabt/Fixture.lean", "formal/Nabt.lean"]
        rows = [{"path": name, "bytes": 0, "sha256": "unit"} for name in names]

        def inventory(entries):
            return {"files": entries, "file_count": len(entries),
                    "sha256": sha256(FINALIZER.wire(entries)).hexdigest()}

        with patch.object(FINALIZER, "checked_identity"):
            self.assertEqual(list(FINALIZER.checked_inventory(inventory(rows))), names)
            for bad in (list(reversed(rows)), rows + [rows[-1]]):
                with self.assertRaisesRegex(ValueError, "unique and ordered"):
                    FINALIZER.checked_inventory(inventory(bad))

    def test_full_gzip_and_terminal_jsonl_record_are_required(self):
        good = gzip.compress(b'{"case":"A"}\n')
        self.assertEqual(FINALIZER.decode_journal(good, "fixture")[2], [{"case": "A"}])
        for bad in (good[:-2], gzip.compress(b'{"case":"A"}'),
                    gzip.compress(b'{"case":"A"}\n\n'), gzip.compress(b'{"case":"A"}\n{')):
            with self.subTest(length=len(bad)), self.assertRaises((ValueError, EOFError, gzip.BadGzipFile)):
                FINALIZER.decode_journal(bad, "fixture")

    def test_exact_reviewed_partial_coverage_remains_partial(self):
        policy, result = coverage_fixture()
        outcome = FINALIZER.check_coverage("construction", result, policy, gate=True)
        self.assertEqual(outcome["passed"], 1)
        self.assertFalse(outcome["strict_pass"])
        self.assertEqual(outcome["failed_cases"], ["B"])

    def test_policy_or_runtime_substitution_cannot_authorize_a_score(self):
        policy, result = coverage_fixture()
        for mutate in (
            lambda r: r.update(documented_boundary_inventory_sha256="caller-policy"),
            lambda r: r["snapshot"].update(runtime_freeze_sha256="caller-runtime"),
            lambda r: r.update(source_sha256="different-source"),
            lambda r: r.update(gold_freeze_sha256="different-gold"),
        ):
            candidate = deepcopy(result)
            mutate(candidate)
            with self.assertRaises(ValueError):
                FINALIZER.check_coverage("construction", candidate, policy, gate=True)

    def test_omitted_case_check_or_failure_cannot_improve_the_score(self):
        policy, result = coverage_fixture()
        for mutate in (
            lambda r: r["cases"].pop(),
            lambda r: r["cases"][1]["checks"].pop(),
            lambda r: r["cases"][1]["failures"].clear(),
            lambda r: r["cases"][1]["failures"][0].update(reason="different failure"),
            lambda r: r.update(passed=2, strict_pass=True),
        ):
            candidate = deepcopy(result)
            mutate(candidate)
            with self.assertRaises(ValueError):
                FINALIZER.check_coverage("construction", candidate, policy, gate=True)

    def test_false_acceptance_errors_and_numeric_booleans_are_never_waived(self):
        policy, result = coverage_fixture()
        for mutate in (
            lambda r: r.update(false_accept_count=1),
            lambda r: r.update(false_accept_count=False),
            lambda r: r.update(execution_errors=["error"]),
            lambda r: r.update(question_execution_errors=["error"]),
            lambda r: r.update(finalization_errors=["error"]),
            lambda r: r["cases"][0]["checks"][0].update(passed=1),
            lambda r: r.update(passed=True),
        ):
            candidate = deepcopy(result)
            mutate(candidate)
            with self.assertRaises(ValueError):
                FINALIZER.check_coverage("construction", candidate, policy, gate=True)

    def test_unreviewed_policy_pin_stops_finalization(self):
        with patch.object(FINALIZER, "POLICY_SHA256", "not-a-reviewed-pin"):
            with self.assertRaisesRegex(ValueError, "not yet pinned"):
                FINALIZER.reviewed_policy({})

    def test_compiled_audit_log_must_contain_every_named_theorem(self):
        names = ["Nabt.Fixture.a", "Nabt.Fixture.b"]
        log = ("NABT_THEOREM Nabt.Fixture.a AXIOMS [propext]\n"
               "NABT_THEOREM Nabt.Fixture.b AXIOMS []\nNABT_THEOREM_COUNT 2\nNABT_AUDIT_OK\n")
        receipt = {"ok": True, "theorem_count": 2, "project_axioms_allowed": False,
                   "all_nabt_declarations_scanned": True, "observed_axioms": ["propext"],
                   "theorem_axioms": {names[0]: ["propext"], names[1]: []}}
        with patch.object(FINALIZER, "THEOREM_COUNT", 2):
            FINALIZER.check_formal_audit(receipt, log, names)
            for bad in (log.replace("Nabt.Fixture.b", "Nabt.Fixture.a"),
                        log.replace("NABT_THEOREM_COUNT 2", "NABT_THEOREM_COUNT 1"),
                        log.replace("propext", "sorryAx")):
                with self.assertRaises(ValueError):
                    FINALIZER.check_formal_audit(receipt, bad, names)

    def inna_fixture(self, directory):
        """Reuse real wire bytes with an explicit unit-test program-identity fixture.

        Unit tests must not need a locally built Lean binary or treat its old
        host-specific hash as a portable expectation. Actual executable checks
        remain in the separately run transport/full gate.
        """
        source = ROOT / "evidence/arabic_completion_v3/inna_fragment_transport_v2"
        target = directory / "arabic-inna-fragment"
        target.mkdir()
        for name in ("lexical_material.json", "expectations.json", "requests.jsonl", "responses.jsonl", "stderr.bin"):
            shutil.copyfile(source / name, target / name)
        report = FINALIZER.load(source / "report.json")
        program = "formal/.lake/build/bin/arabicInnaFragmentProbe"
        report["files_before"] = [
            {"path": program, "bytes": 0, "sha256": "unit-test-program-identity"}
            if item["path"] == program else FINALIZER.record(ROOT / item["path"])
            for item in report["files_before"]]
        report["files_after"] = deepcopy(report["files_before"])
        report["command"] = [str(ROOT / program)]
        self.save_inna_report(target, report)
        index = {item["path"]: item for item in report["files_before"]}
        return target, report, index

    def validate_inna_fixture(self, run, index):
        original = FINALIZER.checked_identity

        def check(item):
            if item["path"] == "formal/.lake/build/bin/arabicInnaFragmentProbe":
                self.assertEqual(item["sha256"], "unit-test-program-identity")
                return ROOT / item["path"]
            return original(item)

        with patch.object(FINALIZER, "checked_identity", side_effect=check):
            return FINALIZER.check_inna_transport(run, index)

    def save_inna_report(self, target, report):
        report["artifacts"] = [FINALIZER.record(target / name) for name in
                               ("lexical_material.json", "expectations.json", "requests.jsonl", "responses.jsonl", "stderr.bin")]
        (target / "report.json").write_bytes(FINALIZER.wire(report) + b"\n")

    def test_retained_wire_is_rechecked_with_a_unit_program_identity(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "artifacts/local") as tmp:
            run = Path(tmp)
            _, _, index = self.inna_fixture(run)
            result = self.validate_inna_fixture(run, index)
            self.assertEqual(result["checked_cases"], 32)
            self.assertFalse(result["source_acquisition_established"])
            self.assertEqual(result["world_truth"], "NOT_ESTABLISHED")

    def test_inna_escalation_or_wire_change_fails_even_with_rehashed_artifacts(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "artifacts/local") as tmp:
            run = Path(tmp)
            target, report, index = self.inna_fixture(run)
            raw = (target / "responses.jsonl").read_bytes()
            rows = [FINALIZER.parse(line) for line in raw.splitlines()]
            rows[0]["world_truth"] = "ESTABLISHED"
            (target / "responses.jsonl").write_bytes(b"".join(FINALIZER.wire(row) + b"\n" for row in rows))
            self.save_inna_report(target, report)
            with self.assertRaisesRegex(ValueError, "authority boundary"):
                self.validate_inna_fixture(run, index)

    def test_inna_source_must_have_been_stable_for_the_entire_full_gate(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "artifacts/local") as tmp:
            run = Path(tmp)
            _, _, index = self.inna_fixture(run)
            index.pop("examples/construction_training.tsv")
            with self.assertRaisesRegex(ValueError, "shorter execution interval"):
                self.validate_inna_fixture(run, index)


if __name__ == "__main__":
    unittest.main()
