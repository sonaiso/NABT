const REPOSITORY = 'sonaiso/NABT';
const WORKFLOW = 'proof-lab.yml';
const ALLOWED_REFS = ['codex/dynamic-proof-lab','codex/attested-testimony-live','codex/semantic-axes-reference'];
const REQUEST_SCHEMA = 'nabt.proof-lab-request.v1';
const MAX_PAYLOAD = 32768;
const MAX_REPORT = 2 * 1024 * 1024;
const MAX_RESULT = 3 * 1024 * 1024;
const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', {fatal:true});
const SHA = /^[a-f0-9]{40}$/;
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const LIMITS = {max_clauses:64,max_readings:64,max_atoms:256,max_closure_steps:256};
const securityHeaders = {'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Permissions-Policy':'camera=(), microphone=(), geolocation=()'};
class LabError extends Error { constructor(code,status=400){super(code);this.code=code;this.status=status;} }
function fail(code,status){throw new LabError(code,status);}
function json(value,status=200){return new Response(JSON.stringify(value),{status,headers:{...securityHeaders,'Content-Type':'application/json; charset=utf-8'}});}
function exactKeys(value,allowed){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!allowed.includes(k)))fail('INVALID_INPUT');}
function unicode(value){if(typeof value!=='string')fail('INVALID_INPUT');for(let i=0;i<value.length;i++){const n=value.charCodeAt(i);if(n>=0xd800&&n<=0xdbff){const next=value.charCodeAt(++i);if(!(next>=0xdc00&&next<=0xdfff))fail('INVALID_UNICODE');}else if(n>=0xdc00&&n<=0xdfff)fail('INVALID_UNICODE');}return value;}
export function validatePayload(value){
  if(value?.mode==='testimony'){
    exactKeys(value,['schema','mode','entry','target']);
    if(value.schema!==REQUEST_SCHEMA)fail('INVALID_INPUT');
    const entry=unicode(value.entry);
    if(!entry.trim()||encoder.encode(entry).length>128||!Array.isArray(value.target)||value.target.length>64)fail('INVALID_INPUT');
    for(const part of value.target)if(!unicode(part).trim()||encoder.encode(part).length>4096)fail('INVALID_INPUT');
    return {schema:REQUEST_SCHEMA,mode:'testimony',entry,target:value.target};
  }
  exactKeys(value,['schema','mode','source_text','query_text','budget']);
  if(value.schema!==REQUEST_SCHEMA||!['inference','benchmark','semantic_axes'].includes(value.mode))fail('INVALID_INPUT');
  if(['benchmark','semantic_axes'].includes(value.mode)){if(Object.keys(value).some(k=>!['schema','mode'].includes(k)))fail('INVALID_INPUT');return {schema:REQUEST_SCHEMA,mode:value.mode};}
  const source=unicode(value.source_text),query=unicode(value.query_text);
  if(!source.trim()||!query.trim()||encoder.encode(source).length>16384||encoder.encode(query).length>4096)fail('INPUT_LIMIT');
  const budget=Object.hasOwn(value,'budget')?value.budget:{};exactKeys(budget,Object.keys(LIMITS));
  for(const [key,n] of Object.entries(budget))if(typeof n!=='number'||!Number.isSafeInteger(n)||n<0||n>LIMITS[key])fail('INVALID_BUDGET');
  return {schema:REQUEST_SCHEMA,mode:'inference',source_text:source,query_text:query,budget};
}
export async function boundedBytes(body,limit){
  if(!body) return new Uint8Array();
  const reader=body.getReader();const parts=[];let size=0;
  try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>limit){await reader.cancel();fail('RESPONSE_LIMIT',502);}parts.push(value);}}
  finally{reader.releaseLock();}
  const out=new Uint8Array(size);let offset=0;for(const part of parts){out.set(part,offset);offset+=part.length;}return out;
}
async function sha(bytes){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
function base64url(bytes){let s='';for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function fromBase64(value){if(!/^[A-Za-z0-9_-]+$/.test(value))fail('INVALID_HANDLE',403);try{return Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));}catch{fail('INVALID_HANDLE',403);}}
async function key(secret){return crypto.subtle.importKey('raw',encoder.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);}
export async function signHandle(data,secret){const raw=encoder.encode(JSON.stringify(data));const signature=await crypto.subtle.sign('HMAC',await key(secret),raw);return base64url(raw)+'.'+base64url(new Uint8Array(signature));}
export async function verifyHandle(handle,secret,now=Date.now()){
  if(typeof handle!=='string'||handle.length>2048)fail('INVALID_HANDLE',403);const pieces=handle.split('.');if(pieces.length!==2)fail('INVALID_HANDLE',403);
  const raw=fromBase64(pieces[0]);if(!await crypto.subtle.verify('HMAC',await key(secret),fromBase64(pieces[1]),raw))fail('INVALID_HANDLE',403);
  let data;try{data=JSON.parse(decoder.decode(raw));}catch{fail('INVALID_HANDLE',403);}
  exactKeys(data,['request_id','payload_sha256','code_sha','mode','created']);
  if(!UUID.test(data.request_id)||!SHA.test(data.code_sha)||! /^[a-f0-9]{64}$/.test(data.payload_sha256)||!['inference','benchmark','testimony','semantic_axes'].includes(data.mode)||!Number.isSafeInteger(data.created)||data.created>now+30000||now-data.created>86400000)fail('EXPIRED_OR_INVALID_HANDLE',403);
  return data;
}
function standard64(bytes){let s='';for(const b of bytes)s+=String.fromCharCode(b);return btoa(s);}
function decode64(value,max){if(typeof value!=='string'||value.length>Math.ceil(max/3)*4||!/^[A-Za-z0-9+/]*={0,2}$/.test(value))fail('ENCRYPTED_PAYLOAD_INVALID',502);let raw;try{raw=atob(value);}catch{fail('ENCRYPTED_PAYLOAD_INVALID',502);}if(btoa(raw)!==value||raw.length>max)fail('ENCRYPTED_PAYLOAD_INVALID',502);return Uint8Array.from(raw,c=>c.charCodeAt(0));}
async function transportKey(hex){if(typeof hex!=='string'||! /^[a-f0-9]{64}$/.test(hex))fail('TRANSPORT_NOT_CONFIGURED',503);return crypto.subtle.importKey('raw',Uint8Array.from(hex.match(/../g),s=>parseInt(s,16)),{name:'AES-GCM'},false,['encrypt','decrypt']);}
export async function encryptEnvelope(text,keyHex,requestId){
  if(typeof text!=='string'||!UUID.test(requestId))fail('ENCRYPTED_PAYLOAD_INVALID',502);
  const nonce=crypto.getRandomValues(new Uint8Array(12));
  const bytes=await crypto.subtle.encrypt({name:'AES-GCM',iv:nonce,additionalData:encoder.encode(requestId),tagLength:128},await transportKey(keyHex),encoder.encode(text));
  return {schema:'nabt.proof-lab-envelope.v1',nonce:standard64(nonce),ciphertext:standard64(new Uint8Array(bytes))};
}
export async function decryptEnvelope(envelope,keyHex,requestId,maxBytes=MAX_REPORT){
  try{exactKeys(envelope,['schema','nonce','ciphertext']);}catch{fail('ENCRYPTED_PAYLOAD_INVALID',502);}if(envelope.schema!=='nabt.proof-lab-envelope.v1'||!UUID.test(requestId))fail('ENCRYPTED_PAYLOAD_INVALID',502);
  const nonce=decode64(envelope.nonce,12),cipher=decode64(envelope.ciphertext,maxBytes+16);if(nonce.length!==12||cipher.length<16)fail('ENCRYPTED_PAYLOAD_INVALID',502);
  try{const bytes=await crypto.subtle.decrypt({name:'AES-GCM',iv:nonce,additionalData:encoder.encode(requestId),tagLength:128},await transportKey(keyHex),cipher);return decoder.decode(bytes);}catch{fail('ENCRYPTED_PAYLOAD_INVALID',502);}
}
function configured(env){return env.NABT_EXECUTION_ENABLED==='true'&&/^[a-f0-9]{64}$/.test(env.NABT_TRANSPORT_KEY??'')&&typeof env.NABT_GITHUB_TOKEN==='string'&&env.NABT_GITHUB_TOKEN.length>0&&typeof env.NABT_SIGNING_KEY==='string'&&env.NABT_SIGNING_KEY.length>=32&&SHA.test(env.NABT_CODE_SHA??'')&&ALLOWED_REFS.includes(env.NABT_REF);}
async function gh(env,path,options={}){
  const response=await fetch('https://api.github.com/repos/'+REPOSITORY+path,{...options,redirect:'manual',signal:AbortSignal.timeout(20000),headers:{'Authorization':'Bearer '+env.NABT_GITHUB_TOKEN,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'NABT-Proof-Lab','Content-Type':'application/json'}});
  if(!response.ok&&response.status!==302){const code=response.status===401||response.status===403?'GITHUB_ACCESS_UNAVAILABLE':response.status===429?'GITHUB_RATE_LIMIT':'GITHUB_REQUEST_FAILED';fail(code,502);}
  return response;
}
async function ghJson(env,path,options){const response=await gh(env,path,options);if(response.status===204)return null;const bytes=await boundedBytes(response.body,4*1024*1024);try{return JSON.parse(decoder.decode(bytes));}catch{fail('GITHUB_RESPONSE_INVALID',502);}}
function checkOrigin(request,url){const origin=request.headers.get('Origin');if((origin&&origin!==url.origin)||request.headers.get('Sec-Fetch-Site')==='cross-site')fail('CROSS_ORIGIN_DENIED',403);}
function activeRuns(runs,ref){return runs.filter(r=>r.event==='workflow_dispatch'&&r.head_branch===ref);}
async function submit(request,env){
  const url=new URL(request.url);checkOrigin(request,url);
  if(!(request.headers.get('Content-Type')??'').toLowerCase().startsWith('application/json'))fail('JSON_REQUIRED',415);
  let input;try{input=JSON.parse(decoder.decode(await boundedBytes(request.body,MAX_PAYLOAD)));}catch(e){if(e instanceof LabError){if(e.code==='RESPONSE_LIMIT')fail('INPUT_LIMIT',413);throw e;}fail('INVALID_JSON');}
  const payload=JSON.stringify(validatePayload(input));
  const ref=await ghJson(env,'/git/ref/heads/'+encodeURIComponent(env.NABT_REF));
  if(ref.object?.sha!==env.NABT_CODE_SHA)fail('BACKEND_VERSION_CHANGED',409);
  const recent=await ghJson(env,'/actions/workflows/'+WORKFLOW+'/runs?event=workflow_dispatch&branch='+encodeURIComponent(env.NABT_REF)+'&per_page=30');
  if(!Array.isArray(recent.workflow_runs))fail('GITHUB_RESPONSE_INVALID',502);
  const now=Date.now();if(activeRuns(recent.workflow_runs,env.NABT_REF).some(r=>r.status!=='completed'||now-Date.parse(r.created_at)<30000))fail('RUN_ALREADY_ACTIVE',429);
  const descriptor={request_id:crypto.randomUUID(),payload_sha256:await sha(encoder.encode(payload)),code_sha:env.NABT_CODE_SHA,mode:input.mode,created:now};
  await ghJson(env,'/actions/workflows/'+WORKFLOW+'/dispatches',{method:'POST',body:JSON.stringify({ref:env.NABT_REF,inputs:{request_id:descriptor.request_id,payload:JSON.stringify(await encryptEnvelope(payload,env.NABT_TRANSPORT_KEY,descriptor.request_id))}})});
  return json({handle:await signHandle(descriptor,env.NABT_SIGNING_KEY),request_id:descriptor.request_id,status:'queued',poll_after_ms:5000},202);
}
function u16(view,pos){if(pos<0||pos+2>view.byteLength)fail('ARTIFACT_ZIP_INVALID',502);return view.getUint16(pos,true);}
function u32(view,pos){if(pos<0||pos+4>view.byteLength)fail('ARTIFACT_ZIP_INVALID',502);return view.getUint32(pos,true);}
function crc32(bytes){let crc=0xffffffff;for(const b of bytes){crc^=b;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
export async function unpackResult(bytes){
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);let eocd=-1;
  for(let p=bytes.length-22;p>=Math.max(0,bytes.length-65557);p--)if(u32(view,p)===0x06054b50&&p+22+u16(view,p+20)===bytes.length){eocd=p;break;}
  if(eocd<0||u16(view,eocd+4)!==0||u16(view,eocd+6)!==0||u16(view,eocd+8)!==1||u16(view,eocd+10)!==1)fail('ARTIFACT_ZIP_INVALID',502);
  const central=u32(view,eocd+16),centralSize=u32(view,eocd+12);if(central+centralSize!==eocd||u32(view,central)!==0x02014b50)fail('ARTIFACT_ZIP_INVALID',502);
  const flags=u16(view,central+8),method=u16(view,central+10),crc=u32(view,central+16),packed=u32(view,central+20),size=u32(view,central+24),nameLen=u16(view,central+28),extraLen=u16(view,central+30),commentLen=u16(view,central+32),local=u32(view,central+42);
  const name=decoder.decode(bytes.subarray(central+46,central+46+nameLen));
  if(name!=='result.json'||(flags&1)||![0,8].includes(method)||size>MAX_RESULT||packed>4*1024*1024||central+46+nameLen+extraLen+commentLen!==eocd||u32(view,local)!==0x04034b50||u16(view,local+8)!==method||u16(view,local+6)!==flags)fail('ARTIFACT_ZIP_INVALID',502);
  const localNameLen=u16(view,local+26),start=local+30+localNameLen+u16(view,local+28);
  if(decoder.decode(bytes.subarray(local+30,local+30+localNameLen))!==name||start+packed>central)fail('ARTIFACT_ZIP_INVALID',502);
  const body=bytes.slice(start,start+packed);let result;
  if(method===0)result=body;else result=await boundedBytes(new Blob([body]).stream().pipeThrough(new DecompressionStream('deflate-raw')),MAX_RESULT);
  if(result.length!==size||crc32(result)!==crc)fail('ARTIFACT_CHECKSUM_FAILED',502);
  try{return JSON.parse(decoder.decode(result));}catch{fail('ARTIFACT_JSON_INVALID',502);}
}
export function validateReport(report,expected){
  if(!report||report.schema!=='nabt.proof-lab-result.v1'||report.request_id!==expected.request_id||report.payload_sha256!==expected.payload_sha256||report.code_sha!==expected.code_sha||report.mode!==expected.mode||report.all_arabic_complete!==false||report.world_truth_established!==false)fail('REPORT_BINDING_FAILED',502);
  const errorStatuses=['INVALID_INPUT','RESOURCE_EXHAUSTED','EXECUTION_FAILED','VERIFICATION_UNAVAILABLE'];
  if(Object.hasOwn(report,'error')){if(typeof report.error!=='string'||report.error.length>128||!errorStatuses.includes(report.status)||report.result||report.benchmark||report.testimony||report.semantic_axes)fail('REPORT_AUTHORITY_INVALID',502);return report;}
  if(report.mode==='semantic_axes'){
    if(report.result||report.benchmark||report.testimony||report.native_sha256!==null||report.status!=='SEMANTIC_AXES_COMPLETE')fail('REPORT_AUTHORITY_INVALID',502);
    validateSemanticAxes(report.semantic_axes);
    if(report.reference_sha256!==report.semantic_axes.reference_sha256||report.runtime_sha256!==report.semantic_axes.adapter_sha256)fail('REPORT_BINDING_FAILED',502);
    return report;
  }
  if(report.semantic_axes)fail('REPORT_AUTHORITY_INVALID',502);
  if(report.mode==='testimony'){
    validateTestimony(report.testimony,report.status);
    if(report.result||report.benchmark)fail('REPORT_AUTHORITY_INVALID',502);
    if(report.testimony.native_checked&&(report.native_sha256!==report.testimony.native_sha256||report.catalogue_sha256!==report.testimony.catalogue_sha256))fail('REPORT_BINDING_FAILED',502);
    return report;
  }
  if(report.testimony)fail('REPORT_AUTHORITY_INVALID',502);
  if(report.mode==='inference'){
    const r=report.result;
    const statuses=['SUPPORTED','REFUTED','CONFLICT','UNKNOWN','DEFER','DISAGREEMENT','INVALID_INPUT','SOURCE_UNAVAILABLE','VERIFICATION_UNAVAILABLE','RESOURCE_EXHAUSTED'];
    if(!r||r.schema!=='nabt.licensed-inference-result.v1'||r.law_id!=='nabt.licensed-inference.v1'||!statuses.includes(r.status)||r.status!==report.status||['verified','native_checked','all_readings_complete','closures_checked'].some(k=>typeof r[k]!=='boolean')||r.all_arabic_complete!==false||r.world_truth_established!==false||report.benchmark)fail('REPORT_AUTHORITY_INVALID',502);
    const measured=['SUPPORTED','REFUTED','CONFLICT','DEFER','DISAGREEMENT'];
    if(r.verified&&(!r.native_checked||!r.all_readings_complete||!r.closures_checked||r.authority!=='SOURCE_RELATIVE_CONSEQUENCE'||![...measured,'UNKNOWN'].includes(r.status)))fail('REPORT_AUTHORITY_INVALID',502);
    if(!r.verified&&(r.native_checked||r.all_readings_complete||r.closures_checked||r.authority!=='UNVERIFIED_PROPOSAL'||measured.includes(r.status)))fail('REPORT_AUTHORITY_INVALID',502);
  }else{
    const b=report.benchmark,summary=b?.summary;
    if(!b||!summary||!Array.isArray(b.rows)||!['BENCHMARK_COMPLETE','BENCHMARK_CONTRACT_FAILURE'].includes(report.status)||report.result||typeof b.contract_gate?.passed!=='boolean'||(report.status==='BENCHMARK_COMPLETE')!==b.contract_gate.passed)fail('REPORT_AUTHORITY_INVALID',502);
    for(const k of ['cases','pass','fail','unmeasured'])if(!Number.isSafeInteger(summary[k])||summary[k]<0)fail('REPORT_AUTHORITY_INVALID',502);
    if(summary.cases!==38||b.rows.length!==summary.cases||summary.pass+summary.fail+summary.unmeasured!==summary.cases)fail('REPORT_AUTHORITY_INVALID',502);
  }
  return report;
}

// v1 measures the Python reader. No Lean-proof declaration is supported here.
export function validateSemanticAxes(suite){
  const deny=()=>fail('REPORT_AUTHORITY_INVALID',502);
  const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
  const text=v=>typeof v==='string'&&v.trim().length>0;
  const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
  const integer=v=>Number.isSafeInteger(v)&&v>=0;
  const axes=['syntax','readings','reference','motive','world'];
  const states=['PASS','FAIL','UNMEASURED','NOT_APPLICABLE'];
  if(!object(suite)||suite.schema!=='nabt.semantic-axes-benchmark.v1'||suite.case_count!==25||!Array.isArray(suite.cases)||suite.cases.length!==suite.case_count||!object(suite.axes)||!text(suite.scope))deny();
  if(!hash(suite.reference_sha256)||!hash(suite.adapter_sha256)||!hash(suite.input_suite_sha256)||suite.lean_native_checked!==false||suite.all_arabic_complete!==false)deny();
  const counts=Object.fromEntries(axes.map(a=>[a,{eligible:0,measured:0,passed:0,failed:0,unmeasured:0}]));
  const ids=new Set();
  for(const row of suite.cases){
    if(!object(row)||!text(row.id)||ids.has(row.id)||!text(row.context_id)||!hash(row.case_input_sha256)||!object(row.input)||!text(row.input.text)||!object(row.input.context)||!object(row.axis_results)||!Array.isArray(row.claims)||row.claims.length!==axes.filter(a=>row.axis_results[a]?.status!=='NOT_APPLICABLE').length)deny();
    ids.add(row.id);
    for(const axis of axes){
      const result=row.axis_results[axis], c=counts[axis];
      if(!object(result)||!states.includes(result.status))deny();
      if(result.status==='NOT_APPLICABLE')continue;
      c.eligible++;
      if(result.status==='UNMEASURED')c.unmeasured++;
      else{c.measured++;c[result.status==='PASS'?'passed':'failed']++;}
    }
    const claimAxes=new Set();
    for(const claim of row.claims){
      const v=claim?.verification;
      if(!object(claim)||!axes.includes(claim.axis)||claimAxes.has(claim.axis)||claim.id!==row.id+':'+claim.axis||!text(claim.statement)||claim.status!==row.axis_results[claim.axis].status||!object(v)||typeof v.checked!=='boolean'||!text(v.scope)||!Array.isArray(v.theorem_references)||v.theorem_references.length!==0)deny();
      claimAxes.add(claim.axis);
      if(v.claim_id!==claim.id||v.input_sha256!==row.case_input_sha256)deny();
      const measured=['PASS','FAIL'].includes(claim.status);
      if(v.checked!==measured||v.kind!==(measured?'PYTHON_REPLAY':'NOT_CHECKED'))deny();
      if(measured?!hash(v.certificate_sha256):v.certificate_sha256!=null)deny();
    }
  }
  if(Object.keys(suite.axes).length!==axes.length)deny();
  for(const axis of axes){
    const actual=counts[axis], declared=suite.axes[axis];
    if(!object(declared)||Object.keys(actual).some(k=>!integer(declared[k])||declared[k]!==actual[k]))deny();
    if(actual.measured===0?declared.rate!==null:typeof declared.rate!=='number'||!Number.isFinite(declared.rate)||Math.abs(declared.rate-actual.passed/actual.measured)>1e-12)deny();
  }
  return suite;
}

export function validateTestimony(t,status){
  const deny=()=>fail('REPORT_AUTHORITY_INVALID',502);
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
async function downloadResult(env,artifact){
  if(!Number.isSafeInteger(artifact.id)||artifact.expired||artifact.size_in_bytes>4*1024*1024||!/^sha256:[a-f0-9]{64}$/.test(artifact.digest??''))fail('ARTIFACT_UNAVAILABLE',502);
  const redirect=await gh(env,'/actions/artifacts/'+artifact.id+'/zip');
  if(redirect.status!==302)fail('ARTIFACT_REDIRECT_INVALID',502);
  let url;try{url=new URL(redirect.headers.get('Location'));}catch{fail('ARTIFACT_REDIRECT_INVALID',502);}
  if(url.protocol!=='https:'||url.username||url.password||!(url.hostname.endsWith('.blob.core.windows.net')||url.hostname.endsWith('.githubusercontent.com')))fail('ARTIFACT_REDIRECT_INVALID',502);
  // Workers supports manual/follow, not Fetch's error mode. Keep redirects
  // forbidden explicitly, and never forward GitHub credentials to the CDN.
  const response=await fetch(url,{redirect:'manual',signal:AbortSignal.timeout(20000)});
  if(response.status>=300&&response.status<400)fail('ARTIFACT_REDIRECT_INVALID',502);
  if(!response.ok)fail('ARTIFACT_UNAVAILABLE',502);
  const bytes=await boundedBytes(response.body,4*1024*1024);
  if('sha256:'+await sha(bytes)!==artifact.digest)fail('ARTIFACT_DIGEST_FAILED',502);
  return unpackResult(bytes);
}
async function poll(url,env){
  const expected=await verifyHandle(url.searchParams.get('handle'),env.NABT_SIGNING_KEY);
  if(expected.code_sha!==env.NABT_CODE_SHA)fail('BACKEND_VERSION_CHANGED',409);
  const data=await ghJson(env,'/actions/workflows/'+WORKFLOW+'/runs?event=workflow_dispatch&branch='+encodeURIComponent(env.NABT_REF)+'&per_page=100');
  if(!Array.isArray(data.workflow_runs))fail('GITHUB_RESPONSE_INVALID',502);
  const matches=data.workflow_runs.filter(r=>r.display_title==='NABT Lab · '+expected.request_id&&r.head_sha===expected.code_sha&&r.event==='workflow_dispatch'&&r.head_branch===env.NABT_REF&&r.path?.split('@')[0]==='.github/workflows/'+WORKFLOW);
  if(matches.length>1)fail('AMBIGUOUS_RUN',502);
  if(matches.length===0){if(Date.now()-expected.created>180000) return json({status:'failed',error:'RUN_NOT_FOUND'});return json({status:'queued',poll_after_ms:5000});}
  const run=matches[0];if(!Number.isSafeInteger(run.id))fail('GITHUB_RESPONSE_INVALID',502);
  const run_url='https://github.com/'+REPOSITORY+'/actions/runs/'+run.id;
  if(run.status!=='completed')return json({status:run.status==='queued'?'queued':'in_progress',run_url,poll_after_ms:5000});
  if(run.conclusion!=='success')return json({status:'failed',run_url,error:'WORKFLOW_'+String(run.conclusion).toUpperCase()});
  const artifacts=await ghJson(env,'/actions/runs/'+run.id+'/artifacts?per_page=100');
  const items=(artifacts.artifacts??[]).filter(a=>a.name==='nabt-lab-'+expected.request_id&&a.workflow_run?.head_sha===expected.code_sha&&a.workflow_run?.id===run.id);
  if(items.length!==1)fail('ARTIFACT_UNAVAILABLE',502);
  const encrypted=await downloadResult(env,items[0]);
  const report=validateReport(JSON.parse(await decryptEnvelope(encrypted,env.NABT_TRANSPORT_KEY,expected.request_id)),expected);
  return json({status:'completed',run_url,artifact_digest:items[0].digest,report});
}
export async function route(request,env,assets){
  try{
    const url=new URL(request.url);
    if(request.method==='GET'&&url.pathname in assets){const asset=assets[url.pathname];return new Response(asset.body,{headers:{...securityHeaders,'Content-Type':asset.type,'Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; font-src 'self'; base-uri 'none'; form-action 'self'"}});}
    if(url.pathname==='/api/config'&&request.method==='GET')return json({ready:configured(env),configuration_status:env.NABT_EXECUTION_ENABLED==='true'?'configured_or_missing_fields':'awaiting_transport_authorization',code_sha:SHA.test(env.NABT_CODE_SHA??'')?env.NABT_CODE_SHA:null,branch:ALLOWED_REFS.includes(env.NABT_REF)?env.NABT_REF:null,law:'nabt.licensed-inference.v1',limits:{...LIMITS,source_bytes:16384,query_bytes:4096},baseline:{total:38,passed:37,failed:1,unmeasured:0,code_sha:'f0d41d3c6320fe78ac31ce60411fbb3442dc8293',scope:'لقطة التقييم المستقل المثبتة للنطاق المحدود؛ ليست قياسًا لكل العربية.'},scope_note:'الاكتمال مقيد بالقانون والنطاق المعلنين. اكتمال العربية كلها وصحة المطابقة للواقع غير مثبتين.'});
    if(url.pathname==='/api/runs'){
      if(!configured(env))fail('BACKEND_NOT_CONFIGURED',503);
      // Access is restricted to the owner by Sites dispatch; service access uses the same boundary.
      if(request.method==='POST')return await submit(request,env);
      if(request.method==='GET')return await poll(url,env);
      return json({error:'METHOD_NOT_ALLOWED'},405);
    }
    return json({error:'NOT_FOUND'},404);
  }catch(error){return json({error:error instanceof LabError?error.code:'BACKEND_UNAVAILABLE'},error instanceof LabError?error.status:502);}
}
