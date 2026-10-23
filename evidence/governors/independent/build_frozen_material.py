from pathlib import Path
import subprocess,json,hashlib,datetime
ROOT=Path('/workspace/scratch/6e4178bfef09/nabt_integration/NABT')
OUT=Path('/tmp/nabt-governor-independent-new')
BASE='5195c57'
PIN='e4c801ffe9171dadedcc3aae23051ea0953ae361'
def jd(path,obj):
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def atom(p,x,positive=True):return {'predicate':p,'args':[x],'positive':positive}
def fact(p,x,positive=True):return atom(p,x,positive)
def add(s,text,facts=(),governor=None,rules=(),accepted=True,forbidden=(),notes=''):
 d={'op':'add','source_id':s,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'gold':{'accepted_required':accepted,'facts':list(facts),'rules':list(rules),'forbidden_facts':list(forbidden),'notes':notes}}
 if governor:
  marker,subject,predicate=governor
  start=text.index(marker)
  end=text.find('.',start)
  if end<0:end=len(text)
  else:end+=1
  spans=[]
  pos=start
  for role,word in [('governor',marker),('subject',subject),('predicate',predicate)]:
   ix=text.index(word,pos)
   spans.append({'role':role,'start':len(text[:ix].encode()),'end':len(text[:ix+len(word)].encode()),'raw':word})
   pos=ix+len(word)
  d['gold']['governor_witness']={'kind':'inna_single_predicate','span_start':len(text[:start].encode()),'span_end':len(text[:end].encode()),'roles':spans}
 return d
def query(i,text,status,goal):return {'op':'query','query_id':i,'text':text,'gold':{'status':status,'goal':goal}}
def remove(s):return {'op':'remove','source_id':s}
def ep(i,group,events,note):return {'id':i,'group':group,'notes':note,'events':events}
E=[]
def simple(i,text,subject,predicate,seed,gov,extra='',querytext=None):
 E.append(ep(i,'declared_scope',[add('source',text,[fact(seed,subject),fact(predicate,subject)],gov),query('answer',querytext or f'هل {subject} هو {predicate}؟','SUPPORTED',atom(predicate,subject))],extra))
