import json
from unittest import TestCase

from tools.grammar_catalog import gateway
from tools.grammar_catalog.relational import RELATIONS
from tools.lexical_training import corpus_concepts as cc, teaching
from tools.lexical_training import train_corpus_concepts as trainer


def lesson(text, index):
    return {"schema": cc.SCHEMA, "text": text, "target_index": index}


class CorpusConceptsTests(TestCase):
    def test_rules_are_fitted_and_need_validation(self):
        def sample(case, gold):
            return trainer.Sample({"case": case}, gold, (1, 1, 1), 1, 2, "", None, None)
        a = sample("GEN", "prep")
        b = sample("NOM", "subject")
        train = [a] * 25 + [b] * 25
        dev = [a] * 6 + [b] * 6
        tree = trainer.fit(train, dev, ["case"])
        self.assertEqual(trainer.prediction(tree, a.x), "prep")
        self.assertEqual(trainer.prediction(tree, b.x), "subject")
        self.assertIsNone(trainer.prediction(tree, {}))
        self.assertIsNone(trainer.prediction(trainer.fit(train, [], ["case"]), a.x))
        corrected = sample("GEN", "idafa")
        tree = trainer.fit([corrected] * 25 + [b] * 25, [corrected] * 6 + [b] * 6, ["case"])
        self.assertEqual(trainer.prediction(tree, a.x), "idafa")

    def test_pattern_calibration_requires_distinct_spellings(self):
        from collections import Counter
        words = ["رَفَعَ", "رَكَعَ", "ضَرَبَ", "نَصَرَ", "دَخَلَ", "خَرَجَ"]
        shape = ("V", "NA", "ACT", "PERF", "0", "0", "0")
        training = {w: {shape} for w in words}
        lex = {cc.key(w): Counter({shape: 7}) for w in words}
        rules, _ = trainer.learn_patterns({"train": training, "dev": training}, lex)
        self.assertFalse(rules)
        dev = dict.fromkeys(["سَبَحَ", "فَتَحَ", "سَكَنَ"], {shape})
        rules, _ = trainer.learn_patterns({"train": training, "dev": dev}, lex)
        self.assertEqual(rules[cc.pattern("نَزَلَ")][0], shape)
        self.assertNotEqual(cc.pattern("نَزَلَ"), cc.pattern("نُزِلَ"))
        self.assertIsNone(cc.pattern("نزل"))

    def test_integrity_and_existing_relation_ids(self):
        model = json.loads(cc.DATA.read_bytes())
        fingerprint = model.pop("model_id")
        self.assertEqual(trainer.sha(trainer.wire(model)), fingerprint)
        relation_ids = {"relation:" + row[0] for row in RELATIONS}
        for _, relation, atlas in cc.FRAMES.values():
            self.assertIn(atlas, model["atlas"])
            if relation:
                self.assertIn(relation, relation_ids)
        def visit(node, names):
            if "children" in node:
                self.assertIn(node["feature"], names)
                for child in node["children"].values():
                    visit(child, names)
            elif node["admitted"]:
                self.assertIn(node["candidate"], cc.FRAMES)
                self.assertGreaterEqual(sum(node["train_counts"].values()), trainer.MIN_TRAIN)
                self.assertGreaterEqual(node["dev_total"], trainer.MIN_DEV)
                self.assertEqual(node["witness"]["projected"], node["candidate"])
        visit(model["tree"], cc.FEATURES)
        visit(model["written_tree"], cc.SURFACE_FEATURES)

    def test_fallback_cannot_reverse_known_voice_or_turn_particle_into_noun(self):
        self.assertFalse(cc.compatible("active", ("V", "NA", "PASS", "PERF", "0", "0", "0")))
        self.assertFalse(cc.compatible("object", ("P", "NA", "NA", "NA", "0", "0", "0")))
        self.assertIsNone(cc.written_features("كتب", None, True))

    def test_voice_withdrawal_and_role_limits(self):
        active = cc.run(lesson("كَتَبَ سَالِمٌ", 0))
        passive = cc.run(lesson("كُتِبَ كِتَابٌ", 0))
        self.assertEqual((active["frame"]["id"], passive["frame"]["id"]), ("active", "passive"))
        self.assertEqual(cc.run(lesson("كتب كِتَابٌ", 0))["decision"], "DEFER")
        prep = cc.run(lesson("إِلَى الْأَرْضِ", 1))
        self.assertEqual(prep["frame"]["id"], "prep")
        self.assertFalse(prep["other_endpoint_identified"])
        self.assertFalse(passive["world_truth_established"])
        self.assertFalse(passive["semantic_license"])
        self.assertIsNone(cc.run(lesson("الْأَرْضِ", 0))["frame"])
        for name in ("target", "context"):
            start, end = prep[name]["utf8_span"]
            self.assertEqual("إِلَى الْأَرْضِ".encode()[start:end].decode(), prep[name]["surface"])

    def test_rejects_gold_in_input_and_invalid_boundaries(self):
        for request in (dict(lesson("كَتَبَ", 0), gold="active"), lesson("كَتَبَ", True),
                        lesson("كَتَبَ", -1), lesson("كَتَبَ؛ كُتِبَ", 1)):
            self.assertEqual(teaching.run_lesson(request)["status"], "INVALID_INPUT")

    def test_public_gateway_replay_binds_the_vowels(self):
        req = {"schema": gateway.REQUEST_SCHEMA, "route": "cognitive.lesson",
               "payload": {"lesson": lesson("كَتَبَ سَالِمٌ", 0)}}
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt, expected_request=req)["valid"])
        self.assertEqual(receipt["execution"]["owner_result"]["frame"]["id"], "active")
        req["payload"]["lesson"]["text"] = "كُتِبَ كِتَابٌ"
        self.assertFalse(gateway.accept_output(receipt, expected_request=req)["valid"])
