"""Fresh Lean/table equality and exhaustive finite independent dispatch oracle."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from tools.grammar_catalog.orchestration import table,dispatch,TABLE_SHA256

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args()
    installed=table()
    fresh=json.loads(subprocess.check_output([str(ROOT/'formal/.lake/build/bin/exportCognitiveDispatch')]))
    if fresh!=installed:raise ValueError('Fresh Lean export differs from frozen dispatch table')
    required=({0,1,2,3},{0,1,2,3,4,5},{0,1,2,3,6},{0,1,2,3,7})
    count=0
    for c in range(6):
        for t in range(6):
            for profile,needs in enumerate(required):
                for mask in range(256):
                    present={n for n in range(8) if mask & (1<<n)}
                    if (dispatch(c,t,profile,mask,policy=installed)=='DISPATCH')!=(c==t and needs<=present):
                        raise ValueError('Dispatch mismatch')
                    count+=1
    result={'ok':True,'law_id':installed['law_id'],'table_sha256':TABLE_SHA256,'cases':count,
            'scope':'6 current layers x 6 target layers x 4 policy profiles x 256 Boolean masks',
            'source_premise_acquisition_proved':False,'general_python_lean_refinement_proved':False}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
