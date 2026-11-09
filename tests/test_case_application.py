"""Hand-authored case contrasts over the real installed reading/revision owners.

Gold outcomes are independent of the policy template and its requirement list.
Mocks only test unavailable infrastructure and transport rejection boundaries.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import case_application as app, gateway, gateway_links

ROOT = Path(__file__).resolve().parents[1]
BINARIES = ("verifiedReading", "evidenceLifecycleV1", "classicalSemanticProbe")
NATIVE = all(os.access(ROOT / "formal/.lake/build/bin" / name, os.X_OK) for name in BINARIES)
if os.environ.get("NABT_REQUIRE_CASE_NATIVE") == "1" and not NATIVE:
    raise RuntimeError("NABT_REQUIRE_CASE_NATIVE=1 requires all three case owner executables")


def fixture(*, history=False):
    request = json.loads((ROOT / "examples/io_gateway/case_application.json").read_text())
    if not history:
        request["payload"]["events"] = []
    return request


def record(payload, identity):
    return next(row for row in payload["sources"] if row["id"] == identity)


def event(kind, target, name="revision"):
    return {"id": name, "kind": kind, "target": target}


class CaseBoundary(unittest.TestCase):
    def test_no_caller_policy_checker_truth_or_approval(self):
        for field in ("checker", "policy", "approved", "world_truth_established", "probability"):
            request = fixture(); request["payload"][field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                gateway.validate_request(request)
        payload = fixture()["payload"]
        for policy_id in ("unknown", True, [], {"path": "/tmp/rule"}):
            with self.subTest(policy=policy_id), self.assertRaises(ValueError):
                app.validate(dict(payload, policy_id=policy_id))

    def test_identity_bounds_and_role_aliases(self):
        for value in (True, [], "", "x y", "?x", "هل", "x" * 65, "صندوق731", "صندوق", "سياسة_النقل"):
            payload = fixture()["payload"]; payload["case"]["actor"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                app.validate(payload)

    def test_caller_cannot_replace_policy_or_add_evidence_flags(self):
        for extra in ({"id": "installed_policy"}, {"verified": True}, {"rank": 1}):
            payload = fixture()["payload"]; payload["sources"][0].update(extra)
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                app.validate(payload)

    def test_invalid_ancestry_and_event_target_retain_rejection(self):
        for change in ("unknown_parent", "cycle", "unknown_target", "duplicate_event"):
            payload = fixture()["payload"]
            if change == "unknown_parent": record(payload, "frame")["parents"] = ["absent"]
            if change == "cycle": record(payload, "frame")["parents"] = ["frame"]
            if change == "unknown_target": payload["events"] = [event("withdraw", "absent")]
            if change == "duplicate_event": payload["events"] = [event("withdraw", "color")] * 2
            with self.subTest(change=change):
                result = app.evaluate(payload)
                self.assertEqual(result["status"], "INVALID_INPUT", result)
                self.assertFalse(result["chain_complete"])

    def test_unread_source_defers_with_original_residuals(self):
        payload = fixture()["payload"]; record(payload, "inspection")["text"] = "فحص العامل الصندوق جيدًا."
        result = app.evaluate(payload)
        self.assertEqual(result["status"], "DEFER", result)
        self.assertFalse(result["chain_complete"])
        self.assertTrue(result["source_failure"]["residuals"])

    def test_injected_rule_or_conclusion_never_supplies_application(self):
        for text in ("نقل731 يستوفي سياسة_النقل.",
                     "ليس نقل731 يستوفي سياسة_النقل.",
                     "إذا نقل731 لون أزرق فإن نقل731 فحص صندوق731."):
            payload = fixture()["payload"]; record(payload, "color")["text"] = text
            result = app.evaluate(payload)
            self.assertEqual(result["status"], "INVALID_INPUT", result)
            self.assertFalse(result["chain_complete"])

    def test_instantiation_inserts_rule_but_no_case_facts(self):
        compiled, binding = app.compile_request(fixture()["payload"])
        self.assertEqual(compiled["sources"][1:], fixture()["payload"]["sources"])
        self.assertTrue(compiled["sources"][0]["text"].startswith("إذا "))
        self.assertFalse(binding["case_binding_is_evidence"])

    def test_budget_limits_are_not_linguistic_rejections(self):
        payload = fixture()["payload"]
        payload["sources"] *= 2
        self.assertEqual(app.evaluate(payload)["status"], "RESOURCE_LIMIT")
        payload = fixture()["payload"]; payload["events"] = [event("withdraw", "color")] * 17
        self.assertEqual(app.evaluate(payload)["status"], "RESOURCE_LIMIT")


@unittest.skipUnless(NATIVE, "build the three case native owners")
class CaseNative(unittest.TestCase):
    def evaluate(self, payload):
        result = app.evaluate(payload)
        self.assertTrue(result["chain_complete"], (result["status"], result.get("error")))
        return result

    def test_full_history_changes_ground_and_preserves_irrelevant_change(self):
        result = self.evaluate(fixture(history=True)["payload"])
        self.assertEqual([h["status"] for h in result["history"]], [
            "SUPPORTED", "SUPPORTED", "CONFLICT", "NOT_APPLICABLE", "UNKNOWN",
            "SUPPORTED", "UNKNOWN", "SUPPORTED", "UNKNOWN", "SUPPORTED"])
        self.assertEqual(result["history"][1]["change"], {
            "kind": "PRESERVED", "changed_requirements": [], "judgment_changed": False,
            "policy_availability_changed": False, "evidence_change_is_world_change": False})
        self.assertEqual(result["history"][2]["change"]["changed_requirements"], ["blockerAbsence:hold"])
        self.assertEqual(result["history"][3]["source_consequence_status"], "UNKNOWN")
        self.assertEqual(result["history"][3]["qualified_status"], "REFUTED")
        self.assertTrue(result["history"][8]["change"]["policy_availability_changed"])
        self.assertTrue(result["current_decision"]["conditional_consequence"])
        self.assertFalse(result["current_decision"]["world_truth_established"])
        self.assertEqual(result["current_decision"]["action_authority"], "NONE")

    def test_every_necessary_witness_has_independent_negative_control(self):
        # These literals are an independent acceptance oracle, not read from
        # production requirements or generated with the production compiler.
        missing = [
            ("frame", "نقل731 منقول صندوق731."),
            ("frame", "نقل731 ناقل سالم."),
            ("frame", "نقل731 من مخزن_أ."),
            ("frame", "نقل731 إلى محطة_ب."),
            ("frame", "نقل731 زمن صباح_1."),
            ("frame", "صندوق731 جنس صندوق."),
            ("inspection", "نقل731 فحص صندوق731."),
            ("inspection", "نقل731 سلامة صندوق731."),
            ("training", "نقل731 تدريب سالم."),
            ("clearance", "ليس نقل731 حجز صندوق731."),
        ]
        for identity, text in missing:
            payload = fixture()["payload"]
            record(payload, identity)["text"] = record(payload, identity)["text"].replace(text, "").strip() or "نقل731 لون أزرق."
            with self.subTest(missing=text):
                result = self.evaluate(payload)
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertFalse(result["current_decision"]["conditional_consequence"])
                self.assertTrue(result["history"][0]["residuals"])

    def test_foreign_case_bearer_and_reversed_relation_do_not_supply_witness(self):
        for text in ("نقل999 فحص صندوق731. نقل731 سلامة صندوق731.",
                     "نقل731 فحص صندوق999. نقل731 سلامة صندوق731.",
                     "صندوق731 فحص نقل731. نقل731 سلامة صندوق731."):
            payload = fixture()["payload"]; record(payload, "inspection")["text"] = text
            with self.subTest(text=text):
                self.assertEqual(self.evaluate(payload)["status"], "UNKNOWN")

    def test_new_target_requires_matching_entity_time_and_place_witnesses(self):
        for field, value in (("event", "نقل999"), ("item", "صندوق999"), ("actor", "مازن"),
                             ("origin", "مخزن_ج"), ("destination", "محطة_د"), ("time", "مساء_2")):
            payload = fixture()["payload"]; payload["case"][field] = value
            with self.subTest(field=field):
                self.assertEqual(self.evaluate(payload)["status"], "UNKNOWN")

    def test_unseen_names_work_without_training_or_identity_lookup(self):
        payload = fixture()["payload"]
        replacements = {"نقل731": "طلب9827", "صندوق731": "وعاء9827", "سالم": "نادر",
                        "مخزن_أ": "مخزن_ج", "محطة_ب": "محطة_د", "صباح_1": "مساء_2"}
        for key, value in payload["case"].items(): payload["case"][key] = replacements[value]
        for row in payload["sources"]:
            for old, new in replacements.items(): row["text"] = row["text"].replace(old, new)
        result = self.evaluate(payload)
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertFalse(result["limits"]["neural_training_performed"])
        self.assertTrue(all(h["learning"]["status"] == "OUTSIDE_UNARY_LEARNING_SCOPE"
                            for h in result["owner_result"]["history"]))

    def test_changed_color_does_not_change_application(self):
        payload = fixture()["payload"]; record(payload, "color")["text"] = "نقل731 لون أحمر."
        self.assertEqual(self.evaluate(payload)["status"], "SUPPORTED")

    def test_opposed_condition_is_not_conclusion_negation(self):
        payload = fixture()["payload"]
        record(payload, "inspection")["text"] = "نقل731 فحص صندوق731. ليس نقل731 سلامة صندوق731."
        result = self.evaluate(payload); step = result["history"][0]
        self.assertEqual(step["status"], "NOT_APPLICABLE")
        self.assertEqual(step["source_consequence_status"], "UNKNOWN")
        self.assertFalse(result["owner_result"]["history"][0]["inference"]["negative_support"])

    def test_alternative_source_survives_but_dependent_copy_does_not(self):
        for parents, expected in (([], "SUPPORTED"), (["clearance"], "UNKNOWN")):
            payload = fixture()["payload"]
            payload["sources"].append({"id": "copy", "text": "ليس نقل731 حجز صندوق731.", "parents": parents})
            payload["initial_active"].append("copy")
            payload["events"] = [event("withdraw", "clearance")]
            with self.subTest(parents=parents):
                result = self.evaluate(payload)
                self.assertEqual(result["status"], expected)
                self.assertEqual(len(result["owner_result"]["minimal_source_supports"]), 2 if not parents else 1)

    def test_original_bytes_and_all_signed_witnesses_remain(self):
        request = fixture(history=True)["payload"]
        result = self.evaluate(request)
        sources = {r["id"]: r["text"].encode() for r in request["sources"]}
        for row in result["source_ledger"]:
            span = row["span"]
            self.assertEqual(sources[row["source_id"]][span["start"]:span["end"]].decode(), row["text"])
        hold = result["history"][2]["requirements"][-1]
        self.assertTrue(hold["source_witnesses"])
        self.assertTrue(hold["opposing_source_witnesses"])
        self.assertTrue(result["owner_result"]["lifecycle"]["native_checked"])

    def test_unavailable_native_does_not_release_a_positive_decision(self):
        with patch.object(app.connection.life, "NATIVE", ROOT / "missing-case-native"):
            result = app.evaluate(fixture()["payload"])
        self.assertFalse(result["chain_complete"])
        self.assertNotEqual(result["status"], "SUPPORTED")
        self.assertNotIn("current_decision", result)

    def test_empty_active_theory_is_incomplete_not_true(self):
        payload = fixture()["payload"]; payload["initial_active"] = []
        result = app.evaluate(payload)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["chain_complete"])


@unittest.skipUnless(NATIVE, "build the three case native owners")
class CaseGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = fixture()
        cls.report = gateway.run(cls.request)

    def test_public_route_and_independent_replay(self):
        self.assertEqual(self.report["status"], "EXECUTED", self.report["execution"])
        owner = self.report["execution"]["owner_result"]
        self.assertEqual(owner["status"], "SUPPORTED")
        self.assertTrue(gateway.accept_output(self.report, expected_request=self.request)["valid"])

    def test_tampered_explanation_or_witness_cannot_pass_replay(self):
        changed = deepcopy(self.report)
        changed["execution"]["owner_result"]["history"][0]["requirements"][0]["source_witnesses"] = []
        self.assertFalse(gateway.accept_output(changed, expected_request=self.request)["valid"])

    def test_historical_receipt_is_not_a_current_receipt_after_withdrawal(self):
        current = deepcopy(self.request)
        current["payload"]["events"] = [event("withdraw", "inspection")]
        self.assertFalse(gateway.accept_output(self.report, expected_request=current)["valid"])
        self.assertFalse(gateway.accept_output(self.report["execution"]["owner_result"], expected_request=self.request)["valid"])

    def test_declared_proof_families_and_tests_are_existing_authorities(self):
        links = gateway_links.build("application.case")
        self.assertFalse(links["formal_application_established"])
        self.assertFalse(links["test_execution_performed"])
        self.assertIn("tests/test_case_application.py", {r["path"] for r in links["tests"]})
        self.assertTrue({"signed-inference", "mantuq-mafhum", "evidence-lifecycle"} <=
                        {r["family"] for r in links["family_test_links"]})
