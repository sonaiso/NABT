"""Checks on lesson construction; semantic results require a verified NTP replay."""
from fractions import Fraction
import json
import unittest

from examples.cognitive_teaching import arabic_science as pilot
from tools.lexical_training import opencyc_inquiry


class TwoSubjectLessons(unittest.TestCase):
    def test_held_out_labels_are_absent_even_after_observations(self):
        for domain in ("arabic", "physics"):
            other = "physics" if domain == "arabic" else "arabic"
            for target in (None, other):
                original = pilot.request(domain, 0, target)["payload"]["input"]["lesson"]
                events = []
                for stage in range(len(pilot.EVENTS) + 1):
                    request = pilot.request(domain, stage, target)
                    self.assertEqual(request["route"], "ntp")
                    lesson = opencyc_inquiry.validate(request["payload"]["input"]["lesson"])
                    self.assertEqual(lesson["slice"], original["slice"])
                    facts = [json.loads(line) for line in lesson["slice"]["ledger"].splitlines()]
                    labelled = {r["id"] for r in facts if lesson["target_class"] in r["formula"]}
                    self.assertEqual(labelled, {"A-label", "B-label", "C-label"})
                    self.assertEqual(len(lesson["events"]), stage)
                    if stage:
                        self.assertEqual(lesson["events"][:-1], events)
                    events = lesson["events"]

    def test_same_written_ending_is_ambiguous_without_governor(self):
        first, _, rows = pilot.domain_rows("arabic")
        self.assertEqual(first[0], "#$Lan")
        self.assertEqual(rows[3][0].split()[1], rows[6][0].split()[1])
        self.assertEqual(rows[3][1], (True, True))
        self.assertEqual(rows[6][1], (False, True))

    def test_force_decrease_can_have_a_different_explanation(self):
        old_dp, old_dt, new_dp, new_dt = pilot.PHYSICS[-1]
        self.assertLess(Fraction(new_dp, new_dt), Fraction(old_dp, old_dt))
        self.assertNotEqual(old_dp, new_dp)
        self.assertFalse(pilot.HELD_OUT["G"])
