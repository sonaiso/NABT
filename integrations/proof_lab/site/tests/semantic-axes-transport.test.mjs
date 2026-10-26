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
test('fixed suite input excludes supplied gold, rules, statuses or executable code',()=>{
  const request={schema:'nabt.proof-lab-request.v1',mode:'semantic_axes'};
  assert.deepEqual(validatePayload(request),request);
  for(const key of ['reference','gold','cases','budget','source_text','verified','code'])assert.throws(()=>validatePayload({...request,[key]:[]}));
});
test('new mode participates in the signed request binding',async()=>{
  const d={...expected,created:Date.now()},secret='test-only-signing-key';
  assert.deepEqual(await verifyHandle(await signHandle(d,secret),secret),d);
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
test('new pinned branch is enabled without exposing secrets',async()=>{
  const response=await route(new Request('https://example.test/api/config'),{
    NABT_EXECUTION_ENABLED:'true',NABT_TRANSPORT_KEY:hash,NABT_GITHUB_TOKEN:'test-only',NABT_SIGNING_KEY:'s'.repeat(32),NABT_CODE_SHA:expected.code_sha,NABT_REF:'codex/semantic-axes-reference'},{});
  const data=await response.json();assert.equal(data.ready,true);assert.equal(data.branch,'codex/semantic-axes-reference');assert.ok(!JSON.stringify(data).includes('test-only'));
});
