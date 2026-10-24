"""Run the expanded trained model without installing PyTorch into NABT runtime."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model-dir',type=Path,default=ROOT/'evidence/source_morphology_training/run_02')
    p.add_argument('--text-file',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    import torch
    from tools.arabic_training.proposal import load_bundle,propose
    torch.set_num_threads(2)
    model,vocab,receipt=load_bundle(args.model_dir)
    with args.text_file.open('rb') as stream:
        raw=stream.read(16385)
    result=propose(raw,model,vocab,receipt)
    if args.text_file.stat().st_size>16384:
        # Do not present the prefix digest as the full input's identity.
        result.update(input_sha256=None,input_bytes=args.text_file.stat().st_size)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')
    return 2 if result['status'] in ('INVALID_INPUT','RESOURCE_LIMIT') else 0


if __name__=='__main__':
    raise SystemExit(main())
