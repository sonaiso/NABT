import test from 'node:test';
import assert from 'node:assert/strict';
import {validatePayload,validateReport,signHandle,verifyHandle} from '../worker/server.mjs';
import {workflowReport,workflowRequest,workflowRequests,workflowId,workflowHash} from './helpers/workflow-fixture.mjs';
const c=globalThis.NabtWorkflowContract;
const expected=r=>({request_id:r.request_id,code_sha:r.code_sha,payload_sha256:r.payload_sha256,mode:r.mode,workflow_request_sha256:r.workflow_request_sha256});
for(const op of ['discourse_boundary','source_inference','six_noun_acquisition']){
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

function rehashWorkflow(report){
 report.adapter_result_json=c.canonical(report.gateway_result.result);
 report.gateway_result.result_sha256=workflowHash(report.adapter_result_json);
 report.gateway_result_json=c.canonical(report.gateway_result);
 report.gateway_result_sha256=workflowHash(report.gateway_result_json);
 return report;
}
for(const [name,change] of [
 ['native check without grammar',r=>r.grammar_certified=false],
 ['different source text',r=>r.source.text='جَاءَ أَبِي زَيْدٍ'],
 ['different source identity',r=>r.source.id='another source'],
 ['different context',r=>r.context='another context'],
 ['no acquired reading',r=>r.reading=null],
 ['unavailable canonical bridge',r=>r.orthographic_bridge.canonical_projection_complete=false],
 ['canonical bridge promoted to raw completeness',r=>r.foundation_complete=true],
 ['unrestored orthographic source',r=>r.orthographic_bridge.raw_reconstruction_checked=false],
 ['deferral promoted to proof',r=>r.status='DEFER'],
 ['authored rule promoted to truth',r=>r.world_truth_established=true],
 ['reference promoted to certainty',r=>r.speaker_reference_established=true],
 ['missing residual declaration',r=>delete r.residuals],
])test('six noun rejects '+name+' even with coherent transport hashes',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'});
 change(report.gateway_result.result);report.gateway_result.status=report.gateway_result.result.status;
 rehashWorkflow(report);assert.throws(()=>validateReport(report,expected(report)));
 await assert.rejects(c.verifyEnvelope(report));
});
test('six noun positive status without its sole named claim is rejected',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'});
 report.gateway_result.claims=[];report.gateway_result.result.claims=[];
 report.gateway_result.workflow_status='NO_SCOPED_CLAIMS';rehashWorkflow(report);
 await assert.rejects(c.verifyEnvelope(report));assert.equal(report.gateway_result.claims.length,0);
 assert.equal(report.gateway_result.result.source_projection_complete,false);
 assert.equal(report.gateway_result.result.foundation_complete,false);
});

test('six noun invalid input receipt may omit source and reading with no positive proof',async()=>{
 const report=workflowReport({op:'six_noun_acquisition',checked:false});
 const result=report.gateway_result.result;
 result.status='INVALID_INPUT';delete result.source;delete result.context;result.reading=null;
 report.gateway_result.status=result.status;rehashWorkflow(report);
 assert.equal(validateReport(report,expected(report)),report);await c.verifyEnvelope(report);
 assert.equal(report.gateway_result.claims.length,0);
});

