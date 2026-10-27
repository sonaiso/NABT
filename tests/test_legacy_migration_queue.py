"""The backlog is exhaustive about interfaces and inert about proof authority."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evidence.legacy_migration_v2 import build_queue as queue


class MigrationQueueTests(unittest.TestCase):
    def test_exact_historical_denominator_and_each_surface_once(self):
        result = queue.build()
        baseline = json.loads((queue.ROOT / queue.BASE_INVENTORY).read_bytes())
        expected = {row["surface_id"] for row in baseline["surfaces"]
                    if row["migration_state"] == queue.ACQUISITION}
        actual = [row["surface_id"] for row in result["acquisition_queue"]]
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(len(actual), 104)
        self.assertEqual(sum(f["baseline_surface_count"] for f in result["families"]), 104)

    def test_transport_is_seven_surfaces_not_seven_completed_commands(self):
        result = queue.build()
        self.assertEqual(len(result["transport_queue"]), 7)
        self.assertIsNone(result["denominators"]["migrated_command_count"])
        self.assertTrue(all(row["required_unit"] == "COMMAND_OR_OPERATION_NOT_WHOLE_SURFACE"
                            for row in result["transport_queue"]))

    def test_plan_never_issues_a_claim_or_completed_acquisition_count(self):
        result = queue.build()
        self.assertFalse(result["source_acquisition_proved_by_this_plan"])
        self.assertIsNone(result["denominators"]["proved_acquisition_count"])
        for row in result["acquisition_queue"]:
            self.assertEqual(row["accepted_claims"], [])
            self.assertEqual(row["lifecycle"]["native_law"], "NOT_ASSESSED_BY_QUEUE")
            self.assertEqual(row["lifecycle"]["implementation_refinement"], "NOT_ASSESSED_BY_QUEUE")

    def test_missing_family_cannot_silently_drop_a_denominator(self):
        with patch.object(queue, "FAMILIES", queue.FAMILIES[1:]):
            with self.assertRaisesRegex(ValueError, "UNASSIGNED_BASELINE_SURFACE"):
                queue.build()

    def test_duplicate_family_cannot_count_surfaces_twice(self):
        with patch.object(queue, "FAMILIES", queue.FAMILIES + [queue.FAMILIES[0]]):
            with self.assertRaisesRegex(ValueError, "OVERLAPPING_FAMILY"):
                queue.build()

    def test_dependency_cycle_and_missing_predecessor_are_rejected(self):
        for families in ([{"id": "a", "depends_on": ["b"]}],
                         [{"id": "a", "depends_on": ["b"]},
                          {"id": "b", "depends_on": ["a"]}]):
            with self.subTest(families=families):
                with self.assertRaisesRegex(ValueError, "UNKNOWN_OR_CYCLIC"):
                    queue._topological(families)

    def test_changed_historical_inventory_is_not_resealed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / queue.BASE_INVENTORY
            target.parent.mkdir(parents=True)
            target.write_bytes((queue.ROOT / queue.BASE_INVENTORY).read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "HISTORICAL_INVENTORY_CHANGED"):
                queue.build(root)

    def test_saved_queue_reproduces_exactly(self):
        self.assertEqual((queue.ROOT / queue.FOLDER / "migration_queue.json").read_bytes(),
                         queue._wire(queue.build()))


if __name__ == "__main__":
    unittest.main()
