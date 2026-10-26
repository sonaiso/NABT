"""Independent controls for source admission, ambiguity and authority bounds.

The three requested nouns and explicit-shadda/OOV contrasts were chosen before
running the new source profile. They are outside the 25-case frozen reference.
Full-corpus checks need the optional pinned external corpus; matrix/withdrawal
tests always run. These checks do not assert population or Arabic completeness.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import attested_lexical_loader as loader
from nabt.discourse_reader import read_discourse, verify_discourse
from nabt.errors import NabtError
from nabt.inflection_reader import read_inflection
from tools import benchmark_semantic_axes as benchmark
from tools import semantic_axes as adapter
from tests.test_semantic_axes import case as protocol_case, execution as protocol_execution


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "evidence/lexical_loading_v1/matrix.json"
REFERENCE = ROOT / "evidence/semantic_axes_v1/revision_2/reference.json"
REFERENCE_DIGEST = "9787e4496118a80a4f352ef19193e1e37976eb282eaf96caaad511ce77ffa431"
CORPUS = ROOT / "artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz"
CONTEXT = {
    "closed_reference_scope": True,
    "entities": [{"id": "thing_a", "name": "أَلِفٌ", "gender": "feminine",
                  "number": "singular", "kind": "thing"}],
    "deixis": [{"form": "هَذِهِ", "entity_ids": ["thing_a"]}],
}


def readings(report):
    return [reading for occurrence in report["occurrences"]
            for reading in occurrence["readings"]]


def attested_protocol_specimen():
    """Protocol specimen only; installed identity labels do not attest this fixture."""
    item, observed = protocol_case(), protocol_execution()
    loading = {
        "schema": "nabt.semantic-axes-lexical-loading.v1", "profile": "attested_qac_v1",
        "source_sha256": loader.SOURCE_SHA256, "matrix_sha256": loader.MATRIX_SHA256,
        "source_record_count": 10, "model_entry_count": 7,
        "matrix_sense_count": 3, "matrix_aligned_count": 2, "matrix_unresolved_count": 1,
        "authority": "SOURCE_ANNOTATION_NOT_SENSE_OR_WORLD_LICENSE", "lean_native_checked": False,
    }
    observed["lexical_profile"] = "attested_qac_v1"
    observed["lexical_loading"] = deepcopy(loading)
    observed["training"]["sha256"] = loading["source_sha256"]
    observed["training"]["authority"] = loading["authority"]
    observed["replay_receipt"].update(lexical_profile="attested_qac_v1",
        lexical_loading=deepcopy(loading), training_sha256=loading["source_sha256"])
    observed["replay_receipt_sha256"] = adapter.identity(observed["replay_receipt"])
    return item, observed, loading


class IndependentProfileReceiptBinding(unittest.TestCase):
    def assert_unmeasured(self, item, observed, loading):
        row = benchmark.score_case(item, observed, lexical_profile="attested_qac_v1",
                                   lexical_loading=loading)
        for axis in ("syntax", "readings", "reference"):
            self.assertEqual(row["axis_results"][axis]["status"], "UNMEASURED", axis)
        self.assertTrue(all(c["verification"]["checked"] is False for c in row["claims"]))

    def test_matching_attested_protocol_preserves_positive_claim_scope_without_lean(self):
        item, observed, loading = attested_protocol_specimen()
        row = benchmark.score_case(item, observed, lexical_profile="attested_qac_v1",
                                   lexical_loading=loading)
        for axis in ("syntax", "readings", "reference"):
            self.assertEqual(row["axis_results"][axis]["status"], "PASS")
            claim = next(c for c in row["claims"] if c["axis"] == axis)
            self.assertEqual(claim["verification"]["kind"], "PYTHON_REPLAY")
            self.assertEqual(claim["verification"]["theorem_references"], [])
        for axis in ("motive", "world"):
            self.assertEqual(row["axis_results"][axis]["status"], "UNMEASURED")

    def test_observation_and_receipt_profiles_cannot_be_relabelled_from_the_suite(self):
        for where in ("execution", "receipt", "both"):
            item, observed, loading = attested_protocol_specimen()
            if where in ("execution", "both"):
                observed["lexical_profile"] = "teaching_v1"
            if where in ("receipt", "both"):
                observed["replay_receipt"]["lexical_profile"] = "teaching_v1"
            observed["replay_receipt_sha256"] = adapter.identity(observed["replay_receipt"])
            with self.subTest(where=where):
                self.assert_unmeasured(item, observed, loading)

    def test_missing_or_contradictory_loading_is_not_source_evidence(self):
        mutations = (
            lambda e: e.update(lexical_loading=None),
            lambda e: e["replay_receipt"].update(lexical_loading=None),
            lambda e: e["lexical_loading"].update(lean_native_checked=True),
            lambda e: e["replay_receipt"]["lexical_loading"].update(matrix_sense_count=True),
            lambda e: e["replay_receipt"]["lexical_loading"].update(matrix_sha256="c" * 64),
        )
        for index, mutate in enumerate(mutations):
            item, observed, loading = attested_protocol_specimen()
            mutate(observed)
            observed["replay_receipt_sha256"] = adapter.identity(observed["replay_receipt"])
            with self.subTest(index=index):
                self.assert_unmeasured(item, observed, loading)

    def test_recomputed_receipt_digest_does_not_override_different_source(self):
        for where in ("training", "receipt"):
            item, observed, loading = attested_protocol_specimen()
            if where == "training":
                observed["training"]["sha256"] = "c" * 64
            else:
                observed["replay_receipt"]["training_sha256"] = "c" * 64
            observed["replay_receipt_sha256"] = adapter.identity(observed["replay_receipt"])
            with self.subTest(where=where):
                self.assert_unmeasured(item, observed, loading)

    def test_consistent_foreign_source_still_conflicts_with_installed_profile(self):
        item, observed, loading = attested_protocol_specimen()
        observed["training"]["sha256"] = "c" * 64
        observed["lexical_loading"]["source_sha256"] = "c" * 64
        observed["replay_receipt"]["training_sha256"] = "c" * 64
        observed["replay_receipt"]["lexical_loading"]["source_sha256"] = "c" * 64
        observed["replay_receipt_sha256"] = adapter.identity(observed["replay_receipt"])
        self.assert_unmeasured(item, observed, loading)

    def test_legacy_teaching_receipt_remains_compatible_without_external_profile_claim(self):
        item, observed = protocol_case(), protocol_execution()
        for data in (observed, observed["replay_receipt"]):
            data.pop("lexical_profile", None)
            data.pop("lexical_loading", None)
        observed["replay_receipt_sha256"] = adapter.identity(observed["replay_receipt"])
        row = benchmark.score_case(item, observed)
        self.assertEqual(row["axis_results"]["syntax"]["status"], "PASS")
        self.assertEqual(row["claims"][0]["verification"]["kind"], "PYTHON_REPLAY")

    def test_removing_only_execution_profile_is_not_an_archived_teaching_receipt(self):
        item, observed, _ = attested_protocol_specimen()
        observed.pop("lexical_profile")
        row = benchmark.score_case(item, observed)
        self.assertEqual(row["axis_results"]["syntax"]["status"], "UNMEASURED")
        self.assertTrue(all(c["verification"]["checked"] is False for c in row["claims"]))

    def test_run_does_not_show_lexical_coverage_for_a_misbound_observation(self):
        item, observed, loading = attested_protocol_specimen()
        observed["lexical_profile"] = "teaching_v1"
        observed["observed"]["acquisition_diagnostics"] = {
            "lexical_occurrences": [{"surface": "مَدْخَلٌ", "reading_count": 2}]}
        with patch.object(benchmark, "load_reference", return_value=({"cases": [item]}, "a" * 64, {})), \
                patch.object(adapter, "lexical_profile_resources", return_value=(None, {}, loading)), \
                patch.object(adapter, "execute_request", return_value=observed):
            result = benchmark.run(lexical_profile="attested_qac_v1")
        self.assertIsNone(result["cases"][0]["lexical_coverage"])
        self.assertEqual(result["axes"]["syntax"]["measured"], 0)
        self.assertEqual(result["axes"]["syntax"]["unmeasured"], 1)
        self.assertIsNone(result["axes"]["syntax"]["rate"])


class IndependentMatrixBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_bytes())

    def test_original_semantic_reference_and_denominators_unchanged(self):
        self.assertEqual(sha256(REFERENCE.read_bytes()).hexdigest(), REFERENCE_DIGEST)
        cases = json.loads(REFERENCE.read_bytes())["cases"]
        self.assertEqual(len(cases), 25)
        self.assertEqual(sum(c["expected"]["reference"].get("status") != "not_applicable"
                             for c in cases), 5)
        for axis in ("motive", "world"):
            self.assertEqual(sum(c["expected"][axis].get("status") != "not_applicable"
                                 for c in cases), 25)

    def test_homographic_candidates_are_not_sense_equivalence(self):
        man = next(e for e in self.matrix["entries"] if e["id"] == "lisan:v2:man")
        self.assertEqual({c["lemma"] for c in man["morphology_candidates"]},
                         {"رَجُل", "رَجِل", "رِجْل"})
        self.assertIs(man["sense_licensed_for_new_occurrence"], False)
        for candidate in man["morphology_candidates"]:
            self.assertIs(candidate["contextual_sense_identified"], False)
            self.assertEqual(candidate["alignment_authority"],
                             "CONSONANTAL_HEADWORD_CANDIDATE_ONLY")

    def test_matrix_counts_do_not_count_repeated_links_as_unique_witnesses(self):
        entries = self.matrix["entries"]
        groups = [c for e in entries for c in e["morphology_candidates"]]
        unique = {(w["source_record"]["byte_start"], w["source_record"]["byte_end"])
                  for c in groups for w in c["witnesses"]}
        self.assertEqual(self.matrix["counts"]["catalogue_senses"], 42)
        self.assertEqual(self.matrix["counts"]["candidate_groups"], len(groups))
        self.assertEqual(self.matrix["counts"]["unique_candidate_source_records"], len(unique))
        self.assertEqual(self.matrix["counts"]["cross_source_senses_licensed"], 0)
        self.assertTrue(all(e["world_truth_asserted"] is False for e in entries))

    def test_missing_source_is_explicit_defer_not_empty_lexicon(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(NabtError) as caught:
                loader.load_attested_lexicon(Path(tmp) / "not-present.gz")
        self.assertEqual(caught.exception.code, "ATTESTED_SOURCE_UNAVAILABLE")
        self.assertEqual(caught.exception.status, "DEFER")

    def test_a_path_with_a_plausible_name_does_not_supply_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "quranic-corpus-morphology-0.4.txt"
            source.write_bytes(b"LOCATION\tFORM\tTAG\tFEATURES\n")
            with patch.object(loader, "learn_qac_lexicon") as learn:
                with self.assertRaises(NabtError) as caught:
                    loader.load_attested_lexicon(source)
                learn.assert_not_called()
        self.assertEqual(caught.exception.code, "ATTESTED_SOURCE_IDENTITY_MISMATCH")

    def test_self_reported_verified_matrix_cannot_override_installed_identity(self):
        forged = deepcopy(self.matrix)
        forged["verified"] = True
        forged["lean_native_checked"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix.json"
            path.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
            with patch.object(loader, "MATRIX_PATH", path):
                with self.assertRaises(NabtError) as caught:
                    loader._installed_matrix()
        self.assertEqual(caught.exception.code, "LEXICAL_MATRIX_IDENTITY_MISMATCH")


@unittest.skipUnless(CORPUS.is_file(), "optional pinned QAC corpus not downloaded")
class IndependentExternalSourceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded = loader.load_attested_lexicon(CORPUS)
        cls.model = cls.loaded.model

    def test_full_source_profile_is_separate_from_nominal_matrix_and_teaching(self):
        report = self.loaded.report
        self.assertIs(report["matrix_filters_runtime"], False)
        self.assertIs(report["teaching_corpus_included"], False)
        self.assertIs(report["query_or_gold_used_for_source_selection"], False)
        self.assertEqual(report["verification_kind"], "PYTHON_SOURCE_REPLAY")
        self.assertEqual(len(self.model.raw), 6309503)
        self.assertEqual(sha256(self.model.raw).hexdigest(),
                         "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46")
        for key in ("lean_native_checked", "world_truth_asserted", "transmission_evaluated",
                    "all_arabic_complete"):
            self.assertIs(report[key], False)

    def test_attested_nouns_have_lexical_readings_but_sky_boundary_is_not_invented(self):
        for text, lemma in (("أَرْضٌ", "أَرْض"), ("شَمْسٌ", "شَمْس")):
            with self.subTest(text=text):
                rows = readings(read_inflection(text, lexical_model=self.model))
                self.assertTrue(any(r["lexical_features"].get("lemma") == lemma
                                    and r["lexical_features"].get("pos") == "N" for r in rows))
        # Source orthography and a lemma candidate alone do not license a new
        # ordinary-spelling surface in the installed learner's current profile.
        self.assertEqual(readings(read_inflection("سَمَاءٌ", lexical_model=self.model)), [])

    def test_explicit_wrong_shadda_and_oov_are_not_coerced_to_known_nouns(self):
        for text in ("أَرَّضٌ", "شَمَّسٌ", "سَمَّاءٌ", "زَظَغٌ"):
            with self.subTest(text=text):
                self.assertEqual(readings(read_inflection(text, lexical_model=self.model)), [])

    def test_resolved_positive_controls_remain_text_claims_not_world_truth(self):
        for text in ("هَذِهِ أَرْضٌ.", "هَذِهِ شَمْسٌ."):
            with self.subTest(text=text):
                report = read_discourse(text, lexical_model=self.model, context=CONTEXT)
                self.assertEqual(report["status"], "LICENSED_DISCOURSE")
                self.assertTrue(report["claims"])
                self.assertTrue(all(c["args"] == ["thing_a"] for c in report["claims"]))
                self.assertEqual(report["world_truth"], "NOT_ESTABLISHED")
                self.assertTrue(verify_discourse(report, text=text, lexical_model=self.model,
                                                context=CONTEXT)["valid"])

    def test_sky_control_remains_unresolved_instead_of_changing_reference(self):
        report = read_discourse("هَذِهِ سَمَاءٌ.", lexical_model=self.model, context=CONTEXT)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])
        self.assertEqual(report["world_truth"], "NOT_ESTABLISHED")

    def test_withdrawal_of_source_or_deixis_invalidates_old_receipt(self):
        text = "هَذِهِ أَرْضٌ."
        report = read_discourse(text, lexical_model=self.model, context=CONTEXT)
        no_deixis = {**CONTEXT, "deixis": []}
        self.assertEqual(read_discourse(text, lexical_model=self.model,
                                       context=no_deixis)["claims"], [])
        self.assertFalse(verify_discourse(report, text=text, lexical_model=self.model,
                                         context=no_deixis)["valid"])
        self.assertFalse(verify_discourse(report, text=text, lexical_model=None,
                                         context=CONTEXT)["valid"])

    def test_source_span_replay_rejects_boolean_and_wrong_feature_witness(self):
        matrix = json.loads(MATRIX.read_bytes())
        for field, value in (("boolean_span", True), ("features", "STEM|POS:N|LEM:forged")):
            mutated = deepcopy(matrix)
            item = next(e for e in mutated["entries"] if e["morphology_candidates"])
            row = item["morphology_candidates"][0]["witnesses"][0]
            if field == "boolean_span":
                row["source_record"]["byte_start"] = value
            else:
                row[field] = value
            with self.subTest(field=field), self.assertRaises(NabtError):
                loader._matrix_report(mutated, self.model.raw, loader.MATRIX_SHA256)


if __name__ == "__main__":
    unittest.main()
