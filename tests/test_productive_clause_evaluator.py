"""Synthetic evaluator attacks; no producer imports or acceptance-case execution.

The acquisition check is an explicit test double here. Existing independent
v3 receipt-audit tests cover that layer; these tests attack the new join,
oracle projections, paired-frame counters, and pre-import freeze boundary.
"""
from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import evaluate_productive_clause_v1 as evaluator
from tools import freeze_productive_clause_v1 as freezer


SOURCE = {"schema": "synthetic-source", "sha256": "source-pin", "sources": 1,
          "passages": 1, "passage_ids": ["p1"],
          "lexical_sources": [{"surface": "ضَرَبَ", "lexeme_id": "DARABA", "source_refs": ["p1"]}],
          "authority": "SOURCE_IDENTITY_AND_AUTHORED_SCOPE"}
SAFE = SimpleNamespace(audit_report=lambda *a, **kw: {
    "source_safe": True, "chain_safe": True, "claim_safe": True})


def span(text, start, end):
    return {"raw": text[start:end], "start": start, "end": end,
            "byte_start": len(text[:start].encode()), "byte_end": len(text[:end].encode())}


def fixture():
    text = "ضَرَبَ زَيْدٌ عَمْرًا"
    request = dict(text=text, source_id="synthetic:1", revision="1", scope="unit",
                   ending="wasl", onset="word_initial")
    spans = [span(text, 0, 6), span(text, 7, 13), span(text, 14, 21)]
    roles = [{"role": "verb", "word_index": 0, "lexeme_id": "DARABA", "nominal_case": None},
             {"role": "agent", "word_index": 1, "lexeme_id": "ZAYD", "nominal_case": "nom"},
             {"role": "patient", "word_index": 2, "lexeme_id": "AMR", "nominal_case": "acc"}]
    # Synthetic arrays exercise equality only, never a claim about A116 values.
    cells = [[1, 2], [3, 4], [5, 6]]
    case = {"id": "synthetic", "slice": "positive_in_scope", "family": "unit",
        "frame_id": "frame-1", "surface_variant": "no_full_stop", "input": request,
        "expected": {"syntax_status": "LICENSED_CLAUSE", "word_cells": cells,
            "word_spans": spans, "roles": roles, "reading": {
                "verb_id": "DARABA", "tense": "past", "voice": "active", "order": "VSO",
                "agent_word_index": 1, "patient_word_index": 2},
            "establishes_world_truth": False, "entails_exclusivity": False}}
    tokens = [{**part, "lexeme": role["lexeme_id"], "category": "verb" if index == 0 else "proper_name",
               "nominal_case": role["nominal_case"]} for index, (part, role) in enumerate(zip(spans, roles))]
    reading = {"verb_index": 0, "subject_index": 1, "object_index": 2,
        "verb_lexeme": "DARABA", "subject_lexeme": "ZAYD", "object_lexeme": "AMR",
        "voice": "active", "tense": "past", "order": "VSO", "subject_case": "nom", "object_case": "acc",
        "verb_source": tokens[0], "subject_source": tokens[1], "object_source": tokens[2],
        "source_words": tokens, "referents": None, "world_truth": None}
    native = {**request, "law_id": evaluator.LAW_ID, "status": "LICENSED_CLAUSE", "tokens": tokens,
              "source_pieces": [span(text, 0, len(text))], "reading": reading,
              "reading_id": "DARABA_ZAYD_AMR_VSO"}
    report = {"schema": "nabt.acquired-productive-clause-result.v1", "law_id": evaluator.COMPOSITE_LAW_ID,
        "status": "LICENSED_CLAUSE", "verified": True, "chain_complete": True,
        "binding": {key: value for key, value in request.items() if key != "text"},
        "source_sha256": evaluator.digest(text.encode()), "source_evidence": deepcopy(SOURCE),
        "syntax": {"verified": True, "status": "LICENSED_CLAUSE", "native_result": native},
        "reading": deepcopy(reading), "gates": {key: True for key in evaluator.JOIN_GATES}, "blocked_by": [],
        "acquisition": {"status": "ACQUIRED", "verified": True, "shape_verified": True,
                        "acquisition": {"words": [{"cells": row} for row in deepcopy(cells)]}},
        "world_truth_established": False, "referents_established": False,
        "entails_exclusivity": False, "all_arabic_complete": False}
    report["candidate_space"] = {"domain_id": evaluator.LAW_ID, "unit": "scoped_syntactic_reading",
        "completeness_scope": "installed_finite_grammar", "count_mode": "EXACT", "count": 1,
        "hartley_bits": 0.0, "unknown_reason": None, "world_truth_established": False,
        "candidates": [{"id": "DARABA_ZAYD_AMR_VSO", "state": "LICENSED", "obligations": []}]}
    return case, report


