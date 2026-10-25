#!/usr/bin/env python3
"""Train/replay a surface model against Qatr reading sets computed by native Lean."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['train','replay'])
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--lean',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,default=ROOT/'evidence/qatr_lean_training/protocol_v1.json')
    args=parser.parse_args()
    from tools.qatr_training.experiment import train,replay
    if args.mode=='train':train(args.source,args.lean,args.output_dir,args.protocol)
    else:print(json.dumps(replay(args.source,args.lean,args.output_dir),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
