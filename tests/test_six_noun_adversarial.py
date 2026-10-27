"""Independent authority/binding attacks, not evidence of Arabic completeness.

The temporary executable and mocked subprocess in transport tests are explicit
fixtures. They exercise rejection of corrupted wire replies; they never count
as native execution or as a linguistic oracle. Native linguistic controls live
in a separate class and use the independently frozen reference material.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from nabt import foundation
from nabt.errors import NabtError
from tests._transport_native import require_native
from tools.linguistic_truth import six_noun as adapter
from tools import benchmark_six_noun_acquisition as benchmark


TEXT = "جَاءَ أَبُو زَيْدٍ"
CONTEXT = "نص تعليمي؛ لا تعيين لشخص أو إثبات لواقعة"


def request(text=TEXT, *, source_id="independent-adversarial", context=CONTEXT):
    return {"source": {"id": source_id, "revision": sha256(text.encode()).hexdigest(),
                       "text": text}, "context": context}


class SixNounIndependentInputAttacks(unittest.TestCase):
    def test_direct_api_foundation_denial_precedes_all_other_work(self):
        error = NabtError("DENIED_FOR_TEST", "foundation unavailable", status="DEFER")
        with patch.object(foundation, "require_foundation", side_effect=error), \
                patch.object(adapter, "_review") as review, patch.object(adapter, "_native") as native:
            with self.assertRaises(NabtError):
                adapter.acquire_six_noun(TEXT)
            review.assert_not_called()
            native.assert_not_called()

    def test_caller_cannot_supply_acquired_features_or_certificate(self):
        for key in ("reading", "grammar_certified", "proof", "checker", "receipt", "source_review",
                    "prerequisites", "companion_meaning", "rule_id", "orthographic_bridge",
                    "node_trace", "nodes", "transition_trace"):
            with self.subTest(key=key), patch.object(adapter, "_native") as native:
                with self.assertRaises(TypeError):
                    adapter.acquire_six_noun(TEXT, **{key: True})
                native.assert_not_called()

    def test_invalid_raw_types_encoding_and_marks_do_not_load_sources(self):
        inputs = (True, 116, {}, b"\xff", "\ud800", "", "َجَاءَ أَبُو زَيْدٍ",
                  "جَاءَ أَبَُو زَيْدٍ", "جَاءَ أَبُُو زَيْدٍ", "جَاءَ أَبُو زَيْدٍّّ")
        with patch.object(adapter, "_review") as review, patch.object(adapter, "_native") as native:
            for value in inputs:
                with self.subTest(value=repr(value)):
                    result = adapter.acquire_six_noun(value)
                    self.assertEqual(result["status"], "INVALID_INPUT")
                    self.assertEqual(result["claims"], [])
                    self.assertFalse(result["native_checked"])
            review.assert_not_called()
            native.assert_not_called()

    def test_request_budget_exhaustion_is_not_language_rejection(self):
        with patch.object(adapter, "_review") as review, patch.object(adapter, "_native") as native:
            result = adapter.acquire_six_noun("س" * adapter._MAX_INPUT_BYTES)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["linguistic_rejection"])
            self.assertEqual(result["claims"], [])
            review.assert_not_called()
            native.assert_not_called()

    def test_source_failure_does_not_become_linguistic_invalidity(self):
        with patch.object(adapter, "_review", side_effect=ValueError("SOURCE_CHANGED")), \
                patch.object(adapter, "_native") as native:
            result = adapter.acquire_six_noun(TEXT)
            self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
            self.assertEqual(result["claims"], [])
            self.assertFalse(result["linguistic_rejection"])
            native.assert_not_called()

    def test_timeout_is_not_absence_of_licensed_readings(self):
        with patch.object(adapter, "_native", side_effect=subprocess.TimeoutExpired("fixture", 30)):
            result = adapter.acquire_six_noun(TEXT)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["linguistic_rejection"])
            self.assertEqual(result["claims"], [])

    def test_receipt_depth_exhaustion_has_no_proof_authority(self):
        with patch.object(adapter, "_native", side_effect=RecursionError("transport depth fixture")):
            result = adapter.acquire_six_noun(TEXT)
            self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
            self.assertFalse(result["native_checked"])
            self.assertFalse(result["linguistic_rejection"])
            self.assertEqual(result["claims"], [])

    def test_declared_node_passages_exist_in_the_independent_frozen_review(self):
        # Static documentary cross-reference integrity, not native execution.
        passages = {row["id"] for row in adapter._review()["passages"]}
        checked = 0
        for case in benchmark._load_reference()["cases"]:
            if case["expected"]["reading_assessment"] != "FULL_FORM_LICENSE_EXPECTED":
                continue
            inp = case["input"]
            replay = adapter._expected(request(inp["text"], source_id=inp["source_id"], context=inp["context"]))
            self.assertEqual(len(replay["node_trace"]), 5, case["id"])
            for node in replay["node_trace"]:
                with self.subTest(case=case["id"], node=node["node_id"]):
                    self.assertEqual(node["rule_source_review_sha256"], adapter._REVIEW_SHA)
                    self.assertTrue(node["passage_ids"])
                    self.assertTrue(set(node["passage_ids"]).issubset(passages))
                    checked += 1
        self.assertGreater(checked, 0)


class SixNounIndependentTransportAttacks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nabt-six-noun-wire-test-")
        self.addCleanup(self.temp.cleanup)
        self.executable = Path(self.temp.name) / "fixture-not-an-executable"
        self.executable.write_bytes(b"explicit transport fixture; not Lean")
        self.req = request()

    def invoke_wire(self, raw, *, returncode=0):
        result = subprocess.CompletedProcess([str(self.executable)], returncode, raw, b"")
        with patch.object(adapter, "_EXECUTABLE", self.executable), \
                patch.object(adapter.subprocess, "run", return_value=result):
            return adapter._native(self.req)

    def test_exact_postcondition_mutations_are_rejected(self):
        # Production replay is used only to manufacture an otherwise consistent
        # wire fixture, not to generate any linguistic expected answer.
        baseline = adapter._expected(self.req)
        mutations = []
        for key, value in (("id", "another-source"), ("revision", "0" * 64),
                           ("text", TEXT + " ")):
            changed = deepcopy(baseline)
            changed["source"][key] = value
            mutations.append(("source." + key, changed))
        for key, value in (("context", "مقام مختلف"), ("grammar_certified", 1),
                           ("foundation_complete", 0), ("strict_language_accepted", True),
                           ("whole_arabic_complete", True), ("external_truth_established", True),
                           ("intended_sense_established", True), ("caller_proof_authority", True)):
            changed = deepcopy(baseline)
            changed[key] = value
            mutations.append((key, changed))
        for key, value in (("start_byte", True), ("end_byte", 0.0),
                           ("word", "أَخُو"), ("grammatical_case", "jarr")):
            changed = deepcopy(baseline)
            self.assertIsNotNone(changed["reading"])
            changed["reading"][key] = value
            mutations.append(("reading." + key, changed))
        changed = deepcopy(baseline)
        changed["source_projection"]["cells"][0] = float(changed["source_projection"]["cells"][0])
        mutations.append(("source_projection.cells.integer_type", changed))
        changed = deepcopy(baseline)
        changed["orthographic_bridge"]["raw"] += " "
        mutations.append(("orthographic_bridge.raw", changed))
        for name, changed in mutations:
            with self.subTest(field=name), self.assertRaises(ValueError):
                self.invoke_wire(adapter._wire(changed) + b"\n")

    def test_duplicate_fields_and_nonfinite_json_are_rejected(self):
        payloads = (b'{"source":{"id":"first","id":"second"}}\n',
                    b'{"grammar_certified":false,"grammar_certified":true}\n',
                    b'{"reading":{"start_byte":NaN}}\n', b'{"number":Infinity}\n')
        for raw in payloads:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.invoke_wire(raw)

    def test_extra_reply_and_nonzero_exit_are_rejected(self):
        wire = adapter._wire(adapter._expected(self.req)) + b"\n"
        with self.assertRaises(ValueError):
            self.invoke_wire(wire + wire)
        with self.assertRaises(ValueError):
            self.invoke_wire(wire, returncode=1)

    def test_native_resource_receipt_is_not_negative_linguistic_result(self):
        with self.assertRaises(OverflowError):
            self.invoke_wire(b'{"status":"RESOURCE_LIMIT"}\n')

    def test_executable_change_during_execution_is_rejected(self):
        raw = adapter._wire(adapter._expected(self.req)) + b"\n"
        def changed_binary(*args, **kwargs):
            self.executable.write_bytes(b"different fixture")
            return subprocess.CompletedProcess(args[0], 0, raw, b"")
        with patch.object(adapter, "_EXECUTABLE", self.executable), \
                patch.object(adapter.subprocess, "run", side_effect=changed_binary), \
                self.assertRaises(ValueError):
            adapter._native(self.req)

    def test_node_trace_cannot_be_relinked_or_numerically_coerced(self):
        # These are corruption fixtures, not an alternate linguistic oracle.
        baseline = adapter._expected(self.req)
        expected_ids = ["prefix", "noun", "complement", "idafa", "sentence"]
        self.assertEqual([node["node_id"] for node in baseline["node_trace"]], expected_ids)
        mutations = []
        for index, original in enumerate(baseline["node_trace"]):
            for key, value in (("node_id", "caller-node"), ("rule_id", "caller-rule"),
                               ("law_id", "another-law"), ("context", "another-context"),
                               ("start_byte", True), ("end_byte", float(original["end_byte"])),
                               ("raw", original["raw"] + " "), ("licensed", False),
                               ("output_number", original["output_number"] + "0"),
                               ("alphabet_id", "another-alphabet"),
                               ("number_domain", "another-number-domain"),
                               ("scope", "ALL_ARABIC_ACCEPTED"),
                               ("rule_source_review_sha256", "0" * 64),
                               ("passage_ids", ["caller-authority"]),
                               ("prerequisites", []),
                               ("alternatives", ["invented-exclusive-reading"]),
                               ("unresolved", [])):
                changed = deepcopy(baseline)
                changed["node_trace"][index][key] = value
                if adapter._wire(changed) != adapter._wire(baseline):
                    mutations.append((original["node_id"] + "." + key, changed))
            changed = deepcopy(baseline)
            changed["node_trace"][index]["source"]["id"] = "other-occurrence"
            mutations.append((original["node_id"] + ".source.id", changed))
            changed = deepcopy(baseline)
            changed["node_trace"][index]["output_cells"][0] = float(original["output_cells"][0])
            mutations.append((original["node_id"] + ".output_cells.type", changed))
            changed = deepcopy(baseline)
            changed["node_trace"][index]["output_face"]["state"] = float(original["output_face"]["state"])
            mutations.append((original["node_id"] + ".output_face.type", changed))
            changed = deepcopy(baseline)
            changed["node_trace"][index]["children"] = ["sentence"]
            mutations.append((original["node_id"] + ".children.cycle", changed))
            changed = deepcopy(baseline)
            changed["node_trace"][index]["prerequisites"][0]["state"] = "unknown"
            mutations.append((original["node_id"] + ".prerequisite.state", changed))
            changed = deepcopy(baseline)
            changed["node_trace"][index]["prerequisites"][0]["origin"] = "caller-attestation"
            mutations.append((original["node_id"] + ".prerequisite.origin", changed))
            if original["input_cells"]:
                changed = deepcopy(baseline)
                changed["node_trace"][index]["input_cells"][0] = []
                mutations.append((original["node_id"] + ".input_cells.detached", changed))
        for label, trace in (("missing", baseline["node_trace"][:-1]),
                             ("duplicate", baseline["node_trace"] + [baseline["node_trace"][0]]),
                             ("reordered", list(reversed(baseline["node_trace"]))),
                             ("empty", [])):
            changed = deepcopy(baseline)
            changed["node_trace"] = deepcopy(trace)
            mutations.append((label, changed))
        for label, changed in mutations:
            with self.subTest(mutation=label), self.assertRaises(ValueError):
                self.invoke_wire(adapter._wire(changed) + b"\n")


class SixNounIndependentScoreAttacks(unittest.TestCase):
    """Synthetic score fixtures test the comparator, not language or native Lean."""

    @staticmethod
    def fixture(case_id):
        case = next(c for c in benchmark._load_reference()["cases"] if c["id"] == case_id)
        inp = case["input"]
        receipt = {"source": request(inp["text"], source_id=inp["source_id"])["source"],
            "context": inp["context"], "status": "DEFER", "native_checked": True,
            "grammar_certified": False, "claims": [], "linguistic_rejection": False,
            "strict_language_accepted": False, "intended_sense_established": False,
            "speaker_reference_established": False, "world_truth_established": False,
            "external_truth_established": False, "tawatur_established": False,
            "whole_arabic_complete": False,
            "reading": {"grammatical_case": case["expected"]["grammatical_case"],
                        "lexeme": case["expected"]["lexeme"]},
            "residuals": ["COMMON_LETTER_CASE_MISMATCH", "DHU_COMPANIONSHIP_NOT_ACQUIRED"]}
        return case, receipt

    def test_negative_answer_for_another_source_is_not_success(self):
        case, receipt = self.fixture("N01")
        self.assertTrue(benchmark._score(case, receipt)["full_form_analysis"])
        receipt["source"]["id"] = "different-occurrence"
        self.assertFalse(benchmark._score(case, receipt)["full_form_analysis"])

    def test_specific_missing_condition_in_another_context_is_not_success(self):
        case, receipt = self.fixture("D01")
        self.assertTrue(benchmark._score(case, receipt)["alternative_specificity"])
        receipt["context"] += " مقام آخر"
        self.assertFalse(benchmark._score(case, receipt)["alternative_specificity"])

    def test_unlicensed_authority_is_never_safe_abstention(self):
        for flag in ("grammar_certified", "strict_language_accepted", "intended_sense_established",
                     "speaker_reference_established", "world_truth_established", "external_truth_established",
                     "tawatur_established", "whole_arabic_complete"):
            case, receipt = self.fixture("N01")
            receipt[flag] = True
            with self.subTest(flag=flag):
                self.assertFalse(benchmark._score(case, receipt)["full_form_analysis"])


class SixNounIndependentNativeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_native("sixNounAcquisition")

    def test_uncertain_and_wrapped_cases_cannot_acquire_positive_authority(self):
        for text in ("جَاءَ ذُو مَالٍ", "جَاءَ أَبَا زَيْدٍ", "جَاءَ أَبِي زَيْدٍ",
                     "قَالَ عَمْرٌو: «جَاءَ أَبُو زَيْدٍ»", "لَمْ يَجِئْ أَبُو زَيْدٍ",
                     "إِنْ جَاءَ أَبُو زَيْدٍ قُمْتُ"):
            with self.subTest(text=text):
                result = adapter.acquire_six_noun(text, context=CONTEXT)
                self.assertTrue(result["native_checked"], result)
                self.assertNotEqual(result["status"], "CHECKED_SIX_NOUN")
                self.assertFalse(result["grammar_certified"])
                self.assertFalse(result["linguistic_rejection"])
                self.assertEqual(result["claims"], [])

    def test_same_grammar_new_context_never_supplies_reference_or_world_truth(self):
        reports = [adapter.acquire_six_noun(TEXT, context=context)
                   for context in ("تعليم النحو بلا أشخاص", "رواية غير مصادق عليها عن واقعة")]
        for result in reports:
            self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
            for flag in ("strict_language_accepted", "intended_sense_established",
                         "speaker_reference_established", "world_truth_established",
                         "external_truth_established", "tawatur_established", "whole_arabic_complete"):
                self.assertIs(result[flag], False)
        self.assertNotEqual(reports[0]["request_sha256"], reports[1]["request_sha256"])
        self.assertNotEqual(reports[0]["receipt_sha256"], reports[1]["receipt_sha256"])

    def test_original_partial_projection_is_not_silently_promoted(self):
        result = adapter.acquire_six_noun(TEXT, source_id="raw-projection-control", context=CONTEXT)
        self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
        self.assertEqual(foundation.inspect_source(TEXT)["status"], "PARTIAL")
        self.assertFalse(result["source_projection_complete"])
        self.assertFalse(result["foundation_complete"])
        receipt = result["native_receipt"]
        self.assertEqual(receipt["source_projection"]["status"], "INCOMPLETE")
        bridge = result["orthographic_bridge"]
        self.assertEqual(bridge["raw"], TEXT)
        self.assertNotEqual(bridge["canonical"], TEXT)
        self.assertTrue(bridge["canonical_projection_complete"])
        self.assertNotEqual(bridge["profile"], receipt["source_projection"]["alphabet_id"])
        raw = TEXT.encode("utf-8")
        reading = result["reading"]
        self.assertEqual(raw[reading["start_byte"]:reading["end_byte"]], "أَبُو".encode("utf-8"))
        self.assertEqual(result["claims"][0]["source"], result["source"])
        self.assertEqual(result["claims"][0]["context"], CONTEXT)

    def test_unobserved_semantic_prerequisite_is_distinct_from_observed_case_mismatch(self):
        unknown = adapter.acquire_six_noun("جَاءَ ذُو زَيْدٍ", context=CONTEXT)
        wrong_case = adapter.acquire_six_noun("جَاءَ أَبِي زَيْدٍ", context=CONTEXT)
        for result in (unknown, wrong_case):
            self.assertTrue(result["native_checked"], result)
            self.assertEqual(result["status"], "DEFER")
            self.assertFalse(result["grammar_certified"])
            self.assertEqual(result["claims"], [])
            self.assertEqual(result["node_trace"], [])
        unknown_states = {item["name"]: item["state"] for item in unknown["reading"]["prerequisites"]}
        wrong_states = {item["name"]: item["state"] for item in wrong_case["reading"]["prerequisites"]}
        self.assertEqual(unknown_states["dhu_companionship"], "unknown")
        self.assertEqual(unknown_states["required_case_matches_observed_ending"], "affirmed")
        self.assertEqual(wrong_states["required_case_matches_observed_ending"], "denied")

    def test_five_node_trace_preserves_source_and_each_child_output(self):
        result = adapter.acquire_six_noun(TEXT, source_id="five-node-control", context=CONTEXT)
        self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
        trace = result["node_trace"]
        self.assertEqual([n["node_id"] for n in trace], ["prefix", "noun", "complement", "idafa", "sentence"])
        self.assertEqual(result["native_receipt"]["node_trace"], trace)
        self.assertEqual(result["claims"][0]["node_trace"], trace)
        nodes = {node["node_id"]: node for node in trace}
        raw = TEXT.encode("utf-8")
        noun_start = len("جَاءَ ".encode("utf-8"))
        noun_end = noun_start + len("أَبُو".encode("utf-8"))
        spans = {"prefix": (0, noun_start), "noun": (noun_start, noun_end),
                 "complement": (noun_end + 1, len(raw)),
                 "idafa": (noun_start, len(raw)), "sentence": (0, len(raw))}
        edges = {"prefix": [], "noun": [], "complement": [],
                 "idafa": ["noun", "complement"], "sentence": ["prefix", "idafa"]}
        for node in trace:
            with self.subTest(node=node["node_id"]):
                self.assertEqual(node["source"], result["source"])
                self.assertEqual(node["context"], CONTEXT)
                self.assertIs(node["licensed"], True)
                self.assertEqual(node["alphabet_id"], "nabt.a116.v1")
                self.assertEqual(node["number_domain"], "nabt.foundation.projected-cells.bijective116.v1")
                self.assertEqual(node["scope"], "INSTALLED_EXACT_SPELLING_COMMON_LETTER_PROFILE")
                self.assertEqual(node["rule_source_review_sha256"], result["source_review"]["sha256"])
                self.assertTrue(node["passage_ids"])
                self.assertTrue(set(node["passage_ids"]).issubset(result["source_review"]["passage_ids"]))
                self.assertEqual((node["start_byte"], node["end_byte"]), spans[node["node_id"]])
                self.assertEqual(raw[node["start_byte"]:node["end_byte"]], node["raw"].encode("utf-8"))
                self.assertEqual(node["children"], edges[node["node_id"]])
                children = [nodes[child] for child in node["children"]]
                self.assertEqual(node["input_cells"], [child["output_cells"] for child in children])
                self.assertEqual(node["input_faces"], [child["output_face"] for child in children])
                if children:
                    self.assertEqual(node["output_cells"], sum([child["output_cells"] for child in children], []))


if __name__ == "__main__":
    unittest.main()
