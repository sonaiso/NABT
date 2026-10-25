import assert from 'node:assert/strict';
import { createHash, webcrypto } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// Independent adversarial checks of the browser-local inspector. These do not
// execute Lean or validate the truth of a supplied report's theorem claims.
const program = readFileSync(new URL('../web/evidence-audit.js', import.meta.url), 'utf8');
const sandbox = vm.createContext({ TextEncoder, TextDecoder, crypto: webcrypto });
vm.runInContext(program, sandbox, { filename: 'evidence-audit.js' });
const api = sandbox.NabtEvidenceAudit;
const text = 'ذَهَبَ الْوَلَدُ';
const sha = value => createHash('sha256').update(value, 'utf8').digest('hex');
const properties = ['started', 'completed', 'found', 'produced', 'accepted', 'stored', 'consumed_by_next'];
const theoremNames = ['tabaqa1_kalimat', 'tabaqa2_maani', 'tabaqa3_hukm', 'tabaqa3_isnad',
  'tabaqa4_ajza', 'tabaqa4_kalam', 'tabaqa4_zaman', 'tabaqa4_mawdi', 'tabaqa4_thabat'];
function fixture() {
  const claim = (ism, tabaqa, rutba) => ({ ism, tabaqa, rutba, qima: true,
    tarjama: ism, burhan: 'reported assertion; no proof replay', sabab_ghiyab: null });
  return {
    schema: 'Tabaqat4Record:v1', timestamp_utc: '2026-10-24T12:07:12.532821+00:00',
    input: { nass_kama_wasal: text, nfc: text, nfc_eq_input: true, sha256: sha(text), codepoints: 16, tahwil: [] },
    tokens: [{ idx: 0, anchor: 'W-34c9ac0f-000', surface: 'ذَهَبَ' }, { idx: 1, anchor: 'W-34c9ac0f-001', surface: 'الْوَلَدُ' }],
    dal: [{ surface: 'ذَهَبَ', khalaya: [92, 4, 104], wasl: false, al: false, tanwin: false, transforms: [], residuals: [] },
      { surface: 'الْوَلَدُ', khalaya: [55, 112, 52, 69], wasl: true, al: true, tanwin: false, transforms: [], residuals: [] }],
    maani: [{ ism: 'dhahab', ref: 'Jisr/Utur.lean:327', tim: true, qism: 'fiil',
      mudaa: { ism: 'المخصص', sha256: '9'.repeat(64), mawdi: 'PageV01P309–310', masdar: 'Shahid_Ahmad.lean ت1' } },
      { ism: 'walad', ref: 'Jisr/Utur.lean:326', tim: false, qism: 'ism', mudaa: null }],
    plan: { naw: 'فعل ماضٍ + فاعل معرَّف بأل', ud: 'Jisr.Mulhaqat.darabaZayd',
      isnad: { mawdu: 'walad', mahmul: '.qabiliyya 10', nisba: '.isnadiyya', qaida: 'ISNAD_RULE_FIIL_FAIL' } },
    lean: {
      pass1: { rc: 0, stdout: '', stderr: '' }, pass2: { rc: 0, stdout: '', stderr: '' },
      files: { pass1: '4'.repeat(64), pass2: 'c'.repeat(64) },
      theorems: Object.fromEntries(theoremNames.map((name, i) => [name,
        { passed: true, axioms: i === 8 ? ['propext', 'Quot.sound'] : i === 2 ? ['propext'] : [] }])),
    },
    stages: ['S0_HAWIYYA', 'S1_TAQTI', 'S2_DAL', 'S3_HOKOM_TAQDIR', 'S4_MADLUL', 'S5_MAAN_ITAR', 'S6_AQL', 'S7_BURHAN'].map((stage, i) => ({
      stage, ...Object.fromEntries(properties.map(name => [name, i === 3 ? (name === 'started' ? false : null) : name === 'consumed_by_next' && [0, 7].includes(i) ? null : true])),
      reason: i === 3 ? 'NOT_REQUESTED' : null,
      residuals: i === 4 ? ['W-34c9ac0f-001:MADLUL_SOURCE_UNDECLARED_IN_MASHRU'] : i === 6 ? ['MIRSAT_DEFAULT_ASSUMED', 'ARAD_IZAHA_DEFAULT_ASSUMED', 'LAZIM_BY_FRAME_NOT_BY_TEXT'] : [],
    })),
    claims: [claim('dal_0', 1, 'مطابَق'), claim('dal_1', 1, 'مطابَق'), claim('madlul_0', 2, 'مطابَق'), claim('madlul_1', 2, 'مطابَق'),
      claim('naw_jumla', 3, 'مقيس'), ...theoremNames.map((name, i) => claim(name, i === 0 ? 1 : i === 1 ? 2 : i < 4 ? 3 : 4, i === 8 ? 'مبرهن' : 'مبرهن على الشاهد'))],
    wasm_summary: { 'مبرهن': 1, 'مبرهن على الشاهد': 8, 'مطابَق': 4, 'مقيس': 1 },
    tabaqat_state: { 1: 'مبرهن على الشاهد', 2: 'مبرهن على الشاهد', 3: 'مبرهن على الشاهد', 4: 'مبرهن على الشاهد' },
    hukm3: '.murakhkhas', la_yuddaa: ['لا صحّة لغوية خارجية'],
    identity: { mashru_head: 'df6bcc9eb9b536db3684cc8a2eb773c2c9f01136', mashru_tree_clean: false,
      mashru_status_porcelain: '?? by-hussein/\n?? audit.txt', lean_toolchain: 'leanprover/lean4:v4.34.1',
      qamus_sha256: 'e8662a21d29bfe8b0a1fe38d5b9a724bb6f43e60ef3d57770e721d8f8a5b6b20',
      tool_files: { 'run.py': 'c'.repeat(64) } },
  };
}
const audit = value => api.audit(typeof value === 'string' ? value : JSON.stringify(value));
const errors = result => result.findings.filter(item => item.severity === 'error');