simple('g01','خالدٌ هو قارئٌ. إنّ خالدًا متأهبٌ.','خالد','متأهب','قارئ',('إنّ','خالدًا','متأهبٌ'),'Natural predication supplies the unique source-local spelling identity; no فرد declaration.')
simple('g02','مُنْذِرٌ هو كَاتِبٌ. إِنَّ مُنْذِرًا مُنْصِتٌ.','مُنْذِر','مُنْصِت','كَاتِب',('إِنَّ','مُنْذِرًا','مُنْصِتٌ'),'Internal diacritics and shadda remain in lexical identity; only licensed final inflection is stripped.')
simple('g03','دانيةُ هي قارئةٌ. إنَّ دانيةَ خبيرةٌ.','دانية','خبيرة','قارئة',('إنَّ','دانيةَ','خبيرةٌ'),'Diptote feminine personal name; no added accusative alif.',querytext='هل دانية هي خبيرة؟')
simple('g04','سعادُ هي بارعةٌ. إِنَّ سعادَ حاضرةٌ.','سعاد','حاضرة','بارعة',('إِنَّ','سعادَ','حاضرةٌ'),'The name and predicate have source-local nominal evidence.',querytext='هل سعاد هي حاضرة؟')
rule={'id':'universal','body':[atom('يقظ','$x')],'head':atom('منتبه','$x')}
E.append(ep('g05','declared_scope',[add('source','حارثٌ هو ملاحظٌ. إنّ حارثًا يقظٌ. كلُّ يقظٍ منتبهٌ.',[fact('ملاحظ','حارث'),fact('يقظ','حارث')],('إنّ','حارثًا','يقظٌ'),[rule]),query('derived','هل حارث هو منتبه؟','SUPPORTED',atom('منتبه','حارث'))],'A novel acquired role feeds an existing universal rule; proof must retain both source statements.'))
simple('g06','المرصدُ هو مبنى. إنّ المرصدَ مجهّزٌ.','المرصد','مجهّز','مبنى',('إنّ','المرصدَ','مجهّزٌ'),'Definite nominal identity is acquired from the earlier explicit predication, not assumed from ال alone.')
E.append(ep('g07','declared_scope',[add('source','"إنّ" هو حرفٌ.',[fact('حرف','إنّ')]),query('literal','هل "إنّ" هو حرف؟','SUPPORTED',atom('حرف','إنّ'))],'Quoted operator is the subject of a metalinguistic predication, not an active governor.'))
E.append(ep('g08','declared_scope',[add('source','ربيعٌ هو باحثٌ. إنّ ربيعًا صبورٌ.',[fact('باحث','ربيع'),fact('صبور','ربيع')],('إنّ','ربيعًا','صبورٌ')),query('present','هل ربيع هو صبور؟','SUPPORTED',atom('صبور','ربيع')),remove('source'),query('removed','هل ربيع هو صبور؟','UNKNOWN',atom('صبور','ربيع'))],'Removing the only complete source must remove its answer and role evidence.'))
E.append(ep('g09','declared_scope',[add('source','منيرٌ هو مترجمٌ. إنّ منيرًا حاضرٌ.',[fact('مترجم','منير'),fact('حاضر','منير')],('إنّ','منيرًا','حاضرٌ')),query('before','هل منير هو حاضر؟','SUPPORTED',atom('حاضر','منير')),add('source','منيرٌ هو مترجمٌ. إنّ منيرًا مسافرٌ.',[fact('مترجم','منير'),fact('مسافر','منير')],('إنّ','منيرًا','مسافرٌ')),query('obsolete','هل منير هو حاضر؟','UNKNOWN',atom('حاضر','منير')),query('new','هل منير هو مسافر؟','SUPPORTED',atom('مسافر','منير'))],'Replacing a source invalidates its earlier proposition and builds the new one; no per-case patch.'))
E.append(ep('g10','declared_scope',[add('source','نادرٌ هو بحّارٌ. إنّ نادرًا علامةٌ.',[fact('بحّار','نادر'),fact('علامة','نادر')],('إنّ','نادرًا','علامةٌ')),add('opposite','ليس نادرٌ هو علامةً.',[fact('علامة','نادر',False)]),query('conflict','هل نادر هو علامة؟','CONFLICT',atom('علامة','نادر')),remove('opposite'),query('resolved','هل نادر هو علامة؟','SUPPORTED',atom('علامة','نادر'))],'A source-bound affirmative is not deleted or silently preferred when an explicit negative arrives.'))
E.append(ep('g11','declared_scope',[add('source','لبيبٌ هو راصدٌ. إنّ لبيبًا متيقظٌ.',[fact('راصد','لبيب'),fact('متيقظ','لبيب')],('إنّ','لبيبًا','متيقظٌ')),query('first','هل لبيب هو متيقظ؟','SUPPORTED',atom('متيقظ','لبيب')),remove('source'),query('absent','هل لبيب هو متيقظ؟','UNKNOWN',atom('متيقظ','لبيب')),add('source','لبيبٌ هو راصدٌ. إنّ لبيبًا متيقظٌ.',[fact('راصد','لبيب'),fact('متيقظ','لبيب')],('إنّ','لبيبًا','متيقظٌ')),query('restored','هل لبيب هو متيقظ؟','SUPPORTED',atom('متيقظ','لبيب'))],'Identical text can return with a new source version; replay must bind its current provenance.'))
E.append(ep('g12','declared_scope',[add('one','هشامٌ هو قارئٌ. إنّ هشامًا منصتٌ.',[fact('قارئ','هشام'),fact('منصت','هشام')],('إنّ','هشامًا','منصتٌ')),add('two','هديلُ هي باحثةٌ. إنّ هديلَ متأهبةٌ.',[fact('باحثة','هديل'),fact('متأهبة','هديل')],('إنّ','هديلَ','متأهبةٌ')),query('one','هل هشام هو منصت؟','SUPPORTED',atom('منصت','هشام')),query('two','هل هديل هي متأهبة؟','SUPPORTED',atom('متأهبة','هديل')),query('no_swap','هل هشام هو متأهبة؟','UNKNOWN',atom('متأهبة','هشام'))],'Identities and witnesses from two new sources must not be interchanged.'))
E.append(ep('g13','beyond_declared_scope',[add('source','إنّ دانيةَ خبيرةٌ.',[fact('خبيرة','دانية')],accepted=False)],'Grammatically meaningful proper name without prior independent identity evidence: suspend in this pilot; record that this is lost coverage, not full understanding.'))
E.append(ep('g14','beyond_declared_scope',[add('source','رائدٌ هو قارئٌ. إنّ رائدًا متنبّهٌ و صبورٌ.',[fact('قارئ','رائد'),fact('متنبّه','رائد'),fact('صبور','رائد')],accepted=False)],'Valid additive coordinated predicates are outside the declared single-predicate governor path; must not silently drop the second predicate.'))
E.append(ep('g15','beyond_declared_scope',[add('source','سامرٌ هو كاتبٌ. مازنٌ هو شاعرٌ. إنّ سامرًا حاضرٌ و إنّ مازنًا غائبٌ.',[fact('كاتب','سامر'),fact('شاعر','مازن'),fact('حاضر','سامر'),fact('غائب','مازن')],accepted=False)],'Two complete coordinated governor clauses must preserve both subjects when eventually supported; current scope defers the source atomically.'))
E.append(ep('g16','beyond_declared_scope',[add('source','إنّ شجرةً مثمرةٌ.',[],('إنّ','شجرةً','مثمرةٌ'),accepted=False,forbidden=[fact('مثمرة','شجرة')],notes='Require named REFERENT_IDENTITY_EVIDENCE obligation while retaining nominal, role, and case cues. New indefinite occurrence must not become a global individual named شجرة.')],'Cues can be extracted without licensing a globally named referent; cue extraction and semantic acceptance are separate metrics.'))
controls=[
('g17','طارقٌ هو مدققٌ. إنّ طارقٌ حاضرٌ.','Wrong subject nominative; do not rewrite it to accusative.'),
('g18','طارقٌ هو مدققٌ. إنّ طارقٍ حاضرٌ.','Wrong subject genitive.'),
('g19','غسانٌ هو رسّامٌ. إنّ غسانًا سعيدًا.','Wrong predicate accusative, though its nominality is clear.'),
('g20','غسانٌ هو رسّامٌ. إنّ غسانًا سعيدٍ.','Wrong predicate genitive.'),
('g21','غسانٌ هو رسامٌ. إنّ غسانًا.','Missing complement must be named; seed cannot cause partial source admission.'),
('g22','إنّ حاضرٌ.','No two-place governor construction; not an implicit subject.'),
('g23','غسانٌ هو رسامٌ. إن غسانًا حاضرٌ.','Bare إن is not automatically the emphasized governor.'),
('g24','غسانٌ هو رسامٌ. إنْ غسانٌ حاضرٌ.','Visible sukun cannot be normalized into shadda; conditional/lightened scope remains unresolved.'),
('g25','كأنّ سامرًا حاضرٌ.','Similarity/appearance operator must not establish factual presence.'),
('g26','ليت سامرًا حاضرٌ.','Wish is not a factual assertion.'),
('g27','لعلّ سامرًا حاضرٌ.','Hope/possibility is not a factual assertion.'),
('g28','كان غسانٌ حاضرًا.','A past-state construction cannot become an unscoped current fact.'),
('g29','ظنّ رائدٌ غسانًا حاضرًا.','An attitude report cannot become the embedded proposition.'),
('g30','"إنّ غسانًا حاضرٌ".','Mention of an entire statement is not endorsement of it.'),
('g31','غسانٌ هو رسامٌ. إنّما غسانٌ حاضرٌ.','ما changes the government construction; unsupported restriction/cessation of government must stay visible.'),
('g32','إنّ حاسرًا متأهّبٌ.','No unique source-local witness authorizes dropping the accusative alif.')]
for i,t,n in controls:
 forbidden=[]
 if i in {'g25','g26','g27'}:forbidden=[fact('حاضر','سامر')]
 if i in {'g28','g29','g30'}:forbidden=[fact('حاضر','غسان')]
 E.append(ep(i,'safety_control',[add('source',t,[],accepted=False,forbidden=forbidden)],n))
