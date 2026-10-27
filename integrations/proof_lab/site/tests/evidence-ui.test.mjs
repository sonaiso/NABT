import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// Browser-local interaction regression harness. Does not render pixels or run
// Lean. Network/storage and HTML injection sinks fail loudly if reached.
const files = name => readFileSync(new URL('../web/' + name, import.meta.url), 'utf8');
const html = files('index.html');
const programs = ['evidence-audit.js', 'evidence-sample.js', 'evidence-ui.js'].map(files);
class Element {
  constructor(tag = 'div', ownerDocument = null) { this.tag = tag; this.children = []; this.listeners = {};
    this.textContent = ''; this.value = ''; this.hidden = false; this.attrs = {}; this.files = [];
    this.ownerDocument = ownerDocument; this.parentElement = null; this.isConnected = false; }
  set innerHTML(_) { throw new Error('Unsafe innerHTML sink reached'); }
  addEventListener(name, handler) { (this.listeners[name] ??= []).push(handler); }
  fire(name, extras = {}) { return Promise.all((this.listeners[name] || []).map(handler => handler({ preventDefault() {}, target: this, ...extras }))); }
  attach(parent) { this.parentElement = parent; this.isConnected = parent.isConnected;
    for (const child of this.children) child.attach(this); }
  disconnect() {
    if (this.ownerDocument?.activeElement === this) this.ownerDocument.activeElement = this.ownerDocument.body;
    this.isConnected = false; this.parentElement = null;
    for (const child of this.children) child.disconnect();
  }
  append(...children) { for (const child of children) { this.children.push(child); child.attach(this); } }
  replaceChildren(...children) { for (const child of this.children) child.disconnect(); this.children = []; this.append(...children); }
  setAttribute(key, value) { this.attrs[key] = value; }
  getAttribute(key) { return this.attrs[key] ?? null; }
  contains(node) { return this === node || this.children.some(child => child.contains(node)); }
  focus() { if (this.isConnected && this.ownerDocument) this.ownerDocument.activeElement = this; this.focused = true; }
  click() { this.clicked = true; return this.fire('click'); }
  remove() { if (this.parentElement) this.parentElement.children = this.parentElement.children.filter(child => child !== this); this.disconnect(); this.removed = true; }
}

const content = node => node.textContent + node.children.map(content).join(' ');
// WebCrypto resolves on the real worker pool. A deadline with a short timer
// yields to that pool under concurrent tests; a count of immediate callbacks
// can expire before any worker has CPU time. Assertions remain unchanged.
const tick = () => new Promise(resolve => setTimeout(resolve, 3));
async function flushUntil(test, description) {
  const deadline = Date.now() + 2000;
  while (Date.now() < deadline) { if (test()) return; await tick(); }
  if (test()) return;
  assert.fail('UI did not settle within 2 seconds: ' + description);
}
async function harness({ cryptoAvailable = true } = {}) {
  const nodes = new Map();
  const document = { activeElement: null };
  const body = new Element('body', document); body.isConnected = true; document.body = body; document.activeElement = body;
  for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) {
    assert(!nodes.has(match[3]), 'Duplicate id ' + match[3]);
    const node = new Element(match[1], document); node.isConnected = true; node.hidden = /\bhidden\b/.test(match[2]); nodes.set(match[3], node);
  }
  const get = id => { assert(nodes.has(id), 'Unknown DOM id ' + id); return nodes.get(id); };
  const blobs = [], calls = [];
  const failRemote = kind => () => { calls.push(kind); throw new Error('Unexpected ' + kind); };
  Object.assign(document, { getElementById: get, createElement: tag => new Element(tag, document), body });
  const storage = { setItem: failRemote('storage write'), getItem: failRemote('storage read') };
  const context = vm.createContext({ document, TextEncoder, TextDecoder, crypto: cryptoAvailable ? webcrypto : undefined,
    Blob, URL: { createObjectURL: blob => { blobs.push(blob); return 'blob:local-' + blobs.length; }, revokeObjectURL() {} },
    fetch: failRemote('network'), localStorage: storage, sessionStorage: storage, setTimeout() {} });
  programs.forEach((program, i) => vm.runInContext(program, context, { filename: ['evidence-audit.js','evidence-sample.js','evidence-ui.js'][i] }));
  await flushUntil(() => get('evidence-loading').hidden, 'initial sample');
  return { get, context, document, body, blobs, calls,
    async activate(node, key) { node.focus(); await node.fire('keydown', { key }); await node.fire('click', { detail: 0 }); await node.fire('keyup', { key }); },
    sample: () => JSON.parse(JSON.stringify(context.NabtEvidenceSample)),
    async paste(record) { get('evidence-input').value = typeof record === 'string' ? record : JSON.stringify(record); await get('audit-evidence').fire('click'); },
  };
}

