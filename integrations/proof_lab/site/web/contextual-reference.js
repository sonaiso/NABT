/* Reference comparisons remain distinct from per-occurrence native receipts. */
'use strict';
(() => {
  const GROUPS = { original_25: 'المرجع الأصلي · ٢٥ حالة محفوظة', independent_20: 'المجموعة المستقلة · ٢٠ حالة منفصلة' };
  const AXES = { syntax: 'صحة التحليل', readings: 'استرجاع القراءات', reference: 'حسم المرجع' };
  const COMPARISONS = { PASS: 'مطابقة المرجع في Python', FAIL: 'مخالفة المرجع في Python', UNMEASURED: 'لم يكتمل القياس', NOT_APPLICABLE: 'خارج مقام المقارنة' };
  const $ = id => document.getElementById(id);
  const text = (id, value) => { $(id).textContent = String(value); };
  const number = n => n.toLocaleString('ar-JO');
  const node = (tag, value, className) => { const el = document.createElement(tag); if (value !== undefined) el.textContent = String(value); if (className) el.className = className; return el; };
  const disclosure = (label, value) => { const element = node('details'), pre = node('pre', JSON.stringify(value, null, 2)); pre.dir = 'ltr'; element.append(node('summary', label), pre); return element; };
  let current = null, liveOrigin = false;
  function reset(message = 'لم يبدأ قياس جديد.') {
    current = null; liveOrigin = false; $('contextual-empty').hidden = false; $('contextual-output').hidden = true; text('contextual-empty-title', message);
    for (const id of ['contextual-group-metrics', 'contextual-cases', 'contextual-case-detail']) $(id).replaceChildren();
    for (const id of ['contextual-scope', 'contextual-run-identity', 'contextual-reference-identity', 'contextual-json']) text(id, '');
  }
  function comparisonCounts(rows) {
    const out = { eligible: 0, measured: 0, passed: 0, failed: 0, unmeasured: 0 };
    for (const item of rows) {
      const status = item.reference_comparison.status;
      if (status === 'NOT_APPLICABLE') continue;
      out.eligible++;
      if (status === 'UNMEASURED') out.unmeasured++;
      else { out.measured++; out[status === 'PASS' ? 'passed' : 'failed']++; }
    }
    return out;
  }
  async function render(report, { live = false } = {}) {
    reset();
    if (!report?.contextual_reference) { text('contextual-empty-title', 'لم يكتمل القياس: ' + String(report?.error || report?.status || 'النتائج غير متاحة')); return; }
    const suite = globalThis.NabtContextualContract.validateEnvelope(report);
    await globalThis.NabtContextualContract.verifyIntegrity(suite);
    current = suite; liveOrigin = live === true; $('contextual-empty').hidden = true; $('contextual-output').hidden = false;
    text('contextual-scope', 'المسار الحالي يفحص الورود الأول في المقام الخارجي. المقارنة بالمرجع في Python مستقلة عن شهادة Lean، وتبقى صحة الجملة كاملة والتواتر وصدق الواقع خارج الدعوى.');
    text('contextual-run-identity', 'الطلب ' + report.request_id + ' · النسخة ' + report.code_sha.slice(0, 12));
    text('contextual-reference-identity', 'المرجع الأصلي: ' + suite.original_reference_sha256 + ' · المرجع المستقل: ' + suite.independent_reference_sha256);
    text('contextual-json', JSON.stringify(report, null, 2));
    for (const [group, title] of Object.entries(GROUPS)) {
      const rows = suite.cases.filter(c => c.group === group), counts = comparisonCounts(rows), card = node('article', undefined, 'card epistemic-group');
      card.append(node('p', title, 'eyebrow'), node('h3', 'مطابقة الإحالة المرجعية'), node('strong', counts.measured ? number(counts.passed) + ' / ' + number(counts.measured) : 'غير مقاس'), node('p', 'مطابق / مقاس · المؤهل: ' + number(counts.eligible)), node('p', 'مخالف: ' + number(counts.failed) + ' · غير مقاس: ' + number(counts.unmeasured), 'field-help'));
      card.append(node('p', 'هذه مقارنة بالتوقع المرجعي في Python. شهادة Lean تفحص الإحالة عند ورود اللفظ ضمن مدخلها، ولا تمنح هذه النسبة برهانًا على فهم الجملة كلها.', 'field-help'));
      if (group === 'original_25') {
        card.append(node('p', 'خط أساس التحليل والقراءات محفوظ كما هو. تبقى محاور الدافع والواقع في المرجع القديم غير مقاسة.', 'field-help'));
        for (const [axis, label] of Object.entries(AXES)) {
          const metric = suite.groups[group].baseline_axes[axis];
          card.append(node('p', 'خط الأساس · ' + label + ': ' + (metric.measured ? number(metric.passed) + ' / ' + number(metric.measured) : 'غير مقاس'), 'field-help'));
        }
      }
      else {
        card.append(node('p', 'هذا مقام اختبار منفصل. تأليفه منفصل إجرائيًا داخل الفريق؛ ليس اختبارًا أعمى خارجيًا. تُبقي الحالات المخالفة والفجوات ظاهرة.', 'field-help'));
        for (const [category, label] of Object.entries({ positive_binding: 'اكتساب إحالة موجبة', alternative_retention: 'حفظ البدائل', safe_nonresolution: 'امتناع آمن فقط' })) {
          const metric = suite.groups[group].metric_categories[category];
          card.append(node('p', label + ': ' + (metric.measured ? number(metric.passed) + ' / ' + number(metric.measured) : 'غير مقاس'), 'field-help'));
        }
      }
      $('contextual-group-metrics').append(card);
    }
    for (const item of suite.cases) {
      const button = node('button', undefined, 'semantic-case-button'); button.type = 'button'; button.dataset.caseId = item.id; button.setAttribute('aria-controls', 'contextual-case-detail'); button.setAttribute('aria-pressed', 'false');
      button.append(node('span', item.id + ' · ' + GROUPS[item.group], 'semantic-case-id'), node('strong', item.input.text), node('span', COMPARISONS[item.reference_comparison.status]));
      button.addEventListener('click', () => select(item.id)); $('contextual-cases').append(button);
    }
    select(suite.cases[0].id);
  }
  function select(id) {
    const item = current?.cases.find(c => c.id === id); if (!item) return;
    for (const button of $('contextual-cases').children) { const active = button.dataset.caseId === id; button.setAttribute('aria-pressed', String(active)); button.classList.toggle('selected', active); }
    const root = $('contextual-case-detail'); root.replaceChildren();
    root.append(node('p', item.id + ' · ' + GROUPS[item.group], 'eyebrow'), node('h3', item.input.text), disclosure('المقام ومدخل الحالة المحفوظ', item.input));
    if (item.baseline_axes) {
      root.append(node('h4', 'خط الأساس المحفوظ · مقارنة Python'));
      for (const [axis, label] of Object.entries(AXES)) root.append(node('p', label + ': ' + COMPARISONS[item.baseline_axes[axis]]));
    }
    root.append(node('h4', 'مقارنة الإحالة بالتوقع المستقل'), node('p', COMPARISONS[item.reference_comparison.status]), disclosure('المتوقع والمرصود وسبب النتيجة', item.reference_comparison));
    renderOccurrences(root, item);
    root.append(node('h4', 'المصادر وحدود الفحص'), disclosure('سجل التنفيذ ومراجع الشواهد والقرائن', item.execution));
    root.append(node('p', 'التواتر غير مقيّم. مطابقة المرشح للفظ في مقام معلن لا تثبت صدق النقل أو الدافع أو الواقع، ولا اكتمال العربية.', 'field-help'));
  }
  function verificationLabel(observation, live = false) {
    if (!live) return 'تصريح مستورد؛ لم يُعد تشغيل Lean';
    if (observation.native_checked !== true || observation.certificate_checked !== true) return 'لا شهادة Lean مقبولة لهذه المحاولة';
    if (observation.status === 'OUT_OF_SCOPE') return 'شهادة Lean بحدود النطاق؛ لم تُحسم الإحالة';
    if (observation.status === 'RESOURCE_LIMIT') return 'شهادة Lean بالتوقف عند حد الموارد';
    if (['NO_LEXICAL_READING', 'UNSUPPORTED_READING', 'OPEN_SCOPE', 'NO_CANDIDATE', 'UNRESOLVED_FEATURES'].includes(observation.status)) return 'شهادة Lean ببقاء الإحالة غير محسومة ضمن هذه المقدمات';
    return 'شهادة Lean مشروطة لهذا الورود ومرشحيه فقط';
  }
  function renderOccurrences(root, item) {
    const observation = item.execution, native = observation.execution, input = native.input;
    root.append(node('h4', 'شهادة إحالة ورود اللفظ'), node('strong', verificationLabel(observation, liveOrigin), liveOrigin && observation.native_checked ? 'contextual-proof' : 'field-help'));
    root.append(node('p', 'لا تفحص هذه الشهادة صحة الجملة كاملة، ولا صحة المقارنة بالتوقع المرجعي، ولا صدق المقام في الواقع.', 'field-help'));
    if (!input) { root.append(node('p', native.error || observation.status)); return; }
    const section = node('section', undefined, 'contextual-occurrence');
    section.append(node('h4', 'اللفظ المفحوص: «' + input.occurrence.surface + '»'), node('p', 'موضع UTF-8: [' + input.occurrence.start_byte + ', ' + input.occurrence.end_byte + ')', 'semantic-case-id'), node('p', 'الحالة: ' + observation.status));
    if (observation.reference) section.append(node('p', 'المرجع المحسوم: ' + (observation.reference.bound_entity_id ?? 'غير محسوم')), node('p', 'كامل المرشحين: ' + (observation.reference.candidate_entity_ids.join(' · ') || 'لا مرشح')));
    section.append(node('p', 'بصمة مدخل Lean: ' + native.input_sha256, 'semantic-case-id'), node('p', 'بصمة إيصال الحالة: ' + observation.receipt_sha256, 'semantic-case-id'));
    section.append(disclosure('كل البدائل المعجمية ونتائجها، دون حذف الغموض', { alternatives: input.alternatives, proposed: native.proposal, native_result: native.native_result }));
    section.append(node('p', 'المصدر: QAC؛ استخراج المقتطفات وتفسير وسومها مقدمات برمجية مستقلة، لا شهادة Lean على صحة النقل الخارجية. أسماء المقام هويات معلنة وليست شواهد معجمية مكتسبة.', 'field-help'));
    section.append(disclosure('مواضع الشواهد وهوياتها وبصماتها', observation.source_bindings), disclosure('نصوص الشواهد المنقولة إلى المدخل', input.donors));
    root.append(section);
  }
  globalThis.NabtContextualReference = Object.freeze({ render, reset, select, comparisonCounts, verificationLabel });
})();
