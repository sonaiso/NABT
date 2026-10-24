from pathlib import Path
import os,re,subprocess,json
root=Path('/workspace/scratch/ad8c550fa52d/NABT-proof-closure/formal')
driver='/workspace/scratch/ad8c550fa52d/lean-driver/lean-explicit'
env={**os.environ,'LEAN_PATH':str(root)}
done=set();records=[]
def build(name):
    if name in done:return
    p=root/(name.replace('.','/')+'.lean')
    if not p.exists():return
    for line in p.read_text().splitlines():
        if line.startswith('import '):
            for dep in line[7:].split():build(dep)
    r=subprocess.run([driver,'-o',str(p.with_suffix('.olean')),str(p)],cwd=root,env=env,capture_output=True,text=True)
    records.append({'module':name,'exit_code':r.returncode,'output':r.stdout+r.stderr})
    Path('/workspace/scratch/ad8c550fa52d/closure-formal.json').write_text(json.dumps(records,indent=2))
    print(name,r.returncode,flush=True)
    if r.returncode:print(r.stdout,r.stderr);raise SystemExit(r.returncode)
    done.add(name)
build('Nabt');build('Audit')
print('COMPLETED',len(done))
