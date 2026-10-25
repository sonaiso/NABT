"""Independent heading/byte-boundary and source-withdrawal counterexamples."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.source_lexicon import SourceIdentityError, SourceLexicon, _scan

ROOT = Path(__file__).resolve().parents[1]
MAQAYIS = ROOT / "evidence/classical_language/sources/maqayis.txt"
LISAN = ROOT / "artifacts/local/lisan.txt"


class HeadingStructure(unittest.TestCase):
    def test_quadriliteral_quintiliteral_and_irregular_not_erased(self):
        parts = ["### | (دحرج)\n# one\n", "### | (سفرجل)\n# two\n",
                 "### | ([بقم)\n# irregular\n", "### | (تم كتاب الباء)\n# end\n"]
        raw = ("preamble\n" + "".join(parts)).encode()
        rows = _scan(raw, "maqayis")
        self.assertEqual([r.heading for r in rows], ["دحرج", "سفرجل", "[بقم", "تم كتاب الباء"])
        self.assertEqual([r.heading_status for r in rows],
                         ["ROOT_HEADER_CANDIDATE"] * 2 + ["REVIEW_REQUIRED", "SECTION_HEADER"])
        for row, expected in zip(rows, parts):
            self.assertEqual(raw[row.start_byte:row.end_byte], expected.encode())

    def test_hamza_maqsura_vowels_and_duplicates_preserved(self):
        labels = ["أبي", "ابي", "أبى", "أَبِي", "أبي"]
        raw = "".join(f"### | ({label})\n# witness\n" for label in labels).encode()
        self.assertEqual([r.heading for r in _scan(raw, "maqayis")], labels)

    def test_lisan_colon_and_adjacent_section_boundaries(self):
        parts = ["### $ قلم: القلم الذي يكتب به.\n", "### | فصل الكاف\n",
                 "### $ قلم: شاهد آخر\n"]
        raw = ("😀 تمهيد\n" + "".join(parts)).encode()
        rows = _scan(raw, "lisan")
        self.assertEqual([r.heading for r in rows], ["قلم", "فصل الكاف", "قلم"])
        self.assertEqual(rows[1].heading_status, "SECTION_HEADER")
        for row, expected in zip(rows, parts):
            self.assertEqual(raw[row.start_byte:row.end_byte].decode(), expected)

    def test_no_trailing_newline_and_empty_heading_survive(self):
        raw = b"prefix\n### |\n### $ " + "كتب: شاهد".encode()
        rows = _scan(raw, "lisan")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1].end_byte, len(raw))
        self.assertEqual(rows[0].heading_status, "REVIEW_REQUIRED")


class PinnedMaqayis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = SourceLexicon.load("maqayis", MAQAYIS)

    def test_exact_attested_quote_in_returned_original_block(self):
        reply = self.index.lookup_exact("كتب")
        quote = "الكاف والتاء والباء أصل صحيح واحد يدل على جمع شيء إلى شيء."
        self.assertEqual(len(reply["alternatives"]), 1)
        row = reply["alternatives"][0]
        self.assertIn(quote, row["raw_block"])
        self.assertEqual(self.index.raw[3092515:3092619].decode(), quote)
        self.assertEqual(hashlib.sha256(row["raw_block"].encode()).hexdigest(), row["block_sha256"])
        self.assertEqual(row["end_byte"]-row["start_byte"], len(row["raw_block"].encode()))

    def test_whole_source_partition_retains_every_byte(self):
        first = self.index.blocks[0].start_byte
        restored = self.index.raw[:first] + b"".join(
            self.index.raw[r.start_byte:r.end_byte] for r in self.index.blocks)
        self.assertEqual(restored, MAQAYIS.read_bytes())
        self.assertTrue(self.index.inventory()["source_bytes_partitioned"])

    def test_duplicate_and_irregular_headings_remain_reviewable(self):
        self.assertEqual(len(self.index.lookup_exact("حسب")["alternatives"]), 2)
        irregular = self.index.lookup_exact(" [بقم")["alternatives"]
        self.assertEqual(len(irregular), 1)
        self.assertEqual(irregular[0]["heading_status"], "REVIEW_REQUIRED")
        self.assertEqual(self.index.lookup_exact("أثوى")["alternatives"][0]["heading_status"],
                         "ROOT_HEADER_CANDIDATE")
        # The literal root فصل is not the section marker فصل + chapter title.
        self.assertEqual(self.index.lookup_exact("فصل")["alternatives"][0]["heading_status"],
                         "ROOT_HEADER_CANDIDATE")

    def test_lookup_does_not_fold_or_license_meaning(self):
        reply = self.index.lookup_exact("كتب")
        for key in ("reading_licensed", "syntactic_licence", "world_truth_asserted",
                    "all_arabic_senses_enumerated"):
            self.assertFalse(reply[key])
        self.assertEqual(self.index.lookup_exact("كَتَبَ")["status"], "NOT_INDEXED")
        self.assertEqual(self.index.lookup_exact("كتاب")["status"], "NOT_INDEXED")
        self.assertIsNone(self.index.inventory()["linguistic_completeness_denominator"])

    def test_mutation_withdrawal_and_direct_constructor_cannot_claim_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.txt"
            for raw in (b"", self.index.raw[:-1], b"!" + self.index.raw[1:], self.index.raw+b"x"):
                path.write_bytes(raw)
                with self.assertRaises(SourceIdentityError):
                    SourceLexicon.load("maqayis", path)
        with self.assertRaises(SourceIdentityError):
            SourceLexicon("maqayis", b"forged")
        with self.assertRaises(FileNotFoundError):
            SourceLexicon.load("maqayis", MAQAYIS.with_name("missing-source-file"))

    def test_modified_manifest_cannot_grant_source_identity(self):
        from nabt.source_lexicon import source_registry
        policy = source_registry()
        policy["sources"]["maqayis"]["bytes"] = 6
        policy["sources"]["maqayis"]["sha256"] = hashlib.sha256(b"forged").hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"policy.json"
            path.write_text(json.dumps(policy))
            with patch("nabt.source_lexicon._MANIFEST", path), self.assertRaises(SourceIdentityError):
                SourceLexicon("maqayis", b"forged")

    def test_no_cross_source_or_forged_block(self):
        block = self.index.blocks[0]
        for forged in (replace(block, start_byte=0), replace(block, block_sha256="0"*64),
                       replace(block, ordinal=True)):
            with self.assertRaises(ValueError):
                self.index.record(forged)

    def test_invalid_inputs_are_separate_from_not_indexed(self):
        for query in (True, 0, "", "x"*257, "كتب\n"):
            with self.assertRaises(ValueError):
                self.index.lookup_exact(query)
        with self.assertRaises(ValueError):
            SourceLexicon.load(True, MAQAYIS)

    def test_cli_returns_structured_lookup_and_source_unavailable(self):
        command = [sys.executable, str(ROOT/"tools/source_lexicon_index.py")]
        reply = json.loads(subprocess.check_output(command+["--root", "كتب"], text=True))
        self.assertEqual(reply["status"], "FOUND_SOURCE_HEADINGS")
        run = subprocess.run(command+["--file", str(MAQAYIS.with_name("missing-source-file"))],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stdout)["status"], "SOURCE_UNAVAILABLE")


@unittest.skipUnless(LISAN.exists(), "optional full pinned Lisan source not downloaded")
class PinnedLisan(unittest.TestCase):
    def test_lisan_original_definition_duplicate_and_long_root(self):
        index = SourceLexicon.load("lisan", LISAN)
        self.assertIn("الفهم: معرفتك الشيء بالقلب.", index.lookup_exact("فهم")["alternatives"][0]["raw_block"])
        self.assertEqual(len(index.lookup_exact("طأطأ")["alternatives"]), 2)
        self.assertTrue(index.lookup_exact("دحرج")["alternatives"])
        # Mention inside prose is not a missing heading silently invented.
        self.assertEqual(index.lookup_exact("سفرجل")["status"], "NOT_INDEXED")
        self.assertTrue(index.inventory()["source_bytes_partitioned"])


class SeparateContextWitnesses(unittest.TestCase):
    def test_contexts_replay_separately_from_dictionary_identity(self):
        path = ROOT/"src/nabt/data/source_evidence/source_lexicon_contexts_v1.json"
        data = json.loads(path.read_text())
        for item in data["contexts"]:
            raw = (ROOT/data["sources"][item["source_id"]]["local_file"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), data["sources"][item["source_id"]]["sha256"])
            span = raw[item["start_byte"]:item["end_byte"]]
            self.assertEqual(span.decode(), item["raw_text"])
            self.assertEqual(hashlib.sha256(span).hexdigest(), item["span_sha256"])
            self.assertFalse(item["world_grounded"])
            self.assertFalse(item["full_vocalization_invented"])
        self.assertEqual(data["lexical_registry"], "source_lexicon_v1.json")
        self.assertFalse(data["automatic_lexical_context_join"])


if __name__ == "__main__":
    unittest.main()
