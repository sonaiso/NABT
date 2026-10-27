"""Boundary tests of the diagnostic, independent of frozen reference outcomes."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
from unittest import TestCase
from unittest.mock import patch

from tools import semantic_axes as adapter
from tools import benchmark_semantic_axes as benchmark


def case():
    return {"id": "test-only", "family": "boundary", "input": {"text": "مَدْخَلٌ.", "context": {}},
        "expected": {"syntax": {"clause_form": "nominal", "required_roles": [
            {"surface": "مَدْخَلٌ", "role": "nominal_subject"}]},
            "readings": {"required": [{"force": "ASSERT", "positive": True}],
                         "forbidden": [{"force": "ASSERT", "positive": False}], "selection": "unique"},
            "reference": {"surface": "مَدْخَلٌ", "status": "resolved", "target_ids": ["item"]},
            "motive": {"status": "underdetermined"}, "world": {"status": "not_established"}}}


def report():
    claim = {"positive": True, "predicate_kind": "property", "predicate": "مَدْخَل",
             "tense": "unspecified", "time": [], "place": [], "restriction": []}
    analysis = {"frame": "nominal_predication", "force": "ASSERT", "span": {"start": 0, "end": 8},
                "analysis_id": "synthetic-test-analysis", "rejected_candidate": False, "licensed_syntax": True,
                "assignments": [{"surface": "مَدْخَلٌ", "actual_role": "nominal_subject", "activated": True}],
                "claims": [claim], "references": [{"surface": "مَدْخَلٌ", "status": "RESOLVED",
                    "candidate_entity_ids": ["item"], "bound_entity_id": "item", "reference_id": "synthetic-ref"}]}
    return {"status": "LICENSED_DISCOURSE", "world_truth": "NOT_ESTABLISHED", "claims": [claim],
            "clauses": [{"status": "LICENSED", "force": "ASSERT", "analyses": [analysis], "obligations": []}]}


def execution(item=None, raw=None):
    item = case() if item is None else item
    raw = report() if raw is None else raw
    return adapter.execute_request(item["input"], lexical_model={},
        reader=lambda *args, **kwargs: deepcopy(raw),
        verifier=lambda *args, **kwargs: {"valid": True, "status": "VERIFIED"})


class SemanticAxesAdapterTests(TestCase):
    def test_gold_and_case_labels_do_not_cross_input_boundary(self):
        item = case()
        item["secret_expected_answer"] = "must not enter runtime"
        request = adapter.build_request(item)
        self.assertEqual(set(request), {"text", "context"})
        request["context"]["changed"] = True
        self.assertEqual(item["input"]["context"], {})

    def test_input_cannot_smuggle_expected_or_proof(self):
        for key in ("expected", "proof", "claims", "case_id", "lexical_model"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                adapter.validate_request({**case()["input"], key: {}})

    def test_input_identity_preserves_raw_unicode(self):
        self.assertNotEqual(adapter.identity({"text": "أ"}), adapter.identity({"text": "أ"}))

    def test_unknown_and_rejected_analyses_never_become_readings(self):
        raw = report()
        raw["clauses"][0]["analyses"][0]["rejected_candidate"] = True
        observed = adapter.observe(raw)
        self.assertEqual(observed["syntax"], [])
        self.assertEqual(observed["readings"], [])
        self.assertEqual(observed["references"], [])
        self.assertIsNone(observed["reading_selection"])

    def test_context_alternatives_do_not_forge_lexical_ambiguity(self):
        raw = report()
        second = deepcopy(raw["clauses"][0]["analyses"][0])
        second["analysis_id"] = "another-reference"
        second["references"][0]["bound_entity_id"] = "other"
        raw["clauses"][0]["analyses"].append(second)
        self.assertEqual(adapter.observe(raw)["reading_selection"], "unique")

    def test_query_is_not_fed_to_reader_or_interpreted_as_answer(self):
        item = case(); item["input"]["query"] = "جواب متوقع؟"
        calls = []
        adapter.execute_request(item["input"], lexical_model={},
            reader=lambda text, **kwargs: calls.append((text, kwargs)) or report(),
            verifier=lambda *args, **kwargs: {"valid": True, "status": "VERIFIED"})
        self.assertEqual(calls[0][0], item["input"]["text"])
        self.assertNotIn("query", calls[0][1])


class SemanticAxesScoringTests(TestCase):
    def test_successful_replay_does_not_measure_motive_or_world(self):
        row = benchmark.score_case(case(), execution())
        self.assertEqual(row["axis_results"]["syntax"]["status"], "PASS")
        for axis in ("motive", "world"):
            self.assertEqual(row["axis_results"][axis]["status"], "UNMEASURED")
            claim = next(c for c in row["claims"] if c["axis"] == axis)
            self.assertFalse(claim["verification"]["checked"])
            self.assertEqual(claim["verification"]["kind"], "NOT_CHECKED")
        self.assertEqual(row["safety_checks"]["no_motive_promotion"], "UNMEASURED")

    def test_contradictory_extra_syntax_is_not_correct_analysis(self):
        raw = report(); other = deepcopy(raw["clauses"][0]["analyses"][0])
        other["frame"] = "verbal_predication"
        raw["clauses"][0]["analyses"].append(other)
        row = benchmark.score_case(case(), execution(raw=raw))
        self.assertEqual(row["axis_results"]["syntax"]["status"], "FAIL")

    def test_bool_integer_polarity_not_coerced(self):
        item = case(); item["expected"]["readings"]["required"][0]["positive"] = 1
        row = benchmark.score_case(item, execution(item))
        self.assertEqual(row["axis_results"]["readings"]["status"], "FAIL")

    def test_empty_gold_requirements_cannot_pass_positive_reading_recall(self):
        item = case(); item["expected"]["readings"]["required"] = []
        row = benchmark.score_case(item, execution(item))
        self.assertEqual(row["axis_results"]["readings"]["status"], "FAIL")
        self.assertIsNone(row["axis_results"]["readings"]["observed"]["required_reading_recall"]["rate"])

    def test_required_roles_must_coexist_in_one_analysis(self):
        item = case(); item["expected"]["syntax"]["required_roles"].append(
            {"surface": "خَبَرٌ", "role": "nominal_predicate"})
        raw = report(); other = deepcopy(raw["clauses"][0]["analyses"][0])
        other["assignments"] = [{"surface": "خَبَرٌ", "actual_role": "nominal_predicate", "activated": True}]
        raw["clauses"][0]["analyses"].append(other)
        row = benchmark.score_case(item, execution(item, raw))
        self.assertEqual(row["axis_results"]["syntax"]["status"], "FAIL")

    def test_unavailable_runtime_retains_eligible_cases_and_null_denominator(self):
        row = benchmark.score_case(case(), {"executed": False, "replay_checked": False})
        metrics = benchmark.summarize([row])
        self.assertEqual(len(row["claims"]), 5)
        for axis in benchmark.AXES:
            self.assertEqual(metrics[axis]["eligible"], 1)
            self.assertEqual(metrics[axis]["unmeasured"], 1)
            self.assertIsNone(metrics[axis]["rate"])

    def test_not_applicable_is_excluded_without_success(self):
        item = case(); item["expected"]["reference"]["status"] = "not_applicable"
        metrics = benchmark.summarize([benchmark.score_case(item, execution(item))])
        self.assertEqual(metrics["reference"]["eligible"], 0)
        self.assertEqual(metrics["reference"]["passed"], 0)
        self.assertIsNone(metrics["reference"]["rate"])

    def test_certificate_bound_to_claim_and_scope_not_portable_to_another_axis(self):
        row = benchmark.score_case(case(), execution())
        measured = [c for c in row["claims"] if c["verification"]["checked"]]
        self.assertEqual(len({c["verification"]["certificate_sha256"] for c in measured}), len(measured))
        for claim in measured:
            self.assertEqual(claim["verification"]["claim_id"], claim["id"])
            self.assertEqual(claim["verification"]["input_sha256"], row["case_input_sha256"])
            self.assertEqual(claim["verification"]["kind"], "PYTHON_REPLAY")
            self.assertEqual(claim["verification"]["theorem_references"], [])

    def test_failure_receipt_retains_case_and_claims(self):
        with patch.object(benchmark, "load_reference", return_value=({"cases": [case()]}, "a" * 64, {})):
            result = benchmark.run(executor=lambda request: (_ for _ in ()).throw(RuntimeError("unavailable")))
        self.assertEqual(result["case_count"], 1)
        self.assertEqual(len(result["cases"][0]["claims"]), 5)
        self.assertEqual(result["axes"]["syntax"]["unmeasured"], 1)
        self.assertEqual(result["historical_natural_use"]["full_case_success"]["denominator"], 6)
        self.assertEqual(result["historical_natural_use"]["full_case_success"]["numerator"], 0)


class SemanticAxesFreezeTests(TestCase):
    def _copy_reference(self, folder):
        source = benchmark.REFERENCE.parent
        for name in ("reference.json", "reference.sha256", "source_review.json", "freeze.json"):
            shutil.copyfile(source / name, folder / name)
        return folder / "reference.json"

    def test_both_published_frozen_reference_versions_validate(self):
        for path in (benchmark.ROOT / "evidence/semantic_axes_v1/reference.json", benchmark.REFERENCE):
            with self.subTest(path=str(path)):
                reference, frozen, manifest = benchmark.load_reference(path)
                self.assertEqual(len(reference["cases"]), 25)
                self.assertEqual(frozen, manifest["reference_sha256"])

    def test_freeze_cannot_misbind_hash_or_coerce_boolean_count(self):
        for key, value in (("reference_sha256", "0" * 64), ("case_count", True),
                           ("frozen_before_adapter_execution", "true")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary); path = self._copy_reference(folder)
                freeze = json.loads((folder / "freeze.json").read_text())
                freeze[key] = value
                (folder / "freeze.json").write_text(json.dumps(freeze))
                with self.assertRaises(ValueError):
                    benchmark.load_reference(path)

    def test_self_rehashed_gold_is_not_a_new_trusted_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); path = self._copy_reference(folder)
            path.write_bytes(path.read_bytes() + b" ")
            (folder / "reference.sha256").write_text(benchmark.digest(path))
            with self.assertRaises(ValueError):
                benchmark.load_reference(path)


class SemanticAxesRealRuntimeControl(TestCase):
    def test_preexisting_teaching_sentence_survives_adapter_projection(self):
        context = json.loads((benchmark.ROOT / "examples/discourse_context.json").read_text())
        out = adapter.execute_request({"text": "زَيْدٌ عَالِمٌ.", "context": context})
        self.assertTrue(out["replay_checked"])
        self.assertEqual(out["observed"]["reader_status"], "LICENSED_DISCOURSE")
        self.assertTrue(out["observed"]["syntax"])
        self.assertTrue(all(row["clause_form"] == "nominal" for row in out["observed"]["syntax"]))
        self.assertEqual(out["verification_kind"], "PYTHON_REPLAY")
        self.assertFalse(out["lean_native_checked"])

    def test_preexisting_temporal_role_has_declared_projection_not_a_gold_lookup(self):
        context = json.loads((benchmark.ROOT / "examples/discourse_context.json").read_text())
        out = adapter.execute_request({"text": "كَتَبَ زَيْدٌ أَمْسِ.", "context": context})
        roles = [role for row in out["observed"]["syntax"] for role in row["roles"]]
        temporal = [role for role in roles if role["surface"] == "أَمْسِ"]
        self.assertTrue(temporal)
        self.assertTrue(all(role["role"] == "temporal_adverb" and role["runtime_role"] == "time_adverb"
                            for role in temporal))
