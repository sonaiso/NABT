"""Scoped slots for agricultural and feeding senses, plus a bounded Arabic clause reader."""
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
import re
import unicodedata

from tools.arabic_training.source_reading import compatible
from .operations import exact_terms

@dataclass(frozen=True)
class Slot:
    role: str
    genus: str
    trait: str
    description: str

def slot(role, genus, trait, description):
    return Slot(role, "نوع_"+genus, "صفة_"+trait, "صفة_"+description)

PLANTER = slot("فاعل","قائم_بالغرس","قادر_على_الزرع","زارع")
PLANTED = slot("مفعول","نبات","صالح_للغرس","مزروع")
SEED = slot("مفعول","بذر","صالح_للبذر","مبذور")
LAND = slot("مفعول","أرض","صالحة_للحرث","محروثة")
EATER = slot("فاعل","حي","قادر_على_تناول_الغذاء","آكل")
FOOD = slot("مفعول","مادة_غذائية","قابل_للتناول","مأكول")
GROWER = slot("حامل","نبات","قابل_للنمو","نابت")
CAUSE = slot("سبب","عامل_إنبات","قادر_على_الإنبات","منبت")
RESULT = slot("محل_الأثر","نبات","قابل_للنمو","مستجيب_للإنبات")
PARTNER = slot("طرف_معاملة","طرف_معاملة","أهل_للمزارعة","مزارع")

@dataclass(frozen=True)
class Frame:
    valency: str
    slots: tuple
    action: str

FEELER = slot("صاحب_شعور","ذي_شعور","قابل_للسرور","سعيد")
STIMULUS = slot("سبب","مؤثر_وجداني","قابل_للإسعاد","مسعد")
FRAMES = {
    "كتابة": Frame("متعد",(slot("فاعل","كاتب_محتمل","قادر_على_الكتابة","كاتب"),
                           slot("مفعول","محتوى","قابل_للكتابة","مكتوب")),"كتابة"),
    "ولادة": Frame("إطار_ولادة",(slot("والدة","كائن_حي","قابل_للولادة","والدة"),
                               slot("وليد","كائن_حي","قابل_لأن_يولد","مولود")),"ولادة"),
    "تجارة": Frame("إطار_معاملة",(PARTNER,slot("متداول","مال","قابل_للتداول","متداول")),"تجارة"),
    "كبر": Frame("لازم",(slot("حامل","نبات","قابل_للنمو","نام"),),"كبر"),
    "نماء": Frame("لازم",(slot("حامل","نبات","قابل_للنمو","نام"),),"نماء"),
    "اخضرار": Frame("لازم",(slot("حامل","نبات","قابل_للاخضرار","مخضر"),),"اخضرار"),
    "سعادة": Frame("لازم",(FEELER,),"سعادة"),
    "إسعاد": Frame("متعد_سببي",(STIMULUS,FEELER),"إسعاد"),
    "موت": Frame("لازم",(slot("حامل","حي","قابل_للموت","ميت"),),"موت"),
    "غرس": Frame("متعد",(PLANTER,PLANTED),"غرس"),
    "بذر": Frame("متعد",(PLANTER,SEED),"بذر"),
    "حرث": Frame("متعد",(PLANTER,LAND),"حرث"),
    "تغذية": Frame("متعد",(EATER,FOOD),"أكل"),
    "نمو": Frame("لازم",(GROWER,),"نمو"),
    "إنبات": Frame("متعد_سببي",(CAUSE,RESULT),"إنبات"),
    "معاملة": Frame("متعد_إلى_شريك",(PARTNER,),"مزارعة"),
}
@dataclass(frozen=True)
class Form:
    word: str
    root: str
    pattern: str
    kind: str
    sense: str
    use: str
    roles: tuple = ()

    @property
    def entry(self):
        return "مدخل_"+self.root+"_"+self.sense+"_"+self.kind

FORMS = []
def forms(root, sense, rows):
    FORMS.extend(Form(w,root,p,k,sense,u,tuple(r.split())) for w,p,k,u,r in rows)

