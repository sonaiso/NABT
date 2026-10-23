"""Pinned-object provenance, checked against independent Git fixtures."""

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
import zlib


TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("nabt_upstream_catalog_test", TOOLS / "catalog_upstream.py")
catalog_tool = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(TOOLS))
try:
    spec.loader.exec_module(catalog_tool)
finally:
    sys.path.pop(0)


class PinnedObjectCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "checkout"
        self.root.mkdir()
        self.git("init", "-q")
        self.original = b"-- pinned source\ntheorem original : True := True.intro\n"
        (self.root / "Original.lean").write_bytes(self.original)
        self.git("add", ".")
        self.git("commit", "-qm", "original source")
        self.pin = self.git("rev-parse", "HEAD")

    def git(self, *arguments):
        return subprocess.check_output(
            ["git", "-C", str(self.root), "-c", "core.hooksPath=/dev/null",
             "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
             "-c", "user.name=NABT provenance test",
             "-c", "user.email=provenance@example.invalid", *arguments],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()

    def inventory(self, *, pin=None, repository="local/test"):
        return catalog_tool.catalog([{
            "repository": repository,
            "commit": self.pin if pin is None else pin,
            "path": str(self.root),
        }])

    def assert_original(self, report):
        self.assertEqual(report["declaration_count"], 1)
        self.assertFalse(report["runtime_authority"])
        repository = report["repositories"][0]
        self.assertEqual(repository["commit"], self.pin)
        self.assertEqual(len(repository["files"]), 1)
        source = repository["files"][0]
        self.assertEqual(source["path"], "Original.lean")
        self.assertEqual(source["file_sha256"], hashlib.sha256(self.original).hexdigest())
        self.assertEqual(source["declarations"], [{"name_as_written": "original", "line": 2}])
        self.assertEqual(source["source_url"],
                         f"https://github.com/local/test/blob/{self.pin}/Original.lean")

    def test_moved_head_dirty_index_and_untracked_bytes_do_not_change_pin(self):
        (self.root / "Original.lean").write_text("theorem later : True := True.intro\n")
        (self.root / "Later.lean").write_text("theorem later_file : True := True.intro\n")
        self.git("add", ".")
        self.git("commit", "-qm", "later source")
        self.assertNotEqual(self.git("rev-parse", "HEAD"), self.pin)
        (self.root / "Original.lean").write_text("theorem staged : True := True.intro\n")
        self.git("add", "Original.lean")
        (self.root / "Original.lean").unlink()
        (self.root / "Untracked.lean").write_text("theorem untracked : True := True.intro\n")
        self.assert_original(self.inventory())

    def test_only_full_existing_commit_object_ids_are_accepted(self):
        self.git("tag", "-a", "annotated", "-m", "a tag is not a commit pin")
        invalid = ["HEAD", self.pin[:12], self.pin.upper(), self.pin + "^{tree}",
                   "--all", "0" * 40, False, 1,
                   self.git("rev-parse", "HEAD^{tree}"),
                   self.git("rev-parse", "HEAD:Original.lean"),
                   self.git("rev-parse", "refs/tags/annotated")]
        for pin in invalid:
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                self.inventory(pin=pin)

    def test_symlink_cannot_import_a_source_outside_the_commit(self):
        external = Path(self.temporary.name) / "external.lean"
        external.write_text("theorem outside : True := True.intro\n")
        (self.root / "Escape.lean").symlink_to(external)
        self.git("add", "Escape.lean")
        self.git("commit", "-qm", "untrusted symbolic link")
        self.pin = self.git("rev-parse", "HEAD")
        self.assert_original(self.inventory())

    def test_source_urls_keep_special_filename_bytes_in_the_path(self):
        relative = "نص #?%\t\n.lean"
        raw = "theorem عربي : True := True.intro\n".encode("utf-8")
        (self.root / relative).write_bytes(raw)
        self.git("add", ".")
        self.git("commit", "-qm", "path that must not become a URL fragment")
        self.pin = self.git("rev-parse", "HEAD")
        row = next(item for item in self.inventory()["repositories"][0]["files"]
                   if item["path"] == relative)
        address = urlsplit(row["source_url"])
        self.assertEqual((address.scheme, address.netloc, address.query, address.fragment),
                         ("https", "github.com", "", ""))
        self.assertEqual(unquote(address.path), f"/local/test/blob/{self.pin}/{relative}")
        self.assertEqual(row["file_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(row["declarations"], [{"name_as_written": "عربي", "line": 1}])

    def test_repository_identity_cannot_escape_the_source_url(self):
        for repository in ("local/test/../../other", "../test", "local/..",
                           "local/test#other", "local/test?other", "local/%2e%2e",
                           "https://github.com/local/test", False):
            with self.subTest(repository=repository), self.assertRaises(ValueError):
                self.inventory(repository=repository)

    def test_malformed_tree_cannot_invent_a_parent_traversal_source_path(self):
        # A normal checkout cannot create this path. A literal Git tree can,
        # so validation must not assume the object database passed git fsck.
        child = self.git("rev-parse", "HEAD^{tree}")
        raw_tree = b"40000 ..\x00" + bytes.fromhex(child)
        tree = subprocess.check_output(
            ["git", "-C", str(self.root), "hash-object", "--literally", "-w",
             "-t", "tree", "--stdin"], input=raw_tree,
        ).strip()
        raw_commit = (b"tree " + tree
                      + b"\nauthor Test <test@example.invalid> 1 +0000"
                      + b"\ncommitter Test <test@example.invalid> 1 +0000"
                      + b"\n\nNoncanonical path fixture\n")
        pin = subprocess.check_output(
            ["git", "-C", str(self.root), "hash-object", "-w", "-t", "commit", "--stdin"],
            input=raw_commit,
        ).decode("ascii").strip()
        with self.assertRaisesRegex(ValueError, "canonical relative path"):
            self.inventory(pin=pin)

    def test_local_blob_replacement_cannot_relabel_different_bytes_as_the_pin(self):
        old_blob = self.git("rev-parse", "HEAD:Original.lean")
        replacement = self.root / "Replacement.lean"
        replacement.write_text("theorem replacement : True := True.intro\n")
        new_blob = self.git("hash-object", "-w", str(replacement))
        self.git("replace", old_blob, new_blob)
        self.assert_original(self.inventory())

    def test_local_commit_replacement_cannot_change_the_pinned_tree(self):
        (self.root / "Original.lean").write_text("theorem replacement : True := True.intro\n")
        self.git("add", ".")
        self.git("commit", "-qm", "replacement commit")
        replacement = self.git("rev-parse", "HEAD")
        self.git("replace", self.pin, replacement)
        self.assert_original(self.inventory())

    def test_loose_objects_cannot_store_other_bytes_under_commit_tree_or_blob_ids(self):
        original_blob = self.git("rev-parse", "HEAD:Original.lean")
        original_tree = self.git("rev-parse", "HEAD^{tree}")
        forged_raw = b"theorem forged : True := True.intro\n"
        forged_blob = subprocess.check_output(
            ["git", "-C", str(self.root), "hash-object", "-w", "--stdin"],
            input=forged_raw,
        ).decode().strip()
        forged_tree_raw = b"100644 Original.lean\x00" + bytes.fromhex(forged_blob)
        forged_tree = subprocess.check_output(
            ["git", "-C", str(self.root), "hash-object", "-w", "-t", "tree", "--stdin"],
            input=forged_tree_raw,
        ).decode().strip()
        old_commit_raw = subprocess.check_output(
            ["git", "-C", str(self.root), "cat-file", "commit", self.pin])
        forged_commit_raw = old_commit_raw.replace(
            b"tree " + original_tree.encode(), b"tree " + forged_tree.encode(), 1)
        for kind, object_id, replacement in (
            ("blob", original_blob, forged_raw),
            ("tree", original_tree, forged_tree_raw),
            ("commit", self.pin, forged_commit_raw),
        ):
            location = self.root / ".git/objects" / object_id[:2] / object_id[2:]
            saved = location.read_bytes()
            header = kind.encode() + b" " + str(len(replacement)).encode() + b"\x00"
            location.chmod(0o600)
            try:
                location.write_bytes(zlib.compress(header + replacement))
                with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "object identity"):
                    self.inventory()
            finally:
                location.write_bytes(saved)

    def test_nested_tree_identity_is_checked_before_following_its_entries(self):
        nested = self.root / "Nested"
        nested.mkdir()
        (nested / "Child.lean").write_text("theorem child : True := True.intro\n")
        self.git("add", ".")
        self.git("commit", "-qm", "nested source")
        self.pin = self.git("rev-parse", "HEAD")
        tree = self.git("rev-parse", "HEAD:Nested")
        original_blob = self.git("rev-parse", "HEAD:Original.lean")
        changed = b"100644 Child.lean\x00" + bytes.fromhex(original_blob)
        location = self.root / ".git/objects" / tree[:2] / tree[2:]
        location.chmod(0o600)
        location.write_bytes(zlib.compress(b"tree " + str(len(changed)).encode() + b"\x00" + changed))
        with self.assertRaisesRegex(ValueError, "object identity"):
            self.inventory()

    def test_sha256_git_repository_uses_its_full_object_identities(self):
        self.root = Path(self.temporary.name) / "sha256-checkout"
        self.root.mkdir()
        self.git("init", "-q", "--object-format=sha256")
        (self.root / "Original.lean").write_bytes(self.original)
        self.git("add", ".")
        self.git("commit", "-qm", "SHA-256 object format")
        self.pin = self.git("rev-parse", "HEAD")
        self.assertEqual(len(self.pin), 64)
        self.assert_original(self.inventory())


if __name__ == "__main__":
    unittest.main()
