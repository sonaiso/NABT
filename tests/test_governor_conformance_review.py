"""Regressions for independently observed conformance-boundary defects.

The probe fixture is built by enumerating total models and their partial
extensions, without calling the runtime assignment checker. These tests
check the comparison boundary, not Lean/Python refinement. The separate
fresh-Lean conformance command remains the mathematical export check.
"""

from copy import deepcopy
import importlib.util
from itertools import product
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt import governors


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "nabt_governor_conformance_review", ROOT / "tools/check_governor_conformance.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def model_export():
    """Small independent finite-model oracle for the declared case algebra."""
    data = json.loads((ROOT / "src/nabt/data/governors.json").read_text(encoding="utf-8"))
    del data["source"]
    probes = []
    for cls in data["classes"]:
        roles = sorted({r for alt in cls["alternatives"] for r, _ in alt}
                       | {r for link in cls["links"] for r in link})
        models = [dict(zip(roles, marks)) for marks in product(range(4), repeat=len(roles))]
        alternatives = []
        for alt in cls["alternatives"]:
            needed = {r for r, _ in alt} | {r for link in cls["links"] for r in link}
            satisfying = [m for m in models
                          if all(m[r] == mark for r, mark in alt)
                          and all(m[left] == m[right] for left, right in cls["links"])]
            alternatives.append((alt, needed, satisfying))
        for values in product((None, 0, 1, 2, 3), repeat=len(roles)):
            partial = dict(zip(roles, values))
            known = {r: v for r, v in partial.items() if v is not None}
            complete, viable = [], []
            for alt, needed, satisfying in alternatives:
                extensions = [m for m in satisfying if known.items() <= m.items()]
                if extensions:
                    viable.append(alt)
                    if needed <= known.keys():
                        complete.append(alt)
            probes.append({"class_code": cls["code"],
                           "assignments": [{"role": r, "mark": v} for r, v in partial.items()],
                           "complete": complete, "viable": viable})
    data["assignment_probes"] = probes
    return data


class GovernorConformanceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.export = model_export()
        # Every mutation starts from a valid full export, not an unrelated
        # malformed input that would fail without the reviewed correction.
        report = CHECKER.check_table(cls.export)
        if report["exhaustive_relevant_role_probes"] != 197:
            raise AssertionError("Independent fixture does not cover the declared finite contract")

    def test_runtime_law_id_must_match_formal_export(self):
        with patch.object(governors, "LAW_ID", "nabt.governors.unrelated"):
            with self.assertRaisesRegex(ValueError, "Runtime law or numeric domain"):
                CHECKER.check_table(self.export)

    def test_runtime_number_domain_must_match_formal_export(self):
        with patch.object(governors, "ROLE_MARK_DOMAIN", "nabt.role-mark.unrelated"):
            with self.assertRaisesRegex(ValueError, "Runtime law or numeric domain"):
                CHECKER.check_table(self.export)

    def test_reordered_duplicate_cannot_replace_a_missing_assignment(self):
        changed = deepcopy(self.export)
        duplicate = deepcopy(next(p for p in changed["assignment_probes"]
                                  if len(p["assignments"]) == 2))
        duplicate["assignments"].reverse()
        changed["assignment_probes"][-1] = duplicate
        self.assertEqual(len(changed["assignment_probes"]), 197)
        with self.assertRaisesRegex(ValueError, "Repeated assignment probe"):
            CHECKER.check_table(changed)

    def test_irrelevant_role_cannot_substitute_for_expected_coverage(self):
        changed = deepcopy(self.export)
        # Class 1 uses roles 0 and 1. Adding unknown role 2 changes neither
        # result, but this is not the exact required relevant-role assignment.
        changed["assignment_probes"][0]["assignments"].append({"role": 2, "mark": None})
        with self.assertRaisesRegex(ValueError, "Probe inventory does not exhaust"):
            CHECKER.check_table(changed)

    def test_reordering_each_assignment_without_duplication_preserves_conformance(self):
        changed = deepcopy(self.export)
        for probe in changed["assignment_probes"]:
            probe["assignments"].reverse()
        self.assertTrue(CHECKER.check_table(changed)["ok"])


if __name__ == "__main__":
    unittest.main()
