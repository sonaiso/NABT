"""Map changed, tracked paths onto the existing reuse families; no linguistic verdict."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
REGISTRY="tools/entropy_framework/registry.json"
GROUPS=("runtime_paths","test_paths","doc_paths","checker_paths")


def change_map(paths,root=ROOT):
    families=json.loads((root/REGISTRY).read_bytes())["reuse"]["families"]
    index={}
    for family in families:
        for group in GROUPS:
            for path in family.get(group,[]):
                index.setdefault(path,[]).append([family["id"],group])
        for module in family["formal_modules"]:
            path="formal/"+module.replace(".","/")+".lean"
            index.setdefault(path,[]).append([family["id"],"formal_modules"])
    return [{"path":p,"family_links":index.get(p,[]),"status":"REFERENCES" if p in index else "UNMAPPED"}
            for p in sorted(set(paths))]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base",required=True)
    p.add_argument("--head",required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    import re
    if not all(re.fullmatch(r"[0-9a-f]{40}",s) for s in (args.base,args.head)):
        p.error("Expected two complete Git commit SHAs")
    data=subprocess.check_output(["git","diff","--no-renames","--name-only","-z",args.base+"..."+args.head,"--"],cwd=ROOT)
    paths=[s.decode() for s in data.split(b"\0") if s]
    rows=change_map(paths)
    out={"schema":"nabt.pr-chain-references.v1","base":args.base,"head":args.head,"files":rows,
         "semantic_closure_established":False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(f"{sum(bool(r['family_links']) for r in rows)} of {len(rows)} changed paths have existing family links")


if __name__=="__main__":main()
