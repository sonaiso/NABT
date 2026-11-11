"""Independent lexical contrasts, held-out dictionary clauses and native gateway replay."""
from copy import deepcopy
import json
import os
import unittest
from unittest.mock import patch

from nabt.derivation import read_derivation
from tools.grammar_catalog import gateway, root_sense
from tools.grammar_catalog.operations import ROOT


def analyze(text, word, target=(), *, start_from=0, case=None):
    start = text.encode().index(word.encode(), start_from)
    query = {"span": [start, start + len(word.encode())], "target": list(target)}
    if case is not None:
        query["case"] = case
    return root_sense.analyze(text, "lesson", query, read_derivation(text, source_id="lesson", scope="relational"))


VERIFIED = ROOT / "formal/.lake/build/bin/verifiedReading"


class RootSenseBoundaries(unittest.TestCase):
    def test_rejects_partial_tokens_offsets_and_caller_conclusions(self):
        req = {"span": [0, 2], "target": []}
        root_sense.validate(req)
        for change in ({"span": [False, 3]}, {"span": [2, 2]}, {"target": "آلة"}, {"approved": True}):
            with self.assertRaises(ValueError):
                root_sense.validate({**req, **change})
        self.assertEqual(analyze("مفتاح", "مف")["reason"], "NO_COMPLETE_DERIVATION_OCCURRENCE")

    def test_native_gate_requires_binary(self):
        if os.environ.get("NABT_REQUIRE_IO_GATEWAY_NATIVE"):
            self.assertTrue(root_sense.PROFILE.is_file() and VERIFIED.is_file())

    def test_unavailable_checker_yields_no_lexical_license(self):
        with patch.object(root_sense.pilot, "file_sha", side_effect=FileNotFoundError):
            report = analyze("العمى", "العمى", ["البصر"])
        self.assertEqual(report["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(report["readings"], [])


@unittest.skipUnless(root_sense.PROFILE.is_file(), "Build lexicalDenotation")
class NativeRootSense(unittest.TestCase):
    def test_arity_uses_attestation_and_keeps_shape_alternatives(self):
        for word, root, arity in (("أَسْرَعَ", "سرع", 3), ("جَرْبَزَ", "جربز", 4)):
            with self.subTest(word=word):
                report = analyze(word, word)
                [row] = report["readings"]
                self.assertEqual((row["sense"]["root"], row["root_arity"]), (root, arity))
                self.assertTrue(row["testimony"]["source_file_replayed"])
                self.assertIn(root, [p["root"] for p in report["profile_shape_candidates"]])
        unseen = analyze("دَنْدَنَ", "دَنْدَنَ")
        self.assertEqual(unseen["readings"], [])
        self.assertIn("دندن", [r["root"] for r in unseen["profile_shape_candidates"]])

    def test_participles_and_fixed_nouns_keep_all_compatible_readings(self):
        for word, expected in (("مُدَحْرِجٌ", ["فاعل"]), ("مدحرَج", ["متأثر"]), ("مدحرج", ["فاعل","متأثر"])):
            self.assertEqual([r["role"] for r in analyze(word, word)["readings"]], expected)
        result = analyze("عقرب", "عقرب", ["من العنكبيات"])
        self.assertEqual([r["genus"] for r in result["readings"]], ["عنكبيات", "مؤشر"])
        self.assertEqual(result["common_installed_indications"], [])

    def test_whole_text_enumerates_unknown_and_repeated_occurrences_in_order(self):
        text = "مدحرج زحل مدحرج جربز الفرس عدا عدوا ثقيلا"
        d = read_derivation(text, source_id="batch", scope="relational")
        with patch.object(root_sense.lexical_testimony, "_native", wraps=root_sense.lexical_testimony._native) as native:
            report = root_sense.analyze(text, "batch", {"target":["عدو"]}, d)
        self.assertEqual(report["status"], "OCCURRENCES_ANALYZED")
        rows = report["occurrences"]
        self.assertEqual([r["occurrence"]["surface"] for r in rows], text.split())
        self.assertEqual(len({r["occurrence_id"] for r in rows}), len(rows))
        self.assertEqual(rows[1]["reason"], "NO_INSTALLED_LEXICAL_ALIGNMENT")
        self.assertEqual(rows[3]["gloss_candidate"]["conditional_denotation"]["indications"], ["tadammun"])
        self.assertEqual([c.args[1]["op"] for c in native.call_args_list], ["root_sense_profile", "root_gloss"])
        with self.assertRaises(ValueError):
            root_sense.validate({"target":[], "case":{}})

    def test_whole_part_and_mental_use_same_native_checker(self):
        for word, target, expected in (("مفتاح", ["آلة", "لفتح القفل الملائم"], "mutabaqa"),
                                       ("دحرجة", ["تحريك جسم"], "tadammun"), ("العمى", ["البصر"], "iltizam")):
            r = analyze(word, word, target)
            self.assertEqual(r["common_installed_indications"], [expected])
            self.assertFalse(r["world_truth_established"])
        self.assertEqual(len(analyze("قلم","قلم")["lexical_owner_reports"]["قلم"]["rows"]), 3)
        with patch.object(root_sense.lexical_testimony, "_citation", side_effect=ValueError("withdrawn")):
            r = analyze("مفتاح", "مفتاح", ["آلة"])
        self.assertEqual((r["status"], r["readings"]), ("VERIFICATION_UNAVAILABLE", []))

    def test_local_gloss_and_transfer_without_an_installed_sense(self):
        for word, subject, manner in (("جربز","الفرس","ثقيلا"), ("رَكَضَ","البعير","سريعا"),
                                       ("هَرْوَلَ","الرجل","سريعا")):
            text = f"سبق {word} {subject} عدا عدوا {manner} ثم"
            out = analyze(text, word, ["عدو"])
            g = out["gloss_candidate"]
            self.assertEqual(g["conditional_denotation"]["indications"], ["tadammun"])
            self.assertEqual(g["conditional_denotation"]["head"], word)
            self.assertEqual(g["participant"]["surface"], subject)
            self.assertEqual(g["manner"]["surface"], manner)
            a,b = g["property_bearer_span"]
            self.assertEqual(text.encode()[a:b].decode(), "عدوا")
            self.assertFalse(g["universal_property"])
            if word != "جربز":
                self.assertEqual(out["readings"], [])
        for text, selected in (("فنع وقال جربز الفرس عدا عدوا ثقيلا", "فنع"),
                               ("جربز الفرس. عدا عدوا ثقيلا","جربز")):
            self.assertIsNone(analyze(text, selected)["gloss_candidate"])

    @unittest.skipUnless(VERIFIED.is_file(), "Build verifiedReading")
    def test_case_requires_pair_and_exact_occurrence_in_clean_ledger(self):
        lesson = json.loads((ROOT/"examples/io_gateway/root_sense_case.json").read_text())["payload"]
        case = lesson["root_sense"]["case"]
        def run(text, ledger, start=0):
            r = analyze(text, "مفتاح", ["آلة"], start_from=start, case=ledger)
            return r["readings"][0]["case"]["status"]
        self.assertEqual(run(lesson["text"],case),"SCOPED_CAPABILITY")
        for altered in ({**case, "counterpart":"قفل2"},
                        {**case,"source":case["source"].replace("مفتاح1 يوافق قفل1.\n","")},
                        {**case,"source":case["source"].replace("ليس مفتاح1 مانع قفل1.\n","")}):
            self.assertEqual(run(lesson["text"],altered),"DEFER")
        self.assertEqual(run(lesson["text"],{**case,"source":case["source"]+"مفتاح1 مانع قفل1.\n"}),"CONFLICT")
        self.assertEqual(run(lesson["text"],case,1),"DEFER")
        self.assertEqual(run("«مفتاح»",case),"DEFER")

    @unittest.skipUnless(VERIFIED.is_file(), "Build verifiedReading")
    def test_alternative_support_and_quadriliteral_role_are_scoped(self):
        case = json.loads((ROOT/"examples/io_gateway/root_sense_case.json").read_text())["payload"]["root_sense"]["case"]
        alternative = case["source"].replace("مفتاح1 يوافق قفل1.\n", "") + (
            "مفتاح1 يناسب قفل1.\nإذا مفتاح1 يناسب قفل1 فإن مفتاح1 يوافق قفل1.\n")
        key = analyze("مفتاح مفتاح", "مفتاح", case={**case, "source": alternative})
        self.assertEqual(key["readings"][0]["case"]["status"], "SCOPED_CAPABILITY")

        # Independently derive the occurrence address from the documented wire format.
        import hashlib
        text = "مُدَحْرَج"
        raw = text.encode()
        binding = ["lesson", hashlib.sha256(raw).hexdigest(), 0, len(raw), "root-profile:rolled"]
        anchor = "r_" + hashlib.sha256(json.dumps(binding, ensure_ascii=False,
                separators=(",", ":")).encode()).hexdigest()
        ledger = (f"{anchor} مرجع حجر1.\n{anchor} طرف سطح1.\nحجر1 عضوية جسم.\n"
                  "حجر1 يقبل_التدحرج_على سطح1.\nليس حجر1 مانع سطح1.\n")
        case = {**case, "entity": "حجر1", "counterpart": "سطح1", "source": ledger}
        r = analyze(text, text, case=case)["readings"][0]["case"]
        self.assertEqual(r["status"], "SCOPED_CAPABILITY")
        self.assertFalse(r["world_occurrence"])
        self.assertEqual(analyze("مُدَحْرِج", "مُدَحْرِج", case=case)["readings"][0]["case"]["status"], "DEFER")

    @unittest.skipUnless(VERIFIED.is_file(), "Build verifiedReading")
    def test_gateway_replays_the_original_request(self):
        q=json.loads((ROOT/"examples/io_gateway/root_sense_case.json").read_text())
        r=gateway.run(q)
        self.assertEqual(r["status"], "EXECUTED", r["execution"])
        owner=r["execution"]["owner_result"]
        self.assertEqual(owner["root_sense"]["readings"][0]["case"]["status"], "SCOPED_CAPABILITY")
        self.assertFalse(owner["world_truth_established"])
        self.assertTrue(gateway.accept_output(r, expected_request=q)["valid"])
        changed=deepcopy(r)
        changed["execution"]["owner_result"]["root_sense"]["readings"][0]["sense"]["root"]="دحرج"
        self.assertFalse(gateway.accept_output(changed, expected_request=q)["valid"])
