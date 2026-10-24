#!/usr/bin/env python3
"""Train actual neural Arabic morphology from pinned source annotations on CPU."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--output-dir', required=True, type=Path)
    p.add_argument('--protocol', type=Path, default=ROOT/'evidence/source_morphology_training/protocol.json')
    args = p.parse_args()
    from tools.arabic_training.experiment import train
    train(args.source, args.output_dir, args.protocol)

if __name__ == '__main__':
    main()
