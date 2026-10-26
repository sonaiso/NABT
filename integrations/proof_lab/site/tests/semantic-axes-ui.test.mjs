import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { webcrypto } from 'node:crypto';
import test from 'node:test';
import vm from 'node:vm';

const file = name => readFileSync(new URL('../web/' + name, import.meta.url), 'utf8');
const html = file('index.html');
const requestId = '11111111-1111-4111-8111-111111111111';
const axes = ['syntax', 'readings', 'reference', 'motive', 'world'];
function suite() {
  const statuses = [ ['PASS', 'PASS', 'UNMEASURED', 'UNMEASURED', 'UNMEASURED'], ['FAIL', 'UNMEASURED', 'PASS', 'NOT_APPLICABLE', 'UNMEASURED'] ];
  const cases = statuses.map((values, i) => ({ id: 'S0' + (i + 1), family: 'context_collision', context_id: 'C0' + (i + 1), case_input_sha256: String(i + 1).repeat(64), input: { text: 'هُوَ هُنَا.', context: { speaker: i ? 'عمرو' : 'زيد', referent: i ? 'عمرو' : 'زيد' } },
    axis_results: Object.fromEntries(axes.map((axis, index) => [axis, { status: values[index], expected: axis === 'reference' ? (i ? 'عمرو' : 'زيد') : 'مرجع مؤلف', observed: values[index] === 'UNMEASURED' ? null : 'قيمة مرصودة', reason: 'نطاق القراءة المثبتة' }])),
    claims: axes.filter((_, index) => values[index] !== 'NOT_APPLICABLE').map(axis => ({ id: 'S0' + (i + 1) + ':' + axis, axis, statement: 'دعوى مستقلة في جهة ' + axis, status: values[axes.indexOf(axis)], verification: { claim_id: 'S0' + (i + 1) + ':' + axis, input_sha256: String(i + 1).repeat(64), certificate_sha256: 'c'.repeat(64), kind: values[axes.indexOf(axis)] === 'UNMEASURED' ? 'NOT_CHECKED' : 'PYTHON_REPLAY', checked: values[axes.indexOf(axis)] !== 'UNMEASURED', scope: 'هذه العبارة ومقامها داخل النموذج المثبت فقط.', theorem_references: [] } })) }));
  return { schema: 'nabt.semantic-axes-benchmark.v1', all_arabic_complete: false, lean_native_checked: false, case_count: 2, scope: 'مرجع تشخيصي محدود، لا اكتمال العربية.', reference_sha256: 'b'.repeat(64), cases,
    axes: { syntax: { eligible: 2, measured: 2, passed: 1, failed: 1, unmeasured: 0, rate: .5 }, readings: { eligible: 2, measured: 1, passed: 1, failed: 0, unmeasured: 1, rate: 1 }, reference: { eligible: 2, measured: 1, passed: 1, failed: 0, unmeasured: 1, rate: 1 }, motive: { eligible: 1, measured: 0, passed: 0, failed: 0, unmeasured: 1, rate: null }, world: { eligible: 2, measured: 0, passed: 0, failed: 0, unmeasured: 2, rate: null } },
    safety_checks: { unsupported_motive_attribution: { passed: 2, eligible: 2, scope: 'منع الادعاء فقط' } } };
}
const receipt = changes => ({ schema: 'nabt.proof-lab-result.v1', mode: 'semantic_axes', request_id: requestId, code_sha: 'a'.repeat(40), all_arabic_complete: false, world_truth_established: false, semantic_axes: suite(), ...changes });
const pure = () => { const context = vm.createContext({ TextEncoder, crypto: webcrypto }); vm.runInContext(file('semantic-axes.js'), context); vm.runInContext(file('evidence-audit.js'), context); return context; };
class Element {
  constructor(tag, document) { this.tag = tag; this.document = document; this.children = []; this.textContent = ''; this.hidden = false; this.disabled = false; this.dataset = {}; this.attrs = {}; this.listeners = {}; this.style = {}; this.value = ''; this.max = ''; this.connected = true; this.classes = new Set(); this.classList = { toggle: (name, on) => on ? this.classes.add(name) : this.classes.delete(name), add: name => this.classes.add(name), remove: name => this.classes.delete(name) }; }
  set innerHTML(_) { throw new Error('Unsafe HTML sink'); }
  get valueAsNumber() { return Number(this.value); }
  addEventListener(name, handler) { (this.listeners[name] ??= []).push(handler); }
  fire(name, event = {}) { for (const fn of this.listeners[name] || []) fn({ preventDefault() {}, target: this, ...event }); }
  setAttribute(key, value) { this.attrs[key] = value; }
  append(...nodes) { this.children.push(...nodes); }
  disconnect() { this.connected = false; if (this.document.activeElement === this) this.document.activeElement = this.document.body; this.children.forEach(n => n.disconnect()); }
  replaceChildren(...nodes) { this.children.forEach(n => n.disconnect()); this.children = nodes; }
  focus() { if (this.connected) this.document.activeElement = this; }
  click() { this.fire('click'); }
  reportValidity() { return true; }
  scrollIntoView() {}
  remove() { this.disconnect(); }
}
const contents = el => el.textContent + ' ' + el.children.map(contents).join(' ');
const flush = async () => { for (let i = 0; i < 25; i++) await Promise.resolve(); };
async function harness({ ready = true } = {}) {
  const document = { activeElement: null }, nodes = new Map(), timers = new Map(), requests = [], storage = new Map(); let n = 0, response;
  document.body = new Element('body', document); document.activeElement = document.body;
  for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) { assert(!nodes.has(match[3])); const el = new Element(match[1], document); el.hidden = /\bhidden\b/.test(match[2]); el.disabled = /\bdisabled\b/.test(match[2]); el.value = /\bvalue="([^"]*)"/.exec(match[2])?.[1] || ''; el.max = /\bmax="([^"]*)"/.exec(match[2])?.[1] || ''; nodes.set(match[3], el); }
  const get = id => { assert(nodes.has(id), 'Unknown node: ' + id); return nodes.get(id); };
  const tabs = [...html.matchAll(/id="tab-([^"]+)"/g)].map(match => { const el = get('tab-' + match[1]); el.dataset.tab = match[1]; return el; });
  const tablist = new Element('div', document);
  Object.assign(document, { getElementById: get, createElement: tag => new Element(tag, document), querySelector: selector => selector === '.tabs' ? tablist : null, querySelectorAll: selector => selector === '[data-tab]' ? tabs : [] });
  const context = vm.createContext({ document, TextEncoder, AbortSignal, Blob, URL, console, Date, Number, JSON, Error,
    sessionStorage: { setItem: (k, v) => storage.set(k, v), getItem: k => storage.get(k) || null, removeItem: k => storage.delete(k) },
    setTimeout: fn => { timers.set(++n, fn); return n; }, clearTimeout: id => timers.delete(id), setInterval: () => -1, clearInterval() {},
    fetch: async (path, options) => { requests.push({ path, options }); return { ok: true, status: 200, json: async () => path === '/api/config' ? { ready, code_sha: 'a'.repeat(40) } : path === '/api/runs' ? { handle: 'sealed-handle', request_id: requestId } : response }; } });
  vm.runInContext(file('semantic-axes.js'), context); vm.runInContext(file('app.js'), context); await flush();
  return { get, document, context, tablist, requests, setResponse: v => { response = v; }, async submit() { get('run-semantic-axes').click(); await flush(); }, async poll() { const next = timers.entries().next().value; assert(next); timers.delete(next[0]); await next[1](); await flush(); }, activate(el, key) { el.focus(); el.fire('keydown', { key }); el.click(); el.fire('keyup', { key }); } };
}

