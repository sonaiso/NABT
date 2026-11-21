"""Finite scope and explicitly interpreted rule profiles for the named ledger.

The finite quantifier owner supplies the universal aggregation plan. All
application premises stay in signed ground rules for native replay. Input
facts alone never establish that this is the correct reading of free text.
"""
from collections import defaultdict

from .composition_quantifier import project

BASE = {
    "صيغة": ("قول", "كم"), "موضوع": ("قول", "نوع"), "مطلوب": ("قول", "عمل"),
    "مجاله": ("قول", "نطاق"), "عين_الخاص": ("قول", "عين"),
    "يحصي": ("نطاق", "عين"), "حصر": ("نطاق", "عدد"),
    "قيد_صفة": ("قول", "صفة"), "قيد_قابلية": ("قول", "عمل"),
    "قيد_مادة": ("قول", "نوع"), "استثناء": ("قول", "نوع"), "أنجز": ("عين", "عمل"),
    "ضرورة_تقدير": ("قول", "وجه"), "مرشح_تقدير": ("قول", "تقدير"),
    "قرينة_التقدير": ("قول", "تقدير"), "يستقيم_به": ("تقدير", "وجه"),
    "يتطلب_فعلا": ("قول", "عمل"), "قرينة_الطلب": ("قول", "عمل"),
    "محل_نظر": ("نظر", "حدث"), "مرجع_نظر": ("نظر", "نظام"),
    "يضبط": ("نظام", "عمل"), "اصطلاح": ("نظام", "نهج"),
    "أصل_معتبر": ("حدث", "نظام"), "وصف_معتبر": ("حدث", "نظام"),
    "سبب": ("حدث", "عمل"),
}
DERIVED = {
    "وجه_التصور": ("لفظ","تصور"), "داخل_الخطاب": ("قول","عين"),
    "مستوفى_للعموم": ("قول","عين"), "شاهد_للإجزاء": ("قول","عين"),
    "وفاء_بالطلب": ("قول","عمل"), "تقدير_مسوغ": ("قول","تقدير"),
    "مدلول_الطلب": ("قول","عمل"), "يسمى_الحكم": ("نظر","لفظ"), "حكم_الاعتبار": ("نظر","حكم"),
    "ترتب_مشروط": ("نظر","عمل"),
}
RULES = [
    ("تصور_نوع", "وجه_التصور w تصور_كلي", ["اسم_كلي w g"]),
    ("تصور_معين", "وجه_التصور w تصور_جزئي", ["علم w x"]),
    ("اقتضاء_التقدير", "تقدير_مسوغ s t",
     ["ضرورة_تقدير s f","مرشح_تقدير s t","يستقيم_به t f","قرينة_التقدير s t"]),
    ("اقتضاء_الطلب", "مدلول_الطلب s a", ["يتطلب_فعلا s a","قرينة_الطلب s a"]),
]
# Every structural verdict uses a particular case, event, standard, and
# declared act. These profiles are finite teaching conventions.
introduced = ["محل_نظر n e", "مرجع_نظر n m", "يضبط m a", "نمط e a"]
for method, invalid_origin, invalid_quality in [
    ("نهج_تمييز", "حكم_باطل", "حكم_فاسد"),
    ("نهج_جمع", "حكم_غير_صحيح", "حكم_غير_صحيح"),
]:
    profile = introduced + ["اصطلاح m " + method]
    for name, conclusion, premises in [
        ("سلامة", "حكم_صحيح", ["أصل_معتبر e m", "وصف_معتبر e m"]),
        ("اختلال_الأصل", invalid_origin, ["!أصل_معتبر e m"]),
        ("اختلال_الوصف", invalid_quality, ["أصل_معتبر e m", "!وصف_معتبر e m"]),
    ]:
        RULES.append((name+"_"+method, "حكم_الاعتبار n "+conclusion, profile+premises))
    labels = {".valid": ("حكم_صحيح", "لفظ_صحيح"),
              ".origin": (invalid_origin, "لفظ_باطل"),
              ".quality": (invalid_quality, "لفظ_فاسد")}
    for code, word in labels.values():
        RULES.append(("لفظ_"+method+"_"+word, "يسمى_الحكم n "+word,
                      profile+["حكم_الاعتبار n "+code]))
    verdicts = tuple(dict.fromkeys(code for code, _ in labels.values()))
    for code in verdicts:
        for other in verdicts:
            if code != other:
                RULES.append(("تنافي_الرتبتين_"+method, "!حكم_الاعتبار n "+other,
                              profile+["حكم_الاعتبار n "+code]))
RULES.append(("ترخيص_الأثر", "ترتب_مشروط n a", introduced + [
    "حكم_الاعتبار n حكم_صحيح", "سبب e a", "شرط e a", "!مانع e a"]))
for reason in ["!سبب e a", "!شرط e a", "مانع e a"]:
    RULES.append(("تعطل_الأثر_"+reason.split()[0].lstrip("!"),
                  "!ترتب_مشروط n a", introduced+[reason]))

SELECTORS = ("صيغة","موضوع","مطلوب","مجاله","استثناء")
FILTERS = {"قيد_صفة":"خاصية", "قيد_قابلية":"قابل", "قيد_مادة":"مادة_من_فئة"}
MODES = {"كم_استغراق","كم_بدل","كم_معين"}
NONE_FILTER = "صفة_بلا_قيد"
NONE_EXCEPTION = "نوع_بلا_استثناء"


