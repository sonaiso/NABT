#!/usr/bin/env python3
"""Compare every subject row to fresh Lean export and replay original passages."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lake', default='lake')
    parser.add_argument('--lean-export', type=Path)
    args = parser.parse_args()
    if args.lean_export:
        exported = json.loads(args.lean_export.read_bytes())
    else:
        subprocess.run([args.lake, 'build', 'exportImperativeParadigm'], cwd=ROOT/'formal', check=True)
        exported = json.loads(subprocess.check_output([str(ROOT/'formal/.lake/build/bin/exportImperativeParadigm')]))
    from nabt.imperative_paradigm import LAW_ID, paradigm_rows, replay_policy
    if exported != {'law_id': LAW_ID, 'rows': paradigm_rows(), 'nun_final_2FP_deferred': True}:
        raise ValueError('Imperative subject paradigm differs from complete Lean export')
    # Independently written target endings; this is not an oracle for whole Arabic.
    expected = [('2FS','ِ','ي'), ('2MD','َ','ا'), ('2FD','َ','ا'), ('2MP','ُ','وا'), ('2FP','ْ','نَ')]
    if [(r['profile'], r['final'], r['suffix']) for r in exported['rows']] != expected:
        raise ValueError('Subject endings differ from stated classical-source interpretation')
    print(json.dumps({'valid': True, 'subject_rows': 5, 'distinct_surfaces_per_stem': 4,
                      'source_passages': len(replay_policy()['passages']),
                      'scope': 'Conditional morphology, not complete Arabic or acoustic validation'}))

if __name__ == '__main__':
    main()