test('initial sample renders 14 claims and declared9/9 without contacting a server or storage', async () => {
  const ui = await harness();
  assert.equal(ui.get('evidence-output').hidden, false);
  assert.equal(ui.get('evidence-sentence').textContent, 'ذَهَبَ الْوَلَدُ');
  assert.equal(ui.get('evidence-sha').textContent, '34c9ac0fff60bc73c9ed17b600b1c133d2f0c83d5b47427e921bb533853450e2');
  assert.equal(ui.get('evidence-claims').children.length, 14);
  assert.match(content(ui.get('evidence-metrics')), /٩ \/ ٩/);
  assert.match(content(ui.get('evidence-metrics')), /٠.*إعادات|إعادات.*٠/s);
  assert.match(ui.get('evidence-origin').textContent, /منقول/);
  assert.match(ui.get('evidence-summary').textContent, /الاتساق والبصمات فقط/);
  assert.equal(ui.calls.length, 0);
});

test('layer, rank and text filters select the matching claim and update its evidence detail', async () => {
  const ui = await harness();
  await ui.get('evidence-layers').children[3].fire('click');
  assert.equal(ui.get('evidence-claims').children.length, 5);
  ui.get('evidence-rank').value = 'مبرهن'; await ui.get('evidence-rank').fire('change');
  assert.equal(ui.get('evidence-claims').children.length, 1);
  assert.match(content(ui.get('claim-detail')), /tabaqa4_thabat/);
  assert.match(content(ui.get('claim-detail')), /Quot.sound/);
  assert.match(content(ui.get('claim-detail')), /لم تتم في هذه الصفحة/);
  ui.get('evidence-search').value = 'NO MATCH'; await ui.get('evidence-search').fire('input');
  assert.equal(ui.get('evidence-claims').children.length, 0);
  assert.equal(ui.get('evidence-claims-empty').hidden, false);
  assert.equal(ui.get('claim-detail').children.length, 0);
});

test('clicking a specific claim updates source, rank and assumptions without changing authority', async () => {
  const ui = await harness();
  const row = ui.get('evidence-claims').children.find(node => content(node).includes('tabaqa4_zaman'));
  assert(row); await row.fire('click');
  assert.match(content(ui.get('claim-detail')), /tabaqa4_zaman/);
  assert.match(content(ui.get('claim-detail')), /المرساة افتراض معلن|إزاحة الحدث مفترضة/);
  assert.match(content(ui.get('claim-detail')), /ناجح بحسب السجل/);
  assert.match(content(ui.get('claim-detail')), /لم تتم في هذه الصفحة/);
});

test('stage matrix preserves unknown vs false vs true accessibility labels', async () => {
  const ui = await harness();
  const row = ui.get('evidence-stages').children.find(node => content(node).includes('S3_HOKOM_TAQDIR'));
  assert.equal(row.children[1].children[0].attrs['aria-label'], 'بدأ: لا');
  assert.equal(row.children[2].children[0].attrs['aria-label'], 'اكتمل: غير مقاس');
  const running = ui.get('evidence-stages').children.find(node => content(node).includes('S4_MADLUL'));
  assert.equal(running.children[1].children[0].attrs['aria-label'], 'بدأ: نعم');
});

