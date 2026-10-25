#!/usr/bin/env python3
"""Register the v6 snapshot while retaining all historical gold and pins.

Run once after review and before the new measurements. No observed freeze is
overwritten, and no additional linguistic failure signature is waived.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD_PATH = 'evidence/arabic_completion_v5/code_freeze_v1.json'
NEW_PATH = 'evidence/arabic_completion_v6/code_freeze_v1.json'
OLD = '06f4f774c5637936b41be95360b07ad6cfe8aaeaa9fee1514396db501112ce57'
SELECTION = 'arabic_completion_v6'


def once(s, a, b):
    if s.count(a) != 1:
        raise ValueError('Expected unique registration anchor: ' + a[:100])
    return s.replace(a, b, 1)


def fresh(path, s):
    with path.open('x', encoding='utf-8') as out:
        out.write(s)


def main():
    raw = (ROOT / NEW_PATH).read_bytes()
    f = json.loads(raw)
    previous_raw = (ROOT / OLD_PATH).read_bytes()
    previous = json.loads(previous_raw)
    assert sha256(previous_raw).hexdigest() == OLD
    assert f['previous_runtime_manifest_sha256'] == OLD
    pin, snap, arc, count = sha256(raw).hexdigest(), f['snapshot_sha256'], f['archive_sha256'], len(f['files'])
    assert count == 99
    sys.path.insert(0, str(ROOT))
    from tools.text_evaluation.integrity import verify_code_freeze
    verify_code_freeze(ROOT / NEW_PATH, ROOT)
    before = (ROOT / 'evidence/arabic_completion_v5/regression_policy_v1.json').read_bytes()
    policy = deepcopy(json.loads(before))
    policy.update(schema='nabt.arabic-completion.regression-policy.v4',
                  previous_policy_sha256=sha256(before).hexdigest(), runtime_freeze_sha256=pin,
                  runtime_snapshot_sha256=snap, runtime_file_count=count,
                  review_timing='Before the new measurements; no new waiver or gold changes.',
                  scope='Conditional classical operators; identical historical cases and residual signatures.')
    policy_text = json.dumps(policy, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    fresh(HERE / 'regression_policy_v1.json', policy_text)
    gate = (ROOT / 'tools/arabic_completion_v5_gate.py').read_text()
    gate = gate.replace(OLD, pin).replace('evidence/arabic_completion_v5/regression_policy_v1.json',
                                       'evidence/arabic_completion_v6/regression_policy_v1.json')
    gate = gate.replace(sha256(before).hexdigest(), sha256(policy_text.encode()).hexdigest())
    gate = gate.replace('Arabic-completion v5 runtime', 'Arabic-completion v6 runtime')
    fresh(ROOT / 'tools/arabic_completion_v6_gate.py', gate)
    post = (ROOT / 'tools/arabic_coverage_postreview_v6.py').read_text()
    post = post.replace(OLD, pin).replace(previous['snapshot_sha256'], snap).replace(previous['archive_sha256'], arc)
    post = post.replace("len(runtime['files']) == 94", f"len(runtime['files']) == {count}")
    post = post.replace('nabt.independent-arabic-postreview-gate.v6', 'nabt.independent-arabic-postreview-gate.v7')
    fresh(ROOT / 'tools/arabic_coverage_postreview_v7.py', post)
    for name in ('word_evaluation.py', 'morphology_evaluation.py'):
        p = ROOT / 'tools' / name
        s = p.read_text()
        s = once(s, 'CODE_FREEZES = {\n', 'CODE_FREEZES = {\n    ' + repr(SELECTION) + ': ' + repr((pin, snap, arc)) + ',\n')
        s = once(s, 'CODE_FREEZE_PATHS = {\n', 'CODE_FREEZE_PATHS = {\n    ' + repr(SELECTION) + ': ROOT / ' + repr(NEW_PATH) + ',\n')
        s = s.replace('version="arabic_completion_v5"', 'version="arabic_completion_v6"').replace('default="arabic_completion_v5"', 'default="arabic_completion_v6"')
        p.write_text(s)
    for name in ('construction_evaluation.py', 'discourse_evaluation.py', 'inflection_evaluation.py'):
        p = ROOT / 'tools' / name
        s = p.read_text()
        lines = s.splitlines(keepends=True)
        index = next(i for i, line in enumerate(lines) if repr(OLD) in line or '"' + OLD + '"' in line)
        row = {'snapshot_sha256': snap, 'archive_sha256': arc, 'file_count': count}
        if name != 'inflection_evaluation.py':
            row['version'] = '0.20.0a1'
        lines.insert(index, '    ' + repr(pin) + ': ' + repr(row) + ',\n')
        s = ''.join(lines)
        if name != 'inflection_evaluation.py':
            anchor = '_CLASSICAL_GATE_SPEC.loader.exec_module(classical_gate)\n'
            s = once(s, anchor, anchor + "_EXTENSION_GATE_SPEC = importlib.util.spec_from_file_location(\n    'classical_extension_gate', Path(__file__).with_name('arabic_completion_v6_gate.py'))\nextension_gate = importlib.util.module_from_spec(_EXTENSION_GATE_SPEC)\n_EXTENSION_GATE_SPEC.loader.exec_module(extension_gate)\n")
            anchor = "    if result['snapshot']['runtime_freeze_sha256'] == classical_gate.RUNTIME_SHA256:\n"
            suite = name.removesuffix('_evaluation.py')
            s = once(s, anchor, "    if result['snapshot']['runtime_freeze_sha256'] == extension_gate.RUNTIME_SHA256:\n        return extension_gate.gate_decision('" + suite + "', result, allow_documented_boundaries)\n" + anchor)
            anchor = "Path(__file__).with_name('arabic_completion_v5_gate.py'), classical_gate.POLICY_PATH,"
            s = once(s, anchor, anchor + "\n                 Path(__file__).with_name('arabic_completion_v6_gate.py'), extension_gate.POLICY_PATH,")
        p.write_text(s.replace(OLD_PATH, NEW_PATH))
    p = ROOT / 'tools/governor_evaluation.py'
    s = once(p.read_text(), 'APPROVED_CODE_FREEZES = {\n', 'APPROVED_CODE_FREEZES = {\n    ' + repr(pin) + ': ' + repr(snap) + ',\n')
    p.write_text(s.replace(OLD_PATH, NEW_PATH))
    for name in ('inflection_cli_evaluation.py', 'arabic_syntax_evaluation.py'):
        p = ROOT / 'tools' / name
        p.write_text(p.read_text().replace(OLD_PATH, NEW_PATH))
    p = ROOT / 'tools/verify_construction_package.py'
    s = p.read_text()
    row = {'selection': SELECTION, 'version': '0.20.0a1', 'profile': SELECTION, 'source_file_count': count,
           'future_operator_support': True, 'snapshot_sha256': snap, 'archive_sha256': arc}
    s = once(s, 'CODE_FREEZE_PINS = {\n', 'CODE_FREEZE_PINS = {\n    ' + repr(pin) + ': ' + repr(row) + ',\n')
    old_paths = {r['path'] for r in previous['files']}
    added = {r['path'].removeprefix('src/') for r in f['files'] if r['path'] not in old_paths}
    profile = 'RELEASE_PROFILES["arabic_completion_v6"] = {\n    **RELEASE_PROFILES["arabic_completion_v5"],\n    "extra_package_files": RELEASE_PROFILES["arabic_completion_v5"]["extra_package_files"] | ' + repr(added) + ',\n}\n'
    s = once(s, 'REQUIRED_PACKAGE_FILES = {\n', profile + 'REQUIRED_PACKAGE_FILES = {\n')
    p.write_text(s.replace('VERSION = "0.19.0a1"', 'VERSION = "0.20.0a1"').replace(OLD_PATH, NEW_PATH))
    for name in ('test_recursive_source_bridge.py', 'test_arabic_evaluation.py'):
        p = ROOT / 'tests' / name
        s = p.read_text().replace(OLD_PATH, NEW_PATH).replace(OLD, pin).replace(previous['snapshot_sha256'], snap)
        if name == 'test_recursive_source_bridge.py':
            s = s.replace('len(frozen["files"]), 94', f'len(frozen["files"]), {count}')
        p.write_text(s)
    p = ROOT / 'tests/test_arabic_coverage_package_verifier.py'
    p.write_text(p.read_text().replace('VERIFIER.DEFAULT_FREEZE, "' + OLD_PATH + '"', 'VERIFIER.DEFAULT_FREEZE, "' + NEW_PATH + '"'))
    p = ROOT / 'tests/test_rational_inquiry_freeze.py'
    s = p.read_text().replace("CURRENT = ROOT / '" + OLD_PATH + "'", "CLASSICAL = ROOT / '" + OLD_PATH + "'\nCURRENT = ROOT / '" + NEW_PATH + "'")
    s = s.replace("MANIFEST_SHA256 = '" + OLD + "'", "MANIFEST_SHA256 = '" + pin + "'")
    s = s.replace("classical = {row['path']: row for row in json.loads(CURRENT.read_text())['files']}", "classical = {row['path']: row for row in json.loads(CLASSICAL.read_text())['files']}")
    anchor = '        verify_code_freeze(CURRENT, ROOT)\n'
    block = "        extended = {row['path']: row for row in json.loads(CURRENT.read_text())['files']}\n        self.assertEqual(set(extended) - set(classical), " + repr({'src/' + x for x in added}) + ")\n        self.assertEqual(set(classical) - set(extended), set())\n        self.assertEqual(sha256(CLASSICAL.read_bytes()).hexdigest(), '" + OLD + "')\n" + anchor
    s = once(s, anchor, block).replace("'arabic_completion_v5'", "'arabic_completion_v6'")
    p.write_text(s)
    test = (ROOT / 'tests/test_completion_v5_gate.py').read_text()
    test = test.replace('from tools import arabic_completion_v4_gate as old', 'from tools import arabic_completion_v5_gate as old').replace('from tools import arabic_completion_v5_gate as current', 'from tools import arabic_completion_v6_gate as current').replace('ClassicalCompletionGateTests', 'ClassicalExtensionGateTests').replace('after["runtime_file_count"], 94', f'after["runtime_file_count"], {count}')
    fresh(ROOT / 'tests/test_completion_v6_gate.py', test)
    oracle = ROOT / 'evidence/arabic_completion_v3/independent_oracle'
    dest = oracle / 'continuation_v6'
    dest.mkdir()
    for name in ('run_oracle_v5.py', 'review_continuation_v5.py', 'run_source_counterexamples_v1.py', 'run_regression_v5.py'):
        text = (oracle / 'continuation_v5' / name).read_text()
        text = text.replace('run_oracle_v5.py', 'run_oracle_v6.py').replace('review_continuation_v5.py', 'review_continuation_v6.py').replace('runner_freeze_v5.json', 'runner_freeze_v6.json').replace(OLD, pin).replace(OLD_PATH, NEW_PATH)
        for stem in ('regression-execution', 'directed-oracle-execution', 'directed-runner-freeze', 'continuation-review'):
            text = text.replace('nabt.completion-' + stem + '.v5', 'nabt.completion-' + stem + '.v6')
        fresh(dest / name.replace('_v5.py', '_v6.py'), text)
    for name in ('Makefile', '.github/workflows/ci.yml'):
        p = ROOT / name
        s = p.read_text().replace(OLD_PATH, NEW_PATH).replace('arabic_completion_v5', 'arabic_completion_v6').replace('arabic_coverage_postreview_v6.py', 'arabic_coverage_postreview_v7.py').replace('continuation_v5/run_regression_v5.py', 'continuation_v6/run_regression_v6.py')
        p.write_text(s)
    print(json.dumps({'runtime_freeze_sha256': pin, 'snapshot_sha256': snap, 'archive_sha256': arc, 'file_count': count}))


if __name__ == '__main__':
    main()
