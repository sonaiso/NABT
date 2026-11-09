"""Independent acceptance examples for scope, evidence and executable replay.

Gold values and finite truth tables are authored here, not read from compiler
rules. Real native executables check every successful production projection.
"""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from tools.grammar_catalog import scoped_composition as app, composition_arithmetic as arithmetic
from tools.grammar_catalog import composition_quantifier as quantifier, gateway, gateway_links

ROOT = Path(__file__).resolve().parents[1]
NATIVE = all(os.access(ROOT / "formal/.lake/build/bin" / n, os.X_OK) for n in
             ("scopedCompositionProbe", "verifiedReading", "evidenceLifecycleV1", "epistemicMeasurement"))
if os.environ.get("NABT_REQUIRE_COMPOSITION_NATIVE") == "1" and not NATIVE:
    raise RuntimeError("Composition release requires its native reader and existing evidence owners")


def fixture(profile):
    return json.loads((ROOT / f"examples/io_gateway/composition_{profile}.json").read_text())


def arithmetic_request(text):
    return {"schema": app.SCHEMA, "profile": "arithmetic", "text": text}


def quantified(text, facts="سالم هو طالب. نادر هو طالب. سالم هو مجتهد. ليس نادر هو مجتهد."):
    return {"schema": app.SCHEMA, "profile": "quantifier", "text": text,
            "domain": ["سالم", "نادر"], "sources": [{"id": "witness", "text": facts, "parents": []}],
            "initial_active": ["scope_policy", "witness"], "events": []}


