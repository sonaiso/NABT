"""Reproduce only the two new suites and their CLI example from a Git archive.

The environment is constructed from a small allowlist. No inherited native
checker setting, original workspace PYTHONPATH, or network operation is used.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time


REVISION = '6f291e2f6905f2d1ac58f4a7fdc61bbed3c8b986'
EVIDENCE = Path(__file__).resolve().parent
REPO = EVIDENCE.parents[3]


def fingerprint(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def main():
    staging = Path(tempfile.mkdtemp(prefix='nabt-derivation-clean-'))
    clean = staging / 'checkout'
    clean.mkdir()
    archive = staging / 'source.tar'
    archive_command = ['git', 'archive', '--format=tar', '--output', str(archive), REVISION]
    exported = subprocess.run(archive_command, cwd=REPO, capture_output=True, check=False)
    if exported.returncode:
        raise RuntimeError('The requested committed tree could not be archived')
    with tarfile.open(archive, 'r:') as source:
        source.extractall(clean, filter='data')

    # Use this interpreter's directory plus OS commands, never the original
    # checkout. In particular no NABT_*, native probe, LEAN_*, LAKE_* or inherited
    # Python module path is passed to the validation processes.
    environment = {
        'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin',
        'PYTHONPATH': 'src:.',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONNOUSERSITE': '1',
        'LANG': 'C.UTF-8',
        'LC_ALL': 'C.UTF-8',
    }
    commands = [
        ('acceptance', [sys.executable, '-B', '-m', 'unittest', 'discover',
                        '-s', 'tests', '-p', 'test_derivation_surface_bridge.py', '-v']),
        ('review', [sys.executable, '-B', '-m', 'unittest', 'discover',
                    '-s', 'tests', '-p', 'test_derivation_surface_review.py', '-v']),
        ('example', [sys.executable, '-B', '-m', 'tools.recursive_bridge',
                     'read-applications', 'examples/derivation_surface_v1/source.txt',
                     '--applications', 'examples/derivation_surface_v1/applications.json']),
        ('replay', [sys.executable, '-B', '-m', 'tools.recursive_bridge',
                    'verify-applications', 'examples/derivation_surface_v1/source.txt',
                    '--applications', 'examples/derivation_surface_v1/applications.json',
                    '--report', str(staging / 'example_report.json')]),
    ]
    runs = []
    for name, command in commands:
        utc = datetime.now(timezone.utc).isoformat()
        begin = time.monotonic()
        result = subprocess.run(command, cwd=clean, env=environment,
                                capture_output=True, check=False, timeout=60)
        elapsed = time.monotonic() - begin
        log = result.stdout + result.stderr
        log_path = EVIDENCE / (name + '.log')
        log_path.write_bytes(log)
        entry = {'name': name, 'command': command, 'cwd': str(clean), 'utc': utc,
                 'elapsed_seconds': elapsed, 'exit_code': result.returncode,
                 'stdout_bytes': len(result.stdout), 'stderr_bytes': len(result.stderr),
                 'log': log_path.name, 'log_sha256': sha256(log).hexdigest()}
        if name in ('acceptance', 'review'):
            match = re.search(rb'Ran (\d+) tests? in ', log)
            entry['test_methods'] = int(match.group(1)) if match else None
            entry['skipped_methods'] = len(re.findall(rb'\.\.\. skipped ', log))
            entry['unittest_ok'] = bool(re.search(rb'^OK$', log, re.MULTILINE))
        if name == 'example' and result.returncode == 0:
            (staging / 'example_report.json').write_bytes(result.stdout)
            (EVIDENCE / 'example_report.json').write_bytes(result.stdout)
            report = json.loads(result.stdout)
            entry['observed_application_statuses'] = [row['report']['status'] for row in report['applications']]
            entry['grammar_certified'] = report['grammar_certified']
            entry['report_id'] = report['report_id']
        if name == 'replay' and result.returncode == 0:
            entry['result'] = json.loads(result.stdout)
        runs.append(entry)

    checked = [
        'tools/derivation_surface_bridge.py', 'tools/recursive_bridge.py',
        'tests/test_derivation_surface_bridge.py', 'tests/test_derivation_surface_review.py',
        'examples/derivation_surface_v1/source.txt',
        'examples/derivation_surface_v1/applications.json',
        'evidence/derivation_surface_v1/independent/freeze.json',
    ]
    record = {
        'schema': 'nabt.derivation-surface-clean-checkout.v1',
        'revision': REVISION, 'method': 'git archive extracted into a fresh /tmp directory',
        'archive_command': archive_command, 'archive_exit_code': exported.returncode,
        'archive': fingerprint(archive), 'checkout': str(clean),
        'isolated_process_environment': environment,
        'inherited_environment_forwarded': False,
        'network_operations': [],
        'absent_local_build_paths': {path: not (clean / path).exists()
            for path in ('artifacts/local', 'formal/.lake', '.lake')},
        'checked_file_fingerprints': {path: fingerprint(clean / path) for path in checked},
        'runs': runs,
        'test_method_total': sum(row.get('test_methods') or 0 for row in runs),
        'passed': all(row['exit_code'] == 0 for row in runs)
            and all(row.get('unittest_ok', True) for row in runs),
        'scope': 'Package independence for these 21 methods and the shipped CLI example/replay. Full kernel, native conformance and remote release gates are separate.',
    }
    (EVIDENCE / 'verification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'revision': REVISION, 'checkout': str(clean), 'passed': record['passed'],
                      'test_method_total': record['test_method_total'],
                      'absent_local_build_paths': record['absent_local_build_paths'],
                      'runs': [{'name': row['name'], 'exit_code': row['exit_code'],
                                'test_methods': row.get('test_methods'),
                                'result': row.get('result')} for row in runs]},
                     ensure_ascii=False, indent=2))
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