for sense in ("غرس","بذر","حرث"):
    forms("زرع",sense,[
        ("زَرَعَ","فَعَلَ","فعل","معلوم","فاعل مفعول"),("زُرِعَ","فُعِلَ","فعل_مجهول","مجهول","مفعول"),
        ("زَرْع","فَعْل","مصدر","مصدر_مجرد_مسموع","فاعل مفعول"),
        ("زِرَاعَة","فِعَالَة","مصدر_ثان","مصدر_مجرد_مسموع","فاعل مفعول"),
        ("زَارِع","فَاعِل","اسم_فاعل","اسم","فاعل"),("مَزْرُوع","مَفْعُول","اسم_مفعول","اسم","مفعول"),
        ("زَرْعَة","فَعْلَة","اسم_مرة","مرة_من_الحدث","فاعل مفعول")])
forms("زرع","محصول",[("زَرْع","فَعْل","اسم_جنس","ناتج_الزرع","")])
forms("زرع","مكان",[("مَزْرَعَة","مَفْعَلَة","اسم_مكان","مكان_الزرع",""),("مَزَارِع","مَفَاعِل","جمع_مكان","أماكن_الزرع","")])
forms("زرع","مهنة",[("مُزَارِع","مُفَاعِل","اسم_مهنة","مهنة_الزراعة","")])
forms("زرع","معاملة",[("زَارَعَ","فَاعَلَ","فعل","معلوم_معاملة","طرف_معاملة"),
                        ("مُزَارَعَة","مُفَاعَلَة","مصدر","مصدر_مزيد_قياسي","طرف_معاملة"),
                        ("مُزَارِع","مُفَاعِل","اسم_فاعل","اسم","طرف_معاملة")])
for sense,use in (("بذور","بذر_مسمى"),("أرض","أرض_مزروعة")):
    forms("زرع",sense,[("زَرِيعَة","فَعِيلَة","اسم",use,"")])
forms("أكل","تغذية",[("أَكَلَ","فَعَلَ","فعل","معلوم","فاعل مفعول"),("أُكِلَ","فُعِلَ","فعل_مجهول","مجهول","مفعول"),
    ("أَكْل","فَعْل","مصدر","مصدر_مجرد_مسموع","فاعل مفعول"),("آكِل","فَاعِل","اسم_فاعل","اسم","فاعل"),
    ("آكِلُونَ","فَاعِلُونَ","جمع_فاعل","جمع_عامل","فاعل"),("مَأْكُول","مَفْعُول","اسم_مفعول","اسم","مفعول"),
    ("مَأْكُولَات","مَفْعُولَات","جمع_مفعول","جمع_محال","مفعول")])
forms("نبت","نمو",[("نَبَتَ","فَعَلَ","فعل","معلوم","حامل"),("نَبَات","فَعَال","مصدر","مصدر_مجرد_مسموع","حامل"),
                     ("نَابِت","فَاعِل","اسم_فاعل","اسم","حامل")])
forms("نبت","جنس",[("نَبَات","فَعَال","اسم_جنس","اسم_نبات","")])
forms("نبت","إنبات",[("أَنْبَتَ","أَفْعَلَ","فعل","معلوم","سبب محل_الأثر"),
    ("إِنْبَات","إِفْعَال","مصدر","مصدر_مزيد_قياسي","سبب محل_الأثر"),
    ("مُنْبِت","مُفْعِل","اسم_فاعل","اسم","سبب")])
for root,sense,past,pattern,roles in (
    ("كبر","كبر","كَبُرَتْ","فَعُلَتْ","حامل"), ("نمو","نماء","نَمَتْ","فَعَتْ","حامل"),
    ("خضر","اخضرار","اِخْضَرَّتْ","اِفْعَلَّتْ","حامل"),("سعد","سعادة","سَعِدَ","فَعِلَ","صاحب_شعور"),
    ("سعد","إسعاد","أَسْعَدَتْ","أَفْعَلَتْ","سبب صاحب_شعور"),("موت","موت","مَاتَ","فَعَلَ","حامل")):
    forms(root,sense,[(past,pattern,"فعل","معلوم",roles)])