test('axis denominator validation rejects lossy integers, disagreement, and invented zero-denominator rates', () => {
  const api = pure().NabtSemanticAxes; assert.equal(api.validate(suite()).case_count, 2);
  for (const bad of [true, 1.5, 9007199254740992]) { const data = suite(); data.axes.syntax.measured = bad; assert.throws(() => api.validate(data)); }
  const mismatch = suite(); mismatch.axes.motive.measured = 1; assert.throws(() => api.validate(mismatch));
  const zero = suite(); zero.axes.world.rate = 0; assert.throws(() => api.validate(zero));
  for (const patch of [{ all_arabic_complete: true }, { lean_native_checked: true }]) assert.throws(() => api.validate({ ...suite(), ...patch }));
  const missing = suite(); missing.cases[0].claims = []; assert.throws(() => api.validate(missing));
  const context = suite(); context.cases[0].input.context = 'untyped'; assert.throws(() => api.validate(context));
  const duplicate = suite(); duplicate.cases[1].id = duplicate.cases[0].id; assert.throws(() => api.validate(duplicate));
});

test('v1 cannot promote any claim to Lean and rejects contradictory local verification', () => {
  const api = pure().NabtSemanticAxes; const claim = suite().cases[0].claims[0];
  assert.match(api.verificationLabel({ ...claim, native_checked: true, verified: true }), /Python/);
  for (const patch of [{ kind: 'LEAN_NATIVE', certificate_sha256: 'e'.repeat(64), theorem_references: ['Nabt.example'] }, { checked: false }, { kind: 'NOT_CHECKED' }, { scope: '' }, { theorem_references: ['Nabt.example'] }, { claim_id: 'wrong-claim' }, { input_sha256: 'f'.repeat(64) }]) {
    const data = suite(); Object.assign(data.cases[0].claims[0].verification, patch); assert.throws(() => api.validate(data));
  }
  const mismatch = suite(); mismatch.cases[0].claims[0].status = 'FAIL'; assert.throws(() => api.validate(mismatch));
  const unmeasured = suite(); unmeasured.cases[0].claims[2].verification.checked = true; assert.throws(() => api.validate(unmeasured));
});

