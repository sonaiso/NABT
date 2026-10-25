"""Public boundary: unknown is not rejection, and source identity is enforced."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SourceExtensionCliTests(unittest.TestCase):
    def call(self, *args):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        run = subprocess.run([sys.executable, "-m", "nabt", *args], cwd=ROOT,
                             env=env, capture_output=True, text=True)
        self.assertFalse(run.stdout and run.stderr)
        return run.returncode, json.loads(run.stdout or run.stderr)

    def test_onset_projection_preserves_written_source(self):
        a, start = self.call("phonology", "idrib", "--start", "ibtida")
        b, joined = self.call("phonology", "idrib", "--start", "wasl")
        self.assertEqual((a, b), (0, 0))
        self.assertEqual(start["written_form"], joined["written_form"])
        self.assertEqual(start["alternatives"][0]["segments"][:2], ["ʔ", "i"])
        self.assertEqual(start["alternatives"][0]["segments"][2:], joined["alternatives"][0]["segments"])
        self.assertFalse(start["acoustic_validation"])

    def test_unknown_catalog_member_defers(self):
        code, row = self.call("phonology", "not-an-installed-example")
        self.assertEqual(code, 3)
        self.assertEqual(row["status"], "UNKNOWN")

    def test_contradictory_boundaries_are_invalid(self):
        code, row = self.call("phonology", "idrib", "--end", "waqf", "--following-id", "alqawm")
        self.assertEqual(code, 2)
        self.assertEqual(row["code"], "INVALID_PHONOLOGICAL_BOUNDARY")

    def test_counterfeit_dictionary_is_not_an_empty_dictionary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fake.txt"
            path.write_text("### | (كتب)\nInvented content", encoding="utf-8")
            code, row = self.call("source-lexicon", "--source", "maqayis", "--file", str(path), "--root", "كتب")
        self.assertEqual(code, 3)
        self.assertEqual(row["code"], "SOURCE_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
