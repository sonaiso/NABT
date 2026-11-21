from itertools import product
import json
from pathlib import Path
import unittest

from tools.grammar_catalog import masdar_frames as m, named_matrix as matrix

def run(text,rows,qs):
    p={"time":"t","known_at":"t","place":"p","reference":"مرجع","ledger":"".join(r+".\n" for r in rows),
       "queries":[q.split() for q in qs]}
    return matrix.analyze(text,"test",p)

class MasdarFramesTest(unittest.TestCase):
    def test_roundtrip_reference(self):
        self.assertEqual(len(m.BY_ENTRY),len(m.FORMS))
        for f in m.FORMS:
            self.assertIn(f.entry,[o['entry'] for o in m.candidates(f.word)])
    def test_same_spelling_does_not_imply_same_sense(self):
        self.assertEqual({x["family"] for x in m.candidates("زريعة")},{"أرض","بذور"})
        self.assertEqual({x["family"] for x in m.candidates("مزارع")},{"مهنة","معاملة","مكان"})
        self.assertEqual({x["category"] for x in m.candidates("مَزَارِعُ")},{"جمع_مكان"})
    def test_article_and_tanwin(self):
        for word in ("آكِلٌ","الآكِلُونَ","المَأْكُولَاتِ","زَرْعَةً","زَرْعًا"):
            self.assertTrue(list(m.candidates(word)),word)
        for word in ("المَأْكُولَاتَ","المَأْكُولَاتٌ","زَرْعَةًا","مَزَارِعٌ"):
            self.assertFalse(list(m.candidates(word)),word)
    def test_source_only_constructor(self):
        q=["مفعول_مقروء قراءة_ف قراءة_ب"]
        rows=["قراءة_ف موضع_لفظ عدد_1","قراءة_ف قرينة_قراءة مدخل_زرع_غرس_فعل","قراءة_ب موضع_لفظ عدد_3"]
        for text,status in [("زَرَعَ الفلاحُ الشجرةَ.","SUPPORTED"),("زَرَعَ الفلاحُ الشجرة.","UNKNOWN"),
                            ("زَرَعَ الفلاحُ الشجرةَ؟","UNKNOWN"),("هل زَرَعَ الفلاحُ الشجرةَ","UNKNOWN"),
                            ("زَرَعَ الفلاحُ، الشجرةَ","UNKNOWN"),("زَرَعَ الفلاحَ الشجرةَ","UNKNOWN")]:
            self.assertEqual(run(text,rows,q)["answers"][0]["status"],status,text)
    def test_no_lexical_identity_from_scope_alone_for_homonyms(self):
        r=run("مزارع",["قراءة_أ موضع_لفظ عدد_1","قراءة_أ مرجع_الأوجه مرجع_زراعة_وغذاء"],
              ["قراءة_معينة قراءة_أ مدخل_زرع_مهنة_اسم_مهنة"])
        self.assertEqual(r["answers"][0]["status"],"UNKNOWN")
    def test_withdraw_referring_expression_membership(self):
        p=json.loads((Path(__file__).resolve().parents[1]/'examples/relations/masdar_frames.json').read_text())["payload"]
        n=p["named_matrix"]
        n["ledger"]=n["ledger"].replace("عين_باء عضوية نوع_شجر.\n","عين_باء عضوية نوع_نبات.\n")
        a=matrix.analyze(p["text"],"test",n)["answers"]
        self.assertEqual([r["status"] for r in a[1:5]],["SUPPORTED","SUPPORTED","UNKNOWN","UNKNOWN"])
    def test_signed_slot_truth_table_independent(self):
        # The name is licensed independently. Membership and the particular trait may
        # each have neither, either or both polarities. Check both raw consequence bits.
        for membership,trait in product(range(4),repeat=2):
            rows=["قراءة_ف موضع_لفظ عدد_1","قراءة_ف مرجع_الأوجه مرجع_زراعة_وغذاء","قراءة_ن موضع_لفظ عدد_2",
                  "قراءة_ن إحالة_اسم عين_ألف","عين_ألف عضوية نوع_عشب"]
            for state,atom in [(membership,"عين_ألف عضوية نوع_نبات"),(trait,"عين_ألف خاصية صفة_قابل_للنمو")]:
                if state&1: rows.append(atom)
                if state&2: rows.append("ليس "+atom)
            res=run("نَبَتَ العشبُ",rows,["صالح_حامل قراءة_ف عين_ألف"])
            a=res["answers"][0]
            self.assertEqual(res["checker"]["status"],"VERIFIED_GROUND_PROJECTION")
            self.assertEqual((a['positive'] is not None,a['negative'] is not None),
                             (bool(membership&1 and trait&1),bool(membership&2 or trait&2)))
    def test_cannot_supply_role_conclusion(self):
        with self.assertRaises(ValueError):
            run("نبت",["قراءة_أ صالح_حامل عين_ألف"],["صالح_حامل قراءة_أ عين_ألف"])
