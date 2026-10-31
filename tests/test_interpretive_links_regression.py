"""Independent boundary checks for the prospective exposed oracle migration."""
from copy import deepcopy
from hashlib import sha256
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import interpretive_links_regression as runner


class CurrentOracleProtocolTests(unittest.TestCase):
    def test_typed_public_call_replay_rejects_bool_ids_reorder_and_extra_fields(self):
        original = {"kind": "public_api_call", "call_id": 1, "name": "learn_qac_lexicon",
                    "case_id": "H01", "question_index": None, "inputs": {"source_id": "authored"},
                    "returned": {"source": {"id": "authored"}}}
        for change in ({"call_id": True}, {"call_id": 2}, {"question_index": False},
                       {"case_id": "H02"}, {"extra_authority": True}, {"error": "ignored"}):
            stream = runner.Calls(saved=[{**deepcopy(original), **change}])
            with self.subTest(change=change), self.assertRaises(ValueError):
                stream.call("learn_qac_lexicon", original["inputs"], cid="H01")
        stream = runner.Calls(saved=[original])
        self.assertEqual(stream.call("learn_qac_lexicon", original["inputs"], cid="H01"), original["returned"])
        stream.complete(1, {"learn_qac_lexicon": 1})

    def test_observation_is_bound_in_full_to_actual_calls_and_order(self):
        row = {"kind": "case_observation", "case_id": "N01", "score": {"passed": True},
               "record": {"report": {"claims": []}}}
        stream = runner.Calls(saved=[deepcopy(row)])
        with self.assertRaises(ValueError):
            stream.emit({**row, "record": {"report": {"claims": ["invented"]}}})
        stream.emit(row)
        with self.assertRaises(ValueError):
            stream.emit(row)

    def test_current_contract_cannot_accept_historical_or_extra_authority_payloads(self):
        report = {key: None for key in runner.REPORT_KEYS}
        report.update(schema="nabt.discourse-report.v2", reader_version="nabt.discourse-reader.v8",
                      claim_binding_schema="nabt.claim-predication-binding.v1", clauses=[])
        runner.current_payload("read_discourse", report)
        for change in ({"schema": "nabt.discourse-report.v1"}, {"reader_version": "nabt.discourse-reader.v7"},
                       {"nominal_morphology": {}}, {"world_verified": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                runner.current_payload("read_discourse", {**report, **change})
        answer = {key: None for key in runner.ANSWER_KEYS}
        answer.update(schema="nabt.discourse-answer.v3", reader_version="nabt.discourse-reader.v8")
        runner.current_payload("ask_discourse", answer)
        for change in ({"schema": "nabt.discourse-answer.v2"}, {"nominal_description_source": {}},
                       {"statistical_blind_sample_claimed": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                runner.current_payload("ask_discourse", {**answer, **change})

    def test_replay_result_is_an_explicit_bool_and_changed_speaker_is_rejected(self):
        for name, expected in (("verify_discourse", True), ("verify_answer_changed_speaker", False)):
            runner.current_payload(name, {"valid": expected})
            for invalid in (int(expected), not expected, None):
                with self.subTest(name=name, invalid=invalid), self.assertRaises(ValueError):
                    runner.current_payload(name, {"valid": invalid})

    def test_current_result_review_rejects_extra_authority_before_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "result.json").write_text(json.dumps({"schema": runner.VERSION, "strict_pass": True}))
            with self.assertRaisesRegex(ValueError, "added or omitted authority fields"):
                runner.review(folder, None, None, None, {})


class CurrentOracleSourceImportTests(unittest.TestCase):
    def test_checked_bytes_survive_temporary_source_and_symlink_swap(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT) as directory, tempfile.TemporaryDirectory() as outside:
            path = Path(directory) / "helper.py"
            path.write_text("VALUE = 'checked'\n")
            row = runner.file_row(path)
            external = Path(outside) / "replacement.py"
            external.write_text("VALUE = 'unapproved'\n")
            with runner.checked_helper_sources([row]):
                path.write_text("VALUE = 'unapproved'\n")
                self.assertEqual(runner.module("direct_checked_helper", path).VALUE, "checked")
                code = SourceFileLoader("dynamic_checked_helper", str(path)).get_code("dynamic_checked_helper")
                scope = {}
                exec(code, scope)
                self.assertEqual(scope["VALUE"], "checked")
                path.unlink()
                path.symlink_to(external)
                code = SourceFileLoader("symlink_checked_helper", str(path)).get_code("symlink_checked_helper")
                scope = {}
                exec(code, scope)
                self.assertEqual(scope["VALUE"], "checked")

    def test_source_must_match_freeze_before_loading_and_unlisted_code_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT) as directory:
            path = Path(directory) / "helper.py"
            path.write_text("VALUE = 1\n")
            row = runner.file_row(path)
            path.write_text("VALUE = 2\n")
            with self.assertRaisesRegex(ValueError, "changed before source import"):
                with runner.checked_helper_sources([row]):
                    pass
            with runner.checked_helper_sources([]), self.assertRaisesRegex(ValueError, "Unfrozen helper import"):
                SourceFileLoader("unfrozen_helper", str(path)).get_code("unfrozen_helper")

    def test_loader_guard_is_restored_even_on_failure(self):
        previous = SourceFileLoader.get_code
        with self.assertRaisesRegex(RuntimeError, "sentinel"):
            with runner.checked_helper_sources([]):
                raise RuntimeError("sentinel")
        self.assertIs(SourceFileLoader.get_code, previous)


class CurrentOracleGateTests(unittest.TestCase):
    def fixture(self):
        retained = json.loads(runner.pinned(runner.ORACLE / "postreview_run_v2/review.json", runner.BASELINE_SHA))
        return {"cases": retained["cases"], "cross_case_checks": retained["cross_case_checks"],
            "mutation_checks": retained["mutation_checks"], "source_counterexamples": {
                "cases": [{"id": "H0" + str(i)} for i in range(1, 7)],
                "summary": {"total": 6, "positive_controls": 2, "negative_cases": 4, "passed": 6,
                    "questions": 4, "status_matches": 4, "independently_validated": 4,
                    "unsafe_check_failures": [], "independent_integrity_failures": [], "gate_pass": True}}}

    def test_retained_partial_result_is_not_full_success_and_new_failures_are_blocked(self):
        results = self.fixture()
        summary = runner.gate(results)
        self.assertTrue(summary["regression_gate_pass"])
        self.assertFalse(summary["strict_pass"])
        self.assertEqual(summary["fixed_cases"], {"total": 22, "passed": 14})
        results["cases"][0]["checks"].append({"check": "new_failure", "passed": False, "kind": "coverage"})
        results["cases"][0]["passed"] = False
        self.assertFalse(runner.gate(results)["regression_gate_pass"])

    def test_exercised_rejection_cannot_become_unexercised_and_source_integrity_is_required(self):
        results = self.fixture()
        results["mutation_checks"][0]["outcome"] = "UNEXERCISED"
        self.assertFalse(runner.gate(results)["regression_gate_pass"])
        results = self.fixture()
        results["source_counterexamples"]["summary"].update(
            independent_integrity_failures=[{"id": "H01", "check": "independent_report_integrity"}], gate_pass=False)
        summary = runner.gate(results)
        self.assertFalse(summary["measurement_valid"])
        self.assertFalse(summary["regression_gate_pass"])

    def test_missing_cases_or_boolean_denominators_are_rejected(self):
        for mutation in ("missing_case", "boolean_count", "untyped_verdict"):
            results = self.fixture()
            if mutation == "missing_case":
                results["cases"].pop()
            elif mutation == "boolean_count":
                results["source_counterexamples"]["summary"]["total"] = True
            else:
                results["cases"][0]["passed"] = 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                runner.gate(results)


class CurrentOracleSourceAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = [runner.file_row(runner.ROOT / path) for path in sorted(runner.dependency_paths())]
        with runner.checked_helper_sources(rows):
            cls.material_runner, cls.sources, _, _ = runner.helpers()
        material, cls.context = cls.sources.load_cases()
        cls.case = material["cases"][0]
        from nabt.corpus_evidence import learn_qac_lexicon
        from nabt.discourse import ask_discourse, read_discourse, verify_discourse, verify_discourse_answer
        api = {f.__name__: f for f in (learn_qac_lexicon, ask_discourse, read_discourse,
                                      verify_discourse, verify_discourse_answer)}
        calls = runner.Calls(log=lambda value: None, api=api)
        raw = (cls.sources.MATERIAL / cls.case["raw_file"]).read_bytes()
        summary = runner.acquire(calls, raw, cls.case["source_id"], cid=cls.case["id"])
        inputs = {**cls.case["input"], "context": cls.context}
        cls.record = runner.observe(calls, cls.case["id"], inputs, cls.case["expected"]["questions"],
                                   {**inputs, "model_summary": summary}, cls.case["source_id"])

    def score(self, record):
        return runner.current_source_score(self.case, record, self.context, self.sources, self.material_runner.E)

    def test_exact_current_schema_is_validated_without_dropping_historical_checks(self):
        old = self.sources.score_case(self.case, self.record, self.context)
        new = self.score(self.record)
        self.assertTrue(new["passed"])
        self.assertEqual(new["schema_adapter"]["payload_fields_removed"], [])
        self.assertFalse(new["schema_adapter"]["historical_check"]["passed"])
        self.assertEqual([c for c in old["checks"] if c["check"] != "independent_report_integrity"],
                         [c for c in new["checks"] if c["check"] != "independent_report_integrity"])

    def test_extra_fields_descriptions_and_missing_selected_link_cannot_be_waived(self):
        for mutation in ("extra", "description", "missing_binding"):
            record = deepcopy(self.record)
            report = record["report"]
            if mutation == "extra":
                report["new_authority"] = True
            elif mutation == "description":
                report["nominal_morphology"] = {}
            else:
                for clause in report["clauses"]:
                    for analysis in clause["analyses"]:
                        analysis["claim_bindings"] = []
            report["report_id"] = sha256(runner.wire({k: v for k, v in report.items() if k != "report_id"})).hexdigest()
            with self.subTest(mutation=mutation):
                score = self.score(record)
                self.assertFalse(score["passed"])
                self.assertFalse(score["schema_adapter"]["complete_current_report_independently_validated"])


if __name__ == "__main__":
    unittest.main()
