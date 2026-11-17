from unittest import TestCase

from tools.grammar_catalog import ayat_al_dayn as verse, gateway
from tools.lexical_training import ayat_questions as q


def state(result):
    return {r["id"]:r["state"] for r in result["cognition"]["claims"]}


class CognitiveChains(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=verse.source()
        cls.full=verse.analyze(cls.text)

    def test_context_does_not_create_a_text_premise(self):
        for key,expected in [("quran_attribution",{"speaker","address"}),
                             ("human_disposition",{"survival","ownership"}),
                             ("ownership_manifestation",{"ownership"}),
                             ("human_audience",{"human","survival","ownership"})]:
            result=verse.analyze(self.text,withdraw_context=[key])
            self.assertEqual({k[4:] for k,v in state(result).items() if v=="WITHDRAWN"},expected)
            self.assertEqual(result["counts"]["active"],16)
        self.assertFalse(self.full["world_truth_established"])

    def test_spoken_word_scope_and_selective_withdrawal(self):
        for i,want,keep in [(1,"believers","if_debt"),(5,"if_then","write"),(11,"write","if_debt"),
                             (9,"term","capacity"),(54,"two","alternative"),(62,"alternative","two"),
                             (97,"exception","sale"),(109,"sale","exception")]:
            with self.subTest(i=i):
                d=state(verse.analyze(self.text,[i]))
                self.assertEqual((d["cog/"+want],d["cog/"+keep]),("WITHDRAWN","SUPPORTED_IN_SCOPE"))
        restored=verse.analyze(self.text,[])
        self.assertEqual(self.full,restored)

    def test_terminology_is_pinned_and_guarded(self):
        c=self.full["cognition"]
        self.assertEqual(c["policy"]["agreement_alias"],"فحوى الخطاب")
        self.assertEqual(c["policy"]["opposition_alias"],"لحن الخطاب")
        self.assertEqual({r["policy"] for r in c["inquiries"]},{"requirement","alert","agreement","opposition"})
        for r in c["inquiries"]:
            self.assertEqual((r["guard"],r["ruling"]),("UNKNOWN_PREMISE",None))
            self.assertTrue(r["missing_slots"])

    def test_unknown_and_inactive_scenes_do_not_invert_a_ruling(self):
        def app(scene,cut=()):
            r=verse.analyze(self.text,cut,scene=scene)
            return {x["id"]:x["state"] for x in r["scene_result"]["applications"]}
        self.assertEqual(app({})["writing_request"],"UNKNOWN_SCENE")
        self.assertEqual(app({"debt":True})["writing_request"],"UNKNOWN_SCENE")
        self.assertEqual(app({"debt":True,"specified_term":True})["writing_request"],"ACTIVE_IN_ASSUMED_SCENE")
        self.assertEqual(app({"debt":False})["writing_request"],"THIS_BRANCH_INACTIVE")
        s={"present_trade":True,"circulated_between_parties":True,"sale":True}
        self.assertEqual(app(s,[97])["trade_exception"],"TEXT_SUPPORT_WITHDRAWN")
        self.assertEqual(app(s,[97])["sale_witnesses"],"ACTIVE_IN_ASSUMED_SCENE")

    def test_readout_scores_cannot_admit_law_or_scene(self):
        from unittest.mock import patch
        baseline=verse.analyze(self.text,question="من المخاطب؟")
        with patch.object(q,"MODEL_SHA","invalid"),patch.object(q,"checked",side_effect=ValueError("bad model")):
            offline=verse.analyze(self.text,question="من المخاطب؟")
        self.assertEqual(baseline["cognition"]["claims"],offline["cognition"]["claims"])
        self.assertEqual(baseline["cognition"]["inquiries"],offline["cognition"]["inquiries"])
        self.assertEqual(offline["cognition"]["question_ranking"]["status"],"MODEL_UNAVAILABLE")
        self.assertEqual(offline["cognition"]["derived_legal_rulings"],[])

    def test_public_replay_and_input_guards(self):
        req={"schema":gateway.REQUEST_SCHEMA,"route":"ayat.read","payload":{"text":self.text,
             "question":"كم شاهدا ذكر النص وما العدد في البديل؟","withdraw_context":["human_disposition"],
             "scene":{"debt":True,"specified_term":True}}}
        r=gateway.run(req)
        self.assertTrue(gateway.accept_output(r,expected_request=req)["valid"])
        result=r["execution"]["owner_result"]
        self.assertEqual(state(result)["cog/ownership"],"WITHDRAWN")
        self.assertEqual(result["cognition"]["question_ranking"]["authority"],"NONE")
        result["cognition"]["derived_legal_rulings"]=["ملزم"]
        self.assertFalse(gateway.accept_output(r,expected_request=req)["valid"])
        for invalid in ({"scene":{"debt":1}},{"scene":{"ruling":True}},{"withdraw_context":["unknown"]},
                        {"withdraw_context":["quran_attribution"]*2},{"question":""}):
            with self.assertRaises(ValueError):
                gateway.validate_request({**req,"payload":{"text":self.text,**invalid}})
