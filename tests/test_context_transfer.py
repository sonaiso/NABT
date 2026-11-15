from copy import deepcopy
import os
from unittest import TestCase, mock, skipUnless

from tools import aligned_acquisition as acquisition
from tools.grammar_catalog import gateway
from tools.lexical_training import context_transfer as ctx, teaching


def lesson(*probes):
    return {"schema":ctx.SCHEMA, **deepcopy(ctx.SEA), "probes":list(probes)}


NATIVE = acquisition._NATIVE_PATH.is_file()
if os.getenv("NABT_REQUIRE_IO_GATEWAY_NATIVE")=="1" and not NATIVE:
    raise RuntimeError("The contextual transfer gate needs alignedAcquisition")


class InputTests(TestCase):
    def test_probe_labels_unknown_fields_and_repeated_sources_rejected(self):
        text = "أمامنا بَحْرٌ أمواجه هادئة."
        for bad in (dict(lesson(text),answers=["literal"]),lesson({"text":text,"label":"literal"}),
                    lesson(ctx.SEA["examples"][0]["text"]),lesson(*([text]*25))):
            result=teaching.run_lesson(bad)
            self.assertEqual(result["status"],"INVALID_INPUT")

    def test_ambiguous_target_and_native_unavailability(self):
        for source in ("بَحْرٌ بَحْرٌ أمواجه هادئة.","لم يظهر بَحْرٌ تتلاطم أمواجه.","«بَحْرٌ في العلم»"):
            self.assertEqual(ctx.run(lesson(source))["predictions"][0]["decision"],"UNRESOLVED")
        with mock.patch.object(acquisition,"_native",side_effect=FileNotFoundError):
            row=ctx.run(lesson("أمامنا بَحْرٌ تتلاطم أمواجه."))["predictions"][0]
            self.assertEqual(row["reason"],"VERIFICATION_UNAVAILABLE")


@skipUnless(NATIVE,"requires the native A116 checker")
class LearningTests(TestCase):
    def test_occurrence_witnesses_before_after_and_withdrawal(self):
        a="أمامنا بَحْرٌ تتلاطم أمواجه."
        b="معلّمنا بَحْرٌ في العلم يجيب عن كل سؤال."
        c="أمامنا بَحْرٌ."
        d="أمامنا بَحْرٌ من العلم تتلاطم أمواجه."
        full=lesson(a,b,c,d)
        rows=ctx.run(full)["predictions"]
        self.assertEqual([r["decision"] for r in rows],["literal","figurative","UNRESOLVED","CONFLICT"])
        self.assertEqual([r["address"]["number"] for r in rows],["8131932"]*4)
        for text,row,gold in zip((a,b),rows,("أمواجه","العلم")):
            match,=row["matches"]
            start,stop=match["utf8_span"]
            self.assertEqual(text.encode()[start:stop].decode(),gold)
        self.assertEqual(rows[1]["interpretation_from_teacher"]["relation"],"المشابهة في السعة")
        self.assertTrue(all(r["decision"]=="UNRESOLVED" for r in ctx.run(dict(full,examples=[]))["predictions"]))
        self.assertFalse(ctx.run(full)["semantic_license"])
        self.assertEqual(ctx.run(lesson("هو بحر في العلم."))["predictions"][0]["decision"],"UNRESOLVED")

    def test_interactive_question_discriminates_and_updates(self):
        task=lesson("رأينا بَحْرٌ أمواجه عالية.")
        for e in task["examples"][:2]:
            e["text"]=e["text"].replace("."," اليوم.")
        task["query_pool"]=["سكن بَحْرٌ في الصباح.","هذا بَحْرٌ أمواجه قوية."]
        first=ctx.run(task)
        self.assertEqual(first["predictions"][0]["reason"],"INDISTINGUISHABLE_TRAINING_CUES")
        self.assertEqual(first["next_query"]["pool_index"],1)
        source=first["next_query"]["text"]
        task["examples"].append({"text":source,"label":"literal"})
        del task["query_pool"]
        row,=ctx.run(task)["predictions"]
        self.assertEqual(row["decision"],"literal")
        self.assertIsNone(row["interpretation_from_teacher"])

    def test_gateway_replay_and_source_mutation(self):
        req={"schema":gateway.REQUEST_SCHEMA,"route":"cognitive.lesson",
             "payload":{"lesson":lesson("أمامنا بَحْرٌ تتلاطم أمواجه.")}}
        result=gateway.run(req)
        valid=gateway.accept_output(result,expected_request=req)
        self.assertTrue(valid["valid"],valid)
        self.assertEqual(result["execution"]["owner_result"]["predictions"][0]["decision"],"literal")
        req["payload"]["lesson"]["probes"][0]="أمامنا بَحْرٌ."
        self.assertFalse(gateway.accept_output(result,expected_request=req)["valid"])
