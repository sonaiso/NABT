import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const specimen=JSON.parse(readFileSync(new URL('../fixtures/inference-native-source.json',import.meta.url),'utf8'));
// Structural specimen: raw_result L04 from independent_final.json. Test IDs,
// commit and optional text are explicitly rebound here; this helper is not
// evidence of a new native execution and is never used by the application.
export function bindInferenceFixture(value,requestId,codeSha){
  const r=structuredClone(value);
  r.schema='nabt.licensed-inference-result.v1'; r.law_id='nabt.licensed-inference.v1';
  r.accepted_language='nabt.explicit-subject-active.v1';
  r.assumptions??=['Source assertions are premises, not external observations.'];
  for(const key of ['all_arabic_complete','world_truth_established','premise_world_truth_established','source_interpretation_historically_proved'])r[key]=false;
  if(!r.verified){r.authority='UNVERIFIED_PROPOSAL';r.readings=[];r.closure_records=[];delete r.native_result;return r;}
  const identity='proof-lab:'+requestId, scope=JSON.stringify({scope:'proof-lab-single-discourse',time:'unspecified'});
  for(const key of ['source','query']){r[key].bytes=Buffer.byteLength(r[key].raw_text);r[key].sha256=createHash('sha256').update(r[key].raw_text).digest('hex');}
  r.source.source_id=identity;r.source.revision=codeSha;
  r.binding={source_id:identity,revision:codeSha,scope:'proof-lab-single-discourse',time:'unspecified',native_scope:scope,authority:'EXPLICIT_DISCOURSE_BINDING'};
  r.proposal={law_id:r.law_id,source:{identity,revision:codeSha,scope,text:r.source.raw_text},query_text:r.query.raw_text,readings:structuredClone(r.closure_records)};
  r.native_result={law_id:r.law_id,authority:r.authority,all_arabic_complete:false,world_truth_established:false,verified:true,status:r.status,source_id:identity,revision:codeSha,source_scope:scope,source_text:r.source.raw_text,query_text:r.query.raw_text,reading_count:r.readings.length,rows:structuredClone(r.readings),aggregate:structuredClone(r.aggregate)};
  return r;
}
export function inferenceFixture(requestId,codeSha,changes={}){
 const result=structuredClone(specimen);Object.assign(result,changes);
 return Object.assign(bindInferenceFixture(result,requestId,codeSha),changes);
}