def negate(atom):
    pred, left, right = atom
    return (pred.removeprefix("!") if pred.startswith("!") else "!"+pred, left, right)


def compile_scopes(atoms, add):
    """Install bounded ground implications, including their selection witnesses.

    Universal success and exhausted alternatives require an explicit count
    plus every named roster entry. Positive alternatives and counterexamples
    work on open rosters. A source with missing selectors grants no rule.
    """
    fields = defaultdict(set)
    subjects = set()
    for pred, left, right in atoms:
        if not pred.startswith("!"):
            fields[left, pred].add(right)
        if pred in SELECTORS:
            subjects.add(left)
    for (left, pred), values in fields.items():
        if pred in (*SELECTORS, *FILTERS, "عين_الخاص","حصر","اصطلاح","محل_نظر","مرجع_نظر","يضبط") and len(values)>1:
            raise ValueError("Use separate reading or standard identities for competing selectors")
        if pred == "صيغة" and not values <= MODES:
            raise ValueError("Unknown quantifier mode")
        if pred == "اصطلاح" and not values <= {"نهج_تمييز","نهج_جمع"}:
            raise ValueError("Unknown teaching convention")
    for subject in sorted(subjects):
        if not all(fields[subject,p] for p in SELECTORS):
            continue
        mode, kind, act, scope, exception = (next(iter(fields[subject,p])) for p in SELECTORS)
        filters = [(p,v) for p in FILTERS for v in fields[subject,p]]
        if len(filters)>1:
            raise ValueError("This fragment has one qualification slot per reading")
        if not filters:
            continue
        fkey, qualifier = filters[0]
        selected = fields[subject,"عين_الخاص"]
        if mode == "كم_معين" and not selected:
            continue
        if mode != "كم_معين" and selected:
            raise ValueError("A named target requires the named mode")
        roster = sorted(fields[scope,"يحصي"])
        if len(roster)>4:
            raise ValueError("The installed finite quantifier accepts at most four individuals per scope")
        header = [(p,subject,v) for p,v in zip(SELECTORS,(mode,kind,act,scope,exception),strict=True)]
        header.append((fkey,subject,qualifier))
        if selected:
            header.append(("عين_الخاص",subject,next(iter(selected))))
        configured = ("قراءة_مضبوطة",subject,scope)
        add(configured,tuple(header),"تعريف_القراءة")
        target=("وفاء_بالطلب",subject,act)
        for x in roster:
            member=("يحصي",scope,x)
            eligible=("داخل_الخطاب",subject,x)
            included=[("عضوية",x,kind)]
            if qualifier != NONE_FILTER:
                included.append((FILTERS[fkey],x,qualifier))
            if exception != NONE_EXCEPTION:
                included.append(("!عضوية",x,exception))
            if selected and x not in selected:
                add(negate(eligible),(configured,member),"خارج_التعيين")
            else:
                add(eligible,(configured,member,*included),"دخول_الفرد")
                for required in included:
                    add(negate(eligible),(configured,member,negate(required)),"خروج_الفرد_بشاهد")
            done=("أنجز",x,act)
            each=("مستوفى_للعموم",subject,x)
            choice=("شاهد_للإجزاء",subject,x)
            add(each,(negate(eligible),),"خروج_من_التكليف")
            add(each,(configured,member,done),"تحقق_المحمول_على_أي_تقدير")
            add(negate(each),(eligible,negate(done)),"فرد_ناقض")
            add(choice,(eligible,done),"شاهد_معين_للإجزاء")
            add(negate(choice),(negate(eligible),),"خارج_البدائل")
            add(negate(choice),(configured,member,negate(done)),"عدم_إنجاز_هذا_البديل")
            if mode=="كم_استغراق":
                add(negate(target),(negate(each),),"مثال_ينقض_الاستغراق")
            else:
                add(target,(choice,),"الإجزاء_بشاهد")
                if mode=="كم_معين" and x in selected:
                    add(negate(target),(negate(choice),),"عدم_إجزاء_المعين")
        for claim in fields[scope,"حصر"]:
            count = int(claim.removeprefix("عدد_"))
            if count < len(roster):
                add(("!حصر",scope,claim),tuple(("يحصي",scope,x) for x in roster[:count+1]),
                    "الجرد_يعارض_عدد_الحصر")
        seal=("حصر",scope,"عدد_"+str(len(roster)))
        if not roster:
            if not selected:
                add(target if mode=="كم_استغراق" else negate(target),
                    (configured,seal),"حكم_المجال_الفارغ_المصرح")
            continue
        # Reuse the installed universal plan. Its first clause quantifies
        # over membership and the local property for each listed individual.
        plan = project("كل عنصر هو مستوفى",roster)["clauses"][0]["body"]
        tests=[]
        for atom in plan:
            x=atom["arguments"][0]
            if atom["predicate"]=="عنصر":
                tests.append(("يحصي",scope,x))
            elif mode=="كم_استغراق":
                tests.append(("مستوفى_للعموم",subject,x))
            else:
                tests.append(("!شاهد_للإجزاء",subject,x))
        if mode!="كم_معين":
            add(target if mode=="كم_استغراق" else negate(target),
                (configured,seal,*tests),"استنفاد_المجال_المحصور")
