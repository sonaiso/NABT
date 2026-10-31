"""New runtime pin must keep all existing completeness/safety gate obligations."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from zipfile import ZipFile

from tools import arabic_completion_v5_gate as old
from tools import arabic_completion_v6_gate as current
from tools.text_evaluation.integrity import verify_code_freeze

ROOT = Path(__file__).resolve().parents[1]

# Include the independent continuation's semantic tamper controls in the
# standard suite as well as its standalone, pre-execution test run.
_REVIEW_TEST = ROOT / 'evidence/arabic_completion_v3/independent_oracle/continuation_v6_review2/test_continuation_v6_review2.py'
_REVIEW_SPEC = importlib.util.spec_from_file_location('completion_v6_review2_tests', _REVIEW_TEST)
_REVIEW_MODULE = importlib.util.module_from_spec(_REVIEW_SPEC)
_REVIEW_SPEC.loader.exec_module(_REVIEW_MODULE)


class ContinuationReview2Tests(_REVIEW_MODULE.ContinuationReview2Tests):
    """Keep semantic controls live; check historical lineage at its own root.

    The archived test is unchanged. A new runtime must not be made to satisfy
    its old dependency freeze by rewriting historical hashes or weakening the
    verifier. The v6 capture contains its complete runtime and checker files.
    """

    def test_new_dependency_lineage_preserves_old_freeze_and_runtime(self):
        bundle = ROOT / 'evidence/arabic_completion_v6/post_base_merge_bundle.zip'
        self.assertEqual(sha256(bundle.read_bytes()).hexdigest(),
                         'eee29217e78af1b5f54a7f7b43554b446a50b205fbfddf1b11d0c1ff38eeb730')
        member = ('evidence/arabic_completion_v6/validation/post_base_merge/oracle/'
                  'strict/result.code.tar.gz')
        with ZipFile(bundle) as saved:
            self.assertEqual(saved.namelist().count(member), 1)
            code = saved.read(member)
        self.assertEqual(sha256(code).hexdigest(),
                         '6a475d9b795c4b4d0cf361830c7c929256392d13d60b681ae0ce43a24d3fef0b')
        with tempfile.TemporaryDirectory() as directory:
            frozen_root = Path(directory)
            with tarfile.open(fileobj=io.BytesIO(code), mode='r:gz') as archive:
                members = archive.getmembers()
                self.assertEqual(len(members), len({item.name for item in members}))
                self.assertTrue(all(item.isfile() and not Path(item.name).is_absolute()
                                    and '..' not in Path(item.name).parts for item in members))
                for item in members:
                    destination = frozen_root / item.name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(item) as contents:
                        destination.write_bytes(contents.read())
            frozen_test = frozen_root / _REVIEW_TEST.relative_to(ROOT)
            self.assertEqual(frozen_test.read_bytes(), _REVIEW_TEST.read_bytes())
            # The capture includes the new dependency freeze. Its parent
            # lineage artifact was retained separately, at this existing pin.
            previous = Path('evidence/arabic_completion_v3/independent_oracle/'
                            'continuation_v6/runner_freeze_v6.json')
            previous_bytes = (ROOT / previous).read_bytes()
            self.assertEqual(sha256(previous_bytes).hexdigest(),
                             'dd9ea0b48e132d55cf2fc8b07a7a66bcc26231af70e9600ec1f4cf209fd56c53')
            (frozen_root / previous).parent.mkdir(parents=True, exist_ok=True)
            (frozen_root / previous).write_bytes(previous_bytes)
            runtime = frozen_root / 'evidence/arabic_completion_v6/code_freeze_v1.json'
            self.assertEqual(sha256(runtime.read_bytes()).hexdigest(),
                             '31bd37d919364742033a08ab4cb557e93b92280539dd7a55364763cae236dfec')
            self.assertEqual(len(verify_code_freeze(runtime, frozen_root)['files']), 99)
            # Fresh interpreter prevents current/archived helper-module mixing.
            script = (
                'import importlib.util,sys\n'
                'spec=importlib.util.spec_from_file_location("archived_lineage",sys.argv[1])\n'
                'module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)\n'
                'case=module.ContinuationReview2Tests('
                '"test_new_dependency_lineage_preserves_old_freeze_and_runtime")\n'
                'case.test_new_dependency_lineage_preserves_old_freeze_and_runtime()\n')
            result = subprocess.run([sys.executable, '-I', '-c', script, str(frozen_test)],
                                    cwd=frozen_root, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_old_freezes_do_not_authorize_the_current_runtime_or_helpers(self):
        with self.assertRaisesRegex(ValueError, 'Runner/dependency changed'):
            _REVIEW_MODULE.P.R.check_runner_freeze(_REVIEW_TEST.parent / 'runner_freeze_v6.json')
        with self.assertRaisesRegex(ValueError, 'Implementation differs from code freeze'):
            verify_code_freeze(ROOT / 'evidence/arabic_completion_v6/code_freeze_v1.json', ROOT)


def fixture(suite):
    return json.loads((ROOT / old.load_policy()["suites"][suite]["strict_measurement"]).read_bytes())


class ClassicalExtensionGateTests(unittest.TestCase):
    def test_new_pin_does_not_authorize_old_runtime_or_fabricated_denominator(self):
        # A real prior fixture remains tied to its prior runtime.
        for suite in ("construction", "discourse"):
            result = fixture(suite)
            self.assertFalse(current.gate_decision(suite, result, True)["gate_pass"])

    def test_only_runtime_identity_changes_in_preserved_residual_policy(self):
        before, after = old.load_policy(), current.load_policy()
        self.assertEqual(before["suites"], after["suites"])
        self.assertEqual(after["runtime_file_count"], 99)
        self.assertNotEqual(before["runtime_freeze_sha256"], after["runtime_freeze_sha256"])

    def test_runtime_pin_cannot_waive_false_acceptance_or_missing_cases(self):
        policy = current.load_policy()
        for suite in ("construction", "discourse"):
            result = fixture(suite)
            # Synthetic gate fixture only; production callers separately verify runtime bytes.
            result["snapshot"].update({k: policy[k] for k in (
                "runtime_freeze_sha256", "runtime_snapshot_sha256", "runtime_file_count")})
            self.assertTrue(current.gate_decision(suite, result, True)["gate_pass"])
            for kind in ("false_accept", "missing_case", "false_total"):
                changed = deepcopy(result)
                if kind == "false_accept":
                    changed["cases"][0]["false_accepts"] = ["invented authority"]
                elif kind == "missing_case":
                    changed["cases"].pop()
                else:
                    changed["passed"] += 1
                self.assertFalse(current.gate_decision(suite, changed, True)["gate_pass"])


if __name__ == "__main__":
    unittest.main()