function replaceSixNounClaim(report,claim){
 report.gateway_result.result.claims[0]=claim;
 report.gateway_result.claims[0]={...structuredClone(claim),origin_path:'claims[0]'};
}
for(const [name,mutate] of [
 ['source identity',claim=>claim.source.id='different source'],
 ['context',claim=>claim.context='different context'],
 ['reading',claim=>claim.reading.word='أَبِي'],
 ['request digest',claim=>claim.request_sha256='0'.repeat(64)],
 ['receipt digest',claim=>claim.receipt_sha256='0'.repeat(64)],
 ['source review digest',claim=>claim.source_review_sha256='0'.repeat(64)],
 ['unresolved premise list',claim=>claim.unresolved_premises=[]],
])test('six noun binds named claim '+name+' to the adapter after outer rehash',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'});
 const claim=structuredClone(report.gateway_result.result.claims[0]);mutate(claim);
 replaceSixNounClaim(report,claim);rehashWorkflow(report);
 assert.throws(()=>validateReport(report,expected(report)));await assert.rejects(c.verifyEnvelope(report));
});
for(const [name,mutate] of [
 ['source identity',n=>n.source.id='different source'],
 ['source revision',n=>n.source.revision='0'.repeat(64)],
 ['context',n=>n.context='different context'],
 ['reading',n=>n.reading.word='أَبِي'],
 ['grammar flag',n=>n.grammar_certified=false],
 ['status',n=>n.status='DEFER'],
 ['bridge',n=>n.orthographic_bridge.canonical='غير مطابق'],
 ['raw projection status',n=>n.source_projection.status='COMPLETE'],
 ['projection number',n=>n.source_projection.number='1'],
 ['source restoration',n=>n.source_restored=false],
 ['unresolved premises',n=>n.unresolved=['UNDECLARED_PREMISE']],
 ['intended sense',n=>n.intended_sense_established=true],
 ['external truth',n=>n.external_truth_established=true],
 ['language acceptance',n=>n.strict_language_accepted=true],
 ['Arabic completeness',n=>n.whole_arabic_complete=true],
])test('six noun binds native '+name+' to its adapter after outer rehash',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'});mutate(report.gateway_result.result.native_receipt);
 rehashWorkflow(report);assert.throws(()=>validateReport(report,expected(report)));
 await assert.rejects(c.verifyEnvelope(report));
});
test('six noun recomputes the exact native receipt digest rather than trusting its label',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),native=report.gateway_result.result.native_receipt;
 native.source_projection.cells=[0];native.source_projection.number='1';
 rehashWorkflow(report);assert.equal(validateReport(report,expected(report)),report);
 await assert.rejects(c.verifyEnvelope(report));
});
test('six noun recomputes the native request digest even when claim and adapter agree',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 r.request_sha256='0'.repeat(64);const claim=structuredClone(r.claims[0]);claim.request_sha256=r.request_sha256;
 replaceSixNounClaim(report,claim);rehashWorkflow(report);
 assert.equal(validateReport(report,expected(report)),report);await assert.rejects(c.verifyEnvelope(report));
});
test('six noun source revision is the exact raw UTF-8 digest, independently of receipt hashes',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 r.source.revision='0'.repeat(64);r.native_receipt.source.revision=r.source.revision;
 for(const node of r.node_trace)node.source.revision=r.source.revision;
 r.native_receipt.node_trace=structuredClone(r.node_trace);
 r.request_sha256=workflowHash({source:r.source,context:r.context});r.receipt_sha256=workflowHash(r.native_receipt);
 const claim=structuredClone(r.claims[0]);claim.source=structuredClone(r.source);claim.node_trace=structuredClone(r.node_trace);
 claim.request_sha256=r.request_sha256;claim.receipt_sha256=r.receipt_sha256;
 replaceSixNounClaim(report,claim);rehashWorkflow(report);
 assert.equal(validateReport(report,expected(report)),report);await assert.rejects(c.verifyEnvelope(report));
});
test('six noun checked deferral remains displayable with no grammar claim',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 r.status='DEFER';r.grammar_certified=false;r.native_receipt.status=r.status;r.native_receipt.grammar_certified=false;r.node_trace=[];r.native_receipt.node_trace=[];
 r.receipt_sha256=workflowHash(r.native_receipt);r.claims=[];
 report.gateway_result.status=r.status;report.gateway_result.claims=[];report.gateway_result.workflow_status='NO_SCOPED_CLAIMS';
 rehashWorkflow(report);await c.verifyEnvelope(report);assert.equal(report.gateway_result.native_checked,true);
 assert.equal(report.gateway_result.claims.length,0);
});

for(const [name,mutate] of [
 ['word',reading=>reading.word='أَبِي'],
 ['prefix',reading=>reading.prefix='رَأَيْتُ '],
 ['complement',reading=>reading.complement_text='عَمْرٍو'],
 ['fractional start',reading=>reading.start_byte=11.1],
 ['Boolean start',reading=>reading.start_byte=true],
 ['negative start',reading=>reading.start_byte=-1],
 ['codepoint offset',reading=>reading.start_byte=6],
 ['truncated end',reading=>reading.end_byte=20],
 ['oversized end',reading=>reading.end_byte=Number.MAX_SAFE_INTEGER],
])test('six noun source bytes reject coherently rehashed reading '+name,async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 mutate(r.reading);r.native_receipt.reading=structuredClone(r.reading);
 r.receipt_sha256=workflowHash(r.native_receipt);
 const claim=structuredClone(r.claims[0]);claim.reading=structuredClone(r.reading);claim.receipt_sha256=r.receipt_sha256;
 replaceSixNounClaim(report,claim);rehashWorkflow(report);
 assert.throws(()=>validateReport(report,expected(report)));await assert.rejects(c.verifyEnvelope(report));
});
test('six noun checked status cannot coexist with denied grammar even with no claims',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 r.grammar_certified=false;r.native_receipt.grammar_certified=false;r.claims=[];
 report.gateway_result.claims=[];report.gateway_result.workflow_status='NO_SCOPED_CLAIMS';
 r.receipt_sha256=workflowHash(r.native_receipt);rehashWorkflow(report);
 await assert.rejects(c.verifyEnvelope(report));
});
test('six noun positive result has one claim, never duplicate certificates',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 r.claims.push(structuredClone(r.claims[0]));
 report.gateway_result.claims.push({...structuredClone(r.claims[1]),origin_path:'claims[1]'});
 rehashWorkflow(report);await assert.rejects(c.verifyEnvelope(report));
});

