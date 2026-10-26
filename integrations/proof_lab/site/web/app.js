'use strict';

(() => {
  const $ = id => document.getElementById(id);
  const number = value => Number.isFinite(value) ? value.toLocaleString('ar-JO') : '—';
  const byteLength = value => new TextEncoder().encode(value).length;
  const pendingKey = 'nabt.proof-lab.pending.v1';
  const state = { config: null, pending: null, timer: null, elapsedTimer: null, failures: 0, inference: null, benchmark: null, semantic_axes: null, epistemic_measurement: null, contextual_reference: null, snapshot: null, submitted: null, pollCount: 0 };
  const examples = {
    supported: { source: 'إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ. عَرَفَ زَيْدٌ الْحَقَّ.', query: 'هَلْ سَارَ زَيْدٌ؟', note: 'تتحقق مقدمة الشرط في النص، فيُختبر إمكان اشتقاق الجواب.' },
    missing: { source: 'إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ.', query: 'هَلْ سَارَ زَيْدٌ؟', note: 'وجود قاعدة شرطية وحده لا يثبت وقوع مقدمتها أو جوابها.' },
    hidden: { source: 'سَارَ زَيْدٌ أَمَامَكَ خَلْفَ الدَّارِ إِنْ عَرَفَ الْحَقَّ.', query: 'هَلْ سَارَ زَيْدٌ أَمَامَكَ خَلْفَ الدَّارِ؟', note: 'فاعل «عَرَفَ» غير مصرح به. هذه النسخة لا تحسم الإحالة تلقائيًا.' },
    inverse: { source: 'إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ. لَمْ يَعْرِفْ زَيْدٌ الْحَقَّ.', query: 'هَلْ لَمْ يَسِرْ زَيْدٌ؟', note: 'نفي مقدمة الشرط لا يرخص نفي الجواب بمجرد الشرط. يتطلب المفهوم ترخيصًا مستقلًا.' },
    outside: { source: 'إِنْ عَرَفَ خَالِدٌ الْحَقَّ رَكَضَ خَالِدٌ. عَرَفَ خَالِدٌ الْحَقَّ.', query: 'هَلْ رَكَضَ خَالِدٌ؟', note: 'خالد وركض خارج معجم هذا المسار. تعليق النتيجة لا يعني الحكم بخطأ الجملة العربية.' }
  };
  const statuses = {
    SUPPORTED: ['الاستنتاج مدعوم', 'تدعم المقدمات الاستعلام وفق القراءات المرخّصة في هذه النسخة. هذا حكم بالنسبة إلى النص، وليس إثباتًا لوقوعه في العالم.', 'positive'],
    REFUTED: ['نقيض الاستنتاج مدعوم', 'يدعم النص نقيض الاستعلام ضمن القانون المعلن. لا يمتد هذا الحكم تلقائيًا إلى صدق الخبر في الواقع.', 'warning'],
    UNKNOWN: ['الاستنتاج غير معلوم', 'لم يُستوفَ دليل مرخّص على الاستعلام أو نقيضه. راجع سبب النتيجة؛ غياب الدليل لا يُعدّ نفيًا.', 'warning'],
    DEFER: ['الاستنتاج معلّق', 'ظهر دعم لا يحقق شروط الحكم الموحد أو السليم من التعارض. يحتفظ المحرك بسبب التعليق والأدلة.', 'warning'],
    CONFLICT: ['تعارض داخل القراءة', 'توجد أدلة متقابلة داخل قراءة مفحوصة. يعرض المحرك التعارض ولا يشتق منه أي نتيجة عشوائية.', 'negative'],
    DISAGREEMENT: ['اختلاف بين القراءات', 'تختلف القراءات في جهة الدعم. لا تُحذف قراءة للوصول إلى جواب واحد.', 'warning'],
    RESOURCE_EXHAUSTED: ['انتهت ميزانية البحث', 'توقف التنفيذ عند حد الموارد المحدد. لم يصدر عن ذلك حكم برفض العبارة لغويًا أو نفي الاستنتاج.', 'warning'],
    RESOURCE_LIMIT: ['انتهت ميزانية البحث', 'تم بلوغ حد الموارد. لا تتحول هذه النتيجة إلى حكم لغوي.', 'warning'],
    INVALID_INPUT: ['المدخل غير صالح للمسار', 'تعذر قبول شكل الطلب أو النص وفق عقد الإدخال. راجع السبب قبل إعادة المحاولة.', 'negative'],
    SOURCE_UNAVAILABLE: ['دليل المصدر غير متاح', 'تعذر استيفاء المصدر المطلوب للتحقق. لا تُمنح سلطة لشهادة غير مكتملة.', 'warning'],
    VERIFICATION_UNAVAILABLE: ['تعذّر التحقق', 'لم يكتمل تشغيل مسار التحقق. لا توجد شهادة مقبولة لهذه المحاولة.', 'warning']
  };
  const families = { original_unresolved:'الإحالة غير المحسومة', conditional_only:'الشرط بلا مقدمة', forward:'الاشتقاق الأمامي', order_invariance:'ترتيب المقدمات', front_conditional:'الشرط المتقدم', no_inverse:'منع عكس الشرط', negative_consequent:'الجواب المنفي', signed_states:'الإثبات والنفي', derived_conflict:'التعارض المشتق', no_explosion:'منع انفجار التعارض', subject_identity:'هوية الفاعل', frame_identity:'هوية الإطار', preserved_adjuncts:'حفظ القيود', quote_boundary:'حدود الاقتباس', question_boundary:'حدود الاستفهام', trailing_input:'بقايا النص', partial_condition:'الشرط الناقص', query_boundary:'حدود الاستعلام', unknown_vocabulary:'حدود المعجم', provenance:'إسناد المصدر', resource:'الموارد', invalid_input:'صلاحية المدخل', aggregation:'تجميع الأدلة' };

  function text(id, value) { $(id).textContent = value == null ? '—' : String(value); }
  function showMessage(message) { $('global-message').hidden = !message; text('global-message', message || ''); }
  function switchTab(name, focus = false) {
    if (!['evidence','inference','coverage','testimony','semantic_axes','guide','epistemic_measurement','contextual_reference'].includes(name)) return;
    document.querySelectorAll('[data-tab]').forEach(tab => { const selected = tab.dataset.tab === name; tab.setAttribute('aria-selected', String(selected)); tab.tabIndex = selected ? 0 : -1; });
    ['evidence','inference','coverage','testimony','semantic_axes','guide','epistemic_measurement','contextual_reference'].forEach(tab => { $('panel-' + tab).hidden = tab !== name; });
    if (focus) $('tab-' + name).focus();
  }
  document.querySelectorAll('[data-tab]').forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));
  document.querySelectorAll('[data-tab-link]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); switchTab(link.dataset.tabLink, true); $('workbench').scrollIntoView({behavior:'smooth',block:'start'}); }));
  document.querySelector('.tabs').addEventListener('keydown', event => {
    const tabs = [...document.querySelectorAll('[data-tab]')];
    let index = tabs.indexOf(document.activeElement);
    if (index < 0) return;
    if (event.key === 'ArrowLeft') index = (index + 1) % tabs.length;
    else if (event.key === 'ArrowRight') index = (index + tabs.length - 1) % tabs.length;
    else if (event.key === 'Home') index = 0;
    else if (event.key === 'End') index = tabs.length - 1;
    else return;
    event.preventDefault(); switchTab(tabs[index].dataset.tab, true);
  });
  function updateInputState() {
    text('source-count', number(byteLength($('source-text').value)) + ' بايت');
    if (state.snapshot && state.inference) {
      let budgetSame = true;
      if (state.snapshot.budget) { try { budgetSame = JSON.stringify(state.snapshot.budget) === JSON.stringify(getBudget()); } catch { budgetSame = false; } }
      $('stale-note').hidden = state.snapshot.source === $('source-text').value && state.snapshot.query === $('query-text').value && budgetSame;
    }
  }
  for (const id of ['source-text','query-text']) $(id).addEventListener('input', () => { document.querySelectorAll('[data-example]').forEach(button => button.classList.remove('active')); updateInputState(); });
  for (const id of ['budget-clauses','budget-readings','budget-atoms','budget-steps']) $(id).addEventListener('input', updateInputState);
  document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
    const item = examples[button.dataset.example];
    $('source-text').value = item.source; $('query-text').value = item.query; text('example-note', item.note);
    document.querySelectorAll('[data-example]').forEach(other => other.classList.toggle('active', other === button)); updateInputState();
  }));
  function enableActions() {
    const disabled = !state.config?.ready || !!state.pending;
    $('run-inference').disabled = disabled; $('run-benchmark').disabled = disabled; $('run-testimony').disabled = disabled; $('run-semantic-axes').disabled = disabled; $('run-epistemic-measurement').disabled = disabled; $('run-contextual-reference').disabled = disabled;
    $('semantic-lexical-profile').disabled = !!state.pending;
  }
  async function request(path, options = {}) {
    const response = await fetch(path, { credentials:'same-origin', cache:'no-store', ...options, headers: { 'Accept':'application/json', ...options.headers }, signal:AbortSignal.timeout(45000) });
    let body;
    try { body = await response.json(); } catch { throw new Error(response.status === 401 || response.status === 403 ? 'يلزم تسجيل الدخول إلى الصفحة الخاصة للوصول إلى المحرك.' : 'تعذر قراءة استجابة الخادم. لم تُقبل شهادة.'); }
    if (!response.ok) {
      const raw = typeof body.error === 'string' ? body.error : body.error?.message || body.message;
      const hints = {401:'يلزم تسجيل الدخول إلى الصفحة الخاصة.',403:'لا تسمح صلاحية الجلسة بتنفيذ هذا الطلب.',429:'يوجد طلب جارٍ أو تم بلوغ حد التكرار. انتظر ثم أعد المحاولة.',503:'خدمة الاختبار غير جاهزة. لم يُنفّذ فحص برهاني.'};
      throw new Error(hints[response.status] || (typeof raw === 'string' ? raw : 'تعذر تنفيذ الطلب (HTTP ' + response.status + ').'));
    }
    return body;
  }
  async function loadConfig() {
    try {
      const config = await request('/api/config'); state.config = config;
      $('connection').className = 'connection ' + (config.ready ? 'ready' : 'error');
      text('connection-text', config.ready ? 'المحرك متصل · تنفيذ فعلي في Lean' : 'المحرك غير جاهز للتنفيذ');
      text('code-sha', typeof config.code_sha === 'string' ? config.code_sha.slice(0, 10) : '—');
      text('law-label', config.law || 'nabt.licensed-inference.v1');
      if (config.baseline) { text('baseline-pass', config.baseline.passed ?? 37); text('baseline-total', config.baseline.total ?? 38); }
      const limits = config.limits || {};
      for (const [name,id] of [['max_clauses','budget-clauses'],['max_readings','budget-readings'],['max_atoms','budget-atoms'],['max_closure_steps','budget-steps']]) {
        if (Number.isInteger(limits[name]) && limits[name] >= 0) { $(id).max = String(limits[name]); $(id).value = String(Math.min(Number($(id).value),limits[name])); }
      }
      if (!config.ready) showMessage('مرصد الأدلة متاح محليًا. ينتظر تنفيذ Lean الحي تفعيل مفتاح النقل الآمن بين الصفحة وGitHub؛ تدقيق السجل المستورد متاح دون ذلك.');
    } catch (error) { $('connection').className='connection error'; text('connection-text','تعذر الاتصال بالمحرك'); showMessage(error.message); }
    enableActions();
  }
  function getBudget() {
    const result = {};
    for (const [name,id] of [['max_clauses','budget-clauses'],['max_readings','budget-readings'],['max_atoms','budget-atoms'],['max_closure_steps','budget-steps']]) {
      const value = $(id).valueAsNumber;
      if (!Number.isInteger(value) || value < 0 || value > Number($(id).max)) throw new Error('حدود ميزانية البحث أعداد صحيحة ضمن المجال الظاهر.');
      result[name] = value;
    }
    return result;
  }
  async function submit(mode) {
    if (state.pending || !state.config?.ready) return;
    showMessage('');
    let payload;
    try {
      payload = {schema:'nabt.proof-lab-request.v1',mode};
      if (mode === 'semantic_axes') {
        const profile = $('semantic-lexical-profile').value || 'teaching_v1';
        if (!['teaching_v1','attested_qac_v1'].includes(profile)) throw new Error('المسار المعجمي غير معروف.');
        if (profile === 'attested_qac_v1') payload.lexical_profile = profile;
      }
      if (mode === 'inference') {
        if (!$('inference-form').reportValidity()) return;
        const source = $('source-text').value, query = $('query-text').value;
        if (byteLength(source) > 16384 || byteLength(query) > 4096) throw new Error('يتجاوز النص حد المختبر: ١٦٣٨٤ بايت للمقدمات و٤٠٩٦ بايت للاستعلام.');
        payload.source_text = source; payload.query_text = query; payload.budget = getBudget();
      }
      if (mode === 'testimony') {
        if (!$('testimony-form').reportValidity()) return;
        payload.entry = $('testimony-entry').value;
        payload.target = $('testimony-target').value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
        if (!payload.target.length || payload.target.length>64 || byteLength(payload.entry)>128 || payload.target.some(s=>byteLength(s)>4096)) throw new Error('المدخل أو المكونات يتجاوز حدود الشهادة.');
      }
      $('run-inference').disabled = true; $('run-benchmark').disabled = true; $('run-testimony').disabled = true; $('run-semantic-axes').disabled = true; $('run-epistemic-measurement').disabled = true; $('run-contextual-reference').disabled = true;
      if (mode === 'semantic_axes') { state.semantic_axes = null; globalThis.NabtSemanticAxes?.reset('جارٍ طلب قياس جديد؛ لا شهادة معروضة حتى اكتماله.'); }
      if (mode === 'epistemic_measurement') { state.epistemic_measurement = null; globalThis.NabtEpistemicMeasurement?.reset('جارٍ طلب القياس؛ لا شهادة معروضة حتى اكتماله.'); }
      if (mode === 'contextual_reference') { state.contextual_reference = null; globalThis.NabtContextualReference?.reset('جارٍ طلب القياس؛ لا شهادة معروضة حتى اكتماله.'); }
      const result = await request('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      if (typeof result.handle !== 'string' || typeof result.request_id !== 'string') throw new Error('استجابة إرسال غير مكتملة. راجع سجل GitHub قبل إعادة الإرسال لتجنب تكرار الطلب.');
      state.pending = {handle:result.handle,request_id:result.request_id,mode,started:Date.now()};
      if (mode === 'semantic_axes') state.pending.lexical_profile = payload.lexical_profile || 'teaching_v1';
      state.submitted = {request_id:result.request_id,payload};
      state.failures=0; state.pollCount=0;
      try { sessionStorage.setItem(pendingKey,JSON.stringify(state.pending)); } catch { /* Polling still works without browser persistence. */ }
      prepareJob(); schedulePoll(result.poll_after_ms);
    } catch (error) { showMessage(error.name === 'TimeoutError' ? 'انتهت مهلة الإرسال. قد يكون GitHub قد استقبل الطلب؛ راجع التنفيذ قبل المحاولة مجددًا.' : error.message); }
    enableActions();
  }
  $('inference-form').addEventListener('submit',event=>{event.preventDefault();submit('inference');});
  $('run-benchmark').addEventListener('click',()=>submit('benchmark'));
  $('run-semantic-axes').addEventListener('click',()=>submit('semantic_axes'));
  $('run-epistemic-measurement').addEventListener('click',()=>submit('epistemic_measurement'));
  $('run-contextual-reference').addEventListener('click',()=>submit('contextual_reference'));
  $('testimony-form').addEventListener('submit',event=>{event.preventDefault();submit('testimony');});
  function prepareJob() {
    $('job-panel').hidden=false; $('job-spinner').hidden=false; $('resume-poll').hidden=true; $('job-link').hidden=true;
    text('job-id',state.pending.request_id);text('job-title','الطلب في انتظار التنفيذ');text('job-description',state.pending.mode==='semantic_axes'?'سيعيد GitHub تشغيل المقارن المرجعي وفحص Python على النسخة المثبتة. لا يتضمن هذا المسار شهادة Lean للدعاوى.':'سيبني GitHub النسخة المثبتة ويشغّل الفحص. مدة الانتظار ليست دليلًا على قبول النتيجة.');
    if(state.elapsedTimer) clearInterval(state.elapsedTimer);
    state.elapsedTimer=setInterval(updateElapsed,1000); updateElapsed();
  }
  function updateElapsed() {
    if (!state.pending) return;
    const seconds=Math.max(0,Math.floor((Date.now()-state.pending.started)/1000));
    text('job-elapsed',Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0'));
  }
  function schedulePoll(delay = 5000) {
    clearTimeout(state.timer);
    state.timer=setTimeout(poll,Math.min(15000,Math.max(5000,Number(delay)||5000)));
  }
  function pausePolling(message) {
    clearTimeout(state.timer);$('job-spinner').hidden=true;$('resume-poll').hidden=false;
    text('job-title','توقفت المتابعة الآلية');text('job-description',message);
  }
  async function poll() {
    if (!state.pending) return;
    if (Date.now()-state.pending.started>25*60*1000) { pausePolling('طال الانتظار. لم يتحول ذلك إلى حكم لغوي. يمكنك استئناف متابعة الطلب نفسه؛ لم يُرسل طلب جديد.'); return; }
    try {
      const result=await request('/api/runs?handle='+encodeURIComponent(state.pending.handle));
      state.pollCount++;
      if (typeof result.run_url==='string' && /^https:\/\/github\.com\/sonaiso\/NABT\/actions\/runs\/\d+$/.test(result.run_url)) { $('job-link').href=result.run_url;$('job-link').hidden=false; }
      if (result.status==='queued') { text('job-title','الطلب في انتظار GitHub');text('job-description','حُفظ معرف الطلب. ستظهر النتيجة بعد اكتمال الفحص على الخادم.'); }
      else if (result.status==='in_progress') {text('job-title','جارٍ تنفيذ الفحص');text('job-description',state.pending.mode==='semantic_axes'?'تجري إعادة فحص Python والمقارنة بالمقامات المستقلة. لم تنتهِ مطابقة التقرير بالطلب بعد.':'يعمل مسار Lean على النسخة المثبتة. لا توجد نتيجة نهائية حتى انتهاء التنفيذ وفحص هوية التقرير.');}
      else if (result.status==='completed') {
        if (!result.report || result.report.request_id!==state.pending.request_id || result.report.mode!==state.pending.mode) throw new Error('لا تتطابق هوية التقرير مع الطلب الجاري. لم تُعرض نتيجة.');
        if(result.report.schema!=='nabt.proof-lab-result.v1' || result.report.all_arabic_complete!==false || result.report.world_truth_established!==false) throw new Error('التقرير يخالف نطاق المختبر المعلن؛ لم تُعرض دعوى غير مرخّصة.');
        const mode=state.pending.mode;
        if(mode==='semantic_axes'&&result.report.semantic_axes&&((result.report.semantic_axes.lexical_profile||'teaching_v1')!==(state.pending.lexical_profile||'teaching_v1')||(Object.hasOwn(result.report,'lexical_profile')&&result.report.lexical_profile!==(state.pending.lexical_profile||'teaching_v1'))))throw new Error('المسار المعجمي في النتيجة لا يطابق الطلب؛ لم تُعرض نتيجة بديلة.');
        if(mode==='inference')renderInference(result.report);else if(mode==='testimony')renderTestimony(result.report);else if(mode==='semantic_axes'){globalThis.NabtSemanticAxes.render(result.report);state.semantic_axes=result.report;}else if(mode==='epistemic_measurement'){await globalThis.NabtEpistemicMeasurement.render(result.report);state.epistemic_measurement=result.report;}else if(mode==='contextual_reference'){await globalThis.NabtContextualReference.render(result.report, {live:true});state.contextual_reference=result.report;}else renderBenchmark(result.report);
        text('job-title','اكتمل التنفيذ واستلام التقرير');text('job-description','النتيجة أدناه مرتبطة بمعرف الطلب وإصدار الشفرة. اكتمال التنفيذ لا يعني أن الاستنتاج مدعوم.');
        finishPending(); return;
      } else if (result.status==='failed') {
        if(state.pending.mode==='semantic_axes'){state.semantic_axes=null;globalThis.NabtSemanticAxes?.reset('تعذّر إكمال التنفيذ؛ لا نتيجة أو شهادة لهذه المحاولة.');}
        if(state.pending.mode==='epistemic_measurement'){state.epistemic_measurement=null;globalThis.NabtEpistemicMeasurement?.reset('تعذّر إكمال التنفيذ؛ لا نتيجة أو شهادة لهذه المحاولة.');}
        if(state.pending.mode==='contextual_reference'){state.contextual_reference=null;globalThis.NabtContextualReference?.reset('تعذّر إكمال التنفيذ؛ لا شهادة لهذه المحاولة.');}
        text('job-title','تعذّر إكمال التنفيذ');text('job-description',typeof result.error==='string'?result.error:'راجع سجل GitHub. لم تُنتج هذه المحاولة شهادة مقبولة.');
        finishPending(); return;
      } else throw new Error('حالة تشغيل غير معروفة من الخادم.');
      state.failures=0;
      schedulePoll(state.pollCount>12?10000:5000);
    } catch(error) {
      state.failures++;
      if(state.failures>=3){pausePolling('تعذر جلب حالة الطلب: '+error.message+' يمكنك استئناف متابعته دون إعادة إرساله.');return;}
      text('job-description','تعذر جلب الحالة مؤقتًا. تُعاد محاولة متابعة الطلب نفسه.');schedulePoll(10000);
    }
  }
  function finishPending(){clearTimeout(state.timer);clearInterval(state.elapsedTimer);state.pending=null;$('job-spinner').hidden=true;$('resume-poll').hidden=true;try{sessionStorage.removeItem(pendingKey);}catch{}enableActions();}
  $('resume-poll').addEventListener('click',()=>{if(!state.pending)return;state.pending.started=Date.now();state.failures=0;$('job-spinner').hidden=false;$('resume-poll').hidden=true;poll();});
  function addTrace(label,content){const item=document.createElement('div');item.className='trace-item';const heading=document.createElement('span');heading.textContent=label;const p=document.createElement('p');p.textContent=content;item.append(heading,p);$('proof-trace').append(item);}
  function literal(atom){if(!atom||typeof atom.predicate!=='string')return 'قضية غير معروضة';return (atom.positive===false?'نفي: ':'')+atom.predicate+' '+(Array.isArray(atom.arguments)?atom.arguments.map(String).join(' · '):'');}
  function renderInference(report){
    state.inference=report;const result=report.result||{};
    const status=result.status||report.status||'VERIFICATION_UNAVAILABLE';const info=statuses[status]||['نتيجة غير مصنفة','راجع التقرير الخام؛ لم تُمنح هذه الحالة وصفًا برهانيًا تلقائيًا.','warning'];
    $('inference-empty').hidden=true;$('inference-output').hidden=false;
    text('result-marker',info[0]);$('result-marker').className='result-marker '+info[2];$('result-verdict').className='result-verdict '+info[2];
    text('verdict-code',status);text('verdict-title',info[0]);text('verdict-description',info[1]);
    text('native-status',result.native_checked===true&&result.verified===true?'شهادة مفحوصة':'لم تثبت شهادة مقبولة');
    text('readings-status',result.all_readings_complete===true?number((result.readings||[]).length)+' · مكتملة ضمن القانون':'لم يُثبت اكتمالها');
    text('closure-status',result.closures_checked===true?'مفحوصة':'غير مثبتة');
    const reason=result.reason||report.error?.code||report.error||'لا سبب مسجّل';
    text('result-reason',typeof reason==='string'?reason:JSON.stringify(reason));
    const reasonNotes={UNRESOLVED_REFERENCE:'لم تُحسم إحالة الفاعل المستتر، فلا تُختار هوية بالحدس.',OUTSIDE_FRAGMENT:'يتضمن النص أو الاستعلام مفردة أو تركيبًا خارج القانون المثبت في هذا المسار.',CHECKED_INSTALLED_GRAMMAR_AND_SOURCE_THEORY:'فُحصت القراءة وشهادة الإغلاق بالنسبة إلى القانون والمقدمات المثبتة.',MAX_CLAUSES:'عدد الجمل تجاوز الميزانية المحددة.',MAX_READINGS:'ميزانية القراءات لا تكفي لإتمام الفحص.',MAX_ATOMS:'عدد القضايا بلغ حد الميزانية.',MAX_CLOSURE_STEPS:'خطوات الإغلاق تجاوزت الحد المحدد.',MAX_CERTIFICATE_BYTES:'حجم الشهادة تجاوز الحد المسموح.'};
    text('result-reason-explanation',reasonNotes[reason]||'السبب التقني محفوظ أدناه وفي التقرير الكامل. لا يُستبدل حكم مفقود بنتيجة مفترضة.');
    $('proof-trace').replaceChildren();
    const records=Array.isArray(result.closure_records)?result.closure_records:[];
    if(result.native_checked===true&&result.verified===true&&records.length){
      const first=records[0];const steps=Array.isArray(first.steps)?first.steps:[];
      const facts=(first.clauses||[]).filter(c=>c.kind==='fact');const rules=(first.clauses||[]).filter(c=>c.kind==='rule');
      steps.slice(0,12).forEach(step=>{if(step.kind==='fact'&&facts[step.index])addTrace('مقدمة من النص',literal(facts[step.index].atom));else if(step.kind==='rule'&&rules[step.index]){const rule=rules[step.index];addTrace('تطبيق قاعدة مرخّصة',(rule.body||[]).map(literal).join(' و ')+' ← '+literal(rule.head));}});
      if(steps.length>12)addTrace('الخطوات الباقية',number(steps.length-12)+' خطوة إضافية محفوظة في الشهادة القابلة للتنزيل.');
      if(!steps.length)addTrace('إغلاق خالٍ من الاشتقاق','لم تسجل القراءة خطوات دعم للاستعلام.');
      if(records.length>1)addTrace('القراءات الأخرى',number(records.length-1)+' قراءة إضافية محفوظة في الأدلة التفصيلية.');
    }else{const p=document.createElement('p');p.className='trace-empty';p.textContent='لا يوجد مسار اشتقاق مقبول يمكن عرضه لهذه المحاولة. راجع سبب التعليق أو التعذر.';$('proof-trace').append(p);}
    const source=result.source?.raw_text||result.native_result?.source_text;
    const query=result.query?.raw_text||result.native_result?.query_text;
    state.snapshot=typeof source==='string'&&typeof query==='string'?{source,query,budget:state.submitted?.request_id===report.request_id?state.submitted.payload.budget:null}:null;
    $('stale-note').hidden=true;
    text('inference-request-id',report.request_id);
    text('executed-source',source??'لم يُحتفظ بالنص في نتيجة التنفيذ هذه.');text('executed-query',query??'لم يُحتفظ بالاستعلام في نتيجة التنفيذ هذه.');
    text('reading-json',JSON.stringify({readings:result.readings||[],aggregate:result.aggregate||null,unclassified_spans:result.unclassified_spans||[],assumptions:result.assumptions||[],all_readings_complete:result.all_readings_complete===true,all_arabic_complete:false},null,2));
    text('inference-timing','زمن المحرك: '+number(report.duration_ms)+' مللي ثانية');text('inference-commit','commit '+String(report.code_sha||'—').slice(0,12));updateInputState();
  }
  function renderTestimony(report){
    state.testimony=report;const t=report.testimony;
    $('testimony-output').hidden=false;$('testimony-rows').replaceChildren();
    text('testimony-json',JSON.stringify(report,null,2));
    text('testimony-input',t?'المدخل المفحوص: '+t.entry+' · المكونات: '+(t.target||[]).join('، '):'');
    text('testimony-status',t?.native_checked===true?(t.rows.length?'Lean مفعل · دلالات مشروطة مفحوصة':'Lean مفعل · المدخل خارج السجل المثبت'):'لم تُقبل شهادة: '+String(report.status));
    text('testimony-disclaimer',t?.app_disclaimer||'تعذر إكمال فحص الشهادة.');
    text('testimony-scope',t?.native_checked===true?'نوع النقل غير مقيّم. التفسير الدلالي مؤلف وغير محكّم استقلالًا. النتيجة لا تعيّن مراد متكلم بعينه.':'راجع سبب التعذر في التقرير.');
    if(!t?.native_checked)return;
    for(const row of t.rows){
      const card=document.createElement('article');card.className='testimony-card';
      const heading=document.createElement('h4');heading.textContent=row.sense_id;
      const source=document.createElement('p');source.textContent=row.testimony.author+' · '+row.testimony.work_title;
      const quote=document.createElement('blockquote');quote.textContent=row.testimony.citation.quotation;
      const transfer=document.createElement('p');transfer.className='field-help';transfer.textContent=row.testimony.source_file_replayed?'النقل: أُعيد فحص بايتات المصدر المحفوظ. لا حكم على صحة الرواية تاريخيًا.':'النقل: طابق الاقتباس السجل المثبت؛ لم يُعَد فحص ملف الأصل في هذا التشغيل.';
      const indications=document.createElement('p');indications.textContent=Object.entries({mutabaqa:'المطابقة',tadammun:'التضمن',iltizam:'الالتزام'}).map(([k,label])=>label+': '+(row.indications[k]===true?'مقبولة في التفسير':'غير مثبتة لهذا الهدف')).join(' · ');
      const condition=document.createElement('p');condition.className='field-help';condition.textContent=row.commitment_conditions.length?'قاعدة اللزوم مقدمة منقولة ومربوطة بهذه القراءة؛ لا تثبت واقعة أو علة حكم.':'لا توجد قاعدة لزوم مودعة لهذه القراءة.';
      card.append(heading,source,quote,transfer,indications,condition);$('testimony-rows').append(card);
    }
  }
  function renderBenchmark(report){
    state.benchmark=report;
    const benchmark=report.benchmark;
    if(!benchmark||!benchmark.summary){showMessage('لم يتضمن التقرير قياسًا مكتملًا. الحالة: '+String(report.status||report.error||'تعذر القياس'));return;}
    const summary=benchmark.summary;const total=summary.cases??summary.total;const passed=summary.pass??summary.passed;const failed=summary.fail??summary.failed;const unmeasured=summary.unmeasured;
    if(![total,passed,failed,unmeasured].every(v=>Number.isInteger(v)&&v>=0)||total!==passed+failed+unmeasured||!Array.isArray(benchmark.rows)||benchmark.rows.length!==total){showMessage('مقام القياس لا يطابق أعداد النتائج. لم تُعرض نسبة غير متسقة.');return;}
    $('benchmark-empty').hidden=true;$('benchmark-output').hidden=false;
    text('bench-pass',number(passed));text('bench-fail',number(failed));text('bench-unmeasured',number(unmeasured));text('bench-total',number(total));
    text('benchmark-contract',benchmark.contract_gate?.passed===true?'اجتازت عقود سلامة التنفيذ وحدود السلطة. هذه بوابة سلامة، وليست إعلانًا باجتياز كل حالات القياس.':'لم تثبت سلامة جميع عقود التنفيذ. راجع التقرير قبل اعتماد المقارنة.');
    for(const[id,value]of[['pass-bar',passed],['fail-bar',failed],['unknown-bar',unmeasured]])$(id).style.width=(total?value/total*100:0)+'%';
    text('benchmark-ratio',number(passed)+' من '+number(total)+' حالة مطابقة للتوقع، ضمن هذه المجموعة وحدها.');
    text('benchmark-request-id',report.request_id);
    text('benchmark-timing','زمن القياس: '+number(report.duration_ms)+' مللي ثانية');text('benchmark-commit','commit '+String(report.code_sha||'—').slice(0,12));renderRows();
  }
  function renderRows(){
    $('benchmark-rows').replaceChildren();const filter=$('case-filter').value;let count=0;
    for(const row of state.benchmark?.benchmark?.rows||[]){
      if(filter!=='all'&&row.outcome!==filter)continue;count++;
      const tr=document.createElement('tr');const id=document.createElement('td');id.textContent=String(row.id||'—');id.dir='ltr';
      const family=document.createElement('td');family.textContent=families[row.family]||String(row.family||'—');
      const outcome=document.createElement('td');const badge=document.createElement('span');badge.className='outcome-badge '+(row.outcome==='FAIL'?'fail':row.outcome==='PASS'?'':'unknown');badge.textContent=row.outcome==='PASS'?'مطابق':row.outcome==='FAIL'?'فجوة':'غير مقاس';outcome.append(badge);
      const detail=document.createElement('td');const disclosure=document.createElement('details');const summary=document.createElement('summary');summary.textContent='عرض الدليل';const pre=document.createElement('pre');pre.dir='ltr';pre.textContent=JSON.stringify({mode:row.mode,checks:row.checks,observed:row.observed},null,2);disclosure.append(summary,pre);detail.append(disclosure);tr.append(id,family,outcome,detail);$('benchmark-rows').append(tr);
    }
    $('empty-filter').hidden=count>0;
  }
  $('case-filter').addEventListener('change',renderRows);
  function download(report){if(!report)return;const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json;charset=utf-8'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='nabt-'+report.mode+'-'+String(report.request_id||'report').replace(/[^a-zA-Z0-9-]/g,'')+'.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  $('download-inference').addEventListener('click',()=>download(state.inference));$('download-benchmark').addEventListener('click',()=>download(state.benchmark));$('download-testimony').addEventListener('click',()=>download(state.testimony));$('download-semantic-axes').addEventListener('click',()=>download(state.semantic_axes));$('download-epistemic-measurement').addEventListener('click',()=>download(state.epistemic_measurement));$('download-contextual-reference').addEventListener('click',()=>download(state.contextual_reference));
  updateInputState();
  loadConfig().then(()=>{
    try{const saved=JSON.parse(sessionStorage.getItem(pendingKey)||'null');if(saved&&typeof saved.handle==='string'&&typeof saved.request_id==='string'&&['inference','benchmark','testimony','semantic_axes','epistemic_measurement','contextual_reference'].includes(saved.mode)&&Number.isFinite(saved.started)){state.pending=saved;prepareJob();switchTab(saved.mode==='benchmark'?'coverage':saved.mode);enableActions();poll();}}catch{try{sessionStorage.removeItem(pendingKey);}catch{}}
  });
})();
