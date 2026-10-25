"""Source-preserving neural proposals. This module grants no NABT authority."""
import json
from pathlib import Path
import re
import unicodedata

import torch
from .data import TASKS, sha, source_constraints
from .experiment import encode, collate
from .model import MorphologyModel, load_weights


def load_bundle(directory):
    directory=Path(directory)
    receipt=json.loads((directory/'bundle.json').read_text())
    for name in ('weights.npz','vocabulary.json'):
        if sha((directory/name).read_bytes()) != receipt['files'][name]:
            raise ValueError('model bundle checksum mismatch')
    vocab=json.loads((directory/'vocabulary.json').read_text())
    architecture=receipt.get('architecture_id','legacy-char-pool-v1')
    if architecture=='char-valid-mask-v2':
        from .model_v2 import MaskedMorphologyModel
        model=MaskedMorphologyModel(vocab)
    elif architecture=='legacy-char-pool-v1':
        model=MorphologyModel(vocab)
    else:
        raise ValueError('unsupported model architecture')
    load_weights(model,directory/'weights.npz')
    model.eval()
    return model,vocab,receipt


@torch.no_grad()
def propose(raw, model, vocab, receipt):
    result=dict(schema='nabt.neural-morphology-proposals.v1',input_sha256=sha(raw),
                input_bytes=len(raw),model_sha256=receipt['files']['weights.npz'],
                authority='NONE',alternatives_complete=False,calibrated_probabilities=False,
                world_truth_established=False,readings_licensed=False,tokens=[])
    if len(raw)>16384:
        return dict(result,status='RESOURCE_LIMIT',reason='input byte budget 16384')
    try:
        text=raw.decode('utf-8',errors='strict')
    except UnicodeDecodeError:
        return dict(result,status='INVALID_INPUT',reason='UTF-8 required')
    matches=list(re.finditer(r'\S+',text))
    if not matches:
        return dict(result,status='INVALID_INPUT',reason='no surface tokens')
    if len(matches)>512 or any(len(m.group())>32 for m in matches):
        return dict(result,status='RESOURCE_LIMIT',reason='512 tokens / 32 characters per token')
    # Exactly one context per input line, with whitespace preserved by offsets.
    lines={}
    for m in matches:
        line=text.count('\n',0,m.start())
        lines.setdefault(line,[]).append(m)
    for line,ms in lines.items():
        words=[dict(text=m.group(),labels=dict.fromkeys(TASKS),affixes=None) for m in ms]
        example=dict(id=str(line),words=words)
        items=encode([example],vocab)
        w,c,lengths,*_=collate(items,len(vocab['affixes']))
        logits=model(w,c,lengths)
        probabilities={t:torch.softmax(logits[t][0],dim=-1).tolist() for t in TASKS}
        affix_scores=torch.sigmoid(logits['affixes'][0]).tolist()
        for i,m in enumerate(ms):
            begin=len(text[:m.start()].encode()); end=len(text[:m.end()].encode())
            word=m.group()
            token=dict(text=word,start_byte=begin,end_byte=end,text_sha256=sha(raw[begin:end]),
                       unseen_surface=word not in vocab['words'],authority='NONE')
            if (not re.search('[\u064b-\u0652]',word)
                    or not any(unicodedata.category(c).startswith('L') for c in word)
                    or not all('\u0600'<=c<='\u06ff' and unicodedata.category(c)[0] in 'LM' for c in word)):
                result['tokens'].append(dict(token,status='UNKNOWN_INPUT_DOMAIN',candidates=None))
                continue
            candidates={t:sorted([dict(label=label,score=score) for label,score in zip(vocab['labels'][t],probabilities[t][i],strict=True)],key=lambda x:(-x['score'],x['label'])) for t in TASKS}
            top={t:candidates[t][0]['label'] for t in TASKS}
            top['affixes']=[a for a,p in zip(vocab['affixes'],affix_scores[i],strict=True) if p>=0.5]
            result['tokens'].append(dict(token,status='UNVERIFIED_MORPHOLOGY_PROPOSAL',
                                         top=top,candidates=candidates,
                                         affix_scores=dict(zip(vocab['affixes'],affix_scores[i],strict=True)),
                                         review_obligations=source_constraints(top['tag'],top['declension'],top['case_mood'])))
    return dict(result,status='UNVERIFIED_MORPHOLOGY_PROPOSAL')
