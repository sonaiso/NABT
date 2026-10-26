import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';
import { report, unavailable, requestId } from './helpers/contextual-fixture.mjs';
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
  const context = vm.createContext({ document, crypto: webcrypto, TextEncoder, TextDecoder, AbortSignal, Blob, URL, console, Date, Number, JSON, Error,
    sessionStorage: { setItem: (k, v) => storage.set(k, v), getItem: k => storage.get(k) || null, removeItem: k => storage.delete(k) },
    setTimeout: fn => { timers.set(++n, fn); return n; }, clearTimeout: id => timers.delete(id), setInterval: () => -1, clearInterval() {},
    fetch: async (path, options) => { requests.push({ path, options }); return { ok: true, status: 200, json: async () => path === '/api/config' ? { ready, code_sha: 'b'.repeat(40) } : path === '/api/runs' ? { handle: 'sealed-handle', request_id: requestId } : response }; } });
  for (const name of ['semantic-axes.js', 'epistemic-contract.js', 'epistemic-measurement.js', 'contextual-contract.js', 'contextual-reference.js', 'app.js']) vm.runInContext(file(name), context);
  await flush();
  return { get, document, context, tablist, requests, setResponse: v => { response = v; }, async submit() { get('run-contextual-reference').click(); await flush(); }, async poll() { const next = timers.entries().next().value; assert(next); timers.delete(next[0]); await next[1](); await flush(); }, activate(el, key) { el.focus(); el.fire('keydown', { key }); el.click(); el.fire('keyup', { key }); } };
}
test('fixed live dispatch preserves separate25/20 comparisons and conditional occurrence receipts', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report() }); await ui.submit();
  assert.deepEqual(JSON.parse(ui.requests.find(r => r.options?.method === 'POST').options.body), { schema: 'nabt.proof-lab-request.v1', mode: 'contextual_reference' }); await ui.poll();
  assert.equal(ui.get('contextual-output').hidden, false); assert.equal(ui.get('contextual-group-metrics').children.length, 2);
  assert.match(contents(ui.get('contextual-group-metrics')), /Python/); assert.match(contents(ui.get('contextual-group-metrics')), /امتناع آمن فقط/);
  assert.equal(ui.get('semantic-output').hidden, true); assert.equal(ui.get('epistemic-output').hidden, true);
});
test('per-case selection keeps Enter/Space focus and separates native certificate from gold failure', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report() }); await ui.submit(); await ui.poll();
  const list = ui.get('contextual-cases'), button = list.children[25];
  for (const key of ['Enter', ' ']) { ui.activate(button, key); assert.equal(ui.document.activeElement, button); assert.equal(list.children[25], button); assert.equal(button.attrs['aria-pressed'], 'true'); }
  const content = contents(ui.get('contextual-case-detail'));
  for (const pattern of [/مخالفة المرجع في Python/, /شهادة Lean مشروطة لهذا الورود/, /UTF-8/, /QAC/, /التواتر غير مقيّم/, /تفسير وسومها مقدمات برمجية مستقلة/]) assert.match(content, pattern);
});
test('quote scope refusal is visible as a failed target comparison rather than successful unresolved understanding', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report() }); await ui.submit(); await ui.poll(); ui.get('contextual-cases').children[26].click();
  assert.match(contents(ui.get('contextual-case-detail')), /شهادة Lean بحدود النطاق/); assert.match(contents(ui.get('contextual-case-detail')), /مخالفة المرجع/);
});
test('new tab keeps RTL navigation and focused button through case updates', async () => {
  const ui = await harness(), tab = ui.get('tab-contextual_reference'); tab.focus(); tab.click();
  assert.equal(ui.get('panel-contextual_reference').hidden, false); assert.equal(ui.document.activeElement, tab);
  ui.tablist.fire('keydown', { key: 'ArrowRight' }); assert.equal(ui.document.activeElement, ui.get('tab-epistemic_measurement'));
  ui.tablist.fire('keydown', { key: 'End' }); assert.equal(ui.document.activeElement, tab);
});
test('unavailable native receipts remain unmeasured and never show a conditional proof label', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report(unavailable()) }); await ui.submit(); await ui.poll();
  assert.equal(ui.get('contextual-output').hidden, false); assert.match(contents(ui.get('contextual-case-detail')), /لا شهادة Lean مقبولة/);
  assert.match(contents(ui.get('contextual-group-metrics')), /غير مقاس/);
});
test('failure or tampered next receipt clears stale evidence before async integrity checks', async () => {
  const ui = await harness(); ui.setResponse({ status: 'completed', report: report() }); await ui.submit(); await ui.poll();
  await ui.submit(); assert.equal(ui.get('contextual-output').hidden, true); assert.equal(ui.get('contextual-case-detail').children.length, 0);
  const failed = report(); delete failed.contextual_reference; failed.status = 'VERIFICATION_UNAVAILABLE'; failed.error = 'NATIVE_UNAVAILABLE'; ui.setResponse({ status: 'completed', report: failed }); await ui.poll(); assert.match(ui.get('contextual-empty-title').textContent, /NATIVE_UNAVAILABLE/);
  await ui.submit(); const tampered = report(); tampered.contextual_reference.cases[20].execution.receipt_sha256 = 'e'.repeat(64); ui.setResponse({ status: 'completed', report: tampered }); await ui.poll(); assert.equal(ui.get('contextual-output').hidden, true);
});
test('import-only label never inherits live authority and disabled connection cannot dispatch', async () => {
  const ui = await harness({ ready: false }); assert.equal(ui.get('run-contextual-reference').disabled, true); await ui.submit(); assert.equal(ui.requests.filter(r => r.options?.method === 'POST').length, 0);
  assert.match(ui.context.NabtContextualReference.verificationLabel(report().contextual_reference.cases[20].execution), /تصريح مستورد/);
  await ui.context.NabtContextualReference.render(report());
  assert.match(contents(ui.get('contextual-case-detail')), /تصريح مستورد؛ لم يُعد تشغيل Lean/);
  assert.doesNotMatch(contents(ui.get('contextual-case-detail')), /شهادة Lean مشروطة لهذا الورود/);
});
