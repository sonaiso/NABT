"""Pedagogical lexical frames for sound roots; candidates preserve original source indices."""
import unicodedata
from .operations import exact_terms
from .root_sense import _compatible_form, _profile_shapes

# Each entry is an adopted sense in this reference. A template alone never grants its frame.
FAMILIES = {
    "مجرد": (("جذب","دفع"), (
        ("فَعْل","مصدر","مؤثر متأثر"), ("فَعَلَ","فعل","مؤثر متأثر"),
        ("فُعِلَ","ماض_مجهول","متأثر"), ("فَاعِل","اسم_فاعل","مؤثر"), ("مَفْعُول","اسم_مفعول","متأثر"))),
    "انفعال": (("جذب","دفع"), (
        ("اِنْفِعَال","مصدر","حامل_تغير"),("اِنْفَعَلَ","فعل","حامل_تغير"),
        ("مُنْفَعِل","اسم_فاعل","حامل_تغير"))),
    "مشاركة": (("جذب","دفع","قتل"), (
        ("تَفَاعُل","مصدر","شريك"), ("تَفَاعَلَ","فعل","شريك"), ("مُتَفَاعِل","اسم_فاعل","شريك"))),
    "تظاهر": (("جهل",), (("تَفَاعُل","مصدر","حامل_تغير"),("تَفَاعَلَ","فعل","حامل_تغير"))),
}
# Labels name property concepts in the adopted sense. Their bearer remains unbound.
QUALITY_FRAMES = {
    ("مجرد","جذب"): ("تأثير_موجه",{"مؤثر":"جاذب","متأثر":"مجذوب"}),
    ("مجرد","دفع"): ("تأثير_موجه",{"مؤثر":"دافع","متأثر":"مدفوع"}),
    ("انفعال","جذب"): ("تغير_حامل",{"حامل_تغير":"منجذب"}),
    ("انفعال","دفع"): ("تغير_حامل",{"حامل_تغير":"مندفع"}),
    ("انفعال_مؤنث","دفع"): ("تغير_حامل",{"حامل_تغير":"مندفعة"}),
    ("مشاركة","جذب"): ("مشاركة",{"شريك":"متجاذب"}),
    ("مشاركة","دفع"): ("مشاركة",{"شريك":"متدافع"}),
    ("مشاركة","قتل"): ("مشاركة",{"شريك":"متقاتل"}),
    ("تظاهر","جهل"): ("تظاهر",{"حامل_تغير":"متجاهل"}),
}
INVENTORY = []
for family,(roots,patterns) in FAMILIES.items():
    for root in roots:
        for template,category,roles in patterns:
            word = template.translate(str.maketrans(dict(zip("فعل",root,strict=True))))
            INVENTORY.append((word,root,template,category,family,roles.split()))
INVENTORY += [("بَيْت","بيت","فَعْل","اسم_جامد","جامد",[]),("حَدِيد","حدد","فَعِيل","اسم_جامد","جامد",[])]
# The witnessed feminine past and nominal accusative have literal boundary evidence.
INVENTORY += [("مُنْدَفِعَة","دفع","مُنْفَعِلَة","اسم_فاعل","انفعال_مؤنث",["حامل_تغير"]),
              ("دَفَعَهُ","دفع","فَعَلَ","فعل_وضمير","مجرد",["مؤثر","متأثر"]),
              ("دَفْعُهُ","دفع","فَعْل","مصدر_مضاف","مجرد",["مؤثر","متأثر"]),
              ("دَفْعَهُ","دفع","فَعْل","مصدر_مضاف","مجرد",["مؤثر","متأثر"]),
              ("دَفْعِهِ","دفع","فَعْل","مصدر_مضاف","مجرد",["مؤثر","متأثر"]),
              ("اِنْدَفَعَتْ","دفع","اِنْفَعَلَ","فعل_مؤنث","انفعال",["حامل_تغير"])]

def candidates(surface):
    for word,root,template,category,family,roles in INVENTORY:
        nominal = category in {"مصدر","اسم_فاعل","اسم_مفعول","اسم_جامد"}
        record = {"surface":word,"category":"اسم فاعل" if nominal else "فعل"}
        matches = _compatible_form(surface,record)
        if nominal and not matches:
            matches = any(_compatible_form(surface,{"surface":suffix,"category":"مقطع"})
                          for suffix in (word+"ًا",word+"اً"))
        if matches:
            family_class, labels = QUALITY_FRAMES.get((family,root),(None,{}))
            yield {"entry":"مدخل_"+root+"_"+family+"_"+category, "canonical":word,
                   "root":root,"template":template,"category":category,"family":family,
                   "roles":["دور_"+r for r in roles],
                   "quality_class":("فئة_"+family_class) if family_class else None,
                   "quality_by_role":{"دور_"+r:"صفة_"+labels[r] for r in roles}}

def shape_proposals(surface):
    """Recover an unlisted root only at the shape layer, retaining all compatible vowels."""
    def skeleton(word):
        return "".join(c for c in word if not unicodedata.category(c).startswith("M"))
    patterns = sorted({template for _,(_,forms) in FAMILIES.items() for template,_,_ in forms})
    table = {p:skeleton(p).translate(str.maketrans("فعل","123")) for p in patterns}
    shapes = _profile_shapes(skeleton(surface),[{"template":t} for t in table.values()])
    offered = []
    for shape in shapes:
        root = shape["root"]
        for template,encoded in table.items():
            if encoded != shape["template"]:
                continue
            word = template.translate(str.maketrans("فعل",root))
            nominal = any(t == template and cat != "فعل" and cat != "ماض_مجهول"
                          for _,(_,forms) in FAMILIES.items() for t,cat,_ in forms)
            if _compatible_form(surface,{"surface":word,"category":"اسم فاعل" if nominal else "فعل"}):
                offered.append({"root":root,"template":template,"status":shape["status"]})
    return offered

def compile_occurrences(atoms, text, add):
    words = exact_terms(text)
    records = []
    for fact in atoms:
        if fact[0] != "موضع_لفظ":
            continue
        _, reading, position = fact
        index = int(position.split("_",1)[1])-1
        if not 0 <= index < len(words):
            raise ValueError("Occurrence outside original source")
        token = words[index]
        options = list(candidates(token["surface"]))
        records.append({**token,"reading":reading,"ordinal":index+1,"candidates":options,
                        "shape_proposals":shape_proposals(token["surface"])})
        for option in options:
            entry = ("مرشح_قراءة",reading,option["entry"])
            add(entry,(fact,),"مطابقة_اللفظ_للمدخل")
            add(("وزن_مرشح",reading,"وزن_"+option["template"]),(entry,),"وزن_المدخل")
            selection = ("قراءة_معينة",reading,option["entry"])
            if option["quality_class"]:
                add(("عائلة_الوصف",reading,option["quality_class"]),(selection,),"أسرة_الصفات_في_المدخل")
            for role,quality in option["quality_by_role"].items():
                add(("قابلية_وصف",reading,quality),(selection,("دور_تتيحه",reading,role)),"الوصف_المرخص_لدور_المدخل")
            for role in option["roles"]:
                add(("دور_تتيحه",reading,role),(("قراءة_معينة",reading,option["entry"]),),"قابلية_القراءة_المعينة")
    return records
