"""Adversarial boundaries for exact source candidates and separate paradigms."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.derivation import (decode_derivation, derivation_number, generate_derivation,
                             installed_registry, pattern_catalog, read_derivation, verify_derivation)
from nabt.errors import NabtError
from nabt.verb_paradigm import (availability_candidates, read_verb_paradigm, verify_verb_paradigm)


def candidates(text, profile="surface_v1"):
    return read_derivation(text, profile=profile)["occurrences"][0]["candidates"]


def pairs(text, profile="surface_v1"):
    return {(c["pattern_id"], c["root"]) for c in candidates(text, profile)}


class DerivationTests(unittest.TestCase):
    def test_27_new_grammar_shapes_against_authored_examples(self):
        # Additional post-implementation examples, not part of the frozen
        # 96-case independent material and not semantic lexical attestations.
        examples = [
            ("masdar.bare.fa3l", "درس", "دَرْس"),
            ("masdar.bare.fa3al", "فرح", "فَرَح"),
            ("masdar.bare.fu3ul", "خرج", "خُرُوج"),
            ("masdar.bare.fa3ala", "شجع", "شَجَاعَة"),
            ("masdar.bare.fu3ula", "سهل", "سُهُولَة"),
            ("masdar.II.taf3il", "علم", "تَعْلِيم"),
            ("masdar.III.mufa3ala", "قتل", "مُقَاتَلَة"),
            ("masdar.III.fi3al", "قتل", "قِتَال"),
            ("masdar.IV.if3al", "كرم", "إِكْرَام"),
            ("masdar.V.tafa33ul", "علم", "تَعَلُّم"),
            ("masdar.VI.tafa3ul", "قتل", "تَقَاتُل"),
            ("masdar.VII.infi3al", "كسر", "اِنْكِسَار"),
            ("masdar.VIII.ifti3al", "كسب", "اِكْتِسَاب"),
            ("masdar.X.istif3al", "غفر", "اِسْتِغْفَار"),
            ("masdar.quad.fa3lala", "دحرج", "دَحْرَجَة"),
            ("instrument.mif3al", "برد", "مِبْرَد"),
            ("instrument.mif3ala", "كنس", "مِكْنَسَة"),
            ("instrument.mif3aal", "فتح", "مِفْتَاح"),
            ("place.maf3al", "كتب", "مَكْتَب"),
            ("place.maf3il", "جلس", "مَجْلِس"),
            ("sifa.fa3al", "حسن", "حَسَن"),
            ("sifa.fa3il", "كرم", "كَرِيم"),
            ("sifa.faa3il", "طهر", "طَاهِر"),
            ("diminutive.fu3ayl", "كلب", "كُلَيْب"),
            ("diminutive.fu3ay3il", "جعفر", "جُعَيْفِر"),
            ("diminutive.fu3ay3iil", "عصفر", "عُصَيْفِير"),
            ("comparative.af3al", "كبر", "أَكْبَر"),
        ]
        for name, root, surface in examples:
            identity = "grammar." + name
            with self.subTest(pattern=identity):
                self.assertEqual(generate_derivation(root, identity)["surface"], surface)
                self.assertIn((identity, root), pairs(surface))
                self.assertTrue(all(not c["lexical_class_activated"] for c in candidates(surface)))
        overlap = pairs("كَاتِب")
        self.assertIn(("nominal.faail", "كتب"), overlap)
        self.assertIn(("grammar.sifa.faa3il", "كتب"), overlap)

    def test_named_nominal_patterns_recover_unlisted_root_without_kind_authority(self):
        report = read_derivation("حَاذِرٌ مَحْذُورٌ")
        first, second = report["occurrences"]
        self.assertIn(("nominal.faail", "حذر"), pairs(first["surface"]))
        self.assertIn(("nominal.mafool", "حذر"), pairs(second["surface"]))
        self.assertEqual(first["axes"]["kind"]["candidates"], ["noun", "verb", "particle"])
        self.assertEqual(first["axes"]["attested_root"]["status"], "DEFER")
        self.assertEqual(first["axes"]["nominal_semantics"]["candidates"], ["jamid", "mushtaq"])
        self.assertEqual(first["axes"]["verb_productivity"]["candidates"], ["jamid", "partial", "full"])
        self.assertIsNone(first["actual_case"])
        self.assertEqual(report["recognition_basis"]["content_word_answer_entries_used"], 0)
        self.assertFalse(report["recognition_basis"]["given_root_list_used"])

    def test_ambiguous_root_and_pattern_both_survive(self):
        found = pairs("انْتَبَر", "stem_exact_v1")
        self.assertIn(("past.VII", "تبر"), found)
        self.assertIn(("past.VIII", "نبر"), found)
        self.assertEqual(read_derivation("انْتَبَر")["occurrences"][0]["shape_status"], "AMBIGUOUS")

    def test_every_literal_is_checked(self):
        self.assertIn(("nominal.faail", "كتب"), pairs("كَاتِب"))
        self.assertNotIn(("nominal.faail", "كتب"), pairs("كَوتِب"))
        self.assertNotIn(("nominal.mafool", "كتب"), pairs("نَكْتُوب"))
        self.assertNotIn(("past.VIII", "كتب"), pairs("اكْثَتَب"))

    def test_exact_boundary_profile_preserves_ending_without_case(self):
        found = [c for c in candidates("كَاتِبٌ") if c["pattern_id"] == "nominal.faail"]
        self.assertEqual(len(found), 1)
        self.assertEqual((found[0]["stem"], found[0]["boundary"]), ("كَاتِب", "ٌ"))
        self.assertEqual(found[0]["surface"], found[0]["stem"] + found[0]["boundary"])
        self.assertIsNone(found[0]["actual_case"])
        self.assertNotIn(("nominal.faail", "كتب"), pairs("كَاتِبٌ", "stem_exact_v1"))
        self.assertNotIn(("nominal.faail", "كتب"), pairs("كَاتِبًا"))

    def test_no_unicode_folding_or_unmarked_vowel_guess(self):
        self.assertIn(("past.II", "علم"), pairs("عَلَّم"))
        self.assertNotIn(("past.II", "علم"), pairs("عَلَّم"))
        self.assertNotIn(("past.IV", "كرم"), pairs("أَكْرَم"))
        self.assertIn(("past.IV", "كرم"), pairs("ءَكْرَم"))
        self.assertFalse(candidates("كاتب"))
        self.assertFalse(candidates("وَكَاتِبٌ"))

    def test_sound_imperfect_scope_and_new_projection_are_explicit(self):
        found = [c for c in candidates("يُعَلِّمُ") if c["pattern_id"] == "imperfect.II"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["root"], "علم")
        self.assertEqual(found[0]["root_domain"], "sound_triliteral_distinct")
        self.assertNotIn(("imperfect.II", "علم"), pairs("يُعَلْلِمُ"))
        self.assertNotIn(("imperfect.III", "قتل"), pairs("يُقَاْتِلُ"))
        self.assertNotIn(("imperfect.I.u", "دعو"), pairs("يَدْعُو"))
        self.assertNotIn(("imperfect.I.u", "مدد"), pairs("يَمْدُدُ"))

    def test_future_marker_is_a_separate_unactivated_relation(self):
        report = read_derivation("سَوْفَ يَكْتُبُ")
        self.assertEqual(len(report["future_proposals"]), 1)
        proposal = report["future_proposals"][0]
        self.assertTrue(proposal["imperfect_shape_candidates"])
        self.assertFalse(proposal["temporal_reading_activated"])
        self.assertIsNone(proposal["future_weight"])
        self.assertIsNone(proposal["actual_tense"])
        for gap in ("\n", "؛ ", ", "):
            self.assertFalse(read_derivation("سَوْفَ" + gap + "يَكْتُبُ")["future_proposals"])
        self.assertFalse(read_derivation("سَيَكْتُبُ")["future_proposals"])
        self.assertIsNone(pattern_catalog()["future_pattern"])

    def test_nun_origin_is_pattern_specific_not_grammatical_nun_type(self):
        found = candidates("انْتَبَر")
        seven = next(c for c in found if c["pattern_id"] == "past.VII")
        eight = next(c for c in found if c["pattern_id"] == "past.VIII")
        self.assertEqual(seven["nun_positions"][0]["structural_origin"], {"type": "literal", "literal": "ن"})
        self.assertEqual(eight["nun_positions"][0]["structural_origin"], {"type": "radical", "root_index": 0})
        self.assertIsNone(seven["nun_positions"][0]["grammatical_nun_type"])
        run = read_derivation("يَكْتُبْنَ")["occurrences"][0]
        self.assertTrue(run["final_nun_observed"])
        self.assertIsNone(run["segmentation"]["nun_type"])

    def test_occurrence_scope_and_utf8_alignment_are_bound(self):
        text = "  كَاتِبٌ\tكَاتِبٌ، «كَاتِبٌ»\n"
        report = read_derivation(text, scope="one")
        self.assertEqual("".join(s["surface"] for s in report["partition"]), text)
        a, b, quoted = report["occurrences"]
        self.assertEqual(quoted["reading_context"], "MENTION")
        self.assertTrue(quoted["candidates"])
        self.assertNotEqual(a["occurrence_id"], b["occurrence_id"])
        self.assertNotEqual(a["candidates"][0]["candidate_id"], b["candidates"][0]["candidate_id"])
        raw = text.encode("utf-8")
        for candidate in a["candidates"]:
            for atom in candidate["alignment"]:
                span = atom["span"]
                self.assertEqual(raw[span["start"]:span["end"]].decode("utf-8"), atom["surface"])
        self.assertTrue(verify_derivation(report, text=text, scope="one")["valid"])
        self.assertFalse(verify_derivation(report, scope="two")["valid"])
        self.assertFalse(verify_derivation(report, source_id="other")["valid"])

    def test_quoted_mentions_have_source_spans_but_no_future_attachment(self):
        text = "«سَوْفَ يَكْتُبُ» كَاتِبٌ"
        report = read_derivation(text)
        self.assertEqual(len(report["occurrences"]), 3)
        self.assertEqual([r["reading_context"] for r in report["occurrences"]], ["MENTION", "MENTION", "UNQUOTED"])
        self.assertFalse(report["future_proposals"])
        self.assertIn(("imperfect.I.u", "كتب"), {(c["pattern_id"], c["root"])
                      for c in report["occurrences"][1]["candidates"]})

    def test_generation_retains_supplied_premises(self):
        result = generate_derivation("كتب", "nominal.mafool", ending="ٌ")
        self.assertEqual(result["surface"], "مَكْتُوبٌ")
        self.assertEqual(result["root_basis"], "SUPPLIED_FORMAL_RADICALS")
        self.assertFalse(result["attested_word"])
        self.assertFalse(result["attested_root"])
        for root in (True, None, "كْتب", "كات", "كت", "كتبب", "aبج"):
            with self.subTest(root=root), self.assertRaises(NabtError):
                generate_derivation(root, "nominal.faail")
        with self.assertRaises(NabtError) as ctx:
            generate_derivation("كتب", "future.I")
        self.assertEqual(ctx.exception.status, "DEFER")
        with self.assertRaises(NabtError):
            generate_derivation("كتب", "past.I.a", ending="ُ")

    def test_full_report_replay_rejects_promoted_or_reordered_evidence(self):
        report = read_derivation("انْتَبَر")
        modifications = [
            lambda r: r["occurrences"][0]["candidates"][0].update(root="كتب"),
            lambda r: r["occurrences"][0]["candidates"][0].update(lexical_class_activated=True),
            lambda r: r["occurrences"][0].update(actual_case="raf"),
            lambda r: r["occurrences"][0]["candidates"].pop(),
            lambda r: r.update(source_restored=1),
            lambda r: r["recognition_basis"].update(given_root_list_used=True),
        ]
        for edit in modifications:
            changed = deepcopy(report)
            edit(changed)
            self.assertFalse(verify_derivation(changed)["valid"])

    def test_codec_preserves_only_replayed_canonical_report(self):
        report = read_derivation("كَاتِبٌ")
        value = derivation_number(report)
        self.assertEqual(decode_derivation(value), report)
        for invalid in (True, -1, "1", 0):
            with self.assertRaises(NabtError):
                decode_derivation(invalid)
        forged = int.from_bytes(b"\x01" + json.dumps(report, ensure_ascii=False).encode(), "big")
        with self.assertRaises(NabtError):
            decode_derivation(forged)

    def test_unknown_invalid_and_exhaustion_differ(self):
        self.assertFalse(read_derivation("unknown")["occurrences"][0]["candidates"])
        for invalid in ("كَاتِبٌُ", "َكَاتِب", b"\xff", True, ""):
            with self.assertRaises(NabtError) as ctx:
                read_derivation(invalid)
            self.assertEqual(ctx.exception.status, "REJECT")
        with self.assertRaises(NabtError) as ctx:
            read_derivation("x" * 8193)
        self.assertEqual((ctx.exception.status, ctx.exception.code), ("DEFER", "RESOURCE_LIMIT"))
        with self.assertRaises(NabtError):
            read_derivation("كَاتِب", profile=True)

    def test_installed_table_cannot_be_replaced_by_caller_metadata(self):
        with patch("nabt.derivation.EXPECTED_TABLE_SHA256", "0" * 64):
            with self.assertRaises(NabtError) as ctx:
                installed_registry()
            self.assertEqual(ctx.exception.status, "DEFER")

    def test_cli_requires_original_source_for_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "text.txt", Path(directory) / "report.json"
            source.write_text("كَاتِبٌ", encoding="utf-8")
            reading = subprocess.run([sys.executable, "-m", "nabt", "read-derivation", str(source)],
                                     capture_output=True, text=True)
            self.assertEqual(reading.returncode, 3)
            target.write_text(reading.stdout, encoding="utf-8")
            cmd = [sys.executable, "-m", "nabt", "verify-derivation", str(target), "--source", str(source)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            source.write_text("حَاذِرٌ", encoding="utf-8")
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)


class VerbParadigmTests(unittest.TestCase):
    def axis(self, body):
        return read_verb_paradigm("الفعل «زلم».\n" + body)["readings"][0]["axis"]

    def test_one_observed_past_does_not_establish_jamid(self):
        axis = self.axis("الماضي مستعمل: «زَلَمَ».")
        self.assertEqual(axis["status"], "DEFER")
        self.assertEqual(set(axis["candidates"]), {"jamid", "partial", "full"})
        axis = self.axis("الماضي مستعمل: «زَلَمَ».\nالمضارع مستعمل: «يَزْلُمُ».")
        self.assertEqual(set(axis["candidates"]), {"partial", "full"})

    def test_classification_uses_explicit_availability_not_semantic_noun_axis(self):
        source = "الفعل «ليس».\nالماضي مستعمل: «لَيْسَ».\nالمضارع غير مستعمل.\nالأمر غير مستعمل."
        report = read_verb_paradigm(source)
        self.assertEqual(report["readings"][0]["axis"]["candidates"], ["jamid"])
        self.assertEqual(report["readings"][0]["axis"]["status"], "LICENSED")
        self.assertEqual(report["world_truth"], "NOT_ESTABLISHED")
        self.assertFalse(report["nominal_semantics_consumed"])
        self.assertFalse(report["absence_from_text_is_negative_evidence"])
        self.assertTrue(verify_verb_paradigm(report, text=source)["valid"])
        removed = source.replace("المضارع غير مستعمل.\n", "")
        self.assertEqual(set(read_verb_paradigm(removed)["readings"][0]["axis"]["candidates"]), {"jamid", "partial"})
        self.assertFalse(verify_verb_paradigm(report, text=removed)["valid"])

    def test_all_three_positive_and_conflicting_or_empty_domains(self):
        all_three = "الماضي مستعمل: «زَلَمَ».\nالمضارع مستعمل: «يَزْلُمُ».\nالأمر مستعمل: «ازْلُمْ»."
        self.assertEqual(self.axis(all_three)["candidates"], ["full"])
        self.assertEqual(self.axis(all_three + "\nالأمر غير مستعمل.")["status"], "CONFLICT")
        empty = "الماضي غير مستعمل.\nالمضارع غير مستعمل.\nالأمر غير مستعمل."
        self.assertEqual(self.axis(empty)["status"], "OUT_OF_DOMAIN")

    def test_unparsed_qualifier_never_silently_disappears(self):
        source = "الماضي مستعمل: «زَلَمَ».\nالمضارع غير مستعمل.\nالأمر غير مستعمل.\nإلا في لهجة أخرى."
        axis = self.axis(source)
        self.assertEqual(axis["status"], "DEFER")
        self.assertFalse(axis["activated"])
        report = read_verb_paradigm("هذا نقل مختلف فيه.\nالفعل «ليس».\n" + source)
        self.assertFalse(report["readings"][0]["axis"]["activated"])

    def test_separate_source_blocks_are_not_merged(self):
        source = "الفعل «زلم».\nالماضي مستعمل: «زَلَمَ».\nالفعل «زلم».\nالمضارع مستعمل: «يَزْلُمُ»."
        a, b = read_verb_paradigm(source)["readings"]
        self.assertNotEqual(a["reading_id"], b["reading_id"])
        self.assertEqual(set(a["axis"]["candidates"]), {"jamid", "partial", "full"})
        self.assertEqual(set(b["axis"]["candidates"]), {"jamid", "partial", "full"})

    def test_mask_boolean_aliases_and_source_identity_are_rejected(self):
        for a, b in ((True, 0), (0, False), (-1, 0), (0, 8), ("1", 0)):
            with self.assertRaises(NabtError):
                availability_candidates(a, b)
        report = read_verb_paradigm("الفعل «زلم».\nالماضي مستعمل: «زَلَمَ».")
        changed = deepcopy(report)
        changed["readings"][0]["positive_mask"] = True
        self.assertFalse(verify_verb_paradigm(changed)["valid"])
        self.assertFalse(verify_verb_paradigm(report, scope="other")["valid"])


if __name__ == "__main__":
    unittest.main()
