"""Reviewer-authored source diagnostics, not a blind Arabic benchmark.

Gold operations/cells below were specified from the fixed original passages and
independent web cross-checks. No production candidate builder or exported control
table is used to calculate the expected answer. The modules consume conditional
morphological analyses; success here does not establish those analyses from text.
"""
from copy import deepcopy
from pathlib import Path
from importlib.resources import files
import json
import unittest
from unittest.mock import patch

from nabt import classical_hamza as hamza
from nabt import classical_weak as weak
from nabt import classical_gemination as gem
from nabt import classical_boundary_affixes as boundary
from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[1]


def wf(cells, index, *, context="ordinary", position="ayn", origin="original", lexeme=""):
    return {"cells": cells, "index": index, "context": context,
            "position": position, "origin": origin, "lexeme": lexeme}


class IndependentSourceObligations(unittest.TestCase):
    def test_obligations_cover_exact_original_unimplemented_set(self):
        original = json.loads((ROOT / "evidence/arabic_completion_v5/rule_implementation_crosswalk.json").read_text())
        obligations = json.loads((ROOT / "evidence/arabic_completion_v6/independent_review/source_obligations_v1.json").read_text())
        expected = {r["rule_id"] for r in original["rows"]
                    if r["status"] == "not_implemented_by_this_extension"}
        cases = obligations["cases"]
        self.assertEqual(len(cases), 24)
        self.assertEqual({c["rule_id"] for c in cases}, expected)
        self.assertEqual(len({c["case_id"] for c in cases}), 24)

    def test_changed_original_source_bytes_cannot_issue_conditional_receipt(self):
        class AlteredResource:
            def __init__(self, original):
                self.original = original

            def joinpath(self, *names):
                return AlteredResource(self.original.joinpath(*names))

            def read_bytes(self):
                raw = self.original.read_bytes()
                if self.original.name.endswith(".txt"):
                    return bytes([raw[0] ^ 1]) + raw[1:]
                return raw

        real = files("nabt")
        probes = (
            (hamza, "HAMZA-FINAL-LONG", {"prefix": ["ب", "ن"], "glide": "ya", "alif_origin": "added", "suffix": []}),
            (weak, "WEAK-MOVE-TO-ALIF", wf([["ق", "a"], ["و", "a"], ["ل", "a"]], 1)),
            (gem, "ASSIM-NUN-B-BLOCKED-TEXT", {"left": ["ن", "s"], "right": ["ب", "a"], "connection": "within_word"}),
            (boundary, "MUGHNI-ANA-BOUNDARY", {"segments": ["ء", "a", "ن", "a:"], "start": "ibtida", "end": "wasl", "analysis": "speaker_pronoun", "profile": "majority"}),
        )
        for module, rule_id, frame in probes:
            with self.subTest(rule_id=rule_id), patch.object(module, "files", lambda _: AlteredResource(real)):
                with self.assertRaises(NabtError) as caught:
                    module.evaluate(rule_id, frame)
                self.assertEqual((caught.exception.code, caught.exception.status),
                                 ("INSTALLED_CONTRACT_FAILED", "DEFER"))