function bindChangedTrace(report){
 const r=report.gateway_result.result;
 r.native_receipt.node_trace=structuredClone(r.node_trace);r.receipt_sha256=workflowHash(r.native_receipt);
 const claim=structuredClone(r.claims[0]);claim.node_trace=structuredClone(r.node_trace);claim.receipt_sha256=r.receipt_sha256;
 replaceSixNounClaim(report,claim);return rehashWorkflow(report);
}
for(const [name,change] of [
 ['missing node',trace=>trace.pop()],
 ['duplicate node',trace=>trace[2]=structuredClone(trace[1])],
 ['changed order',trace=>[trace[0],trace[1]]=[trace[1],trace[0]]],
 ['substituted rule',trace=>trace[1].rule_id='PREFIX_EXACT_V1'],
 ['different source',trace=>trace[1].source.id='another source'],
 ['different context',trace=>trace[1].context='another context'],
 ['different law',trace=>trace[1].law_id='unlicensed.law'],
 ['global scope',trace=>trace[1].scope='ALL_ARABIC'],
 ['different orthographic profile',trace=>trace[1].orthographic_profile='unlicensed.spelling'],
 ['different alphabet',trace=>trace[1].alphabet_id='unicode'],
 ['different number domain',trace=>trace[1].number_domain='utf8'],
 ['different review',trace=>trace[1].rule_source_review_sha256='0'.repeat(64)],
 ['missing passage',trace=>trace[1].passage_ids=[]],
 ['wrong passage',trace=>trace[1].passage_ids=['qatr_subject']],
 ['Boolean span',trace=>trace[1].start_byte=true],
 ['fractional span',trace=>trace[1].start_byte=11.5],
 ['different valid slice',trace=>{trace[1].start_byte=0;trace[1].end_byte=11;trace[1].raw='جَاءَ ';}],
 ['modified raw',trace=>trace[1].raw='أَبِي'],
 ['child order',trace=>trace[3].children.reverse()],
 ['unconsumed child output',trace=>trace[3].input_cells[0]=[0]],
 ['unconsumed child face',trace=>trace[3].input_faces[0].position=0],
 ['invalid output number',trace=>trace[3].output_number='0'],
 ['Boolean cell',trace=>trace[1].output_cells[0]=true],
 ['modified output face',trace=>trace[1].output_face.state=0],
 ['unknown treated as affirmed',trace=>trace[1].prerequisites[0].state='unknown'],
 ['lost prerequisites',trace=>trace[4].prerequisites=[]],
 ['invented alternatives',trace=>trace[1].alternatives=['all readings exhausted']],
 ['invented residuals',trace=>trace[1].unresolved=['SENSE_PROVED']],
 ['license contradiction',trace=>trace[1].licensed=false],
 ['extra authority flag',trace=>trace[1].world_truth_established=true],
])test('node trace rejects '+name+' even when every trace copy and hash agrees',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'});change(report.gateway_result.result.node_trace);
 bindChangedTrace(report);assert.throws(()=>validateReport(report,expected(report)));
 await assert.rejects(c.verifyEnvelope(report));
});
for(const location of ['native_receipt','claim'])test('node trace must match its '+location+' copy',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 if(location==='native_receipt'){r.native_receipt.node_trace[1].raw='أَبِي';r.receipt_sha256=workflowHash(r.native_receipt);
  const claim=structuredClone(r.claims[0]);claim.receipt_sha256=r.receipt_sha256;replaceSixNounClaim(report,claim);
 }else{const claim=structuredClone(r.claims[0]);claim.node_trace[1].raw='أَبِي';replaceSixNounClaim(report,claim);}
 rehashWorkflow(report);assert.throws(()=>validateReport(report,expected(report)));
 await assert.rejects(c.verifyEnvelope(report));
});
test('a deferred receipt cannot retain a positive node license trace',async()=>{
 const report=workflowReport({op:'six_noun_acquisition'}),r=report.gateway_result.result;
 r.status='DEFER';r.grammar_certified=false;r.native_receipt.status='DEFER';r.native_receipt.grammar_certified=false;
 r.receipt_sha256=workflowHash(r.native_receipt);r.claims=[];
 report.gateway_result.status='DEFER';report.gateway_result.claims=[];report.gateway_result.workflow_status='NO_SCOPED_CLAIMS';
 rehashWorkflow(report);await assert.rejects(c.verifyEnvelope(report));
});
