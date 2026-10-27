"""Frozen contextual-reference oracle checks, independent of its new runtime.

No matcher, interpreter, source loader, or benchmark is imported. These tests
pin author decisions, source windows, raw positions, and measurement limits.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "contextual_semantics_v1"
REFERENCE_SHA256 = "6f2e1c1127196d2b5fbbc2f357dbbf1a003881061727e96ad29d153c6628707d"
OLD_SHA256 = "9787e4496118a80a4f352ef19193e1e37976eb282eaf96caaad511ce77ffa431"


def load(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class ContextualSemanticsReferenceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load("reference.json")
        cls.cases = {case["id"]: case for case in cls.reference["cases"]}
        cls.freeze = load("reference.freeze.json")
        old_path = ROOT / cls.reference["historical_reference"]["path"]
        cls.old_bytes = old_path.read_bytes()
        cls.old_reference = json.loads(cls.old_bytes)

    def test_frozen_reference_and_per_case_labels_match_pins(self):
        self.assertEqual(sha256((EVIDENCE / "reference.json").read_bytes()).hexdigest(), REFERENCE_SHA256)
        self.assertEqual(self.freeze["reference_sha256"], REFERENCE_SHA256)
        self.assertIs(self.freeze["frozen_before_new_runtime_execution"], True)
        for field in ("sources", "input_review"):
            self.assertEqual(sha256((EVIDENCE / self.freeze[field]).read_bytes()).hexdigest(),
                             self.freeze[field + "_sha256"])
        for case in self.cases.values():
            with self.subTest(case=case["id"]):
                self.assertEqual(digest(case["input"]), case["input_sha256"])
                self.assertEqual(digest(case["expected"]), case["expected_sha256"])
                self.assertEqual(case["input_sha256"], self.freeze["case_input_sha256"][case["id"]])
                self.assertEqual(case["expected_sha256"], self.freeze["case_expected_sha256"][case["id"]])

    def test_old_twenty_five_remain_exact_and_separate(self):
        self.assertEqual(sha256(self.old_bytes).hexdigest(), OLD_SHA256)
        historical = self.reference["historical_reference"]
        self.assertEqual(historical["sha256"], OLD_SHA256)
        self.assertIs(historical["modified"], False)
        self.assertIs(historical["denominators_merged"], False)
        self.assertEqual(len(self.old_reference["cases"]), 25)
        families = Counter(case["family"] for case in self.old_reference["cases"])
        self.assertEqual(families, {"nominal_event": 5, "nonvolitional_verb": 5,
                                    "temporal_not_causal": 5, "context_collision": 5,
                                    "negation_hypothesis_quote": 5})
        self.assertEqual([case["id"] for case in self.old_reference["cases"]
                          if case["expected"]["reference"]["status"] != "not_applicable"],
                         ["C01", "C02", "C03", "C04", "C05"])

    def test_new_cases_are_distinct_from_each_other_and_old_exact_inputs(self):
        self.assertEqual(len(self.cases), 20)
        self.assertEqual(len(self.reference["cases"]), 20)
        new_inputs = {case["input_sha256"] for case in self.cases.values()}
        self.assertEqual(len(new_inputs), 20)
        old_inputs = {digest(case["input"]) for case in self.old_reference["cases"]}
        self.assertFalse(new_inputs & old_inputs)

    def test_positive_ambiguity_and_nonresolution_denominators_are_separate(self):
        self.assertEqual(Counter(case["family"] for case in self.cases.values()),
                         {"named": 4, "personal": 5, "deictic": 4, "quoted": 6, "partial_clause_boundary": 1})
        self.assertEqual(Counter(case["expected"]["reference"]["status"] for case in self.cases.values()),
                         {"resolved": 12, "ambiguous": 3, "unresolved": 5})
        categories = {"resolved": "positive_binding", "ambiguous": "alternative_retention", "unresolved": "safe_nonresolution"}
        for case in self.cases.values():
            self.assertEqual(case["metric_category"], categories[case["expected"]["reference"]["status"]])
        self.assertEqual(self.reference["metric_policy"]["zero_denominator"], "null")

    def test_runtime_inputs_have_no_gold_or_case_metadata(self):
        for case in self.cases.values():
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case["input"]), {"text", "context"})
                context = case["input"]["context"]
                self.assertFalse(set(context) - {"entities", "speaker", "addressee", "deixis", "closed_reference_scope"})
                self.assertIs(type(context["closed_reference_scope"]), bool)
                for entity in context["entities"]:
                    self.assertEqual(set(entity), {"id", "name", "gender", "number", "kind"})
                    self.assertFalse(any(character.isspace() for character in entity["name"]))
                for binding in context["deixis"]:
                    self.assertEqual(set(binding), {"form", "entity_ids"})
                self.assertEqual(set(case["expected"]), {"reference"})

    def test_positions_are_exact_raw_unicode_codepoints(self):
        for case in self.cases.values():
            with self.subTest(case=case["id"]):
                text = case["input"]["text"]
                expected = case["expected"]["reference"]
                span = expected["span"]
                self.assertIs(type(span["start"]), int)
                self.assertIs(type(span["end"]), int)
                self.assertEqual(text[span["start"]:span["end"]], expected["surface"])
                self.assertEqual(text.count(expected["surface"]), 1)
                self.assertEqual(expected["occurrence"], 0)
                if expected["scope"] == "quote:1":
                    self.assertLess(text.index("«"), span["start"])
                    self.assertLessEqual(span["end"], text.index("»"))
                else:
                    self.assertEqual(expected["scope"], "outer")

    def test_expected_identity_sets_are_declared_not_fabricated(self):
        for case in self.cases.values():
            ids = {entity["id"] for entity in case["input"]["context"]["entities"]}
            expected = case["expected"]["reference"]
            targets = expected["target_ids"]
            self.assertEqual(targets, sorted(set(targets)))
            self.assertTrue(set(targets).issubset(ids))
            if expected["status"] == "resolved":
                self.assertEqual(len(targets), 1)
            elif expected["status"] == "ambiguous":
                self.assertGreater(len(targets), 1)
            else:
                self.assertEqual(expected["status"], "unresolved")
                self.assertEqual(targets, [])

    def test_same_text_context_swaps_have_opposite_gold_bindings(self):
        for first, second in (("CR-N01", "CR-N03"), ("CR-P01", "CR-P02"), ("CR-D01", "CR-D02")):
            a, b = self.cases[first], self.cases[second]
            self.assertEqual(a["input"]["text"], b["input"]["text"])
            self.assertNotEqual(a["input"]["context"], b["input"]["context"])
            self.assertNotEqual(a["expected"]["reference"]["target_ids"], b["expected"]["reference"]["target_ids"])

    def test_singleton_context_does_not_supply_missing_role_or_deixis(self):
        for cid in ("CR-P03", "CR-P05", "CR-D04"):
            case = self.cases[cid]
            self.assertEqual(len(case["input"]["context"]["entities"]), 1)
            self.assertEqual(case["expected"]["reference"]["status"], "unresolved")

    def test_quoted_self_reference_differs_from_external_speaker(self):
        for cid, target in (("CR-Q01", "person_a"), ("CR-Q02", "person_b"),
                            ("CR-Q03", "person_a"), ("CR-Q04", "person_a")):
            case = self.cases[cid]
            self.assertEqual(case["expected"]["reference"]["target_ids"], [target])
            self.assertNotEqual(case["input"]["context"]["speaker"], target)
            self.assertIs(case["limits"]["asserts_speech_event"], False)
            self.assertIs(case["limits"]["asserts_embedded_content_truth"], False)
        self.assertEqual(self.cases["CR-Q05"]["expected"]["reference"]["target_ids"], ["person_a", "person_b"])
        self.assertEqual(self.cases["CR-Q06"]["expected"]["reference"]["status"], "unresolved")

    def test_partial_clause_case_does_not_grant_lexical_or_clause_authority(self):
        case = self.cases["CR-B01"]
        self.assertEqual(case["input"]["text"], "أَنَا ظَرْمَشُوقٌ.")
        self.assertEqual(case["expected"]["reference"]["target_ids"], ["person_a"])
        self.assertEqual(case["measurement_scope"], "REFERENCE_OCCURRENCE_ONLY")
        self.assertIs(case["limits"]["asserts_complete_clause_licensing"], False)
        self.assertIs(case["limits"]["attests_context_names_lexically"], False)

    def test_authorship_and_static_code_exposure_are_disclosed(self):
        independence = self.reference["independence"]
        self.assertIs(independence["existing_input_contract_and_resolver_read"], True)
        self.assertIs(independence["new_runtime_implementation_read"], False)
        self.assertIs(independence["new_runtime_outputs_read"], False)
        self.assertIs(independence["external_blind_holdout"], False)
        self.assertIs(independence["external_human_adjudication"], False)
        self.assertIs(independence["same_team_and_workspace"], True)
        for field in ("complete_clause_licensing_measured", "whole_arabic_complete",
                      "actual_motive_measured", "external_world_truth_measured",
                      "external_lexical_attestation_of_context_names_measured"):
            self.assertIs(self.reference["scope"][field], False)

    def test_source_windows_and_authored_judgments_are_separate(self):
        sources = load("reference_sources.json")["sources"]
        ids = {source["id"] for source in sources}
        self.assertIn("AUTHORED-CONTEXTUAL-ORACLE-V1", ids)
        for source in sources:
            if source["kind"] != "local_primary_text":
                continue
            raw = (ROOT / source["path"]).read_bytes()
            self.assertEqual(sha256(raw).hexdigest(), source["file_sha256"])
            self.assertEqual(sha256(raw[source["byte_start"]:source["byte_end_exclusive"]]).hexdigest(), source["window_sha256"])
        for case in self.cases.values():
            self.assertTrue(set(case["expectation_sources"]).issubset(ids))

    def test_five_range_rows_do_not_inflate_case_or_source_denominators(self):
        review = load("reference_input_review.json")
        self.assertEqual(review["user_rows_count"], 5)
        self.assertIsNone(review["expanded_case_count"])
        self.assertIs(review["has_explicit_contexts"], False)
        self.assertIs(review["has_exact_source_spans"], False)
        self.assertEqual(len(review["mappings"]), 5)
        self.assertEqual(review["frozen_reference_families"]["C01-C05"], "context_collision")
        self.assertEqual(review["source_status"], "AUTHOR_NAMES_WITHOUT_SOURCE_IDENTITY_LOCATOR_OR_EXCERPT_ARE_NOT_VERIFIED_WITNESSES")

    def test_obligation_matrix_is_historical_non_runtime_audit(self):
        matrix = load("reference_obligation_matrix_25.json")
        self.assertEqual(matrix["authority"], "NON_RUNTIME_AUDIT_ARTIFACT")
        self.assertEqual(matrix["freshness"], "LAST_COMMITTED_SNAPSHOTS_NOT_A_NEW_HEAD_MEASUREMENT")
        self.assertEqual(matrix["historical_reference_sha256"], OLD_SHA256)
        self.assertEqual(len(matrix["rows"]), 25)
        old = {case["id"]: case for case in self.old_reference["cases"]}
        self.assertEqual({row["id"] for row in matrix["rows"]}, set(old))
        for row in matrix["rows"]:
            case = old[row["id"]]
            self.assertEqual(row["input"], case["input"])
            self.assertEqual(row["input_sha256"], digest(case["input"]))
            self.assertEqual(row["family"], case["family"])
            self.assertIs(row["required_grammar_obligations"]["validated_as_only_cause"], False)
        for source in matrix["provenance"]:
            self.assertEqual(sha256((ROOT / source["path"]).read_bytes()).hexdigest(), source["sha256"])
