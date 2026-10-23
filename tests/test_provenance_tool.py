"""Counterexamples for commit provenance, independent of declaration parsing."""

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("nabt_catalog_test", TOOLS / "catalog_upstream.py")
catalog_tool = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(TOOLS))
try:
    spec.loader.exec_module(catalog_tool)
finally:
    sys.path.pop(0)


class CommitProvenanceTests(unittest.TestCase):
    def test_inventory_reads_pinned_blobs_even_when_checkout_is_dirty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.check_output(
                    ["git", "-C", directory, "-c", "core.hooksPath=/dev/null",
                     "-c", "commit.gpgsign=false", *args],
                    stderr=subprocess.DEVNULL, text=True,
                ).strip()

            git("init", "-q")
            original = b"theorem pinned_claim : True := True.intro\n"
            (root / "Original.lean").write_bytes(original)
            (root / "Deleted.lean").write_text("theorem also_pinned : True := True.intro\n")
            # A symlink is not a Lean source blob, even if its name ends in .lean.
            (root / "Alias.lean").symlink_to("Original.lean")
            git("add", ".")
            git("-c", "user.name=NABT test", "-c", "user.email=test@example.invalid",
                "commit", "-qm", "pinned snapshot")
            pin = git("rev-parse", "HEAD")
            (root / "Original.lean").write_text("theorem local_edit : True := True.intro\n")
            (root / "Untracked.lean").write_text("theorem untracked : True := True.intro\n")
            (root / "Deleted.lean").unlink()

            report = catalog_tool.catalog([
                {"repository": "local/test", "commit": pin, "path": directory}
            ])
            files = {entry["path"]: entry for entry in report["repositories"][0]["files"]}
            self.assertEqual(set(files), {"Original.lean", "Deleted.lean"})
            self.assertEqual(report["declaration_count"], 2)
            self.assertEqual(files["Original.lean"]["declarations"][0]["name_as_written"], "pinned_claim")
            self.assertEqual(files["Original.lean"]["file_sha256"], hashlib.sha256(original).hexdigest())
            self.assertIn(pin, files["Original.lean"]["source_url"])
            self.assertFalse(report["runtime_authority"])

            with self.assertRaises(ValueError):
                catalog_tool.catalog([
                    {"repository": "local/test", "commit": "0" * 40, "path": directory}
                ])


if __name__ == "__main__":
    unittest.main()
