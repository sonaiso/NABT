import {workflowReport} from './helpers/workflow-fixture.mjs';
import {createHash} from 'node:crypto';
import {bindInferenceFixture} from './helpers/inference-fixture.mjs';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// This is a DOM interaction regression harness, not a browser renderer or a
// Lean verifier. The response fixtures retain the actual native report shape
// and the frozen 38-case benchmark's IDs/families/outcomes. Backend authenticity
// and native proof checking are tested independently.
const html = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const authority = readFileSync(new URL('../web/legacy-authority.js', import.meta.url), 'utf8');
const app = readFileSync(new URL('../web/app.js', import.meta.url), 'utf8');
const pendingKey = 'nabt.proof-lab.pending.v1';
const requestId = '11111111-1111-4111-8111-111111111111';
const sourceText = 'إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ. عَرَفَ زَيْدٌ الْحَقَّ.';
const queryText = 'هَلْ سَارَ زَيْدٌ؟';
const knowledge = { predicate: 'عرف', arguments: ['زيد', 'الحق'], positive: true };
const movement = { predicate: 'سار', arguments: ['زيد'], positive: true };
const clauses = [
  { kind: 'rule', body: [knowledge], head: movement },
  { kind: 'fact', atom: knowledge },
];
const nativeFixture = {
  schema: 'nabt.licensed-inference-result.v1',
  law_id: 'nabt.licensed-inference.v1',
  authority: 'SOURCE_RELATIVE_CONSEQUENCE',
  accepted_language: 'nabt.explicit-subject-active.v1',
  status: 'SUPPORTED',
  verified: true,
  native_checked: true,
  all_readings_complete: true,
  closures_checked: true,
  all_arabic_complete: false,
  world_truth_established: false,
  reason: 'CHECKED_INSTALLED_GRAMMAR_AND_SOURCE_THEORY',
  source: { raw_text: sourceText },
  query: { raw_text: queryText },
  assumptions: ['source assertions are premises, not world observations'],
  readings: [{ clauses, query: movement, positive: true, negative: false,
    clean_positive: true, clean_negative: false, status: 'SUPPORTED' }],
  closure_records: [{ clauses, query: movement,
    steps: [{ kind: 'fact', index: 0 }, { kind: 'rule', index: 0 }],
    known: [knowledge, movement],
    clean_steps: [{ kind: 'fact', index: 0 }, { kind: 'rule', index: 0 }],
    clean_known: [knowledge, movement] }],
  unclassified_spans: [],
  aggregate: { skeptical_clean_positive: true, skeptical_clean_negative: false,
    credulous_positive: true, credulous_negative: false,
    within_reading_conflict: false, cross_reading_opposition: false },
};