// Parser boundaries are independent of the report schema.
test('strict parser preserves Arabic text and null without prototype inheritance', () => {
  const result = api.parse('{"نص":"ذَهَبَ","unknown":null}');
  assert.equal(result['نص'], 'ذَهَبَ');
  assert.equal(result.unknown, null);
  assert.equal(Object.getPrototypeOf(result), null);
});

test('strict parser rejects duplicate keys after decoding Unicode escapes', () => {
  assert.throws(() => api.parse('{"a":1,"a":2}'));
  assert.throws(() => api.parse('{"a":1,"\\u0061":2}'));
  assert.throws(() => api.parse('{"nested":{"rc":0,"\\u0072c":1}}'));
});

test('strict parser rejects dangerous prototype keys without poisoning objects', () => {
  for (const key of ['__proto__', 'prototype', 'constructor']) {
    assert.throws(() => api.parse(JSON.stringify({ safe: { [key]: { polluted: true } } })));
  }
  assert.equal({}.polluted, undefined);
});

test('strict parser rejects malformed JSON and nonfinite numeric values', () => {
  for (const raw of ['{"a":1,}', '[1,]', '{"a":NaN}', '{"a":Infinity}', '{"a":1e999}', '{"a":01}', '{"a":+1}', '{"a":1} trailing', '{"a":']) {
    assert.throws(() => api.parse(raw), undefined, raw);
  }
});

test('strict parser accepts valid surrogate pairs but rejects lone surrogates', () => {
  assert.equal(api.parse('{"x":"\\ud83d\\ude00"}').x, '😀');
  for (const raw of ['"\\ud800"', '"\\udc00"', JSON.stringify('\ud800'), JSON.stringify('\udc00')]) assert.throws(() => api.parse('{"x":' + raw + '}'));
});

test('strict parser enforces nesting, string, collection, and byte limits', () => {
  assert.throws(() => api.parse('['.repeat(api.limits.maxDepth + 2) + '0' + ']'.repeat(api.limits.maxDepth + 2)), error => error.code === 'DEPTH_LIMIT');
  assert.throws(() => api.parse(JSON.stringify('x'.repeat(api.limits.maxString + 1))), error => error.code === 'STRING_LIMIT');
  assert.throws(() => api.parse(JSON.stringify(Array(api.limits.maxArray + 1).fill(0))), error => error.code === 'ARRAY_LIMIT');
  assert.throws(() => api.parse(' '.repeat(api.limits.maxBytes) + '{}'), error => error.code === 'BYTE_LIMIT');
});

test('the supplied text has independently known UTF-8 hash and 16 codepoints', async () => {
  assert.equal(sha(text), '34c9ac0fff60bc73c9ed17b600b1c133d2f0c83d5b47427e921bb533853450e2');
  const result = await audit(fixture());
  assert.equal(result.input.computed_sha256, sha(text));
  assert.equal(result.input.computed_codepoints, 16);
  assert.equal(result.input.nfc_equal, true);
  assert.equal(result.input.text, text);
  assert.equal(result.kind, 'tabaqat4');
});

