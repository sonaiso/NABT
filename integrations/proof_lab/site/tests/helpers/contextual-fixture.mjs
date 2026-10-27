// Authored transport fixtures; declared native results are not executed Lean.
import { createHash } from 'node:crypto';
export const hash = 'a'.repeat(64), code = 'b'.repeat(40), requestId = '11111111-1111-4111-8111-111111111111';
export const canonical = v => Array.isArray(v) ? '[' + v.map(canonical).join(',') + ']' : v !== null && typeof v === 'object' ? '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canonical(v[k])).join(',') + '}' : JSON.stringify(v);
export const digest = (v, raw = false) => createHash('sha256').update(raw ? v : canonical(v)).digest('hex');
export const QAC = 'a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46';
export const LAW = 'nabt.initial-contextual-reference.v1';
export const observationScope = { reference: 'INITIAL_SOURCE_ATTESTED_OCCURRENCE_WITH_EXPLICIT_CONTEXT', source_acquisition: 'PYTHON_PINNED_RAW_SOURCE_REPLAY', typed_annotation_interpretation: 'DECLARED_PREMISE_NOT_PROVED_BY_LEAN', lexical_inventory: 'ALL_SOURCE_BACKED_PERSON_BRIDGE_ALTERNATIVES_FOR_EXACT_SURFACE', sentence_syntax_promoted: false, sentence_readings_promoted: false, context_truth_established: false, world_truth_established: false, hidden_motive_established: false, whole_arabic_complete: false, tawatur_status: 'UNKNOWN' };
const scope = { reference: 'INITIAL_OCCURRENCE_ONLY', comparison: 'PYTHON_REFERENCE_COMPARISON', native: 'CONDITIONAL_REFERENCE_CERTIFICATE_NOT_GOLD_OR_FULL_SENTENCE_PROOF', original_syntax_and_readings: 'UNCHANGED_ATTESTED_QAC_PYTHON_REPLAY', sources: 'PINNED_SOURCE_ANNOTATIONS_AND_DECLARED_CONTEXT_PREMISES', independent_reference: 'AUTHORED_DIAGNOSTIC_NOT_EXTERNAL_BLIND_HOLDOUT' };
const flags = { whole_clause_checked: false, world_truth_established: false, motive_established: false, all_arabic_complete: false };
export function reseal(row) {
  const o = row.execution, e = o.execution;
  row.input_sha256 = digest(row.input); o.input_sha256 = row.input_sha256;
  o.context_sha256 = digest(row.input.context);
  for (const [key, sha] of [['input', 'input_sha256'], ['proposal', 'proposal_sha256'], ['native_result', 'native_result_sha256']]) e[sha] = e[key] === null ? null : digest(e[key]);
  if (o.reference) { const ref = { ...o.reference }; delete ref.reference_id; o.reference.reference_id = digest(ref); }
  row.reference_comparison.observed = structuredClone(o.reference);
  const unsigned = { ...o }; delete unsigned.receipt_sha256; o.receipt_sha256 = digest(unsigned);
  return row;
}
function metric(statuses) { const pass = statuses.filter(s => s === 'PASS').length, fail = statuses.filter(s => s === 'FAIL').length, unmeasured = statuses.filter(s => s === 'UNMEASURED').length; return { eligible: pass + fail + unmeasured, measured: pass + fail, passed: pass, failed: fail, unmeasured }; }
export function recount(s) {
  for (const name of ['original_25', 'independent_20']) {
    const rows = s.cases.filter(c => c.group === name), g = { case_count: rows.length, reference_after: metric(rows.map(c => c.reference_comparison.status)) };
    if (name === 'original_25') g.baseline_axes = Object.fromEntries(['syntax', 'readings', 'reference'].map(a => [a, metric(rows.map(r => r.baseline_axes[a]))]));
    else g.metric_categories = Object.fromEntries(['positive_binding', 'alternative_retention', 'safe_nonresolution'].map(a => [a, metric(rows.filter(r => r.metric_category === a).map(r => r.reference_comparison.status))]));
    s.groups[name] = g;
  }
  return s;
}
export function suite() {
  const result = { schema: 'nabt.contextual-reference-benchmark.v1', law_id: LAW, original_reference_sha256: hash, independent_reference_sha256: hash, baseline_source_sha256: hash, scorer_sha256: hash, source_registry_sha256: hash, runtime_sha256: hash, native_sha256: hash, groups: {}, cases: [], all_cases_native_checked: true, scope: structuredClone(scope), whole_arabic_complete: false, tawatur_evaluated: false, world_truth_established: false, motive_measured: false };
  for (let i = 0; i < 45; i++) {
    const group = i < 25 ? 'original_25' : 'independent_20', outside = i === 26, ambiguous = i === 27, empty = i === 28;
    const surface = ambiguous ? 'هذا' : 'أنا', text = outside ? '«أنا»' : surface + ' عالم.';
    const entities = [{ id: 'person_a', name: 'زيد', gender: 'masculine', number: 'singular', kind: 'person' }, { id: 'person_b', name: 'عمرو', gender: 'masculine', number: 'singular', kind: 'person' }];
    const context = { entities, deixis: ambiguous ? [{ form: surface, entity_ids: ['person_a', 'person_b'] }] : [], closed_reference_scope: true, ...(!empty ? { speaker: 'person_a' } : {}) };
    const input = { text, context };
    const candidates = outside || empty ? [] : ambiguous ? ['person_a', 'person_b'] : ['person_a'];
    const status = outside ? 'OUT_OF_SCOPE' : ambiguous ? 'AMBIGUOUS' : empty ? 'NO_CANDIDATE' : 'RESOLVED', bound = status === 'RESOLVED' ? 'person_a' : null;
    const proposed = { status, reading_ids: outside ? [] : ['reading:1'], candidate_entity_ids: candidates, bound_entity_id: bound, reading_results: outside ? [] : [{ id: 'reading:1', status, candidate_entity_ids: candidates, bound_entity_id: bound }] };
    const record = ambiguous ? '(1:1:1:1)\th*aA\tDEM\tPOS:DEM|MS\n' : '(1:1:1:1)\t>anaA\tPRON\tPOS:PRON|1S\n', start = 10, end = start + Buffer.byteLength(record);
    const nativeInput = { source: { id: 'contextual_reference_input', revision: digest(text, true), text }, occurrence: { start_byte: outside ? 2 : 0, end_byte: (outside ? 2 : 0) + Buffer.byteLength(surface), surface }, context: { ...context, speaker: context.speaker ?? null, addressee: null }, donors: [{ id: 'donor:1', source_id: 'qac_attested_source_v1', source_revision: QAC, start_byte: start, end_byte: end, record }], alternatives: [{ id: 'reading:1', pos: ambiguous ? 'DEM' : 'PRON', profile_code: ambiguous ? '3MS' : '1S', target_surface: surface, source_form: ambiguous ? 'هذَا' : 'أَنَا', donor_ids: ['donor:1'] }], budget: 256, proposed };
    const nativeResult = { law_id: LAW, ...proposed, observed_status: status, certificate_checked: true, ...flags };
    const reference = outside ? null : { surface, status, candidate_entity_ids: candidates, bound_entity_id: bound, reference_id: null, span: { start: 0, end: Array.from(surface).length }, scope: 'outer', occurrence: 0 };
    const expected = i < 20 ? { status: 'not_applicable', target_ids: [] } : { surface, status: outside || empty ? 'unresolved' : ambiguous ? 'ambiguous' : 'resolved', target_ids: outside || empty ? [] : ambiguous ? ['person_a', 'person_b'] : [i === 25 ? 'person_b' : 'person_a'], ...(i >= 25 ? { span: { start: outside ? 1 : 0, end: (outside ? 1 : 0) + Array.from(surface).length }, scope: outside ? 'quote:1' : 'outer', occurrence: 0 } : {}) };
    const cmp = i < 20 ? 'NOT_APPLICABLE' : [25, 26].includes(i) ? 'FAIL' : 'PASS';
    const reason = i < 20 ? 'EXCLUDED_BY_ORIGINAL_REFERENCE_SCOPE' : i === 26 ? 'TARGET_OCCURRENCE_OUTSIDE_EXECUTED_REFERENCE_SCOPE' : i === 25 ? 'REFERENCE_NOT_ACQUIRED_AS_EXPECTED' : 'REFERENCE_MATCH';
    const observation = { schema: 'nabt.contextual-reference-observation.v1', law_id: LAW, status, native_checked: true, certificate_checked: true, reference, input, input_sha256: null, context_sha256: null, lexical_source_sha256: QAC, source_registry_sha256: hash, runtime_sha256: hash, native_sha256: hash, source_bindings: [{ id: 'donor:1', source_id: 'qac_attested_source_v1', source_sha256: QAC, byte_start: start, byte_end: end, content_sha256: digest(record, true), locator: [1, 1, 1, 1] }], scope: structuredClone(observationScope), execution: { input: nativeInput, input_sha256: null, proposal: proposed, proposal_sha256: null, native_result: nativeResult, native_result_sha256: null, native_sha256: hash, error: null }, receipt_sha256: null };
    const row = { id: 'fixture-' + i, group, input, input_sha256: null, metric_category: { resolved: 'positive_binding', ambiguous: 'alternative_retention', unresolved: 'safe_nonresolution', not_applicable: 'not_applicable' }[expected.status], expected_reference: expected, baseline_axes: i < 25 ? { syntax: 'FAIL', readings: 'FAIL', reference: i < 20 ? 'NOT_APPLICABLE' : 'FAIL' } : null, reference_comparison: { status: cmp, expected, observed: reference, reason }, execution: observation };
    result.cases.push(reseal(row));
  }
  return recount(result);
}
export function report(value = suite()) { const digests = Object.fromEntries(['original_reference_sha256', 'independent_reference_sha256', 'baseline_source_sha256', 'scorer_sha256', 'source_registry_sha256', 'runtime_sha256', 'native_sha256'].map(k => [k, value[k]])); return { schema: 'nabt.proof-lab-result.v1', mode: 'contextual_reference', request_id: requestId, code_sha: code, payload_sha256: hash, status: 'CONTEXTUAL_REFERENCE_COMPLETE', all_arabic_complete: false, world_truth_established: false, ...digests, contextual_reference: value }; }
export function unavailable() {
  const s = suite(); s.native_sha256 = null; s.all_cases_native_checked = false;
  for (const r of s.cases) {
    const o = r.execution, e = o.execution;
    Object.assign(o, { native_checked: false, certificate_checked: false, native_sha256: null, status: 'UNMEASURED', reference: null });
    Object.assign(e, { native_result: null, native_result_sha256: null, native_sha256: null, error: 'NATIVE_UNAVAILABLE' });
    if (r.expected_reference.status !== 'not_applicable') Object.assign(r.reference_comparison, { status: 'UNMEASURED', reason: 'NATIVE_REFERENCE_CHECK_UNAVAILABLE' });
    reseal(r);
  }
  return recount(s);
}
