"""Exact metadata replay is a separate obligation from semantic licensing."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import meaning_preservation_inventory as inventory


class MeaningResearchInventoryTests(unittest.TestCase):
    def test_four_independent_denominators_and_unclaimed_authorities(self):
        result = inventory.research_inventory()
        self.assertTrue(result["metadata_verified"])
        self.assertEqual(result["denominators"], {
            "morphology_families": 51, "composition_groups": 34,
            "interpretation_contracts": 15, "nominal_templates": 20})
        self.assertEqual(result["related_source_anchors"], 55)
        self.assertEqual(len(result["records_without_exact_related_anchor"]), 22)
        self.assertTrue(all(value is False for value in result["claims"].values()))
        self.assertIn("NOT_RUNTIME_LICENSING_AUTHORITY", result["authority"])

    def test_template_review_does_not_certify_display_examples(self):
        result = inventory.research_inventory()
        templates = [row for row in result["records"] if row["kind"] == "nominal_template"]
        self.assertEqual([row["local_id"] for row in templates],
                         [prefix + str(index).zfill(2)
                          for prefix, count in (("T", 10), ("Q", 6), ("P", 4))
                          for index in range(1, count + 1)])
        self.assertEqual(templates[0]["label_ar"], "فَعْل")
        self.assertTrue(all(row["display_example_newly_verified"] is False for row in templates))
        self.assertTrue(all(row["formal_status"] == "NO_PER_ROW_THEOREM_OR_FIDELITY_CERTIFICATE"
                            for row in templates))

    def test_changed_pinned_file_does_not_become_authoritative_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / inventory.SCOPE_PATH
            target.parent.mkdir(parents=True)
            target.write_text('{"world_truth_established":true}')
            with patch.object(inventory, "ROOT", root), self.assertRaises(ValueError):
                inventory.research_inventory()

    def test_same_metadata_numbers_preserve_json_scalar_types(self):
        self.assertFalse(inventory._same({"n": True}, {"n": 1}))
        self.assertFalse(inventory._same({"n": 1.0}, {"n": 1}))

    def test_source_pointer_preserves_escaped_keys_and_canonical_index(self):
        value = {"a/b": {"~": ["retained", "other"]}}
        self.assertEqual(inventory._pointer(value, "/a~1b/~0/0"), "retained")
        for bad in ("/a~1b/~0/00", "/a~1b/~0/-1", "/a~1b/~0/2", "/a~2b"):
            with self.subTest(pointer=bad), self.assertRaises(ValueError):
                inventory._pointer(value, bad)

    def test_paths_cannot_escape_or_silently_follow_a_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real.json").write_text("{}")
            (root / "linked.json").symlink_to(root / "real.json")
            with patch.object(inventory, "ROOT", root):
                for name in ("../real.json", "linked.json", "./real.json", "/tmp/real.json"):
                    with self.subTest(path=name), self.assertRaises(ValueError):
                        inventory._path(name)

    def test_mixed_fingerprint_cannot_rebind_an_existing_anchor(self):
        scope = inventory._read(inventory.SCOPE_PATH, inventory.SCOPE_SHA256)
        original = inventory._read(inventory.INVENTORY_PATH, inventory.INVENTORY_SHA256)
        changed = deepcopy(original)
        changed["existing_record_anchors"][0]["record_sha256"] = "0" * 64
        real_read = inventory._read
        def controlled(name, fingerprint, expected_bytes=None):
            if name == inventory.SCOPE_PATH:
                return scope
            if name == inventory.INVENTORY_PATH:
                return changed
            return real_read(name, fingerprint, expected_bytes)
        with patch.object(inventory, "_read", side_effect=controlled), self.assertRaises(ValueError):
            inventory.research_inventory()


if __name__ == "__main__":
    unittest.main()
