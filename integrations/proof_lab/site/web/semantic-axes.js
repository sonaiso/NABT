/* Reference-suite display. A measured comparison is never a semantic proof. */
'use strict';
(() => {
  const AXES = Object.freeze({ syntax: 'صحة التحليل', readings: 'استرجاع القراءات', reference: 'حسم المرجع', motive: 'إسناد الدافع', world: 'الخبر في الواقع' });
  const FAMILIES = { nominal_event: 'أسماء وجمل اسمية ذات أحداث', nonvolitional_verb: 'أفعال غير إرادية', temporal_not_causal: 'زمان بلا سببية', context_collision: 'عبارات تتغير مقاماتها', negation_hypothesis_quote: 'نفي وافتراض واقتباس' };
  const REASONS = { EXCLUDED_BY_REFERENCE_SCOPE: 'هذه الحالة مستبعدة من مقام هذا المحور بحسب المرجع.', EXPECTED_ANALYSIS_NOT_RETURNED: 'لم يسترجع التنفيذ التحليل المطلوب في المرجع.', MOTIVE_CAPABILITY_NOT_IMPLEMENTED: 'اكتساب الدافع من دليل مستقل غير منفذ؛ بقي المحور غير مقاس.', REFERENCE_MATCH: 'تطابقت النتيجة المرصودة مع التوقع المرجعي.', REFERENCE_NOT_ACQUIRED_AS_EXPECTED: 'لم تُكتسب الإحالة كما يطلبها المقام المرجعي.', REQUIRED_READING_OR_SELECTION_NOT_RETURNED: 'لم تُسترجع قراءة مطلوبة أو لم يُحفظ الاختيار المرجعي.', RUNTIME_OR_REPLAY_UNAVAILABLE: 'لم يكتمل التنفيذ أو إعادة فحصه؛ لا نتيجة مرجعية مقاسة.', WORLD_VERIFICATION_NOT_IMPLEMENTED: 'التحقق من صدق القضية في الواقع غير منفذ؛ بقي المحور غير مقاس.' };
  const STATUSES = { PASS: 'مطابقة مرجعية', FAIL: 'مخالفة المرجع', UNMEASURED: 'غير مقاس', NOT_APPLICABLE: 'خارج مقام المحور' };
  const own = (v, k) => Object.prototype.hasOwnProperty.call(v, k);
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const digest = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
  const integer = v => Number.isSafeInteger(v) && v >= 0;
  const nonempty = v => typeof v === 'string' && v.trim().length > 0;
  const display = v => typeof v === 'string' ? v : JSON.stringify(v, null, 2);
  const number = v => integer(v) ? v.toLocaleString('ar-JO') : '—';
  function validate(value) {
    const fail = message => { throw new Error('عقد فصل جهات الدلالة: ' + message); };
    if (!object(value) || value.schema !== 'nabt.semantic-axes-benchmark.v1' || !Array.isArray(value.cases) || !object(value.axes)) fail('مخطط غير معروف.');
    if (value.all_arabic_complete !== false || value.lean_native_checked !== false) fail('هذا الإصدار لا يثبت اكتمال العربية ولا يصدر فحص Lean للدعاوى.');
    if (Object.keys(value.axes).some(axis => !own(AXES, axis))) fail('محور خارج المخطط المثبت.');
    if (!integer(value.case_count) || value.case_count !== value.cases.length) fail('عدد الحالات لا يطابق صفوفها.');
    if (!nonempty(value.scope)) fail('نطاق القياس غير معلن.');
    const counted = Object.fromEntries(Object.keys(AXES).map(id => [id, { eligible: 0, measured: 0, passed: 0, failed: 0, unmeasured: 0 }]));
    const ids = new Set();
    for (const item of value.cases) {
      if (!object(item) || !nonempty(item.id) || !nonempty(item.family) || ids.has(item.id) || !nonempty(item.context_id) || !object(item.input) || !nonempty(item.input.text) || !object(item.input.context) || !object(item.axis_results) || !Array.isArray(item.claims)) fail('هوية الحالة أو مقامها أو نتائجها غير صالحة.');
      if (!digest(item.case_input_sha256)) fail('بصمة مدخل الحالة غير صالحة.');
      ids.add(item.id);
      if (Object.keys(item.axis_results).some(axis => !own(AXES, axis))) fail('محور حالة خارج المخطط المثبت.');
      for (const axis of Object.keys(AXES)) {
        const result = item.axis_results[axis];
        if (!object(result) || !own(STATUSES, result.status)) fail('نتيجة محور غير صالحة.');
        if (result.status === 'NOT_APPLICABLE') continue;
        const count = counted[axis]; count.eligible++;
        if (result.status === 'UNMEASURED') count.unmeasured++;
        else { count.measured++; count[result.status === 'PASS' ? 'passed' : 'failed']++; }
      }
      const claims = new Set(), claimAxes = new Set();
      for (const claim of item.claims) {
        if (!object(claim) || !nonempty(claim.id) || claims.has(claim.id) || !own(AXES, claim.axis) || !nonempty(claim.statement) || !own(STATUSES, claim.status) || !object(claim.verification)) fail('هوية الدعوى أو جهة فحصها غير صالحة.');
        if (claim.id !== item.id + ':' + claim.axis || claimAxes.has(claim.axis)) fail('هوية الدعوى لا تطابق الحالة والمحور أو تكرر المحور.');
        claims.add(claim.id); claimAxes.add(claim.axis);
        const verification = claim.verification;
        if (verification.claim_id !== claim.id || verification.input_sha256 !== item.case_input_sha256) fail('هوية الشهادة لا تطابق الدعوى ومدخل الحالة.');
        if (claim.status !== item.axis_results[claim.axis].status || claim.status === 'NOT_APPLICABLE') fail('نتيجة الدعوى تناقض نتيجة محورها.');
        if (!['PYTHON_REPLAY', 'NOT_CHECKED'].includes(verification.kind) || typeof verification.checked !== 'boolean' || !nonempty(verification.scope) || !Array.isArray(verification.theorem_references) || verification.theorem_references.length) fail('هذا الإصدار يقبل إعادة فحص Python أو دعوى غير مفحوصة فقط.');
        const measured = ['PASS', 'FAIL'].includes(claim.status);
        if (measured && !digest(verification.certificate_sha256)) fail('بصمة إيصال المقارنة غير صالحة.');
        if (verification.checked !== measured || verification.kind !== (measured ? 'PYTHON_REPLAY' : 'NOT_CHECKED')) fail('تصريحات فحص الدعوى متناقضة.');
      }
      for (const axis of Object.keys(AXES)) if (item.axis_results[axis].status !== 'NOT_APPLICABLE' && !claimAxes.has(axis)) fail('محور مؤهل بلا دعوى مستقلة.');
    }
    for (const axis of Object.keys(AXES)) {
      const declared = value.axes[axis], actual = counted[axis];
      if (!object(declared) || Object.keys(actual).some(key => !integer(declared[key]) || declared[key] !== actual[key])) fail('مقام محور «' + AXES[axis] + '» لا يطابق الحالات.');
      if (actual.measured === 0 ? declared.rate !== null : typeof declared.rate !== 'number' || !Number.isFinite(declared.rate) || Math.abs(declared.rate - actual.passed / actual.measured) > 1e-12) fail('نسبة المحور لا تطابق المقام المقاس.');
    }
    return value;
  }
  // Version 1 has Python reference comparisons only. Native certificates need a
  // new contract binding each claim, text, context and checked certificate.
  function verificationLabel(claim, options = {}) {
    if (options.imported) return 'تصريح مستورد؛ لم يُعد فحص الدعوى';
    const v = claim?.verification;
    if (v?.kind === 'PYTHON_REPLAY' && v.checked === true) return 'إعادة فحص Python؛ ليست برهان Lean';
    return 'غير مفحوص';
  }
  const $ = id => document.getElementById(id);
  const text = (id, value) => { $(id).textContent = value == null ? '—' : String(value); };
  const node = (tag, content, className) => { const el = document.createElement(tag); if (content !== undefined) el.textContent = String(content); if (className) el.className = className; return el; };
  let selected = null, current = null;
  function reset(message = '') {
    current = null; selected = null;
    $('semantic-output').hidden = true; $('semantic-empty').hidden = false;
    text('semantic-empty-title', message || 'لم يبدأ قياس هذه المجموعة في الجلسة الحالية.');
    for (const id of ['semantic-axis-metrics', 'semantic-cases', 'semantic-case-detail']) $(id).replaceChildren();
  }
  function render(report) {
    reset();
    if (!report.semantic_axes) { text('semantic-empty-title', 'لم يكتمل القياس: ' + String(report.error || report.status || 'النتائج غير متاحة')); return; }
    const suite = validate(report.semantic_axes); current = suite;
    $('semantic-empty').hidden = true; $('semantic-output').hidden = false;
    text('semantic-scope', suite.scope);
    text('semantic-run-identity', 'الطلب ' + report.request_id + ' · النسخة ' + String(report.code_sha || '—').slice(0, 12));
    text('semantic-reference-identity', 'بصمة المرجع: ' + (suite.reference_sha256 || 'غير متاحة'));
    text('semantic-json', JSON.stringify(report, null, 2));
    for (const [axis, label] of Object.entries(AXES)) {
      const count = suite.axes[axis], card = node('article', undefined, 'semantic-axis-card');
      card.append(node('h3', label), node('strong', count.measured ? number(count.passed) + ' / ' + number(count.measured) : 'غير مقاس'),
        node('p', 'مطابق / مقاس · مقام الحالات المؤهلة: ' + number(count.eligible)),
        node('p', 'غير مقاس: ' + number(count.unmeasured) + ' · مخالف: ' + number(count.failed), 'field-help'));
      $('semantic-axis-metrics').append(card);
    }
    for (const item of suite.cases) {
      const button = node('button', undefined, 'semantic-case-button'); button.type = 'button'; button.dataset.caseId = item.id;
      button.setAttribute('aria-controls', 'semantic-case-detail'); button.setAttribute('aria-pressed', 'false');
      button.append(node('span', item.id + ' · ' + item.context_id.slice(0, 12), 'semantic-case-id'), node('strong', item.input.text), node('span', own(FAMILIES, item.family) ? FAMILIES[item.family] : item.family));
      button.addEventListener('click', () => select(item.id)); $('semantic-cases').append(button);
    }
    if (suite.cases.length) select(suite.cases[0].id);
  }
  function select(id) {
    const item = current?.cases.find(row => row.id === id); if (!item) return; selected = id;
    // Preserve the activated button node and keyboard focus while details change.
    for (const button of $('semantic-cases').children) { const active = button.dataset.caseId === selected; button.setAttribute('aria-pressed', String(active)); button.classList.toggle('selected', active); }
    const detail = $('semantic-case-detail'); detail.replaceChildren();
    detail.append(node('p', item.id + ' · مقام ' + item.context_id, 'eyebrow'), node('h3', item.input.text), node('h4', 'المقام المعلن'), node('pre', display(item.input.context), 'semantic-context'));
    if (item.input.query) detail.append(node('p', 'الاستعلام: ' + item.input.query));
    for (const [axis, label] of Object.entries(AXES)) {
      const result = item.axis_results[axis], section = node('section', undefined, 'semantic-axis-result');
      section.append(node('h4', label + ' · ' + STATUSES[result.status]));
      if (result.reason) section.append(node('p', typeof result.reason === 'string' && own(REASONS, result.reason) ? REASONS[result.reason] : display(result.reason), 'field-help'));
      const comparison = node('details'); comparison.append(node('summary', 'التوقع والنتيجة المرصودة'), node('pre', JSON.stringify({ expected: result.expected ?? null, observed: result.observed ?? null }, null, 2)));
      section.append(comparison);
      for (const claim of item.claims.filter(row => row.axis === axis)) {
        const article = node('article', undefined, 'semantic-claim');
        article.append(node('p', claim.id, 'semantic-case-id'), node('p', claim.statement), node('strong', verificationLabel(claim)), node('p', claim.verification.scope || 'لم يعلن نطاق الفحص.', 'field-help'));
        section.append(article);
      }
      detail.append(section);
    }
    if (item.safety_checks || current.safety_checks) { const safety = node('details'); safety.append(node('summary', 'فحوص منع الإسناد غير المرخص — مقام مستقل'), node('pre', JSON.stringify(item.safety_checks || current.safety_checks, null, 2))); detail.append(safety); }
  }
  globalThis.NabtSemanticAxes = Object.freeze({ AXES, STATUSES, validate, verificationLabel, render, reset });
})();
