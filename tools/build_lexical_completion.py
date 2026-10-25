"""Add source-replayed interpretations without rewriting the v1 catalogue.

Each gloss is an explicitly authored, atomic interpretation. Words occurring
inside a gloss are NOT automatically semantic parts. Deictic 'well known'
glosses stay unresolved. This is not an exhaustive sense inventory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from tools.build_lexical_catalog import citation
from tools.lexical_training.data import fetch_lisan, LISAN_REV, MAQAYIS_REV
from nabt.source_lexicon import SourceLexicon

FOLDER = ROOT / 'evidence/lexical_completion_v1'
BASE_SHA = '13988ecec13e541cf4f7cd242df43badbe718a26d30691fbf7584363d612df49'
# entry index, lexical form, immutable quotation, interpreted whole gloss.
SELECTED = [
 ('earth','أرض','الأرض','الأرض: التي عليها الناس،','التي عليها الناس'),
 ('child','ولد','الولد','والولد، بالضم: ما ولد أيا كان،','ما ولد أيا كان'),
 ('going','ذهب','الذهاب','الذهاب: السير والمرور؛','السير والمرور'),
 ('sitting','جلس','الجلوس','الجلوس: القعود.','القعود'),
 ('exit','خرج','الخروج','الخروج: نقيض الدخول.','نقيض الدخول'),
 ('entry','دخل','الدخول','الدخول: نقيض الخروج،','نقيض الخروج'),
 ('ignorance','جهل','الجهل','الجهل: نقيض العلم،','نقيض العلم'),
 ('knowledge','علم','العلم','والعلم: نقيض الجهل،','نقيض الجهل'),
 ('night','ليل','الليل','الليل: عقيب النهار ومبدؤه من غروب الشمس.','عقيب النهار ومبدؤه من غروب الشمس'),
 ('stone','حجر','الحجر','الحجر: الصخرة،','الصخرة'),
 ('sky','سما','السماء','والسماء: كل ما علاك فأظلك؛','كل ما علاك فأظلك'),
 ('eye-vision','عين','العين','العين: حاسة البصر والرؤية،','حاسة البصر والرؤية'),
 ('eye-spy','عين','العين','والعين: الديدبان والجاسوس.','الديدبان والجاسوس'),
 ('eye-spring','عين','العين','والعين: ينبوع الماء الذي ينبع من الأرض ويجري،','ينبوع الماء الذي ينبع من الأرض ويجري'),
 ('eye-cash','عين','العين','والعين: النقد،','النقد'),
 ('eye-letter','عين','العين','والعين: حرف هجاء،','حرف هجاء'),
 ('bed-lying','سرر','السرير','والسرير: المضطجع،','المضطجع'),
 ('bed-seat','سرر','السرير','والسرير: الذي يجلس عليه معروف.','الذي يجلس عليه'),
 ('sun-deictic','شمس','الشمس','الشمس: معروفة.',None),
 ('tree-stem','شجر','الشجر','الشجر والشجر من النبات: ما قام على ساق؛','من النبات ما قام على ساق'),
 ('tree-rising','شجر','الشجر','وقيل: الشجر\n~~كل ما سما بنفسه، دق أو جل،','كل ما سما بنفسه، دق أو جل'),
 ('man','رجل','الرجل','الرجل: معروف الذكر من نوع الإنسان خلاف المرأة،','الذكر من نوع الإنسان خلاف المرأة'),
 ('truth','صدق','الصدق','الصدق: نقيض الكذب،','نقيض الكذب'),
 ('falsehood','كذب','الكذب','الكذب: نقيض الصدق؛','نقيض الصدق'),
]

def sha(raw): return hashlib.sha256(raw).hexdigest()

def build(lisan_path):
    raw_base=(ROOT/'evidence/lexical_denotation/catalog.json').read_bytes()
    if sha(raw_base)!=BASE_SHA:raise ValueError('v1 catalogue identity changed')
    base=json.loads(raw_base)
    lisan=fetch_lisan(lisan_path)
    index=SourceLexicon('lisan',lisan)
    s3=(ROOT/'evidence/mantuq_mafhum/sources/shakhsiyya3.txt').read_bytes()
    maq=(ROOT/'evidence/classical_language/sources/maqayis.txt').read_bytes()
    SourceLexicon('maqayis',maq)
    sources={'lisan':(lisan,LISAN_REV),'maqayis':(maq,MAQAYIS_REV),
             'shakhsiyya3':(s3,'user-supplied-2026-10-24-excerpt-v1')}
    extras=[]
    for name,entry,lemma,quote,gloss in SELECTED:
        c=citation('lisan',quote,sources)
        blocks=[b for b in index.blocks if b.start_byte<=c['start_byte']<c['end_byte']<=b.end_byte]
        if len(blocks)!=1 or blocks[0].heading!=entry:raise ValueError('Quotation outside expected source heading: '+name)
        extras.append({'id':'lisan:v2:'+name,'root':entry,'lemma':lemma,'citation':c,
            'components':[] if gloss is None else [gloss],
            'interpretation_status':'UNRESOLVED_DEICTIC_GLOSS' if gloss is None else 'AUTHORED_NOT_INDEPENDENTLY_ADJUDICATED',
            'scope':'selected definition reading; whole gloss is atomic',
            'heading_block':{'start_byte':blocks[0].start_byte,'end_byte':blocks[0].end_byte,'sha256':blocks[0].block_sha256},
            'residuals':['PREVIOUS_KNOWLEDGE_REQUIRED'] if gloss is None else []})
    necessity={'sense_id':'lisan:v2:bed-lying','target':'الارتفاع','kind':'mental',
        'citation':citation('shakhsiyya3','كالسرير والارتفاع',sources),
        'alignment_status':'AUTHORED_CROSS_SOURCE_SENSE_ALIGNMENT',
        'scope':'mental transition in this source theory; no assertion of a physical bed or its location'}
    return {**base,'schema':'nabt.lexical-denotation.catalog.v2','base_catalogue_sha256':BASE_SHA,
        'catalogue_id':'nabt.lexical-completion-catalogue.v1',
        'senses':base['senses']+extras,'necessities':base['necessities']+[necessity],
        'selection_note':'24 supplemental authored readings selected from the pinned Lisan; one remains unresolved. No exhaustive sense claim.',
        'source_index_is_not_lemma':True}

def lean(c):
    q=lambda s:json.dumps(s,ensure_ascii=False)
    def cit(x):return '⟨'+', '.join([q(x['work']),q(x['revision']),q(x['source_sha256']),str(x['start_byte']),str(x['end_byte']),q(x['quotation'])])+'⟩'
    lines=['import Nabt.LexicalCatalog','','-- Generated by tools/build_lexical_completion.py. Interpretations remain explicit premises.',
        'namespace Nabt.LexicalCompletionCatalog','open LexicalDenotation',
        'def catalogueId : String := "nabt.lexical-completion-catalogue.v1"']
    for i,s in enumerate(c['senses'][18:]):
        lines.append(f'def extra{i} : Sense := ⟨{q(s["id"])}, {q(s["root"])}, {cit(s["citation"])}, [{", ".join(map(q,s["components"]))}]⟩')
    lines.append('def senses : List Sense := LexicalCatalog.senses ++ ['+', '.join('extra'+str(i) for i in range(24))+']')
    r=c['necessities'][-1]
    lines.append('def necessities : List Necessity := LexicalCatalog.necessities ++ [⟨extra16, '+q(r['target'])+', .mental, '+cit(r['citation'])+'⟩]')
    lines.extend(['end Nabt.LexicalCompletionCatalog',''])
    return '\n'.join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lisan',type=Path,default=ROOT/'artifacts/local/lisan.txt');p.add_argument('--check',action='store_true');a=p.parse_args()
    c=build(a.lisan)
    outputs={FOLDER/'catalog.json':json.dumps(c,ensure_ascii=False,indent=2)+'\n',ROOT/'formal/Nabt/LexicalCompletionCatalog.lean':lean(c)}
    for path,text in outputs.items():
        if a.check:
            if path.read_text()!=text:raise ValueError('Generated catalogue drift: '+str(path))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    print(json.dumps({'readings':len(c['senses']),'interpreted':sum(bool(s['components']) for s in c['senses']),
                      'unresolved':sum(not s['components'] for s in c['senses']),'mental_rules':len(c['necessities']),'world_truth_established':False}))
if __name__=='__main__':main()
