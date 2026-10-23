#!/usr/bin/env python3
"""Record the three authorized preflight targets; this is not make check."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
LAKE = Path('/tmp/nabt-tools/lean-4.34.1-linux/bin/lake')
FREEZE = ROOT / 'evidence/constructions/code_freeze_v2.json'
FREEZE_SHA = '5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1'


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data) -> None:
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def file_row(path: Path) -> dict:
    raw = path.read_bytes()
    return {'path': str(path.relative_to(OUT)), 'bytes': len(raw), 'sha256': digest(raw)}


def source_check() -> dict:
    raw = FREEZE.read_bytes()
    assert digest(raw) == FREEZE_SHA, 'Runtime freeze manifest differs from the authorized v2 pin'
    frozen = json.loads(raw)
    assert len(frozen['files']) == 74
    for row in frozen['files']:
        data = (ROOT / row['path']).read_bytes()
        assert len(data) == row['bytes'] and digest(data) == row['sha256'], row['path']
    actual = {'pyproject.toml'} | {
        str(path.relative_to(ROOT)) for path in (ROOT / 'src/nabt').rglob('*')
        if path.is_file() and path.suffix in {'.py', '.json', '.txt'}
    }
    assert actual == {row['path'] for row in frozen['files']}, 'Runtime inventory differs'
    return {'manifest_path': str(FREEZE.relative_to(ROOT)), 'manifest_sha256': digest(raw),
            'snapshot_sha256': frozen['snapshot_sha256'], 'files_verified': len(actual),
            'all_bytes_match': True, 'checked_at_utc': stamp()}


def probe(argv: list[str]) -> dict:
    result = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'argv': argv, 'returncode': result.returncode,
            'stdout': result.stdout.decode('utf-8', 'replace'),
            'stderr': result.stderr.decode('utf-8', 'replace')}


def main() -> int:
    (OUT / 'logs').mkdir(exist_ok=False)
    source_before = source_check()
    env_record = {
        'recorded_at_utc': stamp(), 'cwd': str(ROOT), 'python_executable': sys.executable,
        'python_version': sys.version, 'platform': platform.platform(),
        'machine': platform.machine(), 'make': shutil.which('make'), 'lake': str(LAKE),
        'locale': {key: os.environ.get(key) for key in ('LANG', 'LC_ALL', 'LC_CTYPE')},
        'recipe_environment': {'PYTHONPATH': str(ROOT / 'src')},
        'tool_probes': [probe(['git', 'rev-parse', 'HEAD']),
                        probe([str(LAKE), '--version']),
                        probe([str(LAKE.parent / 'lean'), '--version']),
                        probe(['make', '--version'])],
        'scope': 'make formal, make conformance, make benchmark only; no full make check; local numeric-kernel benchmark',
        'runtime_before': source_before,
    }
    write_json(OUT / 'environment.json', env_record)
    rows = []
    for target in ('formal', 'conformance', 'benchmark'):
        argv = ['make', target, f'LAKE={LAKE}', f'PYTHON={sys.executable}', f'EVIDENCE_DIR={OUT}']
        stdout_path, stderr_path = (OUT / 'logs' / f'{target}.{kind}' for kind in ('stdout', 'stderr'))
        started = stamp()
        clock = time.monotonic()
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            completed = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr)
        row = {'name': target, 'argv': argv, 'cwd': str(ROOT), 'started_at_utc': started,
               'finished_at_utc': stamp(), 'duration_seconds': time.monotonic() - clock,
               'returncode': completed.returncode, 'stdout': file_row(stdout_path),
               'stderr': file_row(stderr_path)}
        rows.append(row)
        write_json(OUT / 'logs' / f'{target}.command.json', row)
        print(json.dumps({'target': target, 'returncode': completed.returncode,
                          'duration_seconds': row['duration_seconds']}, sort_keys=True), flush=True)
        if completed.returncode:
            break
        if target == 'benchmark':
            raw_stdout = stdout_path.read_text(encoding='utf-8')
            start = raw_stdout.index('{\n')
            benchmark = json.loads(raw_stdout[start:])
            write_json(OUT / 'benchmark.json', benchmark)
    write_json(OUT / 'commands.json', rows)
    runtime_after = source_check()
    ok = len(rows) == 3 and all(row['returncode'] == 0 for row in rows)
    validation = {'schema': 'nabt.construction-release-preflight.v1', 'status': 'PASS' if ok else 'FAIL',
                  'scope': env_record['scope'], 'commands': len(rows),
                  'returncodes': {row['name']: row['returncode'] for row in rows},
                  'runtime_before': source_before, 'runtime_after': runtime_after,
                  'no_full_gate_run': True}
    write_json(OUT / 'validation.json', validation)
    manifest = {'schema': 'nabt.preflight-artifact-manifest.v1',
                'files': [file_row(path) for path in sorted(OUT.rglob('*')) if path.is_file()]}
    write_json(OUT / 'manifest.json', manifest)
    for row in manifest['files']:
        assert file_row(OUT / row['path']) == row, row['path']
    print(json.dumps({'status': validation['status'], 'runtime_files': 74,
                      'validation_sha256': digest((OUT / 'validation.json').read_bytes()),
                      'manifest_sha256': digest((OUT / 'manifest.json').read_bytes())}), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