// Recorded outcomes from evidence/licensed_inference_v1/independent_final.json.
// Compact display fixtures intentionally omit the large raw certificates.
const caseMatrix = [
  ['L01', 'original_unresolved', 'evaluate', 'PASS'],
  ['L02', 'conditional_only', 'evaluate', 'PASS'],
  ['L03', 'conditional_only', 'evaluate', 'PASS'],
  ['L04', 'forward', 'evaluate', 'PASS'],
  ['L05', 'order_invariance', 'evaluate', 'PASS'],
  ['L06', 'front_conditional', 'evaluate', 'PASS'],
  ['L07', 'no_inverse', 'evaluate', 'PASS'],
  ['L08', 'no_inverse', 'evaluate', 'PASS'],
  ['L09', 'negative_consequent', 'evaluate', 'PASS'],
  ['L10', 'signed_states', 'evaluate', 'PASS'],
  ['L11', 'signed_states', 'evaluate', 'PASS'],
  ['L12', 'signed_states', 'evaluate', 'PASS'],
  ['L13', 'signed_states', 'evaluate', 'PASS'],
  ['L14', 'derived_conflict', 'evaluate', 'PASS'],
  ['L15', 'no_explosion', 'evaluate', 'PASS'],
  ['L16', 'subject_identity', 'evaluate', 'PASS'],
  ['L17', 'subject_identity', 'evaluate', 'PASS'],
  ['L18', 'frame_identity', 'evaluate', 'PASS'],
  ['L19', 'frame_identity', 'evaluate', 'PASS'],
  ['L20', 'preserved_adjuncts', 'evaluate', 'PASS'],
  ['L21', 'quote_boundary', 'evaluate', 'PASS'],
  ['L22', 'question_boundary', 'evaluate', 'PASS'],
  ['L23', 'trailing_input', 'evaluate', 'PASS'],
  ['L24', 'partial_condition', 'evaluate', 'PASS'],
  ['L25', 'query_boundary', 'evaluate', 'PASS'],
  ['L26', 'unknown_vocabulary', 'evaluate', 'FAIL'],
  ['L27', 'provenance', 'evaluate', 'PASS'],
  ['L28', 'provenance', 'evaluate', 'PASS'],
  ['L29', 'resource', 'evaluate', 'PASS'],
  ['L30', 'resource', 'evaluate', 'PASS'],
  ['L31', 'invalid_input', 'evaluate', 'PASS'],
  ['L32', 'invalid_input', 'evaluate', 'PASS'],
  ['A01', 'aggregation', 'aggregate_fixture', 'PASS'],
  ['A02', 'aggregation', 'aggregate_fixture', 'PASS'],
  ['A03', 'aggregation', 'aggregate_fixture', 'PASS'],
  ['A04', 'aggregation', 'aggregate_fixture', 'PASS'],
  ['A05', 'aggregation', 'aggregate_fixture', 'PASS'],
  ['A06', 'aggregation', 'aggregate_fixture', 'PASS'],
];
const benchmarkFixture = {
  summary: { cases: 38, pass: 37, fail: 1, unmeasured: 0, executed: 38 },
  contract_gate: { passed: true },
  gold_sha256: '4aae6aa0054d42820626f72fa5194d16902544e86629d1a57f69b52a971707af',
  scope: 'Fixed 38-case independent diagnostic; not all-Arabic completeness.',
  rows: caseMatrix.map(([id, family, mode, outcome]) => ({ id, family, mode, outcome,
    checks: [], observed: { fixture: 'compact display fixture; see source report' } })),
};

function report(mode = 'inference', changes = {}) {
  return structuredClone({
    schema: 'nabt.proof-lab-result.v1', request_id: requestId, mode,
    payload_sha256: 'a'.repeat(64),
    code_sha: 'f0d41d3c6320fe78ac31ce60411fbb3442dc8293',
    duration_ms: 110, native_sha256: 'b'.repeat(64), status: mode === 'inference' ? nativeFixture.status : 'BENCHMARK_COMPLETE', all_arabic_complete: false, world_truth_established: false,
    ...(mode === 'inference' ? { result: bindInferenceFixture(nativeFixture,requestId,'f0d41d3c6320fe78ac31ce60411fbb3442dc8293') } : { benchmark: benchmarkFixture }),
    ...changes,
  });
}

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.listeners = {}; this.children = []; this.hidden = false;
    this.textContent = ''; this.style = {}; this.dataset = {}; this.attrs = {};
    this.value = ''; this.max = ''; this.disabled = false; this.className = '';
    const classes = new Set();
    this.classList = { add: name => classes.add(name), remove: name => classes.delete(name),
      toggle: (name, on) => on ? classes.add(name) : classes.delete(name),
      contains: name => classes.has(name) };
  }
  // The current UI uses textContent/createElement for untrusted result strings.
  // Any future innerHTML route makes these interaction tests fail explicitly.
  set innerHTML(_) { throw new Error('HTML injection sink used in frontend'); }
  get valueAsNumber() { return this.value === '' ? NaN : Number(this.value); }
  addEventListener(name, fn) { (this.listeners[name] ??= []).push(fn); }
  fire(name, event = {}) { for (const fn of this.listeners[name] || []) fn({ preventDefault() {}, ...event }); }
  setAttribute(name, value) { this.attrs[name] = value; }
  append(...values) { this.children.push(...values); }
  replaceChildren(...values) { this.children = values; }
  reportValidity() { return true; }
  focus() {}
  scrollIntoView() {}
  click() { this.fire('click'); }
  remove() {}
}

