"""Create checksums for locally produced arrays; checksums grant no authority."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.arabic_training.data import sha


def package(directory):
    results=json.loads((directory/'RESULTS.json').read_text())
    files={name:sha((directory/name).read_bytes()) for name in ('weights.npz','vocabulary.json')}
    if results['model_sha256']!=files['weights.npz']:
        raise ValueError('selected model identity changed')
    receipt=dict(schema='nabt.neural-proposal-bundle.v1',files=files,source_sha256=results['source_sha256'],
                 training_head=results['head'],torch_version=results['torch_version'],parameters=results['parameters'],
                 architecture_id=results.get('architecture','legacy-char-pool-v1'),
                 authority='NONE',purpose='Unverified morphology proposals; no proof kernel activation',
                 architecture='word48 + char16/conv48 + bidirectional LSTM64 + categorical/affix heads')
    (directory/'bundle.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    package(p.parse_args().directory)
