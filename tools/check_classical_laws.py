#!/usr/bin/env python3
"""Finite cross-language conformance, never a whole-Arabic completeness score."""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

EXPORTS = (
    ('classical_weak', 'exportClassicalWeak'),
    ('classical_hamza', 'exportClassicalHamza'),
    ('classical_gemination', 'exportClassicalGemination'),
    ('classical_boundary_affixes', 'exportClassicalBoundaryAffixes'),
)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def check_export(name, exported):
    module = import_module('nabt.' + name)
    expected = module.finite_export_rows()
    if type(expected) is list:
        expected = {'law_id': module.LAW_ID, 'rows': expected}
        if name == 'classical_boundary_affixes':
            expected['alphabet'] = module.ALPHABET_ID
    if wire(exported) != wire(expected):
        raise ValueError('Lean/Python finite control mismatch: ' + name)
    groups = {key: value for key, value in expected.items() if type(value) is list}
    counts = {}
    for key, rows in groups.items():
        if not rows:
            raise ValueError('Empty conformance group: ' + name + '/' + key)
        # Full rows must be unique. Explicit input identity must be unique too.
        if len({wire(row) for row in rows}) != len(rows):
            raise ValueError('Duplicate conformance rows: ' + name + '/' + key)
        identities = []
        for row in rows:
            if 'frame' in row:
                identities.append(wire((row.get('rule_id'), row['frame'])))
            else:
                identities.append(wire({k: v for k, v in row.items()
                                        if k not in {'actions', 'outputs', 'operations', 'alternatives'}}))
        if len(set(identities)) != len(rows):
            raise ValueError('Repeated conformance input: ' + name + '/' + key)
        counts[key] = len(rows)
    return {'module': name, 'law_id': module.LAW_ID, 'rules': list(module.RULE_IDS),
            'groups': counts, 'matched': sum(counts.values()),
            'export_sha256': sha256(wire(exported)).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lake', default='lake')
    p.add_argument('--export-directory', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        if args.export_directory is None:
            subprocess.run([args.lake, 'build', *(exe for _, exe in EXPORTS)],
                           cwd=ROOT / 'formal', check=True)
        results = []
        for name, exe in EXPORTS:
            raw = ((args.export_directory / (name + '.json')).read_bytes()
                   if args.export_directory else subprocess.check_output(
                       [str(ROOT / 'formal/.lake/build/bin' / exe)]))
            exported = json.loads(raw)
            results.append(check_export(name, exported))
        from nabt.classical_laws import catalog
        actual = catalog()
        if set(r for m in results for r in m['rules']) != {r['rule_id'] for r in actual['rules']}:
            raise ValueError('Conformance does not cover the installed rule-ID domain')
        report = {'schema': 'nabt.classical-law-conformance.v1', 'valid': True,
                  'rule_count': actual['rule_count'], 'groups': results,
                  'finite_controls_matched': sum(r['matched'] for r in results),
                  'scope': 'Exact declared finite control exports; not general Python/Lean equivalence or Arabic coverage.',
                  'premise_acquisition_proved': False, 'whole_arabic_complete': False}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({'valid': False, 'error': str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