class IndependentHamzaLaws(unittest.TestCase):
    def outputs(self, rid, frame):
        result = hamza.evaluate(rid, frame)
        self.assertFalse(result["premises_established"])
        self.assertFalse(result["language_license_granted"])
        self.assertEqual(result["input_frame"], frame)
        self.assertTrue(result["source_spans"])
        return [a["morphophonemes"] for a in result["alternatives"]]

    def test_interrogative_article_preserves_both_source_alternatives(self):
        for boundary in ("ibtida", "wasl"):
            with self.subTest(boundary=boundary):
                self.assertEqual(self.outputs("HAMZA-INTERROGATIVE-AL", {
                    "tail": ["ر", "ج", "ل"], "boundary": boundary}), [
                        ["ء", "ا", "ل", "ر", "ج", "ل"],
                        ["ء", "HAMZA_TASHIL", "ل", "ر", "ج", "ل"]])

    def test_final_glide_requires_added_alif_and_real_final_position(self):
        frame = {"prefix": ["ب", "ن"], "glide": "ya", "alif_origin": "added", "suffix": []}
        self.assertEqual(self.outputs("HAMZA-FINAL-LONG", frame), [["ب", "ن", "ا", "ء"]])
        for change in ({"alif_origin": "radical"}, {"suffix": ["ن"]}):
            with self.subTest(change=change):
                self.assertEqual(self.outputs("HAMZA-FINAL-LONG", dict(frame, **change)), [])
        unknown = hamza.evaluate("HAMZA-FINAL-LONG", dict(frame, alif_origin="unknown"))
        self.assertEqual(unknown["status"], "DEFER")

    def test_active_participle_must_follow_verb_illal(self):
        frame = {"first": "ب", "glide": "ya", "last": "ع", "verb_medial": "changed_to_alif"}
        self.assertEqual(self.outputs("HAMZA-ACTIVE-PARTICIPLE", frame), [["ب", "ا", "ء", "ع"]])
        retained = {"first": "ع", "glide": "waw", "last": "ر", "verb_medial": "retained"}
        self.assertEqual(self.outputs("HAMZA-ACTIVE-PARTICIPLE", retained), [])

    def test_plural_origin_distinguishes_qalaid_maayish_and_nonlong_qasawir(self):
        frame = {"singular": ["ق", "ل", "ا", "د", "ة"],
                 "singular_long_origin": "added_long", "plural_template": "mafail"}
        self.assertEqual(self.outputs("HAMZA-BROKEN-PLURAL", frame), [["ق", "ل", "ا", "ء", "د"]])
        for singular, origin in ((["م", "ع", "ي", "ش", "ة"], "radical_long"),
                                 (["ق", "س", "و", "ر", "ة"], "nonlong")):
            with self.subTest(singular=singular):
                self.assertEqual(self.outputs("HAMZA-BROKEN-PLURAL", {
                    "singular": singular, "singular_long_origin": origin,
                    "plural_template": "mafail"}), [])

    def test_two_glides_exclude_tawawis_long_template(self):
        self.assertEqual(self.outputs("HAMZA-TWO-GLIDES", {
            "underlying_plural": ["ء", "و", "ا", "و", "ل"],
            "plural_template": "mafail"}), [["ء", "و", "ا", "ء", "ل"]])
        self.assertEqual(self.outputs("HAMZA-TWO-GLIDES", {
            "underlying_plural": ["ط", "و", "ا", "و", "ي", "س"],
            "plural_template": "mafail_long"}), [])

    def test_named_command_preserves_minor_form_without_generalized_deletion(self):
        self.assertEqual(self.outputs("HAMZA-LEXICAL-COMMAND", {
            "root": ["ء", "ك", "ل"], "profile": "all_attested"}),
            [["ك", "ل"], ["ء", "و", "ك", "ل"]])
        outside = hamza.evaluate("HAMZA-LEXICAL-COMMAND", {
            "root": ["ء", "س", "ر"], "profile": "all_attested"})
        self.assertEqual(outside["alternatives"], [])
        self.assertEqual(outside["status"], "DEFER")

    def test_hamza_rejects_caller_authority_and_nonatomic_spelling(self):
        good = {"root": ["ء", "ك", "ل"], "profile": "all_attested"}
        for bad in (dict(good, source_verified=True), dict(good, root=["أ", "ك", "ل"]),
                    dict(good, root=[True, "ك", "ل"])):
            with self.subTest(bad=bad), self.assertRaises(NabtError):
                hamza.evaluate("HAMZA-LEXICAL-COMMAND", bad)


