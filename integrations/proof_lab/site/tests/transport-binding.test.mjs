import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import '../web/transport-contract.js';
globalThis.crypto??=webcrypto;
const c=globalThis.NabtTransportContract;
const LAB='tools.proof_lab.run_payload', GATEWAY='tools.licensed_workflow.run_request';
const sha=text=>createHash('sha256').update(text).digest('hex');
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':object(v)?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
function attach(child,{entrypoint=LAB,request={request_id:child.request_id,payload_sha256:child.payload_sha256},claims=[],paths=[],requestText,childText}={}){
 const workflow=entrypoint===GATEWAY;
 const req=requestText??canonical(request),response=childText??canonical(child);
 return {...child,transport_contract:{schema:'nabt.transport-binding.v1',entrypoint,
  command:workflow?child.operation:child.mode,
  policy_id:workflow?'nabt.licensed-workflow.named-claims.v1':`nabt.proof-lab.${child.mode||'invalid'}.v1`,
  authority:workflow?'SCOPED_CHILD_CLAIMS_ONLY':'CHILD_DOMAIN_CONTRACT_RETAINED',
  input_binding:workflow?'EXACT_WORKFLOW_REQUEST':'EXACT_PAYLOAD_DIGEST',request,
  request_canonical:req,request_sha256:sha(req),child_response_canonical:response,
  child_response_sha256:sha(response),child_response_bytes:Buffer.byteLength(response),
  named_claims:claims.map((claim,i)=>({child_path:paths[i],claim_sha256:sha(canonical(claim)),
   claim_canonical:canonical(claim),kind:claim.kind,law_id:claim.proof.law_id})),
  unresolved_premises:['TRANSPORT_METADATA_IS_NOT_KERNEL_PROOF'],transport_binding_kernel_proved:false,
  grants_language_license:false,all_arabic_complete:false}};
}
function lab(mode='benchmark',extra={}){
 return attach({schema:'nabt.proof-lab-result.v1',request_id:'r-independent',payload_sha256:'a'.repeat(64),
  mode,status:'BENCHMARK_COMPLETE',all_arabic_complete:false,world_truth_established:false,...extra});
}
function workflow(operation='scope_acquisition'){
 const request={schema:'nabt.licensed-workflow-request.v1',op:'scope_acquisition',input:{text:'قَالَ زَيْدٌ: «نَصٌّ»'}};
 const claim={kind:'EXACT_SCOPE_ENVELOPE',scope:'Only the exact declared scope envelope',
  proof:{law_id:'nabt.scope-acquisition.v1',theorems:['Nabt.ScopeAcquisition.acquired_exact']},origin_path:'claims[0]'};
 if(operation==='six_noun_acquisition'){request.op=operation;request.input.text='جَاءَ أَبُو زَيْدٍ';claim.kind='SOURCE_BOUND_SIX_NOUN_CONSTRUCTION';claim.proof.law_id='nabt.six-noun-acquisition.v1';}
 const gateway=attach({schema:'nabt.licensed-workflow-response.v1',operation:request.op,status:'CHECKED_SCOPE_ENVELOPE',
  claims:[claim],native_checked:true,strict_language_accepted:false,whole_arabic_complete:false,
  tawatur_established:false,world_truth_established:false,request_sha256:sha(canonical(request))},
  {entrypoint:GATEWAY,request,claims:[claim],paths:['claims[0]']});
 return attach({schema:'nabt.proof-lab-result.v1',request_id:'workflow-independent',payload_sha256:'b'.repeat(64),
  mode:'licensed_workflow',status:'LICENSED_WORKFLOW_COMPLETE',workflow_request:request,gateway_result:gateway,
  all_arabic_complete:false,world_truth_established:false},
  {claims:[claim],paths:['gateway_result.claims[0]']});
}
test('exact JSON parser retains genuine metric values without rounding hidden digits',()=>{
 for(const token of ['1','1.0','0.1','1e-6','0.000001','1.000e0','0.30000000000000004','-0.0','5e-324'])
  assert.equal(c.parseExactJSON(`{"metric":${token}}`).metric,Number(token));
 for(const token of ['1.0000000000000000001','0.10000000000000001','9007199254740993','9007199254740992',
                     '1e-324','1e309','NaN','Infinity','01','+1','1.'])
  assert.throws(()=>c.parseExactJSON(`{"metric":${token}}`),token);
});
test('exact JSON rejects duplicate keys even when Unicode escapes hide the duplicate',()=>{
 for(const text of ['{"a":1,"a":1}','{"a":1,"\\u0061":1}','{"x":{"native_checked":true,"native_checked":false}}',
                    '[1,]','{"a":1,}','{"a":true} false','{"x":"\\ud800"}'])assert.throws(()=>c.parseExactJSON(text),text);
 const parsed=c.parseExactJSON('{"__proto__":{"polluted":true},"constructor":"literal"}');
 assert.equal(Object.getPrototypeOf(parsed),null);assert.equal({}.polluted,undefined);
 assert.equal(parsed.__proto__.polluted,true);
});
for(const mode of ['inference','testimony','benchmark','semantic_axes','epistemic_measurement','contextual_reference'])
 test(`detached ${mode} metadata retains its old child authority with no named proof`,async()=>{
  const report=lab(mode,{metric:0.1});assert.equal(c.validateDetached(report,LAB),report);
  await c.verifyDetached(report,LAB);assert.deepEqual(report.transport_contract.named_claims,[]);
  assert.equal(report.transport_contract.transport_binding_kernel_proved,false);
 });
