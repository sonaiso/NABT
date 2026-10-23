from pathlib import Path
import json,hashlib,datetime,re
D=Path('/tmp/nabt-governor-independent-new')
def write(name,obj):
 (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def atom(p,s):return {'predicate':p,'args':[s],'positive':True}
def source(sid,text,seed,subject,predicate,op='add',rule=None,identity=True):
 marker=next(x for x in ('إِنَّ','إنّ') if x in text)
 start=text.index(marker);end=text.index('.',start)+1
 segment=text[start:end-1].split();assert len(segment)==3
 positions=[];cursor=start
 for role,word in zip(('governor','subject','predicate'),segment):
  p=text.index(word,cursor);cursor=p+len(word)
  positions.append({'role':role,'raw':word,'start':len(text[:p].encode()),'end':len(text[:cursor].encode())})
 facts=[atom(seed,subject),atom(predicate,subject)] if identity else []
 return {'op':op,'source_id':sid,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'gold':{'accepted_required':identity,'facts':facts,'rules':[rule] if rule else [],
                 'forbidden_facts':[] if identity else [atom(predicate,subject)],
                 'governor_witness':{'kind':'inna_single_predicate','span_start':len(text[:start].encode()),'span_end':len(text[:end].encode()),'roles':positions},
                 'referent_identity_required':identity}}
def query(qid,subject,predicate,status='SUPPORTED'):
 return {'op':'query','query_id':qid,'text':f'هل {subject} هو {predicate}؟',
         'gold':{'goal':atom(predicate,subject),'status':status,**({'accepted_statuses':['UNKNOWN','OUT_OF_SCOPE']} if status=='UNKNOWN' else {})}}
def case(cid,events,mode='capability'):
 return {'id':cid,'group':'identity_supplement','mode':mode,'events':events}
r={'body':[atom('مدقق','$x')],'head':atom('متفحّص','$x')}
E=[
 case('h01',[source('one','«رزين» هو مترجمٌ. إنّ رزينًا متيقظٌ.','مترجم','رزين','متيقظ'),query('answer','رزين','متيقظ')]),
 case('h02',[source('one','«إياس» هو رائدٌ. إِنَّ إياسًا متأهّبٌ.','رائد','إياس','متأهّب'),query('answer','إياس','متأهّب')]),
 case('h03',[source('one','«سهيلة» هي راصدةٌ. إنّ سهيلةَ يقظةٌ.','راصدة','سهيلة','يقظة'),query('before','سهيلة','يقظة'),{'op':'remove','source_id':'one'},query('removed','سهيلة','يقظة','UNKNOWN')]),
 case('h04',[source('one','«وجدان» هي شاعرةٌ. إنّ وجدانَ حاضرةٌ.','شاعرة','وجدان','حاضرة'),query('before','وجدان','حاضرة'),source('one','«وجدان» هي شاعرةٌ. إنّ وجدانَ مسافرةٌ.','شاعرة','وجدان','مسافرة',op='replace'),query('obsolete','وجدان','حاضرة','UNKNOWN'),query('new','وجدان','مسافرة')]),
 case('h05',[source('one','«كنان» هو باحثٌ. إنّ كنانًا مدققٌ. كلُّ مدققٍ متفحّصٌ.','باحث','كنان','مدقق',rule=r),query('derived','كنان','متفحّص')]),
 case('h06',[source('one','باحثٌ هو نشيطٌ. إنّ باحثًا متأهّبٌ.','نشيط','باحث','متأهّب',identity=False)],'repeated_indefinite_control')]
write('identity_supplement.json',{'schema':'nabt.governors.identity-supplement.v1','scope':'Five new quoted-name capability episodes and one repeated-indefinite identity control. No فرد declaration. This supplements and never replaces the 32 original episodes or six original excerpts.','episodes':E})
records=[]
for c in E:
 for event in c['events']:
  if event['op'] not in ('add','replace'):continue
  raw=event['text'];statements=[];fs=event['gold']['facts'];rs=event['gold']['rules'];fi=0
  for text in [s.strip() for s in raw.split('.') if s.strip()]:
   start=raw.index(text);tokens=list(re.finditer(r'«[^«»]*»|[^\s«»]+',text));facts=[];rules=[];kinds=[]
   if text.startswith('كلُّ '):
    roles=['quantifier','body.predicate','head.predicate']
    rules=[{'body':[{**a,'args':['?x' if x=='$x' else x for x in a['args']]} for a in rs[0]['body']],
            'head':{**rs[0]['head'],'args':['?x' if x=='$x' else x for x in rs[0]['head']['args']]}}];kinds=['universal']
   elif text.startswith(('إنّ ','إِنَّ ')):
    roles=['governor','subject','predicate']
    if fs:facts=[fs[fi]];fi+=1
   else:
    roles=['quoted_subject' if text.startswith('«') else 'subject','copula','predicate']
    if fs:facts=[fs[fi]];fi+=1
    else:facts=[atom('نشيط','باحث')]
   assert len(tokens)==len(roles)
   statements.append({'start':len(raw[:start].encode()),'end':len(raw[:start+len(text)].encode()),'facts':facts,'rules':rules,'rule_kinds':kinds,
                      'components':[{'start':len(raw[:start+t.start()].encode()),'end':len(raw[:start+t.end()].encode()),'roles':[role]} for t,role in zip(tokens,roles)]})
  normalized_rules=[rule for statement in statements for rule in statement['rules']]
  records.append({'raw_text':raw,'source_text_sha256':event['text_sha256'],'facts':fs,'rules':normalized_rules,'statements':statements})
write('identity_supplement_annotations.json',{'schema':'nabt.governors.identity-supplement-annotations.v1','records':records})
write('prefreeze_protocol_amendment.json',{
 'schema':'nabt.governors.prefreeze-protocol-amendment.v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'new_implementation_opened':False,'new_implementation_results_seen':False,'baseline_results_seen':True,
 'cause':'Builder independent adversarial review found that prior ordinary predication of an indefinite noun establishes nominality but not identity of its next occurrence. The earlier identity agreement was therefore too permissive. This was found before new implementation freeze or evaluator exposure to it.',
 'original_material_change':'None. Original 32-case gold and six original excerpts retain their original expectations and denominators. Baseline result 11/12 of original declared-scope episodes remains published. No old failure or scope expectation is removed.',
 'tightened_scope':'A same-individual assertion now needs explicit name identity already introduced by the existing guillemet-quoted-name convention, or an individual declaration. This supplement uses only the first route. Natural predication alone still supplies nominality, but not indefinite coreference.',
 'added_denominators':{'identity_supplement':6,'capability':5,'repeated_indefinite_control':1},
 'metrics':'Keep original source/question coverage and new supplement coverage separate. Record complete syntactic cue extraction even when referent identity is missing. Missing reference identity is correct suspension; a report claiming reference established without a qualifying witness is a certificate failure.',
 'independence':'Evaluator selected novel names, predicates and episodes before opening new code; shared filesystem procedural separation, no human-expert review.'})
files=['build_identity_supplement.py','identity_supplement.json','identity_supplement_annotations.json','prefreeze_protocol_amendment.json']
freeze={'schema':'nabt.governors.identity-supplement-freeze.v1','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'original_material_freeze_sha256':hashlib.sha256((D/'material_freeze.json').read_bytes()).hexdigest(),
        'files':[{'path':f,'sha256':hashlib.sha256((D/f).read_bytes()).hexdigest(),'bytes':(D/f).stat().st_size} for f in files]}
write('identity_supplement_freeze.json',freeze)
print(json.dumps({'frozen_at_utc':freeze['frozen_at_utc'],'freeze_sha256':hashlib.sha256((D/'identity_supplement_freeze.json').read_bytes()).hexdigest(),'episodes':len(E),'unique_sources':len(records),'no_fard_declarations':all('فرد ' not in e.get('text','') for c in E for e in c['events'])},ensure_ascii=False,indent=2))