const flush = async () => { for (let i = 0; i < 24; i++) await new Promise(resolve=>setImmediate(resolve)); };

async function harness({ ready = true, stored = null, pollResponse = null } = {}) {
  const nodes = new Map();
  for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) {
    assert(!nodes.has(match[3]), 'Duplicate HTML id: ' + match[3]);
    const element = new Element(match[1]);
    element.hidden = /\bhidden\b/.test(match[2]);
    element.disabled = /\bdisabled\b/.test(match[2]);
    element.value = /\bvalue="([^"]*)"/.exec(match[2])?.[1] || '';
    element.max = /\bmax="([^"]*)"/.exec(match[2])?.[1] || '';
    nodes.set(match[3], element);
  }
  const get = id => { assert(nodes.has(id), 'Unknown DOM id: ' + id); return nodes.get(id); };
  get('source-text').value = /<textarea[^>]*id="source-text"[^>]*>([\s\S]*?)<\/textarea>/.exec(html)[1];
  get('case-filter').value = 'all';
  get('testimony-target').value = 'المأوى';
  get('workflow-operation').value='lexical_surface';get('workflow-profile').value='linguistic';
  get('workflow-frame').value=JSON.stringify({root:['ء','ك','ل'],profile:'all_attested'});
  const tabs = ['evidence', 'inference', 'coverage', 'testimony', 'guide'].map(name => {
    const element = get('tab-' + name); element.dataset.tab = name; return element;
  });
  const examples = ['supported', 'missing', 'hidden', 'inverse', 'outside'].map(name => {
    const element = new Element('button'); element.dataset.example = name; return element;
  });
  const tablist = new Element();
  const document = {
    getElementById: get,
    querySelectorAll: selector => selector === '[data-tab]' ? tabs : selector === '[data-example]' ? examples : [],
    querySelector: selector => selector === '.tabs' ? tablist : null,
    createElement: tag => new Element(tag), body: new Element(), activeElement: null,
  };
  const timers = new Map(); const storage = new Map(); const requests = [];
  let timerId = 0; let response = pollResponse || { status: 'in_progress' };
  if (stored) storage.set(pendingKey, JSON.stringify(stored));
  const sandbox = vm.createContext({ document, TextEncoder, AbortSignal, Blob, URL,
    Date, Number, JSON, Error, console, crypto: {subtle:{digest:async(_algorithm,bytes)=>createHash('sha256').update(bytes).digest()}}, Uint8Array,
    sessionStorage: { setItem: (key, value) => storage.set(key, value),
      getItem: key => storage.get(key) || null, removeItem: key => storage.delete(key) },
    setTimeout: fn => { timers.set(++timerId, fn); return timerId; },
    clearTimeout: id => timers.delete(id), setInterval: () => -1, clearInterval() {},
    fetch: async (path, options) => {
      requests.push({ path, options });
      let body;
      if (path === '/api/config') body = { ready, code_sha: 'f'.repeat(40), law: 'nabt.licensed-inference.v1' };
      else if (path === '/api/runs') body = { handle: 'signed-test-handle', request_id: requestId, status: 'queued' };
      else body = response;
      return { ok: true, status: 200, json: async () => structuredClone(body) };
    },
  });
  for(const name of ['workflow-contract.js','workflow-ui.js'])vm.runInContext(readFileSync(new URL('../web/'+name,import.meta.url),'utf8'),sandbox);
  vm.runInContext(authority, sandbox, {filename:'web/legacy-authority.js'});
  vm.runInContext(app, sandbox, { filename: 'web/app.js' });
  await flush();
  return {
    get, nodes, examples, requests, storage,
    setResponse: value => { response = value; },
    posts: () => requests.filter(item => item.options?.method === 'POST'),
    submit: async mode => { get(mode === 'benchmark' ? 'run-benchmark' : mode === 'testimony' ? 'testimony-form' : mode === 'licensed_workflow' ? 'workflow-form' : 'inference-form').fire(mode === 'benchmark' ? 'click' : 'submit'); await flush(); },
    poll: async () => {
      const next = timers.entries().next().value;
      assert(next, 'Expected a scheduled polling callback'); timers.delete(next[0]);
      await next[1](); await flush();
    },
  };
}

