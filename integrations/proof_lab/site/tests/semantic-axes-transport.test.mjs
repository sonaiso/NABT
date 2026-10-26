import test from 'node:test';
import assert from 'node:assert/strict';
import {validatePayload,validateReport,validateSemanticAxes,signHandle,verifyHandle,route} from '../worker/server.mjs';
const axes=['syntax','readings','reference','motive','world'];
const hash='a'.repeat(64);
const expected={request_id:'f2702111-d080-4c99-8c4c-ef43f10a3def',payload_sha256:hash,code_sha:'b'.repeat(40),mode:'semantic_axes'};
function suite(){
  return {schema:'nabt.semantic-axes-benchmark.v1',case_count:25,scope:'Transport contract fixture only',
    reference_sha256:hash,adapter_sha256:hash,input_suite_sha256:hash,lean_native_checked:false,all_arabic_complete:false,
    axes:Object.fromEntries(axes.map(a=>[a,{eligible:25,measured:0,passed:0,failed:0,unmeasured:25,rate:null}])),
    cases:Array.from({length:25},(_,i)=>({id:'case'+i,context_id:hash,case_input_sha256:hash,
      input:{text:'نَصٌّ',context:{}},axis_results:Object.fromEntries(axes.map(a=>[a,{status:'UNMEASURED'}])),
      claims:axes.map(a=>({id:'case'+i+':'+a,axis:a,statement:'No available measurement',status:'UNMEASURED',
        verification:{kind:'NOT_CHECKED',checked:false,scope:'Not checked',theorem_references:[],claim_id:'case'+i+':'+a,input_sha256:hash}}))}))};
}
function report(){return {schema:'nabt.proof-lab-result.v1',...expected,status:'SEMANTIC_AXES_COMPLETE',
  all_arabic_complete:false,world_truth_established:false,native_sha256:null,reference_sha256:hash,runtime_sha256:hash,semantic_axes:suite()};}
