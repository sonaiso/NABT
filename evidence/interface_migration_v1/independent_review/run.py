"""Replay a pre-execution frozen development reference; no population claim."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from tools.licensed_workflow import run_request
BASE=Path(__file__).resolve().parent
PIN='d2f9c5a6b556c84a5738cf4e2b8bce435fc4d7b7821ddcdb4a529e3c008c153e'
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 if args.output.exists():raise ValueError('Refuse overwrite of raw review')
 raw=(BASE/'cases.v1.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
 reference=json.loads(raw); rows=[]
 for case in reference['cases']:
  started=time.perf_counter(); r=run_request(case['request']); elapsed=time.perf_counter()-started
  expected=case['expected']; child=r.get('result',{}); checks=[]
  def check(name,condition):checks.append({'check':name,'passed':condition is True})
  check('no_unlicensed_universal_grants',all(r.get(k) is not True and child.get(k) is not True for k in reference['forbidden_promotions']))
  if 'no_claims' in expected:check('no_positive_claim',r.get('claims')==[])
  if 'native_checked' in expected:check('native_checked',r.get('native_checked') is expected['native_checked'])
  if case['axis'].startswith('scope'):
   env=child.get('envelope'); acquired=child.get('status')=='CHECKED_SCOPE_ENVELOPE' and env is not None
   check('scope_admission',acquired is expected['acquired'])
   if expected['acquired']:
    check('native_envelope',child.get('native_checked') is True and bool(r.get('claims')))
    names={'quoted':'quoted_speaker','negated':'negated_embedding','hypothetical':'hypothetical'}
    check('scope_kind',env is not None and env.get('kind')==names[expected['kind']])
    check('body_preserved',env is not None and env.get('body')==expected['body'])
    check('speaker_label_preserved',env is not None and env.get('speaker_label')==expected['speaker'])
    text=case['request']['input']['text']; start=len(text[:text.index(expected['body'])].encode());end=start+len(expected['body'].encode())
    check('body_exact_byte_span',env is not None and env.get('start_byte')==start and env.get('end_byte')==end)
    check('no_narrator_projection',env is not None and env.get('projects_to_narrator') is False)
  if case['axis']=='transmission':
   reports=child.get('reports',[])
   check('exact_report_count',len(reports)==expected['report_count'])
   check('native_execution',r.get('native_checked') is True)
   check('no_duplicate_or_merged_readings',len({x.get('sense_id') for x in reports})==len(reports))
   check('context_bound',all(x.get('context')==case['request']['input']['context'] for x in reports))
   if 'families' in expected:check('source_families',child.get('source_families')==expected['families'])
   if 'relationship' in expected:check('source_relationship',child.get('source_relationship_status')==expected['relationship'])
  if case['axis']=='exact_form':
   matches=child.get('matches',[])
   check('exact_form_match',bool(matches) is expected['matched'])
   check('matching_witness_count',len(matches)==expected['matching_witness_count'])
   check('no_intended_sense',child.get('intended_sense_established') is False)
   check('source_extraction_independent',child.get('source_row_extraction_kernel_proved') is True)
  rows.append({'id':case['id'],'axis':case['axis'],'checks':checks,'passed':all(x['passed'] for x in checks),'seconds':elapsed,'raw_result':r})
 paths=['tools/licensed_workflow.py','tools/lexical_transmission.py','tools/linguistic_truth/scopes.py','formal/Nabt/ScopeAcquisition.lean','formal/ScopeAcquisitionMain.lean','formal/Nabt/LexicalTransmission.lean','formal/LexicalTransmissionMain.lean','src/nabt/data/framework_foundation.json']
 output={'schema':'nabt.interface-independent-review.v1','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_sha256':PIN,'independent_of_runtime_author':True,'blind_population_sample':False,'runtime_files':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'total':len(rows),'passed':sum(x['passed'] for x in rows),'failed_ids':[x['id'] for x in rows if not x['passed']],'axes':{axis:{'passed':sum(x['passed'] for x in rows if x['axis']==axis),'total':sum(x['axis']==axis for x in rows)} for axis in sorted({x['axis'] for x in rows})},'whole_arabic_complete':False,'results':rows}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 payload=(json.dumps(output,ensure_ascii=False,indent=2)+'\n').encode();args.output.write_bytes(gzip.compress(payload,mtime=0) if args.output.suffix=='.gz' else payload)
 print(json.dumps({k:v for k,v in output.items() if k not in {'results','runtime_files'}},ensure_ascii=False))
 return 0 if output['passed']==output['total'] else 1
if __name__=='__main__':raise SystemExit(main())