test('imported axes retain five denominators but never a live or checked rank', async () => {
  const context = pure(); const report = receipt();
  const out = await context.NabtEvidenceAudit.audit(JSON.stringify(report));
  assert.equal(out.semantic_axes.axes.world.measured, 0); assert.equal(out.authority.lean_replayed, false);
  assert(out.claims.every(c => c.rank === 'تصريح مستورد' && c.replayed === false));
  report.semantic_axes.cases[0].claims[0].verification.kind = 'LEAN_NATIVE';
  await assert.rejects(() => context.NabtEvidenceAudit.audit(JSON.stringify(report)));
});

test('valid failure receipt has no suite payload and is not misreported as zero successful tests', async () => {
  const context = pure(); const report = receipt({ status: 'VERIFICATION_UNAVAILABLE', error: 'CHECKER_MISSING' }); delete report.semantic_axes;
  const out = await context.NabtEvidenceAudit.audit(JSON.stringify(report)); assert.equal(out.operational_failure.measurements_available, false); assert.equal(out.semantic_axes, undefined);
});

test('live dispatch is minimal and axes keep reference comparison apart from proof', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: receipt() }); await ui.submit();
  const posted = ui.requests.find(r => r.options?.method === 'POST'); assert.deepEqual(JSON.parse(posted.options.body), { schema: 'nabt.proof-lab-request.v1', mode: 'semantic_axes' }); await ui.poll();
  assert.equal(ui.get('semantic-output').hidden, false); assert.equal(ui.get('semantic-axis-metrics').children.length, 5);
  assert.match(contents(ui.get('semantic-axis-metrics').children[4]), /غير مقاس/);
  assert.match(contents(ui.get('semantic-case-detail')), /إعادة فحص Python/);
  assert.equal(ui.get('semantic-case-detail').children.flatMap(n => n.children).some(n => n.className === 'semantic-proof'), false);
});

test('case activation by Enter and Space preserves focused button and distinct context', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: receipt() }); await ui.submit(); await ui.poll();
  const list = ui.get('semantic-cases'), second = list.children[1];
  for (const key of ['Enter', ' ']) { ui.activate(second, key); assert.equal(ui.document.activeElement, second); assert.equal(list.children[1], second); assert.equal(second.attrs['aria-pressed'], 'true'); assert.match(contents(ui.get('semantic-case-detail')), /C02/); }
  assert.match(contents(ui.get('semantic-case-detail')), /عمرو/);
});

test('new tab supports RTL keyboard navigation without changing focus to result text', async () => {
  const ui = await harness(); const tab = ui.get('tab-semantic_axes'); tab.focus(); tab.click();
  assert.equal(ui.get('panel-semantic_axes').hidden, false); assert.equal(ui.document.activeElement, tab);
  ui.tablist.fire('keydown', { key: 'ArrowLeft' }); assert.equal(ui.document.activeElement, ui.get('tab-guide'));
  ui.tablist.fire('keydown', { key: 'ArrowRight' }); assert.equal(ui.document.activeElement, tab);
});

test('starting another run and a subsequent failure clear all old claim displays', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: receipt() }); await ui.submit(); await ui.poll(); assert.equal(ui.get('semantic-output').hidden, false);
  await ui.submit(); assert.equal(ui.get('semantic-output').hidden, true); assert.equal(ui.get('semantic-case-detail').children.length, 0);
  const failure = receipt({ status: 'VERIFICATION_UNAVAILABLE', error: 'CHECKER_MISSING' }); delete failure.semantic_axes;
  ui.setResponse({ status: 'completed', report: failure }); await ui.poll(); assert.equal(ui.get('semantic-output').hidden, true); assert.match(ui.get('semantic-empty-title').textContent, /CHECKER_MISSING/);
});

test('disabled connection prevents suite submission', async () => {
  const ui = await harness({ ready: false }); assert.equal(ui.get('run-semantic-axes').disabled, true); await ui.submit(); assert.equal(ui.requests.filter(r => r.options?.method === 'POST').length, 0);
});
