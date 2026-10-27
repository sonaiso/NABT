import test from 'node:test';
import assert from 'node:assert/strict';
import {validatePayload,validateReport,signHandle,verifyHandle} from '../worker/server.mjs';
import {workflowReport,workflowRequest,workflowId} from './helpers/workflow-fixture.mjs';
const c=globalThis.NabtWorkflowContract;
const expected=r=>({request_id:r.request_id,code_sha:r.code_sha,payload_sha256:r.payload_sha256,mode:r.mode,workflow_request_sha256:r.workflow_request_sha256});
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
