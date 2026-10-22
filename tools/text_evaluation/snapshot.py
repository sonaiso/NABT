import hashlib
import json
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[2]
out=Path(sys.argv[1])
candidates=sorted(set(root.glob('src/**/*.py')) | set(root.glob('src/**/*.json')) | set(root.glob('src/**/*.txt')) | {root/'pyproject.toml'})
# Generated packaging indices are absent in fresh checkouts and can be
# rewritten by a build. Future snapshots pin authoritative source/config/data
# only; historical snapshots are kept unchanged.
excluded=[path for path in candidates if any(part.endswith(('.egg-info','.dist-info')) for part in path.relative_to(root).parts[:-1])]
paths=[path for path in candidates if path not in excluded]
manifest={
    'schema':'nabt-independent-evaluation-code-freeze-v1',
    'utc':datetime.now(timezone.utc).isoformat(),
    'repository_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
    'repository_status':subprocess.check_output(['git','status','--short'],cwd=root,text=True),
    'file_selection':'Authoritative source, configuration, and packaged data; generated .egg-info/.dist-info metadata is excluded.',
    'excluded_build_metadata':[str(path.relative_to(root)) for path in excluded],
    'files':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths],
}
manifest['snapshot_sha256']=hashlib.sha256(json.dumps(manifest['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
archive=out.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as tar:
    for path in paths:
        tar.add(path,arcname=str(path.relative_to(root)),recursive=False)
manifest['archive_filename']=archive.name
manifest['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='files'},ensure_ascii=False,indent=2))
