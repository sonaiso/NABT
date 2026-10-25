"""Fetch the exact pinned MASAQ repository copy without rewriting its bytes."""
import argparse
from pathlib import Path
import sys
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.arabic_training.data import DATA_BYTES,DATA_SHA256,sha

URL='https://raw.githubusercontent.com/Saleh1967/Alghanem/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/corpora/MASAQ.csv'


def fetch(output):
    if output.exists():
        raw=output.read_bytes()
    else:
        with urllib.request.urlopen(URL,timeout=90) as stream:
            raw=stream.read(DATA_BYTES+1)
    if len(raw)!=DATA_BYTES or sha(raw)!=DATA_SHA256:
        raise ValueError('pinned MASAQ copy identity mismatch; file not written')
    if not output.exists():
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open('xb') as stream:
            stream.write(raw)
    print(f'verified {len(raw)} bytes sha256={DATA_SHA256}')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    fetch(p.parse_args().output)
