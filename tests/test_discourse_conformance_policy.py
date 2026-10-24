"""The source-policy migration cannot weaken the independent finite checker."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt import discourse_laws


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "discourse_conformance_policy_test", ROOT / "tools/check_discourse_conformance.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class DiscourseConformancePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = CHECKER.parse(CHECKER.TABLE.read_bytes())
        cls.policy = discourse_laws.replay_discourse_policy()

    def test_current_policy_replays_both_bounded_temporal_additions(self):
        report = CHECKER.check_table(self.table)
        self.assertEqual(report["source_policy_id"], "nabt.discourse-grammar-sources.v2")
        self.assertEqual(report["source_passages_replayed"], 24)
        self.assertIn("temporal_noun_examples", report["source_rule_ids"])
        self.assertIn("temporal_ams_built", report["source_rule_ids"])
        self.assertTrue(report["source_policy_inventory_exact"])
        self.assertFalse(report["runtime_reader_checked"])

    def test_missing_rules_and_same_count_replacement_are_rejected(self):
        old_inventory = deepcopy(self.policy)
        old_inventory["rules"].pop("temporal_noun_examples")
        old_inventory["rules"].pop("temporal_ams_built")
        replacement = deepcopy(self.policy)
        replacement["rules"]["unreviewed_temporal_rule"] = replacement["rules"].pop("temporal_ams_built")
        self.assertEqual(len(replacement["rules"]), 24)
        for changed in (old_inventory, replacement):
            with self.subTest(rule_count=len(changed["rules"])):
                with patch.object(discourse_laws, "replay_discourse_policy", return_value=changed):
                    with self.assertRaisesRegex(ValueError, "Source policy inventory differs"):
                        CHECKER.check_table(self.table)

    def test_old_identity_or_unpinned_digest_cannot_inherit_current_inventory(self):
        for field, value, reason in (
                ("policy_id", "nabt.discourse-grammar-sources.v1", "identity"),
                ("policy_sha256", "0" * 64, "pin")):
            changed = deepcopy(self.policy)
            changed[field] = value
            with self.subTest(field=field):
                with patch.object(discourse_laws, "replay_discourse_policy", return_value=changed):
                    with self.assertRaisesRegex(ValueError, "Source policy " + reason + " differs"):
                        CHECKER.check_table(self.table)

    def test_current_source_policy_does_not_waive_finite_law_mismatch(self):
        changed = deepcopy(self.table)
        changed["assertion_rows"][0]["allowed"] = not changed["assertion_rows"][0]["allowed"]
        with self.assertRaisesRegex(ValueError, "Complete fresh Lean export differs"):
            CHECKER.check_table(changed)


if __name__ == "__main__":
    unittest.main()
