"""Public-contract attacks, separate from controlled-language accuracy scores."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from .integrity import require_output, verify_code_freeze, write_report

ROOT=Path(__file__).resolve().parents[2]
SEED='''مفهوم فريد
مفهوم ناعم
مفهوم ثابت
علاقة يتصل
أثير هو فريد
أثير يتصل رواس
إذا ?س هو فريد فإن ?س هو ناعم
إذا ?س يتصل ?ص و ?س هو ناعم فإن ?ص هو ثابت
'''


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--code-freeze',required=True,type=Path)
    args=ap.parse_args()
    require_output(args.output, freeze=args.code_freeze)
    freeze=verify_code_freeze(args.code_freeze)
    from nabt.text_reader import parse_document,parse_query
    from nabt.semantics import SemanticKernel
    from nabt.errors import NabtError
    def kernel():
        k=SemanticKernel()
        assert k.add_document(parse_document(SEED,source_id='seed')).as_dict()['accepted']
        return k
    def ask(k,text='هل رواس هو ثابت؟'):
        return k.query(parse_query(text)).as_dict()
    k=kernel()
    original=ask(k)['proofs']['query']
    outcomes=[]
    def record(ident,passed,details):
        outcomes.append({'id':ident,'passed':passed,'details':details})
    good=k.verify_certificate(original)
    record('valid_certificate',good['accepted'],good)
    def mutate(ident,change):
        cert=copy.deepcopy(original)
        try:
            change(cert)
            result=k.verify_certificate(cert)
            record(ident,not result['accepted'],result)
        except Exception as exc:
            record(ident,False,{'unexpected_exception':type(exc).__name__,'message':str(exc)})
    mutate('forged_query_subject',lambda c:c['query']['args'].__setitem__(0,'بديل'))
    mutate('forged_scope',lambda c:c.__setitem__('scope','other'))
    mutate('forged_source_id',lambda c:c['steps'][0]['clause'].__setitem__('source_id','absent'))
    mutate('forged_source_hash',lambda c:c['steps'][0]['clause'].__setitem__('source_sha256','0'*64))
    mutate('forged_span_hash',lambda c:c['steps'][0]['clause']['span'].__setitem__('span_sha256','0'*64))
    mutate('misaligned_utf8_span',lambda c:c['steps'][0]['clause']['span'].__setitem__('start',c['steps'][0]['clause']['span']['start']+1))
    mutate('negative_span_bound',lambda c:c['steps'][0]['clause']['span'].__setitem__('start',-1))
    mutate('boolean_span_bound',lambda c:c['steps'][0]['clause']['span'].__setitem__('start',True))
    mutate('forged_component_span',lambda c:c['steps'][0]['clause']['component_spans'][0].__setitem__('end',c['steps'][0]['clause']['component_spans'][0]['end']+1))
    mutate('forged_step_predicate',lambda c:c['steps'][-1]['atom'].__setitem__('predicate','مخترع'))
    mutate('forged_fact_argument',lambda c:c['steps'][0]['clause']['atom']['args'].__setitem__(0,'بديل'))
    mutate('forged_rule_head',lambda c:c['steps'][-1]['clause']['head'].__setitem__('predicate','مخترع'))
    mutate('omitted_rule_premise',lambda c:c['steps'][-1]['clause']['body'].pop())
    mutate('wrong_binding',lambda c:c['steps'][-1]['binding'].__setitem__(next(iter(c['steps'][-1]['binding'])),'بديل'))
    mutate('omitted_proof_premises',lambda c:c['steps'][-1].__setitem__('premises',[]))
    mutate('self_reference',lambda c:c['steps'][-1].__setitem__('premises',[len(c['steps'])-1]))
    mutate('flipped_conclusion_sign',lambda c:c['steps'][-1]['atom'].__setitem__('positive',False))
    mutate('wrong_conclusion_index',lambda c:c.__setitem__('conclusion',0))
    mutate('forged_version',lambda c:c.__setitem__('version','invented.v9'))
    mutate('forged_analysis_id',lambda c:c['steps'][0]['clause'].__setitem__('analysis_id','0'*64))
    mutate('forged_clause_id',lambda c:c['steps'][0]['clause'].__setitem__('clause_id','0'*64))
    mutate('forged_world_truth',lambda c:c.__setitem__('world_truth','ESTABLISHED'))

    k.add_document(parse_document('إياد هو مختلف',source_id='unrelated'))
    after_add=k.verify_certificate(original)
    record('unrelated_source_preserves_proof',after_add['accepted'],after_add)
    k.remove_source('unrelated')
    after_remove=k.verify_certificate(original)
    record('unrelated_withdrawal_preserves_proof',after_remove['accepted'],after_remove)
    k.add_document(parse_document('ليس أثير هو فريد',source_id='conflict'))
    contested=k.verify_certificate(original)
    q=ask(k)
    record('new_conflict_invalidates_clean_proof',not contested['accepted'] and q['status']=='DEFER' and q['reason']=='CONTESTED_PREMISES',{'verification':contested,'query_status':q['status'],'query_reason':q['reason']})
    k.remove_source('conflict')
    restored=k.verify_certificate(original)
    record('conflict_withdrawal_restores_proof',restored['accepted'],restored)
    dup=k.add_document(parse_document('ليس أثير هو فريد',source_id='seed')).as_dict()
    record('duplicate_source_rejected_atomically',not dup['accepted'] and ask(k)['status']=='SUPPORTED',dup)
    bad_replace=k.replace_source('أثير هو فريد\nهذا كلام خارج اللغة',source_id='seed').as_dict()
    record('invalid_replacement_preserves_old_source',not bad_replace['accepted'] and ask(k)['status']=='SUPPORTED',bad_replace)
    k.remove_source('seed')
    withdrawn=k.verify_certificate(original)
    record('withdrawn_dependency_invalidates_proof',not withdrawn['accepted'],withdrawn)

    for ident,text in [
        ('unsupported_suffix_no_prefix_leak','زاهر هو مستحدث\nهذا كلام خارج اللغة'),
        ('unsafe_unbound_head','إذا ?س هو سابق فإن ?ص هو لاحق'),
        ('variable_fact_rejected','?س هو جوهري'),
        ('unsupported_disjunction','إذا ?س هو ناعم أو ?س هو ثابت فإن ?س هو قوي'),
        ('unclosed_quote','«اسم غير مغلق هو صريح'),
    ]:
        fresh=SemanticKernel()
        try:
            document=parse_document(text,source_id='hostile')
            report=fresh.add_document(document).as_dict()
            q=fresh.query(parse_query('هل زاهر هو مستحدث؟')).as_dict()
            record(ident,not report['accepted'] and q['status']!='SUPPORTED',{'admission':report,'query_status':q['status']})
        except Exception as exc:
            status=getattr(getattr(exc,'status',None),'value',getattr(exc,'status',None))
            code=getattr(getattr(exc,'code',None),'value',getattr(exc,'code',None))
            record(ident,isinstance(exc,NabtError) and status in {'REJECT','DEFER'} and code!='RESOURCE_LIMIT',
                   {'rejection_exception':type(exc).__name__,'status':status,'code':code,'message':str(exc)})
    for ident,text in [('source_byte_budget',' '*65537),('statement_count_budget','مفهوم عنصر\n'*257)]:
        try:
            parse_document(text,source_id='budget')
            record(ident,False,{'returned_without_resource_deferral':True})
        except Exception as exc:
            status=getattr(getattr(exc,'status',None),'value',getattr(exc,'status',None))
            code=getattr(getattr(exc,'code',None),'value',getattr(exc,'code',None))
            record(ident,status=='DEFER' and code=='RESOURCE_LIMIT',{'exception':type(exc).__name__,'status':status,'code':code,'message':str(exc)})
    summary={'probes':len(outcomes),'passed':sum(o['passed'] for o in outcomes),'failed_ids':[o['id'] for o in outcomes if not o['passed']],
             'scope':'Public-contract adversarial probes and valid controls; separate from heldout controlled-Arabic accuracy.'}
    write_report(args.output, {'schema':'nabt-independent-adversarial-probes-v1','code_freeze':freeze,'summary':summary,'outcomes':outcomes}, freeze=args.code_freeze)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
