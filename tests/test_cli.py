import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nabt.alphabet import MAX_CELLS
from nabt.cli import MAX_JSON_BYTES, main
from nabt.machine import MAX_WEIGHT


class CliTests(unittest.TestCase):
    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(arguments))
        out, err = stdout.getvalue(), stderr.getvalue()
        self.assertFalse(out and err, "A command must have one result channel")
        return code, json.loads(out) if out else None, json.loads(err) if err else None

    def test_encode_decode_full_codec_boundary_and_entry_point(self):
        code, encoded, err = self.invoke("encode", "كَتَبَ")
        self.assertEqual((code, err), (0, None))
        self.assertEqual(encoded["numeric_code"], "1144809")
        code, decoded, err = self.invoke("decode", encoded["numeric_code"])
        self.assertEqual((code, err), (0, None))
        self.assertEqual(decoded["text"], "كَتَبَ")
        self.assertEqual(decoded["scope"], "ENCODING_ONLY")

        # This exceeds Python's default decimal rendering limit; hex must retain
        # every cell rather than disabling limits or truncating the number.
        text = "بَ" * MAX_CELLS
        code, encoded, err = self.invoke("encode", text)
        self.assertEqual((code, err), (0, None))
        self.assertIsNone(encoded["numeric_code"])
        code, decoded, err = self.invoke("decode", encoded["numeric_code_hex"])
        self.assertEqual((code, err), (0, None))
        self.assertEqual(decoded["text"], text)
        self.assertEqual(decoded["cell_length"], MAX_CELLS)
        self.assertEqual(decoded["cells"], [4] * MAX_CELLS)

        completed = subprocess.run([sys.executable, "-m", "nabt", "encode", "كَتَبَ"],
                                   text=True, capture_output=True, check=False)
        self.assertEqual((completed.returncode, completed.stderr), (0, ""))
        self.assertEqual(json.loads(completed.stdout)["numeric_code"], "1144809")

    def test_source_and_generated_certificate_workflows(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "certificate.json"
            for args, status in [(('certify', 'كَتَبَ'), 'LICENSED_SHAPE'),
                                 (('generate', '--weight', '4', '--rank', '0'), 'GENERATED_BY_LAW')]:
                code, certificate, err = self.invoke(*args)
                self.assertEqual((code, err), (0, None))
                self.assertEqual(certificate["status"], status)
                path.write_text(json.dumps(certificate, ensure_ascii=False), encoding="utf-8")
                code, report, err = self.invoke("verify", str(path))
                self.assertEqual((code, report["valid"], err), (0, True, None))
                certificate["rank"] = str(int(certificate["rank"]) + 1)
                path.write_text(json.dumps(certificate), encoding="utf-8")
                code, report, err = self.invoke("verify", str(path))
                self.assertEqual((code, report["valid"], err), (2, False, None))

    def test_certificate_json_boundary_rejects_ambiguity_and_malformed_bytes(self):
        malformed = [(b'{"rank":"0","rank":"1"}', "DUPLICATE_JSON_KEY"),
                     (b'{"nested":{"x":0,"x":1}}', "DUPLICATE_JSON_KEY"),
                     (b'{"rank":NaN}', "INVALID_JSON"),
                     (b'{"rank":Infinity}', "INVALID_JSON"),
                     (b'{"rank":', "INVALID_JSON"),
                     (b'"\xed\xa0\x80"', "INVALID_JSON")]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "certificate.json"
            for raw, expected in malformed:
                with self.subTest(expected=expected, size=len(raw)):
                    path.write_bytes(raw)
                    code, out, err = self.invoke("verify", str(path))
                    self.assertEqual((code, out, err["status"], err["code"]),
                                     (2, None, "REJECT", expected))

    def test_resource_exhaustion_and_missing_file_are_deferred(self):
        for args in [("count", "--weight", str(MAX_WEIGHT + 1)),
                     ("encode", "بَ" * (MAX_CELLS + 1)),
                     ("decode", "1" * 4001),
                     ("decode", "0x1" + "0" * 8192)]:
            with self.subTest(command=args[0], input_size=len(args[-1])):
                code, out, err = self.invoke(*args)
                self.assertEqual((code, out, err["status"], err["code"]),
                                 (3, None, "DEFER", "RESOURCE_LIMIT"))
                self.assertLess(len(err["message"]), 300)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "certificate.json"
            code, out, err = self.invoke("verify", str(path))
            self.assertEqual((code, out, err["status"], err["code"]),
                             (3, None, "DEFER", "IO_ERROR"))
            path.write_bytes(b" " * (MAX_JSON_BYTES + 1))
            code, out, err = self.invoke("verify", str(path))
            self.assertEqual((code, out, err["status"], err["code"]),
                             (3, None, "DEFER", "RESOURCE_LIMIT"))

    def test_rejected_shape_and_incomplete_representation_are_distinct(self):
        code, result, err = self.invoke("analyse", "كُاْ")
        self.assertEqual((code, result["licensed"], err), (2, False, None))
        for word, reason in [("كتب", "MISSING_VOCALIZATION"),
                             ("كَّ", "UNSUPPORTED_ORTHOGRAPHY")]:
            code, out, err = self.invoke("analyse", word)
            self.assertEqual((code, out, err["status"], err["code"]),
                             (3, None, "DEFER", reason))
        code, out, err = self.invoke("analyse", "كَُ")
        self.assertEqual((code, out, err["status"], err["code"]),
                         (2, None, "REJECT", "CONFLICTING_MARKS"))

    def test_invalid_mode_number_and_rank_do_not_produce_a_result(self):
        for args in [("count", "--weight", "1", "--mode", "unknown"),
                     ("decode", "-1"), ("decode", "01"),
                     ("generate", "--weight", "1", "--rank", "168")]:
            with self.subTest(arguments=args):
                code, out, err = self.invoke(*args)
                self.assertEqual((code, out, err["status"]), (2, None, "REJECT"))


if __name__ == "__main__":
    unittest.main()
