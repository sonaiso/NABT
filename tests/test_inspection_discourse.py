import json
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from tools.grammar_catalog import gateway, ntp
from tools.lexical_training import inspection_discourse as lesson, inspection_roles as roles, teaching

TEXT = "أفاد الحارس أن الصندوق مفتوح. إذا ثبت فتحه في سجل المعاينة فأنشئ مسودة، ولا ترسلها."
ATTEMPT = {"op": "attempt"}
WITHDRAW = {"op": "withdraw", "id": "R1"}


def entry(**fields):
    return dict({"op": "observe", "id": "R1", "source": "المعاينة", "kind": "opening",
                 "object_id": "box-2", "scene_id": "visit-7", "actor": None, "polarity": "affirm"}, **fields)


def task(*steps, text=TEXT, objects=None):
    return {"schema": lesson.SCHEMA, "text": text, "scene_id": "visit-7", "steps": list(steps),
            "objects": {"box-2": "الصندوق", "door-1": "الباب"} if objects is None else objects}


class Decisions(TestCase):
    def test_five_answers_across_sixteen_episodes(self):
        # Oracles are independent expectations about the text, ledger, gate and actual artifact.
        # Columns: speaker, tail, inspection, admissible draft, performed draft.
        cases = [
            (task(), "الحارس", "forbid_send", "MISSING", False, False),
            (task(ATTEMPT), "الحارس", "forbid_send", "MISSING", False, False),
            (task(entry()), "الحارس", "forbid_send", "SUPPORTED", True, False),
            (task(entry(), ATTEMPT), "الحارس", "forbid_send", "SUPPORTED", True, True),
            (task(entry(), ATTEMPT, ATTEMPT), "الحارس", "forbid_send", "SUPPORTED", True, True),
            (task(entry(), WITHDRAW, ATTEMPT), "الحارس", "forbid_send", "MISSING", False, False),
            (task(entry(), ATTEMPT, WITHDRAW), "الحارس", "forbid_send", "MISSING", False, True),
            (task(entry(object_id="door-1"), ATTEMPT), "الحارس", "forbid_send", "MISSING", False, False),
            (task(entry(scene_id="visit-6"), ATTEMPT), "الحارس", "forbid_send", "MISSING", False, False),
            (task(entry(kind="open_state"), ATTEMPT), "الحارس", "forbid_send", "MISSING", False, False),
            (task(entry(source="الحارس"), ATTEMPT), "الحارس", "forbid_send", "MISSING", False, False),
            (task(entry(polarity="deny"), ATTEMPT), "الحارس", "forbid_send", "DENIED", False, False),
            (task(entry(), entry(id="R2", polarity="deny"), ATTEMPT), "الحارس", "forbid_send", "CONFLICT", False, False),
            (task(entry(), ATTEMPT, text=TEXT.replace("الحارس", "المهندس")), "المهندس", "forbid_send", "SUPPORTED", True, True),
            (task(entry(), ATTEMPT, text=TEXT.replace("ولا ترسلها", "وأرسلها")), "الحارس", "request_send", "SUPPORTED", True, True),
            (task(entry(), ATTEMPT, text=TEXT.replace("ولا ترسلها", "ولا تنشئها")), "الحارس", "forbid_draft", "SUPPORTED", False, False),
        ]
        for request, speaker, tail, status, admissible, performed in cases:
            with self.subTest(steps=request["steps"], text=request["text"]):
                a = lesson.run(request)["answers"]
                self.assertEqual(a["reported"], {"source": speaker, "content": {"bearer": "الصندوق", "state": "open"}, "force": "assert"})
                self.assertEqual(a["inspection"]["status"], status)
                self.assertEqual(a["requested"], {"source": "CURRENT_SPEAKER", "condition": {"kind": "registered_opening",
                                 "operator": "إذا", "bearer": "الصندوق", "register": "المعاينة"}, "then": "draft", "tail": tail})
                self.assertEqual(a["permitted"]["local"], ["draft"] if admissible else [])
                self.assertEqual(a["permitted"]["send"], "PROHIBITED" if tail == "forbid_send" else "NO_EXECUTOR")
                expected = [{"action": "draft", "scene_id": "visit-7", "object_id": "box-2", "witness_ids": ["R1"],
                             "body": "مسودة معاينة box-2"}] if performed else []
                self.assertEqual(a["performed"], expected)

    def test_answer_each_arabic_question_and_named_speaker(self):
        questions = {"ماذا أفاد الحارس؟":"reported", "ما الذي ثبت في السجل؟":"inspection",
                     "ماذا طلب المتكلّم؟":"requested", "ماذا يجوز فعله الآن؟":"permitted",
                     "ماذا فعلت الماكينة بالفعل؟":"performed"}
        for query, slot in questions.items():
            r = lesson.run(dict(task(entry()), question=query))
            self.assertEqual(r["question_answer"], {"slot":slot, "text":r["arabic_answers"][slot]})
        r = lesson.run(dict(task(text=TEXT.replace("الحارس", "المدير")), question="ماذا أفاد الحارس؟"))
        self.assertIn("لم تنسب القراءة خبرًا إلى الحارس", r["question_answer"]["text"])
        self.assertIn("المدير", r["question_answer"]["text"])
        self.assertIsNone(lesson.run(dict(task(), question="كم طوله؟"))["question_answer"]["slot"])

    def test_source_changes_only_attribution(self):
        before = lesson.run(task(entry(), ATTEMPT))["answers"]
        after = lesson.run(task(entry(), ATTEMPT, text=TEXT.replace("الحارس", "المهندس")))["answers"]
        self.assertEqual([k for k in before if before[k] != after[k]], ["reported"])
        self.assertEqual(before["reported"]["content"], after["reported"]["content"])

    def test_prior_action_independent_of_current_support(self):
        a = lesson.run(task(entry(), ATTEMPT, WITHDRAW))["history"]
        self.assertEqual([x["inspection"]["status"] for x in a], ["MISSING", "SUPPORTED", "SUPPORTED", "MISSING"])
        self.assertEqual([len(x["performed"]) for x in a], [0, 0, 1, 1])
        self.assertEqual(a[1]["inspection"]["witness_ids"], ["R1"])
        self.assertEqual(a[3]["inspection"]["witness_ids"], [])

    def test_actor_condition_records_the_event_in_the_simulator(self):
        sentence = "إذا فتح المهندس الصندوق فسجّل الفتح"
        for actor, object_id, ok in (("المهندس", "box-2", True), ("الحارس", "box-2", False),
                                     (None, "box-2", False), ("المهندس", "door-1", False)):
            result = lesson.run(task(entry(actor=actor, object_id=object_id), ATTEMPT, text=sentence))
            self.assertEqual(result["status"], "READ")
            a = result["answers"]
            self.assertIsNone(a["reported"])
            self.assertEqual(a["requested"]["condition"]["actor"], "المهندس")
            self.assertEqual([x["action"] for x in a["performed"]], ["record_opening"] if ok else [])

    def test_ambiguity_and_reported_state(self):
        for objects in ({}, {"a": "الصندوق", "b": "الصندوق"}):
            a = lesson.run(task(entry(), ATTEMPT, objects=objects))["answers"]
            self.assertEqual(a["inspection"]["status"], "UNRESOLVED_REFERENCE")
            self.assertTrue(a["permitted"]["question"])
            self.assertFalse(a["performed"])
        a = lesson.run(task(entry(), text=TEXT.replace("مفتوح", "مغلق")))["answers"]
        self.assertEqual((a["reported"]["content"]["state"], a["inspection"]["status"]), ("closed", "SUPPORTED"))

    def test_explicit_scope_and_only_active_relevant_witnesses(self):
        r = lesson.run(task(entry(source="الفحص"), entry(id="R2"), entry(id="R3", polarity="deny"),
                            {"op": "withdraw", "id": "R3"}, ATTEMPT))
        self.assertEqual(r["answers"]["performed"][0]["witness_ids"], ["R2"])
        for text in (TEXT.replace(". إذا", "، إذا"), TEXT.replace("فأنشئ", ". فأنشئ"), TEXT + " أرسلها.",
                     TEXT.replace("أن الصندوق", "أن الباب والصندوق"), "«" + TEXT + "»",
                     TEXT.replace("ثبت", "لم يثبت"), TEXT.replace("فأنشئ", "فأَنْشَأَ")):
            with self.subTest(text=text):
                r = lesson.run(task(entry(), ATTEMPT, text=text))
                self.assertEqual(r["status"], "DEFER_READING")
                self.assertFalse(r["answers"]["performed"])
        partial = lesson.run(task(text=TEXT.replace("ثبت", "لم يثبت")))["answers"]
        self.assertEqual(partial["reported"]["source"], "الحارس")
        self.assertIsNone(partial["requested"])

    def test_witnesses_and_recomposition(self):
        r = lesson.run(task())
        raw = TEXT.encode()
        slots = r["reading"]["witnesses_utf8"]
        for k, term in {"reporter":"الحارس", "state":"مفتوح", "if":"إذا", "opening_reference":"فتحه",
                        "register":"المعاينة", "consequence":"فأنشئ مسودة", "coordination":"ولا ترسلها"}.items():
            self.assertEqual(raw[slice(*slots[k])].decode(), term)
        s = TEXT.replace("فأنشئ", "فأعد").replace("إذا", "إن")
        r = lesson.run(task(text=s))
        self.assertNotEqual(r["canonical_text"], s)
        self.assertEqual(lesson.read(r["canonical_text"])["frame"], r["reading"]["frame"])

    def test_rejects_duplicate_witness_identity_and_foreign_action_claims(self):
        for steps in ((entry(), entry()), (WITHDRAW,), (entry(), WITHDRAW, entry()), ({"op":"attempt","done":True},)):
            with self.assertRaises(ValueError):
                lesson.run(task(*steps))
        invalid = dict(task(), performed=["draft"])
        self.assertEqual(teaching.run_lesson(invalid)["status"], "INVALID_INPUT")

    def test_proposals_do_not_authorize_and_unavailable_model_does_not_block(self):
        with patch.object(roles, "propose", side_effect=OSError):
            r = lesson.run(task(entry(), ATTEMPT))
            self.assertEqual(r["role_proposal"]["status"], "MODEL_UNAVAILABLE")
            self.assertEqual(len(r["answers"]["performed"]), 1)
        with patch.object(roles, "propose", return_value={"roles":["request"] * 15, "authority":"NONE"}):
            r = lesson.run(task(ATTEMPT))
            self.assertTrue(r["role_proposal"]["disagreement_term_indices"])
            self.assertEqual(r["answers"]["performed"], [])