test('unconfigured secure transport disables both dynamic actions and produces no request', async () => {
  const ui = await harness({ ready: false });
  assert.equal(ui.get('run-inference').disabled, true);
  assert.equal(ui.get('run-benchmark').disabled, true);
  assert.equal(ui.get('inference-output').hidden, true);
  assert.equal(ui.get('benchmark-output').hidden, true);
  assert.match(ui.get('global-message').textContent, /تفعيل مفتاح النقل الآمن/);
  await ui.submit('inference'); await ui.submit('benchmark');
  assert.equal(ui.posts().length, 0);
});

test('native supported result displays certificate and exact source without claiming world truth', async () => {
  const ui = await harness();
  ui.setResponse({ status: 'completed', report: report() });
  await ui.submit('inference'); await ui.poll();
  assert.equal(ui.get('verdict-code').textContent, 'SUPPORTED');
  assert.equal(ui.get('native-status').textContent, 'شهادة مفحوصة');
  assert.equal(ui.get('proof-trace').children.length, 2);
  assert.equal(ui.get('executed-source').textContent, sourceText);
  assert.equal(ui.get('executed-query').textContent, queryText);
  assert.equal(ui.get('inference-request-id').textContent, requestId);
  assert.match(ui.get('verdict-description').textContent, /ليس إثباتًا لوقوعه في العالم/);
  assert.equal(ui.storage.size, 0);
});

test('unknown conclusion remains distinct from an accepted native certificate', async () => {
  const ui = await harness();
  const value = report(); value.result.status = 'UNKNOWN';
  value.result.source.raw_text = 'إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ.';
  value.result.readings[0].clauses = [clauses[0]];
  value.result.readings[0].status = 'UNKNOWN';
  value.result.readings[0].positive = false;
  value.result.readings[0].clean_positive = false;
  value.result.closure_records[0] = { clauses: [clauses[0]], query: movement,
    steps: [], known: [], clean_steps: [], clean_known: [] };
  value.result.aggregate.skeptical_clean_positive = false;
  value.result.aggregate.credulous_positive = false;
  value.status='UNKNOWN';value.result=bindInferenceFixture(value.result,requestId,value.code_sha);
  ui.setResponse({ status: 'completed', report: value });
  await ui.submit('inference'); await ui.poll();
  assert.equal(ui.get('verdict-code').textContent, 'UNKNOWN');
  assert.equal(ui.get('verdict-title').textContent, 'الاستنتاج غير معلوم');
  assert.equal(ui.get('native-status').textContent, 'شهادة مفحوصة');
});

test('source, query and budget edits mark the previous report stale and retain its original text', async () => {
  const ui = await harness();
  ui.setResponse({ status: 'completed', report: report() });
  await ui.submit('inference'); await ui.poll();
  assert.equal(ui.get('stale-note').hidden, true);
  for (const [id, changed] of [['source-text', '<img src=x onerror=alert(1)>'], ['query-text', 'هَلْ عَرَفَ زَيْدٌ الْحَقَّ؟'], ['budget-steps', '0']]) {
    const original = ui.get(id).value;
    ui.get(id).value = changed; ui.get(id).fire('input');
    assert.equal(ui.get('stale-note').hidden, false);
    assert.equal(ui.get('executed-source').textContent, sourceText);
    ui.get(id).value = original; ui.get(id).fire('input');
    assert.equal(ui.get('stale-note').hidden, true);
  }
});

