"""Exercise the repository's public generation and exact reading APIs without adding a lexicon."""
import argparse
import json
from pathlib import Path
from nabt.derivation import generate_derivation, installed_registry, read_derivation
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output",required=True,type=Path)
w=parser.parse_args().output
w.mkdir(parents=True,exist_ok=True)
out=[]
for p in installed_registry()["patterns"]:
    roots=("زرع","كتب") if p['arity']==3 else ("دحرج","بعثر")
    for root in roots:
        for ending in dict.fromkeys(["",*p['endings']]):
            generated=generate_derivation(root,p['id'],ending=ending)
            report=read_derivation(generated['surface'])
            found=any((c['root'],c['pattern_id'],c['boundary'])==(root,p['id'],ending)
                      for occurrence in report['occurrences'] for c in occurrence['candidates'])
            out.append({'pattern':p['id'],'root':root,'surface':generated['surface'],'boundary':ending,'recovered':found})
(w/'patterns_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
failed=[v for v in out if not v['recovered']]
print(len(set(v['pattern'] for v in out)),len(out),len(failed))
if failed: print(failed[:4]); raise SystemExit(1)
