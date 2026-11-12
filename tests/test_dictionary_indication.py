from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from tools.grammar_catalog import dictionary_reading as law
from tools.lexical_training import dictionary_indication as model
from tools.lexical_training.train_dictionary_indication import DIR, read_tsv
from tools.evaluate_dictionary_reading import evaluate_gold


class DictionaryLearning(unittest.TestCase):
    def test_source_and_root_at_exact_offsets(self):
        raw,rows=law.resources()
        for r in rows:
            self.assertEqual(raw[slice(*r["gloss_span"])].decode(), r["gloss"])
            self.assertEqual(raw[slice(*r["heading_span"])].decode().replace(" ",""), r["root"])
        for r in json.loads((DIR/"evaluation.json").read_bytes())["span"]["cases"]:
            for proposal in r["top"]:
                self.assertEqual(raw[slice(*proposal["span"])].decode(),proposal["text"])
        self.assertEqual(model.MODEL_SHA, sha256((law.ROOT/model.PATH).read_bytes()).hexdigest())

    def test_disjoint_roots_contexts_and_conditional_limits(self):
        report=json.loads((DIR/"evaluation.json").read_bytes())
        protocol=json.loads((DIR/"protocol.json").read_bytes())
        self.assertEqual({r["root"] for r in report["span"]["cases"]},set(protocol["span_heldout_roots"]))
        self.assertFalse({r["text"] for r in read_tsv(DIR/"usage_train.tsv")} &
                         {r["text"] for r in read_tsv(DIR/"usage_test.tsv")})
        self.assertEqual(report["relation"]["by_kind"]["iltizam"]["n"],1)
        self.assertEqual(report["model_sha256"],model.MODEL_SHA)

    @unittest.skipUnless(law.PROFILE.is_file(),"Build lexicalDenotation")
    def test_independent_challenge(self):
        for gold in read_tsv(DIR/"challenge.tsv"):
            with self.subTest(text=gold["text"]):
                self.assertTrue(evaluate_gold(law.analyze(gold["text"]),gold))

    @unittest.skipUnless(law.PROFILE.is_file(),"Build lexicalDenotation")
    def test_witness_withdrawal_does_not_promote_or_erase_another_owner(self):
        text="ما دلالة «العمى» على «البصر»؟"
        good=law.analyze(text)
        self.assertEqual({r["sense_id"]:r["indications"] for r in good["readings"]},
                         {"mukhtar:blind":[],"lisan:ama":["iltizam"]})
        with patch.object(law.testimony,"assess",return_value={"native_checked":False,"status":"SOURCE_UNAVAILABLE"}):
            changed=law.analyze(text)
            self.assertEqual(changed["status"],"PARTIAL_VERIFICATION")
            self.assertEqual([r["sense_id"] for r in changed["readings"]],["mukhtar:blind"])
            self.assertEqual(changed["readings"][0],good["readings"][0])
        with patch.object(law,"resources",side_effect=ValueError("Mukhtar unavailable")):
            self.assertEqual(law.analyze("ما أصل مادة «سيف»؟")["status"],"SOURCE_BOUND_READINGS")
            mismatch=law.analyze("ما معنى «القلم» من مادة «كتب»؟")
            self.assertEqual(mismatch["readings"],[])
            self.assertEqual(mismatch["status"],"VERIFICATION_UNAVAILABLE")
        with patch.object(model,"MODEL_SHA","wrong"):
            self.assertEqual(law.analyze(text)["readings"],good["readings"])

    @unittest.skipUnless(law.PROFILE.is_file(),"Build lexicalDenotation")
    def test_marks_targets_and_out_of_inventory(self):
        for word,sid in (("مُدَحْرِج","root-profile:roller"),("مُدَحْرَج","root-profile:rolled")):
            report=law.analyze(word)
            self.assertEqual([r["sense_id"] for r in report["readings"] if r["sense_id"].startswith("root-profile:")],[sid])
        self.assertFalse(law.compatible("ٱلقلم","قَلَم"))
        self.assertFalse(law.compatible("الأسرع","أَسْرَعَ"))
        self.assertEqual(law.analyze("ما دلالة «العين» على «حاسة + »؟")["status"],"INVALID_QUERY")
        self.assertEqual(law.analyze("ما معنى «العين» في «العين قرب العين»؟")["status"],"CONTEXT_OCCURRENCE_UNRESOLVED")
        self.assertEqual(law.analyze("ما معنى «مقلمة» من مادة «بصر»؟")["readings"],[])
        new=law.analyze("ما معنى «الريحان» من مادة «روح»؟")
        self.assertEqual(new["readings"],[])
        self.assertEqual(new["status"],"UNREVIEWED_ENTRY_PROPOSAL")
        self.assertEqual(new["entry"]["proposals"]["authority"],"NONE")
        self.assertTrue(new["entry"]["proposals"]["extractive"][0]["top_spans"])
