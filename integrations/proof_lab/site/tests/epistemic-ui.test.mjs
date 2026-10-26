import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';
import { report, unavailable, requestId } from './helpers/epistemic-fixture.mjs';
const file = name => readFileSync(new URL('../web/' + name, import.meta.url), 'utf8');
const html = file('index.html');
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
const flush = async () => { for (let i = 0; i < 40; i++) await Promise.resolve(); };
async function harness({ ready = true } = {}) {
  const document = { activeElement: null }, nodes = new Map(), timers = new Map(), requests = [], storage = new Map(); let n = 0, response;
  document.body = new Element('body', document); document.activeElement = document.body;
  for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) { assert(!nodes.has(match[3])); const el = new Element(match[1], document); el.hidden = /\bhidden\b/.test(match[2]); el.disabled = /\bdisabled\b/.test(match[2]); el.value = /\bvalue="([^"]*)"/.exec(match[2])?.[1] || ''; el.max = /\bmax="([^"]*)"/.exec(match[2])?.[1] || ''; nodes.set(match[3], el); }
  const get = id => { assert(nodes.has(id), 'Unknown node: ' + id); return nodes.get(id); };
  const tabs = [...html.matchAll(/id="tab-([^"]+)"/g)].map(match => { const el = get('tab-' + match[1]); el.dataset.tab = match[1]; return el; });
  const tablist = new Element('div', document);
  Object.assign(document, { getElementById: get, createElement: tag => new Element(tag, document), querySelector: selector => selector === '.tabs' ? tablist : null, querySelectorAll: selector => selector === '[data-tab]' ? tabs : [] });
  const context = vm.createContext({ document, crypto: webcrypto, TextEncoder, AbortSignal, Blob, URL, console, Date, Number, JSON, Error,
    sessionStorage: { setItem: (k, v) => storage.set(k, v), getItem: k => storage.get(k) || null, removeItem: k => storage.delete(k) },
    setTimeout: fn => { timers.set(++n, fn); return n; }, clearTimeout: id => timers.delete(id), setInterval: () => -1, clearInterval() {},
    fetch: async (path, options) => { requests.push({ path, options }); return { ok: true, status: 200, json: async () => path === '/api/config' ? { ready, code_sha: 'b'.repeat(40) } : path === '/api/runs' ? { handle: 'sealed-handle', request_id: requestId } : response }; } });
  for (const name of ['semantic-axes.js', 'epistemic-contract.js', 'epistemic-measurement.js', 'app.js']) vm.runInContext(file(name), context);
  await flush();
  return { get, document, context, tablist, requests, setResponse: v => { response = v; }, async submit() { get('run-epistemic-measurement').click(); await flush(); }, async poll() { const next = timers.entries().next().value; assert(next); timers.delete(next[0]); await next[1](); await flush(); }, activate(el, key) { el.focus(); el.fire('keydown', { key }); el.click(); el.fire('keyup', { key }); } };
}
test('live fixed request displays two independent populations and no invented zero rate', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report() }); await ui.submit();
  const posted = ui.requests.find(r => r.options?.method === 'POST'); assert.deepEqual(JSON.parse(posted.options.body), { schema: 'nabt.proof-lab-request.v1', mode: 'epistemic_measurement' }); await ui.poll();
  assert.equal(ui.get('epistemic-output').hidden, false); assert.equal(ui.get('epistemic-group-metrics').children.length, 2);
  assert.match(contents(ui.get('epistemic-group-metrics')), /AUTHORED_SCENARIO/); assert.match(contents(ui.get('epistemic-group-metrics')), /USGS_AGENCY_RECORD/);
  assert.match(contents(ui.get('epistemic-group-metrics').children[1]), /غير مقاس/);
  assert.match(contents(ui.get('epistemic-case-detail')), /شهادة Lean لهذه الدعوى ومدخلها فقط/);
  assert.equal(ui.get('semantic-output').hidden, true);
});
test('case selection preserves Enter/Space focus and displays source revision, pointer and limitations', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report() }); await ui.submit(); await ui.poll();
  const list = ui.get('epistemic-cases'), agency = list.children[5];
  for (const key of ['Enter', ' ']) { ui.activate(agency, key); assert.equal(ui.document.activeElement, agency); assert.equal(list.children[5], agency); assert.equal(agency.attrs['aria-pressed'], 'true'); }
  for (const pattern of [/مطابقة دعوى لسجل رصد مستقل/, /usgs_tohoku_raw.json/, /properties\/mag/, /المراجعة/, /معايرة المستشعرات لم تتحقق/, /بصمة المدخل المفحوص/]) assert.match(contents(ui.get('epistemic-case-detail')), pattern);
});
test('epistemic tab keeps RTL keyboard focus while old tab order remains usable', async () => {
  const ui = await harness(), tab = ui.get('tab-epistemic_measurement'); tab.focus(); tab.click();
  assert.equal(ui.document.activeElement, tab); assert.equal(ui.get('panel-epistemic_measurement').hidden, false);
  ui.tablist.fire('keydown', { key: 'ArrowRight' }); assert.equal(ui.document.activeElement, ui.get('tab-guide'));
  ui.tablist.fire('keydown', { key: 'End' }); assert.equal(ui.document.activeElement, ui.get('tab-licensed_workflow'));
});
test('unavailable native execution preserves counts with no accepted certificate label', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report(unavailable()) }); await ui.submit(); await ui.poll();
  assert.equal(ui.get('epistemic-output').hidden, false); assert.match(contents(ui.get('epistemic-case-detail')), /لا شهادة Lean مقبولة/);
  assert.match(contents(ui.get('epistemic-group-metrics')), /غير مقاس/);
  assert(!contents(ui.get('epistemic-case-detail')).includes('شهادة Lean لهذه الدعوى ومدخلها فقط'));
});
test('new run, failure receipt and contradictory success all leave no stale certificate', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report() }); await ui.submit(); await ui.poll();
  await ui.submit(); assert.equal(ui.get('epistemic-output').hidden, true); assert.equal(ui.get('epistemic-case-detail').children.length, 0);
  const failure = report(); delete failure.epistemic_measurement; failure.error = 'NATIVE_UNAVAILABLE'; failure.status = 'VERIFICATION_UNAVAILABLE';
  ui.setResponse({ status: 'completed', report: failure }); await ui.poll(); assert.match(ui.get('epistemic-empty-title').textContent, /NATIVE_UNAVAILABLE/);
  await ui.submit(); const changed = report(); changed.epistemic_measurement.cases[0].execution.native_result.certificate_checked = false;
  ui.setResponse({ status: 'completed', report: changed }); await ui.poll(); assert.equal(ui.get('epistemic-output').hidden, true);
});
test('proof labels require explicitly live path and both true checked declarations', async () => {
  const ui = await harness(); const row = report().epistemic_measurement.cases[0], label = ui.context.NabtEpistemicMeasurement.verificationLabel;
  assert.match(label(row), /تصريح مستورد/); assert.match(label({ ...row, certificate_checked: false }, true), /لا شهادة/);
});
test('disabled transport cannot dispatch the new suite', async () => { const ui = await harness({ ready: false }); assert.equal(ui.get('run-epistemic-measurement').disabled, true); await ui.submit(); assert.equal(ui.requests.filter(r => r.options?.method === 'POST').length, 0); });
