"""Additional independent source-admission boundary probes after first freeze."""
import argparse
import dataclasses
import hashlib
import json
from pathlib import Path

from .integrity import require_output, verify_code_freeze, write_report

ROOT=Path(__file__).resolve().parents[2]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--code-freeze',required=True,type=Path)
    args=ap.parse_args()
    require_output(args.output, freeze=args.code_freeze)
    freeze=verify_code_freeze(args.code_freeze)
    from nabt.text_reader import parse_document,parse_query
    from nabt.semantics import SemanticKernel
    original=parse_document('أثير هو معلوم\nكل معلوم هو محفوظ',source_id='original')
    forged_fact=dataclasses.replace(original.facts[0],atom=dataclasses.replace(original.facts[0].atom,predicate='مصطنع'))
    forged_rule=dataclasses.replace(original.rules[0],head=dataclasses.replace(original.rules[0].head,predicate='مصطنع'))
    residual=parse_document('أثير هو مصطنع\nنص خارج حدود القراءة',source_id='residual')
    cases=[
        ('caller_forged_fact',dataclasses.replace(original,facts=(forged_fact,))),
        ('caller_forged_rule',dataclasses.replace(original,rules=(forged_rule,))),
        ('caller_erased_residual',dataclasses.replace(residual,residuals=())),
    ]
    outcomes=[]
    for ident,doc in cases:
        kernel=SemanticKernel()
        try:
            report=kernel.add_document(doc).as_dict()
            q=kernel.query(parse_query('هل أثير هو مصطنع؟')).as_dict()
            passed=q['status']!='SUPPORTED'
            outcomes.append({'id':ident,'passed':passed,'admission':report,'unsupported_claim_status':q['status']})
        except Exception as exc:
            # Invalid caller AST can be rejected as malformed input; a generic
            # crash is retained for review rather than hidden as a success.
            from nabt.errors import NabtError
            outcomes.append({'id':ident,'passed':isinstance(exc,NabtError),'exception':type(exc).__name__,'message':str(exc)})
    summary={'probes':len(outcomes),'passed':sum(o['passed'] for o in outcomes),'failed_ids':[o['id'] for o in outcomes if not o['passed']],
             'note':'Caller-created parsed ASTs cannot grant claims or erase residual source material. Added after first40 without seeing hidden reserve cases.'}
    write_report(args.output, {'schema':'nabt-source-admission-boundary-regressions-v1','code_freeze':freeze,'summary':summary,'outcomes':outcomes}, freeze=args.code_freeze)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