class IndependentWeakLaws(unittest.TestCase):
    def outputs(self, rid, frame):
        saved = deepcopy(frame)
        result = weak.evaluate(rid, frame)
        self.assertFalse(result["application_established"])
        self.assertFalse(result["free_text_analysis"])
        self.assertEqual(result["input"], saved)
        self.assertEqual(frame, saved)
        self.assertTrue(result["source_spans"])
        return [a["cells"] for a in result["alternatives"]]

    def test_initial_waw_deletes_before_kasra_but_not_yawjal(self):
        frame = wf([["ي", "a"], ["و", "0"], ["ع", "i"], ["د", "u"]], 1,
                   context="simple_imperfect", position="fa")
        self.assertEqual(self.outputs("WEAK-INITIAL-WAW", frame),
                         [[["ي", "a"], ["ع", "i"], ["د", "u"]]])
        yawjal = wf([["ي", "a"], ["و", "0"], ["ج", "a"], ["ل", "u"]], 1,
                    context="simple_imperfect", position="fa")
        self.assertEqual(self.outputs("WEAK-INITIAL-WAW", yawjal), [])

    def test_open_exception_is_root_specific(self):
        frame = wf([["ي", "a"], ["و", "0"], ["ط", "a"], ["ء", "u"]], 1,
                   context="simple_imperfect", position="fa")
        self.assertEqual(self.outputs("WEAK-INITIAL-OPEN-EXCEPTION", frame),
                         [[["ي", "a"], ["ط", "a"], ["ء", "u"]]])
        frame["cells"][2] = ["ج", "a"]
        frame["cells"][3] = ["ل", "u"]
        self.assertEqual(self.outputs("WEAK-INITIAL-OPEN-EXCEPTION", frame), [])

    def test_sakin_waw_after_kasra_replaces_only_selected_carrier(self):
        frame = wf([["م", "i"], ["و", "0"], ["ز", "a"], ["ا", "0"], ["ن", "u"]], 1)
        self.assertEqual(self.outputs("WEAK-WAW-TO-YA", frame),
                         [[["م", "i"], ["ي", "0"], ["ز", "a"], ["ا", "0"], ["ن", "u"]]])
        frame["cells"][1][1] = "a"
        self.assertEqual(self.outputs("WEAK-WAW-TO-YA", frame), [])

    def test_ya_after_damma_singular_and_ful_plural_have_different_operations(self):
        frame = wf([["م", "u"], ["ي", "0"], ["ق", "i"], ["ن", "u"]], 1, context="singular")
        self.assertEqual(self.outputs("WEAK-YA-TO-WAW", frame),
                         [[["م", "u"], ["و", "0"], ["ق", "i"], ["ن", "u"]]])
        plural = wf([["ب", "u"], ["ي", "0"], ["ض", "u"]], 1, context="ful_plural")
        self.assertEqual(self.outputs("WEAK-YA-TO-WAW", plural),
                         [[["ب", "i"], ["ي", "0"], ["ض", "u"]]])

    def test_move_to_alif_original_vowel_and_follower_blockers(self):
        frame = wf([["ق", "a"], ["و", "a"], ["ل", "a"]], 1)
        self.assertEqual(self.outputs("WEAK-MOVE-TO-ALIF", frame),
                         [[["ق", "a"], ["ا", "0"], ["ل", "a"]]])
        self.assertEqual(self.outputs("WEAK-MOVE-TO-ALIF", dict(frame, origin="transferred")), [])
        for follower in ([["ل", "0"]], [["ا", "0"]], [["ي", "0"], ["ي", "a"]]):
            with self.subTest(follower=follower):
                bad = wf([["ر", "a"], ["ي", "a"], *follower], 1,
                         position="ayn" if follower == [["ل", "0"]] else "lam")
                self.assertEqual(self.outputs("WEAK-MOVE-TO-ALIF", bad), [])

    def test_afal_quality_blocks_medial_ilal(self):
        frame = wf([["ع", "a"], ["و", "i"], ["ر", "a"]], 1, context="afal_quality")
        self.assertEqual(self.outputs("WEAK-AFWAL-BLOCK", frame), [frame["cells"]])
        self.assertEqual(self.outputs("WEAK-MOVE-TO-ALIF", frame), [])

    def test_reciprocal_waw_is_kept_while_ya_changes(self):
        cells = [["ا", "i"], ["ش", "0"], ["ت", "a"], ["و", "a"], ["ر", "u"]]
        frame = wf(cells, 3, context="reciprocal_iftial")
        self.assertEqual(self.outputs("WEAK-IFTIAL-RECIPROCAL", frame), [cells])
        frame = wf([["ا", "i"], ["ب", "0"], ["ت", "a"], ["ي", "a"], ["ع", "u"]], 3,
                   context="reciprocal_iftial")
        self.assertEqual(self.outputs("WEAK-IFTIAL-RECIPROCAL", frame),
                         [[["ا", "i"], ["ب", "0"], ["ت", "a"], ["ا", "0"], ["ع", "u"]]])

    def test_two_eligible_positions_change_last_only(self):
        frame = wf([["ح", "a"], ["ي", "a"], ["ي", "a"]], 1)
        self.assertEqual(self.outputs("WEAK-TWO-ELIGIBLE", frame),
                         [[["ح", "a"], ["ي", "a"], ["ا", "0"]]])
        counterfeit = dict(frame, context="recorded_reverse", lexeme="غاية")
        self.assertEqual(self.outputs("WEAK-TWO-ELIGIBLE", counterfeit), [])

    def test_nominal_suffix_keeps_medial_weak(self):
        frame = wf([["ج", "a"], ["و", "a"], ["ل", "a"], ["ا", "0"], ["ن", "u"]], 1,
                   context="nominal_augment", lexeme="جولان")
        self.assertEqual(self.outputs("WEAK-NOMINAL-SUFFIX-BLOCK", frame), [frame["cells"]])
        self.assertEqual(self.outputs("WEAK-MOVE-TO-ALIF", frame), [])

    def test_vowel_transfer_has_sound_predecessor_and_class_exclusions(self):
        frame = wf([["ي", "a"], ["ق", "0"], ["و", "u"], ["م", "u"]], 2, context="verb")
        self.assertEqual(self.outputs("WEAK-VOWEL-TRANSFER", frame),
                         [[["ي", "a"], ["ق", "u"], ["و", "0"], ["م", "u"]]])
        for context in ("exclamation", "geminate", "weak_final"):
            with self.subTest(context=context):
                self.assertEqual(self.outputs("WEAK-VOWEL-TRANSFER", dict(frame, context=context)), [])
        frame["cells"][1] = ["ي", "0"]
        self.assertEqual(self.outputs("WEAK-VOWEL-TRANSFER", frame), [])

    def test_boolean_index_and_unknown_fields_do_not_become_evidence(self):
        frame = wf([["ق", "a"], ["و", "a"], ["ل", "a"]], 1)
        for bad in (dict(frame, index=True), dict(frame, source_verified=True)):
            with self.subTest(bad=bad), self.assertRaises(NabtError):
                weak.evaluate("WEAK-MOVE-TO-ALIF", bad)