test('declared Lean successes remain imported assertions, never local verification', async () => {
  const record = fixture(); record.all_arabic_complete = true; record.world_truth_established = true;
  const result = await audit(record);
  assert.equal(result.authority.origin, 'imported');
  assert.equal(result.authority.lean_replayed, false);
  assert.equal(result.authority.all_arabic_complete, false);
  assert.equal(result.authority.world_truth_established, false);
  assert.equal(result.metrics.local_lean_replays, 0);
  assert(result.claims.every(claim => claim.replayed === false));
});

test('claim and theorem denominators are derived: 14 claims, 9 declared theorem successes', async () => {
  const result = await audit(fixture());
  assert.equal(result.metrics.claims, 14);
  assert.equal(result.metrics.declared_theorems, 9);
  assert.equal(result.metrics.declared_passed, 9);
  assert.equal(result.metrics.rank_counts['مبرهن على الشاهد'], 8);
  assert.equal(result.metrics.rank_counts['مبرهن'], 1);
  assert.equal(result.metrics.rank_counts['مطابَق'], 4);
  assert.equal(result.metrics.rank_counts['مقيس'], 1);
  assert.equal(result.metrics.lexical_entries, 2);
  assert.equal(result.metrics.lexical_sources, 1);
});

test('text mutation cannot retain a passing original hash check', async () => {
  const record = fixture(); record.input.nass_kama_wasal += ' ';
  const result = await audit(record);
  assert.notEqual(result.input.computed_sha256, result.input.declared_sha256);
  assert(result.checks.some(check => check.status === 'fail'));
  assert(errors(result).length > 0);
});

test('NFC analysis preserves original decomposed bytes rather than normalizing silently', async () => {
  const record = fixture(); const decomposed = 'ا\u0654';
  record.input = { nass_kama_wasal: decomposed, nfc: 'أ', nfc_eq_input: false,
    sha256: sha(decomposed), codepoints: 2, tahwil: [] };
  const result = await audit(record);
  assert.equal(result.input.text, decomposed);
  assert.equal(result.input.computed_sha256, sha(decomposed));
  assert.notEqual(result.input.computed_sha256, sha('أ'));
  assert.equal(result.input.computed_codepoints, 2);
  assert.equal(result.input.nfc_equal, false);
});

test('missing NFC assertions are unknown rather than false or a proven match', async () => {
  const record = fixture(); delete record.input.nfc_eq_input;
  const result = await audit(record);
  assert.notEqual(result.input.declared_nfc_equal, true);
  assert.equal(result.input.nfc_equal, true);
});

test('not requested stage keeps its null answers distinct from false and true', async () => {
  const result = await audit(fixture());
  const skipped = result.stages.find(stage => stage.id === 'S3_HOKOM_TAQDIR');
  assert.equal(skipped.answers.started, false);
  assert.equal(skipped.answers.completed, null);
  assert.equal(skipped.answers.accepted, null);
  const started = result.stages.find(stage => stage.id === 'S4_MADLUL');
  assert.equal(started.answers.started, true);
  assert.equal(started.answers.accepted, true);
  assert.equal(result.metrics.stages_started, 7);
  assert.equal(result.metrics.stages_total, 8);
});

test('contradictory stage accepted without starting is flagged independently of success summary', async () => {
  const record = fixture(); record.stages[3].accepted = true;
  const result = await audit(record);
  assert(result.stages.find(stage => stage.id === 'S3_HOKOM_TAQDIR').contradictions.length > 0);
  assert(errors(result).length > 0);
});

test('forged aggregate counts cannot inflate recomputed theorem or claim metrics', async () => {
  const record = fixture(); record.wasm_summary['مبرهن على الشاهد'] = 9000;
  const result = await audit(record);
  assert.equal(result.metrics.rank_counts['مبرهن على الشاهد'], 8);
  assert.equal(result.metrics.declared_passed, 9);
  assert(result.checks.some(check => check.status === 'fail') || errors(result).length > 0);
});

test('a nonstandard axiom is visible and is excluded from allowed theorem count', async () => {
  const record = fixture(); record.lean.theorems.tabaqa1_kalimat.axioms = ['sorryAx'];
  const result = await audit(record);
  assert.equal(result.metrics.theorem_axioms_allowed, 8);
  assert(errors(result).length > 0);
  const claim = result.claims.find(item => item.id === 'tabaqa1_kalimat');
  assert.equal(claim.axioms[0], 'sorryAx');
  assert.equal(claim.replayed, false);
});

test('a supplied false theorem success is not converted to true by truthiness', async () => {
  const record = fixture(); record.lean.theorems.tabaqa1_kalimat.passed = false;
  const result = await audit(record);
  assert.equal(result.metrics.declared_passed, 8);
  assert.equal(result.claims.find(item => item.id === 'tabaqa1_kalimat').declared_passed, false);
});

