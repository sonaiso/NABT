"""Narrow regression policy for the shared A116 framework-foundation runtime.

This accepts only the still-failing signatures from the complete strict run.
It never edits a score, waives evidence validation, or certifies all Arabic.
The caller must perform source/runtime/raw-journal verification first; this
module checks the finalized evaluator receipt, not arbitrary runtime claims.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SHA256 = 'a192d915f933a8f98ddb4d166f741be4ab976d34cc2c13be71eb940f08ca06e4'
POLICY_PATH = ROOT / 'evidence/framework_foundation_v1/regression_policy_v2.json'
POLICY_SHA256 = '20b8eb82e9df6dd52905d1dd3bde2716fec819302b9a538a6f0965aa42dde275'


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def load_policy(path=POLICY_PATH):
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != POLICY_SHA256:
        raise ValueError('Arabic coverage regression policy bytes changed')
    return json.loads(payload)


def gate_decision(suite, result, allow_documented_boundaries=False):
    """Fail closed on incomplete inventories, altered failures, or bad receipts."""
    integrity, documented, unexpected = [], [], []
    strict = False
    approved = False
    try:
        policy = load_policy()
        expected = policy['suites'][suite]
        snapshot = result['snapshot']
        approved = snapshot['runtime_freeze_sha256'] == RUNTIME_SHA256
        for field in ('runtime_freeze_sha256', 'runtime_snapshot_sha256', 'runtime_file_count'):
            if wire(snapshot[field]) != wire(policy[field]):
                integrity.append('runtime_pin_mismatch:' + field)
        for field in ('gold_freeze_sha256', 'source_sha256'):
            if result[field] != expected[field]:
                integrity.append('material_pin_mismatch:' + field)
        cases = result['cases']
        case_ids = [case['id'] for case in cases]
        expected_ids = [case['id'] for case in expected['cases']]
        if (type(result['total']) is not int or result['total'] != expected['total']
                or case_ids != expected_ids):
            integrity.append('complete_ordered_case_inventory_required')
        if result['measurement_valid'] is not True:
            integrity.append('valid_measurement_required')
        for field in ('execution_errors', 'question_execution_errors'):
            if result[field] != []:
                integrity.append('no_errors_required:' + field)
        if suite == 'construction' and result['finalization_errors'] != []:
            integrity.append('no_errors_required:finalization_errors')
        if (type(result['false_accept_count']) is not int or result['false_accept_count'] != 0
                or type(result['false_accept_case_count']) is not int
                or result['false_accept_case_count'] != 0):
            integrity.append('false_accepts_are_never_waived')
        by_id = {case['id']: case for case in expected['cases']}
        for case in cases:
            case_id = case['id']
            reference = by_id.get(case_id)
            if reference is None:
                integrity.append('unexpected_case:' + case_id)
                continue
            checks, failures = case['checks'], case['failures']
            if ([check['check'] for check in checks] != reference['checks']
                    or any(type(check['passed']) is not bool for check in checks)):
                integrity.append('complete_typed_check_inventory_required:' + case_id)
            failed_checks = [check for check in checks if check['passed'] is False]
            if ([failure['check'] for failure in failures]
                    != [check['check'] for check in failed_checks]):
                integrity.append('case_failure_inventory_mismatch:' + case_id)
            if suite == 'construction' and wire(failures) != wire(failed_checks):
                integrity.append('case_failure_details_mismatch:' + case_id)
            if (type(case['passed']) is not bool or case['passed'] != (not failures)
                    or case['passed'] != (not failed_checks)):
                integrity.append('case_pass_flag_mismatch:' + case_id)
            if case['false_accepts'] != []:
                integrity.append('case_false_acceptance:' + case_id)
            if suite == 'construction' and any(
                    check['check'].startswith('question:')
                    and check.get('details', {}).get('certificate') is not True for check in checks):
                integrity.append('question_certificate_required:' + case_id)
            allowed = {wire(failure) for failure in reference['allowed_failures']}
            for failure in failures:
                item = {'id': case_id, 'check': failure['check'],
                        'signature_sha256': sha256(wire(failure)).hexdigest()}
                (documented if wire(failure) in allowed else unexpected).append(item)
        passed = sum(case['passed'] is True for case in cases)
        if type(result['passed']) is not int or result['passed'] != passed:
            integrity.append('pass_total_mismatch')
        question_count = sum(check['check'].startswith('question:')
                             for case in cases for check in case['checks'])
        if question_count != expected['question_total']:
            integrity.append('complete_question_check_inventory_required')
        raw = result['raw_log']
        if suite == 'construction':
            if not all(raw[field] is True for field in (
                    'complete_gzip_verified', 'canonical_json_verified', 'write_time_inventory_verified')):
                integrity.append('complete_raw_finalization_required')
            for field, value in (('case_count', 86), ('question_count', 106),
                                 ('expected_question_count', 106), ('record_count', 87),
                                 ('execution_error_count', 0), ('question_error_count', 0),
                                 ('early_failure_skipped_questions', 0)):
                if type(raw[field]) is not int or raw[field] != value:
                    integrity.append('raw_count_mismatch:' + field)
            if raw['case_ids'] != expected_ids:
                integrity.append('raw_case_inventory_mismatch')
            records = raw['record_inventory']
            identities = [{'kind': row['kind'], 'id': row['id']} for row in records]
            if [row['index'] for row in records] != list(range(87)) or any(
                    type(row['index']) is not int for row in records):
                integrity.append('raw_record_index_mismatch')
            if sha256(wire(records)).hexdigest() != raw['record_inventory_sha256']:
                integrity.append('raw_inventory_digest_mismatch')
        else:
            if raw['valid'] is not True:
                integrity.append('complete_raw_finalization_required')
            for field, value in (('case_count', 86), ('record_count', 90),
                                 ('profile_count', 2), ('variant_count', 2)):
                if type(raw[field]) is not int or raw[field] != value:
                    integrity.append('raw_count_mismatch:' + field)
            for field, value in (('frozen_case_count', 86), ('frozen_question_count', 74)):
                if type(result[field]) is not int or result[field] != value:
                    integrity.append('frozen_inventory_mismatch:' + field)
            records = raw['records']
            identities = [row['identity'] for row in records]
        if wire(identities) != wire(expected['raw_record_identities']):
            integrity.append('complete_raw_record_inventory_required')
        if any(type(row['bytes']) is not int or row['bytes'] <= 0
               or re.fullmatch('[0-9a-f]{64}', row['sha256']) is None for row in records):
            integrity.append('invalid_raw_record_receipt')
        strict = not integrity and not documented and not unexpected and passed == 86
        if type(result['strict_pass']) is not bool or result['strict_pass'] != strict:
            integrity.append('strict_pass_flag_mismatch')
    except (KeyError, TypeError, ValueError, OSError, AttributeError) as error:
        integrity.append('malformed_or_unpinned_gate_input:' + type(error).__name__)
    return {
        'gate_pass': not integrity and (strict or bool(
            allow_documented_boundaries and approved and not unexpected)),
        'gate_mode': 'documented_partial_coverage_arabic_v4' if allow_documented_boundaries else 'strict',
        'coverage_complete': strict and not integrity,
        'all_arabic_completeness_established': False,
        'documented_boundary_runtime_sha256': RUNTIME_SHA256 if approved else None,
        'documented_boundary_failures': documented,
        'unexpected_failures': unexpected,
        'gate_integrity_errors': integrity,
        'documented_boundary_inventory_sha256': POLICY_SHA256,
        'boundary_policy': 'EXACT_RESIDUAL_FAILURE_PAYLOADS_COMPLETE_INVENTORIES_NO_SAFETY_WAIVER',
        'boundary_policy_revision': 'arabic_completion_v4_preserved_residuals_v1',
        'boundary_policy_runtime_approved': approved,
    }