def gf(prefix, first, second, *, suffix=None, context="command", dialect="attested_union"):
    return {"prefix": prefix, "first": first, "second": second,
            "suffix": [] if suffix is None else suffix, "context": context, "dialect": dialect}


class IndependentGeminationLaws(unittest.TestCase):
    def result(self, rid, frame):
        saved = deepcopy(frame)
        result = gem.evaluate(rid, frame)
        self.assertFalse(result["premises_established"])
        self.assertFalse(result["word_attestation_established"])
        self.assertEqual(result["original_frame"], saved)
        self.assertEqual(frame, saved)
        return result

    def test_voweled_final_contracts_identical_radicals_only(self):
        frame = gf([["ر", "a"]], ["د", "a"], ["د", "a"], context="ordinary")
        alts = self.result("GEM-VOWELED-FINAL", frame)["alternatives"]
        self.assertEqual([a["cells"] for a in alts], [[["ر", "a"], ["د", "s"], ["د", "a"]]])
        self.assertEqual(self.result("GEM-VOWELED-FINAL", dict(frame, second=["ب", "a"]))["alternatives"], [])

    def test_jussive_direct_wasl_changes_after_transfer_only(self):
        frame = gf([["ٱ", "u"], ["ر", "s"]], ["د", "u"], ["د", "s"], dialect="tamim")
        alts = self.result("GEM-JUSSIVE-VARIANTS", frame)["alternatives"]
        self.assertEqual([a["cells"] for a in alts], [
            [["ر", "u"], ["د", "s"], ["د", "a"]],
            [["ر", "u"], ["د", "s"], ["د", "u"]]])
        self.assertTrue(all(a["initial_wasl_removed"] for a in alts))
        hijaz = self.result("GEM-JUSSIVE-VARIANTS", dict(frame, dialect="hijaz"))["alternatives"]
        self.assertEqual([a["cells"] for a in hijaz], [[
            ["ٱ", "u"], ["ر", "s"], ["د", "u"], ["د", "s"]]])

    def test_jussive_distant_wasl_is_not_erased(self):
        frame = gf([["ٱ", "i"], ["س", "s"], ["ت", "a"], ["ع", "s"]],
                   ["د", "i"], ["د", "s"], dialect="tamim")
        alts = self.result("GEM-JUSSIVE-VARIANTS", frame)["alternatives"]
        self.assertTrue(alts)
        for alt in alts:
            self.assertEqual(alt["cells"][:4], [["ٱ", "i"], ["س", "s"], ["ت", "a"], ["ع", "i"]])
            self.assertFalse(alt["initial_wasl_removed"])

    def test_jussive_vowel_harmony_uses_effective_preceding_vowel(self):
        # In اجترر the preceding ت is already open; its vowel is not replaced
        # by the first ر's original kasra. The reported harmony branch follows ت.
        frame = gf([["ٱ", "i"], ["ج", "s"], ["ت", "a"]],
                   ["ر", "i"], ["ر", "s"], dialect="tamim")
        alts = self.result("GEM-JUSSIVE-VARIANTS", frame)["alternatives"]
        self.assertEqual([a["cells"] for a in alts], [[
            ["ٱ", "i"], ["ج", "s"], ["ت", "a"], ["ر", "s"], ["ر", "a"]]])
        long_alif = gf([["م", "a"], ["ا", "s"]], ["د", "i"], ["د", "s"], dialect="tamim")
        self.assertEqual([a["cells"] for a in self.result("GEM-JUSSIVE-VARIANTS", long_alif)["alternatives"]],
                         [[["م", "a"], ["ا", "s"], ["د", "s"], ["د", "a"]]])

    def test_feminine_nun_preserves_bakr_without_inventing_its_vowel(self):
        frame = gf([["ٱ", "u"], ["ر", "s"]], ["د", "u"], ["د", "s"],
                   suffix=[["ن", "a"]], context="feminine")
        alts = self.result("GEM-FEMININE-SUFFIX", frame)["alternatives"]
        self.assertEqual([a["operation"] for a in alts], ["split", "bakr_contraction_unvocalized"])
        self.assertIsNone(alts[1]["cells"])
        self.assertFalse(alts[1]["surface_complete"])
        self.assertEqual(self.result("GEM-FEMININE-SUFFIX", dict(frame, suffix=[]))["alternatives"], [])

    def test_exclamation_and_hallumma_do_not_share_an_operation(self):
        afil = gf([["أ", "a"], ["ح", "s"]], ["ب", "i"], ["ب", "s"], context="exclamation")
        self.assertEqual([a["operation"] for a in self.result("GEM-EXCLAMATION", afil)["alternatives"]], ["split"])
        hallumma = gf([["ه", "a"], ["ل", "u"]], ["م", "s"], ["م", "a"], context="hallumma")
        self.assertEqual([a["operation"] for a in self.result("GEM-EXCLAMATION", hallumma)["alternatives"]], ["retain_hallumma"])

    def test_nun_before_ba_requires_sukun_connection_and_real_ba(self):
        frame = {"left": ["ن", "s"], "right": ["ب", "a"], "connection": "word_boundary_wasl"}
        result = self.result("ASSIM-NUN-B-BLOCKED-TEXT", frame)
        self.assertEqual([a["cells"] for a in result["alternatives"]], [[["م", "s"], ["ب", "a"]]])
        self.assertTrue(result["textual_discrepancy_retained"])
        self.assertIn("alfiyya", {s["source_id"] for s in result["source_spans"]})
        self.assertIn("sibawayhi", {s["source_id"] for s in result["source_spans"]})
        for change in ({"right": ["ي", "a"]}, {"left": ["ن", "a"]}, {"connection": "word_boundary_waqf"}):
            with self.subTest(change=change):
                self.assertEqual(self.result("ASSIM-NUN-B-BLOCKED-TEXT", dict(frame, **change))["alternatives"], [])


