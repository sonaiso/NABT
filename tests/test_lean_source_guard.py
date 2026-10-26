"""Source-guard regressions: character syntax must not mask proof bypasses."""
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from tools import check_integrity


class LeanSourceGuardTests(unittest.TestCase):
    def assert_positions_preserved(self, source, code):
        self.assertEqual(len(source), len(code))
        self.assertEqual([i for i, c in enumerate(source) if c == "\n"],
                         [i for i, c in enumerate(code) if c == "\n"])

    def test_double_quote_character_does_not_open_string(self):
        source = "def quote : Char := '\"'\ntheorem blocked : False := by sorry\n"
        code = check_integrity.lean_code_without_comments_or_strings(source)
        self.assert_positions_preserved(source, code)
        self.assertNotIn('"', code)
        self.assertEqual(code.index("sorry"), source.index("sorry"))

    def test_valid_single_scalar_escapes_remain_bounded(self):
        literals = ["'ع'", "'a'", r"'\n'", r"'\r'", r"'\t'", r"'\\'",
                    r"'\''", r"'\"'", r"'\x22'", r"'\u0022'"]
        for literal in literals:
            with self.subTest(literal=literal):
                source = f"def value : Char := {literal}\naxiom forbidden : False\n"
                code = check_integrity.lean_code_without_comments_or_strings(source)
                self.assert_positions_preserved(source, code)
                self.assertEqual(code.index("axiom"), source.index("axiom"))
                self.assertEqual(code[source.index(literal):source.index(literal) + len(literal)],
                                 " " * len(literal))

    def test_primed_identifiers_and_invalid_multichar_literals_do_not_hide_code(self):
        source = "def f'a' := 1\ndef f' := 2\n'sorry'\n'admit'\n'native_decide'\n"
        code = check_integrity.lean_code_without_comments_or_strings(source)
        self.assertEqual(code, source)

    def test_comments_and_strings_remain_ignored_but_following_code_visible(self):
        source = ('/- sorry /- axiom -/ unsafe -/\n'
                  'def message := "sorry axiom unsafe \\\" admit"\n'
                  'def quote : Char := \'"\' -- native_decide\n'
                  'unsafe def forbidden := 0\n')
        code = check_integrity.lean_code_without_comments_or_strings(source)
        self.assert_positions_preserved(source, code)
        self.assertEqual(re.findall(r"\b(?:sorry|axiom|unsafe|admit|native_decide)\b", code),
                         ["unsafe"])

    def test_every_forbidden_token_is_detected_after_character_quotes(self):
        for token in ("sorry", "sorryAx", "admit", "axiom", "native_decide", "unsafe"):
            for count in (1, 2, 3):
                with self.subTest(token=token, quote_count=count):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        (root / "formal").mkdir()
                        source = "\n".join(f"def q{i} : Char := '\"'" for i in range(count))
                        (root / "formal/Probe.lean").write_text(source + f"\n{token}\n")
                        with patch.object(check_integrity, "ROOT", root):
                            with self.assertRaisesRegex(ValueError, f"Forbidden proof-source tokens: .*{token}"):
                                check_integrity.inspect_lean_sources()

    def test_unterminated_comments_and_strings_still_fail_closed(self):
        for source in ('def q := \'"\'\n"unterminated', '/- unclosed',
                       '/- outer /- inner -/', '"trailing\\'):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "Unterminated Lean comment/string"):
                    check_integrity.lean_code_without_comments_or_strings(source)

    def test_current_shared_transport_is_scanned_without_omission(self):
        source = (check_integrity.ROOT / "formal/ProbeJson.lean").read_text()
        code = check_integrity.lean_code_without_comments_or_strings(source)
        self.assert_positions_preserved(source, code)
        self.assertIn("def uniqueObjectKeys", code)
        self.assertIn("def preflight", code)
        self.assertGreater(check_integrity.inspect_lean_sources(), 0)


if __name__ == "__main__":
    unittest.main()