test('hostile imported markup remains literal text in claims, findings, and detail', async () => {
  const ui = await harness(); const record = ui.sample();
  const malicious = '<img src=x onerror="globalThis.attack=true">';
  record.claims[0].tarjama = malicious; record.claims[0].burhan = malicious;
  record.stages[0].reason = malicious;
  await ui.paste(record);
  assert.equal(ui.get('evidence-output').hidden, false);
  assert(content(ui.get('evidence-claims')).includes(malicious));
  assert(content(ui.get('claim-detail')).includes(malicious));
  assert(content(ui.get('evidence-stages')).includes(malicious));
  assert.equal(ui.context.attack, undefined);
  assert.equal(ui.calls.length, 0);
});

test('invalid replacement hides stale accepted report and disables downloads through state', async () => {
  const ui = await harness(); await ui.paste('{"schema":');
  assert.equal(ui.get('evidence-output').hidden, true);
  assert.equal(ui.get('evidence-loading').hidden, true);
  assert.equal(ui.get('evidence-error').hidden, false);
  await ui.get('download-evidence-review').fire('click');
  await ui.get('download-evidence-source').fire('click');
  assert.equal(ui.blobs.length, 0);
  await ui.get('load-evidence-sample').fire('click');
  assert.equal(ui.get('evidence-output').hidden, false);
  assert.equal(ui.get('evidence-error').hidden, true);
});

test('download separates compact audit from exact source JSON', async () => {
  const ui = await harness(); const original = JSON.stringify(ui.sample(), null, 1) + '\n';
  await ui.paste(original);
  await ui.get('download-evidence-review').fire('click');
  await ui.get('download-evidence-source').fire('click');
  assert.equal(ui.blobs.length, 2);
  const review = JSON.parse(await ui.blobs[0].text());
  assert.equal(review.raw_record, undefined);
  assert.equal(Object.hasOwn(review, 'raw_json'), false, 'compact audit must not duplicate full source payload');
  assert.equal(review.authority.lean_replayed, false);
  assert.match(review.review_notice, /not replayed/);
  assert.equal(await ui.blobs[1].text(), original);
});

test('latest inspection wins when an earlier async audit completes late', async () => {
  const ui = await harness(); const originalAudit = ui.context.NabtEvidenceAudit.audit;
  let release;
  const deferred = new Promise(resolve => { release = resolve; });
  ui.context.NabtEvidenceAudit = { audit: async value => { if (value.includes('OLD_FIRST')) await deferred; return originalAudit(value); } };
  const older = ui.sample(); older.sample_note = 'OLD_FIRST';
  const newer = ui.sample(); newer.sample_note = 'NEW_LATEST';
  ui.get('evidence-input').value = JSON.stringify(older);
  const first = ui.get('audit-evidence').fire('click');
  await ui.paste(newer);
  release(); await first;
  assert.equal(ui.get('evidence-sample-note').textContent, 'NEW_LATEST');
  assert.equal(ui.get('evidence-output').hidden, false);
});

test('invalid UTF-8 file hides stale result without starting a remote execution', async () => {
  const ui = await harness();
  ui.get('evidence-file').files = [{ size: 2, arrayBuffer: async () => Uint8Array.from([0xc3, 0x28]).buffer }];
  await ui.get('evidence-file').fire('change');
  assert.equal(ui.get('evidence-output').hidden, true);
  assert.match(ui.get('evidence-error').textContent, /UTF-8/);
  assert.equal(ui.calls.length, 0);
});