forms("سعد","سعادة",[("سَعَادَة","فَعَالَة","مصدر","مصدر_مجرد_مسموع","صاحب_شعور")])
forms("سعد","إسعاد",[("إِسْعَاد","إِفْعَال","مصدر","مصدر_مزيد_قياسي","سبب صاحب_شعور")])
forms("موت","موت",[("مَوْت","فَعْل","مصدر","مصدر_مجرد_مسموع","حامل")])
forms("خضر","اخضرار",[("اِخْضِرَار","اِفْعِلَال","مصدر","مصدر_مزيد_قياسي","حامل")])
for root,sense,word,roles in (("كتب","كتابة","كِتَابَة","فاعل مفعول"),
                             ("ولد","ولادة","وِلَادَة","والدة وليد"),
                             ("تجر","تجارة","تِجَارَة","طرف_معاملة متداول")):
    forms(root,sense,[(word,"فِعَالَة","مصدر","مصدر_مجرد_مسموع",roles)])
BY_ENTRY={form.entry:form for form in FORMS}
ROLE_NAMES=tuple(dict.fromkeys(s.role for frame in FRAMES.values() for s in frame.slots))
BASE={"قرينة_مدلول":("قراءة","نوع"),"قرينة_الباء":("قراءة","وجه"),"قرينة_ترتيب":("قراءة","رتبة"),"مرجع_الأوجه":("قراءة","مرجع"),"إحالة_اسم":("قراءة","عين"),"تفسير_إضافة":("قراءة","وجه")}
DERIVED={"مدلول_مرشح":("قراءة","نوع"),"إضافة_اسمية":("قراءة","قراءة"),
         "زمان_مذكور":("قراءة","قراءة"),"مكان_مذكور":("قراءة","قراءة"),
         "متعلق_بالباء":("قراءة","قراءة"),"سبب_منسوب":("قراءة","قراءة"),"جهة_الصيغة":("قراءة","جهة"),"تعدية_الأصل":("قراءة","تعدية"),
         "مدلول_الاسم":("قراءة","نوع"),"مرجع_موافق":("قراءة","عين"),
         "فاعل_مقروء":("قراءة","قراءة"),"نائب_مقروء":("قراءة","قراءة"),"مفعول_مقروء":("قراءة","قراءة"),
         "أسرة_المصدر":("قراءة","مصدر"),"حقل_معجمي":("قراءة","جذر"),
         "مضاف_إليه_مقروء":("قراءة","قراءة"),"اقتران_مكتمل":("قراءة","عمل")}
for r in ROLE_NAMES:
    DERIVED.update({"جنس_شرط_"+r:("قراءة","نوع"),"خاصية_شرط_"+r:("قراءة","صفة"),
                    "موضع_"+r:("قراءة","قراءة"),"صالح_"+r:("قراءة","عين")})

def surfaces(form):
    if form.word=="أَسْعَدَتْ":
        return [form.word,"أَسْعَدَتِ"]
    if form.kind.startswith("فعل"):
        return [form.word]
    bases=[form.word,"ال"+form.word]
    if form.use=="جمع_عامل":
        return bases
    # Nouns with the article never receive tanwin. The diptote plural has its own endings.
    bare=form.word
    if form.kind=="جمع_مكان":
        return [bare,bare+"ُ",bare+"َ",*["ال"+bare+v for v in ("","َ","ِ","ُ")]]
    indefinite=[bare+v for v in ("","َ","ِ","ُ","ٌ","ٍ")]
    if form.kind=="جمع_مفعول":
        indefinite=[bare+v for v in ("","ُ","ِ","ٌ","ٍ")]
    elif bare.endswith("ة"):
        indefinite.append(bare+"ً")
    else:
        indefinite.extend((bare+"ًا",bare+"اً"))
    article_marks=("","ِ","ُ") if form.kind=="جمع_مفعول" else ("","َ","ِ","ُ")
    return indefinite+["ال"+bare+v for v in article_marks]

