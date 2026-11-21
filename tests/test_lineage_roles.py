import itertools
import os
import unittest
from tools.grammar_catalog import named_matrix
from tools.grammar_catalog.role_forms import candidates

def evaluate(text,rows,queries):
    p = {"ledger":"".join(row+".\n" for row in rows),"queries":[q.split() for q in queries],
         "time":"t","known_at":"t2","reference":"تعليمي","place":"المختبر"}
    return named_matrix.analyze(text,"unit",p)

class LineageRolesTest(unittest.TestCase):
    def test_all_signed_local_gate_inputs(self):
        # Independent truth table: one bit for each side of each testimony.
        # Only presence of all three required polarities supplies positive support.
        for cells in itertools.product(range(4), repeat=3):
            rows = ["فحص_أ باب_الفحص باب_دور"]
            for state,p in zip(cells,["سبب_الفحص","شرط_الفحص","مانع_الفحص"]):
                row="فحص_أ "+p+" باب_دور"
                if state&1: rows.append(row)
                if state&2: rows.append("ليس "+row)
            result=evaluate("شاهد",rows,["ترخيص_الفحص فحص_أ باب_دور"])
            a=result["answers"][0]
            c,s,b=cells
            self.assertEqual(a["positive"] is not None, bool(c&1 and s&1 and b&2),cells)
            self.assertEqual(a["negative"] is not None, bool(c&2 or s&2 or b&1),cells)
            if result["checker"]["status"] == "CHECKER_UNAVAILABLE" and not os.getenv("NABT_REQUIRE_RELATIONAL_NATIVE"):
                self.assertEqual(result["status"],"PROPOSAL_ONLY")
            else:
                self.assertEqual(result["status"],"VERIFIED_PROJECTION")

    def test_preserved_source_spans_and_incompatible_marks(self):
        r=evaluate("بيت، جُذِبَ ثم جَذْبٌ",["قراءة_أ موضع_لفظ عدد_2","قراءة_ب موضع_لفظ عدد_4"],
                   ["مرشح_قراءة قراءة_أ مدخل_جذب_مجرد_مصدر"])
        for row in r["occurrence_forms"]:
            a,b=row["utf8_span"]
            self.assertEqual("بيت، جُذِبَ ثم جَذْبٌ".encode()[a:b].decode(),row["surface"])
        self.assertEqual(r["answers"][0]["status"],"UNKNOWN")
        self.assertEqual([o["category"] for o in r["occurrence_forms"][0]["candidates"]],["ماض_مجهول"])

    def test_off_reference_and_unlicensed_selection(self):
        r=evaluate("مُسْتَخْرَج",["قراءة_أ موضع_لفظ عدد_1","قراءة_أ قرينة_قراءة مدخل_جذب_مجرد_مصدر"],
                   ["قراءة_معينة قراءة_أ مدخل_جذب_مجرد_مصدر"])
        self.assertEqual(r["occurrence_forms"][0]["candidates"],[])
        self.assertEqual(r["answers"][0]["status"],"UNKNOWN")

    def test_unlisted_root_recovered_only_as_shape(self):
        r=evaluate("تَكَاتُب",["قراءة_أ موضع_لفظ عدد_1"],["دور_تتيحه قراءة_أ دور_شريك"])
        form=r["occurrence_forms"][0]
        self.assertIn(("كتب","تَفَاعُل"),[(s["root"],s["template"]) for s in form["shape_proposals"]])
        self.assertEqual(form["candidates"],[])
        self.assertEqual(r["answers"][0]["status"],"UNKNOWN")

    def test_quality_license_is_role_specific_and_does_not_name_a_bearer(self):
        r=evaluate("مَجْذُوب",["قراءة_أ موضع_لفظ عدد_1","قراءة_أ قرينة_قراءة مدخل_جذب_مجرد_اسم_مفعول"],
                   ["قابلية_وصف قراءة_أ صفة_مجذوب","قابلية_وصف قراءة_أ صفة_جاذب","خاصية عين_الحديد صفة_مجذوب"])
        self.assertEqual([a["status"] for a in r["answers"]],["SUPPORTED","UNKNOWN","UNKNOWN"])

    def test_multiple_coord_values_rejected(self):
        with self.assertRaises(ValueError):
            evaluate("بيت بيت",["قراءة_أ موضع_لفظ عدد_1","قراءة_أ موضع_لفظ عدد_2"],
                     ["وزن_مرشح قراءة_أ وزن_فعل"])
    def test_bad_span_rejected(self):
        with self.assertRaises(ValueError):
            evaluate("بيت",["قراءة_أ موضع_لفظ عدد_0"],["وزن_مرشح قراءة_أ وزن_فعل"])

    def test_self_and_cyclic_lineage_rejected(self):
        for rows in [["نوع_أ فرع_من نوع_أ"],["نوع_أ فرع_من نوع_ب","نوع_ب فرع_من نوع_أ"]]:
            with self.assertRaises(ValueError):
                evaluate("سلالة",rows,["نسب_محقق عين_أ نوع_أ"])

    def test_nonreciprocal_same_template_and_jamid(self):
        samples = list(candidates("تَجَاهُلٌ"))+list(candidates("بَيْتٌ"))
        self.assertEqual([r["roles"] for r in samples],[["دور_حامل_تغير"],[]])
        self.assertEqual(list(candidates("تُجُاهُل")),[])
    def test_scope_id_and_no_role_as_source(self):
        with self.assertRaises(ValueError):
            evaluate("جاذب",["فحص_أ إسناد_مرخص دور_مؤثر"],["إسناد_مرخص فحص_أ دور_مؤثر"])

    def test_nominal_accusative_and_suffix_ambiguity(self):
        self.assertEqual([r['category'] for r in candidates("دَفْعًا")],["مصدر"])
        self.assertEqual({r['category'] for r in candidates("دفعه")},{"مصدر_مضاف","فعل_وضمير"})
