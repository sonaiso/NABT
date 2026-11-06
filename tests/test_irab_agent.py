"""Independent examples and adversarial replay for the i'rab consumer."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog.irab import IrabIndex, analyze, answer, catalog, verify

ROOT = Path(__file__).resolve().parents[1]


class IrabAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexical = (ROOT / "examples/inflection_training.tsv").read_text()
        cls.nominal = json.loads((ROOT / "examples/awamil_agent/nominal.json").read_text())
        cls.nominal_report = analyze(cls.nominal)
        cls.jussive_request = {"text": "لَمْ يَكْتُبُوا", "lexical_text": cls.lexical}
        cls.jussive_report = analyze(cls.jussive_request)

    def read(self, text):
        return analyze({"text": text, "lexical_text": self.lexical})

    def test_four_cases_have_replayed_primary_sources_not_application_authority(self):
        c = catalog()
        cards = {r["domain"]: r for r in c["cards"]}
        for domain in ("raf", "nasb", "jarr", "jazm", "subject", "object", "cause", "effect"):
            with self.subTest(domain=domain):
                self.assertTrue(cards[domain]["sources"])
                self.assertTrue(all(s["raw_text"] and s["sha256"] for s in cards[domain]["sources"]))
                self.assertFalse(cards[domain]["application_certified"])
                self.assertFalse(cards[domain]["full_domain_coverage"])

    def test_retrieval_filters_domains_but_keeps_marks_and_byte_offsets(self):
        result = IrabIndex("jazm").search("لَمْ يَكْتُبُوا المجزومات")
        self.assertEqual([r["id"] for r in result["candidates"]], ["irab:jazm"])
        first = result["query_occurrences"][0]
        self.assertEqual(first["surface"], "لَمْ")
        self.assertEqual(first["utf8_span"], [0, len("لَمْ".encode())])

    def test_long_lived_index_rejects_changed_sources(self):
        index = IrabIndex()
        changed = catalog()
        changed["grammar_catalog_sha256"] = "stale"
        with patch("tools.grammar_catalog.irab.catalog", return_value=changed):
            with self.assertRaisesRegex(ValueError, "STALE_IRAB_CATALOG"):
                index.search("المرفوعات")

    def test_raf_is_not_subjecthood_and_alternatives_are_preserved(self):
        report = self.nominal_report
        self.assertTrue(report["views"]["raf"])
        self.assertEqual(report["views"]["subject"], [])
        self.assertEqual({r["actual_role"] for r in report["rows"] if r["licensed"]},
                         {"nominal_subject", "nominal_predicate"})
        expected = sum(len(a["assignments"]) for c in report["owner_reports"]["discourse"]["clauses"]
                       for a in c["analyses"])
        self.assertEqual(sum(r["owner"] == "discourse" for r in report["rows"]), expected)

    def test_caller_limit_does_not_prune_owner_alternatives(self):
        small = analyze({**self.nominal, "limit": 1})
        self.assertEqual(small["owner_reports"], self.nominal_report["owner_reports"])
        self.assertEqual(small["rows"], self.nominal_report["rows"])
        self.assertEqual(len(small["retrieved_explanation"]["retrieval"]["candidates"]), 1)

    def test_failed_case_candidates_are_not_licensed_views(self):
        bad = analyze({**self.nominal, "text": "زيدٌ حكيمًا."})
        self.assertTrue(bad["rows"])
        self.assertTrue(all(not r["licensed"] for r in bad["rows"]))
        self.assertFalse(any(bad["views"].values()))
        self.assertTrue(all(r["actual_role"] is None and r["inflected_case"] is None for r in bad["rows"]))

    def test_subject_and_attached_object_keep_local_case_and_source_span(self):
        text = "ضَرَبَنِي زَيْدٌ."
        report = analyze({"text": text,
            "lexical_text": (ROOT / "examples/discourse_training.tsv").read_text(),
            "context": json.loads((ROOT / "examples/discourse_context.json").read_text())})
        self.assertTrue(report["views"]["subject"])
        objects = [r for r in report["rows"] if r["actual_role"] == "direct_object"]
        self.assertTrue(objects)
        self.assertTrue(all(r["local_case"] == "nasb" and r["inflected_case"] is None for r in objects))
        for r in report["rows"]:
            self.assertEqual(text.encode()[r["span"]["start"]:r["span"]["end"]].decode(), r["surface"])
        self.assertFalse(report["causal_projection"]["allowed"])

    def test_jussive_deletes_nun_not_the_pronoun(self):
        report = self.jussive_report
        self.assertTrue(report["views"]["jazm"])
        self.assertIn("حذف النون", report["answer_ar"])
        rows = [r for r in report["rows"] if r["licensed"]]
        self.assertEqual({s["sign_name"] for r in rows for s in r["assignment"]["sign_candidates"]}, {"nun_deleted"})
        self.assertEqual(report["views"]["jarr"], [])

    def test_weak_deletion_is_not_residual_damma_or_raf(self):
        report = self.read("لَمْ يَدْعُ")
        self.assertTrue(report["views"]["jazm"])
        self.assertEqual(report["views"]["raf"], [])
        self.assertIn("حذف حرف العلة", report["answer_ar"])
        self.assertFalse(any(self.read("لَمْ يَدْعِ")["views"].values()))

    def test_two_objects_keep_their_distinct_roles_and_embedding(self):
        report = analyze({**self.nominal, "text": "ظن زيدٌ سالمًا حكيمًا."})
        objects = [r for r in report["rows"] if "object" in r["domains"]]
        self.assertEqual({r["actual_role"] for r in objects}, {"zanna_object1", "zanna_object2"})
        self.assertTrue(all(r["inflected_case"] == "nasb" for r in objects))
        self.assertIn("المفعول الأول لظن", report["answer_ar"])
        self.assertIn("المفعول الثاني لظن", report["answer_ar"])
        owner = report["owner_reports"]["discourse"]
        bindings = [b for c in owner["clauses"] for a in c["analyses"] for b in a["claim_bindings"]]
        self.assertTrue(any(b["claim_path"] == ["restriction", 0, "embedded", 0] for b in bindings))

    def test_feminine_nun_keeps_built_local_jazm(self):
        report = self.read("لَمْ يَكْتُبْنَ")
        rows = [r for r in report["rows"] if r["licensed"]]
        self.assertTrue(rows)
        self.assertTrue(all(r["local_case"] == "jazm" and r["inflected_case"] is None for r in rows))
        self.assertIn("مبني في محل جزم", report["answer_ar"])
        self.assertNotIn("حذف النون", report["answer_ar"])

    def test_clause_local_case_does_not_call_a_clause_built(self):
        report=analyze({**self.nominal,'text':'كاد زيدٌ يكتبُ.'})
        rows=[r for r in report['rows'] if r['assignment'].get('case_domain')=='clause_local_case']
        self.assertTrue(rows)
        self.assertIn('في محل نصب',report['answer_ar'])
        self.assertNotIn('مبني في محل نصب',report['answer_ar'])

    def test_cli_owner_exhaustion_returns_resource_limit_for_analyze_and_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            q=Path(directory)/'q.json';r=Path(directory)/'r.json'
            q.write_text(json.dumps({'text':'زيدٌ حكيمٌ. '*33},ensure_ascii=False))
            r.write_text(json.dumps(self.nominal_report,ensure_ascii=False))
            cmd=[sys.executable,'-m','tools.grammar_catalog','irab','analyze','--request',str(q)]
            for suffix in ([],['--verify',str(r)]):
                result=subprocess.run(cmd+suffix,cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(result.returncode,3,result.stdout+result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'],'RESOURCE_LIMIT')

    def test_jarr_and_verbal_nasb_do_not_grant_object_role(self):
        for text, domain, sign in (("مِنْ رَجُلٍ", "jarr", "الكسرة"), ("لَنْ يَكْتُبَ", "nasb", "الفتحة")):
            report = self.read(text)
            self.assertTrue(report["views"][domain])
            self.assertEqual(report["views"]["object"], [])
            self.assertIn(sign, report["answer_ar"])

    def test_bare_word_or_punctuation_does_not_acquire_attachment(self):
        for text in ("رَجُلٍ", "مِنْ؛ رَجُلٍ", "مِنْ\nرَجُلٍ"):
            report = self.read(text)
            self.assertEqual(report["views"]["jarr"], [])

    def test_causal_words_and_retrieved_rule_do_not_supply_witnesses(self):
        retrieved = answer("السببية والمسببية", domain="effect")
        self.assertEqual(retrieved["citations"], ["irab:effect"])
        self.assertFalse(retrieved["application_certified"])
        for text in ("فنجح", "لأن", "إن نجح فسيفرح"):
            report = analyze({"text": text, "query": "السببية", "domain": "cause"})
            self.assertTrue(report["retrieved_explanation"]["citations"])
            self.assertEqual(report["causal_projection"]["status"], "DEFER")
            self.assertFalse(report["causal_projection"]["allowed"])
            self.assertEqual(report["views"]["cause"], [])
            self.assertEqual(report["views"]["effect"], [])

    def test_replay_rejects_wrong_request_and_withdrawn_evidence(self):
        self.assertTrue(verify(self.jussive_report, expected_request=self.jussive_request)["valid"])
        self.assertFalse(verify(self.jussive_report, expected_request={"text": "لَمْ يَكْتُبُوا"})["valid"])
        self.assertFalse(verify(self.jussive_report, expected_request={**self.jussive_request, "text": "لَنْ يَكْتُبُوا"})["valid"])

    def test_replay_covers_display_indexes_sources_and_owner_payload(self):
        mutations = []
        changed = deepcopy(self.jussive_report); changed["answer_ar"] = "فاعل مرفوع"; mutations.append(changed)
        changed = deepcopy(self.jussive_report); changed["rows"][0]["actual_role"] = "active_subject"; mutations.append(changed)
        changed = deepcopy(self.jussive_report); changed["views"]["raf"] = changed["views"]["jazm"]; mutations.append(changed)
        changed = deepcopy(self.jussive_report); changed["causal_projection"]["allowed"] = True; mutations.append(changed)
        changed = deepcopy(self.jussive_report); changed["owner_reports"]["inflection"]["semantic_facts"] = ["invented"]; mutations.append(changed)
        for report in mutations:
            self.assertFalse(verify(report, expected_request=self.jussive_request)["valid"])

    def test_invalid_requests_cannot_inject_authority(self):
        for request in ({"text": "x", "licensed": True}, {"text": "x", "limit": True},
                        {"text": "x", "context": []}, {"text": "x", "domain": "invented"},
                        {"text": "x", "lexical_text": True}, {"text": ""}, {"text": "x", "query": []}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                analyze(request)

    def test_cli_replays_independent_json_and_returns_failure_for_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp)/"request.json"; report = Path(tmp)/"report.json"
            request.write_text(json.dumps(self.jussive_request, ensure_ascii=False))
            report.write_text(json.dumps(self.jussive_report, ensure_ascii=False))
            cmd = [sys.executable, "-m", "tools.grammar_catalog", "irab", "analyze",
                   "--request", str(request), "--verify", str(report)]
            valid = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(valid.returncode, 0, valid.stdout+valid.stderr)
            self.assertTrue(json.loads(valid.stdout)["valid"])
            altered = deepcopy(self.jussive_report); altered["answer_ar"] = "changed"
            report.write_text(json.dumps(altered, ensure_ascii=False))
            invalid = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 2, invalid.stdout+invalid.stderr)
