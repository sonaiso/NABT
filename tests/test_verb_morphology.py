from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import json

from tools.grammar_catalog import gateway
from tools.grammar_catalog.ntp import request
from tools.grammar_catalog.operations import exact_terms
from tools.lexical_training import pattern_learning as net, verb_reading as verbs, verb_sources as sources


def word(surface):
    return verbs.read(exact_terms(surface)[0], None) or {"alternatives": []}


class VerbTransportTests(TestCase):
    def test_boundaries_roots_and_lexical_evidence_in_free_text(self):
        text = "نعم، فَقَرَأْتُمُوهَا ثُمَّ وَسَمِعْتِهَا"
        observed = net.read(text)["licensed_verbs"]
        by_word = {x["surface"]:x for x in observed["occurrences"]}
        reading, = by_word["فَقَرَأْتُمُوهَا"]["alternatives"]
        self.assertEqual((reading["root"],reading["root_display"],reading["form"],reading["person"]),
                         ("قرء","قرأ","I-a","2MP"))
        self.assertGreater(reading["contrast_score"],0)
        self.assertEqual([(p["role"],p["surface"]) for p in reading["segments"]],
                         [("prefix","فَ"),("stem","قَرَأْ"),("subject","تُ"),("plural_mark","مُ"),
                          ("link","و"),("object","هَا")])
        for term in by_word.values():
            for row in term["alternatives"]:
                cursor = term["utf8_span"][0]
                for p in row["segments"]:
                    start, end = p["utf8_span"]
                    self.assertEqual(start,cursor)
                    self.assertEqual(text.encode()[start:end].decode(),p["surface"])
                    cursor = end
                self.assertEqual(cursor,term["utf8_span"][1])
        ref, = by_word["فَقَرَأْتُمُوهَا"]["masdars"]["قرء/I"]["lexical_witnesses"]
        self.assertEqual((sources.ROOT/ref["source"]).read_bytes()[slice(*ref["utf8_span"])].decode(),"قرأ الكتاب قراءة")
        self.assertIn("سمع", {r["root"] for r in by_word["وَسَمِعْتِهَا"]["alternatives"]})

    def test_transfer_subject_objects_and_mutations(self):
        for surface, root, person, obj in (
            ("فَكَتَبْتُمُوهَا","كتب","2MP","هَا"), ("زُرْتُمُونَا","زور","2MP","نَا"),
            ("كَتَبْنَاهَا","كتب","1P","هَا"), ("أَهْدَيْنَاكُمُ","هدي","1P","كُمُ"),
            ("فَكَتَبَهَا","كتب","3MS","هَا"), ("كَتَبُوهَا","كتب","3MP","هَا")):
            rows = word(surface)["alternatives"]
            self.assertTrue(any(r["root"] == root and r.get("person") == person and
                            r["segments"][-1]["surface"] == obj for r in rows), surface)
        self.assertEqual(word("فَكِتَبْتُمُوهَا")["alternatives"], [])
        self.assertEqual(word("لَمْ")["status"],"EXACT_FUNCTION_MARKER")
        self.assertFalse(word("فقرأتموها")["alternatives"])

    def test_aspect_voice_mood_and_masdar_sources(self):
        for surface, root, field, value in (
            ("كَتَبَ","كتب","key","past.I.َ"), ("سَمِعَ","سمع","key","past.I.ِ"),
            ("كَرُمَ","كرم","key","past.I.ُ"), ("كُتِبَ","كتب","voice","passive"),
            ("يَكْتُبُ","كتب","mood","مرفوع"), ("يَكْتُبَ","كتب","mood","منصوب"),
            ("يَكْتُبْ","كتب","mood","مجزوم"), ("قُمْ","قوم","aspect","imperative"),
            ("دَحْرَجَ","دحرج","family","quad"), ("رَمَى","رمي","root_class","ناقص")):
            self.assertTrue(any(r["root"] == root and r.get(field) == value for r in word(surface)["alternatives"]),surface)
        self.assertGreater(len({r["root"] for r in word("قَالَ")["alternatives"]}),1)
        self.assertEqual(word("أَقَامَ")["masdars"]["قوم/IV"]["lexical_witnesses"][0]["masdar"],"إقامة")
        self.assertIn("تَعْلِيم",[r["surface"] for r in word("عَلَّمَ")["masdars"]["علم/II"]["regular_candidates"]])
        self.assertEqual(sources.masdar("بجظ","I")["status"],"DEFER_LEXICAL_WITNESS")
        self.assertTrue(sources.masdar("شبب","I")["lexical_witnesses"])

    def test_neural_withdrawal_preserves_the_conditional_decision(self):
        text = "فَقَرَأْتُمُوهَا"
        with patch.object(verbs,"readouts",side_effect=OSError("withdrawn")):
            result = net.read(text)["licensed_verbs"]
        self.assertIsNone(result["contrast_weights_sha256"])
        r, = result["occurrences"][0]["alternatives"]
        self.assertEqual(r["root_display"],"قرأ")
        self.assertIsNone(r["contrast_score"])
        with patch.object(verbs,"tables",side_effect=ValueError("different rules")):
            self.assertEqual(net.read(text)["licensed_verbs"]["status"],"SOURCE_UNAVAILABLE")

    def test_empirical_masdar_and_context_of_irregular_imperative(self):
        nouns = word("زَكَّى")["masdars"]["زكو/II"]["lexical_witnesses"]
        self.assertIn("تَزْكِيَةٌ",[w["masdar"] for w in nouns])
        by_root, _, _ = sources.studies()
        self.assertTrue(any(row["table"] == "lazim" for row in by_root["جلس"]))
        for surface,context in (("مُرْ","ابتداء"),("فَمُرْ","وصل")):
            rows = [r for r in word(surface)["alternatives"] if r["root"] == "ءمر"]
            self.assertTrue(rows)
            wh = rows[0]["attested_hamza_contexts"]
            self.assertEqual({w["context"] for w in wh},{context})
            self.assertEqual({w["corpus"] for w in wh},{"Hadith"})
            self.assertTrue(all(w["dropped_hamza"] for w in wh))

    def test_five_verbs_use_native_inflection_and_preserve_quranic_spelling(self):
        for text,root,end,expected in (("يَعۡدِلُونَ","عدل","نون",{"مرفوع"}),
                                      ("تَكْتُبَانِ","كتب","نون",{"مرفوع"}),
                                      ("تَكْتُبِينَ","كتب","نون",{"مرفوع"}),
                                      ("يَكْتُبُوا","كتب","حذف",{"منصوب","مجزوم"})):
            rows = [r for r in word(text)["alternatives"] if r.get("ending_sign") and r["root"] == root]
            self.assertEqual({r["mood"] for r in rows},expected)
            for r in rows:
                self.assertEqual("".join(p["surface"] for p in r["segments"]),text)
                self.assertEqual(r["ending_sign"]["sign_name"],"nun_retained" if end=="نون" else "nun_deleted")

    def test_replayed_weights_cover_each_root_class(self):
        raw = json.loads(sources.checked(verbs.HEADS,verbs.HEAD_SHA))
        self.assertEqual(len(raw["heads"]),31)
        bank = raw["cell_readouts"]
        self.assertEqual(len(bank["heads"]),61)
        for name, (train, test) in bank["root_splits"].items():
            self.assertFalse(set(train) & set(test))
            self.assertGreater(bank["evaluation_by_root_class"][name]["positive"],0)
        self.assertTrue(all(len(h["weights"]) == 48 for h in bank["heads"].values()))

    def test_public_ntp_replay_target(self):
        query = request("think", {"text":"ما جذر فَقَرَأْتُمُوهَا؟"})
        receipt = gateway.run(query)
        self.assertEqual(receipt["status"],"EXECUTED",receipt["execution"].get("code"))
        result = receipt["execution"]["owner_result"]["owner_result"]
        card = next(c for c in result["cards"] if c["scope"] == "licensed_root")
        self.assertIn("قرأ",card["understood"])
        self.assertIn("واو الصلة",card["understood"])
        self.assertTrue(gateway.accept_output(receipt,expected_request=query)["valid"])
        forged = deepcopy(receipt)
        row = forged["execution"]["owner_result"]["owner_result"]["learned_patterns"]["licensed_verbs"]["occurrences"][0]
        row["alternatives"][0]["segments"][2]["utf8_span"][1] += 2
        self.assertFalse(gateway.accept_output(forged,expected_request=query)["valid"])