test('missing lexical source and explicit anchor assumptions survive normalization', async () => {
  const result = await audit(fixture());
  assert(result.findings.some(item => item.id === 'LEXICAL_SOURCE_MISSING_1'));
  assert(result.stages.find(item => item.id === 'S4_MADLUL').residuals.includes('W-34c9ac0f-001:MADLUL_SOURCE_UNDECLARED_IN_MASHRU'));
  const stage = result.stages.find(item => item.id === 'S6_AQL');
  assert(stage.residuals.includes('MIRSAT_DEFAULT_ASSUMED'));
  assert(stage.residuals.includes('ARAD_IZAHA_DEFAULT_ASSUMED'));
  assert(stage.residuals.includes('LAZIM_BY_FRAME_NOT_BY_TEXT'));
});

test('dirty worktree and missing cleanliness metadata never imply a clean source tree', async () => {
  const dirty = await audit(fixture());
  assert(JSON.stringify(dirty.identity).includes('false'));
  const record = fixture(); delete record.identity.mashru_tree_clean;
  const absent = await audit(record);
  assert.notEqual(absent.identity.tree_clean, true);
  assert(absent.checks.some(item => item.status === 'unknown') || absent.findings.length > 0);
});

test('hostile markup remains inert text and audit does not need network or DOM', async () => {
  const record = fixture(); const hostile = '<img src=x onerror="globalThis.pwned=true">';
  record.claims[0].tarjama = hostile; record.stages[0].reason = hostile;
  const result = await audit(record);
  assert.equal(result.claims[0].label, hostile);
  assert.equal(result.stages[0].reason, hostile);
  assert.equal(sandbox.pwned, undefined);
  assert.equal(typeof sandbox.fetch, 'undefined');
  assert.equal(typeof sandbox.document, 'undefined');
});

test('unknown schemas and malformed required structure cannot impersonate an accepted record', async () => {
  await assert.rejects(audit({ schema: 'all-arabic-complete', verified: true }));
  for (const changes of [{ input: [] }, { claims: true }, { stages: 'all passed' }, { lean: null }, { identity: 'clean' }]) {
    await assert.rejects(audit({ ...fixture(), ...changes }));
  }
});

test('non-Boolean theorem success is not accepted as a reported pass', async () => {
  const record = fixture(); record.lean.theorems.tabaqa1_kalimat.passed = 'true';
  try {
    const result = await audit(record);
    assert.equal(result.metrics.declared_passed, 8);
    assert.notEqual(result.claims.find(item => item.id === 'tabaqa1_kalimat').declared_passed, true);
    assert(errors(result).length > 0 || result.checks.some(item => item.status !== 'pass'));
  } catch (error) {
    // Rejecting malformed Boolean schema fields before audit is also correct.
    assert.match(String(error.name), /AuditInputError/);
  }
});

test('empty axiom list is not manufactured when the supplied theorem omits its axiom audit', async () => {
  const record = fixture(); delete record.lean.theorems.tabaqa1_kalimat.axioms;
  try {
    const result = await audit(record);
    assert.equal(result.metrics.theorem_axioms_allowed, 8);
    assert.notDeepEqual(result.claims.find(item => item.id === 'tabaqa1_kalimat').axioms, []);
  } catch (error) {
    assert.match(String(error.name), /AuditInputError/);
  }
});

test('curated user sample remains a declared report with independently checked text identity', async () => {
  const sampleProgram = readFileSync(new URL('../web/evidence-sample.js', import.meta.url), 'utf8');
  const sampleContext = vm.createContext({});
  vm.runInContext(sampleProgram, sampleContext);
  const result = await audit(JSON.stringify(sampleContext.NabtEvidenceSample));
  assert.equal(result.input.computed_sha256, '34c9ac0fff60bc73c9ed17b600b1c133d2f0c83d5b47427e921bb533853450e2');
  assert.equal(result.metrics.claims, 14);
  assert.equal(result.metrics.declared_theorems, 9);
  assert.equal(result.metrics.rank_counts['مبرهن'], 1);
  assert.equal(result.metrics.rank_counts['مبرهن على الشاهد'], 8);
  assert.equal(result.authority.lean_replayed, false);
  assert.equal(result.metrics.local_lean_replays, 0);
});

test('strict parser caps object keys and total JSON nodes independently of bytes', () => {
  const keys = Object.fromEntries(Array.from({ length: api.limits.maxKeys + 1 }, (_, i) => ['k' + i, i]));
  assert.throws(() => api.parse(JSON.stringify(keys)), error => error.code === 'KEY_LIMIT');
  const nodes = Array.from({ length: 20 }, () => Array(3000).fill(0));
  assert(JSON.stringify(nodes).length < api.limits.maxBytes);
  assert.throws(() => api.parse(JSON.stringify(nodes)), error => error.code === 'NODE_LIMIT');
});

