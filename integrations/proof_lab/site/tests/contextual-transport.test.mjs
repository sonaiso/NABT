import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';
import { validatePayload, validateReport, validateContextualReference, signHandle, verifyHandle, route } from '../worker/server.mjs';
import { suite, report, unavailable, reseal, recount, hash, digest } from './helpers/contextual-fixture.mjs';
const contract = globalThis.NabtContextualContract, expected = report();
function auditContext() { const context = vm.createContext({ TextEncoder, TextDecoder, crypto: webcrypto }); for (const name of ['contextual-contract.js', 'evidence-audit.js']) vm.runInContext(readFileSync(new URL('../web/' + name, import.meta.url), 'utf8'), context); return context; }
test('contextual requests are fixed and signed independently of every other mode', async () => {
  const req = { schema: 'nabt.proof-lab-request.v1', mode: 'contextual_reference' }; assert.deepEqual(validatePayload(req), req);
  for (const key of ['text', 'context', 'gold', 'code', 'url', 'path', 'lexical_profile', 'verified']) assert.throws(() => validatePayload({ ...req, [key]: 'caller' }));
  const h = { request_id: expected.request_id, code_sha: expected.code_sha, payload_sha256: hash, mode: req.mode, created: Date.now() }; assert.deepEqual(await verifyHandle(await signHandle(h, 'key'), 'key'), h);
});
test('full45case counts, complete native candidates and canonical identities reconcile', async () => {
  assert.equal(validateReport(report(), expected).contextual_reference.cases.length, 45);
  await contract.verifyIntegrity(suite()); await contract.verifyIntegrity(unavailable());
  assert.equal(validateContextualReference(suite()).groups.original_25.reference_after.passed, 5);
  assert.equal(suite().groups.independent_20.reference_after.failed, 2);
});
test('rejects lossy counts/spans, duplicate cases, denominator laundering and false tawatur', () => {
  for (const n of [true, '25', 25.5, -1, NaN, Infinity, 9007199254740992]) { const s = suite(); s.groups.original_25.case_count = n; assert.throws(() => contract.validate(s)); }
  for (const mutate of [s => s.cases[1].id = s.cases[0].id, s => s.cases.pop(), s => s.tawatur_evaluated = true, s => s.native_checked = false, s => s.groups.independent_20.metric_categories.safe_nonresolution.passed++, s => s.cases[0].execution.execution.input.occurrence.start_byte = true]) { const s = suite(); mutate(s); assert.throws(() => contract.validate(s)); }
});
test('native success cannot substitute for a failed independent reference comparison', () => {
  const s = suite(); assert.equal(s.cases[25].execution.native_checked, true); assert.equal(s.cases[25].reference_comparison.status, 'FAIL');
  s.cases[25].reference_comparison.status = 'PASS'; recount(s); assert.throws(() => contract.validate(s));
  const quote = suite(); assert.equal(quote.cases[26].execution.status, 'OUT_OF_SCOPE'); assert.equal(quote.cases[26].expected_reference.status, 'unresolved');
  quote.cases[26].reference_comparison.status = 'PASS'; recount(quote); assert.throws(() => contract.validate(quote));
});
test('cross-context, cross-occurrence and partial candidate receipts fail closed', () => {
  for (const mutate of [
    o => o.native_checked = false, o => o.certificate_checked = false, o => o.execution.native_result.certificate_checked = false,
    o => o.execution.input.context.speaker = 'person_b', o => o.execution.input.source.text = 'بديل',
    o => o.execution.input.occurrence.end_byte--, o => o.execution.proposal.reading_ids = [],
    o => o.execution.input.alternatives.push({ ...o.execution.input.alternatives[0], id: 'extra' }),
    o => o.execution.native_result.reading_results = [], o => o.reference.candidate_entity_ids = [],
    o => o.scope.sentence_readings_promoted = true, o => o.scope.tawatur_status = 'PROVEN',
    o => o.execution.native_result.whole_clause_checked = true, o => o.execution.input.budget = 257,
    o => o.execution.native_result.motive_established = true,
  ]) { const s = suite(); mutate(s.cases[20].execution); assert.throws(() => contract.validate(s)); }
});
test('an intact receipt may preserve ambiguity and safe nonresolution without positive acquisition credit', () => {
  const s = suite(); assert.equal(contract.validate(s), s);
  assert.equal(s.cases[27].execution.reference.bound_entity_id, null); assert.deepEqual(s.cases[27].execution.reference.candidate_entity_ids, ['person_a', 'person_b']);
  assert.equal(s.cases[28].metric_category, 'safe_nonresolution');
  s.cases[28].metric_category = 'positive_binding'; recount(s); assert.throws(() => contract.validate(s));
});
test('unknown required features retain a singleton without resolving or earning positive acquisition credit', async () => {
  const s = suite(), row = s.cases[20], o = row.execution, e = o.execution;
  row.input.context.entities[0].number = 'unknown';
  assert.throws(() => contract.validate(s));
  for (const result of [e.proposal, e.native_result]) {
    result.status = 'UNRESOLVED_FEATURES'; result.bound_entity_id = null;
    result.reading_results[0].status = 'UNRESOLVED_FEATURES'; result.reading_results[0].bound_entity_id = null;
  }
  e.native_result.observed_status = 'UNRESOLVED_FEATURES';
  o.status = 'UNRESOLVED_FEATURES'; o.reference = null;
  Object.assign(row.reference_comparison, { status: 'FAIL', reason: 'TARGET_OCCURRENCE_OUTSIDE_EXECUTED_REFERENCE_SCOPE' });
  reseal(row); recount(s); await contract.verifyIntegrity(s);
  assert.deepEqual(e.native_result.candidate_entity_ids, ['person_a']);
  assert.equal(s.groups.original_25.reference_after.passed, 4);
});
test('common gender is unconstrained while an unknown required demonstrative gender cannot resolve', () => {
  const common = suite(); common.cases[20].input.context.entities[0].gender = 'unknown';
  assert.equal(contract.validate(common), common);
  const required = suite(), o = required.cases[20].execution, e = o.execution;
  o.input.context.entities[0].gender = 'unknown';
  e.input.alternatives[0].pos = 'DEM'; e.input.alternatives[0].profile_code = '3MS';
  e.input.donors[0].record = e.input.donors[0].record.replace('PRON\tPOS:PRON|1S', 'DEM\tPOS:DEM|MS');
  e.input.context.deixis.push({ form: 'أنا', entity_ids: ['person_a'] });
  e.input.donors[0].end_byte = e.input.donors[0].start_byte + Buffer.byteLength(e.input.donors[0].record);
  o.source_bindings[0].byte_end = e.input.donors[0].end_byte;
  assert.throws(() => contract.validate(required));
});
test('source FORM decoding, mark preservation and source location are bound independently of declared POS', () => {
  for (const mutate of [
    o => o.execution.input.alternatives[0].source_form = 'أنت',
    o => o.execution.input.donors[0].record = o.execution.input.donors[0].record.replace('>anaA', '>aniA'),
    o => o.source_bindings[0].locator[0] = 2,
    o => o.source_bindings[0].locator = [true, 1, 1, 1],
    o => o.source_bindings[0].locator = { claim: 'verified' },
  ]) { const s = suite(); mutate(s.cases[20].execution); assert.throws(() => contract.validate(s)); }
  for (const surface of ['أَنّا', 'أِنَا', 'أَنٰا', 'أناََّ']) {
    const s = suite(), row = s.cases[20], o = row.execution, e = o.execution;
    row.input.text = surface + ' عالم.'; e.input.source.text = row.input.text; e.input.source.revision = digest(row.input.text, true);
    e.input.occurrence.surface = surface; e.input.occurrence.end_byte = Buffer.byteLength(surface);
    e.input.alternatives[0].target_surface = surface; o.reference.surface = surface; o.reference.span.end = Array.from(surface).length;
    assert.throws(() => contract.validate(s));
  }
});
test('source, context, occurrence and receipt hashes are independently recomputed', async () => {
  for (const mutate of [o => o.receipt_sha256 = 'b'.repeat(64), o => o.context_sha256 = 'b'.repeat(64), o => o.execution.input_sha256 = 'b'.repeat(64), o => o.reference.reference_id = 'b'.repeat(64), o => o.source_bindings[0].content_sha256 = 'b'.repeat(64)]) { const s = suite(); mutate(s.cases[20].execution); await assert.rejects(() => contract.verifyIntegrity(s)); }
  const s = suite(), row = s.cases[20]; row.execution.execution.input.source.revision = 'b'.repeat(64); reseal(row); await assert.rejects(() => contract.verifyIntegrity(s));
});
test('source records cannot be swapped or clipped while keeping declared success', () => {
  for (const mutate of [o => o.source_bindings = [], o => o.source_bindings[0].source_sha256 = 'b'.repeat(64), o => o.source_bindings[0].byte_start++, o => o.execution.input.donors[0].record = 'OTHER', o => o.execution.input.alternatives[0].donor_ids = [], o => o.execution.input.alternatives[0].profile_code = '3MS']) { const s = suite(); mutate(s.cases[20].execution); assert.throws(() => contract.validate(s)); }
});
test('failure receipts need no suite and never become zero successful measurements', async () => {
  const r = report(); delete r.contextual_reference; r.status = 'VERIFICATION_UNAVAILABLE'; r.error = 'NATIVE_UNAVAILABLE'; assert.equal(validateReport(r, expected), r);
  for (const field of ['contextual_reference', 'semantic_axes', 'epistemic_measurement', 'benchmark', 'result']) assert.throws(() => validateReport({ ...r, [field]: {} }, expected));
  const imported = await auditContext().NabtEvidenceAudit.audit(JSON.stringify(r)); assert.equal(imported.operational_failure.measurements_available, false);
});
test('imports remain unverified assertions even when all45 claimed native certificates are internally consistent', async () => {
  const context = auditContext(), imported = await context.NabtEvidenceAudit.audit(JSON.stringify(report()));
  assert.equal(imported.authority.lean_replayed, false); assert.equal(imported.contextual_reference.cases.length, 45);
  assert(imported.claims.every(c => c.rank === 'تصريح مستورد' && c.replayed === false));
  const r = report(); r.contextual_reference.cases[20].execution.certificate_checked = false;
  await assert.rejects(() => context.NabtEvidenceAudit.audit(JSON.stringify(r)));
});
test('top report identities bind both references and the preserved baseline separately', () => {
  for (const key of ['original_reference_sha256', 'independent_reference_sha256', 'baseline_source_sha256', 'scorer_sha256', 'runtime_sha256', 'native_sha256', 'source_registry_sha256']) { const r = report(); r[key] = 'b'.repeat(64); assert.throws(() => validateReport(r, expected)); }
  const r = report(); r.native_checked = true; assert.throws(() => validateReport(r, expected));
});
test('new branch is available without exposing execution secrets', async () => {
  const response = await route(new Request('https://example.test/api/config'), { NABT_EXECUTION_ENABLED: 'true', NABT_TRANSPORT_KEY: hash, NABT_GITHUB_TOKEN: 'not-exposed', NABT_SIGNING_KEY: 's'.repeat(32), NABT_CODE_SHA: expected.code_sha, NABT_REF: 'codex/contextual-semantic-licenses' }, {});
  const config = await response.json(); assert.equal(config.ready, true); assert.equal(config.branch, 'codex/contextual-semantic-licenses'); assert(!JSON.stringify(config).includes('not-exposed'));
});