test('frozen 38-case result retains its one failure and supports outcome filters', async () => {
  const ui = await harness();
  ui.setResponse({ status: 'completed', report: report('benchmark') });
  await ui.submit('benchmark'); await ui.poll();
  assert.equal(ui.get('benchmark-output').hidden, false);
  assert.equal(ui.get('benchmark-rows').children.length, 38);
  assert.equal(ui.get('bench-total').textContent, (38).toLocaleString('ar-JO'));
  assert.equal(ui.get('bench-fail').textContent, (1).toLocaleString('ar-JO'));
  ui.get('case-filter').value = 'FAIL'; ui.get('case-filter').fire('change');
  assert.equal(ui.get('benchmark-rows').children.length, 1);
  assert.equal(ui.get('benchmark-rows').children[0].children[0].textContent, 'L26');
  ui.get('case-filter').value = 'PASS'; ui.get('case-filter').fire('change');
  assert.equal(ui.get('benchmark-rows').children.length, 37);
  ui.get('case-filter').value = 'UNMEASURED'; ui.get('case-filter').fire('change');
  assert.equal(ui.get('benchmark-rows').children.length, 0);
  assert.equal(ui.get('empty-filter').hidden, false);
  assert.match(ui.get('benchmark-ratio').textContent, /ضمن هذه المجموعة وحدها/);
});

test('inconsistent benchmark denominator is rejected instead of showing an invented percentage', async () => {
  const ui = await harness(); const value = report('benchmark');
  value.benchmark.rows.pop();
  ui.setResponse({ status: 'completed', report: value });
  await ui.submit('benchmark'); await ui.poll();
  assert.equal(ui.get('benchmark-output').hidden, true);
  assert.match(ui.get('global-message').textContent, /مقام القياس لا يطابق/);
});

test('only the pending handle metadata is retained, and reload resumes without duplicate dispatch', async () => {
  const ui = await harness(); await ui.submit('inference');
  const stored = JSON.parse(ui.storage.get(pendingKey));
  assert.deepEqual(Object.keys(stored).sort(), ['handle', 'mode', 'request_id', 'started']);
  assert(!JSON.stringify(stored).includes(sourceText));
  assert(!JSON.stringify(stored).includes(queryText));
  const reloaded = await harness({ stored, pollResponse: { status: 'completed', report: report() } });
  assert.equal(reloaded.posts().length, 0);
  assert(reloaded.requests.some(item => item.path === '/api/runs?handle=signed-test-handle'));
  assert.equal(reloaded.get('verdict-code').textContent, 'SUPPORTED');
  assert.equal(reloaded.storage.size, 0);
});

test('request identity mismatch pauses polling with no accepted report and no second dispatch', async () => {
  const ui = await harness();
  ui.setResponse({ status: 'completed', report: report('inference', { request_id: '22222222-2222-4222-8222-222222222222' }) });
  await ui.submit('inference');
  await ui.poll(); await ui.poll(); await ui.poll();
  assert.equal(ui.get('inference-output').hidden, true);
  assert.equal(ui.get('resume-poll').hidden, false);
  assert.equal(ui.posts().length, 1);
  assert.equal(ui.storage.size, 1);
});

test('whole-Arabic authority promotion in a response is not displayed as an accepted result', async () => {
  const ui = await harness();
  ui.setResponse({ status: 'completed', report: report('inference', { all_arabic_complete: true }) });
  await ui.submit('inference'); await ui.poll(); await ui.poll(); await ui.poll();
  assert.equal(ui.get('inference-output').hidden, true);
  assert.match(ui.get('job-description').textContent, /يخالف نطاق المختبر/);
});

