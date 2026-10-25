"""Cross-reference tampering cannot supply compiled theorem or source authority."""
from copy import deepcopy
import unittest

from tools.licensed_inference.links import REUSED, compose


def fixtures():
    names = ["Nabt.LicensedInference.example", *REUSED]
    rows = [{"name": name, "module": name.rsplit(".", 1)[0],
             "canonical_name": name, "statement_sha256": str(index),
             "source_path": "formal/" + str(index) + ".lean", "source_sha256": "abc",
             "proof_dependencies": [], "axioms": []} for index, name in enumerate(names)]
    compiled = {"theorems": rows, "inputs": {r["source_path"]: "abc" for r in rows}}
    inventory = {"review_sha256": "def", "passages": [{"passage_id": "p"}],
                 "relations": [{"relation_id": "r", "passage_ids": ["p"]}],
                 "source_replay": {"originals_rechecked": False}}
    return inventory, compiled


class LicensedLinks(unittest.TestCase):
    def test_references_do_not_raise_translation_or_world_authority(self):
        inventory, compiled = fixtures()
        result = compose(inventory, compiled)
        self.assertEqual(result["counts"]["new_module_declarations"], 1)
        self.assertFalse(result["source_translation_fidelity_proved"])
        self.assertFalse(result["world_truth_established"])

    def test_missing_or_duplicate_compiled_node_fails(self):
        inventory, compiled = fixtures()
        for rows in (compiled["theorems"][1:], compiled["theorems"][:-1],
                     compiled["theorems"] + [compiled["theorems"][0]]):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                compose(inventory, {**compiled, "theorems": rows})

    def test_source_hash_or_canonical_identity_cannot_be_forged(self):
        inventory, compiled = fixtures()
        for field, value in (("canonical_name", "absent"), ("source_sha256", "forged")):
            changed = deepcopy(compiled)
            changed["theorems"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                compose(inventory, changed)

    def test_missing_or_duplicate_passage_cannot_be_linked(self):
        inventory, compiled = fixtures()
        for passages in ([], inventory["passages"] * 2):
            with self.subTest(passages=passages), self.assertRaises(ValueError):
                compose({**inventory, "passages": passages}, compiled)


if __name__ == "__main__":
    unittest.main()