class Training(TestCase):
    def test_frozen_weights_reproduce_and_paragraphs_are_disjoint(self):
        self.assertEqual(roles.fit(), json.loads(roles.MODEL.read_bytes()))
        seen = set()
        for name in ("train", "development", "holdout"):
            rows = list(roles.examples(roles.DATA / (name + ".tsv")))
            texts = {roles.bare(t) for t, _ in rows}
            self.assertEqual(len(texts), len(rows))
            self.assertFalse(seen & texts)
            seen.update(texts)
            if name == "holdout":
                for text, gold in rows:
                    self.assertEqual(roles.propose(text)["roles"], gold)
                    r = lesson.run(task(text=text))
                    self.assertEqual(r["status"], "READ")
                    self.assertEqual(r["role_proposal"]["disagreement_term_indices"], [])

    def test_public_free_text_reader_binds_same_condition(self):
        request = ntp.request("think", {"text": TEXT})
        receipt = gateway.run(request)
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])
        owner = receipt["execution"]["owner_result"]["owner_result"]
        self.assertEqual(owner["inspection_discourse"], lesson.read(TEXT))
        card, = [c for c in owner["cards"] if c["scope"] == "inspection_discourse"]
        self.assertEqual(card["evidence"]["action_authority"], "NONE")

    def test_registered_gateway_and_replay_bind_actual_inputs(self):
        request = ntp.request("cognitive.lesson", {"lesson": task(entry(), ATTEMPT, WITHDRAW)})
        receipt = gateway.run(request)
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])
        result = receipt["execution"]["owner_result"]
        self.assertEqual(result["owner_result"]["answers"]["inspection"]["status"], "MISSING")
        self.assertEqual(len(result["owner_result"]["answers"]["performed"]), 1)
        self.assertEqual(result["observation_request_path"], "/payload/input/lesson/text")
        altered = deepcopy(request)
        altered["payload"]["input"]["lesson"]["steps"].pop()
        self.assertFalse(gateway.accept_output(receipt, expected_request=altered)["valid"])
