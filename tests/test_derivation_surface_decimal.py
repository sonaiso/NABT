"""Permanent regression for the independently retained decimal-input failure."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'evidence/derivation_surface_v1/review/decimal_input/applications_5000_digit.json'
# This input and its failed CLI/API comparison were committed at a694860 before
# the parse_int correction. Do not construct acceptance data from the parser.
INPUT_SHA256 = 'd7312a035c33a328033f0a3540689aa7a4f0731b0f7592087dc7e0801179ed5f'


class DerivationSurfaceDecimalInputReview(unittest.TestCase):
    def test_decimal_conversion_limit_is_resource_before_missing_source(self):
        raw = INPUT.read_bytes()
        self.assertEqual(len(raw), 5222)
        self.assertEqual(sha256(raw).hexdigest(), INPUT_SHA256)
        with tempfile.TemporaryDirectory(prefix='nabt-decimal-regression-') as directory:
            source = Path(directory) / 'source-does-not-exist.txt'
            self.assertFalse(source.exists())
            run = subprocess.run(
                [sys.executable, '-X', 'int_max_str_digits=4300', '-B', '-m',
                 'tools.recursive_bridge', 'read-applications', str(source),
                 '--applications', str(INPUT)],
                cwd=ROOT, capture_output=True, check=False, timeout=15)
            self.assertFalse(source.exists())
        self.assertEqual(run.returncode, 3, run.stdout.decode('utf-8', 'replace'))
        self.assertEqual(run.stderr, b'')
        result = json.loads(run.stdout)
        self.assertEqual((result['status'], result['code']), ('DEFER', 'RESOURCE_LIMIT'))


if __name__ == '__main__':
    unittest.main()
