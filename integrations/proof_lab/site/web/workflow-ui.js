(() => {
 'use strict';
 const $=id=>document.getElementById(id);
 const names={six_noun_acquisition:'تركيب الأسماء الستة المحدد',lexical_surface:'مطابقة الصيغة المشهودة',lexical_candidates:'المرشحون المعجميون',scope_acquisition:'حدود النطاق والتركيب',discourse_boundary:'حد الاستئناف والتصريح بالقصد',source_inference:'الاستدلال من مصدر محفوظ',lexical_transmission:'جهة النقل المعجمي',classical_control:'معادلة التحكم الصرفي'};
 const samples={six_noun_acquisition:'جَاءَ أَبُو زَيْدٍ',lexical_surface:'عَيْنَ',lexical_candidates:'قَرْءُ',scope_acquisition:'قَالَ زَيْدٌ: «أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ».',discourse_boundary:'لم أر أسداً قط؛ وأقصد بالأسد الحيوان المعروف.',source_inference:'إن عرف زيد الحق سار زيد. عرف زيد الحق.',lexical_transmission:'فرس'};
 const stateLabels={SCOPED_GATEWAY_INSTALLED:'بوابة مثبتة لدعوى محددة؛ الإتاحة تُفحص عند التشغيل',MIGRATED_SCOPED_NATIVE_ADAPTER:'محول أصلي بدعوى محددة',RETAIN_TYPED_PRIMITIVE:'بدائية ذات مجال عددي',RETAIN_NON_AUTHORITATIVE:'تشخيص أو اقتراح بلا سلطة قبول',CHILD_CONTRACT_REVIEW_REQUIRED:'يلزم تدقيق عقد المسار المنقول',ACQUISITION_AND_REFINEMENT_REVIEW_REQUIRED:'يلزم إغلاق التحصيل والمطابقة'};
 function operationChanged(){
  const op=$('workflow-operation').value,classical=op==='classical_control',inference=op==='source_inference';
  $('workflow-text-group').hidden=classical;$('workflow-frame-group').hidden=!classical;
  $('workflow-profile-group').hidden=!['lexical_candidates','discourse_boundary'].includes(op);
  $('workflow-scope-help').hidden=op!=='scope_acquisition';
  $('workflow-six-noun-help').hidden=op!=='six_noun_acquisition';
  $('workflow-discourse-help').hidden=op!=='discourse_boundary';
  $('workflow-inference-help').hidden=!inference;$('workflow-query-group').hidden=!inference;
  $('workflow-context-label').textContent=inference?'نطاق الاستدلال المعلن':'المقام المعلن';
  if(samples[op])$('workflow-text').value=samples[op];
  if(inference)$('workflow-query').value='هل سار زيد؟';
  reset('تغيّرت جهة الفحص؛ نفّذ الطلب لعرض دعاواه المتحققة.');
 }
 $('workflow-operation').addEventListener('change',operationChanged);
 function request(){
  const op=$('workflow-operation').value,context=$('workflow-context').value;
  let input;
  if(op==='classical_control'){
    let frame;try{frame=JSON.parse($('workflow-frame').value);}catch{throw new Error('إطار التحكم يجب أن يكون JSON صالحًا.');}
    input={rule_id:$('workflow-rule').value,frame};
  }else if(op==='source_inference')input={source:$('workflow-text').value,query:$('workflow-query').value,scope:context};
  else input={...(op==='lexical_transmission'?{entry:$('workflow-text').value}:{text:$('workflow-text').value}),context};
  if(op==='lexical_candidates'&&$('workflow-profile').value)input.profile_id=$('workflow-profile').value;
  if(op==='discourse_boundary')input.profile_id=$('workflow-profile').value||null;
  const value={schema:'nabt.licensed-workflow-request.v1',op,input};
  globalThis.NabtWorkflowContract.validateRequest(value);return value;
 }
 function reset(message='لم يُنفّذ طلب في المسار الموحّد بعد.'){$('workflow-output').hidden=true;$('workflow-message').textContent=message;$('workflow-claims').replaceChildren();$('download-workflow').disabled=true;}
 for(const id of ['workflow-text','workflow-query','workflow-context','workflow-profile','workflow-frame','workflow-rule']){
  for(const event of ['input','change'])$(id).addEventListener(event,()=>reset('تغيّرت مدخلات الطلب؛ النتيجة السابقة لا تثبت المدخل الحالي. أعد الفحص.'));
 }
 async function render(report){
  if(report.error){reset('تعذّر التنفيذ: '+String(report.status));return;}
  await globalThis.NabtWorkflowContract.verifyEnvelope(report);
  let currentMatches=false;
  try{currentMatches=globalThis.NabtWorkflowContract.canonical(request())===globalThis.NabtWorkflowContract.canonical(report.workflow_request);}catch{}
  if(!currentMatches){reset('وصل إيصال متحقق لطلب سابق؛ لم يُعرض برهان للمدخلات التي تغيّرت. أعد فحص الطلب الحالي.');return;}
  const g=report.gateway_result,inv=report.migration_inventory;
  $('download-workflow').disabled=false;
  $('workflow-output').hidden=false;$('workflow-message').textContent='اكتمل تشغيل '+names[g.operation]+'. لكل دعوى حدودها؛ اكتمال التنفيذ ليس قبولًا للعربية كلها.';
  $('workflow-status').textContent=g.status;
  $('workflow-native').textContent=g.native_checked?'أُعيد تشغيل المحول الأصلي؛ راجع الدعاوى المسماة أدناه':'لا شهادة نهائية من المحول؛ قد تبقى دعوى جزئية مستقلة محددة أدناه';
  $('workflow-claims').replaceChildren();
  if(!g.claims.length){const p=document.createElement('p');p.textContent='لا توجد دعوى مبرهنة معادة في هذا الطلب. يبقى السبب والبقايا في الإيصال.';$('workflow-claims').append(p);}
  for(const claim of g.claims){
    const card=document.createElement('article');card.className='testimony-card';
    const h=document.createElement('h4');h.textContent='برهان الدعوى المحددة: '+claim.kind;
    const scope=document.createElement('p');scope.textContent=claim.scope;
    const law=document.createElement('p');law.dir='ltr';law.textContent=claim.proof.law_id;
    const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');
    summary.textContent='المبرهنات والمقدمات وهوية الدعوى';pre.dir='ltr';pre.textContent=JSON.stringify(claim,null,2);details.append(summary,pre);card.append(h,scope,law,details);$('workflow-claims').append(card);
  }
  const six=g.operation==='six_noun_acquisition'?g.result:null;
  $('workflow-six-noun-detail').hidden=!six;
  $('workflow-six-noun-residuals').replaceChildren();
  if(six){
    $('workflow-six-noun-projection').textContent='الإسقاط المباشر للنص إلى الأساس116: '+(six.source_projection_complete?'مكتمل تمثيليًا':'غير مكتمل؛ لا يُرقّى بحفظ الجسر الإملائي')+'؛ جسر الرسم المحدد: '+(six.orthographic_bridge?'مرفق بالقراءة، لا يمنح ترخيصًا إملائيًا عامًا':'غير متاح في هذا الإيصال')+'.';
    const pending=six.residuals.length?six.residuals:['NO_RESIDUALS_DECLARED'];
    for(const item of pending){const row=document.createElement('li');row.dir='auto';row.textContent=item;$('workflow-six-noun-residuals').append(row);}
  }
  const transmission=g.result?.source_relationship_status??null;
  $('workflow-transmission').textContent=transmission?'تصنيف النقل في هذا الإيصال: '+String(transmission)+'؛ لا يثبت بذاته التواتر أو صحة الخبر خارجًا.':'لا يمنح هذا المسار وصف التواتر بعدد الشواهد أو بأسماء المؤلفين.';
  $('workflow-migration').replaceChildren();
  for(const[key,count]of Object.entries(inv.states)){const row=document.createElement('p');row.textContent=(stateLabels[key]||key)+' — '+count;$('workflow-migration').append(row);}
  $('workflow-inventory-count').textContent='الجرد المثبت: '+inv.surface_count+' سطحًا. إغلاق حارس الدخول لا يساوي اكتمال تحصيل مقدمات كل سطح.';
  $('workflow-json').textContent=JSON.stringify(report,null,2);
 }
 globalThis.NabtWorkflowUI=Object.freeze({request,reset,render});
 operationChanged();
 reset();
})();
