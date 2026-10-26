"""Foundation freeze migration preserves historical bytes and gate obligations."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from tools import arabic_completion_v6_gate as historical_gate
from tools import framework_foundation_gate as current_gate
from tools.text_evaluation.integrity import verify_code_freeze


ROOT = Path(__file__).resolve().parents[1]
FIRST_FOUNDATION = ROOT / "evidence/framework_foundation_v1/code_freeze_v1.json"
PREVIOUS = ROOT / "evidence/progressive_rule_audit_v1/code_freeze_v1.json"
CURRENT = ROOT / "evidence/source_acquisition_v1/code_freeze_v1.json"
HISTORICAL = ROOT / "evidence/arabic_completion_v6/code_freeze_v1.json"
HISTORICAL_MANIFEST_SHA = "31bd37d919364742033a08ab4cb557e93b92280539dd7a55364763cae236dfec"
HISTORICAL_POLICY_SHA = "5e73cfdae07cdb60a2f93c8cc9961a9ee283d85471f24b5b61eabcb3c3647657"


class FoundationFreezeTests(unittest.TestCase):
    def test_historical_manifest_and_policy_are_unchanged(self):
        self.assertEqual(sha256(HISTORICAL.read_bytes()).hexdigest(), HISTORICAL_MANIFEST_SHA)
        self.assertEqual(sha256(historical_gate.POLICY_PATH.read_bytes()).hexdigest(), HISTORICAL_POLICY_SHA)
        old = json.loads(HISTORICAL.read_text())
        self.assertEqual(sha256(HISTORICAL.with_name(old["archive_filename"]).read_bytes()).hexdigest(),
                         "15bfc5ffdd08667cb79bf530d3b5baecd49f1c0493b8bf252f934b5fea55a922")

    def test_current_inventory_is_exact_and_old_freeze_cannot_authorize_it(self):
        current = verify_code_freeze(CURRENT, ROOT)
        old = json.loads(HISTORICAL.read_text())
        self.assertEqual(current["previous_runtime_manifest_sha256"], sha256(PREVIOUS.read_bytes()).hexdigest())
        self.assertEqual(current["historical_v6_manifest_sha256"], HISTORICAL_MANIFEST_SHA)
        previous = json.loads(PREVIOUS.read_bytes())
        self.assertEqual(sha256(PREVIOUS.read_bytes()).hexdigest(), "b184a00c3c19b3204b889f14567b042c987046e7698f657bf9586ff307f01cf5")
        self.assertEqual(current["changed_runtime_paths"], ["src/nabt/data/framework_foundation.json"])
        previous_rows = {row["path"]: row for row in previous["files"]}
        self.assertEqual([row["path"] for row in current["files"]
                          if row["path"] in previous_rows and row != previous_rows[row["path"]]],
                         ["src/nabt/data/framework_foundation.json"])
        self.assertEqual(current["added_runtime_paths"], [])
        with self.assertRaises(ValueError):
            verify_code_freeze(PREVIOUS, ROOT)
        current_paths = {row["path"] for row in current["files"]}
        old_paths = {row["path"] for row in old["files"]}
        self.assertEqual(current_paths - old_paths,
                         {"src/nabt/foundation.py", "src/nabt/data/framework_foundation.json",
                          "src/nabt/classical_certified.py"})
        self.assertFalse(old_paths - current_paths)
        self.assertEqual(len(current_paths), 102)
        with self.assertRaises(ValueError):
            verify_code_freeze(HISTORICAL, ROOT)

    def test_policy_keeps_all_material_denominators_and_failure_signatures(self):
        old, current = historical_gate.load_policy(), current_gate.load_policy()
        self.assertEqual(old["suites"], current["suites"])
        self.assertEqual(current["previous_policy_sha256"], '4f1660cbba2b513f134f0677e5b48a04d57139b32b9a475b280bd4417a35664f')
        self.assertEqual(current["historical_v6_policy_sha256"], HISTORICAL_POLICY_SHA)
        self.assertEqual(current["runtime_file_count"], 102)
        self.assertEqual(current["runtime_freeze_sha256"], sha256(CURRENT.read_bytes()).hexdigest())
        self.assertNotEqual(current["runtime_freeze_sha256"], old["runtime_freeze_sha256"])

    def test_new_registration_cannot_waive_false_acceptance_or_missing_material(self):
        policy = current_gate.load_policy()
        for suite in ("construction", "discourse"):
            fixture_path = ROOT / historical_gate.load_policy()["suites"][suite]["strict_measurement"]
            historical = json.loads(fixture_path.read_bytes())
            self.assertFalse(current_gate.gate_decision(suite, historical, True)["gate_pass"])
            # A synthetic gate-only fixture. Production callers must separately
            # verify actual current bytes, archive and raw measurement receipts.
            synthetic = deepcopy(historical)
            synthetic["snapshot"].update({key: policy[key] for key in (
                "runtime_freeze_sha256", "runtime_snapshot_sha256", "runtime_file_count")})
            self.assertTrue(current_gate.gate_decision(suite, synthetic, True)["gate_pass"])
            for corruption in ("false_accept", "missing_case", "wrong_total", "wrong_runtime"):
                changed = deepcopy(synthetic)
                if corruption == "false_accept":
                    changed["cases"][0]["false_accepts"] = ["invented authority"]
                elif corruption == "missing_case":
                    changed["cases"].pop()
                elif corruption == "wrong_total":
                    changed["total"] -= 1
                else:
                    changed["snapshot"]["runtime_file_count"] = 99
                with self.subTest(suite=suite, corruption=corruption):
                    self.assertFalse(current_gate.gate_decision(suite, changed, True)["gate_pass"])


if __name__ == "__main__":
    unittest.main()
