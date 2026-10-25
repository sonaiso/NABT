'use strict';

// Imported evidence never enters the live-run channel. Everything in this
// inspector is computed in the browser; no imported text is sent or persisted.
(() => {
  const $ = id => document.getElementById(id);
  const make = (tag, value, className) => { const n = document.createElement(tag); if (value != null) n.textContent = String(value); if (className) n.className = className; return n; };
  const set = (id, value) => { $(id).textContent = value == null ? '—' : String(value); };
  const count = value => Number.isSafeInteger(value) ? value.toLocaleString('ar-JO') : '—';
  const pretty = value => typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  const fields = ['started','completed','found','produced','accepted','stored','consumed_by_next'];
  const labels = ['بدأ','اكتمل','وجد','أنتج','قُبل','حُفظ','استهلكه التالي'];
  const layerNames = ['الدال وحده','المدلول وحده','الإطار والحكم','العقل والإسناد'];
  let review = null, raw = '', sourceName = '', selectedLayer = 0, selectedId = null, sequence = 0;

  function error(message) { set('evidence-error', message); $('evidence-error').hidden = !message; }
  function disclosure(label, value) { const d=make('details'), s=make('summary',label), p=make('pre',pretty(value)); p.dir='auto'; d.append(s,p);return d; }
  function fact(label,value) {const row=make('div',null,'detail-fact');row.append(make('dt',label),make('dd',value));return row;}
  function metric(value,label,detail,tone='') { const n=make('div',null,'evidence-metric '+tone);n.append(make('span',label),make('strong',value),make('p',detail));return n; }
  function filename(prefix) { return prefix+'-'+(review?.input?.computed_sha256||'report').slice(0,12)+'.json'; }
  function download(content,name) { const url=URL.createObjectURL(new Blob([content],{type:'application/json;charset=utf-8'}));const link=make('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000); }

  async function inspect(value,name) {
    const ticket=++sequence;
    // Clear old authority-bearing display before validating a replacement.
    review=null;raw='';$('evidence-output').hidden=true;$('evidence-loading').hidden=false;
    set('evidence-loading','جارٍ فحص البنية وحساب البصمة…');error('');
    try {
      const result=await globalThis.NabtEvidenceAudit.audit(value);
      if(ticket!==sequence)return;
      review=result;raw=value;sourceName=name;selectedLayer=0;selectedId=null;
      $('evidence-search').value='';$('evidence-rank').value='all';
      render();$('evidence-output').hidden=false;$('import-panel').hidden=true;
    }catch(e){if(ticket===sequence)error('لم يُقبل السجل للفحص: '+String(e.message||e));}
    finally{if(ticket===sequence)$('evidence-loading').hidden=true;}
  }
  function render(){
    const rec=review.raw_record;
    set('evidence-origin',sourceName==='sample'?'شاهد منقول · عرض مقتطف':'سجل مستورد · غير معاد التشغيل');
    set('evidence-sentence',review.input?.text||'لا نص محفوظ في هذا التقرير');
    set('evidence-summary','الرتب والأحكام أدناه من السجل. أُعيد هنا فحص الاتساق والبصمات فقط.');
    set('evidence-sha',review.input?.computed_sha256||'غير متاح');
    const hashCheck=review.checks.find(c=>c.id==='TEXT_SHA256')||review.checks.find(c=>/sha256|text_hash/i.test(c.id));
    set('evidence-hash-status',!review.input?'لا نص أصلي مضمن لحساب بصمته':!review.input.computed_sha256?'حساب SHA-256 غير متاح في بيئة المتصفح الحالية':hashCheck?.status==='pass'?'البصمة تطابق النص المستلم':hashCheck?.status==='fail'?'اختلاف في هوية النص — راجع الفجوات':'بصمة محلية؛ راجع فحوص الهوية');
    set('evidence-sample-note',rec.sample_note||'ملف مستورد. بياناته المعلنة تحتاج ملفات المصدر وإعادة التحقق المستقل.');
    const claims=review.claims;
    const witness=claims.filter(c=>c.rank==='مبرهن على الشاهد').length;
    const general=claims.filter(c=>c.rank==='مبرهن').length;
    const theoremValues=Object.values(rec.lean?.theorems||{});
    const declared=theoremValues.filter(t=>t.passed===true).length;
    const lexical=Array.isArray(rec.maani)?rec.maani:[];
    const lexicalWithSource=lexical.filter(m=>m.mudaa&&typeof m.mudaa==='object'&&typeof m.mudaa.ism==='string'&&m.mudaa.ism.trim()&&typeof m.mudaa.sha256==='string'&&/^[a-f0-9]{64}$/.test(m.mudaa.sha256)&&typeof m.mudaa.mawdi==='string'&&m.mudaa.mawdi.trim()).length;
    $('evidence-metrics').replaceChildren(
      metric(count(claims.length),'ادعاءات قابلة للتتبع',count(witness)+' على الشاهد · '+count(general)+' عام بحسب رتب السجل'),
      metric(theoremValues.length?count(declared)+' / '+count(theoremValues.length):'غير مقاس','نجاح Lean المروي','حالات يعلنها السجل؛ ليست إعادة فحص'),
      metric(lexical.length?count(lexicalWithSource)+' / '+count(lexical.length):'غير مقاس','إحالات معجمية معلنة','وجود المرجع لا يثبت مطابقته للمعنى','amber'),
      metric('٠','إعادات تحقق Lean هنا','المتاح: فحص السجل وبصمته محليًا','neutral')
    );
    if(review.kind==='nabt'){
      const b=review.benchmark;
      $('evidence-metrics').replaceChildren(metric(count(review.metrics.claims),'تصريحات مستوردة','لا تُمنح سلطة بالتنزيل أو الاستيراد'),metric(b?count(b.counts.pass)+' / '+count(b.counts.cases):count(review.metrics.readings),'القياس / القراءات المروية',b?'صفوف مطابقة للتوقع في السجل':'عدد القراءات الواردة في الملف'),metric(b?count(b.counts.fail):count(review.metrics.assumptions),b?'إخفاقات في السجل':'افتراضات معلنة','العدد مشتق من الصفوف الفعلية','amber'),metric('٠','إعادات تحقق Lean هنا','سجل مستقل عن مسار التنفيذ الحي','neutral'));
    }
    renderLayers();renderClaims();renderChecks();renderFindings();renderStages();renderProvenance();renderImportedBenchmark();
    $('evidence-limits').replaceChildren(...review.limits.map(v=>make('li',v)));
    set('evidence-raw',raw);
  }
  function renderImportedBenchmark(){
    const b=review.benchmark;$('evidence-imported-benchmark').hidden=!b;
    $('evidence-imported-rows').replaceChildren();if(!b)return;
    set('evidence-imported-scope',typeof b.scope==='string'?b.scope:'نطاق مجموعة مستوردة؛ لا قياس لاكتمال العربية.');
    set('evidence-imported-counts',count(b.counts.cases)+' حالات · '+count(b.counts.pass)+' مطابقة · '+count(b.counts.fail)+' إخفاق · '+count(b.counts.unmeasured)+' غير مقاس');
    for(const row of b.rows){const tr=make('tr');tr.append(make('td',row.id),make('td',row.family||'غير مسجل'),make('td',row.outcome));const detail=make('td');detail.append(disclosure('تفاصيل الحالة',row));tr.append(detail);$('evidence-imported-rows').append(tr);}
  }
  function renderLayers(){
    const root=$('evidence-layers');root.replaceChildren();
    const buttons=[];
    for(let i=0;i<4;i++){
      const layer=review.layers.find(l=>Number(l.id)===i+1);
      const related=review.claims.filter(c=>Number(c.layer)===i+1);
      const node=make('button',null,'layer-card'+(selectedLayer===i+1?' selected':''));node.type='button';node.setAttribute('aria-pressed',String(selectedLayer===i+1));
      node.append(make('span','0'+(i+1),'layer-index'),make('h3',layer?.title||layerNames[i]),make('span',layer?.declared?'رتبة السجل: '+layer.declared:'رتبة غير مسجلة','layer-declared'),make('p',count(related.length)+' ادعاءات · '+(i===0?'هوية النص وترميزه':i===1?'المعنى ومصدره':i===2?'الإطار والترخيص':'المرساة والافتراضات')));
      node.append(make('span',(layer?.issues?.length?count(layer.issues.length)+' التزامات ظاهرة':'التوثيق وإعادة التشغيل لم يُحسما'),'layer-issues'));
      buttons.push(node);
      node.addEventListener('click',()=>{
        selectedLayer=selectedLayer===i+1?0:i+1;
        // Keep the activated DOM node (and keyboard focus) in place.
        buttons.forEach((button,index)=>{
          const selected=selectedLayer===index+1;
          button.className='layer-card'+(selected?' selected':'');
          button.setAttribute('aria-pressed',String(selected));
        });
        renderClaims();
      });root.append(node);
    }
  }
  function renderClaims(){
    const q=$('evidence-search').value.trim().toLocaleLowerCase('ar'),rank=$('evidence-rank').value;
    const items=review.claims.filter(c=>(!selectedLayer||Number(c.layer)===selectedLayer)&&(rank==='all'||rank==='unverified'||c.rank===rank)&&(!q||[c.id,c.label,c.rank,c.evidence,pretty(c.value),...(c.axioms||[])].join(' ').toLocaleLowerCase('ar').includes(q)));
    if(!items.some(c=>c.id===selectedId))selectedId=items[0]?.id||null;
    set('evidence-claim-count',count(items.length)+' / '+count(review.claims.length));
    $('evidence-claims').replaceChildren();
    const buttons=[];
    for(const c of items){
      const button=make('button',null,'claim-row'+(selectedId===c.id?' selected':''));button.type='button';button.setAttribute('aria-pressed',String(selectedId===c.id));
      const top=make('span',null,'claim-row-top');top.append(make('span','ط'+count(Number(c.layer)),'claim-layer'),make('span',c.rank||'بلا رتبة','claim-rank'));
      button.append(top,make('strong',c.label||c.id),make('code',c.id),make('span','افحص المستند والحدود ↙','claim-open'));
      buttons.push({id:c.id,node:button});
      button.addEventListener('click',()=>{
        selectedId=c.id;
        // Selecting a row changes its state/detail, not its identity or focus.
        buttons.forEach(row=>{
          const selected=row.id===selectedId;
          row.node.className='claim-row'+(selected?' selected':'');
          row.node.setAttribute('aria-pressed',String(selected));
        });
        renderClaim(c);
      });$('evidence-claims').append(button);
    }
    $('evidence-claims-empty').hidden=items.length>0;
    renderClaim(items.find(c=>c.id===selectedId));
  }
  function renderClaim(c){
    const target=$('claim-detail');target.replaceChildren();set('claim-detail-title',c?'تفصيل الادعاء':'لا ادعاء محدد');if(!c)return;
    const code=make('code',c.id,'inspector-id');code.dir='ltr';
    target.append(code,make('p',c.label,'inspector-description'));
    const dl=make('dl',null,'detail-facts');dl.append(fact('الرتبة المنقولة',c.rank||'غير مصرح بها'),fact('إعادة فحص Lean','لم تتم في هذه الصفحة'),fact('حالة البرهان المعلنة',c.declared_passed===true?'ناجح بحسب السجل':c.declared_passed===false?'غير ناجح بحسب السجل':'غير مسجلة'));
    target.append(dl,make('h4','الدليل كما ورد'),make('p',c.evidence||'لا مستند مسجل','inspector-evidence'));
    if(Array.isArray(c.axioms)){target.append(make('h4','المسلّمات المعلنة'));const axes=make('div',null,'axiom-list');if(!c.axioms.length)axes.append(make('span','قائمة خالية بحسب السجل'));for(const ax of c.axioms)axes.append(make('code',ax));target.append(axes);}
    target.append(disclosure('القيمة والبنية المسجلة',c.value));
    const related=review.findings.filter(f=>Number(f.layer)===Number(c.layer));
    if(related.length){target.append(make('h4','التزامات في هذه الطبقة'));const list=make('ul',null,'claim-obligations');for(const f of related)list.append(make('li',f.title));target.append(list);}
    target.append(make('p','هذه العدسة تتتبع الادعاء ولا تمنح رتبته سلطة جديدة. نص المبرهنة واعتمادياتها مطلوبان لتحديد مداها.','inspector-boundary'));
  }
  function renderChecks(){
    const list=$('evidence-checks');list.replaceChildren();
    for(const c of review.checks){const d=make('details',null,'audit-check '+(c.status==='pass'?'check-pass':c.status==='fail'?'check-fail':'check-unknown'));const title=make('summary');title.append(make('span',c.label),make('b',c.status==='pass'?'مطابق':c.status==='fail'?'غير متسق':'غير محسوم'));d.append(title,make('p',c.detail));list.append(d);}
  }
  function renderFindings(){set('evidence-findings-count',count(review.findings.length)+' ملاحظات');$('evidence-findings').replaceChildren();for(const f of review.findings){const item=make('article',null,'finding '+(f.severity==='error'?'error':'warning'));item.append(make('span',f.layer?'الطبقة '+count(Number(f.layer)):'سلسلة التحقق','finding-label'),make('h4',f.title),make('p',f.detail),make('code',f.id));$('evidence-findings').append(item);}}
  function renderStages(){
    $('evidence-stages').replaceChildren();$('evidence-stages-empty').hidden=review.stages.length>0;
    for(const s of review.stages){const tr=make('tr');const name=make('th',s.label||s.id);name.scope='row';name.dir='auto';tr.append(name);fields.forEach((key,i)=>{const value=s.answers[key],cell=make('td');const mark=make('span',value===true?'●':value===false?'×':'—','stage-value '+(value===true?'yes':value===false?'no':'unknown'));mark.setAttribute('aria-label',labels[i]+': '+(value===true?'نعم':value===false?'لا':'غير مقاس'));mark.title=value===true?'نعم بحسب السجل':value===false?'لا بحسب السجل':'غير مقاس';cell.append(mark);tr.append(cell);});const rest=make('td');if(s.reason)rest.append(make('p',s.reason));for(const v of s.residuals||[])rest.append(make('code',v,'stage-residual'));for(const v of s.contradictions||[])rest.append(make('p',v,'stage-contradiction'));if(!rest.children.length)rest.append(make('span','—'));tr.append(rest);$('evidence-stages').append(tr);}
  }
  function renderProvenance(){
    const rec=review.raw_record,identity=rec.identity||{};
    const data=[['نوع السجل',rec.schema],['نسخة الشفرة المعلنة',identity.mashru_head||rec.code_sha],['شجرة المصدر',identity.mashru_tree_clean===true?'نظيفة بحسب السجل':identity.mashru_tree_clean===false?'غير نظيفة بحسب السجل':'غير معلومة'],['توزيعة Lean المعلنة',identity.lean_toolchain||rec.toolchain],['بصمة المعجم المعلنة',identity.qamus_sha256],['بصمة ملف البرهان المعلنة',rec.lean?.files?.pass2],['وقت السجل',rec.timestamp_utc||rec.generated_at_utc],['طبيعة الفحص هنا','تحليل محلي لسجل مستورد؛ لا اتصال بمستودع Mashru ولا إعادة تشغيل Lean']];
    $('evidence-provenance').replaceChildren(...data.map(([label,value])=>fact(label,typeof value==='string'?value:value?pretty(value):'غير مسجل')));
  }
  $('open-import').addEventListener('click',()=>{$('import-panel').hidden=false;$('evidence-input').focus();});
  $('close-import').addEventListener('click',()=>{$('import-panel').hidden=true;});
  $('audit-evidence').addEventListener('click',()=>inspect($('evidence-input').value,'pasted'));
  $('evidence-file').addEventListener('change',async()=>{const file=$('evidence-file').files?.[0];if(!file)return;const ticket=++sequence;review=null;raw='';$('evidence-output').hidden=true;$('evidence-loading').hidden=true;if(file.size>2*1024*1024){review=null;raw='';$('evidence-output').hidden=true;error('يتجاوز الملف حد ٢ MiB.');return;}try{const bytes=await file.arrayBuffer();if(ticket!==sequence)return;const value=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);$('evidence-input').value=value;await inspect(value,'file');}catch{if(ticket===sequence){review=null;raw='';$('evidence-output').hidden=true;error('تعذر قراءة الملف بترميز UTF-8 صالح.');}}});
  $('evidence-search').addEventListener('input',()=>{if(review)renderClaims();});$('evidence-rank').addEventListener('change',()=>{if(review)renderClaims();});
  $('download-evidence-review').addEventListener('click',()=>{if(review){const {raw_record,raw_json,...result}=review;download(JSON.stringify({...result,source_kind:sourceName,review_notice:'Local consistency audit only; imported Lean results were not replayed.'},null,2),filename('nabt-evidence-review'));}});
  $('download-evidence-source').addEventListener('click',()=>{if(review)download(raw,filename('nabt-evidence-input'));});
  const sample=()=>{ $('evidence-input').value='';$('evidence-file').value='';return inspect(JSON.stringify(globalThis.NabtEvidenceSample,null,2),'sample'); };
  $('load-evidence-sample').addEventListener('click',sample);
  sample();
})();
