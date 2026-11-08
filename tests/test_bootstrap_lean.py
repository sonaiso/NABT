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
            self.assertEqual(fetch.call_args_list[0].args[0].full_url,b.URL)
            self.assertEqual(fetch.call_args_list[1].args[0].full_url,b.ASSET_URL)
            self.assertEqual(fetch.call_args_list[1].args[0].get_header("Accept"),"application/octet-stream")
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

    def test_api_token_only_on_exact_asset_url_and_removed_on_redirect(self):
        with patch.dict(b.os.environ,{"GITHUB_TOKEN":"synthetic-test-token"}), patch.object(b.urllib.request,"build_opener") as build, patch.object(b.urllib.request,"urlopen") as direct:
            b.open_download(b.URL)
            self.assertIsNone(direct.call_args.args[0].get_header("Authorization"))
            b.open_download(b.ASSET_URL)
            request=build.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header("Authorization"),"Bearer synthetic-test-token")
            moved=b.AssetRedirect().redirect_request(request,None,302,"found",{},"https://release-assets.githubusercontent.com/asset")
            self.assertIsNone(moved.get_header("Authorization"))

    def test_every_installer_step_has_scoped_ci_token(self):
        root=Path(__file__).resolve().parents[1]
        for p in (root/".github/workflows").glob("*.yml"):
            parts=p.read_text().split("      - ")
            for step in parts:
                if "python tools/bootstrap_lean.py" in step:
                    self.assertIn("          GITHUB_TOKEN: ${{ github.token }}",step,str(p))