test('resource exhaustion is displayed without a certified inference claim', async () => {
  const ui = await harness(); const value = report();
  value.result = { status: 'RESOURCE_EXHAUSTED', reason: 'MAX_CLOSURE_STEPS',
    native_checked: false, verified: false, all_readings_complete: false, closures_checked: false,
    source: { raw_text: sourceText }, query: { raw_text: queryText }, readings: [], closure_records: [] };
  value.status='RESOURCE_EXHAUSTED';value.result=bindInferenceFixture(value.result,requestId,value.code_sha);
  ui.setResponse({ status: 'completed', report: value });
  await ui.submit('inference'); await ui.poll();
  assert.equal(ui.get('verdict-title').textContent, 'انتهت ميزانية البحث');
  assert.equal(ui.get('native-status').textContent, 'لم تثبت شهادة مقبولة');
  assert.match(ui.get('verdict-description').textContent, /لم يصدر عن ذلك حكم برفض العبارة لغويًا/);
});

test('zero budget is forwarded but fractional budgets are rejected before submission', async () => {
  const zero = await harness(); zero.get('budget-steps').value = '0';
  await zero.submit('inference');
  assert.equal(JSON.parse(zero.posts()[0].options.body).budget.max_closure_steps, 0);
  const fractional = await harness(); fractional.get('budget-steps').value = '1.5';
  await fractional.submit('inference');
  assert.equal(fractional.posts().length, 0);
  assert.match(fractional.get('global-message').textContent, /أعداد صحيحة/);
});

const testimonyFixture=JSON.parse(readFileSync(new URL('./fixtures/testimony.json',import.meta.url),'utf8'));
test('testimony UI dispatches exact components and keeps provenance apart from Lean result',async()=>{
  const ui=await harness();
  const value=report('testimony',{testimony:testimonyFixture,status:testimonyFixture.status});delete value.benchmark;
  ui.setResponse({status:'completed',report:value});
  await ui.submit('testimony');
  assert.deepEqual(JSON.parse(ui.posts()[0].options.body),{schema:'nabt.proof-lab-request.v1',mode:'testimony',entry:'بيت',target:['المأوى']});
  await ui.poll();
  assert.equal(ui.get('testimony-output').hidden,false);
  assert.match(ui.get('testimony-status').textContent,/Lean مفعل/);
  assert.match(ui.get('testimony-scope').textContent,/نوع النقل غير مقيّم/);
  assert.equal(ui.get('testimony-rows').children.length,1);
  assert.equal(ui.storage.size,0);
});
test('testimony unavailable result clears old rows without a successful check label',async()=>{
  const ui=await harness();
  ui.setResponse({status:'completed',report:report('testimony',{status:'VERIFICATION_UNAVAILABLE',error:'NATIVE_CHECKER_MISSING'})});
  await ui.submit('testimony');await ui.poll();
  assert.match(ui.get('testimony-status').textContent,/لم تُقبل شهادة/);
  assert.equal(ui.get('testimony-rows').children.length,0);
});
test('disabled connection cannot submit testimony',async()=>{
  const ui=await harness({ready:false});await ui.submit('testimony');
  assert.equal(ui.get('run-testimony').disabled,true);assert.equal(ui.posts().length,0);
});


test('legacy inference does not display a native contradiction as proof',async()=>{
 const ui=await harness();const value=report();value.result.native_result.verified=false;
 ui.setResponse({status:'completed',report:value});await ui.submit('inference');
 await ui.poll();await ui.poll();await ui.poll();
 assert.equal(ui.get('inference-output').hidden,true);
 assert.equal(ui.get('resume-poll').hidden,false);
});
test('new inference clears prior displayed authority while retaining the request button',async()=>{
 const ui=await harness();const button=ui.get('run-inference');
 ui.setResponse({status:'completed',report:report()});await ui.submit('inference');await ui.poll();
 assert.equal(ui.get('inference-output').hidden,false);
 assert.match(ui.get('inference-bridge').textContent,/لا يحمل إيصال المسار القديم/);
 ui.setResponse({status:'in_progress'});await ui.submit('inference');
 assert.equal(ui.get('inference-output').hidden,true);assert.equal(ui.get('run-inference'),button);
});


