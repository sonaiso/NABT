"""Independent source/guard composition cases, authored before the adapter.

The gold comes from acceptance_contract.json and hand-written source clauses,
not from a copy of the production closure or verdict function. Native cases
run the installed Lean checker. Mocks below inspect invocation boundaries only.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tools.mantuq_inference import EvaluationBudget
from tools.mantuq_inference import source_bound


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "evidence/mantuq_source_fold_v1/acceptance_contract.json").read_text())
CASES = {row["id"]: row for row in CONTRACT["cases"]}
QUERY = CONTRACT["query"].encode("utf-8")
BINARY = Path(os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
SEMANTIC = Path(os.environ.get("NABT_CLASSICAL_SEMANTIC_PROBE", ROOT / "formal/.lake/build/bin/classicalSemanticProbe"))
NATIVE_AVAILABLE = all(path.is_file() and os.access(path, os.X_OK) for path in (BINARY, SEMANTIC))
if os.environ.get("NABT_REQUIRE_MANTUQ_SOURCE_FOLD_NATIVE") == "1" and not NATIVE_AVAILABLE:
    raise RuntimeError("NABT_REQUIRE_MANTUQ_SOURCE_FOLD_NATIVE=1 requires executable verifiedReading and classicalSemanticProbe")
PLAN_SCHEMA = "nabt.mantuq-source-plan.v1"


def atom(predicate, positive=True):
    return {"predicate": predicate, "arguments": ["سالم"], "positive": positive}


def fixture(name="clean_explicit_requirements"):
    case = CASES[name]
    return case["source"].encode("utf-8"), {
        "schema": PLAN_SCHEMA,
        "policy_id": "guarded_cause",
        "requirements": deepcopy(CONTRACT["requirements"]),
        "bridge_clause": case["bridge_clause"],
    }


def options(**changed):
    return dict({"source_id": "fixture", "revision": "1", "scope": "s",
                 "context": "speaker=salim", "time": "t1", "checker": BINARY,
                 "semantic_probe": SEMANTIC, "timeout": 20}, **changed)


def evaluate(name="clean_explicit_requirements", **changed):
    raw, plan = fixture(name)
    return source_bound.evaluate_source(raw, QUERY, plan, **options(**changed))


def signed_keys(values):
    return {(a["predicate"], tuple(a["arguments"]), a["positive"]) for a in values}


class SourceBoundInputContract(unittest.TestCase):
    def test_plan_cannot_supply_truth_hypotheses_or_authority(self):
        raw, plan = fixture()
        for field, value in (("hypotheses", [atom("نتيجة")]), ("licensed", True),
                             ("world_truth_established", True), ("rule_adoption_established", True),
                             ("action_authority", "GRANTED"), ("readings", [])):
            with self.subTest(field=field):
                changed = dict(deepcopy(plan), **{field: value})
                result = source_bound.evaluate_source(raw, QUERY, changed, **options(checker="/missing"))
                self.assertEqual(result["status"], "INVALID")
                self.assertIs(result["conditional_consequence"], False)

    def test_boolean_integer_and_clause_identity_aliases_are_rejected(self):
        raw, plan = fixture()
        malformed = []
        for value in (0, 1, "true", None):
            changed = deepcopy(plan)
            changed["requirements"][0]["atom"]["positive"] = value
            malformed.append(changed)
        for value in (True, 3, "c03", "c-1", "c3 ", "c3.0"):
            malformed.append(dict(deepcopy(plan), bridge_clause=value))
        for changed in malformed:
            with self.subTest(plan=changed):
                result = source_bound.evaluate_source(raw, QUERY, changed, **options(checker="/missing"))
                self.assertEqual(result["status"], "INVALID")
                self.assertIs(result["conditional_consequence"], False)

    def test_invalid_timeout_does_not_execute_native(self):
        raw, plan = fixture()
        for timeout in (True, 0, -1, 61, 7.5, float("nan"), float("inf"), "20"):
            with self.subTest(timeout=timeout), patch("subprocess.run", side_effect=AssertionError("native called")):
                result = source_bound.evaluate_source(raw, QUERY, plan, **options(timeout=timeout))
                self.assertEqual(result["status"], "INVALID")
                self.assertIs(result["conditional_consequence"], False)

    def test_budget_type_cannot_be_supplied_as_untyped_data(self):
        raw, plan = fixture()
        for budget in (True, 1, {"max_readings": 1}):
            with self.subTest(budget=budget):
                result = source_bound.evaluate_source(raw, QUERY, plan, **options(budget=budget, checker="/missing"))
                self.assertEqual(result["status"], "INVALID")
                self.assertIs(result["conditional_consequence"], False)

    def test_required_native_gate_rejects_missing_either_executable(self):
        for module in ("tests.test_mantuq_source_bound", "tests.test_mantuq_source_fold"):
            for missing in ("NABT_VERIFIED_READING", "NABT_CLASSICAL_SEMANTIC_PROBE"):
                env = dict(os.environ, NABT_REQUIRE_MANTUQ_SOURCE_FOLD_NATIVE="1",
                           NABT_VERIFIED_READING=str(BINARY), NABT_CLASSICAL_SEMANTIC_PROBE=str(SEMANTIC))
                env[missing] = str(ROOT / "nonexistent-native-acceptance-executable")
                run = subprocess.run([sys.executable, "-c", "import importlib; importlib.import_module(" + repr(module) + ")"],
                                     cwd=ROOT, env=env, capture_output=True, text=True, timeout=10)
                with self.subTest(module=module, missing=missing):
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn("NABT_REQUIRE_MANTUQ_SOURCE_FOLD_NATIVE=1", run.stderr)


@unittest.skipUnless(NATIVE_AVAILABLE, "build verifiedReading and classicalSemanticProbe; native acceptance requires both")
class SourceBoundNativeContract(unittest.TestCase):
    def test_frozen_source_and_conditional_matrix(self):
        for case in CONTRACT["cases"]:
            with self.subTest(case=case["id"]):
                result = evaluate(case["id"])
                self.assertEqual(result["schema"], "nabt.mantuq-source-result.v1")
                self.assertEqual(result["status"], case["conditional_status"], result)
                self.assertIs(result["conditional_consequence"], case["conditional_consequence"])
                self.assertEqual(result["source_answer"]["answer"]["status"], case["source_query_status"])
                self.assertEqual(result["input_binding"]["source_text"], case["source"])
                self.assertEqual(result["input_binding"]["query_text"], CONTRACT["query"])
                self.assertIs(result["limits"]["world_truth_established"], False)
                self.assertIs(result["limits"]["all_arabic_complete"], False)
                self.assertIs(result["limits"]["rule_adoption_established"], False)
                self.assertEqual(result["limits"]["action_authority"], "NONE")

    def test_all_full_counterevidence_reaches_conditional_request(self):
        for name in ("blocker_conflict", "opposed_target", "unrelated_conflict", "derived_tainted_requirement"):
            with self.subTest(case=name):
                result = evaluate(name)
                certificate = result["source_answer"]["analysis_certificate"]["kernel_certificate"]
                hypotheses = result["conditional_request"]["readings"][0]["hypotheses"]
                self.assertEqual(signed_keys(hypotheses), signed_keys(certificate["known"]))
                self.assertNotEqual(signed_keys(certificate["known"]), signed_keys(certificate["clean_known"]))

    def test_tainted_requirement_is_not_reasserted_as_a_fresh_fact(self):
        result = evaluate("derived_tainted_requirement")
        self.assertEqual((result["status"], result["reason"]), ("DEFER", "CONTESTED_SOURCE_PREMISE"))
        self.assertIsNone(result["conditional_result"])
        cause = next(r for r in result["source_witnesses"]["requirements"] if r["slot"] == "cause")
        self.assertIsNotNone(cause["full_witness"])
        self.assertIsNone(cause["clean_witness"])
        self.assertIsNone(cause["opposite_full_witness"])

    def test_withdrawing_clean_alternative_restores_defer(self):
        supported = evaluate("clean_alternative_to_tainted_requirement")
        withdrawn = evaluate("derived_tainted_requirement", revision="2")
        self.assertEqual(supported["status"], "SUPPORTED")
        self.assertEqual(withdrawn["status"], "DEFER")
        self.assertIs(withdrawn["conditional_consequence"], False)
        self.assertEqual(withdrawn["input_binding"]["revision"], "2")

    def test_duplicate_support_and_clause_occurrences_survive(self):
        duplicated = evaluate("duplicate_independent_support")
        single = evaluate()
        raw, plan = fixture("duplicate_independent_support")
        without_both = raw.replace("سالم هو سبب.\n".encode(), b"")
        plan["bridge_clause"] = "c2"
        removed = source_bound.evaluate_source(without_both, QUERY, plan, **options(revision="3"))
        self.assertEqual((duplicated["status"], single["status"], removed["status"]),
                         ("SUPPORTED", "SUPPORTED", "UNKNOWN"))
        spans = duplicated["source_answer"]["analysis_certificate"]["source_clauses"]
        self.assertEqual([s["id"] for s in spans], ["c0", "c1", "c2", "c3", "c4"])
        self.assertEqual(spans[0]["text"], spans[1]["text"])
        self.assertNotEqual(spans[0]["byte_start"], spans[1]["byte_start"])

    def test_missing_bridge_is_not_filled_from_a_supported_source_answer(self):
        raw, plan = fixture()
        plan["bridge_clause"] = None
        result = source_bound.evaluate_source(raw, QUERY, plan, **options())
        self.assertEqual(result["source_answer"]["answer"]["status"], "SUPPORTED")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIs(result["conditional_consequence"], False)

    def test_bridge_is_an_exact_original_source_rule(self):
        raw, plan = fixture()
        for clause in ("c0", "c99"):
            with self.subTest(clause=clause):
                result = source_bound.evaluate_source(raw, QUERY, dict(plan, bridge_clause=clause), **options())
                self.assertEqual(result["status"], "INVALID")
        altered = deepcopy(plan)
        altered["requirements"][1]["atom"] = atom("شرطآخر")
        result = source_bound.evaluate_source(raw, QUERY, altered, **options())
        self.assertEqual(result["status"], "INVALID")
        result = source_bound.evaluate_source(raw, "هل سالم هو مختلف؟\n".encode(), plan, **options())
        self.assertEqual(result["status"], "INVALID")

    def test_negative_query_support_is_not_positive_literal_polarity(self):
        raw = ("سالم هو سبب.\nسالم هو شرط.\nليس سالم هو مانع.\n"
               "إذا سالم هو سبب و سالم هو شرط و ليس سالم هو مانع فإن ليس سالم هو نتيجة.\n").encode()
        _, plan = fixture()
        query = "هل ليس سالم هو نتيجة؟\n".encode()
        result = source_bound.evaluate_source(raw, query, plan, **options())
        self.assertEqual(result["status"], "SUPPORTED", result)
        self.assertIs(result["conditional_request"]["conclusion"]["positive"], False)
        self.assertIs(result["source_answer"]["verification"]["native_receipt"]["positive"], True)
        self.assertIs(result["source_answer"]["verification"]["native_receipt"]["negative"], False)

    def test_opposition_requires_a_distinct_correctly_directed_source_relation(self):
        requirements = [
            {"slot": "premise", "atom": atom("شرط", False)},
            {"slot": "necessaryBridge", "atom": atom("ضرورة")},
            {"slot": "qualified", "atom": atom("قيد")},
            {"slot": "countertextAbsence", "atom": atom("نصمانع", False)},
            {"slot": "usualCaseAbsence", "atom": atom("غالب", False)},
        ]
        raw = ("ليس سالم هو شرط.\nسالم هو ضرورة.\nسالم هو قيد.\n"
               "ليس سالم هو نصمانع.\nليس سالم هو غالب.\n"
               "إذا سالم هو نتيجة فإن سالم هو شرط.\n"
               "إذا ليس سالم هو شرط و سالم هو ضرورة و سالم هو قيد و ليس سالم هو نصمانع و ليس سالم هو غالب فإن ليس سالم هو نتيجة.\n").encode()
        plan = {"schema": PLAN_SCHEMA, "policy_id": "opposition", "requirements": requirements,
                "bridge_clause": "c6", "contrast_kind": "condition", "necessary_clause": "c5"}
        query = "هل ليس سالم هو نتيجة؟\n".encode()
        result = source_bound.evaluate_source(raw, query, plan, **options())
        self.assertEqual(result["status"], "SUPPORTED", result)
        missing = source_bound.evaluate_source(raw, query, dict(plan, necessary_clause=None), **options())
        self.assertEqual(missing["status"], "UNKNOWN")
        reversed_raw = raw.replace("إذا سالم هو نتيجة فإن سالم هو شرط.".encode(),
                                   "إذا سالم هو شرط فإن سالم هو نتيجة.".encode())
        invalid = source_bound.evaluate_source(reversed_raw, query, plan, **options())
        self.assertEqual(invalid["status"], "INVALID")

    def test_zero_budget_and_native_unavailability_never_grant_a_consequence(self):
        exhausted = evaluate(budget=EvaluationBudget(max_readings=0))
        self.assertEqual(exhausted["status"], "RESOURCE_EXHAUSTED")
        self.assertIs(exhausted["conditional_consequence"], False)
        unavailable = evaluate(checker="/missing-native-checker")
        self.assertEqual(unavailable["status"], "VERIFICATION_UNAVAILABLE")
        self.assertIs(unavailable["conditional_consequence"], False)

    def test_installed_opposition_refusal_is_not_changed_into_taint_defer(self):
        # Name/innama are categorically refused by the installed source policy.
        # The source's tainted necessity witness must not erase that refusal.
        raw = ("سالم هو أصل.\nليس سالم هو أصل.\nإذا سالم هو أصل فإن سالم هو ضرورة.\n"
               "ليس سالم هو شرط.\nسالم هو قيد.\nليس سالم هو نصمانع.\nليس سالم هو غالب.\n"
               "إذا سالم هو نتيجة فإن سالم هو شرط.\n"
               "إذا ليس سالم هو شرط و سالم هو ضرورة و سالم هو قيد و ليس سالم هو نصمانع و ليس سالم هو غالب فإن ليس سالم هو نتيجة.\n").encode()
        plan = {"schema": PLAN_SCHEMA, "policy_id": "opposition", "requirements": [
            {"slot": "premise", "atom": atom("شرط", False)},
            {"slot": "necessaryBridge", "atom": atom("ضرورة")},
            {"slot": "qualified", "atom": atom("قيد")},
            {"slot": "countertextAbsence", "atom": atom("نصمانع", False)},
            {"slot": "usualCaseAbsence", "atom": atom("غالب", False)}],
            "bridge_clause": "c8", "necessary_clause": "c7", "contrast_kind": "name"}
        query = "هل ليس سالم هو نتيجة؟\n".encode()
        for contrast in ("name", "innama"):
            with self.subTest(contrast=contrast):
                result = source_bound.evaluate_source(raw, query, dict(plan, contrast_kind=contrast), **options())
                self.assertEqual(result["source_answer"]["answer"]["status"], "DEFER")
                self.assertEqual(result["status"], "REFUTED")
                self.assertIs(result["conditional_consequence"], False)
                self.assertEqual(result["conditional_result"]["readings"][0]["reason"],
                                 "SOURCE_POLICY_DOES_NOT_LICENSE_CONTRAST")

    def test_original_native_timeout_is_forwarded_to_every_native_call(self):
        real_run = subprocess.run
        with patch("subprocess.run", wraps=real_run) as observed:
            result = evaluate(timeout=7)
        self.assertEqual(result["status"], "SUPPORTED", result)
        calls = [call for call in observed.call_args_list
                 if call.args and Path(str(call.args[0][0])).name in {"verifiedReading", "classicalSemanticProbe"}]
        self.assertTrue(calls)
        self.assertEqual({Path(str(call.args[0][0])).name for call in calls},
                         {"verifiedReading", "classicalSemanticProbe"})
        self.assertEqual({call.kwargs.get("timeout") for call in calls}, {7})
        self.assertEqual(result["budget"]["native_timeout_seconds"], 7)

    def test_outside_ground_language_is_not_normalized_into_an_accepted_reading(self):
        _, plan = fixture()
        for raw in ("سالم سبب.\n".encode(), "هل سالم هو سبب؟\n".encode(),
                    "ليس كل طالب حاضرًا.\n".encode()):
            with self.subTest(source=raw):
                result = source_bound.evaluate_source(raw, QUERY, plan, **options())
                self.assertNotEqual(result["status"], "SUPPORTED")
                self.assertIs(result["conditional_consequence"], False)


if __name__ == "__main__":
    unittest.main()
