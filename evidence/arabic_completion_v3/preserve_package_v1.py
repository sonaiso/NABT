#!/usr/bin/env python3
"""Preserve, without replacing, the completed isolated wheel verification."""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def digest(data):
    return sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    source = args.run_dir.resolve()
    manifest = json.loads((source / 'manifest.json').read_bytes())
    validation_raw = (source / 'validation.json').read_bytes()
    validation = json.loads(validation_raw)
    assert validation['ok'] is True
    expected = {row['path']: row for row in manifest['files']}
    observed = {str(p.relative_to(source)): p for p in source.rglob('*') if p.is_file()}
    assert set(observed) == set(expected) | {'manifest.json'}
    for name, row in expected.items():
        raw = observed[name].read_bytes()
        assert len(raw) == row['bytes'] and digest(raw) == row['sha256'], name
    archive = HERE / 'package_validation_v1.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as writer:
        for name, path in sorted(observed.items()):
            writer.writestr(name, path.read_bytes())
    with zipfile.ZipFile(archive) as reader:
        assert reader.namelist() == sorted(observed)
        for name, path in observed.items():
            assert reader.read(name) == path.read_bytes(), name
    validation_path = HERE / 'package_validation_v1.json'
    with validation_path.open('xb') as output:
        output.write(validation_raw)
    receipt = {
        'schema': 'nabt.package-validation-preservation.v1',
        'archive': {'path': str(archive.relative_to(ROOT)), 'bytes': archive.stat().st_size,
                    'sha256': digest(archive.read_bytes()), 'entries': len(observed),
                    'all_entry_hashes_verified': True},
        'validation': {'path': str(validation_path.relative_to(ROOT)), 'sha256': digest(validation_raw)},
        'scope': 'Exact isolated wheel installation and 49 authored CLI checks. This is not an Arabic completeness evaluation, lexical acquisition proof, or external truth observation.',
        'script_sha256': digest(Path(__file__).read_bytes()),
    }
    with (HERE / 'package_validation_receipt_v1.json').open('x') as output:
        json.dump(receipt, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
