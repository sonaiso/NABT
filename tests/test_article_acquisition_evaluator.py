"""Synthetic provenance/measurement checks; never open the independent v2 gold.

The temporary guard is the real v1 guard source with fixture-only content pins
substituted before compilation. No imported v1 module globals are modified.
"""
from contextlib import ExitStack, redirect_stdout
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from tools import evaluate_article_acquisition as evaluator
from tools import freeze_article_acquisition as freezer


ACQUISITION = '''
def read_acquired(text, *, source_id, revision, scope, onset, ending):
    complete = onset == "word_initial"
    status = "ACQUIRED" if complete else "DEFER"
    piece = {"start": 0, "end": len(text), "byte_start": 0,
             "byte_end": len(text.encode()), "raw": text,
             "status": "LICENSED" if complete else "DEFER", "rule": "FIXTURE",
             "cells": [4] if complete else []}
    word = {key: piece[key] for key in ("start", "end", "byte_start", "byte_end", "cells")}
    word["status"] = status
    return {"schema": "nabt.acquired-reading.v2", "verified": True, "status": status,
      "authority": "NATIVE_REPLAYED_LOCAL_REPRESENTATION", "acquisition": {
        "law_id": "nabt.aligned-acquisition.v2", "alphabet_id": "nabt.a116.v1",
        "source_id": source_id, "revision": revision, "scope": scope, "text": text,
        "onset": onset, "ending": ending, "status": status, "pieces": [piece], "words": [word]},
      "shape_handoffs": [{"word_index": 0, "mode": ending, "certificate": {"mode": ending},
        "status": "SHAPE_LICENSED" if complete else "ACQUISITION_INCOMPLETE",
        "span": {key: word[key] for key in ("start", "end", "byte_start", "byte_end")}}]}
'''
COMPOSITE = '''
import json
from tools.aligned_acquisition_v2 import read_acquired
def evaluate(source, query, **binding):
    scope = json.dumps({"scope": binding["scope"], "time": binding["time"]}, sort_keys=True, separators=(",", ":"))
    common = {key: binding[key] for key in ("source_id", "revision", "onset")}
    source_report = read_acquired(source, **common, scope=scope, ending=binding["source_ending"])
    query_report = read_acquired(query, **common, scope=scope, ending=binding["query_ending"])
    complete = binding["onset"] == "word_initial"
    status = "SUPPORTED" if complete else "DEFER"
    return {"schema": "nabt.acquired-inference-result.v2", "law_id": "nabt.acquired-inference.v2",
      "binding": {**binding, "native_scope": scope}, "source_acquisition": source_report,
      "query_acquisition": query_report, "chain_complete": complete, "verified": complete,
      "world_truth_established": False, "all_arabic_complete": False, "status": status,
      "answer": {"status": status} if complete else None,
      "licensed_inference": {"law_id": "nabt.licensed-inference.v1", "verified": True,
         "native_checked": True, "closures_checked": True, "status": "SUPPORTED",
         "native_result": {"source_text": source, "query_text": query,
            "source_id": binding["source_id"], "revision": binding["revision"], "source_scope": scope}}}
def verify(report, **binding):
    return {"replay_matches": True, "valid": report["chain_complete"]}
'''


class ArticleEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        original = (evaluator.ROOT / evaluator.BOOTSTRAP_PATH).read_text()
        old_gold, old_spec = b"{}\n", b"old fixture spec\n"
        guard_source = original.replace(
            'GOLD_SHA256 = "d94bc45073f21e082c345bef0eb3ac4636451a6695cc247ce447241ee6ffedf7"',
            'GOLD_SHA256 = "' + evaluator.digest(old_gold) + '"').replace(
            'SPEC_SHA256 = "5f8dda47209169b9e3995fc44e3da0bcf1bfc3580fa74a6dbe2afe4cf7687b7f"',
            'SPEC_SHA256 = "' + evaluator.digest(old_spec) + '"').encode()
        self.case = {"id": "independent-fixture", "family": "orthography", "text": "بَ",
            "onset": "word_initial", "ending": "wasl",
            "expected": {"acquisition_status": "ACQUIRED", "word_cells": [[4]]},
            "goal": {"kind": "acquisition", "positive": True}}
        gold = json.dumps({"schema": "nabt.article-acquisition-gold.v1", "cases": [self.case]}).encode()
        source = json.dumps({"sources": [{"repository_path": "evidence/fixture/retained.txt"}]}).encode()
        files = {name: b"{}\n" for name in evaluator.EXTRA_PATHS}
        files.update({evaluator.BOOTSTRAP_PATH: guard_source,
            "tools/freeze_aligned_acquisition.py": b"# producer fixture\n",
            "tools/aligned_acquisition.py": b"# v1 runtime fixture\n",
            "tools/aligned_acquisition_v2.py": ACQUISITION.encode(),
            "tools/acquired_inference_v2.py": COMPOSITE.encode(),
            "tools/evaluate_article_acquisition.py": b"# v2 evaluator fixture\n",
            "tools/freeze_article_acquisition.py": b"# v2 producer fixture\n",
            "tests/test_fixture.py": b"# frozen test\n",
            "src/nabt/data/fixture.json": b"{}\n", "formal/Fixture.lean": b"-- fixture\n",
            "formal/lean-toolchain": b"leanprover/lean4:fixture\n", "formal/lake-manifest.json": b"{}\n",
            "docs/ACQUISITION_READER_SPEC.md": old_spec,
            "evidence/aligned_acquisition_v1/gold.json": old_gold,
            "evidence/aligned_acquisition_v1/source_evidence.json": b"{}\n",
            "evidence/licensed_inference_v1/source_links.json": b'{"sources": [], "source_registries": []}\n',
            "evidence/fixture/retained.txt": b"exact retained bytes\n",
            evaluator.SPEC_PATH: b"v2 fixture specification\n", evaluator.SOURCE_PATH: source,
            evaluator.GOLD_PATH: gold})
        for name, raw in files.items():
            self.write(name, raw)
        for name in evaluator.NATIVE_PATHS:
            self.write(name, b"#!/bin/sh\nexit 0\n")
            (self.root / name).chmod(0o755)
        self.git("init", "-q")
        self.git("add", *files)
        self.commit()
        self.stack.enter_context(patch.multiple(evaluator, ROOT=self.root,
            BOOTSTRAP_SHA256=evaluator.digest(guard_source), SPEC_SHA256=evaluator.digest(files[evaluator.SPEC_PATH]),
            SOURCE_SHA256=evaluator.digest(source), GOLD_SHA256=evaluator.digest(gold),
            MATRIX_COMMIT=self.git("rev-parse", "HEAD"), FAMILY_COUNTS={"orthography": 1}, CELL_CASES=1))
        self.envelope = freezer.build_freeze()
        self.manifest = self.root / "freeze.json"
        self.save()

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self):
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "Synthetic inputs")

    def save(self):
        self.manifest.write_text(json.dumps(self.envelope))

    def validated(self, phase="first"):
        return evaluator.verify_freeze(self.manifest, phase)

    def modules(self):
        acquisition, composite = ModuleType("fixture_acquisition"), ModuleType("fixture_composite")
        exec(ACQUISITION, acquisition.__dict__)
        with patch.dict(sys.modules, {"tools.aligned_acquisition_v2": acquisition}):
            exec(COMPOSITE, composite.__dict__)
        return acquisition, composite

    def test_union_producer_verifier_and_real_source_imports_pass(self):
        required = {evaluator.SPEC_PATH, evaluator.SOURCE_PATH, evaluator.GOLD_PATH,
            "formal/theorems.json", "tools/article_acquisition.mk", "evidence/fixture/retained.txt",
            "integrations/current_proof_references.mk"} | evaluator.REFERENCE_PATHS
        self.assertTrue(required <= set(self.envelope["baseline"]["files"]))
        self.assertEqual(set(self.envelope["baseline"]["native"]), evaluator.NATIVE_PATHS)
        for phase in ("first", "exposed"):
            envelope, evidence = self.validated(phase)
            report = evaluator.run(envelope, evidence, phase)
            self.assertTrue(report["contract_gate"]["passed"])
            self.assertTrue(report["representation_gate"]["passed"])
            self.assertEqual(report["execution_evidence"]["baseline_phase"], "exposed")
            self.assertEqual(report["execution_evidence"]["held_out_first_execution"], phase == "first")
            self.assertIn("tools/aligned_acquisition_v2.py", report["execution_evidence"]["executed_repository_python"])

    def test_every_v2_evidence_and_native_omission_fails(self):
        for name in evaluator.EXTRA_PATHS | {"evidence/fixture/retained.txt"}:
            with self.subTest(path=name):
                original = self.envelope["baseline"]["files"].pop(name)
                self.save()
                with self.assertRaises((ValueError, KeyError)):
                    self.validated()
                self.envelope["baseline"]["files"][name] = original
        for name in evaluator.NATIVE_PATHS:
            with self.subTest(native=name):
                original = self.envelope["baseline"]["native"].pop(name)
                self.save()
                with self.assertRaisesRegex(ValueError, "three native"):
                    self.validated()
                self.envelope["baseline"]["native"][name] = original

    def test_source_native_overlap_cannot_override_a_source(self):
        source = "tools/aligned_acquisition_v2.py"
        self.envelope["baseline"]["files"][next(iter(evaluator.NATIVE_PATHS))] = self.envelope["baseline"]["files"][source]
        self.save()
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            self.validated()

    def test_initial_mutations_fail_before_matrix_or_runtime(self):
        for name in (evaluator.GOLD_PATH, evaluator.SPEC_PATH, evaluator.SOURCE_PATH,
                     "tools/aligned_acquisition_v2.py", "formal/.lake/build/bin/alignedAcquisitionV2"):
            with self.subTest(path=name):
                envelope, evidence = self.validated()
                path = self.root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"changed")
                with patch.object(evaluator, "load_gold") as gold, patch.object(evaluator.importlib, "import_module") as imports:
                    with self.assertRaisesRegex(ValueError, "initial snapshot"):
                        evaluator.run(envelope, evidence, "first")
                    gold.assert_not_called()
                    imports.assert_not_called()
                path.write_bytes(raw)

    def test_original_envelope_and_returned_object_are_bound(self):
        envelope, evidence = self.validated()
        self.manifest.write_text(self.manifest.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "freeze envelope"):
            evaluator.run(envelope, evidence, "first")
        self.save()
        envelope, evidence = self.validated()
        envelope["content_pins"][evaluator.SPEC_PATH] = "0" * 64
        with self.assertRaisesRegex(ValueError, "freeze envelope"):
            evaluator.run(envelope, evidence, "first")

    def test_final_mutation_fails_integrity(self):
        envelope, evidence = self.validated()
        evaluate = evaluator.evaluate_case
        def mutate(*args):
            result = evaluate(*args)
            self.manifest.write_text(self.manifest.read_text() + " ")
            return result
        with patch.object(evaluator, "evaluate_case", side_effect=mutate):
            report = evaluator.run(envelope, evidence, "first")
        self.assertFalse(report["execution_evidence"]["integrity_valid"])
        self.assertFalse(report["contract_gate"]["passed"])

    def test_exposed_baseline_never_establishes_v2_first_chronology(self):
        self.write("later.txt", b"later")
        self.git("add", "later.txt")
        self.commit()
        self.validated("exposed")
        with self.assertRaisesRegex(ValueError, "HEAD"):
            self.validated("first")
        envelope, evidence = self.validated("exposed")
        with self.assertRaisesRegex(ValueError, "first-run HEAD"):
            evaluator.run(envelope, evidence, "first")

    def test_unrelated_matrix_commit_fails_despite_valid_baseline(self):
        tree = self.git("rev-parse", "HEAD^{tree}")
        unrelated = self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                             "commit-tree", tree, "-m", "Unrelated matrix")
        self.envelope["matrix_commit"] = unrelated
        self.save()
        with patch.object(evaluator, "MATRIX_COMMIT", unrelated):
            self.validated("exposed")
            with self.assertRaises(subprocess.CalledProcessError):
                self.validated("first")

    def test_bootstrap_ignores_ambient_module_and_rejects_changed_source(self):
        poison = ModuleType("tools.evaluate_aligned_acquisition")
        poison.marker = "ambient"
        with patch.dict(sys.modules, {"tools.evaluate_aligned_acquisition": poison}):
            guard = evaluator.load_bootstrap()
            self.assertFalse(hasattr(guard, "marker"))
        path = self.root / evaluator.BOOTSTRAP_PATH
        path.write_bytes(path.read_bytes() + b"\nraise RuntimeError('must not execute')\n")
        with self.assertRaisesRegex(ValueError, "bootstrap differs"):
            evaluator.load_bootstrap()

    def test_preflight_failure_and_success_outputs_are_exclusive(self):
        output = self.root / "first-attempt.json"
        command = ["--output", str(output), "--code-freeze", str(self.root / "absent.json"), "--phase", "first"]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(evaluator.main(command), 2)
        result = output.read_bytes()
        self.assertEqual(json.loads(result)["failure_stage"], "preflight")
        with self.assertRaises(FileExistsError):
            evaluator.main(command)
        self.assertEqual(output.read_bytes(), result)
        good = self.root / "synthetic-success.json"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(evaluator.main(["--output", str(good), "--code-freeze", str(self.manifest), "--phase", "first"]), 0)
        self.assertTrue(json.loads(good.read_bytes())["contract_gate"]["passed"])

    def test_cells_and_intervals_reject_bool_aliases_and_wrong_source(self):
        guard = evaluator.load_bootstrap()
        acquisition, _ = self.modules()
        receipt = acquisition.read_acquired("بَ", source_id="fixture", revision="1", scope="fixture", onset="word_initial", ending="wasl")
        for field, value in (("cells", [True]), ("start", False), ("byte_end", 3), ("raw", "بُ")):
            mutant = copy.deepcopy(receipt["acquisition"])
            mutant["pieces"][0][field] = value
            with self.subTest(field=field):
                checks = evaluator.source_checks(guard, mutant, "بَ", "fixture", "fixture", "word_initial", "wasl")
                self.assertFalse(all(checks.values()))

    def test_source_pieces_cannot_cross_independent_word_boundaries(self):
        guard = evaluator.load_bootstrap()
        acquisition, _ = self.modules()
        text = "بَ بَ"
        report = acquisition.read_acquired("بَ", source_id="fixture", revision="1", scope="fixture",
                                            onset="word_initial", ending="wasl")["acquisition"]
        report.update(text=text, words=[
            {"start": 0, "end": 2, "byte_start": 0, "byte_end": 4, "cells": [4], "status": "ACQUIRED"},
            {"start": 3, "end": 5, "byte_start": 5, "byte_end": 9, "cells": [4], "status": "ACQUIRED"}])
        # All partitions restore the source and have valid UTF-8 intervals and
        # A116 cells. Only the first partition respects both word boundaries.
        partitions = (
            (True, [(0, 2, [4]), (2, 3, []), (3, 5, [4])]),
            (False, [(0, 4, [4]), (4, 5, [4])]),  # Exact reported counterexample.
            (False, [(0, 3, [4]), (3, 5, [4])]),  # Wrong last member end only.
            (False, [(0, 2, [4]), (2, 4, []), (4, 5, [4])]),  # Wrong first member start only.
        )
        for expected, intervals in partitions:
            with self.subTest(intervals=intervals):
                report["pieces"] = [{"start": start, "end": end,
                    "byte_start": len(text[:start].encode("utf-8")),
                    "byte_end": len(text[:end].encode("utf-8")), "raw": text[start:end],
                    "cells": cells, "status": "LICENSED" if cells else "BOUNDARY", "rule": "FIXTURE"}
                    for start, end, cells in intervals]
                checks = evaluator.source_checks(guard, report, text, "fixture", "fixture", "word_initial", "wasl")
                self.assertTrue(all(value for key, value in checks.items() if key != "words"))
                self.assertIs(checks["words"], expected)

    def test_conditional_query_mode_full_chain_and_unmeasured_goals_are_separate(self):
        guard = evaluator.load_bootstrap()
        acquisition, composite = self.modules()
        case = copy.deepcopy(self.case)
        case["goal"] = {"kind": "conditional_inference", "positive": True, "query": "بَ",
            "query_ending": "waqf", "expected_status": "SUPPORTED", "expected_chain_complete": True}
        row = evaluator.evaluate_case(guard, case, acquisition, composite)
        self.assertTrue(row["composite_match"])
        self.assertTrue(row["chain_complete"])
        self.assertEqual(row["composite_result"]["binding"]["query_ending"], "waqf")
        self.assertEqual(row["goal"]["outcome"], "SUCCESS")
        case.update(onset="connected", expected={"acquisition_status": "DEFER", "word_cells": [[]]})
        case["goal"].update(expected_status="DEFER", expected_chain_complete=False)
        row = evaluator.evaluate_case(guard, case, acquisition, composite)
        self.assertTrue(row["composite_match"])
        self.assertFalse(row["chain_complete"])
        self.assertEqual(row["nested_inference_status"], "SUPPORTED")
        self.assertEqual(row["goal"]["outcome"], "MISS")
        self.assertEqual(evaluator.counts([row])["conditional"]["positive_supported_complete"], 0)
        for kind in ("person", "nominal_syntax"):
            case["goal"] = {"kind": kind, "positive": True}
            row = evaluator.evaluate_case(guard, case, acquisition, composite)
            self.assertEqual(row["goal"]["measurement_status"], "UNMEASURED")
            self.assertEqual(row["goal"]["outcome"], "MISS")

    def test_bad_composite_binding_shapes_or_native_reading_never_count_as_complete(self):
        guard = evaluator.load_bootstrap()
        acquisition, composite = self.modules()
        case = copy.deepcopy(self.case)
        case["goal"] = {"kind": "conditional_inference", "positive": True, "query": "بَ",
            "query_ending": "wasl", "expected_status": "SUPPORTED", "expected_chain_complete": True}
        evaluate = composite.evaluate
        changes = (
            lambda r: r["binding"].update(onset="connected"),
            lambda r: r["source_acquisition"].update(shape_handoffs=[]),
            lambda r: r["source_acquisition"]["shape_handoffs"][0].update(mode="waqf"),
            lambda r: r["query_acquisition"]["shape_handoffs"][0]["certificate"].update(mode="waqf"),
            lambda r: r["licensed_inference"]["native_result"].update(query_text="بُ"),
            lambda r: r.update(chain_complete=1),
        )
        for change in changes:
            def altered(*args, **kwargs):
                result = evaluate(*args, **kwargs)
                change(result)
                return result
            with patch.object(composite, "evaluate", side_effect=altered):
                row = evaluator.evaluate_case(guard, case, acquisition, composite)
            self.assertFalse(row["chain_complete"])
            self.assertFalse(row["composite_match"])
            self.assertEqual(row["goal"]["outcome"], "MISS")

    def test_pause_shape_mode_applies_only_to_last_word(self):
        acquisition, _ = self.modules()
        receipt = acquisition.read_acquired("بَ", source_id="fixture", revision="1", scope="fixture", onset="word_initial", ending="wasl")
        word = {"start": 3, "end": 5, "byte_start": 5, "byte_end": 9, "cells": [4], "status": "ACQUIRED"}
        receipt["acquisition"]["words"].append(word)
        receipt["shape_handoffs"].append({"word_index": 1, "mode": "waqf", "certificate": {"mode": "waqf"},
            "status": "SHAPE_LICENSED", "span": {key: word[key] for key in ("start", "end", "byte_start", "byte_end")}})
        self.assertTrue(evaluator.complete_shapes(receipt, "waqf"))
        receipt["shape_handoffs"][0].update(mode="waqf", certificate={"mode": "waqf"})
        self.assertFalse(evaluator.complete_shapes(receipt, "waqf"))

    def test_runtime_exception_retains_case_and_positive_miss(self):
        acquisition = SimpleNamespace(read_acquired=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("fixture")))
        row = evaluator.evaluate_case(evaluator.load_bootstrap(), self.case, acquisition, None)
        self.assertFalse(row["executed"])
        self.assertEqual(row["goal"]["outcome"], "MISS")
        self.assertEqual(evaluator.counts([row])["denominator"], 1)
        self.assertEqual(evaluator.counts([row])["runtime_statuses"], {"EVALUATOR_FAILURE": 1})


if __name__ == "__main__":
    unittest.main()