test('workflow UI dispatches raw input and renders only individually bound claims',async()=>{
 const ui=await harness(),r=workflowReport();
 r.migration_inventory.states={SCOPED_GATEWAY_INSTALLED:1};r.migration_inventory.surfaces[0].migration_state='SCOPED_GATEWAY_INSTALLED';
 ui.setResponse({status:'completed',report:r});
 await ui.submit('licensed_workflow');await ui.poll();
 const payload=JSON.parse(ui.posts()[0].options.body);
 assert.equal(payload.mode,'licensed_workflow');assert.equal(payload.workflow.op,'lexical_surface');
 assert.equal(ui.get('workflow-output').hidden,false);
 assert.equal(ui.get('workflow-claims').children.length,1);
 assert.match(ui.get('workflow-claims').children[0].children[0].textContent,/برهان الدعوى المحددة/);
 assert.match(ui.get('workflow-inventory-count').textContent,/لا يساوي اكتمال تحصيل/);
 assert.match(ui.get('workflow-migration').children[0].textContent,/الإتاحة تُفحص عند التشغيل/);
});
test('workflow failure clears preceding claims and keeps the same keyboard target',async()=>{
 const ui=await harness(),button=ui.get('run-workflow');ui.setResponse({status:'completed',report:workflowReport()});
 await ui.submit('licensed_workflow');await ui.poll();
 ui.setResponse({status:'completed',report:workflowReport({checked:false})});
 await ui.submit('licensed_workflow');assert.equal(ui.get('workflow-output').hidden,true);await ui.poll();
 assert.equal(ui.get('run-workflow'),button);assert.equal(ui.get('workflow-claims').children.length,1);
 assert.match(ui.get('workflow-claims').children[0].textContent,/لا توجد دعوى مبرهنة/);
});


test('scope selector offers an executed envelope and explains its bounded grammar',async()=>{
 const ui=await harness(),select=ui.get('workflow-operation');
 select.value='scope_acquisition';select.fire('change');
 assert.equal(ui.get('workflow-text').value,'قَالَ زَيْدٌ: «أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ».');
 assert.equal(ui.get('workflow-scope-help').hidden,false);
 await ui.submit('licensed_workflow');
 const sent=JSON.parse(ui.posts()[0].options.body).workflow;
 assert.equal(sent.op,'scope_acquisition');assert.equal(sent.input.text,ui.get('workflow-text').value);
 select.value='lexical_surface';select.fire('change');
 assert.equal(ui.get('workflow-scope-help').hidden,true);
});

test('discourse selector preserves its controls and keeps boundary proof separate from intent',async()=>{
 const ui=await harness(),select=ui.get('workflow-operation'),button=ui.get('run-workflow');
 select.value='discourse_boundary';select.fire('change');
 assert.equal(ui.get('workflow-text').value,'لم أر أسداً قط؛ وأقصد بالأسد الحيوان المعروف.');
 assert.equal(ui.get('workflow-discourse-help').hidden,false);
 assert.equal(ui.get('workflow-profile-group').hidden,false);
 assert.equal(ui.get('workflow-query-group').hidden,true);
 ui.setResponse({status:'completed',report:workflowReport({op:'discourse_boundary'})});
 await ui.submit('licensed_workflow');await ui.poll();
 const request=JSON.parse(ui.posts()[0].options.body).workflow;
 assert.equal(request.op,'discourse_boundary');assert.equal(request.input.profile_id,'linguistic');
 assert.equal(ui.get('workflow-operation'),select);assert.equal(ui.get('run-workflow'),button);
 assert.match(ui.get('workflow-claims').children[0].children[0].textContent,/EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE/);
 select.value='lexical_surface';select.fire('change');
 assert.equal(ui.get('workflow-discourse-help').hidden,true);
 assert.equal(ui.get('workflow-output').hidden,true);
 assert.equal(ui.get('workflow-claims').children.length,0);
 assert.equal(ui.get('download-workflow').disabled,true);
});

