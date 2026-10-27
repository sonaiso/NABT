/* Shared transport/import contract. Hash integrity does not authenticate imports. */
'use strict';
(() => {
  const LAW = 'nabt.initial-contextual-reference.v1';
  const QAC_SHA = 'a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46';
  const QAC_BYTES = 6309503;
  const STATES = ['RESOLVED', 'AMBIGUOUS', 'NO_CANDIDATE', 'UNRESOLVED_FEATURES', 'OPEN_SCOPE', 'UNSUPPORTED_READING', 'NO_LEXICAL_READING', 'OUT_OF_SCOPE', 'RESOURCE_LIMIT'];
  const AXES = ['syntax', 'readings', 'reference'];
  const CATEGORIES = ['positive_binding', 'alternative_retention', 'safe_nonresolution'];
  const DIGESTS = ['original_reference_sha256', 'independent_reference_sha256', 'baseline_source_sha256', 'scorer_sha256', 'source_registry_sha256', 'runtime_sha256'];
  const PROFILE_CODES = ['1S', '1P', '2MS', '2MD', '2MP', '2FS', '2FD', '2FP', '3MS', '3MD', '3MP', '3FS', '3FD', '3FP'];
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const own = (v, k) => Object.prototype.hasOwnProperty.call(v, k);
  const integer = v => Number.isSafeInteger(v) && v >= 0;
  const hash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
  const text = v => typeof v === 'string' && v.trim().length > 0;
  const encoder = new TextEncoder(), decoder = new TextDecoder('utf-8', { fatal: true });
  const deny = message => { throw new Error('عقد إحالة اللفظ والمقام: ' + message); };
  function exact(value, keys) { if (!object(value) || Object.keys(value).length !== keys.length || keys.some(k => !own(value, k))) deny('حقول تخالف المخطط المثبت.'); }
  function allowed(value, keys, required = []) { if (!object(value) || Object.keys(value).some(k => !keys.includes(k)) || required.some(k => !own(value, k))) deny('حقول زائدة أو مفقودة.'); }
  function canonical(value) { return Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']' : object(value) ? '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}' : JSON.stringify(value); }
  const same = (a, b) => canonical(a) === canonical(b);
  async function sha(value, raw = false) { const bytes = encoder.encode(raw ? value : canonical(value)); return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(n => n.toString(16).padStart(2, '0')).join(''); }
  function label(v) { if (!text(v) || encoder.encode(v).length > 4096 || /[\u0000-\u001f]/.test(v)) deny('هوية أو عبارة غير صالحة.'); }
  function names(v, maximum = 256) { if (!Array.isArray(v) || v.length > maximum || new Set(v).size !== v.length) deny('قائمة هويات غير صالحة أو مكررة.'); v.forEach(label); }
  function span(v, maximum) { exact(v, ['start', 'end']); if (!integer(v.start) || !integer(v.end) || v.start > v.end || v.end > maximum) deny('حدود الموضع غير صالحة.'); }
  function contextForm(value) { if (typeof value !== 'string' || encoder.encode(value).length > 256 || spellingClusters(value) === null) deny('صيغة مقام غير صالحة.'); }
  function normalizeContext(raw) {
    allowed(raw, ['entities', 'speaker', 'addressee', 'deixis', 'closed_reference_scope']);
    const entities = own(raw, 'entities') ? raw.entities : [], deixis = own(raw, 'deixis') ? raw.deixis : [];
    const out = { entities: [], deixis: [], closed_reference_scope: own(raw, 'closed_reference_scope') ? raw.closed_reference_scope : false };
    if (encoder.encode(canonical(raw)).length > 65536 || typeof out.closed_reference_scope !== 'boolean' || !Array.isArray(entities) || entities.length > 64 || !Array.isArray(deixis) || deixis.length > 64) deny('مقام الإحالة غير صالح.');
    const ids = new Set();
    for (const e of entities) {
      allowed(e, ['id', 'name', 'gender', 'number', 'kind'], ['id', 'name']); label(e.id); contextForm(e.name);
      if (!/^[a-z][a-z0-9_]{0,63}$/.test(e.id) || ids.has(e.id)) deny('هوية كيان غير صالحة أو مكررة.'); ids.add(e.id);
      const item = { id: e.id, name: e.name, gender: own(e, 'gender') ? e.gender : 'unknown', number: own(e, 'number') ? e.number : 'unknown', kind: own(e, 'kind') ? e.kind : 'unknown' };
      if (!['masculine', 'feminine', 'unknown'].includes(item.gender) || !['singular', 'dual', 'plural', 'unknown'].includes(item.number) || !['person', 'place', 'thing', 'unknown'].includes(item.kind)) deny('سمات مقام غير معروفة.');
      out.entities.push(item);
    }
    for (const role of ['speaker', 'addressee']) if (own(raw, role)) { if (!ids.has(raw[role])) deny('المشارك غير مسجل في المقام.'); out[role] = raw[role]; }
    for (const d of deixis) { exact(d, ['form', 'entity_ids']); contextForm(d.form); names(d.entity_ids, 64); if (d.entity_ids.length === 0 || d.entity_ids.some(id => !ids.has(id))) deny('إشارة إلى مرجع غير مسجل.'); out.deixis.push(d); }
    return out;
  }
  function receipt(v, ids, withReadings = true) {
    exact(v, withReadings ? ['status', 'reading_ids', 'candidate_entity_ids', 'bound_entity_id', 'reading_results'] : ['id', 'status', 'candidate_entity_ids', 'bound_entity_id']);
    if (!STATES.includes(v.status)) deny('حالة إحالة غير معروفة.'); names(v.candidate_entity_ids, 64);
    if (v.candidate_entity_ids.some(id => !ids.includes(id))) deny('مرشح خارج المقام.');
    if (!same(v.candidate_entity_ids, ids.filter(id => v.candidate_entity_ids.includes(id)))) deny('ترتيب المرشحين يختلف عن سجل المقام.');
    if (v.status === 'RESOLVED' ? v.candidate_entity_ids.length !== 1 || v.bound_entity_id !== v.candidate_entity_ids[0] : v.bound_entity_id !== null) deny('المرجع المحسوم يناقض حالة الإحالة.');
    if (v.status === 'AMBIGUOUS' && v.candidate_entity_ids.length === 0) deny('غموض بلا بدائل.');
    if (['NO_CANDIDATE', 'RESOURCE_LIMIT', 'OUT_OF_SCOPE', 'NO_LEXICAL_READING'].includes(v.status) && v.candidate_entity_ids.length !== 0) deny('حالة فارغة تحمل مرشحين.');
    if (withReadings) {
      names(v.reading_ids, 64);
      if (!Array.isArray(v.reading_results) || v.reading_results.length > 64) deny('نتائج القراءات غير صالحة.');
      v.reading_results.forEach(r => { label(r.id); receipt(r, ids, false); });
      if (!same(v.reading_ids, v.reading_results.map(r => r.id))) deny('حُذفت قراءة أو تغير ترتيبها.');
    } else label(v.id);
  }
  function nativeInput(v, outer) {
    exact(v, ['source', 'occurrence', 'context', 'donors', 'alternatives', 'budget', 'proposed']);
    exact(v.source, ['id', 'revision', 'text']); label(v.source.id); label(v.source.revision);
    if (v.source.id !== 'contextual_reference_input' || !hash(v.source.revision)) deny('هوية نص Lean غير صالحة.');
    if (v.source.text !== outer.input.text || encoder.encode(v.source.text).length > 65536) deny('نص Lean لا يطابق النص الأصلي.');
    exact(v.occurrence, ['start_byte', 'end_byte', 'surface']);
    const bytes = encoder.encode(v.source.text), o = v.occurrence;
    if (!integer(o.start_byte) || !integer(o.end_byte) || o.start_byte > o.end_byte || o.end_byte > bytes.length || !text(o.surface)) deny('حدود بايتات اللفظ غير صالحة.');
    try { if (decoder.decode(bytes.slice(o.start_byte, o.end_byte)) !== o.surface) deny('اللفظ لا يطابق موضعه.'); } catch { deny('موضع لا يحفظ ترميز UTF-8.'); }
    exact(v.context, ['entities', 'speaker', 'addressee', 'deixis', 'closed_reference_scope']);
    const context = normalizeContext(outer.input.context), normalized = { ...context, speaker: context.speaker ?? null, addressee: context.addressee ?? null };
    if (!same(v.context, normalized)) deny('المقام المفحوص يختلف عن مقام الطلب.');
    if (!integer(v.budget) || v.budget > 256 || !Array.isArray(v.donors) || v.donors.length > 256 || !Array.isArray(v.alternatives) || v.alternatives.length > 64) deny('تجاوز حدود دفتر الإحالة.');
    const donorIds = new Set();
    for (const donor of v.donors) {
      exact(donor, ['id', 'source_id', 'source_revision', 'start_byte', 'end_byte', 'record']); label(donor.id); label(donor.source_id); label(donor.source_revision);
      if (donorIds.has(donor.id) || !integer(donor.start_byte) || !integer(donor.end_byte) || donor.start_byte >= donor.end_byte || donor.end_byte > QAC_BYTES || !text(donor.record) || encoder.encode(donor.record).length > 4096 || encoder.encode(donor.record).length !== donor.end_byte - donor.start_byte) deny('سجل شاهد غير صالح.');
      donorIds.add(donor.id);
    }
    const ids = new Set();
    for (const alt of v.alternatives) {
      exact(alt, ['id', 'pos', 'profile_code', 'target_surface', 'source_form', 'donor_ids']); label(alt.id); label(alt.target_surface); label(alt.source_form); names(alt.donor_ids, 256);
      if (ids.has(alt.id) || !['PRON', 'DEM', 'OTHER'].includes(alt.pos) || (alt.profile_code !== null && !PROFILE_CODES.includes(alt.profile_code)) || alt.donor_ids.some(id => !donorIds.has(id))) deny('بديل معجمي غير صالح.');
      ids.add(alt.id);
    }
    receipt(v.proposed, v.context.entities.map(e => e.id));
    if (v.proposed.reading_ids.some(id => !ids.has(id))) deny('الشهادة تحيل إلى قراءة غير مدخلة.');
  }
  // Mirrors qac.initial-reference-observed-spelling.v1. This replays a declared
  // spelling policy; it does not authenticate the quoted corpus or its analysis.
  const bwLetters = Array.from("'>&<}AbptvjHxd*rzs$SDTZEgfqklmnhwYyFNKaui~o^#`{");
  const bwArabic = Array.from('ءأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىيًٌٍَُِّْٰٓٔٱ');
  const buckwalter = new Map(bwLetters.map((letter, i) => [letter, bwArabic[i]]).concat([
    [':', '\u06dc'], ['@', '\u06df'], ['"', '\u06e0'], ['[', '\u06e2'], [';', '\u06e3'],
    [',', '\u06e5'], ['.', '\u06e6'], ['!', '\u06e8'], ['-', '\u06ea'], ['+', '\u06eb'],
    ['%', '\u06ec'], [']', '\u06ed'], ['_', 'ـ'], [' ', ' ']
  ]));
  function decodeBuckwalter(value) {
    const letters = Array.from(value);
    return letters.every(c => buckwalter.has(c)) ? letters.map(c => buckwalter.get(c)).join('') : null;
  }
  function spellingClusters(value) {
    const clusters = [];
    for (const c of value) {
      if ('ًٌٍَُِّْٰ'.includes(c)) {
        const previous = clusters.at(-1);
        if (!previous || previous.marks.includes(c) || ('ًٌٍَُِْ'.includes(c) && previous.marks.some(m => 'ًٌٍَُِْ'.includes(m)))) return null;
        previous.marks.push(c);
      } else if (/[\u0621-\u063a\u0641-\u064aٱ]/u.test(c)) clusters.push({ carrier: c === 'ٱ' ? 'ا' : c, marks: [] });
      else return null;
    }
    return clusters.length ? clusters : null;
  }
  function surfaceCompatible(observed, expected) {
    const a = spellingClusters(observed), b = spellingClusters(expected);
    return a !== null && b !== null && a.length === b.length && a.every((left, i) => {
      const right = b[i];
      return left.carrier === right.carrier && left.marks.filter(c => 'ًٌٍَُِْ'.includes(c)).every(c => !right.marks.some(m => 'ًٌٍَُِْ'.includes(m)) || right.marks.includes(c)) &&
        (!left.marks.includes('ّ') || right.marks.includes('ّ')) && (!left.marks.includes('ٰ') || right.marks.includes('ٰ'));
    });
  }
  function expectedNativeReceipt(input) {
    const { source, occurrence, context, alternatives, donors, budget } = input;
    const bytes = encoder.encode(source.text), prefix = bytes.slice(0, occurrence.start_byte), suffix = decoder.decode(bytes.slice(occurrence.end_byte));
    const empty = status => ({ status, reading_ids: [], candidate_entity_ids: [], bound_entity_id: null, reading_results: [] });
    if (![...prefix].every(b => [9, 10, 13, 32].includes(b)) || (suffix && ![' ', '\t', '\r', '\n', '.', ',', '!', '?', ':', ';', '،', '؛', '؟'].some(mark => suffix.startsWith(mark)))) return empty('OUT_OF_SCOPE');
    if (alternatives.length + context.entities.length > budget) return empty('RESOURCE_LIMIT');
    if (alternatives.length === 0) return empty('NO_LEXICAL_READING');
    const profiles = code => code === null ? null : { person: Number(code[0]), gender: code.includes('M') ? 'masculine' : code.includes('F') ? 'feminine' : null, number: ({ S: 'singular', D: 'dual', P: 'plural' })[code.slice(-1)] };
    const rows = alternatives.map(a => {
      const p = profiles(a.profile_code);
      const origin = p && a.pos === 'PRON' && p.person === 1 ? 'speaker' : p && a.pos === 'PRON' && p.person === 2 ? 'addressee' : p && a.pos === 'DEM' && p.person === 3 ? 'deixis' : null;
      const supported = a.target_surface === occurrence.surface && a.source_form.length > 0 && a.donor_ids.length > 0 && origin !== null && a.donor_ids.every(id => {
        const d = donors.find(row => row.id === id); if (!d) return false;
        const fields = d.record.replace(/^[ \t\r\n\v\f]+|[ \t\r\n\v\f]+$/g, '').split('\t');
        return fields.length === 4 && decodeBuckwalter(fields[1]) === a.source_form && surfaceCompatible(a.target_surface, a.source_form) && fields[2] === a.pos && fields[3].split('|').includes('POS:' + a.pos) && fields[3].split('|').includes(a.pos === 'DEM' ? a.profile_code.slice(1) : a.profile_code);
      });
      const candidates = supported ? context.entities.filter(e =>
        (origin === 'deixis' ? context.deixis.some(d => d.form === occurrence.surface && d.entity_ids.includes(e.id)) : context[origin] === e.id) &&
        (!p.gender || e.gender === 'unknown' || e.gender === p.gender) && (e.number === 'unknown' || e.number === p.number)).map(e => e.id) : [];
      const confirmed = supported && candidates.every(id => { const e = context.entities.find(row => row.id === id); return (!p.gender || e.gender === p.gender) && e.number === p.number; });
      const status = !supported ? 'UNSUPPORTED_READING' : !context.closed_reference_scope ? 'OPEN_SCOPE' : candidates.length === 0 ? 'NO_CANDIDATE' : candidates.length === 1 && !confirmed ? 'UNRESOLVED_FEATURES' : candidates.length === 1 ? 'RESOLVED' : 'AMBIGUOUS';
      return { id: a.id, status, candidate_entity_ids: candidates, bound_entity_id: status === 'RESOLVED' ? candidates[0] : null };
    });
    const candidates = context.entities.filter(e => rows.some(r => r.candidate_entity_ids.includes(e.id))).map(e => e.id);
    const agreed = rows[0].bound_entity_id !== null && rows.every(r => r.status === 'RESOLVED' && r.bound_entity_id === rows[0].bound_entity_id);
    const status = rows.some(r => r.status === 'UNSUPPORTED_READING') ? 'UNSUPPORTED_READING' : !context.closed_reference_scope ? 'OPEN_SCOPE' : candidates.length === 0 ? 'NO_CANDIDATE' : rows.some(r => r.status === 'UNRESOLVED_FEATURES') ? 'UNRESOLVED_FEATURES' : agreed ? 'RESOLVED' : 'AMBIGUOUS';
    return { status, reading_ids: rows.map(r => r.id), candidate_entity_ids: candidates, bound_entity_id: status === 'RESOLVED' ? rows[0].bound_entity_id : null, reading_results: rows };
  }
  function nativeResult(v, input) {
    const flags = ['whole_clause_checked', 'world_truth_established', 'motive_established', 'all_arabic_complete'];
    if (!object(v) || v.law_id !== LAW || flags.some(k => v[k] !== false)) deny('ترقية غير مرخصة في نتيجة Lean.');
    if (own(v, 'reason')) {
      exact(v, ['law_id', 'status', 'reason', ...flags]);
      if (!['INVALID_INPUT', 'RESOURCE_LIMIT'].includes(v.status) || !text(v.reason)) deny('إيصال تعذر Lean غير صالح.');
      return;
    }
    exact(v, ['law_id', 'status', 'observed_status', 'reading_ids', 'candidate_entity_ids', 'bound_entity_id', 'reading_results', 'certificate_checked', ...flags]);
    if (typeof v.certificate_checked !== 'boolean' || ![...STATES, 'INVALID_CERTIFICATE'].includes(v.status)) deny('نتيجة تحقق غير صالحة.');
    receipt({ status: v.observed_status, reading_ids: v.reading_ids, candidate_entity_ids: v.candidate_entity_ids, bound_entity_id: v.bound_entity_id, reading_results: v.reading_results }, input.context.entities.map(e => e.id));
    if (v.certificate_checked ? v.status !== v.observed_status : v.status !== 'INVALID_CERTIFICATE') deny('تصريحات التحقق متناقضة.');
  }
  function execution(value, item, suite) {
    exact(value, ['schema', 'law_id', 'status', 'native_checked', 'certificate_checked', 'reference', 'input', 'input_sha256', 'context_sha256', 'lexical_source_sha256', 'source_registry_sha256', 'runtime_sha256', 'native_sha256', 'source_bindings', 'scope', 'execution', 'receipt_sha256']);
    if (value.schema !== 'nabt.contextual-reference-observation.v1' || value.law_id !== LAW || typeof value.native_checked !== 'boolean' || value.certificate_checked !== value.native_checked || !same(value.input, item.input) || value.input_sha256 !== item.input_sha256 || !hash(value.context_sha256) || value.lexical_source_sha256 !== QAC_SHA || !hash(value.receipt_sha256)) deny('هوية رصد الإحالة لا تطابق الحالة.');
    for (const k of ['source_registry_sha256', 'runtime_sha256', 'native_sha256']) if (value[k] !== suite[k]) deny('إصدار رصد الإحالة يختلف عن المجموعة.');
    const scope = value.scope;
    exact(scope, ['reference', 'source_acquisition', 'typed_annotation_interpretation', 'lexical_inventory', 'sentence_syntax_promoted', 'sentence_readings_promoted', 'context_truth_established', 'world_truth_established', 'hidden_motive_established', 'whole_arabic_complete', 'tawatur_status']);
    if (scope.reference !== 'INITIAL_SOURCE_ATTESTED_OCCURRENCE_WITH_EXPLICIT_CONTEXT' || scope.source_acquisition !== 'PYTHON_PINNED_RAW_SOURCE_REPLAY' || scope.typed_annotation_interpretation !== 'DECLARED_PREMISE_NOT_PROVED_BY_LEAN' || scope.lexical_inventory !== 'ALL_SOURCE_BACKED_PERSON_BRIDGE_ALTERNATIVES_FOR_EXACT_SURFACE' || scope.tawatur_status !== 'UNKNOWN' || ['sentence_syntax_promoted', 'sentence_readings_promoted', 'context_truth_established', 'world_truth_established', 'hidden_motive_established', 'whole_arabic_complete'].some(k => scope[k] !== false)) deny('حدود الرصد تتضمن سلطة غير مثبتة.');
    const e = value.execution;
    exact(e, ['input', 'input_sha256', 'proposal', 'proposal_sha256', 'native_result', 'native_result_sha256', 'native_sha256', 'error']);
    if (e.input !== null) { nativeInput(e.input, value); if (!same(e.proposal, e.input.proposed) || !hash(e.input_sha256) || !hash(e.proposal_sha256)) deny('اقتراح الشهادة لا يطابق مدخل Lean.'); }
    else if (e.input_sha256 !== null || e.proposal !== null || e.proposal_sha256 !== null || e.native_result !== null || value.native_checked) deny('تعذر الإدخال يخفي نتيجة تحقق.');
    if (e.native_result !== null) { if (e.input === null || !hash(e.native_result_sha256)) deny('نتيجة Lean بلا مدخل.'); nativeResult(e.native_result, e.input); }
    else if (e.native_result_sha256 !== null) deny('بصمة نتيجة غائبة.');
    if (e.native_sha256 !== null && e.native_sha256 !== suite.native_sha256) deny('منفذ Lean يختلف عن النسخة المعلنة.');
    if (value.native_checked) {
      const r = e.native_result;
      if (!hash(suite.native_sha256) || e.native_sha256 !== suite.native_sha256 || e.error !== null || r?.certificate_checked !== true || value.status !== r.observed_status) deny('لا توجد شهادة مقبولة توافق حالة الرصد.');
      if (!same(e.proposal, { status: r.observed_status, reading_ids: r.reading_ids, candidate_entity_ids: r.candidate_entity_ids, bound_entity_id: r.bound_entity_id, reading_results: r.reading_results })) deny('قراءات الشهادة أو مرشحوها لا يطابقون Lean.');
      if (!same(e.proposal, expectedNativeReceipt(e.input))) deny('المرشحون أو الشهادة لا يطابقون كامل دفتر القراءات والمقام.');
      if (!['OUT_OF_SCOPE', 'RESOURCE_LIMIT'].includes(r.observed_status) && !same(r.reading_ids, e.input.alternatives.map(a => a.id))) deny('قائمة القراءات المفحوصة غير كاملة.');
    } else if (!['UNMEASURED', 'INVALID_INPUT', 'RESOURCE_LIMIT', 'OUT_OF_SCOPE'].includes(value.status) || value.reference !== null || e.error === null || !text(e.error) || e.native_result?.certificate_checked === true) deny('تعذر التحقق يناقض الرتبة المعروضة.');
    if (value.reference !== null) {
      const r = value.reference, result = e.native_result;
      exact(r, ['surface', 'status', 'candidate_entity_ids', 'bound_entity_id', 'reference_id', 'span', 'scope', 'occurrence']);
      if (!value.native_checked || !['RESOLVED', 'AMBIGUOUS', 'NO_CANDIDATE'].includes(r.status) || r.status !== value.status || r.scope !== 'outer' || r.occurrence !== 0 || !hash(r.reference_id) || !same(r.candidate_entity_ids, result.candidate_entity_ids) || r.bound_entity_id !== result.bound_entity_id) deny('إحالة معروضة بلا نتيجة مطابقة.');
      span(r.span, Array.from(item.input.text).length);
      if (Array.from(item.input.text).slice(r.span.start, r.span.end).join('') !== r.surface || r.surface !== e.input.occurrence.surface || encoder.encode(Array.from(item.input.text).slice(0, r.span.start).join('')).length !== e.input.occurrence.start_byte || encoder.encode(Array.from(item.input.text).slice(0, r.span.end).join('')).length !== e.input.occurrence.end_byte) deny('اللفظ أو الموضع المعروض يختلف عن المدخل.');
    } else if (value.native_checked && ['RESOLVED', 'AMBIGUOUS', 'NO_CANDIDATE'].includes(value.status)) deny('إحالة مفحوصة مفقودة.');
    if (!Array.isArray(value.source_bindings)) deny('شواهد المصدر غير صالحة.');
    const donors = e.input?.donors ?? [];
    if (value.source_bindings.length !== donors.length) deny('حُذف شاهد من سجل الإحالة.');
    for (let i = 0; i < donors.length; i++) {
      const b = value.source_bindings[i], d = donors[i]; exact(b, ['id', 'source_id', 'source_sha256', 'byte_start', 'byte_end', 'content_sha256', 'locator']);
      if (b.id !== d.id || b.source_id !== d.source_id || b.source_id !== 'qac_attested_source_v1' || b.source_sha256 !== QAC_SHA || d.source_revision !== QAC_SHA || b.byte_start !== d.start_byte || b.byte_end !== d.end_byte || !hash(b.content_sha256) || !Array.isArray(b.locator) || b.locator.length !== 4 || b.locator.some(n => !integer(n) || n === 0) || d.record.split('\t')[0] !== '(' + b.locator.join(':') + ')' ) deny('شاهد النقل لا يطابق مدخل Lean.');
    }
  }
  function gold(v) {
    allowed(v, ['status', 'surface', 'target_ids', 'span', 'scope', 'occurrence'], ['status', 'target_ids']); names(v.target_ids, 64);
    if (!['resolved', 'ambiguous', 'unresolved', 'not_applicable'].includes(v.status)) deny('توقع مرجعي غير معروف.');
    if (v.status !== 'not_applicable' && !text(v.surface)) deny('التوقع بلا لفظ.');
    if (own(v, 'span')) span(v.span, 65536);
    if (own(v, 'scope') && !text(v.scope)) deny('مقام متوقع غير صالح.');
    if (own(v, 'occurrence') && !integer(v.occurrence)) deny('رقم ورود غير صحيح.');
  }
  function compare(expected, observed, checked) {
    if (expected.status === 'not_applicable') return { status: 'NOT_APPLICABLE', reason: 'EXCLUDED_BY_ORIGINAL_REFERENCE_SCOPE' };
    if (!checked) return { status: 'UNMEASURED', reason: 'NATIVE_REFERENCE_CHECK_UNAVAILABLE' };
    if (observed === null) return { status: 'FAIL', reason: 'TARGET_OCCURRENCE_OUTSIDE_EXECUTED_REFERENCE_SCOPE' };
    let equal = observed.surface === expected.surface && (!own(expected, 'span') || same(observed.span, expected.span)) && (!own(expected, 'scope') || expected.scope === 'outer') && (!own(expected, 'occurrence') || expected.occurrence === 0);
    const wanted = expected.target_ids, candidates = observed.candidate_entity_ids;
    if (expected.status === 'resolved') equal = equal && wanted.length === 1 && same([...candidates].sort(), [...wanted].sort()) && observed.bound_entity_id === wanted[0] && observed.status === 'RESOLVED';
    else if (expected.status === 'ambiguous') equal = equal && wanted.length > 1 && same([...candidates].sort(), [...wanted].sort()) && observed.bound_entity_id === null && observed.status === 'AMBIGUOUS';
    else if (expected.status === 'unresolved') equal = equal && candidates.length === 0 && wanted.length === 0 && observed.bound_entity_id === null && observed.status === 'NO_CANDIDATE';
    else equal = false;
    return { status: equal ? 'PASS' : 'FAIL', reason: equal ? 'REFERENCE_MATCH' : 'REFERENCE_NOT_ACQUIRED_AS_EXPECTED' };
  }
  function metric(statuses) { const out = { eligible: 0, measured: 0, passed: 0, failed: 0, unmeasured: 0 }; for (const status of statuses) { if (!['PASS', 'FAIL', 'UNMEASURED', 'NOT_APPLICABLE'].includes(status)) deny('نتيجة مقارنة غير معروفة.'); if (status === 'NOT_APPLICABLE') continue; out.eligible++; if (status === 'UNMEASURED') out.unmeasured++; else { out.measured++; out[status === 'PASS' ? 'passed' : 'failed']++; } } return out; }
  function validate(suite) {
    exact(suite, ['schema', 'law_id', ...DIGESTS, 'native_sha256', 'groups', 'cases', 'all_cases_native_checked', 'scope', 'whole_arabic_complete', 'tawatur_evaluated', 'world_truth_established', 'motive_measured']);
    if (suite.schema !== 'nabt.contextual-reference-benchmark.v1' || suite.law_id !== LAW || DIGESTS.some(k => !hash(suite[k])) || (suite.native_sha256 !== null && !hash(suite.native_sha256)) || typeof suite.all_cases_native_checked !== 'boolean' || !Array.isArray(suite.cases) || suite.cases.length !== 45) deny('هوية مجموعة الإحالة أو مقامها غير صالح.');
    if (['whole_arabic_complete', 'tawatur_evaluated', 'world_truth_established', 'motive_measured'].some(k => suite[k] !== false)) deny('تجاوز نطاق القياس.');
    exact(suite.scope, ['reference', 'comparison', 'native', 'original_syntax_and_readings', 'sources', 'independent_reference']);
    if (!same(suite.scope, { reference: 'INITIAL_OCCURRENCE_ONLY', comparison: 'PYTHON_REFERENCE_COMPARISON', native: 'CONDITIONAL_REFERENCE_CERTIFICATE_NOT_GOLD_OR_FULL_SENTENCE_PROOF', original_syntax_and_readings: 'UNCHANGED_ATTESTED_QAC_PYTHON_REPLAY', sources: 'PINNED_SOURCE_ANNOTATIONS_AND_DECLARED_CONTEXT_PREMISES', independent_reference: 'AUTHORED_DIAGNOSTIC_NOT_EXTERNAL_BLIND_HOLDOUT' })) deny('وصف نطاق المجموعة غير مرخص.');
    exact(suite.groups, ['original_25', 'independent_20']); const ids = new Set();
    for (const item of suite.cases) {
      exact(item, ['id', 'group', 'input', 'input_sha256', 'metric_category', 'expected_reference', 'baseline_axes', 'reference_comparison', 'execution']);
      if (!text(item.id) || ids.has(item.id) || !['original_25', 'independent_20'].includes(item.group) || !hash(item.input_sha256) || ![...CATEGORIES, 'not_applicable'].includes(item.metric_category)) deny('هوية حالة أو مقام غير صالح.'); ids.add(item.id);
      exact(item.input, ['text', 'context']); if (!text(item.input.text) || encoder.encode(canonical(item.input)).length > 65536) deny('النص غير صالح.'); normalizeContext(item.input.context); gold(item.expected_reference);
      execution(item.execution, item, suite);
      if (item.group === 'original_25') { exact(item.baseline_axes, AXES); AXES.forEach(a => metric([item.baseline_axes[a]])); } else if (item.baseline_axes !== null) deny('إضافة خط أساس غير مقاس للمجموعة المستقلة.');
      const category = { resolved: 'positive_binding', ambiguous: 'alternative_retention', unresolved: 'safe_nonresolution', not_applicable: 'not_applicable' }[item.expected_reference.status];
      if (item.metric_category !== category) deny('خلط مقام اكتساب الإحالة بمقام الامتناع.');
      const c = item.reference_comparison; exact(c, ['status', 'expected', 'observed', 'reason']);
      if (!same(c.expected, item.expected_reference) || !same(c.observed, item.execution.reference) || !same({ status: c.status, reason: c.reason }, compare(c.expected, c.observed, item.execution.native_checked))) deny('المقارنة لا تطابق التوقع والمرصود.');
    }
    if (suite.all_cases_native_checked !== suite.cases.every(r => r.execution.native_checked && r.execution.certificate_checked)) deny('رتبة المجموعة تناقض رتب الحالات.');
    for (const group of ['original_25', 'independent_20']) {
      const rows = suite.cases.filter(r => r.group === group), g = suite.groups[group];
      exact(g, group === 'original_25' ? ['case_count', 'reference_after', 'baseline_axes'] : ['case_count', 'reference_after', 'metric_categories']);
      if (g.case_count !== (group === 'original_25' ? 25 : 20) || rows.length !== g.case_count) deny('المقام لا يطابق صفوفه.');
      const pairs = [[g.reference_after, metric(rows.map(r => r.reference_comparison.status))]];
      if (group === 'original_25') { exact(g.baseline_axes, AXES); AXES.forEach(a => pairs.push([g.baseline_axes[a], metric(rows.map(r => r.baseline_axes[a]))])); }
      else { exact(g.metric_categories, CATEGORIES); CATEGORIES.forEach(c => pairs.push([g.metric_categories[c], metric(rows.filter(r => r.metric_category === c).map(r => r.reference_comparison.status))])); }
      for (const [declared, actual] of pairs) { exact(declared, ['eligible', 'measured', 'passed', 'failed', 'unmeasured']); if (Object.values(declared).some(n => !integer(n)) || !same(declared, actual)) deny('مقاييس لا تتفق مع الحالات.'); }
    }
    return suite;
  }
  function validateEnvelope(report) {
    allowed(report, ['schema', 'request_id', 'payload_sha256', 'code_sha', 'native_sha256', 'generated_at_utc', 'duration_ms', 'mode', 'status', 'all_arabic_complete', 'world_truth_established', 'scope', 'law_id', ...DIGESTS, 'runner_sha256', 'measurement_source_sha256', 'toolchain', 'contextual_reference']);
    if (report.schema !== 'nabt.proof-lab-result.v1' || report.mode !== 'contextual_reference' || report.status !== 'CONTEXTUAL_REFERENCE_COMPLETE' || report.all_arabic_complete !== false || report.world_truth_established !== false) deny('غلاف الإحالة غير صالح.');
    if (own(report, 'law_id') && report.law_id !== LAW) deny('قانون الغلاف يختلف عن الشهادة.');
    if (own(report, 'scope') && !same(report.scope, { law_id: LAW, claim: 'Source-bound initial-occurrence reference relative to declared context', verification_kind: 'NATIVE_REFERENCE_RECEIPT_AND_PYTHON_GOLD_COMPARISON', whole_clause: 'NOT_PROVED', whole_arabic: 'NOT_PROVED', external_world: 'NOT_VERIFIED', tawatur: 'NOT_EVALUATED' })) deny('غلاف يتجاوز حدود الشهادة.');
    const suite = validate(report.contextual_reference);
    for (const k of [...DIGESTS, 'native_sha256']) if (report[k] !== suite[k]) deny('هوية الغلاف لا تطابق المجموعة.');
    return suite;
  }
  async function verifyIntegrity(suite) {
    validate(suite);
    for (const item of suite.cases) {
      const observation = item.execution, e = observation.execution;
      if (await sha(item.input) !== item.input_sha256 || await sha(item.input.context) !== observation.context_sha256) deny('بصمة النص أو المقام لا تطابق المحتوى.');
      const unsigned = { ...observation }; delete unsigned.receipt_sha256;
      if (await sha(unsigned) !== observation.receipt_sha256) deny('بصمة رصد الإحالة لا تطابق محتواه.');
      if (e.input !== null && await sha(e.input.source.text, true) !== e.input.source.revision) deny('مراجعة النص لا تطابق بايتاته.');
      for (const [field, digest] of [['input', 'input_sha256'], ['proposal', 'proposal_sha256'], ['native_result', 'native_result_sha256']]) if (e[field] !== null && await sha(e[field]) !== e[digest]) deny('بصمة مدخل Lean أو شهادته أو نتيجته لا تتفق.');
      if (observation.reference !== null) { const ref = { ...observation.reference }; delete ref.reference_id; if (await sha(ref) !== observation.reference.reference_id) deny('بصمة الإحالة غير مطابقة.'); }
      for (let i = 0; i < observation.source_bindings.length; i++) if (await sha(e.input.donors[i].record, true) !== observation.source_bindings[i].content_sha256) deny('مقتطف الشاهد لا يطابق بصمته.');
    }
    return suite;
  }
  globalThis.NabtContextualContract = Object.freeze({ LAW, validate, validateEnvelope, verifyIntegrity, canonical, normalizeContext, compare });
})();
