import json
from collections import Counter
from unittest import TestCase, skipUnless
from unittest.mock import patch

from nabt.source_lexicon import source_registry
from tools.awamil_occurrence_fixtures import fixtures, agrees
from tools.grammar_catalog import morphology_matrix as m
from tools.grammar_catalog.awamil_occurrence import read
from tools.grammar_catalog.awamil_profile import profiles
from tools.grammar_catalog.operations import ROOT


def query(word, *target, occurrence=1):
    return m.analyze(word, "matrix-test", {"occurrence":occurrence,"target":list(target)})


class MatrixDeposit(TestCase):
    def test_workbook_and_governor_owners(self):
        tabs = m.workbook(m.sealed(m.BOOK))
        self.assertEqual(m.sheet_manifest(),json.loads((ROOT/m.DIRECTORY/"sheets.json").read_bytes()))
        self.assertEqual(len(tabs),15)
        readings = {r["A"] for r in tabs["مصفوفة المفاهيم"]}
        self.assertEqual(readings,{f"ق{i:03}" for i in range(1,81)})
        categories = json.loads(m.sealed(m.CLASSIFICATION))
        self.assertEqual(Counter(i for group in categories for i in group["readings"]),Counter(readings))
        governors = {r["A"] for r in tabs["عوامل الجرجاني"]}
        self.assertTrue(all(r["N"] in governors for r in tabs["مصفوفة المفاهيم"]))
        self.assertEqual(len(tabs["شروط الأدوار"]),102)
        self.assertTrue(all(r["A"] in readings for r in tabs["شروط الأدوار"]))
        self.assertTrue(all(r["B"] in readings and r["C"] in governors for r in tabs["شواهد الربط"]))
        for f,row in zip(fixtures(),tabs["عوامل الجرجاني"],strict=True):
            self.assertEqual((row["A"],row["E"]),("jurjani:%03d"%f["factor"],f["text"]))
            actual, = read(row["E"])[0]
            self.assertTrue(agrees(actual,f))
            self.assertEqual(row["N"],actual["reading_ar"])
        by_id,_ = profiles()
        for i,r in enumerate(tabs["عوامل NABT"],1):
            self.assertEqual((r["A"],r["D"]),(f"nabt:{i:03}",by_id[i][2]))
        for sheet, n in [("اختبار الرأس",43),("تجربة الشاهد",16)]:
            self.assertEqual([r["R"] for r in tabs[sheet]],["مطابق"]*n)

    def test_governed_reading_requires_the_witnessed_head_and_occurrence(self):
        bare = query("مَرَرْتُ بمساجدَ", occurrence=2)
        annexed = query("مَرَرْتُ بمساجدِ المدينةِ", occurrence=2)
        for report, sign in ((bare, "الفتحة"), (annexed, "الكسرة")):
            self.assertEqual([r["reading_id"] for r in report["readings"]], ["ق080"])
            frame, = report["governed_frames"]
            self.assertEqual((frame["case"], frame["sign"]), ("جر", sign))
        self.assertEqual(query("مَرَرْتُ بمساجدَ", occurrence=1)["governed_frames"], [])
        self.assertEqual(query("مَسَاجِد")["governed_frames"], [])
        written = query("لَنْ يَكْتُبُوا الرسالةَ", occurrence=2)
        self.assertEqual(written["governed_frames"][0]["link"], "derived_event")
        self.assertNotIn("ق055", [r["reading_id"] for r in written["readings"]])
        tabs = m.workbook(m.sealed(m.BOOK))
        anchors = json.loads(m.sealed(m.DEFINITIONS))["frame_anchors"]
        for row in tabs["شواهد الربط"]:
            text = row["E"]
            position = anchors[row["A"]]["occurrence"]
            frames = m._source_frames(text, position, tabs, anchors)
            frame, = [f for f in frames if f["witness"] == row["A"]]
            for field in ("head", "dependent"):
                left, right = frame[field + "_utf8_span"]
                self.assertEqual(text.encode()[left:right].decode(), frame[field])

    def test_source_bytes_for_every_alignment(self):
        definitions=json.loads(m.sealed(m.DEFINITIONS))
        self.assertEqual(len({r["id"] for r in definitions["readings"]}),22)
        spec=source_registry()["sources"]["maqayis"]
        lex=m.edition((ROOT/spec["checkout_default"]).read_bytes())
        rows={r["A"]:r for r in m.workbook(m.sealed(m.BOOK))["مصفوفة المفاهيم"]}
        for entry in definitions["readings"]:
            row=rows[entry["id"]]
            blocks=lex.lookup_exact(entry["heading"])["alternatives"]
            check=m._assessment(row,"اختبار",entry,blocks,lex.raw,definitions["necessities"],m.sealed(m.RULE),[])
            self.assertEqual(check["status"],"DEFINITION_REPLAYED")
            with self.assertRaises(ValueError):
                m._assessment(row,"اختبار",entry,[],lex.raw,[],b"",[])
        with self.assertRaises(ValueError):
            m._assessment(rows["ق053"],"اختبار",next(r for r in definitions["readings"] if r["id"]=="ق053"),
                lex.lookup_exact("موت")["alternatives"],lex.raw,definitions["necessities"],b"",[])

    def test_occurrence_and_open_readings(self):
        report=query("مَوْت زَرْع",occurrence=2)
        self.assertEqual(report["token"]["utf8_span"],[len("مَوْت ".encode()),len("مَوْت زَرْع".encode())])
        self.assertEqual({r["reading_id"] for r in report["readings"]},{"ق003","ق010","ق017","ق022"})
        self.assertEqual({r["concept_class"] for r in report["readings"]},{"حدث أو عملية","جنس أو فئة أعيان"})
        self.assertIn("NEEDS_SENSE_ALIGNMENT",{r["denotation"]["status"] for r in report["readings"]})
        self.assertFalse(query("سَفَرْجَل")["readings"][0]["source_blocks"])
        self.assertFalse(query("سَفَرْجَل")["world_truth_established"])
        growth, = query("نَمَتْ")["readings"]
        self.assertEqual({edge["chain"] for edge in growth["lineage_examples"]},{"س١","س٥"})
        self.assertFalse(query("نَمَتْ")["individual_eligibility_established"])
        with self.assertRaises(ValueError):query("زرع",occurrence=True)
        with self.assertRaises(ValueError):query("زرع",occurrence=2)
        with self.assertRaises(ValueError):m.validate({"occurrence":1,"target":[],"sense":"ق010"})

    @skipUnless((ROOT/"formal/.lake/build/bin/lexicalDenotation").is_file(),"build lexicalDenotation")
    def test_native_indications_do_not_transfer(self):
        invalid = m.lexical_testimony._native(ROOT/"formal/.lake/build/bin/lexicalDenotation",
            {"op":"morphology_matrix","value":{"id":"ق053","root":"موت","category":"أداة","target":["زوال الحياة"]}})
        self.assertNotIn("indications",invalid)
        whole=query("زَرْع","في الأرض","طرح البذر")
        by_id={r["reading_id"]:r["denotation"] for r in whole["readings"]}
        self.assertEqual(by_id["ق010"]["indications"],["mutabaqa"])
        self.assertEqual(by_id["ق022"]["indications"],[])
        self.assertEqual(whole["common_indications"],[])
        self.assertEqual(query("مَوْت","زوال الحياة")["common_indications"],["tadammun"])
        necessary="امتناع اجتماع الحياة والموت للحامل في الوقت والجهة نفسيهما"
        self.assertEqual(query("مَوْت",necessary)["common_indications"],["iltizam"])
        self.assertEqual(query("مَاتَ",necessary)["common_indications"],[])
        with patch.object(m.lexical_testimony,"_native",side_effect=FileNotFoundError):
            pending=query("مَوْت",necessary)
        self.assertEqual(pending["readings"][0]["denotation"]["status"],"NATIVE_CHECK_UNAVAILABLE")
        self.assertEqual(pending["common_indications"],[])
