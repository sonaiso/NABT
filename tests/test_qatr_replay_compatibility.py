"""A parser hardening review cannot authorize arbitrary training-code drift."""
import ast
from contextlib import contextmanager
import difflib
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import check_qatr_artifacts as gate

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/gate.HISTORICAL_RUN


@contextmanager
def altered_bytes(changes):
    original = Path.read_bytes
    paths = {path.resolve(): raw for path, raw in changes.items()}

    def read(path):
        if path.resolve() in paths:
            return paths[path.resolve()]
        return original(path)

    with patch.object(Path, 'read_bytes', read):
        yield


class QatrReplayCompatibilityTests(unittest.TestCase):
    def test_review_admits_only_the_two_explicit_changes_and_requires_model_replay(self):
        result = gate._verify_implementation(ROOT, RUN)
        self.assertEqual(result['status'], 'REVIEWED_IMPLEMENTATION_MIGRATION')
        self.assertEqual(result['changed_files'],
                         ['formal/ProbeJson.lean', 'tools/qatr_training/experiment.py'])
        self.assertIs(result['model_replay_required'], True)
        self.assertNotIn('ok', result)
        self.assertNotIn('native_checked', result)

    def test_every_original_snapshot_remains_exact(self):
        manifest = json.loads((RUN/'code_manifest.json').read_bytes())
        for name, digest in manifest.items():
            self.assertEqual(sha256((RUN/'code_snapshot'/name).read_bytes()).hexdigest(), digest)
        for name in ('formal/ProbeJson.lean', 'tools/qatr_training/experiment.py'):
            with self.subTest(name=name), altered_bytes({RUN/'code_snapshot'/name: b'changed'}):
                with self.assertRaisesRegex(ValueError, 'historical experiment snapshot changed'):
                    gate._verify_implementation(ROOT, RUN)

    def test_unreviewed_drift_in_model_law_or_evaluator_is_rejected(self):
        for name in ('formal/Nabt/QatrReading.lean', 'tools/qatr_training/model.py',
                     'tools/qatr_training/data.py', 'tools/qatr_training/experiment.py',
                     'formal/ProbeJson.lean'):
            with self.subTest(name=name), altered_bytes({ROOT/name: (ROOT/name).read_bytes()+b'\n'}):
                with self.assertRaisesRegex(ValueError, 'unreviewed experiment implementation change'):
                    gate._verify_implementation(ROOT, RUN)

    def test_old_manifest_cannot_be_rewritten_or_have_entries_removed(self):
        manifest = json.loads((RUN/'code_manifest.json').read_bytes())
        missing = dict(manifest)
        del missing['formal/Nabt/QatrRules.lean']
        for raw in (json.dumps(missing).encode(), json.dumps(manifest, sort_keys=True).encode()):
            with self.subTest(raw=sha256(raw).hexdigest()), altered_bytes({RUN/'code_manifest.json': raw}):
                with self.assertRaisesRegex(ValueError, 'unreviewed experiment implementation change'):
                    gate._verify_implementation(ROOT, RUN)

    def test_empty_duplicate_or_escaping_manifest_rejected(self):
        invalid = (b'{}', b'[]', b'null', b'true', b'{"x":"a","x":"b"}',
                   json.dumps({'../outside': 'a'*64}).encode())
        for raw in invalid:
            with self.subTest(raw=raw), altered_bytes({RUN/'code_manifest.json': raw}):
                with self.assertRaises(ValueError):
                    gate._verify_implementation(ROOT, RUN)

    def test_historical_run_cannot_rebase_manifest_and_all_snapshots_to_current_code(self):
        current = {name: (ROOT/name).read_bytes()
                   for name in gate._current_training_paths(ROOT)}
        manifest = json.dumps({name: sha256(raw).hexdigest()
                               for name, raw in current.items()}, sort_keys=True).encode()
        changes = {RUN/'code_manifest.json': manifest,
                   **{RUN/'code_snapshot'/name: raw for name, raw in current.items()}}
        # Every proposed snapshot now agrees with current code, including the
        # later proposal module. That is still a forbidden rewrite of run_01.
        with altered_bytes(changes):
            with self.assertRaisesRegex(ValueError, 'unreviewed experiment implementation change'):
                gate._verify_implementation(ROOT, RUN)

    def test_every_saved_model_and_measurement_artifact_remains_pinned(self):
        review = json.loads((ROOT/gate.REVIEW).read_bytes())
        self.assertEqual(set(review['preserved_artifacts']),
                         {path.name for path in RUN.iterdir() if path.is_file()})
        for name in review['preserved_artifacts']:
            if name == 'code_manifest.json':
                continue  # separately checked before any compatibility admission
            with self.subTest(name=name), altered_bytes({RUN/name: (RUN/name).read_bytes()+b'\n'}):
                with self.assertRaisesRegex(ValueError, 'historical Qatr artifact changed'):
                    gate._verify_implementation(ROOT, RUN)

    def test_caller_cannot_select_another_run_or_modify_the_installed_review(self):
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)/'run'
            other.mkdir()
            shutil.copyfile(RUN/'code_manifest.json', other/'code_manifest.json')
            shutil.copytree(RUN/'code_snapshot', other/'code_snapshot')
            with self.assertRaisesRegex(ValueError, 'unreviewed experiment implementation change'):
                gate._verify_implementation(ROOT, other)
        with altered_bytes({ROOT/gate.REVIEW: (ROOT/gate.REVIEW).read_bytes()+b'\n'}):
            with self.assertRaisesRegex(ValueError, 'compatibility review changed'):
                gate._verify_implementation(ROOT, RUN)
        # Keeping the same run/manifest identity does not authorize replacing
        # the archived-artifact inventory with an empty list of obligations.
        changed_review = json.loads((ROOT/gate.REVIEW).read_bytes())
        changed_review['preserved_artifacts'] = {}
        with altered_bytes({ROOT/gate.REVIEW: json.dumps(changed_review).encode()}):
            with self.assertRaisesRegex(ValueError, 'compatibility review changed'):
                gate._verify_implementation(ROOT, RUN)

    def test_recorded_patch_exactly_describes_the_reviewed_source_change(self):
        review = json.loads((ROOT/gate.REVIEW).read_bytes())
        chunks = []
        for name in sorted(review['changes']):
            chunks.extend(difflib.unified_diff(
                (RUN/'code_snapshot'/name).read_text().splitlines(True),
                (ROOT/name).read_text().splitlines(True),
                fromfile='run_01/code_snapshot/'+name, tofile=name))
        path = ROOT/gate.REVIEW.parent/review['patch_filename']
        self.assertEqual(path.read_text(), ''.join(chunks))
        with altered_bytes({path: path.read_bytes()+b'\n'}):
            with self.assertRaisesRegex(ValueError, 'compatibility patch changed'):
                gate._verify_implementation(ROOT, RUN)

    def test_training_and_all_historical_replay_comparisons_are_preserved(self):
        name = 'tools/qatr_training/experiment.py'
        before = ast.parse((RUN/'code_snapshot'/name).read_text())
        after = ast.parse((ROOT/name).read_text())
        before_functions = {node.name: node for node in before.body if isinstance(node, ast.FunctionDef)}
        after_functions = {node.name: node for node in after.body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(set(before_functions), set(after_functions))
        for name, node in before_functions.items():
            if name != 'replay':
                self.assertEqual(ast.dump(node), ast.dump(after_functions[name]), name)
        old_body, new_body = before_functions['replay'].body, after_functions['replay'].body
        self.assertEqual([ast.dump(node) for node in old_body[3:-1]],
                         [ast.dump(node) for node in new_body[3:-1]])
        # Only the implementation-admission prefix and an explicit receipt in
        # the final return change. No teacher/prediction/native check disappears.
        self.assertEqual(ast.dump(old_body[0]), ast.dump(new_body[0]))
        old_return, new_return = old_body[-1].value, new_body[-1].value
        self.assertEqual([ast.dump(node) for node in old_return.keywords],
                         [ast.dump(node) for node in new_return.keywords[:-1]])
        self.assertEqual(new_return.keywords[-1].arg, 'implementation')


if __name__ == '__main__':
    unittest.main()
