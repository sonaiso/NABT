from copy import deepcopy
from decimal import Decimal
from itertools import product
import json
from unittest import TestCase, skipUnless

from tests.test_io_gateway import NATIVE
from tools.grammar_catalog import event_scene as scene, gateway
from tools.grammar_catalog import literal_event_roles as roles
from tools.grammar_catalog.water_saturation import estimate

CUT = "الولد جلس على الحرسي وقطع التفاح الذي فوق الطاولة بالسكين في البيت ليأكل التفاح المقطع"
TEA = "الولد الذي شرب الشاي مع السكر بالكوب الاصفر وأكل مع الشاي الكعك الذي فوق الطاولة"


def relation(r, name):
    (link,) = [v for v in r["relations"] if v["relation"] == name]
    return link


def binding(event, role):
    (b,) = [b for b in event["bindings"] if b["role"] == role]
    return b


def surface(r, ref):
    return r["entities"][ref]["mention"]["surface"]


class SceneTests(TestCase):
    def test_cut_preserves_typo_scopes_and_attachment(self):
        r = scene.analyze(CUT)
        sit, cut, eat = r["events"]
        self.assertEqual([e["masdar"] for e in (sit, cut, eat)], ["الجلوس", "القطع", "الأكل"])
        seat = binding(sit, "support")
        self.assertEqual(surface(r, seat["target"]), "الحرسي")
        self.assertEqual(seat["selection"]["status"], "DEFER")
        self.assertFalse(r["open_questions"][0]["substitution_applied"])
        self.assertEqual(binding(scene.analyze(CUT.replace("الحرسي", "الكرسي"))["events"][0], "support")["selection"]["status"],
                         "COMPATIBLE")
        self.assertEqual(binding(sit, "actor")["target"], binding(eat, "actor")["target"])
        self.assertEqual(binding(cut, "patient")["target"], relation(r, "relative_position")["head"])
        self.assertEqual(binding(cut, "instrument")["target"], relation(r, "event_place")["alternative_head"])
        self.assertEqual(relation(r, "purpose")["target"], eat["id"])
        self.assertEqual(eat["scope"], "intended")
        self.assertFalse(relation(r, "purpose")["realized"])
        desc = relation(r, "described_as")
        self.assertEqual((desc["head"], desc["masdar"]), (binding(eat, "patient")["target"], "التقطيع"))
        self.assertFalse(relation(r, "candidate_coreference")["individual_identity_verified"])
        self.assertFalse(r["world_occurrence_verified"])

    def test_tea_sugar_colour_cake_and_relative_scope(self):
        r = scene.analyze(TEA)
        drink, eat = r["events"]
        self.assertEqual([e["scope"] for e in (drink, eat)], ["relative_description"] * 2)
        self.assertEqual(relation(r, "relative_clause")["target"], drink["id"])
        self.assertEqual(surface(r, relation(r, "described_as")["head"]), "الكوب")
        self.assertEqual(surface(r, relation(r, "relative_position")["head"]), "الكعك")
        soluble = relation(r, "possible_dissolution_in")
        self.assertEqual((surface(r, soluble["head"]), surface(r, soluble["target"])), ("السكر", "الشاي"))
        self.assertFalse(soluble["occurrence_inferred"])
        self.assertEqual([e["frame"] for e in r["events"]], ["drink", "eat"])
        for rel in r["relations"]:
            start, end = rel["cue"]["utf8_span"]
            self.assertEqual(TEA.encode()[start:end].decode(), rel["cue"]["surface"])
        joined = scene.analyze(TEA.replace("وأكل", "والسكر جنس له خاصية الذوبان في الشاي وأكل"))
        self.assertEqual([e["frame"] for e in joined["events"]], ["drink", "eat"])
        self.assertTrue(relation(joined, "coordinated_description"))
        self.assertFalse(relation(joined, "stated_disposition")["occurrence_inferred"])
        withdrawn = scene.analyze(TEA.replace("مع السكر ", ""))
        self.assertNotIn("possible_dissolution_in", [v["relation"] for v in withdrawn["relations"]])

    def test_lexicon_and_explicit_dissolution(self):
        r = scene.analyze("التفاح المأكول")
        entity, = r["entities"].values()
        self.assertIn("ثمرة غذائية لحمية", entity["lineage"])
        self.assertIn(("الأكل", "patient"), [(o["masdar"], o["role"]) for o in entity["possible_roles"]])
        self.assertEqual(relation(r, "described_as")["kind_support"], "SUPPORTED")
        self.assertEqual(r["events"], [])
        for t in ("السكر قابل للذوبان في الشاي", "السكر جنس له خاصية الذوبان في الماء"):
            r = scene.analyze(t)
            self.assertEqual(r["events"], [])
            self.assertFalse(relation(r, "stated_disposition")["occurrence_inferred"])
        r = scene.analyze("ذاب السكر في الشاي")
        self.assertEqual(r["events"][0]["masdar"], "الذوبان")
        self.assertEqual(binding(r["events"][0], "medium")["selection"]["status"], "COMPATIBLE")
        self.assertFalse(r["world_occurrence_verified"])

    def test_waw_time_and_two_grammatical_forms_of_purpose(self):
        r = scene.analyze("سار الولد والنهرَ صباحًا")
        self.assertIn("مفعول معه", relation(r, "accompaniment")["syntax"])
        self.assertIn("مفعول فيه", relation(r, "event_time")["syntax"])
        self.assertTrue(relation(scene.analyze("سار الولد والنهر"), "waw_ambiguous"))
        self.assertTrue(relation(scene.analyze("سار الولد والرجلُ"), "coordinated_subject"))
        r = scene.analyze("شرب الولد الماء رغبةً في الارتواء")
        self.assertIn("مفعول لأجله", relation(r, "purpose")["syntax"])
        self.assertEqual(relation(r, "purpose")["understood_subject"], binding(r["events"][0], "actor")["target"])
        r = scene.analyze("أكل الولد الكعك ليشرب الرجل الماء")
        self.assertEqual(surface(r, binding(r["events"][1], "actor")["target"]), "الرجل")

    def test_natural_change_cues_mean_different_things(self):
        r = scene.analyze("اخضرّ الشجر في الربيع")
        green, = r["events"]
        self.assertEqual((green["family"], binding(green, "bearer")["syntax"]), ("change_of_colour", "فاعل ظاهر"))
        self.assertEqual(surface(r, relation(r, "event_time")["target"]), "الربيع")
        self.assertIn("ADJECTIVE_OR_VERB_READING", [p["reason"] for p in scene.analyze("أخضر الشجر في الربيع")["open_questions"]])
        r = scene.analyze("نبت العشب بعد المطر")
        self.assertFalse(relation(r, "after")["cause_inferred"])
        (candidate,) = r["events"][0]["mechanism_candidates"]
        self.assertEqual(candidate["status"], "HYPOTHESIS_ONLY")
        self.assertFalse(candidate["empirically_verified"])
        self.assertEqual(scene.analyze("نبت العشب بعد الجرس")["events"][0]["mechanism_candidates"], [])
        self.assertEqual(len(scene.analyze("نبت الزرع بعد الري")["events"][0]["mechanism_candidates"]), 1)
        self.assertEqual(scene.analyze("نبت العشب")["events"][0]["mechanism_candidates"], [])
        self.assertFalse(any(v["relation"] == "reported_cause" for v in r["relations"]))
        causal = relation(scene.analyze("نبت الزرع بسبب المطر"), "reported_cause")
        self.assertFalse(causal["empirically_verified"])
        self.assertIsNone(scene.analyze("لم ينبت العشب بعد المطر"))
        self.assertIsNone(scene.analyze("نبت العشب بعد المطر؟"))
        self.assertIsNone(scene.analyze("شُرِبَ الولدُ الشايَ"))
        self.assertIsNone(scene.analyze("شرب الولدُ الشايُ بالكوب"))
        self.assertIsNone(scene.analyze("شرب الولد الشاي الذي فوق الطاولة كلام مجهول"))
        self.assertIsNone(scene.analyze("أكل الولد التفاحة"))

    def test_boiling_placeholder_and_quantitative_cross_check(self):
        r = scene.analyze("غلى الماء عند درجة حرارة كذا")
        self.assertIsNone(relation(r, "temperature")["target"])
        self.assertEqual(r["physical_comparisons"][0]["status"], "NEED_ABSOLUTE_PRESSURE")
        for temp in ("١٠٠ درجة مئوية", "٣٧٣٫١٥ كلفن"):
            r = scene.analyze("غلى الماء عند درجة حرارة " + temp + " تحت ضغط ١٠١٤٢٠ باسكال")
            c, = r["physical_comparisons"]
            self.assertEqual((c["status"], c["reported_minus_reference_C"]), ("COMPARED_UNDER_ASSUMPTIONS", "0.000"))
            self.assertFalse(c["occurrence_verified"])
        self.assertEqual(scene.analyze("غلى الحليب تحت ضغط ١٠١٤٢٠ باسكال")["physical_comparisons"][0]["status"],
                         "MATERIAL_OUT_OF_SCOPE")
        self.assertIsNone(estimate(Decimal(170000)))
        self.assertEqual(scene.analyze("غلى الماء تحت ضغط ١٠١٤٢٠ باسكال تحت ضغط ٩٠٠٠٠ باسكال")["physical_comparisons"][0]["status"],
                         "COMPETING_OR_REPEATED_CONDITIONS")

    def test_water_model_on_16_nontraining_rows(self):
        # NISTIR 5078, Table 1. Intervening integer-degree rows excluded from fitting.
        pressures = (72890, 75684, 78568, 81541, 87771, 91030, 94390, 97852,
                     105090, 108870, 112770, 116780, 125150, 129520, 134010, 138630)
        temperatures = [t for t in range(90, 111) if t % 5]
        errors = [abs(estimate(Decimal(p)) - t) for p, t in zip(pressures, temperatures, strict=True)]
        self.assertLess(max(errors), Decimal("0.105"))
        self.assertGreater(min(errors), 0)

    def test_role_training_depends_on_teacher_and_transfers_to_new_word_combinations(self):
        spec = deepcopy(json.loads(scene.DATA.read_bytes())["lessons"]["vessel"])
        model = roles.train("vessel", spec, "test")
        self.assertEqual([g.render(model.language.schema) for g in model.survivors], ["يحوي شرابًا للاستعمال"])
        for row in spec["examples"]:
            row[-1] = row[2]
        revised = roles.train("vessel", spec, "test")
        self.assertEqual([g.render(revised.language.schema) for g in revised.survivors], ["ملوّن"])
        for who, drink, cup in product(("الولد", "الرجل"), ("الماء", "الشاي", "الحليب"), ("الكوب", "الكأس")):
            r = scene.analyze(f"شرب {who} {drink} ب{cup}")
            event, = r["events"]
            for role, expected in (("actor", who), ("patient", drink), ("vessel", cup)):
                b = binding(event, role)
                self.assertEqual((surface(r, b["target"]), b["selection"]["status"]), (expected, "COMPATIBLE"))

    @skipUnless(NATIVE, "native gateway owners required")
    def test_public_replay_for_both_paths(self):
        for route, t in (("relations.analyze", CUT), ("text.read", TEA)):
            req = {"schema": gateway.REQUEST_SCHEMA, "route": route, "payload": {"text": t}}
            receipt = gateway.run(req)
            self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
            result = receipt["execution"]["owner_result"]["event_scene"]
            self.assertEqual(result["coverage"], "COMPLETE_IN_FRAGMENT")
            req["payload"]["text"] = t.replace("الولد", "الرجل")
            self.assertFalse(gateway.accept_output(receipt, expected_request=req)["valid"])