class IndependentBoundaryLaws(unittest.TestCase):
    def result(self, rid, frame):
        saved = deepcopy(frame)
        result = boundary.evaluate(rid, frame)
        self.assertFalse(result["premises_established"])
        self.assertFalse(result["language_license"])
        self.assertEqual(result["input"], saved)
        self.assertEqual(frame, saved)
        return result

    def test_weak_command_shortens_final_vowel_in_2ms_only(self):
        frame = {"segments": ["i", "ر", "م", "i:"], "start": "ibtida", "end": "wasl",
                 "final_radical": "ي", "person": "2ms", "suffix": "none"}
        alts = self.result("CMD-WEAK-DELETE", frame)["alternatives"]
        self.assertEqual([a["segments"] for a in alts], [["i", "ر", "م", "i"]])
        for person in ("2fs", "2dual", "2mp", "2fp"):
            with self.subTest(person=person):
                self.assertEqual(self.result("CMD-WEAK-DELETE", dict(frame, person=person))["alternatives"], [])
        self.assertEqual(self.result("CMD-WEAK-DELETE", dict(frame, suffix="subject"))["alternatives"], [])

    def light(self, segments, shape, *, profile="both", end="waqf", nun_kind="light", following="none"):
        return {"segments": segments, "start": "ibtida", "end": end, "shape": shape,
                "profile": profile, "nun_kind": nun_kind, "following": following}

    def test_light_nun_singular_fatha_becomes_alif_and_heavy_does_not(self):
        frame = self.light(["ض", "ر", "i", "ب", "a", "ن"], "singular_open")
        alts = self.result("AFFIX-LIGHT-NUN-PAUSE", frame)["alternatives"]
        self.assertEqual([a["segments"] for a in alts], [["ض", "ر", "i", "ب", "a:"]])
        for nun in ("heavy", "feminine"):
            self.assertEqual(self.result("AFFIX-LIGHT-NUN-PAUSE", dict(frame, nun_kind=nun))["alternatives"], [])

    def test_light_nun_deleted_subject_is_restored(self):
        frame = self.light(["ض", "ر", "i", "ب", "u", "ن"], "deleted_waw_command")
        self.assertEqual([a["segments"] for a in self.result("AFFIX-LIGHT-NUN-PAUSE", frame)["alternatives"]],
                         [["ض", "ر", "i", "ب", "u:"]])

    def test_light_nun_preserves_khalil_yunus_and_attribution(self):
        frame = self.light(["i", "خ", "ش", "a", "ي", "i", "ن"], "retained_ya_command")
        alts = self.result("AFFIX-LIGHT-NUN-PAUSE", frame)["alternatives"]
        self.assertEqual([a["segments"] for a in alts],
                         [["i", "خ", "ش", "a", "ي"], ["i", "خ", "ش", "a", "ي", "i:"]])
        self.assertEqual([a["evidence_kind"] for a in alts], ["reported_khalil", "reported_yunus"])
        indicative = self.light(["ت", "a", "ض", "ر", "i", "ب", "u", "ن"], "deleted_waw_indicative")
        alts = self.result("AFFIX-LIGHT-NUN-PAUSE", indicative)["alternatives"]
        self.assertEqual([a["evidence_kind"] for a in alts], ["reported_khalil", "source_analogical_yunus"])
        self.assertEqual([a["segments"] for a in alts], [
            ["ت", "a", "ض", "ر", "i", "ب", "u:", "ن"],
            ["ت", "a", "ض", "ر", "i", "ب", "u:"]])

    def test_ana_boundary_distinguishes_majority_minority_and_particle(self):
        frame = {"segments": ["ء", "a", "ن", "a:"], "start": "ibtida", "end": "wasl",
                 "analysis": "speaker_pronoun", "profile": "both"}
        self.assertEqual([a["segments"] for a in self.result("MUGHNI-ANA-BOUNDARY", frame)["alternatives"]],
                         [["ء", "a", "ن", "a"], ["ء", "a", "ن"]])
        self.assertEqual(self.result("MUGHNI-ANA-BOUNDARY", dict(frame, analysis="masdariyya_particle"))["alternatives"], [])
        pause = dict(frame, end="waqf", profile="majority")
        self.assertEqual([a["segments"] for a in self.result("MUGHNI-ANA-BOUNDARY", pause)["alternatives"]],
                         [["ء", "a", "ن", "a:"]])
        self.assertEqual(self.result("MUGHNI-ANA-BOUNDARY", dict(pause, profile="minority_sukun"))["alternatives"], [])

    def test_unsupported_union_member_remains_visible(self):
        ana = {"segments": ["ء", "a", "ن", "a:"], "start": "ibtida", "end": "waqf",
               "analysis": "speaker_pronoun", "profile": "both"}
        dual = self.light(["ت", "a", "ض", "ر", "i", "ب", "a:", "ن", "i"], "indicative_dual")
        for rule_id, frame in (("MUGHNI-ANA-BOUNDARY", ana), ("AFFIX-LIGHT-NUN-PAUSE", dual)):
            with self.subTest(rule_id=rule_id):
                result = self.result(rule_id, frame)
                self.assertTrue(result["alternatives"])
                self.assertTrue(result["unresolved_profiles"])
                self.assertFalse(result["alternatives_complete_within_requested_profile"])


if __name__ == "__main__":
    unittest.main()
