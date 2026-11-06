"""The operational timeout migration cannot alter a frozen oracle command."""
from hashlib import sha256
import json
import unittest

from tools import interpretive_links_regression as runner


class RuntimeBudgetMigrationTests(unittest.TestCase):
    def test_actual_workflow_reconstructs_the_prior_frozen_bytes(self):
        prior = json.loads(runner.pinned(runner.PRIOR_DEPENDENCIES, runner.PRIOR_DEPENDENCIES_SHA))
        row = next(r for r in prior['files'] if r['path'] == '.github/workflows/ci.yml')
        runner.check_runtime_budget((runner.ROOT / row['path']).read_bytes(), row['sha256'])

    def test_other_budget_and_command_changes_are_rejected(self):
        old = b'jobs:\n  runtime:\n    runs-on: ubuntu-24.04\n    timeout-minutes: 20\n    run: check-all\n'
        current = old.replace(b'minutes: 20', b'minutes: 40')
        expected = sha256(old).hexdigest()
        runner.check_runtime_budget(current, expected)
        for bad in (old, current.replace(b'40', b'60'), current + current,
                    current.replace(b'check-all', b'check-subset'), current + b'continue-on-error: true\n'):
            with self.subTest(raw=bad), self.assertRaisesRegex(ValueError, 'only the runtime timeout'):
                runner.check_runtime_budget(bad, expected)

    def test_current_inventory_pins_both_the_prior_freeze_and_new_checks(self):
        snapshot = runner.check_dependencies()
        paths = {r['path'] for r in snapshot['files']}
        self.assertIn(str(runner.PRIOR_DEPENDENCIES.relative_to(runner.ROOT)), paths)
        self.assertIn('tests/test_ci_runtime_budget.py', paths)


if __name__ == '__main__':
    unittest.main()
