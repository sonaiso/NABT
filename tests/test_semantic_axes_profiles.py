"""Installed lexical profiles and occurrence counts do not grant interpretation."""
import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from nabt.errors import NabtError
from tools import benchmark_semantic_axes as benchmark
from tools import proof_lab
from tools import semantic_axes as adapter
from tests.test_semantic_axes import case, execution, report


def installed_resources():
    return SimpleNamespace(model=object(), report={
        "source": {"path": "artifacts/local/external/pinned-test-source.gz",
                   "sha256": "a" * 64, "record_count": 10},
        "model_summary": {"lexical_readings": 7},
        "matrix": {"sha256": "b" * 64, "entry_count": 3,
                   "aligned_entry_count": 2, "unmatched_entry_count": 1}})


def coverage_execution(items):
    return {"executed": True, "replay_checked": True,
            "observed": {"acquisition_diagnostics": {"lexical_occurrences": items}}}


class SemanticAxesInstalledProfileTests(TestCase):
    def test_profile_enum_is_fixed_and_rejects_coercion_or_path_values(self):
        self.assertEqual(adapter.LEXICAL_PROFILES, ("teaching_v1", "attested_qac_v1"))
        for profile in (True, 1, None, {}, "../source", "https://example.invalid/source", "custom"):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                adapter.lexical_profile_resources(profile)

    def test_default_execution_keeps_historical_teaching_profile(self):
        resources = ({}, {"path": "teaching", "sha256": "a" * 64}, None)
        with patch.object(adapter, "lexical_profile_resources", return_value=resources) as load:
            result = adapter.execute_request(case()["input"],
                reader=lambda *args, **kwargs: report(),
                verifier=lambda *args, **kwargs: {"valid": True, "status": "VERIFIED"})
        load.assert_called_once_with("teaching_v1")
        self.assertEqual(result["lexical_profile"], "teaching_v1")
        self.assertIsNone(result["lexical_loading"])
        self.assertFalse(result["lean_native_checked"])

    def test_attested_profile_rejects_substituted_model_reader_and_verifier(self):
        for field, substitute in (("lexical_model", {}), ("reader", lambda: None),
                                  ("verifier", lambda: None)):
            with self.subTest(field=field), patch.object(adapter, "lexical_profile_resources") as load:
                with self.assertRaises(ValueError):
                    adapter.execute_request(case()["input"], lexical_profile="attested_qac_v1",
                                            **{field: substitute})
                load.assert_not_called()

    def test_attested_benchmark_rejects_substituted_executor(self):
        with patch.object(benchmark, "load_reference", return_value=({"cases": [case()]}, "a" * 64, {})), \
                patch.object(adapter, "lexical_profile_resources") as load:
            with self.assertRaises(ValueError):
                benchmark.run(lexical_profile="attested_qac_v1", executor=lambda request: {})
            load.assert_not_called()

    def test_installed_source_counts_are_scoped_and_partition_matrix_entries(self):
        loaded = installed_resources()
        with patch("tools.attested_lexical_loader.load_attested_lexicon", return_value=loaded):
            model, source, loading = adapter.lexical_profile_resources("attested_qac_v1")
        self.assertIs(model, loaded.model)
        self.assertEqual(source["sha256"], "a" * 64)
        self.assertEqual(loading["source_record_count"], 10)
        self.assertEqual(loading["model_entry_count"], 7)
        self.assertEqual(loading["matrix_sense_count"], 3)
        self.assertEqual(loading["matrix_aligned_count"], 2)
        self.assertEqual(loading["matrix_unresolved_count"], 1)
        self.assertIs(loading["lean_native_checked"], False)
        self.assertEqual(loading["authority"], "SOURCE_ANNOTATION_NOT_SENSE_OR_WORLD_LICENSE")

    def test_public_source_counts_reject_lossy_or_invalid_integer_values(self):
        paths = (("source", "record_count"), ("model_summary", "lexical_readings"),
                 ("matrix", "entry_count"), ("matrix", "aligned_entry_count"),
                 ("matrix", "unmatched_entry_count"))
        for section, name in paths:
            for bad in (True, False, 1.5, 1.0, "1", None, -1, 1 << 53):
                with self.subTest(section=section, field=name, bad=bad):
                    loaded = installed_resources()
                    loaded.report[section][name] = bad
                    with patch("tools.attested_lexical_loader.load_attested_lexicon", return_value=loaded), \
                            self.assertRaises(ValueError):
                        adapter.lexical_profile_resources("attested_qac_v1")

    def test_source_count_partition_inconsistency_is_not_published(self):
        loaded = installed_resources()
        loaded.report["matrix"]["unmatched_entry_count"] = 2
        with patch("tools.attested_lexical_loader.load_attested_lexicon", return_value=loaded), \
                self.assertRaises(ValueError):
            adapter.lexical_profile_resources("attested_qac_v1")

    def test_absent_source_cannot_be_counted_as_successful_measurement(self):
        unavailable = NabtError("ATTESTED_SOURCE_UNAVAILABLE", "private-source-location", status="DEFER")
        with patch.object(benchmark, "load_reference", return_value=({"cases": [case()]}, "a" * 64, {})), \
                patch("tools.attested_lexical_loader.load_attested_lexicon", side_effect=unavailable), \
                patch.object(adapter, "execute_request") as execute:
            with self.assertRaises(NabtError) as caught:
                benchmark.run(lexical_profile="attested_qac_v1")
        self.assertEqual(caught.exception.code, "ATTESTED_SOURCE_UNAVAILABLE")
        execute.assert_not_called()


