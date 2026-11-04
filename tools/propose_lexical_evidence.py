#!/usr/bin/env python3
"""Rank source evidence or installed senses for a gloss; never license a meaning.

Dictionary-entry retrieval defaults to lexical cosine. Optional sense mode
requires an explicit root and retains every installed sense for native replay.
"""
import argparse
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.lexical_training.data import ROOT,paired_data,normalize,digest,MAQAYIS_SHA,MAQAYIS_REV

def main(a):
    if getattr(a,'sense_model',None) is not None:
        if a.lisan is not None or a.experimental_weights is not None:
            raise ValueError('sense mode cannot be mixed with dictionary-entry mode')
        from tools.lexical_training.senses import propose
        return propose(a.text,a.root,a.sense_model,a.target)
    if a.lisan is None:
        raise ValueError('--lisan is required for dictionary-entry retrieval')
    if getattr(a,'root',None) is not None or getattr(a,'target',[]):
        raise ValueError('--root/--target require --sense-model')
    import numpy as np
    from tools.lexical_training.model import encode
    import torch
    torch.set_num_threads(4)
    if not 1<=a.top_k<=50:raise ValueError('top-k must be 1..50')
    if not a.text or len(a.text.encode())>8192:raise ValueError('nonempty query at most 8192 UTF8 bytes')
    pairs=paired_data(a.lisan);run=ROOT/'evidence/lexical_denotation/run_01'
    p=json.loads((run/'protocol.json').read_text());idf=np.load(run/'idf.npy',allow_pickle=False)
    query=' '.join(re.findall('[ء-غف-ي]+',normalize(a.text))[:128])
    if not query:raise ValueError('no Arabic retrieval features')
    # No gold/root identity is accepted from the query.
    extra={'query':query,'document':query,'split':'query'}
    x,_,_,_=encode(pairs+[extra],p,idf);n=len(pairs)+1
    q=x[n-1];gallery=x[n:n+len(pairs)]
    if a.experimental_weights:
        w=np.exp(np.clip(np.load(a.experimental_weights,allow_pickle=False),-2,2)/2)
        if w.shape!=(p['buckets'],) or not np.isfinite(w).all():raise ValueError('invalid weight shape/values')
        q=q*w;q=q/(np.linalg.norm(q) or 1);gallery=gallery*w
        gallery=gallery/np.maximum(np.linalg.norm(gallery,axis=1,keepdims=True),1e-12)
    scores=gallery@q;order=np.argsort(-scores,kind='stable')[:a.top_k]
    raw=(ROOT/'evidence/classical_language/sources/maqayis.txt').read_bytes()
    catalog=json.loads((ROOT/'evidence/lexical_denotation/catalog.json').read_text())
    rows=[]
    for i in order:
        pair=pairs[i];entry=pair['maqayis'];start,end=entry['start_byte'],entry['end_byte']
        # Preserve the complete bounded source entry, not a model-generated quote.
        rows.append({'root_index':pair['key'],'score':float(scores[i]),'work':'maqayis',
          'revision':MAQAYIS_REV,'source_sha256':MAQAYIS_SHA,'start_byte':start,'end_byte':end,
          'entry_sha256':digest(raw[start:end]),'source_entry':raw[start:end].decode(),
          'installed_senses':[s for s in catalog['senses'] if normalize(s['root'])==pair['key']],
          'sense_equivalence':'UNMEASURED'})
    return {'schema':'nabt.lexical-evidence-proposal.v1','input':a.text,'input_domain':'prose gloss retrieval',
      'ranker':'experimental diagonal weights' if a.experimental_weights else 'lexical cosine baseline',
      'authority':'NONE','reading_licensed':False,'all_readings_enumerated':False,
      'world_truth_asserted':False,'candidate_gallery_size':len(pairs),'proposals':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--text',required=True)
    p.add_argument('--lisan',type=Path);p.add_argument('--top-k',type=int,default=5,help='dictionary-entry mode only; sense mode retains every alternative')
    p.add_argument('--experimental-weights',type=Path)
    p.add_argument('--sense-model',type=Path,help='optional text-to-sense ranker; retains every installed root sense')
    p.add_argument('--root',help='explicit dictionary root for sense mode; not inferred')
    p.add_argument('--target',action='append',default=[],help='explicit component for the existing conditional Lean check')
    p.add_argument('--verify',type=Path,help='replay a sense report against independently supplied text/root/target/model')
    args=p.parse_args()
    if args.verify is not None and args.sense_model is None:
        p.error('--verify requires --sense-model')
    result=main(args)
    if args.verify is not None:
        from tools.lexical_testimony import _strict_json
        if args.verify.stat().st_size > 2_000_000:
            p.error('report exceeds byte limit')
        expected=_strict_json(args.verify.read_bytes())
        if (json.dumps(expected,sort_keys=True,ensure_ascii=False,allow_nan=False)
                != json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False)):
            p.error('report differs from fresh replay')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if 'conditional_testimony' in result and not result['conditional_testimony']['native_checked']:
        raise SystemExit(2)
