from pathlib import Path
import hashlib,json
P=Path('/tmp/nabt-syntax-independent')
def a(p,*args,positive=True): return {'predicate':p,'args':list(args),'positive':positive}
data={'schema':'nabt.arabic-syntax.gold-review.v1','stage':'Pre-runtime-freeze linguistic review by the same independent author; no new implementation or builder tests inspected.','frozen_corpus_unchanged':True,'purpose':'Avoid labeling a semantically sound common consequence unsafe merely because the broader construction remains outside the declared profile. Original bytes and main annotations remain inspectable.','overrides':[
 {'case_id':'a03','safety_allowed_facts':[a('طبيب','خالد'),a('ماهر','خالد')],'note':'A nominal predicate plus its adjective supports these unary properties; the forbidden result is the spurious binary relation طبيب(خالد,ماهر). Full structured-reading credit remains separate.'},
 {'case_id':'a05','safety_allowed_rules':[{'body':[a('طالب','?x')],'head':a('حاضر','?x',positive=False)}],'note':'Negation of a genus may license a universal negative conditional. It does not license treating طالب as a named individual.'},
 {'case_id':'a07','safety_allowed_facts':[a('حضر','عادل',positive=False)],'note':'The positive completed exception can support exclusion of the named exception from attendance; unknown class membership prevents fabricating other named attendees.'}
],'reporting':'Report the unchanged corpus digest plus this review digest; this review is part of the manual gold frozen before exposure, not a score repair after running the new system.'}
raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode(); (P/'gold_review.json').write_bytes(raw)
print(hashlib.sha256(raw).hexdigest())
