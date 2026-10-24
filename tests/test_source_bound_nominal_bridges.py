"""Counterexamples for two source-bound bridges, not an Arabic accuracy sample."""

from copy import deepcopy
from hashlib import sha256
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import read_discourse, verify_discourse


def record(verse, form, pos, lemma, root, traits="MS", extra=""):
    suffix = "|" + extra if extra else ""
    return f"(1:{verse}:1:1)\t{form}\t{pos}\tSTEM|POS:{pos}|LEM:{lemma}|ROOT:{root}|{traits}{suffix}\n"


CONTEXT = {"entities": [{"id": "teacher", "name": "المعلم", "gender": "masculine",
                         "number": "singular", "kind": "person"}],
           "deixis": [{"form": "هذا", "entity_ids": ["teacher"]}]}
NOMINAL = (record(1, "kariymK", "N", "kariym", "krm") +
           record(2, "kariymN", "ADJ", "kariym", "krm") +
           record(3, "kariymK", "ADJ", "kariym", "krm"))
TEACHER = "".join(record(v, "muEal~im" + end, "N", "muEal~im", "Elm")
                  for v, end in ((4, "N"), (5, "K")))


class SourceBoundNominalBridgeTests(unittest.TestCase):
    def read(self, text="هذا كَرِيمٌ.", raw=NOMINAL, context=None, excluded=()):
        model = learn_qac_lexicon(("LOCATION\tFORM\tTAG\tFEATURES\n" + raw).encode(),
                                 excluded_verses=excluded, source_id="authored_bridge")
        context = deepcopy(CONTEXT if context is None else context)
        report = read_discourse(text, lexical_model=model, context=context, source_id="bridge_target")
        self.assertTrue(verify_discourse(report, lexical_model=model, context=context)["valid"])
        return report, model, context

    def correspondences(self, report):
        return [r["nominal_paradigm_correspondence"] for o in report["occurrences"]
                for r in o["readings"] if "nominal_paradigm_correspondence" in r]

    def test_direct_nominal_pair_preserves_both_pos_readings_and_source(self):
        report, _, _ = self.read()
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        witnesses = self.correspondences(report)
        self.assertTrue(witnesses)
        self.assertTrue(all(w["transferred_fields"] == ["construction"] for w in witnesses))
        self.assertTrue(all(w["recipient_tanwin_supports"] for w in witnesses))
        self.assertTrue(all(not w["semantic_equivalence_claimed"] for w in witnesses))
        noun_rows = [r for o in report["occurrences"] for r in o["readings"]
                     if r["lexical_features"].get("lemma") == "كَرِيم"]
        self.assertEqual({r["lexical_features"]["pos"] for r in noun_rows}, {"N", "ADJ"})
        self.assertTrue(all(r["construction"] == "inflected" for r in noun_rows))

    def test_unmarked_target_keeps_complete_person_candidates(self):
        report, _, _ = self.read(text="هذا كريم.")
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        rows = [r for o in report["occurrences"] for r in o["readings"]
                if r["lexical_features"].get("lemma") == "كَرِيم"]
        self.assertTrue(any(r.get("person_evidence") for r in rows))
        self.assertTrue(all(r["construction"] == "inflected" for r in rows))

    def test_donor_pair_withdrawal_and_exclusion_remove_the_bridge(self):
        for raw, excluded in ((NOMINAL.replace(record(3, "kariymK", "ADJ", "kariym", "krm"), ""), ()),
                              (NOMINAL, ("1:3",))):
            with self.subTest(excluded=excluded):
                report, _, _ = self.read(raw=raw, excluded=excluded)
                self.assertFalse(self.correspondences(report))
                self.assertNotEqual(report["status"], "LICENSED_DISCOURSE")

    def test_own_tanwin_not_borrowed_from_other_pos(self):
        raw = NOMINAL.replace("kariymK\tN\t", "kariymi\tN\t")
        report, _, _ = self.read(raw=raw)
        self.assertFalse(self.correspondences(report))
        self.assertNotEqual(report["status"], "LICENSED_DISCOURSE")

    def test_lemma_root_gender_number_and_derivation_are_not_transferred(self):
        original = record(1, "kariymK", "N", "kariym", "krm")
        variants = [record(1, "kariymK", "N", "kariym", "krm", traits="M"),
                    record(1, "kariymK", "N", "kariym", "krm", traits="FS"),
                    record(1, "kariymK", "N", "kariym", "klm"),
                    record(1, "kariymK", "N", "karam", "krm"),
                    record(1, "kariymK", "N", "kariym", "krm", extra="ACT|PCPL"),
                    record(1, "kariymK", "PN", "kariym", "krm")]
        for variant in variants:
            with self.subTest(variant=variant):
                report, _, _ = self.read(raw=NOMINAL.replace(original, variant))
                self.assertFalse(self.correspondences(report))

    def test_internal_vowels_and_shadda_need_direct_source_equality(self):
        original = record(1, "kariymK", "N", "kariym", "krm")
        for form in ("kuriymK", "kar~iymK"):
            report, _, _ = self.read(text="هذا كريم.", raw=NOMINAL.replace(
                original, record(1, form, "N", "kariym", "krm")))
            self.assertFalse(self.correspondences(report))
            self.assertNotEqual(report["status"], "LICENSED_DISCOURSE")

    def test_forged_pair_receipt_is_rejected_by_replay(self):
        report, model, context = self.read()
        forged = deepcopy(report)
        witness = self.correspondences(forged)[0]
        witness["donors"][0]["paired_terminal_supports"][0]["record_id"] = "0" * 64
        self.assertFalse(verify_discourse(forged, lexical_model=model, context=context)["valid"])

    def test_source_shadda_can_refine_an_unmarked_name(self):
        text = "الْمُعَلِّمُ كَرِيمٌ."
        report, _, _ = self.read(text, raw=TEACHER + NOMINAL)
        self.assertEqual(report["status"], "LICENSED_DISCOURSE")
        refs = [r for c in report["clauses"] for a in c["analyses"] for r in a["references"]
                if r.get("name_correspondence")]
        self.assertTrue(refs)
        self.assertTrue(all(r["bound_entity_id"] == "teacher" for r in refs))
        self.assertTrue(all(not r["name_correspondence"]["context_supplies_lexical_marks"] for r in refs))
        self.assertEqual(report["source_sha256"], sha256(text.encode()).hexdigest())

    def test_explicit_conflicting_name_is_not_normalized_away(self):
        context = deepcopy(CONTEXT)
        context["entities"][0]["name"] = "الْمُعَلَّم"
        report, _, _ = self.read("الْمُعَلِّمُ كَرِيمٌ.", raw=TEACHER + NOMINAL, context=context)
        self.assertFalse(report["claims"])

    def test_context_only_and_wrong_source_template_do_not_create_shadda(self):
        for raw in (NOMINAL, TEACHER.replace("muEal~im", "muEal~am") + NOMINAL):
            report, _, _ = self.read("الْمُعَلِّمُ كَرِيمٌ.", raw=raw)
            self.assertFalse(report["claims"])

    def test_same_written_names_remain_multiple_candidates(self):
        context = deepcopy(CONTEXT)
        context["entities"].append({**context["entities"][0], "id": "other_teacher"})
        report, _, _ = self.read("الْمُعَلِّمُ كَرِيمٌ.", raw=TEACHER + NOMINAL, context=context)
        self.assertFalse(report["claims"])
        refs = [r for c in report["clauses"] for a in c["analyses"] for r in a["references"]
                if r.get("name_correspondence")]
        self.assertTrue(refs)
        self.assertTrue(all(set(r["candidate_entity_ids"]) == {"teacher", "other_teacher"} for r in refs))

    def test_forged_name_reading_identity_is_rejected(self):
        report, model, context = self.read("الْمُعَلِّمُ كَرِيمٌ.", raw=TEACHER + NOMINAL)
        forged = deepcopy(report)
        ref = next(r for c in forged["clauses"] for a in c["analyses"] for r in a["references"]
                   if r.get("name_correspondence"))
        ref["name_correspondence"]["reading_id"] = "0" * 64
        self.assertFalse(verify_discourse(forged, lexical_model=model, context=context)["valid"])


if __name__ == "__main__":
    unittest.main()
