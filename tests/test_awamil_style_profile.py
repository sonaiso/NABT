from itertools import product
import unittest
from unittest.mock import patch

from nabt.governors import check_assignment, installed_table
from tools.grammar_catalog import awamil_cli
from tools.grammar_catalog.awamil_profile import describe, profiles


class TestGovernorStyleProfile(unittest.TestCase):
    def test_fibers_and_member_recovery(self):
        rows, members = profiles()
        self.assertEqual(len(members), 17)
        self.assertEqual(sorted(x for ids in members.values() for x in ids), list(range(1, 101)))
        for row, key in rows.items():
            self.assertIn(row, members[key])
        tags = [key[2] for key in rows.values()]
        styles = ["الخبر", "الطلب", "التمني", "الترجي", "الاستفهام", "النداء"]
        self.assertEqual([tags.count(tag) for tag in styles], [82, 2, 1, 1, 10, 4])

    def test_ambiguity_ellipsis_and_work(self):
        entries = installed_table().entries
        for left, right in [(72, 87), (73, 88), (75, 94), (76, 93)]:
            first = describe(entries[left - 1])
            second = describe(entries[right - 1])
            self.assertEqual(first["same_label_rows"], [left, right])
            self.assertNotEqual(first["table_style"], second["table_style"])
        self.assertEqual(describe(entries[68])["member_rows"], [69, 70])
        self.assertEqual(len(describe(entries[66])["alternatives"]), 2)
        self.assertEqual(describe(entries[50])["equality_links"], [[9, 10]])

    def test_all_projected_work_observations(self):
        rows, members = profiles()
        table = installed_table()
        for entry in table.entries:
            key = rows[entry.row_id]
            equations, links, _, _ = key
            roles = {role for alt in equations for role, _ in alt}
            roles.update(role for link in links for role in link)
            roles = sorted(roles)
            representative = table.entries[members[key][0] - 1]
            for values in product((None, 0, 1, 2, 3), repeat=len(roles)):
                assignment = dict(zip(roles, values, strict=True))
                result = check_assignment(entry.class_code, assignment)
                recovered = check_assignment(representative.class_code, assignment)
                for field in ("complete", "viable", "deficits"):
                    self.assertEqual(result[field], recovered[field], (entry, assignment))
                exact = [
                    [list(pair) for pair in alt] for alt in equations
                    if all(assignment[r] == mark for r, mark in alt)
                    and all(assignment[r] is not None and assignment[r] == assignment[s] for r, s in links)
                ]
                self.assertEqual(result["complete"], exact, (entry, assignment))

    def test_check_compatibility_and_evidence_withdrawal(self):
        request = {"factor_id": "nabt:061", "assignments": {"2": 3}}
        original = awamil_cli.check(request)
        self.assertNotIn("profile", original)
        enriched = awamil_cli.check({**request, "include_profile": True})
        self.assertEqual(original["result"], enriched["result"])
        self.assertEqual(enriched["profile"]["table_style"], "الطلب")
        missing = awamil_cli.check({**request, "assignments": {}, "include_profile": True})
        self.assertEqual(missing["result"]["complete"], [])
        self.assertEqual(missing["profile"], enriched["profile"])
        with self.assertRaises(ValueError):
            awamil_cli.check({**request, "include_profile": 1})

    def test_changed_style_source_cannot_grant_a_profile(self):
        with patch("tools.grammar_catalog.awamil_profile.STYLE_SHA256", "0" * 64):
            with self.assertRaises(ValueError):
                profiles()
