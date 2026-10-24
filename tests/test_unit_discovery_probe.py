"""Transport regressions for the built Lean JSONL probe, not Arabic evaluation.

Run after ``lake build unitDiscoveryProbe``. CI can set
NABT_UNIT_DISCOVERY_PROBE to make a missing executable a hard failure; ordinary
Python-only discovery skips this integration class if Lean has not been built.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def raw_root(first_root: str, first_surface: str) -> bytes:
    """Insert exact JSON string spelling, including deliberately invalid escapes."""
    return (
        '{"op":"root_replay","arity":3,"root":["' + first_root + '","a","b"],'
        '"pattern":[{"slot":0},{"slot":1},{"slot":2}],"surface":"'
        + first_surface + 'ab"}\n'
    ).encode("utf-8")


class UnitDiscoveryProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declared = os.environ.get("NABT_UNIT_DISCOVERY_PROBE")
        cls.probe = Path(declared) if declared else ROOT / "formal/.lake/build/bin/unitDiscoveryProbe"
        if not cls.probe.is_file():
            if declared:
                raise RuntimeError("Declared Lean probe executable is missing: " + str(cls.probe))
            raise unittest.SkipTest("Build unitDiscoveryProbe before running Lean transport integration tests")

    def query(self, payload: bytes):
        run = subprocess.run([str(self.probe)], input=payload, capture_output=True,
                             check=True, timeout=10)
        self.assertEqual(run.stderr, b"")
        replies = [json.loads(line) for line in run.stdout.splitlines()]
        for reply in replies:
            self.assertEqual(reply["law_id"], "nabt.unit-discovery.v1")
            self.assertEqual(reply["scope"], "conditional_on_supplied_interpretations")
            self.assertIs(reply["conditional"], True)
        return replies

    def invalid_unicode(self, payload: bytes):
        replies = self.query(payload)
        self.assertTrue(replies)
        for reply in replies:
            self.assertEqual(reply["status"], "ERROR")
            self.assertEqual(reply["error"], "INVALID_INPUT")
            self.assertNotIn("shape_matches", reply)

    def test_distinct_invalid_surrogates_cannot_collapse_into_a_match(self):
        self.invalid_unicode(raw_root(r"\ud800", r"\ud801"))

    def test_lone_high_and_low_surrogates_are_rejected(self):
        escapes = [r"\ud800", r"\ud801", r"\udbff", r"\udc00", r"\udfff", r"\uDBFF"]
        self.invalid_unicode(b"".join(raw_root(value, value) for value in escapes))

    def test_high_surrogate_needs_an_immediate_low_surrogate(self):
        invalid = [r"\ud800\u0041", r"\ud800\ud800", r"\ud800x\udc00", r"\udc00\ud800"]
        self.invalid_unicode(b"".join(raw_root(value, value) for value in invalid))

    def test_correct_surrogate_pair_matches_its_actual_scalar(self):
        reply, = self.query(raw_root(r"\ud83d\ude00", "😀"))
        self.assertEqual(reply["status"], "OK")
        self.assertIs(reply["shape_matches"], True)
        self.assertEqual(reply["generated_surface"], "😀ab")
        self.assertEqual(reply["recovered_root"], ["😀", "a", "b"])

    def test_explicit_replacement_character_is_not_rejected(self):
        for payload in (raw_root("�", "�"), raw_root(r"\ufffd", "�")):
            with self.subTest(payload=payload):
                reply, = self.query(payload)
                self.assertEqual(reply["status"], "OK")
                self.assertIs(reply["shape_matches"], True)
                self.assertEqual(reply["recovered_root"], ["�", "a", "b"])

    def test_literal_backslash_u_sequences_are_preserved(self):
        atoms = [r"\ud800", r"\udc00"]
        payload = (json.dumps({"op": "partitions", "atoms": atoms}) + "\n").encode()
        reply, = self.query(payload)
        self.assertEqual(reply["status"], "OK")
        self.assertEqual(reply["count"], 2)
        for partition in reply["parts"]:
            self.assertEqual([atom for part in partition for atom in part], atoms)

    def test_invalid_line_does_not_poison_the_following_request(self):
        replies = self.query(raw_root(r"\ud800", r"\ud801") +
                             b'{"op":"partitions","atoms":[]}\n')
        self.assertEqual(len(replies), 2)
        self.assertEqual(replies[0]["error"], "INVALID_INPUT")
        self.assertEqual(replies[1]["status"], "OK")
        self.assertEqual(replies[1]["position_groups"], [[]])


if __name__ == "__main__":
    unittest.main()
