"""A failed audit must not leave a stale successful evidence receipt."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CompletenessReviewReceiptTests(unittest.TestCase):
    def test_missing_checker_replaces_prior_success_with_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'validation.json'
            output.write_text('{"kernel_checked": true}', encoding='utf-8')
            output.with_suffix('.log').write_text('old successful run', encoding='utf-8')
            run = subprocess.run(
                [sys.executable, str(ROOT / 'tools/check_completeness_review.py'),
                 '--lake', str(Path(directory) / 'no-such-lake'), '--output', str(output)],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(run.returncode, 1, run.stderr)
            receipt = json.loads(output.read_text(encoding='utf-8'))
            self.assertIs(receipt['kernel_checked'], False)
            self.assertEqual(receipt['countermodels_checked'], 0)
            self.assertIs(receipt['whole_arabic_completeness_established'], False)
            self.assertIn('no-such-lake', receipt['error'])
            self.assertIn('no-such-lake', output.with_suffix('.log').read_text(encoding='utf-8'))
            self.assertNotIn('old successful run', output.with_suffix('.log').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
