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
  six_noun_acquisition:{required:['text'],optional:['source_id','context'],surface:'tools.linguistic_truth.six_noun.acquire_six_noun',schema:'nabt.six-noun-acquisition-receipt.v1'},
  scope_acquisition:{required:['text'],optional:['source_id','context','profile_id'],surface:'tools.linguistic_truth.scopes.acquire_scope',schema:'nabt.scope-acquisition-receipt.v1'},
  discourse_boundary:{required:['text'],optional:['source_id','context','profile_id'],surface:'tools.linguistic_truth.discourse_boundary.acquire_discourse_boundary',schema:'nabt.discourse-boundary-receipt.v1'},
  source_inference:{required:['source','query'],optional:['source_id','revision','scope','time'],surface:'tools.transport_adapters.certify_inference',schema:'nabt.scoped-source-inference.v1'},
  lexical_transmission:{required:['entry'],optional:['context'],surface:'tools.lexical_transmission.assess_transmission',schema:'nabt.lexical-transmission-receipt.v1'}
 };
 const claimLaws={
  lexical_surface:{EXACT_WITNESSED_FORM_WITH_DECLARED_ANNOTATION:['nabt.lexical-surface-binding.v1']},
  lexical_candidates:{A116_EXACT_INSTALLED_CANDIDATE_SET:['nabt.certified-lexical.v1'],A116_CONDITIONAL_SUPPORTED_USE:['nabt.certified-lexical.v1']},
  classical_control:{CLASSICAL_FINITE_CONTROL_EQUATION:['nabt.classical-weak.v1','nabt.classical-hamza.v1','nabt.classical-gemination.v1','nabt.classical-boundary-affixes.v1']},
  six_noun_acquisition:{SOURCE_BOUND_SIX_NOUN_CONSTRUCTION:['nabt.six-noun-acquisition.v1']},
  scope_acquisition:{EXACT_SCOPE_ENVELOPE:['nabt.scope-acquisition.v1']},
  discourse_boundary:{EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE:['nabt.discourse-boundary-cue.v1']},
  source_inference:{SOURCE_BOUND_FINITE_INFERENCE:['nabt.licensed-inference.v1']},
  lexical_transmission:{SOURCE_BOUND_REPORT_INVENTORY_AND_DEPENDENCY_CLASSIFICATION:['nabt.lexical-transmission.v1']}
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
 const sixNounLaw='nabt.six-noun-acquisition.v1';
 const sixNounReview='315e6c067d9bacded9661bef043594be90437b73f1f695842d1d087d0dac0b8e';
 const sixNounResiduals=['SOURCE_AUTHENTICITY_NOT_ESTABLISHED','RULE_INTERPRETATION_IS_AUTHORED','REFERENCE_INTENT_AND_WORLD_TRUTH_NOT_ESTABLISHED'];
 function exactKeys(v,keys){return object(v)&&same(Object.keys(v).sort(),[...keys].sort());}
 function cellNumber(cells,number){
  if(!Array.isArray(cells)||cells.some(x=>!Number.isInteger(x)||x<0||x>=116)||typeof number!=='string'||!/^(0|[1-9][0-9]*)$/.test(number))deny();
  if(cells.reduce((n,a)=>116n*n+BigInt(a)+1n,0n).toString()!==number)deny();
 }
 function validateSixNoun(r,request,claims){
  if(r.law_id!==sixNounLaw||typeof r.grammar_certified!=='boolean'||typeof r.source_projection_complete!=='boolean'||typeof r.foundation_complete!=='boolean'||r.foundation_complete!==r.source_projection_complete||!Array.isArray(r.claims)||!Array.isArray(r.residuals)||r.residuals.some(x=>typeof x!=='string'))deny();
  for(const key of ['intended_sense_established','speaker_reference_established','world_truth_established','external_truth_established','tawatur_established','whole_arabic_complete','linguistic_rejection'])if(r[key]!==false)deny();
  if(Object.hasOwn(r,'source')&&(!exactKeys(r.source,['id','revision','text'])||r.source.text!==request.input.text||r.source.id!==(request.input.source_id??'user_text')||!hash(r.source.revision)||r.context!==(request.input.context??'unspecified')))deny();
  if(r.grammar_certified!==(r.status==='CHECKED_SIX_NOUN')||claims.length!==(r.grammar_certified?1:0))deny();
  if(!r.native_checked){
   if(Object.hasOwn(r,'native_receipt')||claims.length||r.grammar_certified||r.foundation_complete||r.reading!==null||r.orthographic_bridge!==null)deny();
   return;
  }
  const n=r.native_receipt;
  if(!exactKeys(n,['schema','law_id','source','context','source_projection','status','reading','grammar_certified','foundation_complete','orthographic_bridge','unresolved','source_restored','intended_sense_established','external_truth_established','strict_language_accepted','whole_arabic_complete'])||n.schema!==sixNounLaw||n.law_id!==sixNounLaw||!object(r.source)||!hash(r.request_sha256)||!hash(r.receipt_sha256)||!hash(r.executable_sha256)||r.source_review?.sha256!==sixNounReview)deny();
  for(const field of ['source','context','status','reading','grammar_certified','foundation_complete','orthographic_bridge','intended_sense_established','external_truth_established','strict_language_accepted','whole_arabic_complete'])if(!same(n[field],r[field]))deny();
  if(n.source_restored!==true||!Array.isArray(n.unresolved)||n.unresolved.some(x=>typeof x!=='string')||!same(r.residuals,[...sixNounResiduals,...n.unresolved]))deny();
  const projection=n.source_projection;
  if(!exactKeys(projection,['status','alphabet_id','number_domain','cells','number'])||!['COMPLETE','INCOMPLETE','INVALID'].includes(projection.status)||projection.alphabet_id!=='nabt.a116.v1'||projection.number_domain!=='nabt.foundation.projected-cells.bijective116.v1'||r.source_projection_complete!==(projection.status==='COMPLETE'))deny();
  cellNumber(projection.cells,projection.number);
  if(r.reading!==null){
   const reading=r.reading,fields=['governor','lexeme','ending','complement','prefix','word','complement_text','grammatical_case','observed_case','convention'];
   if(!exactKeys(reading,[...fields,'start_byte','end_byte','prerequisites','alternatives'])||fields.some(key=>typeof reading[key]!=='string')||!reading.word||!reading.complement_text||reading.prefix+reading.word+' '+reading.complement_text!==r.source.text||!Number.isSafeInteger(reading.start_byte)||!Number.isSafeInteger(reading.end_byte)||reading.start_byte<0||reading.end_byte<=reading.start_byte)deny();
   const bytes=text=>new TextEncoder().encode(text);
   if(reading.start_byte!==bytes(reading.prefix).length||reading.end_byte!==reading.start_byte+bytes(reading.word).length||reading.end_byte>bytes(r.source.text).length||!same(Array.from(bytes(r.source.text).slice(reading.start_byte,reading.end_byte)),Array.from(bytes(reading.word))))deny();
   if(!Array.isArray(reading.alternatives)||reading.alternatives.some(x=>typeof x!=='string')||!Array.isArray(reading.prerequisites)||reading.prerequisites.some(p=>!exactKeys(p,['name','state','origin'])||typeof p.name!=='string'||typeof p.origin!=='string'||!['affirmed','denied','unknown','not_applicable'].includes(p.state)))deny();
  }
  if(r.orthographic_bridge!==null){
   const bridge=r.orthographic_bridge;
   if(!exactKeys(bridge,['profile','raw','canonical','cells','number','raw_reconstruction_checked','canonical_projection_complete'])||bridge.profile!=='nabt.six-noun-exact-spelling.v1'||bridge.raw!==r.source.text||typeof bridge.canonical!=='string'||bridge.raw_reconstruction_checked!==true||typeof bridge.canonical_projection_complete!=='boolean')deny();
   cellNumber(bridge.cells,bridge.number);
  }
  if(r.grammar_certified&&(r.status!=='CHECKED_SIX_NOUN'||!object(r.reading)||r.orthographic_bridge?.canonical_projection_complete!==true))deny();
  if(claims.length&&(!r.grammar_certified||r.status!=='CHECKED_SIX_NOUN'))deny();
  for(const claim of claims){
   if(claim.id!=='SOURCE_BOUND_SIX_NOUN_CONSTRUCTION'||claim.authority!=='NATIVE_CHECKED'||claim.source_review_sha256!==r.source_review.sha256||!same(claim.unresolved_premises,r.residuals))deny();
   for(const field of ['source','context','reading','request_sha256','receipt_sha256'])if(!same(claim[field],r[field]))deny();
  }
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
   if(request.op==='six_noun_acquisition')validateSixNoun(r,request,originals);
   const hasExtraction=request.op==='lexical_surface'&&object(r.source_acquisition);
   if(g.claims.length!==originals.length+(hasExtraction?1:0))deny();
   const origins=new Set();
   for(const claim of g.claims){
    if(!object(claim)||typeof claim.kind!=='string'||typeof claim.scope!=='string'||!claim.scope.trim()||!object(claim.proof)||typeof claim.proof.law_id!=='string'||!Array.isArray(claim.proof.theorems)||!claim.proof.theorems.length||claim.proof.theorems.some(x=>typeof x!=='string'||!x.startsWith('Nabt.'))||origins.has(claim.origin_path))deny();
    origins.add(claim.origin_path);
    if(claim.origin_path==='source_acquisition'){
     if(claim.proof.law_id!=='nabt.lexical-source-acquisition.v1')deny();
     if(!hasExtraction||r.source_row_extraction_kernel_proved!==true||r.annotation_field_extraction_kernel_proved!==true||claim.kind!=='EXACT_SOURCE_ROW_AND_ANNOTATION_FIELD_EXTRACTION')deny();
     for(const[k,v]of Object.entries(r.source_acquisition))if(!same(claim[k],v))deny();
    }else{
     if(!Object.hasOwn(claimLaws[request.op],claim.kind)||!claimLaws[request.op][claim.kind].includes(claim.proof.law_id))deny();
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
  if(report.workflow_request.op==='six_noun_acquisition'&&report.gateway_result.result){
   const r=report.gateway_result.result;
   if(r.source&&await digest(r.source.text)!==r.source.revision)deny();
   if(r.native_checked&&(await digest(canonical({source:r.source,context:r.context}))!==r.request_sha256||await digest(canonical(r.native_receipt))!==r.receipt_sha256))deny();
  }
  return report;
 }
 globalThis.NabtWorkflowContract=Object.freeze({validateRequest,validateEnvelope,verifyEnvelope,canonical,digest});
})();