class SemanticAxesProfileTransportTests(TestCase):
    ID = "9aa86fdd-6bb8-44bb-9ccb-1f805ab78c81"
    REQUEST = {"schema": proof_lab.REQUEST_SCHEMA, "mode": "semantic_axes",
               "lexical_profile": "attested_qac_v1"}
    IDENTITY = {"code_sha": "a" * 40, "native_sha256": None,
                "runtime_sha256": "b" * 64, "reference_sha256": "c" * 64}

    def test_request_allows_only_installed_profile_selector(self):
        self.assertEqual(proof_lab.validate_payload(json.dumps(self.REQUEST)), self.REQUEST)
        for field in ("source_path", "source_url", "source", "matrix", "lexical_model", "gold", "cases"):
            with self.subTest(field=field), self.assertRaises(proof_lab.RequestError):
                proof_lab.validate_payload(json.dumps({**self.REQUEST, field: "untrusted"}))
        for profile in (True, 1, None, "qac_attested_source_v1", "https://example.invalid/source"):
            with self.subTest(profile=profile), self.assertRaises(proof_lab.RequestError):
                proof_lab.validate_payload(json.dumps({**self.REQUEST, "lexical_profile": profile}))

    def test_live_dispatch_binds_the_selected_profile(self):
        suite = {"schema": "nabt.semantic-axes-benchmark.v1", "lexical_profile": "attested_qac_v1"}
        with patch.object(proof_lab, "_semantic_axes_identity", return_value=self.IDENTITY), \
                patch.object(benchmark, "run", return_value=suite) as run:
            result = proof_lab.run_payload(self.ID, json.dumps(self.REQUEST))
        run.assert_called_once_with(lexical_profile="attested_qac_v1")
        self.assertEqual(result["lexical_profile"], "attested_qac_v1")
        self.assertEqual(result["status"], "SEMANTIC_AXES_COMPLETE")
        self.assertIsNone(result["native_sha256"])

    def test_source_unavailable_produces_failure_receipt_without_suite_or_private_details(self):
        with patch.object(proof_lab, "_semantic_axes_identity", return_value=self.IDENTITY), \
                patch.object(benchmark, "run", side_effect=NabtError(
                    "ATTESTED_SOURCE_UNAVAILABLE", "private-source-location", status="DEFER")):
            result = proof_lab.run_payload(self.ID, json.dumps(self.REQUEST))
        self.assertEqual(result["status"], "EXECUTION_FAILED")
        self.assertEqual(result["request_id"], self.ID)
        self.assertEqual(result["lexical_profile"], "attested_qac_v1")
        self.assertNotIn("semantic_axes", result)
        self.assertNotIn("private-source-location", json.dumps(result))


class SemanticAxesLexicalCoverageTests(TestCase):
    def test_coverage_counts_occurrences_not_unique_tokens_or_number_of_readings(self):
        items = [{"surface": "زَيْدٌ", "reading_count": 1},
                 {"surface": "زَيْدٌ", "reading_count": 7},
                 {"surface": "مَجْهُولٌ", "reading_count": 0}]
        result = benchmark.lexical_coverage(coverage_execution(items))
        self.assertEqual((result["tokens"], result["covered"], result["uncovered"]), (3, 2, 1))
        self.assertEqual(result["items"], items)

    def test_coverage_never_upgrades_failed_syntax_or_reading_axes(self):
        raw = report()
        raw["clauses"][0]["analyses"] = []
        raw["occurrences"] = [{"surface": "مَدْخَلٌ", "readings": [{"source": "test"}]}]
        observed = execution(raw=raw)
        scored = benchmark.score_case(case(), observed)
        self.assertEqual(benchmark.lexical_coverage(observed)["covered"], 1)
        self.assertEqual(scored["axis_results"]["syntax"]["status"], "FAIL")
        self.assertEqual(scored["axis_results"]["readings"]["status"], "FAIL")
        for axis in ("motive", "world"):
            self.assertEqual(scored["axis_results"][axis]["status"], "UNMEASURED")

    def test_coverage_rejects_noninteger_negative_or_unsafe_counts(self):
        for bad in (True, False, 1.0, 1.5, -1, "1", None, 1 << 53):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                benchmark.lexical_coverage(coverage_execution([{"surface": "أَرْضٌ", "reading_count": bad}]))

    def test_coverage_requires_source_surface_in_every_occurrence(self):
        for bad in (None, 1, "", "   "):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                benchmark.lexical_coverage(coverage_execution([{"surface": bad, "reading_count": 1}]))

    def test_absent_diagnostics_or_failed_replay_are_not_zero_or_success(self):
        samples = [
            {"executed": True, "replay_checked": False, "observed": {}},
            {"executed": True, "replay_checked": True, "observed": {}},
            {"executed": True, "replay_checked": True, "observed": {"acquisition_diagnostics": None}},
            {"executed": True, "replay_checked": True, "observed": {"acquisition_diagnostics": {}}},
        ]
        for item in samples:
            with self.subTest(item=item):
                self.assertIsNone(benchmark.lexical_coverage(item))
