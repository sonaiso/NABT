#!/usr/bin/env python3
"""Fetch a pinned compressed mirror; verify the upstream uncompressed identity."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.lexical_training.data import fetch_lisan,LISAN_SHA
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=fetch_lisan(a.output)
    print({'bytes':len(data),'sha256':LISAN_SHA})
