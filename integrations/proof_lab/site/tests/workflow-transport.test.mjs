import test from 'node:test';
import assert from 'node:assert/strict';
import {validatePayload,validateReport,signHandle,verifyHandle} from '../worker/server.mjs';
import {workflowReport,workflowRequest,workflowRequests,workflowId,workflowHash} from './helpers/workflow-fixture.mjs';
const c=globalThis.NabtWorkflowContract;
const expected=r=>({request_id:r.request_id,code_sha:r.code_sha,payload_sha256:r.payload_sha256,mode:r.mode,workflow_request_sha256:r.workflow_request_sha256});
for(const op of ['discourse_boundary','source_inference']){
 test(op+' preserves raw request and operation-specific proof authority',async()=>{
  const request=workflowRequests[op],payload={schema:'nabt.proof-lab-request.v1',mode:'licensed_workflow',workflow:request};
  assert.deepEqual(validatePayload(payload),payload);assert.equal(c.validateRequest(request),request);
  const report=workflowReport({op});assert.equal(validateReport(report,expected(report)),report);
  await c.verifyEnvelope(report);assert.equal(report.gateway_result.strict_language_accepted,false);
  for(const field of ['proof','verified','checker','native_checked','receipt','budget'])
   assert.throws(()=>c.validateRequest({...request,input:{...request.input,[field]:true}}));
 });
 test(op+' failure has no inherited proof from another operation',async()=>{
  const report=workflowReport({op,checked:false});await c.verifyEnvelope(report);
  assert.equal(report.gateway_result.claims.length,0);
 });
 test(op+' rejects a coherently rehashed claim with another operation law',async()=>{
  const report=workflowReport({op});
  report.gateway_result.claims[0].proof.law_id='nabt.scope-acquisition.v1';
  report.gateway_result.result.claims[0].proof.law_id='nabt.scope-acquisition.v1';
  report.adapter_result_json=c.canonical(report.gateway_result.result);
  report.gateway_result.result_sha256=workflowHash(report.adapter_result_json);
  report.gateway_result_json=c.canonical(report.gateway_result);
  report.gateway_result_sha256=workflowHash(report.gateway_result_json);
  assert.throws(()=>validateReport(report,expected(report)));await assert.rejects(c.verifyEnvelope(report));
 });
}
test('source inference requires a separate query and cannot borrow a discourse context flag',()=>{
 const request=workflowRequests.source_inference;
 assert.throws(()=>c.validateRequest({...request,input:{source:request.input.source}}));
 assert.throws(()=>c.validateRequest({...request,input:{...request.input,context:'unbound context'}}));
});
test('discourse unknown convention remains an explicit null across transport validation',()=>{
 const request={...workflowRequests.discourse_boundary,input:{...workflowRequests.discourse_boundary.input,profile_id:null}};
 assert.equal(c.validateRequest(request),request);
 const payload={schema:'nabt.proof-lab-request.v1',mode:'licensed_workflow',workflow:request};
 assert.deepEqual(validatePayload(payload),payload);
});
test('scoped workflow request accepts only registered raw adapter inputs',()=>{
 const p={schema:'nabt.proof-lab-request.v1',mode:'licensed_workflow',workflow:workflowRequest};
 assert.deepEqual(validatePayload(p),p);
 for(const field of ['proof','verified','checker','native_checked','receipt'])assert.throws(()=>validatePayload({...p,workflow:{...workflowRequest,input:{...workflowRequest.input,[field]:true}}}));
 for(const op of ['route-diagnostic','exec','evaluate','__proto__'])assert.throws(()=>validatePayload({...p,workflow:{...workflowRequest,op}}));
});
test('workflow numbers are safe integers and invalid Unicode cannot dispatch',()=>{
 for(const value of [1.1,Number.MAX_SAFE_INTEGER+1,Infinity,NaN])assert.throws(()=>c.validateRequest({...workflowRequest,input:{...workflowRequest.input,start_byte:value}}));
 assert.throws(()=>c.validateRequest({...workflowRequest,input:{text:'\ud800'}}));
});
test('scoped response binds child claims and canonical digests without blanket proof',async()=>{
 const r=workflowReport();assert.equal(validateReport(r,expected(r)),r);await c.verifyEnvelope(r);
 assert.equal(r.gateway_result.strict_language_accepted,false);
});
const mutations=[
 ['changed native claim',r=>r.gateway_result.claims[0].scope='whole Arabic'],
 ['hidden claim',r=>r.gateway_result.claims=[]],
 ['changed source request',r=>r.workflow_request.input.text='عِيْنَ'],
 ['promoted strict result',r=>r.gateway_result.strict_language_accepted=true],
 ['invented completed migration',r=>r.migration_inventory.all_interfaces_migrated=true],
 ['invented inventory denominator',r=>r.migration_inventory.surface_count=174],
 ['duplicate inventory row',r=>r.migration_inventory.surfaces.push(r.migration_inventory.surfaces[0])],
 ['wrong installed registry',r=>r.registry_sha256='0'.repeat(64)],
 ['wrong adapter digest',r=>r.gateway_result.result_sha256='0'.repeat(64)],
 ['wrong canonical bytes',r=>r.gateway_result_json+=' '],
];
for(const[name,change]of mutations)test('workflow refuses '+name,async()=>{const r=workflowReport();change(r);await assert.rejects(c.verifyEnvelope(r));});
test('failure workflow remains visible with no claims and no borrowed native success',async()=>{
 const r=workflowReport({checked:false});await c.verifyEnvelope(r);assert.equal(r.gateway_result.claims.length,0);
});
test('signed workflow handle requires its own request digest',async()=>{
 const r=workflowReport();const d={...expected(r),created:Date.now()},secret='test-only-workflow-key-1234567890';
 assert.deepEqual(await verifyHandle(await signHandle(d,secret),secret),d);
 delete d.workflow_request_sha256;await assert.rejects(verifyHandle(await signHandle(d,secret),secret));
});

// Rehash all transport bytes to test admitted semantics, not only digest drift.
for(const [name,change] of [
 ['a different registered operation law',r=>{r.gateway_result.claims[0].proof.law_id='nabt.scope-acquisition.v1';r.gateway_result.result.claims[0].proof.law_id='nabt.scope-acquisition.v1';}],
 ['an invented checked claim kind',r=>{r.gateway_result.claims[0].kind='WHOLE_LANGUAGE';r.gateway_result.result.claims[0].kind='WHOLE_LANGUAGE';}],
])test('workflow rejects coherent rehash with '+name,async()=>{
 const r=workflowReport();change(r);
 r.adapter_result_json=c.canonical(r.gateway_result.result);r.gateway_result.result_sha256=workflowHash(r.adapter_result_json);
 r.gateway_result_json=c.canonical(r.gateway_result);r.gateway_result_sha256=workflowHash(r.gateway_result_json);
 assert.throws(()=>validateReport(r,expected(r)));await assert.rejects(c.verifyEnvelope(r));
});