def vos_fixture(*, repeated_name=False):
    """Literal VOS source oracle; never reads gold or calls producer helpers."""
    case, report = fixture()
    text = "ضَرَبَ زَيْدًا زَيْدٌ" if repeated_name else "ضَرَبَ عَمْرًا زَيْدٌ"
    patient_lexeme = "ZAYD" if repeated_name else "AMR"
    patient_surface = "زَيْدًا" if repeated_name else "عَمْرًا"
    spans = [
        {"raw": "ضَرَبَ", "start": 0, "end": 6, "byte_start": 0, "byte_end": 12},
        {"raw": patient_surface, "start": 7, "end": 14, "byte_start": 13, "byte_end": 27},
        {"raw": "زَيْدٌ", "start": 15, "end": 21, "byte_start": 28, "byte_end": 40},
    ]
    expected_roles = [
        {"role": "verb", "word_index": 0, "lexeme_id": "DARABA", "nominal_case": None},
        {"role": "patient", "word_index": 1, "lexeme_id": patient_lexeme, "nominal_case": "acc"},
        {"role": "agent", "word_index": 2, "lexeme_id": "ZAYD", "nominal_case": "nom"},
    ]
    tokens = [{**spans[0], "lexeme": "DARABA", "category": "verb", "nominal_case": None},
              {**spans[1], "lexeme": patient_lexeme, "category": "proper_name", "nominal_case": "acc"},
              {**spans[2], "lexeme": "ZAYD", "category": "proper_name", "nominal_case": "nom"}]
    reading = {"verb_index": 0, "subject_index": 2, "object_index": 1,
        "verb_lexeme": "DARABA", "subject_lexeme": "ZAYD", "object_lexeme": patient_lexeme,
        "voice": "active", "tense": "past", "order": "VOS", "subject_case": "nom", "object_case": "acc",
        "verb_source": tokens[0], "subject_source": tokens[2], "object_source": tokens[1],
        "source_words": tokens, "referents": None, "world_truth": None}
    reading_id = "DARABA_ZAYD_ZAYD_VOS" if repeated_name else "DARABA_ZAYD_AMR_VOS"
    case["input"]["text"] = text
    case["expected"].update(word_spans=spans, roles=expected_roles, reading={
        "verb_id": "DARABA", "tense": "past", "voice": "active", "order": "VOS",
        "agent_word_index": 2, "patient_word_index": 1})
    native = report["syntax"]["native_result"]
    native.update(text=text, tokens=tokens, reading=reading, reading_id=reading_id,
        source_pieces=[{"raw": text, "start": 0, "end": 21, "byte_start": 0, "byte_end": 40}])
    report.update(source_sha256=evaluator.digest(text.encode()), reading=deepcopy(reading))
    report["candidate_space"]["candidates"][0]["id"] = reading_id
    return case, report


def audit(case, report, checks=SAFE):
    return evaluator.audit_clause(case, report, checks, SOURCE)


def defer(report):
    report.update(status="DEFER", verified=False, chain_complete=False, reading=None)
    report["candidate_space"]["candidates"][0]["state"] = "PENDING"