class CompositionBoundary(unittest.TestCase):
    def test_reject_caller_executable_rank_ast_and_unknown_fields(self):
        for name in ("checker", "approved", "truth", "tree", "law", "confidence"):
            request = arithmetic_request("2+3")
            request[name] = True
            with self.subTest(field=name), self.assertRaises(ValueError):
                app.validate(request)

    def test_no_general_language_or_code_evaluation(self):
        for text in ("__import__('os')", "2(3+4)", "2**3", "1.2+3", "٢+٣", "2=2=2", "(2=2)",
                     "ليس كل طالب حاضر", "كل طالب هو مجتهد. انتهى"):
            profile = "quantifier" if "طالب" in text else "arithmetic"
            request = quantified(text) if profile == "quantifier" else arithmetic_request(text)
            with self.subTest(text=text):
                self.assertEqual(app.evaluate(request)["status"], "DEFER")

    def test_source_bounds_and_ast_depth_are_resources_not_truth(self):
        for text in ("1" * 10, "+".join(["1"] * 33), "(" * 13 + "1" + ")" * 13,
                     "+".join(["1"] * 13), "1" + " " * 2048):
            with self.subTest(text=text):
                r = app.evaluate(arithmetic_request(text))
                self.assertEqual(r["status"], "RESOURCE_LIMIT")
                self.assertFalse(r["chain_complete"])

    def test_nonempty_distinct_canonical_bounded_scope(self):
        for domain in ([], ["سالم", "سالم"], [True], ["scope-with-dash"], ["نتيجة_النطاق"], list("abcde")):
            request = quantified("كل طالب هو مجتهد.")
            request["domain"] = domain
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                app.validate(request)

    def test_missing_native_never_releases_computation(self):
        with patch.object(app, "NATIVE", ROOT / "no-composition-binary"):
            r = app.evaluate(arithmetic_request("2+3*4"))
        self.assertEqual(r["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(r["chain_complete"])
        self.assertIsNone(r["native_check"])


@unittest.skipUnless(NATIVE, "build scopedCompositionProbe and existing source owners")
class ArithmeticNative(unittest.TestCase):
    def evaluated(self, text):
        result = app.evaluate(arithmetic_request(text))
        self.assertTrue(result["native_check"]["native_checked"], result)
        return result

    def test_independent_precedence_associativity_and_rational_gold(self):
        cases = {"2+3*4": 14, "(2+3)*4": 20, "8/4*2": 4, "8/(4*2)": 1,
                 "9-3+2": 8, "9-(3+2)": 4, "2^3^2": 512, "(2^3)^2": 64,
                 "-2^2": -4, "(-2)^2": 4, "1/3+1/6": Fraction(1,2),
                 "1/-2": Fraction(-1,2), "2--3": 5, "2^+3": 8, "5^0": 1}
        for text, expected in cases.items():
            with self.subTest(text=text):
                value = self.evaluated(text)["projection"]["result"]
                self.assertEqual(value["status"], "COMPUTED")
                self.assertEqual(value["value"], {"numerator": str(Fraction(expected).numerator),
                                                 "denominator": str(Fraction(expected).denominator)})
                self.assertIsNone(value["truth"])

    def test_parenthesized_transfer_across_unseen_numbers(self):
        # A separately stated ring identity, not a production-parser oracle.
        for a, b, c in ((7,2,5),(9,4,3),(11,6,2),(2,8,7)):
            first = self.evaluated(f"({a}+{b})*{c}")["projection"]
            other = self.evaluated(f"{a}*{c}+{b}*{c}")["projection"]
            self.assertEqual(first["result"]["value"]["numerator"], str((a+b)*c))
            self.assertEqual(first["result"], other["result"])
            self.assertNotEqual(first["operation_tree"], other["operation_tree"])

    def test_utf8_spans_grouping_and_operator_attachment(self):
        text = " (2 + 3) × 4 "
        r = self.evaluated(text)["projection"]
        self.assertEqual(r["tree"]["op"], "mul")
        self.assertEqual(r["tree"]["children"][0]["op"], "group")
        self.assertEqual(r["operation_tree"], ["mul",["add",["number","2"],["number","3"]],["number","4"]])
        for token in r["tokens"]:
            a, b = token["span"]
            self.assertEqual(text.encode()[a:b].decode(), token["raw"])
        core = r["recursive_tree"]
        self.assertEqual((core["kind"],core["rule"],core["left"]["rule"]), ("binary",12,3))
        self.assertEqual(self.evaluated("6÷3")["projection"]["result"]["value"]["numerator"], "2")

    def test_same_value_same_operations_different_source_still_retained(self):
        a = self.evaluated("2+3*4")
        b = self.evaluated("2 + (3 × 4)")
        self.assertEqual(a["projection"]["operation_tree"], b["projection"]["operation_tree"])
        self.assertNotEqual(a["projection"]["tree"], b["projection"]["tree"])
        self.assertNotEqual(a["source"]["sha256"], b["source"]["sha256"])

    def test_quantity_equation_and_world_claim_are_separate(self):
        for text, truth in (("2+3*4=14", True), ("2+3*4=20", False)):
            r = self.evaluated(text)
            self.assertEqual(r["projection"]["result"]["truth"], truth)
            self.assertEqual(r["projection"]["result"]["sort"], "proposition")
            self.assertIsNone(r["projection"]["result"]["value"])
            self.assertFalse(r["limits"]["world_truth_established"])
        self.assertIsNone(self.evaluated("14")["projection"]["result"]["truth"])

    def test_division_and_exponent_failures_preserve_the_tree(self):
        for text, status, reason in (("1/(3-3)", "BLOCKED", "DIVISION_BY_ZERO"),
                ("0^0", "BLOCKED", "ZERO_TO_ZERO_EXCLUDED"),
                ("2^(-1)", "OUTSIDE_SCOPE", "NON_NATURAL_EXPONENT"),
                ("4^(1/2)", "OUTSIDE_SCOPE", "NON_NATURAL_EXPONENT"),
                ("2^13", "RESOURCE_LIMIT", "EXPONENT_BOUND"),
                ("999999999^2", "RESOURCE_LIMIT", "EXACT_VALUE_BOUND")):
            with self.subTest(text=text):
                r = self.evaluated(text)
                self.assertEqual((r["status"],r["projection"]["result"]["reason"]), (status,reason))
                self.assertIsNone(r["projection"]["result"]["value"])
                self.assertTrue(r["projection"]["trace"])

    def test_proposal_tampering_cannot_pass_native_reparse(self):
        original = arithmetic.project
        def forged(text):
            value = original(text)
            value["tree"]["op"] = "mul"
            return value
        with patch.object(arithmetic, "project", forged):
            result = app.evaluate(arithmetic_request("2+3"))
        self.assertEqual(result["status"], "VERIFICATION_FAILED")
        self.assertFalse(result["chain_complete"])

    def test_native_direct_rejects_invalid_text_without_python(self):
        for text, code in (("1+", "DEFER"), ("01", "DEFER"), ("2 3", "DEFER"),
                           ("x+3", "DEFER"), ("9"*10, "RESOURCE_LIMIT")):
            raw = json.dumps({"law_id":app.LAW_ID,"profile":"arithmetic","text":text}).encode()+b"\n"
            native = json.loads(subprocess.run([str(app.NATIVE)],input=raw,capture_output=True,check=True).stdout)
            self.assertEqual(native["code"], code)


@unittest.skipUnless(NATIVE, "build scopedCompositionProbe and existing source owners")
class QuantifierNative(unittest.TestCase):
    def evaluated(self, request):
        r = app.evaluate(request)
        self.assertTrue(r["chain_complete"], (r["status"],r.get("error"),(r["owner_result"] or {}).get("error")))
        return r

    def test_not_all_and_all_not_have_different_scope_and_judgment(self):
        a = self.evaluated(quantified("ليس كل طالب مجتهدًا"))
        b = self.evaluated(quantified("كل طالب غير مجتهد"))
        self.assertEqual((a["status"],b["status"]), ("SUPPORTED","REFUTED"))
        self.assertNotEqual(a["projection"]["frame"]["scope_tree"],b["projection"]["frame"]["scope_tree"])
        self.assertEqual(a["projection"]["frame"]["alignment"], "AUTHORED_LITERAL_ALIAS_V1")

    def test_exhaustive_two_member_classical_truth_table(self):
        for left, right in product((False,True), repeat=2):
            facts = "سالم هو طالب. نادر هو طالب. " + ("" if left else "ليس ") + "سالم هو مجتهد. "
            facts += ("" if right else "ليس ") + "نادر هو مجتهد."
            for text, truth in (("كل طالب هو مجتهد.",left and right),
                                ("ليس كل طالب هو مجتهد.",not(left and right)),
                                ("كل طالب ليس هو مجتهد.",not left and not right)):
                with self.subTest(left=left,right=right,text=text):
                    self.assertEqual(self.evaluated(quantified(text,facts))["status"],
                                     "SUPPORTED" if truth else "REFUTED")

    def test_withdrawal_changes_judgment_and_irrelevance_preserves_it(self):
        r = self.evaluated(fixture("quantifier")["payload"])
        self.assertEqual([h["status"] for h in r["history"]], ["SUPPORTED","SUPPORTED","UNKNOWN","SUPPORTED"])
        self.assertEqual([h["change"] for h in r["history"]], ["INITIAL","PRESERVED","REVISED","REVISED"])
        self.assertTrue(r["owner_result"]["lifecycle"]["native_checked"])
        self.assertFalse(r["limits"]["domain_completeness_in_world_established"])

    def test_missing_membership_and_foreign_bearer_do_not_ground_scope(self):
        cases = ("سالم هو طالب. سالم هو مجتهد. ليس نادر هو مجتهد.",
                 "سالم هو طالب. نادر هو طالب. سالم هو مجتهد. ليس مازن هو مجتهد.",
                 "سالم هو طالب. نادر هو طالب. سالم هو مجتهد.")
        for facts in cases:
            with self.subTest(facts=facts):
                self.assertEqual(self.evaluated(quantified("ليس كل طالب هو مجتهد.",facts))["status"], "UNKNOWN")

    def test_four_member_upper_boundary_and_outside_scope_counterexample(self):
        request = quantified("كل طالب هو مجتهد.")
        request["domain"] = ["سالم","نادر","ليلى","هدى"]
        request["sources"][0]["text"] = (
            "سالم هو طالب. نادر هو طالب. ليلى هو طالب. هدى هو طالب. "
            "سالم هو مجتهد. نادر هو مجتهد. ليلى هو مجتهد. هدى هو مجتهد. "
            "مازن هو طالب. ليس مازن هو مجتهد.")
        self.assertEqual(self.evaluated(request)["status"], "SUPPORTED")
        request["sources"][0]["text"] = request["sources"][0]["text"].replace(
            "هدى هو مجتهد.", "ليس هدى هو مجتهد.")
        self.assertEqual(self.evaluated(request)["status"], "REFUTED")

    def test_new_names_and_concepts_and_question_force(self):
        request = quantified("هل ليس كل مهندس هو حاضر؟", "ليلى هو مهندس. هدى هو مهندس. ليس هدى هو حاضر.")
        request["domain"] = ["ليلى","هدى"]
        r = self.evaluated(request)
        self.assertEqual(r["status"], "SUPPORTED")
        self.assertEqual(r["projection"]["frame"]["force"], "question")
        self.assertEqual(r["projection"]["frame"]["alignment"], "CONTROLLED_COPULA_V1")
        self.assertNotIn(request["text"], [s["text"] for s in r["owner_result"]["request"]["sources"]])
        for token in r["projection"]["frame"]["tokens"]:
            a,b = token["span"]
            self.assertEqual(request["text"].encode()[a:b].decode(),token["raw"])

    def test_conflicting_witnesses_are_retained_and_block_clean_acceptance(self):
        request = quantified("ليس كل طالب هو مجتهد.")
        request["sources"][0]["text"] += " نادر هو مجتهد."
        r = self.evaluated(request)
        self.assertEqual(r["status"], "CONFLICT")
        h = r["owner_result"]["history"][0]
        self.assertTrue(h["inference"]["positive_support"])
        self.assertTrue(h["inference"]["negative_support"])

    def test_policy_withdrawal_and_dependent_witness(self):
        request = quantified("ليس كل طالب هو مجتهد.")
        request["events"] = [{"id":"withdraw_policy","kind":"withdraw","target":"scope_policy"}]
        r = self.evaluated(request)
        self.assertEqual([h["status"] for h in r["history"]], ["SUPPORTED","UNKNOWN"])
        request = fixture("quantifier")["payload"]
        request["sources"][2]["parents"] = ["color"]
        r = self.evaluated(request)
        self.assertEqual(r["history"][1]["status"], "UNKNOWN")
        self.assertNotIn("counterexample",r["history"][1]["ready_sources"])

    def test_no_question_rule_or_conclusion_smuggling_in_evidence(self):
        for text in ("هل سالم هو مجتهد؟", "إذا سالم هو طالب فإن سالم هو مجتهد.",
                     "النطاق نتيجة_النطاق القضية."):
            request = quantified("كل طالب هو مجتهد.",text)
            with self.subTest(text=text):
                r = app.evaluate(request)
                self.assertEqual(r["status"], "INVALID_INPUT")
                self.assertFalse(r["chain_complete"])

    def test_native_detects_forged_quantifier_rule(self):
        proposal = quantifier.project("ليس كل طالب هو مجتهد.",["سالم","نادر"])
        proposal["clauses"][0]["head"]["positive"] = True
        with self.assertRaises(app.connection.ConnectionMismatch):
            app.native({"law_id":app.LAW_ID,"profile":"quantifier", "text":"ليس كل طالب هو مجتهد.",
                        "domain":["سالم","نادر"]},proposal)


@unittest.skipUnless(NATIVE, "build scopedCompositionProbe and existing source owners")
class ConditionalNative(unittest.TestCase):
    def test_rule_without_antecedent_and_evidence_retraction(self):
        r = app.evaluate(fixture("conditional")["payload"])
        self.assertTrue(r["chain_complete"], r.get("error"))
        self.assertEqual([h["status"] for h in r["history"]], ["UNKNOWN","SUPPORTED","UNKNOWN"])
        self.assertFalse(r["interpretation"]["conditional_is_evidence_of_antecedent"])

    def test_no_converse_or_question_as_fact(self):
        request = fixture("conditional")["payload"]
        c = request["connection"]
        c["query"] = "هل سالم هو مجتهد؟"
        c["sources"][2]["text"] = "سالم يستحق منحة."
        c["initial_active"].append("diligence")
        c["events"] = []
        self.assertEqual(app.evaluate(request)["status"], "UNKNOWN")
        c["sources"][2]["text"] = "هل سالم هو مجتهد؟"
        self.assertEqual(app.evaluate(request)["status"], "INVALID_INPUT")


@unittest.skipUnless(NATIVE, "build scopedCompositionProbe and existing source owners")
class CompositionGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = fixture("arithmetic")
        cls.receipt = gateway.run(cls.request)

    def test_public_boundary_and_independent_replay(self):
        self.assertEqual(self.receipt["status"], "EXECUTED", self.receipt["execution"])
        self.assertEqual(self.receipt["execution"]["owner_result"]["status"], "COMPUTED")
        self.assertTrue(gateway.accept_output(self.receipt,expected_request=self.request)["valid"])

    def test_semantic_tree_value_and_source_mutations_are_rejected(self):
        for field in ("tree","result"):
            changed = deepcopy(self.receipt)
            changed["execution"]["owner_result"]["projection"][field] = {}
            self.assertFalse(gateway.accept_output(changed,expected_request=self.request)["valid"])
        request = deepcopy(self.request)
        request["payload"]["text"] = "(2+3)×4=14"
        self.assertFalse(gateway.accept_output(self.receipt,expected_request=request)["valid"])

    def test_native_quantifier_receipt_and_history_tampering(self):
        request = fixture("quantifier")
        receipt = gateway.run(request)
        self.assertEqual(receipt["status"], "EXECUTED", receipt["execution"])
        self.assertTrue(gateway.accept_output(receipt,expected_request=request)["valid"])
        changed = deepcopy(receipt)
        changed["execution"]["owner_result"]["history"][2]["status"] = "SUPPORTED"
        self.assertFalse(gateway.accept_output(changed,expected_request=request)["valid"])

    def test_reuse_links_are_navigation_not_new_formal_coverage(self):
        links = gateway_links.build("composition.analyze")
        self.assertFalse(links["formal_application_established"])
        self.assertIn("tests/test_scoped_composition.py",{r["path"] for r in links["tests"]})
