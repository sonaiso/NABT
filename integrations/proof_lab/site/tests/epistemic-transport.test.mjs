import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';
import { validatePayload, validateReport, validateEpistemicMeasurement, signHandle, verifyHandle, route } from '../worker/server.mjs';
import { suite, unavailable, report, reseal, hash } from './helpers/epistemic-fixture.mjs';
const contract = globalThis.NabtEpistemicContract;
const expected = report();
function importedContext() { const ctx = vm.createContext({ TextEncoder, crypto: webcrypto }); for (const file of ['epistemic-contract.js', 'evidence-audit.js']) vm.runInContext(readFileSync(new URL('../web/' + file, import.meta.url), 'utf8'), ctx); return ctx; }
test('epistemic fixed request and signed handle cannot carry code, paths, gold or authority', async () => {
  const req = { schema: 'nabt.proof-lab-request.v1', mode: 'epistemic_measurement' };
  assert.deepEqual(validatePayload(req), req);
  for (const key of ['url', 'path', 'source_text', 'query', 'budget', 'gold', 'native_checked', 'lexical_profile']) assert.throws(() => validatePayload({ ...req, [key]: 'caller' }));
  const binding = { request_id: expected.request_id, payload_sha256: hash, code_sha: expected.code_sha, mode: req.mode, created: Date.now() };
  assert.deepEqual(await verifyHandle(await signHandle(binding, 'secret'), 'secret'), binding);
});
test('shared contract validates both native receipts and nonvacuous measured populations', async () => {
  assert.equal(validateReport(report(), expected).epistemic_measurement.cases.length, 6);
  await contract.verifyIntegrity(suite());
  await contract.verifyIntegrity(unavailable());
  assert.equal(validateEpistemicMeasurement(unavailable()).groups.agency_record.metrics.refutation.measured, 0);
});
test('rejects lossy counts, noncanonical signed times, duplicate cases and false zero-denominator claims', () => {
  for (const n of [true, '1', 1.5, -1, NaN, Infinity, 9007199254740992]) { const s = suite(); s.groups.agency_record.case_count = n; assert.throws(() => contract.validate(s)); }
  for (const time of [0, true, '-0', '+1', '01', '1.0', ' 1', '9007199254740992', '-9007199254740992']) { const s = suite(); s.cases[0].query.key.time = time; assert.throws(() => contract.validate(s)); }
  for (const mutate of [s => s.cases[1].id = s.cases[0].id, s => s.groups.agency_record.metrics.conflict.passed = 1, s => s.cases.pop(), s => s.all_cases_native_checked = false]) { const s = suite(); mutate(s); assert.throws(() => contract.validate(s)); }
});
test('rejects query changes, incomplete lists, source promotion and contradictory verification declarations', () => {
  for (const mutate of [
    r => r.native_checked = false, r => r.certificate_checked = false, r => r.observed = null,
    r => r.execution.native_result.certificate_checked = false, r => r.execution.native_result.world_truth_established = true,
    r => r.execution.input.query = { ...r.query, positive: false }, r => r.execution.input.interpretations[0].key = { ...r.query.key, entity: 'someone-else' },
    r => r.execution.input.interpretations[0].kind = 'grammar', r => r.execution.input.active_sources = [],
    r => r.execution.input.origins[1].parents = ['query'], r => r.execution.input.interpretations[0].ancestry = ['record', 'query'],
    r => r.evidence_class = 'AGENCY_RECORD', r => r.execution.source_profile = 'usgs_snapshot_v1',
    r => r.execution.native_sha256 = 'c'.repeat(64), r => r.execution.error = 'FAILED',
    r => r.observed.selected_ids = [], r => r.expected.status = 'UNKNOWN',
  ]) { const s = suite(); mutate(s.cases[0]); assert.throws(() => contract.validate(s)); }
});
test('cryptographic consistency binds every case, full input and source content; hashes grant no authority', async () => {
  const scope = suite(); scope.cases[0].proof_scope = 'changed after sealing';
  await assert.rejects(() => contract.verifyIntegrity(scope));
  const input = suite(); input.cases[0].execution.input_sha256 = 'b'.repeat(64);
  const unsigned = { ...input.cases[0] }; delete unsigned.receipt_sha256;
  const { digest } = await import('./helpers/epistemic-fixture.mjs'); input.cases[0].receipt_sha256 = digest(unsigned);
  await assert.rejects(() => contract.verifyIntegrity(input));
  for (const mutate of [r => r.source_bindings[0].content_sha256 = 'b'.repeat(64), r => r.source_bindings = []]) {
    const s = suite(); mutate(s.cases[0]); reseal(s.cases[0]); await assert.rejects(() => contract.verifyIntegrity(s));
  }
});
test('unmeasured receipts retain actual eligible counts without native truth by omission', () => {
  const value = unavailable(); assert.equal(contract.validate(value), value);
  for (const mutate of [r => r.execution.error = null, r => r.observed = r.expected, r => r.comparison = 'PASS', r => r.native_checked = true]) { const s = unavailable(); mutate(s.cases[0]); assert.throws(() => contract.validate(s)); }
});
test('failure envelopes need no benchmark and cannot carry stale measurement payloads', () => {
  const r = report(); delete r.epistemic_measurement; r.status = 'EXECUTION_FAILED'; r.error = 'NATIVE_UNAVAILABLE'; assert.equal(validateReport(r, expected), r);
  for (const key of ['epistemic_measurement', 'semantic_axes', 'result', 'testimony', 'benchmark']) assert.throws(() => validateReport({ ...r, [key]: {} }, expected));
});
test('imports never authenticate even intact declared native receipts and keep both populations separate', async () => {
  const ctx = importedContext(), audit = await ctx.NabtEvidenceAudit.audit(JSON.stringify(report()));
  assert.equal(audit.authority.lean_replayed, false); assert.equal(audit.epistemic_measurement.groups.agency_record.case_count, 1);
  assert(audit.claims.every(c => c.rank === 'تصريح مستورد' && c.replayed === false));
  const bad = report(); bad.epistemic_measurement.cases[0].execution.native_result.certificate_checked = false;
  await assert.rejects(() => ctx.NabtEvidenceAudit.audit(JSON.stringify(bad)));
  const failure = report(); delete failure.epistemic_measurement; failure.status = 'VERIFICATION_UNAVAILABLE'; failure.error = 'UNAVAILABLE';
  assert.equal((await ctx.NabtEvidenceAudit.audit(JSON.stringify(failure))).operational_failure.measurements_available, false);
});
test('top wrapper cannot switch code identity, native identity, runtime or reference', () => {
  for (const key of ['native_sha256', 'runtime_sha256', 'reference_sha256', 'code_sha']) { const r = report(); r[key] = 'c'.repeat(key === 'code_sha' ? 40 : 64); assert.throws(() => validateReport(r, expected)); }
  const r = report(); r.mode = 'benchmark'; assert.throws(() => validateReport(r, { ...expected, mode: 'benchmark' }));
});
test('epistemic branch config is enabled without exposing transport credentials', async () => {
  const r = await route(new Request('https://example.test/api/config'), { NABT_EXECUTION_ENABLED: 'true', NABT_TRANSPORT_KEY: hash, NABT_GITHUB_TOKEN: 'test-secret', NABT_SIGNING_KEY: 's'.repeat(32), NABT_CODE_SHA: expected.code_sha, NABT_REF: 'codex/epistemic-measurement' }, {});
  const data = await r.json(); assert.equal(data.ready, true); assert.equal(data.branch, 'codex/epistemic-measurement'); assert(!JSON.stringify(data).includes('test-secret'));
});
test('native input bounds and active-source identities match Lean, without numeric coercion', () => {
  for (const mutate of [r => r.execution.input.budget = 129, r => r.execution.input.active_sources.push(structuredClone(r.execution.input.active_sources[0])), r => r.query.key.time = '-9007199254740992']) { const s = suite(); mutate(s.cases[0]); assert.throws(() => contract.validate(s)); }
  for (const field of ['verified', 'native_checked', 'all_arabic_complete']) { const s = suite(); s[field] = false; assert.throws(() => contract.validate(s)); }
  const r = report(); r.native_checked = false; assert.throws(() => validateReport(r, expected)); assert.throws(() => contract.validateEnvelope(r));
});
test('agency source path, field, revision and projection cannot be relabelled even with recomputed hashes', async () => {
  for (const field of ['identity', 'revision', 'raw_sha256', 'raw_path', 'field_pointer']) {
    const s = suite(); s.cases[5].source_bindings[0][field] = field.includes('sha256') ? 'd'.repeat(64) : 'other'; reseal(s.cases[5]);
    assert.throws(() => contract.validate(s));
  }
  const s = suite(), row = s.cases[5], input = row.execution.input;
  const wrong = JSON.stringify({ pointer: '/properties/mag', revision: '1792147089160', source_sha256: 'd9cf0301f748786d5ff881edba71e1b19c5b5008b3abeb893e8e88240433ba4a', value: '9.0' });
  input.active_sources[0].content = wrong; input.interpretations[0].source.content = wrong;
  const { digest } = await import('./helpers/epistemic-fixture.mjs'); row.source_bindings[0].content_sha256 = digest(wrong, true); reseal(row);
  await assert.rejects(() => contract.verifyIntegrity(s));
  const alteredMeaning = suite(); alteredMeaning.cases[5].execution.input.interpretations[0].key = { ...alteredMeaning.cases[5].query.key, value: '9.0' };
  assert.throws(() => contract.validate(alteredMeaning));
});
