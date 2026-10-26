(() => {
 'use strict';
 const $=id=>document.getElementById(id);
 const names={lexical_surface:'مطابقة الصيغة المشهودة',lexical_candidates:'المرشحون المعجميون',scope_acquisition:'حدود النطاق والتركيب',lexical_transmission:'جهة النقل المعجمي',classical_control:'معادلة التحكم الصرفي'};
 const samples={lexical_surface:'عَيْنَ',lexical_candidates:'قَرْءُ',scope_acquisition:'«عَيْنَ»',lexical_transmission:'فرس'};
 const stateLabels={MIGRATED_SCOPED_NATIVE_ADAPTER:'محول أصلي بدعوى محددة',RETAIN_TYPED_PRIMITIVE:'بدائية ذات مجال عددي',RETAIN_NON_AUTHORITATIVE:'تشخيص أو اقتراح بلا سلطة قبول',CHILD_CONTRACT_REVIEW_REQUIRED:'يلزم تدقيق عقد المسار المنقول',ACQUISITION_AND_REFINEMENT_REVIEW_REQUIRED:'يلزم إغلاق التحصيل والمطابقة'};
 function operationChanged(){const op=$('workflow-operation').value;const classical=op==='classical_control';$('workflow-text-group').hidden=classical;$('workflow-frame-group').hidden=!classical;$('workflow-profile-group').hidden=op!=='lexical_candidates';if(samples[op])$('workflow-text').value=samples[op];}
 $('workflow-operation').addEventListener('change',operationChanged);
 function request(){
  const op=$('workflow-operation').value,context=$('workflow-context').value;
  let input;
  if(op==='classical_control'){
    let frame;try{frame=JSON.parse($('workflow-frame').value);}catch{throw new Error('إطار التحكم يجب أن يكون JSON صالحًا.');}
    input={rule_id:$('workflow-rule').value,frame};
  }else input={...(op==='lexical_transmission'?{entry:$('workflow-text').value}:{text:$('workflow-text').value}),context};
  if(op==='lexical_candidates'&&$('workflow-profile').value)input.profile_id=$('workflow-profile').value;
  const value={schema:'nabt.licensed-workflow-request.v1',op,input};
  globalThis.NabtWorkflowContract.validateRequest(value);return value;
 }
 function reset(message='لم يُنفّذ طلب في المسار الموحّد بعد.'){$('workflow-output').hidden=true;$('workflow-message').textContent=message;$('workflow-claims').replaceChildren();}
 async function render(report){
  if(report.error){reset('تعذّر التنفيذ: '+String(report.status));return;}
  await globalThis.NabtWorkflowContract.verifyEnvelope(report);
  const g=report.gateway_result,inv=report.migration_inventory;
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
  const transmission=g.result?.source_relationship_status??null;
  $('workflow-transmission').textContent=transmission?'تصنيف النقل في هذا الإيصال: '+String(transmission)+'؛ لا يثبت بذاته التواتر أو صحة الخبر خارجًا.':'لا يمنح هذا المسار وصف التواتر بعدد الشواهد أو بأسماء المؤلفين.';
  $('workflow-migration').replaceChildren();
  for(const[key,count]of Object.entries(inv.states)){const row=document.createElement('p');row.textContent=(stateLabels[key]||key)+' — '+count;$('workflow-migration').append(row);}
  $('workflow-inventory-count').textContent='الجرد المثبت: '+inv.surface_count+' سطحًا. إغلاق حارس الدخول لا يساوي اكتمال تحصيل مقدمات كل سطح.';
  $('workflow-json').textContent=JSON.stringify(report,null,2);
 }
 globalThis.NabtWorkflowUI=Object.freeze({request,reset,render});
 operationChanged();
})();