test('source inference sends separate source and query with explicit scope and stable controls',async()=>{
 const ui=await harness(),select=ui.get('workflow-operation'),button=ui.get('run-workflow'),query=ui.get('workflow-query');
 select.value='source_inference';select.fire('change');
 assert.equal(ui.get('workflow-query-group').hidden,false);
 assert.equal(ui.get('workflow-inference-help').hidden,false);
 assert.equal(ui.get('workflow-profile-group').hidden,true);
 assert.equal(query.value,'هل سار زيد؟');
 ui.setResponse({status:'completed',report:workflowReport({op:'source_inference'})});
 await ui.submit('licensed_workflow');await ui.poll();
 const request=JSON.parse(ui.posts()[0].options.body).workflow;
 assert.equal(request.op,'source_inference');
 assert.equal(request.input.source,'إن عرف زيد الحق سار زيد. عرف زيد الحق.');
 assert.equal(request.input.query,'هل سار زيد؟');
 assert.equal(request.input.scope,'مقام جديد غير محسوم');assert.equal('context' in request.input,false);
 assert.equal(ui.get('workflow-operation'),select);assert.equal(ui.get('run-workflow'),button);
 assert.equal(ui.get('workflow-query'),query);
 assert.match(ui.get('workflow-claims').children[0].children[0].textContent,/SOURCE_BOUND_FINITE_INFERENCE/);
 select.value='lexical_surface';select.fire('change');
 assert.equal(ui.get('workflow-query-group').hidden,true);
 assert.equal(ui.get('workflow-context-label').textContent,'المقام المعلن');
});

for(const id of ['workflow-text','workflow-query','workflow-context','workflow-profile','workflow-frame','workflow-rule'])
test('editing '+id+' clears displayed proof without replacing the keyboard target',async()=>{
 const ui=await harness(),input=ui.get(id),button=ui.get('run-workflow');
 ui.setResponse({status:'completed',report:workflowReport()});
 await ui.submit('licensed_workflow');await ui.poll();
 assert.equal(ui.get('download-workflow').disabled,false);
 input.value+=' changed';input.fire('input');
 assert.equal(ui.get(id),input);assert.equal(ui.get('run-workflow'),button);
 assert.equal(ui.get('workflow-output').hidden,true);assert.equal(ui.get('workflow-claims').children.length,0);
 assert.equal(ui.get('download-workflow').disabled,true);
 assert.match(ui.get('workflow-message').textContent,/النتيجة السابقة لا تثبت المدخل الحالي/);
});

test('a delayed workflow receipt cannot restore proof beside an edited query',async()=>{
 const ui=await harness(),select=ui.get('workflow-operation'),query=ui.get('workflow-query');
 select.value='source_inference';select.fire('change');
 ui.setResponse({status:'completed',report:workflowReport({op:'source_inference'})});
 await ui.submit('licensed_workflow');
 query.value='هل سار عمرو؟';query.fire('input');await ui.poll();
 assert.equal(ui.get('workflow-query'),query);assert.equal(query.value,'هل سار عمرو؟');
 assert.equal(ui.get('workflow-output').hidden,true);assert.equal(ui.get('workflow-claims').children.length,0);
 assert.equal(ui.get('download-workflow').disabled,true);
 assert.match(ui.get('workflow-message').textContent,/إيصال متحقق لطلب سابق/);
});

test('unestablished discourse convention sends explicit null instead of a linguistic default',async()=>{
 const ui=await harness(),select=ui.get('workflow-operation');
 select.value='discourse_boundary';select.fire('change');
 ui.get('workflow-profile').value='';ui.get('workflow-profile').fire('change');
 await ui.submit('licensed_workflow');
 const request=JSON.parse(ui.posts()[0].options.body).workflow;
 assert.equal(request.op,'discourse_boundary');
 assert.equal(Object.hasOwn(request.input,'profile_id'),true);assert.equal(request.input.profile_id,null);
 assert.equal(ui.get('workflow-claims').children.length,0);
});
