#!/usr/bin/env python3
"""Exercise v6 interfaces in an already verified installed wheel, outside checkout."""
from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--package-validation', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    package = json.loads(args.package_validation.read_bytes())
    if package['version'] != '0.20.0a1':
        raise ValueError('Expected the v6 installed package')
    python = Path(package['isolation']['venv']) / 'bin/python'
    cwd = Path(package['isolation']['cwd'])
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    logs = output / 'logs'; logs.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
    rows = []

    def run(label, argv, code, check):
        proc = subprocess.run([str(python), '-I', '-m', 'nabt', *map(str, argv)],
                              cwd=cwd, env=env, capture_output=True)
        (logs / (label + '.stdout')).write_bytes(proc.stdout)
        (logs / (label + '.stderr')).write_bytes(proc.stderr)
        data = json.loads(proc.stdout if proc.returncode == 0 else proc.stderr)
        passed = proc.returncode == code and check(data)
        rows.append({'check': label, 'passed': passed, 'expected_exit': code,
                     'actual_exit': proc.returncode, 'argv': list(map(str, argv))})
        if not passed:
            raise ValueError('Installed interface failed: ' + label)
        return data

    def write(name, value):
        path = cwd / name
        path.write_text(json.dumps(value, ensure_ascii=False))
        return path

    run('catalog', ['classical-laws'], 0,
        lambda d: d['rule_count'] == 24 and d['whole_book_completeness'] is False)
    frame = write('v6-hamza-frame.json', {'root': ['ء', 'ك', 'ل'], 'profile': 'all_attested'})
    receipt = run('hamza-alternatives', ['classical-transform', 'HAMZA-LEXICAL-COMMAND', frame], 0,
                  lambda d: [a['morphophonemes'] for a in d['result']['alternatives']] == [['ك', 'ل'], ['ء', 'و', 'ك', 'ل']]
                  and d['grants_language_license'] is False)
    document = write('v6-receipt.json', receipt)
    run('receipt-replay', ['verify-classical-transform', document], 0,
        lambda d: d['valid'] is True and d['grants_language_license'] is False)
    bad = deepcopy(receipt); bad['result']['alternatives'].pop()
    run('missing-alternative', ['verify-classical-transform', write('v6-missing.json', bad)], 2,
        lambda d: d['code'] == 'CLASSICAL_RECEIPT_MISMATCH')
    bad = deepcopy(receipt); bad['grants_language_license'] = True
    run('forged-authority', ['verify-classical-transform', write('v6-authority.json', bad)], 2,
        lambda d: d['code'] == 'CLASSICAL_RECEIPT_MISMATCH')
    run('unknown-rule', ['classical-transform', 'UNKNOWN', frame], 3,
        lambda d: d['status'] == 'DEFER')
    run('boolean-carrier', ['classical-transform', 'HAMZA-LEXICAL-COMMAND',
        write('v6-bool.json', {'root': [True, 'ك', 'ل'], 'profile': 'all_attested'})], 2,
        lambda d: d['status'] == 'REJECT')
    duplicate = cwd / 'v6-duplicate.json'
    duplicate.write_text('{"root":[],"root":[],"profile":"all_attested"}')
    run('duplicate-json-key', ['classical-transform', 'HAMZA-LEXICAL-COMMAND', duplicate], 2,
        lambda d: d['code'] == 'DUPLICATE_JSON_KEY')
    weak = {'cells': [['ي', 'a'], ['و', '0'], ['ع', 'i'], ['د', 'u']], 'index': 1,
            'context': 'simple_imperfect', 'position': 'fa', 'origin': 'original', 'lexeme': 'وعد'}
    run('weak-operator', ['classical-transform', 'WEAK-INITIAL-WAW', write('v6-weak.json', weak)], 0,
        lambda d: d['result']['alternatives'][0]['cells'] == [['ي', 'a'], ['ع', 'i'], ['د', 'u']])
    ana = {'segments': ['ء', 'a', 'ن', 'a:'], 'start': 'ibtida', 'end': 'wasl',
           'analysis': 'speaker_pronoun', 'profile': 'both'}
    run('ana-alternatives', ['classical-transform', 'MUGHNI-ANA-BOUNDARY', write('v6-ana.json', ana)], 0,
        lambda d: [a['segments'] for a in d['result']['alternatives']] == [['ء', 'a', 'ن', 'a'], ['ء', 'a', 'ن']])
    gem = {'prefix': [['ٱ', 'u'], ['ر', 's']], 'first': ['د', 'u'], 'second': ['د', 's'],
           'suffix': [], 'context': 'command', 'dialect': 'hijaz'}
    run('gemination-dialect', ['classical-transform', 'GEM-JUSSIVE-VARIANTS', write('v6-gem.json', gem)], 0,
        lambda d: [a['operation'] for a in d['result']['alternatives']] == ['split'])
    ana['end'] = 'waqf'
    run('partial-profile-retained', ['classical-transform', 'MUGHNI-ANA-BOUNDARY', write('v6-ana-partial.json', ana)], 0,
        lambda d: d['result']['alternatives_complete_within_requested_profile'] is False
        and bool(d['result']['unresolved_profiles']))
    result = {'valid': True, 'version': package['version'], 'checks': len(rows), 'passed': len(rows),
              'failed': 0, 'package_validation_sha256': sha256(args.package_validation.read_bytes()).hexdigest(),
              'python': str(python), 'cwd': str(cwd), 'rows': rows,
              'scope': 'Installed interfaces and authority boundaries, not Arabic accuracy.'}
    (output / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('valid', 'version', 'checks', 'passed', 'failed')}))


if __name__ == '__main__':
    main()
