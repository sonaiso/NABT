"""Authored checks that an N annotation alone cannot activate a predicate.

The miniature TSV is an instructional premise, not a quotation from QAC or
from an independent evaluation. It does not change the frozen 26-case review.
"""

import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse_reader import read_discourse


TRAINING = (
    b"# Authored predicate-construction boundary premises; not QAC quotations.\n"
    b"LOCATION\tFORM\tTAG\tFEATURES\n"
    b"(1:1:1:1)\t>amosi\tN\tSTEM|POS:N|LEM:>amos|ROOT:Ams|M\n"
    b"(1:2:1:1)\tbaAHiv\tN\tSTEM|POS:N|LEM:baAHiv|ROOT:bHv|MS\n"
    b"(1:3:1:1)\tmuEal~imN\tN\tSTEM|POS:N|LEM:muEal~im|ROOT:Elm|MS\n"
    b"(1:4:1:1)\tmuEal~imK\tN\tSTEM|POS:N|LEM:muEal~im|ROOT:Elm|MS\n"
    b"(1:5:1:1)\tkariymN\tADJ\tSTEM|POS:ADJ|LEM:kariym|ROOT:krm|MS\n"
    b"(1:6:1:1)\tkariymK\tADJ\tSTEM|POS:ADJ|LEM:kariym|ROOT:krm|MS\n"
    b"(1:7:1:1)\tHaAzimN\tPN\tSTEM|POS:PN|LEM:HaAzim|ROOT:Hzm|MS\n"
    b"(1:8:1:1)\tHaAzimK\tPN\tSTEM|POS:PN|LEM:HaAzim|ROOT:Hzm|MS\n"
)
CONTEXT = {
    "entities": [{"id": "hazim", "name": "حازم", "gender": "masculine",
                  "number": "singular", "kind": "person"}],
    "deixis": [{"form": "هذا", "entity_ids": ["hazim"]}],
}


class DiscoursePredicateBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING, source_id="authored_predicate_boundary")

    def _read(self, text):
        return read_discourse(text, lexical_model=self.model, context=CONTEXT)

    def _assert_unknown_predicate_deferred(self, text, surface, role):
        result = self._read(text)
        lexical = [reading for occurrence in result["occurrences"] if occurrence["surface"] == surface
                   for reading in occurrence["readings"]
                   if reading["lexical_features"].get("pos") == "N"]
        self.assertTrue(lexical, "The lexical premise must be present; absence is not the intended guard")
        self.assertTrue(all(r["construction"] is None for r in lexical), lexical)
        assignments = [a for clause in result["clauses"] for analysis in clause["analyses"]
                       for a in analysis["assignments"] if a["role"] == role]
        self.assertTrue(assignments, "The candidate frame must reach predicate construction checking")
        self.assertTrue(all("PREDICATE_CONSTRUCTION_EVIDENCE_REQUIRED" in a["obligations"]
                            for a in assignments), assignments)
        self.assertTrue(all(not a["activated"] and a["actual_role"] is None for a in assignments), assignments)
        self.assertEqual(result["status"], "DEFER")
        self.assertEqual(result["claims"], [])

    def test_unknown_nouns_cannot_be_activated_as_nominal_predicates(self):
        for surface in ("أَمْسِ", "بَاحِث"):
            with self.subTest(surface=surface):
                self._assert_unknown_predicate_deferred("حَازِمٌ " + surface + ".", surface, "nominal_predicate")

    def test_unknown_nouns_cannot_bypass_inna_or_kana_predicate_frames(self):
        for prefix, role in (("إِنَّ هَذَا ", "inna_predicate"), ("كَانَ هَذَا ", "kana_predicate")):
            for surface in ("أَمْسِ", "بَاحِث"):
                with self.subTest(role=role, surface=surface):
                    self._assert_unknown_predicate_deferred(prefix + surface + ".", surface, role)

    def _assert_witnessed_predicate(self, text, role):
        result = self._read(text)
        assignments = [a for clause in result["clauses"] for analysis in clause["analyses"]
                       for a in analysis["assignments"] if a["role"] == role and a["activated"]]
        self.assertEqual(result["status"], "LICENSED_DISCOURSE")
        self.assertTrue(result["claims"])
        self.assertTrue(assignments)
        self.assertTrue(all(a["case_domain"] == "inflected_case" and a["inflected_case"] == "raf"
                            for a in assignments), assignments)

    def test_witnessed_noun_construction_still_licenses_a_predicate(self):
        self._assert_witnessed_predicate("حَازِمٌ مُعَلِّمٌ.", "nominal_predicate")

    def test_witnessed_adjective_construction_still_licenses_a_predicate(self):
        self._assert_witnessed_predicate("حَازِمٌ كَرِيمٌ.", "nominal_predicate")

    def test_witnessed_predicate_still_works_in_the_inna_frame(self):
        self._assert_witnessed_predicate("إِنَّ هَذَا كَرِيمٌ.", "inna_predicate")


if __name__ == "__main__":
    unittest.main()
