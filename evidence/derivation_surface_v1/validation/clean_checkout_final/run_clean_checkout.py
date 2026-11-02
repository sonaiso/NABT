"""Reproduce only the three new suites and their CLI example from a Git archive.

The environment is constructed from a small allowlist. No inherited native
checker setting, original workspace PYTHONPATH, or network operation is used.
Each invocation reserves a new output directory; retained evidence beside this
script is never a rerun destination.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time


REVISION = 'e1e4a950a1f6df4268d18c3211c5e66bccc0f78b'
EVIDENCE = Path(__file__).resolve().parent
REPO = EVIDENCE.parents[3]


def fingerprint(path):
    hasher, size = sha256(), 0
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            hasher.update(chunk)
    return {'bytes': size, 'sha256': hasher.hexdigest()}


def allocate_output_dir(output_dir=None):
    """Reserve one fresh destination before any archive or validation command."""
    if output_dir is not None:
        destination = Path(output_dir).absolute()
        destination.mkdir(parents=True, exist_ok=False)
        return destination
    parent = REPO / 'artifacts' / 'local'
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f'derivation-clean-checkout-{REVISION[:7]}-',
                                 dir=parent))


def write_bytes_exclusive(path, data):
    """Fail on any existing file, including a collision inside a new directory."""
    with path.open('xb') as stream:
        stream.write(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        help='New directory; existing paths are refused. Default: a fresh artifacts/local directory.')
    args = parser.parse_args(argv)
    try:
        output_dir = allocate_output_dir(args.output_dir)
    except OSError as error:
        parser.error('Cannot reserve a fresh output directory: ' + str(error))
    harness_sha256 = fingerprint(Path(__file__).resolve())['sha256']
    staging = Path(tempfile.mkdtemp(prefix='nabt-derivation-clean-'))
    clean = staging / 'checkout'
    clean.mkdir()
    archive = staging / 'source.tar'
    archive_command = ['git', 'archive', '--format=tar', '--output', str(archive), REVISION]
    exported = subprocess.run(archive_command, cwd=REPO, capture_output=True, check=False)
    if exported.returncode:
        raise RuntimeError('The requested committed tree could not be archived')
    with tarfile.open(archive, 'r|') as source:
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
        ('decimal', [sys.executable, '-B', '-m', 'unittest', 'discover',
                     '-s', 'tests', '-p', 'test_derivation_surface_decimal.py', '-v']),
        ('example', [sys.executable, '-B', '-m', 'tools.recursive_bridge',
                     'read-applications', 'examples/derivation_surface_v1/source.txt',
                     '--applications', 'examples/derivation_surface_v1/applications.json']),
        ('replay', [sys.executable, '-B', '-m', 'tools.recursive_bridge',
                    'verify-applications', 'examples/derivation_surface_v1/source.txt',
                    '--applications', 'examples/derivation_surface_v1/applications.json',
                    '--report', str(output_dir / 'example_report.json')]),
    ]
    runs = []
    for name, command in commands:
        utc = datetime.now(timezone.utc).isoformat()
        begin = time.monotonic()
        result = subprocess.run(command, cwd=clean, env=environment,
                                capture_output=True, check=False, timeout=60)
        elapsed = time.monotonic() - begin
        log = result.stdout + result.stderr
        log_path = output_dir / (name + '.log')
        write_bytes_exclusive(log_path, log)
        entry = {'name': name, 'command': command, 'cwd': str(clean), 'utc': utc,
                 'elapsed_seconds': elapsed, 'exit_code': result.returncode,
                 'stdout_bytes': len(result.stdout), 'stderr_bytes': len(result.stderr),
                 'log': log_path.name, 'log_sha256': sha256(log).hexdigest()}
        if name in ('acceptance', 'review', 'decimal'):
            match = re.search(rb'Ran (\d+) tests? in ', log)
            entry['test_methods'] = int(match.group(1)) if match else None
            entry['skipped_methods'] = len(re.findall(rb'\.\.\. skipped ', log))
            entry['unittest_ok'] = bool(re.search(rb'^OK$', log, re.MULTILINE))
        if name == 'example' and result.returncode == 0:
            write_bytes_exclusive(output_dir / 'example_report.json', result.stdout)
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
        'tests/test_derivation_surface_decimal.py',
        'evidence/derivation_surface_v1/review/decimal_input/applications_5000_digit.json',
        'examples/derivation_surface_v1/source.txt',
        'examples/derivation_surface_v1/applications.json',
        'evidence/derivation_surface_v1/independent/freeze.json',
    ]
    record = {
        'schema': 'nabt.derivation-surface-clean-checkout.v1',
        'revision': REVISION, 'method': 'git archive extracted into a fresh /tmp directory',
        'output_directory': str(output_dir), 'harness_sha256': harness_sha256,
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
        'scope': 'Package independence for these 22 methods and the shipped CLI example/replay. Full kernel, native conformance and remote release gates are separate.',
    }
    write_bytes_exclusive(output_dir / 'verification.json',
                          (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'revision': REVISION, 'checkout': str(clean), 'passed': record['passed'],
                      'output_directory': str(output_dir),
                      'test_method_total': record['test_method_total'],
                      'absent_local_build_paths': record['absent_local_build_paths'],
                      'runs': [{'name': row['name'], 'exit_code': row['exit_code'],
                                'test_methods': row.get('test_methods'),
                                'result': row.get('result')} for row in runs]},
                     ensure_ascii=False, indent=2))
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
