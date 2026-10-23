"""Reviewer-counterexample regressions; not heldout-language test episodes."""
import argparse
import hashlib
import json
from pathlib import Path

from .integrity import require_output, verify_code_freeze, write_report

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=[
    ('explicit_complementary_body','إذا ?س هو قويم و ليس ?س هو قويم فإن ?س هو مقبول','هل ركين هو مقبول؟'),
    ('added_premise_refutes_itself','كل صابر هو مظفر\nإذا ?س هو صابر فإن ليس ?س هو صابر','هل صهيب هو مظفر؟'),
    ('added_premise_conflicts_query','كل نام هو متحقق\nإذا ?س هو نام فإن ليس ?س هو متحقق','هل نمير هو متحقق؟'),
    ('existing_negative_blocks_premise','كل باسط هو ناشر\nليس رضوان هو باسط','هل رضوان هو ناشر؟'),
    ('clean_alternative_still_possible','إذا ?س هو صالح و ليس ?س هو صالح فإن ?س هو حسن\nكل نقي هو حسن','هل سوار هو حسن؟'),
    ('negative_query_complementary_body','إذا ?س هو مؤيد و ليس ?س هو مؤيد فإن ليس ?س هو متردد','هل ليس رائد هو متردد؟'),
    ('consistent_conjunction_control','إذا ?س هو ندي و ?س هو رطب فإن ?س هو مزهر\nيسار هو ندي','هل يسار هو مزهر؟'),
]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--code-freeze',required=True,type=Path)
    args=ap.parse_args()
    require_output(args.output, freeze=args.code_freeze)
    freeze=verify_code_freeze(args.code_freeze)
    from nabt.text_reader import parse_document,parse_query
    from nabt.semantics import SemanticKernel
    def load(text):
        k=SemanticKernel()
        assert k.add_document(parse_document(text,source_id='theory')).as_dict()['accepted']
        return k
    def surface(a):
        args=a['args']
        if len(args)==1:
            atom=f'«{args[0]}» هو «{a["predicate"]}»'
        else:
            atom=f'«{args[0]}» «{a["predicate"]}» «{args[1]}»'
        return atom if a['positive'] else 'ليس '+atom
    results=[]
    for ident,text,question in SCENARIOS:
        kernel=load(text)
        before=kernel.query(parse_query(question)).as_dict()
        plans=[]
        for p in before['missing_premises']:
            fresh=load(text)
            supplied='\n'.join(surface(a) for a in p['atoms'])
            admission=fresh.add_document(parse_document(supplied,source_id='completion')).as_dict()
            after=fresh.query(parse_query(question)).as_dict()
            plans.append({'atoms':p['atoms'],'admission_accepted':admission['accepted'],'counterfactual_status':after['status'],'counterfactual_reason':after['reason'],
                          'passed':admission['accepted'] and after['status']=='SUPPORTED'})
        passed=all(p['passed'] for p in plans)
        if ident=='consistent_conjunction_control' and not plans:
            passed=False
        results.append({'id':ident,'query_status':before['status'],'missing_complete':before['missing_complete'],'plans':plans,'passed':passed})
    summary={'reviewer_regression_scenarios':len(results),'passed':sum(r['passed'] for r in results),
             'plans_replayed':sum(len(r['plans']) for r in results),'invalid_returned_plans':sum(not p['passed'] for r in results for p in r['plans']),
             'note':'Created after an independent root-review counterexample; not part of the sealed 60-episode language benchmark.'}
    write_report(args.output, {'schema':'nabt-missing-plan-counterfactual-regressions-v1','code_freeze':freeze,'summary':summary,'results':results}, freeze=args.code_freeze)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