def article_forms(word):
    # Optional citation vocalization for lam and sun-letter assimilation.
    yield word
    if word.startswith("ال") and len(word)>2:
        if word[2] in "تثدذرزسشصضطظلن":
            yield word[:3]+"ّ"+word[3:]
        else:
            yield "الْ"+word[2:]

def spelling(word):
    return re.sub(r"[\u064b-\u0652]","",word)

@lru_cache(maxsize=1)
def lexical_index():
    index=defaultdict(list)
    for form in FORMS:
        for source in surfaces(form):
            for candidate in article_forms(source):
                index[spelling(candidate)].append((form,candidate))
    return index

def candidates(surface):
    matched=set()
    for form,word in lexical_index().get(spelling(surface),()):
        if form in matched or not compatible(surface,word):
            continue
        matched.add(form)
        frame=FRAMES.get(form.sense)
        roles=[s for s in frame.slots if s.role in form.roles] if frame else []
        yield {"entry":form.entry,"canonical":form.word,"root":form.root,"template":form.pattern,
               "category":form.kind,"family":form.sense,"roles":["دور_"+s.role for s in roles],
               "quality_class":("فئة_"+form.sense) if roles else None,
               "quality_by_role":{"دور_"+s.role:s.description for s in roles}}

# A fully marked final case is mandatory for this surface fragment. The type witness
# for an actual referent is always a separate signed ground fact.
NOUNS = {
    "الْفَلَّاح":"فلاح","الْمُزَارِع":"مزارع","الشَّجَرَة":"شجر","النَّبَات":"نبات",
    "الْعُشْب":"عشب","الْحَيَوَان":"حيوان","الْخَرُوف":"خروف","الْمَاء":"ماء",
    "الْحَبّ":"بذر","الْأَرْض":"أرض","الْحَجَر":"حجر","النَّار":"نار","الطَّعَام":"مادة_غذائية","الرَّجُل":"رجل",
    "الطِّفْل":"طفل","الْهَدِيَّة":"هدية","شَجَرَة":"شجر","التِّين":"تين","الزَّيْتُون":"زيتون",
    "الصَّيْف":"صيف","الْحَقْل":"حقل","الطَّاعُون":"مرض_طاعون"}
AMBIGUOUS_NOUNS={"نوع_تين":("نوع_شجر_تين","نوع_ثمر_تين"),
                 "نوع_زيتون":("نوع_شجر_زيتون","نوع_ثمر_زيتون")}
def noun_sense(surface):
    ending=surface[-1:] if surface[-1:] in ("ُ","َ","ِ") else ""
    normal=unicodedata.normalize("NFC",surface)
    for noun,kind in NOUNS.items():
        if compatible(normal,unicodedata.normalize("NFC",noun+ending)):
            return ending,"نوع_"+kind
    return None

@dataclass(frozen=True)
class Construction:
    heads: tuple
    endings: tuple
    genitives: tuple
    adjunct: tuple = ()

def read_construction(text, words):
    if not 2<=len(words)<=6 or text.strip().removesuffix(".").split()!=[w["surface"] for w in words]:
        return None
    tokens=[w["surface"] for w in words]
    heads, endings, genitives=[],[],[]
    adjunct=()
    i=1
    while i<len(tokens):
        if heads and compatible(tokens[i],"فِي") and i+2==len(tokens):
            obj=noun_sense(tokens[i+1])
            if not obj or obj[0] not in ("","ِ") or obj[1] not in ("نوع_صيف","نوع_حقل"):
                return None
            adjunct=("زمان_مذكور" if obj[1]=="نوع_صيف" else "مكان_مذكور",i+1)
            break
        if heads and i+1==len(tokens) and compatible(tokens[i],"بِالْهَدِيَّةِ"):
            adjunct=("متعلق_بالباء",i)
            break
        if heads and i+2==len(tokens) and compatible(tokens[i],"بِمَرَضِ") and compatible(tokens[i+1],"الطَّاعُونِ"):
            adjunct=("متعلق_بالباء",i)
            genitives.append((i,i+1))
            break
        obj=noun_sense(tokens[i])
        if not obj or len(heads)==2:
            return None
        heads.append(i)
        endings.append(obj[0])
        if spelling(tokens[i])=="شجرة" and i+1<len(tokens):
            dep=noun_sense(tokens[i+1])
            if dep and dep[1] in AMBIGUOUS_NOUNS and dep[0] in ("","ِ"):
                genitives.append((i,i+1))
                i+=1
        i+=1
    return Construction(tuple(heads),tuple(endings),tuple(genitives),adjunct)

