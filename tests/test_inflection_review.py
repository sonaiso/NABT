"""Independent evaluation adapter checks; full pinned corpus replay is a separate gate."""
from copy import deepcopy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unicodedata
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("inflection_review", ROOT / "tools/inflection_evaluation.py")
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class IndependentInflectionReviewTests(unittest.TestCase):
    @staticmethod
    def first_relation_example(case_id="INF-T01"):
        path = ROOT / "evidence/inflection/independent_first_run_v1.raw.jsonl.gz"
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            report = next(row["report"] for row in map(json.loads, handle)
                          if row.get("case_id") == case_id and "report" in row)
        _, material, _, _ = review.load_material()
        inputs = next(c["input"] for c in material["cases"] if c["id"] == case_id)
        return report, inputs

    def test_frozen_material_and_disjoint_inventory(self):
        frozen, material, split, law = review.load_material()
        self.assertEqual(frozen["raw_case_count"], 74)
        self.assertEqual(len(material["cases"]), 74)
        self.assertEqual(len(split["excluded_verses"]), 48)
        self.assertEqual(len(law["admitted_rows"]), 45)
        self.assertEqual(len(law["excluded_class_case"]), 15)
        self.assertFalse(frozen["new_runtime_formal_or_table_read_before_freeze"])

    def test_boolean_cannot_be_a_numeric_sign(self):
        sign = {"class": 0, "case": 0, "sign": 1, "mode": 0, "origin": 0,
                "case_name": "nasb", "sign_name": "fatha", "mode_name": "overt", "origin_name": "original"}
        self.assertEqual(review.sign_view(sign)["case"], "nasb")
        for field in ("class", "case", "sign", "mode", "origin"):
            invalid = dict(sign, **{field: False})
            with self.assertRaises(ValueError):
                review.sign_view(invalid)

    def test_names_cannot_override_numeric_sign(self):
        sign = {"class": 0, "case": 2, "sign": 2, "mode": 0, "origin": 0,
                "case_name": "jarr", "sign_name": "fatha", "mode_name": "overt", "origin_name": "original"}
        with self.assertRaises(ValueError):
            review.sign_view(sign)

    def test_poisoning_changes_only_hidden_annotations(self):
        raw = b"# header\r\nLOCATION\tFORM\tTAG\tFEATURES\r\n(2:1:1:1)\tbaHorN\tN\tSTEM|POS:N|LEM:baHor|ROOT:bHr|M|NOM\r\n"
        poisoned = review.source_variant(raw, "case_mood_poisoned")
        erased = review.source_variant(raw, "case_mood_erased")
        self.assertEqual(poisoned, raw.replace(b"|NOM", b"|ACC"))
        self.assertEqual(erased, raw.replace(b"|NOM", b""))
        self.assertEqual(review.source_variant(raw, "heldout_qac"), raw)

    def test_semantic_comparison_ignores_ids_but_not_root(self):
        report = {"status": "DEFER", "frame_status": "CLOSED_FRAME_LANGUAGE", "semantic_facts": [], "relations": [],
                  "source_id": "a", "occurrences": [{"occurrence_id": "a", "surface": "بحر", "kind": "written_run",
                  "span": {"start": 0, "end": 6}, "status": "SOURCE_QUALIFIED_ALTERNATIVES", "obligations": [],
                  "readings": [{"reading_id": "one", "kind": "noun", "construction": None,
                                "lexical_features": {"root": "بحر"}, "sign_candidates": [], "nun_readings": [],
                                "segmentation": {"parts": [{"kind": "nominal_stem", "surface": "بحر",
                                                            "span": {"start": 0, "end": 6}}]}}]}]}
        changed = deepcopy(report)
        changed["source_id"] = "b"
        changed["occurrences"][0]["occurrence_id"] = "b"
        changed["occurrences"][0]["readings"][0]["reading_id"] = "two"
        self.assertEqual(review.semantic_view(report), review.semantic_view(changed))
        changed["occurrences"][0]["readings"][0]["lexical_features"]["root"] = "كتب"
        self.assertNotEqual(review.semantic_view(report), review.semantic_view(changed))

    def test_repeated_surface_preserves_two_targets(self):
        case = {"input": {"text": "بحر بحر"}, "target_surface": "بحر"}
        occurrences = [{"span": {"start": 0, "end": 6}}, {"span": {"start": 7, "end": 13}}]
        self.assertEqual(review.target_occurrences(case, {"occurrences": occurrences}), occurrences)
        with self.assertRaises(ValueError):
            review.target_occurrences(case, {"occurrences": occurrences[:1]})

    def test_preserved_original_relation_is_consistent(self):
        for case_id in ("INF-T01", "INF-T09", "INF-T10", "INF-A14"):
            report, inputs = self.first_relation_example(case_id)
            review.validate_relations(report, inputs)

    def test_relation_cannot_change_case_or_case_domain(self):
        report, inputs = self.first_relation_example()
        for patch in ({"case": 1, "case_name": "raf"}, {"case_domain": "local_case"}):
            corrupted = deepcopy(report)
            corrupted["relations"][0].update(patch)
            with self.assertRaises(ValueError):
                review.validate_relations(corrupted, inputs)

    def test_head_cannot_borrow_occurrence_reading_or_rule(self):
        report, inputs = self.first_relation_example()
        for field, value in (("occurrence_id", "invented"), ("reading_id", "invented"), ("rule_id", "lam_activation")):
            corrupted = deepcopy(report)
            corrupted["relations"][0]["head"][field] = value
            with self.assertRaises(ValueError):
                review.validate_relations(corrupted, inputs)

    def test_support_endpoint_cannot_disagree_with_relation(self):
        report, inputs = self.first_relation_example()
        corrupted = deepcopy(report)
        support = next(s for s in corrupted["relations"][0]["supports"] if s["kind"] == "head_occurrence")
        support["reading_id"] = "invented"
        with self.assertRaises(ValueError):
            review.validate_relations(corrupted, inputs)

    def test_runtime_manifest_must_be_pinned_by_content(self):
        original = ROOT / "evidence/inflection/code_freeze_v1.json"
        review.pinned_runtime_manifest(original)
        changed = json.loads(original.read_bytes())
        changed["snapshot_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "code_freeze_v1.json"
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "not independently pinned"):
                review.pinned_runtime_manifest(path)

    def test_post_review_material_is_separately_pinned(self):
        material = review.load_post_review_material()
        self.assertEqual(len(material["cases"]), 22)
        self.assertFalse(material["new_a2_implementation_read_before_authoring"])
        self.assertTrue(all(c["synthetic_qac_fixture_not_corpus_passage"] for c in material["cases"]))

    @staticmethod
    def nun_example():
        text = "يَسْكُنُونَ"
        raw = text.encode()
        inputs = {"text": text, "source_id": "nun_test", "scope": "test"}
        digest = review.sha256(raw).hexdigest()
        nuns = []
        for index, char in enumerate(text):
            if char != "ن":
                continue
            end = index + 1
            while end < len(text) and unicodedata.combining(text[end]):
                end += 1
            a, b = len(text[:index].encode()), len(text[:end].encode())
            piece = raw[a:b]
            nuns.append({"kind": "radical" if not nuns else "five_verb_raf", "realization": "present",
                         "surface": piece.decode(), "span": {"start": a, "end": b, "source_id": "nun_test",
                         "source_sha256": digest, "span_sha256": review.sha256(piece).hexdigest()}})
        return inputs, {"stem_span": {"start": 0, "end": len(raw)}, "nun_readings": nuns}

    def test_nuns_must_be_correlated_in_one_reading(self):
        inputs, reading = self.nun_example()
        names = ["radical", "inflection_retained"]
        self.assertTrue(review.correlated_nun_positions([reading], names, inputs))
        separated = [dict(reading, nun_readings=[n]) for n in reading["nun_readings"]]
        self.assertFalse(review.correlated_nun_positions(separated, names, inputs))

    def test_nuns_must_be_distinct_source_bound_written_clusters(self):
        inputs, reading = self.nun_example()
        names = ["radical", "inflection_retained"]
        corrupted = deepcopy(reading)
        corrupted["nun_readings"][1]["span"] = corrupted["nun_readings"][0]["span"]
        corrupted["nun_readings"][1]["surface"] = corrupted["nun_readings"][0]["surface"]
        self.assertFalse(review.correlated_nun_positions([corrupted], names, inputs))
        corrupted = deepcopy(reading)
        corrupted["nun_readings"][0]["span"]["source_id"] = "another_source"
        self.assertFalse(review.correlated_nun_positions([corrupted], names, inputs))
        corrupted = deepcopy(reading)
        corrupted["nun_readings"][0]["span"]["start"] = 0
        self.assertFalse(review.correlated_nun_positions([corrupted], names, inputs))

    def test_nun_span_must_include_its_written_combining_marks(self):
        inputs, reading = self.nun_example()
        corrupted = deepcopy(reading)
        for nun in corrupted["nun_readings"]:
            nun["span"]["end"] = nun["span"]["start"] + len("ن".encode())
            nun["span"]["span_sha256"] = review.sha256("ن".encode()).hexdigest()
            nun["surface"] = "ن"
        self.assertFalse(review.correlated_nun_positions([corrupted], ["radical", "inflection_retained"], inputs))

    def test_selected_runtime_cannot_reuse_preloaded_nabt(self):
        with patch.dict(review.sys.modules, {"nabt": types.ModuleType("nabt")}):
            with self.assertRaisesRegex(ValueError, "fresh process"):
                review.require_fresh_runtime()


if __name__ == "__main__":
    unittest.main()
