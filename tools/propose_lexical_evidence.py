#!/usr/bin/env python3
"""Rank pinned Maqayis evidence for a prose gloss; never license a meaning.

If the root is already known, use an exact dictionary index instead. The
default stays lexical cosine because neither training run established a win.
"""
import argparse
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.lexical_training.data import ROOT,paired_data,normalize,digest,MAQAYIS_SHA,MAQAYIS_REV

def main(a):
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
    p.add_argument('--lisan',type=Path,required=True);p.add_argument('--top-k',type=int,default=5)
    p.add_argument('--experimental-weights',type=Path)
    print(json.dumps(main(p.parse_args()),ensure_ascii=False,indent=2))