assert len(E)==32 and len({x['id'] for x in E})==32
jd(OUT/'episodes.json',{'schema':'nabt.governors.independent-episodes.v1','authoring':'Independent evaluator agent, before reading new implementation; author-composed cases, not unseen naturally occurring corpus','episodes':E})
manifest=json.loads(subprocess.check_output(['git','show',BASE+':src/nabt/data/source_evidence/source_manifest.json'],cwd=ROOT))
docs={d['source_id']:d for d in manifest['documents']}
specs=[
('x01','qatr','إن في ذلك لعبرة','fronted_pp_with_deictic',[],True,'Reference and fronted predicate structure require explicit analysis; no standalone named individual fact is licensed.'),
('x02','qatr','قال إني عبد الله','reported_speech',[],True,'Do not collapse reported first-person speech into an unscoped assertion about the compiler or user.'),
('x03','alfiyya','كإن زيدا عالم بأني ... كفء ولكن ابنه ذو ضعن','grammar_example_in_verse',[],True,'Original verse and its example boundary are part of the input; no invented punctuation or vocalization.'),
('x04','alfiyya','وجائز رفعك معطوفا على ... منصوب إن بعد أن تستكملا','grammar_instruction',[],True,'A grammatical instruction about completed إن is not an observation about an individual.'),
('x05','sibawayhi','إن عمرا مسافر','standalone_example',[fact('مسافر','عمرو')],False,'The source gives an example inside a grammar discussion; as a selected utterance its ordinary reading is a traveling person named عمرو, but bare إن, the accusative alif, and name-specific orthography exceed this pilot.'),
('x06','sibawayhi','إن زيدا الظريف منطلق','standalone_modified_example',[fact('منطلق','زيد')],False,'An adjective between the governed subject and predicate must not be taken as the whole predicate. The minimum target meaning does not exhaust adjectival meaning.')]
X=[]
for i,s,needle,kind,gold,must_defer,note in specs:
 d=docs[s]; raw=subprocess.check_output(['git','show',BASE+':src/nabt/data/source_evidence/'+s+'.txt'],cwd=ROOT)
 assert hashlib.sha256(raw).hexdigest()==d['sha256']
 n=needle.encode();start=raw.index(n);end=start+len(n)
 assert raw.find(n,end)<0
 line=raw[:start].count(b'\n')+1
 lines=raw.splitlines(keepends=True); offsets=[0]
 for l in lines:offsets.append(offsets[-1]+len(l))
 cs=offsets[max(0,line-2)];ce=offsets[min(len(lines),line+1)]
 X.append({'id':i,'document_id':s,'pinned_url':d['pinned_url'],'document_sha256':d['sha256'],'document_git_blob':d['git_blob_sha1'],'source_line_1based':line,'byte_start':start,'byte_end':end,'raw_text':needle,'excerpt_sha256':hashlib.sha256(n).hexdigest(),'context_byte_start':cs,'context_byte_end':ce,'context_text':raw[cs:ce].decode(),'kind':kind,'gold':{'facts':gold,'requires_structure_or_defer':must_defer,'expected_profile_acceptance':False,'notes':note},'license':d['declared_corpus_license']})
