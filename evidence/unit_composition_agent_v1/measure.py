"""Reproduce operational coverage, without treating generated forms as gold.

PYTHONPATH=src:. python evidence/unit_composition_agent_v1/measure.py --output /tmp/measurement.json
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from tools.arabic_training.unit_composition import execute, ROOT
from tools.grammar_catalog.unit_catalog import curriculum
from tools.evidence_lifecycle_v1 import wire


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    for owner in ('progressiveUnitProbe','alignedAcquisition'):
        if not (ROOT/'formal/.lake/build/bin'/owner).is_file():
            raise RuntimeError('Build the existing native owners first')
    data=curriculum()
    rows=[]
    for example in data['examples']:
        report=execute(example['request'])
        r=report['result']
        row={'split':example['split'],'request':example['request'],
             'report_sha256':sha256(wire(report).encode()).hexdigest(),
             'execution_snapshot_sha256':report['execution_snapshot_sha256'],
             'status':r['status'],'native_calls':len(report['native_calls'])}
        if r['status']=='FORMAL_PATTERN_GENERATED':
            word=r['lower_trace']['words'][0]
            row.update(surface=r['generator_owner']['surface'],acquisition_status=word['status'],
                       sound_shape_accepted=word.get('native_receipt',{}).get('sound_shape_accepted'),
                       acquired=word['acquisition_owner']['status'])
        rows.append(row)
        if len(rows)%25==0: print('Measured',len(rows),flush=True)
    report={'schema':'nabt.unit-composition-operational-measurement.v1',
            'basis_commit':'7c86e16c217010c0af09c67886522e6e6f991fa4',
            'runner_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'examples':len(rows),'pattern_count':data['patterns'],
            'split_axis':data['split_axis'],'rows':rows,
            'statuses':dict(Counter(r['status'] for r in rows)),
            'acquisition_statuses':dict(Counter(r.get('acquisition_status','NONE') for r in rows)),
            'shape_results':dict(Counter(str(r.get('sound_shape_accepted')) for r in rows)),
            'native_calls':sum(r['native_calls'] for r in rows),
            'linguistic_accuracy_measured':False,'lexical_attestation_established':False,
            'neural_weights_trained':False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in report.items() if k!='rows'},flush=True)


if __name__=='__main__': main()
