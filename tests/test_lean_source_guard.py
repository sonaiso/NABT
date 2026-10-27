"""The proof-token guard must not confuse Char quotes with string boundaries."""
import importlib.util
from pathlib import Path
import re
import unittest

spec = importlib.util.spec_from_file_location("nabt_source_guard", Path(__file__).resolve().parents[1] / "tools/check_integrity.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class LeanSourceGuardTests(unittest.TestCase):
    def test_char_quotes_do_not_hide_following_proof_tokens(self):
        for literal in ("'\"'", "'ب'", r"'\''", r"'\\'", r"'\x00'", r"'\u0061'"):
            source = "def c := " + literal + "\ntheorem blocked : True := by sorry\n"
            cleaned = guard.lean_code_without_comments_or_strings(source)
            self.assertEqual(len(cleaned), len(source))
            self.assertEqual(cleaned.count("\n"), source.count("\n"))
            self.assertRegex(cleaned, r"\bsorry\b")

    def test_char_like_text_in_comments_and_strings_stays_ignored(self):
        source = '''/- outer '"' /- sorry -/ -/\ndef s := "sorry \\\""\ndef c := '"' -- admit\ntheorem ok : True := by trivial\n'''
        cleaned = guard.lean_code_without_comments_or_strings(source)
        self.assertIsNone(re.search(r"\b(?:sorry|admit)\b", cleaned))
        self.assertIn("theorem ok", cleaned)

    def test_identifier_apostrophe_and_malformed_multichar_literal_stay_visible(self):
        source = "def foo' := 1\ndef sorry' := foo'\ndef bad := 'sorry'\n"
        cleaned = guard.lean_code_without_comments_or_strings(source)
        self.assertIn("foo'", cleaned)
        self.assertEqual(len(re.findall(r"\bsorry\b", cleaned)), 2)

    def test_unterminated_real_comment_or_string_still_fails(self):
        for source in ('def c := \'"\'\n/- unfinished', 'def c := \'"\'\n"unfinished'):
            with self.assertRaises(ValueError):
                guard.lean_code_without_comments_or_strings(source)

    def test_all_current_lean_sources_remain_guarded(self):
        self.assertGreater(guard.inspect_lean_sources(), 0)
