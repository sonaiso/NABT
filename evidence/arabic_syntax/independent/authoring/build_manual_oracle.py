from pathlib import Path
import hashlib,json
P=Path('/tmp/nabt-syntax-independent')
def a(p,*args,positive=True): return {'predicate':p,'args':list(args),'positive':positive}
def f(p,x,positive=True): return {'facts':[a(p,x,positive=positive)],'rules':[]}
def r(p,q): return {'facts':[],'rules':[{'body':[a(p,'?x')],'head':a(q,'?x')}]}
manual={
 'لمى طبيبة.':f('طبيبة','لمى'),
 'لمى مهندسة.':f('مهندسة','لمى'),
 'كل باحث دقيق.':r('باحث','دقيق'),
 'عمار باحث.':f('باحث','عمار'),
 'كل باحث مثابر.':r('باحث','مثابر'),
 'مالك حاضر.':f('حاضر','مالك'),
 'ريم حاضرة.':f('حاضرة','ريم'),
 'ليست ريم حاضرة.':f('حاضرة','ريم',False),
 'كل محلل دقيق.':r('محلل','دقيق'),
 'كل دقيق موثوق.':r('دقيق','موثوق'),
 'نبيل محلل.':f('محلل','نبيل'),
 'كل باحثة متأنية.':r('باحثة','متأنية'),
 'زهراء باحثة.':f('باحثة','زهراء'),
 'أروى حاضرة.':f('حاضرة','أروى'),
 'ليست زهراء باحثة.':f('باحثة','زهراء',False),
 'فرد منير. ليس منير علامة.':f('علامة','منير',False),
}
records={}
for filename in ('episodes.json','scope_episodes.json'):
  for c in json.loads((P/filename).read_text())['cases']:
    for e in c['events']:
      if e['op'] not in ('add','replace'): continue
      raw=e['text']; key=hashlib.sha256(raw.encode()).hexdigest()
      if 'gold_facts' in e or 'gold_rules' in e:
        expected={'facts':e.get('gold_facts',[]),'rules':e.get('gold_rules',[])}
        for name in ('gold_query','gold_mode','ambiguity'):
          if name in e: expected[name]=e[name]
      elif raw in manual: expected=manual[raw]
      elif key in records: continue
      else: continue
      if key in records:
        assert records[key]['expected']==expected,(raw,records[key]['expected'],expected)
      records[key]={'raw_text':raw,'source_text_sha256':key,'expected':expected}
missing=[]
for filename in ('episodes.json','scope_episodes.json'):
  for c in json.loads((P/filename).read_text())['cases']:
    for e in c['events']:
      if e['op'] in ('add','replace') and hashlib.sha256(e['text'].encode()).hexdigest() not in records: missing.append((c['id'],e['text']))
assert not missing,missing
# No production parser or recurrence generated these expected interpretations.
data={'schema':'nabt.arabic-syntax.manual-oracle.v1','scope':'Expected source interpretations copied from frozen manual annotations, with manually added repeated/revised source interpretations.','records':list(records.values())}
raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode(); (P/'manual_oracle.json').write_bytes(raw)
print(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(),'unique_source_documents':len(records)}))
