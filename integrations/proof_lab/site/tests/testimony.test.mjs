import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validatePayload,validateTestimony,validateReport,signHandle,verifyHandle} from '../worker/server.mjs';

// Recorded native response; used for transport mutation tests, not a new proof.
const fixture=JSON.parse(readFileSync(new URL('./fixtures/testimony.json',import.meta.url),'utf8'));
const request={schema:'nabt.proof-lab-request.v1',mode:'testimony',entry:'بيت',target:['المأوى']};
test('testimony transport cannot accept caller authority, grades or replacement meanings',()=>{
  assert.deepEqual(validatePayload(request),request);
  for(const k of ['is_verified_by_app','transmission_type','reliability_weight','rules','source_text','budget'])assert.throws(()=>validatePayload({...request,[k]:true}));
  for(const target of [null,'المأوى',[true],[1],[''],['\ud800'],Array(65).fill('x')])assert.throws(()=>validatePayload({...request,target}));
});
test('live testimony mode is bound into the signed handle',async()=>{
  const x={request_id:'11111111-1111-4111-8111-111111111111',payload_sha256:'a'.repeat(64),code_sha:'b'.repeat(40),mode:'testimony',created:Date.now()};
  const key='test-only-transport-key-not-production';
  assert.deepEqual(await verifyHandle(await signHandle(x,key),key),x);
});
test('conditional lexical receipt passes with independent source and interpretation fields',()=>{
  assert.equal(validateTestimony(fixture,fixture.status),fixture);
  assert.equal(fixture.rows[0].indications.tadammun,true);
  assert.equal(fixture.rows[0].testimony.transmission_type,'UNASSESSED');
});
test('contradictions, lossy integer spans, hidden senses and world promotions fail closed',()=>{
  const mutations=[
    t=>t.native_checked=false,t=>t.native_checked=1,t=>t.world_truth_established=true,
    t=>t.historical_authenticity_established=true,t=>t.intended_sense_established=true,
    t=>t.rows[0].testimony.transmission_type='متواتر',
    t=>t.rows[0].testimony.citation.start_byte=1.5,
    t=>t.rows[0].testimony.citation.start_byte=9007199254740992,
    t=>t.rows[0].testimony.source_file_replayed=false,
    t=>t.rows[0].causal_or_legal_conclusion_established=true,
    t=>t.rows[0].indications.iltizam=true,
    t=>t.rows[0].indications.tadammun=1,
    t=>t.rows=[],t=>t.native_request.proposed_ids=[],
    t=>t.native_result.world_truth_asserted=true,
    t=>t.native_result.complete_installed_proposal=false,
    t=>t.common_indications=['iltizam'],t=>t.native_request.target=['مزور'],
  ];
  for(const mutate of mutations){const t=structuredClone(fixture);mutate(t);assert.throws(()=>validateTestimony(t,t.status));}
});
test('valid unavailable receipts are retained without pretending a native result exists',()=>{
  for(const status of ['INVALID_INPUT','SOURCE_UNAVAILABLE','VERIFICATION_UNAVAILABLE','RESOURCE_EXHAUSTED']){
    const t={schema:fixture.schema,law_id:fixture.law_id,status,authority:'UNVERIFIED',native_checked:false,
      all_installed_readings_retained:false,rows:[],world_truth_established:false,all_arabic_complete:false,
      intended_sense_established:false,historical_authenticity_established:false,app_disclaimer:fixture.app_disclaimer};
    assert.equal(validateTestimony(t,status),t);
    assert.throws(()=>validateTestimony({...t,rows:fixture.rows},status));
  }
});
test('testimony receipt cannot be relabelled inference or mixed with a benchmark',()=>{
  const expected={request_id:'id',payload_sha256:'digest',code_sha:'commit',mode:'testimony'};
  const r={schema:'nabt.proof-lab-result.v1',...expected,status:fixture.status,testimony:fixture,all_arabic_complete:false,world_truth_established:false};
  assert.equal(validateReport(r,expected),r);
  assert.throws(()=>validateReport({...r,benchmark:{}},expected));
  assert.throws(()=>validateReport({...r,mode:'inference'},expected));
});
