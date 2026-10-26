/* Display/transport consistency only. This module does not execute Lean or
   establish authenticity of an imported receipt. Authority comes from the
   authenticated pinned run, and only for its exact source-relative claim. */
(() => {
  'use strict';
  const encoder = new TextEncoder();
  const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const invalid = () => { throw new Error('REPORT_AUTHORITY_INVALID'); };
  const same = (a,b) => {
    if(a === b)return true;
    if(Array.isArray(a))return Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>same(v,b[i]));
    if(object(a)&&object(b)){const keys=Object.keys(a).sort();return same(keys,Object.keys(b).sort())&&keys.every(k=>same(a[k],b[k]));}
    return false;
  };
  function validateInference(report) {
    const r=report?.result;
    const checked=['SUPPORTED','REFUTED','CONFLICT','UNKNOWN','DEFER','DISAGREEMENT'];
    const unchecked=['UNKNOWN','INVALID_INPUT','SOURCE_UNAVAILABLE','VERIFICATION_UNAVAILABLE','RESOURCE_EXHAUSTED'];
    if(!object(r)||r.schema!=='nabt.licensed-inference-result.v1'||r.law_id!=='nabt.licensed-inference.v1'||r.accepted_language!=='nabt.explicit-subject-active.v1'||r.status!==report.status)invalid();
    for(const key of ['verified','native_checked','all_readings_complete','closures_checked'])if(typeof r[key]!=='boolean')invalid();
    for(const key of ['all_arabic_complete','world_truth_established','premise_world_truth_established','source_interpretation_historically_proved'])if(r[key]!==false)invalid();
    for(const key of ['strict_language_accepted','intended_sense_established','tawatur_established'])if(Object.hasOwn(r,key)&&r[key]!==false)invalid();
    if(!Array.isArray(r.readings)||!Array.isArray(r.closure_records)||!Array.isArray(r.assumptions)||r.assumptions.some(s=>typeof s!=='string'))invalid();
    if(!r.verified){
      if(r.native_checked||r.all_readings_complete||r.closures_checked||r.authority!=='UNVERIFIED_PROPOSAL'||!unchecked.includes(r.status)||r.readings.length||r.closure_records.length||r.native_result?.verified===true)invalid();
      return {checked:false, claim:null, strict_language_accepted:false};
    }
    if(!r.native_checked||!r.all_readings_complete||!r.closures_checked||r.authority!=='SOURCE_RELATIVE_CONSEQUENCE'||!checked.includes(r.status)||!hash(report.native_sha256)||r.readings.length===0||r.readings.length>64||r.readings.length!==r.closure_records.length||r.assumptions.length===0)invalid();
    const n=r.native_result,p=r.proposal,b=r.binding;
    if(!object(n)||!object(p)||!object(b)||n.verified!==true||n.law_id!==r.law_id||n.authority!==r.authority||n.status!==r.status||n.all_arabic_complete!==false||n.world_truth_established!==false||!Number.isSafeInteger(n.reading_count)||n.reading_count!==r.readings.length||!same(n.rows,r.readings)||!same(n.aggregate,r.aggregate)||p.law_id!==r.law_id||!same(p.readings,r.closure_records))invalid();
    for(const key of ['source','query']){
      const v=r[key];
      if(!object(v)||typeof v.raw_text!=='string'||!v.raw_text.trim()||!Number.isSafeInteger(v.bytes)||v.bytes!==encoder.encode(v.raw_text).length||!hash(v.sha256))invalid();
    }
    if(!object(p.source)||p.source.text!==r.source.raw_text||p.query_text!==r.query.raw_text||n.source_text!==r.source.raw_text||n.query_text!==r.query.raw_text||n.source_id!==r.source.source_id||n.revision!==r.source.revision||p.source.identity!==n.source_id||p.source.revision!==n.revision||p.source.scope!==n.source_scope||b.source_id!==n.source_id||b.revision!==n.revision||b.native_scope!==n.source_scope||b.authority!=='EXPLICIT_DISCOURSE_BINDING')invalid();
    // Bind this old live route to the actual request/commit, not a different
    // checked source which merely carries the same outer success flags.
    if(n.source_id!=='proof-lab:'+report.request_id||n.revision!==report.code_sha)invalid();
    if(typeof b.scope!=='string'||typeof b.time!=='string'||b.native_scope!==JSON.stringify({scope:b.scope,time:b.time}))invalid();
    for(let i=0;i<r.readings.length;i++){
      const row=r.readings[i],c=r.closure_records[i];
      if(!object(row)||!object(c)||!Array.isArray(c.clauses)||!same(row.clauses,c.clauses)||!same(row.query,c.query)||!checked.includes(row.status)||['positive','negative','clean_positive','clean_negative'].some(k=>typeof row[k]!=='boolean'))invalid();
      for(const key of ['steps','known','clean_steps','clean_known'])if(!Array.isArray(c[key]))invalid();
      const facts=c.clauses.filter(x=>x.kind==='fact'),rules=c.clauses.filter(x=>x.kind==='rule');
      for(const step of c.steps){if(!object(step)||!Number.isSafeInteger(step.index)||step.index<0||!['fact','rule'].includes(step.kind)||step.index>=(step.kind==='fact'?facts:rules).length)invalid();}
      // clean_steps index a filtered program; native verification owns that
      // refinement. The UI never reinterprets those indices as full steps.
    }
    return {checked:true, strict_language_accepted:false, claim:{
      id:'nabt.licensed-inference.v1:source-relative-consequence',law_id:r.law_id,
      status:r.status,source_sha256:r.source.sha256,query_sha256:r.query.sha256,
      native_sha256:report.native_sha256,source_id:n.source_id,revision:n.revision,
      discourse_binding:{...b},assumptions:[...r.assumptions],
      scope:'Installed finite active-voice grammar; source assertions are premises.',
      whole_arabic_complete:false,world_truth_established:false,
      full_A116_acquisition_claim:'NOT_CARRIED_BY_THIS_LEGACY_RECEIPT'
    }};
  }
  async function verifyInferenceDigests(report) {
    const view=validateInference(report);
    if(!view.checked)return view;
    for(const key of ['source','query']){
      const value=report.result[key];
      const actual=[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',encoder.encode(value.raw_text)))].map(x=>x.toString(16).padStart(2,'0')).join('');
      if(actual!==value.sha256)invalid();
    }
    return view;
  }
function validateTestimony(t,status){
  const deny=()=>invalid();
  if(!t||t.schema!=='nabt.lexical-testimony.v1'||t.law_id!=='nabt.lexical-denotation.v1'||t.status!==status||!Array.isArray(t.rows)||typeof t.native_checked!=='boolean'||typeof t.all_installed_readings_retained!=='boolean'||typeof t.app_disclaimer!=='string'||!t.app_disclaimer.trim())deny();
  for(const key of ['world_truth_established','all_arabic_complete','intended_sense_established','historical_authenticity_established'])if(t[key]!==false)deny();
  if(!t.native_checked){
    if(!['INVALID_INPUT','SOURCE_UNAVAILABLE','VERIFICATION_UNAVAILABLE','RESOURCE_EXHAUSTED'].includes(status)||t.authority!=='UNVERIFIED'||t.rows.length||t.all_installed_readings_retained||t.native_result)deny();
    return t;
  }
  if(!['CONDITIONAL_INTERPRETATIONS','UNMEASURED_ROOT'].includes(status)||t.authority!=='CONDITIONAL_INTERPRETATION_ONLY'||t.all_installed_readings_retained!==(status==='CONDITIONAL_INTERPRETATIONS')||(t.rows.length>0)!==t.all_installed_readings_retained)deny();
  const n=t.native_result,q=t.native_request;
  if(!n||!q||n.status!==status||n.authority!==t.authority||n.world_truth_asserted!==false||n.all_arabic_senses_enumerated!==false||n.complete_installed_proposal!==t.all_installed_readings_retained||!Array.isArray(n.rows)||n.rows.length!==t.rows.length||!Array.isArray(t.common_indications)||JSON.stringify(t.common_indications)!==JSON.stringify(n.common_indications)||q.root!==t.entry||JSON.stringify(q.target)!==JSON.stringify(t.target))deny();
  if(!/^[a-f0-9]{64}$/.test(t.native_sha256??'')||!/^[a-f0-9]{64}$/.test(t.catalogue_sha256??''))deny();
  const ids=t.rows.map(r=>r.sense_id);
  if(new Set(ids).size!==ids.length||JSON.stringify(ids)!==JSON.stringify(q.proposed_ids))deny();
  const sourceCheck=s=>{
    const c=s?.citation;
    if(!s||s.transmission_type!=='UNASSESSED'||s.historical_authenticity_established!==false||s.retained_catalogue_matched!==true||typeof s.source_file_replayed!=='boolean'||s.source_check!==(s.source_file_replayed?'RETAINED_SOURCE_BYTES_REPLAYED':'RETAINED_QUOTATION_ONLY')||!c||!Number.isSafeInteger(c.start_byte)||!Number.isSafeInteger(c.end_byte)||c.start_byte<0||c.end_byte<=c.start_byte||typeof c.quotation!=='string'||encoder.encode(c.quotation).length!==c.end_byte-c.start_byte)deny();
  };
  for(let i=0;i<t.rows.length;i++){
    const row=t.rows[i],native=n.rows[i];sourceCheck(row.testimony);
    if(row.causal_or_legal_conclusion_established!==false||row.interpretation_status!=='AUTHORED_NOT_INDEPENDENTLY_ADJUDICATED'||!Array.isArray(row.commitment_conditions)||!native?.sense||native.sense.id!==row.sense_id||JSON.stringify(native.sense.components)!==JSON.stringify(row.components)||['work','revision','source_sha256','start_byte','end_byte','quotation'].some(k=>native.sense.citation?.[k]!==row.testimony.citation[k])||!Array.isArray(native.indications))deny();
    for(const k of ['mutabaqa','tadammun','iltizam'])if(row.indications?.[k]!==native.indications.includes(k))deny();
    for(const c of row.commitment_conditions){if(c.relation!=='MENTAL_NECESSITY_PREMISE')deny();sourceCheck(c.source);}
  }
  return t;
}
  globalThis.NabtLegacyAuthority=Object.freeze({validateInference,verifyInferenceDigests,validateTestimony});
})();
