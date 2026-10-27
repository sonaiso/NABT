"""Kernel-check proposed completeness steps; never issue Arabic coverage authority."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REVIEW = Path('evidence/completeness_review_v1/Counterexamples.lean')
EXPECTED = ['finite_generation_need_not_cover', 'a_cycle_has_distinct_models',
            'two_nonempty_classes_need_not_cover', 'set_exclusion_is_not_unconditional_xor']
ALLOWED = {'propext', 'Classical.choice', 'Quot.sound'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_result(output, report, log):
    output.parent.mkdir(parents=True, exist_ok=True)
    # A failed rerun replaces a prior success receipt. Never leave stale success
    # as the result of this invocation; publish the receipt after its log.
    output.with_suffix('.log').write_text(log, encoding='utf-8')
    with tempfile.NamedTemporaryFile(mode='w', dir=output.parent, encoding='utf-8',
                                     delete=False) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        temporary = Path(stream.name)
    temporary.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lake', default='lake')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'schema': 'nabt.completeness-review.v1', 'kernel_checked': False,
              'countermodels_checked': 0, 'whole_arabic_completeness_established': False,
              'world_truth_established': False,
              'scope': 'STATED_PREMISES_INSUFFICIENT_NOT_A_PROOF_OF_ARABIC_INCOMPLETABILITY'}
    log = ''
    try:
        inputs = [ROOT / REVIEW, ROOT / 'tools/check_completeness_review.py',
                  ROOT / 'formal/lean-toolchain', ROOT / 'formal/theorems.json',
                  ROOT / 'formal/Nabt.lean', ROOT / 'formal/lakefile.lean']
        inputs += sorted((ROOT / 'formal/Nabt').rglob('*.lean'))
        before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
        build = subprocess.run([args.lake, 'build', 'Nabt'], cwd=ROOT / 'formal',
                               check=True, capture_output=True, text=True, timeout=300)
        log += build.stdout + build.stderr
        run = subprocess.run([args.lake, 'env', 'lean', '../' + str(REVIEW)],
                             cwd=ROOT / 'formal', capture_output=True, text=True,
                             check=True, timeout=60)
        log += run.stdout + run.stderr
        rows = re.findall(r'NABT_REVIEW_THEOREM CompletenessReview\.(\w+) AXIOMS \[([^\]]*)\]', run.stdout)
        if [name for name, _ in rows] != EXPECTED or run.stdout.count('NABT_COMPLETENESS_REVIEW_OK') != 1:
            raise ValueError('incomplete or duplicated kernel audit output')
        axioms = {name: sorted(a.strip() for a in raw.split(',') if a.strip()) for name, raw in rows}
        if any(not set(values) <= ALLOWED for values in axioms.values()):
            raise ValueError('unapproved axiom')
        if any(sha(ROOT / p) != digest for p, digest in before.items()):
            raise ValueError('review inputs changed during execution')
        report.update({'kernel_checked': True, 'countermodels_checked': len(rows),
                       'theorem_axioms': axioms, 'inputs_sha256': before,
                       'review_theorems_promoted_to_language_catalogue': False})
        save_result(args.output, report, log)
        print(json.dumps({'kernel_checked': True, 'countermodels_checked': len(rows),
                          'whole_arabic_completeness_established': False}))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report.update({'kernel_checked': False, 'error': str(error)})
        if isinstance(error, subprocess.CalledProcessError):
            log += (error.stdout or '') + (error.stderr or '')
        log += '\n' + str(error) + '\n'
        save_result(args.output, report, log)
        print(json.dumps(report))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
