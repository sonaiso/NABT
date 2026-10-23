"""Authored counterexamples for source-bound person/attachment projection.

The miniature QAC-format records are constructed fixtures, not evaluation
gold or quotations. Expected Arabic analyses are written independently of
the installed table and its implementation.
"""

from copy import deepcopy
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.errors import NabtError
from nabt.person_evidence import person_candidates, person_catalog


def corpus(*words):
    lines = ["LOCATION\tFORM\tTAG\tFEATURES"]
    for verse, segments in enumerate(words, 1):
        for segment, (form, tag, features) in enumerate(segments, 1):
            lines.append(f"(1:{verse}:1:{segment})\t{form}\t{tag}\t{features}")
    return ("\n".join(lines) + "\n").encode()


def verb(form, person="3MS", aspect="IMPF", root="ktb", lemma="kataba", extra=""):
    return (form, "V", f"STEM|POS:V|{aspect}|LEM:{lemma}|ROOT:{root}|{person}" + extra)


def pronoun(form, person):
    return (form, "PRON", "SUFFIX|PRON:" + person)


def emphasis(form="n~a"):
    return (form, "EMPH", "SUFFIX|EMPH")


def triples(rows):
    return {tuple(row["person_profile"][name] for name in ("person", "gender", "number"))
            for row in rows if row["person_profile"] is not None}


