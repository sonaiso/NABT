from io import BytesIO
from pathlib import Path
import hashlib
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from tools import bootstrap_lean as b

class BootstrapTests(unittest.TestCase):
    def test_504_retries_and_verifies_before_atomic_install(self):
        data = b"verified fixture"
        with tempfile.TemporaryDirectory() as d, patch.object(b, "SHA256", hashlib.sha256(data).hexdigest()), patch.object(b.time, "sleep") as wait:
            p = Path(d)/"tool.tar.zst"
            with patch.object(b.urllib.request, "urlopen", side_effect=[HTTPError(b.URL,504,"timeout",{},None), BytesIO(data)]) as fetch:
                b.download_verified(p)
            self.assertEqual(p.read_bytes(), data);self.assertEqual(fetch.call_count,2);wait.assert_called_once_with(1)
            self.assertFalse(p.with_suffix(".zst.partial").exists())

    def test_digest_failure_is_not_retried_or_installed(self):
        with tempfile.TemporaryDirectory() as d, patch.object(b.urllib.request,"urlopen",return_value=BytesIO(b"corrupt")) as fetch:
            p=Path(d)/"tool.tar.zst"
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                b.download_verified(p)
            self.assertEqual(fetch.call_count,1);self.assertFalse(p.exists());self.assertFalse(p.with_suffix(".zst.partial").exists())

    def test_permanent_http_failure_not_retried(self):
        with tempfile.TemporaryDirectory() as d, patch.object(b.urllib.request,"urlopen",side_effect=HTTPError(b.URL,404,"missing",{},None)) as fetch:
            with self.assertRaises(HTTPError):b.download_verified(Path(d)/"tool.tar.zst")
            self.assertEqual(fetch.call_count,1)

    def test_transient_retry_budget_is_finite(self):
        with tempfile.TemporaryDirectory() as d, patch.object(b.time,"sleep"), patch.object(b.urllib.request,"urlopen",side_effect=HTTPError(b.URL,504,"timeout",{},None)) as fetch:
            with self.assertRaises(HTTPError):b.download_verified(Path(d)/"tool.tar.zst",attempts=3)
            self.assertEqual(fetch.call_count,3)
