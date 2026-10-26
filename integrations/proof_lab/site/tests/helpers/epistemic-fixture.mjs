import { createHash } from 'node:crypto';
export const hash = 'a'.repeat(64);
export const requestId = '11111111-1111-4111-8111-111111111111';
const canonical = value => Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']' : value !== null && typeof value === 'object' ? '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}' : JSON.stringify(value);
export const digest = (value, raw = false) => createHash('sha256').update(raw ? value : canonical(value)).digest('hex');
export function reseal(row) {
  const e = row.execution;
  for (const [key, target] of [['input', 'input_sha256'], ['proposal', 'proposal_sha256'], ['native_result', 'native_result_sha256']]) e[target] = e[key] === null ? null : digest(e[key]);
  const unsigned = { ...row }; delete unsigned.receipt_sha256; row.receipt_sha256 = digest(unsigned); return row;
}
export function suite() {
  const cases = ['SUPPORTED', 'REFUTED', 'CONFLICT', 'UNKNOWN', 'RESOURCE_LIMIT', 'SUPPORTED'].map((status, i) => {
    const group = i === 5 ? 'agency_record' : 'authored_controls';
    const key = { axis: i === 5 ? 'recorded_observation' : 'reported_motive', entity: 'fixture:entity', predicate: 'fixture:predicate', value: 'fixture:value', unit: 'unit', context: 'context:' + i, time: '-1', place: 'fixture:place' };
    if (i === 5) Object.assign(key, { axis: 'recorded_observation', entity: 'official20110311054624120_30', predicate: 'magnitude:mww', value: '9.1', unit: 'dimensionless', context: 'usgs.preferred-event.v1', time: '1299822384120', place: '142.373,38.297,29' });
    const source = i === 5 ? { identity: 'USGS:official20110311054624120_30', revision: '1792147089160', content: canonical({ pointer: '/properties/mag', revision: '1792147089160', source_sha256: 'd9cf0301f748786d5ff881edba71e1b19c5b5008b3abeb893e8e88240433ba4a', value: '9.1' }) } : { identity: 'fixture:source:' + i, revision: '1', content: 'هذه بيانات اختبار برمجي مؤلفة، وليست رصدًا.' };
    const query = { key, positive: true, origin: 'query' };
    const kind = status === 'UNKNOWN' ? 'lexical' : i === 5 ? 'observation' : 'self_report';
    const base = { id: 'e1', source, key, positive: status !== 'REFUTED', kind, origin: 'record', ancestry: ['record'] };
    const interpretations = status === 'CONFLICT' ? [base, { ...base, id: 'e2', positive: false }] : [base];
    const certificate = { status, support_ids: ['SUPPORTED', 'CONFLICT'].includes(status) ? ['e1'] : [], refutation_ids: status === 'REFUTED' ? ['e1'] : status === 'CONFLICT' ? ['e2'] : [], selected_ids: status === 'CONFLICT' ? ['e1', 'e2'] : ['SUPPORTED', 'REFUTED'].includes(status) ? ['e1'] : [] };
    const input = { query, active_sources: [source], origins: [{ id: 'query', parents: [] }, { id: 'record', parents: [] }], interpretations, budget: status === 'RESOURCE_LIMIT' ? 0 : 2, certificate };
    const nativeResult = { law_id: 'nabt.epistemic-measurement.v1', ...certificate, observed_status: status, certificate_checked: true, world_truth_established: false, hidden_motive_established: false, all_arabic_complete: false };
    return reseal({ id: 'fixture-' + i, group, query, expected: structuredClone(certificate), observed: structuredClone(certificate), comparison: 'PASS', native_checked: true, certificate_checked: true, proof_scope: 'Only this authored transport fixture; no actual world observation is asserted.',
      source_bindings: [{ identity: source.identity, revision: source.revision, content_sha256: digest(source.content, true), raw_sha256: i === 5 ? 'd9cf0301f748786d5ff881edba71e1b19c5b5008b3abeb893e8e88240433ba4a' : null, raw_path: i === 5 ? 'evidence/epistemic_measurement_v1/observations/usgs_tohoku_raw.json' : null, field_pointer: i === 5 ? '/properties/mag' : null }], evidence_class: i === 5 ? 'AGENCY_RECORD' : 'AUTHORED_SCENARIO',
      execution: { input, input_sha256: null, proposal_sha256: null, native_result_sha256: null, native_sha256: hash, proposal: certificate, native_result: nativeResult, error: null, source_profile: i === 5 ? 'usgs_snapshot_v1' : 'authored_controls_v1' } });
  });
  const empty = () => ({ eligible: 0, measured: 0, passed: 0, failed: 0, unmeasured: 0 });
  const one = () => ({ eligible: 1, measured: 1, passed: 1, failed: 0, unmeasured: 0 });
  return { schema: 'nabt.epistemic-measurement-benchmark.v1', law_id: 'nabt.epistemic-measurement.v1', reference_sha256: hash, source_registry_sha256: hash, runtime_sha256: hash, native_sha256: hash, all_cases_native_checked: true,
    hidden_motive_measured: false, free_arabic_acquisition_measured: false, whole_arabic_complete: false, world_truth_established: false, cases,
    groups: { authored_controls: { case_count: 5, metrics: { positive_capability: one(), refutation: one(), conflict: one(), safe_abstention: one(), resource_boundary: one() } }, agency_record: { case_count: 1, metrics: { positive_capability: one(), refutation: empty(), conflict: empty(), safe_abstention: empty(), resource_boundary: empty() } } } };
}
export function unavailable() {
  const value = suite(); value.native_sha256 = null; value.all_cases_native_checked = false;
  for (const row of value.cases) {
    row.native_checked = false; row.certificate_checked = false; row.comparison = 'UNMEASURED'; row.observed = null;
    Object.assign(row.execution, { native_result: null, native_sha256: null, native_result_sha256: null, error: 'NATIVE_UNAVAILABLE' }); reseal(row);
  }
  for (const group of Object.values(value.groups)) for (const metric of Object.values(group.metrics)) Object.assign(metric, { measured: 0, passed: 0, failed: 0, unmeasured: metric.eligible });
  return value;
}
export function report(value = suite()) { return { schema: 'nabt.proof-lab-result.v1', mode: 'epistemic_measurement', request_id: requestId, code_sha: 'b'.repeat(40), payload_sha256: hash, native_sha256: value.native_sha256, runtime_sha256: hash, reference_sha256: hash, source_registry_sha256: hash, status: 'EPISTEMIC_MEASUREMENT_COMPLETE', all_arabic_complete: false, world_truth_established: false, epistemic_measurement: value }; }
