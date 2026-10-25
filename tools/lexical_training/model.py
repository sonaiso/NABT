"""Learned evidence retrieval. Neither scores nor roots authorize a meaning."""
from collections import Counter
import math
import zlib
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

def features(text,buckets):
    values=[]
    for word in text.split():
        values.append('w:'+word)
        word='^'+word+'$'
        for n in [3,4]:
            values.extend('c:'+word[i:i+n] for i in range(len(word)-n+1))
    return Counter(zlib.crc32(x.encode())%buckets for x in values)

def encode(pairs,protocol,idf=None):
    texts=[x['query'] for x in pairs]+[x['document'] for x in pairs]
    fs=[features(s,protocol['buckets']) for s in texts]
    if idf is None:
        df=np.zeros(protocol['buckets'],dtype=np.float32);n=0
        for i,f in enumerate(fs):
            if pairs[i%len(pairs)]['split']=='train':
                df[list(f)]+=1;n+=1
        idf=np.log((n+1)/(df+1))+1
    x=np.zeros((len(fs),protocol['buckets']),dtype=np.float32)
    indices=np.zeros((len(fs),384),dtype=np.int64)
    weights=np.zeros((len(fs),384),dtype=np.float32)
    for i,f in enumerate(fs):
        row=sorted(((k,(1+math.log(v))*float(idf[k])) for k,v in f.items()),key=lambda z:(-z[1],z[0]))[:384]
        norm=math.sqrt(sum(v*v for _,v in row)) or 1
        for j,(k,v) in enumerate(row):
            indices[i,j]=k;weights[i,j]=v/norm;x[i,k]=v/norm
    return x,torch.from_numpy(indices),torch.from_numpy(weights),idf

class Retriever(nn.Module):
    def __init__(self,buckets,dim):
        super().__init__()
        self.embedding=nn.EmbeddingBag(buckets,dim,mode='sum')
        self.projection=nn.Linear(dim,dim)
        self.dropout=nn.Dropout(0.1)
        nn.init.normal_(self.embedding.weight,std=0.03)

    def forward(self,indices,weights):
        x=self.embedding(indices,per_sample_weights=weights)
        return F.normalize(self.projection(self.dropout(torch.tanh(x))),dim=-1)

def embed(model,indices,weights):
    model.eval()
    with torch.no_grad():
        return torch.cat([model(indices[i:i+256],weights[i:i+256]) for i in range(0,len(indices),256)]).numpy()
