"""A successful partial proof must not become CLI language acceptance."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from tools.linguistic_truth import __main__ as cli


class CertifiedLinguisticCliTests(unittest.TestCase):
    def run_cli(self, result):
        output = io.StringIO()
        with patch("sys.argv", ["linguistic_truth", "certify", "--text", "عَيْنَ",
                                "--profile", "linguistic", "--context", "caller-context"]), \
                patch("tools.linguistic_truth.certified.acquire_certified", return_value=result) as acquire, \
                contextlib.redirect_stdout(output):
            code = cli.main()
        return code, json.loads(output.getvalue()), acquire

    def test_partial_claim_has_nonzero_exit_even_with_native_check(self):
        result = {"status": "DEFER", "strict_language_accepted": False,
                  "candidate_set_checked": True, "native_checked": True}
        code, emitted, acquire = self.run_cli(result)
        self.assertEqual(code, 3)
        self.assertEqual(emitted, result)
        self.assertEqual(acquire.call_args.args, ("عَيْنَ",))
        self.assertEqual(acquire.call_args.kwargs["context"], "caller-context")

    def test_missing_native_checker_is_an_error(self):
        code, _, _ = self.run_cli({"status": "VERIFICATION_UNAVAILABLE",
                                  "strict_language_accepted": False})
        self.assertEqual(code, 2)

    def test_resource_exhaustion_never_counts_as_complete(self):
        code, _, _ = self.run_cli({"status": "RESOURCE_EXHAUSTED",
                                  "strict_language_accepted": False})
        self.assertEqual(code, 3)

    def test_truthy_non_boolean_acceptance_is_not_success(self):
        for value in (1, "true", [True]):
            with self.subTest(value=value):
                code, _, _ = self.run_cli({"status": "DEFER",
                                          "strict_language_accepted": value})
                self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