test('hashes exact Python float spelling rather than a JS reserialization',async()=>{
 const report=lab('benchmark',{metric:1});
 const raw=report.transport_contract.child_response_canonical.replace('"metric":1,','"metric":1.0,');
 assert.notEqual(raw,report.transport_contract.child_response_canonical);
 Object.assign(report.transport_contract,{child_response_canonical:raw,child_response_sha256:sha(raw),child_response_bytes:Buffer.byteLength(raw)});
 assert.equal(c.validateDetached(report,LAB),report);await c.verifyDetached(report,LAB);
});
test('rejects coherently rehashed lossy integer and duplicate verification declarations',()=>{
 for(const mutation of ['lossy','duplicate']){
  const report=lab('benchmark',{metric:1});
  const raw=report.transport_contract.child_response_canonical.replace('"metric":1,',mutation==='lossy'
   ?'"metric":1.0000000000000000001,':'"metric":1,"metric":1,');
  Object.assign(report.transport_contract,{child_response_canonical:raw,child_response_sha256:sha(raw),child_response_bytes:Buffer.byteLength(raw)});
  assert.throws(()=>c.validateDetached(report,LAB));
 }
});
test('valid failure receipt requires no benchmark payload',async()=>{
 const report=lab(null,{status:'INVALID_INPUT',request_id:null,payload_sha256:null});
 assert.equal(report.benchmark,undefined);await c.verifyDetached(report,LAB);
});
test('gateway unknown operation preserves a restricted deferral without proof',async()=>{
 const request={schema:'nabt.licensed-workflow-request.v1',op:'old-unmigrated-mode',input:{}};
 const report=attach({operation:request.op,status:'DEFER',reason:'UNMIGRATED_OR_UNKNOWN_OPERATION',
  native_checked:false,claims:[]},{entrypoint:GATEWAY,request});
 await c.verifyDetached(report,GATEWAY);
 report.status='SUPPORTED';assert.throws(()=>c.validateDetached(report,GATEWAY));
});
function resourceDigest(){
 const request={sha256:'c'.repeat(64),bytes:67108865};
 const report=attach({operation:null,status:'RESOURCE_EXHAUSTED',native_checked:false,claims:[],request_sha256:request.sha256},
  {entrypoint:GATEWAY,request});
 report.transport_contract.input_binding='EXACT_WORKFLOW_REQUEST_DIGEST';return report;
}
test('oversized request retains only its original digest and measured byte count',async()=>{
 const report=resourceDigest();await c.verifyDetached(report,GATEWAY);
 assert.notEqual(report.request_sha256,report.transport_contract.request_sha256);
 assert.deepEqual(Object.keys(report.transport_contract.request).sort(),['bytes','sha256']);
});
test('digest-only request cannot be promoted into a checked success',()=>{
 const report=resourceDigest();report.status='SUPPORTED';
 const child={...report};delete child.transport_contract;
 const forged=attach(child,{entrypoint:GATEWAY,request:report.transport_contract.request});
 forged.transport_contract.input_binding='EXACT_WORKFLOW_REQUEST_DIGEST';
 assert.throws(()=>c.validateDetached(forged,GATEWAY));
});
test('resource digest must bind the original request hash and exact byte count',()=>{
 for(const mutation of ['hash','bytes']){
  const report=resourceDigest();
  if(mutation==='hash')report.transport_contract.request.sha256='d'.repeat(64);
  else report.transport_contract.request.bytes=true;
  assert.throws(()=>c.validateDetached(report,GATEWAY));
 }
});
test('nested workflow binding checks exact claims, paths and request bytes',async()=>{
 const report=workflow();await c.verifyDetached(report,LAB);
 assert.equal(report.transport_contract.named_claims[0].child_path,'gateway_result.claims[0]');
 assert.equal(report.gateway_result.transport_contract.named_claims[0].child_path,'claims[0]');
 assert.equal(report.gateway_result.strict_language_accepted,false);
});
for(const [name,mutate] of [
 ['metadata proof promotion',r=>r.transport_contract.transport_binding_kernel_proved=true],
 ['metadata language promotion',r=>r.transport_contract.grants_language_license=true],
 ['unknown policy',r=>r.transport_contract.policy_id='invented'],
 ['unknown entrypoint',r=>r.transport_contract.entrypoint='invented'],
 ['unknown mode',r=>r.mode='execute-anything'],
 ['wrong request id',r=>r.transport_contract.request.request_id='different'],
 ['changed report field',r=>r.status='different'],
 ['integer byte count changed to boolean',r=>r.transport_contract.child_response_bytes=true],
 ['extra metadata authority',r=>r.transport_contract.native_checked=true],
 ['wrong child hash',r=>r.transport_contract.child_response_sha256='0'.repeat(64)],
 ['wrong request hash',r=>r.transport_contract.request_sha256='0'.repeat(64)]
])test(`transport refuses ${name}`,async()=>{const report=lab();mutate(report);await assert.rejects(c.verifyDetached(report,LAB));});
for(const [name,mutate] of [
 ['wrong nested claim path',r=>r.transport_contract.named_claims[0].child_path='gateway_result.result.claims[0]'],
 ['duplicate nested claim',r=>r.transport_contract.named_claims.push(r.transport_contract.named_claims[0])],
 ['wrong nested claim hash',r=>r.transport_contract.named_claims[0].claim_sha256='0'.repeat(64)],
 ['changed nested gateway',r=>r.gateway_result.claims[0].scope='all Arabic'],
 ['hidden nested metadata',r=>delete r.gateway_result.transport_contract],
 ['cross-context request',r=>r.workflow_request.input.text='different']
])test(`transport refuses ${name}`,async()=>{const report=workflow();mutate(report);await assert.rejects(c.verifyDetached(report,LAB));});
test('coherent rehash cannot turn another kind or law into an admitted gateway claim',()=>{
 for(const change of ['kind','law']){
  const report=workflow(),claim=report.gateway_result.claims[0];
  if(change==='kind')claim.kind='WHOLE_ARABIC';else claim.proof.law_id='invented.law';
  const gatewayChild={...report.gateway_result};delete gatewayChild.transport_contract;
  report.gateway_result=attach(gatewayChild,{entrypoint:GATEWAY,request:report.workflow_request,claims:[claim],paths:['claims[0]']});
  const outer={...report};delete outer.transport_contract;
  assert.throws(()=>c.validateDetached(attach(outer,{claims:[claim],paths:['gateway_result.claims[0]']}),LAB));
 }
});
test('non-workflow modes cannot borrow a nested named claim',()=>{
 const report=lab('testimony');
 report.transport_contract.named_claims=workflow().transport_contract.named_claims;
 assert.throws(()=>c.validateDetached(report,LAB));
});
test('transport verifier does not manufacture a proof-authority field',async()=>{
 const report=workflow();await c.verifyDetached(report,LAB);
 assert.equal(Object.hasOwn(report,'proof_authority_established'),false);
 assert.equal(report.transport_contract.grants_language_license,false);
});

test('six noun detached transport accepts only its explicitly named scoped claim',async()=>{
 const report=workflow('six_noun_acquisition');await c.verifyDetached(report,LAB);
 assert.equal(report.transport_contract.named_claims[0].kind,'SOURCE_BOUND_SIX_NOUN_CONSTRUCTION');
 assert.equal(report.transport_contract.named_claims[0].law_id,'nabt.six-noun-acquisition.v1');
 assert.equal(report.transport_contract.grants_language_license,false);
});
