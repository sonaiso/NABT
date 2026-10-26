/* Local evidence inspection. This module never executes Lean, fetches sources,
 * evaluates supplied code, or upgrades an imported assertion into proof.
 * API: NabtEvidenceAudit.parse(rawJSON), await .audit(rawJSON), .limits.
 * Both functions take the original JSON string, not a pre-parsed object, so
 * duplicate keys cannot silently overwrite an assertion before inspection.
 */
(() => {
  'use strict';
  const VERSION = 'nabt.evidence-audit.v1';
  const LIMITS = Object.freeze({ maxBytes: 2097152, maxDepth: 32, maxString: 65536,
    maxArray: 4096, maxKeys: 1024, maxNodes: 50000, maxNumber: 128 });
  const AXIOMS = new Set(['propext', 'Classical.choice', 'Quot.sound']);
  const RANKS = ['مبرهن', 'مبرهن على الشاهد', 'مطابَق', 'مفحوص', 'مقيس', 'تقدير', 'رأي', 'بلا رتبة'];
  const QUESTIONS = ['started', 'completed', 'found', 'produced', 'accepted', 'stored', 'consumed_by_next'];
  const SHA256 = /^[a-f0-9]{64}$/;
  const SHA1 = /^[a-f0-9]{40}$/;
  const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  const string = x => typeof x === 'string';
  const integer = x => Number.isSafeInteger(x);
  const array = x => Array.isArray(x) ? x : [];
  const tri = x => x === true ? true : x === false ? false : null;
  const display = x => x === undefined || x === null ? '—' : typeof x === 'string' ? x : JSON.stringify(x);

  class AuditInputError extends Error {
    constructor(code, message, path = '$') { super(message); this.name = 'AuditInputError'; this.code = code; this.path = path; }
  }
  function fail(code, message, path) { throw new AuditInputError(code, message, path); }
  function validUnicode(s, path) {
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      if (c >= 0xD800 && c <= 0xDBFF) {
        const next = s.charCodeAt(++i);
        if (!(next >= 0xDC00 && next <= 0xDFFF)) fail('INVALID_UNICODE', 'يتضمن النص نصف زوج Unicode غير صالح.', path);
      } else if (c >= 0xDC00 && c <= 0xDFFF) fail('INVALID_UNICODE', 'يتضمن النص نصف زوج Unicode غير صالح.', path);
    }
  }
  // Compare decimal values before exposing a Number to integer-field checks.
  // For example 16.0 and 1.6e1 equal 16, but 16.000000000000001 does not.
  // This is a decimal round-trip contract, not exact binary-float arithmetic.
  function decimalIdentity(token) {
    const [, sign, whole, fraction = '', exponent = '0'] =
      /^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(token);
    let digits = (whole + fraction).replace(/^0+/, '');
    if (!digits) return '0';
    const trailing = /0+$/.exec(digits)?.[0].length ?? 0;
    if (trailing) digits = digits.slice(0, -trailing);
    const power = BigInt(exponent) - BigInt(fraction.length) + BigInt(trailing);
    return sign + digits + 'e' + power.toString();
  }
  function parse(raw) {
    if (!string(raw)) fail('RAW_JSON_REQUIRED', 'يلزم نص JSON الأصلي للفحص.');
    if (raw.length > LIMITS.maxBytes || new TextEncoder().encode(raw).length > LIMITS.maxBytes)
      fail('BYTE_LIMIT', 'يتجاوز ملف التقرير حد ٢ MiB.');
    validUnicode(raw, '$');
    let pos = 0, nodes = 0;
    const whitespace = () => { while (pos < raw.length && /[\x20\t\n\r]/.test(raw[pos])) pos++; };
    function readString(path) {
      const start = pos++;
      let closed = false;
      while (pos < raw.length) {
        const ch = raw[pos++];
        if (ch === '"') { closed = true; break; }
        if (ch === '\\') {
          const escape = raw[pos++];
          if (escape === 'u') {
            if (!/^[a-fA-F0-9]{4}$/.test(raw.slice(pos, pos + 4))) fail('INVALID_JSON', 'ترميز Unicode غير صالح في JSON.', path);
            pos += 4;
          } else if (!escape || !'"\\/bfnrt'.includes(escape)) fail('INVALID_JSON', 'محرف هروب غير صالح في JSON.', path);
        } else if (ch.charCodeAt(0) < 32) fail('INVALID_JSON', 'محرف تحكم غير مرمّز في JSON.', path);
      }
      if (!closed) fail('INVALID_JSON', 'نص JSON غير مكتمل.', path);
      let result;
      try { result = JSON.parse(raw.slice(start, pos)); } catch { fail('INVALID_JSON', 'سلسلة JSON غير صالحة.', path); }
      if (result.length > LIMITS.maxString) fail('STRING_LIMIT', 'أحد الحقول النصية يتجاوز حد الطول.', path);
      validUnicode(result, path);
      return result;
    }
    function value(depth, path) {
      if (depth > LIMITS.maxDepth) fail('DEPTH_LIMIT', 'يتجاوز تداخل التقرير الحد المسموح.', path);
      if (++nodes > LIMITS.maxNodes) fail('NODE_LIMIT', 'يتجاوز عدد عناصر التقرير الحد المسموح.', path);
      whitespace();
      const ch = raw[pos];
      if (ch === '"') return readString(path);
      if (ch === '{') {
        pos++; whitespace();
        const result = Object.create(null), seen = new Set();
        if (raw[pos] === '}') { pos++; return result; }
        while (pos < raw.length) {
          whitespace();
          if (raw[pos] !== '"') fail('INVALID_JSON', 'مفتاح JSON غير صالح.', path);
          const key = readString(path);
          if (seen.has(key)) fail('DUPLICATE_KEY', 'يوجد مفتاح JSON مكرر؛ لم تُختر إحدى القيم.', path + '.' + key);
          if (['__proto__', 'prototype', 'constructor'].includes(key)) fail('RESERVED_KEY', 'مفتاح محجوز غير مسموح في التقرير.', path + '.' + key);
          seen.add(key);
          if (seen.size > LIMITS.maxKeys) fail('KEY_LIMIT', 'يتجاوز عدد الحقول الحد المسموح.', path);
          whitespace();
          if (raw[pos++] !== ':') fail('INVALID_JSON', 'علامة فصل مفتاح JSON مفقودة.', path);
          result[key] = value(depth + 1, path + '.' + key);
          whitespace();
          if (raw[pos] === '}') { pos++; return result; }
          if (raw[pos++] !== ',') fail('INVALID_JSON', 'فاصل JSON غير صالح.', path);
        }
        fail('INVALID_JSON', 'كائن JSON غير مكتمل.', path);
      }
      if (ch === '[') {
        pos++; whitespace();
        const result = [];
        if (raw[pos] === ']') { pos++; return result; }
        while (pos < raw.length) {
          if (result.length >= LIMITS.maxArray) fail('ARRAY_LIMIT', 'يتجاوز عدد صفوف التقرير الحد المسموح.', path);
          result.push(value(depth + 1, path + '[' + result.length + ']'));
          whitespace();
          if (raw[pos] === ']') { pos++; return result; }
          if (raw[pos++] !== ',') fail('INVALID_JSON', 'فاصل قائمة JSON غير صالح.', path);
        }
        fail('INVALID_JSON', 'قائمة JSON غير مكتملة.', path);
      }
      for (const [literal, result] of [['true', true], ['false', false], ['null', null]]) {
        if (raw.slice(pos, pos + literal.length) === literal) { pos += literal.length; return result; }
      }
      const match = /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(raw.slice(pos));
      if (match) {
        pos += match[0].length;
        if (match[0].length > LIMITS.maxNumber)
          fail('NUMBER_LIMIT', 'يتجاوز طول التمثيل العددي الحد المسموح.', path);
        const n = Number(match[0]);
        if (!Number.isFinite(n) || (Number.isInteger(n) && !Number.isSafeInteger(n)))
          fail('INVALID_NUMBER', 'عدد غير منتهٍ أو خارج مجال التمثيل الدقيق.', path);
        if (decimalIdentity(match[0]) !== decimalIdentity(String(n)))
          fail('LOSSY_NUMBER', 'يتغير المعنى العددي عند التحويل؛ لم يُقبل العدد المقرب.', path);
        return n;
      }
      fail('INVALID_JSON', 'قيمة JSON غير صالحة.', path);
    }
    const result = value(0, '$'); whitespace();
    if (pos !== raw.length) fail('INVALID_JSON', 'توجد بقايا بعد نهاية JSON.');
    if (!object(result)) fail('OBJECT_REQUIRED', 'يلزم تقرير JSON على هيئة كائن.');
    return result;
  }

  function requireObject(value, path) { if (!object(value)) fail('SCHEMA_SHAPE', 'يلزم كائن في ' + path, path); return value; }
  function requireArray(value, path) { if (!Array.isArray(value)) fail('SCHEMA_SHAPE', 'تلزم قائمة في ' + path, path); return value; }
  function requireString(value, path) { if (!string(value)) fail('SCHEMA_SHAPE', 'يلزم نص في ' + path, path); return value; }
  function optionalType(o, key, test, path) {
    if (own(o, key) && o[key] !== null && !test(o[key])) fail('SCHEMA_SHAPE', 'نوع الحقل غير صالح: ' + key, path + '.' + key);
  }
  function strings(value, path) {
    const a = requireArray(value, path);
    a.forEach((v, i) => requireString(v, path + '[' + i + ']'));
    return a;
  }
  async function sha256(text) {
    if (!globalThis.crypto?.subtle) return null;
    const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return Array.from(new Uint8Array(digest), x => x.toString(16).padStart(2, '0')).join('');
  }
  function base(raw, record, kind) {
    return { schema: VERSION, kind,
      authority: { origin: 'imported', lean_replayed: false, all_arabic_complete: false, world_truth_established: false },
      input: null, identity: {}, checks: [], findings: [], layers: [], claims: [], stages: [],
      metrics: { claims: 0, declared_theorems: 0, declared_passed: 0, theorem_axioms_allowed: 0,
        local_lean_replays: 0, lexical_entries: 0, lexical_sources: 0, stages_started: 0,
        stages_total: 0, rank_counts: {} },
      limits: ['هذا فحص محلي لبنية السجل واتساقه؛ لم تُشغّل نواة Lean ولم تُقرأ ملفات المصدر.',
        'السجل المستورد يصرّح بنتائجه. نجاح البصمة أو سلامة JSON لا يصادق على صحة دلالته.',
        'لا تستنتج هذه الواجهة اكتمال العربية كلها أو صدق الخبر في العالم.'],
      raw_record: record, raw_json: raw };
  }
  function finding(out, id, severity, title, detail, layer = null) {
    out.findings.push({ id, severity, title, detail, layer });
  }
  function check(out, id, label, status, detail) { out.checks.push({ id, label, status, detail }); }
  function equalsCheck(out, id, label, declared, actual, detail) {
    check(out, id, label, declared === undefined || declared === null || actual === null ? 'unknown' : declared === actual ? 'pass' : 'fail', detail);
  }
  function authorityFinding(out, record, path) {
    for (const key of ['all_arabic_complete', 'world_truth_established']) {
      optionalType(record, key, v => typeof v === 'boolean', path);
      if (record[key] === true) finding(out, 'UNSUPPORTED_AUTHORITY_' + key.toUpperCase(), 'error',
        'دعوى سلطة أوسع من الدليل', 'يصرّح السجل بـ ' + key + '=true. لا يقبل الفاحص المحلي هذه الدعوى ولا يعيدها بوصفها نتيجة مثبتة.');
    }
  }
  async function inspectInput(out, record, tabaqat) {
    const input = tabaqat ? requireObject(record.input, '$.input') : record.source || {};
    const text = tabaqat ? requireString(input.nass_kama_wasal, '$.input.nass_kama_wasal') : input.raw_text;
    if (text !== undefined && !string(text)) fail('SCHEMA_SHAPE', 'النص الأصلي ليس سلسلة.', '$.source.raw_text');
    if (text === undefined) {
      check(out, 'TEXT_HASH', 'مطابقة بصمة النص', 'unknown', 'لم يُضمّن النص الأصلي في السجل.');
      return;
    }
    optionalType(input, 'sha256', string, '$.input');
    optionalType(input, 'codepoints', v => integer(v) && v >= 0, '$.input');
    optionalType(input, 'nfc_eq_input', v => typeof v === 'boolean', '$.input');
    optionalType(input, 'nfc', string, '$.input');
    const computed = await sha256(text), normalized = text.normalize('NFC');
    out.input = { text, declared_sha256: input.sha256 ?? null, computed_sha256: computed,
      declared_codepoints: input.codepoints ?? null, computed_codepoints: Array.from(text).length,
      nfc_equal: normalized === text, declared_nfc_equal: input.nfc_eq_input ?? null };
    equalsCheck(out, 'TEXT_HASH', 'مطابقة بصمة النص', input.sha256, computed,
      computed ? 'حُسبت SHA-256 من بايتات UTF-8 للنص الأصلي دون تطبيع.' : 'WebCrypto غير متاح؛ لم تُحسب بصمة بديلة.');
    equalsCheck(out, 'CODEPOINTS', 'عدد نقاط Unicode', input.codepoints, out.input.computed_codepoints,
      'العدد المحسوب: ' + out.input.computed_codepoints + '؛ يختلف عن عدد الحروف أو المقاطع.');
    equalsCheck(out, 'NFC_FLAG', 'تصريح تطبيع NFC', input.nfc_eq_input, normalized === text,
      'فُحص التطبيع للمقارنة فقط؛ ظل النص الأصلي محفوظًا.');
    if (input.nfc !== undefined) equalsCheck(out, 'NFC_TEXT', 'نسخة NFC المعلنة', input.nfc, normalized, 'مقارنة حقل nfc بالتطبيع المحسوب.');
    if (out.checks.some(x => ['TEXT_HASH','CODEPOINTS','NFC_FLAG','NFC_TEXT'].includes(x.id) && x.status === 'fail'))
      finding(out, 'INPUT_IDENTITY_MISMATCH', 'error', 'هوية النص غير متسقة', 'أحد تصريحات البصمة أو Unicode لا يطابق النص المضمّن.', 1);
  }
  function inspectStages(out, stages) {
    const ids = new Set();
    for (let i = 0; i < stages.length; i++) {
      const s = requireObject(stages[i], '$.stages[' + i + ']');
      const id = requireString(s.stage, '$.stages[' + i + '].stage');
      if (ids.has(id)) fail('DUPLICATE_STAGE', 'معرّف مرحلة مكرر.', '$.stages[' + i + ']');
      ids.add(id);
      const answers = {};
      for (const key of QUESTIONS) {
        optionalType(s, key, v => typeof v === 'boolean', '$.stages[' + i + ']');
        answers[key] = tri(s[key]);
      }
      const contradictions = [];
      if (answers.started === false && QUESTIONS.slice(1).some(k => answers[k] === true)) contradictions.push('نتيجة مرحلة لم يبدأ استدعاؤها');
      if (answers.completed === false && ['produced','accepted','stored','consumed_by_next'].some(k => answers[k] === true)) contradictions.push('مخرجات مكتملة لمرحلة غير مكتملة');
      if (answers.produced === false && ['accepted','stored','consumed_by_next'].some(k => answers[k] === true)) contradictions.push('قبول أو حفظ أو استهلاك دون إنتاج');
      if (answers.accepted === false && answers.consumed_by_next === true) contradictions.push('استهلاك مخرج مرفوض');
      const residuals = s.residuals === undefined ? [] : strings(s.residuals, '$.stages[' + i + '].residuals');
      optionalType(s, 'reason', string, '$.stages[' + i + ']');
      out.stages.push({ id, label: id, answers, reason: s.reason ?? null, residuals, contradictions });
      if (contradictions.length) finding(out, 'STAGE_CONTRADICTION_' + id, 'error', 'تناقض في سجل المرحلة', id + ': ' + contradictions.join('؛ '));
      residuals.forEach((residual, index) => {
        // Known residuals get one explanatory finding below; retain every
        // literal code in its stage without duplicating the same issue card.
        if (/MADLUL_SOURCE_UNDECLARED_IN_MASHRU|MIRSAT_DEFAULT_ASSUMED|ARAD_IZAHA_DEFAULT_ASSUMED|LAZIM_BY_FRAME_NOT_BY_TEXT/.test(residual)) return;
        finding(out, 'DECLARED_RESIDUAL_' + id + '_' + index, 'warning',
          'بقية معلنة في المرحلة', id + ': ' + residual, id.startsWith('S4_') ? 2 : id.startsWith('S5_') ? 3 : id.startsWith('S6_') ? 4 : null);
      });
    }
    out.metrics.stages_total = out.stages.length;
    out.metrics.stages_started = out.stages.filter(x => x.answers.started === true).length;
    out.metrics.stages_unmeasured = out.stages.filter(x => QUESTIONS.some(q => x.answers[q] === null)).length;
    check(out, 'STAGE_CONSISTENCY', 'اتساق حالات المراحل', out.stages.length ? out.stages.some(x => x.contradictions.length) ? 'fail' : 'pass' : 'unknown',
      'نعم/لا/غير مقاس حالات مستقلة. تخطي مرحلة اختيارية لا يُحسب فشلًا أو نجاحًا.');
  }
  function inspectTheorems(out, lean) {
    const theorems = requireObject(lean.theorems, '$.lean.theorems');
    const normalized = Object.create(null);
    for (const [id, raw] of Object.entries(theorems)) {
      const theorem = requireObject(raw, '$.lean.theorems.' + id);
      optionalType(theorem, 'passed', v => typeof v === 'boolean', '$.lean.theorems.' + id);
      const axioms = theorem.axioms === undefined ? null : strings(theorem.axioms, '$.lean.theorems.' + id + '.axioms');
      normalized[id] = { declared_passed: tri(theorem.passed), axioms, axioms_allowed: axioms === null ? null : axioms.every(x => AXIOMS.has(x)) };
      if (normalized[id].axioms_allowed === false) finding(out, 'AXIOM_OUTSIDE_POLICY_' + id, 'error', 'اعتماد خارج سياسة المسلّمات', id + ': ' + axioms.filter(x => !AXIOMS.has(x)).join('، '));
    }
    out.metrics.declared_theorems = Object.keys(normalized).length;
    out.metrics.declared_passed = Object.values(normalized).filter(t => t.declared_passed === true).length;
    out.metrics.theorem_axioms_allowed = Object.values(normalized).filter(t => t.axioms_allowed === true).length;
    const passCodes = [];
    for (const key of ['pass1','pass2']) {
      if (lean[key] !== undefined) {
        const pass = requireObject(lean[key], '$.lean.' + key);
        optionalType(pass, 'rc', integer, '$.lean.' + key);
        passCodes.push(pass.rc);
      }
    }
    check(out, 'DECLARED_LEAN_EXIT', 'رموز خروج Lean المعلنة', passCodes.length !== 2 || passCodes.some(x => x === undefined || x === null) ? 'unknown' : passCodes.every(x => x === 0) ? 'pass' : 'fail',
      'تصريحات السجل: ' + passCodes.map(display).join('، ') + '. لم يُعد تشغيل هذه الأوامر.');
    check(out, 'DECLARED_AXIOM_POLICY', 'قائمة المسلّمات المعلنة', Object.values(normalized).some(x => x.axioms_allowed === false) ? 'fail' : Object.values(normalized).some(x => x.axioms_allowed === null) || !out.metrics.declared_theorems ? 'unknown' : 'pass',
      'القائمة المسموحة للمقارنة: propext، Classical.choice، Quot.sound. لم تُقرأ بيئة Lean للتحقق من التصريح.');
    check(out, 'LEAN_REPLAY', 'إعادة تشغيل البرهان محليًا', 'unknown', 'صفر إعادة تشغيل. أسماء النظريات وpassed وسجل stdout بيانات مستوردة.');
    if (passCodes.some(x => x !== undefined && x !== null && x !== 0) && out.metrics.declared_passed > 0)
      finding(out, 'LEAN_EXIT_THEOREM_CONFLICT', 'error', 'تعثر Lean مع نجاح نظريات معلن', 'يحتوي السجل رمز خروج غير صفري ونظريات passed=true؛ يلزم فحص ملفات التنفيذ.');
    return normalized;
  }
  async function tabaqat(raw, record) {
    const out = base(raw, record, 'tabaqat4');
    requireObject(record.identity, '$.identity');
    requireObject(record.lean, '$.lean');
    requireArray(record.claims, '$.claims');
    requireArray(record.stages, '$.stages');
    authorityFinding(out, record, '$');
    await inspectInput(out, record, true);
    const identity = record.identity;
    optionalType(identity, 'mashru_tree_clean', v => typeof v === 'boolean', '$.identity');
    for (const k of ['mashru_head','mashru_status_porcelain','lean_toolchain','qamus_sha256']) optionalType(identity, k, string, '$.identity');
    out.identity = { engine: 'Mashru', commit: identity.mashru_head ?? null, tree_clean: tri(identity.mashru_tree_clean),
      tree_status: identity.mashru_status_porcelain ?? null, toolchain: identity.lean_toolchain ?? null,
      qamus_sha256: identity.qamus_sha256 ?? null, timestamp: record.timestamp_utc ?? null,
      files_declared: object(identity.tool_files) ? Object.keys(identity.tool_files).length : 0,
      files_retrieved: 0, source_verified: false };
    check(out, 'COMMIT_FORMAT', 'صيغة هوية الالتزام', identity.mashru_head == null ? 'unknown' : SHA1.test(identity.mashru_head) ? 'pass' : 'fail', 'اختبار الصيغة فقط؛ لم يُجلب هذا الالتزام.');
    check(out, 'SOURCE_REPLAY', 'اكتمال حزمة إعادة التحقق', 'unknown', 'البصمات المعطاة لا تتضمن ملفات Lean والمشغّل والمصادر نفسها. لم تُقارن بمحتويات مستقلة.');
    const files = identity.tool_files === undefined ? null : requireObject(identity.tool_files, '$.identity.tool_files');
    if (files) {
      const hashes = Object.values(files);
      hashes.forEach((v, i) => requireString(v, '$.identity.tool_files[' + i + ']'));
      check(out, 'TOOL_HASH_FORMAT', 'صيغة بصمات ملفات الأداة', !hashes.length ? 'unknown' : hashes.every(h => SHA256.test(h)) ? 'pass' : 'fail',
        'تُقبل بصمة SHA-256 الكاملة في تدقيق الصيغة؛ لم تُجلب الملفات نفسها.');
      if (own(files, 't4/qamus.json')) equalsCheck(out, 'QAMUS_HASH_LINK', 'اتساق بصمة المعجم داخل السجل',
        identity.qamus_sha256, files['t4/qamus.json'], 'مقارنة تصريح المعجم ببصمته في جدول الملفات، لا بمحتوى ملف مستقل.');
    }
    if (identity.mashru_tree_clean === false) finding(out, 'DIRTY_WORKTREE', 'warning', 'الشجرة المعلنة غير نظيفة',
      'وجود ملفات غير متعقبة لا يبطل البرهان تلقائيًا، لكنه يمنع نسبة الأداة كلها إلى HEAD وحده. يلزم تضمين الملفات المستخدمة وبصماتها في حزمة قابلة للإعادة.');
    else if (identity.mashru_tree_clean !== true) finding(out, 'WORKTREE_UNMEASURED', 'warning', 'حالة الشجرة غير مقاسة', 'لم يصرّح السجل بقيمة منطقية لحالة الشجرة.');
    if (identity.mashru_tree_clean === true && string(identity.mashru_status_porcelain) && identity.mashru_status_porcelain.trim())
      finding(out, 'WORKTREE_CONTRADICTION', 'error', 'تصريح نظافة الشجرة متناقض', 'tree_clean=true مع سجل porcelain غير فارغ.');
    inspectStages(out, record.stages);
    const theorems = inspectTheorems(out, record.lean);
    const claimIds = new Set(), ranks = Object.create(null);
    RANKS.forEach(rank => { ranks[rank] = 0; });
    for (let i = 0; i < record.claims.length; i++) {
      const c = requireObject(record.claims[i], '$.claims[' + i + ']');
      const id = requireString(c.ism, '$.claims[' + i + '].ism');
      if (claimIds.has(id)) fail('DUPLICATE_CLAIM', 'معرّف ادعاء مكرر.', '$.claims[' + i + ']');
      claimIds.add(id);
      if (!integer(c.tabaqa) || c.tabaqa < 1 || c.tabaqa > 4) fail('SCHEMA_SHAPE', 'رقم الطبقة يجب أن يكون من ١ إلى ٤.', '$.claims[' + i + '].tabaqa');
      optionalType(c, 'rutba', string, '$.claims[' + i + ']');
      optionalType(c, 'tarjama', string, '$.claims[' + i + ']');
      optionalType(c, 'burhan', string, '$.claims[' + i + ']');
      const rank = c.rutba ?? 'بلا رتبة';
      ranks[rank] = (ranks[rank] || 0) + 1;
      const theorem = theorems[id];
      out.claims.push({ id, layer: c.tabaqa, label: c.tarjama || id, value: c.qima ?? null, rank,
        evidence: c.burhan ?? null, axioms: theorem?.axioms ?? null,
        declared_passed: theorem?.declared_passed ?? null, replayed: false });
      if (['مبرهن','مبرهن على الشاهد'].includes(rank) && (!theorem || theorem.declared_passed !== true))
        finding(out, 'CLAIM_WITHOUT_DECLARED_THEOREM_' + id, 'warning', 'رتبة برهانية دون نجاح مطابق في السجل', id + ': لا توجد نظرية مطابقة بمعرّفها وpassed=true.', c.tabaqa);
      if (!RANKS.includes(rank)) finding(out, 'UNKNOWN_RANK_' + id, 'warning', 'رتبة غير معرّفة', rank + ': احتُفظ بالوصف دون منحه سلطة.', c.tabaqa);
    }
    out.metrics.claims = out.claims.length;
    out.metrics.rank_counts = ranks;
    if (ranks['مبرهن'] > 0) finding(out, 'GENERAL_SCOPE_UNINSPECTED', 'warning', 'عموم المبرهنة لم يُفحص',
      'يصف السجل بعض الادعاءات بأنها «مبرهن». لم يُجلب نص النظرية أو حدود تكميمها أو مقدماتها؛ لا يُستنتج العموم من اسمها أو رتبتها.');
    if (record.wasm_summary !== undefined) {
      const summary = requireObject(record.wasm_summary, '$.wasm_summary');
      for (const [rank, n] of Object.entries(summary)) if (!integer(n) || n < 0) fail('SCHEMA_SHAPE', 'عدد رتبة غير صالح.', '$.wasm_summary.' + rank);
      const keys = new Set([...Object.keys(summary), ...Object.keys(ranks)]);
      const consistent = [...keys].every(k => (summary[k] ?? 0) === (ranks[k] ?? 0));
      check(out, 'CLAIM_COUNTS', 'ملخص رتب الادعاءات', consistent ? 'pass' : 'fail', 'أعيد العد من قائمة claims؛ لا يعتمد العرض على wasm_summary.');
      if (!consistent) finding(out, 'CLAIM_COUNT_MISMATCH', 'error', 'ملخص الادعاءات لا يطابق صفوفه', 'الأعداد المعروضة محسوبة من الادعاءات الفعلية في السجل.');
    } else check(out, 'CLAIM_COUNTS', 'ملخص رتب الادعاءات', 'unknown', 'لا ملخص معلن للمقارنة؛ أُعيد عد الادعاءات محليًا.');
    const maani = record.maani === undefined ? [] : requireArray(record.maani, '$.maani');
    out.metrics.lexical_entries = maani.length;
    maani.forEach((rawMeaning, i) => {
      const meaning = requireObject(rawMeaning, '$.maani[' + i + ']');
      const source = meaning.mudaa;
      const full = object(source) && string(source.ism) && !!source.ism.trim() && string(source.mawdi) && !!source.mawdi.trim() && string(source.sha256) && SHA256.test(source.sha256);
      if (full) out.metrics.lexical_sources++;
      else finding(out, 'LEXICAL_SOURCE_MISSING_' + i, 'warning', 'مصدر مدلول غير موثق بالكامل', display(meaning.ism ?? i) + ': يلزم المصدر والموضع وبصمة كاملة. تعريف حقول المدلول داخل البرنامج لا يثبت مطابقته للمعجم.', 2);
    });
    if (!maani.length) finding(out, 'LEXICAL_COVERAGE_UNMEASURED', 'warning', 'إسناد المدلولات غير مقاس', 'لا قائمة معانٍ مستقلة تسمح بعدّ مصادرها.', 2);
    if (record.tokens !== undefined) {
      const tokens = requireArray(record.tokens, '$.tokens');
      tokens.forEach((token, i) => {
        requireObject(token, '$.tokens[' + i + ']');
        requireString(token.surface, '$.tokens[' + i + '].surface');
        optionalType(token, 'idx', v => integer(v) && v >= 0, '$.tokens[' + i + ']');
      });
      out.metrics.tokens = tokens.length;
      const sourceTokens = out.input.text.match(/\S+/gu) || [];
      const same = tokens.length === sourceTokens.length && tokens.every((token, i) => token.surface === sourceTokens[i]);
      check(out, 'TOKEN_SURFACES', 'مطابقة الأسطح للنص', same ? 'pass' : 'fail',
        'مقارنة تقنية بحسب الفصل بالمسافات؛ ليست برهانًا على صحة التقطيع اللغوي.');
      if (record.maani !== undefined) check(out, 'TOKEN_MEANING_COUNT', 'عدد الأسطح والمدلولات',
        tokens.length === maani.length ? 'pass' : 'fail', 'مقارنة عددية لا تتحقق من صحة معنى كل سطح.');
    }
    if (record.dal !== undefined) {
      const dal = requireArray(record.dal, '$.dal');
      const cells = [];
      dal.forEach((word, i) => {
        requireObject(word, '$.dal[' + i + ']');
        requireArray(word.khalaya, '$.dal[' + i + '].khalaya').forEach((cell, j) => {
          if (!integer(cell)) fail('SCHEMA_SHAPE', 'ترميز الخلية يجب أن يكون عددًا صحيحًا.', '$.dal[' + i + '].khalaya[' + j + ']');
          cells.push(cell);
        });
      });
      out.metrics.cells = cells.length;
      check(out, 'CELL_RANGE', 'مجال الخلايا المعلن', !cells.length ? 'unknown' : cells.every(n => n >= 0 && n < 116) ? 'pass' : 'fail',
        'فحص المجال ٠–١١٥ وفق تصريح ٢٩ حاملًا × ٤ حالات؛ جدول المخارج ومطابقة الحرف بالخلية لم يُعاد تحميلهما.');
    }
    const residuals = out.stages.flatMap(s => s.residuals);
    if (residuals.some(x => x.includes('MIRSAT_DEFAULT_ASSUMED')))
      finding(out, 'ANCHOR_ASSUMED', 'warning', 'المرساة افتراض معلن', 'الآن وهنا قيم مُدخلة في الشاهد؛ لا يثبت النص وحده موقع الحدث أو إحداثياته.', 4);
    if (residuals.some(x => x.includes('ARAD_IZAHA_DEFAULT_ASSUMED')))
      finding(out, 'EVENT_OFFSET_ASSUMED', 'warning', 'إزاحة الحدث مفترضة', 'الإزاحة الزمنية الرقمية ليست مستخرجة من صيغة الماضي وحدها؛ يلزم فصل زمن الصيغة عن توقيت الحدث.', 4);
    if (residuals.some(x => x.includes('LAZIM_BY_FRAME_NOT_BY_TEXT')) || out.claims.some(x => x.rank === 'مقيس'))
      finding(out, 'FRAME_SELECTION_CONDITIONAL', 'warning', 'اختيار الإطار يحتاج دليلًا مستقلًا', 'قبول الإطار بعد اختياره لا يبرهن أن اختياره من النص صحيح أو أن جميع البدائل المرخّصة استُنفدت.', 3);
    if (object(record.plan) && object(record.plan.isnad))
      finding(out, 'ISNAD_CONSTRUCTION_NOT_EXTRACTION', 'info', 'الإسناد المعرّف يحتاج عقد استخراج', 'مطابقة بنية الإسناد المنشأة لا تكفي لإثبات استخراجه من النص أو مطابقته لواقعة خارجية.', 3);
    const labels = ['الدالّ وحده', 'المدلول وحده', 'معًا: الإطار والحكم', 'العقل: المرساة والإسناد'];
    if (record.tabaqat_state !== undefined) {
      const states = requireObject(record.tabaqat_state, '$.tabaqat_state');
      for (const [key, value] of Object.entries(states)) {
        if (!['1','2','3','4'].includes(key) || (value !== null && !string(value)))
          fail('SCHEMA_SHAPE', 'رتبة الطبقة يجب أن تكون نصًا أو غير مقاسة.', '$.tabaqat_state.' + key);
      }
    }
    for (let id = 1; id <= 4; id++) {
      const claims = out.claims.filter(c => c.layer === id);
      out.layers.push({ id, title: labels[id - 1], declared: object(record.tabaqat_state) ? record.tabaqat_state[String(id)] ?? null : null,
        summary: 'ادعاءات مستوردة؛ لم يُعد تشغيل Lean', claim_count: claims.length,
        issues: out.findings.filter(f => f.layer === id).map(f => f.id) });
    }
    if (record.la_yuddaa !== undefined) out.limits.push(...strings(record.la_yuddaa, '$.la_yuddaa'));
    finding(out, 'WITNESS_NOT_LANGUAGE_COMPLETENESS', 'info', 'الشاهد ليس استقراءً على اللغة', 'النجاح على عبارة بعينها لا يثبت سلامة المترجم لكل المدخلات أو استنفاد القراءات أو اكتمال العربية كلها.');
    finding(out, 'IMPORTED_REPORT_UNAUTHENTICATED', 'warning', 'التقرير المستورد لم يُعد التحقق منه',
      'لا يمكن توثيق تنفيذ Lean من rc=0 وpassed=true داخل JSON وحدهما. يلزم جلب الملفات المطابقة وبناء النواة وإعادة الفحص بصورة مستقلة.');
    return out;
  }

  async function nabt(raw, record) {
    const out = base(raw, record, 'nabt');
    authorityFinding(out, record, '$');
    const operationalFailure = own(record, 'error');
    const earlyInputFailure = operationalFailure && record.status === 'INVALID_INPUT' && record.mode == null;
    if (!['inference','benchmark','semantic_axes'].includes(record.mode) && !earlyInputFailure)
      fail('SCHEMA_SHAPE', 'نمط تقرير NABT غير معروف.', '$.mode');
    optionalType(record, 'status', string, '$');
    for (const k of ['code_sha','native_sha256','runtime_sha256','runner_sha256','payload_sha256','toolchain','request_id']) optionalType(record, k, string, '$');
    out.identity = { engine: 'NABT', commit: record.code_sha ?? null, tree_clean: null,
      toolchain: record.toolchain ?? null, request_id: record.request_id ?? null,
      timestamp: record.generated_at_utc ?? null, source_verified: false,
      native_sha256: record.native_sha256 ?? null, payload_sha256: record.payload_sha256 ?? null };
    check(out, 'COMMIT_FORMAT', 'صيغة هوية الالتزام', record.code_sha == null ? 'unknown' : SHA1.test(record.code_sha) ? 'pass' : 'fail', 'الصيغة وحدها لا تثبت مصدر التقرير المستورد.');
    check(out, 'LEAN_REPLAY', 'إعادة تشغيل البرهان محليًا', 'unknown', 'لم يُرسل السجل إلى الخادم ولم يُعد تشغيل Lean.');
    const importedClaim = (id, layer, label, value) => out.claims.push({ id, layer, label, value,
      rank: 'تصريح مستورد', evidence: 'قيمة من JSON المستورد؛ لم يُعد تشغيل Lean للتحقق منها.',
      axioms: null, declared_passed: null, replayed: false });
    // run_payload can fail before either payload exists. A valid terminal
    // failure is inspectable evidence of an unmeasured run, not an empty test.
    if (operationalFailure) {
      const error = requireString(record.error, '$.error');
      if (!['INVALID_INPUT','RESOURCE_EXHAUSTED','EXECUTION_FAILED','VERIFICATION_UNAVAILABLE'].includes(record.status)
          || !error.length || error.length > 128 || own(record, 'benchmark') || own(record, 'result') || own(record, 'semantic_axes'))
        fail('SCHEMA_SHAPE', 'غلاف تعذر التنفيذ لا يطابق عقد الحالة والخطأ.', '$.error');
      out.declared_status = record.status;
      out.operational_failure = { status: record.status, error, measurements_available: false };
      importedClaim('operational_status', 3, 'حالة التنفيذ المعلنة: ' + record.status, record.status);
      importedClaim('operational_error', 3, 'سبب تعذر التنفيذ: ' + error, error);
      out.metrics.claims = out.claims.length;
      out.metrics.rank_counts = { 'تصريح مستورد': out.claims.length };
      out.layers = [{ id: 3, title: 'حالة التنفيذ', declared: null,
        summary: 'تعذر تنفيذ معلن؛ لا قياس لغوي', claim_count: out.claims.length, issues: [] }];
      check(out, 'OPERATIONAL_FAILURE', 'غلاف تعذر التنفيذ', 'pass', 'الحالة والخطأ متوافقان مع عقد التعذر؛ لا صفوف قياس متاحة.');
      finding(out, 'OPERATIONAL_FAILURE_UNMEASURED', 'info', 'القياس غير متاح',
        record.status + ': ' + error + '. لا يحسب غياب النتائج صفر نجاحات أو إخفاقًا لغويًا.', 3);
      finding(out, 'IMPORTED_REPORT_UNAUTHENTICATED', 'warning', 'التقرير المستورد غير مصادق عليه',
        'هذه حالة تشغيل من ملف مستورد؛ لم يُعد تشغيل الطلب أو التحقق من مصدره.');
      return out;
    }
    if (record.mode === 'semantic_axes') {
      if (!globalThis.NabtSemanticAxes) fail('SCHEMA_SHAPE', 'مدقق جهات الدلالة غير متاح.', '$.semantic_axes');
      let suite;
      try { suite = globalThis.NabtSemanticAxes.validate(record.semantic_axes); }
      catch (error) { fail('SCHEMA_SHAPE', error.message, '$.semantic_axes'); }
      if (own(suite, 'lexical_profile') && record.lexical_profile !== suite.lexical_profile) fail('SCHEMA_SHAPE', 'المسار المعجمي في التقرير لا يطابق المجموعة.', '$.lexical_profile');
      out.semantic_axes = suite;
      for (const item of suite.cases) for (const c of item.claims) {
        importedClaim(item.id + ':' + c.id, c.axis === 'syntax' ? 1 : ['readings','reference'].includes(c.axis) ? 2 : 4,
          c.statement, { case_id: item.id, context_id: item.context_id, axis: c.axis, status: c.status, verification: c.verification });
      }
      out.metrics.claims = out.claims.length;
      out.metrics.rank_counts = { 'تصريح مستورد': out.claims.length };
      out.layers = ['التركيب', 'القراءات والمرجع', 'حدود الفحص', 'الدافع والواقع'].map((title, i) => ({ id: i + 1, title,
        declared: null, summary: 'دعوى مستوردة؛ لم يُعد فحصها', claim_count: out.claims.filter(c => c.layer === i + 1).length, issues: [] }));
      check(out, 'SEMANTIC_AXIS_COUNTS', 'المقامات المستقلة لجهات الدلالة', 'pass', 'أُعيد العد لكل محور من صفوف الحالات؛ لا نسبة موحدة لاكتمال العربية.');
      out.limits.push('فحوص منع الإسناد غير المرخص مستقلة عن فهم الدافع أو إثبات الواقع. كل تصريح هنا مستورد؛ هذا الإصدار يرفض ترقية فحص Python إلى LEAN_NATIVE.');
    } else if (record.mode === 'benchmark') {
      const b = requireObject(record.benchmark, '$.benchmark');
      const rows = requireArray(b.rows, '$.benchmark.rows');
      const counts = { cases: rows.length, pass: 0, fail: 0, unmeasured: 0 };
      const ids = new Set();
      for (let i = 0; i < rows.length; i++) {
        const row = requireObject(rows[i], '$.benchmark.rows[' + i + ']');
        requireString(row.id, '$.benchmark.rows[' + i + '].id');
        if (ids.has(row.id)) fail('DUPLICATE_CASE', 'معرّف حالة مكرر.', '$.benchmark.rows[' + i + ']');
        ids.add(row.id);
        if (!['PASS','FAIL','UNMEASURED'].includes(row.outcome)) fail('SCHEMA_SHAPE', 'نتيجة حالة غير معروفة.', '$.benchmark.rows[' + i + '].outcome');
        counts[row.outcome.toLowerCase()]++;
      }
      const s = requireObject(b.summary, '$.benchmark.summary');
      const declared = { cases: s.cases ?? s.total, pass: s.pass ?? s.passed, fail: s.fail ?? s.failed, unmeasured: s.unmeasured };
      Object.entries(declared).forEach(([k,v]) => { if (!integer(v) || v < 0) fail('SCHEMA_SHAPE', 'عدد قياس غير صالح.', '$.benchmark.summary.' + k); });
      const match = Object.keys(counts).every(k => counts[k] === declared[k]);
      check(out, 'BENCHMARK_COUNTS', 'مقام القياس ونتائجه', match ? 'pass' : 'fail', 'أُعيد العد من الصفوف؛ هذه نسبة داخل المجموعة المستوردة فقط.');
      if (!match) finding(out, 'BENCHMARK_COUNT_MISMATCH', 'error', 'ملخص القياس لا يطابق صفوفه', 'لا تُستخدم الأعداد المعلنة في حساب المقام.');
      out.benchmark = { counts, rows, scope: b.scope ?? null, gold_sha256: b.gold_sha256 ?? null, declared_contract: b.contract_gate?.passed === true };
      out.metrics.benchmark_cases = counts.cases;
    } else {
      const result = record.result === undefined ? {} : requireObject(record.result, '$.result');
      authorityFinding(out, result, '$.result');
      for (const k of ['verified','native_checked','all_readings_complete','closures_checked']) optionalType(result, k, v => typeof v === 'boolean', '$.result');
      for (const k of ['readings','closure_records','assumptions','unclassified_spans']) optionalType(result, k, Array.isArray, '$.result');
      await inspectInput(out, result, false);
      optionalType(result, 'status', string, '$.result');
      optionalType(record, 'status', string, '$');
      out.declared_status = result.status ?? record.status ?? null;
      out.declared_verification = { verified: tri(result.verified), native_checked: tri(result.native_checked),
        all_readings_complete: tri(result.all_readings_complete), closures_checked: tri(result.closures_checked) };
      out.metrics.readings = array(result.readings).length;
      out.metrics.closures = array(result.closure_records).length;
      out.metrics.assumptions = array(result.assumptions).length;
      optionalType(result, 'authority', string, '$.result');
      const checkedFlags = ['native_checked','all_readings_complete','closures_checked'];
      const checkedStates = ['SUPPORTED','REFUTED','CONFLICT','UNKNOWN','DEFER','DISAGREEMENT'];
      const resultStates = [...checkedStates, 'INVALID_INPUT','SOURCE_UNAVAILABLE','VERIFICATION_UNAVAILABLE','RESOURCE_EXHAUSTED'];
      const statusConflict = (result.status != null && !resultStates.includes(result.status))
        || (record.status != null && !resultStates.includes(record.status))
        || (result.status != null && record.status != null && result.status !== record.status);
      const falseConflict = result.verified === false && (
        checkedFlags.some(k => result[k] === true)
        || (result.authority != null && result.authority !== 'UNVERIFIED_PROPOSAL')
        || ['SUPPORTED','REFUTED','CONFLICT','DEFER','DISAGREEMENT'].includes(result.status));
      const trueConflict = result.verified === true && (
        checkedFlags.some(k => result[k] === false)
        || (result.authority != null && result.authority !== 'SOURCE_RELATIVE_CONSEQUENCE')
        || (result.status != null && !checkedStates.includes(result.status)));
      if (trueConflict || falseConflict)
        finding(out, 'NABT_AUTHORITY_CONTRADICTION', 'error', 'تصريحات التحقق متناقضة',
          falseConflict ? 'verified=false مع علم فحص ناجح أو سلطة أو حكم لا يسمح به عقد النتيجة غير المتحققة.'
            : 'verified=true دون توافق أعلام الفحص والحالة وسلطة الاستدلال.');
      if (statusConflict)
        finding(out, 'NABT_STATUS_CONTRADICTION', 'error', 'حالة النتيجة غير متسقة',
          'الحالة خارج عقد NABT أو مختلفة بين الغلاف والنتيجة.');
      const completeDeclaration = typeof result.verified === 'boolean'
        && checkedFlags.every(k => typeof result[k] === 'boolean')
        && string(result.authority) && string(result.status);
      check(out, 'NABT_VERIFICATION_CONTRACT', 'اتساق تصريحات التحقق',
        trueConflict || falseConflict || statusConflict ? 'fail' : completeDeclaration ? 'pass' : 'unknown',
        'تُراجع العلاقة في الاتجاهين. الحقول الغائبة تظل غير محسومة، وأعلام النجاح بيانات مستوردة.');
      array(result.assumptions).forEach((a,i) => finding(out, 'DECLARED_ASSUMPTION_' + i, 'info', 'افتراض معلن', display(a), 4));
      if (array(result.unclassified_spans).length) finding(out, 'UNCLASSIFIED_SPANS', 'warning', 'بقايا نص غير مصنفة', 'يحفظ السجل أجزاء لم يصنفها المسار. لا تتحول إلى دليل ضمني.', 1);
      if (out.input) importedClaim('source_raw_text', 1, 'النص الأصلي كما سجّله NABT', out.input.text);
      if (object(result.query) && own(result.query, 'raw_text')) {
        requireString(result.query.raw_text, '$.result.query.raw_text');
        importedClaim('query_raw_text', 1, 'الاستعلام الأصلي كما سجّله NABT', result.query.raw_text);
      }
      if (own(result, 'readings')) importedClaim('declared_readings', 2, 'القراءات المحفوظة في السجل', result.readings);
      if (own(result, 'unclassified_spans')) importedClaim('declared_unclassified_spans', 2, 'بقايا النص غير المصنفة', result.unclassified_spans);
      if (own(result, 'status')) importedClaim('declared_inference_status', 3, 'حالة الاستدلال المعلنة', result.status);
      else if (own(record, 'status')) importedClaim('declared_execution_status', 3, 'حالة التنفيذ المعلنة', record.status);
      const flagLabels = { verified: 'تصريح قبول الشهادة', native_checked: 'تصريح الفحص الأصلي',
        all_readings_complete: 'تصريح اكتمال القراءات ضمن القانون', closures_checked: 'تصريح فحص الإغلاق' };
      for (const [key, label] of Object.entries(flagLabels)) if (own(result, key)) importedClaim('declared_' + key, 3, label, result[key]);
      if (own(result, 'closure_records')) importedClaim('declared_closures', 3, 'سجلات الإغلاق المحفوظة', result.closure_records);
      if (own(result, 'assumptions')) importedClaim('declared_assumptions', 4, 'الافتراضات المعلنة', result.assumptions);
      for (const [key, label] of [['world_truth_established','تصريح مطابقة الواقع'],['all_arabic_complete','تصريح اكتمال العربية كلها']]) {
        if (own(result, key)) importedClaim('declared_result_' + key, 4, label + ' داخل النتيجة', result[key]);
        if (own(record, key)) importedClaim('declared_wrapper_' + key, 4, label + ' في الغلاف', record[key]);
      }
      out.metrics.claims = out.claims.length;
      out.metrics.rank_counts = { 'تصريح مستورد': out.claims.length };
      const labels = ['النص الأصلي', 'القراءات والقضايا', 'الاستدلال والإغلاق', 'الافتراضات والواقع'];
      out.layers = labels.map((title,i) => ({ id: i + 1, title, declared: null, summary: 'بيانات سجل NABT مستورد؛ ليست إعادة تحقق', claim_count: out.claims.filter(c => c.layer === i + 1).length,
        issues: out.findings.filter(f => f.layer === i + 1).map(f => f.id) }));
      out.limits.push('هذه أوجه عرض لسجل NABT، وليست ادعاءً بأن بنيته تطابق طبقات Mashru اصطلاحيًا.');
    }
    finding(out, 'IMPORTED_REPORT_UNAUTHENTICATED', 'warning', 'التقرير المستورد غير مصادق عليه', 'المعرفات والبصمات وأعلام النجاح قابلة للكتابة داخل ملف JSON. يظل مسار التنفيذ الحي الموثق منفصلًا.');
    return out;
  }

  async function audit(raw) {
    const record = parse(raw);
    if (record.schema === 'Tabaqat4Record:v1') return tabaqat(raw, record);
    if (record.schema === 'nabt.proof-lab-result.v1') return nabt(raw, record);
    fail('UNSUPPORTED_SCHEMA', 'المخططات المدعومة: Tabaqat4Record:v1 وnabt.proof-lab-result.v1.', '$.schema');
  }
  globalThis.NabtEvidenceAudit = Object.freeze({ parse, audit, limits: LIMITS, version: VERSION, AuditInputError });
})();
