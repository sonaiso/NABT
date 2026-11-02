"""One independent CLI/API classification probe; no production or tests edits.

Run --phase before to retain the original failure and --phase after after the
CLI correction. Existing phase evidence is never overwritten.
"""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]

from nabt.errors import NabtError
from tools.derivation_surface_bridge import evaluate_derivation_surface


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save_once(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', required=True, choices=('before', 'after'))
    args = parser.parse_args()
    record_path = HERE / (args.phase + '.json')
    if record_path.exists():
        raise RuntimeError('Retained phase evidence already exists; do not overwrite it')
    request = {
        'schema': 'nabt.derivation-surface-request.v1',
        'profile': 'medial-alif-unmarked.v1',
        'span': {'start': 0, 'end': 10}, 'root': 'قول',
        'pattern_id': 'past.I.a', 'ending': 'َ',
        'hypotheses': {'context': 'ordinary', 'origin': 'original'},
    }
    # Build the input token literally. str(10**4999) would itself trigger the
    # host's decimal conversion guard and prevent this probe reaching the CLI.
    token = '1' + '0' * 4999
    normal = json.dumps([request], ensure_ascii=False, sort_keys=True,
                        separators=(',', ':'), allow_nan=False)
    assert normal.count('"start":0') == 1
    payload = normal.replace('"start":0', '"start":' + token).encode('utf-8')
    assert len(token) == 5000 and len(payload) > 4096
    input_path = HERE / 'applications_5000_digit.json'
    if input_path.exists():
        assert input_path.read_bytes() == payload
    else:
        save_once(input_path, payload)

    owners = [ROOT / 'tools/recursive_bridge.py', ROOT / 'tools/derivation_surface_bridge.py']
    before = {str(path.relative_to(ROOT)): digest(path) for path in owners}
    api_request = deepcopy(request)
    api_request['span']['start'] = 10 ** 4999
    try:
        result = evaluate_derivation_surface('قَالَ', api_request)
        api_result = {'returned_report': True, 'status': result['status']}
    except NabtError as error:
        api_result = error.as_dict()

    environment = {
        'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin',
        'PYTHONPATH': 'src:.', 'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONNOUSERSITE': '1', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
    }
    with tempfile.TemporaryDirectory(prefix='nabt-decimal-source-absent-') as directory:
        missing_source = str(Path(directory) / 'source-does-not-exist.txt')
        assert not Path(missing_source).exists()
        command = [sys.executable, '-B', '-m', 'tools.recursive_bridge',
                   'read-applications', missing_source, '--applications', str(input_path)]
        started = datetime.now(timezone.utc).isoformat()
        run = subprocess.run(command, cwd=ROOT, env=environment,
                             capture_output=True, check=False, timeout=15)
    save_once(HERE / (args.phase + '.stdout.json'), run.stdout)
    save_once(HERE / (args.phase + '.stderr.log'), run.stderr)
    try:
        cli_result = json.loads(run.stdout)
    except (ValueError, UnicodeError):
        cli_result = {'unparsed_stdout': True}
    api_correct = (api_result.get('status'), api_result.get('code')) == ('DEFER', 'RESOURCE_LIMIT')
    cli_correct = (run.returncode == 3 and
                   (cli_result.get('status'), cli_result.get('code')) == ('DEFER', 'RESOURCE_LIMIT'))
    passed = api_correct and cli_correct
    log = (f'One independent decimal-input classification probe ({args.phase})\n'
           f'Decimal digits: 5000; canonical list bytes: {len(payload)}\n'
           'Expected API: DEFER/RESOURCE_LIMIT\n'
           f'Observed API: {api_result.get("status")}/{api_result.get("code")}\n'
           'Expected CLI: exit 3, DEFER/RESOURCE_LIMIT before absent source\n'
           f'Observed CLI: exit {run.returncode}, {cli_result.get("status")}/{cli_result.get("code")}\n'
           f'Probe: {"PASS" if passed else "FAIL"}\n').encode('utf-8')
    save_once(HERE / (args.phase + '.log'), log)
    record = {
        'schema': 'nabt.derivation-surface-decimal-input-probe.v1',
        'phase': args.phase, 'utc': started, 'probe_count': 1,
        'head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip(),
        'python_version': sys.version,
        'python_int_max_str_digits': getattr(sys, 'get_int_max_str_digits', lambda: None)(),
        'command': command, 'cwd': str(ROOT), 'environment': environment,
        'source_path_existed': False,
        'decimal_digits': len(token), 'input_bytes': len(payload),
        'input_sha256': sha256(payload).hexdigest(), 'input_file': input_path.name,
        'api_result': api_result, 'cli_result': cli_result,
        'cli_exit_code': run.returncode, 'probe_exit_code': 0 if passed else 1,
        'expected_cli': {'exit_code': 3, 'status': 'DEFER', 'code': 'RESOURCE_LIMIT'},
        'owner_sha256_before': before,
        'owner_sha256_after': {str(path.relative_to(ROOT)): digest(path) for path in owners},
        'stdout_sha256': sha256(run.stdout).hexdigest(),
        'stderr_sha256': sha256(run.stderr).hexdigest(),
        'log_sha256': sha256(log).hexdigest(), 'probe_sha256': digest(Path(__file__)),
        'passed': passed,
        'scope': 'One bounded-input classification/order probe, not a kernel or general release gate.',
    }
    save_once(record_path, (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(log.decode('utf-8'), end='')
    print('Retained:', record_path)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
