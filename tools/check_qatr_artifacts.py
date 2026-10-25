#!/usr/bin/env python3
"""Independently replay every archived prediction's exact source binding."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.qatr_training.data import export_teacher, prepare, index_teacher


def check_bindings(examples, records, teacher):
    words=[w for e in examples if e['split']=='test' for w in e['words'] if w['qatr'] is not None]
    if len(records)!=len(words):raise ValueError('source denominator changed')
    lookup=index_teacher(teacher)
    fields={'address','csv_rows','text_sha256','gold_reading','gold_case','reading','case_ranking','authority'}
    for word,record in zip(words,records,strict=True):
        if set(record)!=fields:raise ValueError('prediction schema changed')
        binding=dict(address=word['address'],csv_rows=word['csv_rows'],text_sha256=word['text_sha256'],
                     gold_reading=word['qatr'],gold_case=word['case'],authority='NONE')
        if any(record[k]!=v or type(record[k]) is not type(v) for k,v in binding.items()):
            raise ValueError('source binding changed')
        if any(type(x) is not int for x in record['address']+record['csv_rows']):
            raise ValueError('source identity must use integer fields')
        if record['reading'] not in lookup or not lookup[record['reading']]['rows']:
            raise ValueError('unknown reading set')
        if record['case_ranking'] not in {'raf','nasb','jarr','jazm'}:
            raise ValueError('unknown case ranking')
    return len(words)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--lean',type=Path,required=True)
    p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args()
    teacher=export_teacher(a.lean);examples,_=prepare(a.source,teacher)
    records=[json.loads(s) for s in (a.model_dir/'test_predictions.jsonl').read_text().splitlines()]
    print(json.dumps(dict(ok=True,source_bound_predictions=check_bindings(examples,records,teacher))))

if __name__=='__main__':main()
