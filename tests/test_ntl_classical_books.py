"""Independent byte spans, contrastive roles, dictionary scope and public replay."""
import json
import unittest
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.grammar_catalog import gateway, ntp
from tools.lexical_training import ntl_classical_books as books, teaching

VERB = "نَصَرَ"
NOM = "الْمُعَلِّمُ"
ACC = "الطَّالِبَ"
PROBE = " ".join((VERB, ACC, NOM))
DEMOS = ["مَدَحَ الْحَارِسُ الْعَامِلَ", "مَدَحَ الْحَارِسَ الْعَامِلُ"]


def lesson(text=PROBE, **kwargs):
    return {"schema": books.SCHEMA, "text": text, "source_id": "اختبار", **kwargs}


def answers(result):
    return {q["id"]: q for q in result["questions"]}


class ClassicalBooks(unittest.TestCase):
    def test_role_addresses_and_three_independent_texts(self):
        result = books.run(lesson())
        rows = answers(result)
        self.assertEqual(rows["subject"]["answer"], NOM)
        self.assertEqual(rows["object"]["answer"], ACC)
        self.assertEqual(rows["subject.0"]["decision"], "REFUTED")
        self.assertEqual(rows["world"]["decision"], "UNKNOWN")
        bank = result["syntax_owner"]["witnesses"]
        for ref, filename in (("predication", "sibawayhi.txt"), ("primary", "qatr.txt")):
            w = bank[ref]
            self.assertTrue(w["path"].endswith(filename))
            start, stop = w["utf8_span"]
            self.assertEqual(sha256((books.ROOT / w["path"]).read_bytes()[start:stop]).hexdigest(), w["sha256"])
        entry = result["lexical_owner"]["entries"][0]["owner"]
        self.assertFalse(entry["reading_licensed"])
        statement, = rows["opening.0"]["answer"]
        start, stop = statement["utf8_span"]
        self.assertEqual((books.ROOT / entry["source"]["checkout_default"]).read_bytes()[start:stop].decode(),
                         statement["quote"])
        self.assertIn("إتيان خير وإيتائه", statement["quote"])

    def test_flip_and_abstain_without_case(self):
        swapped = answers(books.run(lesson("نَصَرَ الطَّالِبُ الْمُعَلِّمَ")))
        self.assertEqual(swapped["subject"]["answer"], "الطَّالِبُ")
        unbound = answers(books.run(lesson("نَصَرَ الطالب المعلم")))
        self.assertEqual(unbound["subject"]["decision"], "UNKNOWN")
        self.assertEqual(unbound["heading.0"]["answer"], "نصر")
        for text in ("لم " + PROBE, "قيل «" + PROBE + "»"):
            self.assertEqual(answers(books.run(lesson(text)))["subject"]["decision"], "UNKNOWN")

    def test_withdraw_one_book(self):
        for book in ("sibawayhi", "qatr"):
            res = books.run(lesson(withdraw=[book], examples=DEMOS))
            self.assertEqual(answers(res)["subject.0"]["decision"], "UNKNOWN")
            self.assertEqual(answers(res)["heading.0"]["decision"], "SUPPORTED")
            self.assertIsNone(res["learning"]["history"][0]["teacher"])
        res = books.run(lesson(withdraw=["maqayis"], candidate_heading="نصر"))
        self.assertEqual(answers(res)["matches_heading"]["decision"], "UNKNOWN")
        self.assertEqual(answers(res)["subject"]["decision"], "SUPPORTED")

    def test_bounded_refutation_and_quranic_mark(self):
        for written in ("يَعْدِلُونَ", "يَعۡدِلُونَ"):
            res = books.run(lesson(written, candidate_heading="عقل"))
            self.assertEqual(answers(res)["matches_heading.0"]["decision"], "REFUTED")
            self.assertEqual(answers(res)["heading.0"]["answer"], "عدل")
            self.assertIn("أصلان", answers(res)["opening.0"]["answer"][0]["quote"])
            self.assertEqual(answers(res)["sense"]["decision"], "UNKNOWN")
        self.assertEqual(answers(books.run(lesson("يعدلون", candidate_heading="عدل")))["matches_heading"]["decision"], "UNKNOWN")

    def test_training_on_demonstrations_only(self):
        before = books.run(lesson(examples=DEMOS[:1]))["learning"]
        self.assertEqual(before["survivors"], ["first_noun", "nominative_sign"])
        self.assertIsNone(before["agreed_proposal"])
        after = books.run(lesson(examples=DEMOS))["learning"]
        self.assertEqual(after["survivors"], ["nominative_sign"])
        start, stop = after["agreed_proposal"]
        self.assertEqual(PROBE.encode()[start:stop].decode(), NOM)
        other = books.run(lesson("خَبَرٌ", examples=DEMOS))["learning"]
        self.assertEqual(after["history"], other["history"])
        self.assertFalse(after["seen_exact_text"])
        self.assertTrue(books.run(lesson(DEMOS[0], examples=DEMOS))["learning"]["seen_exact_text"])

    def test_missing_or_corrupt_inflection_evidence_abstains_during_learning(self):
        with TemporaryDirectory() as directory, patch("nabt.inflection.files", return_value=Path(directory)):
            table = Path(directory) / "data/inflection_evidence_table.json"
            table.parent.mkdir()
            for corrupted in (False, True):
                if corrupted:
                    table.write_bytes(b"changed")
                result = teaching.run_lesson(lesson(examples=DEMOS))
                self.assertEqual(result["status"], "COURSE_SESSION")
                self.assertTrue(result["syntax_status"].startswith("GRAMMAR_EVIDENCE_UNAVAILABLE"))
                self.assertEqual(answers(result)["subject"]["decision"], "UNKNOWN")
                learned = result["learning"]
                self.assertEqual(learned["survivors"], list(books.POLICIES))
                self.assertIsNone(learned["probe_votes"]["nominative_sign"])
                self.assertIsNone(learned["agreed_proposal"])

    def test_degraded_dictionary_does_not_negate(self):
        with patch.object(books.SourceLexicon, "load", side_effect=FileNotFoundError):
            rows = answers(books.run(lesson(candidate_heading="نصر")))
        self.assertEqual(rows["matches_heading"]["decision"], "UNKNOWN")
        self.assertEqual(rows["subject"]["decision"], "SUPPORTED")

    def test_all_registered_forms_have_replayable_dictionary_openings(self):
        for domain, spec in books.domains().items():
            for surface, heading in spec["alignments"].items():
                with self.subTest(domain=domain, surface=surface):
                    result = books.run(lesson(surface, domain=domain))
                    rows = answers(result)
                    self.assertEqual(rows["heading.0"]["answer"], heading)
                    self.assertEqual(rows["opening.0"]["decision"], "SUPPORTED")
                    owner = result["lexical_owner"]["entries"][0]["owner"]
                    raw = (books.ROOT / owner["source"]["checkout_default"]).read_bytes()
                    for statement in rows["opening.0"]["answer"]:
                        start, stop = statement["utf8_span"]
                        self.assertEqual(raw[start:stop].decode(), statement["quote"])

    def test_new_lexical_domain_and_bits(self):
        original = lesson("حِمْلٌ", domain="haml-forms", candidate_heading="جمل")
        raw = original.pop("text").encode()
        original["bits"] = "".join(f"{byte:08b}" for byte in raw)
        result = books.run(original)
        self.assertEqual(result["source"]["utf8_hex"], raw.hex())
        rows = answers(result)
        self.assertNotIn("subject", rows)
        self.assertEqual(rows["heading.0"]["answer"], "حمل")
        self.assertEqual(rows["matches_heading.0"]["decision"], "REFUTED")
        self.assertEqual(rows["world"]["decision"], "UNKNOWN")
        self.assertEqual(result["learning"]["status"], "OUTSIDE_DOMAIN")
        self.assertEqual(answers(books.run({**original, "withdraw": ["maqayis"]}))["heading"]["decision"], "UNKNOWN")
        self.assertEqual(answers(books.run(lesson("حِمْلٌ")))["heading"]["decision"], "UNKNOWN")
        self.assertEqual(answers(books.run(lesson("هل " + PROBE + "؟")))["utterance"]["answer"], "استفهام")
        path = books.ROOT / "examples/ntl_classical_books/second_domain.json"
        request = json.loads(path.read_bytes())
        receipt = gateway.run(request)
        self.assertEqual(receipt["status"], "EXECUTED")
        outer = receipt["execution"]["owner_result"]
        self.assertEqual(outer["observation_source_encoding"], "UTF8_BITS")
        self.assertEqual(outer["observation_request_path"], "/payload/input/lesson/bits")
        self.assertEqual(answers(outer["owner_result"])["matches_heading.0"]["decision"], "REFUTED")
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])

    def test_invalid_bytes_and_untrusted_fields(self):
        original = lesson()
        del original["text"]
        for values in ({"bits": "101"}, {"bits": "11111111"}, {"bits": "0000000x"},
                       {"text": PROBE, "domain": "forged"}, {"utf8_hex": "ff"}, {"utf8_hex": "00 "}, {"utf8_hex": "AA"},
                       {"utf8_hex": "df" * 513}, {"text": PROBE, "utf8_hex": PROBE.encode().hex()},
                       {"text": PROBE, "gold": "subject"}, {"text": PROBE, "examples": 2},
                       {"text": PROBE, "withdraw": ["qatr", "qatr"]}):
            result = teaching.run_lesson({**original, **values})
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertFalse(result["execution_measured"])

    def test_normal_gateway_replay_and_input_binding(self):
        path = books.ROOT / "examples/ntl_classical_books/object_first.json"
        request = json.loads(path.read_bytes())
        receipt = gateway.run(request)
        out = receipt["execution"]["owner_result"]
        owner = out["owner_result"]
        self.assertEqual(owner["source"]["text"], PROBE)
        self.assertEqual(out["source_traces"][0]["request_path"], "/payload/input/lesson/utf8_hex")
        self.assertEqual(out["source_traces"][0]["source_encoding"], "UTF8_HEX")
        verb, *nouns = out["source_traces"][0]["observations"]
        self.assertEqual(verb["observation"]["restored"], verb["observation"]["cells"])
        self.assertTrue(all(row["observation"]["status"] == "DEFER_EXACT_A116_READING" for row in nouns))
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])
        other = deepcopy(request)
        other["payload"]["input"]["lesson"]["source_id"] = "different"
        self.assertFalse(gateway.accept_output(receipt, expected_request=other)["valid"])
        self.assertTrue(teaching.verify_lesson(owner, expected_lesson=request["payload"]["input"]["lesson"])["valid"])


if __name__ == "__main__":
    unittest.main()
