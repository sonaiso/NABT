"""Source metadata survives a canonical owner binding; no mocks confer native proof."""
import os
import unittest
from unittest.mock import patch

from tools import explainable_pilot as pilot
from tools.grammar_catalog import opencyc_slice as oc
from tools.lexical_training import opencyc_inquiry as iq
from tests.test_opencyc_inquiry import make_lesson, event, mock_direct_fact_owner


class SourceBindingTests(unittest.TestCase):
    def check_source(self, title):
        req = make_lesson()['slice']
        req['source']['id'] = title
        seen = []
        def unavailable(raw, query, certificate, identity, revision, scope, *args):
            # ground.propose has already parsed these with the ORIGINAL reader.
            self.assertEqual(certificate['source']['identity'], identity)
            self.assertRegex(identity, r'^[a-z][a-z0-9_]*$')
            self.assertLessEqual(len(identity), 128)
            seen.append(identity)
            raise pilot.PilotError('CHECKER_UNAVAILABLE', 'unit boundary only')
        with patch.object(pilot, 'native', side_effect=unavailable):
            report = oc.analyze('كَلْبُ', 'arabic_fixture', req)
        self.assertEqual(report['compiled']['request']['source']['id'], title)
        self.assertEqual(report['native_source_binding']['identity'], seen[0])
        self.assertEqual(report['proposal']['source']['identity'], seen[0])
        self.assertEqual(report['reason'], 'CHECKER_UNAVAILABLE')
        self.assertFalse(report['native_checked'])
        self.assertFalse(report['limits']['source_authenticated'])
        return seen[0]

    def test_metadata_titles_do_not_break_original_owner_identity(self):
        ids = set()
        for title in ('valid_id', 'OpenCyc 2012', 'Arabic/2026', 'مصدر عربي', 'id\nwith newline'):
            with self.subTest(title=title): ids.add(self.check_source(title))
        self.assertEqual(len(ids), 5)

    def test_binding_is_stable(self):
        self.assertEqual(self.check_source('OpenCyc 2012'), self.check_source('OpenCyc 2012'))

    def test_final_effective_slice_is_replayed_after_withdrawal(self):
        lesson = make_lesson()
        lesson['events'] = [event('observe_b', 'observe', '#$B'), event('withdraw_b', 'withdraw', 'b-t')]
        owner = mock_direct_fact_owner(lesson)
        with patch.object(oc, 'analyze', return_value=owner) as replay:
            result = iq.run(lesson)
        replayed = replay.call_args.args[2]
        self.assertEqual(replayed['withdrawn'], ['b-t'])
        self.assertEqual(result['learning']['candidate_counts'], [4, 2, 2])
        self.assertEqual(result['history']['events'][-1]['assessment'],
                         'NOT_ASSESSED_HERE_ONLY_CURRENT_STATE_REPLAYED')


class NativeSourceBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (oc.ROOT / 'formal/.lake/build/bin/verifiedReading').is_file():
            if os.environ.get('NABT_REQUIRE_OPENCYC_NATIVE') == '1':
                raise AssertionError('Original Lean checker required by release gate')
            raise unittest.SkipTest('Original native owner unavailable locally')

    def test_metadata_title_with_spaces_through_actual_owner(self):
        req = make_lesson()['slice']
        req['source']['id'] = 'OpenCyc 2012'
        report = oc.analyze('كَلْبُ', 'arabic_fixture', req)
        self.assertTrue(report['native_checked'], report)
        self.assertEqual(report['status'], 'SUPPORTED')
        self.assertEqual(report['native_receipt']['source_id'], report['native_source_binding']['identity'])
        self.assertEqual(report['compiled']['request']['source']['id'], 'OpenCyc 2012')


if __name__ == '__main__': unittest.main()