def case_roles(form,cases):
    if not cases:
        return {}
    if form.use.startswith("مصدر") and cases==("ِ",):
        return {1:"إضافة"}
    if form.use=="مجهول" and cases==("ُ",):
        return {1:"مفعول"}
    if form.use!="معلوم":
        return {}
    frame=FRAMES[form.sense]
    roles=[s.role for s in frame.slots]
    if len(roles)==1:
        return {1:roles[0]} if cases==("ُ",) else {}
    if cases not in (("ُ",),("ُ","َ"),("َ","ُ")):
        return {}
    return {i:roles[0] if c=="ُ" else roles[1] for i,c in enumerate(cases,1)}

def compile_source(atoms, text, records, add):
    by_pos=defaultdict(list)
    for r in records:
        by_pos[r["ordinal"]].append(r)
    for pred in ("إحالة_اسم","تفسير_إضافة","قرينة_مدلول","قرينة_الباء","قرينة_ترتيب"):
        values=defaultdict(set)
        for p,r,v in atoms:
            if p==pred: values[r].add(v)
        if any(len(vals)>1 for vals in values.values()):
            raise ValueError("One bearer or interpretation per reading; retain alternatives as different readings")
    words=exact_terms(text)
    construction=read_construction(text,words)
    for record in records:
        rid=record["reading"]
        ordinal=("موضع_لفظ",rid,"عدد_"+str(record["ordinal"]))
        noun=noun_sense(record["surface"])
        if noun and noun[1] in AMBIGUOUS_NOUNS:
            for kind in AMBIGUOUS_NOUNS[noun[1]]:
                candidate=("مدلول_مرشح",rid,kind)
                add(candidate,(ordinal,),"وجه_المسمى")
                add(("مدلول_الاسم",rid,kind),(candidate,("قرينة_مدلول",rid,kind)),"تعيين_وجه_المسمى")
        elif noun:
            add(("مدلول_الاسم",rid,noun[1]),(ordinal,),"وجه_الاسم_في_المرجع")
        unique={c["entry"] for c in record["candidates"]}
        if len(unique)==1 and unique <= BY_ENTRY.keys():
            only=next(iter(unique))
            reference = ("مرجع_زراعة_وغذاء" if BY_ENTRY[only].sense in
                         {"غرس","بذر","حرث","تغذية","نمو","إنبات","معاملة","محصول","مكان","مهنة","بذور","أرض","جنس"}
                         else "مرجع_الأدوار_الدلالية")
            add(("قراءة_معينة",rid,only),(("مرجع_الأوجه",rid,reference),("مرشح_قراءة",rid,only)),
                "تفرد_داخل_المرجع_المعين")
        for option in record["candidates"]:
            f=BY_ENTRY.get(option["entry"])
            if not f: continue
            selected=("قراءة_معينة",rid,f.entry)
            add(("جهة_الصيغة",rid,"جهة_"+f.use),(selected,),"وجه_من_المدخل")
            add(("حقل_معجمي",rid,"جذر_"+f.root),(selected,),"حقل_المدخل_المعجمي")
            frame=FRAMES.get(f.sense)
            if frame:
                add(("أسرة_المصدر",rid,"مصدر_"+f.root+"_"+f.sense),(selected,),"ربط_بأسرة_المصدر")
                add(("تعدية_الأصل",rid,"تعدية_"+frame.valency),(selected,),"تعدية_المعنى")
                for s in frame.slots:
                    if s.role in f.roles:
                        add(("جنس_شرط_"+s.role,rid,s.genus),(selected,),"قيد_جنس_الدور")
                        add(("خاصية_شرط_"+s.role,rid,s.trait),(selected,),"قيد_خاصية_الدور")
            if record["ordinal"]!=1 or not construction: continue
            cases=construction.endings
            guards=()
            if "" in cases:
                if f.use=="معلوم" and len(frame.slots)==1 and cases==("",):
                    cases=("ُ",)
                elif f.use=="معلوم" and len(frame.slots)==2 and len(cases)==2 and all(
                        observed in ("",expected) for observed,expected in zip(cases,("ُ","َ"))):
                    cases=("ُ","َ")
                    guards=(("قرينة_ترتيب",rid,"رتبة_فاعل_ثم_مفعول"),)
                else:
                    continue
            roles=case_roles(f,cases)
            if not roles: continue
            for left,right in construction.genitives:
                for h in by_pos[left+1]:
                    for d in by_pos[right+1]:
                        add(("إضافة_اسمية",h["reading"],d["reading"]),
                            (selected,("موضع_لفظ",h["reading"],"عدد_"+str(left+1)),
                             ("موضع_لفظ",d["reading"],"عدد_"+str(right+1)),*guards),"إضافة_الشاهد")
            if construction.adjunct:
                relation,idx=construction.adjunct
                for arg in by_pos[idx+1]:
                    adjunct=(relation,rid,arg["reading"])
                    add(adjunct,(selected,("موضع_لفظ",arg["reading"],"عدد_"+str(idx+1)),*guards),"تعلق_شبه_الجملة")
                    if relation=="متعلق_بالباء" and f.sense in ("موت","سعادة"):
                        add(("سبب_منسوب",rid,arg["reading"]),(selected,adjunct,("قرينة_الباء",rid,"وجه_سببية")),"قراءة_الباء_السببية")
            for position,role in roles.items():
                idx=construction.heads[position-1]
                for arg in by_pos[idx+1]:
                    argid=arg["reading"]
                    body=(selected,("موضع_لفظ",argid,"عدد_"+str(idx+1)),*guards)
                    if role=="إضافة":
                        link=("مضاف_إليه_مقروء",rid,argid)
                        add(link,body,"جر_الإضافة")
                        for slotname in f.roles:
                            add(("موضع_"+slotname,rid,argid),(selected,link,("تفسير_إضافة",rid,"وجه_"+slotname)),"قرينة_لوجه_الإضافة")
                    else:
                        grammatical = "نائب_مقروء" if f.use=="مجهول" else (
                            "فاعل_مقروء" if cases[position-1]=="ُ" else "مفعول_مقروء")
                        add((grammatical,rid,argid),body,"إعراب_الشاهد")
                        add(("موضع_"+role,rid,argid),body,"وزن_وإعراب_الشاهد")
