#!/usr/bin/env python3
"""Complete finite control conformance; not a linguistic/acoustic benchmark."""
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
        subprocess.run([args.lake, 'build', 'exportPhonologicalModes'], cwd=ROOT / 'formal', check=True)
        exported = json.loads(subprocess.check_output([str(ROOT / 'formal/.lake/build/bin/exportPhonologicalModes')]))
    from nabt.phonological_modes import LAW_ID, Mode, Profile, _suffixes, realize, replay_policy
    if exported['law_id'] != LAW_ID:
        raise ValueError('Different phonological law')
    expected_onset_keys = {(s, v) for s in ('ibtida', 'wasl') for v in (None, 'a', 'i', 'u')}
    onset_rows = {(r['start'], r['vowel']):r['segments'] for r in exported['onsets']}
    expected_endings = {('stable',None)} | {(k,v) for k in ('short','tanwin','feminine','weak','single') for v in ('a','i','u')}
    expected_suffix_keys = {(e,p,k,v) for e in ('wasl','waqf') for p in ('standard_core','sibawayhi_attested_options') for k,v in expected_endings}
    suffix_rows = {(r['end'],r['profile'],r['ending'],r['vowel']):r['suffixes'] for r in exported['endings']}
    if (set(onset_rows) != expected_onset_keys or len(exported['onsets']) != 8 or
            set(suffix_rows) != expected_suffix_keys or len(exported['endings']) != 64):
        raise ValueError('Control export has missing or duplicate cases')
    for (end,profile,kind,vowel),suffixes in suffix_rows.items():
        actual=[list(s) for s,_ in _suffixes({'ending':kind,'vowel':vowel},Mode(end),Profile(profile))]
        if actual != suffixes:
            raise ValueError(('Suffix conformance failed',end,profile,kind,vowel))
    # Hand-transcribed control counterexamples independent of the runtime helper.
    if (onset_rows[('wasl','u')] != [] or onset_rows[('ibtida','i')] != ['ʔ','i'] or
            suffix_rows[('waqf','standard_core','feminine','u')] != [['h']] or
            suffix_rows[('waqf','standard_core','tanwin','a')] != [['a:']] or
            suffix_rows[('waqf','sibawayhi_attested_options','weak','i')] != [[],['i','h']]):
        raise ValueError('Export contradicts independently transcribed controls')
    policy=replay_policy(); count=0
    for example in policy['examples']:
        for start in ('ibtida','wasl'):
            for end in ('wasl','waqf'):
                for profile in ('standard_core','sibawayhi_attested_options'):
                    report=realize(example['example_id'],start=start,end=end,profile=profile)
                    expected=[onset_rows[(start,example['wasl_vowel'])]+example['body']+suffix
                              for suffix in suffix_rows[(end,profile,example['ending'],example['vowel'])]]
                    if [a['segments'] for a in report['alternatives']] != expected:
                        raise ValueError(('Catalogue conformance failed',example['example_id'],start,end,profile))
                    if report['written_form'] != example['written_form'] or report['deleted_radicals'] != example['deleted_radicals']:
                        raise ValueError('Source or morphology trace mutated')
                    count+=1
    print(json.dumps({'valid':True,'onset_controls':8,'ending_controls':64,
                      'catalogue_boundary_combinations':count,'source_passages':len(policy['passages']),
                      'scope':'Conditional symbolic correspondence; no acoustic or complete-Arabic claim'}))


if __name__ == '__main__':
    main()
