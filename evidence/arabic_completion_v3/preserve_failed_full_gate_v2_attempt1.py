#!/usr/bin/env python3
"""Preserve the rejected measurement exactly; never repair its incomplete gzip."""
from hashlib import sha256
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PHASE = Path(__file__).resolve().parent
RUN = ROOT / 'artifacts/local/arabic-completion-full-validation-v2'
OUTPUT = PHASE / 'failed_full_gate_v2_attempt1'
DIAGNOSIS = ROOT / 'artifacts/local/arabic-completion-runtime-v2-continuation/full_gate_failure_diagnosis_v1.json'
DIAGNOSIS_SHA = 'eca9b80d8e7ff036883c1050947440f441c21f73f71c8c5b1bd75e9bf0f296eb'
FAILED_RAW = 'arabic-completion-oracle/strict/raw.jsonl.gz'
FAILED_SHA = 'b6f7a8c38110806739b2252ad7964ad120e4c7f17eae2f8be18cecbec15dce15'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def inventory():
    rows = []
    for path in sorted(RUN.rglob('*')):
        require(not path.is_symlink(), 'Unexpected symlink in failed attempt')
        if path.is_file():
            raw = path.read_bytes()
            rows.append({'path': str(path.relative_to(RUN)), 'bytes': len(raw), 'sha256': digest(raw)})
    return rows


def main():
    require(not OUTPUT.exists(), 'Never replace a preserved attempt')
    execution = json.loads((RUN / 'execution.json').read_bytes())
    require(execution['all_required_gates_passed'] is False and execution['exit_code'] == 2
            and execution['executable_inputs_unchanged'] is True, 'Different failure contract')
    require(digest((RUN / FAILED_RAW).read_bytes()) == FAILED_SHA, 'Rejected raw bytes changed')
    diagnostic = DIAGNOSIS.read_bytes()
    require(digest(diagnostic) == DIAGNOSIS_SHA, 'Independent diagnosis changed')
    rows = inventory()
    OUTPUT.mkdir()
    archive = OUTPUT / 'failed_attempt.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for item in rows:
            target.writestr(item['path'], (RUN / item['path']).read_bytes())
    with zipfile.ZipFile(archive) as saved:
        require(saved.namelist() == [item['path'] for item in rows], 'Archive inventory changed')
        for item in rows:
            raw = saved.read(item['path'])
            require(len(raw) == item['bytes'] and digest(raw) == item['sha256'], 'Archive bytes changed')
    require(inventory() == rows, 'Failed attempt changed while preserving it')
    (OUTPUT / 'diagnosis.json').write_bytes(diagnostic)
    (OUTPUT / 'execution.json').write_bytes((RUN / 'execution.json').read_bytes())
    receipt = {
        'schema': 'nabt.failed-full-gate-preservation.v1',
        'status': 'FAILED_MEASUREMENT_INTEGRITY_NOT_APPROVED',
        'source_run': str(RUN.relative_to(ROOT)),
        'archive': {'path': str(archive.relative_to(ROOT)), 'bytes': archive.stat().st_size,
                    'sha256': digest(archive.read_bytes()), 'entries': len(rows)},
        'all_files_preserved_exactly': True, 'files': rows,
        'rejected_raw_member': FAILED_RAW, 'rejected_raw_sha256': FAILED_SHA,
        'raw_complete': False, 'missing_bytes': 374596, 'retained_records': 194, 'expected_records': 214,
        'diagnosis_sha256': DIAGNOSIS_SHA, 'cause_established': False,
        'evidence_repaired': False, 'scoring_or_integrity_requirements_relaxed': False,
        'next_action': 'New complete execution using the same frozen runner and runtime; this failed attempt cannot supply release approval.',
        'script_sha256': digest(Path(__file__).read_bytes()),
    }
    (OUTPUT / 'preservation.json').write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'archive': receipt['archive'], 'failed_attempt_preserved': True,
                      'repair_or_success_claimed': False}))


if __name__ == '__main__':
    main()
