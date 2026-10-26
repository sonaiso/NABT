"""Strict authority tests: actual native claims and hostile receipt mutations.

These are contract/counterexample tests, not a population language score.
"""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from nabt import foundation
from nabt.errors import NabtError
from tools.linguistic_truth import certified

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'formal/.lake/build/bin/linguisticTruth'


class CertifiedBoundary(unittest.TestCase):
    def test_public_api_has_no_imported_authority_or_checker_path(self):
        for argument in ('native_checked', 'proof', 'root', 'known', 'ledger', 'executable'):
            with self.subTest(argument=argument), self.assertRaises(TypeError):
                certified.acquire_certified('قَرْءُ', **{argument: True})

    def test_shared_foundation_denial_precedes_acquisition(self):
        with patch.object(foundation, 'require_foundation',
                          side_effect=NabtError('FOUNDATION_TEST_DENIED', 'test', status='DEFER')):
            with patch.object(certified.runtime, 'acquire') as acquire:
                with self.assertRaisesRegex(NabtError, 'test'):
                    certified.acquire_certified('قَرْءُ', profile_id='linguistic')
                acquire.assert_not_called()

    def test_invalid_marks_never_reach_combined_native_gate(self):
        for text in ('َ', 'قَرْءُُ', 'قَرْءَُ'):
            with self.subTest(text=text), patch.object(certified, '_native') as native:
                report = certified.acquire_certified(text, profile_id='linguistic')
                self.assertEqual(report['status'], 'INVALID_INPUT')
                self.assertFalse(report['native_checked'])
                self.assertFalse(report['strict_language_accepted'])
                self.assertEqual(report['claims'], [])
                native.assert_not_called()

    def test_native_protocol_rejects_duplicate_and_nonfinite_fields(self):
        for raw in ('{"native_checked":false,"native_checked":true}',
                    '{"nested":{"a":1,"a":2}}', '{"cells":[NaN]}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                certified._strict_json(raw)

    def test_native_resource_receipt_is_not_misreported_as_verification_failure(self):
        fake = subprocess.CompletedProcess([], 0,
            b'{"status":"RESOURCE_LIMIT","message":"bounded response exhausted"}', b'')
        with patch.object(certified.subprocess, 'run', return_value=fake):
            with self.assertRaisesRegex(OverflowError, 'RESOURCE_LIMIT'):
                certified._native({})

    def test_transport_limits_precede_process_and_fail_on_oversized_output(self):
        with patch.object(certified.subprocess, 'run') as run:
            with self.assertRaisesRegex(OverflowError, 'REQUEST_LIMIT'):
                certified._native({'payload': 'x' * certified._MAX_NATIVE_BYTES})
            run.assert_not_called()
        fake = subprocess.CompletedProcess([], 0, b'x' * (certified._MAX_NATIVE_RESPONSE_BYTES + 1), b'')
        with patch.object(certified.subprocess, 'run', return_value=fake):
            with self.assertRaisesRegex(OverflowError, 'RESPONSE_LIMIT'):
                certified._native({})


@unittest.skipUnless(NATIVE.is_file(), 'native linguisticTruth built in formal CI')
class CertifiedNativeClaims(unittest.TestCase):
    def test_complete_a116_source_certifies_candidates_not_intention(self):
        report = certified.acquire_certified('قَرْءُ', profile_id='linguistic',
            source_id='independent-claim', context='medical-reading')
        self.assertEqual(report['foundation_source']['status'], 'COMPLETE')
        self.assertTrue(report['native_checked'])
        self.assertTrue(report['candidate_set_checked'])
        self.assertFalse(report['conditional_use_checked'])
        self.assertFalse(report['strict_language_accepted'])
        self.assertEqual(report['status'], 'DEFER')
        self.assertIn('ACQUISITION_NOT_KERNEL_PROVED', report['residuals'])
        self.assertEqual(len(report['claims']), 1)
        claim = report['claims'][0]
        self.assertEqual(claim['kind'], 'A116_EXACT_INSTALLED_CANDIDATE_SET')
        self.assertEqual(claim['proof']['kind'], 'NATIVE_LEAN_RECEIPT')
        self.assertEqual(claim['binding']['source']['text'], 'قَرْءُ')
        self.assertEqual(claim['binding']['frame']['occurrence']['context'], 'medical-reading')
        self.assertGreater(claim['candidate_count'], 1)
        self.assertFalse(report['all_arabic_complete'])
        self.assertFalse(report['world_truth_established'])
        self.assertFalse(report['tawatur_evaluated'])

    def test_candidate_enumeration_does_not_prove_surface_to_lexeme_acquisition(self):
        # Both are direct A116 representations. The current retrieval adapter
        # proposes the same expression label after removing marks; no theorem
        # here licenses either spelling as that lexeme in this context.
        for text in ('عَيْنَ', 'عِيْنَ'):
            with self.subTest(text=text):
                report = certified.acquire_certified(text, profile_id='linguistic')
                self.assertTrue(report['candidate_set_checked'])
                self.assertFalse(report['lexical_surface_licensed'])
                self.assertFalse(report['strict_language_accepted'])
                self.assertFalse(report['conditional_use_checked'])
                for claim in report['claims']:
                    self.assertIn('OCCURRENCE_TO_LEXEME_NOT_KERNEL_PROVED', claim['unresolved_premises'])
                    self.assertIn('Surface-to-lexeme acquisition is not kernel-proved', claim['scope'])

    def test_partial_source_cannot_get_a116_proof_from_semantic_support(self):
        report = certified.acquire_certified('أعني بالأسد الحيوان المفترس', profile_id='linguistic')
        self.assertTrue(report['diagnostic']['native_checked'])
        self.assertTrue(report['diagnostic']['occurrences'][0]['certified_sense_ids'])
        self.assertTrue(report['native_checked'])
        self.assertEqual(report['foundation_source']['status'], 'PARTIAL')
        self.assertIn('SOURCE_TO_A116_INCOMPLETE', report['residuals'])
        self.assertFalse(report['candidate_set_checked'])
        self.assertFalse(report['conditional_use_checked'])
        self.assertEqual(report['claims'], [])
        self.assertFalse(report['strict_language_accepted'])

    def test_missing_profile_cannot_borrow_a_hypothesis_certificate(self):
        with patch.object(certified, '_native') as native:
            result = certified.acquire_certified('قَرْءُ')
        self.assertEqual(result['reason'], 'CONVENTION_PROFILE_UNESTABLISHED')
        self.assertEqual(result['claims'], [])
        self.assertFalse(result['candidate_set_checked'])
        native.assert_not_called()

    def test_missing_native_binary_does_not_trust_diagnostic_success(self):
        with patch.object(certified, '_native', side_effect=FileNotFoundError('withheld binary')):
            result = certified.acquire_certified('قَرْءُ', profile_id='linguistic')
        self.assertTrue(result['diagnostic']['native_checked'])
        self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')
        self.assertFalse(result['native_checked'])
        self.assertFalse(result['strict_language_accepted'])
        self.assertEqual(result['claims'], [])

    def test_full_response_mutations_cannot_create_a_proof(self):
        original = certified.acquire_certified('قَرْءُ', profile_id='linguistic')
        receipt = original['occurrences'][0]['native_receipt']
        mutations = []
        for key, value in (('source_number', '0'), ('candidate_set_checked', 1),
                           ('projection_status', 'PARTIAL'), ('native_acquisition_proof', True),
                           ('world_truth_established', True), ('all_arabic_complete', True),
                           ('certified_from_a116', True), ('extra_authority', True)):
            row = deepcopy(receipt)
            row[key] = value
            mutations.append((key, row))
        row = deepcopy(receipt)
        row['cells'][0] = True
        mutations.append(('boolean-cell', row))
        row = deepcopy(receipt)
        row['source']['text'] = 'قَرْءُ '
        mutations.append(('foreign-source', row))
        row = deepcopy(receipt)
        row['semantic']['rows'][0]['verdict'] = 'SUPPORTED_PREMISES'
        mutations.append(('semantic-claim', row))
        for name, changed in mutations:
            with self.subTest(name=name), patch.object(certified, '_native', return_value=changed):
                result = certified.acquire_certified('قَرْءُ', profile_id='linguistic')
                self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')
                self.assertFalse(result['native_checked'])
                self.assertEqual(result['claims'], [])

    def test_source_mismatch_is_rejected_before_native_certification(self):
        diagnostic = certified.runtime.acquire('قَرْءُ', profile_id='linguistic')
        diagnostic['source']['raw_text'] = 'قَرْءُ '
        with patch.object(certified.runtime, 'acquire', return_value=diagnostic):
            with patch.object(certified, '_native') as native:
                result = certified.acquire_certified('قَرْءُ', profile_id='linguistic')
        self.assertEqual(result['reason'], 'ACQUISITION_SOURCE_MISMATCH')
        self.assertEqual(result['claims'], [])
        native.assert_not_called()

    def test_changed_explicit_context_cannot_borrow_native_request(self):
        diagnostic = certified.runtime.acquire('قَرْءُ', profile_id='linguistic', context='first')
        with patch.object(certified.runtime, 'acquire', return_value=diagnostic):
            with patch.object(certified, '_native') as native:
                result = certified.acquire_certified('قَرْءُ', profile_id='linguistic', context='second')
        self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')
        self.assertEqual(result['claims'], [])
        native.assert_not_called()

    def test_native_timeout_is_resource_exhaustion_not_language_rejection(self):
        with patch.object(certified, '_native', side_effect=subprocess.TimeoutExpired('native', 60)):
            result = certified.acquire_certified('قَرْءُ', profile_id='linguistic')
        self.assertEqual(result['status'], 'RESOURCE_EXHAUSTED')
        self.assertFalse(result['strict_language_accepted'])
        self.assertFalse(result['native_checked'])
        self.assertEqual(result['claims'], [])


if __name__ == '__main__':
    unittest.main()