class ProjectionTests(unittest.TestCase):
    def test_complete_synthetic_join(self):
        case, report = fixture()
        result = audit(case, report)
        self.assertTrue(result["complete_chain"])
        self.assertTrue(result["acquisition_complete"])
        self.assertTrue(result["syntax_contract_match"])
        self.assertFalse(result["false_authorization"])

    def test_vos_distinct_names_preserves_source_role_order(self):
        case, report = vos_fixture()
        projected = evaluator.reading_projection(report["syntax"]["native_result"])
        self.assertEqual(projected["roles"], case["expected"]["roles"])
        result = audit(case, report)
        self.assertTrue(result["complete_chain"])
        self.assertTrue(result["syntax_contract_match"])
        self.assertFalse(result["false_authorization"])

    def test_vos_repeated_name_keeps_both_occurrences(self):
        case, report = vos_fixture(repeated_name=True)
        projected = evaluator.reading_projection(report["syntax"]["native_result"])
        self.assertEqual(projected["roles"], case["expected"]["roles"])
        self.assertEqual([(r["role"], r["word_index"]) for r in projected["roles"]],
                         [("verb", 0), ("patient", 1), ("agent", 2)])
        self.assertTrue(audit(case, report)["complete_chain"])

    def test_vos_sorting_does_not_authorize_role_or_source_transfer(self):
        mutations = [
            lambda n: n["reading"].update(object_index=True),
            lambda n: n["reading"].update(subject_index=2.0),
            lambda n: n["reading"].update(subject_index=1),
            lambda n: n["reading"].update(subject_index=1, object_index=2),
            lambda n: n["reading"].update(subject_source=deepcopy(n["tokens"][1])),
            lambda n: n["tokens"][2].update(start=7, byte_start=13),
        ]
        for repeated in (False, True):
            for mutate in mutations:
                with self.subTest(repeated_name=repeated, mutation=mutate):
                    case, report = vos_fixture(repeated_name=repeated)
                    native = report["syntax"]["native_result"]
                    mutate(native)
                    # Keep outer and native readings equal: the failure must be
                    # their source/role binding, not a trivial copy mismatch.
                    report["reading"] = deepcopy(native["reading"])
                    result = audit(case, report)
                    self.assertFalse(result["complete_chain"])
                    self.assertFalse(result["syntax_contract_match"])
                    self.assertTrue(result["false_authorization"])

    def test_typed_json_distinguishes_booleans_floats_and_nonfinite(self):
        self.assertFalse(evaluator.same(True, 1))
        self.assertFalse(evaluator.same(1.0, 1))
        self.assertFalse(evaluator.same(float("nan"), float("nan")))
        self.assertFalse(evaluator.same({"x": False}, {"x": 0}))

    def test_each_source_binding_and_role_mutation_refuses_status_credit(self):
        mutations = [
            lambda r: r["binding"].update(scope="elsewhere"),
            lambda r: r["syntax"]["native_result"].update(revision="2"),
            lambda r: r["syntax"]["native_result"]["tokens"][1].update(byte_start=0),
            lambda r: r["syntax"]["native_result"]["reading"].update(subject_index=True),
            lambda r: r["syntax"]["native_result"]["reading"].update(subject_index=2, object_index=1),
            lambda r: r["syntax"]["native_result"]["reading"].update(subject_lexeme="BAKR"),
            lambda r: r["syntax"]["native_result"]["reading"].update(referents={"agent": "external person"}),
            lambda r: r["syntax"]["native_result"]["source_pieces"][0].update(start=False),
            lambda r: r.update(schema="unversioned", verified=1),
            lambda r: r.update(entails_exclusivity=True),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                case, report = fixture(); mutate(report)
                result = audit(case, report)
                self.assertTrue(result["false_authorization"])
                self.assertFalse(result["complete_chain"])
                self.assertFalse(result["syntax_contract_match"])

    def test_join_requires_every_gate_cell_native_and_citation_link(self):
        mutations = [lambda r: r["gates"].pop("source_shapes"),
            lambda r: r["gates"].update(source_shapes=1),
            lambda r: r["syntax"].update(verified=False),
            lambda r: r["acquisition"].update(shape_verified=False),
            lambda r: r["acquisition"]["acquisition"]["words"][0].update(cells=[True, 2]),
            lambda r: r["source_evidence"].pop("passage_ids"),
            lambda r: r["source_evidence"]["lexical_sources"][0].update(source_refs=[]),
            lambda r: r.update(source_sha256="wrong"),
            lambda r: r.update(blocked_by=["source_shapes"])]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                case, report = fixture(); mutate(report)
                result = audit(case, report)
                self.assertFalse(result["complete_chain"])
                self.assertTrue(result["false_authorization"])

    def test_repeated_name_still_requires_distinct_occurrence(self):
        case, report = fixture()
        native = report["syntax"]["native_result"]
        native["tokens"][2]["lexeme"] = "ZAYD"
        native["reading"]["object_lexeme"] = "ZAYD"
        native["reading"]["object_source"] = deepcopy(native["tokens"][1])
        report["reading"] = deepcopy(native["reading"])
        case["expected"]["roles"][2]["lexeme_id"] = "ZAYD"
        self.assertFalse(audit(case, report)["complete_chain"])

    def test_correct_nested_syntax_with_acquisition_debt_is_miss(self):
        case, report = fixture(); defer(report)
        report["acquisition"].update(status="DEFER", verified=False, shape_verified=False)
        report["gates"]["source_acquired"] = False
        report["blocked_by"] = ["source_acquired"]
        report["candidate_space"]["candidates"][0]["obligations"] = ["source_acquired"]
        result = audit(case, report)
        self.assertTrue(result["syntax_contract_match"])
        self.assertFalse(result["complete_chain"])
        self.assertFalse(result["acquisition_complete"])
        self.assertFalse(result["false_authorization"])

    def test_unsafe_nested_acquisition_is_not_hidden_by_outer_defer(self):
        case, report = fixture(); defer(report)
        unsafe = SimpleNamespace(audit_report=lambda *a, **kw: {
            "source_safe": False, "chain_safe": False, "claim_safe": False})
        result = audit(case, report, unsafe)
        self.assertTrue(result["false_authorization"])
        self.assertFalse(result["syntax_contract_match"])

    def test_outside_null_projections_remain_unmeasured_and_no_license(self):
        case, report = fixture(); defer(report)
        case["slice"] = "outside_scope"; case["frame_id"] = None
        case["expected"].update(syntax_status="DEFER", word_cells=None, word_spans=None, roles=[], reading=None)
        report["syntax"].update(status="DEFER")
        report["syntax"]["native_result"].update(status="DEFER", reading=None, reading_id=None)
        report["candidate_space"].update(count_mode="UNMEASURED", count=None, hartley_bits=None,
            candidates=[], unknown_reason="NATIVE_READING_NOT_WITHIN_VERIFIED_SCOPE")
        result = audit(case, report)
        self.assertTrue(result["control_match"])
        self.assertIsNone(result["word_cells_match"])
        self.assertIsNone(result["word_spans_match"])
        report["syntax"]["native_result"]["status"] = "LICENSED_CLAUSE"
        self.assertTrue(audit(case, report)["false_authorization"])

    def test_candidate_identity_count_and_pending_license_are_checked(self):
        mutations = [lambda r: r.pop("candidate_space"),
            lambda r: r["candidate_space"].update(count=999),
            lambda r: r["candidate_space"].update(count=True),
            lambda r: r["candidate_space"].update(hartley_bits=1.0),
            lambda r: r["candidate_space"].update(domain_id="unbounded"),
            lambda r: r["candidate_space"]["candidates"][0].update(id="borrowed"),
            lambda r: r["syntax"]["native_result"].update(reading_id="borrowed")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                case, report = fixture(); mutate(report)
                result = audit(case, report)
                self.assertFalse(result["complete_chain"])
                self.assertTrue(result["false_authorization"])
        case, report = fixture(); defer(report)
        report["candidate_space"]["candidates"][0]["state"] = "LICENSED"
        self.assertTrue(audit(case, report)["false_authorization"])

    def test_rejection_cannot_hide_acquisition_debt(self):
        case, report = fixture(); defer(report)
        case["slice"] = "negative_in_scope"
        case["expected"].update(syntax_status="REJECTED_IN_SCOPE", roles=[], reading=None)
        report["status"] = report["syntax"]["status"] = "REJECTED_IN_SCOPE"
        report["syntax"]["native_result"].update(status="REJECTED_IN_SCOPE", reading=None, reading_id=None)
        report["gates"]["finite_grammar_reading"] = False
        report["blocked_by"] = ["finite_grammar_reading"]
        report["candidate_space"].update(count=0, hartley_bits=None, candidates=[])
        self.assertTrue(audit(case, report)["control_match"])
        report["acquisition"].update(status="DEFER", verified=False, shape_verified=False)
        report["gates"]["source_acquired"] = False
        report["blocked_by"] = ["source_acquired", "finite_grammar_reading"]
        result = audit(case, report)
        self.assertTrue(result["candidate_space_consistent"])
        self.assertFalse(result["control_match"])
        self.assertTrue(result["false_authorization"])


class FreezeBoundaryTests(unittest.TestCase):
    def test_review1_refuses_first_before_any_runtime_or_bootstrap(self):
        with patch.object(evaluator, "load_bootstrap") as bootstrap:
            with self.assertRaisesRegex(ValueError, "exposed reruns only"):
                evaluator.verify_freeze(Path("unused.json"), "first")
            bootstrap.assert_not_called()

    def test_pinned_bootstrap_strict_json(self):
        guard = evaluator.load_bootstrap()
        for raw in (b'{"a":1,"a":2}', b'{"a":{"b":1,"b":2}}', b'{"a":NaN}', b'[]'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                guard.parse_json(raw)

    def test_initial_snapshot_binds_sources_natives_gold_and_head(self):
        inner = {"files": {"source": "s"}, "native": {"native": "n"}, "commit": "implementation"}
        initial = {"files": {"source": "s", "native": "n"}, "head": "implementation",
                   "gold_sha256": evaluator.GOLD_SHA256}
        for phase in ("first", "exposed"):
            guard = SimpleNamespace(snapshot=lambda *_: deepcopy(initial))
            self.assertEqual(evaluator.initial_snapshot(guard, inner, phase), initial)
            for field in ("source", "native", "gold"):
                bad = deepcopy(initial)
                if field == "gold": bad["gold_sha256"] = "changed"
                else: bad["files"][field] = "changed"
                with self.subTest(phase=phase, field=field), self.assertRaises(ValueError):
                    evaluator.initial_snapshot(SimpleNamespace(snapshot=lambda *_: bad), inner, phase)
        initial["head"] = "later"
        with self.assertRaises(ValueError):
            evaluator.initial_snapshot(guard, inner, "first")

    def test_required_inventory_uses_shared_bootstrap_and_all_packet_sources(self):
        guard = evaluator.load_bootstrap()
        inventory = {"tools/new_reader.py", "formal/New.lean", "src/nabt/data/test.json"}
        sources = {"sources": [{"local_path": "src/nabt/data/source_evidence/qatr.txt"}], "source_registries": []}
        packets = [{"sources": [{"repository_path": "raw/source.txt"}],
                    "passages": [{"local_path": "raw/passage.txt"}],
                    "upstream_dependencies": [{"path": "frozen/upstream.json"}]}]
        actual = evaluator.required_paths(guard, inventory, sources, packets)
        self.assertTrue(inventory <= actual)
        self.assertTrue(evaluator.REFERENCES <= actual)
        self.assertTrue({"raw/source.txt", "raw/passage.txt", "frozen/upstream.json"} <= actual)
        self.assertFalse(actual & evaluator.NATIVE_PATHS)
        packets[0]["sources"][0]["repository_path"] = "../escape"
        with self.assertRaises(ValueError):
            evaluator.required_paths(guard, inventory, sources, packets)

    def test_exposed_phase_does_not_relax_native_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native = {}
            for name in evaluator.NATIVE_PATHS:
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"native fixture"); path.chmod(0o700)
                native[name] = evaluator.digest(path.read_bytes())
            inner = {"commit": "0" * 40, "files": {**evaluator.PINS,
                      evaluator.BOOTSTRAP_PATH: evaluator.BOOTSTRAP_SHA256,
                      "tools/evaluate_productive_clause_v1.py": "review-source-hash"}, "native": native}
            envelope = {"schema": evaluator.SCHEMA, "evaluator_id": evaluator.EVALUATOR_ID,
                "evaluator_review": evaluator.EVALUATOR_REVIEW, "content_pins": evaluator.PINS,
                "source_commit": evaluator.SOURCE_COMMIT, "matrix_commit": evaluator.MATRIX_COMMIT,
                "bootstrap": {"path": evaluator.BOOTSTRAP_PATH, "sha256": evaluator.BOOTSTRAP_SHA256},
                "baseline": inner}
            guard = SimpleNamespace(load_json=lambda _: (envelope, "manifest"),
                verify_freeze=lambda *args: (inner, {}), git=lambda *a, **kw: "",
                parse_json=lambda _: {}, INFERENCE_SOURCE_PATH="inference.json", GOLD_PATH=root / "old.json",
                local_path=lambda name: root / name)
            with patch.object(evaluator, "load_bootstrap", return_value=guard), \
                    patch.object(evaluator, "required_paths", return_value=set()):
                _, evidence = evaluator.verify_freeze(root / "manifest", "exposed")
                self.assertEqual(evidence["evaluator_id"], evaluator.EVALUATOR_ID)
                self.assertEqual(evidence["evaluator_sha256"], "review-source-hash")
                envelope["evaluator_id"] = "old-evaluator"
                with self.assertRaises(ValueError):
                    evaluator.verify_freeze(root / "manifest", "exposed")
                envelope["evaluator_id"] = evaluator.EVALUATOR_ID
                name = sorted(native)[0]
                (root / name).write_bytes(b"changed executable")
                with self.assertRaisesRegex(ValueError, "native executable"):
                    evaluator.verify_freeze(root / "manifest", "exposed")
                inner["native"].pop(name)
                with self.assertRaisesRegex(ValueError, "exactly the four"):
                    evaluator.verify_freeze(root / "manifest", "exposed")

    def test_preflight_failure_is_retained_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "first.json"
            args = ["--output", str(output), "--code-freeze", "missing.json", "--phase", "first"]
            with patch.object(evaluator, "verify_freeze", side_effect=ValueError("synthetic boundary failure")), \
                    patch.object(evaluator, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluator.main(args), 2)
                run.assert_not_called()
                saved = output.read_bytes()
                self.assertEqual(json.loads(saved)["failure_stage"], "preflight")
                with self.assertRaises(FileExistsError): evaluator.main(args)
                self.assertEqual(output.read_bytes(), saved)

    def test_freeze_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "freeze.json"
            output.write_text("retain me")
            with patch.object(freezer, "build_freeze", return_value={}):
                with self.assertRaises(FileExistsError): freezer.main(["--output", str(output)])
            self.assertEqual(output.read_text(), "retain me")


class PopulationTests(unittest.TestCase):
    def test_frame_requires_both_distinct_surface_variants(self):
        case, report = fixture()
        row = {**{key: case[key] for key in ("id", "slice", "frame_id", "surface_variant")},
               **audit(case, report), "raw_result": report}
        other = deepcopy(row); other.update(id="other", surface_variant="full_stop")
        self.assertEqual(evaluator.counts([row, other])["positive_frames"]["complete"], 1)
        other["complete_chain"] = False
        summary = evaluator.counts([row, other])
        self.assertEqual(summary["positive_surfaces"]["complete"], 1)
        self.assertEqual(summary["positive_frames"]["complete"], 0)
        self.assertEqual(summary["positive_surfaces"]["misses"], ["other"])
        other["complete_chain"] = True; other["surface_variant"] = "no_full_stop"
        self.assertEqual(evaluator.counts([row, other])["positive_frames"]["complete"], 0)

    def test_empty_population_never_passes(self):
        self.assertFalse(evaluator.acceptance(evaluator.counts([]), True)["passed"])


if __name__ == "__main__":
    unittest.main()
