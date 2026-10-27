"""Integrity and scope checks for independently authored epistemic references.

This module intentionally imports no production interpreter, matcher, or scorer.
It checks frozen oracle inputs/labels and independently inspected source fields;
it does not compute expected decisions by repeating the matching algorithm.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "epistemic_measurement_v1"
REFERENCE_SHA256 = "d3754d7d04ba83c69e25ea0c4d661da4bde4795633429cd64979f21f87a9fe70"
REGISTRY_SHA256 = "9c972a7a76ae90711b20208d57bb648d0560bee9d5c13c52eaaf920e5043c6c6"
AGENCY_SHA256 = "ccbf599e3d1536e8f3b5ab29ca40508e82e192770c14b23d7cc880f2b7725a6d"
USGS_SHA256 = "d9cf0301f748786d5ff881edba71e1b19c5b5008b3abeb893e8e88240433ba4a"
OLD_REFERENCE_SHA256 = "9787e4496118a80a4f352ef19193e1e37976eb282eaf96caaad511ce77ffa431"
KEY_FIELDS = {"axis", "entity", "predicate", "value", "unit", "context", "time", "place"}
TIME = re.compile(r"(?:0|[1-9][0-9]*|-[1-9][0-9]*)\Z")


def load(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


class EpistemicReferenceIntegrityTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load("reference.json")
        cls.cases = {case["id"]: case for case in cls.reference["cases"]}
        cls.agency = load("agency_reference.json")
        cls.agency_cases = {case["id"]: case for case in cls.agency["cases"]}

    def test_reference_bytes_and_freezes_are_pinned(self):
        for filename, expected_hash in (
            ("reference.json", REFERENCE_SHA256),
            ("agency_reference.json", AGENCY_SHA256),
            ("authored_registry.json", REGISTRY_SHA256),
        ):
            with self.subTest(filename=filename):
                self.assertEqual(sha256((EVIDENCE / filename).read_bytes()).hexdigest(), expected_hash)
        for ref_name, freeze_name in (
            ("reference.json", "reference.freeze.json"),
            ("agency_reference.json", "agency_reference.freeze.json"),
        ):
            reference, freeze = load(ref_name), load(freeze_name)
            self.assertEqual(freeze["reference"], ref_name)
            self.assertEqual(freeze["reference_sha256"], sha256((EVIDENCE / ref_name).read_bytes()).hexdigest())
            self.assertEqual(freeze["case_count"], len(reference["cases"]))
            for case in reference["cases"]:
                with self.subTest(case=case["id"]):
                    self.assertEqual(case["input_sha256"], digest(case["input"]))
                    self.assertEqual(case["expected_sha256"], digest(case["expected"]))
                    self.assertEqual(freeze["case_input_sha256"][case["id"]], case["input_sha256"])
                    self.assertEqual(freeze["case_expected_sha256"][case["id"]], case["expected_sha256"])

    def test_old_twenty_five_are_not_relabelled_or_merged(self):
        historical = self.reference["historical_reference"]
        self.assertEqual(historical["sha256"], OLD_REFERENCE_SHA256)
        self.assertEqual(sha256((ROOT / historical["path"]).read_bytes()).hexdigest(), OLD_REFERENCE_SHA256)
        self.assertIs(historical["modified"], False)
        self.assertIs(historical["denominators_merged"], False)

    def test_quote_erratum_preserves_original_bytes_and_all_gold_labels(self):
        erratum = load("reference_erratum.json")
        self.assertEqual(erratum["classification"], "REFERENCE_FIXTURE_BUGFIX_NOT_BLIND_NEW_REFERENCE")
        self.assertIs(erratum["chronology"]["runtime_agent_executed_original_reference_before_fix"], True)
        self.assertIs(erratum["chronology"]["reference_author_had_read_runtime_implementation_or_results_when_fixing"], False)
        self.assertIs(erratum["chronology"]["blind_evaluation"], False)
        old_dir = EVIDENCE / erratum["original"]["directory"]
        self.assertEqual(sha256((old_dir / "reference.json").read_bytes()).hexdigest(),
                         "80b6b1f1cb552f8ec50723a765c15bc0b90f16c85d42badd61bb8a5050ee3ff1")
        self.assertEqual(sha256((old_dir / "authored_registry.json").read_bytes()).hexdigest(),
                         "fdb9c8a2423cb4c15842a9acdd866b8e1a60694c6353618283db0e05963db641")
        self.assertEqual(sha256((old_dir / "reference.freeze.json").read_bytes()).hexdigest(),
                         "af0fcd1b8d60655f98ec4d1d137493ab7832793fb92f0a3c75bfc0110b82711e")
        old_reference = json.loads((old_dir / "reference.json").read_text(encoding="utf-8"))
        self.assertEqual([(case["id"], case["expected"]) for case in old_reference["cases"]],
                         [(case["id"], case["expected"]) for case in self.reference["cases"]])
        changed = [old["id"] for old, new in zip(old_reference["cases"], self.reference["cases"])
                   if old["input_sha256"] != new["input_sha256"]]
        self.assertEqual(changed, ["EM-M05", "EM-W04"])
        self.assertEqual([item["case_id"] for item in erratum["changed_cases"]], changed)
        self.assertEqual(erratum["corrected"]["reference_sha256"], REFERENCE_SHA256)
        self.assertEqual(erratum["corrected"]["registry_sha256"], REGISTRY_SHA256)

    def test_unique_ids_and_separate_capability_denominators(self):
        self.assertEqual(len(self.reference["cases"]), 32)
        self.assertEqual(len(self.cases), 32)
        self.assertEqual(len(self.agency["cases"]), 11)
        self.assertEqual(len(self.agency_cases), 11)
        self.assertFalse(set(self.cases) & set(self.agency_cases))
        self.assertEqual(Counter(case["expected"]["status"] for case in self.cases.values()),
                         {"SUPPORTED": 7, "REFUTED": 2, "CONFLICT": 2, "UNKNOWN": 20, "RESOURCE_LIMIT": 1})
        self.assertEqual(Counter(case["expected"]["status"] for case in self.agency_cases.values()),
                         {"SUPPORTED": 1, "REFUTED": 1, "UNKNOWN": 8, "RESOURCE_LIMIT": 1})
        categories = {"SUPPORTED": "positive_capability", "REFUTED": "refutation",
                      "CONFLICT": "conflict", "UNKNOWN": "safe_abstention", "RESOURCE_LIMIT": "resource_boundary"}
        for case in (*self.cases.values(), *self.agency_cases.values()):
            self.assertEqual(case["metric_category"], categories[case["expected"]["status"]])

    def test_authorship_and_measurement_limits_are_explicit(self):
        for reference in (self.reference, self.agency):
            for flag in ("runtime_implementation_read", "runtime_results_read",
                         "external_human_adjudication", "blind_evaluation"):
                self.assertIs(reference["independence"][flag], False)
            self.assertIs(reference["independence"]["same_team_and_environment"], True)
            for flag in ("natural_language_acquisition_measured", "hidden_motive_identification_measured",
                         "physical_world_truth_measured", "whole_arabic_complete", "domain_transfer_measured"):
                self.assertIs(reference["scope"][flag], False)
            self.assertEqual(reference["scope"]["claim_acquisition"], "STRUCTURED_PREINTERPRETED_INPUT")
        self.assertEqual(self.reference["group"], "authored_controls")
        self.assertEqual(self.agency["group"], "agency_record")
        self.assertEqual(self.reference["metric_policy"]["zero_denominator"], "null")

    def assert_key_shape(self, key):
        self.assertEqual(set(key), KEY_FIELDS)
        self.assertTrue(all(type(value) is str and value for value in key.values()))
        self.assertRegex(key["time"], TIME)
        self.assertLessEqual(abs(int(key["time"])), 9007199254740991)
        self.assertIn(key["axis"], ("reported_motive", "recorded_observation", "hidden_motive"))

    def test_all_inputs_obey_the_frozen_typed_boundary(self):
        for case in (*self.cases.values(), *self.agency_cases.values()):
            with self.subTest(case=case["id"]):
                request = case["input"]
                self.assertNotIn("expected", request)
                self.assertNotIn("id", request)
                self.assertEqual(set(request["query"]), {"key", "positive", "origin"})
                self.assert_key_shape(request["query"]["key"])
                self.assertIs(type(request["query"]["positive"]), bool)
                self.assertIs(type(request["budget"]), int)
                self.assertGreaterEqual(request["budget"], 0)
                self.assertLessEqual(request["budget"], 128)
                if case["source_profile"] == "usgs_snapshot_v1":
                    self.assertEqual(set(request), {"query", "budget"})
                    continue
                self.assertEqual(set(request), {"query", "active_sources", "origins", "interpretations", "budget", "certificate"})
                self.assertIsNone(request["certificate"])
                origins = [origin["id"] for origin in request["origins"]]
                self.assertEqual(len(origins), len(set(origins)))
                self.assertIn(request["query"]["origin"], origins)
                for origin in request["origins"]:
                    self.assertEqual(set(origin), {"id", "parents"})
                    self.assertTrue(set(origin["parents"]).issubset(origins))
                for item in request["interpretations"]:
                    self.assertEqual(set(item), {"id", "source", "key", "positive", "kind", "origin", "ancestry"})
                    self.assert_key_shape(item["key"])
                    self.assertIs(type(item["positive"]), bool)
                    self.assertEqual(set(item["source"]), {"identity", "revision", "content"})
                    self.assertIn(item["origin"], origins)
                    self.assertTrue(set(item["ancestry"]).issubset(origins))

    def test_expected_witness_ids_are_not_fabricated_or_duplicated(self):
        for case in self.cases.values():
            with self.subTest(case=case["id"]):
                ledger_ids = [item["id"] for item in case["input"]["interpretations"]]
                self.assertEqual(len(ledger_ids), len(set(ledger_ids)))
                expected = case["expected"]
                self.assertEqual(set(expected), {"status", "support_ids", "refutation_ids", "selected_ids"})
                for field in ("support_ids", "refutation_ids", "selected_ids"):
                    self.assertEqual(len(expected[field]), len(set(expected[field])))
                    self.assertTrue(set(expected[field]).issubset(ledger_ids))
                self.assertFalse(set(expected["support_ids"]) & set(expected["refutation_ids"]))
                self.assertEqual(set(expected["selected_ids"]), set(expected["support_ids"]) | set(expected["refutation_ids"]))
                self.assertEqual(expected["selected_ids"], [item for item in ledger_ids if item in expected["selected_ids"]])

    def test_negative_query_has_relative_support_not_absolute_polarity(self):
        case = self.cases["EM-M09"]
        self.assertIs(case["input"]["query"]["positive"], False)
        self.assertIs(case["input"]["interpretations"][0]["positive"], False)
        self.assertEqual(case["expected"], {"status": "SUPPORTED", "support_ids": ["EM-M09-e1"],
                                          "refutation_ids": [], "selected_ids": ["EM-M09-e1"]})

    def test_conflict_gold_retains_interleaved_complete_witnesses(self):
        self.assertEqual(self.cases["EM-W03"]["expected"], {
            "status": "CONFLICT", "support_ids": ["EM-W03-e1", "EM-W03-e3"],
            "refutation_ids": ["EM-W03-e2"], "selected_ids": ["EM-W03-e1", "EM-W03-e2", "EM-W03-e3"]})

    def test_absence_and_different_value_are_not_gold_refutations(self):
        self.assertEqual(self.cases["EM-M04"]["input"]["interpretations"], [])
        self.assertEqual(self.cases["EM-M04"]["expected"]["status"], "UNKNOWN")
        case = self.cases["EM-W04"]
        self.assertNotEqual(case["input"]["query"]["key"]["value"], case["input"]["interpretations"][0]["key"]["value"])
        self.assertEqual(case["expected"]["status"], "UNKNOWN")
        self.assertEqual(case["expected"]["refutation_ids"], [])

    def test_hypothetical_and_unattributed_quotation_are_not_self_reports(self):
        for cid, kind in (("EM-M07", "hypothetical"), ("EM-M08", "quotation")):
            self.assertEqual(self.cases[cid]["input"]["interpretations"][0]["kind"], kind)
            self.assertEqual(self.cases[cid]["expected"]["status"], "UNKNOWN")

    def test_authored_source_quotes_keep_the_declared_speaker_and_value(self):
        other_speaker = self.cases["EM-M05"]["input"]["interpretations"][0]
        self.assertEqual(other_speaker["key"]["entity"], "person:baa")
        self.assertEqual(other_speaker["source"]["content"], "قَالَ بَاءٌ: خَرَجْتُ لِطَلَبِ الْعِلْمِ.")
        other_value = self.cases["EM-W04"]["input"]["interpretations"][0]
        self.assertEqual(other_value["key"]["value"], "ajar")
        self.assertEqual(other_value["source"]["content"], "سَجَّلَ الرَّاصِدُ أَنَّ الْحَاوِيَةَ مُوَارَبَةٌ.")

    def test_transitive_query_dependence_fixture_is_retained(self):
        case = self.cases["EM-W12"]
        request = case["input"]
        self.assertEqual(request["interpretations"][0]["ancestry"], [
            "origin:EM-W12:1", "origin:EM-W12:middle", "query:EM-W12"])
        parents = {node["id"]: node["parents"] for node in request["origins"]}
        self.assertEqual(parents["origin:EM-W12:1"], ["origin:EM-W12:middle"])
        self.assertEqual(parents["origin:EM-W12:middle"], ["query:EM-W12"])
        self.assertEqual(case["expected"]["status"], "UNKNOWN")

    def test_source_tuple_tampering_is_a_deliberate_negative_control(self):
        request = self.cases["EM-W10"]["input"]
        active, interpreted = request["active_sources"][0], request["interpretations"][0]["source"]
        self.assertEqual(active["identity"], interpreted["identity"])
        self.assertEqual(active["revision"], interpreted["revision"])
        self.assertNotEqual(active["content"], interpreted["content"])
        self.assertEqual(self.cases["EM-W10"]["expected"]["status"], "UNKNOWN")

    def test_hidden_motive_and_resource_results_remain_distinct(self):
        for cid in ("EM-H01", "EM-H02"):
            self.assertEqual(self.cases[cid]["expected"]["status"], "UNKNOWN")
            self.assertEqual(self.cases[cid]["metric_category"], "safe_abstention")
        self.assertEqual(self.cases["EM-R01"]["input"]["budget"], 0)
        self.assertEqual(self.cases["EM-R01"]["expected"]["status"], "RESOURCE_LIMIT")
        self.assertEqual(self.cases["EM-R01"]["metric_category"], "resource_boundary")

    def test_authored_registry_is_not_external_truth_authority(self):
        registry = load("authored_registry.json")
        self.assertEqual(registry["authority"], "AUTHORED_SCENARIO_NOT_EMPIRICAL_OR_HUMAN_TESTIMONY")
        registered = set()
        for row in registry["sources"]:
            self.assertEqual(row["source_tuple_sha256"], digest(row["source"]))
            self.assertEqual(row["content_sha256"], sha256(row["source"]["content"].encode("utf-8")).hexdigest())
            self.assertEqual(row["data_origin"], "AUTHORED_SCENARIO")
            self.assertIs(row["external_truth_authority"], False)
            registered.add(row["source_tuple_sha256"])
        for case in self.cases.values():
            sources = case["input"]["active_sources"] + [item["source"] for item in case["input"]["interpretations"]]
            self.assertTrue(all(digest(source) in registered for source in sources))


class EpistemicAgencySourceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load("agency_reference.json")
        cls.raw = (EVIDENCE / cls.reference["source_binding"]["raw_path"].split("epistemic_measurement_v1/", 1)[1]).read_bytes()
        cls.record = json.loads(cls.raw)

    def test_actual_primary_capture_has_independent_digest(self):
        self.assertEqual(sha256(self.raw).hexdigest(), USGS_SHA256)
        self.assertEqual(len(self.raw), 113445)
        self.assertEqual(self.reference["source_binding"]["raw_sha256"], USGS_SHA256)
        self.assertEqual(self.reference["scope"]["data_origin"], "INSTITUTIONAL_OBSERVATION_REPORT")
        self.assertEqual(self.reference["scope"]["query_origin"], "AUTHORED_STRUCTURED_PROBE")

    def test_preferred_field_type_scope_and_time_inspected_directly(self):
        self.assertEqual(self.record["id"], "official20110311054624120_30")
        self.assertEqual(self.record["properties"]["mag"], 9.1)
        self.assertEqual(self.record["properties"]["magType"], "mww")
        self.assertEqual(self.record["properties"]["time"], 1299822384120)
        self.assertEqual(self.record["properties"]["updated"], 1792147089160)
        self.assertEqual(self.record["geometry"]["coordinates"], [142.373, 38.297, 29])
        baseline = self.reference["cases"][0]["input"]["query"]["key"]
        self.assertEqual(baseline, {"axis": "recorded_observation", "entity": "official20110311054624120_30",
                                   "predicate": "magnitude:mww", "value": "9.1", "unit": "dimensionless",
                                   "context": "usgs.preferred-event.v1", "time": "1299822384120", "place": "142.373,38.297,29"})

    def test_alternate_origin_and_uncertainty_are_not_conflated(self):
        origins = self.record["properties"]["products"]["origin"]
        magnitudes = [origin["properties"].get("magnitude") for origin in origins]
        self.assertIn("9.0", magnitudes)
        self.assertIn("9.09", magnitudes)
        self.assertNotIn("magnitude-error", origins[0]["properties"])
        self.assertEqual(self.reference["source_binding"]["uncertainty"], "NOT_DECLARED_FOR_SELECTED_PREFERRED_VALUE")
        alternate = next(case for case in self.reference["cases"] if case["id"] == "USGS-03")
        self.assertEqual(alternate["expected"]["status"], "UNKNOWN")

    def test_agency_probe_does_not_supply_or_certify_its_own_evidence(self):
        for case in self.reference["cases"]:
            self.assertEqual(set(case["input"]), {"query", "budget"})
            self.assertEqual(case["source_profile"], "usgs_snapshot_v1")
            self.assertNotIn("certificate", case["input"])
            self.assertNotIn("interpretations", case["input"])
            self.assertEqual(case["acquisition"], "STRUCTURED_PREINTERPRETED_INPUT")
        self.assertEqual(self.reference["metric_policy"]["external_sensor_validation"], "UNMEASURED")