function attestedSuite(){
  const s=suite();s.lexical_profile='attested_qac_v1';
  s.lexical_loading={schema:'nabt.semantic-axes-lexical-loading.v1',profile:'attested_qac_v1',matrix_sha256:hash,source_sha256:hash,
    authority:'SOURCE_ANNOTATION_NOT_SENSE_OR_WORLD_LICENSE',lean_native_checked:false,
    source_record_count:10,model_entry_count:7,matrix_sense_count:3,matrix_aligned_count:2,matrix_unresolved_count:1};
  for(const row of s.cases){
    row.lexical_coverage={tokens:2,covered:1,uncovered:1,items:[{surface:'نَصٌّ',reading_count:2},{surface:'مَجْهُولٌ',reading_count:0}]};
    row.execution={executed:true,replay_checked:true,lexical_profile:s.lexical_profile,lexical_loading:structuredClone(s.lexical_loading),input_sha256:row.case_input_sha256,
      training:{path:'pinned-source.gz',sha256:hash,authority:s.lexical_loading.authority},
      replay_receipt:{lexical_profile:s.lexical_profile,lexical_loading:structuredClone(s.lexical_loading),training_sha256:hash,input_sha256:row.case_input_sha256,replay:{valid:true,status:'VERIFIED'}},
      observed:{acquisition_diagnostics:{lexical_occurrences:structuredClone(row.lexical_coverage.items)}}};
  }
  return s;
}
test('fixed suite input excludes supplied gold, rules, statuses or executable code',()=>{
  const request={schema:'nabt.proof-lab-request.v1',mode:'semantic_axes'};
  assert.deepEqual(validatePayload(request),request);
  for(const key of ['reference','gold','cases','budget','source_text','verified','code'])assert.throws(()=>validatePayload({...request,[key]:[]}));
});
test('new mode participates in the signed request binding',async()=>{
  const d={...expected,created:Date.now()},secret='test-only-signing-key';
  assert.deepEqual(await verifyHandle(await signHandle(d,secret),secret),d);
});
test('only installed lexical profiles may enter the request or signed handle',async()=>{
  const request={schema:'nabt.proof-lab-request.v1',mode:'semantic_axes',lexical_profile:'attested_qac_v1'};
  assert.deepEqual(validatePayload(request),request);
  assert.deepEqual(validatePayload({...request,lexical_profile:'teaching_v1'}),{schema:request.schema,mode:request.mode});
  for(const value of ['custom',null,true,{},''])assert.throws(()=>validatePayload({...request,lexical_profile:value}));
  const d={...expected,created:Date.now(),lexical_profile:'attested_qac_v1'},secret='test-only-signing-key';
  assert.deepEqual(await verifyHandle(await signHandle(d,secret),secret),d);
  await assert.rejects(async()=>verifyHandle(await signHandle({...d,mode:'inference'},secret),secret));
});
test('attested report is bound to the requested profile without promoting source counts',()=>{
  const r=report();r.semantic_axes=attestedSuite();r.lexical_profile='attested_qac_v1';
  assert.equal(validateReport(r,{...expected,lexical_profile:'attested_qac_v1'}),r);
  assert.throws(()=>validateReport(r,expected));
  assert.throws(()=>validateReport(report(),{...expected,lexical_profile:'attested_qac_v1'}));
  r.lexical_profile='teaching_v1';assert.throws(()=>validateReport(r,{...expected,lexical_profile:'attested_qac_v1'}));
});
test('suite profile cannot relabel a successful execution, source or replay receipt',()=>{
  for(const mutate of [
    e=>e.lexical_profile='teaching_v1',e=>e.replay_receipt.lexical_profile='teaching_v1',
    e=>e.training.sha256='b'.repeat(64),e=>e.replay_receipt.training_sha256='b'.repeat(64),
    e=>e.lexical_loading=null,e=>e.replay_receipt.lexical_loading=null,
    e=>e.lexical_loading.matrix_sha256='b'.repeat(64),e=>e.replay_receipt.lexical_loading.source_sha256='b'.repeat(64),
    e=>e.lexical_loading.source_record_count++,e=>e.replay_receipt.lexical_loading.authority='WORLD_TRUTH',
    e=>e.replay_receipt.replay.valid=false,e=>e.replay_receipt.replay.status='UNVERIFIED',
    e=>e.input_sha256='b'.repeat(64),e=>e.replay_receipt.input_sha256='b'.repeat(64),
  ]){const s=attestedSuite();mutate(s.cases[0].execution);assert.throws(()=>validateSemanticAxes(s));}
  const teaching=attestedSuite();teaching.lexical_profile='teaching_v1';delete teaching.lexical_loading;
  for(const row of teaching.cases){const e=row.execution;e.lexical_profile='teaching_v1';e.lexical_loading=null;e.training.authority='PRE_EXISTING_AUTHORED_TEACHING_CORPUS_NOT_EXTERNAL_ATTESTATION';e.replay_receipt.lexical_profile='teaching_v1';e.replay_receipt.lexical_loading=null;}
  assert.equal(validateSemanticAxes(teaching),teaching);
  teaching.cases[0].execution.training.sha256='b'.repeat(64);teaching.cases[0].execution.replay_receipt.training_sha256='b'.repeat(64);
  assert.throws(()=>validateSemanticAxes(teaching));
});
test('lexical loading counts and token coverage reconcile their distinct populations',()=>{
  assert.equal(validateSemanticAxes(attestedSuite()).lexical_loading.matrix_sense_count,3);
  for(const mutate of [
    s=>s.lexical_loading.matrix_sense_count=4,s=>s.lexical_loading.matrix_aligned_count=true,
    s=>s.lexical_loading.source_record_count=1.5,s=>s.lexical_loading.authority='WORLD_TRUTH',
    s=>s.lexical_loading.lean_native_checked=true,s=>delete s.lexical_loading,
    s=>s.cases[0].lexical_coverage.covered=2,s=>s.cases[0].lexical_coverage.items[0].reading_count=true,
    s=>s.cases[0].lexical_coverage.items[0].surface='آخَرٌ',s=>s.cases[0].lexical_coverage=null,
    s=>s.cases[0].execution.replay_checked=false,s=>delete s.cases[0].lexical_coverage,
  ]){const s=attestedSuite();mutate(s);assert.throws(()=>validateSemanticAxes(s));}
  const failed=attestedSuite();failed.cases[0].execution={executed:false,replay_checked:false};failed.cases[0].lexical_coverage=null;
  assert.equal(validateSemanticAxes(failed),failed);
  for(const execution of [null,{}, {executed:'false',replay_checked:false},{executed:false,replay_checked:'false'},{executed:false,replay_checked:true}]){
    const changed=structuredClone(failed);changed.cases[0].execution=execution;assert.throws(()=>validateSemanticAxes(changed));
  }
});
test('valid unavailable measurements preserve eligible denominators',()=>{
  assert.equal(validateReport(report(),expected).semantic_axes.axes.syntax.rate,null);
});
test('failure receipt needs no suite and cannot carry stale success payloads',()=>{
  const r=report();delete r.semantic_axes;r.status='EXECUTION_FAILED';r.error='INTERNAL_EXECUTION_FAILURE';
  assert.equal(validateReport(r,expected),r);
  for(const key of ['semantic_axes','testimony','result','benchmark'])assert.throws(()=>validateReport({...r,[key]:{}},expected));
});
test('runtime and reference identity must agree with the bound suite',()=>{
  for(const key of ['reference_sha256','runtime_sha256']){const r=report();r[key]='c'.repeat(64);assert.throws(()=>validateReport(r,expected));}
});
test('forbids false verification contradictions, cross-claim and cross-context certificates',()=>{
  for(const patch of [{checked:true},{kind:'LEAN_NATIVE'},{claim_id:'other:syntax'},{input_sha256:'c'.repeat(64)},{certificate_sha256:hash},{theorem_references:['Unrelated.theorem']}]){
    const s=suite();Object.assign(s.cases[0].claims[0].verification,patch);assert.throws(()=>validateSemanticAxes(s));
  }
  const s=suite();s.cases[0].claims[0].status='PASS';assert.throws(()=>validateSemanticAxes(s));
});
test('rejects numeric coercion, dropped cases, duplicate cases and inflated denominators',()=>{
  for(const value of [true,'25',25.5,-1,NaN,Infinity,Number.MAX_SAFE_INTEGER+1]){
    const s=suite();s.axes.syntax.eligible=value;assert.throws(()=>validateSemanticAxes(s));
  }
  for(const mutate of [s=>s.cases.pop(),s=>s.cases[1].id=s.cases[0].id,s=>s.axes.syntax.rate=0,s=>s.axes.extra=s.axes.syntax]){
    const s=suite();mutate(s);assert.throws(()=>validateSemanticAxes(s));
  }
});
test('semantic suite cannot be attached to an unrelated live mode',()=>{
  const r=report();r.mode='testimony';assert.throws(()=>validateReport(r,{...expected,mode:'testimony'}));
});
test('inapplicable claim cannot replace an eligible claim with matching count and unique axes',()=>{
  const s=suite(),row=s.cases[0];
  row.axis_results.reference.status='NOT_APPLICABLE';
  row.claims=row.claims.filter(claim=>claim.axis!=='reference');
  s.axes.reference={eligible:24,measured:0,passed:0,failed:0,unmeasured:24,rate:null};
  assert.equal(validateSemanticAxes(s),s);
  // Keep four unique claim axes and coherent IDs/statuses, but remove the
  // eligible syntax claim and substitute the excluded reference claim.
  row.claims[0]={id:row.id+':reference',axis:'reference',statement:'Excluded axis',status:'NOT_APPLICABLE',
    verification:{kind:'NOT_CHECKED',checked:false,scope:'Excluded',theorem_references:[],claim_id:row.id+':reference',input_sha256:hash}};
  assert.throws(()=>validateSemanticAxes(s));
});
test('new pinned branch is enabled without exposing secrets',async()=>{
  const response=await route(new Request('https://example.test/api/config'),{
    NABT_EXECUTION_ENABLED:'true',NABT_TRANSPORT_KEY:hash,NABT_GITHUB_TOKEN:'test-only',NABT_SIGNING_KEY:'s'.repeat(32),NABT_CODE_SHA:expected.code_sha,NABT_REF:'codex/attested-lexical-matrix'},{});
  const data=await response.json();assert.equal(data.ready,true);assert.equal(data.branch,'codex/attested-lexical-matrix');assert.ok(!JSON.stringify(data).includes('test-only'));
});
