import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash, createCipheriv, createDecipheriv} from 'node:crypto';
import {deflateRawSync} from 'node:zlib';
import {validatePayload,boundedBytes,signHandle,verifyHandle,unpackResult,validateReport,route,encryptEnvelope,decryptEnvelope} from '../worker/server.mjs';

const SCHEMA='nabt.proof-lab-request.v1';
const CODE='a'.repeat(40), DIGEST='b'.repeat(64);
const ID='f2702111-d080-4c99-8c4c-ef43f10a3def';
const KEY='test-only-signing-secret-000000000000000000000';
const TRANSPORT='12'.repeat(32);
const ENV={NABT_TRANSPORT_KEY:TRANSPORT,NABT_GITHUB_TOKEN:'test-only-not-a-real-token',NABT_SIGNING_KEY:KEY,NABT_CODE_SHA:CODE,NABT_EXECUTION_ENABLED: 'true',
  NABT_REF:'codex/dynamic-proof-lab'};
const INPUT={schema:SCHEMA,mode:'inference',source_text:'إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ. عَرَفَ زَيْدٌ الْحَقَّ.',query_text:'هَلْ سَارَ زَيْدٌ؟'};
function descriptor(extra={}){return {request_id:ID,payload_sha256:DIGEST,code_sha:CODE,mode:'inference',created:Date.now(),...extra};}
function successResult(extra={}){return {schema:'nabt.licensed-inference-result.v1',law_id:'nabt.licensed-inference.v1',status:'SUPPORTED',authority:'SOURCE_RELATIVE_CONSEQUENCE',verified:true,native_checked:true,all_readings_complete:true,closures_checked:true,all_arabic_complete:false,world_truth_established:false,readings:[],closure_records:[],...extra};}
function report(extra={}){return {schema:'nabt.proof-lab-result.v1',...descriptor(),duration_ms:10,status:'SUPPORTED',scope:{whole_arabic:'NOT_PROVED',external_world:'NOT_VERIFIED'},all_arabic_complete:false,world_truth_established:false,result:successResult(),...extra};}
function expectCode(code){return e=>e?.code===code;}
const response=v=>new Response(JSON.stringify(v),{headers:{'Content-Type':'application/json'}});
function request(body=INPUT,headers={}){return new Request('https://lab.example/api/runs',{method:'POST',headers:{'Content-Type':'application/json','Origin':'https://lab.example',...headers},body:typeof body==='string'?body:JSON.stringify(body)});}
async function mockedFetch(fn,body){const old=globalThis.fetch;globalThis.fetch=fn;try{return await body();}finally{globalThis.fetch=old;}}
function digest(bytes){return createHash('sha256').update(bytes).digest('hex');}
function crc32(bytes){let c=0xffffffff;for(const b of bytes){c^=b;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;}
function makeZip(value,{method=0,name='result.json',raw,centralMutator,localMutator,count=1}={}){
  const data=raw??Buffer.from(JSON.stringify(value));const packed=method===8?deflateRawSync(data):data;const n=Buffer.from(name);const crc=crc32(data);
  const local=Buffer.alloc(30+n.length);local.writeUInt32LE(0x04034b50,0);local.writeUInt16LE(20,4);local.writeUInt16LE(method,8);local.writeUInt32LE(crc,14);local.writeUInt32LE(packed.length,18);local.writeUInt32LE(data.length,22);local.writeUInt16LE(n.length,26);n.copy(local,30);if(localMutator)localMutator(local);
  const central=Buffer.alloc(46+n.length);central.writeUInt32LE(0x02014b50,0);central.writeUInt16LE(20,4);central.writeUInt16LE(20,6);central.writeUInt16LE(method,10);central.writeUInt32LE(crc,16);central.writeUInt32LE(packed.length,20);central.writeUInt32LE(data.length,24);central.writeUInt16LE(n.length,28);n.copy(central,46);if(centralMutator)centralMutator(central);
  const end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(count,8);end.writeUInt16LE(count,10);end.writeUInt32LE(central.length,12);end.writeUInt32LE(local.length+packed.length,16);
  return Buffer.concat([local,packed,central,end]);
}
function completedRun(extra={}){return {id:123,display_title:'NABT Lab · '+ID,head_sha:CODE,event:'workflow_dispatch',head_branch:ENV.NABT_REF,path:'.github/workflows/proof-lab.yml',status:'completed',conclusion:'success',created_at:new Date().toISOString(),...extra};}
async function pollWith({run=completedRun(),artifactExtra={},zip,reportValue=report(),redirect='https://proof.blob.core.windows.net/result.zip',reportBinding=descriptor(),downloadStatus=200}={},inspect){
  zip ??= makeZip(await encryptEnvelope(JSON.stringify(reportValue),TRANSPORT,reportBinding.request_id));
  const handle=await signHandle(reportBinding,KEY);let downloaded=false;
  const result=await mockedFetch(async(url,options={})=>{
    url=String(url);inspect?.(url,options);
    if(url.includes('/workflows/proof-lab.yml/runs?'))return response({workflow_runs:Array.isArray(run)?run:[run]});
    if(url.endsWith('/runs/123/artifacts?per_page=100'))return response({artifacts:[{id:321,name:'nabt-lab-'+ID,expired:false,size_in_bytes:zip.length,digest:'sha256:'+digest(zip),workflow_run:{id:123,head_sha:CODE},...artifactExtra}]});
    if(url.endsWith('/artifacts/321/zip'))return new Response(null,{status:302,headers:{Location:redirect}});
    if(url===redirect){downloaded=true;return new Response(zip,{status:downloadStatus,headers:downloadStatus>=300?{Location:'https://unapproved.example/result.zip'}:{}});}
    assert.fail('Unexpected URL '+url);
  },()=>route(new Request('https://lab.example/api/runs?handle='+encodeURIComponent(handle)),ENV,{}));
  return {response:result,body:await result.json(),downloaded};
}

test('preserves exact Arabic text and accepts explicit zero resource budgets',()=>{
  const result=validatePayload({...INPUT,budget:{max_clauses:0,max_readings:0,max_atoms:0,max_closure_steps:0}});
  assert.equal(result.source_text,INPUT.source_text);assert.equal(result.query_text,INPUT.query_text);assert.equal(result.budget.max_clauses,0);
});
test('rejects authority, executable, rule and arbitrary ref input fields',()=>{
  for(const key of ['verified','all_arabic_complete','world_truth_established','executable','rules','ref'])assert.throws(()=>validatePayload({...INPUT,[key]:true}),expectCode('INVALID_INPUT'));
});
test('rejects missing fields, wrong schema/mode, arrays, null and nonstrings',()=>{
  for(const value of [null,[],{}, {...INPUT,schema:'other'},{...INPUT,mode:'lean-code'},{...INPUT,source_text:[]},{...INPUT,query_text:4}])assert.throws(()=>validatePayload(value));
});
test('budgets require bounded safe integers, never bool/float/text/null',()=>{
  for(const value of [true,false,1.1,-1,'2',Number.MAX_SAFE_INTEGER,NaN,Infinity])assert.throws(()=>validatePayload({...INPUT,budget:{max_atoms:value}}),expectCode('INVALID_BUDGET'));
  assert.throws(()=>validatePayload({...INPUT,budget:{max_clauses:65}}),expectCode('INVALID_BUDGET'));
  for(const value of [[],{unbounded:1},'none'])assert.throws(()=>validatePayload({...INPUT,budget:value}));
});
test('UTF-8 byte limits apply to Arabic, and lone UTF-16 surrogates are rejected',()=>{
  assert.throws(()=>validatePayload({...INPUT,source_text:'ع'.repeat(8193)}),expectCode('INPUT_LIMIT'));
  assert.throws(()=>validatePayload({...INPUT,query_text:'ع'.repeat(2049)}),expectCode('INPUT_LIMIT'));
  for(const value of ['\ud800','\udfff','a\ud800x'])assert.throws(()=>validatePayload({...INPUT,source_text:value}),expectCode('INVALID_UNICODE'));
  assert.equal(validatePayload({...INPUT,source_text:'😀'}).source_text,'😀');
});
test('benchmark requests cannot smuggle source text or resource policy',()=>{
  assert.deepEqual(validatePayload({schema:SCHEMA,mode:'benchmark'}),{schema:SCHEMA,mode:'benchmark'});
  for(const key of ['source_text','query_text','budget'])assert.throws(()=>validatePayload({schema:SCHEMA,mode:'benchmark',[key]:''}));
});
test('bounded stream rejects excess chunks and cancels input',async()=>{
  let canceled=false;const stream=new ReadableStream({start(c){c.enqueue(new Uint8Array(8));c.enqueue(new Uint8Array(8));},cancel(){canceled=true;}});
  await assert.rejects(boundedBytes(stream,12),expectCode('RESPONSE_LIMIT'));assert.equal(canceled,true);
  assert.deepEqual(await boundedBytes(new Blob(['abc']).stream(),3),new Uint8Array([97,98,99]));
});
test('signed handle round trips all binding fields',async()=>{
  const input=descriptor();assert.deepEqual(await verifyHandle(await signHandle(input,KEY),KEY),input);
});
test('handle rejects body/signature tampering, wrong key, truncated and invalid encodings',async()=>{
  const handle=await signHandle(descriptor(),KEY);const [raw,sig]=handle.split('.');
  for(const bad of [raw+'.'+(sig[0]==='a'?'b':'a')+sig.slice(1),'a'+raw.slice(1)+'.'+sig,handle+'.x','.',raw+'.!','x'.repeat(2049)])await assert.rejects(verifyHandle(bad,KEY));
  await assert.rejects(verifyHandle(handle,KEY+'wrong'));
});
test('handle expiration and future clock skew are bounded',async()=>{
  const now=Date.now();
  for(const created of [now-86400001,now+30001,'now',1.1])await assert.rejects(verifyHandle(await signHandle(descriptor({created}),KEY),KEY,now));
});
test('handle rejects signed malformed identifiers and unsupported modes',async()=>{
  for(const patch of [{request_id:'bad'},{request_id:ID.toUpperCase()},{code_sha:'bad'},{payload_sha256:'bad'},{mode:'arbitrary'},{extra:1}])await assert.rejects(verifyHandle(await signHandle(descriptor(patch),KEY),KEY));
});
test('ZIP stored and raw-deflate archives return the exact Unicode report',async()=>{
  const input={text:'العربية',value:3};assert.deepEqual(await unpackResult(makeZip(input)),input);assert.deepEqual(await unpackResult(makeZip(input,{method:8})),input);
});
test('ZIP rejects wrong filename, extra directory entries, encryption and unsupported methods',async()=>{
  for(const zip of [makeZip({},{name:'../result.json'}),makeZip({},{name:'sub/result.json'}),makeZip({},{name:'directory/'}),makeZip({},{count:2}),makeZip({},{method:99}),makeZip({},{centralMutator:b=>b.writeUInt16LE(1,8)})])await assert.rejects(unpackResult(zip));
});
test('ZIP rejects checksum mutation, truncation, oversized result and bad local metadata',async()=>{
  for(const zip of [makeZip({},{centralMutator:b=>b.writeUInt32LE(123,16)}),makeZip({}).subarray(0,20),makeZip({},{centralMutator:b=>b.writeUInt32LE(3145729,24)}),makeZip({},{localMutator:b=>b.writeUInt16LE(8,8)})])await assert.rejects(unpackResult(zip));
});
test('ZIP validates decoded output size rather than trusting its declared size',async()=>{
  const zip=makeZip(null,{method:8,raw:Buffer.alloc(3145729,32),centralMutator:b=>b.writeUInt32LE(12,24)});
  await assert.rejects(unpackResult(zip),expectCode('RESPONSE_LIMIT'));
});
test('ZIP rejects malformed result JSON and unexpected trailing bytes',async()=>{
  await assert.rejects(unpackResult(makeZip(null,{raw:Buffer.from('not-json')})),expectCode('ARTIFACT_JSON_INVALID'));
  await assert.rejects(unpackResult(Buffer.concat([makeZip({}),Buffer.from('x')])));
});
test('report requires matching request, input digest, source commit and mode',()=>{
  const expected=descriptor();assert.equal(validateReport(report(),expected).status,'SUPPORTED');
  for(const patch of [{schema:'wrong'},{request_id:ID.slice(0,-1)+'a'},{payload_sha256:'0'.repeat(64)},{code_sha:'0'.repeat(40)},{mode:'benchmark'}])assert.throws(()=>validateReport(report(patch),expected),expectCode('REPORT_BINDING_FAILED'));
});
test('report cannot promote whole Arabic or world truth and cannot fake native verification',()=>{
  const expected=descriptor();for(const patch of [{all_arabic_complete:true},{world_truth_established:true}])assert.throws(()=>validateReport(report(patch),expected));
  for(const patch of [{all_arabic_complete:true},{world_truth_established:true},{native_checked:false}])assert.throws(()=>validateReport(report({result:successResult(patch)}),expected),expectCode('REPORT_AUTHORITY_INVALID'));
});
test('config excludes credentials and exposes only bounded scope',async()=>{
  const res=await route(new Request('https://lab.example/api/config'),ENV,{});const text=await res.text();assert.equal(res.status,200);assert.ok(!text.includes(ENV.NABT_GITHUB_TOKEN));assert.ok(!text.includes(KEY));const data=JSON.parse(text);assert.equal(data.ready,true);assert.equal(data.baseline.total,38);assert.equal(data.baseline.passed,37);
});
test('missing configuration is a structured unavailability result with no GitHub call',async()=>{
  await mockedFetch(()=>assert.fail('Network must not be called'),async()=>{const res=await route(request(),{},{});assert.equal(res.status,503);assert.deepEqual(await res.json(),{error:'BACKEND_NOT_CONFIGURED'});});
});
test('cross-origin browser writes are rejected before GitHub access',async()=>{
  await mockedFetch(()=>assert.fail('Network must not be called'),async()=>{
    for(const headers of [{Origin:'https://evil.example'},{'Sec-Fetch-Site':'cross-site'}]){const res=await route(request(INPUT,headers),ENV,{});assert.equal(res.status,403);assert.deepEqual(await res.json(),{error:'CROSS_ORIGIN_DENIED'});}
  });
});
test('plain forms and malformed JSON cannot dispatch a workflow',async()=>{
  await mockedFetch(()=>assert.fail('Network must not be called'),async()=>{
    const form=await route(request('source=x',{'Content-Type':'text/plain'}),ENV,{});assert.equal(form.status,415);
    const bad=await route(request('{'),ENV,{});assert.equal(bad.status,400);
  });
});
test('branch drift is refused before dispatch',async()=>{
  let calls=0;const res=await mockedFetch(()=>{calls++;return response({object:{sha:'0'.repeat(40)}});},()=>route(request(),ENV,{}));assert.equal(res.status,409);assert.equal(calls,1);assert.deepEqual(await res.json(),{error:'BACKEND_VERSION_CHANGED'});
});
test('active and newly started runs impose bounded admission',async()=>{
  for(const run of [completedRun({status:'in_progress'}),completedRun()]){
    let calls=0;const res=await mockedFetch(()=>++calls===1?response({object:{sha:CODE}}):response({workflow_runs:[run]}),()=>route(request(),ENV,{}));assert.equal(res.status,429);assert.equal(calls,2);
  }
});
test('submit dispatches only fixed workflow/ref and signs hash of exact dispatched JSON',async()=>{
  const calls=[];const res=await mockedFetch((url,options)=>{
    calls.push([String(url),options]);if(calls.length===1)return response({object:{sha:CODE}});if(calls.length===2)return response({workflow_runs:[]});return new Response(null,{status:204});
  },()=>route(request(),ENV,{}));
  assert.equal(res.status,202);const submitted=await res.json();const data=await verifyHandle(submitted.handle,KEY);const dispatch=JSON.parse(calls[2][1].body);
  assert.equal(dispatch.ref,ENV.NABT_REF);assert.equal(dispatch.inputs.request_id,data.request_id);
  const envelope=JSON.parse(dispatch.inputs.payload);assert.equal(envelope.schema,'nabt.proof-lab-envelope.v1');
  assert.ok(!calls[2][1].body.includes(INPUT.source_text));assert.ok(!calls[2][1].body.includes(INPUT.query_text));assert.ok(!calls[2][1].body.includes('source_text'));
  const plaintext=await decryptEnvelope(envelope,TRANSPORT,data.request_id);assert.equal(digest(Buffer.from(plaintext)),data.payload_sha256);assert.equal(JSON.parse(plaintext).source_text,INPUT.source_text);
  assert.ok(calls.every(([url])=>url.startsWith('https://api.github.com/repos/sonaiso/NABT/')));assert.ok(calls[2][0].endsWith('/actions/workflows/proof-lab.yml/dispatches'));
});
test('GitHub error details and thrown exception secrets never reach browser',async()=>{
  for(const fn of [()=>new Response(ENV.NABT_GITHUB_TOKEN+KEY,{status:403}),()=>{throw new Error(ENV.NABT_GITHUB_TOKEN+KEY);}]){
    const res=await mockedFetch(fn,()=>route(request(),ENV,{}));const text=await res.text();assert.equal(res.status,502);assert.ok(!text.includes(ENV.NABT_GITHUB_TOKEN));assert.ok(!text.includes(KEY));
  }
});
test('cross-run commit/path/event/branch substitutions are not accepted',async()=>{
  for(const patch of [{head_sha:'0'.repeat(40)},{head_branch:'main'},{event:'push'},{path:'.github/workflows/ci.yml'},{display_title:'other'}]){const {body}=await pollWith({run:completedRun(patch)});assert.equal(body.status,'queued');assert.ok(!body.report);}
});
test('duplicate matching workflow runs are refused as ambiguous',async()=>{
  const {response:res,body}=await pollWith({run:[completedRun(),completedRun({id:124})]});assert.equal(res.status,502);assert.equal(body.error,'AMBIGUOUS_RUN');
});
test('failed workflow never yields an inference result',async()=>{
  const {body}=await pollWith({run:completedRun({conclusion:'failure'})});assert.equal(body.status,'failed');assert.equal(body.error,'WORKFLOW_FAILURE');assert.ok(!body.report);
});
test('artifact binding rejects other run, wrong digest and expired artifacts',async()=>{
  for(const patch of [{workflow_run:{id:124,head_sha:CODE}},{workflow_run:{id:123,head_sha:'0'.repeat(40)}},{digest:'sha256:'+'0'.repeat(64)},{expired:true},{size_in_bytes:4194305}]){const {response:res,body}=await pollWith({artifactExtra:patch});assert.equal(res.status,502);assert.ok(!body.report);}
});
test('archive redirects cannot target arbitrary hosts or forward authorization',async()=>{
  for(const redirect of ['https://evil.example/result.zip','http://proof.blob.core.windows.net/result.zip','https://user:pass@proof.blob.core.windows.net/result.zip']){const {body,downloaded}=await pollWith({redirect});assert.equal(body.error,'ARTIFACT_REDIRECT_INVALID');assert.equal(downloaded,false);}
  let downloadHeaders;const {body}=await pollWith({},(url,options)=>{if(url.startsWith('https://proof.blob.core.windows.net')){downloadHeaders=options.headers;assert.equal(options.redirect,'manual');}else{assert.equal(options.headers.Authorization,'Bearer '+ENV.NABT_GITHUB_TOKEN);assert.equal(options.redirect,'manual');}});assert.equal(downloadHeaders,undefined);assert.equal(body.status,'completed');assert.equal(body.report.result.verified,true);
});
test('artifact payload hash mismatch is rejected after successful authenticated download',async()=>{
  const {response:res,body}=await pollWith({reportValue:report({payload_sha256:'0'.repeat(64)})});assert.equal(res.status,502);assert.equal(body.error,'REPORT_BINDING_FAILED');
});
test('completed receipt works when runtime rejects unsupported redirect error mode',async()=>{
  const {response:res,body}=await pollWith({},(_url,options)=>{
    // Cloudflare Request supports follow/manual; Node accepts an extra error mode.
    if(options.redirect==='error')throw new TypeError('unsupported redirect mode');
  });
  assert.equal(res.status,200);assert.equal(body.status,'completed');
  assert.equal(body.report.result.native_checked,true);
});
test('artifact CDN redirects are refused without a second fetch or credential forwarding',async()=>{
  for(const downloadStatus of [301,302,303,307,308]){
    const calls=[];
    const {response:res,body}=await pollWith({downloadStatus},(url,options)=>calls.push([url,options]));
    assert.equal(res.status,502);assert.equal(body.error,'ARTIFACT_REDIRECT_INVALID');
    assert.equal(calls.filter(([url])=>url.startsWith('https://proof.blob.core.windows.net')).length,1);
    assert.ok(calls.every(([url])=>!url.includes('unapproved.example')));
    assert.equal(calls.at(-1)[1].headers,undefined);
    assert.equal(calls.at(-1)[1].redirect,'manual');
  }
});
test('API and asset responses have no-store, MIME and script-origin protections',async()=>{
  const res=await route(new Request('https://lab.example/'),ENV,{'/':{body:'hello',type:'text/html; charset=utf-8'}});assert.equal(await res.text(),'hello');assert.equal(res.headers.get('Cache-Control'),'no-store');assert.equal(res.headers.get('X-Content-Type-Options'),'nosniff');assert.ok(res.headers.get('Content-Security-Policy').includes("script-src 'self'"));
  const no=await route(new Request('https://lab.example/not-found'),ENV,{});assert.equal(no.status,404);
});

test('explicit null budget and whitespace-only text are rejected before dispatch',()=>{
  assert.throws(()=>validatePayload({...INPUT,budget:null}));
  for(const value of ['',' ','\t\r\n']){
    assert.throws(()=>validatePayload({...INPUT,source_text:value}));
    assert.throws(()=>validatePayload({...INPUT,query_text:value}));
  }
});
test('oversize browser payload is an input limit, not an upstream server failure',async()=>{
  await mockedFetch(()=>assert.fail('Network must not be called'),async()=>{
    const res=await route(request(' '.repeat(32769)),ENV,{});assert.equal(res.status,413);assert.deepEqual(await res.json(),{error:'INPUT_LIMIT'});
  });
});
test('report success must contain typed checked-result flags and coherent status',()=>{
  const expected=descriptor();
  for(const value of [null,undefined,[],{}])assert.throws(()=>validateReport(report({result:value}),expected));
  for(const patch of [{verified:'true'},{verified:1},{native_checked:'true'},{closures_checked:false},{all_readings_complete:false},{authority:'UNVERIFIED_PROPOSAL'},{status:'INVENTED_SUCCESS'}])assert.throws(()=>validateReport(report({result:successResult(patch)}),expected));
  assert.throws(()=>validateReport(report({status:'UNKNOWN',result:successResult()}),expected));
});

test('unverified live receipts cannot retain checked flags, authority or measured conclusions',()=>{
  const expected=descriptor();
  const base={status:'UNKNOWN',verified:false,native_checked:false,all_readings_complete:false,closures_checked:false,authority:'UNVERIFIED_PROPOSAL'};
  assert.equal(validateReport(report({status:'UNKNOWN',result:successResult(base)}),expected).result.verified,false);
  for(const patch of [{native_checked:true},{all_readings_complete:true},{closures_checked:true},{authority:'SOURCE_RELATIVE_CONSEQUENCE'},{all_readings_complete:null},{closures_checked:undefined}])
    assert.throws(()=>validateReport(report({status:'UNKNOWN',result:successResult({...base,...patch})}),expected),expectCode('REPORT_AUTHORITY_INVALID'));
  for(const status of ['SUPPORTED','REFUTED','CONFLICT','DEFER','DISAGREEMENT'])
    assert.throws(()=>validateReport(report({status,result:successResult({...base,status})}),expected),expectCode('REPORT_AUTHORITY_INVALID'));
});

test('checked UNKNOWN remains valid but operational failure cannot claim checked success',()=>{
  const expected=descriptor();
  assert.equal(validateReport(report({status:'UNKNOWN',result:successResult({status:'UNKNOWN'})}),expected).result.verified,true);
  for(const status of ['INVALID_INPUT','RESOURCE_EXHAUSTED','VERIFICATION_UNAVAILABLE','SOURCE_UNAVAILABLE'])
    assert.throws(()=>validateReport(report({status,result:successResult({status})}),expected),expectCode('REPORT_AUTHORITY_INVALID'));
});

test('AES-GCM envelopes hide plaintext, use fresh nonces and preserve exact UTF-8',async()=>{
  const input=JSON.stringify(INPUT),a=await encryptEnvelope(input,TRANSPORT,ID),b=await encryptEnvelope(input,TRANSPORT,ID);
  assert.equal(a.schema,'nabt.proof-lab-envelope.v1');assert.equal(Buffer.from(a.nonce,'base64').length,12);assert.notEqual(a.nonce,b.nonce);assert.notEqual(a.ciphertext,b.ciphertext);
  assert.equal(await decryptEnvelope(a,TRANSPORT,ID),input);assert.ok(!JSON.stringify(a).includes(INPUT.source_text));assert.ok(!JSON.stringify(a).includes('source_text'));
  const cipher=Buffer.from(a.ciphertext,'base64'),decipher=createDecipheriv('aes-256-gcm',Buffer.from(TRANSPORT,'hex'),Buffer.from(a.nonce,'base64'));decipher.setAAD(Buffer.from(ID));decipher.setAuthTag(cipher.subarray(-16));assert.equal(Buffer.concat([decipher.update(cipher.subarray(0,-16)),decipher.final()]).toString('utf8'),input);
});
test('decryption agrees with independently assembled Node AES-GCM envelope',async()=>{
  const nonce=Buffer.alloc(12,7),cipher=createCipheriv('aes-256-gcm',Buffer.from(TRANSPORT,'hex'),nonce);cipher.setAAD(Buffer.from(ID));
  const input='شهادة عربية',bytes=Buffer.concat([cipher.update(Buffer.from(input)),cipher.final(),cipher.getAuthTag()]);
  assert.equal(await decryptEnvelope({schema:'nabt.proof-lab-envelope.v1',nonce:nonce.toString('base64'),ciphertext:bytes.toString('base64')},TRANSPORT,ID),input);
});
test('GCM binds request ID and rejects wrong keys, tamper and truncated tags',async()=>{
  const input=await encryptEnvelope('secret-text',TRANSPORT,ID),altered=Buffer.from(input.ciphertext,'base64');altered[0]^=1;
  await assert.rejects(decryptEnvelope(input,'34'.repeat(32),ID));
  await assert.rejects(decryptEnvelope(input,TRANSPORT,'f2702111-d080-4c99-8c4c-ef43f10a3dea'));
  await assert.rejects(decryptEnvelope({...input,ciphertext:altered.toString('base64')},TRANSPORT,ID));
  await assert.rejects(decryptEnvelope({...input,ciphertext:Buffer.alloc(15).toString('base64')},TRANSPORT,ID));
});
test('envelope rejects unknown fields, noncanonical base64, nonce lengths and plaintext excess',async()=>{
  const input=await encryptEnvelope('x'.repeat(32),TRANSPORT,ID);
  for(const patch of [{schema:'wrong'},{extra:1},{nonce:'!'}, {nonce:Buffer.alloc(11).toString('base64')},{ciphertext:input.ciphertext+'='},{ciphertext:true}])await assert.rejects(decryptEnvelope({...input,...patch},TRANSPORT,ID));
  await assert.rejects(decryptEnvelope(input,TRANSPORT,ID,16));
  await assert.rejects(encryptEnvelope('data','bad-key',ID));
});
test('published artifact must itself contain encryption envelope, never raw report JSON',async()=>{
  const {response:res,body}=await pollWith({zip:makeZip(report())});assert.equal(res.status,502);assert.ok(!body.report);
});
test('a cryptographically valid result encrypted for another request is rejected',async()=>{
  const other='f2702111-d080-4c99-8c4c-ef43f10a3dea',zip=makeZip(await encryptEnvelope(JSON.stringify(report()),TRANSPORT,other));
  const {response:res,body}=await pollWith({zip});assert.equal(res.status,502);assert.ok(!body.report);
});
test('backend refuses to operate without the transport encryption key',async()=>{
  const env={...ENV};delete env.NABT_TRANSPORT_KEY;
  const config=await route(new Request('https://lab.example/api/config'),env,{});assert.equal((await config.json()).ready,false);
  await mockedFetch(()=>assert.fail('No plaintext fallback'),async()=>{const res=await route(request(),env,{});assert.equal(res.status,503);});
});

test('benchmark receipts keep the fixed denominator and cannot use booleans as counts',()=>{
  const expected=descriptor({mode:'benchmark'});
  const benchmark={schema:'nabt.licensed-inference.independent-result.v1',gold_sha256:DIGEST,summary:{cases:38,pass:37,fail:1,unmeasured:0},contract_gate:{passed:true},rows:Array.from({length:38},(_,i)=>({id:'L'+i,outcome:i===0?'FAIL':'PASS'}))};
  const value=report({mode:'benchmark',status:'BENCHMARK_COMPLETE',result:undefined,benchmark});
  assert.equal(validateReport(value,expected).benchmark.summary.fail,1);
  for(const patch of [{cases:37},{pass:38},{pass:true},{fail:-1},{unmeasured:0.1}])assert.throws(()=>validateReport({...value,benchmark:{...benchmark,summary:{...benchmark.summary,...patch}}},expected));
  assert.throws(()=>validateReport({...value,benchmark:{...benchmark,rows:benchmark.rows.slice(1)}},expected));
  assert.throws(()=>validateReport({...value,benchmark:{...benchmark,contract_gate:{passed:false}}},expected));
});
test('structured execution failures cannot carry a simultaneous proof result',()=>{
  const expected=descriptor();const error=report({status:'RESOURCE_EXHAUSTED',result:undefined,error:'RESULT_BYTE_LIMIT'});
  assert.equal(validateReport(error,expected).status,'RESOURCE_EXHAUSTED');
  for(const patch of [{status:'SUPPORTED'},{error:true},{error:'x'.repeat(129)},{result:successResult()}])assert.throws(()=>validateReport({...error,...patch},expected));
});
test('private configuration never returns transport or signing secrets',async()=>{
  const res=await route(new Request('https://lab.example/api/config'),ENV,{});const text=await res.text();
  for(const secret of [TRANSPORT,KEY,ENV.NABT_GITHUB_TOKEN])assert.ok(!text.includes(secret));
});

test('public configuration identifies the actual pinned testimony branch, never the old default',async()=>{
  const res=await route(new Request('https://lab.example/api/config'),{...ENV,NABT_REF:'codex/attested-testimony-live'},{});
  const c=await res.json();assert.equal(c.ready,true);assert.equal(c.branch,'codex/attested-testimony-live');assert.equal(c.code_sha,CODE);
});
