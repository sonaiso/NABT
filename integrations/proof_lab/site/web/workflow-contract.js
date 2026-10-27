/* Transport/display consistency for registered scoped native adapters.
   A browser validates a receipt; it never executes Lean or grants an imported
   receipt authenticity. Each proof remains attached to its original claim. */
(() => {
 'use strict';
 const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
 const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
 const deny=()=>{throw new Error('WORKFLOW_CONTRACT_INVALID');};
 const definitions={
  lexical_surface:{required:['text'],optional:['start_byte','end_byte','source_id','context','referent','time'],surface:'tools.linguistic_truth.surface.certify_surface',schema:'nabt.witnessed-surface-receipt.v2'},
  lexical_candidates:{required:['text'],optional:['profile_id','budget','source_id','subject','time','context'],surface:'tools.linguistic_truth.certified.acquire_certified',schema:'nabt.certified-linguistic-acquisition.v1'},
  classical_control:{required:['rule_id','frame'],optional:[],surface:'nabt.classical_certified.evaluate_certified',schema:'nabt.classical-certified-control.v1'},
  scope_acquisition:{required:['text'],optional:['source_id','context','profile_id'],surface:'tools.linguistic_truth.scopes.acquire_scope',schema:'nabt.scope-acquisition-receipt.v1'},
  lexical_transmission:{required:['entry'],optional:['context'],surface:'tools.lexical_transmission.assess_transmission',schema:'nabt.lexical-transmission-receipt.v1'}
 };
 function portable(v,depth=0){
  if(depth>32)deny();
  if(typeof v==='number'&&!Number.isSafeInteger(v))deny();
  if(typeof v==='string')for(let i=0;i<v.length;i++){const c=v.charCodeAt(i);if(c>=0xd800&&c<=0xdbff){const d=v.charCodeAt(++i);if(!(d>=0xdc00&&d<=0xdfff))deny();}else if(c>=0xdc00&&c<=0xdfff)deny();}
  if(Array.isArray(v))v.forEach(x=>portable(x,depth+1));
  else if(object(v))for(const[k,x]of Object.entries(v)){portable(k,depth+1);portable(x,depth+1);}
 }
 function compare(a,b){const x=Array.from(a,c=>c.codePointAt(0)),y=Array.from(b,c=>c.codePointAt(0));for(let i=0;i<Math.min(x.length,y.length);i++)if(x[i]!==y[i])return x[i]-y[i];return x.length-y.length;}
 function canonical(v){if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';if(object(v))return '{'+Object.keys(v).sort(compare).map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';return JSON.stringify(v);}
 const same=(a,b)=>canonical(a)===canonical(b);
 function validateRequest(r){
  if(!object(r)||!same(Object.keys(r).sort(),['input','op','schema'])||r.schema!=='nabt.licensed-workflow-request.v1'||!Object.hasOwn(definitions,r.op)||!object(r.input))deny();
  const d=definitions[r.op];if(d.required.some(k=>!Object.hasOwn(r.input,k))||Object.keys(r.input).some(k=>![...d.required,...d.optional].includes(k)))deny();
  portable(r);return r;
 }
 function validateEnvelope(report){
  if(report?.mode!=='licensed_workflow'||report.status!=='LICENSED_WORKFLOW_COMPLETE'||report.all_arabic_complete!==false||report.world_truth_established!==false||report.result||report.testimony||report.benchmark||report.semantic_axes||report.epistemic_measurement||report.contextual_reference)deny();
  const request=validateRequest(report.workflow_request),g=report.gateway_result,d=definitions[request.op],inv=report.migration_inventory;
  if(!object(g)||g.schema!=='nabt.licensed-workflow-response.v1'||g.operation!==request.op||typeof g.status!=='string'||!['SCOPED_CLAIMS_AVAILABLE','NO_SCOPED_CLAIMS'].includes(g.workflow_status)||typeof g.native_checked!=='boolean'||!Array.isArray(g.claims)||g.claims.length>128)deny();
  for(const k of ['strict_language_accepted','whole_arabic_complete','tawatur_established','world_truth_established'])if(g[k]!==false)deny();
  if(g.workflow_status!==(g.claims.length?'SCOPED_CLAIMS_AVAILABLE':'NO_SCOPED_CLAIMS')||g.display_contract?.proof_source!=='claims[*].proof'||g.display_contract?.native_checked_is_not_blanket_proof!==true)deny();
  if(!hash(report.workflow_request_sha256)||g.request_sha256!==report.workflow_request_sha256||!hash(report.gateway_result_sha256)||typeof report.gateway_result_json!=='string'||!same(JSON.parse(report.gateway_result_json),g))deny();
  if(!object(inv)||inv.schema!=='nabt.interface-migration-inventory.v1'||!hash(inv.registry_sha256)||inv.registry_sha256!==report.registry_sha256||inv.all_interfaces_migrated!==false||inv.whole_arabic_complete!==false||!Array.isArray(inv.surfaces)||!Number.isSafeInteger(inv.surface_count)||inv.surface_count!==inv.surfaces.length||!object(inv.states))deny();
  const ids=new Set(),counts={};
  for(const row of inv.surfaces){if(!object(row)||typeof row.surface_id!=='string'||ids.has(row.surface_id)||typeof row.migration_state!=='string'||row.whole_language_claim!==false||!Array.isArray(row.pending_obligations))deny();ids.add(row.surface_id);counts[row.migration_state]=(counts[row.migration_state]||0)+1;}
  if(!same(counts,inv.states))deny();
  if(g.result){
   const r=g.result;
   if(!object(r)||r.schema!==d.schema||g.surface_id!==d.surface||g.registry_sha256!==report.registry_sha256||r.status!==g.status||r.native_checked!==g.native_checked||r.strict_language_accepted!==false||!hash(g.result_sha256)||typeof report.adapter_result_json!=='string'||!same(JSON.parse(report.adapter_result_json),r))deny();
   const originals=Array.isArray(r.claims)?r.claims:[];
   const hasExtraction=request.op==='lexical_surface'&&object(r.source_acquisition);
   if(g.claims.length!==originals.length+(hasExtraction?1:0))deny();
   const origins=new Set();
   for(const claim of g.claims){
    if(!object(claim)||typeof claim.kind!=='string'||typeof claim.scope!=='string'||!claim.scope.trim()||!object(claim.proof)||typeof claim.proof.law_id!=='string'||!Array.isArray(claim.proof.theorems)||!claim.proof.theorems.length||claim.proof.theorems.some(x=>typeof x!=='string'||!x.startsWith('Nabt.'))||origins.has(claim.origin_path))deny();
    origins.add(claim.origin_path);
    if(claim.origin_path==='source_acquisition'){
     if(!hasExtraction||r.source_row_extraction_kernel_proved!==true||r.annotation_field_extraction_kernel_proved!==true||claim.kind!=='EXACT_SOURCE_ROW_AND_ANNOTATION_FIELD_EXTRACTION')deny();
     for(const[k,v]of Object.entries(r.source_acquisition))if(!same(claim[k],v))deny();
    }else{
     const match=/^claims\[(0|[1-9][0-9]*)\]$/.exec(claim.origin_path||'');
     if(!match||!r.native_checked)deny();const index=Number(match[1]);if(index>=originals.length)deny();
     const copy={...claim};delete copy.origin_path;if(!same(copy,originals[index]))deny();
    }
   }
  }else if(g.claims.length||g.native_checked||report.adapter_result_json!==null)deny();
  return report;
 }
 async function digest(text){return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(x=>x.toString(16).padStart(2,'0')).join('');}
 async function verifyEnvelope(report){
  validateEnvelope(report);
  if(await digest(canonical(report.workflow_request))!==report.workflow_request_sha256||await digest(report.gateway_result_json)!==report.gateway_result_sha256)deny();
  if(report.gateway_result.result&&await digest(report.adapter_result_json)!==report.gateway_result.result_sha256)deny();
  return report;
 }
 globalThis.NabtWorkflowContract=Object.freeze({validateRequest,validateEnvelope,verifyEnvelope,canonical,digest});
})();
