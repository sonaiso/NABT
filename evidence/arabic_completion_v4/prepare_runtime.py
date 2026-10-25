#!/usr/bin/env python3
"""Freeze the productive extension without replacing historical snapshots."""
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
PREVIOUS_SHA = '045d6b3d6d3c2f6744b3157a2bd3cbf025b401e2efd215d8a4200182685978dd'
CHANGED = {'pyproject.toml', 'src/nabt/__init__.py', 'src/nabt/person_evidence.py', 'src/nabt/construction_nominals.py', 'src/nabt/discourse_reader.py'}
ADDED = {'src/nabt/productive_forms.py', 'src/nabt/data/productive_forms.json', 'src/nabt/data/source_evidence/productive_forms_v1.json'}


def main():
    previous_raw = (ROOT / 'evidence/arabic_completion_v3/code_freeze_v2.json').read_bytes()
    assert sha256(previous_raw).hexdigest() == PREVIOUS_SHA
    previous = json.loads(previous_raw)
    actual = {'pyproject.toml'} | {
        str(p.relative_to(ROOT)) for p in (ROOT / 'src').rglob('*')
        if p.is_file() and '__pycache__' not in p.parts
        and not any(v.endswith(('.egg-info', '.dist-info')) for v in p.parts)}
    actual -= {'src/nabt/data/source_evidence/README.md',
               'src/nabt/data/source_evidence/LICENSE-DATA.md',
               'src/nabt/data/source_evidence/.gitattributes'}
    assert actual == {r['path'] for r in previous['files']} | ADDED
    old_rows = {r['path']: r for r in previous['files']}
    rows, changed = [], set()
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for name in sorted(actual):
                old = old_rows.get(name, {'path': name})
                path = ROOT / old['path']
                assert path.is_file() and not path.is_symlink()
                raw = path.read_bytes()
                row = {'path': old['path'], 'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}
                if row != old:
                    changed.add(old['path'])
                rows.append(row)
                member = tarfile.TarInfo(old['path'])
                member.size, member.mode, member.mtime = len(raw), 0o644, 0
                archive.addfile(member, io.BytesIO(raw))
    assert changed == CHANGED | ADDED and len(rows) == 83
    bundle = buffer.getvalue()
    manifest = {
        'schema': previous['schema'], 'utc': datetime.now(timezone.utc).isoformat(),
        'repository_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'repository_status': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        'file_selection': previous['file_selection'],
        'excluded_build_metadata': previous['excluded_build_metadata'],
        'previous_runtime_manifest_sha256': PREVIOUS_SHA,
        'change_scope': 'Versioned source-conditioned productive imperative and accusative-alif laws; no universal completeness claim.',
        'changed_runtime_paths': sorted(changed), 'files': rows,
        'snapshot_sha256': sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
        'archive_filename': 'code_freeze_v1.tar.gz', 'archive_sha256': sha256(bundle).hexdigest(),
    }
    raw = json.dumps(manifest, ensure_ascii=False, indent=2).encode() + b'\n'
    for name in ('code_freeze_v1.json', 'code_freeze_v1.tar.gz'):
        assert not (FOLDER / name).exists(), 'Never overwrite an observed freeze'
    (FOLDER / 'code_freeze_v1.tar.gz').write_bytes(bundle)
    (FOLDER / 'code_freeze_v1.json').write_bytes(raw)
    print(json.dumps({'manifest_sha256': sha256(raw).hexdigest(),
        'snapshot_sha256': manifest['snapshot_sha256'], 'archive_sha256': manifest['archive_sha256'],
        'files': len(rows), 'changed_paths': sorted(changed)}))


if __name__ == '__main__':
    main()
