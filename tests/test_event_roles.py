"""Compare source roles with their distinct semantic, referential and causal obligations."""
import unittest

from tools.grammar_catalog import named_matrix


def read(source, entry, questions, evidence=()):
    rows = [f"قراءة_{i} موضع_لفظ عدد_{i}" for i in range(1, len(source.rstrip(".").split())+1)]
    rows += ["قراءة_1 قرينة_قراءة مدخل_"+entry, *evidence]
    frame = dict(time="t",known_at="u",place="p",reference="دفتر الأدوار",
                 ledger="".join(row+".\n" for row in rows),queries=[q.split() for q in questions])
    return named_matrix.analyze(source,"role-contrast",frame)


def statuses(result):
    return [a["status"] for a in result["answers"]]


class EventRolesTest(unittest.TestCase):
    def test_same_object_position_different_fig_referents(self):
        base=["قراءة_2 إحالة_اسم عين_رجل","عين_رجل عضوية نوع_رجل","قراءة_3 إحالة_اسم عين_تين"]
        for verb,entry,sense,genus,trait in (
            ("زَرَعَ","زرع_غرس_فعل","شجر_تين","نبات","صالح_للغرس"),
            ("أَكَلَ","أكل_تغذية_فعل","ثمر_تين","مادة_غذائية","قابل_للتناول")):
            with self.subTest(verb=verb):
                source=verb+" الرجلُ التينَ"
                q=["مفعول_مقروء قراءة_1 قراءة_3","صالح_مفعول قراءة_1 عين_تين",
                   "صالح_فاعل قراءة_1 عين_تين","مدلول_مرشح قراءة_3 نوع_شجر_تين",
                   "مدلول_مرشح قراءة_3 نوع_ثمر_تين"]
                rows=base+["عين_تين عضوية نوع_"+sense,"نوع_"+sense+" نوع نوع_"+genus,"عين_تين خاصية صفة_"+trait]
                self.assertEqual(statuses(read(source,entry,q,rows)),["SUPPORTED","UNKNOWN","UNKNOWN","SUPPORTED","SUPPORTED"])
                self.assertEqual(statuses(read(source,entry,q,rows+["قراءة_3 قرينة_مدلول نوع_"+sense])),
                                 ["SUPPORTED","SUPPORTED","UNKNOWN","SUPPORTED","SUPPORTED"])

    def test_unmarked_transitive_requires_order_evidence(self):
        q=["فاعل_مقروء قراءة_1 قراءة_2","مفعول_مقروء قراءة_1 قراءة_3"]
        self.assertEqual(statuses(read("زرع الرجل التين","زرع_غرس_فعل",q)),["UNKNOWN","UNKNOWN"])
        self.assertEqual(statuses(read("زرع الرجل التين","زرع_غرس_فعل",q,
                                      ["قراءة_1 قرينة_ترتيب رتبة_فاعل_ثم_مفعول"])),["SUPPORTED","SUPPORTED"])

    def test_tree_is_subject_and_fig_is_genitive(self):
        for verb,entry,tail,context in [("كبرت","كبر_كبر_فعل","",""),
                                        ("اخضرت","خضر_اخضرار_فعل"," في الصيف","زمان_مذكور"),
                                        ("نمت","نمو_نماء_فعل"," في الحقل","مكان_مذكور")]:
            source=verb+" شجرة التين"+tail
            q=["فاعل_مقروء قراءة_1 قراءة_2","موضع_حامل قراءة_1 قراءة_2","إضافة_اسمية قراءة_2 قراءة_3",
               "مفعول_مقروء قراءة_1 قراءة_3","سبب_منسوب قراءة_1 قراءة_2"]
            expected=["SUPPORTED"]*3+["UNKNOWN"]*2
            if context:
                q.extend([context+" قراءة_1 قراءة_5","سبب_منسوب قراءة_1 قراءة_5"])
                expected+=["SUPPORTED","UNKNOWN"]
            self.assertEqual(statuses(read(source,entry,q)),expected)

    def test_happiness_experiencer_and_presenter(self):
        q=["فاعل_مقروء قراءة_1 قراءة_2","موضع_صاحب_شعور قراءة_1 قراءة_2","متعلق_بالباء قراءة_1 قراءة_3",
           "سبب_منسوب قراءة_1 قراءة_3"]
        self.assertEqual(statuses(read("سعد الطفل بالهدية","سعد_سعادة_فعل",q)),["SUPPORTED"]*3+["UNKNOWN"])
        q=["فاعل_مقروء قراءة_1 قراءة_2","موضع_سبب قراءة_1 قراءة_2",
           "مفعول_مقروء قراءة_1 قراءة_3","موضع_صاحب_شعور قراءة_1 قراءة_3","فاعل حدث_تقديم عين_مقدم"]
        self.assertEqual(statuses(read("أسعدت الهديةُ الطفلَ","سعد_إسعاد_فعل",q)),["SUPPORTED"]*4+["UNKNOWN"])

        with_presenter=read("أسعدت الهديةُ الطفلَ","سعد_إسعاد_فعل",q,["حدث_تقديم فاعل عين_مقدم"])
        self.assertEqual(statuses(with_presenter),["SUPPORTED"]*5)

    def test_reported_cause_and_disease_are_not_a_volitional_agent(self):
        source="مات الرجل بمرض الطاعون"
        q=["فاعل_مقروء قراءة_1 قراءة_2","موضع_حامل قراءة_1 قراءة_2","إضافة_اسمية قراءة_3 قراءة_4",
           "سبب_منسوب قراءة_1 قراءة_3","موضع_فاعل قراءة_1 قراءة_2","سبب حدث_وفاة عمل_موت"]
        self.assertEqual(statuses(read(source,"موت_موت_فعل",q,["قراءة_1 قرينة_الباء وجه_سببية"])),
                         ["SUPPORTED"]*4+["UNKNOWN"]*2)
        self.assertEqual(statuses(read(source,"موت_موت_فعل",q)),["SUPPORTED"]*3+["UNKNOWN"]*3)
        self.assertEqual(statuses(read("مات الرجل","موت_موت_فعل",q[:2])),["SUPPORTED","SUPPORTED"])

    def test_shared_pattern_has_different_requirements(self):
        for word,entry,pred,genus in [("الزراعة","زرع_غرس_مصدر_ثان","مفعول","نبات"),
                ("الولادة","ولد_ولادة_مصدر","وليد","كائن_حي"),("التجارة","تجر_تجارة_مصدر","متداول","مال"),
                ("الكتابة","كتب_كتابة_مصدر","مفعول","محتوى")]:
            q=["وزن_مرشح قراءة_1 وزن_فِعَالَة","جنس_شرط_"+pred+" قراءة_1 نوع_"+genus]
            self.assertEqual(statuses(read(word,entry,q)),["SUPPORTED","SUPPORTED"])

    def test_bad_case_and_embedded_clause_do_not_license_attachment(self):
        for s in ("نمت شجرة التين في الحقلُ","هل نمت شجرة التين في الحقل","نمت شجرة التين، في الحقل"):
            q=["مكان_مذكور قراءة_1 قراءة_5"]
            self.assertEqual(statuses(read(s,"نمو_نماء_فعل",q)),["UNKNOWN"])
