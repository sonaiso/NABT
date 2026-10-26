import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {inferenceFixture} from './helpers/inference-fixture.mjs';
import '../web/legacy-authority.js';
const ID='11111111-1111-4111-8111-111111111111',CODE='a'.repeat(40);
const authority=globalThis.NabtLegacyAuthority;
function report(){return {request_id:ID,code_sha:CODE,status:'SUPPORTED',native_sha256:'b'.repeat(64),result:inferenceFixture(ID,CODE)};}
const changes=[
 ['missing native result',r=>delete r.result.native_result],
 ['contradictory native verification',r=>r.result.native_result.verified=false],
 ['different source',r=>r.result.native_result.source_text+=' '],
 ['different query',r=>r.result.native_result.query_text+=' '],
 ['different discourse scope',r=>r.result.binding.native_scope='{}'],
 ['different request identity',r=>r.request_id='22222222-2222-4222-8222-222222222222'],
 ['different executable hash shape',r=>r.native_sha256=null],
 ['omitted reading',r=>r.result.readings=[]],
 ['omitted certificate',r=>r.result.closure_records=[]],
 ['altered proof step',r=>r.result.closure_records[0].steps[0].index=999],
 ['altered native aggregation',r=>r.result.native_result.aggregate.skeptical_clean_positive=false],
 ['fractional count',r=>r.result.native_result.reading_count=1.5],
 ['invented full acquisition',r=>r.result.strict_language_accepted=true],
 ['invented tawatur',r=>r.result.tawatur_established=true],
 ['invented external truth',r=>r.result.premise_world_truth_established=true],
];
for(const [name,change]of changes)test('legacy authority refuses '+name,()=>{const r=report();change(r);assert.throws(()=>authority.validateInference(r),/REPORT_AUTHORITY_INVALID/);});
test('complete legacy native bindings expose only the precise conditional claim',async()=>{
 globalThis.crypto??=webcrypto;const r=report(),v=await authority.verifyInferenceDigests(r);
 assert.equal(v.checked,true);assert.equal(v.strict_language_accepted,false);
 assert.equal(v.claim.source_id,'proof-lab:'+ID);assert.equal(v.claim.source_sha256,r.result.source.sha256);
 assert.equal(v.claim.full_A116_acquisition_claim,'NOT_CARRIED_BY_THIS_LEGACY_RECEIPT');
 assert.deepEqual(v.claim.assumptions,r.result.assumptions);
});
test('matching inner and outer forged source digests still fail actual byte hashing',async()=>{
 const r=report();r.result.source.sha256='0'.repeat(64);
 assert.equal(authority.validateInference(r).checked,true);
 await assert.rejects(authority.verifyInferenceDigests(r),/REPORT_AUTHORITY_INVALID/);
});
test('unverified failure without benchmark or native payload remains displayable',()=>{
 const r=report();r.status='RESOURCE_EXHAUSTED';r.result=inferenceFixture(ID,CODE,{status:r.status,verified:false,native_checked:false,all_readings_complete:false,closures_checked:false,authority:'UNVERIFIED_PROPOSAL'});
 const v=authority.validateInference(r);assert.equal(v.checked,false);assert.equal(v.claim,null);
});