class PersonEvidenceTests(unittest.TestCase):
    def read(self, text, *words, excludes=()):
        return person_candidates(text, lexical_model=learn_qac_lexicon(corpus(*words), excluded_verses=excludes))

    def test_no_prefix_authority_without_a_lexical_family(self):
        for surface in ("يكتب", "تكتب", "أكتب", "نكتب", "يكتبون", "كتابك"):
            self.assertEqual(person_candidates(surface), [])
        self.assertEqual(self.read("تكتب", [verb("takotubu", "3MS")]), [])

    def test_ta_retains_second_masculine_and_third_feminine(self):
        rows = self.read("تَكْتُبُ", [verb("yakotubu")])
        self.assertEqual(triples(rows), {(2, 0, 0), (3, 1, 0)})
        self.assertTrue(all(row["family"] == "plain" for row in rows))
        self.assertTrue(all(row["supports"] for row in rows))

    def test_first_person_gender_unspecified_and_hamza_not_bare_alif(self):
        self.assertEqual(triples(self.read("أَكْتُبُ", [verb("yakotubu")])), {(1, 2, 0)})
        rows = self.read("نَكْتُبُ", [verb("yakotubu")])
        self.assertEqual(triples(rows), {(1, 2, 2)})
        self.assertTrue(all(row["gender_name"] is None for row in rows))
        self.assertEqual(self.read("اكتب", [verb("yakotubu")]), [])

    def test_hamza_collision_is_not_silently_repaired(self):
        rows = self.read("أأكل", [verb("ya>okulu", root="Akl", lemma=">akala")])
        self.assertEqual(rows, [])

    def test_full_dual_family_has_three_ta_profiles(self):
        words = [verb("yakotuba", "3MD"), pronoun("Ani", "3MD")]
        self.assertEqual(triples(self.read("تَكْتُبَانِ", words)), {(2, 0, 1), (2, 1, 1), (3, 1, 1)})
        self.assertEqual(triples(self.read("يَكْتُبَا", words)), {(3, 0, 1)})
        self.assertEqual(self.read("أكتبان", words), [])

    def test_five_verb_deletion_keeps_person_and_no_nun_span(self):
        words = [verb("yakotubu", "3MP"), pronoun("wna", "3MP")]
        rows = self.read("تَكْتُبُوا", words)
        self.assertEqual(triples(rows), {(2, 0, 2)})
        for row in rows:
            self.assertEqual(row["class_candidates"], [10])
            self.assertEqual(row["possible_cases"], [0, 3])
            nun, = [n for n in row["nun_readings"] if n["kind"] == "five_verb_raf"]
            self.assertEqual(nun["realization"], "deleted")
            self.assertIsNone(nun["span"])
        self.assertEqual(self.read("تكتبوا", words, excludes=("1:1",)), [])

    def test_five_verb_requires_complete_vocalic_and_person_geometry(self):
        bad = [verb("yakotuba", "3MP"), pronoun("wna", "3MP")]
        self.assertEqual(self.read("يكتبون", bad), [])
        singular = [verb("yakotubu")]
        self.assertEqual(self.read("يكتبون", singular), [])
        self.assertEqual(self.read("تكتبين", singular), [])

    def test_feminine_nun_is_distinct_from_five_verb_nun(self):
        words = [verb("yakotubo", "3FP"), pronoun("na", "3FP")]
        rows = self.read("تَكْتُبْنَ", words)
        self.assertEqual(triples(rows), {(2, 1, 2)})
        self.assertTrue(all(row["construction"] == "built" and not row["class_candidates"] for row in rows))
        self.assertEqual({n["kind"] for row in rows for n in row["nun_readings"]}, {"feminine_subject"})

    def test_radical_and_inflection_nuns_stay_distinct(self):
        words = [verb("yasokunu", "3MP", root="skn", lemma="sakana"), pronoun("wna", "3MP")]
        rows = self.read("يَسْكُنُونَ", words)
        self.assertTrue(rows)
        for row in rows:
            radical, inflection = row["nun_readings"]
            self.assertEqual((radical["surface"], inflection["surface"]), ("نُ", "نَ"))
            self.assertLess(radical["span"]["byte_end"], inflection["span"]["byte_start"])

    def test_separate_pronouns_keep_missing_gender_evidence(self):
        self.assertEqual(triples(person_candidates("أنت")), {(2, 0, 0), (2, 1, 0)})
        self.assertEqual(triples(person_candidates("أَنْتِ")), {(2, 1, 0)})
        self.assertEqual(triples(person_candidates("هما")), {(3, 0, 1), (3, 1, 1)})
        self.assertEqual(triples(person_candidates("أنا")), {(1, 2, 0)})

    def test_object_suffix_and_bare_valency_need_independent_full_host(self):
        base = [verb("Daraba", aspect="PERF", root="Drb", lemma="Daraba")]
        attached = [*base, pronoun("hu", "3MS")]
        rows = self.read("ضَرَبَهُ", base, attached)
        self.assertTrue(rows)
        self.assertTrue(all(r["attached_pronouns"][0]["attachment_candidates"] == ["verbal_object"] for r in rows))
        self.assertTrue(all(r["valency_witnesses"] for r in self.read("ضَرَبَ", base, attached)))
        withdrawn = self.read("ضَرَبَهُ", attached)
        self.assertTrue(withdrawn)
        self.assertTrue(all(not r["valency_witnesses"] and not r["attached_pronouns"][0]["licensed"] for r in withdrawn))

    def test_duplicate_source_attestations_do_not_create_new_person_readings(self):
        base = [verb("Daraba", aspect="PERF", root="Drb", lemma="Daraba")]
        attached = [*base, pronoun("hu", "3MS")]
        single = self.read("ضَرَبَهُ", base, attached)
        many = self.read("ضَرَبَهُ", base, *([attached] * 40))
        self.assertEqual(len(single), len(many))
        self.assertEqual(triples(single), triples(many))
        self.assertTrue(all(len(row["supports"]) <= 8 for row in many))

    def test_taa_subject_is_not_an_object_or_a_bare_verb_person(self):
        words = [verb("katabo", person="1S", aspect="PERF"), pronoun("tu", "1S")]
        rows = self.read("كَتَبْتُ", words)
        self.assertEqual(triples(rows), {(1, 2, 0)})
        self.assertTrue(all(not row["valency_witnesses"] for row in rows))
        self.assertEqual(self.read("كتب", words), [])

    def test_unmarked_kaf_preserves_both_correlated_suffix_profiles(self):
        base = [verb("Daraba", aspect="PERF", root="Drb", lemma="Daraba")]
        attached = [*base, pronoun("ka", "2MS")]
        rows = self.read("ضربك", base, attached)
        self.assertEqual({tuple(r["attached_pronouns"][0]["person_profile"][k]
                               for k in ("person", "gender", "number")) for r in rows}, {(2, 0, 0), (2, 1, 0)})
        feminine = self.read("ضَرَبَكِ", base, attached)
        self.assertTrue(feminine)
        self.assertTrue(all(r["attached_pronouns"][0]["person_profile"]["gender"] == 1 for r in feminine))

    def test_haa_allomorph_vowel_is_not_freely_changed_after_same_host(self):
        base = [verb("Daraba", aspect="PERF", root="Drb", lemma="Daraba")]
        attached = [*base, pronoun("hu", "3MS")]
        self.assertTrue(self.read("ضَرَبَهُ", base, attached))
        self.assertEqual(self.read("ضَرَبَهِ", base, attached), [])

    def test_nominal_possessive_is_a_conditional_attachment_not_world_ownership(self):
        a = [("kitaAbN", "N", "STEM|POS:N|LEM:kitaAb|ROOT:ktb|MS|NOM")]
        b = [("kitaAbK", "N", "STEM|POS:N|LEM:kitaAb|ROOT:ktb|MS|GEN")]
        attached = [("kitaAbu", "N", "STEM|POS:N|LEM:kitaAb|ROOT:ktb|MS"), pronoun("ka", "2MS")]
        rows = self.read("كِتَابُكَ", a, b, attached)
        self.assertTrue(rows)
        self.assertTrue(all(r["attached_pronouns"][0]["attachment_candidates"] == ["possessive"] for r in rows))
        self.assertTrue(all(not r["valency_witnesses"] for r in rows))

    def test_nominal_features_survive_the_person_bridge_without_inventing_unknowns(self):
        rows = self.read("كاتبة", [("kaAtibapN", "N", "STEM|POS:N|LEM:kaAtibap|ROOT:ktb|FS")])
        self.assertEqual(triples(rows), {(3, 1, 0)})
        partial = self.read("كاتب", [("kaAtibN", "N", "STEM|POS:N|LEM:kaAtib|ROOT:ktb|M")])
        self.assertTrue(partial)
        self.assertTrue(all(r["person_profile"] is None and r["gender_name"] == "masculine" and
                            r["number_name"] is None for r in partial))

    def test_protective_nun_needs_one_source_partition_and_external_base(self):
        base = [verb("Daraba", aspect="PERF", root="Drb", lemma="Daraba")]
        attached = [*base, pronoun("niy", "1S")]
        rows = self.read("ضَرَبَنِي", base, attached)
        self.assertTrue(rows)
        for row in rows:
            nun, = [n for n in row["nun_readings"] if n["kind"] == "protective"]
            self.assertEqual(nun["surface"], "نِ")
            self.assertEqual("ضَرَبَنِي".encode()[nun["span"]["byte_start"]:nun["span"]["byte_end"]].decode(), "نِ")
        self.assertFalse(any(n["kind"] == "protective" for r in self.read("ضَرَبَنِي", attached)
                             for n in r["nun_readings"]))

    def test_source_root_or_lemma_mismatch_cannot_supply_external_host(self):
        wrong = [verb("Daraba", aspect="PERF", root="Drb", lemma="OTHER")]
        attached = [verb("Daraba", aspect="PERF", root="Drb", lemma="Daraba"), pronoun("niy", "1S")]
        rows = self.read("ضَرَبَنِي", wrong, attached)
        self.assertTrue(rows)
        self.assertTrue(all(not row["valency_witnesses"] for row in rows))

    def test_direct_emphasis_has_full_host_and_actual_separate_nun_positions(self):
        base = [verb("yasokunu", root="skn", lemma="sakana")]
        attached = [verb("yasokuna", root="skn", lemma="sakana"), emphasis()]
        rows = self.read("يَسْكُنَنَّ", base, attached)
        self.assertTrue(rows)
        for row in rows:
            radical, emph = row["nun_readings"]
            self.assertEqual((radical["surface"], emph["surface"]), ("نَ", "نَّ"))
            self.assertEqual(emph["directness"], "direct")
            self.assertEqual(row["construction"], "built")
            self.assertEqual(row["class_candidates"], [])
        residual = self.read("يَسْكُنَنَّ", attached)
        self.assertTrue(all(r["construction"] is None for r in residual))
        self.assertTrue(all(n.get("directness") == "unknown" for r in residual for n in r["nun_readings"] if n["kind"] == "emphasis"))

    def test_written_adjacency_does_not_license_direct_emphasis(self):
        base = [verb("yakotubu", "3MP"), pronoun("wna", "3MP")]
        missing_subject = [verb("yakotuba", "3MP"), emphasis()]
        rows = self.read("يَكْتُبَنَّ", base, missing_subject)
        self.assertTrue(rows)
        self.assertTrue(all(r["construction"] is None for r in rows))
        self.assertFalse(any(n.get("directness") == "direct" for r in rows for n in r["nun_readings"]))

    def test_dual_alif_separation_does_not_claim_deleted_nun_case(self):
        base = [verb("yakotuba", "3MD"), pronoun("Ani", "3MD")]
        attached = [verb("yakotuba", "3MD"), pronoun("A", "3MD"), emphasis("n~i")]
        rows = self.read("يَكْتُبَانِّ", base, attached)
        self.assertTrue(rows)
        self.assertTrue(any(n.get("directness") == "separated" for r in rows for n in r["nun_readings"]))
        self.assertTrue(all(not r["class_candidates"] and not r["possible_cases"] for r in rows))

    def test_emphatic_alif_does_not_create_a_visible_nun(self):
        rows = self.read("يَكْتُبَا", [verb("yakotubu")], [verb("yakotuba"), emphasis("A")])
        self.assertTrue(rows)
        self.assertTrue(all(n["span"] is None for r in rows for n in r["nun_readings"] if n["kind"] == "emphasis"))

    def test_hollow_shortening_requires_source_root_full_shape_and_final_sukun(self):
        base = [verb("yaquwlu", root="qwl", lemma="qaAla")]
        rows = self.read("يَقُلْ", base)
        self.assertTrue(rows)
        self.assertTrue(all(r["variant"] == "hollow_short_from_full_base" and r["possible_cases"] == [3] for r in rows))
        self.assertEqual(self.read("يَقُلُ", base), [])
        self.assertEqual(self.read("يقل", [verb("yaquwlu", root="qll", lemma="qaAla")]), [])

    def test_default_active_is_a_qac_format_rule_not_universal_absence(self):
        rows = self.read("يكتب", [verb("yakotubu")])
        self.assertTrue(all(r["voice"] == "active" and r["voice_basis"] == "QAC_DEFAULT_ACTIVE_ABSENT_PASS" for r in rows))
        self.assertEqual(self.read("يكتب", [verb("yakotubu", extra="|ACT|PASS")]), [])

    def test_case_mood_poison_changes_provenance_not_person_semantics(self):
        a = self.read("تكتب", [verb("yakotubu", extra="|MOOD:IND")])
        b = self.read("تكتب", [verb("yakotubu", extra="|MOOD:JUS")])
        self.assertEqual(triples(a), triples(b))
        self.assertEqual({tuple(r["class_candidates"]) for r in a}, {tuple(r["class_candidates"]) for r in b})
        self.assertNotEqual({r["id"] for r in a}, {r["id"] for r in b})

    def test_results_do_not_assign_case_role_or_reference_and_are_fresh(self):
        rows = person_candidates("أنت")
        for row in rows:
            self.assertTrue(all(key not in row for key in ("actual_role", "actual_case", "local_case", "referent")))
        rows[0]["person_profile"]["person"] = 99
        self.assertEqual({r["person_profile"]["person"] for r in person_candidates("أنت")}, {2})

    def test_caller_model_or_invalid_scalar_cannot_supply_authority(self):
        for value in (None, 1, True, [], b"x"):
            with self.assertRaises(NabtError):
                person_candidates(value)
        with self.assertRaises(NabtError):
            person_candidates("يكتب", lexical_model={"status": "VERIFIED"})
        with self.assertRaises(NabtError):
            person_candidates("ن" * 9000)
        with self.assertRaises(NabtError):
            person_candidates("\ud800")


if __name__ == "__main__":
    unittest.main()
