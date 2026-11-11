"""Independent examples of finite partitions and scoped opening clauses."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from tools.grammar_catalog import gateway, genus_chains as chains

REQUEST = json.loads((Path(__file__).resolve().parents[1] / "examples/relations/genus_opening.json").read_text())
BASE = REQUEST["payload"]["genus_chains"]
RIVAL = "غطاء نوع مصنوع.\nغطاء لازم منفصل.\n"


def run(ledger=None, text="الباب مفتوح.", **changes):
    request = {**BASE, **changes}
    if ledger is not None:
        request["ledger"] = ledger
    return chains.analyze(text, "lesson", request)


class GenusAndProperty(unittest.TestCase):
    def test_rival_reopens_partition_and_exclusion_needs_a_witness(self):
        a = run()
        self.assertEqual(a["partition"]["selected"], "باب_مفصلي")
        self.assertEqual(a["partition"]["candidates"][0]["membership"], "UNKNOWN")
        source = BASE["ledger"] + RIVAL
        self.assertEqual(run(source)["partition"]["decision"], "DEFER")
        self.assertEqual(run(source + "الباب خاصية منفصل.\n")["partition"]["decision"], "DEFER")
        self.assertEqual(run(source + "ليس الباب خاصية منفصل.\n")["partition"]["selected"], "باب_مفصلي")
        self.assertIsNone(run(BASE["ledger"].replace("الباب عضوية مصنوع.\n", ""))["partition"]["selected"])

    def test_disjoint_counterexample_is_local_and_traces_to_original_utf8(self):
        scope = BASE["ledger"] + RIVAL + "باب_مفصلي يباين غطاء.\nالعينة عضوية باب_مفصلي.\n"
        report = run(scope + "العينة عضوية غطاء.\n")
        self.assertEqual(report["partition"]["decision"], "CONFLICT")
        conflict, = report["disjoint_conflicts"]
        self.assertEqual(conflict["common_individual"], "العينة")
        restored = []
        for i in conflict["witness_indices"]:
            row = report["witnesses"][i]
            start, end = row["byte_span"]
            restored.append((scope + "العينة عضوية غطاء.\n").encode()[start:end].decode())
        self.assertEqual({s.rstrip(".") for s in restored}, {"باب_مفصلي يباين غطاء", "العينة عضوية باب_مفصلي", "العينة عضوية غطاء"})
        self.assertEqual(run(scope)["disjoint_conflicts"], [])
        self.assertEqual(report["capability"]["status"], "SUPPORTED")

    def test_inherited_membership_and_property_chain(self):
        extra = "باب_مفصلي_خشبي نوع باب_مفصلي.\nالباب عضوية باب_مفصلي_خشبي.\n"
        source = BASE["ledger"].replace("الباب خاصية ذو_مفصل.\n", "") + extra
        r = run(source)
        self.assertEqual(r["capability"]["status"], "SUPPORTED")
        self.assertEqual(r["partition"]["candidates"][0]["membership"], "SUPPORTED")
        self.assertEqual(r["hierarchies"]["genus_ancestors"]["باب_مفصلي_خشبي"], sorted(["باب_مفصلي", "مصنوع", "شيء"]))
        self.assertEqual(r["hierarchies"]["property_ancestors"]["ذو_مفصل"], ["ذو_وصلة"])
        inherited = r["entity_properties"]["ذو_وصلة"]
        self.assertEqual(inherited["status"], "SUPPORTED")
        self.assertTrue(inherited["positive_witness_indices"])
        without = run(source.replace("باب_مفصلي لازم ذو_مفصل.\n", ""))
        self.assertEqual(without["capability"]["status"], "UNKNOWN")
        self.assertEqual(without["partition"]["candidates"][0]["membership"], "SUPPORTED")

    def test_withdrawal_alternate_support_and_unrelated_judgments(self):
        extra = "الباب خاصية ذو_وصلة.\n"
        original = BASE["ledger"]
        cut = original.replace("الباب خاصية ذو_مفصل.\n", "")
        self.assertEqual(run(cut)["capability"]["status"], "UNKNOWN")
        self.assertEqual(run(cut + extra)["capability"]["status"], "SUPPORTED")
        self.assertEqual(run(original)["attribute_bridge"]["text_relation"], run(cut)["attribute_bridge"]["text_relation"])
        opposite = run(original + "ليس الباب خاصية ذو_مفصل.\n")
        self.assertEqual(opposite["partition"]["decision"], "CONFLICT")
        self.assertEqual(opposite["capability"]["status"], "DEFER")
        self.assertEqual(run(original + extra + "ليس الباب خاصية ذو_مفصل.\n")["capability"]["status"], "SUPPORTED")

    def test_conditional_capability_blocker_and_its_absence(self):
        s = BASE["ledger"].replace("ليس الباب مانع فتح.\n", "")
        self.assertEqual(run(s)["capability"]["status"], "UNKNOWN")
        self.assertEqual(run(s + "الباب مانع فتح.\n")["capability"]["status"], "REFUTED")
        self.assertEqual(run(BASE["ledger"] + "الباب مانع فتح.\n")["capability"]["status"], "CONFLICT")
        self.assertEqual(run(BASE["ledger"].replace("الباب شرط فتح.\n", ""))["capability"]["status"], "UNKNOWN")

    def test_unbound_and_outside_profile_preserve_readings_without_join(self):
        for t in ("قابل للفتح", "مفتوح", "فُتح", "لم يُفتح", "لكي يُفتح"):
            bridge = run(text=t)["attribute_bridge"]
            self.assertNotEqual(bridge["text_relation"], "DEFER")
            self.assertIsNone(bridge["bearer"])
            self.assertEqual(bridge["independent_capability"], "UNBOUND")
        for t in ("فتح الباب.", "قال إن الباب مفتوح.", "«الباب مفتوح»", "الباب مفتوح؟", "البابُ مفتوحٌ ثم أُغلق.", "فُتِحَ البابَ."):
            self.assertEqual(run(text=t)["reading"]["kind"], "DEFER")
        self.assertEqual(run(text="لم يُفتح الباب.")["reading"]["voice"], "UNRESOLVED")

    def test_five_unseen_clauses_keep_source_truth_and_subject_apart(self):
        rows = [("الصندوقُ قابلٌ للفتح.", "DISPOSITION", "NOT_ASSERTED"),
                ("الصندوق مفتوحٌ.", "STATE", "NOT_ASSERTED"), ("فُتِحَ الصندوقُ.", "ASSERTED_PASSIVE", "ASSERTED"),
                ("لم يُفْتَحْ الصندوقُ.", "NEGATED_EVENT", "DENIED"), ("لكي يُفْتَحَ الصندوقُ.", "PURPOSE", "INTENDED")]
        for text, kind, event_scope in rows:
            r = run(BASE["ledger"].replace("الباب", "الصندوق"), text, entity="الصندوق")
            b = r["attribute_bridge"]
            self.assertEqual((b["text_relation"], b["event_in_text"], b["bearer"]), (kind, event_scope, "الصندوق"))
            self.assertEqual(b["external_occurrence"], "UNKNOWN")
            self.assertFalse(r["world_truth_established"])

    def test_no_ledger_keeps_text_intelligible_and_world_unknown(self):
        r = run("", "الباب مفتوح.")
        self.assertEqual(r["reading"]["kind"], "STATE")
        self.assertEqual(r["partition"]["decision"], "DEFER")
        self.assertEqual(r["capability"]["status"], "UNKNOWN")
        self.assertFalse(r["world_truth_established"])

    def test_bad_taxonomy_and_forged_inputs(self):
        for bad in ("باب_مفصلي نوع يتيم.", "مصنوع نوع باب_مفصلي.", "ذو_وصلة أخص ذو_مفصل.", "مزيف يصدق فتح.", "الباب قابلية فتح.",
                    "إذا الباب خاصية ذو_مفصل فإن الباب عضوية باب_مفصلي."):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                run(BASE["ledger"] + bad)
        with self.assertRaises(ValueError):
            run(approved=True)

    def test_budget_never_returns_partial_classification(self):
        source = BASE["ledger"] + "".join(f"باب_مفصلي{i} نوع مصنوع.\n" for i in range(20)) + "".join(
            f"شخص{i} عضوية مصنوع.\n" for i in range(20))
        r = run(source)
        self.assertEqual(r["status"], "RESOURCE_LIMIT")
        self.assertNotIn("partition", r)

    def test_gateway_replay_and_native_status(self):
        receipt = gateway.run(REQUEST)
        self.assertEqual(receipt["status"], "EXECUTED", receipt["execution"])
        owner = receipt["execution"]["owner_result"]
        self.assertFalse(owner["world_truth_established"])
        r = owner["genus_chains"]
        check = r["checker"]["status"]
        if os.environ.get("NABT_REQUIRE_RELATIONAL_NATIVE") or check != "CHECKER_UNAVAILABLE":
            self.assertEqual(check, "VERIFIED_GROUND_PROJECTION")
            self.assertTrue(r["checker"]["receipt"]["verified"])
        else:
            self.assertEqual(r["status"], "PROPOSAL_ONLY")
        self.assertTrue(gateway.accept_output(receipt, expected_request=REQUEST)["valid"])
        wrong = deepcopy(receipt)
        wrong["execution"]["owner_result"]["genus_chains"]["partition"]["selected"] = "آخر"
        self.assertFalse(gateway.accept_output(wrong, expected_request=REQUEST)["valid"])


if __name__ == "__main__":
    unittest.main()
