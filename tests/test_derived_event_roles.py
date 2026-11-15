from itertools import product
import json
from unittest import TestCase, skipUnless

from tests.test_io_gateway import NATIVE
from tools.grammar_catalog import derived_event_roles as d, gateway


def candidate(text):
    (result,) = d.analyze(text)["candidates"]
    return result


class DerivedRoles(TestCase):
    def test_teaching_examples(self):
        groups = {
            "LICENSED": (
                "أَجْلَسَ الرَّجُلُ الوَلَدَ عَلَى الكُرْسِيِّ", "أَخْرَجَ الرَّجُلُ الوَلَدَ مِنَ البَيْتِ",
                "اِسْتَخْرَجَ الرَّجُلُ النِّفْطَ مِنَ الأَرْضِ", "اِنْقَطَعَ الحَبْلُ",
                "قَطَعَ الوَلَدُ الحَبْلَ فَانْقَطَعَ", "اِنْكَسَرَ الزُّجَاجُ",
                "اِنْتَقَلَ الكُرْسِيُّ إِلَى البَيْتِ", "قَطَّعَ الوَلَدُ التُّفَّاحَ",
                "أَنْبَتَ المَطَرُ العُشْبَ", "أَنْبَتَ الرَّجُلُ العُشْبَ",
                "اِخْضَرَّ الشَّجَرُ", "أَلْبَسَ الرَّجُلُ الوَلَدَ الثَّوْبَ", "كَسَّرَ الوَلَدُ الزُّجَاجَ"),
            "BLOCKED": (
                "أَجْلَسَ الرَّجُلُ الكُرْسِيَّ", "اِسْتَخْرَجَ المَطَرُ النِّفْطَ",
                "اِنْكَسَرَ المَاءُ", "اِنْكَسَرَ الزُّجَاجُ لِيَنْفَعَ", "اِنْعَلَمَ",
                "قَطَّعَ الوَلَدُ المَاءَ", "اِقْطَعَّ"),
            "UNRESOLVED": ("أَنْبَتَ الكُسُوفُ العُشْبَ",),
            "DEFERRED_SENSE": ("أَقْطَعَ الرَّجُلُ الوَلَدَ التُّفَّاحَ",)}
        for status, texts in groups.items():
            for t in texts:
                with self.subTest(t=t):
                    c = candidate(t)
                    self.assertEqual(c["status"], status)
                    self.assertEqual([s["stage"] for s in c["decision_chain"]],
                        ["base", "weight", "lexical_sense", "forms", "role_transfer", "kind_properties", "decision"])
        reversed_order = candidate("أَلْبَسَ الرَّجُلُ الثَّوْبَ الوَلَدَ")
        by_order = {tuple(r["order"]): r for r in reversed_order["readings"]}
        self.assertEqual(by_order[0, 1, 2]["status"], "BLOCKED")
        self.assertEqual(by_order[0, 2, 1]["status"], "LICENSED")
        self.assertIn("تقديم", by_order[0, 2, 1]["order_witness"]["quote"])

    def test_sense_gate_and_witness_withdrawal(self):
        r = candidate("أقطع الرجلُ الولدَ التفاحَ")
        self.assertEqual(r["weight"]["other_witness"]["gloss"], "إقطاع الأرض")
        self.assertEqual(r["readings"][0]["hypothetical_slot_status"], "LICENSED")
        self.assertTrue(all(row["status"] == "DEFERRED_SENSE" for row in r["readings"]))
        books = d.sources()
        books["mukhtar_sihah"] = ("incorrect digest", ())
        lesson = d.Lesson(d.DATA.read_bytes(), d.lesson().previous, books)
        cell = lesson.cell("جلس","IV")
        self.assertTrue(cell["missing_target_source"])
        self.assertIsNone(cell["target_witness"])
        t = "أجلس الرجلُ الولدَ"
        verb, *tail = d.exact_terms(t)
        self.assertEqual(d.analyze_form(lesson, t, verb, "جلس", "IV", tail)["status"], "DEFERRED_SENSE")

    def test_effect_witness_and_purpose(self):
        alone = candidate("انقطع الحبلُ")["readings"][0]
        self.assertEqual(alone["cause"], "OPEN")
        t = "كَسَرَ الرجلُ الزجاجَ فَانْكَسَرَ"
        row = candidate(t)["readings"][0]
        self.assertEqual(row["cause"], "PRIOR_EVENT_IN_RESULT_READING")
        self.assertEqual(row["antecedent"]["patient"]["mention"], row["bindings"]["bearer"]["mention"])
        start, end = row["link"]["cue"]["utf8_span"]
        self.assertEqual(t.encode()[start:end].decode(), "فَ")
        self.assertFalse(row["link"]["empirically_verified"])
        fronted = candidate("قطع الحبلَ الولدُ فانقطع")["readings"][0]
        self.assertEqual(fronted["antecedent"]["patient"]["mention"]["surface"], "الحبلَ")
        self.assertEqual(fronted["cause"], "PRIOR_EVENT_IN_RESULT_READING")
        self.assertEqual(candidate("قطع الولدُ الحبلَ فانقطع الحبلُ")["readings"][0]["cause"], "OPEN")
        self.assertIsNone(d.analyze("شرب الرجل الماء فانكسر"))
        self.assertIsNone(d.analyze("لم ينكسر الزجاج"))
        self.assertIsNone(d.analyze("انكسر الزجاج؟"))
        self.assertIsNone(d.analyze("أُجْلِسَ الرجلُ الولدَ"))
        self.assertIsNone(d.analyze("أجلس الرجل الولد، قال"))
        self.assertIsNone(candidate("أجلس الرجلُ الولدَ")["readings"][0]["purpose"])
        self.assertFalse(candidate("أجلس الرجلُ الولدَ لينفع")["readings"][0]["purpose"]["realized"])
        self.assertIn("لام العاقبة", candidate("انكسر الزجاج لينفع")["readings"][0]["purpose"]["other_readings_open"])

    def test_forms_and_roles(self):
        r = candidate("أجلس الرجلُ الولدَ على المقعد")
        self.assertEqual((r["generated"]["past"], r["generated"]["masdar"], r["generated"]["active"],
                          r["generated"]["passive"]), ("أَجْلَسَ","إِجْلَاس","مُجْلِس","مُجْلَس"))
        self.assertEqual(r["frame"]["transfer"], {"agent":"patient"})
        self.assertEqual(r["readings"][0]["bindings"]["causer"]["witnesses"], [{"kind":"حيوان","value":True}])
        self.assertEqual(candidate("قَطَّعَ الولدُ التفاحَ")["generated"]["active"], "مُقَطِّع")
        self.assertEqual(candidate("اخضرّ الشجر")["generated"]["masdar"], "اِخْضِرَار")
        self.assertEqual(candidate("انتقل الكرسي")["readings"][0]["bindings"]["bearer"]["grammar"], "فاعل")
        self.assertEqual(candidate("أجلس الرجلُ الولدُ")["reason"], "EXPLICIT_CASE_MARKS_EXCLUDE_THESE_ROLES")

    def test_54_cells_and_counted_genus_domain(self):
        r = d.analyze(d.CATALOG_QUERY)
        symbols = {"ATTESTED":"+","OTHER_SENSE":"!","BLOCKED_TRANSFORMATION":"-",
                   "REDIRECT":">","NO_TARGET_WITNESS":"?"}
        expected = {"قطع":"+!+?-!", "خضر":"-?--+-", "جلس":"-+---?", "نبت":"-+----",
                    "خرج":"-+---+", "كسر":"+?+?-?", "علم":"-+---!", "نقل":"-?>+-?", "لبس":"-+>!-?"}
        for root, targets in expected.items():
            cells = [c for c in r["matrix"] if c["root"] == root]
            self.assertEqual([c["form"] for c in cells], ["II","IV","VII","VIII","IX","X"])
            self.assertEqual("".join(symbols[c["status"]] for c in cells), targets)
        self.assertEqual(len(r["role_counts"]),12)
        self.assertEqual(len(set(r["domain"])), r["denominator"])
        for slots in r["role_counts"].values():
            for row in slots.values():
                named = [k for group in row["by_status"].values() for k in group]
                self.assertCountEqual(named, r["domain"])
                self.assertEqual(row["accepted"], len(row["by_status"]["LICENSED"]))
        self.assertEqual(set(r["role_counts"]["جلس.IV"]["seat"]["by_status"]["LICENSED"]), {"مقعد","كرسي"})
        self.assertIn("كسوف",r["role_counts"]["نبت.IV"]["causer"]["by_status"]["UNRESOLVED"])

    def test_supervision_changes_rule_and_conflict_stays_open(self):
        data = json.loads(d.DATA.read_bytes())
        for example in data["gate_lessons"]["intensify"]["examples"]:
            example[-1] = example[2]
        data["properties"]["رجل"] = {"ذو إرادة":False}
        lex = d.Lesson(json.dumps(data).encode(), d.lesson().previous, d.sources())
        self.assertFalse(lex.cell("كسر","II")["weight_allows"])
        self.assertTrue(lex.cell("نقل","II")["weight_allows"])
        self.assertEqual(d.selection(lex,{"kind":"رجل","surface":"الرجل"},"ذو إرادة")["status"],"CONFLICT")

    def test_transfer_unseen_combinations(self):
        for actor, sitter, seat in product(("الرجلُ","الولدُ","الطِّفلُ"),("الولدَ","الرجلَ","الطِّفلَ"),("الكرسي","المقعد")):
            row, = candidate(f"أجلس {actor} {sitter} على {seat}")["readings"]
            self.assertEqual(row["status"],"LICENSED")
            self.assertEqual(row["bindings"]["patient"]["mention"]["surface"],sitter)
            self.assertEqual(row["adjuncts"][0]["choices"][0]["role"],"seat")
        for new_role in ("الحبلَ","القميصَ","الثوبَ"):
            self.assertEqual(candidate(f"أجلس الولدُ {new_role}")["status"],"BLOCKED")
        self.assertEqual(candidate("أجلس الولدُ الغريمَ")["status"],"UNRESOLVED")

    @skipUnless(NATIVE, "requires native gateway owners")
    def test_public_routes_replay_and_reject_changed_source(self):
        for route, text in (("text.read","أَجْلَسَ الرَّجُلُ الوَلَدَ"),
                            ("relations.analyze",d.CATALOG_QUERY)):
            req = {"schema":gateway.REQUEST_SCHEMA,"route":route,"payload":{"text":text}}
            rec = gateway.run(req)
            self.assertTrue(gateway.accept_output(rec,expected_request=req)["valid"])
            report = rec["execution"]["owner_result"]["derived_event_roles"]
            if route == "text.read":
                self.assertEqual(report["candidates"][0]["status"],"LICENSED")
            else:
                self.assertEqual(len(report["matrix"]),54)
            req["payload"]["text"] += "."
            self.assertFalse(gateway.accept_output(rec,expected_request=req)["valid"])