jd(OUT/'original_excerpts.json',{'schema':'nabt.governors.independent-excerpts.v1','selection':'Six exact, newly selected intervals from already available books; not new books and not a random language sample. No normalization or vocalization. Context preserved separately. Original grammar examples are evaluated as selected utterances, not as external world-truth reports.','examples':X})
protocol={
 'schema':'nabt.governors.independent-protocol.v1',
 'baseline_commit':subprocess.check_output(['git','rev-parse',BASE],cwd=ROOT,text=True).strip(),
 'mashru_commit':PIN,
 'profile':'nabt.arabic-governors.v1','task':'governor_inquiry',
 'freeze_before':'No new governor_reader, arabic_reader, semantics, program implementation or new tests have been read by this evaluator.',
 'separation':'Procedural agent separation on shared filesystem; neither access-control isolation nor human-linguist review. Expectations authored from prior docs and primary texts; never from runtime output.',
 'group_denominators':{'declared_scope':12,'beyond_declared_scope':4,'safety_control':16,'original_excerpts':6},
 'declared_scope':'Explicit unquoted إنّ/إِنَّ/إنَّ, single subject and predicate; independent nominal evidence; source-local named identity from natural prior explicit predication; overt correct case; unique stem witness for added accusative alif. Quoted mentions are not operators. Existing v1 grammar remains usable in this explicitly versioned profile.',
 'not_in_scope':['Automatic individual identity from an indefinite nominal','Coordinated governor predicates or clauses','Bare إن as automatic emphatic operator','Unlicensed accusative-alif deletion','Temporal and belief operator semantics','New world-truth claims'],
 'metrics':[
  'Complete episode coverage: every required positive source matches exact independent fact/rule projection and all query/revision results match; unknown/defer is not positive coverage.',
  'Safe controls: reject or retain genuinely scoped nonassertive content without forbidden flat facts; separate from complete-reading numerator.',
  'Governor cue extraction: report byte-exact governor/subject/predicate spans, nominality witness, observed case, independently computed target role, and source-local identity witness where required.',
  'Indefinite cue extraction g16 must be distinguished from accepted named-reference semantics; explicit missing-reference obligation required.',
  'Original excerpts: exact bytes/context provenance, retained structure or suspension, full reading coverage reported separately.',
  'Source lifecycle: successful removal/replacement removes obsolete evidence; new answers cite current active source versions only.',
  'Certificates: independent atom/rule/substitution/query/source-span checks. Missing, truncated, wrong-role, wrong-source, wrong-query, malformed proofs fail replay rather than become safe abstention.'
 ],
 'expected_bounds':{'unsafe_admitted_facts':0,'wrong_source_or_query_certificate_acceptances':0,'byte_roundtrip_failures':0},
 'coverage_gate':'Report actual coverage out of each frozen denominator; do not replace failed cases. Do not claim release or broad Arabic competence from an empty-acceptance safety pass.',
 'timing':'Single local execution is diagnostic only; repeated/controlled timing not required by this linguistic scope.',
 'revisions':'Never rewrite gold after opening implementation/results. Corrections, if necessary, are additive dated errata with original results preserved.',
 'mutation_plan':['governor role span shifted by one UTF-8 byte','subject and predicate role spans swapped','source identity replaced with another episode source','supporting grammar-source citation removed/replaced','proof query replaced by an unrelated atom','proof node or premise omitted','malformed proof structures must fail replay']
}
jd(OUT/'protocol.json',protocol)
validation={'episodes':len(E),'groups':{k:sum(e['group']==k for e in E) for k in ('declared_scope','beyond_declared_scope','safety_control')},'original_excerpts':len(X),'all_original_bytes_match':True,'no_fard_declarations':all('فرد ' not in x.get('text','') for e in E for x in e['events']),'authoring_runtime_reads':[]}
for e in E:
 for ev in e['events']:
  if 'text_sha256' in ev:assert hashlib.sha256(ev['text'].encode()).hexdigest()==ev['text_sha256']
  for w in ev.get('gold',{}).get('governor_witness',{}).get('roles',[]): assert ev['text'].encode()[w['start']:w['end']].decode()==w['raw']
jd(OUT/'dataset_validation.json',validation)
files=['build_frozen_material.py','episodes.json','original_excerpts.json','protocol.json','dataset_validation.json']
freeze={'schema':'nabt.governors.independent-material-freeze.v1','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[{'path':p,'sha256':hashlib.sha256((OUT/p).read_bytes()).hexdigest(),'bytes':(OUT/p).stat().st_size} for p in files]}
jd(OUT/'material_freeze.json',freeze)
print(json.dumps({'frozen_at_utc':freeze['frozen_at_utc'],'files':len(files),'freeze_sha256':hashlib.sha256((OUT/'material_freeze.json').read_bytes()).hexdigest(),'validation':validation},ensure_ascii=False,indent=2))