test('oversized replacement cancels loading indicator even if an earlier audit is pending', async () => {
  const ui = await harness(); const originalAudit = ui.context.NabtEvidenceAudit.audit;
  let release; const deferred = new Promise(resolve => { release = resolve; });
  ui.context.NabtEvidenceAudit = { audit: async value => { await deferred; return originalAudit(value); } };
  ui.get('evidence-input').value = JSON.stringify(ui.sample());
  const old = ui.get('audit-evidence').fire('click');
  assert.equal(ui.get('evidence-loading').hidden, false);
  ui.get('evidence-file').files = [{ size: 2097153, arrayBuffer: async () => { throw new Error('must not read oversized file'); } }];
  await ui.get('evidence-file').fire('change');
  release(); await old;
  assert.equal(ui.get('evidence-output').hidden, true);
  assert.match(ui.get('evidence-error').textContent, /٢ MiB/);
  assert.equal(ui.get('evidence-loading').hidden, true);
});

test('imported NABT inference shows declared fields and assumptions while retaining unverified origin', async () => {
  const ui = await harness();
  await ui.paste({ schema: 'nabt.proof-lab-result.v1', mode: 'inference', code_sha: 'a'.repeat(40),
    all_arabic_complete: false, world_truth_established: false,
    result: { source: { raw_text: 'سَارَ زَيْدٌ.' }, query: { raw_text: 'هَلْ سَارَ زَيْدٌ؟' },
      status: 'SUPPORTED', verified: true, native_checked: true, all_readings_complete: true, closures_checked: true,
      readings: [{}], closure_records: [{}], assumptions: ['لا يُفترض صدق الخبر في الواقع'], unclassified_spans: [] } });
  assert.equal(ui.get('evidence-output').hidden, false);
  assert.equal(ui.get('evidence-sentence').textContent, 'سَارَ زَيْدٌ.');
  assert.match(ui.get('evidence-origin').textContent, /غير معاد التشغيل/);
  assert.equal(ui.get('evidence-stages').children.length, 0);
  assert.equal(ui.get('evidence-stages-empty').hidden, false);
  assert(content(ui.get('evidence-claims')).includes('declared_native_checked'));
  const nativeRow = ui.get('evidence-claims').children.find(node => content(node).includes('declared_native_checked'));
  await nativeRow.fire('click');
  assert.match(content(ui.get('claim-detail')), /تصريح مستورد/);
  assert.match(content(ui.get('claim-detail')), /لم تتم في هذه الصفحة/);
  assert.equal(ui.get('evidence-imported-benchmark').hidden, true);
  assert.equal(ui.calls.length, 0);
});

test('imported benchmark renders all actual rows and displays count discrepancy instead of trusting summary', async () => {
  const ui = await harness();
  await ui.paste({ schema: 'nabt.proof-lab-result.v1', mode: 'benchmark', benchmark: {
    summary: { cases: 3, pass: 3, fail: 0, unmeasured: 0 }, scope: 'ثلاث حالات مستقلة للتجربة',
    rows: [{ id: 'P', outcome: 'PASS' }, { id: 'F', outcome: 'FAIL' }, { id: 'U', outcome: 'UNMEASURED' }],
  } });
  assert.equal(ui.get('evidence-output').hidden, false);
  assert.equal(ui.get('evidence-imported-benchmark').hidden, false);
  assert.equal(ui.get('evidence-imported-rows').children.length, 3);
  assert.equal(ui.get('evidence-imported-counts').textContent, '٣ حالات · ١ مطابقة · ١ إخفاق · ١ غير مقاس');
  assert.equal(ui.get('evidence-imported-scope').textContent, 'ثلاث حالات مستقلة للتجربة');
  assert.match(content(ui.get('evidence-findings')), /BENCHMARK_COUNT_MISMATCH/);
  assert.match(content(ui.get('evidence-metrics')), /١ \/ ٣/);
  assert.match(ui.get('evidence-origin').textContent, /غير معاد التشغيل/);
  assert.equal(ui.calls.length, 0);
});

