"""Module provenance must not invent repository inputs from virtual filenames."""
from contextlib import chdir
from hashlib import sha256
from importlib.machinery import ModuleSpec
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
import unittest
from unittest.mock import patch

from tools import benchmark_licensed_inference as licensed
from tools import benchmark_linguistic_truth as linguistic
from tools.linguistic_truth import marked_forms, sources
from tools.linguistic_truth.correction import CITATION


class BenchmarkModuleProvenanceTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.root = Path(directory).resolve()
        files = {
            'gold.json': '{}',
            'formal/lean-toolchain': 'test-toolchain\n',
            'evidence/licensed_inference_v1/source_links.json':
                '{"sources":[],"source_registries":[]}',
            'evidence/linguistic_truth_v1/source_inventory.json': '{"sources":[]}',
            CITATION['path']: 'test source bytes',
            str(marked_forms.REVIEW_PATH): 'test review bytes',
            str(sources.SUPPLEMENT_PATH): 'test supplement bytes',
        }
        for name, data in files.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(data)
        self.enterContext(chdir(self.root))
        self.enterContext(patch.object(marked_forms, '_load_review', return_value={'sources': []}))
        # These tests isolate Python-module provenance with a synthetic root.
        # Production byte authentication is covered by the source replay tests;
        # do not ask its pinned reader to authorize this synthetic catalogue.
        self.enterContext(patch.object(sources, 'build_inventory', return_value={'sources': []}))

    def snapshots(self, filename, origin=None):
        module = ModuleType('external_virtual_provenance_fixture')
        module.__file__ = filename
        module.__spec__ = ModuleSpec(module.__name__, loader=None, origin=origin)
        for benchmark, method, key in (
            (licensed, 'snapshot', 'repository_python'),
            (linguistic, 'evidence_snapshot', 'python_repository_modules'),
        ):
            def snapshot(benchmark=benchmark, method=method):
                with patch.object(benchmark, 'ROOT', self.root), \
                     patch.object(benchmark, 'GOLD_PATH', self.root / 'gold.json'), \
                     patch.dict(sys.modules, {module.__name__: module}):
                    return getattr(benchmark, method)()
            # Contexts belong to the actual call, not a suspended generator;
            # a failing assertion must not leave patches active or emit a
            # misleading GeneratorExit subtest error.
            yield snapshot, key

    def test_virtual_relative_filename_is_not_a_repository_input(self):
        # Even an identically named file in cwd does not establish provenance.
        (self.root / '_ops.py').write_text('unrelated = True\n')
        for origin in (None, '_ops.py'):
            for snapshot, key in self.snapshots('_ops.py', origin):
                self.assertNotIn('_ops.py', snapshot()[key])

    def test_relative_filename_preserves_absolute_repository_origin(self):
        source = self.root / 'attested.py'
        source.write_text('value = 1\n')
        for snapshot, key in self.snapshots('_virtual.py', str(source)):
            modules = snapshot()[key]
            self.assertEqual(modules['attested.py'], sha256(source.read_bytes()).hexdigest())
            self.assertNotIn('_virtual.py', modules)

    def test_absolute_external_origin_is_not_rebased_into_repository(self):
        (self.root / '_ops.py').write_text('unrelated = True\n')
        origin = self.root.parent / 'external_source_fixture.py'
        for snapshot, key in self.snapshots('_ops.py', str(origin)):
            self.assertEqual(snapshot()[key], {})

    def test_missing_absolute_repository_source_fails_closed(self):
        missing = self.root / 'missing.py'
        for snapshot, _ in self.snapshots(str(missing)):
            with self.assertRaises(FileNotFoundError):
                snapshot()

    def test_missing_repository_origin_fails_closed(self):
        missing = self.root / 'missing.py'
        for snapshot, _ in self.snapshots('_relative.py', str(missing)):
            with self.assertRaises(FileNotFoundError):
                snapshot()


if __name__ == '__main__':
    unittest.main()
