/* Shared structural contract for Worker, browser and imported reports.
 * Validation checks consistency; it never authenticates an imported record. */
'use strict';
(() => {
  const LAW = 'nabt.epistemic-measurement.v1';
  const CATEGORIES = Object.freeze({ SUPPORTED: 'positive_capability', REFUTED: 'refutation', CONFLICT: 'conflict', UNKNOWN: 'safe_abstention', RESOURCE_LIMIT: 'resource_boundary' });
  const GROUPS = Object.freeze({ authored_controls: 'AUTHORED_SCENARIO', agency_record: 'AGENCY_RECORD' });
  const AXES = ['reported_motive', 'recorded_observation', 'hidden_motive'];
  const USGS = Object.freeze({ identity: 'USGS:official20110311054624120_30', revision: '1792147089160', raw_sha256: 'd9cf0301f748786d5ff881edba71e1b19c5b5008b3abeb893e8e88240433ba4a', raw_path: 'evidence/epistemic_measurement_v1/observations/usgs_tohoku_raw.json', pointer: '/properties/mag', value: '9.1' });
  const USGS_KEY = Object.freeze({ axis: 'recorded_observation', entity: 'official20110311054624120_30', predicate: 'magnitude:mww', value: '9.1', unit: 'dimensionless', context: 'usgs.preferred-event.v1', time: '1299822384120', place: '142.373,38.297,29' });
  const KINDS = ['self_report', 'observation', 'lexical', 'grammar', 'hypothetical', 'quotation'];
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const integer = v => Number.isSafeInteger(v) && v >= 0;
  const text = v => typeof v === 'string' && v.trim().length > 0 && v.length <= 131072;
  const hash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
  const own = (v, k) => Object.prototype.hasOwnProperty.call(v, k);
  const deny = message => { throw new Error('عقد قياس القصد والرصد: ' + message); };
  function exact(v, keys) { if (!object(v) || Object.keys(v).length !== keys.length || keys.some(k => !own(v, k))) deny('حقول غير مطابقة للمخطط.'); }
  function canonical(v) {
    if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']';
    if (object(v)) return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canonical(v[k])).join(',') + '}';
    return JSON.stringify(v);
  }
  const same = (a, b) => canonical(a) === canonical(b);
  function names(v) { if (!Array.isArray(v) || v.length > 256 || v.some(n => !text(n)) || new Set(v).size !== v.length) deny('معرفات الأدلة غير صالحة أو مكررة.'); }
  function key(v) {
    exact(v, ['axis', 'entity', 'predicate', 'value', 'unit', 'context', 'time', 'place']);
    if (!AXES.includes(v.axis) || ['entity', 'predicate', 'value', 'unit', 'context', 'place'].some(k => !text(v[k]))) deny('مفتاح الدعوى غير صالح.');
    if (typeof v.time !== 'string' || (!/^(?:0|-?[1-9][0-9]{0,15})$/.test(v.time) || BigInt(v.time) > 9007199254740991n || BigInt(v.time) < -9007199254740991n)) deny('الزمن يجب أن يكون سلسلة عدد صحيح معيارية بلا تحويل عددي.');
  }
  function query(v) { exact(v, ['key', 'positive', 'origin']); key(v.key); if (typeof v.positive !== 'boolean' || !text(v.origin)) deny('قطبية الاستعلام أو منشؤه غير صالح.'); }
  function source(v) { exact(v, ['identity', 'revision', 'content']); if (!text(v.identity) || !text(v.revision) || !text(v.content)) deny('هوية المصدر أو محتواه غائب.'); }
  function receipt(v) {
    exact(v, ['status', 'support_ids', 'refutation_ids', 'selected_ids']);
    if (!own(CATEGORIES, v.status)) deny('حالة شهادة غير معروفة.');
    for (const k of ['support_ids', 'refutation_ids', 'selected_ids']) names(v[k]);
    if (v.support_ids.some(id => v.refutation_ids.includes(id)) || v.selected_ids.length !== v.support_ids.length + v.refutation_ids.length || [...v.support_ids, ...v.refutation_ids].some(id => !v.selected_ids.includes(id))) deny('قوائم الشهادة لا تتفق.');
    const positive = v.support_ids.length > 0, negative = v.refutation_ids.length > 0;
    const classified = positive ? (negative ? 'CONFLICT' : 'SUPPORTED') : (negative ? 'REFUTED' : 'UNKNOWN');
    if (v.status === 'RESOURCE_LIMIT' ? v.selected_ids.length !== 0 : v.status !== classified) deny('الحالة تناقض قوائم الدليل.');
  }
  function input(v) {
    exact(v, ['query', 'active_sources', 'origins', 'interpretations', 'budget', 'certificate']); query(v.query);
    if (!integer(v.budget) || v.budget > 128 || !Array.isArray(v.active_sources) || v.active_sources.length > 128 || !Array.isArray(v.origins) || v.origins.length > 256 || !Array.isArray(v.interpretations) || v.interpretations.length > 128) deny('حدود المدخل غير صالحة.');
    v.active_sources.forEach(source);
    if (new Set(v.active_sources.map(s => s.identity)).size !== v.active_sources.length) deny('تكررت هوية مصدر نشط.');
    const origins = new Map();
    for (const entry of v.origins) { exact(entry, ['id', 'parents']); if (!text(entry.id) || origins.has(entry.id)) deny('هوية منشأ مكررة.'); names(entry.parents); origins.set(entry.id, entry); }
    if (!origins.has(v.query.origin) || [...origins.values()].some(o => o.parents.some(p => !origins.has(p)))) deny('مرجع منشأ مفقود.');
    const ids = new Set();
    for (const entry of v.interpretations) {
      exact(entry, ['id', 'source', 'key', 'positive', 'kind', 'origin', 'ancestry']); source(entry.source); key(entry.key); names(entry.ancestry);
      if (!text(entry.id) || ids.has(entry.id) || typeof entry.positive !== 'boolean' || !KINDS.includes(entry.kind) || !origins.has(entry.origin) || entry.ancestry.some(id => !origins.has(id))) deny('سجل التفسير غير صالح.');
      ids.add(entry.id);
    }
    receipt(v.certificate);
    if (v.certificate.selected_ids.some(id => !ids.has(id))) deny('الشهادة تشير إلى دليل خارج المدخل.');
  }
  function native(v) {
    if (!object(v) || v.law_id !== LAW || v.world_truth_established !== false || v.hidden_motive_established !== false || v.all_arabic_complete !== false) deny('حدود نتيجة Lean متناقضة.');
    if (own(v, 'reason')) {
      exact(v, ['law_id', 'status', 'reason', 'world_truth_established', 'hidden_motive_established', 'all_arabic_complete']);
      if (!['INVALID_INPUT', 'RESOURCE_LIMIT'].includes(v.status) || !text(v.reason)) deny('إيصال إخفاق Lean غير صالح.');
      return;
    }
    exact(v, ['law_id', 'status', 'observed_status', 'support_ids', 'refutation_ids', 'selected_ids', 'certificate_checked', 'world_truth_established', 'hidden_motive_established', 'all_arabic_complete']);
    if (typeof v.certificate_checked !== 'boolean' || ![...Object.keys(CATEGORIES), 'INVALID_CERTIFICATE'].includes(v.status)) deny('تصريح فحص الشهادة غير صالح.');
    receipt({ status: v.observed_status, support_ids: v.support_ids, refutation_ids: v.refutation_ids, selected_ids: v.selected_ids });
    if (v.certificate_checked ? v.status !== v.observed_status : v.status !== 'INVALID_CERTIFICATE') deny('نتيجة الفحص تناقض رتبتها.');
  }
  function validate(suite) {
    exact(suite, ['schema', 'law_id', 'reference_sha256', 'source_registry_sha256', 'runtime_sha256', 'native_sha256', 'groups', 'cases', 'all_cases_native_checked', 'hidden_motive_measured', 'free_arabic_acquisition_measured', 'whole_arabic_complete', 'world_truth_established']);
    if (!object(suite) || suite.schema !== 'nabt.epistemic-measurement-benchmark.v1' || suite.law_id !== LAW || !Array.isArray(suite.cases) || suite.cases.length < 1 || suite.cases.length > 256 || typeof suite.all_cases_native_checked !== 'boolean') deny('مخطط مجموعة غير صالح.');
    for (const k of ['reference_sha256', 'source_registry_sha256', 'runtime_sha256']) if (!hash(suite[k])) deny('هوية مجموعة أو برنامج مفقودة.');
    for (const k of ['hidden_motive_measured', 'free_arabic_acquisition_measured', 'whole_arabic_complete', 'world_truth_established']) if (suite[k] !== false) deny('تجاوز حدود القياس.');
    if (suite.native_sha256 !== null && !hash(suite.native_sha256)) deny('بصمة منفذ Lean غير صالحة.');
    exact(suite.groups, Object.keys(GROUPS));
    const counts = Object.fromEntries(Object.keys(GROUPS).map(group => [group, { case_count: 0, metrics: Object.fromEntries(Object.values(CATEGORIES).map(c => [c, { eligible: 0, measured: 0, passed: 0, failed: 0, unmeasured: 0 }])) }]));
    const ids = new Set();
    for (const item of suite.cases) {
      exact(item, ['id', 'group', 'query', 'expected', 'observed', 'comparison', 'native_checked', 'certificate_checked', 'receipt_sha256', 'proof_scope', 'source_bindings', 'evidence_class', 'execution']);
      if (!text(item.id) || ids.has(item.id) || !own(GROUPS, item.group) || item.evidence_class !== GROUPS[item.group] || !text(item.proof_scope) || !['PASS', 'FAIL', 'UNMEASURED'].includes(item.comparison) || typeof item.native_checked !== 'boolean' || typeof item.certificate_checked !== 'boolean') deny('هوية الدعوى أو مقامها أو حدودها غير صالحة.');
      ids.add(item.id); query(item.query); receipt(item.expected);
      if (item.observed !== null) receipt(item.observed);
      const execution = item.execution;
      exact(execution, ['input', 'input_sha256', 'proposal_sha256', 'native_result_sha256', 'native_sha256', 'proposal', 'native_result', 'error', 'source_profile']);
      if (execution.input !== null) {
        input(execution.input); receipt(execution.proposal);
        if (!same(execution.input.query, item.query) || !same(execution.input.certificate, execution.proposal)) deny('الاستعلام أو الشهادة لا يطابق المدخل الذي فُحص.');
      } else if (execution.proposal !== null || execution.input_sha256 !== null || execution.proposal_sha256 !== null || item.native_checked) deny('إيصال مدخل غير صالح يناقض رتبة الفحص.');
      if ((execution.input !== null && (!hash(execution.input_sha256) || !hash(execution.proposal_sha256))) || (execution.native_result_sha256 !== null && !hash(execution.native_result_sha256)) || (execution.native_sha256 !== null && !hash(execution.native_sha256)) || (execution.error !== null && !text(execution.error))) deny('هويات التنفيذ أو خطئه غير صالحة.');
      if (execution.source_profile !== (item.group === 'authored_controls' ? 'authored_controls_v1' : 'usgs_snapshot_v1')) deny('مصدر التنفيذ لا ينتمي إلى مقامه.');
      if (execution.native_result !== null) native(execution.native_result);
      if ((execution.native_result === null) !== (execution.native_result_sha256 === null)) deny('بصمة النتيجة لا تطابق وجودها.');
      if (execution.native_sha256 !== null && execution.native_sha256 !== suite.native_sha256) deny('منفذ الحالة لا يطابق منفذ المجموعة.');
      if (item.native_checked !== item.certificate_checked) deny('تصريحا التحقق متناقضان.');
      if (item.native_checked) {
        if (!hash(suite.native_sha256) || execution.native_sha256 !== suite.native_sha256 || !hash(item.receipt_sha256) || item.observed === null || item.comparison === 'UNMEASURED' || execution.error !== null || execution.native_result?.certificate_checked !== true) deny('دعوى مفحوصة بلا شهادة مرتبطة مكتملة.');
        const r = execution.native_result;
        if (!same(item.observed, execution.proposal) || !same(item.observed, { status: r.observed_status, support_ids: r.support_ids, refutation_ids: r.refutation_ids, selected_ids: r.selected_ids })) deny('القوائم المرصودة والشهادة ونتيجة Lean مختلفة.');
        if (item.comparison !== (same(item.expected, item.observed) ? 'PASS' : 'FAIL')) deny('المقارنة لا تطابق المرجع والمرصود.');
        const ledger = execution.input, q = ledger.query;
        const originMap = new Map(ledger.origins.map(o => [o.id, o.parents]));
        const admissible = ledger.budget < ledger.interpretations.length ? [] : ledger.interpretations.filter(e =>
          ledger.active_sources.some(s => same(s, e.source)) && same(e.key, q.key) &&
          ((e.kind === 'self_report' && q.key.axis === 'reported_motive') || (e.kind === 'observation' && q.key.axis === 'recorded_observation')) &&
          e.ancestry.includes(e.origin) && !e.ancestry.includes(q.origin) && e.ancestry.every(o => originMap.get(o).every(parent => e.ancestry.includes(parent))));
        const selected = admissible.map(e => e.id), support = admissible.filter(e => e.positive === q.positive).map(e => e.id), refutation = admissible.filter(e => e.positive !== q.positive).map(e => e.id);
        const status = ledger.budget < ledger.interpretations.length ? 'RESOURCE_LIMIT' : support.length ? (refutation.length ? 'CONFLICT' : 'SUPPORTED') : refutation.length ? 'REFUTED' : 'UNKNOWN';
        if (!same(item.observed, { status, support_ids: support, refutation_ids: refutation, selected_ids: selected })) deny('الشهادة تخالف كامل سجل التفسير أو قيوده.');
      } else {
        if (item.observed !== null || !hash(item.receipt_sha256) || item.comparison !== 'UNMEASURED' || execution.error === null || execution.native_result?.certificate_checked === true) deny('تصريحات عدم الفحص تتناقض مع النتيجة.');
      }
      if (item.group === 'agency_record' && execution.input !== null && execution.input.interpretations.some(e => !same(e.key, USGS_KEY) || e.kind !== 'observation' || e.positive !== true)) deny('ترجمة سجل الوكالة لا تطابق الحقل المفضل المثبت.');
      if (!Array.isArray(item.source_bindings) || item.source_bindings.length > 256) deny('روابط المصادر غير صالحة.');
      for (const binding of item.source_bindings) {
        exact(binding, ['identity', 'revision', 'content_sha256', 'raw_sha256', 'raw_path', 'field_pointer']);
        if (!text(binding.identity) || !text(binding.revision) || !hash(binding.content_sha256)) deny('هوية شهادة المصدر غير صالحة.');
        if (item.group === 'authored_controls') {
          if (binding.raw_sha256 !== null || binding.raw_path !== null || binding.field_pointer !== null) deny('مصدر مؤلف يزعم رصدًا خارجيًا.');
        } else if (binding.identity !== USGS.identity || binding.revision !== USGS.revision || binding.raw_sha256 !== USGS.raw_sha256 || binding.raw_path !== USGS.raw_path || binding.field_pointer !== USGS.pointer) deny('رابط الوكالة لا يطابق الملف والموضع المثبتين.');
      }
      const count = counts[item.group]; count.case_count++;
      const metric = count.metrics[CATEGORIES[item.expected.status]]; metric.eligible++;
      if (item.comparison === 'UNMEASURED') metric.unmeasured++;
      else { metric.measured++; metric[item.comparison === 'PASS' ? 'passed' : 'failed']++; }
    }
    if (suite.all_cases_native_checked !== suite.cases.every(row => row.native_checked)) deny('تصريح فحص المجموعة يخالف حالاتها.');
    for (const group of Object.keys(GROUPS)) {
      const declared = suite.groups[group]; exact(declared, ['case_count', 'metrics']);
      if (!integer(declared.case_count) || declared.case_count !== counts[group].case_count) deny('مقام المجموعة لا يطابق صفوفها.');
      exact(declared.metrics, Object.values(CATEGORIES));
      for (const category of Object.values(CATEGORIES)) {
        const metric = declared.metrics[category]; exact(metric, ['eligible', 'measured', 'passed', 'failed', 'unmeasured']);
        if (Object.values(metric).some(n => !integer(n)) || !same(metric, counts[group].metrics[category])) deny('أعداد القياس لا تطابق الحالات.');
      }
    }
    return suite;
  }
  function validateEnvelope(report) {
    const allowed = ['schema', 'request_id', 'payload_sha256', 'code_sha', 'native_sha256', 'generated_at_utc', 'duration_ms', 'mode', 'status', 'all_arabic_complete', 'world_truth_established', 'scope', 'reference_sha256', 'source_registry_sha256', 'runtime_sha256', 'runner_sha256', 'measurement_source_sha256', 'toolchain', 'epistemic_measurement'];
    if (!object(report) || Object.keys(report).some(k => !allowed.includes(k)) || report.schema !== 'nabt.proof-lab-result.v1' || report.mode !== 'epistemic_measurement' || report.status !== 'EPISTEMIC_MEASUREMENT_COMPLETE' || report.all_arabic_complete !== false || report.world_truth_established !== false) deny('غلاف القياس أو حدود سلطته غير صالح.');
    const suite = validate(report.epistemic_measurement);
    for (const k of ['native_sha256', 'runtime_sha256', 'reference_sha256', 'source_registry_sha256']) if (report[k] !== suite[k]) deny('غلاف القياس لا يطابق هويات المجموعة.');
    return suite;
  }
  async function sha(value, raw = false) {
    const data = new TextEncoder().encode(raw ? value : canonical(value));
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data)), n => n.toString(16).padStart(2, '0')).join('');
  }
  async function verifyIntegrity(suite) {
    validate(suite);
    for (const item of suite.cases) {
      const unsigned = { ...item }; delete unsigned.receipt_sha256;
      if (await sha(unsigned) !== item.receipt_sha256) deny('بصمة إيصال الدعوى لا تطابق محتواه.');
      const execution = item.execution;
      for (const [field, digest] of [['input', 'input_sha256'], ['proposal', 'proposal_sha256'], ['native_result', 'native_result_sha256']]) {
        if (execution[field] !== null && await sha(execution[field]) !== execution[digest]) deny('بصمة مدخل التنفيذ أو نتيجته لا تطابق المحتوى.');
      }
      const sources = execution.input === null ? [] : [...execution.input.active_sources, ...execution.input.interpretations.map(e => e.source)];
      const tuples = new Map();
      for (const source of sources) {
        const digest = await sha(source.content, true);
        tuples.set(canonical([source.identity, source.revision, digest]), source);
      }
      const bindings = new Set();
      for (const b of item.source_bindings) {
        const tuple = canonical([b.identity, b.revision, b.content_sha256]);
        if (!tuples.has(tuple) || bindings.has(tuple)) deny('رابط المصدر لا يطابق سجل المدخل أو يتكرر.');
        if (item.group === 'agency_record') {
          const content = tuples.get(tuple).content;
          let projection; try { projection = JSON.parse(content); } catch { deny('إسقاط الوكالة ليس JSON صالحًا.'); }
          const expected = { pointer: USGS.pointer, revision: USGS.revision, source_sha256: USGS.raw_sha256, value: USGS.value };
          if (!same(projection, expected) || content !== canonical(expected)) deny('إسقاط الحقل لا يطابق السجل والموضع والمراجعة المثبتة.');
        }
        bindings.add(tuple);
      }
      if (bindings.size !== tuples.size) deny('حُذف مصدر من روابط الدعوى.');
    }
    return suite;
  }
  globalThis.NabtEpistemicContract = Object.freeze({ LAW, CATEGORIES, GROUPS, validate, validateEnvelope, verifyIntegrity, canonical });
})();
