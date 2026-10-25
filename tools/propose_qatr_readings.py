#!/usr/bin/env python3
"""Propose, without acceptance authority, Qatr reading sets for an exact text span."""
import argparse
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--text',required=True);p.add_argument('--target',type=int,required=True)
    p.add_argument('--lean',type=Path,required=True)
    p.add_argument('--model-dir',type=Path,default=ROOT/'evidence/qatr_lean_training/run_01')
    a=p.parse_args()
    if len(a.text.encode())>1048576:p.error('text exceeds 1 MiB')
    spans=list(re.finditer(r'\S+',a.text))
    if len(spans)>512:p.error('text exceeds 512 tokens')
    if not 0<=a.target<len(spans):p.error('target must identify a token')
    if len(spans[a.target].group())>32:p.error('target exceeds the trained 32-character scope')
    import torch
    from tools.arabic_training.data import sha
    from tools.arabic_training.model import load_weights
    from tools.qatr_training.data import export_teacher,index_teacher
    from tools.qatr_training.experiment import encode,collate
    from tools.qatr_training.model import QatrModel
    from tools.qatr_training.proposal import project_ranking
    teacher=export_teacher(a.lean)
    if teacher!=json.loads((a.model_dir/'lean_teacher.json').read_text()):
        raise ValueError('native teacher does not match model protocol')
    result=json.loads((a.model_dir/'RESULTS.json').read_text())
    if sha((a.model_dir/'weights.npz').read_bytes())!=result['weights_sha256']:
        raise ValueError('model weights changed')
    vocab=json.loads((a.model_dir/'vocab.json').read_text())
    torch.set_num_threads(result['protocol']['threads'])
    model=QatrModel(vocab);load_weights(model,a.model_dir/'weights.npz');model.eval()
    example=dict(id='proposal',words=[dict(text=m.group(),qatr=None,case=None) for m in spans])
    words,chars,lengths,_,_=collate(encode([example],vocab))
    with torch.no_grad():reading_logits,case_logits=model(words,chars,lengths)
    label=vocab['readings'][int(reading_logits[0,a.target].argmax())]
    proposed=project_ranking(index_teacher(teacher)[label],case_logits[0,a.target].tolist())
    span=spans[a.target]
    proposed.update(text=a.text,text_sha256=sha(a.text.encode()),
                    target_start_byte=len(a.text[:span.start()].encode()),
                    target_end_byte=len(a.text[:span.end()].encode()),
                    proposed_observation=label,model_sha256=result['weights_sha256'])
    print(json.dumps(proposed,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