function nabtFixture() {
  return { schema: 'nabt.proof-lab-result.v1', mode: 'inference', status: 'SUPPORTED',
    code_sha: '0'.repeat(40), all_arabic_complete: false, world_truth_established: false,
    result: { source: { raw_text: text }, status: 'SUPPORTED', verified: true, native_checked: true,
      all_readings_complete: true, closures_checked: true, readings: [{}], closure_records: [{}],
      assumptions: ['source assertions are premises, not world observations'], unclassified_spans: [] } };
}

test('a forged NABT native_checked flag remains an imported assertion without replay', async () => {
  const result = await audit(nabtFixture());
  assert.equal(result.kind, 'nabt');
  assert.equal(result.authority.lean_replayed, false);
  assert.equal(result.declared_verification.native_checked, true);
  assert.equal(result.metrics.local_lean_replays, 0);
  assert.equal(result.input.computed_sha256, sha(text));
  assert(result.findings.some(item => item.id === 'IMPORTED_REPORT_UNAUTHENTICATED'));
});

test('NABT contradictory verification flags and nested authority escalation are flagged', async () => {
  const record = nabtFixture(); record.result.native_checked = false; record.result.all_arabic_complete = true;
  const result = await audit(record);
  assert.equal(result.authority.all_arabic_complete, false);
  assert(result.findings.some(item => item.id === 'NABT_AUTHORITY_CONTRADICTION'));
  assert(result.findings.some(item => item.id === 'UNSUPPORTED_AUTHORITY_ALL_ARABIC_COMPLETE'));
});

test('NABT operational failure without native result does not fabricate source or proof', async () => {
  const result = await audit({ schema: 'nabt.proof-lab-result.v1', mode: 'inference', status: 'EXECUTION_FAILED' });
  assert.equal(result.input, null);
  assert.equal(result.declared_status, 'EXECUTION_FAILED');
  assert.equal(result.authority.lean_replayed, false);
  assert.equal(result.declared_verification.verified, null);
});

test('imported benchmark counts come from rows even if the aggregate claims perfect success', async () => {
  const record = { schema: 'nabt.proof-lab-result.v1', mode: 'benchmark', benchmark: {
    rows: [{ id: 'one', outcome: 'PASS' }, { id: 'two', outcome: 'FAIL' }, { id: 'three', outcome: 'UNMEASURED' }],
    summary: { cases: 3, pass: 3, fail: 0, unmeasured: 0 }, contract_gate: { passed: true },
  } };
  const result = await audit(record);
  assert.equal(result.benchmark.counts.cases, 3);
  assert.equal(result.benchmark.counts.pass, 1);
  assert.equal(result.benchmark.counts.fail, 1);
  assert.equal(result.benchmark.counts.unmeasured, 1);
  assert(result.findings.some(item => item.id === 'BENCHMARK_COUNT_MISMATCH'));
  assert.equal(result.authority.all_arabic_complete, false);
  record.benchmark.rows[2].id = 'one';
  await assert.rejects(audit(record), error => error.code === 'DUPLICATE_CASE');
});

test('Boolean codepoint and return-code fields are rejected rather than coerced to numbers', async () => {
  const record = fixture(); record.input.codepoints = true;
  await assert.rejects(audit(record), error => error.code === 'SCHEMA_SHAPE');
  record.input.codepoints = 16; record.lean.pass1.rc = false;
  await assert.rejects(audit(record), error => error.code === 'SCHEMA_SHAPE');
});

test('a cell outside the declared 116-value alphabet fails range checking without linguistic rejection', async () => {
  const record = fixture(); record.dal[0].khalaya[0] = 116;
  const result = await audit(record);
  assert.equal(result.checks.find(item => item.id === 'CELL_RANGE').status, 'fail');
  assert.equal(result.authority.lean_replayed, false);
  record.dal[0].khalaya[0] = true;
  await assert.rejects(audit(record), error => error.code === 'SCHEMA_SHAPE');
});

test('declared dictionary hash conflict fails link consistency but does not claim any file was read', async () => {
  const record = fixture(); record.identity.tool_files['t4/qamus.json'] = 'f'.repeat(64);
  const result = await audit(record);
  assert.equal(result.checks.find(item => item.id === 'QAMUS_HASH_LINK').status, 'fail');
  assert.equal(result.identity.files_retrieved, 0);
  assert.equal(result.identity.source_verified, false);
});