RULES=[("تحقيق_إحالة_الاسم","مرجع_موافق n x",["إحالة_اسم n x","مدلول_الاسم n g","عضوية x g"])]
for name in ROLE_NAMES:
    base=["موضع_"+name+" r n","مرجع_موافق n x","جنس_شرط_"+name+" r g","خاصية_شرط_"+name+" r p"]
    for sign,g,t,label in (("","","","تحقق"),("!","!","","انتفاء_الجنس"),("!","","!","انتفاء_الخاصية")):
        required = [g+"عضوية x g"] if g else ([t+"خاصية x p"] if t else ["عضوية x g","خاصية x p"])
        RULES.append((label+"_الدور_"+name,sign+"صالح_"+name+" r x",base+required))

# Complete pairing requires the same selected verbal reading. Edibility is relational.
for form in FORMS:
    if form.use!="معلوم": continue
    frame=FRAMES[form.sense]
    body=["قراءة_معينة r "+form.entry]
    for s,var in zip(frame.slots,("x","y")):
        body.append("صالح_"+s.role+" r "+var)
    if form.sense=="تغذية":
        body+=["عضوية x g","غذاء_لصنف y g"]
    RULES.append(("اكتمال_قابلية_"+form.sense,"اقتران_مكتمل r عمل_"+frame.action,body))
