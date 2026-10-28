"""Exercise actual imports, timestamp bytecode caches and package shadowing."""
from contextlib import ExitStack
import importlib
from importlib.resources import files
import os
from pathlib import Path
import py_compile
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import evaluate_aligned_acquisition as evaluator


class FrozenRuntimeImportsTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.saved_modules = {n: m for n, m in tuple(sys.modules.items()) if evaluator.runtime_module(n)}
        self.saved_path = sys.path[:]
        def restore():
            for name in tuple(sys.modules):
                if evaluator.runtime_module(name):
                    del sys.modules[name]
            sys.modules.update(self.saved_modules)
            sys.path[:] = self.saved_path
            importlib.invalidate_caches()
        self.stack.callback(restore)
        for name in self.saved_modules:
            del sys.modules[name]
        self.stack.enter_context(patch.object(evaluator, "ROOT", self.root))
        sys.path[:0] = [str(self.root), str(self.root / "src")]
        self.files = {
            "tools/aligned_acquisition.py": b"from nabt import helper\nMARKER = helper.MARKER\n",
            "tools/licensed_inference/__init__.py": b"MARKER = 'good'\n",
            "src/nabt/__init__.py": b"from . import helper\n",
            "src/nabt/helper.py": b"MARKER = 'good'\n",
        }
        for name, raw in self.files.items():
            self.write(name, raw)
        self.freeze = {"files": {name: evaluator.digest(raw) for name, raw in self.files.items()}}

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def test_timestamp_pyc_is_ignored_for_modules_and_package_initializers(self):
        for relative, module in (("src/nabt/helper.py", "nabt.helper"),
                                 ("tools/licensed_inference/__init__.py", "tools.licensed_inference")):
            with self.subTest(module=module):
                path = self.root / relative
                stamp = path.stat().st_mtime_ns
                original = path.read_bytes()
                replacement = original.replace(b"good", b"evil")
                self.assertEqual(len(original), len(replacement))
                path.write_bytes(replacement)
                os.utime(path, ns=(stamp, stamp))
                cache = py_compile.compile(str(path), doraise=True,
                    invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
                path.write_bytes(original)
                os.utime(path, ns=(stamp, stamp))
                # Demonstrate the real bypass: -B disables writes, not cache reads.
                with patch.object(sys, "dont_write_bytecode", True):
                    cached = importlib.import_module(module)
                self.assertEqual(cached.MARKER, "evil")
                cache_bytes = Path(cache).read_bytes()
                with evaluator.frozen_runtime(self.freeze) as imports:
                    fresh = importlib.import_module(module)
                    self.assertEqual(fresh.MARKER, "good")
                    self.assertIsNot(fresh, cached)
                    self.assertEqual(imports.executed[relative], evaluator.digest(original))
                self.assertIs(sys.modules[module], cached)
                self.assertEqual(Path(cache).read_bytes(), cache_bytes)

    def test_external_regular_packages_cannot_shadow_frozen_namespace_or_dependencies(self):
        external = self.root / "installed"
        for name in ("tools", "nabt"):
            self.write("installed/" + name + "/__init__.py", b"MARKER = 'external'\n")
        self.write("installed/tools/aligned_acquisition.py", b"MARKER = 'external'\n")
        self.write("installed/nabt/helper.py", b"MARKER = 'external'\n")
        # A later regular tools package wins over an earlier namespace package.
        sys.path.append(str(external))
        external_tools = importlib.import_module("tools.aligned_acquisition")
        self.assertEqual(external_tools.MARKER, "external")
        # Preload a different nabt dependency as well, from the installed tree.
        sys.path.insert(0, str(external))
        external_nabt = importlib.import_module("nabt.helper")
        self.assertEqual(external_nabt.MARKER, "external")
        with evaluator.frozen_runtime(self.freeze) as imports:
            runtime = importlib.import_module("tools.aligned_acquisition")
            self.assertEqual(runtime.MARKER, "good")
            self.assertEqual(sys.modules["nabt.helper"].MARKER, "good")
            self.assertEqual(Path(runtime.__file__), self.root / "tools/aligned_acquisition.py")
            self.assertIn("src/nabt/helper.py", imports.executed)
        self.assertIs(sys.modules["tools.aligned_acquisition"], external_tools)
        self.assertIs(sys.modules["nabt.helper"], external_nabt)

    def test_unlisted_dependency_is_blocked_before_its_code_executes(self):
        marker = self.root / "executed"
        self.write("tools/unfrozen.py", ("from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n").encode())
        with evaluator.frozen_runtime(self.freeze):
            with self.assertRaisesRegex(ModuleNotFoundError, "absent from validated freeze"):
                importlib.import_module("tools.unfrozen")
        self.assertFalse(marker.exists())

    def test_replacement_after_snapshot_is_rejected_at_source_import(self):
        self.write("src/nabt/helper.py", b"raise AssertionError('unfrozen code executed')\n")
        with evaluator.frozen_runtime(self.freeze), self.assertRaisesRegex(ImportError, "differs from validated freeze"):
            importlib.import_module("tools.aligned_acquisition")

    def test_injected_module_origin_and_package_path_are_rejected(self):
        for field in ("__file__", "__path__"):
            with self.subTest(field=field), self.assertRaisesRegex(ImportError, "(origin|package path) changed"):
                with evaluator.frozen_runtime(self.freeze):
                    module = importlib.import_module("nabt")
                    setattr(module, field, str(self.root / "outside.py") if field == "__file__" else ["/outside"])

    def test_unlisted_namespace_initializer_is_not_silently_ignored(self):
        self.write("tools/__init__.py", b"raise AssertionError('unfrozen initializer')\n")
        with evaluator.frozen_runtime(self.freeze), self.assertRaisesRegex(ImportError, "unfrozen package initializer"):
            importlib.import_module("tools.aligned_acquisition")

    def test_frozen_package_data_remains_readable(self):
        name, raw = "src/nabt/data/fixture.json", b'{"fixed": true}\n'
        self.write(name, raw)
        self.freeze["files"][name] = evaluator.digest(raw)
        with evaluator.frozen_runtime(self.freeze):
            package = importlib.import_module("nabt")
            self.assertEqual(files(package).joinpath("data", "fixture.json").read_bytes(), raw)

    def test_repository_runtime_imports_use_frozen_sources_and_existing_package_data(self):
        actual_root = Path(__file__).resolve().parents[1]
        source_paths = [*actual_root.glob("tools/**/*.py"), *actual_root.glob("src/nabt/**/*.py")]
        frozen = {"files": {p.relative_to(actual_root).as_posix(): evaluator.digest(p.read_bytes())
                            for p in source_paths}}
        with patch.object(evaluator, "ROOT", actual_root), evaluator.frozen_runtime(frozen) as imports:
            acquisition = importlib.import_module("tools.aligned_acquisition")
            inference = importlib.import_module("tools.licensed_inference")
            self.assertTrue(callable(acquisition.read_acquired))
            self.assertTrue(callable(inference.evaluate))
            self.assertIn("tools/aligned_acquisition.py", imports.executed)
            self.assertIn("src/nabt/machine.py", imports.executed)


if __name__ == "__main__":
    unittest.main()
