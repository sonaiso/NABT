"""User-facing contract, with independent expected contrasts and a real gateway replay."""
from copy import deepcopy
from io import BytesIO
from unittest import TestCase, mock, skipUnless
from urllib.parse import urlencode

from tools import aligned_acquisition
from tools.grammar_catalog import gateway, gateway_links, gateway_routes, reader_client as client, text_reading as reader

READY = all((reader.ROOT / "formal/.lake/build/bin" / p).is_file() for p in (
    "alignedAcquisition", "connectedAcquisitionV3", "lexicalDenotation", "linguisticTruth", "progressiveUnitProbe"))
LION = "أعني بالأسد الرجل الشجاع"
EXCLUSION = " لا الحيوان المفترس"


class TextBoundaries(TestCase):
    def test_text_only_and_quotation_boundaries(self):
        for field in ("context", "lexical_text", "accepted", "usage_context", "route"):
            with self.assertRaises(ValueError):
                gateway_routes.validate("text.read", {"text": "القرء", field: True})
        for clause in ("«واسأل القرية»", "لم أقل واسأل القرية", "واسأل القرية؟", "واسأل القَرِيَّة", "واسأل القريةَ غداً"):
            self.assertEqual(reader.citation_card(clause), [])
        row, = reader.citation_card("  وَاسْأَلِ الْقَرْيَةَ.")
        ev = row["evidence"]
        raw = (reader.ROOT / ev["source_path"]).read_bytes()
        self.assertIn("أي أهل القرية", raw[ev["start_byte"]:ev["end_byte"]].decode())
        self.assertFalse(ev["estimated_word_written"])

    def test_text_receipt_inherits_orchestration_families_tests_and_debts(self):
        links = gateway_links.build("text.read")
        owner = gateway_links.build("cognitive.orchestrate")
        families = {row["family"] for row in links["family_test_links"]}
        self.assertTrue({"identity", "transition-law", "progressive-units", "mantuq-mafhum"} <= families)
        for field in ("family_test_links", "declarations", "tests", "open_obligations"):
            with self.subTest(field=field):
                self.assertEqual(links[field], owner[field])
        self.assertFalse(links["test_execution_performed"])

    def test_names_have_local_open_references_only(self):
        _, mentions = reader.lexical_context("زيد حكيم")
        self.assertEqual([r["name"] for r in mentions], ["زيد"])
        self.assertEqual(reader.lexical_context("زيد وزيد زيد")[1], [])
        self.assertFalse(reader.citation_card("رأيت القرية"))

    def test_http_only_shows_verified_cards_and_escapes_input(self):
        form = urlencode({"text": "<script>"}).encode()
        env = {"PATH_INFO": "/", "REQUEST_METHOD": "POST", "CONTENT_TYPE": "application/x-www-form-urlencoded",
               "CONTENT_LENGTH": str(len(form)), "wsgi.input": BytesIO(form)}
        with mock.patch.object(gateway, "run", return_value={"status": "EXECUTED", "execution": {"owner_result": {"untrusted": "forged"}}}), \
             mock.patch.object(gateway, "accept_output", return_value={"valid": False, "status": "REJECT"}):
            statuses = []
            html = b"".join(client.application(env, lambda status, headers: statuses.append(status))).decode()
        self.assertEqual(statuses, ["503 Service Unavailable"])
        self.assertNotIn("forged", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


@skipUnless(READY, "Build native cognitive-orchestration owners")
class NativeTextReading(TestCase):
    def test_nominal_conditional_readings_and_independent_replay(self):
        req = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": {"text": "زيد حكيم"}}
        report = gateway.run(req)
        self.assertEqual(report["status"], "EXECUTED", report["execution"].get("code"))
        result = report["execution"]["owner_result"]
        views = [c for c in result["cards"] if c["scope"] == "conditional_predication"]
        self.assertTrue(any("زيد" in c["understood"] and "حَكِيم" in c["understood"] for c in views))
        self.assertEqual({c["degree"] for c in views}, {"قراءة مشروطة بالضبط"})
        self.assertEqual(result["grammar_stop"], "orthography")
        self.assertFalse(result["world_truth_established"])
        self.assertTrue(gateway.accept_output(report, expected_request=req)["valid"])
        tampered = deepcopy(report)
        tampered["execution"]["owner_result"]["cards"][0]["understood"] = "خبر باطل"
        self.assertFalse(gateway.accept_output(tampered, expected_request=req)["valid"])

    def test_remaining_acceptance_cases_from_one_public_field(self):
        cases = [
            (LION, {"expressed_intent", "use_deferred"}),
            (LION + EXCLUSION, {"expressed_intent", "conditional_use"}),
            ("القرء", {"lexical_alternatives"}),
            ("أعني بالقرء الطهر والحيض", {"expressed_intent", "conditional_use"}),
            ("واسأل القرية", {"attested_ellipsis"}),
            ("لفظغيرمعروف", {"unresolved"}),
        ]
        for text, scopes in cases:
            with self.subTest(text=text):
                view = client.checked_view(text)
                self.assertTrue(view["verified"], view)
                self.assertEqual({c["scope"] for c in view["cards"]}, scopes)
                self.assertTrue(all(c[k] for c in view["cards"] for k, _ in client.LABELS))
                self.assertFalse(view["world_truth_established"])

    def test_substitution_premise_is_visible_in_both_clients(self):
        view = client.checked_view("زيد حكيط")
        self.assertTrue(view["verified"], view)
        readings = [c for c in view["cards"] if c["scope"] == "conditional_predication"]
        self.assertTrue(readings)
        for c in readings:
            ed, = [m for m in c["evidence"]["conditional_source"]["mappings"] if m["spelling_edit"]]
            self.assertFalse(ed["spelling_edit"]["original_is_error_established"])
            self.assertEqual(ed["observed"], "حكيط")
            self.assertNotEqual(c["degree"], "قراءة مشروطة بالضبط")
            for rendered in (client.as_text(view), client.page(view=view)):
                self.assertIn("«حكيط»", rendered)
                self.assertIn("«" + ed["proposed"] + "»", rendered)
                self.assertIn("لم يثبت خطأ الرسم الأصلي", rendered)
        self.assertEqual(view["source"]["text"], "زيد حكيط")

    def test_mixed_literal_and_unresolved_figurative_senses(self):
        view = client.checked_view("أعني بالأسد الحيوان المفترس والرجل الشجاع")
        self.assertTrue(view["verified"], view)
        intent, = [c for c in view["cards"] if c["scope"] == "expressed_intent"]
        self.assertEqual(set(intent["evidence"]["selected"]), {"asad_animal", "asad_brave"})
        accepted, = [c for c in view["cards"] if c["scope"] == "conditional_use"]
        deferred, = [c for c in view["cards"] if c["scope"] == "use_deferred"]
        self.assertEqual(accepted["evidence"]["sense_id"], "asad_animal")
        self.assertEqual(deferred["evidence"]["sense_id"], "asad_brave")
        self.assertIn("الرجل الشجاع", deferred["understood"])
        self.assertIn("استبعاد", deferred["unresolved"])
        self.assertEqual(deferred["evidence"]["occurrence"], accepted["evidence"]["occurrence"])

    def test_missing_checker_surfaces_with_and_without_independent_cards(self):
        # Exercise the installed acquisition owner without changing the checkout's executables.
        with mock.patch.object(aligned_acquisition, "_native", side_effect=FileNotFoundError):
            for source, other in (("زيد", set()), ("واسأل القرية", {"attested_ellipsis"})):
                with self.subTest(source=source):
                    result = reader.analyze(source)
                    self.assertEqual({c["scope"] for c in result["cards"]}, {"technical"} | other)
                    technical, = [c for c in result["cards"] if c["scope"] == "technical"]
                    self.assertEqual(technical["degree"], "VERIFICATION_UNAVAILABLE")
                    self.assertIn("NATIVE_CHECKER_UNAVAILABLE", technical["why"])
                    view = {**result, "verified": True}
                    for rendered in (client.as_text(view), client.page(view=view)):
                        self.assertIn("NATIVE_CHECKER_UNAVAILABLE", rendered)

    def test_failed_replay_on_spelling_candidate_keeps_its_parent_span(self):
        replay = aligned_acquisition._native
        def mismatch(request):
            if request["text"] == "حَكِيمٌ":
                return {}
            return replay(request)
        with mock.patch.object(aligned_acquisition, "_native", side_effect=mismatch):
            result = reader.analyze("زيد حكيط")
        technical, = [c for c in result["cards"] if c["scope"] == "technical"]
        self.assertEqual(technical["degree"], "VERIFICATION_FAILED")
        self.assertIn("NATIVE_REPLAY_MISMATCH", technical["why"])
        location, = technical["evidence"]["locations"]
        span = location["span"]
        self.assertEqual(result["source"]["text"].encode()[span["start"]:span["end"]].decode(), "حكيط")
        self.assertEqual((location["observed"], location["proposed"]), ("حكيط", "حَكِيمٌ"))
        self.assertNotIn("unresolved", {c["scope"] for c in result["cards"]})

    def test_branch_budget_is_not_reported_as_missing_linguistic_evidence(self):
        result = reader.analyze("زيد زيد زيد زيد زيد")
        row, = result["cards"]
        self.assertEqual((row["scope"], row["degree"]), ("technical", "RESOURCE_EXHAUSTED"))
        self.assertEqual(row["evidence"]["reason"], result["orchestration"]["source_reading"]["branch_status"])

    def test_conditional_profiles_and_withdrawal(self):
        def extract(s):
            r = reader.usage.acquire(s, source_id="input")
            return reader.use_cards(r, reader.profile_reports(s, "input", r))
        before, after = extract(LION), extract(LION + EXCLUSION)
        self.assertIn("use_deferred", [x["scope"] for x in before])
        self.assertEqual([c["evidence"]["selected"] for c in before if c["scope"] == "expressed_intent"],
                         [c["evidence"]["selected"] for c in after if c["scope"] == "expressed_intent"])
        branches = [x["evidence"] for x in after if x["scope"] == "conditional_use"]
        self.assertEqual([(r["profile_id"], r["use_kind"]) for r in branches], [("linguistic", "figurative")])
        self.assertTrue(branches[0]["witness_id"])
        self.assertFalse(any(x["scope"] == "conditional_use" for x in extract("«" + LION + EXCLUSION + "»")))
        alternatives = extract("القرء")
        self.assertEqual([c["scope"] for c in alternatives], ["lexical_alternatives"])
        both = extract("أعني بالقرء الطهر والحيض")
        self.assertEqual(set(next(c["evidence"]["selected"] for c in both if c["scope"] == "expressed_intent")), {"qur_hayd", "qur_tuhr"})
        self.assertIn("lexical_conflict", [x["scope"] for x in extract("أعني بالأسد الحيوان المفترس لا الحيوان المفترس")])
