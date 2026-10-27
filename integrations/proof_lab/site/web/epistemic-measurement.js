/* Live display of exact evidence-bound receipts; imports use the audit view. */
'use strict';
(() => {
  const GROUP_LABELS = { authored_controls: 'حالات ضبط مؤلفة · AUTHORED_SCENARIO', agency_record: 'مقارنة سجل وكالة · USGS_AGENCY_RECORD' };
  const AXIS_LABELS = { reported_motive: 'نسبة القصد المصرّح به إلى قائله', recorded_observation: 'مطابقة دعوى لسجل رصد مستقل', hidden_motive: 'الدافع الباطن · فحص الامتناع فقط' };
  const METRIC_LABELS = { positive_capability: 'استرجاع الدعم المرخص', refutation: 'استرجاع النفي الصريح', conflict: 'حفظ التعارض', safe_abstention: 'الامتناع عند غياب الترخيص', resource_boundary: 'حفظ حد الموارد' };
  const STATES = { SUPPORTED: 'دعم في الدليل المحدد', REFUTED: 'نفي صريح في الدليل المحدد', CONFLICT: 'دليلان متعارضان', UNKNOWN: 'لا دليل مرخص', RESOURCE_LIMIT: 'توقف عند ميزانية البحث' };
  const COMPARISONS = { PASS: 'مطابقة المرجع', FAIL: 'مخالفة المرجع', UNMEASURED: 'غير مقاس' };
  const number = n => n.toLocaleString('ar-JO');
  const $ = id => document.getElementById(id);
  const text = (id, value) => { $(id).textContent = String(value); };
  const node = (tag, value, className) => { const el = document.createElement(tag); if (value !== undefined) el.textContent = String(value); if (className) el.className = className; return el; };
  let current = null;
  function reset(message = 'لم يبدأ قياس جديد.') {
    current = null; $('epistemic-empty').hidden = false; $('epistemic-output').hidden = true; text('epistemic-empty-title', message);
    for (const id of ['epistemic-group-metrics', 'epistemic-cases', 'epistemic-case-detail']) $(id).replaceChildren();
    for (const id of ['epistemic-scope', 'epistemic-run-identity', 'epistemic-reference-identity', 'epistemic-json']) text(id, '');
  }
  function verificationLabel(item, trustedLive = false) {
    if (!trustedLive) return 'تصريح مستورد؛ لم يُعد تشغيل Lean';
    if (item.native_checked !== true || item.certificate_checked !== true) return 'لا شهادة Lean مقبولة لهذه الدعوى';
    if (item.observed?.status === 'RESOURCE_LIMIT') return 'شهادة Lean بتوقف الفحص عند حد الموارد';
    if (item.observed?.status === 'UNKNOWN') return 'شهادة Lean بعدم وجود دليل مرخص في هذا السجل';
    return 'شهادة Lean لهذه الدعوى ومدخلها فقط';
  }
  function details(label, value) { const el = node('details'); const pre = node('pre', JSON.stringify(value, null, 2)); pre.dir = 'ltr'; el.append(node('summary', label), pre); return el; }
  async function render(report) {
    reset();
    if (!report?.epistemic_measurement) { text('epistemic-empty-title', 'لم يكتمل القياس: ' + String(report?.error || report?.status || 'النتائج غير متاحة')); return; }
    const suite = globalThis.NabtEpistemicContract.validateEnvelope(report);
    if (globalThis.NabtEpistemicContract.verifyIntegrity) await globalThis.NabtEpistemicContract.verifyIntegrity(suite);
    current = suite; $('epistemic-empty').hidden = true; $('epistemic-output').hidden = false;
    text('epistemic-scope', 'الاستعلامات المعروضة مُعيَّرة قبل الفحص. الشهادة تتحقق من اختيار الدليل والقطبية وكامل القوائم ضمن سجل الإدخال؛ ليست إثباتًا لصدق المصدر أو الواقع العام.');
    text('epistemic-run-identity', 'الطلب ' + report.request_id + ' · النسخة ' + String(report.code_sha || '—').slice(0, 12));
    text('epistemic-reference-identity', 'المرجع: ' + suite.reference_sha256 + ' · سجل المصادر: ' + suite.source_registry_sha256);
    text('epistemic-json', JSON.stringify(report, null, 2));
    for (const [group, label] of Object.entries(GROUP_LABELS)) {
      const value = suite.groups[group], article = node('article', undefined, 'card epistemic-group');
      article.append(node('p', label, 'eyebrow'), node('h3', group === 'authored_controls' ? 'سلامة العقد في حالات الضبط' : 'مطابقة دعوى لسجل رصد مستقل'), node('p', 'مقام المجموعة: ' + number(value.case_count) + ' حالة'));
      article.append(node('p', group === 'authored_controls' ? 'مصدر هذه الحالات تأليف مرجعي داخل المشروع. نسبة القصد المصرّح به إلى قائله تختبر في هذا النطاق؛ لا مقابلة بشرية أو رصد للدافع النفسي.' : 'المصدر: وكالة USGS. هذه اختبارات على سجل واحد وحقل مقدار مفضل واحد، وليست قياسات فيزيائية مستقلة متعددة. المقارنة بنسخة معلومة؛ لا معايرة مستقلة للأجهزة ولا إثبات للحقيقة الفيزيائية العامة.', 'field-help'));
      const metrics = node('div', undefined, 'semantic-axis-metrics');
      for (const [category, title] of Object.entries(METRIC_LABELS)) {
        const count = value.metrics[category], card = node('section', undefined, 'semantic-axis-card');
        card.append(node('h4', title), node('strong', count.measured > 0 ? number(count.passed) + ' / ' + number(count.measured) : 'غير مقاس'), node('p', 'مطابق / مقاس · المؤهل: ' + number(count.eligible)), node('p', 'مخالف: ' + number(count.failed) + ' · غير مقاس: ' + number(count.unmeasured), 'field-help'));
        metrics.append(card);
      }
      article.append(metrics); $('epistemic-group-metrics').append(article);
    }
    for (const item of suite.cases) {
      const button = node('button', undefined, 'semantic-case-button'); button.type = 'button'; button.dataset.caseId = item.id; button.setAttribute('aria-controls', 'epistemic-case-detail'); button.setAttribute('aria-pressed', 'false');
      button.append(node('span', item.id + ' · ' + GROUP_LABELS[item.group], 'semantic-case-id'), node('strong', AXIS_LABELS[item.query.key.axis]), node('span', item.query.key.entity + ' · ' + item.query.key.predicate + ' · ' + item.query.key.value), node('span', COMPARISONS[item.comparison]));
      button.addEventListener('click', () => select(item.id)); $('epistemic-cases').append(button);
    }
    select(suite.cases[0].id);
  }
  function select(id) {
    const item = current?.cases.find(row => row.id === id); if (!item) return;
    // Keep the activated button connected: Enter/Space never move focus away.
    for (const button of $('epistemic-cases').children) { const active = button.dataset.caseId === id; button.setAttribute('aria-pressed', String(active)); button.classList.toggle('selected', active); }
    const root = $('epistemic-case-detail'); root.replaceChildren();
    root.append(node('p', item.id + ' · ' + GROUP_LABELS[item.group], 'eyebrow'), node('h3', AXIS_LABELS[item.query.key.axis]), node('p', item.observed ? STATES[item.observed.status] : 'لم يكتمل الفحص'), node('p', COMPARISONS[item.comparison]));
    root.append(node('h4', 'الدعوى المحددة ومقامها'), details('الاستعلام: الجهة والكيان والقيمة والوحدة والزمان والمكان', item.query));
    root.append(node('strong', verificationLabel(item, true), item.native_checked ? 'epistemic-proof' : 'field-help'), node('p', item.proof_scope, 'field-help'));
    root.append(node('p', 'بصمة المدخل المفحوص: ' + item.execution.input_sha256, 'semantic-case-id'));
    if (item.receipt_sha256) root.append(node('p', 'بصمة الإيصال: ' + item.receipt_sha256, 'semantic-case-id'));
    root.append(details('المرجع والمرصود — كامل قوائم الدعم والنفي والاختيار', { expected: item.expected, observed: item.observed }));
    root.append(node('h4', 'المصدر وإجراء القياس وحدوده'));
    const agency = item.group === 'agency_record';
    root.append(node('p', agency ? 'الإجراء: إسقاط الحقل المحدد من لقطة USGS المحفوظة ثم مقارنة الدعوى المقيدة به. الأداة: سجل وكالة زلزالية؛ معايرة المستشعرات لم تتحقق هنا. عدم يقين المقدار غير مصرح به في الحقل المفضل.' : 'الإجراء: مقارنة سجلات مؤلفة مستقلة عن اقتراح المحرك. الأداة: عقد مرجعي برمجي؛ لا جهاز رصد ولا قياس نفسي.', 'field-help'));
    for (const source of item.source_bindings) {
      const section = node('section', undefined, 'epistemic-source');
      section.append(node('p', 'نوع المصدر: ' + GROUP_LABELS[item.group]), node('p', 'الهوية: ' + source.identity), node('p', 'المراجعة: ' + source.revision), node('p', 'بصمة المحتوى: ' + source.content_sha256));
      if (agency) section.append(node('p', 'المسار المحفوظ: ' + source.raw_path), node('p', 'موضع الحقل: ' + source.field_pointer), node('p', 'بصمة الملف الخام: ' + source.raw_sha256));
      root.append(section);
    }
    root.append(details('مدخل Lean الكامل ونتيجته — مقدمات الشهادة', item.execution));
    root.append(node('p', 'حدود مستقلة: اكتساب هذه الدعوى من النص العربي الحر، وصدق القصد الباطن، وصدق الواقع العام، واكتمال العربية كلها غير مقاسة.', 'field-help'));
  }
  globalThis.NabtEpistemicMeasurement = Object.freeze({ render, reset, select, verificationLabel });
})();
