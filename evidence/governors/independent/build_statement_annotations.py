from pathlib import Path
import json,hashlib,datetime,re
D=Path('/tmp/nabt-governor-independent-new')
cases=json.loads((D/'episodes.json').read_text())['episodes']

def atom(p,x,positive=True):return {'predicate':p,'args':[x],'positive':positive}
def annotation(raw,statement,roles,facts=(),rules=(),kinds=()):
 start=raw.index(statement); end=start+len(statement)
 tokens=list(re.finditer(r'«[^«»]*»|[^\s«»]+',statement))
 assert len(tokens)==len(roles),(statement,len(tokens),len(roles))
 return {'start':len(raw[:start].encode()),'end':len(raw[:end].encode()),'facts':list(facts),'rules':list(rules),'rule_kinds':list(kinds),'components':[{'start':len(raw[:start+t.start()].encode()),'end':len(raw[:start+t.end()].encode()),'roles':[role]} for t,role in zip(tokens,roles)]}
records={}
for case in cases:
 if case['group']!='declared_scope':continue
 for ev in case['events']:
  if ev['op']!='add':continue
  raw=ev['text'];digest=hashlib.sha256(raw.encode()).hexdigest()
  if digest in records:continue
  statements=[p.strip() for p in raw.split('.') if p.strip()]
  facts=ev['gold']['facts']; rules=[]
  for rule in ev['gold']['rules']:
   body=[{**a,'args':['?x' if x=='$x' else x for x in a['args']]} for a in rule['body']]
   head={**rule['head'],'args':['?x' if x=='$x' else x for x in rule['head']['args']]}
   rules.append({'body':body,'head':head})
  anns=[];factindex=0
  for s in statements:
   if s.startswith('كلُّ '):
    anns.append(annotation(raw,s,['quantifier','body.predicate','head.predicate'],rules=rules,kinds=['universal']))
   elif s.startswith(('إنّ ','إنَّ ','إِنَّ ')):
    anns.append(annotation(raw,s,['governor','subject','predicate'],facts=[facts[factindex]]));factindex+=1
   elif s.startswith('ليس '):
    anns.append(annotation(raw,s,['negation','subject','copula','predicate'],facts=[facts[factindex]]));factindex+=1
   else:
    anns.append(annotation(raw,s,['quoted_subject' if s.startswith('"') else 'subject','copula','predicate'],facts=[facts[factindex]]));factindex+=1
  assert factindex==len(facts)
  records[digest]={'source_text_sha256':digest,'raw_text':raw,'facts':facts,'rules':rules,'statements':anns}
obj={'schema':'nabt.governors.independent-statement-annotations.v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Authored solely from the already frozen authored cases and explicit manual component-role choices, before opening new code/results. No production-reader import. The gold notation $x is mapped to alpha-equivalent ?x in replay input.','records':list(records.values())}
p=D/'statement_annotations.json';p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
freeze={'schema':'nabt.governors.annotation-freeze.v1','created_at_utc':obj['created_at_utc'],'parent_freeze_sha256':hashlib.sha256((D/'material_freeze.json').read_bytes()).hexdigest(),'files':[{'path':x,'sha256':hashlib.sha256((D/x).read_bytes()).hexdigest(),'bytes':(D/x).stat().st_size} for x in ('build_statement_annotations.py','statement_annotations.json')]}
f=D/'annotation_freeze.json';f.write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'records':len(records),'annotation_freeze_sha256':hashlib.sha256(f.read_bytes()).hexdigest()},indent=2))
