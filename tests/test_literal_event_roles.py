"""Independent role expectations for the controlled kind/property lesson."""
from copy import deepcopy
from itertools import product
import json
from unittest import TestCase, skipUnless

from tests.test_io_gateway import NATIVE
from tools.grammar_catalog import gateway, literal_event_roles as er


def select(text, event, order="VSO"):
    return next(r for r in er.analyze(text)["readings"] if r["event"] == event and r["order"] == order)


class LiteralEventRoles(TestCase):
    def test_all_24_substitutions_share_their_role_guards_and_keep_their_own_mentions(self):
        signatures = {}
        humans = ("الولد", "الرجل")
        fruits = ("التفاحة", "البرتقال", "الفراولة")
        for event, verb, tools in (("eat", "أكل", ("",)), ("cut", "قطع", ("بالسكين", "بالسيف", "بالمشرط"))):
            for human, fruit, tool in product(humans, fruits, tools):
                text = " ".join(filter(None, (verb, human, fruit, tool)))
                with self.subTest(text=text):
                    frame = select(text, event)
                    self.assertEqual(frame["status"], "COMPATIBLE")
                    mentions = [r["mention"]["surface"] for r in frame["roles"].values()]
                    self.assertEqual(mentions, [human, fruit] + ([tool[1:]] if tool else []))
                    signature = []
                    for role in frame["roles"].values():
                        hypothesis, = role["property_rules"]
                        signature.append((role["learning_revision"], hypothesis["condition"]))
                        start, end = role["mention"]["utf8_span"]
                        self.assertEqual(text.encode()[start:end].decode(), role["mention"]["surface"])
                    self.assertEqual(signatures.setdefault(event, signature), signature)
                    self.assertEqual(select(text, event, "VOS")["status"], "INCOMPATIBLE")

    def test_all_45_partial_property_profiles_follow_the_relevant_coordinate(self):
        inventory = json.loads(er.DATA.read_bytes())
        coordinate = {"eater": 0, "food": 0, "operator": 1, "sliceable": 1, "edge": 0}
        for name, index in coordinate.items():
            spec = inventory["lessons"][name]
            model = er.train(name, spec, inventory["version"])
            for pair in product((True, False, None), repeat=2):
                with self.subTest(name=name, pair=pair):
                    values = dict(zip(spec["features"], pair))
                    case = model.language.schema.case("held-profile", "test", values)
                    value = pair[index]
                    expected = (False, True) if value is None else (value,)
                    self.assertEqual(model.predict(case).possible, expected)

    def test_case_marks_override_word_order_and_do_not_rescue_an_incompatible_reading(self):
        r, = er.analyze("أَكَلَ التُّفَّاحَةَ الْوَلَدُ")["readings"]
        self.assertEqual((r["order"], r["status"]), ("VOS", "COMPATIBLE"))
        r, = er.analyze("أَكَلَ التُّفَّاحُ الْوَلَدَ")["readings"]
        self.assertEqual(r["roles"]["actor"]["status"], "INCOMPATIBLE")
        self.assertEqual(r["roles"]["patient"]["status"], "DEFER")
        self.assertEqual(er.analyze("أكل الولدُ التفاحُ")["status"], "CASE_MISMATCH")

    def test_instrument_and_scope_boundaries(self):
        bad = select("قطع الولد التفاحة بالملعقة", "cut")
        self.assertEqual(bad["roles"]["instrument"]["status"], "INCOMPATIBLE")
        unk = select("قطع الولد التفاحة بالجسم", "cut")
        self.assertEqual(unk["roles"]["instrument"]["status"], "DEFER")
        self.assertNotIn("instrument", select("قطع الولد التفاحة", "cut")["roles"])
        for text in ("قُطِعَ الولد التفاحة", "قطع الولد التفاحة؟", "قطع الولد، التفاحة", "أكل الولد التفاحة أمس",
                     "قطع الولد التفاحة بَالسّكين", "قطع الولد التفاحة بالسكينُ", "لم يأكل الولد التفاحة"):
            report = er.analyze(text)
            self.assertFalse(report and report["readings"], text)
        r, = er.analyze("قَطَّعَ الولدُ التفاحةَ")["readings"]
        self.assertEqual(r["masdar"], "التقطيع")
        self.assertEqual(er.analyze("قَطَعَ الولدُ التفاحةَ")["readings"][0]["masdar"], "القطع")

    def test_withdrawal_conflict_and_a_changed_teaching_label(self):
        inv = json.loads(er.DATA.read_bytes())
        spec = inv["lessons"]["edge"]
        model = er.train("edge", spec, inv["version"])
        noun = {"surface": "السكين"}
        def apply():
            return er.apply_role((noun, *er.profile("سكين", inv)), model)["status"]
        self.assertEqual(apply(), "COMPATIBLE")
        inv["properties"]["سكين"] = {"له حدّ عامل": False}
        self.assertEqual(apply(), "CONFLICT")
        del inv["properties"]["أداة ذات حدّ عامل"]["له حدّ عامل"]
        self.assertEqual(apply(), "INCOMPATIBLE")
        del inv["properties"]["سكين"]
        self.assertEqual(apply(), "DEFER")
        # Flip the teaching judgments to the distracting predicate in a separate fixture.
        altered = deepcopy(spec)
        for row in altered["examples"]:
            row[-1] = row[2]
        revised = er.train("edge", altered, inv["version"])
        self.assertEqual([g.render(revised.language.schema) for g in revised.survivors], ["له مقبض"])

    @skipUnless(NATIVE, "native gateway owners required")
    def test_both_public_routes_replay_the_source_and_reject_tampering(self):
        for route in ("text.read", "relations.analyze"):
            with self.subTest(route=route):
                req = {"schema": gateway.REQUEST_SCHEMA, "route": route,
                       "payload": {"text": "قطع الرجل الفراولة بالمشرط"}}
                receipt = gateway.run(req)
                verified = gateway.accept_output(receipt, expected_request=req)
                self.assertTrue(verified["valid"], verified)
                owner = receipt["execution"]["owner_result"]
                self.assertFalse(owner["world_truth_established"])
                result = owner["literal_event_roles"]
                self.assertFalse(result["occurrence_established"])
                self.assertTrue(any(r["status"] == "COMPATIBLE" for r in result["readings"]))
                req["payload"]["text"] = "قطع الرجل الفراولة بالملعقة"
                self.assertFalse(gateway.accept_output(receipt, expected_request=req)["valid"])
