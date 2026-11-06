"""Exhaust two-cell A116 products through real bounded native pages.

PYTHONPATH=src:. python evidence/unit_composition_agent_v1/measure_cells.py --output /tmp/cells.json
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from tools.arabic_training.unit_composition import execute
from tools.evidence_lifecycle_v1 import wire


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    offset=accepted=0
    pages=[]
    while offset<116**2:
        request={'op':'cell_page','length':2,'offset':offset,'limit':128,'mode':'wasl'}
        report=execute(request)
        row=report['result']
        if row['status']!='CELL_PRODUCT_PAGE': raise RuntimeError(row)
        count=row['count']
        if not 1<=count<=128: raise ValueError('Nonprogressing page')
        # Independent fixed-length address check, separate from codec decoding.
        for i,cells in enumerate(row['cells'],offset):
            if cells != [i//116,i%116]: raise ValueError('Cartesian address mismatch')
        accepted+=sum(r['sound_shape_accepted'] for r in row['receipts'])
        pages.append({'offset':offset,'count':count,'report_sha256':sha256(wire(report).encode()).hexdigest(),
                      'execution_snapshot_sha256':report['execution_snapshot_sha256']})
        offset+=count
        if row['next_offset']!=(offset if offset<116**2 else None):
            raise ValueError('Noncontiguous page cursor')
        if len(pages)%20==0: print('Measured cell pairs',offset,flush=True)
    result={'schema':'nabt.unit-composition-cell-pairs-measurement.v1',
            'domain':{'alphabet':'nabt.a116.v1','length':2,'mode':'wasl','entry':0},
            'runner_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'measured':offset,'sound_shape_accepted':accepted,'sound_shape_rejected':offset-accepted,
            'full_97_state_effects_replayed':offset,'all_pairs_measured':offset==116**2,
            'lexical_or_grammatical_license_established':False,
            'three_or_four_cell_products_exhausted':False,'pages':pages}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='pages'},flush=True)


if __name__=='__main__': main()
