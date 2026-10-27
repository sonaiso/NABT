"""Storage integrity does not change a measurement or supply proof authority."""
from copy import deepcopy
import gzip
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verification_byte_bundle",
    ROOT / "evidence/source_acquisition_v1/pack_verification.py")
BUNDLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUNDLE)


class VerificationByteBundleTests(unittest.TestCase):
    def fixture(self, base):
        source = base / "original"
        source.mkdir()
        data = b"independent raw receipt\x00" * 500
        (source / "first.gz").write_bytes(gzip.compress(data, mtime=10))
        (source / "second.gz").write_bytes(gzip.compress(data, mtime=11))
        (source / "nested").mkdir()
        (source / "nested/شاهد.json").write_bytes(b'{"native_checked":false}\n')
        (source / "empty").write_bytes(b"")
        return source

    def test_round_trip_preserves_exact_gzip_headers_and_all_file_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = self.fixture(base)
            packed = BUNDLE._pack(source, base / "bundle")
            rows = {row["path"]: row for row in packed["files"]}
            self.assertNotEqual(rows["first.gz"]["sha256"], rows["second.gz"]["sha256"])
            self.assertEqual(rows["first.gz"]["segments"][1], rows["second.gz"]["segments"][1])
            self.assertLess(sum(packed["objects"].values()), sum(row["bytes"] for row in packed["files"]))
            BUNDLE._restore(base / "bundle", base / "restored")
            self.assertEqual([p.relative_to(source) for p in BUNDLE._inventory(source)],
                             [p.relative_to(base / "restored") for p in BUNDLE._inventory(base / "restored")])
            for row in packed["files"]:
                raw = (base / "restored" / row["path"]).read_bytes()
                self.assertEqual(raw, (source / row["path"]).read_bytes())
                self.assertEqual(sha256(raw).hexdigest(), row["sha256"])
            self.assertEqual(packed["authority"], "byte-preservation-only")

    def test_changed_archive_is_rejected_before_any_output_is_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            BUNDLE._pack(self.fixture(base), base / "bundle")
            path = base / "bundle/objects.zip"
            path.write_bytes(path.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "Archive changed"):
                BUNDLE._restore(base / "bundle", base / "restored")
            self.assertFalse((base / "restored").exists())

    def test_manifest_tampering_cannot_change_paths_sizes_objects_or_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            original = BUNDLE._pack(self.fixture(base), base / "bundle")
            mutations = []
            for name in ("../escape", "/escape", ".", "nested/../escape"):
                changed = deepcopy(original)
                changed["files"][0]["path"] = name
                mutations.append(changed)
            changed = deepcopy(original); changed["files"].append(deepcopy(changed["files"][0])); mutations.append(changed)
            changed = deepcopy(original); changed["files"][0]["bytes"] = False; mutations.append(changed)
            changed = deepcopy(original); changed["files"][0]["sha256"] = "0" * 64; mutations.append(changed)
            changed = deepcopy(original); changed["files"][0]["segments"] = ["0" * 64]; mutations.append(changed)
            changed = deepcopy(original); changed["authority"] = "kernel-checked"; mutations.append(changed)
            changed = deepcopy(original); changed["objects"][next(iter(changed["objects"]))] = True; mutations.append(changed)
            for index, manifest in enumerate(mutations):
                with self.subTest(mutation=index):
                    (base / "bundle/manifest.json").write_text(json.dumps(manifest))
                    with self.assertRaises(ValueError):
                        BUNDLE._restore(base / "bundle", base / "restored")
                    self.assertFalse((base / "restored").exists())

    def test_existing_outputs_and_source_symlinks_are_never_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = self.fixture(base)
            BUNDLE._pack(source, base / "bundle")
            with self.assertRaisesRegex(ValueError, "new"):
                BUNDLE._pack(source, base / "bundle")
            with self.assertRaisesRegex(ValueError, "new"):
                BUNDLE._restore(base / "bundle", source)
            (source / "link").symlink_to(source / "first.gz")
            with self.assertRaisesRegex(ValueError, "Symlinks"):
                BUNDLE._pack(source, base / "other")
            self.assertFalse((base / "other").exists())


if __name__ == "__main__":
    unittest.main()
