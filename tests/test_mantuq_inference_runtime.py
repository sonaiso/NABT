"""Independent edge cases for the explicit-assumption adapter, not Arabic gold."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from tools.mantuq_inference import EvaluationBudget, evaluate, guard_verdict, opposition_shape
from tools.mantuq_inference.evaluator import ROOT
from nabt.errors import resource_limit


def atom(name, positive=True, arguments=None):
    return {"predicate": name, "arguments": arguments or ["case"], "positive": positive}


def request(policy="guarded_cause"):
    slots = {
        "matching": ["premise"],
        "guarded_cause": ["cause", "condition", "blockerAbsence"],
        "opposition": ["premise", "necessaryBridge", "qualified", "countertextAbsence", "usualCaseAbsence"],
        "analogy": ["originRuling", "sharedCause", "transferBridge", "condition", "blockerAbsence"],
    }[policy]
    requirements = [{"slot": s, "atom": atom(s, s not in {"blockerAbsence", "countertextAbsence", "usualCaseAbsence"})} for s in slots]
    conclusion = atom("effect", policy != "opposition")
    relation = None
    if policy == "opposition":
        requirements[0]["atom"] = atom("condition", False)
        relation = {"kind": "necessary", "antecedent": atom("effect"),
                    "consequent": atom("condition"), "basis": "caller_assumption"}
    reading = {"reading_id": "r1", "requirements": requirements,
               "hypotheses": [deepcopy(r["atom"]) for r in requirements],
               "bridge": {"body": [deepcopy(r["atom"]) for r in requirements],
                          "head": deepcopy(conclusion), "basis": "caller_assumption"}}
    result = {"schema": "nabt.mantuq-inference-request.v1", "policy_id": policy,
              "binding": {"source_id": "fixture", "source_text": "مثال صوري مشروط لا شاهد منقول",
                          "scope": "s", "context": "speaker=a;addressee=b", "time": "t1"},
              "conclusion": conclusion, "readings": [reading]}
    if policy == "opposition":
        result["contrast_kind"] = "condition"
        reading["necessary_relation"] = relation
    return result


class ConditionalAdapter(unittest.TestCase):
    def test_public_guards_preserve_typed_atom_identity(self):
        bad = {"value": True, "positive": 1, "scope": "x"}
        self.assertEqual(guard_verdict("direct", [{"role": "premise", "atom": bad}], [bad]), "INVALID_PROFILE")
        good = {"value": 1, "positive": True, "scope": "x"}
        negative = dict(good, positive=False)
        self.assertFalse(opposition_shape(dict(good, value=True), good, negative, negative))
        self.assertFalse(opposition_shape(good, good, dict(negative, positive=0), negative))
        self.assertTrue(opposition_shape(good, good, negative, negative))

    def test_no_bridge_cannot_be_created_from_complete_guards(self):
        p = request(); p["readings"][0]["bridge"] = None
        r = evaluate(p)
        self.assertEqual(r["status"], "UNKNOWN")
        self.assertEqual(r["readings"][0]["guard_status"], "SUPPORTED_PREMISES")
        self.assertFalse(r["conditional_consequence"])

    def test_missing_negative_blocker_is_not_default_negation(self):
        p = request(); p["readings"][0]["hypotheses"].pop()
        self.assertEqual(evaluate(p)["status"], "UNKNOWN")

    def test_opposed_obligation_does_not_refute_conclusion(self):
        p = request(); p["readings"][0]["hypotheses"][-1]["positive"] = True
        r = evaluate(p)
        self.assertEqual(r["status"], "REFUTED")
        self.assertEqual(r["reason"], "REQUIRED_PREMISE_OPPOSED_NOT_CONCLUSION_NEGATION")

    def test_conflict_is_retained_and_does_not_explode(self):
        p = request(); p["readings"][0]["hypotheses"].append(atom("cause", False))
        r = evaluate(p)
        self.assertEqual(r["status"], "CONFLICT")
        self.assertFalse(r["conditional_consequence"])

    def test_incomplete_alternative_is_not_discarded(self):
        p = request(); p["readings"][0]["bridge"] = None
        p["readings"].append(dict(deepcopy(p["readings"][0]), reading_id="r2", hypotheses=None))
        r = evaluate(p)
        self.assertEqual(r["status"], "UNKNOWN")
        self.assertEqual(len(r["readings"]), 2)

    def test_budget_exhaustion_distinct_from_unknown(self):
        r = evaluate(request(), budget=EvaluationBudget(max_readings=0))
        self.assertEqual(r["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(r["declared_request_scan_complete"])
        with self.assertRaises(ValueError):
            EvaluationBudget(max_readings=True)

    def test_authority_flags_and_malformed_scalars_rejected(self):
        for key in ("proof_of_completeness", "is_empirical_reality", "confidence_score", "licensed"):
            p = request(); p[key] = True
            self.assertEqual(evaluate(p)["status"], "INVALID")
        p = request(); p["conclusion"]["positive"] = 1
        self.assertEqual(evaluate(p)["status"], "INVALID")
        p = request(); p["binding"]["source_text"] = "\ud800"
        self.assertEqual(evaluate(p)["status"], "INVALID")

    def test_duplicate_or_aliased_obligations_rejected(self):
        p = request(); p["readings"][0]["requirements"][1]["atom"] = atom("cause")
        self.assertEqual(evaluate(p)["status"], "INVALID")
        p = request(); p["readings"].append(deepcopy(p["readings"][0]))
        self.assertEqual(evaluate(p)["status"], "INVALID")

    def test_bridge_and_scope_substitution_rejected(self):
        p = request(); p["readings"][0]["bridge"]["head"]["arguments"] = ["other"]
        self.assertEqual(evaluate(p)["status"], "INVALID")
        p = request(); p["readings"][0]["hypotheses"][0]["arguments"] = ["other-time"]
        self.assertEqual(evaluate(p)["status"], "UNKNOWN")

    def test_opposition_needs_typed_necessity_not_forward_rule(self):
        p = request("opposition"); p["readings"][0]["necessary_relation"] = None
        self.assertEqual(evaluate(p)["status"], "UNKNOWN")
        p = request("opposition"); relation = p["readings"][0]["necessary_relation"]
        relation["antecedent"], relation["consequent"] = relation["consequent"], relation["antecedent"]
        self.assertEqual(evaluate(p)["status"], "INVALID")
        p = request("opposition"); p["contrast_kind"] = "name"
        self.assertEqual(evaluate(p)["status"], "REFUTED")

    def test_opposition_distinct_countertext_and_usual_case_guards(self):
        for slot in ("countertextAbsence", "usualCaseAbsence"):
            p = request("opposition")
            p["readings"][0]["hypotheses"] = [a for a in p["readings"][0]["hypotheses"] if a["predicate"] != slot]
            self.assertEqual(evaluate(p)["status"], "UNKNOWN")

    def test_native_timeout_is_structured(self):
        with patch("tools.mantuq_inference.evaluator._native_consequence", side_effect=subprocess.TimeoutExpired("lean", 60)):
            r = evaluate(request())
        self.assertEqual(r["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(r["conditional_consequence"])

    def test_native_parser_resource_limit_preserves_details(self):
        with patch("tools.mantuq_inference.evaluator._native_consequence",
                   side_effect=resource_limit("statement budget", maximum=256)):
            r = evaluate(request())
        self.assertEqual(r["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(r["readings"][0]["error"]["code"], "RESOURCE_LIMIT")
        self.assertEqual(r["readings"][0]["error"]["details"], {"maximum": 256})

    def test_native_string_resource_limit_stays_exhaustion(self):
        with patch("tools.mantuq_inference.evaluator._native_consequence",
                   side_effect=ValueError("RESOURCE_LIMIT: source or query too large")):
            r = evaluate(request())
        self.assertEqual(r["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(r["readings"][0]["error"]["code"], "RESOURCE_LIMIT")

    def test_large_explicit_budget_does_not_override_native_bound(self):
        p = request("matching")
        p["readings"][0]["hypotheses"].extend(atom("extra_" + str(i)) for i in range(400))
        r = evaluate(p, budget=EvaluationBudget(max_hypotheses=512, max_total_atoms=1000))
        self.assertEqual(r["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(r["conditional_consequence"])

    def test_target_counterevidence_alone_is_not_a_contradiction(self):
        p = request("matching"); p["readings"][0]["bridge"] = None
        p["readings"][0]["hypotheses"] = [atom("effect", False)]
        r = evaluate(p)
        self.assertEqual(r["status"], "UNKNOWN")
        self.assertTrue(r["readings"][0]["conclusion_counterevidence"])

    def test_analogy_missing_transfer_and_actual_branch(self):
        p = request("analogy")
        p["readings"][0]["hypotheses"] = [a for a in p["readings"][0]["hypotheses"] if a["predicate"] != "transferBridge"]
        self.assertEqual(evaluate(p)["status"], "UNKNOWN")
        p = request("analogy"); p["readings"][0]["hypotheses"][1]["arguments"] = ["different-branch"]
        self.assertEqual(evaluate(p)["status"], "UNKNOWN")

    def test_extra_independent_guards_are_not_collapsed(self):
        p = request(); reading = p["readings"][0]
        extra = {"slot": "blockerAbsence:second_path", "atom": atom("other_blocker", False)}
        reading["requirements"].append(extra)
        reading["bridge"]["body"].append(deepcopy(extra["atom"]))
        self.assertEqual(evaluate(p)["status"], "UNKNOWN")


class NativeConditionalAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((ROOT / "formal/.lake/build/bin" / name).is_file() for name in ("verifiedReading", "classicalSemanticProbe")):
            raise unittest.SkipTest("build existing native verifiedReading and classicalSemanticProbe")

    def test_all_four_conditional_profiles_replay_in_native_lean(self):
        for policy in ("matching", "guarded_cause", "opposition", "analogy"):
            with self.subTest(policy=policy):
                r = evaluate(request(policy))
                self.assertEqual(r["status"], "SUPPORTED", r)
                self.assertTrue(r["conditional_consequence"])
                self.assertFalse(r["semantic_bridge_proved"])
                self.assertFalse(r["occurrence_classification_proved"])
                self.assertFalse(r["world_truth_established"])
                self.assertFalse(r["all_arabic_complete"])
                self.assertEqual(r["readings"][0]["proof"]["kind"], "generated_assumption_transcript")

    def test_native_clean_support_postcondition_is_checked(self):
        receipt = evaluate(request())["readings"][0]["proof"]["lean"]
        receipt["execution"].update(status="CONFLICT", negative=True, clean_positive=False)
        with patch("tools.mantuq_inference.evaluator.mantuq_mafhum.derive_controlled", return_value=receipt):
            r = evaluate(request())
        self.assertEqual(r["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(r["conditional_consequence"])

    def test_all_readings_must_support_even_with_one_valid_proof(self):
        p = request(); other = deepcopy(p["readings"][0]); other["reading_id"] = "other"
        other["hypotheses"].pop(); p["readings"].append(other)
        r = evaluate(p)
        self.assertEqual(r["status"], "UNKNOWN")
        self.assertEqual([a["status"] for a in r["readings"]], ["SUPPORTED", "UNKNOWN"])

    def test_every_context_field_changes_transcript_identity(self):
        baseline = evaluate(request())["binding_sha256"]
        for field in ("source_id", "source_text", "scope", "context", "time"):
            p = request(); p["binding"][field] += "_different"
            result = evaluate(p)
            self.assertEqual(result["status"], "SUPPORTED")
            self.assertNotEqual(result["binding_sha256"], baseline)


if __name__ == "__main__":
    unittest.main()
