import unittest

from tools.grammar_catalog.named_matrix import analyze, read_ledger


def check(lines, *queries):
    request = {
        "ledger": "\n".join(s + "." for s in lines),
        "queries": [q.split() for q in queries],
        "time": "زمن أول", "known_at": "وقت النقل", "place": "المشهد", "reference": "الدفتر",
    }
    return analyze("شاهد تعليمي", "test", request)


class NamedMatrixTest(unittest.TestCase):
    def test_name_material_and_membership(self):
        result = check(["عين_س عضوية نوع_خاتم", "عين_س مادة نوع_ذهب", "نوع_ذهب نوع نوع_فلز"],
                       "عضوية عين_س نوع_ذهب", "مادة_من_فئة عين_س نوع_فلز")
        self.assertEqual([a["status"] for a in result["answers"]], ["UNKNOWN", "SUPPORTED"])
        self.assertEqual(result["answers"][1]["positive"]["observation_ids"], [2, 3])

    def test_independent_name_and_kinship(self):
        facts = ["عين_س عضوية نوع_أسد", "عين_س جنس_حيوي جنس_أنثى"]
        qs = ["يسمى عين_س لفظ_لبوة", "أم عين_س عين_ش"]
        self.assertEqual([r["status"] for r in check(facts, *qs)["answers"]], ["SUPPORTED","UNKNOWN"])
        with_parent = check(facts + ["عين_س والد عين_ش"], *qs)
        self.assertEqual([r["status"] for r in with_parent["answers"]], ["SUPPORTED","SUPPORTED"])
        self.assertFalse(with_parent["world_truth_established"])

    def test_conflict_and_independent_support(self):
        obs = ["عين_س عضوية نوع_أسد", "عين_س جنس_حيوي جنس_أنثى", "ليس عين_س جنس_حيوي جنس_أنثى"]
        qs = ["جنس_حيوي عين_س جنس_أنثى", "يسمى عين_س لفظ_لبوة", "عضوية عين_س نوع_أسد"]
        self.assertEqual([r["status"] for r in check(obs,*qs)["answers"]], ["CONFLICT","DEFER","SUPPORTED"])
        self.assertEqual(check(obs + ["لفظ_لبوة علم عين_س"], qs[1])["answers"][0]["status"], "SUPPORTED")

    def test_kinds_and_genealogies_are_distinct(self):
        obs = ["نوع_أسد نوع نوع_سنوري", "نوع_نمر نوع نوع_سنوري",
               "عين_أ والد عين_ب", "عين_أ والد عين_ج"]
        res = check(obs, "يشترك_بأصل نوع_أسد نوع_نمر", "سلف_مشترك عين_ب عين_ج",
                    "أخ عين_ب عين_ج","أخ عين_ب عين_ب")
        self.assertEqual([a["status"] for a in res["answers"]], ["SUPPORTED","SUPPORTED","UNKNOWN","UNKNOWN"])
        with self.assertRaises(ValueError):
            check(["نوع_أ نوع نوع_ب","نوع_ب نوع نوع_أ"],"عضوية عين_ج نوع_ب")

    def test_frame_measurements(self):
        obs=["عين_بيت عضوية نوع_بيت","نوع_بيت حد_القرب_متر عدد_50"]
        q="خاصية عين_بيت صفة_قريب"
        for value,expected in [("50","SUPPORTED"),("51","REFUTED")]:
            self.assertEqual(check(obs+["عين_بيت مسافة_متر عدد_"+value],q)["answers"][0]["status"],expected)
        self.assertEqual(check(obs,q)["answers"][0]["status"],"UNKNOWN")

    def test_events_need_independent_evidence(self):
        obs=["عين_أ عضوية نوع_حديد","نوع_حديد قابلية_النوع عمل_صهر",
             "حدث_م نمط عمل_صهر","حدث_م محل عين_أ","حدث_م شرط عمل_صهر",
             "حدث_م وسيلة عين_ح","عين_ح عضوية نوع_حرارة","نوع_حرارة تلائم عمل_صهر"]
        qs=["قابل عين_أ عمل_صهر","ممكن_بشروطه حدث_م عمل_صهر","أثر_مروي حدث_م عمل_صهر"]
        self.assertEqual([r["status"] for r in check(obs,*qs)["answers"]],["SUPPORTED","UNKNOWN","UNKNOWN"])
        self.assertEqual([r["status"] for r in check(obs+["ليس حدث_م مانع عمل_صهر"],*qs)["answers"]],
                         ["SUPPORTED","SUPPORTED","UNKNOWN"])
        self.assertEqual(check(obs+["حدث_آخر وقع عمل_صهر"],qs[2])["answers"][0]["status"],"UNKNOWN")

    def test_ill_typed_sources(self):
        for row in ("عين_ق مادة عين_ذهب.", "عين_ق طول_سم عدد_01.", "عين_ق يسمى لفظ_أسد."):
            with self.subTest(row=row), self.assertRaises(ValueError):
                read_ledger(row)
