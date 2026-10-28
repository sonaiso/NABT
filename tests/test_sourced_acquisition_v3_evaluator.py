"""Evaluator boundaries using synthetic data, never the independent gold."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import evaluate_sourced_acquisition_v3 as evaluator


class FrozenEvaluatorBoundaries(unittest.TestCase):
    def test_projections_preserve_json_scalar_types(self):
        report = {"count": True, "flag": 1, "a/b": [{"~x": "value"}]}
        self.assertEqual(evaluator.matches(report, {"/count": 1, "/flag": True}),
                         {"/count": False, "/flag": False})
        self.assertEqual(evaluator.pointer(report, "/a~1b/0/~0x"), "value")
        for path in ("/a~1b/-1", "/a~1b/00", "/a~1b/١", "/absent", "/count/item"):
            self.assertFalse(evaluator.matches(report, {path: None})[path])

    def test_initial_source_and_native_hashes_are_bound_to_validated_freeze(self):
        freeze = {"files": {"tools/example.py": "source-pin"},
                  "native": {"formal/.lake/build/bin/example": "native-pin"}, "commit": "head"}
        good = {"files": {**freeze["files"], **freeze["native"]},
                "gold_sha256": evaluator.GOLD_SHA256, "head": "head"}
        for target in ("tools/example.py", "formal/.lake/build/bin/example"):
            changed = {**good, "files": {**good["files"], target: "stable-but-not-frozen"}}
            guard = SimpleNamespace(snapshot=lambda *_: changed)
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "initial snapshot"):
                evaluator.initial_snapshot(guard, freeze, "exposed")
        guard = SimpleNamespace(snapshot=lambda *_: good)
        self.assertEqual(evaluator.initial_snapshot(guard, freeze, "first"), good)

    def test_matrix_and_first_head_are_checked_before_execution(self):
        freeze = {"files": {"a": "pin"}, "native": {}, "commit": "expected"}
        for mutation in ({"gold_sha256": "other"}, {"head": "other"}):
            snapshot = {"files": {"a": "pin"}, "gold_sha256": evaluator.GOLD_SHA256,
                        "head": "expected", **mutation}
            with self.assertRaises(ValueError):
                evaluator.initial_snapshot(SimpleNamespace(snapshot=lambda *_: snapshot), freeze, "first")

    def test_required_inventory_includes_new_source_dependencies_and_current_links(self):
        seen = []
        guard = SimpleNamespace(required_freeze_paths=lambda *_: {"tools/base.py"},
                                local_path=lambda path: seen.append(path))
        packets = [{"sources": [{"repository_path": "evidence/retained/source.txt"}],
                    "upstream_dependencies": [{"path": "evidence/upstream.json"}]},
                   {"sources": [{"path": "evidence/lexicon/source.txt"}]}]
        paths = evaluator.required_paths(guard, {"evidence/linguistic_truth_v1/inventory.json"}, {}, packets)
        for name in ("evidence/retained/source.txt", "evidence/lexicon/source.txt",
                     "evidence/upstream.json", "evidence/operator_traceability_v1/registry.json",
                     "evidence/linguistic_truth_v1/inventory.json",
                     "integrations/current_proof_references.mk"):
            self.assertIn(name, paths)
        self.assertTrue(evaluator.REFERENCES <= paths)
        self.assertFalse(evaluator.NATIVE_PATHS & paths)
        self.assertEqual(len(seen), 3)

    def test_failed_first_preflight_is_preserved_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "first.json"
            argv = ["--phase", "first", "--code-freeze", str(Path(directory) / "absent.json"),
                    "--output", str(target)]
            with patch.object(evaluator, "verify_freeze", side_effect=ValueError("synthetic rejected freeze")), \
                    patch.object(evaluator, "run") as run, redirect_stdout(StringIO()):
                self.assertEqual(evaluator.main(argv), 2)
                run.assert_not_called()
                document = json.loads(target.read_text())
                self.assertEqual(document["status"], "EVALUATOR_FAILURE")
                self.assertEqual(document["failure_stage"], "preflight")
                self.assertEqual(document["phase"], "first")
                original = target.read_bytes()
                with self.assertRaises(FileExistsError):
                    evaluator.main(argv)
                self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