test('missing WebCrypto leaves digest unavailable without inventing a successful hash comparison', async () => {
  const ui = await harness({ cryptoAvailable: false });
  assert.equal(ui.get('evidence-output').hidden, false);
  assert.equal(ui.get('evidence-sha').textContent, 'غير متاح');
  assert.match(ui.get('evidence-hash-status').textContent, /حساب SHA-256 غير متاح/);
  assert.doesNotMatch(ui.get('evidence-hash-status').textContent, /تطابق النص/);
  assert.equal(ui.calls.length, 0);
  await ui.get('download-evidence-review').fire('click');
  const result = JSON.parse(await ui.blobs[0].text());
  assert.equal(result.input.computed_sha256, null);
  assert.equal(result.checks.find(item => item.id === 'TEXT_HASH').status, 'unknown');
  assert.equal(result.authority.lean_replayed, false);
});

// A native button activation dispatches click for Enter/Space. This harness
// models focus loss on DOM removal, so keeping a detached node's `focused`
// property true cannot accidentally satisfy these regressions.
test('keyboard layer activation keeps focus on the activated layer after selecting and toggling', async () => {
  const ui = await harness();
  for (const key of ['Enter', ' ']) {
    const layer = ui.get('evidence-layers').children[2];
    await ui.activate(layer, key);
    const current = ui.get('evidence-layers').children[2];
    assert(ui.document.activeElement === current, 'focus must remain on a connected layer button');
    assert.equal(current.isConnected, true);
    assert.equal(current.attrs['aria-pressed'], key === 'Enter' ? 'true' : 'false');
  }
});

test('keyboard claim activation keeps focus on the selected claim and opens its detail', async () => {
  const ui = await harness();
  for (const [key, id] of [['Enter','tabaqa3_hukm'], [' ','tabaqa4_zaman']]) {
    const row = ui.get('evidence-claims').children.find(node => content(node).includes(id));
    assert(row); await ui.activate(row, key);
    const current = ui.get('evidence-claims').children.find(node => content(node).includes(id));
    assert(ui.document.activeElement === current, 'selection must not drop focus to body');
    assert.equal(current.isConnected, true);
    assert.equal(current.attrs['aria-pressed'], 'true');
    assert.match(content(ui.get('claim-detail')), new RegExp(id));
  }
});

test('search and rank filtering never steal focus to a newly selected claim', async () => {
  const ui = await harness();
  const search = ui.get('evidence-search'); search.focus(); search.value = 'tabaqa4';
  await search.fire('input');
  assert.equal(ui.document.activeElement, search);
  assert.equal(ui.get('evidence-claims').children.length, 5);
  const rank = ui.get('evidence-rank'); rank.focus(); rank.value = 'مبرهن'; await rank.fire('change');
  assert.equal(ui.document.activeElement, rank);
  assert.equal(ui.get('evidence-claims').children.length, 1);
});

test('benchmark failure receipt displays its failure status and reason instead of a parsing rejection', async () => {
  const ui = await harness();
  await ui.paste({ schema: 'nabt.proof-lab-result.v1', mode: 'benchmark', status: 'VERIFICATION_UNAVAILABLE',
    error: 'NATIVE_CHECKER_MISSING', native_sha256: null, all_arabic_complete: false, world_truth_established: false });
  assert.equal(ui.get('evidence-output').hidden, false);
  assert.equal(ui.get('evidence-error').hidden, true);
  assert.equal(ui.get('evidence-imported-benchmark').hidden, true);
  assert.equal(ui.get('evidence-imported-rows').children.length, 0);
  assert.match(content(ui.get('evidence-claims')), /VERIFICATION_UNAVAILABLE|حالة التنفيذ/);
  assert(content(ui.get('evidence-claims')).includes('NATIVE_CHECKER_MISSING') || content(ui.get('claim-detail')).includes('NATIVE_CHECKER_MISSING'), 'reason must be visible as a claim label or detail');
  assert.equal(ui.calls.length, 0);
});
