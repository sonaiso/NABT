#!/usr/bin/env python3
"""Register a completed v5 runtime freeze without replacing historical pins.

Run only after prepare_runtime.py has produced the approved final snapshot.
No gold, prior result, old manifest, or old policy is rewritten.
"""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OLD='eda208c3e092a8185a3223ba8f0848ff6d0232aca3b8c3e94645482233d7dcb9'
OLD_SNAPSHOT='5338e35cd0575996e5df0f8d00a6319add42c610764ece7f8bc898d79a30e797'
OLD_ARCHIVE='614377594215e73cc2ecd0e3b2ce12e19da64d4dd6f8f4aa4e55e5604ef52d43'
OLD_PATH='evidence/arabic_completion_v4/code_freeze_v2.json'
NEW_PATH='evidence/arabic_completion_v5/code_freeze_v1.json'
SELECTION='arabic_completion_v5'


def replace_once(s,old,new):
    if s.count(old)!=1: raise ValueError(f'Expected one registration anchor: {old[:100]!r}')
    return s.replace(old,new,1)


def write_new(path,text):
    with path.open('x',encoding='utf-8') as out: out.write(text)


def main():
    raw=(HERE/'code_freeze_v1.json').read_bytes()
    freeze=json.loads(raw); pin=sha256(raw).hexdigest(); snap=freeze['snapshot_sha256']; arc=freeze['archive_sha256']; count=len(freeze['files'])
    if freeze['previous_runtime_manifest_sha256']!=OLD or count!=94:
        raise ValueError('Unexpected approved predecessor or runtime inventory')
    from sys import path as search_path
    search_path.insert(0,str(ROOT))
    from tools.text_evaluation.integrity import verify_code_freeze
    verify_code_freeze(HERE/'code_freeze_v1.json',ROOT)
    # Preserve every case/check/failure signature exactly. Metadata names the new runtime.
    previous=(ROOT/'evidence/arabic_completion_v4/regression_policy_v2.json').read_bytes()
    policy=deepcopy(json.loads(previous))
    policy.update(schema='nabt.arabic-completion.regression-policy.v3',
        previous_policy_sha256=sha256(previous).hexdigest(),runtime_freeze_sha256=pin,
        runtime_snapshot_sha256=snap,runtime_file_count=count,
        review_timing='Before the new frozen-runtime measurements; inherits only exact previously documented residual signatures. No new waiver.',
        scope='Identical independently frozen construction/discourse material and previous residual signatures; source inventory, phonology and imperative extension; all new failures remain failures.')
    policy_raw=json.dumps(policy,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    write_new(HERE/'regression_policy_v1.json',policy_raw)
    policy_pin=sha256(policy_raw.encode()).hexdigest()
    gate=(ROOT/'tools/arabic_completion_v4_gate.py').read_text()
    gate=gate.replace(OLD,pin).replace('evidence/arabic_completion_v4/regression_policy_v2.json','evidence/arabic_completion_v5/regression_policy_v1.json')
    gate=gate.replace('0ee8013f18b3087fd8e9dbaeb4050986389760711fdfffb12dc56edc6f20771b',policy_pin)
    gate=gate.replace('reviewed Arabic-completion v3 runtime','classical-source Arabic-completion v5 runtime')
    write_new(ROOT/'tools/arabic_completion_v5_gate.py',gate)
    post=(ROOT/'tools/arabic_coverage_postreview_v5.py').read_text().replace(OLD,pin).replace(OLD_SNAPSHOT,snap).replace(OLD_ARCHIVE,arc)
    post=post.replace("len(runtime['files']) == 83",f"len(runtime['files']) == {count}")
    post=post.replace('nabt.independent-arabic-postreview-gate.v5','nabt.independent-arabic-postreview-gate.v6')
    post=post.replace('new productive runtime and new public trace','new classical-source runtime and new public trace')
    write_new(ROOT/'tools/arabic_coverage_postreview_v6.py',post)
    # Add new entries rather than changing any historical registration.
    for name in ('word_evaluation.py','morphology_evaluation.py'):
        p=ROOT/'tools'/name;s=p.read_text()
        s=replace_once(s,'CODE_FREEZES = {\n','CODE_FREEZES = {\n    '+repr(SELECTION)+': '+repr((pin,snap,arc))+',\n')
        s=replace_once(s,'CODE_FREEZE_PATHS = {\n','CODE_FREEZE_PATHS = {\n    '+repr(SELECTION)+': ROOT / '+repr(NEW_PATH)+',\n')
        s=s.replace('version="arabic_completion_v4_review2"','version="arabic_completion_v5"')
        s=s.replace('default="arabic_completion_v4_review2"','default="arabic_completion_v5"')
        p.write_text(s)
    for name in ('construction_evaluation.py','discourse_evaluation.py','inflection_evaluation.py'):
        p=ROOT/'tools'/name;s=p.read_text(); lines=s.splitlines(keepends=True)
        index=next(i for i,l in enumerate(lines) if repr(OLD) in l or '"'+OLD+'"' in l)
        record={'snapshot_sha256':snap,'archive_sha256':arc,'file_count':count}
        if name!='inflection_evaluation.py':record['version']='0.19.0a1'
        lines.insert(index,'    '+repr(pin)+': '+repr(record)+',\n');s=''.join(lines)
        if name!='inflection_evaluation.py':
            anchor='_PRODUCTIVE_GATE_SPEC.loader.exec_module(productive_gate)\n'
            block=anchor+"_CLASSICAL_GATE_SPEC = importlib.util.spec_from_file_location(\n    'classical_completion_gate', Path(__file__).with_name('arabic_completion_v5_gate.py'))\nclassical_gate = importlib.util.module_from_spec(_CLASSICAL_GATE_SPEC)\n_CLASSICAL_GATE_SPEC.loader.exec_module(classical_gate)\n"
            s=replace_once(s,anchor,block)
            anchor="    if result['snapshot']['runtime_freeze_sha256'] == productive_gate.RUNTIME_SHA256:\n"
            suite=name.removesuffix('_evaluation.py')
            new="    if result['snapshot']['runtime_freeze_sha256'] == classical_gate.RUNTIME_SHA256:\n        return classical_gate.gate_decision('"+suite+"', result, allow_documented_boundaries)\n"+anchor
            s=replace_once(s,anchor,new)
            anchor="Path(__file__).with_name('arabic_completion_v4_gate.py'), productive_gate.POLICY_PATH):"
            new="Path(__file__).with_name('arabic_completion_v4_gate.py'), productive_gate.POLICY_PATH,\n                 Path(__file__).with_name('arabic_completion_v5_gate.py'), classical_gate.POLICY_PATH,\n                 Path(__file__).with_name('imperative_paradigm_validation.py')):"
            s=replace_once(s,anchor,new)
        s=s.replace(OLD_PATH,NEW_PATH) # Only the default path occurs in these registry modules.
        p.write_text(s)
    p=ROOT/'tools/governor_evaluation.py';s=p.read_text()
    s=replace_once(s,'APPROVED_CODE_FREEZES = {\n','APPROVED_CODE_FREEZES = {\n    '+repr(pin)+': '+repr(snap)+',\n')
    p.write_text(s.replace(OLD_PATH,NEW_PATH))
    for name in ('inflection_cli_evaluation.py','arabic_syntax_evaluation.py'):
        p=ROOT/'tools'/name;p.write_text(p.read_text().replace(OLD_PATH,NEW_PATH))
    p=ROOT/'tools/verify_construction_package.py';s=p.read_text()
    record={'selection':SELECTION,'version':'0.19.0a1','profile':SELECTION,'source_file_count':count,
            'future_operator_support':True,'snapshot_sha256':snap,'archive_sha256':arc}
    s=replace_once(s,'CODE_FREEZE_PINS = {\n','CODE_FREEZE_PINS = {\n    '+repr(pin)+': '+repr(record)+',\n')
    old_files={r['path'] for r in json.loads((ROOT/OLD_PATH).read_bytes())['files']}
    added=sorted(r['path'].removeprefix('src/') for r in freeze['files'] if r['path'] not in old_files)
    profile='RELEASE_PROFILES["arabic_completion_v5"] = {\n    **RELEASE_PROFILES["arabic_completion_v4"],\n    "extra_package_files": RELEASE_PROFILES["arabic_completion_v4"]["extra_package_files"] | '+repr(set(added))+',\n}\n'
    s=replace_once(s,'REQUIRED_PACKAGE_FILES = {\n',profile+'REQUIRED_PACKAGE_FILES = {\n')
    s=s.replace('VERSION = "0.18.0a1"','VERSION = "0.19.0a1"').replace(OLD_PATH,NEW_PATH)
    p.write_text(s)
    # Current-inventory tests move forward; explicit historical tests remain pinned.
    for name in ('test_recursive_source_bridge.py','test_arabic_evaluation.py'):
        p=ROOT/'tests'/name;s=p.read_text().replace(OLD_PATH,NEW_PATH).replace(OLD,pin).replace(OLD_SNAPSHOT,snap)
        if name=='test_recursive_source_bridge.py':s=s.replace('len(frozen["files"]), 83','len(frozen["files"]), '+str(count))
        p.write_text(s)
    p=ROOT/'tests/test_arabic_coverage_package_verifier.py';s=p.read_text().replace('VERIFIER.DEFAULT_FREEZE, "'+OLD_PATH+'"','VERIFIER.DEFAULT_FREEZE, "'+NEW_PATH+'"');p.write_text(s)
    p=ROOT/'tests/test_rational_inquiry_freeze.py';s=p.read_text()
    s=s.replace("CURRENT = ROOT / '"+OLD_PATH+"'", "PRODUCTIVE = ROOT / '"+OLD_PATH+"'\nCURRENT = ROOT / '"+NEW_PATH+"'")
    s=s.replace("MANIFEST_SHA256 = '"+OLD+"'","MANIFEST_SHA256 = '"+pin+"'")
    s=s.replace("productive = {row['path']: row for row in json.loads(CURRENT.read_text())['files']}","productive = {row['path']: row for row in json.loads(PRODUCTIVE.read_text())['files']}")
    anchor='        verify_code_freeze(CURRENT, ROOT)\n'
    block="        classical = {row['path']: row for row in json.loads(CURRENT.read_text())['files']}\n        self.assertEqual(set(classical) - set(productive), "+repr(set('src/'+x for x in added))+")\n        self.assertEqual(set(productive) - set(classical), set())\n        self.assertEqual(sha256(PRODUCTIVE.read_bytes()).hexdigest(), '"+OLD+"')\n"+anchor
    s=replace_once(s,anchor,block)
    s=s.replace("'arabic_completion_v4_review2'","'arabic_completion_v5'")
    p.write_text(s)
    oldtest=(ROOT/'tests/test_completion_v4_gate.py').read_text()
    newtest=oldtest.replace('from tools import arabic_completion_gate as old','from tools import arabic_completion_v4_gate as old').replace('from tools import arabic_completion_v4_gate as current','from tools import arabic_completion_v5_gate as current').replace('ProductiveCompletionGateTests','ClassicalCompletionGateTests').replace('after["runtime_file_count"], 83','after["runtime_file_count"], '+str(count))
    write_new(ROOT/'tests/test_completion_v5_gate.py',newtest)
    # New directed-oracle continuation, same original material and historical records.
    oracle=ROOT/'evidence/arabic_completion_v3/independent_oracle'; destination=oracle/'continuation_v5';destination.mkdir()
    for old_name,new_name in [('run_oracle_v4.py','run_oracle_v5.py'),('review_continuation_v4.py','review_continuation_v5.py'),('run_source_counterexamples_v1.py','run_source_counterexamples_v1.py'),('run_regression_v4.py','run_regression_v5.py')]:
        s=(oracle/'continuation_v4'/old_name).read_text()
        s=s.replace('run_oracle_v4.py','run_oracle_v5.py').replace('review_continuation_v4.py','review_continuation_v5.py')
        s=s.replace('runner_freeze_v4_review3.json','runner_freeze_v5.json').replace(OLD,pin).replace(OLD_PATH,NEW_PATH)
        s=s.replace('nabt.completion-regression-execution.v4','nabt.completion-regression-execution.v5')
        s=s.replace('nabt.completion-directed-oracle-execution.v4','nabt.completion-directed-oracle-execution.v5').replace('nabt.completion-directed-runner-freeze.v4','nabt.completion-directed-runner-freeze.v5').replace('nabt.completion-continuation-review.v4','nabt.completion-continuation-review.v5')
        s=s.replace('separately approved guard-only runtime','separately frozen classical-source runtime').replace('versioned productive runtime','versioned classical-source runtime')
        write_new(destination/new_name,s)
    print(json.dumps({'runtime_freeze_sha256':pin,'snapshot_sha256':snap,'archive_sha256':arc,'file_count':count,'regression_policy_sha256':policy_pin,'next':'Run checks, then freeze new oracle dependencies before its first runtime execution.'}))

if __name__=='__main__':main()
