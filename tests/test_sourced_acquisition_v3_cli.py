"""CLI exit codes must distinguish failed proof replay from ordinary deferral."""
import copy
from contextlib import redirect_stdout
from io import StringIO
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import connected_acquisition_v3 as connected
from tools import sourced_acquisition_cli as cli


class CommandExitStatus(unittest.TestCase):
    def test_failed_shape_replay_is_a_process_failure_in_both_display_modes(self):
        for onset in ('word_initial', 'connected'):
            proposal = connected.propose_acquisition('قمتُ', onset=onset)
            self.assertEqual(proposal['status'], 'ACQUIRED')
            proposal['verified'] = True
            for summary in (False, True):
                argv = ['--task', 'pronunciation', '--text', 'قمتُ', '--onset', onset]
                if summary:
                    argv.append('--summary')
                output = StringIO()
                with self.subTest(onset=onset, summary=summary), \
                        patch.object(connected, 'acquire', return_value=copy.deepcopy(proposal)), \
                        patch.object(connected, 'verify_certificate',
                                     return_value=SimpleNamespace(valid=False)) as replay, \
                        redirect_stdout(output):
                    status = cli.main(argv)
                    replay.assert_called_once()
                    report = json.loads(output.getvalue())
                    self.assertEqual(report['status'], 'SHAPE_CHECK_FAILED')
                    self.assertFalse(report['shape_verified'])
                    self.assertEqual(status, 2)

    def test_ordinary_deferred_reading_remains_a_successful_execution(self):
        proposal = connected.propose_acquisition('قمت')
        self.assertEqual(proposal['status'], 'DEFER')
        proposal['verified'] = False
        for summary in (False, True):
            argv = ['--task', 'pronunciation', '--text', 'قمت']
            if summary:
                argv.append('--summary')
            output = StringIO()
            with self.subTest(summary=summary), \
                    patch.object(connected, 'acquire', return_value=copy.deepcopy(proposal)), \
                    patch.object(connected, 'verify_certificate') as replay, redirect_stdout(output):
                status = cli.main(argv)
                replay.assert_not_called()
                self.assertEqual(json.loads(output.getvalue())['status'], 'DEFER')
                self.assertEqual(status, 0)


if __name__ == '__main__':
    unittest.main()
