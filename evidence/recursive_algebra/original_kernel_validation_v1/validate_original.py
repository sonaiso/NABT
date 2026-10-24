from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/workspace/scratch/93a907621097/NABT')
SOURCE = Path('/workspace/scratch/93a907621097/recursive_import/RecursiveLicensedAlgebra.lean')
LEAN = Path('/tmp/nabt-tools/lean-4.34.1-linux/bin/lean')
OUT = ROOT / 'evidence/recursive_algebra/original_kernel_validation_v1'
OUT.mkdir(parents=True, exist_ok=False)
EXPECTED = 'bc3fe692f788d6b16bc6ec3ebe6f4c3ba94e8e269d568786097405cf41eb6805'

def sha(data): return hashlib.sha256(data).hexdigest()
def record(path):
    return {'path':str(path), 'bytes':path.stat().st_size, 'sha256':sha(path.read_bytes())}

original = SOURCE.read_bytes()
assert sha(original) == EXPECTED
names = re.findall(r'^theorem\s+([A-Za-z0-9_]+)',original.decode(),re.M)
assert len(names) == len(set(names)) == 32
commands = []

def run(name, args):
    start = datetime.now(timezone.utc).isoformat(); clock = time.monotonic()
    stdout = OUT / (name + '.stdout.log'); stderr = OUT / (name + '.stderr.log')
    with stdout.open('xb') as out, stderr.open('xb') as err:
        result = subprocess.run(args,cwd=SOURCE.parent,stdout=out,stderr=err,timeout=180)
    entry = {'name':name,'command':list(map(str,args)),'started_utc':start,
             'seconds':round(time.monotonic()-clock,3),'returncode':result.returncode,
             'stdout':record(stdout),'stderr':record(stderr)}
    commands.append(entry)
    print(json.dumps({'name':name,'returncode':result.returncode,'seconds':entry['seconds']}),flush=True)
    return result.returncode,stdout,stderr

version_code,version_path,_=run('version',[str(LEAN),'--version'])
compile_code,compile_out,compile_err=run('compile_original',[str(LEAN),str(SOURCE)])
assert compile_code==0
checks = '\n-- Independent axiom inspection; original source bytes above are unchanged.\n' + ''.join(
    '#print axioms RecursiveLicensedAlgebra.' + name + '\n' for name in names)
audit_input=OUT/'OriginalKernelAxiomAudit.lean'
with audit_input.open('xb') as target: target.write(original + checks.encode())
assert audit_input.read_bytes().startswith(original)
audit_code,audit_out,audit_err=run('axiom_audit',[str(LEAN),str(audit_input)])
assert audit_code==0
text=audit_out.read_text()
found={}
for name,block in re.findall(r"'([^']+)' depends on axioms:\s*\[([^]]*)\]",text,re.S):
    found[name]=[x.strip() for x in block.split(',') if x.strip()]
for name in re.findall(r"'([^']+)' does not depend on any axioms",text): found[name]=[]
expected_names={'RecursiveLicensedAlgebra.'+name for name in names}
assert set(found)==expected_names,(set(found)^expected_names,text)
observed=sorted({a for values in found.values() for a in values})
allowed={'propext','Quot.sound','Classical.choice'}
assert set(observed)<=allowed
assert SOURCE.read_bytes()==original
result={'schema':'nabt.recursive-algebra.original-kernel-validation.v1',
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'source':record(SOURCE),'compiler':record(LEAN),'compiler_version':version_path.read_text().strip(),
        'source_unchanged':True,'compile_original_success':compile_code==0,'axiom_audit_success':audit_code==0,
        'theorem_count':32,'theorem_axioms':found,'observed_axioms':observed,
        'custom_axioms_allowed':False,'audit_input':record(audit_input),'commands':commands,
        'ok':version_code==compile_code==audit_code==0 and set(observed)<=allowed,
        'scope':'All32 theorem declarations in the exact user-supplied original Std-only kernel. No claim that Arabic rule premises or source adapters were proved by these declarations.'}
with (OUT/'validation.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
with (OUT/'validate_original.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps({'ok':result['ok'],'theorem_count':32,'observed_axioms':observed,
                  'validation_sha256':sha((OUT/'validation.json').read_bytes())}),flush=True)
