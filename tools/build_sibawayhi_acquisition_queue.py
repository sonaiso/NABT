"""Stage upstream written forms for review, never infer unseen vowel readings."""
import argparse
from collections import Counter,defaultdict
import csv
import io
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.arabic_training.data import sha
PIN='678ca5144698b571a42804b19b8d1680766df7f2339cf6c9c53d84994051fdd9'


def build(source):
    raw=source.read_bytes()
    if len(raw)!=33549 or sha(raw)!=PIN:
        raise ValueError('Sibawayhi derived inventory identity mismatch')
    reader=csv.DictReader(io.StringIO(raw.decode()),delimiter='\t')
    if reader.fieldnames!=['tier','skeleton','token','rule','edition','line']:
        raise ValueError('unexpected inventory schema')
    grouped=defaultdict(list); rows=list(reader)
    for number,row in enumerate(rows,2):
        grouped[(row['tier'],row['token'])].append(dict(tsv_row=number,upstream_edition=row['edition'],
                                                       upstream_line=int(row['line']),extraction_rule=row['rule'],
                                                       upstream_skeleton=row['skeleton']))
    items=[dict(id=f'SIB-ACQ-{i:03}',tier=tier,written_form=token,source_rows=refs,
                vocalized_readings=None,interpretations=None,independent_human_review=None,
                training_eligible=False,status='UNMEASURED',
                obligations=['Reopen cited edition bytes and bind exact passage',
                             'Distinguish abstract pattern from attested lexical example',
                             'Record every licensed vocalization with contextual conditions',
                             'Assign morphology, interpretation and lexical identity independently',
                             'Review source rights and adjudicate annotations before training'])
           for i,((tier,token),refs) in enumerate(sorted(grouped.items()),1)]
    return dict(schema='nabt.sibawayhi-acquisition-queue.v1',upstream_repository='Saleh1967/Alghanem',
                upstream_commit='9d8fa03a51f894416e0abaf3b6821c5ae6441dcd',
                upstream_path='corpora/sibawayh-abniya.tsv',source_sha256=sha(raw),source_bytes=len(raw),
                upstream_rows=len(rows),unique_written_forms=len({r['token'] for r in rows}),
                distinct_tier_form_pairs=len(items),tier_rows=dict(Counter(r['tier'] for r in rows)),
                note='Two editions are citation witnesses, not independent training samples. Unvocalized pattern strings are not learned Arabic readings.',
                items=items)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(build(args.source),stream,ensure_ascii=False,indent=2);stream.write('\n')
