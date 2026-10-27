/* Exact detached transport integrity only. Neither hashes nor this validator
   authenticate an imported receipt, execute Lean, or grant a proof authority.
   Existing domain validators remain mandatory for every displayed claim. */
(() => {
 'use strict';
 const LAB='tools.proof_lab.run_payload', GATEWAY='tools.licensed_workflow.run_request';
 const modes=new Set(['inference','testimony','benchmark','semantic_axes','epistemic_measurement','contextual_reference','licensed_workflow']);
 const laws={
  discourse_boundary:{EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE:['nabt.discourse-boundary-cue.v1']},
  source_inference:{SOURCE_BOUND_FINITE_INFERENCE:['nabt.licensed-inference.v1']},
  lexical_surface:{EXACT_WITNESSED_FORM_WITH_DECLARED_ANNOTATION:['nabt.lexical-surface-binding.v1'],EXACT_SOURCE_ROW_AND_ANNOTATION_FIELD_EXTRACTION:['nabt.lexical-source-acquisition.v1']},
  lexical_candidates:{A116_EXACT_INSTALLED_CANDIDATE_SET:['nabt.certified-lexical.v1'],A116_CONDITIONAL_SUPPORTED_USE:['nabt.certified-lexical.v1']},
  classical_control:{CLASSICAL_FINITE_CONTROL_EQUATION:['nabt.classical-weak.v1','nabt.classical-hamza.v1','nabt.classical-gemination.v1','nabt.classical-boundary-affixes.v1']},
  six_noun_acquisition:{SOURCE_BOUND_SIX_NOUN_CONSTRUCTION:['nabt.six-noun-acquisition.v1']},
  scope_acquisition:{EXACT_SCOPE_ENVELOPE:['nabt.scope-acquisition.v1']},
  lexical_transmission:{SOURCE_BOUND_REPORT_INVENTORY_AND_DEPENDENCY_CLASSIFICATION:['nabt.lexical-transmission.v1']}
 };
 const fail=reason=>{throw new Error('TRANSPORT_CONTRACT_INVALID:'+reason);};
 const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
 const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
 const exactKeys=(v,keys)=>object(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 function unicode(s){
  for(let i=0;i<s.length;i++){
   const c=s.charCodeAt(i);
   if(c>=0xd800&&c<=0xdbff){const d=s.charCodeAt(++i);if(!(d>=0xdc00&&d<=0xdfff))fail('unpaired_surrogate');}
   else if(c>=0xdc00&&c<=0xdfff)fail('unpaired_surrogate');
  }
 }
 function decimalIdentity(token){
  const m=/^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(token);
  if(!m||token.length>1024)fail('numeric_token');
  let digits=(m[2]+(m[3]||'')).replace(/^0+/, '');
  if(!digits)return '0';
  const trail=/0*$/.exec(digits)[0].length;
  if(trail)digits=digits.slice(0,-trail);
  const exponent=BigInt(m[4]||'0')-BigInt((m[3]||'').length)+BigInt(trail);
  return m[1]+digits+'e'+exponent.toString();
 }
 function exactNumber(token){
  const value=Number(token);
  if(!Number.isFinite(value)||(Number.isInteger(value)&&!Number.isSafeInteger(value)))fail('unsafe_number');
  // Compare decimal values, not binary rational expansions. Thus ordinary
  // metrics 0.1, 1.0 and 1e-6 are allowed; hidden discarded digits are not.
  if(decimalIdentity(token)!==decimalIdentity(String(value)))fail('lossy_numeric_conversion');
  return value;
 }
 function parseExactJSON(text){
  if(typeof text!=='string'||text.length>64*1024*1024)fail('json_size_or_type');
  unicode(text);
  let i=0;
  const space=()=>{while(i<text.length&&/[ \n\r\t]/.test(text[i]))i++;};
  function string(){
   const start=i++;
   while(i<text.length){
    const c=text[i++];
    if(c==='"'){let value;try{value=JSON.parse(text.slice(start,i));}catch{fail('json_string');}unicode(value);return value;}
    if(c==='\\')i++;
   }
   fail('unterminated_string');
  }
  function value(depth){
   if(depth>64)fail('json_depth');space();const c=text[i];
   if(c==='"')return string();
   if(c==='{'){
    i++;space();const out=Object.create(null), seen=new Set();
    if(text[i]==='}'){i++;return out;}
    while(true){
     space();if(text[i]!=='"')fail('object_key');const key=string();
     if(seen.has(key))fail('duplicate_key');seen.add(key);space();
     if(text[i++]!==':')fail('object_colon');out[key]=value(depth+1);space();
     const sep=text[i++];if(sep==='}')return out;if(sep!==',')fail('object_separator');
    }
   }
   if(c==='['){
    i++;space();const out=[];if(text[i]===']'){i++;return out;}
    while(true){out.push(value(depth+1));space();const sep=text[i++];if(sep===']')return out;if(sep!==',')fail('array_separator');}
   }
   for(const [literal,result]of [['true',true],['false',false],['null',null]])if(text.startsWith(literal,i)){i+=literal.length;return result;}
   const match=/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(i));
   if(!match)fail('json_value');i+=match[0].length;return exactNumber(match[0]);
  }
  const out=value(0);space();if(i!==text.length)fail('json_tail');return out;
 }
 function portable(v,depth=0,ancestors=new Set()){
  if(depth>64)fail('object_depth');
  if(v===null||typeof v==='boolean')return;
  if(typeof v==='string'){unicode(v);return;}
  if(typeof v==='number'){if(!Number.isFinite(v)||(Number.isInteger(v)&&!Number.isSafeInteger(v)))fail('unsafe_number');return;}
  if(!object(v)&&!Array.isArray(v))fail('non_json_value');
  if(ancestors.has(v))fail('cyclic_object');
  if(object(v)&&![Object.prototype,null].includes(Object.getPrototypeOf(v)))fail('non_plain_object');
  ancestors.add(v);
  for(const[k,x]of Object.entries(v)){unicode(k);portable(x,depth+1,ancestors);}
  ancestors.delete(v);
 }
 function same(a,b){
  if(typeof a!==typeof b)return false;
  if(a===null||b===null||typeof a!=='object')return Object.is(a,b)||a===b;
  if(Array.isArray(a)!==Array.isArray(b))return false;
  if(Array.isArray(a))return a.length===b.length&&a.every((v,i)=>same(v,b[i]));
  const keys=Object.keys(a);return keys.length===Object.keys(b).length&&keys.every(k=>Object.hasOwn(b,k)&&same(a[k],b[k]));
 }
 function claimAllowed(claim,operation){
  if(!object(claim)||typeof operation!=='string'||typeof claim.kind!=='string'
     ||!Object.hasOwn(laws,operation)||!Object.hasOwn(laws[operation],claim.kind)
     ||typeof claim.scope!=='string'||!claim.scope.trim()||!object(claim.proof)
     ||!laws[operation][claim.kind].includes(claim.proof.law_id)
     ||!Array.isArray(claim.proof.theorems)||!claim.proof.theorems.length
     ||claim.proof.theorems.some(t=>typeof t!=='string'||!t.startsWith('Nabt.')))fail('claim_policy');
 }
 function validateDetached(report,expectedEntrypoint){
  if(![LAB,GATEWAY].includes(expectedEntrypoint)||!object(report))fail('entrypoint');
  portable(report);
  const binding=report.transport_contract;
  const fields=['schema','entrypoint','command','policy_id','authority','input_binding','request','request_canonical','request_sha256',
   'child_response_canonical','child_response_sha256','child_response_bytes','named_claims','unresolved_premises',
   'transport_binding_kernel_proved','grants_language_license','all_arabic_complete'];
  if(!exactKeys(binding,fields)||binding.schema!=='nabt.transport-binding.v1'||binding.entrypoint!==expectedEntrypoint)fail('binding_fields');
  for(const field of ['transport_binding_kernel_proved','grants_language_license','all_arabic_complete'])if(binding[field]!==false)fail('metadata_authority');
  if(!hash(binding.request_sha256)||!hash(binding.child_response_sha256)
     ||!Number.isSafeInteger(binding.child_response_bytes)||binding.child_response_bytes<0
     ||typeof binding.child_response_canonical!=='string'||typeof binding.request_canonical!=='string'
     ||!Array.isArray(binding.named_claims)||binding.named_claims.length>128
     ||!Array.isArray(binding.unresolved_premises)||binding.unresolved_premises.some(v=>typeof v!=='string'||!v))fail('binding_values');
  if(!same(parseExactJSON(binding.request_canonical),binding.request))fail('request_bytes');
  const child={...report};delete child.transport_contract;
  if(!same(parseExactJSON(binding.child_response_canonical),child)
     ||new TextEncoder().encode(binding.child_response_canonical).length!==binding.child_response_bytes)fail('child_bytes');
  let claims=[],prefix='',operation=null;
  if(expectedEntrypoint===GATEWAY){
   if(binding.policy_id!=='nabt.licensed-workflow.named-claims.v1'||binding.authority!=='SCOPED_CHILD_CLAIMS_ONLY'
      ||binding.command!==report.operation||!Array.isArray(report.claims))fail('gateway_policy');
   operation=report.operation;claims=report.claims;
   if(operation!==null&&typeof operation!=='string')fail('operation_type');
   if(binding.input_binding==='UNBOUND_INVALID_INPUT'){
    if(!same(binding.request,{unrepresentable_request:true})||report.status!=='INVALID_INPUT'||claims.length||report.native_checked!==false)fail('invalid_input_binding');
   }else if(binding.input_binding==='EXACT_WORKFLOW_REQUEST_DIGEST'){
    if(!exactKeys(binding.request,['sha256','bytes'])||!hash(binding.request.sha256)
       ||!Number.isSafeInteger(binding.request.bytes)||binding.request.bytes<0
       ||report.request_sha256!==binding.request.sha256||report.status!=='RESOURCE_EXHAUSTED'
       ||claims.length||report.native_checked!==false)fail('resource_digest_binding');
   }else if(binding.input_binding==='EXACT_WORKFLOW_REQUEST'){
    if(operation!==null&&(!object(binding.request)||binding.request.op!==operation))fail('gateway_request_operation');
    if(Object.hasOwn(report,'request_sha256')&&report.request_sha256!==binding.request_sha256)fail('gateway_request_digest');
   }else fail('gateway_input_binding');
   if(!Object.hasOwn(laws,operation)){
    const failed=(operation===null&&['INVALID_INPUT','RESOURCE_EXHAUSTED'].includes(report.status))
       ||(typeof operation==='string'&&report.status==='DEFER'&&report.reason==='UNMIGRATED_OR_UNKNOWN_OPERATION');
    if(!failed||claims.length||report.native_checked!==false)fail('unknown_operation');
   }
   prefix='claims';
  }else{
   const mode=report.mode;
   if(mode!==null&&!modes.has(mode))fail('unknown_mode');
   if(binding.command!==mode||binding.policy_id!==`nabt.proof-lab.${mode||'invalid'}.v1`
      ||binding.authority!=='CHILD_DOMAIN_CONTRACT_RETAINED'||binding.input_binding!=='EXACT_PAYLOAD_DIGEST'
      ||!same(binding.request,{request_id:report.request_id,payload_sha256:report.payload_sha256}))fail('lab_policy');
   if(mode==='licensed_workflow'&&Object.hasOwn(report,'gateway_result')){
    validateDetached(report.gateway_result,GATEWAY);claims=report.gateway_result.claims;
    operation=report.gateway_result.operation;prefix='gateway_result.claims';
    if(!same(report.workflow_request,report.gateway_result.transport_contract.request))fail('nested_workflow_request');
   }
  }
  if(claims.length!==binding.named_claims.length)fail('named_claim_count');
  for(let i=0;i<claims.length;i++){
   const row=binding.named_claims[i],claim=claims[i];claimAllowed(claim,operation);
   if(!exactKeys(row,['child_path','claim_sha256','claim_canonical','kind','law_id'])
      ||row.child_path!==`${prefix}[${i}]`||!hash(row.claim_sha256)||row.kind!==claim.kind
      ||row.law_id!==claim.proof.law_id||!same(parseExactJSON(row.claim_canonical),claim))fail('claim_binding');
  }
  return report;
 }
 async function digest(text){
  if(typeof text!=='string')fail('digest_type');unicode(text);
  return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
 }
 async function verifyDetached(report,expectedEntrypoint){
  validateDetached(report,expectedEntrypoint);
  const binding=report.transport_contract;
  // Hash exact producer bytes. Never round-trip Python floats through JS.
  if(await digest(binding.request_canonical)!==binding.request_sha256
     ||await digest(binding.child_response_canonical)!==binding.child_response_sha256)fail('digest_mismatch');
  for(const row of binding.named_claims)if(await digest(row.claim_canonical)!==row.claim_sha256)fail('claim_digest');
  if(expectedEntrypoint===LAB&&report.mode==='licensed_workflow'&&Object.hasOwn(report,'gateway_result'))
   await verifyDetached(report.gateway_result,GATEWAY);
  return report;
 }
 globalThis.NabtTransportContract=Object.freeze({parseExactJSON,validateDetached,verifyDetached,digest});
})();
