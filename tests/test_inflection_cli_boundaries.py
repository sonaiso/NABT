"""Authored CLI input-boundary checks, independent of the review corpus."""

import contextlib
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt.cli import main
from nabt.inflection_reader import MAX_REPORT_BYTES, read_inflection
from nabt.word_reader import MAX_SOURCE_BYTES


TRAINING = (
    b"LOCATION\tFORM\tTAG\tFEATURES\n"
    b"(1:1:1:1)\tkitAbN\tN\tSTEM|POS:N|LEM:kitAb|ROOT:ktb|MS\n"
)


class InflectionCliBoundaryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "source.txt"
        self.source.write_text("رَجُلٌ", encoding="utf-8")
        self.report = self.directory / "report.json"
        self.report.write_text(json.dumps(read_inflection("رَجُلٌ"), ensure_ascii=False), encoding="utf-8")

    def invoke(self, *arguments):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main([str(a) for a in arguments])
        self.assertFalse(out.getvalue() and err.getvalue(), "Use one structured result channel")
        return code, json.loads(out.getvalue()) if out.getvalue() else None, \
            json.loads(err.getvalue()) if err.getvalue() else None

    def commands_with_corpus(self, path):
        return (("audit-corpus", path, "--format", "qac"),
                ("learn-qac-lexicon", path),
                ("read-inflection", self.source, "--qac", path),
                ("verify-inflection", self.report, "--source", self.source, "--qac", path))

    def test_malformed_gzip_has_structured_rejection_across_corpus_commands(self):
        full = gzip.compress(TRAINING, mtime=0)
        crc = bytearray(full)
        crc[-8] ^= 1
        malformed = {
            "truncated_trailer": full[:-4],
            "invalid_deflate_block": bytes.fromhex("1f8b0800000000000003") + b"\x07" + b"\0" * 8,
            "bad_header": b"not-gzip",
            "bad_crc": bytes(crc),
        }
        for name, raw in malformed.items():
            path = self.directory / (name + ".gz")
            path.write_bytes(raw)
            for arguments in self.commands_with_corpus(path):
                with self.subTest(failure=name, command=arguments[0]):
                    code, out, err = self.invoke(*arguments)
                    self.assertEqual((code, out, err["status"], err["code"]),
                                     (2, None, "REJECT", "INVALID_CORPUS_COMPRESSION"))

    def test_valid_gzip_and_plain_corpus_have_the_same_decoded_evidence(self):
        plain, compressed = self.directory / "corpus.tsv", self.directory / "corpus.tsv.gz"
        plain.write_bytes(TRAINING)
        compressed.write_bytes(gzip.compress(TRAINING, mtime=0))
        for command, options in (("audit-corpus", ("--format", "qac")), ("learn-qac-lexicon", ())):
            with self.subTest(command=command):
                first = self.invoke(command, plain, *options)
                self.assertEqual(first[0], 0)
                self.assertIsNone(first[2])
                self.assertEqual(first, self.invoke(command, compressed, *options))

    def test_missing_corpus_keeps_io_defer_including_gzip_paths(self):
        for suffix in (".tsv", ".gz"):
            path = self.directory / ("missing" + suffix)
            for arguments in self.commands_with_corpus(path):
                with self.subTest(suffix=suffix, command=arguments[0]):
                    code, out, err = self.invoke(*arguments)
                    self.assertEqual((code, out, err["status"], err["code"]),
                                     (3, None, "DEFER", "IO_ERROR"))

    def test_oversized_text_reads_at_most_one_extra_byte_and_skips_all_analysis(self):
        # Fewer than 8192 characters can already exceed the UTF-8 byte budget.
        payload = "ب".encode("utf-8") * (MAX_SOURCE_BYTES // 2 + 1)
        original_open = Path.open
        for verifying in (False, True):
            reads = []

            class ObservedStream(io.BytesIO):
                def read(self, size=-1):
                    reads.append(size)
                    return super().read(size)

            def opening(path, *args, **kwargs):
                return ObservedStream(payload) if path == self.source else original_open(path, *args, **kwargs)

            arguments = ("verify-inflection", self.report, "--source", self.source) if verifying else \
                ("read-inflection", self.source)
            with self.subTest(verifying=verifying), patch.object(Path, "open", opening), \
                    patch("nabt.corpus_evidence.learn_qac_lexicon") as learner, \
                    patch("nabt.inflection_reader.read_inflection") as reader, \
                    patch("nabt.inflection_reader.verify_inflection") as verifier:
                code, out, err = self.invoke(*arguments, "--qac", self.directory / "unread-corpus.gz")
                self.assertEqual((code, out, err["status"], err["code"]),
                                 (3, None, "DEFER", "RESOURCE_LIMIT"))
                self.assertEqual(err["details"]["maximum_bytes"], MAX_SOURCE_BYTES)
                self.assertEqual(reads, [MAX_SOURCE_BYTES + 1])
                learner.assert_not_called()
                reader.assert_not_called()
                verifier.assert_not_called()

    def test_exact_source_byte_limit_remains_readable_and_replayable(self):
        word = "رَجُلٌ".encode("utf-8")
        raw = b" " * (MAX_SOURCE_BYTES - len(word)) + word
        self.source.write_bytes(raw)
        code, report, err = self.invoke("read-inflection", self.source)
        self.assertEqual((code, err, report["status"]), (3, None, "DEFER"))
        self.assertEqual(report["raw_text"].encode("utf-8"), raw)
        self.report.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
        code, checked, err = self.invoke("verify-inflection", self.report, "--source", self.source)
        self.assertEqual((code, err, checked["valid"], checked["status"]), (0, None, True, "VERIFIED"))

    def test_report_then_source_diagnostics_precede_optional_corpus_compilation(self):
        absent_source, absent_corpus = self.directory / "missing-source", self.directory / "missing-corpus.gz"
        self.report.write_bytes(b"{")
        code, out, err = self.invoke("verify-inflection", self.report, "--source", absent_source,
                                     "--qac", absent_corpus)
        self.assertEqual((code, out, err["code"]), (2, None, "INVALID_JSON"))
        self.report.write_bytes(b"{}")
        code, out, err = self.invoke("verify-inflection", self.report, "--source", absent_source,
                                     "--qac", absent_corpus)
        self.assertEqual((code, out, err["status"], err["code"]), (3, None, "DEFER", "IO_ERROR"))
        self.assertIn(str(absent_source), err["message"])
        self.assertNotIn(str(absent_corpus), err["message"])

    def test_report_budget_and_source_mismatch_diagnostics_remain_distinct(self):
        self.report.write_bytes(b" " * (MAX_REPORT_BYTES + 1))
        code, out, err = self.invoke("verify-inflection", self.report, "--source", self.source)
        self.assertEqual((code, out, err["status"], err["code"]), (3, None, "DEFER", "RESOURCE_LIMIT"))
        self.assertEqual(err["details"]["maximum_bytes"], MAX_REPORT_BYTES)
        self.report.write_text(json.dumps(read_inflection("كَتَبَ"), ensure_ascii=False), encoding="utf-8")
        code, checked, err = self.invoke("verify-inflection", self.report, "--source", self.source)
        self.assertEqual((code, err, checked["valid"], checked["status"], checked["code"]),
                         (2, None, False, "REJECT", "INVALID_INFLECTION_REPORT"))

    def test_exclusions_still_require_a_corpus_before_files_are_read(self):
        code, out, err = self.invoke("verify-inflection", self.directory / "missing-report",
                                     "--source", self.directory / "missing-source", "--exclude-verse", "1:1")
        self.assertEqual((code, out, err["status"], err["code"]),
                         (2, None, "REJECT", "INVALID_CORPUS_EXCLUSIONS"))


if __name__ == "__main__":
    unittest.main()
